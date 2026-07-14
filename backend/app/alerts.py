"""Rule-based low-stock and depletion-rate alerting.

Called as a BackgroundTask after a movement is saved.  A failure here
never blocks or reverts the movement — the ledger is already written.
"""

from datetime import datetime, timezone, timedelta

from .db import get_conn, put_conn


def check_and_create_alerts(product_id: int, branch_id: int) -> None:
    """Run both rules for a single product+branch pair and insert alerts."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # --- fetch current quantity + threshold ---
            cur.execute(
                """
                SELECT sl.quantity, p.low_stock_threshold
                FROM stock_levels sl
                JOIN products p ON p.id = sl.product_id
                WHERE sl.product_id = %s AND sl.branch_id = %s
                """,
                (product_id, branch_id),
            )
            row = cur.fetchone()
            if not row:
                return
            quantity, threshold = row

            # --- rule 1: threshold ---
            should_alert = quantity < threshold

            # --- rule 2: depletion-rate (would run out within 3 days) ---
            if not should_alert:
                days_until_empty = _days_until_empty(cur, product_id, branch_id, quantity)
                if days_until_empty is not None and days_until_empty < 3:
                    should_alert = True

            # --- resolve old alerts if stock is healthy ---
            if not should_alert:
                cur.execute(
                    """
                    UPDATE low_stock_alerts
                    SET resolved = true
                    WHERE product_id = %s AND branch_id = %s AND resolved = false
                    """,
                    (product_id, branch_id),
                )
            else:
                # avoid duplicate unresolved alerts for the same product+branch
                cur.execute(
                    """
                    SELECT 1 FROM low_stock_alerts
                    WHERE product_id = %s AND branch_id = %s AND resolved = false
                    """,
                    (product_id, branch_id),
                )
                if not cur.fetchone():
                    cur.execute(
                        """
                        INSERT INTO low_stock_alerts (product_id, branch_id)
                        VALUES (%s, %s)
                        """,
                        (product_id, branch_id),
                    )
        conn.commit()
    except Exception:
        conn.rollback()
    finally:
        put_conn(conn)


def compute_depletion_rate(cur, days: int = 7):
    """Return list of depletion-rate dicts for the given window."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    cur.execute(
        """
        SELECT
            sm.product_id,
            p.name  AS product_name,
            sm.branch_id,
            b.name  AS branch_name,
            COALESCE(SUM(ABS(sm.change_qty)), 0)::float / %s AS avg_daily_outbound,
            sl.quantity AS current_stock
        FROM stock_movements sm
        JOIN products p ON p.id = sm.product_id
        JOIN branches b ON b.id = sm.branch_id
        JOIN stock_levels sl ON sl.product_id = sm.product_id AND sl.branch_id = sm.branch_id
        WHERE sm.change_qty < 0 AND sm.created_at >= %s
        GROUP BY sm.product_id, p.name, sm.branch_id, b.name, sl.quantity
        """,
        (days, cutoff),
    )
    rows = cur.fetchall()
    result = []
    for product_id, product_name, branch_id, branch_name, avg_daily, current_stock in rows:
        days_until_empty = (current_stock / avg_daily) if avg_daily > 0 else None
        fast = days_until_empty is not None and days_until_empty < 3
        result.append({
            "product_id": product_id,
            "product_name": product_name,
            "branch_id": branch_id,
            "branch_name": branch_name,
            "avg_daily_outbound": round(avg_daily, 2),
            "current_stock": current_stock,
            "days_until_empty": round(days_until_empty, 1) if days_until_empty else None,
            "fast_depleting": fast,
        })
    return result


def _days_until_empty(cur, product_id: int, branch_id: int, quantity: int) -> float | None:
    """Avg daily outbound over last 7 days → days until stock hits 0."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    cur.execute(
        """
        SELECT COALESCE(SUM(ABS(change_qty)), 0)::float / 7.0
        FROM stock_movements
        WHERE product_id = %s AND branch_id = %s
          AND change_qty < 0 AND created_at >= %s
        """,
        (product_id, branch_id, cutoff),
    )
    avg_daily = cur.fetchone()[0]
    if avg_daily <= 0:
        return None
    return quantity / avg_daily