"use client";

import { useRef, useState } from "react";

// ============================================================================
// Types TypeScript pour la Web Speech API (reconnaissance vocale du navigateur)
// ============================================================================
// La Web Speech API est une fonctionnalite du NAVIGATEUR (pas de React, pas
// de Next.js) : elle permet de transformer la voix captee par le micro en
// texte, directement cote client, sans passer par notre backend. Le
// probleme, c'est que TypeScript ne fournit pas toujours des types tout
// prets et fiables pour cette API (elle reste partiellement
// experimentale/prefixee selon les navigateurs) : on definit donc nous-
// memes les formes (interfaces) des objets qu'elle manipule, pour garder
// la verification de types de TypeScript tout en restant honnete sur ce
// que l'API expose reellement.

// Forme de l'evenement recu quand la reconnaissance vocale a reconnu du
// texte AVEC SUCCES. `extends Event` : c'est un evenement DOM classique
// (comme un `click` ou un `submit`), auquel s'ajoute une propriete
// `results` specifique a la reconnaissance vocale.
interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
}

// Evenement specifique declenche par le navigateur quand la reconnaissance
// vocale ECHOUE. Contrairement a une erreur JavaScript classique, il ne
// contient pas de message texte utilisable directement : il fournit un
// CODE (`error`) standardise, a nous de le traduire en message
// comprehensible pour l'utilisateur (voir `VOICE_ERROR_MESSAGES` plus bas).
interface SpeechRecognitionErrorEvent extends Event {
  error: string;
}

// Description de ce que sait faire un objet "reconnaissance vocale" une
// fois cree (voir `new SpeechRecognition()` plus bas dans le code) :
// - lang : la langue parlee attendue (ici "fr-FR" pour le francais).
// - interimResults : si true, le navigateur renvoie des resultats
//   "provisoires" pendant que la personne parle encore (mot par mot) ; on
//   le met a false ici pour n'obtenir que le resultat FINAL, plus fiable
//   et plus simple a gerer.
// - onresult / onend / onerror : les 3 "callbacks" (fonctions de rappel)
//   que le navigateur appelle automatiquement a differents moments du
//   cycle de vie de l'ecoute (resultat pret / ecoute terminee / erreur).
// - start() / stop() : demarrer et arreter l'ecoute du micro.
interface SpeechRecognitionInstance {
  lang: string;
  interimResults: boolean;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onend: (() => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  start: () => void;
  stop: () => void;
}

// Type d'un "constructeur" de reconnaissance vocale : une fonction qu'on
// peut appeler avec `new` (ex: `new SpeechRecognition()`) et qui renvoie un
// objet conforme a SpeechRecognitionInstance defini ci-dessus. On en a
// besoin car en JavaScript, `SpeechRecognition` (le nom de la classe
// fournie par le navigateur) n'est pas une simple fonction, c'est une
// CLASSE — TypeScript distingue "le type d'une instance" (SpeechRecognitionInstance)
// du "type du constructeur qui cree ces instances" (SpeechRecognitionConstructor).
interface SpeechRecognitionConstructor {
  new (): SpeechRecognitionInstance;
}

// Selon le navigateur, la classe de reconnaissance vocale est exposee sous
// des noms differents sur l'objet global `window` :
// - `SpeechRecognition` (nom standard, Chrome/Edge recents)
// - `webkitSpeechRecognition` (prefixe historique webkit, Safari et
//   anciennes versions de Chrome)
// On declare donc un type "Window enrichi" qui accepte OPTIONNELLEMENT
// (`?`) ces deux proprietes, puisqu'aucun des deux n'est garanti present
// (ex: sur Firefox, aucune des deux n'existe).
type SpeechRecognitionWindow = Window & {
  SpeechRecognition?: SpeechRecognitionConstructor;
  webkitSpeechRecognition?: SpeechRecognitionConstructor;
};

// ============================================================================
// Traduction des codes d'erreur du navigateur en messages francais clairs.
// ============================================================================
// La Web Speech API renvoie toujours un code technique en anglais (ex:
// "not-allowed", "no-speech"...), jamais un message pret a afficher a
// l'utilisateur. On centralise ici la correspondance code -> message, ce
// qui permet d'ajouter facilement un nouveau cas plus tard sans toucher a
// la logique de `toggleVoiceInput`.
//
// Liste des codes reellement emis par les navigateurs (Chrome/Edge/Safari) :
// https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognitionErrorEvent/error
const VOICE_ERROR_MESSAGES: Record<string, string> = {
  // L'utilisateur a refuse (ou n'a jamais accorde) la permission d'acces
  // au microphone dans son navigateur. C'est le cas le plus frequent en
  // production : il faut guider l'utilisateur vers les reglages du
  // navigateur, un simple "reessayez" ne suffit pas ici.
  "not-allowed":
    "Le microphone est bloque. Autorisez l'acces au microphone dans les parametres de votre navigateur, puis reessayez.",
  // Meme cause que "not-allowed" mais renvoyee par certains navigateurs
  // (notamment d'anciennes versions de Safari) sous un code different.
  "permission-denied":
    "Le microphone est bloque. Autorisez l'acces au microphone dans les parametres de votre navigateur, puis reessayez.",
  // Aucune parole n'a ete detectee pendant un certain delai (l'utilisateur
  // n'a rien dit, ou trop doucement) : ce n'est pas vraiment une "erreur"
  // grave, on encourage juste a reessayer.
  "no-speech":
    "Aucune parole detectee. Rapprochez-vous du microphone et reessayez.",
  // Le navigateur ne trouve aucun peripherique microphone sur l'appareil
  // (ordinateur sans micro branche, permission systeme bloquee, etc.).
  "audio-capture":
    "Aucun microphone detecte sur cet appareil. Verifiez qu'un microphone est bien connecte.",
  // Erreur reseau : certains navigateurs (Chrome notamment) envoient
  // l'audio a un serveur distant pour le transcrire, une coupure de
  // connexion internet declenche ce code.
  network:
    "Probleme de connexion reseau. Verifiez votre connexion internet et reessayez.",
  // Le service de reconnaissance vocale du navigateur est temporairement
  // indisponible ou desactive par une politique de securite/entreprise.
  "service-not-allowed":
    "Le service de reconnaissance vocale est indisponible pour le moment.",
  // Code renvoye quand la reconnaissance est interrompue par un appel a
  // recognition.stop()/.abort() — CE N'EST PAS UNE VRAIE ERREUR, c'est
  // souvent l'utilisateur lui-meme qui a clique pour arreter. On la liste
  // ici mais on l'ignore volontairement plus bas (voir toggleVoiceInput)
  // pour ne pas afficher un message d'erreur alarmant a tort.
  aborted: "",
};

// Message de secours pour tout code d'erreur non repertorie ci-dessus
// (nouveaux codes ajoutes par les navigateurs, cas rares/inconnus...).
const DEFAULT_VOICE_ERROR_MESSAGE =
  "Impossible d'utiliser le microphone. Reessayez dans quelques instants.";

// ============================================================================
// ChatInput : barre de saisie du widget de chat (texte + micro + envoi).
// ============================================================================
// Recoit une seule prop : `onSend`, une fonction fournie par le composant
// parent (ChatWidget) a appeler avec le texte final quand l'utilisateur
// veut envoyer un message — que ce texte vienne du clavier ou du micro.
// Ce composant ne sait pas comment le message est traite ensuite (envoi au
// backend, etc.) : il se contente de "remonter" le texte au parent, ce qui
// le rend simple a reutiliser et a tester independamment.
export default function ChatInput({
  onSend,
}: {
  onSend: (text: string) => void;
}) {
  // Texte actuellement tape (ou dicte) dans le champ de saisie.
  const [value, setValue] = useState("");
  // true pendant que le micro est en train d'ecouter (utilise pour changer
  // l'apparence du bouton micro et afficher le bon aria-label/title).
  const [isListening, setIsListening] = useState(false);
  // Message d'erreur a afficher sous la barre de saisie (null = aucune
  // erreur a afficher). Voir VOICE_ERROR_MESSAGES plus haut pour le detail
  // des messages possibles.
  const [voiceError, setVoiceError] = useState<string | null>(null);
  // useRef (et non useState) pour stocker l'objet de reconnaissance vocale
  // en cours : on a besoin d'y acceder/le modifier dans des callbacks
  // (onend, onerror) sans provoquer de nouveau rendu du composant a chaque
  // fois — un useRef ne declenche jamais de re-rendu quand on change
  // `.current`, contrairement a un useState.
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);

  // Gestion de l'envoi classique via le clavier + bouton "Envoyer" (ou
  // touche Entree, qui declenche nativement la soumission d'un <form>).
  function handleSubmit(e: React.FormEvent) {
    // Empeche le comportement par defaut du navigateur (recharger la page
    // au submit d'un formulaire HTML), puisqu'on gere l'envoi nous-memes
    // en JavaScript.
    e.preventDefault();
    // .trim() retire les espaces avant/apres : on evite d'envoyer un
    // message vide ou compose uniquement d'espaces.
    if (!value.trim()) return;
    onSend(value.trim());
    // On vide le champ apres l'envoi, pret pour le prochain message.
    setValue("");
  }

  // Active ou desactive la saisie vocale au clic sur le bouton micro.
  // Cette fonction gere tout le cycle de vie : detection du support
  // navigateur, demarrage de l'ecoute, reception du texte reconnu, et
  // gestion des erreurs.
  function toggleVoiceInput() {
    // `window as SpeechRecognitionWindow` : on "convainc" TypeScript que
    // l'objet global `window` peut contenir les proprietes
    // SpeechRecognition/webkitSpeechRecognition definies plus haut (elles
    // n'existent pas dans les types standards de `window` fournis par
    // TypeScript, puisque cette API n'est pas encore un standard officiel
    // stable sur tous les navigateurs).
    const speechWindow = window as SpeechRecognitionWindow;
    // `??` (nullish coalescing) : on essaie d'abord le nom standard
    // `SpeechRecognition`, et si absent (undefined), on retombe sur le nom
    // prefixe `webkitSpeechRecognition`. Si aucun des deux n'existe (ex:
    // Firefox), le resultat final est `undefined`.
    const SpeechRecognition =
      speechWindow.SpeechRecognition ?? speechWindow.webkitSpeechRecognition;

    // Cas 1 : le navigateur ne supporte pas du tout la reconnaissance
    // vocale (ex: Firefox). On informe l'utilisateur et on s'arrete la —
    // impossible d'aller plus loin sans cette API.
    if (!SpeechRecognition) {
      setVoiceError("La saisie vocale n'est pas prise en charge par ce navigateur.");
      return;
    }

    // Cas 2 : le micro est DEJA en train d'ecouter et l'utilisateur
    // reclique sur le bouton -> on interprete ca comme une demande
    // d'ARRET. `recognitionRef.current?.stop()` utilise l'operateur
    // optionnel `?.` par securite (au cas ou la reference serait deja
    // nulle), meme si en pratique elle ne devrait jamais l'etre ici
    // puisque isListening ne peut etre true que si recognitionRef.current
    // a ete rempli plus bas.
    if (isListening) {
      recognitionRef.current?.stop();
      return;
    }

    // Cas 3 (cas normal) : on demarre une NOUVELLE session d'ecoute.
    // On cree une nouvelle instance a chaque demarrage (plutot que d'en
    // reutiliser une seule pour toute la duree de vie du composant) car
    // les objets SpeechRecognition ne sont generalement PAS concus pour
    // etre redemarres plusieurs fois de suite de maniere fiable — creer
    // une instance fraiche a chaque fois evite des comportements
    // incoherents entre navigateurs.
    const recognition = new SpeechRecognition();
    // Langue attendue : francais de France. Ameliore nettement la
    // precision de la reconnaissance par rapport a une langue par defaut
    // (souvent l'anglais americain).
    recognition.lang = "fr-FR";
    // false = on ne veut que le resultat FINAL (une fois que la personne a
    // fini de parler), pas des resultats partiels mot par mot pendant
    // qu'elle parle encore. Plus simple a gerer et plus fiable pour notre
    // cas d'usage (remplir un champ de texte).
    recognition.interimResults = false;

    // Callback appele quand la reconnaissance a reussi a transformer la
    // voix en texte.
    recognition.onresult = (event) => {
      // `event.results` est une liste de resultats (un par "segment" de
      // parole reconnu). Chaque resultat contient lui-meme une liste
      // d'ALTERNATIVES possibles (la meilleure etant a l'index [0]).
      // `Array.from(...)` convertit cette liste (qui n'est pas un vrai
      // tableau JavaScript, juste un objet "array-like") en veritable
      // tableau, pour pouvoir utiliser `.map()` dessus.
      const transcript = Array.from(event.results)
        .map((result) => result[0].transcript)
        .join(" ");
      // On ajoute le texte reconnu A LA SUITE du texte deja present dans
      // le champ (plutot que de l'ecraser), pour permettre a l'utilisateur
      // de combiner clavier et voix, ou de dicter en plusieurs fois.
      // On utilise la forme "callback" de setValue (`(currentValue) => ...`)
      // plutot que `setValue(value + transcript)` pour toujours partir de
      // la valeur la plus a jour, meme si plusieurs mises a jour d'etat
      // s'enchainent rapidement.
      setValue((currentValue) =>
        currentValue ? `${currentValue} ${transcript}` : transcript
      );
    };

    // Callback appele quand l'ecoute se termine, QUELLE QU'EN SOIT LA
    // RAISON (fin normale apres un silence, ou arret manuel via stop()).
    // On remet toujours l'etat "ecoute terminee" et on vide la reference,
    // pour permettre de demarrer une toute nouvelle session au prochain clic.
    recognition.onend = () => {
      setIsListening(false);
      recognitionRef.current = null;
    };

    // Callback appele en cas d'ECHEC de la reconnaissance vocale.
    // Gestion detaillee des erreurs : on lit `event.error` (le code
    // technique fourni par le navigateur, ex: "not-allowed", "no-speech")
    // et on va chercher le message francais correspondant dans
    // VOICE_ERROR_MESSAGES defini plus haut, au lieu d'afficher un seul
    // message generique pour toutes les erreurs.
    recognition.onerror = (event) => {
      setIsListening(false);
      recognitionRef.current = null;

      // Cas particulier "aborted" : declenche quand l'utilisateur clique
      // lui-meme sur le bouton pour arreter la saisie vocale (via
      // recognition.stop() dans le Cas 2 plus haut). Ce n'est pas un vrai
      // probleme, donc on n'affiche AUCUN message d'erreur dans ce cas —
      // sinon l'utilisateur verrait un message alarmant a chaque fois
      // qu'il arrete volontairement le micro, ce qui serait trompeur.
      if (event.error === "aborted") {
        setVoiceError(null);
        return;
      }

      // Pour tous les autres codes, on cherche le message correspondant
      // dans notre dictionnaire VOICE_ERROR_MESSAGES. Si le code n'y
      // figure pas (nouveau code introduit par un navigateur, cas rare
      // non repertorie), on retombe sur DEFAULT_VOICE_ERROR_MESSAGE plutot
      // que d'afficher un code technique en anglais brut a l'utilisateur
      // final (ex: on ne veut jamais qu'il voie juste "network" a l'ecran).
      const message = VOICE_ERROR_MESSAGES[event.error] || DEFAULT_VOICE_ERROR_MESSAGE;
      setVoiceError(message);
    };

    // On efface un eventuel message d'erreur precedent avant de
    // (re)demarrer une ecoute, pour ne pas laisser un vieux message
    // affiche a l'ecran pendant une nouvelle tentative.
    setVoiceError(null);
    // On memorise cette instance pour pouvoir l'arreter plus tard (Cas 2
    // ci-dessus) et on met a jour l'etat visuel du bouton.
    recognitionRef.current = recognition;
    setIsListening(true);
    // Demarre reellement l'ecoute du microphone (declenche la demande de
    // permission navigateur si c'est la premiere fois).
    recognition.start();
  }

  return (
    // `relative` sur le <form> : necessaire pour que le message d'erreur
    // (positionne en `absolute` plus bas) se positionne PAR RAPPORT A ce
    // formulaire, et non par rapport a toute la page.
    <form onSubmit={handleSubmit} className="relative flex border-t p-2 gap-2">
      {/* Champ de saisie texte classique, "controle" par React (sa valeur
          est toujours synchronisee avec l'etat `value`). */}
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Ecrivez votre message..."
        className="flex-1 border rounded-full px-4 py-2 text-sm outline-none"
      />
      {/*
        Bouton micro. type="button" (et non "submit") est IMPORTANT : sans
        ca, cliquer sur le micro a l'interieur du <form> declencherait
        aussi handleSubmit et enverrait un message vide par erreur.
        aria-label/title changent selon l'etat pour rester coherents avec
        ce que l'utilisateur voit (icone micro vs icone stop), utile aussi
        pour les technologies d'assistance (lecteurs d'ecran).
      */}
      <button
        type="button"
        onClick={toggleVoiceInput}
        aria-label={isListening ? "Arrêter la saisie vocale" : "Parler à l'assistant"}
        title={isListening ? "Arrêter la saisie vocale" : "Parler à l'assistant"}
        className={`rounded-full px-3 py-2 text-sm font-medium transition ${
          isListening
            ? "bg-danger text-white"
            : "bg-gray-100 text-gray-700 hover:bg-gray-200"
        }`}
      >
        {/* Symbole "stop" (carre) pendant l'ecoute, symbole micro sinon */}
        {isListening ? "■" : "🎙"}
      </button>
      {/* Bouton d'envoi classique : type="submit" declenche handleSubmit
          via l'evenement onSubmit du <form> ci-dessus. */}
      <button
        type="submit"
        className="bg-primary text-white rounded-full px-4 py-2 text-sm font-medium"
      >
        Envoyer
      </button>
      {/*
        Message d'erreur, affiche uniquement si voiceError n'est pas null.
        `role="alert"` : indique aux lecteurs d'ecran qu'il s'agit d'une
        information importante a annoncer immediatement (accessibilite).
        `absolute mt-12` : positionne le message SOUS la barre de saisie
        sans pousser le reste de la mise en page (il "flotte" par-dessus).
      */}
      {voiceError && (
        <p className="absolute mt-12 px-2 text-xs text-danger" role="alert">
          {voiceError}
        </p>
      )}
    </form>
  );
}