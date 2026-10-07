"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { clearAdminToken } from "@/lib/admin-auth";
import {
  AdminAuthError, createRestaurant, deleteRestaurant, fetchAdminRestaurants, imageFileToDataUrl,
  reorderRestaurants, updateRestaurant, validateRestaurant, RESTAURANT_LIMITS,
  type AdminRestaurant, type RestaurantInput,
} from "@/lib/restaurants";

// Formulaire vide, reutilise a l'ouverture et apres chaque enregistrement.
const EMPTY_FORM: RestaurantInput = { name: "", city: "", cuisine: "", description: "", image_url: "" };

type Message = { kind: "success" | "error"; text: string } | null;

// ============================================================================
// RestaurantAdmin : gestion des restaurants par l'ADMINISTRATEUR
// ============================================================================
// Fonctionnalites :
//   - ajouter un restaurant ;
//   - modifier un restaurant existant (le formulaire passe en mode edition) ;
//   - masquer / afficher un restaurant sur l'accueil sans le supprimer ;
//   - changer l'ordre du carrousel (boutons Monter / Descendre) ;
//   - retirer definitivement un restaurant (avec confirmation).
export default function RestaurantAdmin() {
  const router = useRouter();
  const [restaurants, setRestaurants] = useState<AdminRestaurant[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [form, setForm] = useState<RestaurantInput>(EMPTY_FORM);
  // null = mode AJOUT ; un id = mode EDITION de ce restaurant.
  const [editingId, setEditingId] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<Message>(null);
  const [preparingImage, setPreparingImage] = useState(false);
  const [confirmId, setConfirmId] = useState<string | null>(null);
  // Id du restaurant sur lequel une action rapide est en cours (masquer,
  // deplacer, retirer) : ses boutons sont desactives pendant ce temps.
  const [busyId, setBusyId] = useState<string | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  const formRef = useRef<HTMLFormElement>(null);

  // Gestion commune des erreurs : si la session admin a expire, on se
  // deconnecte et on retourne a la page de connexion.
  const handleError = useCallback((error: unknown, fallback: string) => {
    if (error instanceof AdminAuthError) {
      clearAdminToken();
      router.replace("/admin/login");
      return;
    }
    setMessage({ kind: "error", text: error instanceof Error ? error.message : fallback });
  }, [router]);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      setRestaurants(await fetchAdminRestaurants());
    } catch (error) {
      if (error instanceof AdminAuthError) handleError(error, "");
      else setLoadError(error instanceof Error ? error.message : "Chargement impossible.");
    } finally {
      setLoading(false);
    }
  }, [handleError]);

  useEffect(() => { void load(); }, [load]);

  // Remplace UN restaurant de la liste par sa version a jour (renvoyee par l'API).
  const replace = (updated: AdminRestaurant) =>
    setRestaurants((current) => current.map((r) => (r.id === updated.id ? updated : r)));

  function update<K extends keyof RestaurantInput>(key: K, value: RestaurantInput[K]) {
    setForm((current) => ({ ...current, [key]: value }));
    setErrors((current) => ({ ...current, [key]: "" }));
    setMessage(null);
  }

  function resetForm() {
    setForm(EMPTY_FORM);
    setEditingId(null);
    setErrors({});
    if (fileInput.current) fileInput.current.value = "";
  }

  // Passe le formulaire en mode edition, pre-rempli avec le restaurant choisi.
  function startEdit(restaurant: AdminRestaurant) {
    setEditingId(restaurant.id);
    setForm({
      name: restaurant.name, city: restaurant.city, cuisine: restaurant.cuisine,
      description: restaurant.description, image_url: restaurant.image_url,
    });
    setErrors({});
    setMessage(null);
    if (fileInput.current) fileInput.current.value = "";
    // Sur mobile, le formulaire est au-dessus de la liste : on y remonte.
    formRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  async function onFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setPreparingImage(true);
    try {
      update("image_url", await imageFileToDataUrl(file));
    } catch (error) {
      setErrors((current) => ({ ...current, image_url: error instanceof Error ? error.message : "Image invalide." }));
      event.target.value = "";
    } finally {
      setPreparingImage(false);
    }
  }

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (saving) return;
    const validation = validateRestaurant(form);
    setErrors(validation);
    if (Object.keys(validation).length > 0) return;

    setSaving(true);
    setMessage(null);
    try {
      if (editingId) {
        const updated = await updateRestaurant(editingId, form);
        replace(updated);
        setMessage({ kind: "success", text: `${updated.name} a ete mis a jour.` });
      } else {
        const created = await createRestaurant(form);
        setRestaurants((current) => [...current, created]);
        setMessage({ kind: "success", text: `${created.name} est maintenant visible sur la page d'accueil.` });
      }
      resetForm();
    } catch (error) {
      // La saisie est conservee pour pouvoir reessayer.
      handleError(error, "Enregistrement impossible.");
    } finally {
      setSaving(false);
    }
  }

  async function toggleVisible(restaurant: AdminRestaurant) {
    setBusyId(restaurant.id);
    setMessage(null);
    try {
      const updated = await updateRestaurant(restaurant.id, { visible: !restaurant.visible });
      replace(updated);
      setMessage({ kind: "success", text: updated.visible ? `${updated.name} est de nouveau affiche sur l'accueil.` : `${updated.name} est masque de l'accueil.` });
    } catch (error) {
      handleError(error, "Modification impossible.");
    } finally {
      setBusyId(null);
    }
  }

  // Deplace un restaurant d'une place vers le haut (-1) ou le bas (+1).
  async function move(index: number, direction: -1 | 1) {
    const target = index + direction;
    if (target < 0 || target >= restaurants.length) return;
    const previous = restaurants;
    // Copie de la liste, puis echange des deux elements.
    const next = [...restaurants];
    [next[index], next[target]] = [next[target], next[index]];
    // Mise a jour "optimiste" : l'ecran change tout de suite, et on revient
    // a l'ancien ordre si le serveur refuse.
    setRestaurants(next);
    setBusyId(restaurants[index].id);
    setMessage(null);
    try {
      setRestaurants(await reorderRestaurants(next.map((r) => r.id)));
    } catch (error) {
      setRestaurants(previous);
      handleError(error, "Changement d'ordre impossible.");
    } finally {
      setBusyId(null);
    }
  }

  async function onDelete(restaurant: AdminRestaurant) {
    setBusyId(restaurant.id);
    setMessage(null);
    try {
      await deleteRestaurant(restaurant.id);
      setRestaurants((current) => current.filter((r) => r.id !== restaurant.id));
      if (editingId === restaurant.id) resetForm();
      setMessage({ kind: "success", text: `${restaurant.name} a ete supprime definitivement.` });
    } catch (error) {
      handleError(error, "Suppression impossible.");
    } finally {
      setBusyId(null);
      setConfirmId(null);
    }
  }

  const inputClass = (field: string) =>
    `mt-1 block w-full rounded-lg border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary-light ${
      errors[field] ? "border-danger bg-red-50" : "border-gray-300"
    }`;
  const visibleCount = restaurants.filter((r) => r.visible).length;
  const smallButton = "rounded-full border px-3 py-1.5 text-xs font-medium transition disabled:opacity-40";

  return (
    <div>
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Restaurants de la plateforme</h1>
        <p className="mt-1 text-sm text-gray-600">
          Les restaurants visibles defilent dans le carrousel de la page d&apos;accueil, dans l&apos;ordre ci-dessous.
        </p>
      </header>

      {message && (
        <div role={message.kind === "error" ? "alert" : "status"}
          className={`mb-6 rounded-lg px-4 py-3 text-sm ${message.kind === "error" ? "bg-red-50 text-danger" : "bg-green-50 text-success"}`}>
          {message.text}
        </div>
      )}

      <div className="grid items-start gap-6 lg:grid-cols-[380px_minmax(0,1fr)]">
        {/* ===================== FORMULAIRE (ajout ou edition) ===================== */}
        <form ref={formRef} onSubmit={onSubmit} noValidate
          className={`scroll-mt-6 space-y-4 rounded-2xl border bg-white p-5 ${editingId ? "border-primary ring-2 ring-primary/20" : "border-gray-200"}`}>
          <h2 className="font-semibold text-gray-900">{editingId ? "Modifier le restaurant" : "Ajouter un restaurant"}</h2>

          <Field id="name" label="Nom *" error={errors.name}>
            <input id="name" value={form.name} maxLength={RESTAURANT_LIMITS.name} disabled={saving}
              aria-invalid={Boolean(errors.name)} onChange={(e) => update("name", e.target.value)} className={inputClass("name")} />
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field id="city" label="Ville *" error={errors.city}>
              <input id="city" value={form.city} maxLength={RESTAURANT_LIMITS.city} disabled={saving}
                aria-invalid={Boolean(errors.city)} onChange={(e) => update("city", e.target.value)} className={inputClass("city")} />
            </Field>
            <Field id="cuisine" label="Cuisine" error={errors.cuisine}>
              <input id="cuisine" value={form.cuisine} maxLength={RESTAURANT_LIMITS.cuisine} disabled={saving}
                placeholder="Congolaise" onChange={(e) => update("cuisine", e.target.value)} className={inputClass("cuisine")} />
            </Field>
          </div>
          <Field id="description" label="Description courte" error={errors.description}>
            <textarea id="description" rows={3} value={form.description} maxLength={RESTAURANT_LIMITS.description} disabled={saving}
              onChange={(e) => update("description", e.target.value)} className={inputClass("description")} />
          </Field>

          {/* Deux facons d'ajouter l'image : un fichier OU une adresse web. */}
          <Field id="image-file" label={editingId ? "Nouvelle photo (facultatif)" : "Photo *"} error={errors.image_url}>
            <input id="image-file" ref={fileInput} type="file" accept="image/*" disabled={saving} onChange={onFileChange}
              className="mt-1 block w-full text-sm file:mr-3 file:rounded-full file:border-0 file:bg-primary/10 file:px-4 file:py-2 file:font-semibold file:text-primary" />
          </Field>
          <Field id="image-url" label="Ou adresse de l'image">
            <input id="image-url" type="url" placeholder="https://..." disabled={saving}
              value={form.image_url.startsWith("data:") ? "" : form.image_url}
              onChange={(e) => {
                if (fileInput.current) fileInput.current.value = "";
                update("image_url", e.target.value.trim());
              }}
              className={inputClass("image_url")} />
          </Field>

          {preparingImage && <p className="text-sm text-gray-500">Preparation de l&apos;image...</p>}
          {form.image_url && !preparingImage && (
            // eslint-disable-next-line @next/next/no-img-element -- apercu local (data:) ou URL externe
            <img src={form.image_url} alt="Apercu de la photo" className="aspect-[4/3] w-full rounded-lg bg-gray-100 object-cover" />
          )}

          <div className="flex gap-2">
            <button type="submit" disabled={saving || preparingImage}
              className="flex-1 rounded-full bg-primary px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:opacity-50">
              {saving ? "Enregistrement..." : editingId ? "Enregistrer les modifications" : "Ajouter a la page d'accueil"}
            </button>
            {editingId && (
              <button type="button" onClick={() => { resetForm(); setMessage(null); }} disabled={saving}
                className="rounded-full border border-gray-300 px-4 py-2.5 text-sm">
                Annuler
              </button>
            )}
          </div>
        </form>

        {/* ===================== LISTE ===================== */}
        <section aria-labelledby="restaurants-list">
          <h2 id="restaurants-list" className="mb-3 font-semibold text-gray-900">
            Ordre du carrousel {!loading && !loadError && `(${visibleCount} visible${visibleCount > 1 ? "s" : ""} sur ${restaurants.length})`}
          </h2>

          {loading && <p className="text-sm text-gray-500" role="status">Chargement...</p>}
          {loadError && (
            <div role="alert" className="rounded-lg bg-red-50 p-4 text-sm text-danger">
              {loadError}
              <button type="button" onClick={() => void load()} className="ml-2 font-semibold underline">Reessayer</button>
            </div>
          )}
          {!loading && !loadError && restaurants.length === 0 && (
            <p className="rounded-2xl border border-dashed border-gray-300 p-6 text-center text-sm text-gray-500">
              Aucun restaurant. Ajoutez le premier avec le formulaire.
            </p>
          )}

          {/* <ol> : liste ORDONNEE, car l'ordre a un sens (celui du carrousel). */}
          <ol className="space-y-3">
            {restaurants.map((restaurant, index) => {
              const busy = busyId === restaurant.id;
              return (
                <li key={restaurant.id}
                  className={`flex gap-4 rounded-2xl border bg-white p-3 ${editingId === restaurant.id ? "border-primary" : "border-gray-200"} ${restaurant.visible ? "" : "bg-gray-50"}`}>
                  {/* eslint-disable-next-line @next/next/no-img-element -- images de sources variees */}
                  <img src={restaurant.image_url} alt=""
                    className={`h-24 w-28 shrink-0 rounded-xl bg-gray-100 object-cover sm:w-36 ${restaurant.visible ? "" : "opacity-40 grayscale"}`} />
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-xs font-semibold text-gray-400">#{index + 1}</span>
                      <h3 className="truncate font-semibold text-gray-900">{restaurant.name}</h3>
                      {!restaurant.visible && (
                        <span className="rounded-full bg-gray-200 px-2 py-0.5 text-xs font-medium text-gray-700">Masque</span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600">{[restaurant.cuisine, restaurant.city].filter(Boolean).join(" · ")}</p>

                    <div className="mt-2 flex flex-wrap gap-2">
                      {confirmId === restaurant.id ? (
                        // Suppression en deux temps, pour eviter un clic accidentel.
                        <>
                          <button type="button" onClick={() => void onDelete(restaurant)} disabled={busy}
                            className={`${smallButton} border-danger bg-danger text-white`}>
                            {busy ? "Suppression..." : "Confirmer la suppression"}
                          </button>
                          <button type="button" onClick={() => setConfirmId(null)} disabled={busy}
                            className={`${smallButton} border-gray-300`}>Annuler</button>
                        </>
                      ) : (
                        <>
                          <button type="button" onClick={() => void move(index, -1)} disabled={busy || index === 0}
                            aria-label={`Monter ${restaurant.name}`} className={`${smallButton} border-gray-300 hover:bg-gray-50`}>↑</button>
                          <button type="button" onClick={() => void move(index, 1)} disabled={busy || index === restaurants.length - 1}
                            aria-label={`Descendre ${restaurant.name}`} className={`${smallButton} border-gray-300 hover:bg-gray-50`}>↓</button>
                          <button type="button" onClick={() => startEdit(restaurant)} disabled={busy || saving}
                            className={`${smallButton} border-gray-300 hover:bg-gray-50`}>Modifier</button>
                          <button type="button" onClick={() => void toggleVisible(restaurant)} disabled={busy}
                            className={`${smallButton} border-gray-300 hover:bg-gray-50`}>
                            {restaurant.visible ? "Masquer" : "Afficher"}
                          </button>
                          <button type="button" onClick={() => setConfirmId(restaurant.id)} disabled={busy}
                            aria-label={`Supprimer ${restaurant.name}`}
                            className={`${smallButton} border-danger/40 text-danger hover:bg-red-50`}>Supprimer</button>
                        </>
                      )}
                    </div>
                  </div>
                </li>
              );
            })}
          </ol>
        </section>
      </div>
    </div>
  );
}

function Field({ id, label, error, children }: {
  id: string; label: string; error?: string; children: React.ReactNode;
}) {
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium text-gray-700">{label}</label>
      {children}
      {error && <p className="mt-1 text-xs text-danger">{error}</p>}
    </div>
  );
}
