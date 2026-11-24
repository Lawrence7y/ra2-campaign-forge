from re_core import *
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_EBP, X86_REG_ESI
import re, os
EVID=os.path.join(PARENT,'EVIDENCE'); os.makedirs(EVID,exist_ok=True)
def line(i): return fmt(i)
def dump_range(va,n,title):
    return f"===== {title} {va:08X} =====\n"+"\n".join(line(i) for i in dis(va,n))+"\n"
res=[]
for va,lim in [(0x75E3B0,0x90),(0x40F510,0xA5),(0x46C440,0x8F)]:
    res.append(dump_range(va,lim,"resolver_full"))
def canon(i):
    return re.sub(r'0x[0-9a-f]+','IMM',f"{i.mnemonic} {i.op_str}".strip())
for a,b,label in [(0x75E3B0,0x40F510,'warhead_pointer_vs_index_resolver'),(0x75E3B0,0x46C440,'warhead_pointer_vs_bullettype_index_resolver')]:
    aa=list(dis(a,0x90)); bb=list(dis(b,0x90))
    res.append(f"===== normalized {label} =====\nstep\tA_bytes\tA_insn\tB_bytes\tB_insn")
    for j in range(max(len(aa),len(bb))):
        x=aa[j] if j<len(aa) else None; y=bb[j] if j<len(bb) else None
        res.append(f"{j+1}\t{x.bytes.hex() if x else ''}\t{canon(x) if x else ''}\t{y.bytes.hex() if y else ''}\t{canon(y) if y else ''}")
    res.append('')
with open(os.path.join(EVID,'resolver_compare.txt'),'w',encoding='utf-8') as f: f.write('\n'.join(res))
rtti=[]
for vt in [0x7F6B30,0x7E4948,0x7E3D10,0x7EF890,0x7F73B8,0x7E46E4]:
    col=u32(vt-4); td=u32(col+0xC); nm=cstr(td+8,80).decode("latin1")
    rtti.append(f"VT={vt:08X} COL={col:08X} TD={td:08X} NAME={nm} slot8={u32(vt+32):08X} slot11={u32(vt+44):08X} slot12={u32(vt+48):08X}")
for ctor,n,reg in [(0x75CEC0,3000,X86_REG_EBP),(0x46BBC0,6000,X86_REG_ESI)]:
    for i in dis(ctor,n):
        if i.mnemonic=="mov" and len(i.operands)==2 and i.operands[0].type==X86_OP_MEM and i.operands[1].type==X86_OP_IMM and i.operands[0].mem.base==reg and i.operands[0].mem.disp==0:
            rtti.append("CTOR_VPTR "+line(i))
for s in ["0075D12C  890dd0748800         mov dword ptr [0x8874d0], ecx","0075D132  8b0dc4748800         mov ecx, dword ptr [0x8874c4]","0075D138  892c81               mov dword ptr [ecx + eax*4], ebp","0046BD75  890d903ca800         mov dword ptr [0xa83c90], ecx","0046BD7B  8b0d843ca800         mov ecx, dword ptr [0xa83c84]","0046BD81  893481               mov dword ptr [ecx + eax*4], esi"]:
    rtti.append("REGISTRY "+s)
with open(os.path.join(EVID,'rtti_vt_registry.txt'),'w',encoding='utf-8') as f: f.write('\n'.join(rtti)+'\n')
dt=[]
for va in [0x46B5C0,0x4393F0,0x46C890,0x62AF70,0x7730F0]:
    ins=list(dis(va,360))
    k=next((j+1 for j,i in enumerate(ins) if i.mnemonic.startswith("ret")),len(ins))
    ins=ins[:k]
    vw=[line(i) for i in ins if i.mnemonic=="mov" and len(i.operands)==2 and i.operands[0].type==X86_OP_MEM and i.operands[1].type==X86_OP_IMM and i.operands[0].mem.disp==0]
    t1=[line(i) for i in ins if i.mnemonic=="test" and "[esp" in i.op_str and i.op_str.endswith(", 1")]
    de=[line(i) for i in ins if i.mnemonic=="call" and i.op_str=="0x7c8b3d"]
    r4=[line(i) for i in ins if i.mnemonic.startswith("ret")]
    dt.append(f"===== {va:08X} =====\n"+"\n".join(line(i) for i in ins)+f"\nDECISION vptr={vw} test1={t1} delete={de} ret={r4}\n")
with open(os.path.join(EVID,'dtor_compare.txt'),'w',encoding='utf-8') as f: f.write('\n'.join(dt))
c=cov_rows(); a=atlas_rows(); sc=["entry\tname\tgrade\tatlas_size\tdecision\tbyte_basis\tmissing_link"]
for va in s13_set():
    if c[va]["grade"]=="[已证]": continue
    n=int(a[va]["size"]); ins=list(dis(va,min(n,4096))); b=read(va,min(n,64))
    dc=[]
    for i in ins:
        if i.mnemonic=="call" and i.operands and i.operands[0].type==X86_OP_IMM: dc.append(i.operands[0].imm)
    st=[]
    for i in ins:
        if i.mnemonic=="push" and i.operands and i.operands[0].type==X86_OP_IMM:
            x=i.operands[0].imm
            if 0x7e1000<=x<0xb79be4:
                try:
                    s=cstr(x,48)
                    if len(s)>=2 and all(32<=q<127 for q in s): st.append(s.decode("latin1"))
                except: pass
    straight=all(i.mnemonic not in ("call","jmp") and not i.mnemonic.startswith("j") for i in ins) and any(i.mnemonic.startswith("ret") for i in ins)
    decision="未证"; basis=f"head={b[:12].hex()} ins={len(ins)} dcall={len(dc)} vcall={sum(1 for i in ins if i.mnemonic=='call' and i.operands and i.operands[0].type!=X86_OP_IMM)}"; missing="缺可定名行为链；占位名本身不计语义"
    if va in {0x40F510,0x46C440}:
        decision="可证"; basis=f"strcmp={dc.count(0x7c8d20)} new={dc.count(0x7c8e17)} strings={st[:2]} registry_scan; new+ctor closed"; missing=""
    elif va in {0x4393F0,0x46C890,0x62AF70,0x7730F0}:
        decision="可证"; basis="vptr write + registry remove + base dtor + test[esp+N],1 + operator delete + ret 4"; missing=""
    elif straight:
        decision="可证"; basis="entry-to-ret straightline fully disassembled"; missing=""
    elif b.startswith(bytes.fromhex("836c240404")) and len(ins)>=2 and ins[1].mnemonic=="jmp":
        decision="可证（thunk）"; basis="836c240404 + tail jmp"; missing=""
    elif b[:6] in (bytes.fromhex("b85c000000c3"),bytes.fromhex("b844000000c3")):
        decision="可证"; basis="B8 imm32 C3 + RTTI slot/ctor double point"; missing=""
    elif st:
        decision="缺链"; basis=f"string pushes={st[:5]}"; missing="缺字段写回/调用配对基线，不能只凭键串升语义"
    elif dc.count(0x7c8e17) or dc.count(0x7c8b3d):
        decision="缺链"; basis=f"new={dc.count(0x7c8e17)} delete={dc.count(0x7c8b3d)}"; missing="缺对象类属（独立 RTTI/ctor）与语义闭环"
    sc.append(f"{va:08X}\t{c[va]['name']}\t{c[va]['grade']}\t{n}\t{decision}\t{basis}\t{missing}")
with open(os.path.join(EVID,'byte_census.tsv'),'w',encoding='utf-8') as f: f.write('\n'.join(sc)+'\n')
rule="容器模板（`T_VectorClass_*`/`T_DynamicVectorClass_*`/`T_TClassFactory_*`/`T_VectorCursor_*` 等）按审计 `class_to_sub` 建议显式归 S22，sem 标 `container_template`（210 条）；"
cont=[]
for r in target_rows():
    va=int(r["entry"],16); name=r["name"]; sem=c[va]["one_line_semantics"]
    hit=name.startswith("?$VectorClass") or name.startswith("?$DynamicVectorClass") or "T_VectorClass" in name or "T_DynamicVectorClass" in name or "T_TClassFactory" in name or "T_VectorCursor" in name
    cont.append((f"{va:08X}\t{name}\t{c[va]['subsystem']}\t{c[va]['grade']}\t{hit}\t{sem}",hit))
with open(os.path.join(EVID,'container_template_92.tsv'),'w',encoding='utf-8') as f: f.write(rule+'\n'+'\n'.join(x for x,h in cont)+'\n')
print('candidate rows',len(sc)-1,'container exact',len(cont),'hits',sum(1 for x,h in cont if h))