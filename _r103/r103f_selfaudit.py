#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r103f_selfaudit.py —— 本轮事故与自错的机械复核（不靠记忆，靠盘上字节）

R103 发生了三次自错，本脚本把每一次都做成可复跑的判据，避免只写在摘要里：

  E1 沙箱写穿透事故：sandbox 里 DISC_RECHECK 第 5 列的产物若是 symlink，写它就等于写**真树**。
     判据：现状下 sbxlib.PRODUCTS 全部是实体（islink=False）；反控用 R102 的旧建法（全 symlink）
     复现「写穿透」，并证明守卫 guard_write 会抛出。
  E2 换行纪律：check_disc.py 补丁必须只用 CRLF 增行（LF-only 行号集合恒为 [24,25]）；
     R14_COMMON 新增节必须只用 LF（CRLF 计数恒 1081）。两条都有反控。
  E3 配对纪律：未打补丁门禁（GATE_VER=R102）只能配 R102 版 DISC_RECHECK；
     配 R103 版会同时触发 C7/C10 —— 那是配对错误，不是被测判据（纪律 32 零信息格）。
"""
import glob, hashlib, io, json, os, shutil, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sbxlib as S

OUT = os.path.join(S.REAL, '_r103')
checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

RES = {}

# ================================================================ E1 写穿透事故
S.prepare()
links = [r for r in S.PRODUCTS if os.path.islink(os.path.join(S.SBX, r))]
RES['E1'] = {'products': len(S.PRODUCTS), 'symlinked': links,
             'real_products_sha': {}}
ck('E1a 现沙箱：DISC_RECHECK 引用的 %d 个产物全部是实体文件（无 symlink）' % len(S.PRODUCTS),
   links == [], 'symlinked=%s' % links)

# 取 id 3 的产物，在沙箱里写一格再核对真树 sha 未变
row3 = [r for r in S.rows(S.SBX)[0] if r[0] == '3'][0]
prod_rel = row3[4].strip().replace('\\', '/')
real_prod = os.path.join(S.REAL, prod_rel)
sbx_prod = os.path.join(S.SBX, prod_rel)
before = hashlib.sha256(io.open(real_prod, 'rb').read()).hexdigest()
txt = io.open(sbx_prod, encoding='utf-8', newline='').read()
io.open(sbx_prod, 'w', encoding='utf-8', newline='').write(txt + '\n# R103 sandbox write probe\n')
after = hashlib.sha256(io.open(real_prod, 'rb').read()).hexdigest()
io.open(sbx_prod, 'w', encoding='utf-8', newline='').write(txt)
RES['E1']['real_products_sha'][prod_rel] = {'before': before, 'after': after}
ck('E1b 沙箱里写 id 3 的产物，真树该文件 sha256 不变（写不透）', before == after, before[:16])

# 反控：用 R102 旧建法（产物不复制）复现穿透，并用 guard_write 拦住
SBX_OLD = '/tmp/r103_sbx_old'
if os.path.isdir(SBX_OLD):
    shutil.rmtree(SBX_OLD)
os.makedirs(SBX_OLD)
for e in os.listdir(S.REAL):
    if e == 'lead':
        continue
    os.symlink(os.path.join(S.REAL, e), os.path.join(SBX_OLD, e))
os.makedirs(os.path.join(SBX_OLD, 'lead'))
for e in os.listdir(os.path.join(S.REAL, 'lead')):
    if e == 'next_re_20261117_r14':
        continue
    os.symlink(os.path.join(S.REAL, 'lead', e), os.path.join(SBX_OLD, 'lead', e))
os.makedirs(os.path.join(SBX_OLD, S.R14REL))
for e in os.listdir(os.path.join(S.REAL, S.R14REL)):
    s = os.path.join(S.REAL, S.R14REL, e)
    d = os.path.join(SBX_OLD, S.R14REL, e)
    if e in ('check_disc.py', 'DISC_RECHECK.tsv', 'DISC_UNVERIFIABLE.tsv', 'R14_COMMON.md'):
        shutil.copy2(s, d)
    else:
        os.symlink(s, d)
old_prod = os.path.join(SBX_OLD, prod_rel)
_olde = S.escape_path(old_prod)
RES['E1']['old_sandbox_symlink_component'] = _olde
ck('E1c 反控：R102 的旧建法下该产物路径上有一段 symlink（写它就会改真树，这就是事故机制）',
   _olde is not None, 'symlink_component=%s' % _olde)
ck('E1c2 关键：只查末端 islink 会漏掉（末端不是 symlink，父目录才是）',
   os.path.islink(old_prod) is False and _olde is not None,
   'islink(file)=%s symlink(dir)=%s' % (os.path.islink(old_prod), _olde))
try:
    S.guard_write(old_prod)
    raised = False
    msg = 'no exception'
except RuntimeError as e:
    raised = True
    msg = str(e)[:80]
RES['E1']['guard_msg'] = msg
ck('E1d guard_write 作为结构性防线：对 symlink 路径必抛 RuntimeError', raised, msg)
shutil.rmtree(SBX_OLD)

# ================================================================ E2 换行纪律
gate = io.open(os.path.join(S.REAL, S.R14REL, 'check_disc.py'), 'rb').read()
def lf_only_line_nos(b):
    out, s, n = [], 0, 0
    while True:
        i = b.find(b'\n', s)
        if i < 0:
            break
        n += 1
        if i == 0 or b[i - 1:i] != b'\r':
            out.append(n)
        s = i + 1
    return out
RES['E2'] = {'gate_crlf': gate.count(b'\r\n'), 'gate_lf_only_lines': lf_only_line_nos(gate)}
ck('E2a check_disc.py：CRLF=%d，LF-only 行号集合仍为 [24, 25]（补丁只用 CRLF 增行）'
   % gate.count(b'\r\n'), lf_only_line_nos(gate) == [24, 25], lf_only_line_nos(gate))

rc = io.open(os.path.join(S.REAL, S.R14REL, 'R14_COMMON.md'), 'rb').read()
RES['E2b'] = {'rc_crlf': rc.count(b'\r\n')}
ck('E2b R14_COMMON.md：CRLF 计数 == 1081（未因本轮改动漂移）', rc.count(b'\r\n') == 1081,
   'CRLF=%d' % rc.count(b'\r\n'))

dr = io.open(os.path.join(S.REAL, S.R14REL, 'DISC_RECHECK.tsv'), 'rb').read()
ck('E2c DISC_RECHECK.tsv：仍 LF-only（CR 数 0）', b'\r' not in dr, 'CR-free')

# ================================================================ E3 配对纪律
baks = sorted(glob.glob(os.path.join(S.REAL, S.R14REL, 'R17_LEAD_BASELINE',
                                     'R103.before_check_disc_C13C14C15_*.bak')))
dkbaks = sorted(glob.glob(os.path.join(S.REAL, S.R14REL, 'R17_LEAD_BASELINE',
                                       'R103.before_DISC_RECHECK_ver_*.bak')))
RES['E3'] = {'gate_bak': [os.path.basename(x) for x in baks],
             'dr_bak': [os.path.basename(x) for x in dkbaks]}
ck('E3a 两个 R103 备份都在盘上（门禁 + DISC_RECHECK）', bool(baks) and bool(dkbaks),
   RES['E3'])

G_OLD = io.open(baks[-1], encoding='utf-8', newline='').read()
D_OLD = io.open(dkbaks[-1], encoding='utf-8', newline='').read()
ck('E3b 备份门禁 GATE_VER=R102、备份 DISC_RECHECK 登记 R102（成对，可直接配对跑）',
   "GATE_VER = 'R102'" in G_OLD and "GATE_VER = 'R102'" in D_OLD, '')
ck('E3c 现门禁 GATE_VER=R103、现 DISC_RECHECK 登记 R103（成对）',
   "GATE_VER = 'R103'" in gate.decode('utf-8') and "GATE_VER = 'R103'" in dr.decode('utf-8'), '')

# 交叉配对反控：旧门禁配新表 ⇒ C7/C10 一起响（零信息）
S.prepare()
io.open(S.p(S.SBX, 'check_disc.py'), 'w', encoding='utf-8', newline='').write(G_OLD)
rc_x, f_x, _ = S.run()
RES['E3']['cross_pair'] = {'exit': rc_x, 'fails': f_x[:5]}
ck('E3d 交叉配对反控：旧门禁(R102) + 现表(登记 R103) ⇒ 同时触发 C7 与 C10（证明配对必须成对）',
   rc_x == 1 and any(x.startswith('C10') for x in f_x) and any(x.startswith('C7') for x in f_x),
   [x[:60] for x in f_x][:3])

# 正确配对 ⇒ exit 0
D_OLD_SBX = S.p(S.SBX, 'DISC_RECHECK.tsv')
io.open(D_OLD_SBX, 'w', encoding='utf-8', newline='').write(D_OLD)
io.open(S.p(S.SBX, 'R14_COMMON.md'), 'w', encoding='utf-8', newline='').write(
    io.open(os.path.join(S.REAL, S.R14REL, 'R14_COMMON.md'), encoding='utf-8', newline='').read())
rc_p, f_p, _ = S.run()
ck('E3e 正确配对：旧门禁(R102) + 旧表(登记 R102) ⇒ exit 0（反向控制的前提成立）',
   rc_p == 0, 'exit=%d fails=%s' % (rc_p, f_p[:3]))

json.dump({'checks': checks, 'results': RES},
          io.open(os.path.join(OUT, 'r103f_selfaudit.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('\n%d checks, %d FAIL' % (len(checks), nf))
sys.exit(1 if nf else 0)
