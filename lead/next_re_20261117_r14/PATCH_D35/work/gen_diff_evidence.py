# -*- coding: utf-8 -*-
"""Generate byte-diff evidence files for PATCH-D35."""
import hashlib, os
SRC = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
DST = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\PATCH_D35\work\gamemd_patched.exe"
EV  = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\PATCH_D35\EVIDENCE"
CAVE_OFF, CAVE_LEN = 0x3DF781, 63
orig = open(SRC,"rb").read(); new = open(DST,"rb").read()
diffs=[i for i in range(len(orig)) if orig[i]!=new[i]]
lines=["offset_hex\tVA_hex\toriginal\tpatched\tin_cave"]
for i in diffs:
    lines.append(f"0x{i:x}\t0x{0x400000+i:x}\t{orig[i]:02X}\t{new[i]:02X}\tYES")
open(os.path.join(EV,"byte_diff.tsv"),"w").write("\n".join(lines)+"\n")
# cave before/after full hexdump
with open(os.path.join(EV,"cave_before_after.txt"),"w") as f:
    f.write("CAVE VA [0x7DF781,0x7DF7C0) file [0x3DF781,0x3DF7C0) len=63\n")
    f.write("BEFORE:\n"+" ".join(f"{b:02X}" for b in orig[CAVE_OFF:CAVE_OFF+CAVE_LEN])+"\n")
    f.write("AFTER :\n"+" ".join(f"{b:02X}" for b in new[CAVE_OFF:CAVE_OFF+CAVE_LEN])+"\n")
    f.write("\nOFFSET-BY-OFFSET (VA: before -> after):\n")
    for k in range(CAVE_LEN):
        va=0x7DF781+k; a=orig[CAVE_OFF+k]; b=new[CAVE_OFF+k]
        f.write(f"  0x{va:x}: {a:02X} -> {b:02X}" + ("  *" if a!=b else "") + "\n")
# hashes
with open(os.path.join(EV,"hashes.txt"),"w") as f:
    f.write("orig_gamemd_sha256="+hashlib.sha256(orig).hexdigest().upper()+"\n")
    f.write("patched_copy_sha256="+hashlib.sha256(new).hexdigest().upper()+"\n")
    f.write("orig_size="+str(len(orig))+"\npatched_size="+str(len(new))+"\n")
    f.write("total_diff_bytes="+str(len(diffs))+"\n")
    out=[i for i in diffs if not(CAVE_OFF<=i<CAVE_OFF+CAVE_LEN)]
    f.write("outside_cave_diff_count="+str(len(out))+"\n")
print("diff lines:",len(diffs),"outside:",len(out))
