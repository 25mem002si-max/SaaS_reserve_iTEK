// ============================================================================
// Routes "restaurants" + connexion ADMIN du serveur simule (mock-server.js)
// ============================================================================
// Routes ajoutees :
//   PUBLIC
//     GET    /restaurants               -> restaurants VISIBLES, dans l'ordre
//   ADMINISTRATEUR (jeton admin obligatoire : en-tete Authorization: Bearer ...)
//     POST   /auth/admin/login          -> connexion admin, renvoie un jeton
//     GET    /admin/restaurants         -> tous les restaurants (meme masques)
//     POST   /admin/restaurants         -> ajouter
//     PATCH  /admin/restaurants/:id     -> modifier et/ou masquer/afficher
//     DELETE /admin/restaurants/:id     -> supprimer definitivement
//     PUT    /admin/restaurants/order   -> nouvel ordre { ids: [...] }
//
// Les restaurants sont enregistres dans restaurants.json (a cote de ce
// fichier) : ils survivent a un redemarrage. Les jetons admin, eux, sont
// gardes en memoire : apres un redemarrage, l'admin doit se reconnecter.
//
// OUTIL DE DEVELOPPEMENT UNIQUEMENT. Le vrai backend (Dev 2) devra :
// stocker les comptes admin en base avec mot de passe hache (bcrypt/argon2),
// emettre un vrai JWT avec role "admin", verifier ce role sur chaque route
// /admin/..., et limiter les tentatives de connexion.

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const DATA_FILE = path.join(__dirname, "restaurants.json");

// Identifiants admin de developpement. Modifiables sans toucher au code :
//   ADMIN_EMAIL=moi@exemple.com ADMIN_PASSWORD=secret node mock-server.js
const ADMIN_EMAIL = process.env.ADMIN_EMAIL || "admin@saas.local";
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || "admin123";
const adminTokens = new Set();

// Restaurants de depart, utilises tant que restaurants.json n'existe pas.
// picsum.photos fournit des images d'exemple libres de droits.
const DEFAULT_RESTAURANTS = [
  { name: "Le Palais du Katanga", city: "Lubumbashi", cuisine: "Congolaise", description: "Poulet moambe, poisson braise et terrasse animee.", image_url: "https://picsum.photos/seed/katanga/800/600" },
  { name: "Chez Maman Tshala", city: "Kinshasa", cuisine: "Traditionnelle", description: "Une cuisine familiale genereuse, comme a la maison.", image_url: "https://picsum.photos/seed/tshala/800/600" },
  { name: "La Terrasse du Fleuve", city: "Kinshasa", cuisine: "Grillades", description: "Vue sur le fleuve et grillades au feu de bois.", image_url: "https://picsum.photos/seed/fleuve/800/600" },
  { name: "Bistro Copperbelt", city: "Lubumbashi", cuisine: "Francaise", description: "Bistro moderne, plats du jour et desserts maison.", image_url: "https://picsum.photos/seed/copperbelt/800/600" },
].map((r, i) => ({ id: `rest-${i + 1}`, created_at: new Date().toISOString(), ...r }));

// Charge le fichier et complete les anciens restaurants qui n'avaient pas
// encore "visible" et "position" (version precedente de ce module).
function load() {
  let list;
  try {
    list = JSON.parse(fs.readFileSync(DATA_FILE, "utf8"));
  } catch {
    list = DEFAULT_RESTAURANTS;
  }
  return list.map((r, i) => ({ visible: true, ...r, position: typeof r.position === "number" ? r.position : i }));
}

function save(list) {
  fs.writeFileSync(DATA_FILE, JSON.stringify(list, null, 2));
}

const sorted = (list) => [...list].sort((a, b) => a.position - b.position);
// Renumerote 0, 1, 2... pour eviter les trous apres une suppression.
const renumber = (list) => sorted(list).map((r, i) => ({ ...r, position: i }));
// Version publique : on retire les champs internes a l'administration.
const toPublic = ({ visible, position, ...rest }) => rest;

// Verifie un champ texte : chaine, longueur max, et non vide si obligatoire.
function textOk(value, max, required) {
  return typeof value === "string" && value.trim().length <= max && (!required || value.trim().length > 0);
}
const imageOk = (v) => typeof v === "string" && /^(https?:\/\/|data:image\/)/.test(v);

// Middleware : bloque toute requete /admin/... sans jeton admin valide.
function requireAdmin(req, res, next) {
  const header = req.headers.authorization || "";
  const token = header.startsWith("Bearer ") ? header.slice(7) : "";
  if (!token) return res.status(401).json({ error: "Jeton manquant" });
  if (!adminTokens.has(token)) return res.status(403).json({ error: "Acces administrateur refuse" });
  next();
}

module.exports = function registerRestaurantRoutes(app) {
  let restaurants = load();

  // ---------------- PUBLIC ----------------
  app.get("/restaurants", (req, res) => {
    res.json(sorted(restaurants).filter((r) => r.visible).map(toPublic));
  });

  // ---------------- CONNEXION ADMIN ----------------
  app.post("/auth/admin/login", (req, res) => {
    const { email, password } = req.body || {};
    if (email !== ADMIN_EMAIL || password !== ADMIN_PASSWORD) {
      return res.status(401).json({ error: "Identifiants invalides" });
    }
    const token = crypto.randomBytes(24).toString("hex");
    adminTokens.add(token);
    res.json({ access_token: token });
  });

  // Toutes les routes declarees apres cette ligne et commencant par /admin
  // passent d'abord par requireAdmin.
  app.use("/admin", requireAdmin);

  // ---------------- ADMIN ----------------
  app.get("/admin/restaurants", (req, res) => res.json(sorted(restaurants)));

  app.post("/admin/restaurants", (req, res) => {
    const { name, city, cuisine = "", description = "", image_url } = req.body || {};
    const valid = textOk(name, 80, true) && textOk(city, 60, true) &&
      textOk(cuisine, 60, false) && textOk(description, 300, false) && imageOk(image_url);
    if (!valid) return res.status(422).json({ error: "Donnees invalides" });

    const restaurant = {
      id: crypto.randomUUID(),
      name: name.trim(), city: city.trim(), cuisine: cuisine.trim(),
      description: description.trim(), image_url,
      visible: true,
      position: restaurants.length, // ajoute en fin de carrousel
      created_at: new Date().toISOString(),
    };
    restaurants.push(restaurant);
    save(restaurants);
    res.status(201).json(restaurant);
  });

  // Doit etre declaree AVANT "/admin/restaurants/:id", sinon Express
  // prendrait "order" pour un id.
  app.put("/admin/restaurants/order", (req, res) => {
    const ids = req.body && req.body.ids;
    const known = new Set(restaurants.map((r) => r.id));
    // L'ordre doit contenir chaque restaurant exactement une fois.
    if (!Array.isArray(ids) || ids.length !== known.size || new Set(ids).size !== ids.length || !ids.every((id) => known.has(id))) {
      return res.status(422).json({ error: "Ordre invalide" });
    }
    restaurants = restaurants.map((r) => ({ ...r, position: ids.indexOf(r.id) }));
    save(restaurants);
    res.json(sorted(restaurants));
  });

  app.patch("/admin/restaurants/:id", (req, res) => {
    const current = restaurants.find((r) => r.id === req.params.id);
    if (!current) return res.status(404).json({ error: "Introuvable" });
    const body = req.body || {};
    // Chaque champ est facultatif ; s'il est present, il doit etre valide.
    const rules = {
      name: (v) => textOk(v, 80, true), city: (v) => textOk(v, 60, true),
      cuisine: (v) => textOk(v, 60, false), description: (v) => textOk(v, 300, false),
      image_url: imageOk, visible: (v) => typeof v === "boolean",
    };
    const changes = {};
    for (const [key, isValid] of Object.entries(rules)) {
      if (!(key in body)) continue;
      if (!isValid(body[key])) return res.status(422).json({ error: `Champ invalide : ${key}` });
      changes[key] = typeof body[key] === "string" && key !== "image_url" ? body[key].trim() : body[key];
    }
    const updated = { ...current, ...changes };
    restaurants = restaurants.map((r) => (r.id === updated.id ? updated : r));
    save(restaurants);
    res.json(updated);
  });

  app.delete("/admin/restaurants/:id", (req, res) => {
    const before = restaurants.length;
    restaurants = restaurants.filter((r) => r.id !== req.params.id);
    if (restaurants.length === before) return res.status(404).json({ error: "Introuvable" });
    restaurants = renumber(restaurants);
    save(restaurants);
    res.sendStatus(204);
  });
};
