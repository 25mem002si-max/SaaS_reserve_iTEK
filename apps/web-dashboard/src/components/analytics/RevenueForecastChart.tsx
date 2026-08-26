"use client";

import { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import { fetchRevenueForecast } from "@/lib/api";

export default function RevenueForecastChart() {
  const [data, setData] = useState<{ month: string; revenue: number }[]>([]);

  useEffect(() => {
    fetchRevenueForecast().then(setData).catch(console.error);
  }, []);

  return (
    <div className="bg-white rounded-xl p-4 shadow">
      <h2 className="font-semibold mb-2">Prevision de chiffre d'affaires</h2>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="month" />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="revenue" stroke="#16A34A" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
