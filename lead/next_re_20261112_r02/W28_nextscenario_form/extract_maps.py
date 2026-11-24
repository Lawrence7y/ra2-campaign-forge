#!/usr/bin/env python3
"""W28 / T1+T2: extract official RA2/YR campaign maps from MIX containers
with the project's own ra2forge/mixlib.py, then byte-compare [Basic] NextScenario.

STRICTLY OFFLINE / READ-ONLY on sources:
  - game dir (ra2youli) is opened 'rb' only, never written
  - W21..W27 delivery dirs are read only
  - all output goes to <this script's dir>/out/

Usage:
  python extract_maps.py                      # default paths (repo layout)
  python extract_maps.py --root D:/... --out D:/.../out
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_ROOT = Path(r"D:\Project\ra2-campaign-forge")
DEFAULT_MIXLIB = (DEFAULT_ROOT / "lead" / "next_re_20261112_r02" /
                  "W26_dlc_unseal_fix" / "ra2forge_patched_v9" /
                  "ra2forge" / "mixlib.py")
DEFAULT_GAME = DEFAULT_ROOT / "ra2youli"

# Containers to try. theme*.mix are C&C (non-TS) format -> mixlib refuses them.
CONTAINERS = [
    "maps01.mix", "maps02.mix", "mapsmd03.mix",
    "expandmd01.mix", "expandmd98.mix",
    "ra2md.mix", "ra2.mix", "multi.mix", "multimd.mix",
    "langmd.mix", "language.mix", "wdt.mix",
    "movies01.mix", "movies02.mix", "movmd03.mix",
    "theme.mix", "thememd.mix",
]

# Official campaign maps named by BATTLEMD.INI [SOV1]/[ALL1] (and debug chain).
OFFICIAL_MAPS = [
    "SOV01UMD.MAP", "ALL01UMD.MAP",
    "SOV02SMD.MAP", "ALL02UMD.MAP",
    "ALL03UMD.MAP", "ALL04DMD.MAP", "ALL05UMD.MAP", "ALL06UMD.MAP",
    "ALL07SMD.MAP", "SOV03UMD.MAP", "SOV04DMD.MAP", "SOV05UMD.MAP",
    "SOV06LMD.MAP", "SOV07TMD.MAP",
    "SOV01T.MAP", "ALL01T.MAP",
    "LOCAL MIX DATABASE.DAT",
]

def ra2forge_files(root: Path, game: Path):
    """ra2forge products to compare (all READ-ONLY sources)."""
    w27 = root / "lead" / "next_re_20261112_r02" / "W27_campaign_live"
    return [
        ("W27_pkg_generated",
         w27 / "pkg" / "W27 Live Campaign" / "ECH01.MAP", "ECH01.MAP"),
        ("W27_pkg_generated_ECH02",
         w27 / "pkg" / "W27 Live Campaign" / "ECH02.MAP", "ECH02.MAP"),
        ("W27_sandbox_deployed",
         w27 / "sandbox_game" / "ECH01.MAP", "ECH01.MAP"),
        ("ra2youli_deployed", game / "ECH01.MAP", "ECH01.MAP"),
        ("ra2youli_bak", game / "ECH01.MAP.ra2forge.bak", "ECH01.MAP.ra2forge.bak"),
    ]


def load_mixlib(path: Path):
    spec = importlib.util.spec_from_file_location("w28_ra2forge_mixlib", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load mixlib from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def eol_stripped(line: bytes) -> bytes:
    return line.rstrip(b"\r\n")


def parse_basic(data: bytes) -> dict:
    """Byte-exact scan: locate [Basic], return raw lines incl. the NextScenario line."""
    out: dict = {"found": False, "section_offset": None, "raw_lines": [],
                 "keys": {}, "nextscenario": None}
    pos = 0
    in_basic = False
    for line in data.splitlines(keepends=True):
        stripped = eol_stripped(line).strip()
        if stripped.startswith(b"[") and stripped.endswith(b"]"):
            if in_basic:
                break  # next section -> [Basic] ended
            if stripped.lower() == b"[basic]":
                in_basic = True
                out["found"] = True
                out["section_offset"] = pos
                out["section_header_raw"] = repr(eol_stripped(line))
            pos += len(line)
            continue
        if in_basic:
            out["raw_lines"].append(repr(line))
            if b"=" in stripped:
                k, v = stripped.split(b"=", 1)
                out["keys"][k.decode("latin-1")] = {
                    "raw_line": repr(line),
                    "raw_value": repr(v),
                    "value_str": v.decode("latin-1"),
                    "offset": pos,
                }
                if k.decode("latin-1").lower() == "nextscenario":
                    out["nextscenario"] = {
                        "raw_line": repr(line),
                        "raw_value": repr(v),
                        "value_str": v.decode("latin-1"),
                        "value_hex": v.hex(),
                        "offset": pos,
                        "line_ending": ("CRLF" if line.endswith(b"\r\n")
                                        else "LF" if line.endswith(b"\n") else "none"),
                    }
        pos += len(line)
    return out


def candidate_names(value: str) -> list[str]:
    """Variants the engine / mixlib could hash for a NextScenario value."""
    cands = [value]
    low = value.lower()
    if low.endswith(".map"):
        cands += [value[:-4], value[:-4] + ".MAP", value.upper(), value.lower()]
    else:
        cands += [value + ".MAP", value + ".map", value.upper(), value.lower()]
    seen, uniq = set(), []
    for c in cands:
        if c not in seen:
            seen.add(c)
            uniq.append(c)
    return uniq


def blind_enumeration(mixlib, opened: dict, out: Path, report: dict) -> dict:
    """Walk EVERY entry of the maps*.mix containers by index (no name needed),
    parse [Basic] NextScenario from INI-looking entries, and resolve each raw
    value against every container's CRC/classic id set.  This gives a large,
    name-independent sample of the OFFICIAL writing convention."""
    id_sets = {
        cn: {int(e["id"], 16) for e in r["entries"]}
        for cn, r in report["containers"].items() if r.get("opened")
    }
    rows: list[dict] = []
    lines: list[str] = []
    for cn in ("maps01.mix", "maps02.mix", "mapsmd03.mix", "expandmd01.mix"):
        if cn not in opened:
            continue
        mf = opened[cn]
        lines.append(f"=== {cn} ===")
        for i, e in enumerate(mf.all_entries()):
            raw = mf.read_entry(e)
            head = raw[:80]
            if not head.lstrip().startswith(b"["):
                continue  # not a plain-INI map (rules/sound/binary/shp)
            b = parse_basic(raw)
            ns = b["nextscenario"]
            row = {
                "container": cn, "idx": i, "id": f"{e.id:08X}",
                "offset": e.offset, "size": e.size,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "first_section": head.split(b"\r\n")[0].split(b"\n")[0][:60]
                    .decode("latin-1", "replace"),
                "basic_found": b["found"], "basic_offset": b["section_offset"],
                "nextscenario": ns,
                "altnextscenario": b["keys"].get("AltNextScenario"),
            }
            if ns:
                v = ns["value_str"]
                c, cl = mixlib.crc_hash(v), mixlib.classic_hash(v)
                row["raw_value_crc"] = f"{c:08X}"
                row["raw_value_classic"] = f"{cl:08X}"
                row["raw_value_containers"] = [
                    k for k, s in id_sets.items() if c in s or cl in s]
                probes = {}
                for cand in candidate_names(v):
                    cc, ccl = mixlib.crc_hash(cand), mixlib.classic_hash(cand)
                    probes[cand] = {
                        "crc": f"{cc:08X}", "classic": f"{ccl:08X}",
                        "containers": [k for k, s in id_sets.items()
                                       if cc in s or ccl in s],
                    }
                row["target_probe"] = probes
            rows.append(row)
            lines.append(
                f"  #{i:02d} id={e.id:08X} size={e.size:<8} "
                f"first={row['first_section']!r:<24} basic@{b['section_offset']} "
                f"NS={ns['raw_value'] if ns else None!r:<22} "
                f"eol={ns['line_ending'] if ns else '-':<4} "
                f"same_or_any={row.get('raw_value_containers')} "
                f"AltNS={(b['keys'].get('AltNextScenario') or {}).get('raw_value')}")
        lines.append("")
    (out / "blind_enumeration.txt").write_text("\n".join(lines), encoding="utf-8")
    (out / "blind_enumeration.json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"rows": rows}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    ap.add_argument("--game", type=Path, default=DEFAULT_GAME)
    ap.add_argument("--mixlib", type=Path, default=DEFAULT_MIXLIB)
    ap.add_argument("--out", type=Path, default=HERE / "out")
    args = ap.parse_args()

    # allow overriding root without rebuilding every constant
    root, game, mixlib_path, out = args.root, args.game, args.mixlib, args.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "official_maps").mkdir(exist_ok=True)
    (out / "basic_sections").mkdir(exist_ok=True)

    mixlib = load_mixlib(mixlib_path)
    report: dict = {
        "tool": "W28 extract_maps.py",
        "mixlib_path": str(mixlib_path),
        "mixlib_sha256": hashlib.sha256(mixlib_path.read_bytes()).hexdigest(),
        "game_dir": str(game),
        "containers": {},
        "official": {},
        "ra2forge": {},
        "errors": [],
    }

    # ---- open all containers, enumerate index ----
    opened: dict[str, object] = {}
    enum_lines: list[str] = []
    for cname in CONTAINERS:
        p = game / cname
        rec: dict = {"path": str(p), "exists": p.exists()}
        if p.exists():
            rec["size_bytes"] = p.stat().st_size
        try:
            mf = mixlib.MixFile(p)
            opened[cname] = mf
            ents = mf.all_entries()
            rec["opened"] = True
            rec["num_entries"] = len(ents)
            rec["data_start"] = mf.data_start
            rec["entries"] = [{"id": f"{e.id:08X}", "offset": e.offset,
                               "size": e.size} for e in ents]
            enum_lines.append(f"=== {cname}  size={rec['size_bytes']}  "
                              f"entries={len(ents)}  data_start={mf.data_start} ===")
            for e in ents:
                enum_lines.append(f"  id={e.id:08X}  offset={e.offset:<12}  size={e.size}")
        except Exception as exc:
            rec["opened"] = False
            rec["error"] = f"{type(exc).__name__}: {exc}"
            report["errors"].append(f"{cname}: {rec['error']}")
        report["containers"][cname] = rec
        enum_lines.append("")
    (out / "mix_enumeration.txt").write_text("\n".join(enum_lines), encoding="utf-8")

    # ---- resolve + extract official maps ----
    basic_dump: list[str] = []
    for name in OFFICIAL_MAPS:
        rec: dict = {"name": name,
                     "crc": f"{mixlib.crc_hash(name):08X}",
                     "classic": f"{mixlib.classic_hash(name):08X}",
                     "found_in": []}
        for cname, mf in opened.items():
            data = mf.get(name)
            if data is not None:
                entry_hit = None
                for e in mf.all_entries():
                    if e.id in (mixlib.crc_hash(name), mixlib.classic_hash(name)):
                        entry_hit = {"id": f"{e.id:08X}", "offset": e.offset,
                                     "size": e.size}
                        break
                rec["found_in"].append({"container": cname, "len": len(data),
                                       "sha256": hashlib.sha256(data).hexdigest(),
                                       "head_hex": data[:24].hex(),
                                       "entry": entry_hit})
        # use FIRST container hit as canonical extraction source
        if rec["found_in"]:
            src = rec["found_in"][0]
            mf = opened[src["container"]]
            data = mf.get(name)
            dst = out / "official_maps" / name
            dst.write_bytes(data)  # verbatim copy, never modified
            rec["copy"] = str(dst)
            rec["extracted_from"] = src["container"]
            b = parse_basic(data)
            rec["basic"] = b
            (out / "basic_sections" / (name + ".basic.txt")).write_text(
                f"# source: {src['container']} :: {name}\n"
                f"# section_offset: {b['section_offset']}\n"
                + "\n".join(b["raw_lines"]) + "\n", encoding="utf-8")
            basic_dump.append(f"=== {name}  <- {src['container']}  "
                              f"len={len(data)}  sha256={src['sha256']} ===")
            basic_dump.append(f"  [Basic] offset={b['section_offset']}  "
                              f"found={b['found']}")
            for k, v in b["keys"].items():
                if k.lower() in ("nextscenario", "altnextscenario", "endofgame",
                                 "name", "player", "missionname", "briefing"):
                    basic_dump.append(f"  {v['raw_line']}")
            ns = b["nextscenario"]
            if ns:
                targets: dict = {}
                for cand in candidate_names(ns["value_str"]):
                    hits = []
                    for cname, m in opened.items():
                        if m.get(cand) is not None:
                            hits.append(cname)
                    targets[cand] = {"crc": f"{mixlib.crc_hash(cand):08X}",
                                     "classic": f"{mixlib.classic_hash(cand):08X}",
                                     "in_containers": hits}
                rec["nextscenario_target_probe"] = targets
                basic_dump.append(f"  -> target probes: {json.dumps(targets, ensure_ascii=False)}")
                # same-container check on the RAW value, using the exact bytes
                same = [c for c, m in opened.items() if m.get(ns["value_str"]) is not None]
                rec["raw_value_in_same_container"] = src["container"] in same
                rec["raw_value_in_containers"] = same
        else:
            rec["copy"] = None
            rec["extracted_from"] = None
        report["official"][name] = rec
        basic_dump.append("")
    (out / "basic_sections_dump.txt").write_text("\n".join(basic_dump), encoding="utf-8")

    # ---- ra2forge generated / deployed ECH01.MAP ----
    rf_lines: list[str] = []
    for label, path, disp in ra2forge_files(root, game):
        rec: dict = {"label": label, "path": str(path), "exists": path.exists()}
        if path.exists():
            data = path.read_bytes()
            rec["size_bytes"] = len(data)
            rec["sha256"] = hashlib.sha256(data).hexdigest()
            b = parse_basic(data)
            rec["basic"] = b
            rf_lines.append(f"=== {label} :: {path}  len={len(data)} ===")
            rf_lines.append(f"  [Basic] offset={b['section_offset']} found={b['found']}")
            for k, v in b["keys"].items():
                if k.lower() in ("nextscenario", "altnextscenario", "endofgame",
                                 "name", "player", "missionname", "briefing"):
                    rf_lines.append(f"  {v['raw_line']}")
            (out / "basic_sections" / (label + ".ECH01.basic.txt")).write_text(
                "\n".join(b["raw_lines"]) + "\n", encoding="utf-8")
        else:
            rf_lines.append(f"=== {label} :: {path}  MISSING ===")
        report["ra2forge"][label] = rec
        rf_lines.append("")
    (out / "ra2forge_ech01_basic.txt").write_text("\n".join(rf_lines), encoding="utf-8")

    # ---- blind, name-independent enumeration of every maps*.mix entry ----
    blind = blind_enumeration(mixlib, opened, out, report)
    report["blind_enumeration_count"] = len(blind["rows"])

    for mf in opened.values():
        mf.close()

    (out / "nextscenario_raw.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    # console summary
    print("== mixlib ==", mixlib_path, "sha256", report["mixlib_sha256"][:16])
    for c, r in report["containers"].items():
        print(f"  {c:<16} opened={r.get('opened')} n={r.get('num_entries')} "
              f"err={r.get('error','')}")
    print("== official [Basic] NextScenario (byte-exact) ==")
    for n, r in report["official"].items():
        if r.get("basic", {}).get("nextscenario"):
            ns = r["basic"]["nextscenario"]
            print(f"  {n:<18} <- {r['extracted_from']:<16} "
                  f"raw={ns['raw_value']:<28} eol={ns['line_ending']} "
                  f"same_mix={r.get('raw_value_in_same_container')} "
                  f"in={r.get('raw_value_in_containers')}")
        elif r["found_in"]:
            print(f"  {n:<18} <- {r['extracted_from']:<16} NO [Basic]/NextScenario")
    print("== ra2forge ECH01 [Basic] NextScenario ==")
    for label, r in report["ra2forge"].items():
        ns = r.get("basic", {}).get("nextscenario")
        print(f"  {label:<28} exists={r['exists']} "
              f"raw={ns['raw_value'] if ns else None}")
    print("== blind enumeration ==", len(blind["rows"]), "INI map entries")
    from collections import Counter
    forms = Counter()
    for r in blind["rows"]:
        ns = r["nextscenario"]
        if ns:
            v = ns["value_str"]
            forms[v] += 1
    for v, n in forms.most_common():
        print(f"  NS={v!r:<20} count={n}")
    print("OUT:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
