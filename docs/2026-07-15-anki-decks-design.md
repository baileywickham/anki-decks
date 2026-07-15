# Anki Decks Repo — Design

Date: 2026-07-15. Approved by Bailey in-session.

## Purpose

Version-controlled source of truth for Bailey's Anki decks (interview prep +
ML/math coursework). Content lives as readable YAML in a private GitHub repo;
a build script produces `.apkg` files that are imported into desktop Anki and
synced to phone via AnkiWeb.

## Layout

```
anki-decks/
├── decks/
│   ├── interview-prep/   # process.yaml, llm-serving.yaml, python-fluency.yaml, values.yaml
│   └── ml-math/          # jax.yaml, …
├── build.py              # genanki builder
├── dist/                 # built .apkg files (gitignored)
└── docs/                 # this design doc
```

## Card source format

Each YAML file declares its full Anki deck name and a list of cards:

```yaml
deck: Interview Prep::LLM Serving
cards:
  - id: kv-cache-01          # permanent — never change once reviews exist
    type: basic              # basic | cloze | code
    front: What dominates GPU memory in LLM serving?
    back: The KV cache.
    tags: [llm-serving]
  - id: prefill-decode-01
    type: cloze
    text: "Prefill is {{c1::compute}}-bound; decode is {{c2::memory-bandwidth}}-bound."
  - id: heapq-smallest-01
    type: code
    front: Get the k smallest items from a list.
    back: |
      import heapq
      heapq.nsmallest(k, xs)
```

## Stability guarantees (the important part)

- **Note GUID** = `genanki.guid_for(deck_name, card_id)` — re-importing an
  updated `.apkg` edits notes in place; review scheduling is never reset.
- **Model IDs** and **deck IDs** are fixed constants / stable hashes.
- Consequence: never rename a deck or change a card `id` casually — that
  creates duplicates on import. Edit fields freely; they update in place.

## Build & workflow

`uv run build.py` → one `.apkg` per top-level deck in `dist/`.
Import via File → Import in desktop Anki → Sync → AnkiWeb → phone.

## Note models

Three custom models with fixed IDs: Basic (front/back), Cloze, Code
(front prompt / monospace pre-formatted back).

## Out of scope (for now)

Real card content — Bailey will say when to start authoring. Only sample
cards to verify the import/update round-trip ship initially. AnkiConnect
push and media support are possible later extensions.
