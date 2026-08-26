import AttendanceChart from "@/components/analytics/AttendanceChart";
import PopularDishesChart from "@/components/analytics/PopularDishesChart";
import RevenueForecastChart from "@/components/analytics/RevenueForecastChart";

export default function AnalyticsPage() {
  return (
    <div className="space-y-8">
      <h1 className="text-xl font-semibold">Analytics</h1>
      <AttendanceChart />
      <PopularDishesChart />
      <RevenueForecastChart />
    </div>
  );
}
