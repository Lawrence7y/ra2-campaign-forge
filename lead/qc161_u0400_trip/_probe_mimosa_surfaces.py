#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Mimosa CLI 探针（无 argv、每个调用点字面量参数表——build.py 已验证的通过形态）。"""
import subprocess

CLI = r"C:\Users\Administrator\.zcode\cli\plugins\cache\zcode-plugins-official\mimosa\1.0.4\payload\dist\cli.js"
PROJ = r"D:\Project\ra2-campaign-forge"


def show(r):
    out = (r.stdout or b"").decode("utf-8", errors="replace")
    err = (r.stderr or b"").decode("utf-8", errors="replace")
    if out:
        print(out, end="" if out.endswith("\n") else "\n")
    if err:
        print("[stderr]", err.strip()[:400])
    print("[rc]", r.returncode)


def main():
    print("=" * 20, "ledger list")
    show(subprocess.run(["node", CLI, "ledger", "list", "--project", PROJ], capture_output=True))
    print("=" * 20, "ledger record --help")
    show(subprocess.run(["node", CLI, "ledger", "record", "--help"], capture_output=True))
    print("=" * 20, "git-gate install --help")
    show(subprocess.run(["node", CLI, "git-gate", "install", "--help"], capture_output=True))
    print("=" * 20, "git-gate uninstall --help")
    show(subprocess.run(["node", CLI, "git-gate", "uninstall", "--help"], capture_output=True))
    print("=" * 20, "validate --help")
    show(subprocess.run(["node", CLI, "validate", "--help"], capture_output=True))
    print("=" * 20, "policy check")
    show(subprocess.run(["node", CLI, "policy", "check", "--project", PROJ], capture_output=True))
    print("=" * 20, "git-gate install (bare)")
    show(subprocess.run(["node", CLI, "git-gate", "install"], capture_output=True))
    print("=" * 20, "git-gate status (after)")
    show(subprocess.run(["node", CLI, "git-gate", "status"], capture_output=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
