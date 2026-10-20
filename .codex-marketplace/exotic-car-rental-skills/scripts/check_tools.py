#!/usr/bin/env python3
"""Every catalog tool a skill names must exist.

The skills tell the agent which CarRentalList MCP tool to call. A tool renamed
on the server, or a typo in a SKILL.md, sends the agent to a call that fails.
This check compares the tool names written in backticks in the skills and
references against lib/carrentallist_client.py TOOLS, and with --live against
the server's own tools/list.

Run from the repo root:

    python3 scripts/check_tools.py          # static
    python3 scripts/check_tools.py --live   # also asks the server (network)
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lib"))
import carrentallist_client as client  # noqa: E402

#: Backticked snake_case words that look like tool names but are arguments,
#: values or file names.
NOT_TOOLS = {
    "priced_only", "max_min_age", "unlimited_miles", "max_deposit", "min_rating",
    "claimed_only", "price_asc", "price_desc", "new_arrivals", "price_drops",
    "price_rises", "most_expensive", "biggest_fleets", "most_reviewed",
    "largest_fleet", "highest_rated", "best_lamborghini", "best_rolls_royce",
    "best_miami", "best_los_angeles", "best_las_vegas", "min_price", "max_price",
    "next_cursor", "plan_exotic_weekend",
    # structured fields of get_company / search_companies (references/catalog-data.md)
    "review_count", "price_history_recent", "as_of", "min_age", "deposit_min", "deposit_max",
    "miles_included", "min_rental_hours", "insurance_required", "checked_at",
}
CALL = re.compile(r"`([a-z]+(?:_[a-z]+)+)`")


def documents():
    yield from sorted((ROOT / "skills").glob("*/SKILL.md"))
    yield from sorted((ROOT / "references").glob("*.md"))
    yield ROOT / "SKILL.md"


def main() -> int:
    known = set(client.TOOLS)
    problems = []
    used = set()
    for path in documents():
        for name in CALL.findall(path.read_text(encoding="utf-8")):
            if name in NOT_TOOLS:
                continue
            used.add(name)
            if name not in known:
                problems.append(f"{path.relative_to(ROOT)}: `{name}` is not a catalog tool")

    if "--live" in sys.argv:
        try:
            live = {t["name"] for t in client.list_tools()}
        except client.CatalogError as exc:
            print(f"live check skipped: {exc}")
            return 2
        for gone in sorted(known - live):
            problems.append(f"lib TOOLS lists {gone}, which the server no longer publishes")
        for new in sorted(live - known):
            problems.append(f"the server publishes {new}, missing from lib TOOLS")

    if problems:
        print("Catalog tools:\n" + "\n".join("  " + p for p in problems))
        return 1
    print(f"OK: the skills name {len(used)} catalog tools, all published"
          + (" (checked live)." if "--live" in sys.argv else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
