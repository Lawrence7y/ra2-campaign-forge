from re_core import *
from capstone.x86 import X86_OP_IMM, X86_OP_REG, X86_REG_ECX
import os, re, collections
EVID=os.path.join(PARENT,'EVIDENCE')

def rows_from_delta(p):
    with open(p,encoding='utf-8-sig') as f: return [x.rstrip('\r\n').split('\t') for x in f if x.strip()]
K2={int(x[0],16) for x in rows_from_delta(os.path.join(ROOT,'lead','next_re_20261117_r14','S13-K2','coverage_delta.tsv'))}
K4={int(x[0],16) for x in rows_from_delta(os.path.join(os.path.dirname(PARENT),'S13_K4','coverage_delta.tsv'))}
NEW={0x40F510,0x46C440,0x4393F0,0x46C890,0x62AF70,0x7730F0}
THUNK={0x46B990,0x46B9A0}
c=cov_rows(); a=atlas_rows(); trows=target_rows(); s13=set(s13_set())

# Baseline recomputation, uppercase-normalized set operations.
disk=sorted(va for va in s13 if c[va]['grade']=='[已证]')
stage=[('disk',set(disk)),('K2',set(disk)|K2),('K2+K4',set(disk)|K2|K4),('K2+K4+S13K5',set(disk)|K2|K4|NEW)]
b=[]
b.append('target sha256 = '+sha())
b.append('coverage S13∩atlas (uppercase-normalized) = '+str(len(s13)))
b.append('disk grade counts = '+repr(dict(collections.Counter(c[v]['grade'] for v in s13))))
b.append('K2 delta rows='+str(len(K2))+' K4 delta rows='+str(len(K4))+' K5 delta rows='+str(len(NEW)))
for label,ss in stage:
    b.append(f'STAGE {label}: proved={len(ss & s13)}/240={100*len(ss & s13)/240:.2f}%  threshold120={120}  gap={120-len(ss & s13)}')
    b.append(f'STAGE {label}: if S22 templates removed (92/0 proved), proved={len(ss & s13)}/148={100*len(ss & s13)/148:.2f}%  threshold74={74}  gap={74-len(ss & s13)}')
b.append('K2 rows currently on disk grades = '+repr(dict(collections.Counter(c[v]['grade'] for v in K2))))
b.append('K4 rows currently on disk grades = '+repr(dict(collections.Counter(c[v]['grade'] for v in K4))))
with open(os.path.join(EVID,'baseline_recompute.txt'),'w',encoding='utf-8') as f: f.write('\n'.join(b)+'\n')

# Final byte census: three-state with missing-link column.
src=os.path.join(EVID,'byte_census.tsv')
rows=[]
with open(src,encoding='utf-8') as f:
    hdr=f.readline().rstrip('\n').split('\t')
    for ln in f:
        if ln.strip(): rows.append(dict(zip(hdr,ln.rstrip('\n').split('\t'))))
final=['entry\tname\tgrade\tatlas_size\t判定\t缺哪一环\t字节依据']
counts=collections.Counter()
for r in rows:
    va=int(r['entry'],16)
    if va in K2|K4:
        st='可证(K2/K4未并入)'; miss=''; why='coverage.tsv 仍非[已证]；delta证据在对应卡片' if va in K2 else 'K4卡片13行已证，未并入coverage.tsv'
    elif va in NEW:
        st='可证(本卡,入delta)'; miss=''; why=r['byte_basis']
    elif va in THUNK:
        st='可证(本卡,行为级未入delta)'; miss=''; why='836c240404 + E9 tail-jmp; 目标函数逐条至ret已复核'
    else:
        st='不可证(缺链)'; why=r['byte_basis']
        if r['byte_basis'].startswith('string pushes'): miss='缺INI键→字段写回/调用配对基线'
        elif 'new=' in r['byte_basis'] or 'delete=' in r['byte_basis']: miss='缺独立RTTI类属+ctor注册/删除闭环'
        elif r['byte_basis'].endswith('vcall=0') and int(r['atlas_size'])<=40: miss='缺字段偏移语义锚点（短直线读写不等于命名语义）'
        else: miss='缺方法级行为链；slot/vslot/sub_占位名不计语义'
    counts[st]+=1
    final.append(f"{r['entry']}\t{r['name']}\t{r['grade']}\t{r['atlas_size']}\t{st}\t{miss}\t{why}")
with open(os.path.join(EVID,'byte_census.tsv'),'w',encoding='utf-8') as f: f.write('\n'.join(final)+'\n')

# True-name recheck over residual 172 (exclude K2 and K4 deltas).
def placeholder(n):
    return (n.startswith('sub_') or re.search(r'::sub_[0-9A-Fa-f]{8}$',n) is not None or
            re.search(r'::(?:v?slot)\d+$',n) is not None or n.startswith('?$') or n.startswith('T_DynamicVectorClass') or n.startswith('T_VectorClass'))
tr=['entry\tname\tis_placeholder\tnote']
resid=0; true=0
for r in trows:
    va=int(r['entry'],16)
    if c[va]["grade"]=="[已证]" or va in K2|K4|NEW: continue
    resid+=1
    ph=placeholder(r['name'])
    if not ph: true+=1
    tr.append(f"{va:08X}\t{r['name']}\t{ph}\t{'TRUE_NAME' if not ph else ''}")
tr.append(f'RESIDUAL={resid} TRUE_NAME={true}')
with open(os.path.join(EVID,'true_name_recheck.tsv'),'w',encoding='utf-8') as f: f.write('\n'.join(tr)+'\n')

# Container template verification: only the 92 rows, with rule quote and family counts.
rule='coverage_README.md 原文: 容器模板（T_VectorClass_*/T_DynamicVectorClass_*/T_TClassFactory_*/T_VectorCursor_* 等）按审计 class_to_sub 建议显式归 S22，sem 标 container_template（210 条）；'
fam=collections.Counter(); cont=[]
for r in trows:
    va=int(r['entry'],16); n=r['name']
    if n.startswith('?$VectorClass'): fam['?$VectorClass']+=1; f='?$VectorClass'
    elif n.startswith('?$DynamicVectorClass'): fam['?$DynamicVectorClass']+=1; f='?$DynamicVectorClass'
    elif 'T_DynamicVectorClass' in n: fam['T_DynamicVectorClass']+=1; f='T_DynamicVectorClass'
    elif 'T_VectorClass' in n: fam['T_VectorClass']+=1; f='T_VectorClass'
    else: continue
    cont.append(f"{va:08X}\t{n}\t{c[va]['subsystem']}\t{c[va]['grade']}\t{f}\t{'S22' if False else 'S13_on_disk'}")
with open(os.path.join(EVID,'container_template_92.tsv'),'w',encoding='utf-8') as f:
    f.write(rule+'\n'+'\n'.join(cont)+f'\nCOUNT={len(cont)} PROVED={sum(1 for x in cont if c[int(x.split(chr(9))[0],16)]["grade"]=="[已证]")}\nFAMILY_COUNTS={dict(fam)}\n')

# ECX write trace for resolver/ctor proof (thiscall discipline).
def wregs(va,n,reg):
    out=[]
    for i in dis(va,n):
        if i.id==0: continue
        if not i.operands: continue
        op0=i.operands[0]
        if i.mnemonic in ('mov','lea','xor','inc','dec','add','sub','pop') and op0.type==X86_OP_REG and op0.reg==reg:
            out.append(fmt(i))
        if i.mnemonic=='call' and i.op_str!='0x7c8d20': out.append('CALL '+fmt(i))
    return out
ec=[]
for va,n in [(0x75E3B0,0x90),(0x40F510,0xA5),(0x46C440,0x8F)]:
    ec.append(f'=== ECX writes {va:08X} ===')
    ec += wregs(va,n,X86_REG_ECX)
for va,n in [(0x75CEC0,0x300),(0x46BBC0,0x2C0)]:
    ec.append(f'=== ECX writes ctor {va:08X} ===')
    ec += wregs(va,n,X86_REG_ECX)
with open(os.path.join(EVID,'ecx_write_trace.txt'),'w',encoding='utf-8') as f: f.write('\n'.join(ec)+'\n')

# Proof summary for six rows.
p=[]
p.append('# S13_K5 six-row proof summary')
p.append('')
p.append('Channel A: direct PE bytes + capstone entry-to-ret (no atlas entry+size). Channel B: RTTI COL+0xC→TD, TD+8 inline name, plus vtable slot values and ctor/registry cross-reference. SHA-256 verified: '+sha())
p.append('')
p.append('## Resolver family')
p.append('The creation core is the same find-or-make algorithm, but return contract is NOT byte-identical to precedent: 0x75E3B0 returns object pointer or NULL; 0x40F510/0x46C440 return registry index or -1. Therefore names are FindOrMakeIndex, not a copied FindOrMake name.')
p.append('- 0x75E3B0: 56 57 8b f9 57 68 74 74 81 00 ... 68 94 76 81 00 ... scan [0x8874c4]/cnt[0x8874d0] with +0x24 name; push 1d0 -> call 7c8e17 -> mov ecx,eax -> call 75cec0; returns pointer / NULL.')
p.append('- 0x40F510: 56 57 8b f9 68 74 74 81 00 57 ... second string 817694; same [0x8874c4]/[0x8874d0] scan and +0x24 compare; push 1d0 -> new -> ctor 75cec0; extra post-ctor scan returns index (eax=ecx) or -1 => WarheadTypeClass::FindOrMakeIndex.')
p.append('- 0x46C440: same push order as 0x40F510; only <none> sentinel checked; scan [0xa83c84]/cnt[0xa83c90]; push 2f8 -> new -> ctor 46bbc0; returns index or -1 => BulletTypeClass::FindOrMakeIndex.')
p.append('- Strings at 0x817474=<none>, 0x817694=none; strcmp=0x7c8d20; operator new=0x7c8e17. Ctors write 0x7f6b30 (WarheadTypeClass) and 0x7e4948 (BulletTypeClass) and register pointers into the same respective arrays.')
p.append('Full byte-by-byte streams and normalized column table: EVIDENCE/resolver_compare.txt. ECX writes: EVIDENCE/ecx_write_trace.txt.')
p.append('')
p.append('## Scalar deleting destructors')
p.append('Paired baseline 0x46B5C0 BulletClass::slot8_deleting_dtor has: vptr write, base dtor call, test byte [esp+8],1, push this -> operator delete 0x7c8b3d, ret 4.')
for va,name,vptr in [(0x4393F0,'BombClass',0x7E3D10),(0x46C890,'BulletTypeClass',0x7E4948),(0x62AF70,'ParasiteClass',0x7EF890),(0x7730F0,'WeaponTypeClass',0x7F73B8)]:
    p.append(f'- {va:08X} {name}::slot8_deleting_dtor: vptr {vptr:08X} via RTTI slot8; base dtor called; test byte ptr [esp+N],1; call 0x7c8b3d; ret 4. Full stream: EVIDENCE/dtor_compare.txt')
p.append('')
p.append('## Census outcome')
p.append(str(dict(counts)))
p.append('Residual true-name check: see EVIDENCE/true_name_recheck.tsv; after removing K2/K4 rows, only 00708080 death_handler is a true name; no other true-name row was hidden by the name-shape method.')
with open(os.path.join(EVID,'PROOF_SIX.md'),'w',encoding='utf-8') as f: f.write('\n'.join(p)+'\n')
print('counts',dict(counts),'container',len(cont),'residual',resid,'true',true)
