// ============================================================================
// HomeFooter : pied de page de la vitrine publique.
// ============================================================================
// Volontairement tres simple : une page de reservation doit rester
// focalisee sur son objectif principal, on evite donc de disperser
// l'attention avec un pied de page charge de liens.
export default function HomeFooter() {
  return (
    // bg-primary : bleu fonce du theme. text-white/70 : blanc a 70% d'opacite (discret).
    // mt-auto : pousse le footer tout en bas grace au parent "flex flex-col min-h-screen" dans page.tsx.
    <footer className="bg-primary text-white/70 mt-auto">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 text-sm flex flex-col sm:flex-row items-center justify-between gap-2">
        {/* getFullYear() : annee courante calculee automatiquement, jamais a mettre a jour a la main */}
        <p>© {new Date().getFullYear()} SaaS Reservation IA — Tous droits reserves.</p>
        <p>Reservation de restaurant assistee par intelligence artificielle en RDC.</p>
      </div>
    </footer>
  );
}