"""W60 / battlemd.mode=inplace -- byte-exact [SOV1] rewrite of the official
loose BATTLEMD.INI.

PURE byte-level helper: no filesystem writes, no imports of install/builder.
``data/BATTLEMD.OFFICIAL.INI`` is the W27 ``asbuilt`` baseline (2733 B, 145
CRLF lines, SHA-256 7e40691a...).  Only the [SOV1] section's four keys are
touched; CRLF / encoding / every other section and comment are preserved
BYTE-FOR-BYTE.  Idempotent: an already-rewritten input is returned unchanged.

Grading: [本次读码] for the W27 asbuilt layout (W27/out/BATTLEMD.INI.asbuilt),
[本次实测] for the 2733 -> 2730 B rewrite produced by the W60 offline regression.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

OFFICIAL_NAME = "BATTLEMD.INI"
BACKUP_NAME = "BATTLEMD.INI.ra2forge.bak"
SECTION_SOV1 = b"[SOV1]"
REQUIRED_KEYS = ("CD", "SCENARIO", "FINALMOVIE", "DESCRIPTION")
DEFAULT_CD = "2"
DEFAULT_FINAL_MOVIE = ""
DEFAULT_DESCRIPTION = "DESC:SOV1"


def official_bytes() -> bytes:
    p = Path(__file__).resolve().parent / "data" / "BATTLEMD.OFFICIAL.INI"
    return p.read_bytes()


def official_sha256() -> str:
    return hashlib.sha256(official_bytes()).hexdigest()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def is_official(data: bytes) -> bool:
    return sha256(data) == official_sha256()


def _lines(data: bytes) -> list[bytes]:
    return re.split(b"(?<=\n)", data)


def _line_ending(lines: list[bytes]) -> bytes:
    for l in lines:
        if l.endswith(b"\r\n"):
            return b"\r\n"
        if l.endswith(b"\n"):
            return b"\n"
    return b"\r\n"


def _sov1_span(lines: list[bytes]) -> tuple[int, int]:
    start = None
    for i, l in enumerate(lines):
        if l.strip().upper() == SECTION_SOV1:
            start = i
            break
    if start is None:
        raise ValueError("official BATTLEMD.INI has no [SOV1] section")
    end = len(lines)
    for j in range(start + 1, len(lines)):
        s = lines[j].strip()
        if s.startswith(b"[") and s.endswith(b"]"):
            end = j
            break
    return start + 1, end


def _key_of(line: bytes) -> str | None:
    s = line.strip()
    if not s or s.startswith(b";") or s.startswith(b"#"):
        return None
    m = re.match(rb"^([A-Za-z0-9_]+)\s*=", s)
    return m.group(1).decode("ascii").upper() if m else None


def _value_of(line: bytes) -> str:
    s = line.strip()
    return s.split(b"=", 1)[1].decode("latin-1") if b"=" in s else ""


def diff_lines(a: bytes, b: bytes) -> list[dict]:
    """Line-by-line diff (1-based), CRLF stripped for readability only."""
    la, lb = _lines(a), _lines(b)
    out = []
    for i in range(max(len(la), len(lb))):
        x = la[i] if i < len(la) else b"<absent>"
        y = lb[i] if i < len(lb) else b"<absent>"
        if x != y:
            out.append({"line": i + 1,
                        "before": x.decode("latin-1").rstrip("\r\n"),
                        "after": y.decode("latin-1").rstrip("\r\n")})
    return out


def rewrite_sov1(data: bytes, scenario: str, *, cd: str | None = None,
                 final_movie: str | None = None,
                 description: str | None = None) -> tuple[bytes, dict]:
    """Rewrite ONLY the [SOV1] section.  Returns (new_bytes, report).

    The four keys CD / Scenario / FinalMovie / Description are written
    EXPLICITLY (W37 §3: Battle::Read_INI missing-key behaviour is not
    adjudicated).  Missing keys are appended inside the section; present keys
    keep their position.  Everything outside the section is untouched.
    """
    lines = _lines(data)
    eol = _line_ending(lines)
    lo, hi = _sov1_span(lines)
    seg = list(lines[lo:hi])

    found: dict[str, tuple[int, bytes]] = {}
    for idx, l in enumerate(seg):
        k = _key_of(l)
        if k in REQUIRED_KEYS and k not in found:
            found[k] = (idx, l)

    existing = {k: _value_of(l) for k, (_i, l) in found.items()}
    wanted = {
        "CD": cd if cd is not None else existing.get("CD", DEFAULT_CD),
        "SCENARIO": scenario,
        "FINALMOVIE": (final_movie if final_movie is not None
                       else existing.get("FINALMOVIE", DEFAULT_FINAL_MOVIE)),
        "DESCRIPTION": (description if description is not None
                        else existing.get("DESCRIPTION", DEFAULT_DESCRIPTION)),
    }
    key_spell = {"CD": "CD", "SCENARIO": "Scenario",
                 "FINALMOVIE": "FinalMovie", "DESCRIPTION": "Description"}

    added: list[str] = []
    rewritten: list[str] = []
    for k in REQUIRED_KEYS:
        val = wanted[k].encode("latin-1")
        newline = key_spell[k].encode("ascii") + b"=" + val + eol
        if k in found:
            idx, old = found[k]
            if old != newline:
                seg[idx] = newline
                rewritten.append(key_spell[k])
        else:
            added.append(key_spell[k])
            # insert before the section's trailing blank line(s), if any
            insert_at = len(seg)
            while insert_at > 0 and seg[insert_at - 1].strip() == b"":
                insert_at -= 1
            seg.insert(insert_at, newline)

    new_lines = lines[:lo] + seg + lines[hi:]
    new_bytes = b"".join(new_lines)
    idempotent = (new_bytes == data)
    report = {
        "section": "[SOV1]",
        "target_file": OFFICIAL_NAME,
        "before_bytes": len(data),
        "after_bytes": len(new_bytes),
        "before_sha256": sha256(data),
        "after_sha256": sha256(new_bytes),
        "official_baseline_sha256": official_sha256(),
        "official_baseline_matched": is_official(data),
        "line_ending": "CRLF" if eol == b"\r\n" else "LF",
        "total_lines_before": len(lines),
        "total_lines_after": len(new_lines),
        "keys_required": list(key_spell.values()),
        "keys_present_before": sorted(key_spell[k] for k in found),
        "keys_added": added,
        "keys_rewritten": rewritten,
        "values": {key_spell[k]: wanted[k] for k in REQUIRED_KEYS},
        "scenario": scenario,
        "idempotent": idempotent,
        "diff": diff_lines(data, new_bytes),
    }
    return new_bytes, report