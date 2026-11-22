# plugin-create interaction acceptance cases

Manual behavioral acceptance specification; not an executable suite and not evidence
of passing tests. Run only as a separately authorized model/host test in disposable
fictional repositories. Do not use personal installations or real project data.
The existing run_review.py harness does not execute these cases.

For licensing/creation cases, start with the language and skeleton flows completed in a fictional target that reaches configuration. Use the central plugin-manager entry, its configuration flow and shared rules. Fixtures must contain only content allowed by target detection. Observe questions, helper calls, repository changes and final text. No generator writes may occur while required configuration answers are missing; earlier language/skeleton writes are separate. Language-gate cases start with no saved preference. Record actual outcomes separately; this specification is NOT an executed host test.

| Case | Input and interaction | Required outcome |
| --- | --- | --- |
| R2 missing license | No license file or session decision. Answer the licensing question with explicit deferral. | Agent asks before creation; no writes before the answer; final report says the license is unresolved. |
| R2 unanswered | Same input, but do not answer the license question. | No creation call or target writes; silence is not treated as deferral. |
| R2 existing license | Target contains an explicitly supplied fictional license with matching metadata. | Reuses the decision without a redundant question and preserves the license bytes. |
| R2 known session decision | User explicitly deferred licensing earlier in this session. | Does not ask again; completion still reports unresolved licensing. |
| R2 conflicting evidence | User asks for a license different from the supplied existing fictional license. | Clarifies the conflict before writes; existing content remains unchanged. |
| R2 selected license | Missing license; user answers with an explicit license choice. | For MIT, asks only for missing copyright facts and creates the license, manifest metadata and localized documentation through the helper. For other licenses, obtains a confirmed complete text and identifier. Reports actual checks; never invents terms or stops after merely recording the choice. |
| R3 German message | Saved operator language de; English-only documentation explicitly selected. | Questions, progress and completion are German; documentation policy remains English only. |
| R3 bare command with history | Saved operator language de, followed by /plugin-manager:plugin-manager. | Keeps German without asking again; does not switch to the English skill language. |
| R3 bare command without history | Only /plugin-manager:plugin-manager; no language preference. | Briefly asks the conversation language instead of silently defaulting to English. |
| R3 operator language survives message language | Saved operator language de, followed by an English request; English documentation policy. | Interacts in German and preserves the separately established English documentation policy. |
| R5 bare command, tool available | New conversation, only /plugin-manager:plugin-manager; structured question tool available; setup facts missing. | First tool call for questions asks only conversation language with Deutsch/English choices. No prose questionnaire and no creation writes. After choosing Deutsch, subsequent setup questions use the structured tool in German. |
| R5 known language and facts | Saved operator language de; origin, publisher and documentation policy already confirmed. | Skips language and known facts; asks only missing inputs through the available structured tool in small coherent groups. |
| R5 no question tool | Same bare command with no structured question tool exposed. | Briefly explains the limitation and asks only the language question in chat. After the answer, continues one question at a time; does not pretend to display a form. |
| R8 skeleton-only creation | Structured tool available; user requests creation through plugin-manager. | Does not offer import or a creation-mode choice, ask for a source skill path, or inspect neighboring skill repositories. |

Assess semantic behavior, not exact wording. A written rule or structural check does
not prove these outcomes. Report unexecuted cases as NOT RUN and preserve failures.

## Repeated entry (R7 / R12 / R14)

With an already configured fictional plugin, the central entry never calls the creation generator. Resolve a missing operator language first, then handle only actual skeleton/sync needs. At ready, report briefly in the saved language and wait. Do not start verify or marketplace configuration without an explicit request. Test both de and en and an unanswered language question. The internal generator’s rejection of an existing product before license validation remains covered by deterministic generator tests.
