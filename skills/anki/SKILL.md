---
name: anki
description: Use when asked to create, add, edit, or remove Anki flashcards or decks — "make me cards about X", "add this to my Anki", or any spaced-repetition/memorization request.
---

# Anki Cards

Bailey's Anki cards live as YAML in the private repo at `~/workspace/anki-decks`
(github.com/baileywickham/anki-decks). The YAML is the source of truth;
`push.py` upserts it into live desktop Anki via AnkiConnect and syncs to his
phone via AnkiWeb. Always go through the repo — never add or edit notes
directly via AnkiConnect, AppleScript, or the Anki UI.

## Workflow — a card change is these four steps, in order

1. `cd ~/workspace/anki-decks && git pull`
   (if the directory is missing: `git clone git@github.com:baileywickham/anki-decks.git ~/workspace/anki-decks`)
2. Add or edit YAML under `decks/` (format below).
3. `uv run push.py` — launches Anki if needed, upserts changed cards, triggers
   AnkiWeb sync. Read its output: report the added/updated counts and relay any
   orphan warnings to Bailey verbatim.
4. `git add -A && git commit && git push` — git history is the audit trail of
   every card change across sessions. A push into Anki without a git commit is
   an unfinished job, whether or not Bailey asked for a commit.

## Card format

One YAML file per subdeck:

```yaml
deck: Interview Prep::LLM Serving   # `::` creates subdecks
cards:
  - id: kv-cache-01     # permanent kebab-case slug — never change once pushed
    type: basic         # basic | cloze | code
    front: What dominates GPU memory in LLM serving?
    back: The KV cache.
    tags: [llm-serving]
```

Types: `basic` (front/back) · `cloze` (`text` with `{{c1::…}}`, optional
`extra`) · `code` (`front` prompt, `back` verbatim code, rendered monospace).

## Invariants

- Never change a card's `id` or a file's `deck:` name once pushed — Anki sees
  a new note and duplicates it.
- Never delete notes from Anki. Removing a card from YAML only makes push.py
  flag an orphan; deletion is Bailey's call, in the Anki UI.
- Only touch decks defined in this repo. Decks Bailey made by hand in Anki are
  off limits.
- Never import `dist/*.apkg` into his main collection — push.py manages it and
  GUIDs won't match, so an import duplicates every note. `.apkg` (via
  `uv run build.py`) is only for bootstrapping a brand-new collection.

## Authoring good cards

- One fact per card. Prefer `cloze` for dense factual sentences, `code` for
  Python idioms, `basic` for definitions and "why" questions.
- Grep existing YAML for the topic first; edit near-duplicates instead of
  adding parallel cards.
- ids: topic slug + counter (`prefill-decode-01`), unique within the deck.
