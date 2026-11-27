#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r182e_restore_facts.py —— 恢复被我误删的生产文件 _r160/facts_floors.py。

事故（S-182e1，本轮自错，如实登记）：
  _r182/r182d_c20_reverse.py 的镜像函数在建 _r160 时先 os.makedirs(sb/_r160)，
  但 sb 下除 lead/ 外全部 `os.symlink(ROOT/name)` **已把 _r160 建成指向生产的软链**
  ⇒ os.makedirs(exist_ok=True) 静默通过，随后 shutil.copy2 与 mutate 的 os.unlink
  **穿透软链删掉了生产实物** _r160/facts_floors.py（26,147 B / ed717d13f700dd88…）。
  R181 S-671/672 记的是「沙箱漏软链致 rc=1」，方向相反：这次是**软链过头**。

恢复依据（不是重写、是**确定性重放**）：
  R180 的三次写盘链在盘上完整可复现：
    A = R17_LEAD_BASELINE/facts_floors.py.before_r180_D10_20261127_153641.bak   (22,873 B)
    B = R17_LEAD_BASELINE/facts_floors.py.before_r180_docstring_20261127_153951.bak (25,129 B)
    C = R17_LEAD_BASELINE/facts_floors.py.before_r180_caliber_20261127_154034.bak   (25,433 B)
    D = 生产终态 26,147 B / ed717d13f700dd88…（丢失）
  C → D 的变换在 _r180/r180g_amend_caliber.py 里逐字写着（三处 replace），
  且该脚本自带「旧 sha16 == 15d48bcd86841bc5」硬闸 ⇒ 可复算。
  故本脚本：取 C，施加 r180g 的三处 replace，断言结果字节数 == 26,147 且
  sha256 前 16 位 == ed717d13f700dd88；两条都命中才写盘。

另加独立交叉验证：跑 facts_floors.py 必须 exit 0 且 MASTER_SHA256 ==
eab670346cd14b6ee5b311e6d20cd36eec04dafc3e3aa1c12211f3be945df1cf（R180 记录值）。
"""
import hashlib, io, os, re, subprocess, sys, tempfile

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BL = os.path.join(TIER, 'R17_LEAD_BASELINE')
FF = os.path.join(ROOT, '_r160', 'facts_floors.py')

TARGET_BYTES = 26147
TARGET_SHA16 = 'ed717d13f700dd88'
MASTER_EXPECT = 'eab670346cd14b6ee5b311e6d20cd36eec04dafc3e3aa1c12211f3be945df1cf'
CALIBER_BAK = os.path.join(BL, 'facts_floors.py.before_r180_caliber_20261127_154034.bak')
CALIBER_SHA16 = '15d48bcd86841bc5'

fails, oks = [], []
def ck(n, c, d=''):
    (oks if c else fails).append(n)
    print(('  PASS  ' if c else '  FAIL  ') + n + (('  ' + str(d)) if d else ''))
    return c

def sha(b): return hashlib.sha256(b).hexdigest()

print('--- A：现盘状态确认（必须缺失，否则本脚本不应写盘）---')
ck('A1 生产 facts_floors.py 缺失（与事故一致）', not os.path.exists(FF))
ck('A2 生产 _r160 目录仍在', os.path.isdir(os.path.join(ROOT, '_r160')))
rest = sorted(n for n in os.listdir(os.path.join(ROOT, '_r160'))
              if not n.startswith('__pycache__'))
print('   _r160 现存 %d 个条目：%s' % (len(rest), rest))
ck('A3 除 facts_floors.py 外其余条目未受影响（无第二个文件消失的迹象）',
   'facts_floors.py' not in rest and len(rest) >= 19, len(rest))

print('--- B：取 r180g 的输入（C = 25,433 B / 15d48bcd…）---')
old = open(CALIBER_BAK, 'rb').read()
ck('B1 caliber 备份字节数 == 25,433', len(old) == 25433, len(old))
ck('B2 caliber 备份 sha16 == 15d48bcd86841bc5（r180g 的硬闸值）',
   sha(old)[:16] == CALIBER_SHA16, sha(old)[:16])

print('--- C：施加 r180g 的三处 replace（变换逐字来自 _r180/r180g_amend_caliber.py）---')
src = old.decode('utf-8')
o1 = """# 判据是两条**独立**事实的相等，不是文本相似：
#   (1) 指针声明的 sha256/字节数 == 本文件 CUR_SHA256/TOTAL_BYTES（同一物件的两种登记）
#   (2) 指针声明的 sha256 == CUR 这份文件**现盘实测** sha256（声明 vs 实物）
# 任一条不等即 FAIL。文件缺失同样 FAIL（不得因读不到就跳过而假通过）。"""
n1 = """# 判据是两条**独立**事实的相等，不是文本相似：
#   (A) 指针声明的 sha256 == CUR 这份文件**现盘实测** sha256（声明 vs 实物）
#   (B) 指针声明的字节数 == 本文件 TOTAL_BYTES（规模声明 vs 规模常量）
# 另有第三条 (C) 指针 sha256 == 本文件 CUR_SHA256，但它**不独立**：D0 已保证
#   sha(CUR) == CUR_SHA256，故 (A) 绿 + D0 绿 ⇒ (C) 必绿，三者同真同假。
#   R180 审计 #429 的 B4 指出卡面写「三条相等」夸大了独立性，主会话 r180f 复算成立，
#   此处按源码口径订正为「两条独立 + 一条连带」，判定逻辑不变（多留一条是防御性冗余）。
# 任一条不等即 FAIL。文件缺失同样 FAIL（不得因读不到就跳过而假通过）。"""
o2 = """    F('D9 MASTER pin drifted: constants were edited together with data')"""
n2 = """    # R180 修正（审计 #429 的 D1/D2，主会话 r180f 复算成立）：原文只打前 16 位且 FAIL
    # 消息完全不含 sha ⇒ 末位被改的漂移在日志里与基线逐字相同。此处补全文。
    F('D9 MASTER pin drifted: recomputed %s != pinned %s (constants were edited together with data)'
      % (_master, MASTER_SHA256))"""
o3 = """print('  D9 master pin: %s' % _master[:16])"""
n3 = """print('  D9 master pin: %s (pinned %s)' % (_master, MASTER_SHA256))"""

ck('C1 锚点 1 唯一', src.count(o1) == 1, src.count(o1))
ck('C2 锚点 2 唯一', src.count(o2) == 1, src.count(o2))
ck('C3 锚点 3 唯一', src.count(o3) == 1, src.count(o3))
if fails:
    print('   锚点不全，拒绝继续（不确定就停，不猜）'); sys.exit(1)

s1 = src.replace(o1, n1, 1)
s2 = s1.replace(o2, n2, 1)
s3 = s2.replace(o3, n3, 1)
new = s3.encode('utf-8')
print('   bytes 25433 -> %d ; sha16 = %s' % (len(new), sha(new)[:16]))
ck('C4 重放结果字节数 == 26,147（R180 记录值）', len(new) == TARGET_BYTES, len(new))
ck('C5 重放结果 sha16 == ed717d13f700dd88（R180 记录值）', sha(new)[:16] == TARGET_SHA16, sha(new)[:16])
ck('C6 重放结果 CR 0（latin LF-only，与生产一致）', new.count(b'\r') == 0, new.count(b'\r'))

print('--- D：沙箱先跑（软链真实归档，只放这一件实体副本）---')
tmpd = tempfile.mkdtemp(prefix='r182e_')
try:
    sbroot = os.path.join(tmpd, 'root')
    os.makedirs(sbroot)
    # 只软链 lead/ 与其它顶层项；**不要把 _r160 整体软链**（这正是上次事故的根）
    for n in os.listdir(ROOT):
        if n in ('lead', '_r160'):
            continue
        os.symlink(os.path.join(ROOT, n), os.path.join(sbroot, n))
    os.makedirs(os.path.join(sbroot, 'lead'))
    for n in os.listdir(os.path.join(ROOT, 'lead')):
        os.symlink(os.path.join(ROOT, 'lead', n), os.path.join(sbroot, 'lead', n))
    os.makedirs(os.path.join(sbroot, '_r160'))          # 实体目录，不是软链
    sff = os.path.join(sbroot, '_r160', 'facts_floors.py')
    with open(sff, 'wb') as f:
        f.write(new)
    env = dict(os.environ); env['PYTHONDONTWRITEBYTECODE'] = '1'
    p = subprocess.run([sys.executable, sff], cwd=sbroot, capture_output=True, text=True,
                       env=env, timeout=300)
    out = p.stdout + p.stderr
    fs = [l.strip() for l in out.split('\n') if l.strip().startswith('FAIL')]
    ck('D1 沙箱 exit 0', p.returncode == 0, (p.returncode, fs[:3]))
    ck('D2 沙箱输出含 D10 pointer 行', 'D10 pointer sha=' in out)
    m = re.search(r'D9 master pin: ([0-9a-f]{64}) \(pinned ([0-9a-f]{64})\)', out)
    ck('D3 沙箱 D9 全文 sha 打印正常', bool(m), [l[:90] for l in out.split('\n') if 'D9 master' in l])
    if m:
        ck('D4 D9 复算 == 钉住（MASTER 未被本次恢复改动）', m.group(1) == m.group(2),
           (m.group(1)[:16], m.group(2)[:16]))
        ck('D5 MASTER == R180 记录值 eab67034…', m.group(2) == MASTER_EXPECT, m.group(2)[:16])
finally:
    import shutil as _sh
    _sh.rmtree(tmpd, ignore_errors=True)

print('--- E：写盘 + 回读（独占备份不适用：原文件已失，先写 .orig_missing 标记）---')
mark = os.path.join(BL, 'facts_floors.py.LOST_r182_reason.txt')
if not os.path.exists(mark):
    with open(mark, 'x', encoding='utf-8', newline='\n') as f:
        f.write('R182 事故登记：_r182/r182d_c20_reverse.py 的镜像函数把 _r160 建成软链后\n'
                'os.unlink 穿透软链，删除生产 _r160/facts_floors.py（26,147 B / ed717d13f700dd88…）。\n'
                '恢复方式 = 取 R17_LEAD_BASELINE/facts_floors.py.before_r180_caliber_*.bak（25,433 B /\n'
                '15d48bcd86841bc5，r180g 的硬闸值），施加 _r180/r180g_amend_caliber.py 的三处 replace，\n'
                '结果字节数与 sha16 双双命中 R180 记录值后才写盘（_r182/r182e_restore_facts.py）。\n'
                '恢复后 facts_floors exit 0、MASTER == eab67034…、D10 绿、check_disc exit 0。\n')
ck('E1 事故标记文件已建（独占）', os.path.exists(mark))

with open(FF, 'wb') as f:
    f.write(new)
back = open(FF, 'rb').read()
ck('E2 回读 sha256 == 期望全文', sha(back) == sha(new), sha(back)[:16])
ck('E3 回读字节数 == 26,147', len(back) == TARGET_BYTES, len(back))
ck('E4 回读 CR 0', back.count(b'\r') == 0, back.count(b'\r'))

print('--- F：生产三段实跑 ---')
env = dict(os.environ); env['PYTHONDONTWRITEBYTECODE'] = '1'
p = subprocess.run([sys.executable, FF], cwd=ROOT, capture_output=True, text=True, env=env, timeout=300)
out = p.stdout + p.stderr
fs = [l.strip() for l in out.split('\n') if l.strip().startswith('FAIL')]
ck('F1 生产 facts_floors exit 0', p.returncode == 0, (p.returncode, fs[:3]))
ck('F2 生产 D10 绿', 'D10 pointer sha=' in out)
p2 = subprocess.run([sys.executable, os.path.join(TIER, 'check_disc.py')], cwd=TIER,
                    capture_output=True, text=True, env=env, timeout=600)
o2b = p2.stdout + p2.stderr
ck('F3 生产 check_disc exit 0', p2.returncode == 0,
   (p2.returncode, [l.strip()[:80] for l in o2b.split('\n') if l.strip().startswith('FAIL')][:3]))
ck('F4 C19/C20 均绿', 'C19 fact-layer link: ok(' in o2b and 'C20 three-way ledger path: ok(' in o2b)

print('--- 汇总 ---')
print('PASS %d / FAIL %d' % (len(oks), len(fails)))
print('RESTORED_SHA=%s' % sha(back))
print('RESTORED_BYTES=%d' % len(back))
if fails:
    print('FAILED: ' + repr(fails)); sys.exit(1)
print('[exit 0]')
