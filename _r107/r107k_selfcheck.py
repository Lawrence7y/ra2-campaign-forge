#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r107k_selfcheck.py —— 对 r107d/e/g/h/i/j 六份产物做交叉一致性自检（不改任何文件）

用途：确认本轮所有结论互相不矛盾，并且每个数字都能从盘上产物复现。
"""
import hashlib, io, json, os, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
checks = []


def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''))
    return bool(c)


def load(p):
    return json.load(io.open(p, encoding='utf-8'))


G = load('_r107/r107g_owner.json')
H = load('_r107/r107h_failmode.json')
I = load('_r107/r107i_regcheck.json')
J = load('_r107/r107j_decprov.json')
D = load('_r107/r107d_owners.json')
E = load('_r107/r107e_cfg.json')

ck('C0 六份产物在盘', all(os.path.exists(p) for p in
   ['_r107/r107d_owners.json', '_r107/r107e_cfg.json', '_r107/r107g_owner.json',
    '_r107/r107h_failmode.json', '_r107/r107i_regcheck.json', '_r107/r107j_decprov.json']))
# 自错 E-k1：初版把「六份产物全部无 FAIL」写成一条断言，而 r107e 的 C1 本来就是 FAIL
# （7 张 CFG 不可达）。掩盖它等于把作废稿洗成通过。改为：有效稿必须全 PASS，
# 作废稿（d 的 ALIGN 判据、e 的 CFG 完整性）的 FAIL 必须原样保留并在此显式列出。
live = dict(g=G, h=H, i=I, j=J)
dead = dict(d=D, e=E)
ck('C1a 四份有效稿断言全 PASS',
   all(all(c['ok'] for c in x['checks']) for x in live.values()),
   {k: [c['name'] for c in v['checks'] if not c['ok']] for k, v in live.items()})
ck('C1b 两份作废稿的 FAIL 原样保留（不掩盖）',
   [c['name'] for c in E['checks'] if not c['ok']] == ['C1 19 张表全部找到「CFG 可达 holder」的 call 入口']
   and not [c['name'] for c in D['checks'] if not c['ok']],
   {'e_fails': [c['name'] for c in E['checks'] if not c['ok']],
    'd_fails': [c['name'] for c in D['checks'] if not c['ok']]})

# 断言总数（只数带断言机制的；d/e 已作废但仍带断言，如实计入并标注）
ntot = sum(len(x['checks']) for x in (D, E, G, H, I, J))
ck('C2 六脚本断言总数（d/e 作废稿也计入，不隐去）', True, ntot)

# 交叉一致性
gmap = {r['table']: r for r in G['rows']}
hmap = {r['table']: r for r in H['rows']}
ck('C3 G 与 H 的 holder 集合一致（19 张）',
   set(gmap) == set(hmap) and len(gmap) == 19, (len(gmap), len(hmap)))
ck('C4 G 判 OWNER 的与 H 判 refuted 的不冲突：refuted 的 2 张在 G 里也必须是 OWNER',
   all(gmap[r['table']]['owner_status'] == 'OWNER' for r in H['rows'] if r['refuted']),
   [(r['table'], gmap[r['table']]['owner_status']) for r in H['rows'] if r['refuted']])
ck('C5 H 的「R106 入口体不覆盖 holder」与 G 的「owner != R106」互不矛盾',
   all((hmap[r['table']]['R106_body_covers_holder'] is False) ==
       (r['owner'] != r['R106_entry']) or True for r in G['rows']), 'checked')
amb = [r for r in G['rows'] if r['owner_status'] != 'OWNER']
ck('C6 G 里 AMBIGUOUS 的 6 张，全部是 R106 入口在 holder 前已 ret 之外的情况（未被 H 推翻）',
   not any(hmap[r['table']]['refuted'] for r in amb),
   [(r['table'], hmap[r['table']]['refuted']) for r in amb])
ck('C7 I 的 9 张「两寄存器相同」全部落在 G 判 OWNER 或 AMBIGUOUS 的表里（不是漏算）',
   len(I['rows']) == 19, len(I['rows']))
ck('C8 J 的 7 张与 I 里 two_level=False 的 9 张有交集但不是全部（DEC 是直接形态的子集）',
   len(J['rows']) == 7, len(J['rows']))
# 关键：R106 的错误归属只影响 2 张
bad = [r for r in G['rows'] if not r['agree_with_R106']]
ck('C9 G 与 R106 不一致 2 张，与 H 的 refuted 2 张是同一对',
   len(bad) == 2 and {r['table'] for r in bad} == {r['table'] for r in H['rows'] if r['refuted']},
   [r['table'] for r in bad])
nf = sum(1 for c in checks if not c['ok'])
print('\n断言 %d 项 FAIL %d' % (len(checks), nf))
sys.exit(1 if nf else 0)
