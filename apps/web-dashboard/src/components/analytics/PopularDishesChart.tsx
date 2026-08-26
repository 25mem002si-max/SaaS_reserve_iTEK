"use client";

import { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
} from "recharts";
import { fetchPopularDishes } from "@/lib/api";

const COLORS = ["#1E3A8A", "#3B82F6", "#F59E0B", "#16A34A", "#DC2626"];

export default function PopularDishesChart() {
  const [data, setData] = useState<{ name: string; value: number }[]>([]);

  useEffect(() => {
    fetchPopularDishes().then(setData).catch(console.error);
  }, []);

  return (
    <div className="bg-white rounded-xl p-4 shadow">
      <h2 className="font-semibold mb-2">Plats populaires</h2>
      <ResponsiveContainer width="100%" height={250}>
        <PieChart>
          <Pie data={data} dataKey="value" nameKey="name" outerRadius={90}>
            {data.map((_, index) => (
              <Cell key={index} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
