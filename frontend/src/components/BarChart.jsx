import { useMemo } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

const BRANCH_COLORS = ["#4f9551", "#f5a623", "#5b8def", "#e5484d", "#a855f7"];

export default function StockBarChart({ stock, branches }) {
  const data = useMemo(() => {
    if (!stock || !branches) return [];
    const productsMap = {};
    stock.forEach((s) => {
      if (!productsMap[s.product_name]) {
        productsMap[s.product_name] = { product: s.product_name };
      }
      productsMap[s.product_name][s.branch_name] = s.quantity;
    });
    return Object.values(productsMap);
  }, [stock, branches]);

  if (!data.length) {
    return <p className="placeholder">No data to chart.</p>;
  }

  const branchNames = branches.map((b) => b.name);

  return (
    <div className="chart-container" style={{ height: 380 }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 10, bottom: 10, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2e3a" />
          <XAxis dataKey="product" tick={{ fill: "#9ca3af", fontSize: 11 }} angle={-15} height={60} textAnchor="end" />
          <YAxis tick={{ fill: "#9ca3af", fontSize: 12 }} />
          <Tooltip
            contentStyle={{
              background: "#1a1d27",
              border: "1px solid #2a2e3a",
              borderRadius: 8,
              color: "#e4e4e7",
            }}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          {branchNames.map((name, i) => (
            <Bar key={name} dataKey={name} fill={BRANCH_COLORS[i % BRANCH_COLORS.length]} radius={[4, 4, 0, 0]} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}