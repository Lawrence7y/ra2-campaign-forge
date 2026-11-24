"""S09-KPROVED3 step 2: L1 all-holder enumeration + L2/⑯ base-level attribution."""
from __future__ import annotations

import csv

import k3lib as k

EV = k.OUT / "EVIDENCE"
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


def short_name(rtti_name: str) -> str:
    s = rtti_name
    if s.startswith(".?AV"):
        s = s[4:]
    elif s.startswith(".?AU"):
        s = s[4:]
    if s.endswith("@@"):
        s = s[:-2]
    return s.replace("@", "::")


def base_chain(t) -> list[str]:
    chd = k.u32(t["col"] + 0x10)
    num = k.u32(chd + 8) if chd else 0
    arr = k.u32(chd + 0xC) if chd else 0
    out = []
    if arr:
        for i in range(num or 0):
            bcd = k.u32(arr + 4 * i)
            td = k.u32(bcd) if bcd else 0
            nm = k.cstr(td + 8) if td else None
            if nm:
                out.append(nm)
    return out


tables = k.rtti_tables()
by_name = {}
for t in tables:
    by_name.setdefault(t["name"], t)

rows = []
with (EV / "CLASS_ATTRIB.tsv").open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n")
    w.writerow(
        [
            "entry",
            "n_holders",
            "all_holder_names",
            "all_slots",
            "common_base_rtti",
            "attribution_rule",
            "delta_name",
            "base_chain_evidence",
        ]
    )
    for es in CANDIDATES:
        e = int(es, 16)
        hits = k.tables_holding(tables, e)
        names = [t["name"] for t, _ in hits]
        slots = [slot for _, slot in hits]
        chains = [base_chain(t) for t, _ in hits]
        if len({s for s in slots}) != 1:
            raise SystemExit(f"non-uniform slots for {es}: {slots}")
        slot = slots[0]
        if len(hits) == 1:
            common = names[0]
            rule = "single-holder; table class = owner"
        else:
            common_set = set(chains[0])
            for ch in chains[1:]:
                common_set &= set(ch)
            # most-derived common base: its own class descriptor contains all other common bases
            candidates = []
            for nm in sorted(common_set):
                t = by_name.get(nm)
                if not t:
                    continue
                bset = set(base_chain(t))
                if (common_set - {nm}) <= bset:
                    candidates.append((len(bset), nm))
            if not candidates:
                raise SystemExit(f"no common base RTTI table for {es}: {sorted(common_set)}")
            common = max(candidates)[1]
            rule = "L1/⑯ multi-holder same slot; ownership lifted to most-derived common base"
        delta_name = f"{short_name(common)}::slot{slot}"
        chain_txt = ";".join(
            f"{n}:[{','.join(short_name(x) for x in ch)}]" for n, ch in zip(names, chains)
        )
        w.writerow(
            [
                es,
                str(len(hits)),
                ";".join(names),
                ";".join(str(s) for s in slots),
                common,
                rule,
                delta_name,
                chain_txt,
            ]
        )
        rows.append((es, len(hits), common, delta_name))
        print(es, "holders", len(hits), "base", common, "delta_name", delta_name, "slot", slot)
