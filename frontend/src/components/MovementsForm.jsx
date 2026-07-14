import { useState, useEffect } from "react";

export default function MovementsForm({ products, branches, onSubmitted }) {
  const [productId, setProductId] = useState("");
  const [branchId, setBranchId] = useState("");
  const [changeQty, setChangeQty] = useState("");
  const [reason, setReason] = useState("restock");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (products.length && !productId) setProductId(products[0].id);
    if (branches.length && !branchId) setBranchId(branches[0].id);
  }, [products, branches]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setSubmitting(true);
    try {
      const qty = parseInt(changeQty, 10);
      if (!Number.isInteger(qty) || qty === 0) {
        throw new Error("Quantity must be a non-zero integer.");
      }
      await onSubmitted({
        product_id: parseInt(productId, 10),
        branch_id: parseInt(branchId, 10),
        change_qty: qty,
        reason,
      });
      setSuccess("Movement recorded successfully.");
      setChangeQty("");
      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="form-row">
        <div>
          <label>Product</label>
          <select value={productId} onChange={(e) => setProductId(e.target.value)}>
            {products.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label>Branch</label>
          <select value={branchId} onChange={(e) => setBranchId(e.target.value)}>
            {branches.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name}
              </option>
            ))}
          </select>
        </div>
      </div>
      <div className="form-row">
        <div>
          <label>Quantity (+in / -out)</label>
          <input
            type="number"
            value={changeQty}
            onChange={(e) => setChangeQty(e.target.value)}
            placeholder="e.g. 50 or -20"
          />
        </div>
        <div>
          <label>Reason</label>
          <select value={reason} onChange={(e) => setReason(e.target.value)}>
            <option value="restock">restock</option>
            <option value="sale">sale</option>
            <option value="damaged">damaged</option>
            <option value="transfer">transfer</option>
          </select>
        </div>
      </div>
      {error && <div className="error-msg">{error}</div>}
      {success && <div className="success-msg">{success}</div>}
      <button type="submit" disabled={submitting}>
        {submitting ? "Recording…" : "Record Movement"}
      </button>
    </form>
  );
}