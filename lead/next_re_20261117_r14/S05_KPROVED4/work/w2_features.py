# -*- coding: utf-8 -*-
"""S05-KPROVED4 · 反汇编 + CFG extent + ③b 特征检测（自写）。
capstone skipdata=True；op.index 陷阱按 §8.1⑲ 处理（无 index 返回 0 非 None）。"""
import json, sys, capstone, ax_lib

CAND = [
 "0040BA50","0040CDC0","00410220","00410230","00410BE0","0050EA00","00512D30",
 "00513100","005134D0","005F9720","005F9950","006F3F40","006F4A70","006F6CA0",
 "006FFBE0","00703860","00704350","00708D70","00709A30","00709A40","0070C250",
 "0070E280","0070E2B0","00711EB0","00711F00","007171A0",
]

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.skipdata = True
md.detail = True

def disasm_window(pe, entry, maxbytes=0x3000):
    va = entry
    code = pe.bytes_at(va, maxbytes)
    if not code: return [], None
    insns = []
    for i in md.disasm(code, va):
        insns.append(i)
        # 停在函数末尾：ret 后接 int3/nop 填充，或走太远
        if i.mnemonic in ('ret','retf') and len(insns)>3:
            nxt = va + (i.address-va) + i.size
            # 看后续 16 字节是否多为 int3/nop
            tail = pe.bytes_at(nxt, 16) or b''
            pad = sum(1 for b in tail[:8] if b in (0xCC,0x90))
            if pad>=5:
                break
    return insns, (insns[-1].address+insns[-1].size if insns else va)

def mem_disp(i):
    """返回第一个 mem 操作数的 (base_reg_name, index_reg_name_or_None, disp)，否则 None。
    处理 capstone op.index 无索引=0 陷阱：index==0 视作 None（除非 base 也异常）。"""
    for op in i.operands:
        if op.type == capstone.x86.X86_OP_MEM:
            m = op.mem
            base = i.reg_name(m.base) if m.base else None
            idx = i.reg_name(m.index) if m.index else None  # index==0 -> None
            return base, idx, m.disp
    return None

def features(insns, entry):
    f = dict(n=len(insns), end=insns[-1].address+insns[-1].size if insns else entry)
    f['rets']=[]; f['indirect_jmps']=[]; f['backedges']=[]; f['sentinel_m1']=[]
    f['imm_ret']=[]; f['writes_in_loop']=0; f['b8_imm_c3']=[]; f['calls']=[]
    addrs=[i.address for i in insns]
    addr_set=set(addrs)
    for k,i in enumerate(insns):
        off=i.address-entry
        m=i.mnemonic; op=i.op_str
        if m=='ret' or m.startswith('ret '): f['rets'].append((hex(off),op))
        if m in ('jmp','call'):
            # 间接跳转/调用：操作数含 '['
            if '[' in op and ('*' in op or op.strip().startswith('dword') or op.strip().startswith('word')):
                f['indirect_jmps'].append((hex(off),m,op))
            if m=='call' and op.strip().startswith('0x'):
                f['calls'].append((hex(off),op))
            # 回边：目标 <= 当前地址（循环）
            try:
                parts=op.split()
                tgt=int(parts[-1],16) if parts[-1].startswith('0x') else None
                if tgt is not None and tgt<=i.address and m.startswith('j'):
                    f['backedges'].append((hex(off),m,op,hex(tgt-entry)))
            except Exception: pass
        if m.startswith('cmp') and ('-1' in op):
            f['sentinel_m1'].append((hex(off),m,op))
        if m=='mov' and op.startswith('eax,') and '0x' in op:
            # 检测 B8 imm32 C3 需看字节，下面单独做
            pass
    # B8 imm32 C3 形态（GetSize/WhatAmI 常量返回桩）
    for k,i in enumerate(insns):
        raw=bytes_from(i)
        if len(raw)>=6 and raw[0]==0xB8 and raw[5]==0xC3:
            imm=int.from_bytes(raw[1:5],'little')
            f['b8_imm_c3'].append((hex(i.address-entry),hex(imm)))
    return f

def bytes_from(i):
    # capstone insn.bytes
    return bytes(i.bytes)

def main():
    pe=ax_lib.load()
    out={}
    for ent in CAND:
        e=int(ent,16)
        insns,end=disasm_window(pe,e)
        f=features(insns,e)
        out[ent]=dict(n=f['n'],end=hex(f['end']),size=hex(f['end']-e),
                      n_ret=len(f['rets']),n_indjmp=len(f['indirect_jmps']),
                      n_backedge=len(f['backedges']),n_sentinel_m1=len(f['sentinel_m1']),
                      n_b8c3=len(f['b8_imm_c3']),n_calls=len(f['calls']),
                      indjmp=f['indirect_jmps'][:12],backedges=f['backedges'][:16],
                      sent=f['sentinel_m1'][:20],b8c3=f['b8_imm_c3'][:12])
        print('%s size=%-7s n=%-5d ret=%-3d indjmp=%-3d back=%-3d sent-1=%-3d b8c3=%-3d calls=%d' %
              (ent,out[ent]['size'],f['n'],len(f['rets']),len(f['indirect_jmps']),
               len(f['backedges']),len(f['sentinel_m1']),len(f['b8_imm_c3']),len(f['calls'])))
    with open('features.json','w',encoding='utf-8') as fo:
        json.dump(out,fo,ensure_ascii=False,indent=1)

if __name__=='__main__': main()
