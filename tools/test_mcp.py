"""Smoke-test the MCP server over stdio."""
import json
import subprocess
import sys

msgs = [
    {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
    {"jsonrpc": "2.0", "method": "notifications/initialized"},
    {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
    {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
        "name": "validate_campaign",
        "arguments": {"design_json": open(
            "examples/demo_campaign.json", encoding="utf-8").read()}},
    },
]
proc = subprocess.run(
    [sys.executable, "mcp/ra2forge_mcp.py"],
    input="\n".join(json.dumps(m) for m in msgs) + "\n",
    capture_output=True, text=True, cwd="D:/Project/ra2-campaign-forge",
    env={"PYTHONPATH": "D:/Project/ra2-campaign-forge", "SYSTEMROOT": __import__("os").environ.get("SYSTEMROOT", "")},
)
for line in proc.stdout.strip().splitlines():
    resp = json.loads(line)
    if resp.get("id") == 2:
        print("tools:", [t["name"] for t in resp["result"]["tools"]])
    elif resp.get("id") == 3:
        print("validate:", resp["result"]["content"][0]["text"][:200])
    else:
        print("init ok:", resp.get("result", {}).get("serverInfo"))
print("stderr:", proc.stderr[:200] or "(empty)")
