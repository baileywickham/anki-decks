# /// script
# requires-python = ">=3.11"
# dependencies = ["genanki>=0.13", "pyyaml>=6"]
# ///
"""Push YAML card sources into a running Anki via AnkiConnect, then sync.

Usage: uv run push.py

Upserts every card in decks/**/*.yaml into the live collection, keyed by the
hidden AD-ID field ("<deck name>/<card id>"). Never deletes: notes that exist
in repo-managed decks but not in the YAML are reported for manual review.
If Anki isn't running (or AnkiConnect isn't installed), falls back to
building .apkg files and printing import instructions.
"""

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request

import build

ANKICONNECT_URL = "http://localhost:8765"


def invoke(action: str, **params):
    payload = json.dumps({"action": action, "version": 6, "params": params}).encode()
    with urllib.request.urlopen(urllib.request.Request(ANKICONNECT_URL, payload), timeout=30) as r:
        resp = json.load(r)
    if resp.get("error"):
        sys.exit(f"error: AnkiConnect {action}: {resp['error']}")
    return resp["result"]


def anki_available() -> bool:
    try:
        urllib.request.urlopen(ANKICONNECT_URL, timeout=2)
        return True
    except (urllib.error.URLError, OSError):
        return False


def ensure_anki_running() -> bool:
    if anki_available():
        return True
    if sys.platform == "darwin":
        print("Anki not running - launching it...")
        subprocess.run(["open", "-a", "Anki"], check=False)
        for _ in range(30):
            time.sleep(1)
            if anki_available():
                return True
    return False


def ensure_models() -> None:
    existing = set(invoke("modelNames"))
    for key, model in build.MODELS.items():
        field_names = [f["name"] for f in model.fields]
        if model.name not in existing:
            invoke(
                "createModel",
                modelName=model.name,
                inOrderFields=field_names,
                css=build.CSS,
                isCloze=(key == "cloze"),
                cardTemplates=[
                    {"Name": t["name"], "Front": t["qfmt"], "Back": t["afmt"]}
                    for t in model.templates
                ],
            )
            print(f"created note model {model.name!r}")
        else:
            # Models imported from pre-AD-ID .apkg builds lack the AD-ID field.
            missing = [f for f in field_names if f not in invoke("modelFieldNames", modelName=model.name)]
            for f in missing:
                invoke("modelFieldAdd", modelName=model.name, fieldName=f, index=len(field_names) - 1)
                print(f"added field {f!r} to model {model.name!r}")


def push() -> None:
    decks = list(build.iter_decks())  # exits on duplicate ids
    ensure_models()

    added = updated = unchanged = 0
    yaml_ids = set()
    for deck_name, cards in decks:
        invoke("createDeck", deck=deck_name)
        for card in cards:
            model, fields = build.render_fields(deck_name, card)
            aid = fields["AD-ID"]
            yaml_ids.add(aid)
            tags = card.get("tags", [])
            note_ids = invoke("findNotes", query=f'"AD-ID:{aid}"')
            if not note_ids:
                nid = invoke(
                    "addNote",
                    note={
                        "deckName": deck_name,
                        "modelName": model.name,
                        "fields": fields,
                        "tags": tags,
                        "options": {"allowDuplicate": True},
                    },
                )
                # Anki 26 + AnkiConnect ignores deckName on addNote; place explicitly.
                invoke("changeDeck", cards=invoke("findCards", query=f"nid:{nid}"), deck=deck_name)
                added += 1
                continue
            if len(note_ids) > 1:
                sys.exit(f"error: multiple notes claim AD-ID {aid!r}: {note_ids} — fix in Anki first")
            (info,) = invoke("notesInfo", notes=note_ids)
            current = {name: v["value"] for name, v in info["fields"].items()}
            if current == fields and sorted(info["tags"]) == sorted(tags):
                unchanged += 1
                continue
            invoke("updateNote", note={"id": note_ids[0], "fields": fields, "tags": tags})
            updated += 1

    # Orphans: repo-managed notes (they carry an AD-ID) no longer in the YAML.
    # Scan the whole collection, not just decks present in the YAML — otherwise
    # deleting an entire deck file hides its orphans.
    orphans = []
    for nid in invoke("findNotes", query='"AD-ID:_*"'):
        (info,) = invoke("notesInfo", notes=[nid])
        aid = info["fields"].get("AD-ID", {}).get("value", "")
        if aid and aid not in yaml_ids:
            orphans.append(aid)

    print(f"pushed: {added} added, {updated} updated, {unchanged} unchanged")
    if orphans:
        print("\nWARNING: notes in Anki but no longer in YAML (never auto-deleted):")
        for aid in orphans:
            print(f"  - {aid}")
        print("Delete them in Anki (Browse > search the AD-ID) if removal was intended.")

    try:
        invoke("sync")
        print("AnkiWeb sync triggered.")
    except SystemExit as e:
        print(f"note: sync skipped ({e}). Log into AnkiWeb in Anki, or sync manually.")


def main() -> None:
    if not ensure_anki_running():
        sys.exit(
            "error: AnkiConnect unreachable. Ensure Anki is installed and has the\n"
            "AnkiConnect add-on (code 2055492159), then re-run.\n"
            "Do NOT import dist/*.apkg into a collection push.py has already managed --\n"
            "GUIDs won't match and every note would be duplicated."
        )
    push()


if __name__ == "__main__":
    main()
