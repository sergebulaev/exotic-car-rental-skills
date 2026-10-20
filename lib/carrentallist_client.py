#!/usr/bin/env python3
"""Read-only client for the CarRentalList catalog MCP server.

The skills prefer the MCP connector when the agent has one
(https://mcp.carrentallist.com/mcp added to Claude, ChatGPT, Cursor or Codex).
When it does not, they call this script instead. It speaks the same JSON-RPC
over plain HTTPS POST, so the answers are identical either way.

No key, no account, no dependency beyond the standard library. The server is
public and read-only; it is rate limited per IP, so keep calls to what the task
needs (a market scan is 3 to 6 calls, not 50).

Usage:

    python3 <bundle root>/lib/carrentallist_client.py tools
    python3 lib/carrentallist_client.py price_overview '{"make": "Lamborghini", "city": "Miami"}'
    python3 lib/carrentallist_client.py search_companies '{"city": "Miami", "state": "FL"}'

Prints the tool's text answer (Markdown with carrentallist.com links to cite).
Add --json to print the structured content instead, when the tool returns it.
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

ENDPOINT = "https://mcp.carrentallist.com/mcp"
TIMEOUT = 30
USER_AGENT = "exotic-car-rental-skills/1.0 (+https://github.com/sergebulaev/exotic-car-rental-skills)"

#: The tools the server publishes. scripts/check_tools.py compares the names
#: the skills use against this list, and --live against the server itself.
TOOLS = (
    "search_vehicles",
    "get_company",
    "browse_locations",
    "browse_makes",
    "vehicle_availability",
    "search_companies",
    "price_overview",
    "catalog_highlights",
    "top_companies",
    "search_news",
    "get_news_article",
    "search",
    "fetch",
)


class CatalogError(RuntimeError):
    """The server answered with an error, or could not be reached."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """The endpoint never redirects. If something in between does, stop."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401
        raise CatalogError(f"unexpected redirect {code} to {newurl}")


_OPENER = urllib.request.build_opener(_NoRedirect)


def _rpc(method: str, params: dict | None = None) -> dict:
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "User-Agent": USER_AGENT,
        },
    )
    try:
        with _OPENER.open(req, timeout=TIMEOUT) as res:
            raw = res.read()
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            raise CatalogError("rate limited by the catalog server; wait a minute and retry") from exc
        raise CatalogError(f"HTTP {exc.code} from the catalog server") from exc
    except (urllib.error.URLError, OSError) as exc:  # OSError: timeouts, resets, disconnects
        raise CatalogError(f"catalog server unreachable: {exc}") from exc
    try:
        payload = json.loads(raw.decode("utf-8"))
    except ValueError as exc:  # an HTML error page or a proxy answer, not JSON-RPC
        raise CatalogError("the catalog server returned a non-JSON response") from exc
    if not isinstance(payload, dict):
        raise CatalogError("the catalog server returned an unexpected response")
    error = payload.get("error")
    if error is not None:
        message = error.get("message") if isinstance(error, dict) else str(error)
        raise CatalogError(message or "unknown error")
    result = payload.get("result")
    return result if isinstance(result, dict) else {}


def list_tools() -> list[dict]:
    """The live tool list: name, description and JSON input schema."""
    return _rpc("tools/list").get("tools", [])


def call(tool: str, arguments: dict | None = None) -> dict:
    """Call one tool. Returns the MCP result: content blocks + structuredContent."""
    if tool not in TOOLS:
        raise CatalogError(f"unknown tool {tool!r}; run `tools` to list them")
    result = _rpc("tools/call", {"name": tool, "arguments": arguments or {}})
    if result.get("isError"):
        raise CatalogError(text_of(result) or f"{tool} failed")
    return result


def text_of(result: dict) -> str:
    """The text blocks of a result, joined: what the skill reads and cites."""
    return "\n\n".join(b.get("text", "") for b in result.get("content", []) if b.get("type") == "text")


def main(argv: list[str]) -> int:
    args = [a for a in argv if a != "--json"]
    as_json = len(args) != len(argv)
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    try:
        if args[0] == "tools":
            for t in list_tools():
                required = t.get("inputSchema", {}).get("required", [])
                props = ", ".join(f"{k}{'*' if k in required else ''}" for k in t.get("inputSchema", {}).get("properties", {}))
                print(f"{t['name']}({props})")
            return 0
        arguments = json.loads(args[1]) if len(args) > 1 else {}
        if not isinstance(arguments, dict):
            print("arguments must be a JSON object", file=sys.stderr)
            return 2
        result = call(args[0], arguments)
    except json.JSONDecodeError as exc:
        print(f"arguments are not valid JSON: {exc}", file=sys.stderr)
        return 2
    except CatalogError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if as_json and "structuredContent" in result:
        print(json.dumps(result["structuredContent"], indent=2, ensure_ascii=False))
    else:
        print(text_of(result))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
