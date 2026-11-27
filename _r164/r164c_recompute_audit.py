#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R164-C · 复算审计员 #383（deepseek/audit）的七条判定（§2.12 规则 D）

审计员结论一律不整段采信：每条都写成本脚本里可失败断言，正控反控成对。
本轮它指出 r164a 里有**三处硬编码 PASS / 恒真断言**与**一处措辞过弱**，
本脚本先复算事实，再由 r164a 的修订版（v2）把判据补实。
"""
import hashlib
import io
import json
import os
import re
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
A2 = 'lead/next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json'
CG = 'lead/next_re_20261117_r14/C01_census/EVIDENCE/callgraph.json'
R164A = '_r164/r164a_a2_rule.py'
FLOORS = '_r160/facts_floors.py'
OUT = '_r164/r164c_recompute_audit.json'

FAIL = 0
RES = []


def ck(name, cond, detail=''):
    global FAIL
    ok = bool(cond)
    if not ok:
        FAIL += 1
    RES.append({'id': name, 'ok': ok, 'detail': str(detail)[:400]})
    print(('PASS ' if ok else 'FAIL ') + name + (('  :: ' + str(detail)[:280]) if detail else ''))


MARK = b'}, "bounds": ['
raw = open(A2, 'rb').read()
i = raw.find(MARK)
calls_txt = raw[:i + 1]
calls = json.loads(calls_txt.decode('utf-8') + '}')['calls']
A2_PAIRS = set((t, s) for t, v in calls.items() for s in v)

# ---------------------------------------------------------------- 1 · D1g 恒真
print('== 1 · 审计员第 1 条：r164a 里哪些断言没有约束力 ==')
src = io.open(R164A, encoding='utf-8').read()
ck('T1a r164a 原文含 `or True`（恒真尾缀）', 'or True' in src, src.count('or True'))
ck('T1b r164a 原文含 `ck(…, True, …)` 硬编码 PASS',
   bool(re.search(r"ck\([^)]*?,\s*True,\s*'", src, re.S)), None)
ck('T1c 审计员说 D1b/D1c 是有序比较 ⇒ 复算：源码同时含 == 序列比较与 all(...==)',
   'list(recon.keys()) == list(calls.keys())' in src and 'recon[k] == calls[k]' in src)
# 反控：把 D1b 的判据换成集合比较后，交换两键就检不出
ks = list(calls)
sw = set(ks)
ck('T1d 反控：集合比较对「交换两键顺序」无分辨力（set 相等）⇒ 必须用序列比',
   sw == set([ks[1], ks[0]] + ks[2:]), None)

# ---------------------------------------------------------------- 2 · E1 长度差
print('== 2 · 审计员第 2 条：E1 的 ser[:-1] 不含净长度差 ==')
ser = json.dumps({'calls': calls}, ensure_ascii=False).encode('utf-8')
ck('T2a len(ser)=913,239 / len(calls_txt)=913,238', len(ser) == 913239 and len(calls_txt) == 913238,
   (len(ser), len(calls_txt)))
ck('T2b 差的 1 B 就是外层右花括号', ser[-1:] == b'}' and calls_txt[-1:] == b'}')
ck('T2c 反控：ser 中部插 1 B ⇒ ser[:-1] 长度 913,239 ≠ 913,238（净长度差先被长度比抓住）',
   len((ser[:1000] + b'X' + ser[1000:])[:-1]) == 913239, len((ser[:1000] + b'X' + ser[1000:])[:-1]))

# ---------------------------------------------------------------- 3 · 尾填充区间未被断言
print('== 3 · 审计员第 3 条：C1c 只钉计数、没钉区间 ==')
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

data = io.open('ra2bench/gamemd.exe', 'rb').read()
pe = pefile.PE('ra2bench/gamemd.exe', fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
t = [s for s in pe.sections if s.Name.decode().rstrip('\x00') == '.text'][0]
TEXT_VA = IB + t.VirtualAddress
VS_END = TEXT_VA + t.Misc_VirtualSize
RAW_END = TEXT_VA + t.SizeOfRawData


def starts_of(blob):
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.skipdata = True
    return [a for a, *_ in md.disasm_lite(blob, TEXT_VA)]


s_vs = set(starts_of(data[t.PointerToRawData:t.PointerToRawData + t.Misc_VirtualSize]))
s_raw = starts_of(data[t.PointerToRawData:t.PointerToRawData + t.SizeOfRawData])
extra = [a for a in s_raw if a not in s_vs]
ck('T3a raw 起点 %d / VS 起点 %d / 差 %d' % (len(s_raw), len(s_vs), len(extra)),
   len(s_raw) == 1394186 and len(s_vs) == 1392592 and len(extra) == 1594, len(extra))
ck('T3b 差集全部落在 [VS 尾界, raw 尾界) 内',
   all(VS_END <= a < RAW_END for a in extra),
   (hex(min(extra)), hex(max(extra)), hex(VS_END), hex(RAW_END)))
ck('T3c 差集 < VS_END 的条数 == 0（审计员说的这一点 r164a 原来只写在注释里）',
   sum(1 for a in extra if a < VS_END) == 0)
ck('T3d 该区间字节全 0x00（3,187 B）',
   data[t.PointerToRawData + (VS_END - TEXT_VA):t.PointerToRawData + (RAW_END - TEXT_VA)]
   == b'\x00' * (RAW_END - VS_END),
   RAW_END - VS_END)
ck('T3e 反控：把起点集 >= VS_END 的条数写死为 0 是恒真（starts 来自长度=VSZ 的 blob）',
   sum(1 for x in s_vs if x >= VS_END) == 0 and max(s_vs) < VS_END, hex(max(s_vs)))

# ---------------------------------------------------------------- 4 · F7 措辞过弱
print('== 4 · 审计员第 4 条：F7 硬编码 PASS，两产物差集未量化 ==')
cg = json.load(open(CG, encoding='utf-8'))
# 顶层键是**调用目标**（十进制字符串形式），条目里的 site 是站点、src 是调用者函数
CG_PAIRS = set()
for k, v in cg.items():
    for e in v:
        CG_PAIRS.add(('%08X' % int(k), '%08X' % e['site']))
ck('T4a callgraph.json 顶层键 6,273 / 条目 57,577', len(cg) == 6273 and len(CG_PAIRS) == 57577,
   (len(cg), len(CG_PAIRS)))
ck('T4b a2 对数 68,253', len(A2_PAIRS) == 68253, len(A2_PAIRS))
inter = A2_PAIRS & CG_PAIRS
ck('T4c 交集 57,576', len(inter) == 57576, len(inter))
ck('T4d a2 独有 10,677 / cg 独有 1', len(A2_PAIRS - CG_PAIRS) == 10677
   and len(CG_PAIRS - A2_PAIRS) == 1, (len(A2_PAIRS - CG_PAIRS), len(CG_PAIRS - A2_PAIRS)))
ck('T4e cg 独有那 1 对就是 (007C8B3D 目标, 0074836A 站点)；cg 的 src 是**调用者**、顶层键才是目标',
   CG_PAIRS - A2_PAIRS == {('007C8B3D', '0074836A')}, list(CG_PAIRS - A2_PAIRS)[:2])
ck('T4f cg ⊆ a2 不成立（cg 有 1 对不在 a2）⇒「口径不同」不能简化成「只差跳过策略」',
   not CG_PAIRS <= A2_PAIRS)
# a2 独有的 10,677 对：都是 skipdata 起点产出的（站点都在 bounds 里）
ck('T4g 反控：a2 独有的 10,677 对里，站点全在 bounds 起点集内',
   all(int(s, 16) in s_vs for _, s in (A2_PAIRS - CG_PAIRS)),
   sum(1 for _, s in (A2_PAIRS - CG_PAIRS) if int(s, 16) not in s_vs))

# ---------------------------------------------------------------- 5 · facts_floors 常量清单
print('== 5 · 审计员第 5 条：与当前版绑定的常量清单 ==')
ft = io.open(FLOORS, encoding='utf-8').read()


def lineno(pat):
    m = re.search(pat, ft, re.M)
    return None if not m else ft[:m.start()].count('\n') + 1


ck('T5a EXPECT_CUR 行号存在且是唯一带 V544 版本串的常量',
   "R17_R116_FACTINDEX_V544" in ft and ft.count('R17_R116_FACTINDEX_V544') == 1,
   lineno(r'^EXPECT_CUR'))
ck('T5b CUR 是别名（指向 EXPECT_CUR）', 'CUR = EXPECT_CUR' in ft)
ck('T5c CUR_SHA256 / TOTAL_BYTES / MASTER_SHA256 三个 pin 都在', all(
   re.search(r'^%s = ' % k, ft, re.M) for k in ('CUR_SHA256', 'TOTAL_BYTES', 'MASTER_SHA256')))
ck('T5d 反控：全文无任何 GATE_ 常量（审计员报的 docstring 与实现不符 —— 复算成立）',
   not re.search(r'^GATE_[A-Z_]+\s*=', ft, re.M) and 'GATE' in ft,
   [l for l in ft.split('\n') if 'GATE' in l][:2])
# D9 拼接字段：11 项，不含 EXPECT_CUR
m = re.search(r'_master = hashlib\.sha256\(\(.\\n.\.join\(\[(.*?)\]\)\)', ft, re.S)
segs = m.group(1)
# 注意：正则尾缀不能加 \b（`canon_g(GRADES)` 以 `)` 收尾，`)`→`,` 之间无词边界）
names = re.findall(r'(CUR_SHA256|TOTAL_BYTES|canon_g\(GRADES\)|canon_f\(FLOORS\)|canon_e\(EVID\)|'
                   r'canon_eb\(EVIDB\)|canon_l\(LOST\)|ITEMS|UNIQ|LOST_ITEMS|LOST_UNIQ)', segs)
ck('T5e D9 拼入 11 项且顺序如审计员所列', len(names) == 11, names)
ck('T5f D9 **不含** EXPECT_CUR（只改路径不改内容时 D9 不变）', 'EXPECT_CUR' not in segs)
ck('T5g 反控：D9 输入里也没有任何 GATE 计数', 'GATE' not in segs)

# ---------------------------------------------------------------- 6 · FLOORS 等值 pin
print('== 6 · 审计员第 6 条：FLOORS 事实上是等值 pin ==')
rows = {}
for line in io.open('lead/next_re_20261117_r14/R17_R116_FACTINDEX_V544/FACT_INDEX.tsv',
                    encoding='utf-8').read().split('\n'):
    if not line.strip():
        continue
    f = line.split('\t')
    rows[f[0]] = f
FL = dict((a, (int(b), int(c))) for a, b, c in re.findall(
    r"'([^']+)': \((\d+), (\d+)\),", re.search(r'FLOORS = \{\n(.*?)\n\}', ft, re.S).group(1)))
eq = sum(1 for k in FL if FL[k] == (len(rows[k][1].encode()), len(rows[k][4].encode())))
ck('T6a FLOORS 与现台账逐条相等 54/54（⇒ 事实等值 pin，不是宽松下界）', eq == 54, eq)
ck('T6b 反控：D6 是「<」判据 ⇒ 追加不触发（不是 bug）',
   'if s < fs' in ft and 'if l < fl' in ft)
ck('T6c D8 是「len(raw) < TOTAL_BYTES」判据 ⇒ 追加不触发', 'if len(raw) < TOTAL_BYTES' in ft)
ck('T6d D0 是等值 sha ⇒ 追加必被它抓住（真正拦截路径）',
   'if not IGNORE_PIN and sha != CUR_SHA256' in ft)

# ---------------------------------------------------------------- 落盘
print('\n== 结果 ==')
print('FAIL = %d ; 断言 %d' % (FAIL, len(RES)))
json.dump({'round': 'R164', 'script': 'r164c_recompute_audit.py', 'fail': FAIL, 'asserts': RES,
           'facts': {'a2_pairs': len(A2_PAIRS), 'cg_pairs': len(CG_PAIRS),
                     'inter': len(inter), 'a2_only': len(A2_PAIRS - CG_PAIRS),
                     'cg_only': len(CG_PAIRS - A2_PAIRS),
                     'cg_only_pair': sorted(CG_PAIRS - A2_PAIRS),
                     'raw_starts': len(s_raw), 'vs_starts': len(s_vs), 'extra': len(extra)}},
          io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('wrote', OUT)
sys.exit(1 if FAIL else 0)
