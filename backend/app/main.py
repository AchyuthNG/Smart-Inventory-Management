from fastapi import FastAPI, BackgroundTasks, Query

from .db import get_conn, put_conn
from .models import (
    MovementCreate,
    MovementResultOut,
    StockLevelOut,
    ProductOut,
    BranchOut,
    AlertOut,
    DepletionRateOut,
    MovementOut,
    PaginatedMovementsOut,
)
from .alerts import check_and_create_alerts, compute_depletion_rate

app = FastAPI(title="Schrute Paper Co. — Inventory API", version="1.0")


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@app.get("/api/health")
def health():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return {"status": "ok"}
    finally:
        put_conn(conn)


# ---------------------------------------------------------------------------
# POST /api/movements  — transactional, concurrency-safe
# ---------------------------------------------------------------------------
@app.post("/api/movements", response_model=MovementResultOut)
def create_movement(movement: MovementCreate, bg: BackgroundTasks):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("BEGIN")

            # Ensure a stock_levels row exists (for first movement on a SKU+branch)
            cur.execute(
                """
                INSERT INTO stock_levels (product_id, branch_id, quantity, version)
                VALUES (%s, %s, 0, 0)
                ON CONFLICT (product_id, branch_id) DO NOTHING
                """,
                (movement.product_id, movement.branch_id),
            )

            # --- atomic conditional update ---
            cur.execute(
                """
                UPDATE stock_levels
                SET quantity = quantity + %s,
                    version = version + 1
                WHERE product_id = %s AND branch_id = %s
                  AND quantity + %s >= 0
                RETURNING quantity, version
                """,
                (movement.change_qty, movement.product_id, movement.branch_id, movement.change_qty),
            )
            row = cur.fetchone()

            if row is None:
                # outbound would oversell — reject, roll back, do NOT insert movement
                conn.rollback()
                return _oversold_error(movement)

            new_qty, new_version = row

            # --- insert into the append-only ledger ---
            cur.execute(
                """
                INSERT INTO stock_movements (product_id, branch_id, change_qty, reason)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (movement.product_id, movement.branch_id, movement.change_qty, movement.reason),
            )
            movement_id = cur.fetchone()[0]

            conn.commit()

            # --- background alerting: never blocks the movement ---
            bg.add_task(check_and_create_alerts, movement.product_id, movement.branch_id)

            return MovementResultOut(movement_id=movement_id, new_quantity=new_qty)
    except Exception as exc:
        conn.rollback()
        raise
    finally:
        put_conn(conn)


def _oversold_error(movement: MovementCreate):
    from fastapi import HTTPException
    raise HTTPException(
        status_code=409,
        detail=(
            f"Insufficient stock for product_id={movement.product_id} "
            f"at branch_id={movement.branch_id}: cannot apply "
            f"change_qty={movement.change_qty}."
        ),
    )


# ---------------------------------------------------------------------------
# GET /api/stock
# ---------------------------------------------------------------------------
@app.get("/api/stock", response_model=list[StockLevelOut])
def get_stock(
    branch_id: int | None = Query(None),
    product_id: int | None = Query(None),
):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            query = """
                SELECT sl.product_id, p.name, p.sku,
                       sl.branch_id, b.name,
                       sl.quantity, sl.version,
                       p.low_stock_threshold
                FROM stock_levels sl
                JOIN products p ON p.id = sl.product_id
                JOIN branches b ON b.id = sl.branch_id
                WHERE 1=1
            """
            params: list = []
            if branch_id is not None:
                query += " AND sl.branch_id = %s"
                params.append(branch_id)
            if product_id is not None:
                query += " AND sl.product_id = %s"
                params.append(product_id)
            query += " ORDER BY b.name, p.name"
            cur.execute(query, params)
            rows = cur.fetchall()
            return [
                StockLevelOut(
                    product_id=r[0], product_name=r[1], sku=r[2],
                    branch_id=r[3], branch_name=r[4],
                    quantity=r[5], version=r[6],
                    low_stock_threshold=r[7],
                    is_low=r[5] < r[7],
                )
                for r in rows
            ]
    finally:
        put_conn(conn)


# ---------------------------------------------------------------------------
# GET /api/products
# ---------------------------------------------------------------------------
@app.get("/api/products", response_model=list[ProductOut])
def get_products():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, sku, name, low_stock_threshold FROM products ORDER BY name")
            return [ProductOut(id=r[0], sku=r[1], name=r[2], low_stock_threshold=r[3]) for r in cur.fetchall()]
    finally:
        put_conn(conn)


# ---------------------------------------------------------------------------
# GET /api/branches
# ---------------------------------------------------------------------------
@app.get("/api/branches", response_model=list[BranchOut])
def get_branches():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM branches ORDER BY name")
            return [BranchOut(id=r[0], name=r[1]) for r in cur.fetchall()]
    finally:
        put_conn(conn)


# ---------------------------------------------------------------------------
# GET /api/alerts
# ---------------------------------------------------------------------------
@app.get("/api/alerts", response_model=list[AlertOut])
def get_alerts(
    resolved: bool = Query(False, description="If true, return resolved alerts; default unresolved only"),
):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT a.id, a.product_id, p.name, a.branch_id, b.name,
                       a.triggered_at, a.resolved
                FROM low_stock_alerts a
                JOIN products p ON p.id = a.product_id
                JOIN branches b ON b.id = a.branch_id
                WHERE a.resolved = %s
                ORDER BY a.triggered_at DESC
                """,
                (resolved,),
            )
            return [
                AlertOut(
                    id=r[0], product_id=r[1], product_name=r[2],
                    branch_id=r[3], branch_name=r[4],
                    triggered_at=r[5].isoformat(), resolved=r[6],
                )
                for r in cur.fetchall()
            ]
    finally:
        put_conn(conn)


# ---------------------------------------------------------------------------
# GET /api/stats/depletion-rate
# ---------------------------------------------------------------------------
@app.get("/api/stats/depletion-rate", response_model=list[DepletionRateOut])
def get_depletion_rate(days: int = Query(7, ge=1, le=90)):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            rows = compute_depletion_rate(cur, days)
            return [DepletionRateOut(**r) for r in rows]
    finally:
        put_conn(conn)


# ---------------------------------------------------------------------------
# GET /api/movements — append-only ledger, paginated + filterable
# ---------------------------------------------------------------------------
@app.get("/api/movements", response_model=PaginatedMovementsOut)
def get_movements(
    branch_id: int | None = Query(None),
    product_id: int | None = Query(None),
    reason: str | None = Query(None, description="Filter by reason e.g. 'sale','restock','damaged','transfer'"),
    limit: int = Query(25, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            where = "WHERE 1=1"
            params: list = []
            if branch_id is not None:
                where += " AND sm.branch_id = %s"
                params.append(branch_id)
            if product_id is not None:
                where += " AND sm.product_id = %s"
                params.append(product_id)
            if reason is not None:
                where += " AND sm.reason = %s"
                params.append(reason)

            # total count (before pagination)
            cur.execute(
                f"SELECT COUNT(*) FROM stock_movements sm {where}",
                params,
            )
            total = cur.fetchone()[0]

            cur.execute(
                f"""
                SELECT sm.id,
                       sm.product_id, p.name, p.sku,
                       sm.branch_id, b.name,
                       sm.change_qty,
                       sm.reason,
                       sm.created_at
                FROM stock_movements sm
                JOIN products p ON p.id = sm.product_id
                JOIN branches b ON b.id = sm.branch_id
                {where}
                ORDER BY sm.created_at DESC, sm.id DESC
                LIMIT %s OFFSET %s
                """,
                params + [limit, offset],
            )
            rows = cur.fetchall()
            items = [
                MovementOut(
                    id=r[0],
                    product_id=r[1], product_name=r[2], sku=r[3],
                    branch_id=r[4], branch_name=r[5],
                    change_qty=r[6],
                    direction="in" if r[6] >= 0 else "out",
                    reason=r[7],
                    created_at=r[8].isoformat(),
                )
                for r in rows
            ]
            return PaginatedMovementsOut(
                items=items,
                total=total,
                limit=limit,
                offset=offset,
                has_more=(offset + limit) < total,
            )
    finally:
        put_conn(conn)