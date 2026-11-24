import capstone, pefile, struct, bisect, json, time
P = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
COV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11_DIRECT\work"
pe = pefile.PE(P); data = open(P,"rb").read()
sec = [s for s in pe.sections if s.Name.rstrip(b"\x00")==b".text"][0]
BASE = pe.OPTIONAL_HEADER.ImageBase + sec.VirtualAddress
NBYTES = sec.Misc_VirtualSize
code = data[sec.PointerToRawData: sec.PointerToRawData+NBYTES]
TEXT_END = BASE + NBYTES
# --- full linear disassembly, skipdata=True ---
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.skipdata = True
n_instr=0; n_real=0; n_e8=0; n_e8_call=0
calls=[]  # (site_addr, target_addr)
for ins in md.disasm(code, BASE):
    n_instr+=1
    if ins.id!=0 and ins.mnemonic!=".byte": n_real+=1
    off = ins.address-BASE
    if 0<=off<len(code) and code[off]==0xE8:
        n_e8+=1
        if ins.mnemonic=="call" and ins.size==5 and off+5<=len(code):
            rel = struct.unpack_from("<i", code, off+1)[0]
            tgt = ins.address + 5 + rel
            calls.append((ins.address, tgt))
            n_e8_call+=1
print("SCAN", "n_instr",n_instr,"n_real",n_real,"n_e8",n_e8,"n_e8_call",n_e8_call,"text",hex(BASE),hex(TEXT_END))
# self-check (19): capstone mem.index trap - demonstrate op.index returns 0 for no-index mem
md2 = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md2.detail=True
x = list(md2.disasm(b"\xff\x10", 0x1000))[0]  # call [eax]
op = x.operands[0]
print("SELFCHECK19", "mem.index", op.mem.index, "type", type(op.mem.index).__name__, "is_None", op.mem.index is None)
# dump all calls
with open(OUT+r"\all_e8_calls.tsv","w",encoding="utf8") as f:
    f.write("site\ttarget\n")
    for s,t in calls: f.write(f"{s:08X}\t{t:08X}\n")
# --- atlas functions ---
at = {}
for line in open(ATLAS,encoding="utf8").read().splitlines()[1:]:
    if not line.strip(): continue
    c=line.split("\t"); e=c[0].strip().upper();
    if not e: continue
    at[e]=(int(c[1]), int(c[0],16), int(c[2]))
# at[entry] = (size, entry_int, n_instr)
fn_list = sorted([(eiv, sz, e) for e,(sz,eiv,ni) in at.items()])
fn_entries = [x[0] for x in fn_list]
def caller_of(site):
    i=bisect.bisect_right(fn_entries, site)-1
    # walk backwards looking for a containing function (atlas may overlap)
    best=None
    for j in range(i, max(-1, i-40), -1):
        e,sz,eh = fn_list[j]
        if site < e+sz:
            if best is None or sz<best[1]: best=(eh,sz,e)
    return best  # (entry_hex, size, entry_int)
# --- coverage S11 static rows ---
covrows=[]
for line in open(COV,encoding="utf8").read().splitlines()[1:]:
    if not line.strip(): continue
    c=line.split("\t")
    if len(c)<8: continue
    entry=c[0].strip().upper(); sub=c[1].strip(); grade=c[4].strip(); name=c[2].strip(); sem=c[3].strip()
    if sub.upper()=="S11" and entry in at:
        covrows.append((entry,grade,name,sem))
static = [r for r in covrows if r[1]=="[静态推断]"]
print("COV", "s11_atlas", len(covrows), "static", len(static), "proved", sum(1 for r in covrows if r[1]=="[已证]"))
# target->sites map
from collections import defaultdict
tmap=defaultdict(list)
for s,t in calls: tmap[f"{t:08X}"].append(s)
# resolve each static row
res=[]
for entry,grade,name,sem in static:
    eiv=int(entry,16); sz,ni = at[entry][0], at[entry][2]
    body_end=eiv+sz
    sites=tmap.get(entry,[])
    for s in sites:
        caller=caller_of(s)
        # anti-self-loop: caller function range must not contain entry; fallback: site not in target body
        if caller:
            ce,csz,ceiv=caller
            selfloop = (ceiv<=eiv<ceiv+csz)
            caller_desc=f"{ce}+{csz}"
        else:
            selfloop = (eiv<=s<body_end)
            caller_desc="UNKNOWN"
        res.append((entry, name, sem, f"{s:08X}", caller_desc, "SELFLOOP" if selfloop else "OK"))
with open(OUT+r"\s11_direct_raw.tsv","w",encoding="utf8") as f:
    f.write("entry\tname\tsem\tsite\tcaller\tstatus\n")
    for r in res: f.write("\t".join(r)+"\n")
# summary
entries_with_site=set(r[0] for r in res)
entries_pass=set(r[0] for r in res if r[5]=="OK")
print("RESULT", "static_entries", len(static), "entries_with_any_site", len(entries_with_site), "entries_with_OK_site", len(entries_pass), "total_raw_sites", len(res))
json.dump({"n_instr":n_instr,"n_real":n_real,"n_e8":n_e8,"n_e8_call":n_e8_call,"base":hex(BASE),"end":hex(TEXT_END),"static_entries":len(static),"entries_ok":len(entries_pass)}, open(OUT+r"\scan_meta.json","w"))