"""The IncidentDesk MCP server: read-only tools over DemoSoft's incidents and postmortems.

A local (stdio) MCP server with no dependencies beyond the Python standard library, so an agent environment can start
it without installing anything. It serves the export in data/demo/ and needs an IncidentDesk API key in
INCIDENTDESK_API_KEY. In Copilot cloud agent the key comes from the Agents secret COPILOT_MCP_INCIDENTDESK_KEY:

    "incidentdesk": {
      "type": "local",
      "command": "python3",
      "args": ["mcp/incidentdesk_mcp.py"],
      "env": {"INCIDENTDESK_API_KEY": "$COPILOT_MCP_INCIDENTDESK_KEY"},
      "tools": ["*"]
    }

Try it by hand:  INCIDENTDESK_API_KEY=idk_test_... python3 mcp/incidentdesk_mcp.py --check
"""

from __future__ import annotations  # runs on the system Python 3.9 of a Mac, too

import json
import os
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "demo"
SERVER = {"name": "incidentdesk", "version": "1.0.0"}
PROTOCOL = "2025-06-18"


def log(message: str) -> None:
    print(f"incidentdesk-mcp: {message}", file=sys.stderr, flush=True)


def check_key() -> None:
    key = os.environ.get("INCIDENTDESK_API_KEY", "")
    if not key:
        log("INCIDENTDESK_API_KEY is not set. Add the Agents secret COPILOT_MCP_INCIDENTDESK_KEY and map it in the MCP "
            "configuration (env: INCIDENTDESK_API_KEY).")
        sys.exit(1)
    if not key.startswith("idk_") or len(key) < 20:
        log("INCIDENTDESK_API_KEY was rejected: an IncidentDesk key starts with idk_.")
        sys.exit(1)


def load(name: str) -> list[dict]:
    return json.loads((DATA / f"{name}.json").read_text())


def list_incidents(service: str = "", status: str = "", priority: str = "", limit: int = 20) -> list[dict]:
    rows = [i for i in load("incidents")
            if (not service or i["service"] == service) and (not status or i["status"] == status)
            and (not priority or i["priority"] == priority)]
    rows.sort(key=lambda i: i["opened_at"], reverse=True)
    return [{k: v for k, v in i.items() if k != "timeline"} for i in rows[: max(1, min(limit, 100))]]


def get_incident(key: str) -> dict:
    for incident in load("incidents"):
        if incident["key"] == key:
            return incident
    raise LookupError(f"No incident {key}")


def list_postmortems(include_drafts: bool = False) -> list[dict]:
    return [{"key": p["key"], "incident": p["incident"], "title": p["title"], "published_at": p["published_at"]}
            for p in load("postmortems") if include_drafts or p["published_at"]]


def get_postmortem(key: str) -> dict:
    for pm in load("postmortems"):
        if pm["key"] == key:
            return pm
    raise LookupError(f"No postmortem {key}")


def search_postmortems(text: str) -> list[dict]:
    words = text.lower().split()
    found = []
    for pm in load("postmortems"):
        haystack = " ".join(str(pm.get(f) or "") for f in ("title", "summary", "impact", "root_cause")).lower()
        if all(w in haystack for w in words):
            found.append({"key": pm["key"], "title": pm["title"], "root_cause": pm["root_cause"]})
    return found


def schema(properties: dict, required: tuple = ()) -> dict:
    return {"type": "object", "properties": properties, "required": list(required)}


TEXT = {"type": "string"}
TOOLS = {
    "list_incidents": (list_incidents, "List incidents, newest first. Filters are optional.",
                       schema({"service": {**TEXT, "description": "service slug, e.g. login-service"},
                               "status": {**TEXT, "enum": ["open", "acknowledged", "waiting", "resolved"]},
                               "priority": {**TEXT, "enum": ["P1", "P2", "P3", "P4"]},
                               "limit": {"type": "integer", "minimum": 1, "maximum": 100}})),
    "get_incident": (get_incident, "One incident with its timeline, by key (INC-4821).",
                     schema({"key": TEXT}, ("key",))),
    "list_postmortems": (list_postmortems, "List postmortems; drafts only when asked.",
                         schema({"include_drafts": {"type": "boolean"}})),
    "get_postmortem": (get_postmortem, "One postmortem by key (PM-117): summary, impact, root cause, actions.",
                       schema({"key": TEXT}, ("key",))),
    "search_postmortems": (search_postmortems, "Postmortems whose text contains every word of the query.",
                           schema({"text": TEXT}, ("text",))),
}


def handle(request: dict) -> dict | None:
    method, params = request.get("method"), request.get("params") or {}
    if method == "initialize":
        result = {"protocolVersion": params.get("protocolVersion", PROTOCOL), "capabilities": {"tools": {}},
                  "serverInfo": SERVER}
    elif method == "tools/list":
        result = {"tools": [{"name": n, "description": d, "inputSchema": s, "annotations": {"readOnlyHint": True}}
                            for n, (_, d, s) in TOOLS.items()]}
    elif method == "tools/call":
        name = params.get("name")
        if name not in TOOLS:
            return {"jsonrpc": "2.0", "id": request.get("id"), "error": {"code": -32602, "message": f"Unknown tool {name}"}}
        try:
            data = TOOLS[name][0](**(params.get("arguments") or {}))
            result = {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False)}]}
        except (LookupError, TypeError) as e:
            result = {"content": [{"type": "text", "text": str(e)}], "isError": True}
        log(f"{name} {json.dumps(params.get('arguments') or {})}")
    elif method == "ping":
        result = {}
    elif "id" not in request:
        return None  # a notification, e.g. notifications/initialized
    else:
        return {"jsonrpc": "2.0", "id": request["id"], "error": {"code": -32601, "message": f"Unknown method {method}"}}
    return {"jsonrpc": "2.0", "id": request.get("id"), "result": result}


def main() -> None:
    check_key()
    if "--check" in sys.argv:
        print(f"ok: {len(load('incidents'))} incidents, {len(load('postmortems'))} postmortems, tools: {', '.join(TOOLS)}")
        return
    log(f"ready, {len(TOOLS)} read-only tools")
    for line in sys.stdin:
        if not line.strip():
            continue
        response = handle(json.loads(line))
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
