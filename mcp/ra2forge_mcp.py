"""Minimal MCP (Model Context Protocol) stdio server exposing RA2 Campaign Forge.

Tools:
  - validate_campaign(design_json)  -> validation report
  - build_campaign(design_json, out_dir, install_dir?) -> built files; with
    install_dir it installs the whole package (loose appended BATTLEMD98.INI +
    maps + expandmd98.mix) through ra2forge.install, with per-file backups
  - inspect_map(path)               -> map summary

Register in ZCode Desktop (settings.json):
  "mcpServers": {
    "ra2-campaign-forge": {
      "command": "python",
      "args": ["D:/Project/ra2-campaign-forge/mcp/ra2forge_mcp.py"],
      "env": { "PYTHONPATH": "D:/Project/ra2-campaign-forge" }
    }
  }

Implements the MCP stdio transport (initialize / tools/list / tools/call)
with plain JSON-RPC — no third-party dependencies.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ra2forge import design as design_mod  # noqa: E402
from ra2forge import install as install_mod  # noqa: E402
from ra2forge.builder import build  # noqa: E402

PROTOCOL_VERSION = "2024-11-05"


def tool_validate(args: dict) -> dict:
    try:
        design = json.loads(args["design_json"])
        warnings = design_mod.validate(design)
        return {
            "content": [{"type": "text", "text": json.dumps(
                {"ok": True, "missions": len(design["missions"]),
                 "warnings": warnings}, ensure_ascii=False, indent=2)}],
        }
    except Exception as exc:  # noqa: BLE001
        return {"content": [{"type": "text", "text": f"INVALID: {exc}"}],
                "isError": True}


def tool_build(args: dict) -> dict:
    try:
        design = json.loads(args["design_json"])
        warnings = design_mod.validate(design)
        out_dir = args.get("out_dir", "out")
        mix = build(design, out_dir)
        text = f"built: {mix}"
        if warnings:
            text += "\nwarnings: " + "; ".join(warnings)
        install_dir = args.get("install_dir")
        if install_dir:
            game = Path(install_dir)
            if not (game / "gamemd.exe").exists():
                text += f"\ninstall skipped: {game} has no gamemd.exe"
            else:
                # D1 (FORGE-2): the installer must copy the WHOLE package. The
                # registration lives in the loose BATTLEMD98.INI, so copying the
                # MIX alone left the campaign invisible in the game while still
                # reporting success. ra2forge.install also backs up + records
                # every replaced file, so 'uninstall' can restore it exactly.
                try:
                    report = install_mod.install_package(mix.parent, game)
                except (OSError, ValueError) as exc:
                    text += f"\ninstall failed: {exc}"
                else:
                    text += f"\ninstalled into {report['game_dir']}:"
                    for action in report["actions"]:
                        text += f"\n  {action}"
                    for warning in report["warnings"]:
                        text += f"\n  warning: {warning}"
        return {"content": [{"type": "text", "text": text}]}
    except Exception as exc:  # noqa: BLE001
        return {"content": [{"type": "text", "text": f"BUILD FAILED: {exc}"}],
                "isError": True}


def tool_inspect(args: dict) -> dict:
    try:
        import re
        text = Path(args["path"]).read_bytes().decode("gbk", errors="replace")
        secs = re.findall(r"^\[([^\]]+)\]", text, re.M)
        summary = {"sections": len(secs), "has": [s for s in
                   ("Map", "Basic", "Triggers", "Waypoints", "Structures") if s in secs]}
        m = re.search(r"^\[Basic\]\s*$(.*?)(?=^\[|\Z)", text, re.M | re.S)
        if m:
            for line in m.group(1).splitlines():
                if line.startswith(("Name=", "NextScenario=", "Player=")):
                    summary.setdefault("basic", []).append(line[:100])
        return {"content": [{"type": "text", "text": json.dumps(
            summary, ensure_ascii=False, indent=2)}]}
    except Exception as exc:  # noqa: BLE001
        return {"content": [{"type": "text", "text": f"error: {exc}"}],
                "isError": True}


TOOLS = [
    {
        "name": "validate_campaign",
        "description": "Validate an RA2 campaign design JSON (schema per docs/DESIGN.md)",
        "inputSchema": {
            "type": "object",
            "properties": {"design_json": {"type": "string",
                                           "description": "the design JSON as a string"}},
            "required": ["design_json"],
        },
    },
    {
        "name": "build_campaign",
        "description": "Compile a campaign design into game files "
                       "(maps + BATTLEMD98.INI (loose, appended) + "
                       "expandmd98.mix), optionally installing the whole "
                       "package into a Yuri's Revenge directory",
        "inputSchema": {
            "type": "object",
            "properties": {
                "design_json": {"type": "string"},
                "out_dir": {"type": "string"},
                "install_dir": {"type": "string",
                                "description": "optional game dir to install into"},
            },
            "required": ["design_json"],
        },
    },
    {
        "name": "inspect_map",
        "description": "Summarize an RA2/YR .map file",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
]

HANDLERS = {
    "validate_campaign": tool_validate,
    "build_campaign": tool_build,
    "inspect_map": tool_inspect,
}


def _force_utf8_stdio() -> None:
    """Speak UTF-8 on the JSON-RPC channel.

    JSON-RPC over stdio is UTF-8 by definition, but on Windows Python picks the
    ANSI code page for the pipes (cp936 here), so a non-ASCII payload (Chinese
    campaign names, descriptions, briefings - all of them normal content for this
    tool) left the server as GBK bytes and a UTF-8 client could not decode the
    reply. Verified: 'build_campaign' on examples/demo_campaign.json emitted
    0xb8 ... (cp936) before this call, and valid UTF-8 after it.
    """
    for stream in (sys.stdin, sys.stdout):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError, OSError):  # pragma: no cover
            pass


def main():
    _force_utf8_stdio()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        method = req.get("method", "")
        rid = req.get("id")
        if method == "initialize":
            result = {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "ra2-campaign-forge", "version": "0.3.0"},
            }
        elif method == "notifications/initialized":
            continue
        elif method == "tools/list":
            result = {"tools": TOOLS}
        elif method == "tools/call":
            params = req.get("params", {})
            handler = HANDLERS.get(params.get("name"))
            result = handler(params.get("arguments", {})) if handler else {
                "content": [{"type": "text", "text": f"unknown tool {params.get('name')}"}],
                "isError": True,
            }
        elif method == "ping":
            result = {}
        else:
            if rid is None:
                continue
            send({"jsonrpc": "2.0", "id": rid,
                  "error": {"code": -32601, "message": "method not found"}})
            continue
        if rid is not None:
            send({"jsonrpc": "2.0", "id": rid, "result": result})


def send(obj: dict):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
