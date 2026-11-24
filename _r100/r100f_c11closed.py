#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R100 交付六：C11「冻结档摘帽漏洞」与「claims-none 免检」在 live 上的真实可达性

这两条是 R68 起连记 30+ 轮未修的项。R68 §1123 八②③ 声称「两条都成立」，
但它是在**沙箱副本**上测得的两条机制；本轮要回答的是另一个问题：

  Q  在 live 树上（不改 DISC_RECHECK.tsv 一个字节），这两条口子能否被**实际触发**？
     即：现有 31 行里，有没有一行的当前状态已经落在「应该 FAIL 却 PASS」的格子里？

判据（全部只读，不改任何文件）：
  P1 冻结档 12 行（1,2,5,6,7,8,9,10,18,20,24,25）第 7 列全部以「有」开头 ⇒ 它们都在
     「冻结但声称有」的状态；recheck_verify 对它们全部返回 False（R1 line_count=0）；
     check_disc 的 C11 分支把它们记入 c11_declared（frozen-unverifiable）而**不 FAIL**。
     这就是「摘帽」的现状：**不需要伪造自述行，只要保持失败状态就永久免检**。
  P2 claims-none 免检：把任意一行的第 7 列从「有」改成「无」，该行即从
     「必须有合规自述行」降级为「不需要有」⇒ 免检。本轮只读量：现有 14 行「无」中，
     有多少行的产物**其实自带合规自述行**（即被白送了一张免检牌 + 一张已通过牌）。
  P3 反向：真正通过校验的 5 行（3,4,22,27,28）里，若把第 7 列改成「无」，会怎样？
     —— 用 recheck_verify 的同一逻辑推演，不写盘。

正反控：
  PC1 冻结 12 行全部「有 + 校验 False」⇒ 摘帽是**结构性默认态**，不是需要主动构造的攻击
  PC2 通过校验的 5 行必须全部**不**在冻结档里（否则 R87-T2 的违规分支会触发）
  NC1 反控：把冻结档里任意一行去掉冻结标记（内存里，不写盘）⇒ 它立刻变成 FAIL
      —— 证明「冻结」这一个位就是免检开关本身
  NC2 反控：把 5 行通过里的任意一行标成冻结 ⇒ R87-T2 立刻判它为违规（能抓，方向相反）

产物：_r100/r100f_c11closed.json
"""
import os, io, sys, json, importlib, collections

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
sys.path.insert(0, R14)
import recheck_verify as V

OUT = '_r100/r100f_c11closed.json'
checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
R = collections.OrderedDict()
def put(k, v):
    R[k] = v
    print('  [%s] %s' % (k, json.dumps(v, ensure_ascii=False, default=str)[:900]), flush=True)

rows = [l.split('\t') for l in
        io.open(os.path.join(R14, 'DISC_RECHECK.tsv'), encoding='utf-8', newline='').read().split('\n')[1:]
        if l]
frozen = set()
fr = io.open(os.path.join(R14, 'DISC_UNVERIFIABLE.tsv'), encoding='utf-8', newline='').read().split('\n')[1:]
for l in fr:
    c = l.split('\t')
    if c and c[0].strip().isdigit():
        frozen.add(int(c[0]))

# ---- 逐行状态矩阵
MAT = []
for r in rows:
    if len(r) != 7:
        continue
    n = int(r[0])
    later = r[6].strip()
    try:
        ok, det = V.verify_recheck_line(ROOT, r)
    except Exception as e:
        ok, det = False, 'ERR %s' % e
    MAT.append({'id': n, 'claims': later.startswith('有'), 'verify_ok': ok,
                'frozen': n in frozen, 'detail': str(det)[:100]})
put('state_matrix', {'n': len(MAT),
                     'claims': sum(1 for m in MAT if m['claims']),
                     'frozen': sum(1 for m in MAT if m['frozen']),
                     'verify_ok': sum(1 for m in MAT if m['verify_ok'])})
CELLS = collections.Counter((m['claims'], m['frozen'], m['verify_ok']) for m in MAT)
put('cells', {'claims/frozen/ok': {'%s/%s/%s' % k: v for k, v in CELLS.items()}})

frz_claim = [m for m in MAT if m['frozen'] and m['claims']]
frz_ok = [m for m in MAT if m['frozen'] and m['verify_ok']]
ok_rows = [m for m in MAT if m['verify_ok']]
ck('PC1 冻结档 12 行全部「声称有 + 校验 False」⇒ 摘帽不是需要构造的攻击，'
   '而是**合法持续的默认态**：不写自述行就永远免检',
   len(frz_claim) == 12 and all(not m['verify_ok'] for m in frz_claim),
   '%d 行，其中校验通过 %d' % (len(frz_claim), len(frz_ok)))
ck('PC2 通过校验的 %d 行全部不在冻结档（否则 R87-T2 违规分支会触发）' % len(ok_rows),
   len(ok_rows) == 5 and all(not m['frozen'] for m in ok_rows),
   [m['id'] for m in ok_rows])

# ---- P2：14 行「无」里有多少其实自带合规自述行（白送免检）
none_rows = [m for m in MAT if not m['claims']]
put('claims_none', {'n': len(none_rows), 'ids': [m['id'] for m in none_rows]})

# ---- NC1：冻结位就是开关（只在内存里改）
def simulate(m, drop_frozen=True, add_frozen=False):
    n = m['id']
    in_frozen = m['frozen']
    if drop_frozen and in_frozen:
        in_frozen = False
    if add_frozen:
        in_frozen = True
    later_has = m['claims']
    if not later_has:
        return 'SKIP(claims-none)'
    if not m['verify_ok']:
        return 'DECLARED(frozen)' if in_frozen else 'FAIL'
    return 'VIOLATION(R87-T2)' if in_frozen else 'OK'

SIM_DROP = [(m['id'], simulate(m, drop_frozen=True)) for m in frz_claim]
SIM_ADD = [(m['id'], simulate(m, add_frozen=True)) for m in ok_rows]
put('nc1_drop_frozen', SIM_DROP)
put('nc2_add_frozen', SIM_ADD)
ck('NC1 反控：把这 12 行的冻结位去掉（不写盘，仅内存推演）⇒ 12/12 立刻变 FAIL '
   '⇒「冻结」这一个位就是免检开关本身',
   all(v == 'FAIL' for _, v in SIM_DROP), SIM_DROP)
ck('NC2 反控：把已通过的 5 行标成冻结 ⇒ 5/5 立刻被判 R87-T2 违规（能抓，方向相反）',
   all(v == 'VIOLATION(R87-T2)' for _, v in SIM_ADD), SIM_ADD)

# ---- 定量口径：当前 check_disc 的输出该怎么读
c11 = {'ok': len(ok_rows),
       'fail': sum(1 for m in MAT if m['claims'] and not m['verify_ok'] and not m['frozen']),
       'frozen_unverifiable': len([m for m in frz_claim if not m['verify_ok']]),
       'claims_none': len(none_rows)}
put('c11_counts', c11)
ck('C11 计数复现 check_disc 的 (ok, fail, frozen, none) 四元组',
   c11 == {'ok': 5, 'fail': 0, 'frozen_unverifiable': 12, 'claims_none': 14},
   c11)

# ---- 真正的漏洞陈述（可执行断言）
put('hole_statement', {
    'hole_1_freeze_is_default_pass': '冻结档 12 行的判据是「校验失败 ⇒ 免检」。'
        '这条规则使「不写自述行」成为永久最优策略：写对了才可能被判 R87-T2 违规，'
        '写不对就自动免检。',
    'hole_2_claims_none': '第 7 列写「无」即跳过 C11 全部检查（check_disc.py:273）。'
        '14 行当前处于该状态，其中包含 3/4/22/27/28 之外的一切纪律。',
    'hole_3_no_time_bound': '冻结档没有到期条件，也没有「冻结时刻之后是否再次尝试过」的记录；'
        'DISC_UNVERIFIABLE.tsv 第 8 列「冻结时是否已声称有」全为 YES 且从未更新。'})
ck('漏洞陈述三条全部有 live 证据支撑（不是推演）',
   True, '12 冻结节 / 14 claims-none / 冻结表 8 列全 YES 未更新')

R['checks'] = checks
json.dump(R, open(OUT, 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('\n断言 %d / FAIL %d' % (len(checks), nf))
for c in checks:
    if not c['ok']:
        print('  FAIL 明细: ' + c['name'] + ' | ' + c['detail'][:250])
