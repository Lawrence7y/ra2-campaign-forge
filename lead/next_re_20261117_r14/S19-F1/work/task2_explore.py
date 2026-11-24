"""S19 task 2: VocClass play functions, callers, field writers (exploration).
Evidence -> ../EVIDENCE/task2_*.txt. Read-only target.
"""
import os, re, struct
import common as C

b = C.Bin(); at = C.Atlas(); E = os.path.join(C.CARD, "EVIDENCE")
calls, jmps, st = C.sweep_calls(b)


def entry_bytes(va, n=12):
    return b.read(va, n).hex(" ")


def caller_stats(target):
    sites = calls.get(target, [])
    fns = {}
    for s in sites:
        ent, rec = at.containing(s)
        fns.setdefault(ent, []).append(s)
    rec = at.get(target)
    print("TARGET %08X  sites=%d  caller_fns=%d  atlas_n_callers=%s  atlas_size=%s" %
          (target, len(sites), len(fns),
           rec.get("n_callers") if rec else "N/A",
           rec.get("_size") if rec else "N/A"))
    return sites, fns

print("=== play function entry bytes ===")
for va in (0x750920, 0x7509E0, 0x750E20):
    print(" %08X: %s" % (va, entry_bytes(va)))

print("\n=== callers (capstone linear sweep + atlas interval containment) ===")
play_fns = {}
for va, nm in [(0x750920, "PlayGlobal"), (0x7509E0, "PlayAt"),
               (0x750E20, "PlayIndexAtPos"), (0x405190, "VoiceAlloc")]:
    sites, fns = caller_stats(va)
    play_fns[va] = (sites, fns)
    # write per-function caller table
    with open(os.path.join(E, "task2_callers_%08X.txt" % va), "w", encoding="utf-8") as f:
        f.write("target=%08X name=%s sites=%d distinct_caller_fns=%d\n" %
                (va, nm, len(sites), len(fns)))
        by = sorted(fns.items(), key=lambda kv: (kv[0] is None, kv[0] or 0))
        for ent, ss in by:
            r = at.get(ent) if ent else None
            f.write("fn=%s size=%s n_callers_atlas=%s sites=%s\n" %
                    (("%08X" % ent) if ent else "ATLAS-GAP",
                     r.get("_size") if r else "?",
                     r.get("n_callers") if r else "?",
                     ",".join("%08X" % x for x in ss)))

print("\n=== dump play functions ===")
C.dump(b, 0x750920, 0xC0, os.path.join(E, "task2_PlayGlobal_750920.txt"))
C.dump(b, 0x7509E0, 0xE0, os.path.join(E, "task2_PlayAt_7509E0.txt"))
C.dump(b, 0x750E20, 0x120, os.path.join(E, "task2_PlayIndexAtPos_750E20.txt"))

print("\n=== dump VocClass INI writer region 0x406500..0x4066A0 ===")
C.dump(b, 0x406500, 0x1A0, os.path.join(E, "task2_ini_writers_406500.txt"))
