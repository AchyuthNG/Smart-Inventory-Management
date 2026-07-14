import { useState, useEffect, useCallback } from "react";
import { api } from "./api.js";
import { usePolling } from "./usePolling.js";
import StockTable from "./components/StockTable.jsx";
import MovementsForm from "./components/MovementsForm.jsx";
import AlertsPanel from "./components/AlertsPanel.jsx";
import StockBarChart from "./components/BarChart.jsx";
import Ledger from "./components/Ledger.jsx";

export default function App() {
  // static data
  const [products, setProducts] = useState([]);
  const [branches, setBranches] = useState([]);
  const [healthOk, setHealthOk] = useState(false);

  // polled data
  const stock = usePolling(api.getStock, 7000);
  const alerts = usePolling(api.getAlerts, 10000);

  // bump this after each new movement so the ledger refetches
  const [ledgerRefreshKey, setLedgerRefreshKey] = useState(0);

  useEffect(() => {
    api.getProducts().then(setProducts).catch(() => {});
    api.getBranches().then(setBranches).catch(() => {});
  }, []);

  useEffect(() => {
    const checkHealth = () => api.health().then(() => setHealthOk(true)).catch(() => setHealthOk(false));
    checkHealth();
    const id = setInterval(checkHealth, 15000);
    return () => clearInterval(id);
  }, []);

  const handleMovement = useCallback(
    async (payload) => {
      await api.createMovement(payload);
      // immediate refetch after a successful POST
      await stock.refetch();
      await alerts.refetch();
      setLedgerRefreshKey((k) => k + 1);
    },
    [stock, alerts],
  );

  return (
    <div className="app">
      <div className="header">
        <h1>
          Schrute Paper Co. <span>· Inventory</span>
        </h1>
        <span style={{ color: "var(--text-dim)", fontSize: "0.85rem" }}>
          API {healthOk ? "online" : "offline"}
          <span className={`health-dot ${healthOk ? "health-ok" : "health-bad"}`}></span>
        </span>
      </div>

      <div className="grid">
        <div className="panel">
          <h2>Stock Levels</h2>
          <StockTable stock={stock.data} />
        </div>
        <div className="panel">
          <h2>Record Movement</h2>
          <MovementsForm products={products} branches={branches} onSubmitted={handleMovement} />
        </div>
      </div>

      <div className="grid">
        <div className="panel">
          <h2>Stock by Product & Branch</h2>
          <StockBarChart stock={stock.data} branches={branches} />
        </div>
        <div className="panel">
          <h2>Low-Stock Alerts</h2>
          <AlertsPanel alerts={alerts.data} />
        </div>
      </div>

      <div className="grid">
        <div className="panel full-panel">
          <h2>Stock Movements Ledger</h2>
          <Ledger products={products} branches={branches} refreshKey={ledgerRefreshKey} />
        </div>
      </div>
    </div>
  );
}