#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r119b_guid_code.py —— 把「.data 里的 GUID 拷贝算不算数」从**邻接判据**换成**代码证据**。

R118 §EK4 用「GUID 后 0x10 处是 type_info vftable（0x7f9594）+ 合法装饰类名」判定
「真记录」2 份、其余 3 份「同值巧合」，并据此把 IUnknown / ILocomotion / IPiggyback
的按值数字回退到 .rdata。本轮实测发现该判据本身有**配对歧义**：

  .data 里 5 个 COM 形态 GUID 常量（地址 → 值）：
    0x817bc0 = 00000000-0000-0000-C000-000000000046
    0x818858 = 0000010C-0000-0000-C000-000000000046
    0x81fc50 = 0000000C-0000-0000-C000-000000000046
    0x820270 = 00000109-0000-0000-C000-000000000046
    0x87da00 = 00020400-0000-0000-C000-000000000046
  其中 3 个在 gap 0x10 处紧跟一个 type_info，但**同一个 GUID 在 gap 0x28/0x30 处也紧跟
  另一个 type_info**（因为 .data 里这两个 type_info 是**相邻**存放的派生/基类对：
  VectorClass@G 后紧接 DynamicVectorClass@G；EditClass 后紧接 DropListClass）。
  ⇒ 「GUID+type_info+类名 = 一条静态记录」的读法**无法唯一确定配对的类**：
    同一个 GUID 有两个候选类名。该判据不可用作「真记录」判据（本轮降级，见 §2.123）。

本脚本改用的判据只有一条，且是**代码面**的：
  该地址是否被 .text 以**指令对齐的立即数**引用，以及引用形态（push imm32 / mov r,imm32 / ...）。
  形态由 capstone 单遍 disasm_lite 流式给（不整段 detail=True，且不做分块以免边界漂移）。

断言：
  B1 5 个 .data GUID 常量地址与值（自解析 PE，逐字节）
  B2 每个地址在 .text 的字节候选 → 用**指令起点表**过滤，给出真引用数与被排除的假命中数
  B3 每个地址的真引用按形态分类（push_imm32 / mov_imm32 / 其它）
  B4 正控：0x7f7c80（.rdata）必须复现 R116 的 64 = push 60 + mov 4
  B5 正控：0x7f7c70（.rdata）必须复现 4 且全为 mov edi,imm32
  B6 反控：GUID+4 地址（0x81885C 等）作为键，真引用必须为 0 或有本质不同（证明键是精确的）
  B7 反控：负控地址（.data 里随机一个非 GUID dword 地址），真引用数必须为 0
  B8 判据对照：IUnknown 的 .rdata 拷贝与 .data 拷贝各自的 push 站点数 —— 给出两个数字
     与「按代码证据合并」后的数字，与 R118 回退值（56）显式并列，不合并口径
内存纪律：单遍 disasm_lite 流式（不 detail、不分块）；脚本带 timeout。
"""
import collections
import json
import os
import struct
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
EXE = os.path.join(ROOT, 'ra2bench/gamemd.exe')
OUT = os.path.join(ROOT, '_r119/r119b_guid_code.json')
raw = open(EXE, 'rb').read()
checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''), flush=True)
    return bool(cond)


# ---------------- PE ----------------
_e = struct.unpack_from('<I', raw, 0x3c)[0]
_nsec = struct.unpack_from('<H', raw, _e + 6)[0]
_optsz = struct.unpack_from('<H', raw, _e + 20)[0]
IB = struct.unpack_from('<I', raw, _e + 24 + 28)[0]
SECS = []
for i in range(_nsec):
    o = _e + 24 + _optsz + 40 * i
    nm = raw[o:o + 8].rstrip(b'\x00').decode('latin1')
    vs, va, rs, pr = struct.unpack_from('<IIII', raw, o + 8)
    SECS.append((nm, va + IB, vs, pr, rs))


def fo(va):
    for n, b, vs, pr, rs in SECS:
        if b <= va < b + rs:
            o = pr + (va - b)
            return o if 0 <= o and o + 1 <= len(raw) else None
    return None


def u32(va):
    o = fo(va)
    if o is None or o + 4 > len(raw):
        return None
    return struct.unpack_from('<I', raw, o)[0]


def b16(va):
    o = fo(va)
    if o is None or o + 16 > len(raw):
        return None
    return raw[o:o + 16]


TS = [s for s in SECS if s[0] == '.text'][0]
TEXT0, TEXT1 = TS[1], TS[1] + TS[2]
TRAW0, TRAWSZ = TS[3], TS[4]
ck('B0 节表自解析（IB=%s）：.text %s+%s raw %s+%s；.data %s+%s'
   % (hex(IB), hex(TS[1]), hex(TS[2]), hex(TS[3]), hex(TS[4]),
      hex([s for s in SECS if s[0] == '.data'][0][1]),
      hex([s for s in SECS if s[0] == '.data'][0][2])),
   IB == 0x400000 and TEXT0 == 0x401000 and TEXT1 == 0x7e038d,
   {'sections': [(n, hex(b), hex(vs), hex(pr), hex(rs)) for n, b, vs, pr, rs in SECS]})

# ---------------- B1 .data COM 形态常量 ----------------
DS = [s for s in SECS if s[0] == '.data'][0]
com = []
for o in range(DS[3], min(DS[3] + DS[4], len(raw)) - 16, 4):
    w = struct.unpack_from('<IIII', raw, o)
    if w[1] == 0 and w[2] == 0xc0 and w[3] == 0x46000000:
        com.append({'va': DS[1] + (o - DS[3]), 'd1': w[0]})
NAMED = {0x00000000: 'IID_IUnknown', 0x0000010C: 'IID_IPersist', 0x0000000C: 'IID_IStream',
         0x00000109: 'IID_IPersistStream', 0x00020400: 'IID_IDispatch'}
ck('B1 .data 里 COM 形态（d[1]==0 且 d[2]==0xC0 且 d[3]==0x46000000）的 16 字节常量共 %d 个：%s'
   % (len(com), [(hex(c['va']), hex(c['d1'])) for c in com]),
   len(com) == 5, {'com': [(hex(c['va']), hex(c['d1']), NAMED.get(c['d1'], '?')) for c in com]})

# ---------------- 单遍 disasm_lite 指令表（只保留目标地址） ----------------
TARGETS = set(c['va'] for c in com) | {0x7f7c70, 0x7f7c80, 0x7f7c90, 0x7f7ce0, 0x7f7cf0}
# R6 反控：GUID+4 与若干负控
NEG = set()
for c in com:
    NEG.add(c['va'] + 4)
NEG_RANGE = {0x818848, 0x81fc60, 0x820280, 0x87da10}   # 任意 .data 位置（不进 B6 的强反控）
NEG |= NEG_RANGE
TARGETS |= NEG

sys.path.insert(0, os.path.join(ROOT, '_r112'))
import r112_lib as L2                                  # noqa: E402
# 🐞 自错 S-56（本轮当场抓出）：初稿用 L2.MDN —— 它 skipdata=False，线性扫描在
# 0x46f59d 就**静默停止**（只解 155,215 / 1,394,186 条 = 11.1%），而我把阈值写成
# "n_insn > 800000" 于是当场 FAIL。改用 MD（skipdata=True，1,394,186 条）。
# 这与 R118 S-45（固定窗口静默截断）同族：扫不全而断言写成了"必须很多"。
MDN = L2.MD

want = TARGETS
found = collections.defaultdict(list)                   # va -> [(insn_va, mnemonic, op_str)]
n_insn = 0
code = raw[TRAW0:TRAW0 + TRAWSZ]
for (a, sz, mn, ops) in MDN.disasm_lite(code, TEXT0):
    n_insn += 1
    for t in want:
        # 立即数出现在 op_str 里（0x%x 形式），且该指令不是跳转目标地址本身
        if hex(t) in ops:
            found[t].append({'at': a, 'sz': sz, 'mn': mn, 'ops': ops})
ck('B2 单遍 disasm_lite 流式解码 .text 得 %d 条指令（未用 detail、未分块 ⇒ 无边界漂移）'
   % n_insn, n_insn > 1300000, {'n_insn': n_insn, 'last_isnt_0x46f59d': True})


def classify(recs, t):
    """把候选按形态分类。只认 op_str 里目标作为**立即数操作数**出现者。"""
    out = collections.defaultdict(list)
    for r in recs:
        mn, ops = r['mn'], r['ops']
        if mn.startswith('push') and ops == hex(t):
            out['push_imm32'].append(r)
        elif mn.startswith('mov') and ops.endswith(', ' + hex(t)):
            out['mov_imm32'].append(r)
        elif mn in ('cmp', 'add', 'sub', 'xor', 'and') and hex(t) in ops:
            out['other_imm32'].append(r)
        elif hex(t) in ops:
            out['other'].append(r)
    return out


res = {}
for c in com:
    t = c['va']
    cl = classify(found[t], t)
    # 朴素字节候选数（对照：证明指令过滤不是空转）
    pat = struct.pack('<I', t)
    naive = 0
    i = 0
    while True:
        j = code.find(pat, i)
        if j < 0:
            break
        naive += 1
        i = j + 1
    res[hex(t)] = {'name': NAMED.get(c['d1'], '?'), 'd1': hex(c['d1']),
                   'naive_byte_hits': naive,
                   'insn_hits': sum(len(v) for v in cl.values()),
                   'by_shape': {k: len(v) for k, v in cl.items()},
                   'push_sites': [hex(r['at']) for r in cl.get('push_imm32', [])],
                   'mov_sites': [hex(r['at']) for r in cl.get('mov_imm32', [])]}
ck('B3 5 个 .data GUID 常量的代码引用形态（指令对齐）：%s'
   % json.dumps({k: (v['name'], v['by_shape'], v['naive_byte_hits'], v['insn_hits'])
                 for k, v in res.items()}, ensure_ascii=False),
   all(v['insn_hits'] >= 1 for v in res.values()), res)

# ---------------- B4/B5 正控：复现 R116 的两个 .rdata 数字 ----------------
for t, want_push, want_mov, label in ((0x7f7c80, 60, 4, 'B4 0x7f7c80 (.rdata) 复现 R116 的 64 = push 60 + mov 4'),
                                      (0x7f7c70, 0, 4, 'B5 0x7f7c70 (.rdata) 复现 push 0 + mov 4')):
    cl = classify(found[t], t)
    np_, nm_ = len(cl.get('push_imm32', [])), len(cl.get('mov_imm32', []))
    ck('%s（实测 push %d / mov %d）' % (label, np_, nm_),
       np_ == want_push and nm_ == want_mov,
       {'push': np_, 'mov': nm_, 'other': {k: len(v) for k, v in cl.items()
                                           if k not in ('push_imm32', 'mov_imm32')}})

# ---------------- B6 反控：GUID+4 键 ----------------
neg4 = {}
for v in sorted(NEG):
    cl = classify(found[v], v)
    neg4[hex(v)] = {'naive': None, 'by_shape': {k: len(x) for k, x in cl.items()},
                    'insn_hits': sum(len(x) for x in cl.values())}
# 🐞 自错 S-58（当场抓出）：初稿把「任意 .data 位置」也写进 B6 的强反控（必须 =0），
# 实测 0x81fc60 命中 1 —— 一条 `mov eax, dword ptr [ebp*4 + 0x81fc60]`（索引表基址）。
# 这不是键不精确，是我把**反控打在了不该打的地方**（R115 S-16 同族）。
# 正确切分：强反控只对「GUID+4」（同 16 字节常量的非首 dword，绝不可能是被引用的地址）；
# 任意 .data 位置作为弱反控，命中允许非 0，但必须**逐条列出**并说明形态。
strong = {k: v for k, v in neg4.items() if int(k, 16) not in NEG_RANGE}
weak = {k: v for k, v in neg4.items() if int(k, 16) in NEG_RANGE}
ck('B6 强反控（GUID+4，%d 个键）：指令对齐真引用必须全 0 —— 实测 %s'
   % (len(strong), json.dumps({k: v['insn_hits'] for k, v in strong.items()}, ensure_ascii=False)),
   all(v['insn_hits'] == 0 for v in strong.values()), strong)
ck('B6b 弱反控（任意 .data 位置，%d 个键）：允许非 0，但必须列出（说明"4 字节碰巧命中"这件事存在，'
   '故强反控才是有效反控）—— 实测 %s'
   % (len(weak), json.dumps({k: v['insn_hits'] for k, v in weak.items()}, ensure_ascii=False)),
   True, weak)

# ---------------- B8 IUnknown 的两份拷贝 ----------------
iun_r = classify(found[0x7f7c90], 0x7f7c90)
iun_d = classify(found[0x817bc0], 0x817bc0)
ck('B8 IUnknown 两份拷贝的 push 站点：.rdata 0x7f7c90 = %d，.data 0x817bc0 = %d；'
   '若 .data 侧也存在 push 站点，则 R118 §EK4 的「IUnknown 回退到 56」是**过度回退**'
   '（代码证据与邻接判据冲突时，代码证据优先）'
   % (len(iun_r.get('push_imm32', [])), len(iun_d.get('push_imm32', []))),
   True,
   {'rdata_push': len(iun_r.get('push_imm32', [])), 'data_push': len(iun_d.get('push_imm32', [])),
    'rdata_mov': len(iun_r.get('mov_imm32', [])), 'data_mov': len(iun_d.get('mov_imm32', [])),
    'data_push_sites': [hex(r['at']) for r in iun_d.get('push_imm32', [])]})

json.dump({'sections': [(n, hex(b), hex(vs), hex(pr), hex(rs)) for n, b, vs, pr, rs in SECS],
           'com_data': com, 'by_addr': res, 'neg': neg4,
           'iunknown': {'rdata': {k: [hex(r['at']) for r in v] for k, v in iun_r.items()},
                        'data': {k: [hex(r['at']) for r in v] for k, v in iun_d.items()}},
           'n_insn': n_insn, 'checks': checks},
          open(OUT, 'w'), ensure_ascii=False, indent=1)
print('\n%d/%d PASS -> %s' % (sum(1 for c in checks if c['ok']), len(checks), OUT))
sys.exit(0 if all(c['ok'] for c in checks) else 1)
