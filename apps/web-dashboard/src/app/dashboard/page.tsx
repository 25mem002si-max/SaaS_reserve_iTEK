import FloorPlan from "@/components/dashboard/FloorPlan";
import AgentToggle from "@/components/dashboard/AgentToggle";

// Vue synoptique de la salle en temps reel + interrupteur agent IA
export default function DashboardHomePage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Vue de la salle</h1>
        <AgentToggle />
      </div>
      <FloorPlan />
    </div>
  );
}
