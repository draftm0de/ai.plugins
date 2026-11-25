# Skill standards / Skill-Standards

Managed by the plugin manager and identical in every plugin. Do not edit it here.

## Cut

- One skill per action. The call, not the model, selects the action. A plugin with exactly one skill can be called
  bare (`/plugin`); with several skills every call carries the skill name (`/plugin:skill`).
- With several skills, Claude Code gets one `commands/<skill>.md` per skill; Codex has no command files.
- A skill description names the task and its boundary in one short text. It does not cover several actions.

## Boundaries as structure

- A read-only skill has no path that writes. Publishing never acts without a concrete approval and never commits on its own.
- A skill that changes something shows the consequences first and writes only after an explicit yes, in every plugin.
- A gate and a setup skill belong only to a plugin whose writing skills depend on a state of the person's project
  (a configuration, a prepared folder). Without such a state the plugin has neither; do not invent one.
- With such a state, a writing skill asks a shared gate first. The gate is one read-only script and one flow text that
  every writing skill follows. When the gate is closed the skill stops, writes nothing and points to the one skill that
  sets up.
- That setup skill is exactly one per plugin, brings the project into the configured state, may be called
  repeatedly and runs the open step and nothing else.
- The kind of a repository is never a call argument; it comes from the state of the folder.

## Text

- Every skill loads the operator-language reference before it talks to the person and follows its section "How a skill
  uses the language" (language from the helper only, everything the person reads in it, passed on to scripts that print
  text); the skill text does not repeat these rules. It follows `messages.md` for every failure and stop.
- Skill and flow texts do not duplicate wording that belongs to the message catalogue or to this standard.
- Instruction texts are not product behavior. Test them with contracts and model cases, never as acceptance.
