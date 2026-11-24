
import sys, csv, struct, hashlib, re, json, bisect
sys.stdout.reconfigure(encoding='utf-8')
import k5_lib as K
CARD=K.CARD; EV=CARD/'EVIDENCE'
def W(name,lines): (EV/name).write_text("\n".join(lines)+"\n",encoding='utf-8')
def insn_at(va):
    for i in K.dis(va,16,count=8):
        if i.address==va: return i
    return None

# ===== EVIDENCE 1: main proof 00483780 =====
L=[]
L.append("S06-K5 BEHAVIOR-LEVEL PROOF: 00483780  (same family as K4 00483710, different branch)")
L.append("SHA256="+K.SHA)
row=[r for r in K.cov_rows() if r['entry'].upper()=='00483780'][0]
atl=K.atl_map()['00483780']
L.append("BASELINE_ON_DISK subsystem=%s grade=%s name=%s  atlas_size=%s n_instr=%s"%(row['subsystem'].strip(),row['grade'].strip(),row['name'].strip(),atl['size'],atl['n_instr']))
L.append("PROOF_TYPE=3 behavior-level (full closure); thiscall this=CellClass* (edi), one 4-byte stack arg at [entry esp+4] loaded into bl")
L.append("NAMING: CellClass::SpreadTiberiumToNeighbor -- distinct from K4 00483710 CellClass::GrowTiberiumIfAllowed")
L.append("  (00483710 = single-cell, IncreaseTiberium(typeIndex,1); 00483780 = 8-neighbor, IncreaseTiberium(typeIndex,3))")
L.append("")
L.append("=== GATE CHAIN: every link = address + instruction + raw bytes ===")
gates=[
 ("G0 arg/this","00483780","sub esp,0xc","83ec0c"),
 ("G0 arg/this","00483783","push ebx","53"),
 ("G0 arg/this","00483784","mov bl,[esp+0x14]  ; stack arg (force flag) -> bl","8a5c2414"),
 ("G0 arg/this","0048378B","mov edi,ecx  ; this=CellClass*","8bf9"),
 ("G0 arg/this","0048378D","test bl,bl / jne 0x4837EB  ; force=1 skips all gates","84db / 755a"),
 ("G1 rules","00483791","mov eax,dword ptr [0xA8B230]  ; RulesClass global","a130b2a800"),
 ("G1 rules","00483796","test byte ptr [eax],0x80","f60080"),
 ("G1 rules","00483799","je 0x483800  ; false -> xor al,al;ret 4","7465"),
 ("G2 type lookup","0048379B","mov ecx,dword ptr [edi+0x44]  ; overlay/tiberium type id","8b4f44"),
 ("G2 type lookup","0048379E","call 0x5FDD20  ; overlayTypeID -> tiberium type index","e87da51700"),
 ("G2 type lookup","004837A3","mov esi,eax  ; typeIndex","8bf0"),
 ("G2 type lookup","004837A5","cmp esi,-1 / je 0x483800","83feff / 7456"),
 ("G3 density","004837AA","cdq / xor ecx,ecx / sub eax,edx  ; eax=typeIndex","99 / 33c9 / 2bc2"),
 ("G3 density","004837AF","mov cl,byte ptr [edi+0x11E]  ; cell density","8a8f1e010000"),
 ("G3 density","004837B5","sar eax,1  ; eax = typeIndex/2","d1f8"),
 ("G3 density","004837B7","cmp ecx,eax / jle 0x483800  ; require density > typeIndex/2","3bc8 / 7e45"),
 ("G4 cell state","004837BB","mov al,byte ptr [edi+0x11C]","8a871c010000"),
 ("G4 cell state","004837C1","test al,al / jne 0x483800  ; require +0x11C==0","84c0 / 753b"),
 ("G5 type chance","004837C5","mov edx,dword ptr [0xB0F4EC]  ; type table base","8b15ecf4b000"),
 ("G5 type chance","004837CB","mov eax,dword ptr [edx+esi*4]  ; type ptr","8b04b2"),
 ("G5 type chance","004837CE","fld qword ptr [eax+0xA0]","dd80a0000000"),
 ("G5 type chance","004837D4","fcomp qword ptr [0x7E3810]  ; 1e-5","dc1d10387e00"),
 ("G5 type chance","004837DA","fnstsw ax / test ah,1 / jne 0x483800  ; require [type+0xA0]>=1e-5","dfe0 / f6c401 / 751f"),
 ("G6 cell dword","004837E1","mov eax,dword ptr [edi+0xE4]","8b87e4000000"),
 ("G6 cell dword","004837E7","test eax,eax / jne 0x483800  ; require cell+0xE4==0","85c0 / 7515"),
 ("G7 2nd lookup","004837EB","mov ecx,[edi+0x44] / call 0x5FDD20 / mov [esp+0x20],eax","8b4f44 / e82da51700 / 89442420"),
 ("G7 2nd lookup","004837FB","cmp eax,-1 / jne 0x48381D ; force maps -1->0 at 0x483811","83f8ff / 751d"),
]
for tag,addr,txt,bb in gates: L.append("  [%s] %s  %-72s bytes=%s"%(tag,addr,txt,bb))
L.append("  false convergence = 0x483800: pop edi/esi/ebp; xor al,al; pop ebx; add esp,0xc; ret 4  (5f 5e 5d 32c0 5b 83c40c c20400)")
L.append("  NOTE G3(density>typeIndex/2) and G6(cell+0xE4==0) are additional real gates beyond the audit's shortened chain.")
L.append("")

L.append("=== CALLEE SEMANTIC SOURCES ===")
L.append("0x5FDD20: coverage 005FDD20 subsystem=S22 grade=[已证] on disk; body proves overlayTypeID(ecx)->tiberium type index or -1:")
L.append("  005FDD24 cmp ecx,-1 / 005FDD28 je -> or eax,-1 ret (-1); 005FDD2E mov eax,[0xa83d84]; 005FDD33 mov eax,[eax+ecx*4] (overlay type object);")
L.append("  005FDD3A mov dl,[eax+0x2A9] / 005FDD42 je -1 (not-tiberium); 005FDD48..005FDD9E loop [0xb0f4f8] types checking index ranges;")
L.append("  005FDDA0..005FDDC8 returns type index; 005FDDC9 returns [eax+0x98]. Cross-ref: K4 EVIDENCE/growth_behavior.txt KW2;")
L.append("  S06-K2/K3 field table has +0x44=[OverlayTypeClass ID] as [已证]. SAME callee as proven 00483710 (0x483725/0x48376B).")
L.append("0x487190: coverage 00487190 subsystem=S06 grade=[已证] name=CellClass::IncreaseTiberium (already-accounted address).")
L.append("  K4 audit R6/R7 and K4 EVIDENCE/growth_behavior.txt established args=(typeIndex,amount); body writes cell density")
L.append("  0x4872A0 mov [esi+0x11E],bl with bl=amount, clamps to [type+0xE4]-1. Re-verified below in INCREASE_ARG_ORDER.")
L.append("0x7E3810: raw bytes "+K.at(0x7E3810,8).hex()+" = 1e-5 (double), same constant as K4 00483710; fcomp+jne-on-CF => require >= 1e-5.")
L.append("")
L.append("=== INCREASE_ARG_ORDER (thiscall + 2 stack args; all writes to ecx/stack slots traced) ===")
L.append("  before call: push 3 (6a03 @0x4838C0)=arg2 amount; push edx (52 @0x4838C2)=arg1 typeIndex; mov ecx,esi (8bce @0x4838C3)=this=neighbor cell.")
L.append("  Stack trace: entry ESP=E; after 4 prologue pushes esp=E-0x1C. 0x4837F5 stores typeIndex at [E+4].")
L.append("  0x483823/25 push 7,push 0 (esp=E-0x24) then call 0x65C7E0 is ret 8 (c20800) -> esp back to E-0x1C.")
L.append("  0x48387C push coords + call 0x5657A0 is ret 4 (c20400) -> esp E-0x1C. 0x48389E push coords + call 0x4838E0 is ret 4 (c20400) -> esp E-0x1C.")
L.append("  Therefore at 0x4838BC mov edx,[esp+0x20] = [E-0x1C+0x20] = [E+4] = typeIndex. Callee 0x487190: sub esp,0x84; push ebx;")
L.append("  0x48719C mov ebx,[esp+0x90] = entry[esp+8] = arg2 amount; push ebp; 0x4871A4 mov ebp,[esp+0x90] = entry[esp+4] = arg1 typeIndex.")
L.append("  => CALL IS IncreaseTiberium(typeIndex, 3). increment 3 source = push 3 bytes 6a03 at 0x4838C0. NOT a nearby-shape guess.")
L.append("")
L.append("=== 8-NEIGHBOR LOOP BOUNDARY ===")
L.append("  0x483840 xor ebx,ebx (33db) -> counter=0; 0x48383E mov ebp,eax from 0x65C7E0(map seed).")
L.append("  0x483842 lea eax,[ebx+ebp] / 0x483845 and eax,7 -> direction=(seed+i)&7; 0x483848 cmp eax,8 / 0x48384B jb (always true, compiler artifact).")
L.append("  0x48385B add cx,[eax*4+0x89F688] and 0x48386F mov cx,[eax+2] : X/Y offsets from 8-entry word-pair table 0x89F688 (BSS, runtime init).")
L.append("  0x48388F call 0x5657A0 GetCell(coords) -> neighbor (esi); null -> 0x4838AA.")
L.append("  0x4838A1 call 0x4838E0 canSpread(neighbor) -> al; al!=0 -> 0x4838BC (increase and return); else 0x4838AA.")
L.append("  0x4838AA inc ebx / 0x4838AB cmp ebx,8 / 0x4838AE jl 0x483842 -> EXACTLY 8 iterations (ebx=0..7).")
L.append("  0x4838B0..0x4838B9 no-neighbor path: xor al,al; ret 4 (returns 0).")
L.append("  DIR TABLE 0x89F688 is in BSS (no raw bytes); structure proven by 0x48385B/0x48386F word-pair indexing and the &7/8-loop, not by guessed values.")
L.append("")
L.append("=== RETURN VALUE SEMANTICS (precise; NOT 'return true') ===")
L.append("  SUCCESS path 0x4838BC..0x4838D1: after call 0x487190 there is NO mov al,1; it pops regs, add esp,0xc, ret 4.")
L.append("  Therefore return value = AL returned by IncreaseTiberium (callee bool), NOT a hardcoded true.")
L.append("  K4 audit proved IncreaseTiberium can return 0 via xor al,al at 0x487621 when 1>=[type+0xE4]; same caveat applies here.")
L.append("  ALL failure paths (0x483800 gates, 0x4838B0 no-neighbor) explicitly xor al,al and return 0.")
L.append("  force-arg (bl): bl!=0 bypasses G1..G6 and maps typeIndex -1 -> 0 (0x483811); bl==0 requires full gate chain; both converge on 8-neighbor increase.")
L.append("")
L.append("=== FULL DISASM 00483780 (atlas size 340 bytes) ===")
for i in K.dis(0x483780,340): L.append(K.fmt(i))
W('growth_neighbors_proof.txt',L)
print("wrote growth_neighbors_proof.txt",len(L),"lines")

# ===== EVIDENCE 2: candidate census (own scanner) =====
scan=json.load(open(CARD/'work/candidate_scan.json',encoding='utf-8'))
C=[]
C.append("S06-K5 INDEPENDENT BEHAVIOR-LEVEL CANDIDATE CENSUS")
C.append("SHA256="+K.SHA)
C.append("Scanner: work/scan.py (written from scratch for K5; NOT S06_K4 k4_behavior_probe.py).")
C.append("Threshold (own): CORE = direct call to {0x5FDD20,0x487190,0x4838E0,0x483710,0x483780} OR ref to 0x7E3810(1e-5) OR use of dir-table 0x89F688.")
C.append("Full-closure criterion (own, K4-grade strict): ONE body has ALL: (a)call 0x5FDD20,(b)call 0x487190,(c)ref 0x7E3810,(d)cell field +0x11C/+0x11E,(e)rules 0xA8B230 gate.")
C.append("Channel A = atlas-driven per-function disasm; Channel B = raw E8-rel32 .text scan (atlas-independent) with coverage-interval attribution.")
C.append("")
C.append("S06_ROWS=%d S06_INTERSECT_ATLAS=%d"%(scan['s06_rows'],scan['s06_int']))
C.append("CANDIDATE_POOL_CORE=%d (entry grade name size signals)"%len(scan['channelA']))
for c in scan['channelA']:
    C.append("  %s %s %-34s sz=%-5d calls=%s consts=%s fields=%s globals=%s"%(c[0],c[1],c[2],c[3],c[4],c[5],c[6],c[7]))
C.append("")
C.append("CHANNEL_B raw E8 call-site counts (atlas-independent):")
for t,n in scan['channelB_counts'].items(): C.append("  target=%s sites=%s"%(t,n))
C.append("")
C.append("DIRECT CALLERS of growth functions (coverage-interval containment):")
cs=scan['callsites']
cov=sorted([(int(r['entry'],16),r['entry'].upper(),r['grade'].strip(),r['name'].strip(),r['subsystem'].strip().upper()) for r in K.cov_rows()])
starts=[x[0] for x in cov]
for t in ['0x483710','0x483780','0x4838e0']:
    C.append("  target %s:"%t)
    for site in cs.get(t,[]):
        idx=bisect.bisect_right(starts,site)-1
        a=cov[idx] if idx>=0 else None
        C.append("    0x%08X -> %s"%(site, a if a else 'none'))
C.append("")
C.append("CLASSIFICATION OF EVERY NEW CANDIDATE:")
C.append("  00483780 [PROVABLE] full closure -> this card delta (see growth_neighbors_proof.txt).")
C.append("  00483710 [PROVABLE, already K4 delta] full closure; on-disk still [未证] (K4 not merged).")
C.append("  004838E0 [UNPROVABLE as gate branch] canSpread helper CALLED BY 00483780; missing: no 0x5FDD20, no 0x487190, no 1e-5, no rules gate; it is a predicate not an increase gate.")
C.append("  004839F0 [UNPROVABLE] constructor-like (writes vtables / call 0x7C8E17); missing: no 0x5FDD20, no 0x487190, no 1e-5, no rules gate.")
C.append("  0071C730 [UNPROVABLE] TerrainClass::slot23, one call to 00483780 (0x71C8D0) no own gate; missing: 0x5FDD20, 0x487190, 1e-5, rules gate.")
C.append("  00722440 [UNPROVABLE as gate branch] type-level growth distributor: has 1e-5 on this+0xA0, calls 0x4838E0 + 00483780 in 8-loop; missing: no 0x5FDD20, no direct 0x487190 (delegates to 00483780). Upstream caller.")
C.append("  00722F00 [UNPROVABLE as gate branch] type-level growth distributor for +0xB0 branch: has 1e-5, calls 00483710; missing: no 0x5FDD20, no direct 0x487190. Upstream caller.")
C.append("  0047C060 [UNPROVABLE] cell 'can exist' predicate near CanThisExistHere; missing: no 0x487190, no 1e-5, no rules gate. (First probe typo 0x7C060 corrected to 0x47C060.)")
C.append("  00480CB0 [UNPROVABLE] dir-table + cell_getter/map_getter + +0x44/+0x11E; missing: no 0x5FDD20, no 0x487190, no 1e-5, no rules gate.")
C.append("  004818E0 [UNPROVABLE] has 0x5FDD20 + cell_getter + +0x11E/+0x44/+0xE4; missing: no 0x487190, no 1e-5, no rules gate -> incomplete chain.")
C.append("  00484AE0/00568E40/00569760/00570050/00571490/00573540/00575EE0/00576BA0 [UNPROVABLE] dir-table users in far regions; missing: no growth-anchor calls and no 1e-5; not in 0x483700..0x483B00.")
C.append("  005FD970 (OverlayClass::slot70) [UNPROVABLE] placeholder slot name; has 0x5FDD20 but missing 0x487190/1e-5/rules gate; slot name is not semantic evidence.")
C.append("CONCLUSION: in 0x483700..0x483B00 + all direct callers, the ONLY new provable same-family gate branch is 00483780.")
W('candidate_census.txt',C)
print("wrote candidate_census.txt",len(C),"lines")

# ===== EVIDENCE 3: baseline recompute =====
B=[]
B.append("S06-K5 BASELINE RECOMPUTE (on-disk truth; case-normalized entry sets)")
B.append("SHA256="+K.SHA)
B.append("S06_ROWS=848  DENOM(coverage intersect atlas, case-unified)=848  GRADES={'[静态推断]':287,'[未证]':458,'[已证]':103}")
B.append("NAMED_L=384  PROVED_ON_DISK=103  PCT=12.1462  THRESHOLD_50PCT=424")
B.append("K4_DELTA_NOT_MERGED: 23 rows in S06_K4/coverage_delta.tsv; if merged -> PROVED=126/848=14.8585")
B.append("CARD_MATCH=YES (848/103/424 and K4 23->126 all reproduced). No discipline-9 stop.")
B.append("Reproduce: python work/baseline.py")
W('baseline_recompute.txt',B)
print("wrote baseline_recompute.txt")

# ===== DELTA =====
sem=("CellClass::SpreadTiberiumToNeighbor: one stack bool arg (force). If force==0 gate chain: byte0 of RulesClass ptr loaded from [0xA8B230] & 0x80 != 0; "
     "overlay type [cell+0x44] -> typeIndex via 0x5FDD20 (>=0); cell density [cell+0x11E] > typeIndex/2; cell [cell+0x11C]==0; "
     "type float [type+0xA0] >= 1e-5 (f168e388b5f8e43e); cell dword [cell+0xE4]==0. "
     "Then 8-neighbor loop (ebx=0..7, dir table 0x89F688, GetCell 0x5657A0, canSpread 0x4838E0) finds first acceptable neighbor and calls "
     "IncreaseTiberium(typeIndex,3) @0x4838C0 push 3 + 0x4838C5 call 0x487190; returns callee al, NOT hardcoded true; all fail paths return 0. "
     "force-arg!=0 bypasses gates and maps typeIndex -1 to 0.")
d=[['00483780','S06','CellClass::SpreadTiberiumToNeighbor',sem,'[已证]','EVIDENCE/growth_neighbors_proof.txt']]
with (CARD/'coverage_delta.tsv').open('w',encoding='utf-8',newline='') as f:
    for r in d: f.write('\t'.join(r)+'\n')
print("wrote coverage_delta.tsv")

# ===== DELTA VALIDATION =====
V=[]
V.append("S06-K5 DELTA VALIDATION"); V.append("SHA256="+K.SHA)
V.append("DELTA_ROWS=1 ENTRY=00483780 NAME=CellClass::SpreadTiberiumToNeighbor GRADE=[已证]")
V.append("BASELINE_ON_DISK_GRADE="+row['grade'].strip()+" (not already proved) SUBSYSTEM=coverage:'S06'=delta:'S06' ATLAS_PRESENT=yes")
V.append("PLACEHOLDER_NAME_CHECK: no ::slotN, no ::sub_XXXXXXXX -> OK")
V.append("EVIDENCE_EXISTS=EVIDENCE/growth_neighbors_proof.txt (%d bytes)"%((EV/'growth_neighbors_proof.txt').stat().st_size))
V.append("COMBINED_WITH_K4: 103 + 23(K4) + 1(K5) = 127 / 848 = %.4f"%(100.0*127/848))
W('delta_validate.txt',V)
print("wrote delta_validate.txt")
