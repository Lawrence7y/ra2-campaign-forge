# -*- coding: utf-8 -*-
"""R16_SLOTN_B3 独立复核（只读）：
1) delta 13 行 entry 集 == slotN43 数据行 31..43；
2) 第 1/2/3/5/6/7/8 列与 coverage.tsv 逐字节相同；
3) 第 4 列严格以 coverage 原第 4 列为前缀；
4) grade 列逐字节 == [已证]（UTF-8）；
5) 每行 ④ 正文含 §12.6 且不含 §12.4；
6) 6 项字节级复核（独立再算一次，不依赖 gen_delta 的 verify_summary）。
"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
PROBE = os.path.join(R14, 'PROBE_802')
sys.path.insert(0, PROBE)
import probe
sys.dont_write_bytecode = True
EXE = os.path.join(os.path.dirname(os.path.dirname(R14)), 'ra2youli', 'gamemd.exe')
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
DELTA = os.path.join(HERE, 'delta.tsv')
SLOTN = os.path.join(PROBE, 'slotN43.tsv')
SCAN = os.path.join(HERE, 'scan_raw.json')

def load_cov():
    cov={}
    with open(COV,'rb') as f:
        raw=f.read()
    for ln in raw.split(b'\n'):
        if not ln: continue
        c=ln.split(b'\t')
        if len(c)==8:
            try: e=c[0].decode('ascii').upper()
            except Exception: continue
            cov.setdefault(e,c)
    return cov

cov=load_cov()
# slotN43 data rows 31..43 entries
with open(SLOTN,encoding='utf-8') as f:
    data=f.read().splitlines()[1:]
b3=[ln.split('\t')[0].upper() for ln in data[30:43]]

# delta rows (bytes)
with open(DELTA,'rb') as f:
    dlines=[ln for ln in f.read().split(b'\n') if ln]
dheader=dlines[0]
drows=dlines[1:]
print('delta header cols', len(dheader.split(b'\t')))
print('delta rows', len(drows))

bad=0
grade_ok=0
prefix_ok=0
colok=0
discl_ok=0
dentries=[]
for ln in drows:
    c=ln.split(b'\t')
    assert len(c)==8, ('delta col count', len(c))
    e=c[0].decode('ascii').upper(); dentries.append(e)
    o=cov.get(e)
    if o is None:
        print('MISSING in cov',e); bad+=1; continue
    # columns 1/2/3/5/6/7/8
    if all(c[i]==o[i] for i in (0,1,2,4,5,6,7)):
        colok+=1
    else:
        print('COL MISMATCH',e,[(i,c[i][:20],o[i][:20]) for i in (0,1,2,4,5,6,7) if c[i]!=o[i]])
        bad+=1
    # col4 prefix
    if c[3].startswith(o[3]):
        prefix_ok+=1
    else:
        print('PREFIX FAIL',e); bad+=1
    # grade
    if c[4].decode('utf-8')=='[已证]':
        grade_ok+=1
    else:
        print('GRADE FAIL',e,c[4]); bad+=1
    # §12.6 present, §12.4 absent in appended text
    appended=c[3][len(o[3]):].decode('utf-8')
    if ('§12.6' in appended) and ('§12.4' not in appended):
        discl_ok+=1
    else:
        print('DISC FAIL',e,'has126',('§12.6' in appended),'has124',('§12.4' in appended)); bad+=1

print('entry set == B3 rows 31..43:', sorted(dentries)==sorted(b3), len(dentries))
print('col 1/2/3/5/6/7/8 byte-identical:', colok, '/', len(drows))
print('col4 strict prefix preserved:', prefix_ok, '/', len(drows))
print('grade == [已证]:', grade_ok, '/', len(drows))
print('§12.6 present & §12.4 absent:', discl_ok, '/', len(drows))
print('BAD:', bad)

# independent 6 byte checks from scan_raw
img=probe.Image(EXE)
import capstone
scan=json.load(open(SCAN,encoding='utf-8'))
# apply same fixes as gen_delta (read fields for final vt/site/func)
fields={}
with open(os.path.join(HERE,'fields.tsv'),encoding='utf-8') as f:
    for ln in f.read().splitlines()[1:]:
        if ln.strip():
            p=ln.split('\t'); fields[p[0]]=p
six=[0,0,0,0,0,0]; rtti=0
import re
for r in scan['rows']:
    e=r['entry']; p=fields[e]
    slot=int(p[2]); vt=int(p[3],16); col=int(p[5],16); off=int(p[6]); td=int(p[7],16); mg=p[8]; site=int(p[9],16)
    checks=[
      img.u32(vt+slot*4)==int(e,16),
      img.u32(vt-4)==col,
      img.u32(col+4)==off,
      img.u32(col+12)==td,
      img.cstr(td+8,256)==mg,
    ]
    code=bytes(img.buf[site-img.base:site-img.base+12])
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True
    ins=next(md.disasm(code,site))
    imm=ins.operands[1].imm & 0xFFFFFFFF if (ins.mnemonic=='mov' and len(ins.operands)==2 and ins.operands[1].type==capstone.x86.X86_OP_IMM) else None
    checks.append(imm==vt)
    for i,v in enumerate(checks):
        if v: six[i]+=1
    cls=p[1]
    if probe.col_name_match(cls,mg)=='match': rtti+=1
print('independent 6 byte checks (each /13):',six)
print('independent rtti_class==row_class:',rtti,'/13')
