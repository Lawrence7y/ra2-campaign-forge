# W99 Task2: census of memory operands with displacement 0xE4 (and 0xE8, +0x30) in ALL executable sections.
# Writes vs reads via capstone access flags, cross-checked by mnemonic.
import sys, os, json, csv
sys.path.insert(0, os.path.dirname(__file__))
from common import PE, IMAGEBASE, MD, va2off

OUT_JSON = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r09\W99_crash_writer\EVIDENCE\task2_disp_census.json"
OUT_CSV  = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r09\W99_crash_writer\EVIDENCE\task2_disp_census.csv"

WRITE_MN = {"mov", "add", "or", "and", "sub", "xor", "inc", "dec", "xadd",
            "cmpxchg", "movzx", "movsx", "set"}  # movzx/movsx/set never write mem; kept for fallback clarity
READ_MN  = {"push", "test", "cmp", "call", "jmp", "lea"}  # lea does NOT touch memory content

def exe_sections():
    out = []
    for s in PE.sections:
        ch = s.Characteristics
        if ch & 0x20000000:  # IMAGE_SCN_MEM_EXECUTE
            out.append((s.Name.rstrip(b"\x00").decode("ascii", "replace"),
                        IMAGEBASE + s.VirtualAddress, s.SizeOfRawData))
    return out

def access_of(insn, op):
    acc = getattr(op, "access", None)
    return acc  # 1=read,2=write,3=rw (capstone5)

def mn_fallback(insn):
    """crude write detector when access flags unavailable"""
    return insn.mnemonic in ("mov", "add", "or", "and", "sub", "xor", "inc", "dec", "xadd", "cmpxchg", "adc", "sbb", "neg", "not")

rows = []
hits = {0xE4: 0, 0xE8: 0, 0x30: 0}
for name, base, rawsz in exe_sections():
    code = va2off(base) and open(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe", "rb").read()  # not used; placeholder
# proper: read each section once
with open(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe", "rb") as f:
    blob = f.read()

for name, base, rawsz in exe_sections():
    off0 = va2off(base)
    code = blob[off0:off0 + rawsz]
    for insn in MD.disasm(code, base):
        for op in insn.operands:
            if op.type == 3:  # X86_OP_MEM
                d = op.mem.disp
                if d in (0xE4, 0xE8, 0x30):
                    acc = access_of(insn, op)
                    is_wr = (acc == 2 or acc == 3) or (acc is None and mn_fallback(insn) and op.access == 2)
                    # decide write by access flag primarily
                    if acc is not None:
                        is_wr = bool(acc & 2)
                    else:
                        is_wr = mn_fallback(insn)
                    rows.append({
                        "va": "0x%08X" % insn.address,
                        "section": name,
                        "disp": "0x%X" % d,
                        "is_write": int(is_wr),
                        "access_flag": str(acc),
                        "bytes": insn.bytes.hex().upper(),
                        "text": "%s %s" % (insn.mnemonic, insn.op_str),
                    })
                    hits[d] += 1

with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(rows, f, indent=1)
with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["va"])
    w.writeheader()
    w.writerows(rows)

print("total disp hits:", hits)
from collections import Counter
c = Counter((r["disp"], r["is_write"]) for r in rows)
for k in sorted(c):
    print("disp=%s write=%d -> %d insns" % (k[0], k[1], c[k]))
print("JSON rows:", len(rows), "->", OUT_JSON)
# print all 0xE4 writes and all 0xE8 writes
print("\n== all disp 0xE4 WRITE sites ==")
for r in rows:
    if r["disp"] == "0xE4" and r["is_write"]:
        print("%s: %-20s %s %s" % (r["va"], r["bytes"], r["text"], "(access=%s)" % r["access_flag"]))
print("\n== all disp 0xE8 WRITE sites ==")
for r in rows:
    if r["disp"] == "0xE8" and r["is_write"]:
        print("%s: %-20s %s %s" % (r["va"], r["bytes"], r["text"], "(access=%s)" % r["access_flag"]))
