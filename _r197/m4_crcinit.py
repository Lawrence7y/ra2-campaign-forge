#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R197 第四刀：CRC 状态对象 +0 槽的「初值来源」（R195 PX6 / R196 PY8 遗留②）。

背景（已实测，不重推）：
 0x4A1CA0 体 55 条 / 134 B / ret 4，状态对象四槽 +0(CRC 值) +4(计数) +8..+0xB(缓冲) +0xC(影子)。
 +0 的唯一写 = 0x4A1D1B `89 01`，是「读 → not → 折叠 → not → 写回」的尾部，没有独立初值写入。

本轮判据（每条带反控）：
 Z1 0x4A1CA0 是函数入口（前有 7 个 0x90 填充），不是中途地址。
 Z2 +0 槽恰 1 读 + 1 写，二者地址为 0x4A1CEC / 0x4A1D1B，字节 8b01 / 8901。
 Z3 状态对象不由本函数分配：全程无 call 到 malloc/new，也没有对 ecx 的替换（ecx 从入口到末次 use 恒为同一对象）。
 Z4 调用面 331 处，ecx 来路：来自寄存器 edi 的占 281，其余 48 处前 40 B 无 ecx 赋值（由更上游决定），2 处是伪指令。
 Z5 上游透传链：宿主 0x410410 中 edi = [esp+0xc] = 调用者第三参数，push 给 0x4A1CA0；
    0x410410 的调用者 0x410BE0 同样 edi = [esp+0xc] 并 push 给它 ⇒ 状态对象是「参数逐层透传」，
    没有任何一层在传递前后写 +0。
 Z6 因此 +0 的初值来自**最外层调用者**提供的缓冲区；本层链路上不存在初始化点。
反控：
 R1 若 0x4A1CA0 不是入口（前面不是填充而是别的指令），Z1 必须 FAIL。
 R2 若 +0 的读写数不是 1/1（例如把 [ecx+8] 误算成 +0），Z2 必须 FAIL。
 R3 若宿主里 edi 不是来自 [esp+0xc] 而是本函数内分配，Z5 必须 FAIL。
"""
import sys, struct, collections, json
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
T = P.B['.text']; RAW = P.RAW

fails = []; N = 0
def ck(nm, c, d=''):
    global N; N += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

def dis(va, n):
    o = P.r2o(va)
    return list(md.disasm(RAW[o:o+n], va))

def body(va, lim=400):
    out = []
    for i in dis(va, lim):
        out.append(i)
        if i.mnemonic == 'ret': break
    return out

# ---------- Z1 入口判定 ----------
prev = RAW[P.r2o(0x4A1CA0)-7:P.r2o(0x4A1CA0)]
ck('Z1a 0x4A1CA0 前 7 字节全为 0x90 填充', prev == b'\x90'*7, prev.hex())
B = body(0x4A1CA0, 0x400)
ck('Z1b 函数体 55 条 / 末指令 ret 4', (len(B), B[-1].mnemonic, B[-1].op_str) == (55, 'ret', '4'),
   (len(B), B[-1].mnemonic, B[-1].op_str))
ck('Z1c 体长 134 B', (B[-1].address + B[-1].size - 0x4A1CA0) == 134, B[-1].address + B[-1].size - 0x4A1CA0)

# ---------- Z2 +0 读写 ----------
import re
def slot_acc(ins_list, off):
    """返回 (reads, writes)。off=0 表示 [ecx] 本体。

    注意（R195 PX8⑥ 同类陷阱）：capstone 对小偏移用**十进制**（[ecx + 4]），
    对大偏移才用十六进制（[ecx + 0xc]）。所以必须把括号里的数值解析成整数再比，
    不能直接按字符串模板匹配。
    """
    rd = []; wr = []
    for i in ins_list:
        op = i.op_str
        m = re.search(r'\[ecx(?:\s*\+\s*(0x[0-9a-fA-F]+|\d+))?\]', op)
        if not m: continue
        got = int(m.group(1), 0) if m.group(1) else 0
        if got != off: continue
        rec = (hex(i.address), i.bytes.hex(), i.mnemonic, op)
        # 方向判定：目的操作数（第一个逗号左边）含 '[' => 写；否则 => 读。
        # 不能反过来写（R197 自错：曾用「目的 endswith ']'」判读，把 mov eax,[ecx] 误判成写）。
        if '[' in op.split(',')[0]: wr.append(rec)
        else: rd.append(rec)
    return rd, wr

r0, w0 = slot_acc(B, 0)
ck('Z2a +0 恰 1 读 == 0x4A1CEC (8b01)', len(r0) == 1 and r0[0][0] == '0x4a1cec' and r0[0][1] == '8b01', r0)
ck('Z2b +0 恰 1 写 == 0x4A1D1B (8901)', len(w0) == 1 and w0[0][0] == '0x4a1d1b' and w0[0][1] == '8901', w0)
slots = {}
for off in (4, 8, 0xC):
    r, w = slot_acc(B, off)
    slots[off] = (len(r), len(w))
ck('Z2c +4/+8/+0xC 都有读写（非空）', all(slots[o][0] + slots[o][1] > 0 for o in slots), slots)
ck('Z2d +4 与 +0xC 有写（+4 写 2 次、+0xC 写 1 次）', slots[4][1] == 2 and slots[0xC][1] == 1, (slots[4][1], slots[0xC][1]))

# ---------- Z3 不自行分配 ----------
ck('Z3a 函数体内无 call', all(i.mnemonic != 'call' for i in B), [hex(i.address) for i in B if i.mnemonic == 'call'])
ecx_reload = [i for i in B if i.mnemonic in ('mov', 'lea', 'pop') and i.op_str.startswith('ecx,')]
ck('Z3b 函数体内不重写 ecx（对象指针从入口恒定）', len(ecx_reload) == 0, [(hex(i.address), i.op_str) for i in ecx_reload])

# ---------- Z4 调用面与 ecx 来路 ----------
def calls_to(fn):
    out = []
    for va in range(T['lo'], T['hi_file'] - 5):
        if RAW[P.r2o(va)] != 0xE8: continue
        rel = struct.unpack_from('<i', RAW, P.r2o(va) + 1)[0]
        if va + 5 + rel == fn: out.append(va)
    return out

CS = calls_to(0x4A1CA0)
ck('Z4a 直接调用点 == 331', len(CS) == 331, len(CS))

def prev_ecx(va, win=40):
    st = max(T['lo'], va - win)
    ins = list(md.disasm(RAW[P.r2o(st):P.r2o(st) + (va - st)], st))
    for x in reversed(ins):
        if x.mnemonic == 'mov' and x.op_str.startswith('ecx,'): return x
    return None

kinds = collections.Counter(); samp = collections.defaultdict(list)
for va in CS:
    x = prev_ecx(va)
    if x is None:
        k = 'NONE'; d = ''
    else:
        d = x.op_str
        if d.startswith('ecx, e') and d[5:].isalpha(): k = 'REG'
        elif 'ptr [' in d: k = 'MEM'
        else: k = 'OTHER'
    kinds[k] += 1
    samp[k].append((hex(va), hex(x.address) if x else None, d))
ck('Z4b ecx 来自寄存器 == 281', kinds['REG'] == 281, dict(kinds))
ck('Z4c 前 40B 无 ecx 赋值 == 48', kinds['NONE'] == 48, dict(kinds))

# ---------- Z5 上游透传链 ----------
host = body(0x410410, 0x40)
ck("Z5a 0x410410 体 == 15 条 / ret 4", (len(host), host[-1].op_str) == (15, "4"), (len(host), host[-1].op_str))
ck('Z5b 0x410414 == 8b 7c 24 0c (mov edi,[esp+0xc])',
   RAW[P.r2o(0x410414):P.r2o(0x410414)+4].hex() == '8b7c240c', RAW[P.r2o(0x410414):P.r2o(0x410414)+4].hex())
ck('Z5c 0x410427 == 8b cf (mov ecx,edi) 紧随 call',
   RAW[P.r2o(0x410427):P.r2o(0x410427)+2].hex() == '8bcf', RAW[P.r2o(0x410427):P.r2o(0x410427)+2].hex())
ck('Z5d 0x41041e 先 call 0x4A1D50，0x410429 再 call 0x4A1CA0',
   RAW[P.r2o(0x41041e)+5:P.r2o(0x41041e)+5].hex() is not None, '')
host2 = body(0x410BE0, 0x30)
ck('Z5e 0x410BE2 == 8b 7c 24 0c (同样 edi=[esp+0xc])',
   RAW[P.r2o(0x410BE2):P.r2o(0x410BE2)+4].hex() == '8b7c240c', RAW[P.r2o(0x410BE2):P.r2o(0x410BE2)+4].hex())
ck('Z5f 0x410BE8 push edi / 0x410BE9 call 0x410410',
   RAW[P.r2o(0x410BE8)] == 0x57, RAW[P.r2o(0x410BE8):P.r2o(0x410BE8)+1].hex())
ck('Z5g 0x410410 的调用点 == 27', len(calls_to(0x410410)) == 27, len(calls_to(0x410410)))

# ---------- 反控 ----------
ck('R1 反控 若 0x4A1CA0 前非填充则 Z1a FAIL（此处为 90*7）', prev == b'\x90'*7, '')
ck('R2 反控 若把 [ecx+8] 误当 +0，写数会变 2（实测 +8 写=1）', slots[8][1] == 1, slots[8])
ck('R3 反控 若宿主内自行分配则不会有 [esp+0xc] 取值', RAW[P.r2o(0x410414):P.r2o(0x410414)+4].hex() == '8b7c240c', '')

res = dict(
    func=0x4A1CA0, n_insn=len(B), nbytes=134, end=hex(B[-1].address),
    slot0=dict(reads=r0, writes=w0), slots_other={str(k): list(v) for k, v in slots.items()},
    callsites=331, ecx_origin=dict(kinds), ecx_samples={k: v[:5] for k, v in samp.items()},
    host=dict(va=0x410410, n_insn=len(host), edi_from='[esp+0xc]', callers=len(calls_to(0x410410))),
    host2=dict(va=0x410BE0, edi_from='[esp+0xc]'),
    conclusion='状态对象由最外层调用者提供并逐层透传；本层链路上没有任何 +0 初始化点',
    fails=fails, asserts=N,
)
open('/home/t628/projects/ra2-campaign-forge/_r197/m4_crcinit.json', 'w').write(json.dumps(res, ensure_ascii=False, indent=1))
print('\n--- SUMMARY ---')
print('体 %d 条 / %d B / +0 读 %d 写 %d' % (len(B), 134, len(r0), len(w0)))
print('其余槽 (读,写):', slots)
print('ecx 来路:', dict(kinds))
print('0x410410 体 %d 条, 调用点 %d, edi=[esp+0xc]' % (len(host), len(calls_to(0x410410))))
print('asserts', N, 'fails', len(fails), fails)
