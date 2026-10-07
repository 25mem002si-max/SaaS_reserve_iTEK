import { getAdminToken } from "./admin-auth";

// ============================================================================
// Restaurants affiches sur la page d'accueil publique
// ============================================================================
// Ce fichier regroupe TOUT ce qui concerne la liste des restaurants :
//   1. les types TypeScript ;
//   2. les regles de validation du formulaire ;
//   3. la conversion d'une photo choisie sur l'ordinateur en image legere ;
//   4. les appels a l'API :
//      - PUBLIC  : GET /restaurants (visiteurs de la page d'accueil) ;
//      - ADMIN   : /admin/restaurants... (reserve a l'administrateur).

// Ce que voit un visiteur. On ne reutilise pas le type `Restaurant` de
// types.ts, qui decrit le restaurant COMPLET en base (devise, cles Mobile
// Money...) : ici, seulement les informations PUBLIQUES.
export interface PublicRestaurant {
  id: string;
  name: string;
  city: string;
  cuisine: string;
  description: string;
  // URL http(s) d'une image, OU image encodee en texte ("data:image/...")
  // quand l'administrateur a choisi une photo depuis son ordinateur.
  image_url: string;
  created_at: string;
}

// Ce que voit l'administrateur : en plus, la visibilite et l'ordre.
export interface AdminRestaurant extends PublicRestaurant {
  visible: boolean; // false = masque de l'accueil, mais pas supprime
  position: number; // ordre dans le carrousel (0 = premier)
}

// Donnees saisies dans le formulaire : l'id, la date et la position sont
// decides par le serveur, jamais par le navigateur.
export type RestaurantInput = Pick<PublicRestaurant, "name" | "city" | "cuisine" | "description" | "image_url">;

// Erreur speciale : la session admin est absente ou expiree. Les composants
// la reconnaissent pour renvoyer l'administrateur vers la page de connexion.
export class AdminAuthError extends Error {}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// Limites partagees entre le formulaire (maxLength) et la validation.
export const RESTAURANT_LIMITS = { name: 80, city: 60, cuisine: 60, description: 300 } as const;

// ----------------------------------------------------------------------------
// Validation
// ----------------------------------------------------------------------------
// Renvoie { nomDuChamp: "message" }. Un objet vide = tout est correct.
// Le serveur refait ces controles : la validation du navigateur sert au
// confort de l'utilisateur, pas a la securite.
export function validateRestaurant(data: RestaurantInput): Record<string, string> {
  const errors: Record<string, string> = {};
  const check = (field: keyof typeof RESTAURANT_LIMITS, required: boolean, label: string) => {
    const value = data[field].trim();
    if (required && !value) errors[field] = `${label} est obligatoire.`;
    else if (value.length > RESTAURANT_LIMITS[field]) errors[field] = `${RESTAURANT_LIMITS[field]} caracteres maximum.`;
  };
  check("name", true, "Le nom du restaurant");
  check("city", true, "La ville");
  check("cuisine", false, "La cuisine");
  check("description", false, "La description");

  if (!data.image_url) errors.image_url = "Ajoutez une photo ou l'adresse d'une image.";
  else if (!isValidImageUrl(data.image_url)) errors.image_url = "L'adresse doit commencer par https:// ou http://.";
  return errors;
}

function isValidImageUrl(value: string): boolean {
  if (value.startsWith("data:image/")) return true;
  try {
    const url = new URL(value);
    return url.protocol === "https:" || url.protocol === "http:";
  } catch {
    return false;
  }
}

// Verifient qu'un objet recu de l'API a bien la forme attendue. Sans ce
// controle, une reponse incorrecte du serveur ferait planter l'affichage.
function isPublicRestaurant(value: unknown): value is PublicRestaurant {
  if (!value || typeof value !== "object") return false;
  const r = value as Record<string, unknown>;
  return ["id", "name", "city", "cuisine", "description", "image_url", "created_at"]
    .every((key) => typeof r[key] === "string");
}

function isAdminRestaurant(value: unknown): value is AdminRestaurant {
  if (!isPublicRestaurant(value)) return false;
  const r = value as unknown as Record<string, unknown>;
  return typeof r.visible === "boolean" && typeof r.position === "number";
}

// ----------------------------------------------------------------------------
// Photo choisie sur l'ordinateur -> image legere
// ----------------------------------------------------------------------------
// Une photo de telephone peut peser plusieurs Mo. On la redimensionne (cote le
// plus long = 1200 px) et on la recompresse en JPEG avant l'envoi. En
// production, on enverrait plutot le fichier a un service de stockage
// (S3, Cloudinary...) et on ne garderait que son URL.
export async function imageFileToDataUrl(file: File, maxSize = 1200, quality = 0.8): Promise<string> {
  if (!file.type.startsWith("image/")) throw new Error("Le fichier choisi n'est pas une image.");
  if (file.size > 15 * 1024 * 1024) throw new Error("Image trop lourde (15 Mo maximum).");

  const bitmap = await createImageBitmap(file).catch(() => {
    throw new Error("Impossible de lire cette image.");
  });
  const scale = Math.min(1, maxSize / Math.max(bitmap.width, bitmap.height));
  const canvas = document.createElement("canvas");
  canvas.width = Math.round(bitmap.width * scale);
  canvas.height = Math.round(bitmap.height * scale);
  const context = canvas.getContext("2d");
  if (!context) throw new Error("Votre navigateur ne peut pas preparer l'image.");
  context.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  bitmap.close();
  return canvas.toDataURL("image/jpeg", quality);
}

// ----------------------------------------------------------------------------
// Appels API
// ----------------------------------------------------------------------------
async function request(path: string, options: RequestInit = {}, admin = false): Promise<Response> {
  const token = admin ? getAdminToken() : null;
  if (admin && !token) throw new AdminAuthError("Connectez-vous en tant qu'administrateur.");

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...options,
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
      },
    });
  } catch {
    // fetch echoue (TypeError) quand le serveur est eteint ou injoignable.
    throw new Error("Serveur injoignable. Verifiez que l'API (ou mock-server.js) est lancee.");
  }
  if (response.status === 401) throw new AdminAuthError("Session administrateur expiree. Reconnectez-vous.");
  if (response.status === 403) throw new AdminAuthError("Ce compte n'a pas les droits administrateur.");
  if (response.status === 404) throw new Error("Restaurant introuvable ou route absente de l'API.");
  if (response.status === 413) throw new Error("Image trop lourde pour le serveur.");
  if (response.status === 422) throw new Error("Le serveur refuse ces donnees. Verifiez les champs.");
  if (!response.ok) throw new Error(`Erreur du serveur (${response.status}).`);
  return response;
}

async function readAdminRestaurant(response: Response): Promise<AdminRestaurant> {
  const body: unknown = await response.json();
  if (!isAdminRestaurant(body)) throw new Error("Reponse inattendue du serveur.");
  return body;
}

// trim() retire les espaces en trop au debut et a la fin des textes.
const clean = (data: RestaurantInput): RestaurantInput => ({
  name: data.name.trim(), city: data.city.trim(), cuisine: data.cuisine.trim(),
  description: data.description.trim(), image_url: data.image_url,
});

// ----- PUBLIC : page d'accueil ------------------------------------------------
// Le serveur ne renvoie que les restaurants VISIBLES, deja tries dans l'ordre
// choisi par l'administrateur.
export async function fetchRestaurants(): Promise<PublicRestaurant[]> {
  const body: unknown = await (await request("/restaurants")).json();
  if (!Array.isArray(body)) throw new Error("Reponse inattendue du serveur.");
  return body.filter(isPublicRestaurant);
}

// ----- ADMIN : espace /admin --------------------------------------------------
// Tous les restaurants, y compris masques, tries par position.
export async function fetchAdminRestaurants(): Promise<AdminRestaurant[]> {
  const body: unknown = await (await request("/admin/restaurants", {}, true)).json();
  if (!Array.isArray(body)) throw new Error("Reponse inattendue du serveur.");
  return body.filter(isAdminRestaurant).sort((a, b) => a.position - b.position);
}

export async function createRestaurant(data: RestaurantInput): Promise<AdminRestaurant> {
  return readAdminRestaurant(await request("/admin/restaurants", {
    method: "POST", body: JSON.stringify(clean(data)),
  }, true));
}

// PATCH : on n'envoie que ce qui change (les champs du formulaire, OU juste
// la visibilite quand on clique sur Masquer/Afficher).
export async function updateRestaurant(
  id: string, changes: Partial<RestaurantInput> & { visible?: boolean },
): Promise<AdminRestaurant> {
  return readAdminRestaurant(await request(`/admin/restaurants/${encodeURIComponent(id)}`, {
    method: "PATCH", body: JSON.stringify(changes),
  }, true));
}

export async function deleteRestaurant(id: string): Promise<void> {
  // encodeURIComponent protege l'URL si l'id contient un caractere special.
  await request(`/admin/restaurants/${encodeURIComponent(id)}`, { method: "DELETE" }, true);
}

// Envoie l'ordre complet des ids ; le serveur renvoie la liste a jour.
export async function reorderRestaurants(ids: string[]): Promise<AdminRestaurant[]> {
  const body: unknown = await (await request("/admin/restaurants/order", {
    method: "PUT", body: JSON.stringify({ ids }),
  }, true)).json();
  if (!Array.isArray(body)) throw new Error("Reponse inattendue du serveur.");
  return body.filter(isAdminRestaurant).sort((a, b) => a.position - b.position);
}
