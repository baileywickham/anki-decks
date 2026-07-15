# anki-decks

Version-controlled Anki deck sources. YAML in `decks/` is the source of
truth; `build.py` compiles it to `.apkg` files you import into desktop Anki,
which syncs everywhere via AnkiWeb.

## Usage

```sh
uv run push.py             # upserts into live Anki via AnkiConnect + syncs AnkiWeb
```

`push.py` launches Anki if it isn't running, adds/updates cards in place
(matched by the hidden AD-ID field), never deletes (orphans are flagged for
manual review), and triggers an AnkiWeb sync so phones pick the changes up.
Requires the AnkiConnect add-on (code `2055492159`).

`uv run build.py` still produces `dist/*.apkg`, but **only for bootstrapping a
brand-new collection** — never import an `.apkg` into a collection push.py
already manages; the GUIDs won't match and every note gets duplicated.

## Authoring cards

Each `decks/**/*.yaml` file targets one Anki deck:

```yaml
deck: Interview Prep::LLM Serving   # `::` makes subdecks
cards:
  - id: kv-cache-01     # permanent unique id — NEVER change once imported
    type: basic         # basic | cloze | code
    front: What dominates GPU memory in LLM serving?
    back: The KV cache.
    tags: [llm-serving]
```

- `basic`: `front` / `back`
- `cloze`: `text` with `{{c1::…}}` deletions, optional `extra`
- `code`: `front` prompt, `back` is verbatim code (rendered monospace)

## Rules that protect your review history

- Never change a card's `id` or its file's `deck` name once imported —
  Anki sees a brand-new note and you get duplicates.
- Edit `front`/`back`/`text` freely; re-import updates in place.
- Design doc: `docs/2026-07-15-anki-decks-design.md`
