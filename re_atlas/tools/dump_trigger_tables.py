"""Re-derive the three trigger dispatch tables from gamemd.exe bytes.

Emits a machine-readable dump plus the two-level event lookup resolved to
target addresses. Read-only.

The point this script exists to encode: the Event dispatch is TWO levels,
    target = table1[ selector[kind - 0x0D] ]
not one. Reading 0x71F218 as a flat 49-slot table walks into the selector
bytes and yields fake dwords such as 0x0B0B0B0B.

Run from the repository root:
    python re_atlas/tools/dump_trigger_tables.py [--json]
"""

import json
import os
import struct
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")

IB = 0x400000
TEXT_LO, TEXT_HI = 0x401000, 0x7E1000

ACTION_TBL, ACTION_N = 0x6DFDEC, 145
TEAM_TBL, TEAM_N = 0x6E9F74, 65
EVENT_TBL1, EVENT_N1 = 0x71F218, 12
EVENT_SEL, EVENT_NSEL = 0x71F248, 49
EVENT_KIND_BASE = 0x0D
EVENT_FALLBACK_SEL = 0x0B

BLOB = None


def blob():
    global BLOB
    if BLOB is None:
        if not os.path.isfile(EXE):
            sys.exit(
                f"gamemd.exe not found at:\n  {EXE}\n"
                "This repository intentionally does not ship the game binary.\n"
                "Place a clean Yuri's Revenge gamemd.exe at ra2youli/gamemd.exe\n"
                "(or edit EXE at the top of this script) and run again."
            )
        with open(EXE, "rb") as fh:
            BLOB = fh.read()
    return BLOB


def u32(va):
    return struct.unpack_from("<I", blob(), va - IB)[0]


def raw(va, n):
    return blob()[va - IB: va - IB + n]


def in_text(v):
    return TEXT_LO <= v < TEXT_HI


def dump_dword_table(base, n, label):
    vals = [u32(base + 4 * i) for i in range(n)]
    return {
        "label": label,
        "table_va": base,
        "entries": n,
        "in_text": sum(1 for v in vals if in_text(v)),
        "unique_targets": len({v for v in vals if in_text(v)}),
        "min": min(vals), "max": max(vals),
        "values": vals,
    }


def event_lookup():
    t1 = [u32(EVENT_TBL1 + 4 * i) for i in range(EVENT_N1)]
    sel = list(raw(EVENT_SEL, EVENT_NSEL))
    fallback = t1[EVENT_FALLBACK_SEL]
    rows = []
    for idx, code in enumerate(sel):
        tgt = t1[code] if code < EVENT_N1 else None
        rows.append({"slot": idx, "kind": EVENT_KIND_BASE + idx,
                     "selector": code, "target": tgt,
                     "is_fallback": tgt == fallback})
    return {
        "table1_va": EVENT_TBL1, "table1": t1,
        "selector_va": EVENT_SEL, "selector_bytes": sel,
        "fallback_selector": EVENT_FALLBACK_SEL,
        "fallback_target": fallback,
        "kind_base": EVENT_KIND_BASE,
        "slots": len(sel),
        "distinct_targets_all_slots": len({r["target"] for r in rows if r["target"] is not None}),
        "slots_on_fallback": sum(1 for r in rows if r["is_fallback"]),
        "rows": rows,
    }


def main():
    out = {
        "action": dump_dword_table(ACTION_TBL, ACTION_N, "TActionClass::Execute"),
        "team": dump_dword_table(TEAM_TBL, TEAM_N, "TeamClass::AI"),
        "event": event_lookup(),
    }
    c = Counter(v for v in out["action"]["values"] if in_text(v))
    out["action"]["shared_targets"] = [
        {"target": t,
         "action_indices": [i for i, v in enumerate(out["action"]["values"]) if v == t]}
        for t, n in c.items() if n > 1
    ]

    if "--json" in sys.argv:
        print(json.dumps(out, indent=1))
        return

    for key in ("action", "team"):
        t = out[key]
        print(f'# {t["label"]}: table=0x{t["table_va"]:06X} entries={t["entries"]} '
              f'in_text={t["in_text"]} unique={t["unique_targets"]} '
              f'range=0x{t["min"]:06X}..0x{t["max"]:06X}')
    for s in out["action"]["shared_targets"]:
        print(f'#   shared target 0x{s["target"]:06X} <- actions {s["action_indices"]}')

    ev = out["event"]
    print(f'# event: table1=0x{ev["table1_va"]:06X} ({len(ev["table1"])} dwords) '
          f'selector=0x{ev["selector_va"]:06X} ({ev["slots"]} bytes, kind 0x{ev["kind_base"]:02X}..)')
    print(f'#   fallback: selector {ev["fallback_selector"]} -> 0x{ev["fallback_target"]:06X}')
    print(f'#   distinct targets over all slots = {ev["distinct_targets_all_slots"]}')
    print(f'#   slots on fallback               = {ev["slots_on_fallback"]}')
    print("#   kind  slot  sel  target")
    for r in ev["rows"]:
        tgt = f'0x{r["target"]:06X}' if r["target"] is not None else "INVALID"
        print(f'#   0x{r["kind"]:02X}  {r["slot"]:4d}  {r["selector"]:3d}  {tgt}')


main()
