"""S19 task 1: audio init (DirectSound IAT) + per-frame update entry."""
import os
import common as C

b = C.Bin()
at = C.Atlas()
E = os.path.join(C.CARD, "EVIDENCE")

calls, jmps, st = C.sweep_calls(b)
print("sweep:", st)


def show_callers(target, label):
    sites = calls.get(target, [])
    print("\n--- callers of %08X (%s): %d sites ---" % (target, label, len(sites)))
    fns = {}
    for s in sites:
        ent, rec = at.containing(s)
        key = ent if ent else None
        fns.setdefault(key, []).append(s)
        print("  site %08X  fn=%s" % (s, ("%08X" % ent) if ent else "ATLAS-GAP"))
    print("  distinct caller functions (interval containment): %d" % len(fns))
    return sites, fns


print("=== dsound import ===")
for dll, nm, iat in b.imports():
    if "sound" in dll.lower():
        print("  dll=%s name=%s IAT=%08X" % (dll, nm, iat))
x = C.abs_xrefs(b, 0x7E1050)
print("  abs xrefs to IAT: %s" % [("%08X" % r["va"]) for r in x])
show_callers(0x7C89DA, "DirectSoundCreate thunk")

C.dump(b, 0x409470, 0x150, os.path.join(E, "task1_init_409470.txt"))
show_callers(0x409470, "AudioInit(this)")

C.dump(b, 0x4095B0, 0x340, os.path.join(E, "task1_thread_4095B0.txt"))
show_callers(0x4095B0, "DirectSound thread proc (CreateThread arg)")

C.dump(b, 0x406F70, 0x90, os.path.join(E, "task1_frame_406F70.txt"))
show_callers(0x406F70, "AudioFrameUpdate")
show_callers(0x48D080, "Game::UnknownCall (frame hook)")

print("\n--- jmp sites to 0x409470 ---", [("%08X" % v) for v in jmps.get(0x409470, [])])
