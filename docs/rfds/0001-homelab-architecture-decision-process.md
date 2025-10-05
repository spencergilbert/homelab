# RFD 0001: Homelab Architecture Decision Process

<!-- RFD-META
Status: Accepted
Date: 2025-10-05
Author: spencergilbert
-->

---

## Overview

This RFD establishes a lightweight, written process for documenting architectural decisions in the homelab.
It defines how RFDs are created, structured, and maintained — ensuring decisions are recorded, discoverable, and reviewable over time.

---

## Problem

As the homelab evolves, decisions around hardware, networking, automation, and service design become increasingly interconnected.
Without durable documentation, context is lost — future changes risk undoing prior work or repeating old mistakes.
A simple, durable process is needed to preserve design reasoning without introducing unnecessary overhead.

---

## Discussion

This process draws inspiration from Oxide Computer’s RFDs, which emphasize thoughtful design discussions written in clear prose.
Each RFD should be a self-contained text document — version-controlled, numbered, and easily readable in plain text.

**Core principles**

* **Write for your future self.** Capture *why*, not just *what*.
* **Favor prose over rigidity.** These are working documents, not formal specifications. Write in narrative, conversational prose — explain your thinking like you're talking to a colleague. Use "I" or "we". Say what's interesting about an approach, what concerns you had, what tradeoffs you considered. The goal is to preserve the *thinking*, not just the conclusion.
* **Keep it lightweight.** Use git for history and review; avoid unnecessary tooling lock-in.
* **Make discovery easy.** Every RFD is numbered, linked, and indexed for reference.

Oxide's RFDs demonstrate this balance well — they're written as design discussions that explain the reasoning process, alternatives considered, and why certain tradeoffs made sense at the time. This approach preserves context that's otherwise lost when decisions are documented as bullet points or commit messages.

---

## Proposed Direction

As the foundational RFD, this document bootstraps the process by defining it. Once accepted, all subsequent RFDs follow this process.

### Organization and Format

RFDs live in a dedicated directory (like `docs/rfds/`) where they can be easily found and indexed. The naming scheme is straightforward: a four-digit number followed by a descriptive title in kebab-case — something like `0002-network-topology.md`. This keeps them sequentially organized while making the content obvious at a glance. Tooling should handle the numbering so you don't have to think about it.

All RFDs use Markdown for consistency and ease of presentation. If needs change over time, we can evolve to a different standard format, but consistency within the collection is important.

### Metadata and Status

Each RFD begins with a structured comment block that captures essential metadata:

```
<!-- RFD-META
Status: Draft
Date: YYYY-MM-DD
Author: username
-->
```

This metadata is machine-readable (for indexing and tooling) while staying out of the way when reading the document. Additional fields can be added over time as needs emerge.

RFDs progress through a simple lifecycle: `Draft` while being actively written or discussed, `Accepted` when the direction is agreed upon and ready for implementation, `Superseded` if replaced by a later RFD (which should reference the old one), or `Rejected` if considered but not adopted.

In this repo, RFDs are approved by the maintainer when confident in the direction. Implementation may precede or follow acceptance depending on the decision's nature — sometimes you need to build something to validate the approach, other times the design is solid enough to accept before implementation.

### Structure and Content

RFDs should include clear sections for context, discussion, and outcome. The structure used in this document — Overview, Problem, Discussion, Proposed Direction, Outcome — works well as a default, but it's not a rigid requirement. Some decisions might need different sections to tell their story clearly.

What's important is writing in declarative voice, as if describing the final form, regardless of current status. This makes RFDs easier to read and understand — you're not constantly translating "we will do X" versus "we are doing X" based on status changes.

### When to Write an RFD

When to write an RFD is a judgment call. If a decision has lasting architectural impact, or if you'll want to remember *why* you made a choice six months from now, document it. Hardware selection, network topology changes, service architecture, automation strategy — these warrant RFDs. Routine configuration tweaks or package updates probably don't.

### Discovery and Creation

A canonical index of all RFDs must be maintained for easy discovery. The index should be reproducible — whether it's generated manually, by script, or through automation may evolve over time, but there needs to be a reliable way to find what exists.

New RFDs should originate from a shared template that reflects the current structure and metadata expectations. The mechanism for creating RFDs (manual copying, scripts, tooling) may change, but the resulting documents need to remain consistent and readable.

---

## Outcome

The RFD process is adopted as the primary mechanism for recording architectural and technical decisions in the homelab.
All future changes with lasting impact — hardware selection, service topology, automation strategy, or architectural experiments — should have an associated RFD.

This document serves as the canonical process definition and a style guide for subsequent RFDs.

---

## References

* Oxide RFDs: [https://rfd.shared.oxide.computer/](https://rfd.shared.oxide.computer/)
* ADR GitHub Template Collection: [https://github.com/joelparkerhenderson/architecture_decision_record](https://github.com/joelparkerhenderson/architecture_decision_record)
* Michael Nygard — "Documenting Architecture Decisions": [https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions.html](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions.html)

