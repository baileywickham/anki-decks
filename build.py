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

# AD-ID holds "<deck name>/<card id>" so push.py can find repo-managed notes
# in a live collection. It is never rendered on cards.
BASIC_MODEL = genanki.Model(
    BASIC_MODEL_ID,
    "AD Basic",
    fields=[{"name": "Front"}, {"name": "Back"}, {"name": "AD-ID"}],
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
    fields=[{"name": "Text"}, {"name": "Extra"}, {"name": "AD-ID"}],
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
    fields=[{"name": "Front"}, {"name": "Back"}, {"name": "AD-ID"}],
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


MODELS = {"basic": BASIC_MODEL, "cloze": CLOZE_MODEL, "code": CODE_MODEL}


def ad_id(deck_name: str, card: dict) -> str:
    return f"{deck_name}/{card['id']}"


def render_fields(deck_name: str, card: dict) -> tuple[genanki.Model, dict[str, str]]:
    """Render a YAML card into its note model and named HTML field values."""
    ctype = card.get("type", "basic")
    if ctype == "basic":
        fields = {"Front": as_html(card["front"]), "Back": as_html(card["back"])}
    elif ctype == "cloze":
        fields = {"Text": as_html(card["text"]), "Extra": as_html(card.get("extra", ""))}
    elif ctype == "code":
        fields = {"Front": as_html(card["front"]), "Back": code_block(card["back"])}
    else:
        raise ValueError(f"{card['id']}: unknown card type {ctype!r}")
    fields["AD-ID"] = ad_id(deck_name, card)
    return MODELS[ctype], fields


def iter_decks():
    """Yield (deck_name, cards) per YAML file, exiting on duplicate card ids."""
    seen: dict[str, Path] = {}
    for path in sorted(DECKS_DIR.rglob("*.yaml")):
        doc = yaml.safe_load(path.read_text())
        for card in doc.get("cards", []):
            key = ad_id(doc["deck"], card)
            if key in seen:
                sys.exit(f"error: duplicate card id: {key} in {path} and {seen[key]}")
            seen[key] = path
        yield doc["deck"], doc.get("cards", [])


def make_note(deck_name: str, card: dict) -> genanki.Note:
    model, fields = render_fields(deck_name, card)
    note = genanki.Note(
        model=model,
        fields=[fields[f["name"]] for f in model.fields],
        tags=card.get("tags", []),
    )
    note.guid = genanki.guid_for(deck_name, card["id"])
    return note


def main() -> None:
    decks: dict[str, genanki.Deck] = {}
    packages: dict[str, list[genanki.Deck]] = defaultdict(list)
    total = 0

    for deck_name, cards in iter_decks():
        if deck_name not in decks:
            decks[deck_name] = genanki.Deck(deck_id(deck_name), deck_name)
            packages[deck_name.split("::")[0]].append(decks[deck_name])
        for card in cards:
            decks[deck_name].add_note(make_note(deck_name, card))
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
