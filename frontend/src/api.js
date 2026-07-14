const BASE = "/api";

async function request(path, options) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch (e) {}
    throw new Error(detail);
  }
  const text = await res.text();
  return text ? JSON.parse(text) : null;
}

export const api = {
  health: () => request("/health"),
  getStock: (params = {}) => {
    const qs = new URLSearchParams();
    if (params.branch_id) qs.set("branch_id", params.branch_id);
    if (params.product_id) qs.set("product_id", params.product_id);
    const suffix = qs.toString() ? `?${qs}` : "";
    return request(`/stock${suffix}`);
  },
  getProducts: () => request("/products"),
  getBranches: () => request("/branches"),
  getAlerts: () => request("/alerts"),
  getDepletionRate: (days = 7) => request(`/stats/depletion-rate?days=${days}`),
  getMovements: (params = {}) => {
    const qs = new URLSearchParams();
    if (params.branch_id) qs.set("branch_id", params.branch_id);
    if (params.product_id) qs.set("product_id", params.product_id);
    if (params.reason) qs.set("reason", params.reason);
    qs.set("limit", params.limit ?? 25);
    qs.set("offset", params.offset ?? 0);
    return request(`/movements?${qs}`);
  },
  createMovement: (payload) =>
    request("/movements", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};