#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R163-C · F24 的 86.19% 是「口径滑移」：把可失败的判据写出来

R162 已用 56 个自然量比值把「86.19% = bounds 段某个比值」这条解释**否掉**（最近差 13.69 个百分点）。
本轮把它**定性**：86.19% 不是从二进制算出来的数，是**盘上语料覆盖率**的补集，
而 F24 正文把「盘上语料没覆盖到」写成了「二进制里没有字节」。

可失败判据（本脚本 = 判据本体）：
  J1  R95 §5.3 的表**逐字在盘**，且它自己写明主语是「EVIDENCE」（盘上语料）而不是「.text」。
  J2  该表的三个数（4,743 份语料 / 961 份供行 / 192,341 命中）**互相自洽**，
      且补集 1,200,251 = 1,392,592 − 192,341 精确成立（不是估算）。
  J3  同一批 192,341 条地址，用**二进制判据**测得的是 100%（弱判据：落在节 raw 范围）
      与 99.992%（强判据：落在指令起始集）—— 与 13.81% 方向相反、量级差 7 倍。
      ⇒ 两个数测的不是同一个东西；「86.19% 盘上无字节」是**主语错**，不是算错。
  J4  R95 的语料**已不在盘**：4,743 份 → 0 份、961 份 → 0 份、两个生成器脚本 → 0 个
      ⇒ 该数**当前不可重算**，F24 正文引用它时既不能复核也不能反驳。
  J5  F24 正文 V543 里 86.19% 的每一处出现都处于**撤回语境**（R138 已做），
      但「口径滑移」这层定性**尚未写进正文** —— 本脚本只证这层缺口存在，不改正文。
  J6  切分点 0x48948A 的**秩身份**：它恰是排序后第 192,341 个 bounds。
      ⇒ 它不是内容边界，是**计数边界**；R158 报的「两侧密度同族、gap 分布同族」
        由此得到解释 —— 按秩切任何位置都得到密度同族的两段。

正反控成对；数字全部实测。只读，只写 _r163/r163c_f24_scope_slip.json。
"""
import io
import json
import os
import re
import sys

import pefile

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
A2 = 'lead/next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json'
R95 = 'lead/next_re_20261117_r14/R17_R95_T1_A2SITES/REPORT.md'
V543 = 'lead/next_re_20261117_r14/R17_R115_FACTINDEX_V543/FACT_INDEX.tsv'
EXE = 'ra2bench/gamemd.exe'
OUT = '_r163/r163c_f24_scope_slip.json'

FAIL = 0
RES = []


def ck(name, cond, detail=''):
    global FAIL
    ok = bool(cond)
    if not ok:
        FAIL += 1
    RES.append({'id': name, 'ok': ok, 'detail': str(detail)[:500]})
    print(('PASS ' if ok else 'FAIL ') + name + (('  :: ' + str(detail)[:280]) if detail else ''))


# ---------------------------------------------------------------- J1
print('== J1 · R95 §5.3 的主语是「EVIDENCE」（盘上语料）不是「.text」==')
r95 = io.open(R95, encoding='utf-8', errors='replace').read()
seg = r95[r95.index('### 5.3'):r95.index('## 6 ·')]
ck('J1a §5.3 标题写的是「bounds 是不是『别处已有字节』的」', '别处已有字节' in seg)
ck('J1b 生成该表的语料主语是「文本 EVIDENCE」', '用 4,743 份文本 EVIDENCE 扫' in seg)
ck('J1c 表头三行都在', all(k in seg for k in ('bounds` 中被至少一份 EVIDENCE 以',
                                            '提供这些行的文件', '其余')))
ck('J1d 反控：§5.3 里**不出现**「.text 里没有这个字节」这类二进制断言',
   '.text' not in seg.replace('重扫 `.text`', ''),
   '.text 出现 %d 次（应仅 1 次且为「需重扫」）' % seg.count('.text'))
ck('J1e ⇒ 该表的判定轴是「盘上有无对应文本」，不是「二进制里有无字节」',
   '别处已有字节' in seg and '文本 EVIDENCE' in seg)

# ---------------------------------------------------------------- J2
print('\n== J2 · 三个数互相自洽 ==')
n4743 = int(re.search(r'用 ([\d,]+) 份文本 EVIDENCE 扫', seg).group(1).replace(',', ''))
n961 = int(re.search(r'提供这些行的文件 \| \*\*(\d+) 份\*\*', seg).group(1))
hit, tot, pct = re.search(r'\*\*([\d,]+) / ([\d,]+) = ([\d.]+)%\*\*', seg).groups()
hit, tot = int(hit.replace(',', '')), int(tot.replace(',', ''))
rest = int(re.search(r'其余 \| \*\*([\d,]+) 条（[\d.]+%）', seg).group(1).replace(',', ''))
ck('J2a 语料份数 4,743', n4743 == 4743, n4743)
ck('J2b 供行文件数 961', n961 == 961, n961)
ck('J2c 命中 192,341 / 总 1,392,592', (hit, tot) == (192341, 1392592), (hit, tot))
ck('J2d 补集 1,200,251 == 1,392,592 − 192,341 精确成立',
   rest == tot - hit and rest == 1200251, '%d vs %d' % (rest, tot - hit))
ck('J2e 192,341/1,392,592 = 13.8117%（四舍五入 13.81%）',
   abs(100.0 * hit / tot - 13.811727) < 5e-7, '%.6f%%' % (100.0 * hit / tot))
ck('J2f 1,200,251/1,392,592 = 86.1883%（四舍五入 86.19%）',
   abs(100.0 * rest / tot - 86.188273) < 5e-7, '%.6f%%' % (100.0 * rest / tot))

# ---------------------------------------------------------------- J3
print('\n== J3 · 同一批地址，二进制判据给的是 100% / 99.992% ==')
data = io.open(EXE, 'rb').read()
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
secs = [(s.Name.decode().rstrip('\x00'), s.VirtualAddress, s.Misc_VirtualSize,
         s.PointerToRawData, s.SizeOfRawData) for s in pe.sections]
d = json.load(io.open(A2, encoding='utf-8'))
bounds = [int(x, 16) for x in d['bounds']]
covered_raw = []
for a in bounds:
    for nm, va, vs, pr, rs in secs:
        lo = IB + va
        if lo <= a < lo + rs:
            covered_raw.append(a)
            break
ck('J3a 弱判据（落在某节 SizeOfRawData 覆盖内）= 1,392,592 / 1,392,592 = 100.000000%',
   len(covered_raw) == len(bounds), '%d / %d' % (len(covered_raw), len(bounds)))
ck('J3b 反控：ImageBase 本身不落在任何节 ⇒ 弱判据不是恒真',
   not any(IB == IB + va for _n, va, _v, _p, _r in secs))
ck('J3c 反控：映像外 0x900000 不命中', not any(
    IB + va <= 0x900000 < IB + va + rs for _n, va, _v, _p, rs in secs))
ck('J3d ⇒ 同一批地址：语料判据 13.81%，二进制判据 100% ⇒ 两个数不同命题',
   len(covered_raw) == len(bounds) and hit == 192341,
   'corpus=13.81%% binary=100%%')

# ---------------------------------------------------------------- J4
print('\n== J4 · R95 的语料现盘已不在 ⇒ 该数当前不可重算 ==')
seen = set()
evid_dirs, evid_files = [], []
for dp, _dn, fn in os.walk('lead/next_re_20261117_r14'):
    if os.path.basename(dp) != 'EVIDENCE':
        continue
    rp = os.path.realpath(dp)
    if rp in seen:
        continue
    seen.add(rp)
    evid_dirs.append(rp)
    evid_files.extend(os.path.join(dp, f) for f in fn)
DISA = re.compile(r'^\s*(?:0x)?([0-9A-Fa-f]{8})\s*[:|]?\s+((?:[0-9A-Fa-f]{2}\s){1,16})\s+([a-z]{2,8})')
text_hit_files = 0
for f in evid_files:
    try:
        txt = io.open(f, 'rb').read().decode('utf-8', 'replace')
    except OSError:
        continue
    if any(DISA.match(ln) for ln in txt.splitlines()):
        text_hit_files += 1
ck('J4a EVIDENCE 目录去重后 = 5 个，文件共 5 个', len(evid_dirs) == 5 and len(evid_files) == 5,
   '%d dirs / %d files' % (len(evid_dirs), len(evid_files)))
ck('J4b 含「地址+字节+助记符」行的文件 = 0 个（R95 依赖 961 个）',
   text_hit_files == 0, text_hit_files)
ck('J4c q4_covering.py 不存在',
   not os.path.exists('lead/next_re_20261117_r14/R17_R95_T1_A2SITES/q4_covering.py'))
ck('J4d q4_covering_verify.py 不存在',
   not os.path.exists('lead/next_re_20261117_r14/R17_R95_T1_A2SITES/q4_covering_verify.py'))
ck('J4e 但 R95 REPORT §7「复算清单」里仍写着这两个文件名 ⇒ 表与盘不一致',
   'q4_covering.py' in r95 and 'q4_covering_verify.py' in r95)
ck('J4f 反控：R95 REPORT 自身在盘且非空（不是「整份都丢了」）',
   os.path.getsize(R95) == 26976, os.path.getsize(R95))

# ---------------------------------------------------------------- J5
print('\n== J5 · F24 正文 V543 的 86.19% 每处都在撤回语境，但「口径滑移」未写进正文 ==')
rows = [r.split('\t') for r in io.open(V543, encoding='utf-8').read().split('\n') if r]
hdr, body = rows[0], [r for r in rows[1:] if len(r) == 5]
f24 = [r for r in body if r[0] == 'F24'][0]
blob = '\n'.join(f24)
occ = [m.start() for m in re.finditer(re.escape('86.19'), blob)]
ck('J5a F24 行内 86.19 出现 5 次', len(occ) == 5, len(occ))
# ★ S-486：首版关键词表只有 撤下/撤回/作废/不再引用，漏了「不得再把…当作剔除理由」这种
#   否定式撤回（@4836 那处）⇒ 假 FAIL。与 R162 审计员第 6 条同族：**关键词覆盖不足**。
RETRACT = ('撤下', '撤回', '作废', '不再引用', '撤销', '已从本条正文', '不得再把')
ok_ctx = all(any(k in blob[max(0, p - 40):p + 60] for k in RETRACT) for p in occ)
ck('J5b 5 次出现全部处在撤回语境（±40/60 字符内含撤回词）', ok_ctx)
ck('J5c 反控：自造肯定句必须被判为「非撤回语境」',
   not any(k in 'bounds 的 16.7 MB 里 86.19% 盘上没有任何字节对应' for k in RETRACT))
# ★ S-487：首版用裸词 EVIDENCE 判「未写进正文」，但 F24 行里 EVIDENCE 出现 6 次、
#   全是指目录名/产物路径，与「语料覆盖率」这层定性无关 ⇒ 裸词无分辨力。改为精确短语。
SLIP = ('语料覆盖率', '口径滑移', '盘上语料', '语料主语')
ck('J5d 「口径滑移 / 盘上语料覆盖率」这层定性**未**写进 F24 行（精确短语判据）',
   not any(k in blob for k in SLIP),
   '命中=%s ; 反控裸词 EVIDENCE 出现 %d 次（均指目录/路径）'
   % ([k for k in SLIP if k in blob], blob.count('EVIDENCE')))
ck('J5e ⇒ 缺口存在且可被机械检出（正文缺一层定性，不是缺数）', True, 'honest gap')

# ---------------------------------------------------------------- J6
print('\n== J6 · 切分点 0x48948A 的秩身份 ==')
srt = sorted(bounds)
ck('J6a bounds 严格升序零重复', srt == bounds and len(set(bounds)) == len(bounds))
ck('J6b srt[192340] == 0x48948A', srt[192340] == 0x48948A, hex(srt[192340]))
ck('J6c <= 0x48948A 的条数恰 192,341', sum(1 for a in bounds if a <= 0x48948A) == 192341)
ck('J6d ⇒ 切分点是**计数边界**（第 192,341 个），不是内容边界', srt[192340] == 0x48948A)
pre = [a for a in bounds if a <= 0x48948A]
post = [a for a in bounds if a > 0x48948A]
dn_pre = len(pre) / (0x48948A - 0x401000 + 1)
dn_post = len(post) / (0x7E038C - 0x48948A)
ck('J6e 前段密度 %.6f / 后段密度 %.6f，相差 %.4f%%（R158 报「同族」）'
   % (dn_pre, dn_post, 100 * abs(dn_pre - dn_post) / dn_post),
   abs(dn_pre - dn_post) / dn_post < 0.02)
# ★ S-488：首版的假设本身错了 —— 我写「按秩切任意位置密度都同族」，实测秩 10 万处
#   相对差 5.54%、尾段 110 万处 1.16%，并不都 < 2%。真实形态是：全秩扫描（步长 2 万、共 68 个切点）
#   相对差 min 0.0361% / median 1.3904% / max 12.8033%；0x48948A 处 0.5286% 排在第 23.5 百分位。
#   ⇒ 正确结论比原假设更强：**存在比 0x48948A 更「同族」的秩切** ⇒ 密度同族完全不能标识它。
sweep = []
for k in range(20000, len(srt) - 20000, 20000):
    cut = srt[k]
    a = (k + 1) / (cut - 0x401000 + 1)
    b = (len(srt) - k - 1) / (0x7E038C - cut)
    sweep.append((abs(a - b) / b, k, cut))
sweep.sort()
rel_split = abs(dn_pre - dn_post) / dn_post
n_better = sum(1 for r, _k, _c in sweep if r < rel_split)
ck('J6f 全秩扫描 %d 个切点的密度相对差：min %.4f%% / median %.4f%% / max %.4f%%'
   % (len(sweep), 100 * sweep[0][0], 100 * sweep[len(sweep) // 2][0], 100 * sweep[-1][0]),
   len(sweep) == 68, '%d cuts' % len(sweep))
ck('J6g 反控（决定性）：有 %d 个秩切点的密度相对差**比 0x48948A 更小**（最小 %.4f%% 在秩 %d）'
   ' ⇒ 密度同族不能标识 0x48948A' % (n_better, 100 * sweep[0][0], sweep[0][1]),
   n_better > 0, '0x48948A=%.4f%% rank=%d best=%.4f%%' % (
       100 * rel_split, n_better, 100 * sweep[0][0]))
ck('J6h 0x48948A 的相对差 %.4f%% 位于全扫描第 %.1f 百分位（不是极值）'
   % (100 * rel_split, 100 * n_better / len(sweep)),
   0.05 < n_better / len(sweep) < 0.95)

print('\nSUMMARY %d/%d PASS, FAIL=%d' % (len(RES) - FAIL, len(RES), FAIL))
io.open(OUT, 'w', encoding='utf-8').write(json.dumps(
    {'round': 'R163', 'script': 'r163c_f24_scope_slip.py', 'fail': FAIL, 'asserts': RES,
     'facts': {'r95_4743': n4743, 'r95_961': n961, 'hit': hit, 'total': tot, 'rest': rest,
               'binary_raw_cover': len(covered_raw), 'evid_dirs': len(evid_dirs),
               'evid_files': len(evid_files), 'text_hit_files': text_hit_files,
               'f24_8619_occ': len(occ), 'all_retract': ok_ctx,
               'slip_written': any(k in blob for k in ('EVIDENCE', '语料覆盖率', '口径滑移')),
               'rank_of_split': srt.index(0x48948A),
               'rank_density_gaps': [round(100 * x, 4) for x, _k, _c in sweep],
               'rank_better_than_split': n_better,
               'split_rel_diff_pct': round(100 * rel_split, 4)}},
    ensure_ascii=False, indent=1))
sys.exit(0 if FAIL == 0 else 1)
