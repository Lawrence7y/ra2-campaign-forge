# R17-R35-V5657A0-TABLE / work.py
# Static read-only rebuild. Writes disasm.txt and sites8.tsv; REPORT.md is authored separately.
import hashlib, os, struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

IMG = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R35_V5657A0_TABLE"
EXPECT_PREFIX = "73201CC0"
TARGET = 0x5657A0
CALLER = 0x43F180
CALLER_SIZE = 2443
SITES = [0x43F210,0x43F2A7,0x43F2C5,0x43F2EF,0x43F30B,0x43F39C,0x43F3BF,0x43F587]

data = open(IMG,"rb").read()
sha = hashlib.sha256(data).hexdigest().upper()
assert sha.startswith(EXPECT_PREFIX), sha
pe = pefile.PE(IMG)
ib = pe.OPTIONAL_HEADER.ImageBase
text = [s for s in pe.sections if s.Name.startswith(b".text")][0]
text_lo = text.PointerToRawData
text_hi = text_lo + text.SizeOfRawData

def rd(va, n):
    return data[pe.get_offset_from_rva(va - ib):pe.get_offset_from_rva(va - ib)+n]

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False

def fmt(ins):
    return "%08X  %-24s %s %s" % (ins.address, ins.bytes.hex(" "), ins.mnemonic, ins.op_str)

body = rd(TARGET, 56)
target_ins = list(md.disasm(body, TARGET))
assert target_ins[-1].address == 0x5657D5 and target_ins[-1].mnemonic == "ret"
disasm_lines = ["# 0x5657A0 body, 56 bytes, anchored linear decode", "# bytes: " + body.hex(" "), "# no C3/C2 scan"] + [fmt(i) for i in target_ins]

pos = text_lo; e8_hits = []
while True:
    pos = data.find(b"\xe8", pos, text_hi - 4)
    if pos < 0: break
    va = ib + text.VirtualAddress + (pos - text_lo)
    disp = struct.unpack("<i", data[pos+1:pos+5])[0]
    if va + 5 + disp == TARGET: e8_hits.append(va)
    pos += 1
assert len(e8_hits) == 1439, len(e8_hits)

call_ins = list(md.disasm(rd(CALLER, CALLER_SIZE), CALLER))
by_addr = {i.address: k for k, i in enumerate(call_ins)}
found = [i.address for i in call_ins if i.mnemonic == "call" and i.op_str.lower().endswith("0x5657a0") and i.address in SITES]
assert found == SITES, found

PATHS = {0x43F210:"A正常/mode1|3入口预检(0x43F1E9->0x43F210)",0x43F2A7:"A正常/mode1|3双层格循环",0x43F2C5:"A正常/mode1|3双层格循环",0x43F2EF:"A正常/mode1|3双层格循环",0x43F30B:"A正常/mode1|3双层格循环",0x43F39C:"A正常/mode1|3双层格循环(overlay/invalidate内)",0x43F3BF:"A正常/mode1|3双层格循环(overlay/invalidate内)",0x43F587:"A正常/mode1|3边界补扫(0x43F526后)"}
USES = {0x43F210:("stack_arg","栈参/对象指针给 vslot+0x1AC can-place;非 this"),0x43F2A7:("this","this -> 0x47C620"),0x43F2C5:("field_read","读 +0x38 比较"),0x43F2EF:("field_read","读 +0xEC 比较"),0x43F30B:("field_read","读 +0x48 比较"),0x43F39C:("field_write","写 +0x48=-1"),0x43F3BF:("this","this -> 0x4852D0"),0x43F587:("this","this -> 0x486E70")}
rows = ["site\tpath\tprev_6\tcall\tnext_8\tret_use_class\tret_use_detail"]
for s in SITES:
    k = by_addr[s]
    rows.append("\t".join(["0x%08X" % s, PATHS[s], " | ".join(fmt(x) for x in call_ins[max(0,k-6):k]), fmt(call_ins[k]), " | ".join(fmt(x) for x in call_ins[k+1:k+9]), USES[s][0], USES[s][1]]))

open(os.path.join(OUT,"disasm.txt"),"w",encoding="utf-8",newline="\n").write("\n".join(disasm_lines)+"\n")
open(os.path.join(OUT,"sites8.tsv"),"w",encoding="utf-8",newline="\n").write("\n".join(rows)+"\n")
print("sha", sha, "e8", len(e8_hits), "sites", len(found))
