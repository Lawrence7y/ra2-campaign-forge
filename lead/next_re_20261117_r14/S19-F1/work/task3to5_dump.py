"""S19 tasks 3-5: dump EVA trigger, VQA player, Theme functions + callers."""
import os, struct
import common as C

b = C.Bin(); at = C.Atlas(); E = os.path.join(C.CARD, "EVIDENCE")
calls, jmps, st = C.sweep_calls(b)

TARGETS = [
    (0x449C30, 0x180, "EVA_StructureSold_trigger"),
    (0x445F80, 0x180, "EVA_NuclearSilo_trigger"),
    (0x752700, 0x180, "EVA_QueueVoice"),
    (0x752480, 0x220, "EVA_enqueue_decision"),
    (0x752760, 0x120, "EVA_FrameUpdate"),
    (0x759C30, 0x260, "VQA_player"),
    (0x7209D0, 0x180, "Theme_AI"),
    (0x720B20, 0x180, "Theme_QueueSong"),
    (0x720BB0, 0x320, "Theme_PlaySong_Stop"),
    (0x720EA0, 0x160, "Theme_Stop"),
    (0x407B60, 0x90, "AudioStream_PlayWAV"),
]
for va, sz, nm in TARGETS:
    C.dump(b, va, sz, os.path.join(E, "task3to5_%s_%08X.txt" % (nm, va)))
    sites = calls.get(va, [])
    fns = set()
    for s in sites:
        e, r = at.containing(s)
        fns.add(e)
    print("%08X %-28s callers=%3d sites=%d fns=%s" %
          (va, nm, len(fns), len(sites),
           ",".join("%08X" % x if x else "GAP" for x in sorted(fns, key=lambda z: (z is None, z)))))

print("\n=== byte scan for volume string addresses (whole file) ===")
data = b.pe.__data__
for va, nm in [(0x8330C1, "SoundVolume"), (0x8330A1, "ScoreVolume"),
               (0x8330AD, "VoiceVolume"), (0x8330BC, "SoundVolume2")]:
    pat = struct.pack("<I", va)
    hits = []
    i = 0
    while True:
        i = data.find(pat, i)
        if i < 0: break
        where = "?"
        for s in b.sections:
            if s["raw"] <= i < s["raw"] + s["rawsize"]:
                where = "%08X" % (s["va"] + i - s["raw"])
                break
        hits.append(where)
        i += 1
    print("  %08X %-14s hits=%d %s" % (va, nm, len(hits), hits[:20]))
