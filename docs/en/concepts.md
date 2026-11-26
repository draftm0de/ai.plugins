# 💡 Concepts

[Deutsch](../de/concepts.md) | **English**

[Home](../../README.en.md) · [Installation](installation.md) · [Concepts](concepts.md) · [Development](development.md)

Claude and ChatGPT can do a lot: write texts, answer questions, explain code, collect ideas. What they do not know is how *you* or your company want a particular task done. Which steps belong to it? What needs care? What should the result look like?

That is exactly what you teach them with extensions. Nothing is retrained. The assistant gets instructions and, where needed, tools, and follows them for the fitting task. Three terms build on each other here:

| Term | The question behind it | In everyday life |
| --- | --- | --- |
| 🏬 **Marketplace** | Where do I find extensions? | the app store |
| 📦 **Plugin** | What do I install? | an app |
| 📋 **Skill** | How is a task done? | a work instruction |

## Marketplace

> **The place where you find extensions.**

A marketplace is a directory, much like an app store. It tells you which extensions exist, what they are meant for and where they come from. You add it once in your app or on the command line. After that you install what you need from it, and get newer states later in the same way.

The marketplace itself does no tasks. It only offers. It does not have to be public either: a company can run its own internal marketplace so that everyone in the team works with the same extensions. Before you add one, look at who offers it, because an extension works with your content.

## Plugin

> **The package you install.**

A plugin bundles everything that belongs to one field of work: one or more skills, plus the templates, knowledge or small programs they need. So you do not install every instruction on its own but the whole package at once.

A plugin can be very small and solve exactly one task. It can also cover a whole field of work, with several skills that fit together. When you no longer need it, you remove it, and the assistant works as before.

## Skill

> **The work instruction for one task.**

A skill is comparable to a work instruction for a new employee. It describes what to do, in which order and by which rules. It can also say when to ask back and what must never happen, for example: show first, change only after your yes.

The gain lies in repetition. What you have described well once, you do not have to explain again every time. And everyone who uses the same skill gets the same process.

### An example

Imagine a plugin that supports you with job applications:

```text
Marketplace
└── Plugin "Career"
    ├── Skill "CV"
    └── Skill "Interview training"
```

You install the plugin once and have both skills. The skill "Interview training" could say, for example: read the job posting, take your experience into account, ask only one question at a time, rate your answer and suggest an improvement.

<hr>

This page is created automatically by `/plugin-manager:docs`. Do not edit it by hand.
