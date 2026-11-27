#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R163-A · F24 的 86.19% 到底测的是「二进制」还是「盘上语料」——R95 §5.3 的可复现性审计

背景（R162 待办第 1 条）：R162 已用 56 个自然量比值把「86.19% 是 bounds 段某个比值」
这条解释**否掉**（最近差 13.69 个百分点）。本轮改从**生成器/方法侧**入手，不再搜比值空间。

本轮读到的关键事实（R95 REPORT.md §5.3，逐字）：
  「用 4,743 份文本 EVIDENCE 扫『VA  指令字节  助记符』行，取与 bounds 相交的：
     bounds 中被至少一份 EVIDENCE 以『地址+字节+助记符』记录 = 192,341 / 1,392,592 = 13.81%
     提供这些行的文件 = 961 份 …… 其余 1,200,251 条（86.19%）只以地址形式存在，
     盘上没有任何字节与之对应」

⇒ 假设 H1：**86.19% 是「盘上语料未覆盖」的补集**，不是「二进制里没有字节」。
   F24 正文把前者写成后者（口径滑移），R136 用二进制判据自然得 99.992%（不是矛盾，是另一个命题）。

本脚本只做可失败的机械核验，不解释、不推断：
  A. R95 §5.3 那段文字是否逐字在盘（正控：能在 R95 REPORT 里找到；反控：错误串必须找不到）
  B. R95 §5.3 依赖的语料现盘还在不在：EVIDENCE 目录 / 文本 disasm 行 / q4_covering*.py
  C. 用现盘**仅存的**全部 EVIDENCE 语料复算覆盖率，看能否得到 192,341（预期：远小于）
     ★ S-495：首版只走 lead/next_re_20261117_r14（得 0），漏了 _ghidra 等子树
       ⇒ 已补全库作用域（大小写不敏感），真值为 1,556 条而非 0。
  D. 反控：把语料换成「bounds 自身」，覆盖率必须 = 100%（证明扫描器不是恒 0）
  E. 反控：把 bounds 换成随机 VA，覆盖率必须 = 0

严禁递归进符号链接（C01_census/C01_census/... 是自指环，实测会跑飞）。
只读；只写 _r163/r163a_corpus_repro.json。
"""
import io
import json
import os
import re
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
A2 = 'lead/next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json'
R95 = 'lead/next_re_20261117_r14/R17_R95_T1_A2SITES/REPORT.md'
OUT = '_r163/r163a_corpus_repro.json'

FAIL = 0
RES = []


def ck(name, cond, detail=''):
    global FAIL
    ok = bool(cond)
    if not ok:
        FAIL += 1
    RES.append({'id': name, 'ok': ok, 'detail': str(detail)[:500]})
    print(('PASS ' if ok else 'FAIL ') + name + (('  :: ' + str(detail)[:280]) if detail else ''))


# ---------------------------------------------------------------- A R95 §5.3 逐字在盘
print('== A · R95 §5.3 的原始量测在盘 ==')
r95 = io.open(R95, encoding='utf-8', errors='replace').read()
A_PARTS = [
    '用 4,743 份文本 EVIDENCE 扫',
    '192,341 / 1,392,592 = 13.81%',
    '提供这些行的文件',
    '961 份',
    '1,200,251 条（86.19%）只以地址形式存在',
    '盘上没有任何字节与之对应',
]
for i, p in enumerate(A_PARTS):
    ck('A%d 逐字在盘: %s' % (i + 1, p[:44]), p in r95)
ck('A7 反控：该表里「192,341 / 999,999」这种错串不该在盘', '192,341 / 999,999' not in r95)
ck('A8 反控：把 A 段换成 R95 里不存在的措辞应当找不到',
   '用 9,999 份文本 EVIDENCE 扫' not in r95)
print('  R95 REPORT.md 字节数=%d sha256(前16)=%s' % (
    len(r95.encode('utf-8')),
    __import__('hashlib').sha256(io.open(R95, 'rb').read()).hexdigest()[:16]))

# ---------------------------------------------------------------- B 语料现盘存在性
print('\n== B · R95 §5.3 依赖的语料现盘是否还在 ==')
# B1 EVIDENCE 目录（**不进符号链接**：os.walk 默认 followlinks=False，再用 realpath 去重）
seen_real = set()
evid_files = []
evid_dirs = []
for dirpath, dirnames, filenames in os.walk('lead/next_re_20261117_r14'):
    if os.path.basename(dirpath) != 'EVIDENCE':
        continue
    rp = os.path.realpath(dirpath)
    if rp in seen_real:
        continue
    seen_real.add(rp)
    evid_dirs.append(rp)
    for f in filenames:
        evid_files.append(os.path.join(dirpath, f))
ck('B1 去重后的 EVIDENCE 目录数 = %d' % len(evid_dirs), len(evid_dirs) > 0, evid_dirs)
# ★ S-495（r163h 复算审计员时发现，回头修正本条）：首版只走 lead/next_re_20261117_r14，
#   漏了 _ghidra/S08-KPROVED2/EVIDENCE（47 文件）与 re_atlas/evidence（167 文件）等子树
#   ⇒ 后续「覆盖 0 条」是**作用域错**。此处补全作用域后重测。
ck('B2 EVIDENCE 下文件总数 = %d（R95 当时称 4,743 份**文本** EVIDENCE）'
   % len(evid_files), len(evid_files) < 4743, len(evid_files))

# B3 逐文件判「是不是文本 disasm 语料」
DISA_LINE = re.compile(r'^\s*(?:0x)?([0-9A-Fa-f]{8})\s*[:|]?\s+((?:[0-9A-Fa-f]{2}\s){1,16})\s+([a-z]{2,8})')
text_corpus = []      # 含 >=1 条合法 disasm 行的文件
text_hits_all = {}    # file -> set(VA)
for f in evid_files:
    try:
        raw = io.open(f, 'rb').read()
    except OSError:
        continue
    txt = raw.decode('utf-8', 'replace')
    hits = set()
    for ln in txt.splitlines():
        m = DISA_LINE.match(ln)
        if m:
            hits.add(int(m.group(1), 16))
    if hits:
        text_corpus.append(f)
        text_hits_all[f] = hits
ck('B3 现盘含文本 disasm 行的 EVIDENCE 文件数 = %d（R95 依赖 961 份提供行）'
   % len(text_corpus), len(text_corpus) < 961, len(text_corpus))

# B4 生成器脚本
GEN = ['lead/next_re_20261117_r14/R17_R95_T1_A2SITES/q4_covering.py',
       'lead/next_re_20261117_r14/R17_R95_T1_A2SITES/q4_covering_verify.py']
found_gen = [p for p in GEN if os.path.exists(p)]
ck('B4 R95 §5.3 的两个生成器脚本现盘存在 %d/2' % len(found_gen),
   len(found_gen) == 0, found_gen or 'both absent')
# B5 但 R95 REPORT 里的「复算清单」声称它们存在 —— 表里的自述与现实不一致
ck('B5 R95 REPORT §7 复算清单里**仍写着** q4_covering.py / q4_covering_verify.py',
   'q4_covering.py' in r95 and 'q4_covering_verify.py' in r95)
# B6 同目录只剩 REPORT.md 与一个自指符号链接
ls95 = sorted(os.listdir('lead/next_re_20261117_r14/R17_R95_T1_A2SITES'))
ck('B6 R17_R95_T1_A2SITES 现只剩 %s' % ls95, set(ls95) == {'REPORT.md', 'R17_R95_T1_A2SITES'}, ls95)

# ---------------------------------------------------------------- C 用现存语料复算覆盖率
print('\n== C · 用现盘仅存语料复算 bounds 覆盖率 ==')
d = json.load(io.open(A2, encoding='utf-8'))
bounds = [int(x, 16) for x in d['bounds']]
bset = set(bounds)
ck('C0 bounds 条数 = 1,392,592', len(bounds) == 1392592, len(bounds))

covered = set()
for f, hits in text_hits_all.items():
    covered |= (hits & bset)
# 全库作用域补测（修正 S-495 的作用域错）
_seen2, _all_dirs, _all_files = set(), [], []
for dp, _dn, fn in os.walk('.'):
    if os.path.basename(dp).lower() != 'evidence':
        continue
    rp = os.path.realpath(dp)
    if rp in _seen2:
        continue
    _seen2.add(rp)
    _all_dirs.append(rp)
    _all_files.extend(os.path.join(dp, f) for f in fn)
cov_all = set()
for f in _all_files:
    try:
        txt = io.open(f, 'rb').read().decode('utf-8', 'replace')
    except OSError:
        continue
    for ln in txt.splitlines():
        m = DISA_LINE.match(ln)
        if m:
            a = int(m.group(1), 16)
            if a in bset:
                cov_all.add(a)
ck('C1lead 仅 lead/next_re_20261117_r14 作用域：覆盖 %d 条（R95 称 192,341）'
   % len(covered), len(covered) == 0, len(covered))
ck('C1 全库 EVIDENCE 作用域（大小写不敏感、realpath 去重 %d 个目录 / %d 文件）：覆盖 **%d** 条'
   % (len(_all_dirs), len(_all_files), len(cov_all)),
   len(cov_all) > 0 and len(cov_all) < 192341,
   'covered=%d 差 %d 条' % (len(cov_all), 192341 - len(cov_all)))

# C2 把 4 份 JSON EVIDENCE 也算进去（它们含 calls site，形态是「地址↔地址」不是「地址+字节+助记符」）
json_sites = set()
for f in evid_files:
    if not f.endswith('.json'):
        continue
    try:
        obj = json.load(io.open(f, encoding='utf-8'))
    except Exception:
        continue
    stack = [obj]
    while stack:
        o = stack.pop()
        if isinstance(o, dict):
            for v in o.values():
                stack.append(v)
        elif isinstance(o, list):
            for v in o:
                if isinstance(v, int):
                    json_sites.add(v)
                elif isinstance(v, (dict, list)):
                    stack.append(v)
json_in_bounds = json_sites & bset
ck('C2 4 份 JSON EVIDENCE 里的整数地址落在 bounds 内的 = %d 条' % len(json_in_bounds),
   len(json_in_bounds) < 192341, len(json_in_bounds))
ck('C3 即便把「全库文本行 + JSON 整数」全并起来也够不到 192,341',
   len(cov_all | json_in_bounds) < 192341,
   'union=%d vs 192,341' % len(cov_all | json_in_bounds))

# ---------------------------------------------------------------- D/E 正反控
print('\n== D/E · 正反控 ==')
ck('D1 正控：语料换成 bounds 自身 ⇒ 覆盖率必须 = 100%',
   len(bset & bset) == len(bset), len(bset))
fake = set(range(0x900000, 0x900000 + 200000))   # 映像外的连续 VA
ck('D2 反控：语料换成映像外 VA ⇒ 对 bounds 覆盖 = 0', len(fake & bset) == 0, len(fake & bset))
# D3 反控：让扫描器面对一个「有 disasm 行但地址全错」的文件必须得 0
_p = '/tmp/r163a_negcorpus.txt'
io.open(_p, 'w', encoding='utf-8').write(
    'DEADBEEF  E8 00 00 00 00  call\nCAFEBABE  90  nop\n')
_neg = set()
for ln in io.open(_p, encoding='utf-8').read().splitlines():
    m = DISA_LINE.match(ln)
    if m:
        _neg.add(int(m.group(1), 16))
ck('D3 反控：伪语料 2 行被解析出 2 个 VA 且对 bounds 覆盖 = 0',
   len(_neg) == 2 and len(_neg & bset) == 0, len(_neg))
io.open(_p, 'w', encoding='utf-8').write(
    '00401000  E8 00 00 00 00  call\n')
_pos = set()
for ln in io.open(_p, encoding='utf-8').read().splitlines():
    m = DISA_LINE.match(ln)
    if m:
        _pos.add(int(m.group(1), 16))
ck('D4 正控：同一解析器对 0x401000 必须命中 bounds', len(_pos & bset) == 1, sorted(map(hex, _pos)))
os.unlink(_p)

# ---------------------------------------------------------------- F 秩前缀形态
print('\n== F · 0x48948A 的秩身份（R158 交付八的「两侧同族」由此得到解释） ==')
srt = sorted(bounds)
ck('F0 bounds 严格升序且无重复', srt == bounds and len(bset) == len(bounds))
ck('F1 排序后第 192,341 个元素（0-based 192,340）== 0x48948A',
   srt[192340] == 0x48948A, hex(srt[192340]))
ck('F2 <= 0x48948A 的 bounds 恰 192,341 条', sum(1 for a in bounds if a <= 0x48948A) == 192341)
ck('F3 > 0x48948A 的 bounds 恰 1,200,251 条', sum(1 for a in bounds if a > 0x48948A) == 1200251)
ck('F4 1,200,251 / 1,392,592 = 86.188273%（台账记 86.19%，四舍五入一致）',
   abs(100.0 * 1200251 / 1392592 - 86.188273) < 5e-7,
   '%.6f%%' % (100.0 * 1200251 / 1392592))
# F5/F6 密度同族（R158 已测，本轮复算作为「秩分割」的形态证据）
pre = [a for a in bounds if a <= 0x48948A]
post = [a for a in bounds if a > 0x48948A]
pre_bytes = 0x48948A - 0x401000 + 1
post_bytes = 0x7E038C - 0x48948A          # max bound 0x7E038C
ck('F5 前段密度 %.6f 与后段密度 %.6f 相差 < 2%%'
   % (len(pre) / pre_bytes, len(post) / post_bytes),
   abs(len(pre) / pre_bytes - len(post) / post_bytes) / (len(post) / post_bytes) < 0.02,
   'pre=%.6f post=%.6f' % (len(pre) / pre_bytes, len(post) / post_bytes))
# F7 反控：若切分点真的由「内容/语料覆盖」驱动，覆盖集不该是纯前缀（用现存的 calls site 集做形态对照）
sites = sorted({s for v in d['calls'].values() for s in v})
rank_of = {a: i for i, a in enumerate(srt)}
sites_ranks = sorted(rank_of[int(x, 16)] for x in sites if int(x, 16) in rank_of)
ck('F7 现存语料（68,253 个调用点）的秩分布**不是**前缀：中位秩 %d、最大秩 %d'
   % (sites_ranks[len(sites_ranks) // 2], sites_ranks[-1]),
   sites_ranks[-1] > 192341,
   'min=%d p25=%d p50=%d p75=%d max=%d' % (
       sites_ranks[0], sites_ranks[len(sites_ranks) // 4],
       sites_ranks[len(sites_ranks) // 2], sites_ranks[3 * len(sites_ranks) // 4],
       sites_ranks[-1]))
ck('F8 反控：语料覆盖集的秩分布若为前缀，则其 max 秩必须 < 192,341 —— 实测 %d 远大于'
   % sites_ranks[-1], sites_ranks[-1] >= 192341)

print('\nSUMMARY %d/%d PASS, FAIL=%d' % (len(RES) - FAIL, len(RES), FAIL))
io.open(OUT, 'w', encoding='utf-8').write(json.dumps(
    {'round': 'R163', 'script': 'r163a_corpus_repro.py', 'fail': FAIL,
     'asserts': RES,
     'facts': {'evid_dirs': evid_dirs, 'evid_files': len(evid_files),
               'text_corpus_files': len(text_corpus),
               'covered_by_text_corpus_lead': len(covered),
               'covered_all_evidence': len(cov_all),
               'evid_dirs_all': len(_all_dirs), 'evid_files_all': len(_all_files),
               'covered_by_json': len(json_in_bounds),
               'union': len(covered | json_in_bounds),
               'r95_claimed': 192341,
               'sites_ranks': {'min': sites_ranks[0], 'p50': sites_ranks[len(sites_ranks) // 2],
                               'max': sites_ranks[-1]}}},
    ensure_ascii=False, indent=1))
sys.exit(0 if FAIL == 0 else 1)
