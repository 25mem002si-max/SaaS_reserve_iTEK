"use strict";

/**
 * Exécution autonome : node --test settings-tests/model.test.cjs
 *
 * Le projet possède déjà TypeScript. On le résout depuis son package.json,
 * puis transpile uniquement le modèle dans un fichier CommonJS temporaire.
 * Aucun serveur Next.js, navigateur ou paquet supplémentaire n'est nécessaire.
 * transpileModule vérifie la syntaxe, pas les types : le contrôle strict du
 * modèle peut être effectué séparément avec le compilateur TypeScript.
 */
const assert = require("node:assert/strict");
const { test, after } = require("node:test");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { createRequire } = require("node:module");

// Dans le monorepo, placer ce test dans apps/web-dashboard/settings-tests.
// La seconde option permet aussi de le lancer à côté du squelette livré.
const projectRoot = fs.existsSync(path.resolve(__dirname, "../package.json"))
  ? path.resolve(__dirname, "..")
  : path.resolve(__dirname, "../web-dashboard-scaffold");
const projectRequire = createRequire(path.join(projectRoot, "package.json"));
const ts = projectRequire("typescript");
const modelPath = path.join(projectRoot, "src/lib/restaurant-settings.ts");
const compiled = ts.transpileModule(fs.readFileSync(modelPath, "utf8"), {
  fileName: modelPath,
  reportDiagnostics: true,
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2020,
    strict: true,
    esModuleInterop: true,
  },
});
const syntaxErrors = (compiled.diagnostics || []).filter(
  (diagnostic) => diagnostic.category === ts.DiagnosticCategory.Error,
);
assert.deepEqual(
  syntaxErrors.map((diagnostic) =>
    ts.flattenDiagnosticMessageText(diagnostic.messageText, "\n"),
  ),
  [],
  "Le modèle TypeScript doit être syntaxiquement valide.",
);

// Le fichier généré reste hors du projet ; les deux fichiers de travail sont
// les seules sources nécessaires. Le nettoyage concerne uniquement ce dossier
// temporaire propre à cette exécution, jamais les fichiers du workspace.
const temporaryDirectory = fs.mkdtempSync(path.join(os.tmpdir(), "settings-model-"));
after(() => fs.rmSync(temporaryDirectory, { recursive: true, force: true }));
const temporaryModule = path.join(temporaryDirectory, "restaurant-settings.cjs");
fs.writeFileSync(temporaryModule, compiled.outputText, "utf8");
const {
  SETTINGS_TABS,
  createDemoSettings,
  cloneSettings,
  validateSettings,
  isRestaurantSettings,
} = require(temporaryModule);

/** Chaque cas reçoit un objet neuf, pour éviter une dépendance entre tests. */
function errorsFor(tab, change) {
  const settings = createDemoSettings();
  change(settings);
  return validateSettings(tab, settings);
}

function hasErrors(errors, paths) {
  for (const fieldPath of paths) {
    assert.equal(typeof errors[fieldPath], "string", `Erreur attendue : ${fieldPath}`);
    assert.ok(errors[fieldPath].length > 0, `Message vide : ${fieldPath}`);
  }
}

/** Geler récursivement rend visible une mutation accidentelle du validateur. */
function deepFreeze(value) {
  for (const child of Object.values(value)) {
    if (child !== null && typeof child === "object") deepFreeze(child);
  }
  return Object.freeze(value);
}

test("les exports et les quatre onglets respectent le contrat", () => {
  for (const exported of [
    createDemoSettings, cloneSettings, validateSettings, isRestaurantSettings,
  ]) {
    assert.equal(typeof exported, "function");
  }
  assert.deepEqual(
    SETTINGS_TABS.map(({ id, label }) => ({ id, label })),
    [
      { id: "general", label: "Général" },
      { id: "hours", label: "Horaires" },
      { id: "reservations", label: "Réservations" },
      { id: "agent", label: "Assistant IA" },
    ],
  );
  assert.ok(SETTINGS_TABS.every((tab) => typeof tab.description === "string" && tab.description));
});

test("les paramètres de démonstration sont valides sur chaque onglet", () => {
  const settings = createDemoSettings();
  assert.equal(settings.general.name, "Restaurant Démonstration");
  assert.equal(settings.general.city, "Lubumbashi");
  assert.equal(settings.general.currency, "USD");
  assert.equal(settings.general.timezone, "Africa/Lubumbashi");
  assert.deepEqual(
    settings.hours.days.map((day) => day.id),
    ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
  );
  assert.deepEqual(
    settings.hours.days.map((day) => day.label),
    ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"],
  );
  assert.equal(settings.hours.days[0].closed, true);
  for (const day of settings.hours.days.slice(1)) {
    assert.equal(day.closed, false);
    assert.deepEqual(day.slots, [
      { start: "12:00", end: "15:00" },
      { start: "18:00", end: "22:00" },
    ]);
  }
  assert.equal(isRestaurantSettings(settings), true);
  for (const { id } of SETTINGS_TABS) {
    assert.deepEqual(validateSettings(id, settings), {}, id);
  }
});

test("la fabrique ne partage ni objets imbriqués ni services entre jours", () => {
  const first = createDemoSettings();
  const second = createDemoSettings();
  const original = structuredClone(second);
  first.general.name = "Autre restaurant";
  first.hours.days[1].slots[0].start = "11:00";
  first.hours.closures.push({ date: "2026-12-25", reason: "Fête" });
  first.reservations.maxGuests = 20;
  first.agent.name = "Autre assistant";
  assert.equal(first.hours.days[2].slots[0].start, "12:00");
  assert.deepEqual(second, original);
  assert.deepEqual(createDemoSettings(), original);
});

test("le clonage produit un brouillon profondément indépendant", () => {
  const original = createDemoSettings();
  original.hours.closures.push({ date: "2026-12-25", reason: "Fête" });
  const snapshot = structuredClone(original);
  const draft = cloneSettings(original);
  assert.deepEqual(draft, original);
  draft.general.name = "Brouillon";
  draft.hours.days[1].slots[0].end = "16:00";
  draft.hours.days[0].closed = false;
  draft.hours.closures[0].reason = "Travaux";
  draft.reservations.minGuests = 5;
  draft.agent.instructions = "Consignes modifiées";
  assert.deepEqual(original, snapshot);
});

test("le clonage conserve NaN pour permettre la correction d'un champ vidé", () => {
  const settings = createDemoSettings();
  settings.reservations.minGuests = NaN;
  const draft = cloneSettings(settings);
  assert.ok(Number.isNaN(draft.reservations.minGuests));
  hasErrors(validateSettings("reservations", draft), ["reservations.minGuests"]);
});

test("la garde et la validation ne modifient pas les originaux, même non triés", () => {
  const settings = createDemoSettings();
  settings.hours.days[1].slots.reverse();
  settings.hours.closures.push(
    { date: "2026-12-25", reason: "Fête" },
    { date: "2026-10-01", reason: "Travaux" },
  );
  const snapshot = structuredClone(settings);
  deepFreeze(settings);
  assert.equal(isRestaurantSettings(settings), true);
  for (const { id } of SETTINGS_TABS) assert.deepEqual(validateSettings(id, settings), {});
  assert.deepEqual(settings, snapshot);
});

test("les champs généraux obligatoires refusent les blancs", () => {
  const errors = errorsFor("general", (settings) => {
    settings.general.name = " \t ";
    settings.general.address = "";
    settings.general.city = " ";
    settings.general.timezone = "";
  });
  hasErrors(errors, ["general.name", "general.address", "general.city", "general.timezone"]);
  assert.equal(Object.keys(errors).length, 4);
});

test("les coordonnées et la description restent facultatives", () => {
  assert.deepEqual(errorsFor("general", (settings) => {
    for (const key of ["description", "phone", "whatsapp", "email"]) {
      settings.general[key] = " ";
    }
  }), {});
});

test("les téléphones acceptent plusieurs pays et des formats locaux", () => {
  for (const number of [
    "+243 970 000 000", "+33 1 42 68 53 00", "+1 (212) 555-0123",
    "+44 20 7946 0958", "+91 98765 43210", "0970 000 000", "01.42.68.53.00",
  ]) {
    assert.deepEqual(errorsFor("general", (settings) => {
      settings.general.phone = number;
      settings.general.whatsapp = number;
    }), {}, number);
  }
});

test("les téléphones refusent les lettres, les indicatifs mal placés et les longueurs aberrantes", () => {
  for (const number of ["abc", "12345", "++243970000000", "243+970000000", "1234567890123456", "+33\n142685300"]) {
    hasErrors(errorsFor("general", (settings) => {
      settings.general.phone = number;
      settings.general.whatsapp = number;
    }), ["general.phone", "general.whatsapp"]);
  }
});

test("les e-mails acceptent les alias et refusent les formes manifestement invalides", () => {
  for (const email of ["accueil+reservation@example.com", " contact@restaurant.cd "]) {
    assert.deepEqual(errorsFor("general", (settings) => {
      settings.general.email = email;
    }), {});
  }
  for (const email of [
    "contact", "a@b", "a@@example.com", "a b@example.com", "a@example..com",
    "a@-example.com", ".a@example.com", "a..b@example.com", "a@example.com.",
  ]) {
    hasErrors(errorsFor("general", (settings) => {
      settings.general.email = email;
    }), ["general.email"]);
  }
});

test("les fuseaux sont contrôlés par Intl, pas par une liste nationale", () => {
  for (const timezone of ["UTC", "Africa/Lubumbashi", "Europe/Paris", "America/New_York", "Asia/Kolkata"]) {
    assert.deepEqual(errorsFor("general", (settings) => {
      settings.general.timezone = timezone;
    }), {}, timezone);
  }
  hasErrors(errorsFor("general", (settings) => {
    settings.general.timezone = "Planète/Inconnue";
  }), ["general.timezone"]);
});

test("les textes et les préférences générales ont des limites explicites", () => {
  hasErrors(errorsFor("general", (settings) => {
    settings.general.name = "n".repeat(121);
    settings.general.description = "d".repeat(2001);
    settings.general.address = "a".repeat(301);
    settings.general.city = "v".repeat(121);
    settings.general.currency = "EUR";
    settings.general.language = "de";
  }), [
    "general.name", "general.description", "general.address", "general.city",
    "general.currency", "general.language",
  ]);
});

test("un jour ouvert exige au moins un service", () => {
  hasErrors(errorsFor("hours", (settings) => {
    settings.hours.days[0].closed = false;
  }), ["hours.days.0.slots"]);
});

test("les services d'un jour fermé sont ignorés, sans être effacés", () => {
  const settings = createDemoSettings();
  settings.hours.days[0].slots = [
    { start: "", end: "impossible" },
    { start: "23:00", end: "01:00" },
    { start: "12:00", end: "15:00" },
    { start: "13:00", end: "16:00" },
  ];
  const snapshot = structuredClone(settings);
  assert.deepEqual(validateSettings("hours", settings), {});
  assert.deepEqual(settings, snapshot);
});

test("les heures exigent HH:mm et refusent 24:00", () => {
  for (const time of ["", " ", "9:00", "12:0", "24:00", "12:60", "12:00:00", " 12:00", "12:00\n", "12:00\r", "-1:00"]) {
    hasErrors(errorsFor("hours", (settings) => {
      settings.hours.days[1].slots = [{ start: time, end: time }];
    }), ["hours.days.1.slots.0.start", "hours.days.1.slots.0.end"]);
  }
});

test("les horaires inversés, identiques ou nocturnes sont refusés", () => {
  for (const [start, end] of [["15:00", "12:00"], ["12:00", "12:00"], ["22:00", "02:00"]]) {
    hasErrors(errorsFor("hours", (settings) => {
      settings.hours.days[1].slots = [{ start, end }];
    }), ["hours.days.1.slots.0.end"]);
  }
});

test("les chevauchements sont détectés, même imbriqués, identiques ou non triés", () => {
  for (const slots of [
    [{ start: "12:00", end: "15:00" }, { start: "14:00", end: "18:00" }],
    [{ start: "12:00", end: "20:00" }, { start: "14:00", end: "15:00" }],
    [{ start: "12:00", end: "15:00" }, { start: "12:00", end: "15:00" }],
    [{ start: "14:00", end: "18:00" }, { start: "12:00", end: "15:00" }],
  ]) {
    hasErrors(errorsFor("hours", (settings) => {
      settings.hours.days[1].slots = slots;
    }), ["hours.days.1.slots.0.start", "hours.days.1.slots.1.start"]);
  }
});

test("les services consécutifs et les bornes quotidiennes sont autorisés", () => {
  assert.deepEqual(errorsFor("hours", (settings) => {
    settings.hours.days[1].slots = [
      { start: "15:00", end: "23:59" },
      { start: "00:00", end: "15:00" },
    ];
  }), {});
});

test("les dates exceptionnelles sont strictes et respectent les années bissextiles", () => {
  for (const date of ["", "2026-02-29", "2026-02-30", "2026-04-31", "1900-02-29", "2026-13-01", "2026-00-01", "2026-01-00", "2026-1-01", "0000-01-01", "2026-01-01T00:00:00Z", " 2026-01-01", "2026-01-01\n", "2026-01-01\r"]) {
    hasErrors(errorsFor("hours", (settings) => {
      settings.hours.closures = [{ date, reason: "" }];
    }), ["hours.closures.0.date"]);
  }
  for (const date of ["2024-02-29", "2000-02-29", "2026-12-31", "0099-01-01"]) {
    assert.deepEqual(errorsFor("hours", (settings) => {
      settings.hours.closures = [{ date, reason: "" }];
    }), {}, date);
  }
});

test("les fermetures en doublon signalent chaque ligne et limitent les motifs", () => {
  hasErrors(errorsFor("hours", (settings) => {
    settings.hours.closures = [
      { date: "2026-12-25", reason: "" },
      { date: "2026-12-25", reason: "r".repeat(301) },
      { date: "2026-12-25", reason: "Autre raison" },
    ];
  }), [
    "hours.closures.0.date", "hours.closures.1.date",
    "hours.closures.2.date", "hours.closures.1.reason",
  ]);
});

test("les tableaux horaires ont des plafonds et sept identifiants distincts", () => {
  hasErrors(errorsFor("hours", (settings) => {
    settings.hours.days[1].id = "mon";
    settings.hours.days[1].slots = Array.from({ length: 9 }, (_, index) => ({
      start: `${String(index).padStart(2, "0")}:00`,
      end: `${String(index).padStart(2, "0")}:30`,
    }));
    settings.hours.closures = Array.from({ length: 367 }, () => ({
      date: "2026-01-01", reason: "",
    }));
  }), ["hours.days", "hours.days.1.slots", "hours.closures"]);
});

const integerLimits = {
  minGuests: [1, 1000],
  maxGuests: [1, 1000],
  advanceNoticeMinutes: [0, 43200],
  maxAdvanceDays: [1, 365],
  slotMinutes: [5, 240],
  durationMinutes: [5, 1440],
  graceMinutes: [0, 120],
  cancellationHours: [0, 720],
};

test("tous les nombres entiers refusent NaN, l'infini, les fractions et les valeurs vides", () => {
  for (const field of Object.keys(integerLimits)) {
    for (const value of [NaN, Infinity, -Infinity, "", " ", "12", null, undefined, true, 1.5]) {
      hasErrors(errorsFor("reservations", (settings) => {
        settings.reservations[field] = value;
      }), [`reservations.${field}`]);
    }
  }
});

test("les capacités et les délais respectent leurs bornes inclusives", () => {
  for (const [field, [minimum, maximum]] of Object.entries(integerLimits)) {
    for (const value of [minimum - 1, maximum + 1]) {
      hasErrors(errorsFor("reservations", (settings) => {
        settings.reservations[field] = value;
      }), [`reservations.${field}`]);
    }
    for (const value of [minimum, maximum]) {
      assert.deepEqual(errorsFor("reservations", (settings) => {
        settings.reservations.minGuests = 1;
        settings.reservations.maxGuests = 1000;
        settings.reservations[field] = value;
      }), {}, `${field} = ${value}`);
    }
  }
});

test("le minimum du groupe ne peut pas dépasser le maximum", () => {
  hasErrors(errorsFor("reservations", (settings) => {
    settings.reservations.minGuests = 10;
    settings.reservations.maxGuests = 2;
  }), ["reservations.minGuests", "reservations.maxGuests"]);
  assert.deepEqual(errorsFor("reservations", (settings) => {
    settings.reservations.minGuests = 10;
    settings.reservations.maxGuests = 10;
  }), {});
});

test("un acompte actif exige un montant positif, fini et dans les limites de son type", () => {
  for (const depositType of ["fixed", "percent"]) {
    for (const depositValue of [0, -1, NaN, Infinity, -Infinity, "", "10", null]) {
      hasErrors(errorsFor("reservations", (settings) => {
        Object.assign(settings.reservations, {
          depositEnabled: true, depositType, depositValue,
        });
      }), ["reservations.depositValue"]);
    }
  }
  hasErrors(errorsFor("reservations", (settings) => {
    Object.assign(settings.reservations, {
      depositEnabled: true, depositType: "percent", depositValue: 100.01,
    });
  }), ["reservations.depositValue"]);
  hasErrors(errorsFor("reservations", (settings) => {
    Object.assign(settings.reservations, {
      depositEnabled: true, depositType: "fixed", depositValue: 1000000001,
    });
  }), ["reservations.depositValue"]);
});

test("les acomptes acceptent les décimales et un pourcentage de 100", () => {
  for (const [depositType, depositValue] of [
    ["fixed", 0.01], ["fixed", 250000], ["fixed", 1000000000],
    ["percent", 0.1], ["percent", 25.5], ["percent", 100],
  ]) {
    assert.deepEqual(errorsFor("reservations", (settings) => {
      Object.assign(settings.reservations, {
        depositEnabled: true, depositType, depositValue, confirmationMode: "deposit",
      });
    }), {});
  }
});

test("le montant d'un acompte désactivé est inactif, mais le mode acompte exige son activation", () => {
  assert.deepEqual(errorsFor("reservations", (settings) => {
    settings.reservations.depositEnabled = false;
    settings.reservations.depositValue = 0;
  }), {});
  hasErrors(errorsFor("reservations", (settings) => {
    settings.reservations.confirmationMode = "deposit";
    settings.reservations.depositEnabled = false;
  }), ["reservations.depositEnabled"]);
});

test("les modes de confirmation et d'acompte inconnus sont refusés", () => {
  hasErrors(errorsFor("reservations", (settings) => {
    settings.reservations.confirmationMode = "instant";
    settings.reservations.depositType = "ratio";
  }), ["reservations.confirmationMode", "reservations.depositType"]);
  assert.deepEqual(errorsFor("reservations", (settings) => {
    settings.reservations.confirmationMode = "manual";
  }), {});
});

test("l'assistant actif exige son nom, son accueil, ses consignes et un seuil entier positif", () => {
  hasErrors(errorsFor("agent", (settings) => {
    settings.agent.name = " ";
    settings.agent.welcomeMessage = "";
    settings.agent.instructions = "\n";
    settings.agent.humanThreshold = 0;
  }), ["agent.name", "agent.welcomeMessage", "agent.instructions", "agent.humanThreshold"]);
  for (const value of [-1, 101, NaN, Infinity, 1.5, "", "3", null]) {
    hasErrors(errorsFor("agent", (settings) => {
      settings.agent.humanThreshold = value;
    }), ["agent.humanThreshold"]);
  }
  for (const value of [1, 100]) {
    assert.deepEqual(errorsFor("agent", (settings) => {
      settings.agent.humanThreshold = value;
    }), {});
  }
});

test("l'assistant désactivé n'exige pas ses champs inactifs", () => {
  assert.deepEqual(errorsFor("agent", (settings) => {
    Object.assign(settings.agent, {
      enabled: false, name: "", welcomeMessage: "", instructions: "", humanThreshold: 0,
    });
  }), {});
});

test("les textes de l'assistant sont bornés et son téléphone facultatif est vérifié", () => {
  hasErrors(errorsFor("agent", (settings) => {
    settings.agent.name = "n".repeat(101);
    settings.agent.welcomeMessage = "b".repeat(2001);
    settings.agent.instructions = "i".repeat(10001);
    settings.agent.handoffPhone = "appelez-moi";
  }), ["agent.name", "agent.welcomeMessage", "agent.instructions", "agent.handoffPhone"]);
  for (const handoffPhone of ["", "+44 20 7946 0958"]) {
    assert.deepEqual(errorsFor("agent", (settings) => {
      settings.agent.handoffPhone = handoffPhone;
    }), {});
  }
});

test("chaque onglet ne renvoie que ses propres erreurs", () => {
  const settings = createDemoSettings();
  settings.general.name = "";
  settings.hours.days[1].slots = [];
  settings.reservations.minGuests = NaN;
  settings.agent.name = "";
  for (const { id } of SETTINGS_TABS) {
    const errors = validateSettings(id, settings);
    assert.ok(Object.keys(errors).length > 0);
    assert.ok(Object.keys(errors).every((key) => key.startsWith(`${id}.`)));
  }
});

test("la garde refuse les réponses absentes, partielles et les types primitifs", () => {
  for (const value of [null, undefined, false, 12, "{}", [], {}, { general: {} }]) {
    assert.equal(isRestaurantSettings(value), false);
  }
  const complete = createDemoSettings();
  for (const section of ["general", "hours", "reservations", "agent"]) {
    const missingSection = cloneSettings(complete);
    delete missingSection[section];
    assert.equal(isRestaurantSettings(missingSection), false, section);
    for (const field of Object.keys(complete[section])) {
      const missingField = cloneSettings(complete);
      delete missingField[section][field];
      assert.equal(isRestaurantSettings(missingField), false, `${section}.${field}`);
    }
  }
});

test("la garde refuse les mauvais types de tous les champs scalaires", () => {
  const complete = createDemoSettings();
  for (const section of ["general", "reservations", "agent"]) {
    for (const [field, value] of Object.entries(complete[section])) {
      const malformed = cloneSettings(complete);
      malformed[section][field] = typeof value === "string" ? 12 : "incorrect";
      assert.equal(isRestaurantSettings(malformed), false, `${section}.${field}`);
    }
  }
  for (const field of [...Object.keys(integerLimits), "depositValue"]) {
    for (const value of [NaN, Infinity, -Infinity]) {
      const malformed = createDemoSettings();
      malformed.reservations[field] = value;
      assert.equal(isRestaurantSettings(malformed), false, field);
    }
  }
  for (const value of [NaN, Infinity, -Infinity]) {
    const malformed = createDemoSettings();
    malformed.agent.humanThreshold = value;
    assert.equal(isRestaurantSettings(malformed), false);
  }
});

test("la garde n'accepte aucun mode ni préférence inconnu", () => {
  for (const [section, field, value] of [
    ["general", "currency", "EUR"], ["general", "language", "de"],
    ["reservations", "confirmationMode", "instant"],
    ["reservations", "depositType", "ratio"],
  ]) {
    const settings = createDemoSettings();
    settings[section][field] = value;
    assert.equal(isRestaurantSettings(settings), false, `${section}.${field}`);
  }
  for (const mode of ["automatic", "manual", "deposit"]) {
    const settings = createDemoSettings();
    settings.reservations.confirmationMode = mode;
    settings.reservations.depositType = "percent";
    settings.general.currency = "CDF";
    settings.general.language = "en";
    assert.equal(isRestaurantSettings(settings), true);
  }
});

test("la garde exige sept jours canoniques distincts, des libellés textes et des services structurés", () => {
  const mutations = [
    (s) => { s.hours.days = null; },
    (s) => { s.hours.days = {}; },
    (s) => { s.hours.days.pop(); },
    (s) => { s.hours.days.push(cloneSettings(s).hours.days[0]); },
    (s) => { s.hours.days[1].id = "mon"; },
    (s) => { s.hours.days[1].id = "monday"; },
    (s) => { s.hours.days[1].label = 7; },
    (s) => { s.hours.days[1].closed = "false"; },
    (s) => { s.hours.days[1].slots = null; },
    (s) => { s.hours.days[1].slots = {}; },
    (s) => { s.hours.days[1].slots[0] = null; },
    (s) => { s.hours.days[1].slots[0].start = 1200; },
    (s) => { delete s.hours.days[1].slots[0].end; },
    (s) => { s.hours.closures = {}; },
    (s) => { s.hours.closures = [null]; },
    (s) => { s.hours.closures = [{ date: "2026-01-01" }]; },
    (s) => { s.hours.closures = [{ date: 20260101, reason: "" }]; },
    (s) => { s.hours.closures = [{ date: "", reason: false }]; },
  ];
  mutations.forEach((mutate, index) => {
    const settings = createDemoSettings();
    mutate(settings);
    assert.equal(isRestaurantSettings(settings), false, `Cas ${index}`);
  });
});

test("la garde refuse aussi les tableaux clairsemés et les collections démesurées", () => {
  const mutations = [
    (s) => { delete s.hours.days[2]; },
    (s) => { delete s.hours.days[1].slots[0]; },
    (s) => { s.hours.closures = new Array(1); },
    (s) => { s.hours.days[1].slots = Array.from({ length: 9 }, () => ({ start: "", end: "" })); },
    (s) => { s.hours.closures = Array.from({ length: 367 }, () => ({ date: "", reason: "" })); },
    (s) => { s.agent.instructions = "x".repeat(20001); },
    (s) => { s.hours.days[0].label = "x".repeat(20001); },
    (s) => { s.hours.closures = [{ date: "", reason: "x".repeat(20001) }]; },
  ];
  mutations.forEach((mutate, index) => {
    const settings = createDemoSettings();
    mutate(settings);
    assert.equal(isRestaurantSettings(settings), false, `Cas ${index}`);
  });
});

test("la garde contrôle la forme, sans appliquer les règles métier ni imposer l'ordre des jours", () => {
  const settings = createDemoSettings();
  settings.general.name = "";
  settings.general.phone = "à corriger";
  settings.general.timezone = "à sélectionner";
  settings.reservations.minGuests = -1.5;
  settings.reservations.confirmationMode = "deposit";
  settings.reservations.depositEnabled = false;
  settings.agent.humanThreshold = -1;
  settings.hours.days.reverse();
  settings.hours.days[0].label = "Sunday";
  settings.hours.days[0].slots = [{ start: "horaire à corriger", end: "" }];
  settings.hours.closures = [{ date: "2026-02-30", reason: "" }];
  assert.equal(isRestaurantSettings(settings), true);
  for (const { id } of SETTINGS_TABS) {
    assert.ok(Object.keys(validateSettings(id, settings)).length > 0);
  }
});
