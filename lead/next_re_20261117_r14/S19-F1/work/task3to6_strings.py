"""S19 tasks 3-6: locate Theme/EVA/VQA/volume code via strings+xrefs."""
import os
import common as C

b = C.Bin(); at = C.Atlas(); E = os.path.join(C.CARD, "EVIDENCE")
absx = C.sweep_abs(b)

needles = ["Theme", "EVA_", "VQA", "SoundVolume", "MusicVolume", "BGMVolume",
           "SFXVolume", "Volume", "PlayVQA", "Movie", "BINK", "Subtitle"]
found = []
for sec in (".rdata", ".data"):
    for va, s in C.find_strings(b, needles, section=sec):
        found.append((sec, va, s))

# group by needle-ish
for sec, va, s in found:
    refs = absx.get(va, [])
    refstr = ",".join(r["site"] for r in refs[:8])
    print("[%s] %08X %-40r xrefs=%d %s" % (sec, va, s[:40], len(refs), refstr))

with open(os.path.join(E, "task3to6_strings.txt"), "w", encoding="utf-8") as f:
    for sec, va, s in found:
        refs = absx.get(va, [])
        f.write("[%s]\t%08X\t%r\txrefs=%d\t%s\n" %
                (sec, va, s, len(refs), ",".join(r["site"] for r in refs)))
