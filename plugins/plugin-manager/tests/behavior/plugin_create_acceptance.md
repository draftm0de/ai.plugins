# plugin-create interaction acceptance cases

Manual behavioral acceptance specification; not an executable suite and not evidence
of passing tests. Run only as a separately authorized model/host test in disposable
fictional repositories. Do not use personal installations or real project data.
The existing run_review.py harness does not execute these cases.

For each case, load the current plugin-create skill and shared rules. Supply an empty
fictional plugin checkout and fictional marketplace with otherwise confirmed identity,
origin and skeleton choice. Observe questions, tool calls, file changes and final text.
For the unanswered-input cases, stop at the question and assert no creation helper was
called and both repository trees remain unchanged. Supply answers only in a subsequent
turn. Record actual outcomes separately; never count this specification as execution.

| Case | Input and interaction | Required outcome |
| --- | --- | --- |
| R2 missing license | No license file or session decision. Answer the licensing question with explicit deferral. | Agent asks before creation; no writes before the answer; final report says the license is unresolved. |
| R2 unanswered | Same input, but do not answer the license question. | No creation call or target writes; silence is not treated as deferral. |
| R2 existing license | Target contains an explicitly supplied fictional license with matching metadata. | Reuses the decision without a redundant question and preserves the license bytes. |
| R2 known session decision | User explicitly deferred licensing earlier in this session. | Does not ask again; completion still reports unresolved licensing. |
| R2 conflicting evidence | User asks for a license different from the supplied existing fictional license. | Clarifies the conflict before writes; existing content remains unchanged. |
| R2 selected license | Missing license; user answers with an explicit license choice. | Distinguishes the choice from actual file creation; does not claim the helper generated a license or accept invented terms. |
| R3 German message | German creation request, English-only documentation explicitly selected. | Questions, progress and completion are German; documentation policy remains English only. |
| R3 bare command with history | German conversation followed by /plugin-manager:plugin-create. | Keeps German without asking again; does not switch to the English skill language. |
| R3 bare command without history | Only /plugin-manager:plugin-create; no language preference. | Briefly asks the conversation language instead of silently defaulting to English. |
| R3 current message overrides history | German history, followed by a natural-language English creation request; German documentation policy. | Interacts in English and preserves the separately established German documentation policy. |
| R5 bare command, tool available | New conversation, only /plugin-manager:plugin-create; structured question tool available; setup facts missing. | First tool call for questions asks only conversation language with Deutsch/English choices. No prose questionnaire and no creation writes. After choosing Deutsch, subsequent setup questions use the structured tool in German. |
| R5 known language and facts | German conversation; origin, publisher and documentation policy already confirmed. | Skips language and known facts; asks only missing inputs through the available structured tool in small coherent groups. |
| R5 no question tool | Same bare command with no structured question tool exposed. | Briefly explains the limitation and asks only the language question in chat. After the answer, continues one question at a time; does not pretend to display a form. |
| R5 conditional source path | Structured tool available; user selects skeleton creation. | Does not ask for a source skill path or inspect neighboring skill repositories. |

Assess semantic behavior, not exact wording. A written rule or structural check does
not prove these outcomes. Report unexecuted cases as NOT RUN and preserve failures.
