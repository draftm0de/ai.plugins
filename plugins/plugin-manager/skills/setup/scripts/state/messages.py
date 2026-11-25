"""The one place that turns a failure into the message shown to the person (R25, R26).

Pure text: no file access except the optional operator language, no state. A failure with a known code gets its
catalogue wording, anything else the "cause not known" wording; the raw error text is only returned as detail.
Layout (two paragraphs of running text, no labels) and wording live here and nowhere else."""
import json
from pathlib import Path

LANGUAGES = ('en', 'de')
DEFAULT_LANGUAGE = 'en'

# action names as the person knows them; the headline names what was asked for, never a helper or flow
ACTIONS = {'setup': 'setup', 'docs': 'docs', 'modify': 'modify', 'publish': 'publish', 'verify': 'verify'}

HEADLINE = {
    'en': 'The {action} action could not be completed, because {cause}.',
    'de': 'Die Aktion {action} konnte nicht abgeschlossen werden, weil {cause}.',
}
STOPPED = {
    'en': 'The {action} action was stopped, because {cause}.',
    'de': 'Die Aktion {action} wurde abgebrochen, weil {cause}.',
}
STOPPED_ANY = {
    'en': 'The requested action was stopped, because {cause}.',
    'de': 'Die angefragte Aktion wurde abgebrochen, weil {cause}.',
}
PLEASE = {'en': 'Please {way}.', 'de': 'Bitte {way}.'}
REPEAT = {'en': 'Then call /plugin-manager:{skill} again.', 'de': 'Rufe danach /plugin-manager:{skill} erneut auf.'}
CHANGED = {
    'none': {'en': 'Nothing was changed.', 'de': 'Es wurde nichts geändert.'},
    'language': {'en': 'The language you chose was saved.', 'de': 'Die Sprache, die du gewählt hast, wurde gespeichert.'},
}

# code -> cause (after "because") and way (after "Please"), per language; {facts} are filled from the failure
CATALOGUE = {
    'git_missing': {
        'en': ('Git is not installed or cannot be found', 'install Git'),
        'de': ('Git nicht installiert ist oder nicht gefunden wird', 'installiere Git'),
    },
    'not_a_repository': {
        'en': ('the folder {path} is not recognised as a Git repository',
               'either initialise a Git repository in an IDE (for example VS Code) or run `git init` in a terminal in that folder'),
        'de': ('der Ordner {path} nicht als Git-Repository erkannt wird',
               'initialisiere entweder in einer IDE (zum Beispiel VS Code) ein Git-Repository oder führe in einem Terminal in diesem Ordner `git init` aus'),
    },
    'plugin_without_repository': {
        'en': ('the folder {path} is not recognised as a Git repository and has no GitHub address yet',
               'run `git init` in that folder, in an IDE (for example VS Code) or in a terminal, and then '
               '`git remote add origin https://github.com/<owner>/<name>.git` (the repository does not have to exist yet)'),
        'de': ('der Ordner {path} nicht als Git-Repository erkannt wird und noch keine GitHub-Adresse hat',
               'führe in diesem Ordner, in einer IDE (zum Beispiel VS Code) oder in einem Terminal, `git init` aus und danach '
               '`git remote add origin https://github.com/<owner>/<name>.git` (das Repository muss auf GitHub noch nicht existieren)'),
    },
    'no_origin': {
        'en': ('the folder {path} has no GitHub address yet',
               'run `git remote add origin https://github.com/<owner>/<name>.git` in that folder (the repository does not have to exist yet)'),
        'de': ('der Ordner {path} noch keine GitHub-Adresse hat',
               'führe in diesem Ordner `git remote add origin https://github.com/<owner>/<name>.git` aus (das Repository muss auf GitHub noch nicht existieren)'),
    },
    'inside_repository': {
        'en': ('the folder {path} lies inside the Git repository {root}', 'choose the folder that is itself the repository'),
        'de': ('der Ordner {path} im Git-Repository {root} liegt', 'wähle den Ordner, der selbst das Repository ist'),
    },
    'address_not_plain': {
        'en': ('the address {address} is not a plain GitHub address',
               'use the form `https://github.com/<owner>/<name>.git`, without user name or password'),
        'de': ('die Adresse {address} keine einfache GitHub-Adresse ist',
               'verwende die Form `https://github.com/<owner>/<name>.git`, ohne Benutzername und Passwort'),
    },
    'address_differs': {
        'en': ('the given address {address} differs from the GitHub address of the folder ({origin})',
               'use the address of the folder, or change the GitHub address of the folder first'),
        'de': ('die angegebene Adresse {address} von der GitHub-Adresse des Ordners ({origin}) abweicht',
               'verwende die Adresse des Ordners oder ändere zuerst die GitHub-Adresse des Ordners'),
    },
    'other_content': {
        'en': ('the folder {path} already holds other files that are not part of a plugin',
               'either start in an empty folder or move the other files out of the folder'),
        'de': ('der Ordner {path} bereits andere Dateien enthält, die nicht zu einem Plugin gehören',
               'beginne entweder in einem leeren Ordner oder verschiebe die anderen Dateien aus dem Ordner'),
    },
    'existing_differs': {
        'en': ('some files in {path} already exist with other content',
               'keep them as they are, or choose by hand which version stays (the setup asks for each file)'),
        'de': ('einige Dateien in {path} bereits mit anderem Inhalt vorhanden sind',
               'behalte sie, wie sie sind, oder entscheide von Hand, welche Fassung bleibt (das Setup fragt bei jeder Datei nach)'),
    },
    'unsupported_format': {
        'en': ('the file {path} has a format this version does not read',
               'move or rename the file (the Manager never converts or deletes it)'),
        'de': ('die Datei {path} ein Format hat, das diese Version nicht liest',
               'verschiebe die Datei oder benenne sie um (der Manager wandelt sie nie um und löscht sie nie)'),
    },
    'not_configured': {
        'en': ('this folder is not configured yet', 'run /plugin-manager:setup first'),
        'de': ('dieser Ordner noch nicht konfiguriert ist', 'führe zuerst /plugin-manager:setup aus'),
    },
    'invalid_name': {
        'en': ('the technical name is not valid', 'give a name in lowercase kebab-case (letters, digits and single hyphens, for example `my-plugin`)'),
        'de': ('der technische Name nicht gültig ist', 'gib einen Namen in Kleinbuchstaben mit Bindestrichen an (Buchstaben, Ziffern und einzelne Bindestriche, zum Beispiel `mein-plugin`)'),
    },
    'empty_display_name': {
        'en': ('the display name is empty', 'give a display name'),
        'de': ('der Anzeigename leer ist', 'gib einen Anzeigenamen an'),
    },
    'empty_description': {
        'en': ('the description is empty', 'give a description'),
        'de': ('die Beschreibung leer ist', 'gib eine Beschreibung an'),
    },
    'nothing_to_change': {
        'en': ('no change was given', 'give a name, a display name or a description'),
        'de': ('keine Änderung angegeben wurde', 'gib einen Namen, einen Anzeigenamen oder eine Beschreibung an'),
    },
    'unknown': {
        'en': ('the cause is not known (an unexpected error)',
               'either call the same skill again (it checks the state first, so repeating is safe) or run `/plugin-manager:verify` for a read-only check of the folder'),
        'de': ('die Ursache nicht bekannt ist (ein unerwarteter Fehler)',
               'rufe entweder denselben Skill erneut auf (er prüft zuerst den Zustand, Wiederholen ist also sicher) oder führe `/plugin-manager:verify` für eine reine Lese-Prüfung des Ordners aus'),
    },
}

# state-helper conflicts (Conflict.code) that are known causes; every other conflict is not known
CONFLICT_CODES = {'not_fresh': 'other_content', 'config_format': 'unsupported_format', 'not_configured': 'not_configured'}

# the gate: why a writing skill stops (the reason follows "only partly (...)")
GATE_REASONS = {
    'en': {'stop': 'something in this folder blocks the setup', 'language': 'the language is not set yet',
           'configure': 'this folder is not configured yet', 'skeleton': 'some required files or settings are missing or outdated',
           'sync': 'a managed file needs your decision', 'style': 'the writing style docs/style.md is missing'},
    'de': {'stop': 'etwas in diesem Ordner blockiert die Einrichtung', 'language': 'die Sprache ist noch nicht gesetzt',
           'configure': 'dieser Ordner ist noch nicht konfiguriert', 'skeleton': 'einige benötigte Dateien oder Einstellungen fehlen oder sind veraltet',
           'sync': 'eine verwaltete Datei braucht deine Entscheidung', 'style': 'der Schreibstil docs/style.md fehlt'},
}
GATE_CAUSE = {'en': 'this folder is not set up yet, or only partly ({reason})',
              'de': 'dieser Ordner noch nicht oder nur teilweise eingerichtet ist ({reason})'}
GATE_WAY = {'en': 'Please run /plugin-manager:setup first.', 'de': 'Führe zuerst /plugin-manager:setup aus.'}


class Failure(ValueError):
    """A failure with a catalogue code and the facts the wording needs. Still a ValueError for existing handlers."""

    def __init__(self, code, **facts):
        if code not in CATALOGUE:
            raise KeyError('Unknown failure code: ' + code)
        self.code, self.facts = code, {key: str(value) for key, value in facts.items()}
        super().__init__(render_plain(code, self.facts) + (' [' + self.facts['detail'] + ']' if 'detail' in self.facts else ''))


def pick(language):
    return language if language in LANGUAGES else DEFAULT_LANGUAGE


def language_for(root, requested=None):
    """The requested language, else the operator language saved in the folder, else English (never guessed)."""
    if requested in LANGUAGES:
        return requested
    try:
        text = (Path(root) / '.project' / 'operator.json').read_text(encoding='utf-8')
        saved = json.loads(text).get('operator_language')
    except (OSError, ValueError, AttributeError, TypeError):
        saved = None
    return pick(saved)


def render_plain(code, facts, language='en'):
    cause, way = CATALOGUE[code][pick(language)]
    return (cause + '; please ' + way if pick(language) == 'en' else cause + '; bitte ' + way).format_map(_Facts(facts))


class _Facts(dict):
    def __missing__(self, key):
        return '{' + key + '}'


def render(action, code, facts=None, language=None, changed=None, skill=None, stopped=False, repeat=True):
    """The two-paragraph message. `changed` is one of CHANGED or None (the sentence is then left out)."""
    lang = pick(language)
    cause, way = CATALOGUE[code][lang]
    return _layout(lang, action, cause.format_map(_Facts(facts or {})), way.format_map(_Facts(facts or {})), changed, skill or action, stopped, repeat)


def _layout(lang, action, cause, way, changed, skill, stopped, repeat):
    first = (STOPPED if stopped else HEADLINE)[lang].format(action=ACTIONS.get(action, action), cause=cause)
    if changed in CHANGED:
        first += ' ' + CHANGED[changed][lang]
    second = PLEASE[lang].format(way=way)
    if repeat:
        second += ' ' + REPEAT[lang].format(skill=skill)
    return first + '\n\n' + second


def gate_message(action, next_state, language=None):
    """The stop of a writing skill at a closed gate."""
    lang = pick(language)
    reason = GATE_REASONS[lang].get(next_state, GATE_REASONS[lang]['stop'])
    cause = GATE_CAUSE[lang].format(reason=reason)
    first = STOPPED[lang].format(action=action, cause=cause) if action else STOPPED_ANY[lang].format(cause=cause)
    return first + '\n\n' + GATE_WAY[lang]


def classify(error, folder=None):
    """Catalogue code and facts of an error, or ('unknown', {}). Only coded failures are known causes."""
    code = getattr(error, 'code', None)
    if isinstance(error, Failure):
        return error.code, dict({'path': str(folder)} if folder else {}, **error.facts)
    if code in CONFLICT_CODES:
        return CONFLICT_CODES[code], {'path': str(folder) if folder else str(getattr(error, 'path', '.'))}
    return 'unknown', {}


def explain(action, error, language=None, changed=None, skill=None, folder=None):
    """Message and technical detail for any error. The detail is for the person only on request."""
    code, facts = classify(error, folder)
    return {'message': render(action, code, facts, language, changed, skill),
            'known': code != 'unknown', 'code': code, 'detail': str(error)}
