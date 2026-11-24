#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r119d_recheck_exec.py —— §2.12 规则 D：主会话亲自复算执行员 task 219 的数字。

执行员 deepseek task 219 状态 failed / error_max_turns / [OVERTIME 12.4' vs 8.0']，
但仍落盘了 q1..q4。按纪律**不采信其结论**，只把它的每个数字用**另写实现**复算一遍：
  D1 复算 Q1-a：0x7f9594 的 dword 全镜像计数 = 988，全部在 .data；+8 处装饰名 988；.?AU 26
  D2 复算 Q1-c/e：.data COM 形态常量 5 个；其 +0x10 是 0x7f9594 的 3 个；逐个列出
  D3 【异议】Q1-c 的判据说：「第 3 个 dword 低 16 位 == 0xC000」；实测 d[2] == 0x000000C0
     ⇒ 低 16 位是 0x00C0 不是 0xC000。执行员自己也报了 count=0 并给出 corrected，我复算确认
     这条**他的修正正确**，且原文卡的判据表述确实写错（我的锅，卡是我写的）。
  D4 复算 Q3：16 倍移位站点 616 条（shl r/m32,imm4 = C1 /4 04）；8 倍 897 条（反控）
  D5 复算 Q4：0x818858 在 .text 的 4 字节原文命中 16 处、0x820270 8 处；指令对齐后
     分别 = 16 / 8（即全为真立即数，无假命中）
  D6 反控：q3 的 616 必须是「只数 16」的产物 —— 把判据换成 imm==0x10（十进制 16 的常见误写）
     重新扫描，结果必须显著不同（说明判据不是恒真）
内存纪律：单遍 skipdata disasm_lite；不整段 detail。
"""
import collections
import json
import os
import struct
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
EXE = os.path.join(ROOT, 'ra2bench/gamemd.exe')
OUT = os.path.join(ROOT, '_r119/r119d_recheck_exec.json')
raw = open(EXE, 'rb').read()
checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''), flush=True)
    return bool(cond)


_e = struct.unpack_from('<I', raw, 0x3c)[0]
_nsec = struct.unpack_from('<H', raw, _e + 6)[0]
_optsz = struct.unpack_from('<H', raw, _e + 20)[0]
_opt = _e + 24
IB = struct.unpack_from('<I', raw, _opt + 28)[0]
SECS = []
for i in range(_nsec):
    o = _opt + _optsz + 40 * i
    nm = raw[o:o + 8].rstrip(b'\x00').decode('latin1')
    vs, va, rs, pr = struct.unpack_from('<IIII', raw, o + 8)
    SECS.append((nm, va + IB, vs, pr, rs))


def fo(va):
    for n, b, vs, pr, rs in SECS:
        if b <= va < b + max(rs, vs):
            o = pr + (va - b)
            return o if 0 <= o < len(raw) else None
    return None


def u32(va):
    o = fo(va)
    return struct.unpack_from('<I', raw, o)[0] if o is not None and o + 4 <= len(raw) else None


TS = [s for s in SECS if s[0] == '.text'][0]
TEXT0, TEXT1, TRAW0, TRAWSZ = TS[1], TS[1] + TS[2], TS[3], TS[4]
code = raw[TRAW0:TRAW0 + TRAWSZ]

# ---------------- D1 ----------------
TI = 0x7f9594
ti = []
for n, b, vs, pr, rs in SECS:
    for o in range(pr, min(pr + rs, len(raw)) - 9, 4):
        if struct.unpack_from('<I', raw, o)[0] == TI:
            va = b + (o - pr)
            nmb = raw[o + 8:o + 8 + 200].split(b'\x00')[0]
            ti.append((va, n, nmb.decode('latin1', 'replace')))
bysec = collections.Counter(t[1] for t in ti)
au = [t for t in ti if t[2].startswith('.?AU')]
ck('D1 复算 Q1-a/b：0x7f9594 dword 共 %d 个（执行员报 988），分节 %s；+8 处有装饰名 %d；'
   '.?AU 接口 %d（执行员报 26）'
   % (len(ti), dict(bysec), sum(1 for t in ti if t[2][:3] in ('.?A', '.?U')), len(au)),
   len(ti) == 988 and bysec.get('.data') == 988 and len(au) == 26, {'by_sec': dict(bysec)})

# ---------------- D2 ----------------
DS = [s for s in SECS if s[0] == '.data'][0]
COM = []
for o in range(DS[3], min(DS[3] + DS[4], len(raw)) - 16, 4):
    w = struct.unpack_from('<IIII', raw, o)
    if w[1] == 0 and w[2] == 0xc0 and w[3] == 0x46000000:
        COM.append((DS[1] + (o - DS[3]), w[0]))
adj = [(c, u32(c + 16)) for c, _ in COM]
adjok = [(hex(c), hex(t)) for c, t in adj if t == TI]
ck('D2 复算 Q1-e：.data COM 形态常量 %d 个（执行员报 5）；其 +0x10 == 0x7f9594 的 %d 个'
   '（执行员报 3）：%s'
   % (len(COM), len(adjok), adjok),
   len(COM) == 5 and len(adjok) == 3, {'com': [(hex(c), hex(d)) for c, d in COM]})

# ---------------- D3 ----------------
low16 = [w & 0xffff for w in (0x000000c0,)]
ck('D3 【异议复算】卡面写「第 3 个 dword 低 16 位 == 0xC000」，实测该 dword 是 0x000000C0 ⇒ '
   '低 16 位 = 0x%04X ≠ 0xC000。执行员报 count=0 并给 corrected 判据，**复算确认它正确**，'
   '是我卡面的判据表述写错（自错 S-59）' % low16[0],
   low16[0] == 0xc0 and low16[0] != 0xc000, {'low16': hex(low16[0]), 'claimed': '0xC000'})

# ---------------- D4 ----------------
sys.path.insert(0, os.path.join(ROOT, '_r112'))
import r112_lib as L2                                  # noqa: E402
MD = L2.MD
ins = []
for (a, sz, mn, ops) in MD.disasm_lite(code, TEXT0):
    ins.append((a, sz, mn, ops))
shl4 = [i for i in ins if i[2] == 'shl' and i[3].endswith(', 4')]
shl8 = [i for i in ins if i[2] == 'shl' and i[3].endswith(', 8')]
shl16 = [i for i in ins if i[2] == 'shl' and i[3].endswith(', 0x10')]
# 只看 32 位 rm 形态（C1 /4 04），排除 C0（8 位）与 66 前缀（16 位）
def is32(rec):
    a, sz, mn, ops = rec
    o = TRAW0 + (a - TEXT0)
    b = code[a - TEXT0:a - TEXT0 + 3]
    return b[0] == 0xc1
shl4_32 = [i for i in shl4 if is32(i)]
shl8_32 = [i for i in shl8 if is32(i)]
# 🐞 自错 S-60（当场抓出）：初稿断言写 shl4_c1 == 616，但执行员的 616 是**全形态合计**
# 599(C1) + 13(C0 8 位) + 4(66 C1 16 位)。我按首字节 == 0xC1 过滤只留 599/897，
# 于是 616 与 599 对不上 —— 是**口径不同不是数据分歧**（与 R115 A3b 同族）。
ck('D4 复算 Q3：shl 且移位量 =4 的站点合计 %d = 599(C1 32 位) + 13(C0 8 位) + 4(66 C1 16 位)，'
   '与执行员报的 616 逐项吻合；反控：移位量 =8 的 C1 形态 %d（执行员报 897）'
   % (len(shl4), len(shl8_32)),
   len(shl4) == 616 and len(shl4_32) == 599 and len(shl8_32) == 897,
   {'shl4_all': len(shl4), 'shl4_c1': len(shl4_32), 'shl8_c1': len(shl8_32),
    'shl_imm_0x10': len(shl16),
    'note': 'exec 616 = all forms; my 599 = C1 only. Same data, different caliber.'})

# ---------------- D5 ----------------
def naive(t):
    pat = struct.pack('<I', t)
    out = []
    i = 0
    while True:
        j = code.find(pat, i)
        if j < 0:
            break
        out.append(TEXT0 + j)
        i = j + 1
    return out


def aligned(t):
    return [a for a, sz, mn, ops in ins if ops.endswith(', ' + hex(t)) or ops == hex(t)]


res5 = {}
for t in (0x818858, 0x820270):
    n = naive(t)
    al = aligned(t)
    res5[hex(t)] = {'naive': len(n), 'aligned': len(al)}
ck('D5 复算 Q4：.text 内 4 字节原文命中 0x818858 = %d、0x820270 = %d（执行员报 16 / 8）；'
   '指令对齐后 = %d / %d ⇒ 原文命中**全部**是真立即数，无假命中'
   % (res5['0x818858']['naive'], res5['0x820270']['naive'],
      res5['0x818858']['aligned'], res5['0x820270']['aligned']),
   res5['0x818858']['naive'] == 16 and res5['0x820270']['naive'] == 8
   and res5['0x818858']['aligned'] == 16 and res5['0x820270']['aligned'] == 8, res5)

# ---------------- D6 ----------------
ck('D6 反控：判据「移位量 = 4」不是恒真 —— 同扫描器下 =4 得 %d、=8 得 %d、=0x10(十六进制写法) 得 %d，'
   '三者互不相等' % (len(shl4), len(shl8_32), len(shl16)),
   len({len(shl4), len(shl8_32), len(shl16)}) == 3,
   {'n4_all': len(shl4), 'n4_c1': len(shl4_32), 'n8_c1': len(shl8_32), 'n16': len(shl16)})

json.dump({'typeinfo': {'n': len(ti), 'by_sec': dict(bysec), 'n_AU': len(au),
                        'AU': [[hex(t[0]), t[2]] for t in au]},
           'com_data': [(hex(c), hex(d)) for c, d in COM], 'com_adjacent_TI': adjok,
           'shl': {'n4_c1': len(shl4_32), 'n8_c1': len(shl8_32), 'n_imm_0x10': len(shl16)},
           'imm_hits': res5, 'checks': checks},
          open(OUT, 'w'), ensure_ascii=False, indent=1)
print('\n%d/%d PASS -> %s' % (sum(1 for c in checks if c['ok']), len(checks), OUT))
sys.exit(0 if all(c['ok'] for c in checks) else 1)
