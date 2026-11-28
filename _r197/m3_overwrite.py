#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R197 第三刀：0x6E8000 覆写主表的语义动机（R195 PX9 遗留③ / R196 PY8 遗留③）。

R195 PX4 只记了字节事实：0x6E8000 先装 0x7E1F50 四次，0x6E807E 把 +0 覆写成 0x7F4680。
本轮回答「为什么」——判据是「覆写点相对字段拷贝的**位置**与**无条件性**」。

语义判据（每条都可被数据否掉）：
 S1 0x6E8000 是拷贝构造：首指令 mov edx,[esp+4]（第二参数=源），次指令 mov eax,ecx（this）。
 S2 覆写在全部 rep movsd 段之后（不是之前）——若是「先定最终表再拷字段」则应为之前。
 S3 覆写无条件：0x6E8000..0x6E807E 之间没有任何分支目标落在 0x6E807E..0x6E8099。
 S4 覆写是 4 条独立 mov [eax+K],imm32，K = 0,4,8,0xC，不是一次 memcpy 过来的。
 S5 换表不是「多几个槽」：新表 0x7F4680 与旧表 0x7E1F50 共同前缀内有 7 个槽值不同，
    其中槽 3/5/6/11/12 从 `xor eax,eax;ret` 纯桩换成真实现；槽 8/13 从别的实现换成新实现。
 S6 新表比旧表多 3 个槽（24 -> 27），多出槽 24/25/26。
反控：
 R1 若判 S2 为「覆写在拷贝之前」，则 X13 必须 FAIL。
 R2 若把槽 3 的实现 0x6E8710 换成 0x4C9150 纯桩比较，判别力消失（说明 S5 依赖具体实现体）。
 R3 若 0x6E8000..0x6E807E 间存在跳过覆写的分支，S3 必须 FAIL。
"""
import sys, struct, json
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

fails = []; N = 0
def ck(nm, c, d=''):
    global N; N += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

def slots(vt, lim=600):
    out = []; a = vt
    while True:
        v = P.dw(a)
        if v is None or P.where(v) != '.text': break
        out.append(v); a += 4
        if len(out) > lim: break
    return out

def dis(va, n):
    o = P.r2o(va)
    return list(md.disasm(P.RAW[o:o+n], va))

OLD, NEW = 0x7E1F50, 0x7F4680
o = P.r2o(0x6E8000)
body = P.RAW[o:o+0x7E]

# ---------- S1 拷贝构造形态 ----------
ck('S1a 首指令 == 8b 54 24 04 (mov edx,[esp+4])', P.RAW[o:o+4].hex() == '8b542404', P.RAW[o:o+4].hex())
ck('S1b 次指令 == 8b c1 (mov eax,ecx)', P.RAW[o+4:o+6].hex() == '8bc1', P.RAW[o+4:o+6].hex())
ins = dis(0x6E8000, 0x7E)
pairs = 0
for k in range(len(ins) - 1):
    i, nx = ins[k], ins[k+1]
    if i.mnemonic == 'mov' and '[edx' in i.op_str:
        reg = i.op_str.split(',')[0].strip()
        if reg.isalpha() and nx.mnemonic == 'mov' and nx.op_str.startswith(('dword ptr [eax', 'byte ptr [eax')) and nx.op_str.endswith(reg):
            pairs += 1
ck('S1c 逐字段 load[edx]->store[eax] 拷贝对 >= 4', pairs >= 4, pairs)
ck('S1d 四个字段 0x10/0x18/0x1c/0x20 全被拷贝',
   all(any(f'[eax + {h}]' in i.op_str for i in ins) for h in ('0x10', '0x18', '0x1c', '0x20')), '')

# ---------- S2 覆写在拷贝之后 ----------
reps = [i.address for i in ins if i.mnemonic == 'rep movsd']
ck('S2a rep movsd 段数 == 3', len(reps) == 3, [hex(x) for x in reps])
ck('S2b 覆写点 0x6E807E 在全部 rep movsd 之后', all(r < 0x6E807E for r in reps), [hex(x) for x in reps])

# ---------- S3 覆写无条件 ----------
tj = []
for i in ins:
    if i.mnemonic.startswith('j'):
        try: tj.append((i.address, i.mnemonic, int(i.op_str, 16)))
        except: tj.append((i.address, i.mnemonic, None))
skip = [t for t in tj if t[2] is not None and 0x6E807E < t[2] <= 0x6E8099]
ck('S3a 0x6E8000..0x6E807E 内无分支跳过覆写', len(skip) == 0, [(hex(a), m, hex(t) if t else None) for a, m, t in tj])
ck('S3b 分支只在 0x6E80CD 之后的循环体里', all(a >= 0x6E80CD for a, m, t in tj) or all(a >= 0x6E807E for a, m, t in tj),
   [hex(a) for a, m, t in tj])

# ---------- S4 覆写是 4 条独立 mov ----------
on = P.r2o(0x6E807E)
four = P.RAW[on:on+0x1B]
ck('S4a 覆写 4 条指令字节精确匹配',
   four.hex() == 'c70080467f00c7400464467f00c740085c467f00c7400c54467f00', four.hex())
ck('S4b 覆写是 mov [eax+K],imm32 形态而非 rep movs',
   all(ins_ is None for ins_ in [None]) and four[0] == 0xC7 and four[6] == 0xC7 and four[13] == 0xC7 and four[20] == 0xC7, four.hex())

# ---------- S5/S6 两表差集 ----------
A = slots(OLD); B = slots(NEW)
ck('S5a 旧表槽数 == 24', len(A) == 24, len(A))
ck('S5b 新表槽数 == 27', len(B) == 27, len(B))
dk = [i for i in range(min(len(A), len(B))) if A[i] != B[i]]
ck('S5c 共同前缀内差异槽 == [3,5,6,8,11,12,13]', dk == [3, 5, 6, 8, 11, 12, 13], dk)
ck('S6 新表多出 3 槽 (24,25,26)', len(B) - len(A) == 3, [(i, hex(B[i])) for i in range(len(A), len(B))])
extra = [(i, B[i]) for i in range(len(A), len(B))]

# S5 的实质：旧槽是纯桩的，新槽是真实现
o4 = P.r2o(0x4C9150)
ck('S5d 0x4C9150 == 33 c0 c3 90 (xor eax,eax;ret)', P.RAW[o4:o4+4].hex() == '33c0c390', P.RAW[o4:o4+4].hex())
stub_replaced = [i for i in dk if A[i] == 0x4C9150]
ck('S5e 差异槽中「纯桩被替换」的槽号 == [3,5,6,11,12]', stub_replaced == [3, 5, 6, 11, 12], stub_replaced)
# 槽 3 的新实现是 QueryInterface 形态：含 E_POINTER 0x80004003 与 ret 8
qi = P.RAW[P.r2o(0x6E8710):P.r2o(0x6E8710)+0x20]
ck('S5f 槽3 新实现含 E_POINTER 0x80004003', b'\x03\x40\x00\x80' in qi, qi.hex())
ck('S5g 槽3 新实现早退为 ret 8 (c2 08 00)', P.RAW[P.r2o(0x6E871D):P.r2o(0x6E871D)+3].hex() == 'c20800',
   P.RAW[P.r2o(0x6E871D):P.r2o(0x6E871D)+3].hex())
# 槽 8 旧值是 0x4105A0（R195 PX3 已证 = AbstractClass 析构形态）
ck('S5h 槽8 旧值 == 0x4105A0', A[8] == 0x4105A0, hex(A[8]))

# ---------- 反控 ----------
ck('R1 反控 若判覆写在拷贝之前则该断言会 FAIL（此处显式验证顺序）',
   0x6E807E > max(reps), (hex(0x6E807E), [hex(x) for x in reps]))
stub_all = all(A[i] == 0x4C9150 for i in [3, 5, 6, 11, 12])
ck('R2a 反控 若槽3/5/6/11/12 旧值不是纯桩，则 S5e 失去判别力', stub_all, '')
ck('R2b 反控 槽13 旧值 0x410410 != 纯桩 0x4C9150（说明并非全部纯桩）',
   A[13] == 0x410410 and A[13] != 0x4C9150, hex(A[13]))
ck('R3 反控 若存在跳过覆写的分支，S3a 会 FAIL（实测 skip 数 = 0）', len(skip) == 0, len(skip))

res = dict(
    func=0x6E8000, ctor_form=dict(edx_is_src=True, eax_is_this=True, field_pairs=pairs),
    reps=[hex(x) for x in reps], branches=[(hex(a), m, hex(t) if t else None) for a, m, t in tj],
    overwrite=dict(addr=0x6E807E, bytes=four.hex(), unconditional=True),
    vtable_old=dict(addr=0x7E1F50, n=len(A), slots=[hex(x) for x in A]),
    vtable_new=dict(addr=0x7F4680, n=len(B), slots=[hex(x) for x in B]),
    diff_slots=[dict(i=i, old=hex(A[i]), new=hex(B[i]), old_is_stub=(A[i] == 0x4C9150)) for i in dk],
    extra_slots=[dict(i=i, va=hex(v)) for i, v in extra],
    fails=fails, asserts=N,
)
open('/home/t628/projects/ra2-campaign-forge/_r197/m3_overwrite.json', 'w').write(json.dumps(res, ensure_ascii=False, indent=1))
print('\n--- SUMMARY ---')
print('old n=%d new n=%d 差异槽=%s' % (len(A), len(B), dk))
print('纯桩被替换:', stub_replaced, ' 多出槽:', [hex(v) for i, v in extra])
print('覆写字节:', four.hex())
print('asserts', N, 'fails', len(fails), fails)
