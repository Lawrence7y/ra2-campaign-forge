"""Command line interface: validate / build / install / uninstall / verify / inspect / example."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import design as design_mod
from .builder import BuildError, build
from .install import (
    EXIT_SEAL_MISSING,
    EXIT_SEAL_MISMATCH,
    EXIT_UNINSTALL_PARTIAL,
    EXIT_VERIFY_DIGEST,
    EXIT_VERIFY_DRIFT,
    EXIT_VERIFY_STRUCTURAL,
    PackageIdentityBlocked,
    install_package,
    uninstall,
)
from .verify import verify_install

# PKG-IDENT01: distinguishable exit codes for the identity refusals
# (argparse errors keep the conventional 2, everything else unexpected is 1)
EXIT_PACKAGE_MISMATCH = 3
EXIT_LEGACY_ADOPT_REQUIRED = 4

# SEAL-CHAIN01: the exit-code table, quoted in verify --help, uninstall
# --help and VERIFY.md. 5 > 6 > 7/8 > 9 is the severity order: verify
# reports every finding and exits with the most severe class present.
VERIFY_EXIT_CODES_TEXT = """\
exit codes:
  0  everything ok (orphans, if any, are listed but do not change the
     code; a directory with no install record also verifies as 0 -
     nothing to check)
  1  the check itself failed to run (unexpected error)
  2  command-line usage error (argparse)
  5  manifest structure unusable (not JSON / required fields missing)
  6  package_digest mismatch - the manifest's own records are not
     self-consistent
  7  install seal MISSING for a seal-era manifest (tool >= 0.7)
  8  install seal MISMATCH / corrupt / aliased
  9  drift: recorded files changed or missing on disk
when several classes apply, the exit code is the MOST SEVERE one
(5 > 6 > 7/8 > 9); every finding is still listed. Old manifests (tool
< 0.7, no seal) verify in degraded mode: warned, still fully run.
The seal detects accidents, not attacks - it is not anti-tamper."""

# UNSEAL-FIX01 (W25, tool 0.8): the uninstall exit-code table. Quoted in
# uninstall --help, VERIFY.md and UNSEAL_FIX.md - the three must stay
# identical. The --json "exit_code_meaning" values come from the same table.
UNINSTALL_EXIT_CODES_TEXT = """\
exit codes (uninstall):
  0  completed - the recorded lifecycle was processed (or there was
     nothing to remove). Two documented sub-cases also exit 0: entry
     refusals keep the record for a later retry (each one listed as a
     warning; behavior unchanged since tool 0.7), and a non-qualifying
     install-record slot is not acted on (report status "failed", see
     the warning)
  1  the uninstall itself failed unexpectedly (error on stderr)
  2  command-line usage error (argparse)
  7  uninstall REFUSED: install seal MISSING for a seal-era manifest
     (tool >= 0.7) - nothing removed, nothing restored, record kept
  8  uninstall REFUSED: install seal MISMATCH / corrupt / aliased
  10 partial completion (report status "completed_with_warnings"):
     the main uninstall COMPLETED - the record was deleted and every
     recorded file was processed - but the FINAL cleanup failed (the
     install seal could not be removed). The warning names the stray
     seal file and the recovery (clear the obstacle and delete it by
     hand, or re-run the install of the SAME package and uninstall
     again). New in tool 0.8 (UNSEAL-FIX01): tool 0.7 exited 1 here
     and lost the actions report
report status values (report dict / uninstall --json "status"):
  completed - the command ran to its defined end (see exit 0 notes)
  completed_with_warnings - main flow done, final cleanup failed
  failed - refused: seal gate (exit 7/8) or a non-qualifying record
           slot (exit 0, unchanged since tool 0.7)"""

UNINSTALL_EXIT_MEANINGS = {
    0: "completed - the recorded lifecycle was processed (or there was "
       "nothing to remove; entry refusals keep the record for a retry, "
       "and a non-qualifying record slot is not acted on - see warnings)",
    1: "the uninstall itself failed unexpectedly (error on stderr)",
    2: "command-line usage error (argparse)",
    EXIT_SEAL_MISSING: "uninstall REFUSED: install seal MISSING for a "
                       "seal-era manifest (tool >= 0.7)",
    EXIT_SEAL_MISMATCH: "uninstall REFUSED: install seal MISMATCH / "
                        "corrupt / aliased",
    EXIT_UNINSTALL_PARTIAL: "partial completion (completed_with_warnings): "
                            "the main uninstall completed but the final "
                            "cleanup failed - the install seal could not "
                            "be removed (see warnings)",
}


def _uninstall_exit_code(report: dict) -> int:
    """UNSEAL-FIX01: map the uninstall report to its CLI exit code."""
    if report.get("refused"):
        return (EXIT_SEAL_MISSING if report["refused"] == "seal_missing"
                else EXIT_SEAL_MISMATCH)
    if report.get("status") == "completed_with_warnings":
        return EXIT_UNINSTALL_PARTIAL
    return 0


def _uninstall_json(report: dict) -> dict:
    """UNSEAL-FIX01: the uninstall report as JSON - same facts, same exit
    code and the same three-state status as the text report."""
    code = _uninstall_exit_code(report)
    return {"tool": "ra2forge", "command": "uninstall",
            "game_dir": str(report.get("game_dir", "")),
            "status": report.get("status"),
            "actions": report.get("actions", []),
            "warnings": report.get("warnings", []),
            "refused": report.get("refused"),
            "exit_code": code,
            "exit_code_meaning": UNINSTALL_EXIT_MEANINGS.get(code, f"exit {code}")}


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
                             "NO effect on install and never overrides any "
                             "refusal - not the package-identity gate (exit 3 "
                             "on a different declared package_id, exit 4 when "
                             "identity is undeclared), not path-safety, "
                             "corrupt-record, backup-protection or strict-risk "
                             "blocks; release content conflicts with "
                             "--allow-content-conflict instead")
    p_inst.add_argument("--allow-content-conflict", action="store_true",
                        help="release ONLY definite content conflicts (each one "
                             "is logged); never releases path-safety, "
                             "corrupt-record, backup-protection blocks or the "
                             "package-identity gate")
    p_inst.add_argument("--adopt-legacy", action="store_true",
                        help="assert explicitly that this install is the "
                             "intended successor of the install record already "
                             "in the game directory when the identity is "
                             "undeclared (record has no package_id, or this "
                             "package has no ra2forge_package.json). Without "
                             "it those cases are refused with exit 4. Does "
                             "NOT release the different-package_id refusal "
                             "(exit 3) or any other gate")

    p_un = sub.add_parser("uninstall", help="remove the package and restore backups",
                          description="Remove the recorded package files, "
                                      "restore every backup and delete the "
                                      "install record together with its "
                                      "seal. UNSEAL-FIX01 (tool 0.8): the "
                                      "final seal cleanup is fault-tolerant "
                                      "- a seal that cannot be removed "
                                      "(read-only, open handle) leaves the "
                                      "completed uninstall fully reported "
                                      "with an explicit warning and exit "
                                      "code 10 instead of aborting with "
                                      "exit 1 and a lost report.",
                          epilog=UNINSTALL_EXIT_CODES_TEXT,
                          formatter_class=argparse.RawDescriptionHelpFormatter)
    p_un.add_argument("--game", required=True, metavar="GAME_DIR")
    p_un.add_argument("--legacy", action="store_true",
                      help="also clean files placed by ra2forge <= FORGE-1 "
                           "(BATTLEMD.INI override / loose maps / mix)")
    p_un.add_argument("--drop-legacy-battlemd", action="store_true",
                      help="with --legacy: delete a legacy BATTLEMD.INI override "
                           "that has no backup (it is moved to "
                           "BATTLEMD.INI.ra2forge.removed.bak)")
    p_un.add_argument("--force", action="store_true",
                      help="delete files even when their sha256 changed. Does "
                           "NOT bypass the install-seal gate: a seal-era "
                           "manifest (tool >= 0.7) whose seal is missing "
                           "(exit 7) or mismatched/corrupt (exit 8) refuses "
                           "the whole uninstall - nothing removed, nothing "
                           "restored, record kept. Old manifests (no seal) "
                           "uninstall as before with a degraded-mode warning. "
                           "The seal detects accidents, not attacks - it is "
                           "not anti-tamper")
    p_un.add_argument("--json", dest="as_json", action="store_true",
                      help="print the full uninstall report as a JSON object "
                           "(same three-state status and same exit codes as "
                           "the text report)")

    p_ver = sub.add_parser(
        "verify", help="read-only drift check of the installed package record",
        description="Read-only verification of ra2forge_install.json and the "
                    "files it recorded: manifest structure, package_digest "
                    "self-consistency (of the RECORDS only), per-file disk "
                    "sha256 (ok / changed / missing), ra2forge orphans "
                    "(*.ra2forge.bak etc. not accounted for by the manifest), "
                    "and the install seal. Writes NOTHING.",
        epilog=VERIFY_EXIT_CODES_TEXT,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p_ver.add_argument("--game", required=True, metavar="GAME_DIR",
                       help="the game directory to check (read-only; "
                            "gamemd.exe is NOT required)")
    p_ver.add_argument("--json", dest="as_json", action="store_true",
                       help="print the full report as a JSON object (same "
                            "exit codes as the text report)")

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
                                     args.allow_content_conflict,
                                     adopt_legacy=args.adopt_legacy)
        except PackageIdentityBlocked as exc:
            # PKG-IDENT01: distinguishable exit codes - 3 = a different
            # declared package_id (never releasable), 4 = undeclared identity
            # (releasable only by --adopt-legacy)
            print(f"error: {exc}", file=sys.stderr)
            return (EXIT_PACKAGE_MISMATCH if exc.kind == "package_mismatch"
                    else EXIT_LEGACY_ADOPT_REQUIRED)
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
        code = _uninstall_exit_code(report)
        if args.as_json:
            # UNSEAL-FIX01: same facts / three-state status / exit code as
            # the text report - machine consumers read the same semantics.
            print(json.dumps(_uninstall_json(report), indent=2,
                             ensure_ascii=False))
            return code
        if report.get("refused"):
            # SEAL-CHAIN01: distinguishable seal-gate refusals - the game
            # directory was not modified by this run.
            print("uninstall refused - nothing was removed or restored:")
            _print_report(report)
        else:
            print(f"uninstalled from {report['game_dir']}:")
            _print_report(report)
        # UNSEAL-FIX01: the explicit three-state summary line - completed /
        # completed_with_warnings / failed - matching the exit code above.
        print(f"  status: {report['status']} (exit code {code})")
        return code

    if args.cmd == "verify":
        try:
            report = verify_install(args.game)
        except OSError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        if args.as_json:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            _print_verify(report)
        return report["exit_code"]

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


def _print_verify(r: dict) -> None:
    """Human-readable verify report (same facts as the --json object)."""
    print(f"verify report for {r['game_dir']}")
    if not r["manifest_present"]:
        for w in r["warnings"]:
            print(f"  note: {w}")
        print(f"  exit code: {r['exit_code']} ({r['exit_code_meaning']})")
        return
    era = ("LEGACY / degraded (no seal expected)"
           if r["legacy_degraded"] else "seal era (tool >= 0.7)")
    print(f"  manifest: {r['manifest_version'] or '<no version>'}  [{era}]")
    if r["structural"]:
        print(f"  structure: FAIL ({len(r['structural'])} finding(s))")
        for s in r["structural"]:
            print(f"    - {s}")
    else:
        print("  structure: OK")
    d = r["digest"]
    if d is None:
        print("  package_digest: (skipped - legacy manifest has no digest)")
    elif d["match"] is None:
        print(f"  package_digest: SKIPPED ({d['note']})")
    elif d["match"]:
        print(f"  package_digest: OK  {str(d['recorded'])[:12]}... "
              "(self-consistency of the records only - not proof of what is "
              "on disk)")
    else:
        print(f"  package_digest: MISMATCH  recorded={str(d['recorded'])[:12]}..."
              f"  recomputed={str(d['recomputed'])[:12]}...")
    s = r["seal"]
    if not s["expected"]:
        print(f"  seal: not expected ({s['state']})"
              + (f" - {s['detail']}" if s["detail"] else ""))
    elif s["state"] == "ok":
        print(f"  seal: OK ({s['path']})")
    else:
        print(f"  seal: {s['state'].upper()} - {s['detail']}")
    counts = r["counts"]
    print(f"  files: {counts['ok']} ok, {counts['changed']} changed, "
          f"{counts['missing']} missing/unreadable  (of "
          f"{len(r['files'])} recorded)")
    for f in r["files"]:
        mark = {"ok": "ok      ", "changed": "CHANGED ",
                "missing": "MISSING "}.get(f["status"], "ERROR   ")
        line = f"    {mark} {f['name']}"
        if f["status"] == "changed":
            line += (f"  (recorded {str(f['recorded_sha256'])[:12]}..., "
                     f"disk {str(f['disk_sha256'])[:12]}...)")
        print(line)
    if r["orphans"]:
        print(f"  orphans: {counts['orphans']} (ra2forge files the manifest "
              "does not account for; listed, do not change the exit code)")
        for o in r["orphans"]:
            print(f"    - {o}")
    else:
        print("  orphans: none")
    for w in r["warnings"]:
        print(f"  note: {w}")
    print(f"  exit code: {r['exit_code']} ({r['exit_code_meaning']})")


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
