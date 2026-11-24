"""S19 task 2b: VocClass writer callers, readers, size, RTTI name check."""
import os, struct, re
import common as C

b = C.Bin(); at = C.Atlas(); E = os.path.join(C.CARD, "EVIDENCE")
calls, jmps, st = C.sweep_calls(b)
absx = C.sweep_abs(b)

writers = {
    0x406520: "Attack(+0x138)",
    0x406530: "Decay(+0x13C)",
    0x406540: "Priority(+0x40)",
    0x406550: "Volume(+0x18)",
    0x406570: "Control(+0x10)+Attack/Decay",
    0x4065C0: "Type(+0x14)",
    0x4065D0: "Limit(+0x48)",
    0x4065E0: "Range(+0x50)",
    0x4065F0: "MinVolume(+0x54)",
    0x406600: "MinDelay(+0x58)/MaxDelay(+0x5C)",
    0x406610: "MinFDelta(+0x60)/MaxFDelta(+0x64)",
    0x406620: "VShift(+0x68)",
    0x406640: "Loop(+0x4C)",
}

print("=== writer -> callers ===")
allcallers = set()
for w, nm in writers.items():
    sites = calls.get(w, [])
    fns = set()
    for s in sites:
        e, r = at.containing(s)
        fns.add(e)
        allcallers.add(e)
    print(" %08X %-34s sites=%2d fns=%s" %
          (w, nm, len(sites), ",".join("%08X" % x if x else "GAP" for x in sorted(fns, key=lambda z: (z is None, z)))))

print("\n=== candidate parse function(s): callers shared by many writers ===")
cnt = {}
for w in writers:
    for e in set(at.containing(s)[0] for s in calls.get(w, [])):
        cnt[e] = cnt.get(e, 0) + 1
for e, n in sorted(cnt.items(), key=lambda kv: -kv[1])[:8]:
    print("  %s called by %d writers" % (("%08X" % e) if e else "GAP", n))

# Dump the top parse function
if cnt:
    top = max(cnt.items(), key=lambda kv: kv[1])[0]
    if top:
        r = at.get(top)
        size = r.get("_size") if r else 0x600
        try: size = int(size)
        except Exception: size = 0x600
        print("\n=== dump parse fn %08X size %d ===" % (top, size))
        C.dump(b, top, min(size + 16, 0x2000), os.path.join(E, "task2_ini_parse_%08X.txt" % top))

print("\n=== search immediate 0x148 (VocClass size) in .text ===")
t = b.text(); data = b.pe.__data__[t["raw"]:t["raw"]+t["rawsize"]]
m = C.md32(skipdata=True)
pat = struct.pack("<I", 0x148)
hits = []
i = 0
while True:
    i = data.find(pat, i)
    if i < 0: break
    va = t["va"] + i
    # check instruction boundary via abs sweep? use quick decode at va-5..va
    hits.append(va)
    i += 1
print("  byte hits count=%d sample=%s" % (len(hits), [("%08X" % x) for x in hits[:30]]))

print("\n=== RTTI name strings containing VocClass/AudioStream/AudioController/AudioIDXData ===")
for sec in (".rdata", ".data"):
    found = C.find_strings(b, ["VocClass", "AudioStream", "AudioController", "AudioIDXData"], section=sec)
    for va, s in found[:40]:
        print("  [%s] %08X %r" % (sec, va, s[:80]))
