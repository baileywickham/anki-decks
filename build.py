# /// script
# requires-python = ">=3.11"
# dependencies = ["genanki>=0.13", "pyyaml>=6"]
# ///
"""Build .apkg files from the YAML card sources in decks/.

Usage: uv run build.py

One .apkg is written to dist/ per top-level Anki deck (the part of the
`deck:` name before the first `::`). Note GUIDs derive from (deck name,
card id), so re-importing an updated .apkg edits notes in place without
resetting review scheduling. Never rename a deck or change a card id once
reviews exist — that duplicates the note on import.
"""

import hashlib
import html
import sys
from collections import defaultdict
from pathlib import Path

import genanki
import yaml

ROOT = Path(__file__).parent
DECKS_DIR = ROOT / "decks"
DIST_DIR = ROOT / "dist"

# Fixed model IDs — never change these once decks are in circulation.
BASIC_MODEL_ID = 1626061707001
CLOZE_MODEL_ID = 1626061707002
CODE_MODEL_ID = 1626061707003

CSS = """\
.card {
  font-family: -apple-system, "Helvetica Neue", sans-serif;
  font-size: 20px;
  text-align: center;
  color: #1a1a1a;
  background-color: #fdfdfd;
}
pre {
  text-align: left;
  background: #282c34;
  color: #abb2bf;
  padding: 12px 16px;
  border-radius: 8px;
  overflow-x: auto;
}
code { font-family: "SF Mono", Menlo, monospace; font-size: 16px; }
.cloze { font-weight: bold; color: #0b6bcb; }
"""

BASIC_MODEL = genanki.Model(
    BASIC_MODEL_ID,
    "AD Basic",
    fields=[{"name": "Front"}, {"name": "Back"}],
    templates=[{
        "name": "Card 1",
        "qfmt": "{{Front}}",
        "afmt": "{{FrontSide}}<hr id=answer>{{Back}}",
    }],
    css=CSS,
)

CLOZE_MODEL = genanki.Model(
    CLOZE_MODEL_ID,
    "AD Cloze",
    model_type=genanki.Model.CLOZE,
    fields=[{"name": "Text"}, {"name": "Extra"}],
    templates=[{
        "name": "Cloze",
        "qfmt": "{{cloze:Text}}",
        "afmt": "{{cloze:Text}}<br>{{Extra}}",
    }],
    css=CSS,
)

CODE_MODEL = genanki.Model(
    CODE_MODEL_ID,
    "AD Code",
    fields=[{"name": "Front"}, {"name": "Back"}],
    templates=[{
        "name": "Card 1",
        "qfmt": "{{Front}}",
        "afmt": "{{FrontSide}}<hr id=answer>{{Back}}",
    }],
    css=CSS,
)


def deck_id(name: str) -> int:
    """Stable numeric deck ID from the deck name."""
    return int.from_bytes(hashlib.sha256(name.encode()).digest()[:6], "big")


def as_html(text: str) -> str:
    return text.strip().replace("\n", "<br>")


def code_block(code: str) -> str:
    return f"<pre><code>{html.escape(code.strip())}</code></pre>"


def make_note(deck_name: str, card: dict) -> genanki.Note:
    cid = card["id"]
    ctype = card.get("type", "basic")
    tags = card.get("tags", [])
    if ctype == "basic":
        model, fields = BASIC_MODEL, [as_html(card["front"]), as_html(card["back"])]
    elif ctype == "cloze":
        model, fields = CLOZE_MODEL, [as_html(card["text"]), as_html(card.get("extra", ""))]
    elif ctype == "code":
        model, fields = CODE_MODEL, [as_html(card["front"]), code_block(card["back"])]
    else:
        raise ValueError(f"{cid}: unknown card type {ctype!r}")
    note = genanki.Note(model=model, fields=fields, tags=tags)
    note.guid = genanki.guid_for(deck_name, cid)
    return note


def main() -> None:
    decks: dict[str, genanki.Deck] = {}
    packages: dict[str, list[genanki.Deck]] = defaultdict(list)
    seen_guids: dict[str, str] = {}
    total = 0

    for path in sorted(DECKS_DIR.rglob("*.yaml")):
        doc = yaml.safe_load(path.read_text())
        deck_name = doc["deck"]
        if deck_name not in decks:
            decks[deck_name] = genanki.Deck(deck_id(deck_name), deck_name)
            packages[deck_name.split("::")[0]].append(decks[deck_name])
        for card in doc.get("cards", []):
            note = make_note(deck_name, card)
            key = f"{deck_name}/{card['id']}"
            if note.guid in seen_guids:
                sys.exit(f"error: duplicate card id: {key} collides with {seen_guids[note.guid]}")
            seen_guids[note.guid] = key
            decks[deck_name].add_note(note)
            total += 1

    DIST_DIR.mkdir(exist_ok=True)
    for top, deck_list in packages.items():
        out = DIST_DIR / f"{top.replace(' ', '-').lower()}.apkg"
        genanki.Package(deck_list).write_to_file(out)
        n = sum(len(d.notes) for d in deck_list)
        print(f"wrote {out.relative_to(ROOT)}  ({len(deck_list)} decks, {n} notes)")
    print(f"total: {total} notes")


if __name__ == "__main__":
    main()
