# Mit Freigabe veröffentlichen

## Vorbereiten

Bitte den Manager: „Bereite publish für dieses Repository vor.“ Er prüft Änderungen und Ziel, schlägt die Commit-Nachricht vor und bereitet PR-Text, Dateiauswahl und Prüfungen vor. Bis zur Freigabe werden weder Commit noch Push oder PR ausgeführt. Ein Changelog kann datierte Änderungen festhalten, ist aber keine Voraussetzung.

## Freigeben

Du prüfst Diff, Nachricht, Repository, Branch und Merge-Methode. Eine konkrete Anfrage lautet beispielsweise: „Soll ich den benannten Feature-Branch anlegen, die ausgewählten Änderungen mit der gezeigten Nachricht darauf committen und pushen, den PR erstellen und nach erfolgreichen Checks und erforderlichen Reviews mergen?“ Das ist ein Beispiel, keine aktuelle Freigabeanfrage. Eine Teilfreigabe erlaubt nur die genannten Schritte.

## Ausführen und fortsetzen

Der Host führt Git und GitHub aus; der lokale Helfer hält Plan, Freigabe und belegte Schritte fest und legt mit start-branch ausschließlich den freigegebenen lokalen Feature-Branch an. Im PR-Modus endet Publish beim beobachteten Merge. Keine Versionsauswahl, Tags, Releases oder Katalogpromotion. Bei Fehlern bleibt der erreichte Stand sichtbar; geänderte Inhalte brauchen neue Prüfung und Freigabe. Journals liegen außerhalb von Quelle und Installation. Alte Release-Journals lassen sich nicht im neuen Ablauf fortsetzen.

## Grenzen

GitHub-Zugriff und geeignete Host-Werkzeuge sind nötig. GitLab-MRs sind noch nicht integriert. Branch-Regeln und erforderliche Reviews bleiben verbindlich. Ein neues Plugin wird zuerst in seinem Repository veröffentlicht, anschließend sein Eintrag im separaten Marketplace; bestehende Nutzer müssen gegebenenfalls synchronisieren. Der vollständige Live-Publish-Ablauf ist noch nicht separat abgenommen.

[Usage](usage.md) · [Installation](installation.md)

Plugin und Marketplace erhalten eigene Pläne und Journale. Neue oder geänderte externe Quellen erfordern im Marketplace-Plan `dependencies` mit beobachteter Repository-URL, vollständigem Commit-Hash und Nachweis. Ein fehlgeschlagener Plugin-Schritt blockiert die abhängige Marketplace-Veröffentlichung. Der Helfer prüft Nachweisfelder; der Agent muss den tatsächlichen GitHub-Stand prüfen.

## Erstveröffentlichung ohne HEAD

Für Plugin- und Marketplace-Repositories gibt es einen ausdrücklich gewählten Modus `publication_mode: "initial"`. Er setzt einen lokalen Stand ohne ersten Commit und ein nachweislich leeres Remote ohne Branches voraus. Der konkrete Plan enthält Dateiauswahl, erste Commit-Nachricht, bestätigten Default-Branch, Repository, Prüfungen und `remote_empty_evidence`. Die Freigabe muss ausdrücklich den ersten Commit und direkten Push ohne PR abdecken; zusätzlich ist `--confirm-initial-publication` erforderlich. Vorbereitung und Freigabe erzeugen selbst keinen Commit.

Nach Freigabe werden leerer Remote-Zustand und Branch-Regeln erneut geprüft, der erste Commit erstellt, ohne Force gepusht und der tatsächliche Remote-Inhalt geprüft. Der Abschluss heißt `published`. Erfordert der Host einen bereits vorhandenen Basisbranch oder verbietet Regeln zufolge den direkten Push, wird gestoppt; es gibt keinen ungefragten Seed-Commit. Reguläre PR-Pläne benötigen `base_commit` und `base_evidence` für einen vorhandenen Remote-Basisbranch. Spätere Änderungen verwenden den PR-Ablauf.

Schema-4-Journale binden auch das Vorhandensein und den Inhalt von `.codex-plugin/plugin.json`. Hinzufügen, Ändern oder Entfernen macht eine Freigabe ungültig, auch außerhalb der ausgewählten Dateien. Schema-1/2/3-Journale benötigen einen neuen Plan und eine neue Freigabe.

## Regulärer Feature-Branch und Rechte

Vorbereitung → konkrete Freigabe → Branch → Commit → Push → PR → Checks → Merge. Der Manager schlägt einen aussagekräftigen Namen wie `improve-marketplace-setup` vor, ohne claude/ oder codex/. Der Plan bindet diesen Namen sowie den beobachteten `default_branch`; Default- und Basisbranch sind als Feature-Branch ausgeschlossen. Erst nach Freigabe legt `start-branch` den Branch an. Bei Wiederaufnahme wird derselbe überprüfte Branch anhand des Journals weiterverwendet; Namenskollisionen, fehlende Branches oder abweichende Heads stoppen den Ablauf. `check-before-commit` verlangt den aktiven genehmigten Branch. Der separat freizugebende Bootstrap bleibt die einzige Ausnahme für vollständig leere Repositories.

Git und Python 3.10+ sind für die Verwaltungswerkzeuge erforderlich; Make ist nur ein Komfortzugang. Für die Verwaltung wird die Host-CLI nur bei automatischer lokaler Installation/Aktualisierung benötigt; ausdrücklich gestartete Modelltests benötigen ebenfalls eine authentifizierte CLI. Publish verwendet einen ausreichend leistungsfähigen GitHub-Connector oder alternativ authentifiziertes gh; keine GitLab-MRs. Vorher Remote-Lesen, Push, PR-Erstellung/-Lesen, Checks, Regeln und kontrolliertes Mergen samt Rechten prüfen. Fehlende Fähigkeiten konkret melden, keine Werkzeuge automatisch installieren. Keine zusätzlichen Python-Pakete, Release-Actions oder Versions-/Tag-Pflichten.

Der Plan enthält `provider` und Nachweise in `capabilities`; der Helfer meldet fehlende Fähigkeiten einzeln. Der Agent prüft die tatsächlichen Rechte und Werkzeuge, ohne schreibende Testaktionen. [Kanonische Voraussetzungen](../../skills/_shared/references/prerequisites.md).
