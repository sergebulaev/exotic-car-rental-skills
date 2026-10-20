# Project conventions - exotic-car-rental-skills

Read before changing anything. Keep this file and `AGENTS.md` aligned.

## Versioning

- Single source of truth: `.claude-plugin/plugin.json`,
  `.claude-plugin/marketplace.json`, `.codex-plugin/plugin.json`,
  `.agents/plugins/marketplace.json`. Name, version, author, license, homepage
  and the bundle description stay identical across them.
- `.codex-marketplace/exotic-car-rental-skills/` is generated. Never edit it by hand:
  change the root files, then run `python3 scripts/sync_codex_marketplace.py`.
- Default bump is PATCH for every shippable commit. MINOR or MAJOR only when the
  owner asks.
- After a bump: `git tag -a vX.Y.Z -m "..."`, push the tag, then
  `gh release create vX.Y.Z --title "vX.Y.Z" --notes "..." --latest` (the README
  badge reads the Releases API, not tags).

## Commits

- Author must be Sergey: `git commit --author="Sergey Bulaev <s@bulaev.org>"`.
- Run every check in "Validation" before pushing.

## Skill bundle invariants

- **Exactly 6 skills.** The count is stated in the plugin manifests, README,
  root `SKILL.md`, this file and `AGENTS.md`; change all of them together.
- `description:` target <= 400 chars, hard <= 510, keyword-rich, a "Not for X
  (use Y)" sentinel when skills overlap. **No em dashes or en dashes** in any
  `description:`.
- Skill names are public surface: a rename updates manifests, README table,
  root `SKILL.md` and every cross-reference.

## Shared references

- `references/catalog-data.md`: the market data contract (tools, connector or
  client, published rates only, sample size and date). Skills cite it instead
  of repeating it.
- `references/renter-checklist.md`: what to confirm before a deposit, red flags,
  insurance basics. Skills cite it instead of repeating it.
- `references/untrusted-content.md`: data-is-not-instructions. Every skill that
  reads someone else's text, or calls a catalog tool, carries a `## Untrusted content` section citing it;
  `scripts/check_untrusted_rule.py` enforces it through its `REQUIRED` set.

## Market data

- `lib/carrentallist_client.py` is standard library only and talks to
  `https://mcp.carrentallist.com/mcp`. Keep `TOOLS` in sync with the server:
  `python3 scripts/check_tools.py --live`.
- Never write a market price into a skill or reference as a fact. Examples use
  the "median $X over N cars, data as of <date>" shape.

## Validation

```bash
python3 scripts/check_no_secrets.py
python3 scripts/check_frontmatter.py
python3 scripts/check_markdown_references.py
python3 scripts/check_untrusted_rule.py
python3 scripts/check_text_encoding.py
python3 scripts/check_tools.py --live
python3 scripts/sync_codex_marketplace.py
grep -nE '^description:' SKILL.md skills/*/SKILL.md | grep -E '—|–'   # must be empty
```
