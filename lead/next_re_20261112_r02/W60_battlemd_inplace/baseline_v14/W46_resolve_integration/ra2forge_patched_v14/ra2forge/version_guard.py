"""W43 / S3 -- W38-S1 VERSION_GUARD_CONTRACT.md ``classify()`` wiring.

This is the first time the S1 criteria are connected to the ACTUAL write
entries.  It is deliberately OPT-IN: the legacy ``install``/``uninstall``
code paths call :func:`guard_write_entry` only when a ``--version-guard``
fixture/baseline is supplied.  With no switch, nothing in this module runs
and the build artifacts stay byte-for-byte identical to v12.

Why opt-in (documented in S3_IMPLEMENTATION.md / DISAGREE.md):
  W38-S1 §3 step 2 mandates UNKNOWN + NO_ADJUDICATED_BASELINE when no
  adjudicated BASELINE.json exists, and §4 denies ALL game-dir writes under
  UNKNOWN/MISMATCH.  Making that the DEFAULT would refuse all 57 inherited
  regression installs (their gamemd.exe is an inert placeholder, not a PE)
  and would violate the "no new switch => byte-identical" requirement.
  The Lead's S3 card asks for the criteria to be "connected to the write
  entries", not for a behaviour change of the default path.

Pure offline: this module only READS files and optionally writes a
guard_report.json to the caller-specified path (never to a game directory).
It never launches a process, never attaches, never parses a real game binary
into memory beyond a sequential read for SHA-256.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import struct
from pathlib import Path

from . import s3_contract as C

__all__ = [
    "VersionGuardBlocked", "classify", "guard_write_entry",
    "collect_l0", "collect_l1", "GUARD_EXIT_CODES",
]


class VersionGuardBlocked(Exception):
    """Raised by a guarded write entry when S1 denies the operation."""

    def __init__(self, message: str, *, verdict: dict, exit_code: int):
        super().__init__(message)
        self.verdict = verdict
        self.exit_code = int(exit_code)


def _now() -> str:
    return _dt.datetime.now().astimezone().isoformat(timespec="seconds")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# L0 : C06 (gamemd.exe existence) + C13 (absolute path / normalization)
# ---------------------------------------------------------------------------

def collect_l0(game_dir) -> dict:
    """W38-S1 §3 step 0.  Existence is ONLY an L0 pre-check, never identity."""
    game = Path(game_dir).resolve()
    exe = game / "gamemd.exe"
    return {
        "dir_ok": bool(game.is_dir() and exe.is_file()),
        "game_dir": str(game),
        "gamemd_abs_path": str(exe),
        "observed_at": _now(),
    }


# ---------------------------------------------------------------------------
# L1 : C01 full SHA / C02 .text SHA / C04 section table / C08 size / C13 path
# ---------------------------------------------------------------------------

def _pe_l1(raw: bytes) -> dict:
    """Minimal, deterministic PE section-table reader (C02 + C04).

    Fixed parsing convention (W38-S1 C02 requires ONE convention): DOS
    e_lfanew at 0x3C, COFF header 20 bytes, optional header size from
    COFF, section headers 40 bytes each.  .text raw bytes are
    [PointerToRawData : PointerToRawData+SizeOfRawData].
    Raises ValueError when the bytes are not a usable PE (=> CRITERION_MISSING).
    """
    if len(raw) < 0x40 or raw[:2] != b"MZ":
        raise ValueError("not an MZ executable")
    e_lfanew = struct.unpack_from("<I", raw, 0x3C)[0]
    if e_lfanew + 24 > len(raw) or raw[e_lfanew:e_lfanew + 4] != b"PE\x00\x00":
        raise ValueError("no PE signature")
    coff = e_lfanew + 4
    number_of_sections = struct.unpack_from("<H", raw, coff + 2)[0]
    size_of_optional = struct.unpack_from("<H", raw, coff + 16)[0]
    opt = coff + 20
    if opt + size_of_optional > len(raw) or size_of_optional < 2:
        raise ValueError("truncated optional header")
    magic = struct.unpack_from("<H", raw, opt)[0]
    # PE32 = 0x10b; SizeOfImage at opt+56 for both PE32 and PE32+.
    if magic not in (0x10B, 0x20B):
        raise ValueError("unsupported optional-header magic")
    size_of_image = struct.unpack_from("<I", raw, opt + 56)[0]
    sections_at = opt + size_of_optional
    sections = []
    text_sha = None
    for i in range(number_of_sections):
        off = sections_at + 40 * i
        if off + 40 > len(raw):
            raise ValueError("truncated section table")
        name = raw[off:off + 8].split(b"\x00", 1)[0].decode("ascii", "replace")
        virtual_size, virtual_address, raw_size, raw_offset = \
            struct.unpack_from("<IIII", raw, off + 8)
        characteristics = struct.unpack_from("<I", raw, off + 36)[0]
        sections.append({
            "name": name,
            "virtual_address": virtual_address,
            "virtual_size": virtual_size,
            "raw_offset": raw_offset,
            "raw_size": raw_size,
            "characteristics": characteristics,
        })
        if name == ".text" and raw_offset + raw_size <= len(raw) and raw_size > 0:
            text_sha = _sha256(raw[raw_offset:raw_offset + raw_size])
    if text_sha is None:
        raise ValueError("no readable .text section")
    return {
        "c02_text_sha256": text_sha,
        "c04_size_of_image": size_of_image,
        "c04_number_of_sections": number_of_sections,
        "c04_has_detour_section": any(s["name"] == ".detour" for s in sections),
        "c04_sections": sections,
        "c03_timestamp": struct.unpack_from("<I", raw, coff + 4)[0],
    }


def collect_l1(game_dir, *, injected: dict | None = None) -> dict:
    """Read L1 criteria.  ``injected`` is an OFFLINE FIXTURE (ACCEPTANCE_S2
    §0: the regression injects guard_state/evidence; real deployments omit
    it and this function reads the actual bytes).  Injected values are
    labelled ``source="injected_fixture"`` -- never presented as measured.
    """
    l0 = collect_l0(game_dir)
    if injected is not None:
        ev = dict(injected)
        ev.setdefault("c13_abs_path", l0["gamemd_abs_path"])
        ev["source"] = "injected_fixture"
        ev["observed_at"] = _now()
        # Normalise the "obtained" bookkeeping from a compact fixture form.
        got = ev.pop("unobtainable", []) or []
        ev["missing"] = list(got)
        ev["obtained"] = {c: (c not in got) for c in
                          ("C01", "C02", "C04", "C08", "C13")}
        return ev
    exe = Path(l0["gamemd_abs_path"])
    if not l0["dir_ok"]:
        return {"source": "disk", "observed_at": _now(),
                "missing": ["C01", "C02", "C04", "C08", "C13"],
                "obtained": {c: False for c in ("C01", "C02", "C04", "C08", "C13")},
                "c13_abs_path": l0["gamemd_abs_path"]}
    try:
        raw = exe.read_bytes()
        pe = _pe_l1(raw)
        return {
            "source": "disk", "observed_at": _now(),
            "c01_full_sha256": _sha256(raw),
            "c08_size": len(raw),
            "c13_abs_path": str(exe),
            "missing": [], "obtained": {c: True for c in
                                        ("C01", "C02", "C04", "C08", "C13")},
            **pe,
        }
    except (OSError, ValueError, struct.error) as exc:
        return {"source": "disk", "observed_at": _now(),
                "c13_abs_path": str(exe),
                "c01_full_sha256": _sha256(raw) if "raw" in locals() and raw else None,
                "c08_size": len(raw) if "raw" in locals() and raw else 0,
                "pe_error": str(exc),
                "missing": ["C02", "C04"],
                "obtained": {"C01": True, "C02": False, "C04": False,
                             "C08": True, "C13": True}}


L1_FIELDS = ("c01_full_sha256", "c02_text_sha256", "c04_size_of_image",
             "c04_number_of_sections", "c04_has_detour_section",
             "c04_sections", "c08_size", "c13_abs_path")


def _verdict(state, reason_codes, *, evidence, missing, baseline_id=None,
             force_unknown=False, write_allowed=False) -> dict:
    return {
        "schema_version": "w38-s1-1",
        "state": state,
        "write_allowed": bool(write_allowed),
        "baseline_id": baseline_id,
        "edition_label": "",
        "reason_codes": list(reason_codes),
        "evidence": evidence,
        "missing_criteria": list(missing),
        "byte_windows_ok": state == "KNOWN_GOOD",
        "force_unknown_used": bool(force_unknown),
        "observed_at": _now(),
        "detour_classification": C.DETOUR_CLASSIFICATION_DEFAULT,
    }


def classify(game_dir, *, baseline=None, declared_baseline_id=None,
             evidence=None, force_unknown=False) -> dict:
    """W38-S1 §3 classify() -- deterministic, no cache (R9).

    ``baseline`` is the parsed BASELINE.json (``{"entries": [...]}``) or the
    ``baseline`` member of an S3 guard fixture.  ``evidence`` is an optional
    injected L1 fixture for offline regression.
    """
    l0 = collect_l0(game_dir)
    l1 = collect_l1(game_dir, injected=evidence)
    ev_lines = [{
        "id": "C06", "obtained": l0["dir_ok"],
        "value": l0["gamemd_abs_path"], "source": l0["game_dir"],
        "observed_at": l0["observed_at"],
    }, {
        "id": "L1", "obtained": all(l1["obtained"].values()),
        "value": {k: l1.get(k) for k in L1_FIELDS},
        "source": l1.get("source", "disk"),
        "observed_at": l1.get("observed_at"),
        "abs_path": l1.get("c13_abs_path"),
    }]
    missing = list(l1.get("missing", []))

    # step 0 -- L0
    if not l0["dir_ok"]:
        return _verdict("DIR_INVALID", ["GAMEMD_ABSENT", "DIR_INVALID"],
                        evidence=ev_lines, missing=["C06"] + missing,
                        force_unknown=force_unknown)
    # step 1 -- L1 all mandatory (R1)
    if missing:
        return _verdict("UNKNOWN", ["CRITERION_MISSING", "CRITERION_UNREADABLE"]
                        + missing, evidence=ev_lines, missing=missing,
                        force_unknown=force_unknown)
    # step 2 -- adjudicated entries only (schema const false is NOT relaxed)
    entries = [e for e in (baseline or {}).get("entries", [])
               if e.get("adjudicated") is True]
    if not entries:
        return _verdict("UNKNOWN", ["NO_ADJUDICATED_BASELINE"],
                        evidence=ev_lines, missing=missing,
                        force_unknown=force_unknown)

    def _match(e):
        ident = e.get("identity", {})
        return all(l1.get(k) == ident.get(k) for k in L1_FIELDS)

    exact = [e for e in entries if _match(e)]
    if len(exact) == 1:
        return _verdict("KNOWN_GOOD", [], evidence=ev_lines, missing=[],
                        baseline_id=exact[0].get("id"),
                        force_unknown=force_unknown, write_allowed=True)
    if len(exact) > 1:
        return _verdict("UNKNOWN", ["MULTI_COPY_AMBIGUOUS"],
                        evidence=ev_lines, missing=[],
                        force_unknown=force_unknown)
    # step 4 -- positive conflict evidence => MISMATCH
    decl = declared_baseline_id or (entries[0].get("id") if len(entries) == 1 else None)
    if decl is not None:
        b = next((e for e in entries if e.get("id") == decl), None)
        if b is not None:
            ident = b.get("identity", {})
            codes = []
            if l1.get("c01_full_sha256") != ident.get("c01_full_sha256"):
                codes.append("FULL_SHA_MISMATCH")
            if l1.get("c02_text_sha256") != ident.get("c02_text_sha256"):
                codes.append("TEXT_SHA_MISMATCH")
            if l1.get("c08_size") != ident.get("c08_size"):
                codes.append("SIZE_MISMATCH")
            if l1.get("c04_sections") != ident.get("c04_sections"):
                codes.append("SECTION_TABLE_MISMATCH")
            if codes:
                return _verdict("MISMATCH", codes, evidence=ev_lines,
                                missing=[], baseline_id=decl,
                                force_unknown=force_unknown)
    return _verdict("UNKNOWN", ["NO_BASELINE_MATCH", "EDITION_UNKNOWN"],
                    evidence=ev_lines, missing=[], force_unknown=force_unknown)


def _load_guard_fixture(path) -> dict:
    p = Path(path)
    if not p.is_file():
        raise ValueError(f"--version-guard fixture not found: {p}")
    try:
        data = json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"--version-guard fixture is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("--version-guard fixture must be a JSON object")
    return data


def _write_report(report_path, report: dict) -> str | None:
    if not report_path:
        return None
    p = Path(report_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                 encoding="utf-8")
    return str(p)


def guard_write_entry(entry_id: str, game_dir, guard_ctx: dict):
    """W38-S1 §4 decision-table gate for one write entry.

    Returns ``None`` when the write is ALLOWED (KNOWN_GOOD), otherwise raises
    :class:`VersionGuardBlocked` with the S1 exit code.  A guard_report.json
    is written to ``guard_ctx['report']`` (caller-supplied, OUTSIDE any game
    directory) with ``wrote_game_dir: false`` (W38-S1 §6.1 invariant 7).

    Only E1 / E3 / E2b-in-game are game-dir write entries.  E2a/E5 stay
    read-only / package-dir and are never gated here.
    """
    # "E2b->E1" is the W38-S1 §1.2 path-attribution reclassification: a
    # --csf-out write point that resolves inside a game directory is treated
    # as an install-level E1 entry.  It is gated identically (L1 + C12).
    if entry_id not in ("E1", "E3", "E2b", "E2b->E1"):
        return None
    fx = _load_guard_fixture(guard_ctx["fixture"])
    baseline = fx.get("baseline", fx if "entries" in fx else {"entries": []})
    verdict = classify(
        game_dir, baseline=baseline,
        declared_baseline_id=(guard_ctx.get("declared_baseline_id")
                              or fx.get("declared_baseline_id")),
        evidence=fx.get("evidence"),
        force_unknown=bool(guard_ctx.get("force_unknown")
                           or fx.get("force_unknown")),
    )
    state = verdict["state"]
    # W38-S1 §5 R5: --force-unknown is READ-ONLY degradation ONLY.
    if guard_ctx.get("force_unknown") and "FORCE_UNKNOWN_READONLY_ONLY" \
            not in verdict["reason_codes"]:
        verdict["reason_codes"].append("FORCE_UNKNOWN_READONLY_ONLY")
    report = {
        "schema_version": "w38-s1-1",
        "verdict": verdict,
        "report_written_to": str(guard_ctx.get("report") or "<not written>"),
        "wrote_game_dir": False,
        "entry_id": entry_id,
        "operator": "W43-S3",
        "command_line": " ".join(str(x) for x in guard_ctx.get("argv", [])),
    }
    rp = _write_report(guard_ctx.get("report"), report)
    if rp:
        report["report_written_to"] = rp
    if state == "KNOWN_GOOD":
        return None
    code = C.GUARD_EXIT_CODES.get(state, 20)
    msg = (f"version guard REFUSED {entry_id}: guardVerdict.state={state} "
           f"reason_codes={verdict['reason_codes']} "
           f"missing_criteria={verdict['missing_criteria']} -- "
           f"ALL_GAME_DIR_WRITES denied, zero bytes written (W38-S1 §4/R3). "
           f"--force-unknown is read-only degradation only (R5); "
           f"--force/--allow-content-conflict/--adopt-legacy/--legacy do NOT "
           f"change guard_state (§4 cross-state invariant). "
           f"exit {code}")
    raise VersionGuardBlocked(msg, verdict=verdict, exit_code=code)


def guard_check_json(game_dir, fixture_path, report_path=None) -> dict:
    """Read-only helper used by the new ``guard-check`` CLI subcommand."""
    fx = _load_guard_fixture(fixture_path)
    baseline = fx.get("baseline", fx if "entries" in fx else {"entries": []})
    v = classify(game_dir, baseline=baseline,
                 declared_baseline_id=fx.get("declared_baseline_id"),
                 evidence=fx.get("evidence"),
                 force_unknown=bool(fx.get("force_unknown")))
    report = {"schema_version": "w38-s1-1", "verdict": v,
              "report_written_to": report_path or "<not written>",
              "wrote_game_dir": False, "operator": "W43-S3"}
    rp = _write_report(report_path, report)
    if rp:
        report["report_written_to"] = rp
    return report
