# Graph Report - char-finder  (2026-10-16)

## Corpus Check
- 73 files · ~46,626 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 3)

## Summary
- 556 nodes · 546 edges · 51 communities (39 shown, 12 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `53984c25`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Capo Finder — Project Context
- Issue tracker: GitHub
- Triage
- teach/SKILL.md
- Process
- db.py
- Codebase Design
- During the session
- HTML Report Format
- template.sh
- Agent Instructions
- Ask Matt
- Diagnosing Bugs
- Project Instructions for AI Agents
- Steps
- Test-Driven Development
- Process
- writing-for-agents/SKILL.md
- Steps
- wayfinder/SKILL.md
- Migrate to Shoehorn
- Steps
- Scaffold Exercises
- to-spec/SKILL.md
- CODING_RULES.md — AI Development Guidelines for Capo Finder
- Process
- <Questionnaire title>
- writing-shape/SKILL.md
- Beads
- Process
- Sections
- writing-beats/SKILL.md
- Capo Finder Implementation Plan & Monitoring Document
- loop-me/SKILL.md
- Reference
- chief-of-staff/SKILL.md
- hitl-loop.template.sh
- GLOSSARY.md Format
- writing-fragments/SKILL.md
- block-dangerous-git.sh
- implement-spec/SKILL.md
- CREDITS.md

## God Nodes (most connected - your core abstractions)
1. `Capo Finder — Project Context` - 16 edges
2. `run_wizard()` - 12 edges
3. `get_connection()` - 12 edges
4. `Steps` - 9 edges
5. `Triage` - 9 edges
6. `🔥 Algoritma Deal Detection: HBDS (Hedonic-Bayesian Deal Scoring)` - 9 edges
7. `Ask Matt` - 8 edges
8. `Codebase Design` - 8 edges
9. `Diagnosing Bugs` - 8 edges
10. `HTML Report Format` - 8 edges

## Surprising Connections (you probably didn't know these)
- None detected - all connections are within the same source files.

## Import Cycles
- None detected.

## Communities (51 total, 12 thin omitted)

### Community 0 - "Capo Finder — Project Context"
Cohesion: 0.05
Nodes (36): 🔥 Algoritma Deal Detection: HBDS (Hedonic-Bayesian Deal Scoring), 📡 API, 🔐 Authentication, Badge & Threshold, Capo Finder — Project Context, Cold Start & Fallback, 🔄 Data Refresh, 💾 Database Schema (SQLite) (+28 more)

### Community 1 - "Issue tracker: GitHub"
Cohesion: 0.06
Nodes (30): Before exploring, read these, Domain Docs, File structure, Flag ADR conflicts, Use the glossary's vocabulary, Conventions, Issue tracker: GitHub, Pull requests as a triage surface (+22 more)

### Community 2 - "Triage"
Cohesion: 0.06
Nodes (29): Bad agent brief, Behavioral, not procedural, Complete acceptance criteria, Durability over precision, Examples, Explicit scope boundaries, Good agent brief (bug), Good agent brief (enhancement) (+21 more)

### Community 3 - "teach/SKILL.md"
Cohesion: 0.07
Nodes (25): Learning Record Format, Numbering, Optional sections, Supersession, Template, What does _not_ qualify, When to write a learning record, MISSION.md Format (+17 more)

### Community 4 - "Process"
Cohesion: 0.07
Nodes (25): 1. State the question, 2. Isolate the logic in a portable module, 3. Build the shareable HTML file, 4. Hand it over, 5. Capture the answer and the prototype, Anti-patterns, Logic Prototype, Process (+17 more)

### Community 5 - "db.py"
Cohesion: 0.13
Nodes (8): cleanup_old_history(), get_avg_price_by_rarity(), get_connection(), get_headers(), get_lowest_price_by_bucket(), init_db(), save_headers(), save_price_history()

### Community 6 - "Codebase Design"
Cohesion: 0.09
Nodes (21): 1. In-process, 2. Local-substitutable, 3. Remote but owned (Ports & Adapters), 4. True external (Mock), Deepening, Dependency categories, Seam discipline, Testing strategy: replace, don't layer (+13 more)

### Community 7 - "During the session"
Cohesion: 0.09
Nodes (19): ADR Format, Numbering, Optional sections, Template, What qualifies, When to offer an ADR, GLOSSARY.md Format, Rules (+11 more)

### Community 8 - "HTML Report Format"
Cohesion: 0.10
Nodes (18): Call-graph collapse, Candidate card, Cross-section (good for layered shallowness), Diagram patterns, Hand-built boxes-and-arrows (when Mermaid's layout fights you), Header, HTML Report Format, Mass diagram (good for "interface as wide as implementation") (+10 more)

### Community 9 - "template.sh"
Cohesion: 0.22
Nodes (18): ask(), ask_secret(), banner(), _clear(), _existing(), finish(), note(), open_url() (+10 more)

### Community 10 - "Agent Instructions"
Cohesion: 0.12
Nodes (16): Agent Context Profiles, Agent Instructions, Always Do, Beads Issue Tracker, Beads Issue Tracker, CLI, GitNexus — Code Intelligence, Never Do (+8 more)

### Community 11 - "Ask Matt"
Cohesion: 0.12
Nodes (14): Phase boundaries, Primary and secondary sources, The five options, The tree, These are judgement calls, Ask Matt, Codebase health, Context hygiene (+6 more)

### Community 12 - "Diagnosing Bugs"
Cohesion: 0.13
Nodes (14): Completion criterion: a tight loop that goes red, Diagnosing Bugs, Minimise, Non-deterministic bugs, Phase 1: Build a feedback loop, Phase 2: Reproduce + minimise, Phase 3: Hypothesise, Phase 4: Instrument (+6 more)

### Community 13 - "Project Instructions for AI Agents"
Cohesion: 0.13
Nodes (14): Agent Context Profiles, Always Do, Architecture Overview, Beads Issue Tracker, Build & Test, CLI, Conventions & Patterns, GitNexus — Code Intelligence (+6 more)

### Community 14 - "Steps"
Cohesion: 0.15
Nodes (12): 1. Detect package manager, 2. Install dependencies, 3. Initialize Husky, 4. Create `.husky/pre-commit`, 5. Create `.lintstagedrc`, 6. Create `.prettierrc` (if missing), 7. Verify, 8. Commit (+4 more)

### Community 15 - "Test-Driven Development"
Cohesion: 0.15
Nodes (10): Designing for Mockability, When to Mock, Anti-patterns, Rules of the loop, Seams: where tests go, Test-Driven Development, What a good test is, Bad Tests (+2 more)

### Community 16 - "Process"
Cohesion: 0.15
Nodes (12): 1. Gather context, 2. Explore the codebase (optional), 3. Draft vertical slices, 4. Quiz the user, 5. Publish the tickets to the configured tracker, Acceptance criteria, Blocked by, <NN>: <Ticket title> (+4 more)

### Community 17 - "writing-for-agents/SKILL.md"
Cohesion: 0.15
Nodes (11): Context pointers, Information hierarchy, Leading words, Invocation, Router skills, Skill mechanics, Splitting by invocation, Pruning (+3 more)

### Community 18 - "Steps"
Cohesion: 0.17
Nodes (11): 1. Detect the environment, 2. Install dependency-cruiser, 3. Write the config, 4. Wire it into the checks, 5. Scaffold the example package, 6. Prove the rules bite, 7. Document the convention, Notes (+3 more)

### Community 19 - "wayfinder/SKILL.md"
Cohesion: 0.17
Nodes (11): Chart the map, Fog of war, Invocation, Out of scope, Plan, don't do, Refer by name, The Map, The map body (+3 more)

### Community 22 - "Migrate to Shoehorn"
Cohesion: 0.20
Nodes (9): `as Type` → `fromPartial()`, `as unknown as Type` → `fromAny()`, Install, Large objects with few needed properties, Migrate to Shoehorn, Migration patterns, When to use each, Why shoehorn? (+1 more)

### Community 24 - "Steps"
Cohesion: 0.22
Nodes (8): 1. Ask scope, 2. Copy the hook script, 3. Add hook to settings, 4. Ask about customization, 5. Verify, Setup Git Guardrails, Steps, What Gets Blocked

### Community 25 - "Scaffold Exercises"
Cohesion: 0.22
Nodes (8): Directory naming, Example: stubbing from a plan, Exercise variants, Lint rules summary, Moving/renaming exercises, Required files, Scaffold Exercises, Workflow

### Community 26 - "to-spec/SKILL.md"
Cohesion: 0.22
Nodes (8): Further Notes, Implementation Decisions, Out of Scope, Problem Statement, Process, Solution, Testing Decisions, User Stories

### Community 29 - "CODING_RULES.md — AI Development Guidelines for Capo Finder"
Cohesion: 0.22
Nodes (8): 1. 🛡️ Mandatory Skill Rule (`/ponytail`), 2. ⚡ Environment & Package Management (`uv`), 3. 🧮 Data & Math Processing, 4. 🗄️ SQLite Best Practices, 5. 🚀 FastAPI & Async Patterns, 6. 🎨 Frontend & Templates (Jinja2 + Minimal Modern CSS), 7. 🧹 Code Cleanliness & Style, CODING_RULES.md — AI Development Guidelines for Capo Finder

### Community 30 - "Process"
Cohesion: 0.25
Nodes (7): 1. Pin the fixed point, 2. Identify the spec source, 3. Identify the standards sources, 4. Spawn both sub-agents in parallel, 5. Aggregate, Process, Why two axes

### Community 31 - "<Questionnaire title>"
Cohesion: 0.25
Nodes (7): Anything else?, Context, Document structure, How to answer, <Questionnaire title>, <Theme heading>, What load is the system expected to handle at launch?

### Community 32 - "writing-shape/SKILL.md"
Cohesion: 0.25
Nodes (7): Conversational feel, Format arguments to actually have, Grounding, Out of scope, Pulling from the pile, The loop, Writing rhythm

### Community 35 - "Beads"
Cohesion: 0.29
Nodes (6): Beads, Core CLI Workflow, First Step, Preferred Route, Rules, What Belongs In Beads

### Community 36 - "Process"
Cohesion: 0.29
Nodes (6): 1. Scope the procedure, 2. Map each stage's journey, 3. Author the wizard, 4. Verify and hand off, Process, Wizard

### Community 37 - "Sections"
Cohesion: 0.33
Nodes (5): Evidence, Guidance, Merge Danger, Sections, Summary

### Community 38 - "writing-beats/SKILL.md"
Cohesion: 0.33
Nodes (5): Ending the journey, Grounding, Pulling from the pile, What is a beat, Writing rhythm

### Community 39 - "Capo Finder Implementation Plan & Monitoring Document"
Cohesion: 0.33
Nodes (5): Beads Issues Table, Capo Finder Implementation Plan & Monitoring Document, Execution Protocol, Progress Tracker, Project Summary & Architecture

### Community 40 - "loop-me/SKILL.md"
Cohesion: 0.40
Nodes (4): Definition of done, The loop lens, The workspace, Vocabulary

### Community 41 - "Reference"
Cohesion: 0.40
Nodes (4): Files, Implementation vs Review, Reference, Steps

### Community 42 - "chief-of-staff/SKILL.md"
Cohesion: 0.50
Nodes (3): Schedules, Strategic View, Subagents

### Community 43 - "hitl-loop.template.sh"
Cohesion: 0.83
Nodes (3): capture(), hitl-loop.template.sh script, step()

### Community 44 - "GLOSSARY.md Format"
Cohesion: 0.50
Nodes (3): GLOSSARY.md Format, Rules, Structure

### Community 45 - "writing-fragments/SKILL.md"
Cohesion: 0.50
Nodes (3): File format, What is a fragment, Writing rhythm

## Knowledge Gaps
- **351 isolated node(s):** `block-dangerous-git.sh script`, `The five options`, `The tree`, `Primary and secondary sources`, `These are judgement calls` (+346 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 392 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What connects `block-dangerous-git.sh script`, `The five options`, `The tree` to the rest of the system?**
  _351 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Capo Finder — Project Context` be split into smaller, more focused modules?**
  _Cohesion score 0.05405405405405406 - nodes in this community are weakly interconnected._
- **Should `Issue tracker: GitHub` be split into smaller, more focused modules?**
  _Cohesion score 0.05555555555555555 - nodes in this community are weakly interconnected._
- **Should `Triage` be split into smaller, more focused modules?**
  _Cohesion score 0.0625 - nodes in this community are weakly interconnected._
- **Should `teach/SKILL.md` be split into smaller, more focused modules?**
  _Cohesion score 0.06896551724137931 - nodes in this community are weakly interconnected._
- **Should `Process` be split into smaller, more focused modules?**
  _Cohesion score 0.07407407407407407 - nodes in this community are weakly interconnected._
- **Should `db.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13 - nodes in this community are weakly interconnected._