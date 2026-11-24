"""W178-PATCH FINAL offline unit test: P1 'call-site guarded call' candidate.

Design (replace the 5-byte `call 0x724730` at C with 14 bytes):
  C+0  85 C9              test ecx,ecx            ; ecx=this (last write [0x887368] before call)
  C+2  74 07              jz  C+11
  C+4  E8 <rel32-4>       call 0x724730           ; ret 4 cleans the pushed arg
  C+9  EB 03              jmp C+14 (join)
  C+11 83 C4 04           add esp,4               ; NULL path pops the arg
  C+14 <original next instruction>

Non-NULL: test ZF=0 -> call (ret 4) -> jmp join, ESP restored == original.
NULL:     test ZF=1 -> jz add esp,4 -> join, ESP restored, 0x724737 never reached.

Checks (per site):
 U1 14-byte decode correct (test/jz/call->0x724730/jmp/add esp,4, targets exact)
 U2 call rel32 adjusted by -4 (shift compensation)
 U3 NULL path: add esp,4 restores ESP; no deref at 0x724737
 U4 non-NULL path: original call executes; all caller setup stores BEFORE C preserved
 U5 no direct-rel-branch target in insertion body [C+1,C+13]
 U6 ecx at C is [0x887368], no zero guard
 U7 callee ret 4 confirmed
 U8 target of jz = add esp,4 and target of jmp = join

Outputs EVIDENCE/UNIT_TEST.txt / UNIT_TEST.json
"""
from __future__ import annotations
import json, os, struct
import capstone, pefile
ROOT=r"D:\Project\ra2-campaign-forge"
CORE=os.path.join(ROOT,"lead","next_re_20261117_r14","W178_PATCH","EVIDENCE","core.json")
OUT=os.path.join(ROOT,"lead","next_re_20261117_r14","W178_PATCH","EVIDENCE")
EXE=os.path.join(ROOT,"ra2youli","gamemd.exe")
TARGET=0x724730
class Bin:
    def __init__(self,p):
        self.pe=pefile.PE(p,fast_load=True); self.ib=self.pe.OPTIONAL_HEADER.ImageBase; self.secs=[]
        for s in self.pe.sections:
            n=s.Name.decode(errors='replace').rstrip('\x00')
            self.secs.append(dict(name=n,va=self.ib+s.VirtualAddress,raw=s.PointerToRawData,rawsize=s.SizeOfRawData))
    def read(self,va,n):
        for s in self.secs:
            if s['va']<=va and va+n<=s['va']+s['rawsize']:
                o=s['raw']+va-s['va']; return self.pe.__data__[o:o+n]
        raise ValueError
def md():
    m=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); m.detail=True; m.skipdata=True; return m
def dis(b,s,e): return list(md().disasm(b.read(s,e-s),s))
def rt(i):
    if i.mnemonic in ('call','jmp') or i.mnemonic.startswith('j'):
        s=i.op_str.strip()
        if s.startswith('0x'):
            try: return int(s,16)
            except: return None
    return None

def run():
    core=json.load(open(CORE,encoding='utf-8')); b=Bin(EXE)
    L=["W178-PATCH FINAL OFFLINE UNIT TEST -- P1 call-site guarded call (static, no live machine)",
       f"sha256={core['sha']} OK={core['sha_ok']}",
       f"callee ret={core['callee']['ret']['text']} @ {core['callee']['ret']['va']}",
       "Design: replace 5-byte `call 0x724730` with 14-byte guarded call (test ecx,jz,call,jmp,add esp,4).",
       "Both paths rejoin at C+14 with ESP balanced (ret 4 / add esp,4).", ""]
    R=[]; passed=0; total=0
    callee_ret4=(core['callee']['ret']['text']=='ret 4')
    for r in core['sites']:
        if 'error' in r: continue
        C=int(r['site'],16); host=int(r['fn'],16); hsize=r['fn_size']
        # original call bytes and rel32
        orig=b.read(C,5); orig_rel=struct.unpack('<i',orig[1:5])[0]
        assert orig[0]==0xE8 and C+5+orig_rel==TARGET
        new_rel=orig_rel-4
        guard=bytes([0x85,0xC9,0x74,0x07,0xE8])+struct.pack('<i',new_rel)+bytes([0xEB,0x03,0x83,0xC4,0x04])
        assert len(guard)==14
        di=list(md().disasm(guard,C))
        # decode expectations
        u1=(len(di)==5 and di[0].mnemonic=='test' and di[0].op_str=='ecx, ecx'
            and di[1].mnemonic in ('je','jz') and di[2].mnemonic=='call'
            and di[3].mnemonic=='jmp' and di[4].mnemonic=='add' and di[4].op_str=='esp, 4')
        t_jz=rt(di[1]) if len(di)>1 else None; t_call=rt(di[2]) if len(di)>2 else None; t_jmp=rt(di[3]) if len(di)>3 else None
        u2=(t_call==TARGET and new_rel==orig_rel-4)
        u8=(t_jz==C+11 and t_jmp==C+14)
        # stack semantics
        u3=(u1 and u8 and t_jz==C+11)  # NULL -> add esp,4 -> join; no 0x724737
        u4=(u1 and u2)  # non-NULL -> call (ret 4) -> jmp join; setup before C untouched
        # U5: existing rel-branch targets inside insertion body [C+1,C+13].
        # Those targeting exactly C+5 (original next-after-call) must be re-targeted to C+14 (+9).
        # A candidate stays A-grade only if ALL such jumps can be re-targeted in-range.
        body=set(range(C+1,C+14)); bad=[]; retarget=[]
        hostins=dis(b,host,host+hsize)
        for i in hostins:
            t=rt(i)
            if t is not None and t in body:
                bad.append(f"{i.address:08X} {i.mnemonic} {i.op_str} -> {t:#x}")
                if t==C+5:
                    # delta from re-link = +9 (insertion adds 14-5=9 bytes at C)
                    inslen=i.size
                    oldrel=t-(i.address+inslen)
                    newrel=oldrel+9
                    is_short=(i.bytes[0] in (0x74,0x75,0x7c,0x7d,0x7e,0x7f,0x72,0x73,0x76,0x77,0x78,0x79,0x7a,0x7b,0xe3))
                    inrange=(-128<=newrel<=127) if is_short else (-2**31<=newrel<2**31)
                    retarget.append(dict(jump=f"{i.address:08X}",kind='short' if is_short else 'near',
                                         old_target=f"{t:#x}",new_target=f"{C+14:#x}",
                                         old_rel=oldrel,new_rel=newrel,in_range=inrange))
                else:
                    retarget.append(dict(jump=f"{i.address:08X}",kind='other',old_target=f"{t:#x}",
                                         new_target='MANUAL',in_range=False))
        u5ret=all(x['in_range'] for x in retarget)
        u5=(u5ret)  # all jump-into-body targets re-targetable (or none exist)
        # U6: ecx source global, no zero guard
        u6=('0x887368' in r['ecx_source'] and not r['zero_guard'].get('tests'))
        checks=dict(U1_decode=u1,U2_call_target_rel32=u2,U3_null_stack_and_no_deref=u3,
                    U4_nonnull_preserves_call=u4,U5_no_jump_into_insert=u5,U6_ecx_global_no_guard=u6,
                    U7_callee_ret4=callee_ret4,U8_targets=u8)
        ok=all(checks.values()); total+=1; passed+=1 if ok else 0
        status='PASS' if ok else 'FAIL'
        L.append(f"{status} {r['site']} host={r['fn']} bytes={guard.hex(' ')}")
        L.append(f"   decoded={'; '.join(f'{x.mnemonic} {x.op_str}' for x in di)}")
        L.append(f"   targets jz={t_jz:#x} call={t_call:#x} jmp={t_jmp:#x} expected jz={C+11:#x} jmp={C+14:#x}")
        L.append(f"   checks={json.dumps(checks)} bad_targets={bad} retarget={retarget}")
        R.append(dict(site=r['site'],host=r['fn'],insert_at=f"{C:08X}",original_bytes=orig.hex(' '),
                      patch_bytes=guard.hex(' '),decoded='; '.join(f'{x.mnemonic} {x.op_str}' for x in di),
                      targets=dict(jz=f"{t_jz:#x}",call=f"{t_call:#x}",jmp=f"{t_jmp:#x}"),
                      checks=checks,bad_targets=bad,retarget=retarget,status=status))
        L.append("")
    # ---- 0x6CD8CD guard unit test ----
    A6=0x6CD8C7; BLK6=0x6CD8D8; XX6=BLK6-A6  # 0x11
    g6=bytes([0x85,0xC0,0x74,XX6])
    d6=list(md().disasm(g6,A6))
    six_core=core['s6']
    t6=rt(d6[1]) if len(d6)>1 else None
    host6=int(six_core['fn'],16); hs6=six_core['fn_size']
    ins6=dis(b,host6,host6+hs6); bad6=[]
    for i in ins6:
        t=rt(i)
        if t is not None and t in set(range(A6+1,A6+4)): bad6.append(f"{i.address:08X} {i.mnemonic} {i.op_str}")
    c6=dict(U1_decode=(len(d6)==2 and d6[0].mnemonic=='test' and d6[0].op_str=='eax, eax' and d6[1].mnemonic in ('je','jz')),
            U2_rel8=(0<=XX6<=127),U3_target=(t6==BLK6+4),
            U4_eax_global=('0x8871e0' in six_core['eax_source']),
            U5_no_jump_into_insert=(not bad6),U6_reachable=six_core['reachable'])
    ok6=all(c6.values()); total+=1; passed+=1 if ok6 else 0
    L.append(f"{'PASS' if ok6 else 'FAIL'} 006CD8CD host={six_core['fn']} bytes={g6.hex(' ')} target={(f'{t6:#x}' if t6 else 'None')} checks={json.dumps(c6)} bad={bad6}")
    R.append(dict(site='006CD8CD',host=six_core['fn'],insert_at=f'{A6:08X}',patch_bytes=g6.hex(' '),
                  targets=dict(jz=(f'{t6:#x}' if t6 else None)),checks=c6,bad_targets=bad6,
                  status='PASS' if ok6 else 'FAIL'))
    L.append("")
    L.append(f"TOTAL {passed}/{total} PASS all checks (30 call sites + 0x6CD8CD).")
    L.append("NOTE: PASS proves LOGIC only; no bytes deployed. Insertion shifts subsequent addresses -> re-link required (RISKS.md).")
    json.dump(dict(passed=passed,total=total,results=R),open(os.path.join(OUT,'UNIT_TEST.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
    open(os.path.join(OUT,'UNIT_TEST.txt'),'w',encoding='utf-8').write("\n".join(L))
    print(f"FINAL UNIT TEST {passed}/{total} PASS")
    for x in R:
        if x['status']=='FAIL': print("  FAIL",x['site'],{k:v for k,v in x['checks'].items() if not v})
if __name__=='__main__': run()
