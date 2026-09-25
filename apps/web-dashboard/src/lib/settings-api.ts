import { getToken } from "./auth";
import { isRestaurantSettings, type RestaurantSettings, type SettingsTab } from "./restaurant-settings";

/**
 * Contrat PROPOSÉ au développeur backend, pas un endpoint supposé existant.
 * Le mode API est activé explicitement par NEXT_PUBLIC_SETTINGS_MODE=api.
 * Un échec réseau ne doit jamais être remplacé silencieusement par une
 * sauvegarde de démonstration : cela donnerait une fausse impression de succès.
 */
export const SETTINGS_MODE =
  process.env.NEXT_PUBLIC_SETTINGS_MODE === "api" ? "api" : "preview";

export interface SettingsResponse {
  settings: RestaurantSettings;
  // Version opaque renvoyée par le serveur, utilisée pour éviter d'écraser
  // une modification faite entre-temps depuis un autre ordinateur.
  version: string;
}

async function requestSettings(options: RequestInit = {}): Promise<SettingsResponse> {
  const url = process.env.NEXT_PUBLIC_API_URL;
  if (!url) throw new Error("L’adresse de l’API n’est pas configurée.");
  let token: string | null;
  try {
    // On réutilise le mécanisme d'authentification du projet, sans modifier
    // les autres pages. Le mode aperçu n'appelle jamais cette fonction.
    token = getToken();
  } catch {
    throw new Error("La session est inaccessible dans ce navigateur. Reconnectez-vous.");
  }
  if (!token) throw new Error("Connectez-vous pour accéder aux paramètres du restaurant.");

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch(`${url.replace(/\/$/, "")}/settings/restaurant`, {
      ...options,
      signal: controller.signal,
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
        ...options.headers,
      },
    });
    if (response.status === 401) throw new Error("Votre session a expiré. Reconnectez-vous.");
    if (response.status === 403) throw new Error("Votre rôle ne permet pas de modifier ces paramètres.");
    if (response.status === 404) throw new Error("L’API des paramètres n’est pas encore disponible.");
    if (response.status === 409 || response.status === 412) {
      throw new Error("Une autre personne a modifié ces paramètres. Conservez vos changements avant de recharger la page.");
    }
    if (response.status === 422) throw new Error("Le serveur refuse ces valeurs. Vérifiez les règles saisies.");
    if (!response.ok) throw new Error("L’API ne peut pas traiter la demande pour le moment.");

    // Une assertion TypeScript ne valide pas un JSON reçu : on contrôle
    // réellement sa structure avant d'autoriser l'interface à l'utiliser.
    const body: unknown = await response.json();
    if (!body || typeof body !== "object" || !("settings" in body) ||
        !("version" in body) || typeof body.version !== "string" ||
        !body.version || !isRestaurantSettings(body.settings)) {
      throw new Error("La réponse de l’API ne respecte pas le format attendu.");
    }
    return { settings: body.settings, version: body.version };
  } catch (error) {
    if (controller.signal.aborted) {
      // Un délai dépassé ne prouve pas qu'une écriture n'a pas eu lieu côté
      // serveur. Ne pas annoncer un échec définitif, ni relancer un PATCH.
      throw new Error("Délai dépassé. L’état de l’enregistrement est incertain ; vérifiez-le avant de réessayer.");
    }
    if (error instanceof TypeError) throw new Error("Connexion à l’API impossible. Vérifiez le réseau et sa configuration.");
    if (error instanceof SyntaxError) throw new Error("La réponse de l’API n’est pas un JSON valide.");
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

export function loadRestaurantSettings() {
  return requestSettings();
}

export function saveRestaurantSection<K extends SettingsTab>(
  section: K,
  values: RestaurantSettings[K],
  version: string,
) {
  return requestSettings({
    method: "PATCH",
    // Le backend doit vérifier cette version atomiquement avec l'écriture.
    // Le restaurant et les droits viennent du JWT, jamais d'un ID arbitraire
    // accepté sans contrôle depuis le navigateur.
    headers: { "If-Match": version },
    body: JSON.stringify({ section, values }),
  });
}
