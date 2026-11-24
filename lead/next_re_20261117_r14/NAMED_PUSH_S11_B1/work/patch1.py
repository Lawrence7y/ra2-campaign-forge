import re
p='gen_evidence.py'
s=open(p,encoding='utf-8').read()

# 1) func_tail 取末 8 条（保证含 mov eax,esi）
s=s.replace('    return ins[-5:]', '    return ins[-8:]')

# 2) 基类 ctor 调用点：改成现场定位（在构造器体内找 call 0x55A6C0）
s=s.replace(
'''    L.append("调用基类构造器    = 004AF543 处 call 0x55a6c0；0x55A6C0 体内 %s ⇒ 是基类 ctor（不是 0x55A6F0 那个重置基类 vptr 的析构体）"
             % (ins_at(sp["base_ctor"])))''',
'''    bsite = [i for i in dis(sp["ctor"], read_va(sp["ctor"], ATLAS.get(sp["ctor"], 0xA0)))
             if i.id == X86_INS_CALL and i.operands and i.operands[0].type == X86_OP_IMM
             and (i.operands[0].imm & 0xFFFFFFFF) == sp["base_ctor"]]
    if bsite:
        i0 = bsite[0]
        L.append("调用基类构造器    = %s  %-14s %s；0x55A6C0 体内 %s ⇒ 是基类 ctor（不是 0x55A6F0 那个重置基类 vptr 的析构体）"
                 % (hx(i0.address), i0.bytes.hex().upper(), i0.mnemonic + " " + i0.op_str, ins_at(sp["base_ctor"])))
    else:
        L.append("调用基类构造器    = 未在构造器体内找到 call 0x55A6C0（异常，需复核）")''')
open(p,'w',encoding='utf-8').write(s)
print('patched')
