"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  cloneSettings, createDemoSettings, SETTINGS_TABS, validateSettings,
  type RestaurantSettings, type SettingsTab,
} from "@/lib/restaurant-settings";
import { SETTINGS_MODE, loadRestaurantSettings, saveRestaurantSection } from "@/lib/settings-api";

/** Comparaison adaptée à ce petit objet JSON, sans Date, Map ou référence cyclique.
 * On compare section par section : enregistrer Général ne valide pas Horaires.
 */
const same = (a: unknown, b: unknown) => JSON.stringify(a) === JSON.stringify(b);

export function useRestaurantSettings() {
  const preview = SETTINGS_MODE === "preview";
  const [saved, setSaved] = useState<RestaurantSettings>(createDemoSettings);
  const [draft, setDraft] = useState<RestaurantSettings>(createDemoSettings);
  const [loading, setLoading] = useState(!preview);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [feedback, setFeedback] = useState<{ kind: "success" | "error"; text: string } | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const version = useRef("");
  const mounted = useRef(false);
  // Une ref empêche un double envoi même avant le prochain rendu React.
  const savingLock = useRef(false);
  const leaveConfirmed = useRef(false);

  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; };
  }, []);

  useEffect(() => {
    if (preview) return;
    let current = true;
    setLoading(true);
    setLoadError(null);
    loadRestaurantSettings().then((response) => {
      if (!current) return;
      version.current = response.version;
      setSaved(cloneSettings(response.settings));
      setDraft(cloneSettings(response.settings));
    }).catch((error: unknown) => {
      if (current) setLoadError(error instanceof Error ? error.message : "Chargement impossible.");
    }).finally(() => { if (current) setLoading(false); });
    // Une ancienne réponse ne doit pas remplacer les données d'un nouvel
    // effet, notamment lors du double montage de StrictMode en développement.
    return () => { current = false; };
  }, [preview, reloadKey]);

  const dirtyTabs = SETTINGS_TABS.filter(({ id }) => !same(draft[id], saved[id])).map(({ id }) => id);
  const dirty = dirtyTabs.length > 0;

  useEffect(() => {
    if (!dirty && !saving) return;
    const warn = (event: BeforeUnloadEvent) => {
      if (leaveConfirmed.current) return;
      event.preventDefault();
      event.returnValue = "";
    };
    // Protège le rechargement/la fermeture, selon les capacités du navigateur.
    // Les clics de navigation interne sont traités séparément dans le panneau.
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty, saving]);

  function updateSection<K extends SettingsTab>(section: K, values: RestaurantSettings[K]) {
    if (savingLock.current) return;
    setDraft((previous) => ({ ...previous, [section]: values }));
    setFeedback(null);
    setErrors({});
  }

  function discard(section: SettingsTab) {
    if (savingLock.current) return;
    setDraft((previous) => ({ ...previous, [section]: cloneSettings(saved)[section] }));
    setErrors({});
    setFeedback(null);
  }

  async function save(section: SettingsTab) {
    if (savingLock.current || loading || loadError) return;
    // Un nombre vidé vaut NaN dans le formulaire. Lorsqu'on désactive sa
    // fonctionnalité, on restaure la dernière valeur finie au lieu d'envoyer
    // null (résultat de JSON.stringify(NaN)) à l'API.
    const candidate = cloneSettings(draft);
    if (!candidate.reservations.depositEnabled && !Number.isFinite(candidate.reservations.depositValue)) {
      candidate.reservations.depositValue = saved.reservations.depositValue;
    }
    if (!candidate.agent.enabled && !Number.isFinite(candidate.agent.humanThreshold)) {
      candidate.agent.humanThreshold = saved.agent.humanThreshold;
    }
    const validation = validateSettings(section, candidate);
    setErrors(validation);
    setFeedback(null);
    if (Object.keys(validation).length) return;
    savingLock.current = true;
    setSaving(true);
    try {
      if (preview) {
        // C'est un instantané EN MÉMOIRE, pas une écriture durable.
        // Aucun localStorage, secret ou appel à l'agent réel dans ce mode.
        setSaved((previous) => ({ ...previous, [section]: candidate[section] }));
        setDraft((previous) => ({ ...previous, [section]: candidate[section] }));
        setFeedback({ kind: "success", text: "Brouillon conservé dans cet aperçu uniquement. Un rechargement l’efface." });
      } else {
        const response = await saveRestaurantSection(section, candidate[section], version.current);
        if (!mounted.current) return;
        version.current = response.version;
        // Conserve les brouillons des autres onglets ; les sections non
        // modifiées reçoivent en revanche la valeur canonique du serveur.
        const next = cloneSettings(response.settings);
        for (const tab of SETTINGS_TABS) {
          if (tab.id !== section && !same(draft[tab.id], saved[tab.id])) {
            Object.assign(next, { [tab.id]: draft[tab.id] });
          }
        }
        setSaved(cloneSettings(response.settings));
        setDraft(next);
        setFeedback({ kind: "success", text: "Les paramètres de cet onglet ont été enregistrés par le serveur." });
      }
    } catch (error) {
      if (mounted.current) setFeedback({ kind: "error", text: error instanceof Error ? error.message : "Enregistrement impossible." });
    } finally {
      savingLock.current = false;
      if (mounted.current) setSaving(false);
    }
  }

  const clearFeedback = useCallback(() => { setFeedback(null); setErrors({}); }, []);
  return {
    preview, saved, draft, loading, loadError, saving, errors, feedback,
    dirty, dirtyTabs, updateSection, discard, save, clearFeedback,
    // La boîte de confirmation a déjà obtenu l'accord de l'utilisateur.
    // Évite de lui poser une seconde fois la même question via beforeunload.
    confirmLeave: () => { leaveConfirmed.current = true; },
    retry: () => setReloadKey((value) => value + 1),
  };
}
