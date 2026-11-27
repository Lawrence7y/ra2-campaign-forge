# -*- coding: utf-8 -*-
"""R183 I：收口补 —— 如实登记 S-183f1（四件套先写、C16 重钉后补）并补实测终态。
fail-closed：CR 硬闸 + 旧文前缀 + 回读。"""
import hashlib, io, os, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BL = os.path.join(TIER, 'R17_LEAD_BASELINE')
LOCK = os.path.join(ROOT, 'lead/LEAD_LOCK')
BRD = os.path.join(TIER, 'STATUS_BOARD.md')
stamp = time.strftime('%Y%m%d_%H%M%S')
fails, n = [], 0
def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)

ADD_LOCK = '''
**PM10. 📌 收口补（同轮第二段，如实登记一处顺序错误）. S-183f1 属「先写结论、后做验证」**：`r183f_c16_repin.py` 首次创建时 `cd` 落错目录（在 `lead/` 下而非库根）⇒ **脚本文件根本没生成**，而我接着跑了四件套追加脚本，于是 PM6 与 §2.188 里「C16_FLOORS 180 → 181 条并重钉 pin」这句话**当时并不成立**。发现方式是回到 `_r183/` 清点产物时少一个文件。补跑实测：**21 断言 0 FAIL**，`check_disc.py` **75,304 → 75,318 B（+14）/ `3d455edd07d30656` → `e3d37fc04c354d8b`**，`C16_FLOORS` 180 → **181** 条、pin **`70f66602…` → `5311d6b9…`**，反控三条（floor 调大 1 / 删 187 / 其余 180 条未变）真跑通过；补跑后三门复跑 `check_disc` exit 0（`C16d floor-table pin: 5311d6b9… (OK)`、`182 sections measured (pinned 181) / unpinned 1`）、`facts_floors` exit 0、`gate_runner` G1=G2=G3=ok。⇒ 结论本身现在成立，但**写文顺序错了**：应「先跑脚本、再写它成功」。这条与 S-183e3（把崩溃 exit 1 当判据失败）同族 —— **都把「脚本跑了」当成「脚本按预期跑了」**，族谱第七次。
'''

ADD_BRD = '''
**收口补（同轮第二段，如实登记）**：`r183f_c16_repin.py` 首建时 `cd` 落错目录、**文件根本没生成**，而四件套先写了「C16 已重钉」⇒ 当时不成立。补跑 **21 断言 0 FAIL**：`check_disc.py` **75,304 → 75,318 B / `3d455edd…` → `e3d37fc0…`**，`C16_FLOORS` 180 → **181** 条、pin **`70f66602…` → `5311d6b9…`**；三门复跑 exit 0 / G1=G2=G3=ok，`182 sections measured (pinned 181) / unpinned 1`。**族谱**：与 S-183e3 同族（把「脚本跑了」当成「脚本按预期跑了」），第七次。
'''

print('== A · 旧态 ==')
bows = {}
for p, cr in ((LOCK, 137), (BRD, 0)):
    b = open(p, 'rb').read(); bows[p] = b
    ck('A %s CR == %d' % (os.path.basename(p), cr), b.count(b'\r') == cr, b.count(b'\r'))
ck('A 看板行数 %d <= 300' % bows[BRD].count(b'\n'), bows[BRD].count(b'\n') <= 300, bows[BRD].count(b'\n'))

print('== B · 构造 ==')
nl = bows[LOCK].decode('utf-8').rstrip('\n') + '\n' + ADD_LOCK.lstrip('\n')
nb = bows[BRD].decode('utf-8').rstrip('\n') + '\n' + ADD_BRD.lstrip('\n')
ck('B LOCK CR 保持 137', nl.count('\r') == 137, nl.count('\r'))
ck('B LOCK 旧文是新文前缀', nl.startswith(bows[LOCK].decode('utf-8').rstrip('\n')))
ck('B BOARD CR 保持 0', nb.count('\r') == 0, nb.count('\r'))
ck('B BOARD 行数 %d <= 300' % nb.count('\n'), nb.count('\n') <= 300, nb.count('\n'))
ck('B PM10 在场', '**PM10. 📌 收口补' in nl)
ck('B 收口补段在场', '收口补（同轮第二段，如实登记）' in nb)

if fails:
    print('★ fail-closed：%d 条未过，不写盘' % len(fails)); sys.exit(1)

print('== C · 写盘 ==')
for p, oldraw, newtxt in ((LOCK, bows[LOCK], nl), (BRD, bows[BRD], nb)):
    assert open(p, 'rb').read() == oldraw, '母本被外部改动: %s' % p
    o = hashlib.sha256(oldraw).hexdigest()
    bak = os.path.join(BL, '%s.before_r183_add_%s.bak' % (os.path.basename(p), stamp))
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f: f.write(oldraw)
    ck('C1 %s 备份独占' % os.path.basename(p), hashlib.sha256(open(bak, 'rb').read()).hexdigest() == o)
    io.open(p, 'w', encoding='utf-8', newline='').write(newtxt)
    back = open(p, 'rb').read()
    ck('C2 %s 回读一致' % os.path.basename(p), hashlib.sha256(back).hexdigest() == hashlib.sha256(newtxt.encode()).hexdigest())
    print('   %-20s %d -> %d B ; sha %s' % (os.path.basename(p), len(oldraw), len(back), hashlib.sha256(back).hexdigest()[:16]))

print('== D · 终态 ==')
for p, cr in ((LOCK, 137), (BRD, 0)):
    b = open(p, 'rb').read()
    ck('D %s CR == %d' % (os.path.basename(p), cr), b.count(b'\r') == cr, b.count(b'\r'))
print('   看板行数 %d' % open(BRD, 'rb').read().count(b'\n'))
print('\n== %d 断言, %d FAIL ==' % (n, len(fails)))
sys.exit(1 if fails else 0)
