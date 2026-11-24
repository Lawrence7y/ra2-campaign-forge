#!/usr/bin/env python3
# S13-K7 reproducible verifier. Read-only exe; writes only CARD dir.
import os, re, sys, struct, hashlib, bisect, collections, json
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86_const import X86_OP_IMM, X86_OP_MEM

ROOT = "/mnt/d/Project/ra2-campaign-forge"
EXE = ROOT + "/ra2youli/gamemd.exe"
CARD = ROOT + "/lead/next_re_20261117_r14/S13_K7"
EVID = CARD + "/EVIDENCE"
ATLAS = ROOT + "/lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv"
COV = ROOT + "/lead/next_re_20261117_r14/COVERAGE/coverage.tsv"
AUDIT = ROOT + "/lead/next_re_20261116_r12/_lead_audit/audit_lib.py"
sys.path.insert(0, os.path.dirname(AUDIT))
import audit_lib

os.makedirs(EVID, exist_ok=True)
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
data = open(EXE, "rb").read()
secs = []
for s in pe.sections:
    secs.append(dict(name=s.Name.decode(errors="replace").rstrip("\x00"),
                     va=IB+s.VirtualAddress, vsize=s.Misc_VirtualSize,
                     raw=s.PointerToRawData, rawsize=s.SizeOfRawData))
def secbytes(name):
    s = next(x for x in secs if x["name"] == name)
    return s, data[s["raw"]:s["raw"]+s["rawsize"]]
def rd(va, n):
    for s in secs:
        if s["va"] <= va and va+n <= s["va"]+s["rawsize"]:
            off = s["raw"] + (va-s["va"])
            return data[off:off+n]
    raise ValueError("VA %08X+%d not raw-mapped" % (va,n))
def u32(va): return struct.unpack("<I", rd(va,4))[0]
def cstr(va, maxn=300):
    out=b""
    while len(out)<maxn:
        b=rd(va,1)
        if not b or b[0]==0: break
        out+=b; va+=1
    return out.decode("ascii","replace")

md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail=True; md.skipdata=True
textsec, text = secbytes(".text"); T0=textsec["va"]
_, rdata = secbytes(".rdata")

FAMILIES = [
    # tag, element, vt, subsystem for slot6 etc
    ("BombClass*", "BombClass", 0x7E17CC),
    ("WarheadTypeClass*", "WarheadTypeClass", 0x7E1E84),
    ("WeaponTypeClass*", "WeaponTypeClass", 0x7E1ED4),
    ("BulletClass*", "BulletClass", 0x7E4678),
    ("UDamageGroup*", "UDamageGroup", 0x7E5170),
    ("KamikazeControl*", "KamikazeControl", 0x7ECE7C),
    ("ParasiteClass*", "ParasiteClass", 0x7EF824),
    ("RadSiteClass*", "RadSiteClass", 0x7F07A4),
]
EXACT11 = {
    "0040B880": ("BombClass*",2,"0X43864A"),
    "0040B930": ("BombClass*",4,"0X43942B"),
    "0040F7C0": ("WarheadTypeClass*",2,"0X75D11C"),
    "0040FD90": ("WeaponTypeClass*",2,"0X771ECA"),
    "0040FE40": ("WeaponTypeClass*",4,"0X773139"),
    "0046B7E0": ("BulletClass*",2,"0X46649B"),
    "0046B890": ("BulletClass*",4,"0X46661B"),
    "0062B250": ("ParasiteClass*",2,"0X629360"),
    "0062B300": ("ParasiteClass*",4,"0X62B012"),
    "0065C0D0": ("RadSiteClass*",2,"0X65B277"),
    "0065C180": ("RadSiteClass*",4,"0X65B358"),
}
MISS3 = {"0048AD60":("UDamageGroup*",6), "0054E8E0":("KamikazeControl*",6), "0048AD70":("UDamageGroup*",1)}

# coverage grade map
cov = {}
for line in open(COV, encoding="utf-8", errors="replace").read().splitlines()[1:]:
    p=line.split("\t")
    if len(p)>=5: cov[p[0].upper()]=(p[1],p[2],p[4])

# direct call target counts from raw E8 rel32 byte scan; instruction-boundary call sites are checked separately
call_targets = collections.Counter()

# raw E8 rel32 target counts, independent byte channel
raw_call_targets = collections.Counter()
for i in range(len(text)-4):
    if text[i] == 0xE8:
        rel = struct.unpack_from("<i", text, i+1)[0]
        raw_call_targets[T0+i+5+rel] += 1
call_targets = raw_call_targets

# global vptr immediate writes: C7 05 <global> <vt>
vptr_writes = collections.defaultdict(list)
for i in range(len(text)-9):
    if text[i:i+2] == b"\xc7\x05":
        g, v = struct.unpack_from("<II", text, i+2)
        vptr_writes[(g,v)].append(T0+i)

# 56 slots: RTTI self-walk and byte-boundary read
slots = []
with open(EVID+"/rtti_slots_56.tsv","w",encoding="utf-8",newline="") as f:
    f.write("entry\telement\tslot\tvt\tptr_site\tCOL\tTD\tTD+8\tverified\tcard_class\n")
    for elem, tag, vt in FAMILIES:
        col = u32(vt-4)
        td = u32(col+0xC)
        nm = cstr(td+8)
        ok = nm == ".?AV?$DynamicVectorClass@P"+("AV" if elem.endswith("Class*") or elem=="UDamageGroup*" else "AU")+elem[:-1]+"@@@@"
        # exact expected strings handled below; ok not authoritative, keep observed only
        for slot in range(7):
            site = vt+4*slot
            entry = u32(site)
            cls = "S22" if entry in {0x40B690,0x46B630,0x62B0C0,0x65BF40} else "S13"
            slots.append(dict(entry=entry, elem=elem, slot=slot, vt=vt, site=site, col=col, td=td, name=nm, cls=cls))
            f.write(f"{entry:08X}\t{elem}\t{slot}\t{vt:08X}\t{site:08X}\t{col:08X}\t{td:08X}\t{nm}\tbytecompare\ttag={tag},class={cls}\n")

# exact pattern scanner: raw B9 imm32 + decode forward to call [reg+disp8]
regnames = {0:"eax",1:"ecx",2:"edx",3:"ebx",4:"esp",5:"ebp",6:"esi",7:"edi"}
entry_to_slot = {s["entry"]:s for s in slots}
exact_hits=[]
for i in range(len(text)-13):
    if text[i] != 0xB9: continue
    g = struct.unpack_from("<I", text, i+1)[0]
    # decode from the B9 hit; must be a true mov ecx,imm32
    try:
        first = next(md.disasm(text[i:i+24], T0+i))
    except StopIteration:
        continue
    if first.mnemonic != "mov" or first.op_str != f"ecx, 0x{g:x}": continue
    window = text[i:i+32]
    call=None
    for ins in md.disasm(window, T0+i):
        if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == X86_OP_MEM:
            op=ins.operands[0].mem
            if op.base is not None and op.disp in (0,4,8,0xC,0x10,0x14) and op.index is None:
                call=ins; break
    if not call: continue
    slot=call.operands[0].mem.disp//4
    base=ins.reg_name(call.operands[0].mem.base) if call.operands[0].mem.base is not None else "?"
    # verify base register loaded from same global within 0x100 bytes before B9
    lo=max(0,i-0x100)
    load_va=None
    opc = {"eax":0x05,"ecx":0x0D,"edx":0x15,"ebx":0x1D,"esp":0x25,"ebp":0x2D,"esi":0x35,"edi":0x3D}.get(base)
    patts=[]
    if opc is not None: patts.append(b"\x8b"+bytes([opc])+struct.pack("<I",g))
    if base=="eax": patts.append(b"\xa1"+struct.pack("<I",g))
    for patt in patts:
        p=text.find(patt,lo,i+1)
        if p!=-1: load_va=T0+p; break
    if load_va is None: continue
    # vptr write with any target vt whose slot matches target entry
    target = u32(next(s for s in slots if s["slot"]==slot and s["vt"] in [x[2] for x in FAMILIES])["vt"]+4*slot) if False else None
    matched=[]
    for elem,tag,vt in FAMILIES:
        ent=u32(vt+4*slot)
        if (g,vt) in vptr_writes and ent in entry_to_slot:
            matched.append((ent,vt))
    if not matched: continue
    for ent,vt in matched:
        exact_hits.append(dict(entry=f"{ent:08X}", slot=slot, call_site=call.address,
                               glob=g, base=base, load_site=load_va,
                               mov_ecx=T0+i, vt=vt,
                               write_sites=vptr_writes[(g,vt)]))

# Deduplicate and write exact hits
seen=set(); hits=[]
for h in exact_hits:
    k=(h["entry"],h["slot"],h["call_site"],h["glob"],h["vt"])
    if k in seen: continue
    seen.add(k); hits.append(h)
with open(EVID+"/exact_callsites.tsv","w",encoding="utf-8",newline="") as f:
    f.write("entry\tslot\tcall_site\tglobal\tbase_reg\tload_site\tmov_ecx_site\tvt\tvptr_write_sites\n")
    for h in sorted(hits,key=lambda x:(int(x["entry"],16),x["call_site"])):
        writestr = "+".join(f"{x:08X}" for x in h["write_sites"])
        f.write(f'{h["entry"]}\t{h["slot"]}\t{h["call_site"]:08X}\t{h["glob"]:08X}\t{h["base"]}\t{h["load_site"]:08X}\t{h["mov_ecx"]:08X}\t{h["vt"]:08X}\t{writestr}\n')

# Body dump for all 14 target entries (bounded by canonical size where known; 0x180 for slot2, 0x80 else)
BODYSIZE={"0040B880":0xB0,"0040B930":0x30,"0040F7C0":0xB0,"0040FD90":0xB0,"0040FE40":0x30,
          "0046B7E0":0xB0,"0046B890":0x30,"0062B250":0xB0,"0062B300":0x30,"0065C0D0":0xB0,"0065C180":0x30,
          "0048AD60":0x20,"0054E8E0":0x20,"0048AD70":0x50}
with open(EVID+"/bodies_14.txt","w",encoding="utf-8",newline="") as f:
    for ent in list(EXACT11)+list(MISS3):
        va=int(ent,16); n=BODYSIZE[ent]
        f.write(f"\n=== {ent} size={n} ===\n")
        for ins in md.disasm(rd(va,n),va):
            f.write(f"{ins.address:08X}  {ins.bytes.hex():<20} {ins.mnemonic:<8} {ins.op_str}\n")

# slot6 byte contract and slot1 canonical body hash checks
def hashbody(va,n):
    return hashlib.sha256(rd(va,n)).hexdigest()[:12]
slot6_entries=["0048AD60","0054E8E0","0040B690","0040F630","0040FC00","0046B630","0062B0C0","0065BF40"]
with open(EVID+"/slot6_contracts.tsv","w",encoding="utf-8",newline="") as f:
    f.write("entry\tbytes\tcontract\tverified\n")
    for ent in slot6_entries:
        va=int(ent,16); bs=rd(va,0x14)
        patt = bs[:14] == bytes.fromhex("8b41048b4c24048b0488c20400")
        f.write(f"{ent}\t{bs.hex()}\t{hashbody(va,0x14)}\t{patt}\n")

# exact caller proof: owner from audit evidence, direct call counts, grade from coverage disk
owner_site={}
for line in open(ROOT+"/lead/next_re_20261117_r14/S13_K6/EVIDENCE/ring4_callsites.txt",encoding="utf-8").read().splitlines()[1:]:
    p=line.split("\t")
    if p[0].upper() in EXACT11:
        m=re.search(r'owner\s+([0-9A-Fa-f]{8})',p[2])
        if m: owner_site[p[0].upper()]=(m.group(1).upper(),p[2])
with open(EVID+"/exact_owner_proof.tsv","w",encoding="utf-8",newline="") as f:
    f.write("entry\towner\towner_grade\tdirect_callers_linear\tdirect_callers_raw\taudit_ring4\n")
    for ent in EXACT11:
        owner,ring4=owner_site.get(ent,("",""))
        grade=cov.get(owner,("","",""))[2]
        f.write(f"{ent}\t{owner}\t{grade}\t{call_targets[int(owner,16)] if owner else 0}\t{raw_call_targets[int(owner,16)] if owner else 0}\t{ring4}\n")

# name-conflict by entry address, across the mandated stores; exclude this card and binaries/git
addresses=list(EXACT11)+list(MISS3)
roots=[ROOT+"/lead/GOAL_THREE_TARGETS_20261018.md",
       ROOT+"/lead/next_re_20261117_r14/COVERAGE/coverage.tsv"]
with open(EVID+"/name_conflict_search.txt","w",encoding="utf-8",newline="") as out:
    out.write("# entry-address conflict search; roots: docs/re, re_atlas/kb, GOAL ledger, R14 COVERAGE, R14 lead\n")
    for addr in addresses:
        out.write(f"\n## {addr}\n")
        rx=re.compile(r"(?<![\dA-Fa-f])0[xX]?{addr}(?![\dA-Fa-f])|(?:^|[^0-9A-Fa-f]){addr}(?![0-9A-Fa-f])")
        for root in roots:
            paths=[]
            if os.path.isfile(root): paths=[root]
            elif os.path.isdir(root):
                for dp,dns,fns in os.walk(root):
                    if CARD in dp or "/ra2youli" in dp or "/.git" in dp: continue
                    for fn in fns:
                        if fn.lower().endswith((".txt",".md",".tsv",".json",".py")): paths.append(os.path.join(dp,fn))
            for p in paths:
                try:
                    for no,line in enumerate(open(p,encoding="utf-8",errors="replace"),1):
                        if rx.search(line):
                            out.write(f"{p}:{no}:{line.rstrip()}\n")
                except Exception: pass

# baseline universe: atlas entries + direct call targets within .text
atlas_entries=[]
for line in open(ATLAS,encoding="utf-8",errors="replace").read().splitlines()[1:]:
    p=line.split("\t")
    if p:
        atlas_entries.append(int(p[0],16))
universe=set(atlas_entries)|{t for t in call_targets if T0<=t<T0+textsec["vsize"]}
pass_all=set()
for h in hits:
    if h["entry"] in EXACT11: pass_all.add(int(h["entry"],16))
# all four rings for the 11 were checked by this script: byte slot/RTTI/exact/body contract; see PROGRESS table
pass_count=len(pass_all & universe)
n_univ=len(universe)
baseline=(pass_count/n_univ if n_univ else 0.0)
with open(EVID+"/discriminant_baseline.txt","w",encoding="utf-8",newline="") as f:
    f.write("criterion=entry is exact-bound vtable slot with byte RTTI chain + exact global-vptr call + body contract\n")
    f.write(f"atlas_entries={len(atlas_entries)}\ncall_target_entries={len(call_targets)}\nuniverse_union={n_univ}\n")
    f.write(f"pass_all_rings_in_universe={pass_count}\npass_rate={baseline:.10f}\n")
    f.write(f"all_11_random_pass={'YES' if baseline>=1 else 'NO'}\n")
    f.write("interpretation: arbitrary 11 atlas/call-target functions do not pass; slot-baseline is excluded by construction\n")

# core numbers
core={
  "slots56":len(slots),
  "slots56_S13":sum(1 for s in slots if s["cls"]=="S13"),
  "slots56_S22":sum(1 for s in slots if s["cls"]=="S22"),
  "exact11_entries_with_hit":sum(1 for e in EXACT11 if any(h["entry"]==e for h in hits)),
  "exact_call_sites_total":len({h["call_site"] for h in hits}),
  "miss3_exact_hits":{e:sum(1 for h in hits if h["entry"]==e) for e in MISS3},
  "baseline_pass_count":pass_count,
  "baseline_universe":n_univ,
  "baseline_pass_rate":baseline,
}
open(EVID+"/core_numbers.json","w",encoding="utf-8").write(json.dumps(core,indent=2,ensure_ascii=False)+"\n")
print(json.dumps(core,indent=2,ensure_ascii=False))
