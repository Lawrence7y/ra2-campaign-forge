#!/usr/bin/env python3
# Verify S21 direct candidates byte-by-byte: entry validity, 16B align, prologue,
# caller owner/subsystem, atexit pattern, self-loop. Report-only 18 conflict lookup.
import os,sys,io,json,struct,re,bisect
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8",errors="replace")
import pefile, capstone
ROOT=r"D:\Project\ra2-campaign-forge"
OUT=os.path.join(ROOT,"lead","next_re_20261117_r14","S21_DIRECT")
WK=os.path.join(OUT,"work"); EV=os.path.join(OUT,"EVIDENCE")
EXE=os.path.join(ROOT,"ra2youli","gamemd.exe")
COV=os.path.join(ROOT,"lead","next_re_20261117_r14","COVERAGE","coverage.tsv")
ATLAS=os.path.join(ROOT,"lead","next_re_20261112_r10","W130_atlas","function_atlas.tsv")
def norm(a):return a.upper().replace("0X","")

data=open(EXE,"rb").read();pe=pefile.PE(EXE,fast_load=True);ib=pe.OPTIONAL_HEADER.ImageBase
sec=[s for s in pe.sections if s.Name.rstrip(b"\x00").decode()==".text"][0]
va=ib+sec.VirtualAddress; code=data[sec.PointerToRawData:sec.PointerToRawData+sec.SizeOfRawData]
def readbytes(addr,n):
    o=addr-va
    if o<0 or o+n>len(code):return None
    return code[o:o+n]
grade={};name={};cov_by_entry={}
for l in open(COV,encoding="utf-8").read().splitlines()[1:]:
    if not l.strip():continue
    f=l.split("\t");a=norm(f[0]);grade[a]=f[4];name[a]=f[2]
    cov_by_entry.setdefault(a,[]).append(dict(sub=f[1],name=f[2],grade=f[4]))
atlas={}
for l in open(ATLAS,encoding="utf-8").read().splitlines()[1:]:
    if not l.strip():continue
    f=l.split("\t");atlas[norm(f[0])]=int(f[1])
intervals=sorted((int(a,16),int(a,16)+sz) for a,sz in atlas.items())
starts=[x[0] for x in intervals]
def owner(addr):
    i=bisect.bisect_right(starts,addr)-1
    if i>=0 and intervals[i][0]<=addr<intervals[i][1]:return f"{intervals[i][0]:08X}"
    return None
hits=[]
for l in open(os.path.join(WK,"s21_direct_hits.tsv"),encoding="utf-8").read().splitlines()[1:]:
    f=l.split("\t")
    if int(f[3])>0 and f[1]!="[已证]":
        hits.append(dict(entry=f[0],grade=f[1],name=f[2],sites=f[5].split(";")))
print("non-proved direct candidate rows:",len(hits))
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
verified=[]
for h in hits:
    entry=h["entry"];en=int(entry,16)
    ebytes=readbytes(en,16)
    align16=(en%16==0)
    pred=readbytes(en-16,16)
    pred_tail=pred[-1] if pred else None
    pro=[]
    if ebytes:
        try:
            for ins in md.disasm(ebytes,en,count=3):
                pro.append((ins.mnemonic+" "+ins.op_str).strip())
        except Exception:pass
    rec=dict(entry=entry,grade_old=h["grade"],name=h["name"],align16=align16,
             pred_tail=(f"{pred_tail:02X}" if pred_tail is not None else ""),
             entry_bytes=(ebytes[:16].hex() if ebytes else ""),prologue=pro,sites=[])
    for site in h["sites"]:
        si=int(site,16);b=readbytes(si,5)
        if b is None or b[0]!=0xE8:
            rec["sites"].append(dict(site=site,ok=False,why="read/bytes"));continue
        rel=struct.unpack("<i",b[1:5])[0];calc=(si+5+rel)&0xFFFFFFFF
        callok=False
        try:
            ins=next(md.disasm(b,si),None)
            callok=(ins is not None and ins.id==capstone.x86.X86_INS_CALL and len(ins.operands)==1
                    and ins.operands[0].type==capstone.x86.X86_OP_IMM)
        except Exception:pass
        own=owner(si)
        selfloop=(own is not None and int(own,16)<=en<int(own,16)+atlas[own])
        own_sub=cov_by_entry.get(own,[])
        own_subs=sorted(set(x["sub"] for x in own_sub))
        prev5=readbytes(si-5,5)
        atexit_push=bool(prev5 and prev5[0]==0x68)
        is_atexit_reg=(calc==0x7C978A)
        rec["sites"].append(dict(site=site,bytes=b.hex(),rel=rel,target=f"{calc:08X}",
            callok=callok,owner=own,owner_subs=own_subs,atexit_push=atexit_push,
            is_atexit_reg=is_atexit_reg,selfloop=selfloop,ok=(calc==en and callok and not selfloop)))
    rec["n_ok"]=sum(1 for s in rec["sites"] if s.get("ok"))
    rec["caller_subs"]=sorted(set(sub for s in rec["sites"] for sub in s.get("owner_subs",[])))
    rec["any_atexit"]=any(s.get("atexit_push") or s.get("is_atexit_reg") for s in rec["sites"])
    verified.append(rec)
json.dump(dict(verified=verified),open(os.path.join(EV,"verify_direct.json"),"w",encoding="utf-8"),indent=2,ensure_ascii=False)
print("")
for rec in verified:
    print(rec["entry"],rec["grade_old"],rec["name"][:22],"align16="+str(rec["align16"]),
          "pred="+rec["pred_tail"],"pro="+"|".join(rec["prologue"][:2])[:26],
          "nOK="+str(rec["n_ok"]),"atexit="+str(rec["any_atexit"]),
          "callers="+",".join(rec["caller_subs"]))
print("wrote EVIDENCE/verify_direct.json")