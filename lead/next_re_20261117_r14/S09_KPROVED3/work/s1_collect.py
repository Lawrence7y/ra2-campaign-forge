"""S09-KPROVED3 step 1: own RTTI/E8 enumeration, candidate evidence and full function dumps."""
from __future__ import annotations

import csv
from pathlib import Path

import k3lib as k

OUT = k.OUT
EV = OUT / "EVIDENCE"
EV.mkdir(parents=True, exist_ok=True)

CANDIDATES = [
    "0048E5A0",
    "0048E620",
    "004A8960",
    "004A9840",
    "004A9DD0",
    "004AA050",
    "004AAD20",
    "004AAD30",
]


def write_tsv(path: Path, header: list[str], rows: list[list]):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def hx(v: int) -> str:
    return f"{v:08X}"


# ---------- RTTI tables (all, and all holders of the 8 candidates) ----------
tables = k.rtti_tables()
with (EV / "VTABLES_ALL.tsv").open("w", encoding="utf-8") as f:
    f.write("# 1214 RTTI-readable vtable starts / 14044 .text slots; col_slot=vt-4 address containing COL pointer\n")
    f.write("vt\tcol\tcol_slot\ttd\tname\tslot_count\n")
    for t in tables:
        f.write(
            f"{hx(t['vt'])}\t{hx(t['col'])}\t{hx(t['col_slot'])}\t{hx(t['td'])}\t{t['name']}\t{len(t['slots'])}\n"
        )

cand_set = {int(e, 16) for e in CANDIDATES}
holder_rows = []
for t in tables:
    for slot, val in enumerate(t["slots"]):
        if val in cand_set:
            holder_rows.append(
                [
                    hx(val),
                    hx(t["vt"]),
                    str(slot),
                    hx(t["vt"] + 4 * slot),
                    hx(t["col_slot"]),
                    hx(t["col"]),
                    hx(t["td"]),
                    t["name"],
                    str(len(t["slots"])),
                ]
            )
holder_rows.sort(key=lambda r: (r[0], int(r[2])))
write_tsv(
    EV / "VTABLES_ALL8.tsv",
    [
        "entry",
        "vt",
        "slot",
        "slot_addr",
        "col_slot_addr",
        "col_struct",
        "td",
        "td_plus8_name",
        "vt_slot_count",
    ],
    holder_rows,
)

# ---------- full .text E8 sweep ----------
insns, calls = k.full_e8_sweep()
with (EV / "E8_SWEEP_SUMMARY.txt").open("w", encoding="utf-8") as f:
    f.write(
        f"TEXT [{hx(k.TEXT_LO)},{hx(k.TEXT_HI)}) VirtualSize=0x{k.TEXT['vsize']:X} "
        f"insns={len(insns)} E8@boundary={len(calls)}\n"
    )
    f.write("capstone 5.0.7 skipdata=True; E8 accepted only when decoded as 5-byte call.\n")

calls_by_target: dict[int, list[dict]] = {}
for c in calls:
    calls_by_target.setdefault(c["target"], []).append(c)

# ---------- S09 population and own A recompute ----------
CLS = k.BASE / "lead" / "next_re_20261117_r14" / "SURVEY_RING24" / "EVIDENCE" / "classification.tsv"
with CLS.open(encoding="utf-8") as f:
    s09 = [r for r in csv.DictReader(f, delimiter="\t") if r["subsystem"] == "S09"]

entry_to_hits: dict[int, list] = {}
for e in (int(r["entry"], 16) for r in s09):
    entry_to_hits[e] = k.tables_holding(tables, e)

a_rows = []
for r in s09:
    e = int(r["entry"], 16)
    has2 = 1 if entry_to_hits.get(e) else 0
    cs = calls_by_target.get(e, [])
    lo, hi, sites = k.direct_sites_for(e, cs) if cs else (0, 0, [])
    good = [s for s in sites if s["ok"]]
    has4dir = 1 if good else 0
    livevt = 1 if r.get("livevt_valid") == "1" else 0
    loose4 = 1 if r.get("has4_loose") == "1" else 0
    a_rows.append(
        [
            r["entry"],
            r["name"],
            str(has2),
            str(has4dir),
            str(livevt),
            str(loose4),
            "1" if has2 and has4dir else "0",
            "1" if has2 and (has4dir or livevt) else "0",
            "1" if has2 and (has4dir or loose4) else "0",
        ]
    )

write_tsv(
    EV / "A_RECOMPUTE.tsv",
    [
        "entry",
        "name",
        "has2_own_rtti",
        "has4dir_out_own",
        "livevt_classification",
        "has4loose_classification",
        "in_A_direct_own",
        "in_A_strict_own",
        "in_A_loose_own",
    ],
    a_rows,
)

n_direct = sum(int(r[6]) for r in a_rows)
n_strict = sum(int(r[7]) for r in a_rows)
n_loose = sum(int(r[8]) for r in a_rows)
n_has2 = sum(int(r[2]) for r in a_rows)
n_has4 = sum(int(r[3]) for r in a_rows)
with (EV / "A_RECOMPUTE_SUMMARY.txt").open("w", encoding="utf-8") as f:
    f.write(f"S09_population_rows={len(s09)}\n")
    f.write(f"has2_own_rtti={n_has2}\n")
    f.write(f"has4dir_out_own={n_has4}\n")
    f.write(f"A_direct_own={n_direct}\n")
    f.write(f"A_strict_own(incl classification livevt_valid)={n_strict}\n")
    f.write(f"A_loose_own={n_loose}\n")
    f.write("livevt flag is the only field reused from SURVEY classification.tsv; ②/④-direct are recomputed above.\n")

# ---------- candidate direct sites, extents, full disassembly ----------
name_by_entry = {r["entry"]: r["name"] for r in s09}
site_rows = []
extent_rows = []
for es in CANDIDATES:
    e = int(es, 16)
    lo, hi, sites = k.direct_sites_for(e, calls_by_target.get(e, []))
    for s in sites:
        site_rows.append(
            [
                es,
                hx(s["site"]),
                s["bytes"],
                f"{s['rel'] & 0xFFFFFFFF:08X}",
                hx(s["site"] + 5 + s["rel"]),
                "1" if s["site"] + 5 + s["rel"] == e else "0",
                hx(lo),
                hx(hi),
                "1" if s["in_body"] else "0",
                "1" if s["selfloop"] else "0",
                "1" if s["ok"] else "0",
            ]
        )
    cfg_lo, cfg_hi, cfg_ins = k.cfg_extent(e)
    lin = k.decode_range(e, cfg_hi)
    cfg_addrs = {i.address for i in cfg_ins}
    lin_addrs = {i.address for i in lin}
    extent_rows.append(
        [
            es,
            hx(cfg_lo),
            hx(cfg_hi),
            str(len(cfg_ins)),
            str(len(lin)),
            str(len(cfg_addrs - lin_addrs)),
            str(len(lin_addrs - cfg_addrs)),
        ]
    )
    with (EV / f"DISASM_{es}.txt").open("w", encoding="utf-8") as f:
        f.write(f"S09-KPROVED3 full function dump {es} {name_by_entry.get(es, '')}\n")
        f.write(
            f"EXTENT cfg=[{hx(cfg_lo)},{hx(cfg_hi)}) cfg_insns={len(cfg_ins)} "
            f"linear_insns={len(lin)} cfg_only={len(cfg_addrs-lin_addrs)} linear_only={len(lin_addrs-cfg_addrs)}\n"
        )
        f.write("ADDR      OFF     BYTES                 MNEMONIC  OPERANDS\n")
        for ins in lin:
            f.write(
                f"{ins.address:08X}  +0x{ins.address-e:04X}  {ins.bytes.hex():<24}  "
                f"{ins.mnemonic:<8}  {ins.op_str}\n"
            )

write_tsv(
    EV / "DIRECT_SITES_8.tsv",
    [
        "entry",
        "site",
        "bytes",
        "rel32",
        "site_plus5_plus_rel",
        "equals_entry",
        "body_lo",
        "body_hi",
        "site_in_body",
        "selfloop",
        "ok_external",
    ],
    site_rows,
)
write_tsv(
    EV / "EXTENTS_8.tsv",
    [
        "entry",
        "cfg_lo",
        "cfg_hi",
        "cfg_insns",
        "linear_insns",
        "cfg_only_addrs",
        "linear_only_addrs",
    ],
    extent_rows,
)

print(f"tables={len(tables)} slots={sum(len(t['slots']) for t in tables)}")
print(f"insns={len(insns)} E8={len(calls)}")
print(
    f"S09 rows={len(s09)} has2={n_has2} has4dir={n_has4} "
    f"A_direct={n_direct} A_strict={n_strict} A_loose={n_loose}"
)
print(f"holder_rows={len(holder_rows)} direct_site_rows={len(site_rows)}")
