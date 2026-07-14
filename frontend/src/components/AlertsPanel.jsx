export default function AlertsPanel({ alerts }) {
  if (!alerts || alerts.length === 0) {
    return <p className="placeholder">No active alerts. 🎉</p>;
  }

  return (
    <div>
      {alerts.map((a) => (
        <div key={a.id} className="alert-item">
          <div>
            <div style={{ fontWeight: 600 }}>
              {a.product_name}
            </div>
            <div className="meta">
              {a.branch_name} · {new Date(a.triggered_at).toLocaleString()}
            </div>
          </div>
          <span className="badge badge-danger">Low Stock</span>
        </div>
      ))}
    </div>
  );
}