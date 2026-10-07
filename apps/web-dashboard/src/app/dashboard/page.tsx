import FloorPlan from "@/components/dashboard/FloorPlan";
import AgentToggle from "@/components/dashboard/AgentToggle";

// Vue synoptique de la salle en temps reel + interrupteur agent IA
export default function DashboardHomePage() {
  return (
    <div className="space-y-8 p-6 max-w-7xl mx-auto">
      {/* En-tête stylisé et centré */}
      <div className="flex flex-col items-center justify-center space-y-4 text-center">
        <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 bg-clip-text text-transparent drop-shadow-sm underline decoration-2 underline-offset-8 decoration-indigo-500/80">
          Vue de la salle
        </h1>
        
        {/* Conteneur pour le bouton de bascule */}
        <div className="bg-slate-50 p-1.5 rounded-xl shadow-sm border border-slate-100 transition-all hover:shadow-md">
          <AgentToggle />
        </div>
      </div>

      {/* Zone principale du plan de salle */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 min-h-[500px] transition-all hover:shadow-md">
        <FloorPlan />
      </div>
    </div>
  );
}
