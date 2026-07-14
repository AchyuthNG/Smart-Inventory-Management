import { useState, useEffect, useCallback } from "react";

const REASONS = ["", "restock", "sale", "damaged", "transfer"];
const PAGE_SIZE = 15;

export default function Ledger({ products, branches, refreshKey }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  // filters
  const [branchFilter, setBranchFilter] = useState("");
  const [productFilter, setProductFilter] = useState("");
  const [reasonFilter, setReasonFilter] = useState("");

  // pagination
  const [offset, setOffset] = useState(0);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiGetMovements({
        branch_id: branchFilter || undefined,
        product_id: productFilter || undefined,
        reason: reasonFilter || undefined,
        limit: PAGE_SIZE,
        offset,
      });
      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [branchFilter, productFilter, reasonFilter, offset]);

  // refetch whenever filters/pagination/refreshKey change
  useEffect(() => {
    fetchData();
  }, [fetchData, refreshKey]);

  // reset pagination when filters change
  useEffect(() => {
    setOffset(0);
  }, [branchFilter, productFilter, reasonFilter]);

  const total = data?.total ?? 0;
  const items = data?.items ?? [];
  const hasPrev = offset > 0;
  const hasNext = data?.has_more ?? false;

  return (
    <div>
      <div className="ledger-filters">
        <select value={branchFilter} onChange={(e) => setBranchFilter(e.target.value)}>
          <option value="">All branches</option>
          {branches.map((b) => (
            <option key={b.id} value={b.id}>
              {b.name}
            </option>
          ))}
        </select>
        <select value={productFilter} onChange={(e) => setProductFilter(e.target.value)}>
          <option value="">All products</option>
          {products.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
        <select value={reasonFilter} onChange={(e) => setReasonFilter(e.target.value)}>
          {REASONS.map((r) => (
            <option key={r} value={r}>
              {r === "" ? "All reasons" : r}
            </option>
          ))}
        </select>
      </div>

      {error && <div className="error-msg">{error}</div>}

      {!loading && items.length === 0 && !error ? (
        <p className="placeholder">No movements found for these filters.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Branch</th>
              <th>Product</th>
              <th>Direction</th>
              <th>Qty</th>
              <th>Reason</th>
            </tr>
          </thead>
          <tbody>
            {items.map((m) => (
              <tr key={m.id}>
                <td className="ts">{new Date(m.created_at).toLocaleString()}</td>
                <td>{m.branch_name}</td>
                <td>{m.product_name}</td>
                <td>
                  <span className={`badge badge-${m.direction}`}>
                    {m.direction === "in" ? "Inbound" : "Outbound"}
                  </span>
                </td>
                <td style={{ fontWeight: 600, color: m.change_qty >= 0 ? "var(--accent)" : "var(--danger)" }}>
                  {m.change_qty >= 0 ? "+" : ""}
                  {m.change_qty}
                </td>
                <td style={{ color: "var(--text-dim)" }}>{m.reason || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {total > PAGE_SIZE && (
        <div className="ledger-pager">
          <button
            onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
            disabled={!hasPrev}
          >
            ← Prev
          </button>
          <span className="pager-info">
            {offset + 1}–{Math.min(offset + PAGE_SIZE, total)} of {total}
          </span>
          <button
            onClick={() => setOffset(offset + PAGE_SIZE)}
            disabled={!hasNext}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}

// local helper so we don't need props drilling of api
import { api } from "../api.js";
function apiGetMovements(params) {
  return api.getMovements(params);
}