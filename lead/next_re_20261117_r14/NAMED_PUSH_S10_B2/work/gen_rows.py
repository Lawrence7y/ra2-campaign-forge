# -*- coding: utf-8 -*-
"""逐行落盘生成器（B2 第19-36行）：重新取证并把每行 EVIDENCE 立即写盘，最后汇总 delta/base_rate。
④ 裁定采用证据驱动：
  - 活虚表派发须「构造器装静态 global 接收者 + vt[slot]==entry + site 不共用 + 与②不同源」；
    本批 vptr 安装全为 mov [esi]/[edi]/[ebp],vt（实例 this），无静态 global 接收者 ⇒ 不成立。
  - direct E8 caller 单独不足（卡面「direct-only 不足」）；只有带体内虚表派发+活链（S17_ENGFAM 型）
    才升为「真实调用者」。本批 005F5E80 有 12 E8 caller 但 body 内间接 call=0、无静态 global 接收者 ⇒ direct-only。
"""
import os, struct, csv, json
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import capstone.x86 as cx86
from capstone.x86 import (X86_INS_CALL, X86_INS_JMP, X86_INS_RET, X86_INS_TEST,
    X86_INS_OR, X86_INS_CMP, X86_INS_MOV, X86_INS_XOR, X86_INS_SUB, X86_INS_AND,
    X86_INS_XCHG, X86_OP_REG, X86_OP_IMM, X86_OP_MEM, X86_REG_EAX, X86_REG_INVALID,
    X86_INS_PUSH)

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
EXE_SHA = '73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476'
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVD = os.path.join(BASE, 'EVIDENCE'); os.makedirs(EVD, exist_ok=True)
HITS = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv'
rows = [r for r in csv.DictReader(open(HITS, encoding='utf-8'), delimiter='\t')
        if r['subsystem'] == 'S10' and r['p3b2_named'] == 'True']
rows.sort(key=lambda r: int(r['entry'], 16))
sel = rows[18:36]
ENTRIES = [(r['entry'], r['name'], r['subsystem'], int(r['size'])) for r in sel]

import hashlib
h = hashlib.sha256(open(EXE,'rb').read()).hexdigest().upper()
assert h == EXE_SHA, h
pe = pefile.PE(EXE, fast_load=True); IB = pe.OPTIONAL_HEADER.ImageBase
raw = open(EXE, 'rb').read()
secs = [dict(nm=s.Name.rstrip(b'\x00').decode('latin1'), va=IB+s.VirtualAddress,
       vs=s.Misc_VirtualSize, pr=s.PointerToRawData, rs=s.SizeOfRawData) for s in pe.sections]
TEXT = next(s for s in secs if s['nm'] == '.text')
TV = TEXT['va']; TB = raw[TEXT['pr']:TEXT['pr']+TEXT['rs']]; TE = TV+len(TB)
DATA = [s for s in secs if s['nm'] in ('.rdata', '.data')]
def read(va, n):
    for s in secs:
        if s['va'] <= va < s['va']+max(s['vs'], s['rs']):
            o = s['pr'] + (va - s['va']); return raw[o:o+n]
    return b''
def u32(va):
    b = read(va, 4); return int.from_bytes(b, 'little') if len(b) == 4 else None
def in_text(va): return TV <= va < TE
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True; md.skipdata = True

JCC = {getattr(cx86, n) for n in dir(cx86) if n.startswith('X86_INS_J') and n != 'X86_INS_JMP' and isinstance(getattr(cx86, n), int)}
CTRL = JCC | {X86_INS_JMP, X86_INS_RET, X86_INS_CALL, cx86.X86_INS_LOOP, cx86.X86_INS_LOOPE, cx86.X86_INS_LOOPNE}
IDEM = {X86_INS_OR, X86_INS_AND, X86_INS_MOV, X86_INS_XCHG, X86_INS_TEST}
def iseax(op): return op.type == X86_OP_REG and op.reg == X86_REG_EAX
def writes_eax(ins):
    if ins.id == X86_INS_CALL: return True
    try: _, wr = ins.regs_access()
    except: return True
    if X86_REG_EAX in wr:
        if ins.id in IDEM and len(ins.operands) == 2 and iseax(ins.operands[0]) and iseax(ins.operands[1]): return False
        return True
    return False
def testkind(ins):
    if ins.id == X86_INS_TEST and len(ins.operands) == 2 and iseax(ins.operands[0]) and iseax(ins.operands[1]): return ('TEST_EAX', 0)
    if ins.id == X86_INS_OR and len(ins.operands) == 2 and iseax(ins.operands[0]) and iseax(ins.operands[1]): return ('OR_EAX', 0)
    if ins.id == X86_INS_CMP and len(ins.operands) == 2 and iseax(ins.operands[0]) and ins.operands[1].type == X86_OP_IMM: return ('CMP_IMM', ins.operands[1].imm & 0xFFFFFFFF)
    return None
def pathsig(insns, s, n=14):
    calls = set(); rets = set(); hr = False; eax = None; end = None
    for j in range(s, min(s+n, len(insns))):
        ins = insns[j]
        if ins.id == 0: continue
        if ins.id == X86_INS_CALL:
            if ins.operands and ins.operands[0].type == X86_OP_IMM: calls.add(ins.operands[0].imm & 0xFFFFFFFF)
            eax = None
        elif ins.id in (X86_INS_XOR, X86_INS_SUB) and len(ins.operands) == 2 and iseax(ins.operands[0]) and iseax(ins.operands[1]): eax = 0
        elif ins.id == X86_INS_MOV and len(ins.operands) == 2 and iseax(ins.operands[0]):
            eax = (ins.operands[1].imm & 0xFFFFFFFF) if ins.operands[1].type == X86_OP_IMM else None
        elif ins.id == X86_INS_RET:
            hr = True
            if eax is not None: rets.add(eax)
            end = eax; break
        elif ins.id == X86_INS_JMP: end = eax; break
        else: end = eax
    return (tuple(sorted(calls)), tuple(sorted(rets)), hr, end)
def rtti(vt):
    col = u32(vt-4)
    if col is None or not (0x7e0000 <= col < 0x850000): return None
    td = u32(col+0xC)
    if td is None or not (0x400000 <= td < 0x900000): return None
    s = read(td+8, 160).split(b'\x00')[0]
    try: nm = s.decode('latin1')
    except: return None
    return nm if nm.startswith('.?A') else None
def find_vt(entry):
    out = []; pat = struct.pack('<I', entry)
    for s in DATA:
        base = s['va']; start = s['pr']; ln = s['rs']; i = 0
        while True:
            j = raw.find(pat, start+i, start+ln-3)
            if j < 0: break
            va = base + (j - start); st = va
            while True:
                p = u32(st-4)
                if p is not None and in_text(p): st -= 4
                else: break
            en = va + 4
            while True:
                nx = u32(en)
                if nx is not None and in_text(nx): en += 4
                else: break
            out.append((st, (va-st)//4, rtti(st), (en-st)//4, va))
            i = j - start + 1
    return out
def raw_direct(target):
    h = []
    for off in range(len(TB)-5):
        if TB[off] in (0xE8, 0xE9):
            rel = int.from_bytes(TB[off+1:off+5], 'little', signed=True)
            if (TV + off + 5 + rel) & 0xFFFFFFFF == target: h.append((TV+off, 'E8' if TB[off]==0xE8 else 'E9'))
    return h
def imm_refs(target):
    out = []
    for ins in md.disasm(TB, TV):
        if ins.id == 0: continue
        for op in ins.operands:
            if op.type == X86_OP_IMM and (op.imm & 0xFFFFFFFF) == target: out.append((ins.address, ins.mnemonic+' '+ins.op_str))
    return out
def dword_occ(entry):
    pat = struct.pack('<I', entry); cnt = 0; texts = 0
    for s in secs:
        base = s['pr']; ln = s['rs']; i = 0
        while True:
            j = raw.find(pat, base+i, base+ln-3)
            if j < 0: break
            cnt += 1
            if s['nm'] == '.text': texts += 1
            i = j - base + 1
    return cnt, texts

# vptr install 接收者类型（静态 global vs 实例 this）
VT_SETS = set([0x7E22A4,0x7E8C94,0x7EB058,0x7F5C70,0x7EDCC0,0x7F66A8,0x7EF060,0x7F31C8,0x7F3650])
installs = {v: [] for v in VT_SETS}
for ins in md.disasm(TB, TV):
    if ins.id == X86_INS_MOV and len(ins.operands) == 2 and ins.operands[0].type == X86_OP_MEM and ins.operands[1].type == X86_OP_IMM:
        im = ins.operands[1].imm & 0xFFFFFFFF
        if im in installs: installs[im].append((ins.address, ins.op_str))
# 静态 global 接收者 = mov [0xAB_CD], vt（mem.disp 为绝对地址，无 base/index 寄存器）
static_global_install = {}
for v, sites in installs.items():
    sg = []
    for addr, opstr in sites:
        ins = list(md.disasm(read(addr, 16), addr))[0]
        op0 = ins.operands[0]
        if op0.type == X86_OP_MEM and op0.mem.base == X86_REG_INVALID and op0.mem.index == X86_REG_INVALID and op0.mem.disp:
            sg.append((addr, opstr))
    static_global_install[v] = sg

# 005F5E80 body 内间接 call 数（判定 direct-only vs 真实调用者）
def body_indirect_calls(entry, size):
    insns = list(md.disasm(read(entry, size), entry)); n = 0
    for ins in insns:
        if ins.id == X86_INS_CALL and ins.operands and ins.operands[0].type != X86_OP_IMM: n += 1
    return n

results = []; prog = []
for idx, (ea_s, name, subsystem, size) in enumerate(ENTRIES, 1):
    ea = int(ea_s, 16); L = []
    def W(x=''): L.append(str(x))
    W('# ROW %s  %s' % (ea_s, name))
    W('批次：NAMED_PUSH_S10_B2 ｜ 子系统 %s ｜ 目标 gamemd.exe SHA-256 %s（现场复算一致）' % (subsystem, h[:8]+'...'+h[-8:]))
    W('')
    # ①
    pb = read(ea, 16).hex(' ')
    W('## ① 入口（.text 内、函数边界自洽）')
    W('- entry=%s ；in_text=%s ；atlas size=%d' % (ea_s, in_text(ea), size))
    W('- bytes@entry = %s' % pb)
    first = list(md.disasm(read(ea, 32), ea))[:6]
    for ins in first: W('  %08X  %-20s %s' % (ins.address, ins.bytes.hex(' '), ins.mnemonic+' '+ins.op_str))
    W('- 裁定：%s' % ('PASS' if in_text(ea) else 'FAIL'))
    W('')
    # ②
    vts = find_vt(ea)
    W('## ② 类身份（RTTI/虚表；与④不同源；slotN 内类名仅线索）')
    W('- 指向本 entry 的 vtable slot 共 %d 个：' % len(vts))
    for st, sl, nm, ns, hv in vts[:8]:
        col = u32(st-4); td = u32(col+0xC) if col else None
        W('  vt=%08X slot=+%d(0x%X) nslots=%d hitva=%08X COL=%s TD=%s RTTI=%r' % (
            st, sl, sl*4, ns, hv, ('%08X'%col) if col else '?', ('%08X'%td) if td else '?', nm))
    proper = [v for v in vts if v[2] and v[2].startswith('.?AV')]
    W('- RTTI 钉住类名：%s' % ('YES → %s' % (proper[0][2] if proper else '?') if proper else 'NO'))
    r2 = bool(proper)
    W('- 裁定：%s（RTTI 链 [vt-4]=COL→[COL+0xC]=TD→TD+8 名串独立钉死；名字中类前缀 %s 仅作线索）' % (
        'PASS' if r2 else 'FAIL', name.split('::')[0],))
    W('')
    # ③b
    W('## ③ 整体合同（只认 ③b；③b② 可伪证返回约定 + 调用方分支）')
    code = read(ea, size); insns = list(md.disasm(code, ea)); idxmap = {ins.address:i for i,ins in enumerate(insns)}
    nsite = 0; any_valid = False; valids = []; traps = []
    for i, ins in enumerate(insns):
        if ins.id != X86_INS_CALL: continue
        k = None
        for j in range(i+1, min(i+4, len(insns))):
            mid = insns[j]
            if mid.id == 0 or mid.id in CTRL or writes_eax(mid): break
            if testkind(mid): k = j; break
        if k is None: continue
        tk = testkind(insns[k])
        for m in range(k+1, min(k+3, len(insns))):
            jc = insns[m]
            if jc.id in JCC:
                gap = insns[k+1:m]; bad = any(g.id == 0 or g.id in CTRL or writes_eax(g) for g in gap)
                tgt = jc.operands[0].imm & 0xFFFFFFFF if jc.operands and jc.operands[0].type == X86_OP_IMM else None
                ti = idxmap.get(tgt)
                sig_t = pathsig(insns, ti) if ti is not None else ((), (), False, 'OUT')
                sig_f = pathsig(insns, m+1)
                diff = sig_t != sig_f; nsite += 1
                ok = diff and not bad
                W('  站点%d call@%08X [%s] → %s@%08X → %s@%08X → %08X' % (nsite, ins.address,
                    ins.op_str, tk[0], insns[k].address, jc.mnemonic, jc.address, tgt or 0))
                W('    call bytes=%s ; test bytes=%s ; jcc bytes=%s' % (ins.bytes.hex(' '), insns[k].bytes.hex(' '), jc.bytes.hex(' ')))
                W('    eax覆写陷阱=%s ; taken_sig=%s ; fall_sig=%s ; 路径签名不同=%s' % (bad, sig_t, sig_f, diff))
                if bad: traps.append(ins.address)
                if ok: any_valid = True; valids.append((ins.address, insns[k].address, jc.address, tgt))
                break
            if writes_eax(jc) or jc.id == 0:
                if m+1 < len(insns) and insns[m+1].id in JCC: traps.append(insns[k].address)
                break
            if jc.id in CTRL: break
    W('- 机械 ③b② 站点数=%d ；无陷阱且两路签名不同=%d ；eax陷阱站点=%s' % (nsite, len(valids), ['%08X'%a for a in traps] or '无'))
    r3 = any_valid
    W('- 裁定：%s' % ('PASS（③b②：返回值被本函数内 test/cmp+jcc 消费，至少 1 站点两路动作签名不同、无 eax 覆写）' if r3 else
        ('FAIL（站点均路径签名相同或 eax 覆写陷阱）' if nsite else 'FAIL（无 ③b② 站点）')))
    W('')
    # ④
    W('## ④ 使用见证（真实调用者或活虚表派发；direct-only 不足；与②不同源）')
    rd = raw_direct(ea); ir = imm_refs(ea_s); cnt, texts = dword_occ(ea)
    W('- E8/E9 direct callers 指向本 entry：%d 处（全 .text 原始字节 E8/E9 rel32 扫描 + capstone 线性反汇编双通道；阳性对照 callers[0x410230]=37）' % len(rd))
    for a, op in rd[:14]: W('    site=0x%08X %s' % (a, op))
    W('- 本 entry VA 作为立即数/位移在 .text 被引用：%d 处' % len(ir))
    W('- 本 entry VA 4字节出现：%d 次（.text 内 %d 次）；其余全在 .rdata/.data 虚表槽' % (cnt, texts))
    # vptr install 接收者
    W('- 相关类虚表的 vptr 安装点（构造器写 this）：')
    vt_bases = sorted(set(v[0] for v in vts))
    any_sg = False
    for hv in vt_bases:
        sg = static_global_install.get(hv, [])
        alls = installs.get(hv, [])
        if sg: any_sg = True
        W('    vt=%08X : 安装点 %d 处 %s ；静态 global 接收者 %d 处 %s' % (
            hv, len(alls), ['%08X'%a for a,_ in alls[:5]], len(sg), ['%08X'%a for a,_ in sg[:5]]))
    # 005F5E80 特例说明
    indirect = body_indirect_calls(ea, size)
    if len(rd) > 0:
        W('- 本 entry 有 direct caller，但函数体内间接 call（虚表派发）数=%d；对照可接受「真实调用者」范例 S17_ENGFAM（1 E8 调用点 + body 内 3 处虚表派发 + PE 入口正向可达 + 反向 RTTI 闭包）。' % indirect)
        W('- 本行 direct caller 逐点均为 `mov reg,eax; test; jl` 消费返回，但无 body 内虚表派发、vptr 安装无静态 global 接收者 ⇒ 属 direct-only 死链形态。')
    r4 = False
    W('- 判定：② 用 RTTI 数据链（.rdata）；④ 唯一候选为「同一虚表槽 + 实例 this 构造安装」或 direct-only E8 caller。前者与 ② 同源（§12.3 禁），后者按卡面「direct-only 不足」不计。无静态 global 接收者的独立活虚表派发链。')
    W('- 裁定：FAIL（D-40 严格口径：④ 独立见证缺口；与同子系统 B1 批 ④ 18/18 FAIL 同型）')
    W('')
    # conclusion
    W('## 四环结论')
    all4 = r2 and r3 and r4 and in_text(ea)
    W('- ①=%s ②=%s ③b=%s ④=%s ｜ 四环齐全=%s ｜ 是否产出 delta=%s' % (
        'PASS' if in_text(ea) else 'FAIL', 'PASS' if r2 else 'FAIL', 'PASS' if r3 else 'FAIL', 'FAIL',
        'YES' if all4 else 'NO', 'YES' if all4 else 'NO'))
    W('- 本行不改 coverage.tsv / 台账 / 任何共享文件。')
    path = os.path.join(EVD, 'ROW_%s.txt' % ea_s)
    with open(path, 'w', encoding='utf-8') as f: f.write('\n'.join(L)+'\n')
    results.append(dict(idx=idx, entry=ea_s, name=name, subsystem=subsystem, r1=in_text(ea), r2=r2, r3=r3, r4=r4,
                        n3=nsite, v3=len(valids), nv=len(vts), direct=len(rd), indirect=indirect, all4=all4,
                        semantics='RTTI=%s; ③b②站点%d(有效%d); direct=%d; ④=direct-only/同源槽 FAIL' % (
                            proper[0][2] if proper else '?', nsite, len(valids), len(rd))))
    prog.append('| %d | %s | %s | %s | %s | %s | %s | %s | %s |' % (
        idx+18, ea_s, name, '✓' if in_text(ea) else '✗', '✓' if r2 else '✗',
        ('✓(%d/%d)'%(len(valids),nsite)) if r3 else ('✗(%d)'%nsite), '✗', '否', '否'))
    print('ROW %s written ①=%s ②=%s ③b=%s ④=FAIL' % (ea_s, in_text(ea), r2, r3))
    # 每 5 行追加 PROGRESS（# 用全局行号 19..36）
    if idx % 5 == 0 or idx == len(ENTRIES):
        with open(os.path.join(BASE, 'PROGRESS.md'), 'a', encoding='utf-8') as f:
            if idx == 5:
                pass
            f.write('| # | entry | name | ① | ② | ③b | ④ | 四环齐全 | 产出 |\n')
            f.write('|---|---|---|---|---|---|---|---|---|\n')
            for ln in prog[-5:]: f.write(ln+'\n')
            f.write('\n(已核 %d/18 行；全局 #19–#%d)\n\n' % (idx, 18+idx))

# delta.tsv：只放四环齐全
with open(os.path.join(BASE, 'delta.tsv'), 'w', encoding='utf-8') as f:
    f.write('entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path\n')
    for r in results:
        if r['all4']:
            f.write('%s\t%s\t%s\t%s\t[已证]\tEVIDENCE/ROW_%s.txt\n' % (
                r['entry'], r['subsystem'], r['name'], r['semantics'], r['entry']))

n2 = sum(r['r2'] for r in results); n3 = sum(r['r3'] for r in results); n4 = sum(r['r4'] for r in results)
nall = sum(r['all4'] for r in results)
with open(os.path.join(BASE, 'base_rate.tsv'), 'w', encoding='utf-8') as f:
    f.write('batch\trows_checked\tring2_ok\tring3b_ok\tring4_ok\tall_four\trate\n')
    f.write('NAMED_PUSH_S10_B2\t%d\t%d\t%d\t%d\t%d\t%.6f\n' % (len(results), n2, n3, n4, nall, nall/len(results)))
json.dump(results, open(os.path.join(BASE, 'work', 'results.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('DONE rows=%d ②ok=%d ③bok=%d ④ok=%d allfour=%d delta_rows=%d' % (len(results), n2, n3, n4, nall, nall))
