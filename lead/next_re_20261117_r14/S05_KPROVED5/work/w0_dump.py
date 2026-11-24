# -*- coding: utf-8 -*-
"""S05-KPROVED5 · w0: 精确反汇编 22 名候选（用 classification.tsv 的 ext_lo/ext_hi，不跨函数）。
③b 模式探测（供选题，最终以人工逐条核对 EVIDENCE 为准）。"""
import os, sys, csv, json
sys.path.insert(0, os.path.dirname(__file__))
import ax_lib
from capstone import *
from capstone.x86 import *

CLS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_RING24\EVIDENCE\classification.tsv"
OUT = os.path.join(os.path.dirname(__file__), "disasm")
os.makedirs(OUT, exist_ok=True)

CAND = ["0040BA50","0040CDC0","00410220","00410230","00410BE0","0050EA00","00512D30",
        "00513100","005134D0","005F9720","006F3F40","006F4A70","006F6CA0","00708D70",
        "00709A30","00709A40","0070C250","0070E280","0070E2B0","00711EB0","00711F00","007171A0"]

ext = {}
meta = {}
for r in csv.DictReader(open(CLS, encoding='utf-8'), delimiter='\t'):
    e = r['entry'].upper()
    if e in CAND:
        try:
            ext[e] = (int(r['ext_lo'], 16), int(r['ext_hi'], 16))
        except Exception:
            pass
        meta[e] = dict(name=r['name'], rtti=r['rtti_classes'], vt=r['rtti_vt'], slot=r['rtti_slot'],
                       sites=r['ring4_direct_sites'], ndir=r['n_direct_out'])

pe = ax_lib.load()
MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.detail = True; MD.skipdata = True

allres = {}
for e in CAND:
    lo, hi = ext[e]
    off = pe.off(lo); size = hi - lo
    raw = pe.buf[off:off+size]
    insns = list(MD.disasm(raw, lo))
    lines = []
    for i in insns:
        lines.append("%08X  +0x%04X  %-8s %s" % (i.address, i.address-lo, i.mnemonic, i.op_str))
    with open(os.path.join(OUT, "DIS_%s.txt" % e), 'w', encoding='utf-8') as f:
        f.write("\n".join(lines) + "\n")
    # ③b 机械特征（在精确 extent 内）
    addrs = [i.address for i in insns]; idx = {a:k for k,a in enumerate(addrs)}
    jt=[]; err=[]; loops=[]; guards={}
    for k,i in enumerate(insns):
        # jump table: jmp dword ptr [reg*4+...]
        if i.mnemonic=='jmp' and '*' in i.op_str and 'ptr' in i.op_str:
            jt.append((i.address-lo, i.op_str))
        # err: cmp ...,-1 / 0x80004002 / sentinel 0x7fff then jcc/ret within 8
        if i.mnemonic=='cmp' and any(x in i.op_str for x in ['-1','0x80004002','0x7fff','0xffff']):
            for z in insns[k+1:k+9]:
                if z.mnemonic.startswith('j') or z.mnemonic.startswith('ret') or z.mnemonic.startswith('set') or z.mnemonic.startswith('cmov'):
                    err.append((i.address-lo, i.op_str)); break
        # jcc targets (for guard chains)
        if i.mnemonic.startswith('j') and i.mnemonic!='jmp':
            try:
                t=int(i.op_str,16)
                guards.setdefault(t,[]).append(i.address-lo)
            except: pass
        # backedges with body write+cmp+advance
        if i.mnemonic.startswith('j') and i.mnemonic!='jmp':
            try: t=int(i.op_str,16)
            except: continue
            ti=idx.get(t)
            if ti is None or ti>k: continue
            body=insns[ti:k+1]
            if len(body)<4: continue
            w=bc=adv=False
            for z in body:
                dst=z.op_str.split(',')[0].strip() if ',' in z.op_str else ''
                if z.mnemonic in ('mov','or','and','add','sub','xor','inc','dec') and dst.startswith(('dword ptr','word ptr','byte ptr')): w=True
                if z.mnemonic=='cmp': bc=True
                if z.mnemonic in ('inc','dec','add','sub') and any(r in z.op_str for r in ('esi','edi','ebx','eax','ecx','edx','ebp')): adv=True
            if w and bc and adv:
                loops.append((t-lo, i.address-lo, len(body)))
    # distinct jcc targets >=3
    distinct_gates = len([t for t,v in guards.items() if len(v)>=1])
    allres[e] = dict(size=size, n=len(insns), jump_tables=jt, errcode=err, loops=loops,
                     distinct_jcc_targets=distinct_gates,
                     guard_targets={('%08X'%t):v for t,v in sorted(guards.items())},
                     meta=meta[e])

json.dump(allres, open(os.path.join(os.path.dirname(__file__), "dump_features.json"),'w',encoding='utf-8'),
          ensure_ascii=False, indent=1)
for e in CAND:
    r=allres[e]
    print("%s sz=%d n=%d jt=%d err=%d loops=%d gatedist=%d  %s" %
          (e,r['size'],r['n'],len(r['jump_tables']),len(r['errcode']),len(r['loops']),
           r['distinct_jcc_targets'],r['meta']['name']))
print("done")
