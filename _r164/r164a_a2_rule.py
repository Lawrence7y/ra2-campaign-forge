#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R164-A · a2_sites.json 全件可复现：把 R163 的「口径已复原、代码未复原」这条欠账结掉

R163 复原了 `bounds` 的一条等式，但 `calls` 段（6,728 键 / 68,253 对）无规则，
故 R163 待办第 1 条写「口径已复原、代码未复原」。本轮把**整个文件**复原成一段代码：

  H1  bounds 逐位等于 capstone(skipdata=True, VirtualSize blob) 的起点序列（R163 已证，本轮复算）
  H2  calls 逐键逐值（含**键顺序**与**键内站点顺序**）等于：
      同一次扫描里 mnemonic == 'call' 且操作数为立即数地址的 (目标 → 站点) 反向索引，
      键按**目标首次出现顺序**插入（dict 插入序），键内站点按扫描顺序追加
      ⇒ 不需要任何排序、去重、后处理；生成器 = 一次线性扫描 + 两个 dict/list
  H3  序列化逐字节闭合：calls 前缀 913,238 B + `, "bounds": [` + 数组段 16,711,104 B = 17,624,355 B
      数组段恰为 12 B × 1,392,592（`"XXXXXXXX", ` 形态，默认分隔符 ", "）

附加（结掉 R95 §6 未取得第 1 条的机制）：
  H4  R95 报「a2_sites 漏了 1 条直接调用 (target=007C8B3D, site=0074836A)」。
      该站点字节确为 E8 且 rel32 指向 0x7C8B3D，但它**落在某个 skip 块内部**（起点 0x748368 / 3 B）
      ⇒ 规则本身就不产出它（不是生成器漏写）；且 `C01_census/EVIDENCE/callgraph.json`
      里确有这一对 ⇒ 两件互不矛盾，只是扫描口径不同（本件用 skipdata，那份没跳数据）。

正反控成对；数字全部实测。只读二进制/JSON；只写 _r164/r164a_a2_rule.json。

★ 内存纪律：起点集用 array('I')（1.39M × 4 B ≈ 5.6 MB），不建 list-of-int / 第二份 set；
  `bounds` 用流式逐位比对；skipdata 必须**整段一次扫**（分块会在块边界重切出伪起点）。
"""
import array
import hashlib
import io
import json
import os
import sys

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
EXE = 'ra2bench/gamemd.exe'
A2 = 'lead/next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json'
CG = 'lead/next_re_20261117_r14/C01_census/EVIDENCE/callgraph.json'
OUT = '_r164/r164a_a2_rule.json'

FAIL = 0
RES = []


def ck(name, cond, detail=''):
    global FAIL
    ok = bool(cond)
    if not ok:
        FAIL += 1
    RES.append({'id': name, 'ok': ok, 'detail': str(detail)[:400]})
    print(('PASS ' if ok else 'FAIL ') + name + (('  :: ' + str(detail)[:300]) if detail else ''))


# ---------------------------------------------------------------- 0 · 段表 / 分段
print('== 0 · 段表 / 分段 ==')
data = io.open(EXE, 'rb').read()
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
t = [s for s in pe.sections if s.Name.decode().rstrip('\x00') == '.text'][0]
TEXT_VA = IB + t.VirtualAddress
TEXT_RSZ = t.SizeOfRawData
TEXT_VSZ = t.Misc_VirtualSize
VS_END = TEXT_VA + TEXT_VSZ
VS_BLOB = data[t.PointerToRawData:t.PointerToRawData + TEXT_VSZ]

raw_a2 = open(A2, 'rb').read()
ck('A0 a2_sites.json 17,624,355 B', len(raw_a2) == 17624355, len(raw_a2))
print('  sha256 =', hashlib.sha256(raw_a2).hexdigest())
ck('A0c .text VA=0x401000 / VSz=4,060,045 / 尾界 0x7E038D',
   TEXT_VA == 0x401000 and TEXT_VSZ == 4060045 and VS_END == 0x7E038D,
   '%#x / %d / %#x' % (TEXT_VA, TEXT_VSZ, VS_END))

MARK = b'}, "bounds": ['
ck('A1 分段标记 `}, "bounds": [` 在文件中恰出现 1 次', raw_a2.count(MARK) == 1, raw_a2.count(MARK))
i_mark = raw_a2.find(MARK)
ck('A1b 标记起始偏移 913,237', i_mark == 913237, i_mark)
SPLIT = i_mark + 1                                   # `}` 属 calls 段
calls_txt = raw_a2[:SPLIT]                           # `{"calls": {...}`（外层花括号待补）
rest_txt = raw_a2[SPLIT:]                            # `, "bounds": [ ... ]}`
ck('A1c calls 前缀 913,238 B（结尾是 calls 对象的 }）', len(calls_txt) == 913238, len(calls_txt))
ck('A1d 余段 16,711,117 B，以 `, "bounds": [` 开头、`]}` 结尾',
   len(rest_txt) == 16711117 and rest_txt.startswith(b', "bounds": ')
   and rest_txt.endswith(b']}'), (len(rest_txt), rest_txt[:14]))
ck('A1e 长度闭合 913,238 + 16,711,117 = 17,624,355',
   len(calls_txt) + len(rest_txt) == len(raw_a2), (len(calls_txt), len(rest_txt)))

ARR_HEAD = b', "bounds": ['
arr_txt = rest_txt[len(ARR_HEAD):]                   # `"00401000", ... ]}`

# ---------------------------------------------------------------- 1 · 解析
print('== 1 · 解析两段 ==')
obj = json.loads(calls_txt.decode('utf-8') + '}')
ck('B0 前缀补一个 } 能独立解析成单键 calls', list(obj.keys()) == ['calls'], list(obj.keys()))
calls = obj['calls']
btxt = arr_txt.rstrip()
ck('B0b bounds 数组段以 ]} 收尾', btxt.endswith(b']}'), btxt[-6:])
bounds = [int(x.strip().strip(b'"'), 16) for x in btxt[:-2].split(b',')]
ck('B0c calls 键 6,728 / 对 68,253', len(calls) == 6728
   and sum(len(v) for v in calls.values()) == 68253,
   (len(calls), sum(len(v) for v in calls.values())))
ck('B0d bounds 1,392,592 条 / 无重复', len(bounds) == 1392592 and len(set(bounds)) == 1392592,
   len(bounds))

# ---------------------------------------------------------------- 2 · skipdata 扫描（整段一次）
print('== 2 · capstone skipdata=True（VirtualSize blob，整段一次） ==')
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True
starts = array.array('I')
recon = {}          # 目标 → [站点...]（扫描序）
n_call_all = 0
n_imm = 0
blocks = []         # skip 块 (start,size)，只留 "被 call 站点落在内部" 所需的那些
COVER = 0x74836A
COVER_HEX = '0074836A'
cover = None
prev = None
for a, sz, mn, op in md.disasm_lite(VS_BLOB, TEXT_VA):
    starts.append(a)
    if mn == 'call':
        n_call_all += 1
        if op.startswith('0x'):
            n_imm += 1
            recon.setdefault('%08X' % int(op, 16), []).append('%08X' % a)
    if prev is not None and prev[0] <= COVER < prev[0] + prev[1]:
        cover = prev
    prev = (a, sz)
print('  starts=%d ; call 指令 %d（立即数 %d）; 目标 %d'
      % (len(starts), n_call_all, n_imm, len(recon)))

# ---------------------------------------------------------------- 3 · H1 bounds 逐位
print('== 3 · H1 bounds 逐位 ==')
ck('C1 bounds 逐位 == skipdata 起点序列（条数、顺序、值全同）',
   len(starts) == len(bounds) and all(a == b for a, b in zip(starts, bounds)),
   (len(starts), len(bounds)))
ck('C1b 末尾 0x7E038C < 尾界 0x7E038D；起点集 >= 尾界 0 条',
   bounds[-1] == 0x7E038C and sum(1 for x in starts if x >= VS_END) == 0, hex(bounds[-1]))
md2 = Cs(CS_ARCH_X86, CS_MODE_32)
md2.skipdata = True
RAW_BLOB = data[t.PointerToRawData:t.PointerToRawData + TEXT_RSZ]
n_raw = sum(1 for _ in md2.disasm_lite(RAW_BLOB, TEXT_VA))
ck('C1c 反控：raw blob（SizeOfRawData）起点 %d = bounds + %d'
   % (n_raw, n_raw - len(bounds)), n_raw == 1394186 and n_raw - len(bounds) == 1594)
# R164 自错 S-498：上一版只钉了计数，「多出的 1,594 条全在尾填充区」只写在注释里（审计员 #383 第 3 条）。
# 这里把区间直接断言出来，且对「尾填充区全 0x00」也钉一条 —— 后者才是 1,594 这个数的来由。
md3 = Cs(CS_ARCH_X86, CS_MODE_32)
md3.skipdata = True
raw_starts = [a for a, *_ in md3.disasm_lite(RAW_BLOB, TEXT_VA)]
# ★ R164 自错 S-500：首版写成 `a not in set(starts)` —— set 在生成器里**每轮重建**
#   （1,394,186 × 1,392,592），与 R162 的 S-475 同族。改为先建一次再用。
STARTSET = set(starts)
extra = [a for a in raw_starts if a not in STARTSET]
ck('C1d 多出的 %d 条全部落在 [VS 尾界 0x7E038D, raw 尾界 0x7E1000)' % len(extra),
   len(extra) == 1594 and all(VS_END <= a < TEXT_VA + TEXT_RSZ for a in extra),
   (len(extra), hex(min(extra)), hex(max(extra))))
ck('C1e 多出的条里 < VS 尾界的有 0 条', sum(1 for a in extra if a < VS_END) == 0)
ck('C1f 该区间 3,187 B 全 0x00 ⇒ skipdata 逐字节跳过，2 B × 1,593 + 1 B × 1 = 1,594',
   data[t.PointerToRawData + (VS_END - TEXT_VA):t.PointerToRawData + (TEXT_VA + TEXT_RSZ - TEXT_VA)]
   == b'\x00' * 3187 and 1593 * 2 + 1 == 3187, 3187)
b2 = list(bounds)
b2[0] += 4
ck('C1d 反控：bounds[0] 改 +4 ⇒ 逐位相等必失败',
   not (len(starts) == len(b2) and all(a == b for a, b in zip(starts, b2))))

# ---------------------------------------------------------------- 4 · H2 calls 逐键逐值（含顺序）
print('== 4 · H2 calls 逐键逐值（含键顺序与键内顺序） ==')
ck('D1 目标键集合相等', set(recon) == set(calls), (len(recon), len(calls)))
ck('D1b **键顺序**相等（= 目标首次出现顺序，非字典序、非排序）',
   list(recon.keys()) == list(calls.keys()),
   (list(recon.keys())[:3], list(calls.keys())[:3]))
ck('D1c **键内站点顺序**相等（= 扫描顺序，非排序）',
   all(recon[k] == calls[k] for k in recon),
   [k for k in recon if recon[k] != calls[k]][:3])
ck('D1d 对数 68,253 相等', sum(len(v) for v in recon.values()) == 68253,
   sum(len(v) for v in recon.values()))
ck('D1e 反控：把 call 的寄存器/内存操作数也算进来 ⇒ 94,786 != 68,253',
   n_call_all == 94786 and n_call_all != 68253, n_call_all)
ck('D1f 反控：键顺序确实不是字典序（前 3 键 %s）' % list(calls.keys())[:3],
   list(calls.keys())[:3] != sorted(calls)[:3], list(calls.keys())[:3])
# R164 自错 S-499：上一版本行写成 `... or True`（恒真，审计员 #383 第 1 条）。
# 换成两条有分辨力的反控：排序后的键序与文件序必不相同；按「最小站点升序」排也与文件序不同。
ks_file = list(calls)
ck('D1g 反控：把键排序后的序列与文件序**必不相同**（否则 D1b 无分辨力）',
   sorted(ks_file) != ks_file, (sorted(ks_file)[:3], ks_file[:3]))
by_min = sorted(ks_file, key=lambda k: int(calls[k][0], 16))
# 实测结果**必须如实写**：文件序与「按键内首个站点升序」排出来的序列**恰好相同**
# —— 因为扫描本身单调推进，目标的首次出现与其首个站点同时单调。故这两种口径
# **本镜像上不可分辨**；可分辨的只有「非字典序」（D1g）与「== 扫描首次出现序」（D1b）。
ck('D1h 文件序 == 「按键内首个站点升序」排序（两口径本镜像不可分辨，如实记）',
   by_min == ks_file, (by_min[:3], ks_file[:3]))
c3 = dict((k, list(v)) for k, v in calls.items())
c3.setdefault('00401000', []).append('00401000')
ck('D2 反控：注入一对伪造 ⇒ 键集合/键内序列必不相等',
   set(c3) != set(recon) or any(c3[k] != recon.get(k) for k in set(c3) & set(recon)))

# ---------------------------------------------------------------- 5 · H3 序列化逐字节
print('== 5 · H3 序列化逐字节 ==')
ser = json.dumps({'calls': calls}, ensure_ascii=False).encode('utf-8')
ck('E1 json.dumps 默认分隔符 + dict 插入序 ⇒ 逐字节复现 calls 前缀（差 1 个外层 }）',
   ser[:-1] == calls_txt, (len(ser), len(calls_txt)))
ser_arr = (', '.join('"%08X"' % v for v in bounds) + ']}').encode('utf-8')
ck('E1b bounds 数组段逐字节复现（%d B）' % len(ser_arr), ser_arr == arr_txt,
   (len(ser_arr), len(arr_txt)))
ck('E1c 数组段 = 12 B × 1,392,592（`"XXXXXXXX", ` 形态）⇒ 16,711,104 B',
   len(arr_txt) == 12 * 1392592 and len(arr_txt) == 16711104, len(arr_txt))
ck('E1d 全长闭合：913,238（calls 前缀）+ 13（`, "bounds": [`）+ 16,711,104（数组段）= 17,624,355',
   len(calls_txt) + len(ARR_HEAD) + len(arr_txt) == len(raw_a2),
   (len(calls_txt), len(ARR_HEAD), len(arr_txt)))

# ---------------------------------------------------------------- 6 · H4 R95 漏条机制
print('== 6 · H4 R95 §6 漏条机制 ==')


def at(va, n):
    o = t.PointerToRawData + (va - TEXT_VA)
    return data[o:o + n]


byt = at(COVER, 5)
tgt = (COVER + 5 + int.from_bytes(byt[1:5], 'little', signed=True)) & 0xFFFFFFFF
ck('F1 站点 0074836A 首字节 E8（确是直接调用）', byt[0] == 0xE8, byt.hex())
ck('F2 rel32 目标 == 007C8B3D', tgt == 0x7C8B3D, '%08X' % tgt)
ck('F3 该站点不在 skipdata 起点集里（在的话规则就会产出它）', COVER not in STARTSET)
ck('F4 它落在一条 skip 块内部：起点 %s 长度 %d 位移 %d'
   % (('%08X' % cover[0]) if cover else '?', cover[1] if cover else -1,
      (COVER - cover[0]) if cover else -1),
   cover is not None and cover[0] < COVER < cover[0] + cover[1], cover)
ck('F5 a2_sites 的 007C8B3D 键存在（4,498 站点），但不含 0074836A',
   '007C8B3D' in calls and '0074836A' not in calls['007C8B3D'],
   len(calls.get('007C8B3D', [])))
cg = json.load(open(CG, encoding='utf-8'))
cg_pair = [e for v in cg.values() for e in v if e.get('src') == 0x748360 and e.get('site') == COVER]
ck('F6 callgraph.json 里有一条 site=0074836A 的条目（其 src=00748360 是**调用者**、不是目标）'
   ' ⇒ 该站点在那份扫描里是被当作指令的',
   len(cg_pair) >= 1, cg_pair[:2])
# R164 自错 S-501：上一版本行是 ck(..., True, 'mechanism') —— 硬编码 PASS、无测量（审计员 #383 第 4 条）。
# 改成量化两产物的**全量**差集：不是只差这 1 对，而是 a2 独有 10,677 对 / cg 独有 1 对。
# 且 cg 的 `src` 是**调用者**、顶层键（十进制字符串）才是目标 —— F6 用 src 去比是本轮第三处口径错。
CG_PAIRS = set()
for k, v in cg.items():
    for e in v:
        CG_PAIRS.add(('%08X' % int(k), '%08X' % e['site']))
A2_PAIRS = set((t, s) for t, v in calls.items() for s in v)
ck('F7 反控：callgraph.json 顶层键是**目标**（不是 src）⇒ 该对写作 (007C8B3D, 0074836A)',
   ('007C8B3D', COVER_HEX) in CG_PAIRS and ('007C8B3D', COVER_HEX) not in A2_PAIRS,
   sorted(CG_PAIRS - A2_PAIRS)[:2])
ck('F8 两产物全量差集：a2 68,253 对 / cg 57,577 对 / 交集 57,576 / a2 独有 10,677 / cg 独有 1',
   len(A2_PAIRS) == 68253 and len(CG_PAIRS) == 57577
   and len(A2_PAIRS & CG_PAIRS) == 57576
   and len(A2_PAIRS - CG_PAIRS) == 10677 and len(CG_PAIRS - A2_PAIRS) == 1,
   (len(A2_PAIRS), len(CG_PAIRS), len(A2_PAIRS & CG_PAIRS),
    len(A2_PAIRS - CG_PAIRS), len(CG_PAIRS - A2_PAIRS)))
ck('F9 a2 独有的 10,677 对站点全在 skipdata 起点集内（= 本件多扫出的数据区调用）',
   all(int(s_, 16) in STARTSET for _, s_ in (A2_PAIRS - CG_PAIRS)),
   sum(1 for _, s_ in (A2_PAIRS - CG_PAIRS) if int(s_, 16) not in STARTSET))
ck('F10 ⇒ 差异不是「只差跳过策略」一句话能盖住：15.6% 的对数缺口必须一起报',
   round(100.0 * len(A2_PAIRS - CG_PAIRS) / len(A2_PAIRS), 2) == 15.64,
   round(100.0 * len(A2_PAIRS - CG_PAIRS) / len(A2_PAIRS), 2))

# ---------------------------------------------------------------- 7 · 环绕 / 非起点目标
print('== 7 · 环绕调用与「目标不是指令起点」 ==')
TEXT_RAW_END = TEXT_VA + TEXT_RSZ
outside = [(k, s) for k, v in calls.items() for s in v if not (TEXT_VA <= int(k, 16) < TEXT_RAW_END)]
ck('G1 目标落在 .text 之外的调用恰 9 对（32 位环绕调用被计入、未被过滤）',
   len(outside) == 9, len(outside))
R95_9 = ['00409FF2', '0052EB58', '0052EBC1', '005A0074', '006DFE39', '0070E915', '00783B68',
         '007CA1D8', '007DCBC8']
ck('G1b 这 9 对的站点集合逐一等于 R95 §5.2 的 9 条站点',
   sorted(s for _, s in outside) == sorted(R95_9), sorted(s for _, s in outside)[:3])
ok = 0
for k, s in outside:
    S = int(s, 16)
    bb = at(S, 5)
    if bb[0] == 0xE8 and (S + 5 + int.from_bytes(bb[1:5], 'little', signed=True)) & 0xFFFFFFFF == int(k, 16):
        ok += 1
ck('G1c 9 对全部按 mod 2^32 字节算术闭合', ok == 9, ok)
sstarts = set(starts)
nstart = [(k, s) for k, v in calls.items() for s in v if int(k, 16) not in sstarts]
ck('G2 目标不是指令起点的对 = %d 对（skipdata 自己的产物：环绕目标 + 数据块内目标）'
   % len(nstart), len(nstart) == 110, len(nstart))

# ---------------------------------------------------------------- 落盘
print('\n== 结果 ==')
print('FAIL = %d ; 断言 %d' % (FAIL, len(RES)))
json.dump({'round': 'R164', 'script': 'r164a_a2_rule.py', 'fail': FAIL, 'asserts': RES,
           'facts': {'a2_bytes': len(raw_a2),
                     'a2_sha256': hashlib.sha256(raw_a2).hexdigest(),
                     'calls_keys': len(calls),
                     'calls_pairs': sum(len(v) for v in calls.values()),
                     'bounds': len(bounds), 'skipdata_vs_starts': len(starts),
                     'skipdata_raw_starts': n_raw, 'call_insns_all': n_call_all,
                     'call_insns_imm': n_imm, 'calls_prefix_bytes': len(calls_txt),
                     'bounds_array_bytes': len(arr_txt),
                     'targets_outside_text': len(outside),
                     'targets_not_start': len(nstart)}},
          io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('wrote', OUT)
sys.exit(1 if FAIL else 0)
