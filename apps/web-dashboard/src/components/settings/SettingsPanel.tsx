"use client";

import { useEffect, useRef, useState, type ReactNode, type KeyboardEvent } from "react";
import { useRestaurantSettings } from "@/hooks/useRestaurantSettings";
import { SETTINGS_TABS, type RestaurantSettings, type SettingsTab } from "@/lib/restaurant-settings";
import styles from "./SettingsPanel.module.css";

/**
 * Les champs partagent le même contrat d'accessibilité : un vrai label,
 * un identifiant stable et une erreur reliée par aria-describedby.
 * La présentation reste ici ; les règles métier sont dans restaurant-settings.
 */
function Field({ id, label, hint, error, children }: {
  id: string; label: string; hint?: string; error?: string; children: ReactNode;
}) {
  return <div className={styles.field}>
    <label htmlFor={id}>{label}</label>
    {children}
    {hint && <p id={`${id}-hint`} className={styles.hint}>{hint}</p>}
    {error && <p id={`${id}-error`} className={styles.fieldError}>{error}</p>}
  </div>;
}

function Section({ title, description, children }: { title: string; description?: string; children: ReactNode }) {
  return <section className={styles.section}>
    <div className={styles.sectionHeading}><h3>{title}</h3>{description && <p>{description}</p>}</div>
    {children}
  </section>;
}

function Switch({ label, description, checked, onChange }: {
  label: string; description?: string; checked: boolean; onChange: (value: boolean) => void;
}) {
  return <label className={styles.switchRow}>
    <span><strong>{label}</strong>{description && <small>{description}</small>}</span>
    {/* Une checkbox native conserve le fonctionnement clavier et le focus.
        Le dessin du commutateur est seulement une couche visuelle. */}
    <span className={styles.switch}>
      <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} />
      <span aria-hidden="true" />
    </span>
  </label>;
}

export default function SettingsPanel() {
  const state = useRestaurantSettings();
  const { draft, errors } = state;
  const [active, setActive] = useState<SettingsTab>("general");
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [pending, setPending] = useState<{ type: "discard"; tab: SettingsTab } | { type: "leave"; url: string } | null>(null);
  const dialog = useRef<HTMLDialogElement>(null);
  const form = useRef<HTMLFormElement>(null);
  const tabButtons = useRef<Array<HTMLButtonElement | null>>([]);
  const activeInfo = SETTINGS_TABS.find((tab) => tab.id === active)!;
  const currentDirty = state.dirtyTabs.includes(active);

  useEffect(() => {
    setTheme(window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  }, []);

  useEffect(() => {
    if (pending) dialog.current?.showModal();
    else dialog.current?.close();
  }, [pending]);

  useEffect(() => {
    if (!Object.keys(errors).length) return;
    // Amène immédiatement le clavier sur le premier champ à corriger.
    form.current?.querySelector<HTMLElement>('[aria-invalid="true"]')?.focus();
  }, [errors]);

  useEffect(() => {
    if (!state.dirty && !state.saving) return;
    const intercept = (event: MouseEvent) => {
      if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      const anchor = (event.target as Element).closest?.("a[href]") as HTMLAnchorElement | null;
      if (!anchor || anchor.target === "_blank" || anchor.hasAttribute("download")) return;
      const url = new URL(anchor.href, window.location.href);
      if (!["http:", "https:"].includes(url.protocol) || url.href.split("#")[0] === window.location.href.split("#")[0]) return;
      // Capture AVANT Next Link : sinon le routeur pourrait quitter la page
      // avant l'affichage de la confirmation. Les onglets, eux, conservent
      // leurs brouillons et ne nécessitent pas de confirmation.
      event.preventDefault();
      event.stopPropagation();
      if (!state.saving) setPending({ type: "leave", url: url.href });
    };
    document.addEventListener("click", intercept, true);
    return () => document.removeEventListener("click", intercept, true);
  }, [state.dirty, state.saving]);

  // Les clés de champ sont les mêmes dans le modèle, les erreurs et le DOM.
  // Pas de recherche fragile par position lorsque des services sont ajoutés.
  const attributes = (id: string, hasHint = false) => ({
    id,
    name: id,
    "aria-invalid": Boolean(errors[id]),
    "aria-describedby": [hasHint ? `${id}-hint` : "", errors[id] ? `${id}-error` : ""].filter(Boolean).join(" ") || undefined,
  });

  function text(section: "general" | "agent", key: string, label: string, hint?: string, multiline = false, type = "text") {
    const id = `${section}.${key}`;
    const values = draft[section] as unknown as Record<string, string>;
    // Limites alignées sur la validation, afin qu'une valeur admise par
    // l'API reste éditable sans être tronquée par le formulaire.
    const limits: Record<string, number> = {
      name: section === "general" ? 120 : 100, city: 120, address: 300,
      description: 2000, welcomeMessage: 2000, instructions: 10000,
      phone: 50, whatsapp: 50, handoffPhone: 50, email: 254,
    };
    const change = (value: string) => {
      if (section === "general") state.updateSection("general", { ...draft.general, [key]: value });
      else state.updateSection("agent", { ...draft.agent, [key]: value });
    };
    return <Field key={id} id={id} label={label} hint={hint} error={errors[id]}>
      {multiline
        ? <textarea {...attributes(id, Boolean(hint))} rows={3} maxLength={limits[key]} value={values[key]} onChange={(e) => change(e.target.value)} />
        : <input {...attributes(id, Boolean(hint))} type={type} maxLength={limits[key]} value={values[key]} onChange={(e) => change(e.target.value)} />}
    </Field>;
  }

  function number(section: "reservations" | "agent", key: string, label: string, hint?: string, min = 0, max = 10000, step = 1) {
    const id = `${section}.${key}`;
    const value = (draft[section] as unknown as Record<string, number>)[key];
    return <Field id={id} label={label} hint={hint} error={errors[id]}>
      <input {...attributes(id, Boolean(hint))} type="number" min={min} max={max} step={step}
        value={Number.isFinite(value) ? value : ""}
        onChange={(e) => {
          // Un champ vidé reste vide (NaN), pas zéro. La validation peut
          // ainsi distinguer « information absente » et « délai de 0 ».
          const next = e.target.value === "" ? NaN : Number(e.target.value);
          if (section === "reservations") state.updateSection(section, { ...draft.reservations, [key]: next });
          else state.updateSection(section, { ...draft.agent, [key]: next });
        }} />
    </Field>;
  }

  function select(id: string, label: string, value: string, options: Array<[string, string]>, change: (value: string) => void, hint?: string) {
    return <Field id={id} label={label} hint={hint} error={errors[id]}>
      <select {...attributes(id, Boolean(hint))} value={value} onChange={(e) => change(e.target.value)}>
        {options.map(([key, caption]) => <option key={key} value={key}>{caption}</option>)}
      </select>
    </Field>;
  }

  function switchTab(tab: SettingsTab) {
    if (state.saving) return;
    setActive(tab);
    state.clearFeedback();
  }

  function tabKeys(event: KeyboardEvent, index: number) {
    let next = index;
    if (event.key === "ArrowRight") next = (index + 1) % SETTINGS_TABS.length;
    else if (event.key === "ArrowLeft") next = (index - 1 + SETTINGS_TABS.length) % SETTINGS_TABS.length;
    else if (event.key === "Home") next = 0;
    else if (event.key === "End") next = SETTINGS_TABS.length - 1;
    else return;
    event.preventDefault();
    tabButtons.current[next]?.focus();
    switchTab(SETTINGS_TABS[next].id);
  }

  function changeDay(index: number, patch: Partial<RestaurantSettings["hours"]["days"][number]>) {
    state.updateSection("hours", {
      ...draft.hours,
      days: draft.hours.days.map((day, i) => i === index ? { ...day, ...patch } : day),
    });
  }

  return <main className={styles.root} data-theme={theme}>
    <header className={styles.header}>
      <div>
        <p className={styles.eyebrow}>ESPACE RESTAURATEUR / CONFIGURATION</p>
        <h1>Paramètres du restaurant</h1>
        <p className={styles.lead}>Votre établissement, vos horaires, vos règles.</p>
      </div>
      <button className={styles.quietButton} type="button" onClick={() => setTheme(theme === "light" ? "dark" : "light")}>
        {theme === "light" ? "Mode sombre" : "Mode clair"}
      </button>
    </header>

    <div className={styles.notice}>
      <span className={styles.modeBadge}>{state.preview ? "MODE APERÇU" : "MODE API"}</span>
      <p>{state.preview
        ? "Données de démonstration. Les brouillons restent dans cette page et sont perdus au rechargement. Aucun effet sur le restaurant réel."
        : "Les réglages sont chargés et enregistrés auprès de l’API de votre restaurant."}</p>
    </div>

    <div className={styles.tabs} role="tablist" aria-label="Rubriques des paramètres">
      {SETTINGS_TABS.map((tab, index) => <button
        type="button" role="tab" key={tab.id} id={`tab-${tab.id}`} aria-controls={`panel-${tab.id}`}
        aria-selected={active === tab.id} tabIndex={active === tab.id ? 0 : -1}
        disabled={state.saving} ref={(node) => { tabButtons.current[index] = node; }}
        onKeyDown={(event) => tabKeys(event, index)} onClick={() => switchTab(tab.id)}
      ><span className={styles.tabIndex}>{String(index + 1).padStart(2, "0")}</span>{tab.label}
        {state.dirtyTabs.includes(tab.id) && <span className={styles.dirtyDot} aria-label="Modifications non enregistrées" />}
      </button>)}
    </div>

    {/* Les cibles aria-controls existent aussi quand leur onglet est masqué
        ou que les données sont en chargement. Aucun formulaire n'est dupliqué. */}
    {SETTINGS_TABS.filter((tab) => tab.id !== active || state.loading || Boolean(state.loadError)).map((tab) =>
      <div key={tab.id} role="tabpanel" id={`panel-${tab.id}`} aria-labelledby={`tab-${tab.id}`} hidden />)}

    {state.loading ? <div className={styles.loading} role="status" aria-live="polite"><div className={styles.skeleton} /><div className={styles.skeleton} />Chargement des paramètres…</div>
      : state.loadError ? <div className={styles.loadError} role="alert"><h2>Paramètres indisponibles</h2><p>{state.loadError}</p><button type="button" className={styles.primaryButton} onClick={state.retry}>Réessayer le chargement</button></div>
      : <div className={styles.content}>
        <div className={styles.editor}>
          <div className={styles.panelHeading}><div><h2>{activeInfo.label}</h2><p>{activeInfo.description}</p></div><span className={styles.smallBadge}>{currentDirty ? "Brouillon modifié" : "À jour dans " + (state.preview ? "l’aperçu" : "l’API")}</span></div>
          <form ref={form} noValidate onSubmit={(e) => { e.preventDefault(); void state.save(active); }}>
            <fieldset disabled={state.saving} className={styles.formFields}>
              <div role="tabpanel" id={`panel-${active}`} aria-labelledby={`tab-${active}`}>
                {active === "general" && <>
                  <Section title="Identité de l’établissement" description="Les informations qui présenteront votre restaurant aux clients.">
                    {text("general", "name", "Nom du restaurant *")}
                    {text("general", "description", "Description", "Présentez votre cuisine et l’expérience proposée.", true)}
                  </Section>
                  <Section title="Coordonnées" description="Des contacts professionnels, accessibles à votre équipe.">
                    <div className={styles.grid}>{text("general", "phone", "Téléphone", undefined, false, "tel")}{text("general", "whatsapp", "WhatsApp", undefined, false, "tel")}{text("general", "email", "Email professionnel", undefined, false, "email")}{text("general", "city", "Ville *")}</div>
                    {text("general", "address", "Adresse *")}
                  </Section>
                  <Section title="Préférences régionales">
                    <div className={styles.grid}>
                      {select("general.timezone", "Fuseau horaire", draft.general.timezone,
                        Array.from(new Set(["Africa/Lubumbashi", "Africa/Kinshasa", "UTC", draft.general.timezone])).map((zone) => [zone, zone]),
                        (timezone) => state.updateSection("general", { ...draft.general, timezone }), "Référence pour les horaires et les réservations.")}
                      {select("general.currency", "Devise de référence", draft.general.currency, [["USD", "USD · Dollar américain"], ["CDF", "CDF · Franc congolais"]],
                        (currency) => state.updateSection("general", { ...draft.general, currency: currency as "USD" | "CDF" }))}
                      {select("general.language", "Langue d’accueil souhaitée", draft.general.language, [["fr", "Français"], ["en", "Anglais"]],
                        (language) => state.updateSection("general", { ...draft.general, language: language as "fr" | "en" }), "Préférence transmise à l’agent ; ne traduit pas ce dashboard.")}
                    </div>
                    <p className={styles.inlineNote}>Changer de devise ne convertit pas les montants historiques. Cette règle doit être appliquée côté serveur avant toute utilisation réelle.</p>
                  </Section>
                </>}

                {active === "hours" && <>
                  <Section title="Semaine habituelle" description={`Horaires dans le fuseau conservé ${state.saved.general.timezone}. Chaque service doit se terminer le même jour.`}>
                    <div className={styles.schedule}>
                      {draft.hours.days.map((day, dayIndex) => <div className={styles.day} key={day.id}>
                        <div className={styles.dayHeading}>
                          <Switch label={day.label} checked={!day.closed} onChange={(open) => changeDay(dayIndex, { closed: !open, slots: open && day.slots.length === 0 ? [{ start: "12:00", end: "15:00" }] : day.slots })} />
                          <span className={styles.hint}>{day.closed ? "Fermé" : "Ouvert"}</span>
                        </div>
                        {!day.closed && <div className={styles.slots}>
                          {day.slots.map((slot, slotIndex) => <div className={styles.slot} key={`${day.id}-${slotIndex}`}>
                            {(["start", "end"] as const).map((key) => {
                              const id = `hours.days.${dayIndex}.slots.${slotIndex}.${key}`;
                              return <Field key={id} id={id} label={`${key === "start" ? "Ouverture" : "Fermeture"} ${slotIndex + 1}`} error={errors[id]}>
                                <input {...attributes(id)} type="time" value={slot[key]} onChange={(e) => changeDay(dayIndex, { slots: day.slots.map((s, i) => i === slotIndex ? { ...s, [key]: e.target.value } : s) })} />
                              </Field>;
                            })}
                            <button type="button" className={styles.removeButton} disabled={day.slots.length <= 1} aria-label={`Supprimer le service ${slotIndex + 1} du ${day.label}`}
                              onClick={() => changeDay(dayIndex, { slots: day.slots.filter((_, i) => i !== slotIndex) })}>Retirer</button>
                          </div>)}
                          {errors[`hours.days.${dayIndex}.slots`] && <p className={styles.fieldError}>{errors[`hours.days.${dayIndex}.slots`]}</p>}
                          <button type="button" className={styles.textButton} disabled={day.slots.length >= 8} onClick={() => changeDay(dayIndex, { slots: [...day.slots, { start: "", end: "" }] })}>+ Ajouter un service</button>
                        </div>}
                      </div>)}
                    </div>
                  </Section>
                  <Section title="Fermetures exceptionnelles" description="Une fermeture exceptionnelle concerne toute la journée.">
                    {draft.hours.closures.length === 0 && <p className={styles.empty}>Aucune fermeture exceptionnelle. Votre semaine habituelle s’applique.</p>}
                    {draft.hours.closures.map((closure, index) => <div className={styles.closure} key={index}>
                      <Field id={`hours.closures.${index}.date`} label="Date de fermeture" error={errors[`hours.closures.${index}.date`]}>
                        <input {...attributes(`hours.closures.${index}.date`)} type="date" value={closure.date} onChange={(e) => state.updateSection("hours", { ...draft.hours, closures: draft.hours.closures.map((item, i) => i === index ? { ...item, date: e.target.value } : item) })} />
                      </Field>
                      <Field id={`hours.closures.${index}.reason`} label="Motif interne" error={errors[`hours.closures.${index}.reason`]}>
                        <input {...attributes(`hours.closures.${index}.reason`)} maxLength={300} value={closure.reason} onChange={(e) => state.updateSection("hours", { ...draft.hours, closures: draft.hours.closures.map((item, i) => i === index ? { ...item, reason: e.target.value } : item) })} />
                      </Field>
                      <button type="button" className={styles.removeButton} aria-label={`Supprimer la fermeture ${index + 1}`} onClick={() => state.updateSection("hours", { ...draft.hours, closures: draft.hours.closures.filter((_, i) => i !== index) })}>Retirer</button>
                    </div>)}
                    <button type="button" className={styles.secondaryButton} disabled={draft.hours.closures.length >= 366} onClick={() => state.updateSection("hours", { ...draft.hours, closures: [...draft.hours.closures, { date: "", reason: "" }] })}>+ Ajouter une fermeture</button>
                  </Section>
                </>}

                {active === "reservations" && <>
                  <Section title="Accueil et capacité" description="Des limites pour les nouvelles demandes, pas une modification des réservations existantes.">
                    <div className={styles.grid}>
                      {number("reservations", "minGuests", "Personnes minimum", undefined, 1, 1000)}
                      {number("reservations", "maxGuests", "Personnes maximum", undefined, 1, 1000)}
                      {number("reservations", "slotMinutes", "Intervalle des créneaux (min)", "Exemple : un départ toutes les 30 minutes.", 5, 240)}
                      {number("reservations", "durationMinutes", "Occupation prévue (min)", "Durée pendant laquelle une table est réservée.", 5, 1440)}
                    </div>
                  </Section>
                  <Section title="Délais de réservation">
                    <div className={styles.grid}>
                      {number("reservations", "advanceNoticeMinutes", "Préavis minimum (min)", "0 autorise les demandes immédiates.", 0, 43200)}
                      {number("reservations", "maxAdvanceDays", "Réserver jusqu’à (jours)", undefined, 1, 365)}
                      {number("reservations", "graceMinutes", "Tolérance de retard (min)", undefined, 0, 120)}
                      {number("reservations", "cancellationHours", "Annulation avant l’arrivée (h)", "Délai minimum souhaité ; aucune annulation automatique ici.", 0, 720)}
                    </div>
                  </Section>
                  <Section title="Confirmation et acompte">
                    {select("reservations.confirmationMode", "Mode de confirmation", draft.reservations.confirmationMode,
                      [["manual", "Validation par le personnel"], ["automatic", "Confirmation automatique"], ["deposit", "Après paiement d’un acompte"]],
                      (mode) => state.updateSection("reservations", { ...draft.reservations, confirmationMode: mode as RestaurantSettings["reservations"]["confirmationMode"], depositEnabled: mode === "deposit" ? true : draft.reservations.depositEnabled }))}
                    <Switch label="Demander un acompte" description="Configuration uniquement. Aucun paiement n’est déclenché par ce formulaire." checked={draft.reservations.depositEnabled} onChange={(depositEnabled) => state.updateSection("reservations", { ...draft.reservations, depositEnabled })} />
                    {errors["reservations.depositEnabled"] && <p className={styles.fieldError}>{errors["reservations.depositEnabled"]}</p>}
                    {draft.reservations.depositEnabled && <div className={styles.grid}>
                      {select("reservations.depositType", "Calcul de l’acompte", draft.reservations.depositType, [["fixed", "Montant fixe"], ["percent", "Pourcentage"]],
                        (depositType) => state.updateSection("reservations", { ...draft.reservations, depositType: depositType as "fixed" | "percent" }))}
                      {number("reservations", "depositValue", draft.reservations.depositType === "percent" ? "Acompte (%)" : `Acompte (${state.saved.general.currency})`, draft.reservations.depositType === "percent" ? "La base de calcul sera définie avec le backend." : "Devise actuellement conservée dans Général, pas celle d’un éventuel brouillon.", 0.01, draft.reservations.depositType === "percent" ? 100 : 1000000000, 0.01)}
                    </div>}
                  </Section>
                </>}

                {active === "agent" && <>
                  <Section title="Disponibilité de l’assistant">
                    <Switch label="Activer l’assistant IA" description={state.preview ? "Simulation uniquement : l’agent du restaurant reste inchangé." : "Le backend doit partager cet état avec l’interrupteur de la page Salle."} checked={draft.agent.enabled} onChange={(enabled) => state.updateSection("agent", { ...draft.agent, enabled })} />
                    <p className={styles.inlineNote}>{draft.agent.enabled ? "Configuration : l’assistant est prévu pour accueillir les demandes." : "Configuration : les demandes doivent être prises en charge par le personnel."}</p>
                  </Section>
                  <Section title="Accueil et personnalité">
                    {text("agent", "name", draft.agent.enabled ? "Nom de l’assistant *" : "Nom de l’assistant")}
                    {text("agent", "welcomeMessage", draft.agent.enabled ? "Message de bienvenue *" : "Message de bienvenue", "Aperçu du texte uniquement, sans appel à un modèle IA.", true)}
                    {text("agent", "instructions", draft.agent.enabled ? "Consignes complémentaires *" : "Consignes complémentaires", "Cuisine, accès, accueil. Ne saisissez aucun mot de passe ni clé secrète.", true)}
                  </Section>
                  <Section title="Relais vers votre équipe">
                    <div className={styles.grid}>{number("agent", "humanThreshold", "Transférer à partir de (personnes)", "Taille de groupe nécessitant une intervention humaine.", 1, 100)}{text("agent", "handoffPhone", "Téléphone du personnel", undefined, false, "tel")}</div>
                    <p className={styles.inlineNote}>Les disponibilités, prix et paiements restent sous le contrôle du backend. Ces consignes ne doivent jamais permettre à l’IA de contourner les règles du restaurant.</p>
                  </Section>
                </>}
              </div>
            </fieldset>
            {Object.keys(errors).length > 0 && <div role="alert" className={styles.errorBox}>Vérifiez les champs indiqués. Aucun changement n’a été enregistré.<ul>{Object.entries(errors).map(([key, message]) => <li key={key}>{message}</li>)}</ul></div>}
            {state.feedback && <div role={state.feedback.kind === "error" ? "alert" : "status"} className={state.feedback.kind === "error" ? styles.errorBox : styles.successBox}>{state.feedback.text}</div>}
            <footer className={styles.actions}>
              <p>{state.saving ? "Enregistrement en cours…" : currentDirty ? "Modifications à conserver dans cet onglet" : "Aucune modification dans cet onglet"}</p>
              <div><button type="button" className={styles.secondaryButton} disabled={!currentDirty || state.saving} onClick={() => setPending({ type: "discard", tab: active })}>Annuler</button>
                <button type="submit" className={styles.primaryButton} disabled={!currentDirty || state.saving}>{state.saving ? "Enregistrement…" : state.preview ? "Conserver le brouillon" : "Enregistrer les modifications"}</button></div>
            </footer>
          </form>
        </div>

        <aside className={styles.context}>
          <p className={styles.eyebrow}>VOTRE CONFIGURATION</p>
          <h2>{draft.general.name || "Votre restaurant"}</h2>
          <p>{draft.general.city || "Ville à renseigner"}</p>
          <dl><div><dt>Devise</dt><dd>{draft.general.currency}</dd></div><div><dt>Fuseau</dt><dd>{draft.general.timezone}</dd></div><div><dt>Jours ouverts</dt><dd>{draft.hours.days.filter((day) => !day.closed).length} / 7</dd></div><div><dt>Assistant prévu</dt><dd>{draft.agent.enabled ? "Activé" : "Désactivé"}</dd></div></dl>
          <p className={styles.hint}>Résumé de vos saisies, y compris les brouillons non enregistrés.</p>
          {active === "agent" ? <div className={styles.tip}><h3>Aperçu de l’accueil</h3><p className={styles.message}>{draft.agent.welcomeMessage || "Votre message de bienvenue apparaîtra ici."}</p><p className={styles.hint}>Exemple de texte, pas une conversation réelle.</p></div>
            : <div className={styles.tip}><h3>Un onglet à la fois</h3><p>Vos saisies restent disponibles quand vous changez d’onglet. Enregistrez chaque rubrique séparément.</p><p>Les points bleus repèrent les modifications à conserver.</p></div>}
        </aside>
      </div>}

    {/* <dialog> fournit confinement du focus et fermeture Échap sans ajouter
        une bibliothèque. Annuler ne supprime que le brouillon de l'onglet. */}
    <dialog ref={dialog} className={styles.dialog} onCancel={() => setPending(null)} onClose={() => setPending(null)}>
      <h2>{pending?.type === "leave" ? "Quitter les paramètres ?" : "Annuler les modifications ?"}</h2>
      <p>{pending?.type === "leave" ? "Les changements non enregistrés seront perdus. Dans l’aperçu, les brouillons conservés seront également effacés." : "Le dernier état conservé de cet onglet sera restauré. Les autres onglets resteront inchangés."}</p>
      <div className={styles.dialogActions}>
        <button type="button" autoFocus className={styles.secondaryButton} onClick={() => setPending(null)}>Continuer la saisie</button>
        <button type="button" className={styles.primaryButton} onClick={() => {
          if (pending?.type === "discard") state.discard(pending.tab);
          if (pending?.type === "leave") {
            state.confirmLeave();
            window.location.assign(pending.url);
          }
          setPending(null);
        }}>{pending?.type === "leave" ? "Quitter sans enregistrer" : "Annuler cet onglet"}</button>
      </div>
    </dialog>
  </main>;
}
