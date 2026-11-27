#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R173 D：F23 的「18 条 / 4 条」两口径与「全部失联」的闭世界复核。

F23 statement ③ 写：按 basename 精确口径 18 条（主份 1 + 备份 17，17 份字节两两不同）；
按「路径含 /COVERAGE/」口径 4 条。R173 现场复算这四个数 + 存活数，并加一条此前无人测的：
**在没有 coverage.tsv 的前提下，F23 的 458/291/293/1,196/1,654 是否可由任何在盘文件重数**。

反控：
 N1 把基准根换成仓库根，存活数必须仍为 0（证明不是拼接错）。
 N2 清单里已知在盘的 a2_sites.json 必须判存活（证明 isfile 逻辑可用）。
 N3 把 basename 匹配从 == 改成 contains，条数必须严格变大（证明「精确口径」真的是精确）。
"""
import collections, json, os, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
LEAD = os.path.join(ROOT, 'lead')
MAN = os.path.join(LEAD, 'next_re_20261117_r14/R17_R101_TIER_FINAL_4417/tier_final_4417.tsv')
fails, n = [], 0
def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)

rows = [l.split('\t') for l in open(MAN, encoding='utf-8').read().rstrip('\n').split('\n')[1:]]
ck('D1 清单 4,417 数据行、每行 4 列', len(rows) == 4417 and all(len(r) == 4 for r in rows),
   (len(rows), min(len(r) for r in rows), max(len(r) for r in rows)))

def rel(p): return p.replace('\\', '/')
bn = [r for r in rows if os.path.basename(rel(r[0])) == 'coverage.tsv']
ck('D2 basename 精确 == coverage.tsv 的记录恰 18 条', len(bn) == 18, len(bn))
ck('D3 这 18 条的字节值两两不同（distinct 18）',
   len(set(int(r[1]) for r in bn)) == 18, len(set(int(r[1]) for r in bn)))
alive_bn = [r for r in bn if os.path.isfile(os.path.join(LEAD, rel(r[0])))]
ck('D4 18 条里在盘存活恰 0 条', len(alive_bn) == 0, len(alive_bn))

cp = [r for r in rows if '/COVERAGE/' in rel(r[0])]
ck('D5 路径含 /COVERAGE/ 的记录恰 28 条', len(cp) == 28, len(cp))
cp_cov = [r for r in cp if os.path.basename(rel(r[0])) == 'coverage.tsv']
ck('D6 其中 basename 为 coverage.tsv 的恰 4 条', len(cp_cov) == 4,
   [(rel(r[0]), r[1]) for r in cp_cov])
alive_cp = [r for r in cp if os.path.isfile(os.path.join(LEAD, rel(r[0])))]
ck('D7 28 条里在盘存活恰 0 条（整个 COVERAGE 树已失）', len(alive_cp) == 0, len(alive_cp))
ck('D8 lead/next_re_20261117_r14/COVERAGE 目录不存在',
   not os.path.isdir(os.path.join(LEAD, 'next_re_20261117_r14/COVERAGE')), True)

# N1 / N2 / N3
alive_root = [r for r in bn if os.path.isfile(os.path.join(ROOT, rel(r[0])))]
ck('N1 反控：基准根换成仓库根，存活数仍 0', len(alive_root) == 0, len(alive_root))
a2 = [r for r in rows if rel(r[0]).endswith('a2_sites.json')]
ck('N2 反控：a2_sites.json 判存活为真（isfile 逻辑可用，不是恒假）',
   len(a2) == 1 and os.path.isfile(os.path.join(LEAD, rel(a2[0][0]))), len(a2))
bn_loose = [r for r in rows if 'coverage.tsv' in os.path.basename(rel(r[0]))]
ck('N3 反控：basename 改成 contains 后条数严格变大（精确口径确实是精确的）',
   len(bn_loose) > len(bn), (len(bn), len(bn_loose)))

# F23 计数能否由在盘文件重数：候选替代物
# S-599：首版 D9 断言「清单里 0 条」——实测恰 1 条（427,038 B，路径
# next_re_20261112_r10/W130_atlas/function_atlas.tsv），但存活 0 ⇒ 结论「无从重数」不变，
# 断言值错了。改成实测三分量：记录数 / 记录字节 / 存活数。
_at = [r for r in rows if os.path.basename(rel(r[0])) == 'function_atlas.tsv']
ck('D9 清单里 function_atlas.tsv 恰 1 条、427,038 B、存活 0（有下落但已失）',
   len(_at) == 1 and _at[0][1] == '427038'
   and not os.path.isfile(os.path.join(LEAD, rel(_at[0][0]))),
   [(rel(r[0]), r[1]) for r in _at])
atlas_hits = []
for base, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d != '.git']
    if 'function_atlas.tsv' in files: atlas_hits.append(os.path.join(base, 'function_atlas.tsv'))
ck('D10 全库 os.walk 找到 function_atlas.tsv 恰 0 个', len(atlas_hits) == 0, atlas_hits)
ck('D11 lead/next_re_20261112_r10 目录不存在',
   not os.path.isdir(os.path.join(LEAD, 'next_re_20261112_r10')), True)

# 4 个计数在盘上有没有「同名字面」带出处（不是重数，只是找下落）
t = open(os.path.join(LEAD, 'next_re_20261117_r14/R17_R125_FACTINDEX_V553/FACT_INDEX.tsv'),
         encoding='utf-8').read()
f23 = [r.split('\t') for r in t.rstrip('\n').split('\n')[1:] if r.startswith('F23\t')][0]
for lit in ('4,147,334', '18,498', '1,654', '1,196', '291', '293'):
    print('   F23 内字面 %-10s stmt=%d lim=%d 全表=%d' %
          (lit, f23[1].count(lit), f23[4].count(lit), t.count(lit)))
ck('D12 F23 行内四个数（458/291/293/1,196）与分母 1,654 均有字面',
   all(x in f23[1] for x in ('458', '291', '293', '1,196', '1,654')), True)

print()
print('SUMMARY: %d assertions, %d FAIL' % (n, len(fails)))
json.dump(dict(fails=fails, asserts=n,
               basename_18=len(bn), alive=len(alive_bn),
               coverage_path_28=len(cp), coverage_path_cov_4=len(cp_cov),
               coverage_path_alive=len(alive_cp),
               atlas_files=len(atlas_hits)),
          open('/home/t628/projects/ra2-campaign-forge/_r173/r173d_f23_layer.json', 'w'),
          ensure_ascii=False, indent=1)
sys.exit(1 if fails else 0)
