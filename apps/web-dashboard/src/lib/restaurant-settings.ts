/**
 * Modèle indépendant de React, du navigateur et du transport réseau.
 *
 * Deux contrôles complémentaires sont volontairement séparés :
 * - isRestaurantSettings vérifie la structure d'une réponse inconnue ;
 * - validateSettings vérifie les règles métier d'un brouillon, onglet par onglet.
 *
 * Une chaîne vide ou un entier négatif peuvent donc passer la garde de structure,
 * tout en produisant une erreur de saisie. Cela permet d'afficher et de corriger
 * des paramètres incomplets sans confondre leur forme avec leur validité métier.
 */
export type SettingsTab = "general" | "hours" | "reservations" | "agent";

export type RestaurantSettings = {
  general: {
    name: string;
    description: string;
    phone: string;
    whatsapp: string;
    email: string;
    address: string;
    city: string;
    timezone: string;
    currency: "USD" | "CDF";
    language: "fr" | "en";
  };
  hours: {
    days: Array<{
      id: string;
      label: string;
      closed: boolean;
      slots: Array<{ start: string; end: string }>;
    }>;
    closures: Array<{ date: string; reason: string }>;
  };
  reservations: {
    minGuests: number;
    maxGuests: number;
    advanceNoticeMinutes: number;
    maxAdvanceDays: number;
    slotMinutes: number;
    durationMinutes: number;
    graceMinutes: number;
    cancellationHours: number;
    confirmationMode: "automatic" | "manual" | "deposit";
    depositEnabled: boolean;
    depositType: "fixed" | "percent";
    depositValue: number;
  };
  agent: {
    enabled: boolean;
    name: string;
    welcomeMessage: string;
    instructions: string;
    handoffPhone: string;
    humanThreshold: number;
  };
};

export const SETTINGS_TABS: Array<{
  id: SettingsTab;
  label: string;
  description: string;
}> = [
  {
    id: "general",
    label: "Général",
    description: "Identité, coordonnées et préférences du restaurant.",
  },
  {
    id: "hours",
    label: "Horaires",
    description: "Services hebdomadaires et fermetures exceptionnelles.",
  },
  {
    id: "reservations",
    label: "Réservations",
    description: "Capacité, délais, confirmation et acompte.",
  },
  {
    id: "agent",
    label: "Assistant IA",
    description: "Accueil automatisé, consignes et relais humain.",
  },
];

const DAYS = [
  ["mon", "Lundi"],
  ["tue", "Mardi"],
  ["wed", "Mercredi"],
  ["thu", "Jeudi"],
  ["fri", "Vendredi"],
  ["sat", "Samedi"],
  ["sun", "Dimanche"],
] as const;

// Ces plafonds défensifs limitent les collections et les chaînes provenant
// d'une réponse externe. Ils ne remplacent pas les limites métier plus fines.
const MAX_SERVICES = 8;
const MAX_CLOSURES = 366;
const MAX_RESPONSE_TEXT = 20_000;

/** Chaque appel reconstruit tous les tableaux et objets, sans référence partagée. */
export function createDemoSettings(): RestaurantSettings {
  return {
    general: {
      name: "Restaurant Démonstration",
      description: "Une table conviviale au cœur de Lubumbashi.",
      phone: "+243 970 000 000",
      whatsapp: "+243 970 000 000",
      email: "contact@restaurant-demo.example",
      address: "1, avenue de la Libération",
      city: "Lubumbashi",
      timezone: "Africa/Lubumbashi",
      currency: "USD",
      language: "fr",
    },
    hours: {
      days: DAYS.map(([id, label]) => ({
        id,
        label,
        closed: id === "mon",
        slots:
          id === "mon"
            ? []
            : [
                { start: "12:00", end: "15:00" },
                { start: "18:00", end: "22:00" },
              ],
      })),
      closures: [],
    },
    reservations: {
      minGuests: 1,
      maxGuests: 12,
      advanceNoticeMinutes: 60,
      maxAdvanceDays: 60,
      slotMinutes: 30,
      durationMinutes: 90,
      graceMinutes: 15,
      cancellationHours: 24,
      confirmationMode: "automatic",
      depositEnabled: false,
      depositType: "fixed",
      depositValue: 10,
    },
    agent: {
      enabled: true,
      name: "Assistant Démonstration",
      welcomeMessage: "Bonjour ! Comment pouvons-nous préparer votre visite ?",
      instructions:
        "Réponds en français avec courtoisie. Vérifie les disponibilités avant " +
        "de confirmer une réservation et propose un relais humain en cas de doute.",
      handoffPhone: "",
      humanThreshold: 3,
    },
  };
}

/**
 * Le brouillon ne doit jamais modifier les paramètres déjà enregistrés.
 * structuredClone conserve aussi NaN dans une saisie numérique incomplète :
 * contrairement à JSON, il ne transforme pas silencieusement NaN en null.
 */
export function cloneSettings(settings: RestaurantSettings): RestaurantSettings {
  return structuredClone(settings);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isText(value: unknown): value is string {
  return typeof value === "string" && value.length <= MAX_RESPONSE_TEXT;
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function isOneOf<T extends string>(
  value: unknown,
  choices: readonly T[],
): value is T {
  return typeof value === "string" && choices.some((choice) => choice === value);
}

function isBoundedArray<T>(
  value: unknown,
  maximum: number,
  isItem: (item: unknown) => item is T,
): value is T[] {
  if (!Array.isArray(value) || value.length > maximum) return false;
  // for…of observe aussi les cases vides d'un tableau clairsemé ; every()
  // les ignorerait et pourrait ainsi accepter une collection incomplète.
  for (const item of value) {
    if (!isItem(item)) return false;
  }
  return true;
}

/** Garde sans coercition : "12", null, NaN et Infinity ne sont pas des nombres valides. */
export function isRestaurantSettings(value: unknown): value is RestaurantSettings {
  if (!isRecord(value)) return false;
  const { general, hours, reservations, agent } = value;
  if (
    !isRecord(general) ||
    !isRecord(hours) ||
    !isRecord(reservations) ||
    !isRecord(agent)
  ) {
    return false;
  }

  if (
    ![
      "name", "description", "phone", "whatsapp", "email",
      "address", "city", "timezone",
    ].every((key) => isText(general[key])) ||
    !isOneOf(general.currency, ["USD", "CDF"]) ||
    !isOneOf(general.language, ["fr", "en"])
  ) {
    return false;
  }

  if (
    !isBoundedArray(
      hours.days,
      DAYS.length,
      (day): day is RestaurantSettings["hours"]["days"][number] =>
        isRecord(day) &&
        isOneOf(day.id, DAYS.map(([id]) => id)) &&
        isText(day.label) &&
        typeof day.closed === "boolean" &&
        isBoundedArray(
          day.slots,
          MAX_SERVICES,
          (slot): slot is { start: string; end: string } =>
            isRecord(slot) && isText(slot.start) && isText(slot.end),
        ),
    ) ||
    hours.days.length !== DAYS.length ||
    new Set(hours.days.map((day) => day.id)).size !== DAYS.length
  ) {
    return false;
  }

  // L'identité des jours est canonique ; leur ordre et les libellés restent
  // libres, afin d'autoriser une présentation localisée sans modifier le modèle.
  if (
    !isBoundedArray(
      hours.closures,
      MAX_CLOSURES,
      (closure): closure is { date: string; reason: string } =>
        isRecord(closure) && isText(closure.date) && isText(closure.reason),
    ) ||
    ![
      "minGuests", "maxGuests", "advanceNoticeMinutes", "maxAdvanceDays",
      "slotMinutes", "durationMinutes", "graceMinutes", "cancellationHours",
      "depositValue",
    ].every((key) => isFiniteNumber(reservations[key])) ||
    !isOneOf(reservations.confirmationMode, ["automatic", "manual", "deposit"]) ||
    typeof reservations.depositEnabled !== "boolean" ||
    !isOneOf(reservations.depositType, ["fixed", "percent"]) ||
    typeof agent.enabled !== "boolean" ||
    !["name", "welcomeMessage", "instructions", "handoffPhone"].every(
      (key) => isText(agent[key]),
    ) ||
    !isFiniteNumber(agent.humanThreshold)
  ) {
    return false;
  }
  return true;
}

/** V1 : heures locales strictes, entre 00:00 et 23:59, sans passage à minuit. */
function minutesSinceMidnight(value: unknown): number | null {
  // La longueur exacte exclut aussi un retour à la ligne final : en JavaScript,
  // l'ancre « $ » seule peut correspondre juste avant ce dernier caractère.
  if (
    typeof value !== "string" ||
    value.length !== 5 ||
    !/^(?:[01]\d|2[0-3]):[0-5]\d$/.test(value)
  ) {
    return null;
  }
  const [hours, minutes] = value.split(":").map(Number);
  return hours * 60 + minutes;
}

function isCalendarDate(value: unknown): value is string {
  if (
    typeof value !== "string" ||
    value.length !== 10 ||
    !/^\d{4}-\d{2}-\d{2}$/.test(value)
  ) {
    return false;
  }
  const [year, month, day] = value.split("-").map(Number);
  if (year < 1 || month < 1 || month > 12 || day < 1) return false;
  // Le calcul explicite évite deux pièges de Date : la normalisation du
  // 31 février en mars et le traitement particulier des années 00 à 99.
  const leapYear = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const lengths = [31, leapYear ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  return day <= lengths[month - 1];
}

function isEmail(value: string): boolean {
  if (value.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return false;
  const [local, domain] = value.split("@");
  // Validation volontairement pratique, sans prétendre couvrir les adresses
  // RFC exotiques : les alias avec « + » restent notamment acceptés.
  return (
    local.length <= 64 &&
    /^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+$/.test(local) &&
    !local.startsWith(".") &&
    !local.endsWith(".") &&
    !local.includes("..") &&
    domain.split(".").every(
      (label) =>
        label.length <= 63 &&
        /^[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?$/.test(label),
    )
  );
}

/**
 * Renvoie uniquement les erreurs de l'onglet demandé, sans modifier les données.
 * Les clés sont des chemins stables : l'interface peut rattacher chaque message
 * au champ concerné, y compris dans les tableaux indexés à partir de zéro.
 */
export function validateSettings(
  tab: SettingsTab,
  data: RestaurantSettings,
): Record<string, string> {
  const errors: Record<string, string> = {};

  const text = (
    path: string,
    value: unknown,
    maximum: number,
    required = false,
  ): value is string => {
    if (typeof value !== "string" || (required && value.trim().length === 0)) {
      errors[path] = required ? "Ce champ est obligatoire." : "Saisissez un texte.";
      return false;
    }
    if (value.length > maximum) {
      errors[path] = `Utilisez au maximum ${maximum} caractères.`;
      return false;
    }
    return true;
  };

  const phone = (path: string, value: unknown) => {
    if (!text(path, value, 50) || !value.trim()) return;
    const cleaned = value.trim();
    const digits = cleaned.replace(/\D/g, "");
    // Aucun indicatif national imposé : numéros locaux ou internationaux,
    // avec espaces, points, tirets ou parenthèses. Les lettres sont refusées.
    if (!/^\+?[0-9 ().-]+$/.test(cleaned) || digits.length < 7 || digits.length > 15) {
      errors[path] = "Saisissez un numéro de téléphone valide (7 à 15 chiffres).";
    }
  };

  const integer = (
    path: string,
    value: unknown,
    minimum: number,
    maximum: number,
  ): value is number => {
    // Ne jamais utiliser Number(value) ici : Number("") vaut zéro et masquerait
    // une saisie vide. Un champ numérique vidé peut également fournir NaN.
    if (!isFiniteNumber(value) || !Number.isInteger(value)) {
      errors[path] = "Saisissez un nombre entier valide.";
      return false;
    }
    if (value < minimum || value > maximum) {
      errors[path] = `Saisissez une valeur comprise entre ${minimum} et ${maximum}.`;
      return false;
    }
    return true;
  };

  if (tab === "general") {
    const general = data.general;
    text("general.name", general.name, 120, true);
    text("general.description", general.description, 2_000);
    text("general.address", general.address, 300, true);
    text("general.city", general.city, 120, true);
    phone("general.phone", general.phone);
    phone("general.whatsapp", general.whatsapp);
    if (text("general.email", general.email, 254) && general.email.trim()) {
      if (!isEmail(general.email.trim())) {
        errors["general.email"] = "Saisissez une adresse e-mail valide.";
      }
    }
    if (text("general.timezone", general.timezone, 100, true)) {
      try {
        // Intl connaît les fuseaux réellement pris en charge par l'exécution ;
        // une liste limitée au Congo empêcherait inutilement l'internationalisation.
        new Intl.DateTimeFormat("fr", { timeZone: general.timezone });
      } catch {
        errors["general.timezone"] = "Sélectionnez un fuseau horaire reconnu.";
      }
    }
    if (!isOneOf(general.currency, ["USD", "CDF"])) {
      errors["general.currency"] = "Sélectionnez USD ou CDF.";
    }
    if (!isOneOf(general.language, ["fr", "en"])) {
      errors["general.language"] = "Sélectionnez le français ou l’anglais.";
    }
  }

  if (tab === "hours") {
    const { days, closures } = data.hours;
    if (
      days.length !== DAYS.length ||
      days.some((day) => !DAYS.some(([id]) => id === day.id)) ||
      new Set(days.map((day) => day.id)).size !== DAYS.length
    ) {
      errors["hours.days"] = "Renseignez les sept jours de la semaine, sans doublon.";
    }

    days.forEach((day, dayIndex) => {
      // Les services conservés pour un jour fermé sont inactifs : les ignorer
      // permet de fermer puis rouvrir le jour sans effacer sa configuration.
      if (day.closed) return;
      const path = `hours.days.${dayIndex}.slots`;
      if (day.slots.length === 0) {
        errors[path] = "Ajoutez au moins un service pour un jour ouvert.";
      } else if (day.slots.length > MAX_SERVICES) {
        errors[path] = `Prévoyez au maximum ${MAX_SERVICES} services par jour.`;
      }
      const intervals: Array<{ start: number; end: number; index: number }> = [];
      day.slots.forEach((slot, index) => {
        const start = minutesSinceMidnight(slot.start);
        const end = minutesSinceMidnight(slot.end);
        if (start === null) errors[`${path}.${index}.start`] = "Utilisez le format HH:mm.";
        if (end === null) errors[`${path}.${index}.end`] = "Utilisez le format HH:mm.";
        if (start === null || end === null) return;
        if (end <= start) {
          errors[`${path}.${index}.end`] =
            "La fin doit suivre le début le même jour ; les services de nuit ne sont pas pris en charge.";
          return;
        }
        intervals.push({ start, end, index });
      });

      // Comparer les intervalles sans trier les données évite toute mutation.
      // Les bornes sont semi-ouvertes : 12:00–15:00 puis 15:00–18:00 est autorisé.
      for (let index = 0; index < intervals.length; index += 1) {
        for (let other = index + 1; other < intervals.length; other += 1) {
          const left = intervals[index];
          const right = intervals[other];
          if (left.start < right.end && right.start < left.end) {
            errors[`${path}.${left.index}.start`] = "Les services ne doivent pas se chevaucher.";
            errors[`${path}.${right.index}.start`] = "Les services ne doivent pas se chevaucher.";
          }
        }
      }
    });

    if (closures.length > MAX_CLOSURES) {
      errors["hours.closures"] = `Prévoyez au maximum ${MAX_CLOSURES} fermetures exceptionnelles.`;
    }
    const seenDates = new Map<string, number>();
    closures.forEach((closure, index) => {
      const path = `hours.closures.${index}`;
      text(`${path}.reason`, closure.reason, 300);
      if (!isCalendarDate(closure.date)) {
        errors[`${path}.date`] = "Saisissez une date réelle au format AAAA-MM-JJ.";
        return;
      }
      const previous = seenDates.get(closure.date);
      if (previous !== undefined) {
        errors[`${path}.date`] = "Cette date de fermeture est déjà renseignée.";
        errors[`hours.closures.${previous}.date`] = "Cette date de fermeture est déjà renseignée.";
      } else {
        seenDates.set(closure.date, index);
      }
    });
  }

  if (tab === "reservations") {
    const reservations = data.reservations;
    const validMin = integer("reservations.minGuests", reservations.minGuests, 1, 1_000);
    const validMax = integer("reservations.maxGuests", reservations.maxGuests, 1, 1_000);
    if (validMin && validMax && reservations.minGuests > reservations.maxGuests) {
      errors["reservations.minGuests"] = "Le minimum ne doit pas dépasser le maximum.";
      errors["reservations.maxGuests"] = "Le maximum doit être au moins égal au minimum.";
    }
    // Limites V1 : préavis de 30 jours, horizon d'un an, pas de 5 min à 4 h,
    // durée de 5 min à 24 h, tolérance de 2 h et annulation jusqu'à 30 jours.
    integer("reservations.advanceNoticeMinutes", reservations.advanceNoticeMinutes, 0, 43_200);
    integer("reservations.maxAdvanceDays", reservations.maxAdvanceDays, 1, 365);
    integer("reservations.slotMinutes", reservations.slotMinutes, 5, 240);
    integer("reservations.durationMinutes", reservations.durationMinutes, 5, 1_440);
    integer("reservations.graceMinutes", reservations.graceMinutes, 0, 120);
    integer("reservations.cancellationHours", reservations.cancellationHours, 0, 720);

    if (!isOneOf(reservations.confirmationMode, ["automatic", "manual", "deposit"])) {
      errors["reservations.confirmationMode"] = "Sélectionnez un mode de confirmation valide.";
    } else if (reservations.confirmationMode === "deposit" && !reservations.depositEnabled) {
      errors["reservations.depositEnabled"] = "Activez l’acompte pour ce mode de confirmation.";
    }
    if (!isOneOf(reservations.depositType, ["fixed", "percent"])) {
      errors["reservations.depositType"] = "Sélectionnez un montant fixe ou un pourcentage.";
    }
    if (reservations.depositEnabled) {
      // Les montants monétaires et les pourcentages admettent des décimales,
      // contrairement aux capacités et aux délais exprimés en unités entières.
      // Un plafond élevé du fixe reste compatible avec des montants en CDF.
      const maximum = reservations.depositType === "percent" ? 100 : 1_000_000_000;
      if (
        !isFiniteNumber(reservations.depositValue) ||
        reservations.depositValue <= 0 ||
        reservations.depositValue > maximum
      ) {
        errors["reservations.depositValue"] =
          reservations.depositType === "percent"
            ? "Saisissez un pourcentage strictement positif et inférieur ou égal à 100."
            : "Saisissez un montant strictement positif, au maximum de 1 000 000 000.";
      }
    }
  }

  if (tab === "agent") {
    const agent = data.agent;
    text("agent.name", agent.name, 100, agent.enabled);
    text("agent.welcomeMessage", agent.welcomeMessage, 2_000, agent.enabled);
    text("agent.instructions", agent.instructions, 10_000, agent.enabled);
    // Comme les autres coordonnées, le téléphone de relais est facultatif ;
    // s'il est renseigné, son format doit rester exploitable.
    phone("agent.handoffPhone", agent.handoffPhone);
    if (agent.enabled) {
      integer("agent.humanThreshold", agent.humanThreshold, 1, 100);
    }
  }
  return errors;
}
