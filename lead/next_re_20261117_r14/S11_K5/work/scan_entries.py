#!/usr/bin/env python3
"""S11-K5: dump on-disk S11 coverage rows with raw bytes and capstone skipdata shape."""
from pathlib import Path
import csv,struct,json,hashlib
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
ROOT=Path(r"D:\Project\ra2-campaign-forge")
COV=ROOT/"lead/next_re_20261117_r14/COVERAGE/coverage.tsv"
EXE=ROOT/"ra2youli/gamemd.exe"; CARD=ROOT/"lead/next_re_20261117_r14/S11_K5"
data=EXE.read_bytes(); pe=pefile.PE(str(EXE),fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
    secs.append({"name":s.Name.rstrip(b"\0").decode("latin1"),"va":IB+s.VirtualAddress,"end":IB+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData),"raw":s.PointerToRawData,"rsize":s.SizeOfRawData})
def off(va):
    for s in secs:
        if s["va"]<=va<s["end"]:
            d=va-s["va"]
            if d<s["rsize"]: return s["raw"]+d
    return None
def at(va,n):
    o=off(va); return None if o is None else data[o:o+n]
def u32(va):
    b=at(va,4); return None if b is None or len(b)<4 else struct.unpack("<I",b)[0]
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
rows=[]
with COV.open("r",encoding="utf-8",newline="") as f:
    for r in csv.DictReader(f,delimiter="\t"):
        if r.get("subsystem","").strip().upper()=="S11":
            rows.append(r)
out=[]; lines=[]
lines.append("S11-K5 COVERAGE ROW BYTE SHAPE DUMP")
lines.append("SHA256="+hashlib.sha256(data).hexdigest().upper())
lines.append("capstone="+__import__("capstone").__version__)
for r in rows:
    va=int(r["entry"].strip(),16); b=at(va,64)
    ins=list(md.disasm(b or b"",va,count=8))
    shape=""
    if b and len(b)>=6 and b[0]==0xB8 and b[5]==0xC3:
        shape="B8_IMM32_C3 imm=%08X"%struct.unpack_from("<I",b,1)[0]
    elif b and len(b)>=3 and b[0]==0x33 and b[1]==0xC0 and b[2]==0xC3:
        shape="XOR_EAX_EAX_RET"
    elif b and len(b)>=2 and b[0]==0x6A and b[2:3]==b"\xc3":
        shape="PUSH_IMM8_RET"
    elif b and len(b)==1 and b[0]==0xC3:
        shape="RET"
    elif b and len(b)>=1 and b[0]==0x8D:
        shape="LEA_START"
    rec={"entry":r["entry"].strip().upper(),"name":r.get("name",""),"grade":r.get("grade",""),"evidence":r.get("evidence",""),"raw16":(b[:16].hex() if b else None),"shape":shape,"asm":"; ".join(f"{i.mnemonic} {i.op_str}" for i in ins)}
    out.append(rec)
    lines.append(f'ENTRY {rec["entry"]} GRADE={rec["grade"]} NAME={rec["name"]} SHAPE={shape} BYTES={rec["raw16"]} ASM={rec["asm"]} EVIDENCE={rec["evidence"]}')
(CARD/"work/entry_shapes.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
(CARD/"EVIDENCE/entry_shapes.txt").write_text("\n".join(lines)+"\n",encoding="utf-8")
print("rows",len(rows))
from collections import Counter
print("shapes",Counter(x["shape"] for x in out))
print("B8 entries",[x["entry"] for x in out if x["shape"].startswith("B8_IMM32_C3")])
