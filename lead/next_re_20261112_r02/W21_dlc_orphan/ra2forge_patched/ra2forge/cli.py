"""Command line interface: validate / build / install / uninstall / inspect / example."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import design as design_mod
from .builder import BuildError, build
from .install import install_package, uninstall


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="python -m ra2forge",
        description="Generate a complete Red Alert 2 / Yuri's Revenge "
                    "storyline campaign from a design JSON.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_val = sub.add_parser("validate", help="validate a campaign design JSON")
    p_val.add_argument("design", help="path to design JSON")

    p_build = sub.add_parser("build", help="compile a design into game files")
    p_build.add_argument("--design", required=True, help="path to design JSON")
    p_build.add_argument("--out", default="out", help="output directory")
    p_build.add_argument("--install", metavar="GAME_DIR", default=None,
                         help="also install the package into this game directory "
                              "(backs up every replaced file)")
    p_build.add_argument("--allow-content-conflict", action="store_true",
                         help="with --install: release ONLY definite content "
                              "conflicts (each one is logged); never releases "
                              "path-safety, corrupt-record or backup-protection "
                              "blocks")

    p_inst = sub.add_parser("install", help="install an already built package")
    p_inst.add_argument("--package", required=True, metavar="DIR",
                        help="built package directory (holds BATTLEMD98.INI)")
    p_inst.add_argument("--game", required=True, metavar="GAME_DIR")
    p_inst.add_argument("--force", action="store_true",
                        help="accepted for backward compatibility only; it has "
                             "no effect on install (release content conflicts "
                             "with --allow-content-conflict; everything else "
                             "is a hard gate - see DLC-STRICT01)")
    p_inst.add_argument("--allow-content-conflict", action="store_true",
                        help="release ONLY definite content conflicts (each one "
                             "is logged); never releases path-safety, "
                             "corrupt-record or backup-protection blocks")

    p_un = sub.add_parser("uninstall", help="remove the package and restore backups")
    p_un.add_argument("--game", required=True, metavar="GAME_DIR")
    p_un.add_argument("--legacy", action="store_true",
                      help="also clean files placed by ra2forge <= FORGE-1 "
                           "(BATTLEMD.INI override / loose maps / mix)")
    p_un.add_argument("--drop-legacy-battlemd", action="store_true",
                      help="with --legacy: delete a legacy BATTLEMD.INI override "
                           "that has no backup (it is moved to "
                           "BATTLEMD.INI.ra2forge.removed.bak)")
    p_un.add_argument("--force", action="store_true",
                      help="delete files even when their sha256 changed")

    p_ex = sub.add_parser("example", help="write an example design JSON")
    p_ex.add_argument("path", nargs="?", default="demo_campaign.json")

    p_ins = sub.add_parser("inspect", help="show summary of a .map file")
    p_ins.add_argument("map", help="path to .map file")

    args = parser.parse_args(argv)

    if args.cmd == "validate":
        design = _load(args.design)
        try:
            warnings = design_mod.validate(design)
        except design_mod.DesignError as exc:
            print(f"INVALID: {exc}", file=sys.stderr)
            return 1
        n = len(design["missions"])
        print(f"OK: {n} mission(s)")
        for w in warnings:
            print(f"  warning: {w}")
        return 0

    if args.cmd == "example":
        path = Path(args.path)
        # [更正 2026-10-04 · 依据 A-69 F-6 / DP-23 · 卡片 ⑩] this is the only
        # remaining Path.write_text() in the shipped CLI, and it is deliberately
        # NOT routed through ra2forge.install's staged, alias-proof primitive:
        # the path here is the user's own output argument (demo_campaign.json by
        # default), never a slot in a game directory, so the reparse-point threat
        # model those primitives exist for does not apply. It does mean the claim
        # "write_text is zero" is scoped to install.py and must never be widened
        # to ra2forge/** - this comment is the guard against reading the next
        # sweep's zero as a whole-package zero.
        path.write_text(json.dumps(design_mod.default_design(), indent=2,
                                   ensure_ascii=False), encoding="utf-8")
        print(f"wrote {path}")
        return 0

    if args.cmd == "build":
        design = _load(args.design)
        try:
            warnings = design_mod.validate(design)
            for w in warnings:
                print(f"warning: {w}")
            mix_path = build(design, args.out)
        except (BuildError, design_mod.DesignError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(f"built: {mix_path}")
        print(f"package: {mix_path.parent}")
        if args.install:
            try:
                report = install_package(mix_path.parent, args.install,
                                         allow_content_conflict=
                                         args.allow_content_conflict)
            except (OSError, ValueError) as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 1
            print(f"installed into {report['game_dir']}:")
            _print_report(report)
            print("start gamemd.exe -> New Campaign -> the campaign list gains one "
                  "extra entry (the official campaigns are unchanged)")
        return 0

    if args.cmd == "install":
        try:
            report = install_package(args.package, args.game,
                                     allow_content_conflict=
                                     args.allow_content_conflict)
        except (OSError, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(f"installed into {report['game_dir']}:")
        _print_report(report)
        return 0

    if args.cmd == "uninstall":
        try:
            report = uninstall(args.game, legacy=args.legacy,
                               drop_legacy_battlemd=args.drop_legacy_battlemd,
                               force=args.force)
        except (OSError, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(f"uninstalled from {report['game_dir']}:")
        _print_report(report)
        return 0

    if args.cmd == "inspect":
        text = _read_map_text(Path(args.map))
        import re
        secs = re.findall(r"^\[([^\]]+)\]", text, re.M)
        interesting = ["Map", "Basic", "Houses", "Waypoints", "Structures",
                       "Units", "Infantry", "Triggers", "Events", "Actions",
                       "Tags", "TaskForces", "TeamTypes", "ScriptTypes"]
        print(f"{args.map}: {len(secs)} sections")
        for s in interesting:
            if s in secs:
                print(f"  [{s}]")
        m = re.search(r"^\[Basic\]\s*$(.*?)(?=^\[|\Z)", text, re.M | re.S)
        if m:
            for line in m.group(1).splitlines():
                if line.startswith(("Name=", "NextScenario=", "Player=", "Briefing=")):
                    print(f"  {line[:120]}")
        return 0
    return 1


def _print_report(report: dict) -> None:
    for action in report.get("actions", []):
        print(f"  {action}")
    if "risks" in report or "notices" in report:  # DLC-STRICT01 three classes
        for risk in report.get("risks", []):
            print(f"  risk (unresolvable, strict refuses): {risk}")
        for notice in report.get("notices", []):
            print(f"  notice (does not block): {notice}")
    else:
        for warning in report.get("warnings", []):
            print(f"  warning: {warning}")


def _load(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        print(f"error: {path} not found", file=sys.stderr)
        raise SystemExit(1)
    # utf-8-sig: Windows editors happily prepend a BOM to a design JSON
    with open(p, encoding="utf-8-sig") as f:
        return json.load(f)


def _read_map_text(path: Path) -> str:
    """Decode a .map the same way the game reads it (ANSI/GBK on CN installs)."""
    data = path.read_bytes()
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("gbk", errors="replace")


if __name__ == "__main__":
    raise SystemExit(main())
