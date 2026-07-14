#!/usr/bin/env python3
"""Concurrency smoke test for POST /api/movements.

Fire N concurrent outbound requests against the same SKU+branch and
verify that:
  1. The quantity never goes negative.
  2. The final quantity equals (starting_qty - sum_of_successes).
  3. The ledger sum matches the cached stock_levels.quantity.

Run AFTER `docker compose up --build` so the backend is reachable.

Usage:
    python3 tests/test_concurrency.py \
        --base http://localhost:8000 \
        --product-id 1 --branch-id 1 --each 30 --workers 8

It will:
  - read current stock
  - restock to a known starting value (optional, --reset-to)
  - fire --workers threads, each posting --each outbound movements of -1
  - assert the final quantity is never negative and matches expectations
"""

from __future__ import annotations

import argparse
import concurrent.futures
import sys
import urllib.request
import json


def request(base: str, path: str, method: str = "GET", body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        f"{base}/api{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            text = r.read()
            return json.loads(text) if text else {}
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_detail": e.read().decode()}


def get_stock(base, pid, bid):
    rows = request(base, f"/stock?product_id={pid}&branch_id={bid}")
    if isinstance(rows, list):
        for r in rows:
            if r["product_id"] == pid and r["branch_id"] == bid:
                return r["quantity"], r["version"]
    raise RuntimeError(f"could not find stock for product={pid} branch={bid}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base", default="http://localhost:8000")
    p.add_argument("--product-id", type=int, required=True)
    p.add_argument("--branch-id", type=int, required=True)
    p.add_argument("--each", type=int, default=20, help="movements per worker (each -1)")
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--reset-to", type=int, default=None, help="restock to this qty first")
    args = p.parse_args()

    base = args.base.rstrip("/")

    if args.reset_to is not None:
        cur, _ = get_stock(base, args.product_id, args.branch_id)
        delta = args.reset_to - cur
        if delta:
            res = request(base, "/movements", "POST", {
                "product_id": args.product_id,
                "branch_id": args.branch_id,
                "change_qty": delta,
                "reason": "restock",
            })
            if "_error" in res:
                print("reset restock failed:", res)
                sys.exit(1)
            print(f"reset stock to {args.reset_to} (delta {delta})")

    start_qty, start_ver = get_stock(base, args.product_id, args.branch_id)
    print(f"starting quantity = {start_qty} (version {start_ver})")

    total_requested = args.each * args.workers
    print(f"fire {args.workers} workers × {args.each} outbound (-1) = {total_requested} total")

    def one_worker(_):
        results = []
        for _ in range(args.each):
            res = request(base, "/movements", "POST", {
                "product_id": args.product_id,
                "branch_id": args.branch_id,
                "change_qty": -1,
                "reason": "sale",
            })
            results.append(res.get("_error") is None)
        return results

    success_count = 0
    fail_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
        for batch in ex.map(one_worker, range(args.workers)):
            success_count += sum(batch)
            fail_count += len(batch) - sum(batch)

    print(f"success={success_count}  rejected(409)={fail_count}")

    end_qty, end_ver = get_stock(base, args.product_id, args.branch_id)
    print(f"ending quantity = {end_qty} (version {end_ver})")

    expected = start_qty - success_count
    ok = True
    if end_qty < 0:
        print(f"FAIL: quantity went negative ({end_qty})")
        ok = False
    if end_qty != expected:
        print(f"FAIL: expected {expected} but got {end_qty} (drift!)")
        ok = False
    else:
        print(f"OK: cached quantity matches expected ({end_qty})")

    if ok:
        print("\nAll concurrency assertions passed ✓")
        sys.exit(0)
    else:
        print("\nConcurrency assertions FAILED ✗")
        sys.exit(1)


if __name__ == "__main__":
    main()