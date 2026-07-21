# anki-decks

YAML-sourced Anki cards plus the tooling that pushes them into live Anki
(AnkiConnect) and syncs to AnkiWeb. See `skills/anki/SKILL.md` for the card
workflow and invariants — that skill is the contract; follow it.

## This repo is also a published Claude Code plugin

The repo doubles as the `anki` plugin: `.claude-plugin/plugin.json` +
`skills/anki/SKILL.md`. It is listed in Bailey's public marketplace repo
(github.com/baileywickham/claude-plugins) with `source: github:baileywickham/anki-decks`,
so **pushing to main here IS publishing** — installs and updates pull from
this repo directly. The repo is public; everything in it (cards included) is
visible to anyone.

Users install with:

```
/plugin marketplace add baileywickham/claude-plugins
/plugin install anki@baileywickham
```

## Publishing a skill or tooling change

1. Edit `skills/anki/SKILL.md` and/or the scripts. For skill edits, follow
   superpowers:writing-skills (baseline the failure, verify with a subagent).
2. Bump `version` in `.claude-plugin/plugin.json` (semver: tooling or skill
   behavior change = minor, typo = patch).
3. Sync Bailey's local live copy — the skill loads from
   `~/.claude/skills/anki/SKILL.md` in his sessions, not from the plugin:
   `cp skills/anki/SKILL.md ~/.claude/skills/anki/SKILL.md`
4. Commit and push to main. No marketplace-repo change needed unless the
   plugin's name/description/keywords change (those live in
   claude-plugins/.claude-plugin/marketplace.json).

## Known gap before promoting widely

`SKILL.md` is Bailey-specific (his repo path, his GitHub remote). A stranger
installing the plugin gets instructions pointing at Bailey's card repo.
Genericizing (point the workflow at the user's own clone/fork, parameterize
the path) is required before advertising the plugin beyond personal use.
