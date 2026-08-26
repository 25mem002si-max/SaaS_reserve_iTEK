"use client";

import { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import { fetchAttendanceStats } from "@/lib/api";

export default function AttendanceChart() {
  const [data, setData] = useState<{ day: string; guests: number }[]>([]);

  useEffect(() => {
    fetchAttendanceStats().then(setData).catch(console.error);
  }, []);

  return (
    <div className="bg-white rounded-xl p-4 shadow">
      <h2 className="font-semibold mb-2">Frequentation (7 derniers jours)</h2>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="day" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="guests" fill="#3B82F6" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
