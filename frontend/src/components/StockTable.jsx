import { useMemo } from "react";

export default function StockTable({ stock }) {
  const rows = useMemo(() => {
    if (!stock) return [];
    return [...stock].sort((a, b) =>
      a.branch_name.localeCompare(b.branch_name) || a.product_name.localeCompare(b.product_name),
    );
  }, [stock]);

  if (!stock || stock.length === 0) {
    return <p className="placeholder">No stock data yet.</p>;
  }

  return (
    <table>
      <thead>
        <tr>
          <th>Branch</th>
          <th>Product</th>
          <th>SKU</th>
          <th>Qty</th>
          <th>Threshold</th>
          <th>Status</th>
          <th>Ver</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={`${r.branch_id}-${r.product_id}`}>
            <td>{r.branch_name}</td>
            <td>{r.product_name}</td>
            <td style={{ color: "var(--text-dim)", fontSize: "0.8rem" }}>{r.sku}</td>
            <td style={{ fontWeight: 600 }}>{r.quantity}</td>
            <td style={{ color: "var(--text-dim)" }}>{r.low_stock_threshold}</td>
            <td>
              {r.quantity < r.low_stock_threshold ? (
                <span className="badge badge-danger">Low</span>
              ) : (
                <span className="badge badge-ok">OK</span>
              )}
            </td>
            <td style={{ color: "var(--text-dim)" }}>{r.version}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}