"""verify - read-only drift detection for an installed ra2forge package.

SEAL-CHAIN01 (W23): the manifest is plain-text JSON and uninstall acts on
it, so a hand-edited or accidentally mangled manifest can silently drive
deletions and restores (W21 UNCOVERED §3). `verify` reports - without
writing anything:

  1. manifest structure   - JSON parses, required fields present and
                            well-formed (plain file name + 64-hex sha256 per
                            entry, package_digest present for seal-era
                            manifests);
  2. package_digest       - recomputed over the manifest's OWN files[]
                            records vs the recorded package_digest. NOTE:
                            this proves the manifest's INTERNAL consistency
                            only - the records could still disagree with
                            the disk (check 3 is what looks at the disk);
  3. per-file disk check  - the actual sha256 of every recorded file vs the
                            recorded one: ok / changed / missing (a file
                            that cannot be read is reported as unreadable
                            and counts as drift);
  4. orphans              - ra2forge-characteristic files on disk that the
                            manifest does not account for (*.ra2forge.bak,
                            *.ra2forge.removed.bak, *.ra2forge-stage*),
                            minus the manifest/seal pair itself. Orphans
                            are listed but do NOT change the exit code;
  5. install seal         - for seal-era manifests (tool >= 0.7) the seal
                            must exist and match the manifest's canonical
                            bytes; older manifests run in DEGRADED mode
                            (warned, still fully executed).

BOUNDARY (do not widen when quoting this): the seal detects ACCIDENTS - it
is NOT anti-tamper and NOT a security boundary. Whoever can edit the
manifest can recompute the seal. Nothing here is cryptographic trust.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from .install import (
    MANIFEST_NAME,
    SEAL_NAME,
    _derived_slot_error,
    evaluate_seal,
    _manifest_is_seal_era,
    sha256_of,
    EXIT_VERIFY_STRUCTURAL,
    EXIT_VERIFY_DIGEST,
    EXIT_SEAL_MISSING,
    EXIT_SEAL_MISMATCH,
    EXIT_VERIFY_DRIFT,
)

EXIT_OK = 0

# most severe first; verify reports every finding and exits with the worst
_SEVERITY_ORDER = (EXIT_VERIFY_STRUCTURAL, EXIT_VERIFY_DIGEST,
                   EXIT_SEAL_MISSING, EXIT_SEAL_MISMATCH, EXIT_VERIFY_DRIFT)

EXIT_MEANINGS = {
    EXIT_OK: "everything ok (orphans, if any, are listed without changing "
             "the code; a directory with no install record also verifies "
             "as 0 - nothing to check)",
    1: "the check itself failed to run (unexpected error)",
    2: "command-line usage error (argparse)",
    EXIT_VERIFY_STRUCTURAL: "manifest structure unusable (not JSON, required "
                            "fields missing/malformed)",
    EXIT_VERIFY_DIGEST: "package_digest mismatch - the manifest's own "
                        "records are not self-consistent",
    EXIT_SEAL_MISSING: "install seal MISSING for a seal-era manifest "
                       "(tool >= 0.7)",
    EXIT_SEAL_MISMATCH: "install seal MISMATCH / corrupt / aliased",
    EXIT_VERIFY_DRIFT: "drift: recorded files changed or missing on disk",
}

_ORPHAN_MARKERS = (".ra2forge.bak", ".ra2forge.removed.bak", ".ra2forge-stage")


def _is_orphan_name(name: str) -> bool:
    low = name.lower()
    return any(low.endswith(m) or m in low for m in _ORPHAN_MARKERS)


def _entry_structural_error(entry, idx: int) -> str | None:
    """Why this files[] entry is structurally unusable, or None."""
    where = f"files[{idx}]"
    if not isinstance(entry, dict):
        return f"{where}: not a JSON object"
    name = entry.get("name")
    if not isinstance(name, str) or not name:
        return f"{where}: 'name' missing or not a string"
    if (name in (".", "..") or Path(name).name != name
            or "/" in name or "\\" in name):
        return (f"{where}: {name!r} is not a plain file name inside the "
                "game directory")
    sha = entry.get("sha256")
    if not isinstance(sha, str) or len(sha) != 64:
        return f"{where} ({name}): 'sha256' missing or not a 64-char string"
    if any(ch not in "0123456789abcdef" for ch in sha.lower()):
        return f"{where} ({name}): 'sha256' is not 64 hex digits"
    return None


def verify_install(game_dir) -> dict:
    """Read-only verification of the install record in game_dir.

    Returns a JSON-serialisable report; report["exit_code"] is the CLI exit
    code (see EXIT_MEANINGS / verify --help). Never writes, never deletes.
    """
    game = Path(game_dir)
    manifest_path = game / MANIFEST_NAME
    report: dict = {
        "tool": "ra2forge",
        "command": "verify",
        "game_dir": str(game),
        "manifest_present": False,
        "manifest_version": None,
        "legacy_degraded": False,
        "structural": [],
        "digest": None,
        "seal": None,
        "files": [],
        "orphans": [],
        "warnings": [],
        "counts": {"ok": 0, "changed": 0, "missing": 0, "orphans": 0},
        "exit_code": EXIT_OK,
        "exit_code_meaning": EXIT_MEANINGS[EXIT_OK],
    }

    def worst_of(codes) -> int:
        for code in _SEVERITY_ORDER:
            if code in codes:
                return code
        return EXIT_OK

    def finalize(codes) -> None:
        code = worst_of(codes)
        report["exit_code"] = code
        report["exit_code_meaning"] = EXIT_MEANINGS.get(
            code, f"exit {code}")

    if not manifest_path.is_file():
        report["warnings"].append(
            f"no {MANIFEST_NAME} in {game} - nothing to verify "
            "(an install with 'python -m ra2forge install' writes it)")
        return report
    report["manifest_present"] = True

    # the record is never read through an alias - same criteria as
    # install/uninstall use for the record slot
    rec_err = _derived_slot_error(game, MANIFEST_NAME, "install record")
    if rec_err:
        report["structural"].append(f"install record unusable: {rec_err}")
        finalize([EXIT_VERIFY_STRUCTURAL])
        return report
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as exc:
        report["structural"].append(f"{MANIFEST_NAME} is not readable "
                                    f"UTF-8 text ({exc})")
        finalize([EXIT_VERIFY_STRUCTURAL])
        return report
    except ValueError as exc:
        report["structural"].append(f"{MANIFEST_NAME} is not valid JSON "
                                    f"({exc})")
        finalize([EXIT_VERIFY_STRUCTURAL])
        return report
    if not isinstance(manifest, dict):
        report["structural"].append("malformed structure (expected a JSON "
                                    "object)")
        finalize([EXIT_VERIFY_STRUCTURAL])
        return report
    version = manifest.get("version")
    report["manifest_version"] = version if isinstance(version, str) else None

    legacy = not _manifest_is_seal_era(manifest)
    report["legacy_degraded"] = legacy
    if legacy:
        report["warnings"].append(
            f"legacy manifest (tool version {manifest.get('version')!r}): "
            "predates the install seal - verifying in DEGRADED mode (no "
            "package_digest / seal checks; file-level checks still run)")

    entries = manifest.get("files")
    if not isinstance(entries, list):
        report["structural"].append("malformed structure (expected a "
                                    "'files' list)")
        finalize([EXIT_VERIFY_STRUCTURAL])
        return report

    # -- 1. structure
    bad_indexes: set[int] = set()
    for idx, entry in enumerate(entries):
        err = _entry_structural_error(entry, idx)
        if err:
            report["structural"].append(err)
            bad_indexes.add(idx)
    if not legacy and not isinstance(manifest.get("package_digest"), str):
        report["structural"].append("seal-era manifest lacks a string "
                                    "'package_digest' field")
        bad_indexes.add(-1)  # marker: digest checks are meaningless
    structural_any = bool(report["structural"])

    # -- 2. package_digest (self-consistency of the RECORDS ONLY)
    if legacy:
        report["digest"] = None
    elif structural_any:
        report["digest"] = {"recorded": manifest.get("package_digest"),
                            "recomputed": None, "match": None,
                            "note": "skipped - structural failures above "
                                    "make the records unusable"}
    else:
        lines = sorted(f"{e['name']} {e['sha256'].lower()}" for e in entries)
        recomputed = hashlib.sha256("\n".join(lines).encode("utf-8")) \
            .hexdigest()
        recorded = manifest.get("package_digest")
        report["digest"] = {"recorded": recorded, "recomputed": recomputed,
                            "match": recorded == recomputed,
                            "note": "self-consistency of the manifest's own "
                                    "records only - NOT proof of what is on "
                                    "disk (see files[])"}

    # -- 5. seal (independent of JSON validity: hashes the canonical bytes)
    seal_info = evaluate_seal(game, manifest, manifest_path)
    seal_state = seal_info["state"]
    report["seal"] = {"expected": not legacy, "state": seal_state,
                      "detail": seal_info["detail"],
                      "path": seal_info["path"]}
    if seal_state == "not_expected" and seal_info["detail"]:
        report["warnings"].append(f"install seal note: {seal_info['detail']}")
    seal_codes: set[int] = set()
    if seal_state == "missing":
        seal_codes.add(EXIT_SEAL_MISSING)
    elif seal_state in ("mismatch", "corrupt", "aliased"):
        seal_codes.add(EXIT_SEAL_MISMATCH)

    # -- 3. per-file disk check (structurally valid entries only)
    for idx, entry in enumerate(entries):
        if idx in bad_indexes:
            continue
        name = entry["name"]
        recorded_sha = entry["sha256"].lower()
        dest = game / name
        if not dest.is_file():
            status, disk_sha = "missing", None
        else:
            try:
                disk_sha = sha256_of(dest)
                status = "ok" if disk_sha == recorded_sha else "changed"
            except OSError as exc:
                disk_sha = None
                status = f"unreadable ({exc})"
        report["files"].append({"name": name, "recorded_sha256": recorded_sha,
                                "disk_sha256": disk_sha, "status": status})
    counts = report["counts"]
    counts["ok"] = sum(1 for f in report["files"] if f["status"] == "ok")
    counts["changed"] = sum(1 for f in report["files"]
                            if f["status"] == "changed")
    counts["missing"] = sum(1 for f in report["files"]
                            if f["status"].startswith(("missing",
                                                       "unreadable")))

    # -- 4. orphans (listed; never change the exit code)
    accounted = {os.path.normcase(MANIFEST_NAME),
                 os.path.normcase(SEAL_NAME)}
    for idx, entry in enumerate(entries):
        if idx in bad_indexes or not isinstance(entry, dict):
            continue
        if isinstance(entry.get("name"), str):
            accounted.add(os.path.normcase(entry["name"]))
        backup = entry.get("backup")
        if isinstance(backup, str) and backup:
            accounted.add(os.path.normcase(backup))
    for p in sorted(game.iterdir()):
        if not p.is_file() or not _is_orphan_name(p.name):
            continue
        if os.path.normcase(p.name) in accounted:
            continue
        report["orphans"].append(p.name)
    counts["orphans"] = len(report["orphans"])

    codes: set[int] = set(seal_codes)
    if structural_any:
        codes.add(EXIT_VERIFY_STRUCTURAL)
    if report["digest"] and report["digest"]["match"] is False:
        codes.add(EXIT_VERIFY_DIGEST)
    if counts["changed"] or counts["missing"]:
        codes.add(EXIT_VERIFY_DRIFT)
    finalize(codes)
    return report
