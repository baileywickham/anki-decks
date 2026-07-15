# anki-decks

Version-controlled Anki deck sources. YAML in `decks/` is the source of
truth; `build.py` compiles it to `.apkg` files you import into desktop Anki,
which syncs everywhere via AnkiWeb.

## Usage

```sh
uv run build.py            # writes dist/*.apkg (one per top-level deck)
```

Then in desktop Anki: **File → Import** each changed `.apkg`, then **Sync**.
Re-importing updates existing cards in place — review scheduling is preserved.

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
