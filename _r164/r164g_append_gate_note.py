#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r164g_append_gate_note.py —— 把「门禁 R163 → R164 联动」这一节补进四件套

时序说明：四件套（r164e）先写完，门禁升级（r164f）在其后完成 —— 因为门禁的 C16
逐节下界需要 2.169 的**实测字节**，而 2.169 必须先落盘才能实测。故本脚本把门禁结果
补写进四件套，属于**同一轮内的一次受控追加**（不改任何已有字符，只追加）。

约束：R14_COMMON CR 保持 1081、台账 CR 337、LEAD_LOCK CR 137、看板 CR 0 且行数 <= 300。
追加一律用 `\\n`（四件里新增段本来就是 LF 结尾，混用会改变 CR 计数）。
"""
import hashlib
import io
import os
import sys
import time

R = '/home/t628/projects/ra2-campaign-forge'
T = R + '/lead/next_re_20261117_r14'
RC = T + '/R14_COMMON.md'
LED = R + '/lead/GOAL_THREE_TARGETS_20261018.md'
LOCK = R + '/lead/LEAD_LOCK'
BRD = T + '/STATUS_BOARD.md'
BD = T + '/R17_LEAD_BASELINE'

NOTE = (
    '**十二 · 门禁 R163 → R164（本节落盘后补写，因为 C16 下界要用本节实测字节）.** '
    'GATE_VER `R163` → `R164`；C16 新增 `169: 5331`（= §2.169 实测 **10,662 B** 的一半），'
    '逐节表 **162 → 163 节**；随之重钉四处常量：`C16_FLOORS_SHA256` `8773c1be…` → **`ed568171…`**、'
    '`FREEZE_SHA256` `3e454a8f…` → **`85afa34f…`**（`DISC_UNVERIFIABLE.tsv` 纪律号 20 的 col4 同步）、'
    '`C7_TEXT_SHA256` `0fdc2083…` → **`6ecc3726…`**、`C7_ROW_SHA[\'20\']` `77508b2c…` → **`56498816…`**。'
    '**反控**：`C14_TEXT_SHA256` 一字未动（`a740bcc9…` 前后相同）—— 这两张表本轮都不该动。'
    '**三段验证**：① 沙箱预演（三层镜像 + 显式构造 `DR=R999` 的失配副本）exit 0 / FAIL 0 / C16 unpinned 0，'
    '且负控副本报 `C10 self GATE_VER registered`；② 生产 `gate_runner` 实名复验 G1=ok（`check_disc` exit 0 / FAIL 0）/ '
    'G2=ok（`facts_floors` exit 0 / FAIL 0）/ G3 六条全 PASS（GATE_VER 三处一致 `R164`、'
    '`FREEZE` == 现盘 sha、`facts CUR_SHA256` == 现盘 V544 sha、`TOTAL_BYTES` == 100,616、'
    '`C16_FLOORS_SHA256` 由 163 节重算、`MASTER_SHA256` 由常量重算）；③ 直取主门禁 NOTE 行 '
    '`C16 per-section floors: 163 sections measured (pinned 163), hollow/deficient 0, missing 0, unpinned 0, min margin 20`。'
    '**自错 S-509**：`r164f` 首版把「插入新行」写成了 `169` 在**判断**、`168` 在**插入**（两侧不对称）⇒ '
    '`0.5` 与 `0.5b` 两条当场 FAIL、脚本 abort 未写盘；改成两侧同键后一次通过。'
)

fails = []


def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  :: ' + str(d)[:200]) if d else ''))
    if not ok:
        fails.append(n)
    return ok


def rb(p):
    with open(p, 'rb') as f:
        return f.read()


def sha(b):
    return hashlib.sha256(b).hexdigest()


def bak(path, tag):
    stamp = time.strftime('%Y%m%d_%H%M%S')
    out = os.path.join(BD, os.path.basename(path) + '.before_r164g_%s_%s.bak' % (tag, stamp))
    fd = os.open(out, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(rb(path))
    return out


print('== 0 · 旧态 ==')
o = {k: rb(p) for k, p in (('rc', RC), ('led', LED), ('lock', LOCK), ('brd', BRD))}
for k, b in o.items():
    print('  %-5s %d B CR=%d lines=%d' % (k, len(b), b.count(b'\r'), b.count(b'\n')))
ck('0.1 R14_COMMON CR 1081', o['rc'].count(b'\r') == 1081, o['rc'].count(b'\r'))
ck('0.2 台账 CR 337', o['led'].count(b'\r') == 337, o['led'].count(b'\r'))
ck('0.3 LEAD_LOCK CR 137', o['lock'].count(b'\r') == 137, o['lock'].count(b'\r'))
ck('0.4 看板 CR 0 / 行数 <= 300', o['brd'].count(b'\r') == 0 and o['brd'].count(b'\n') <= 300,
   o['brd'].count(b'\n'))
DONE = all('门禁 R163 → R164（本节落盘后补写' in o[k].decode('utf-8') for k in ('rc', 'led', 'lock'))
print('  已完成标记:', DONE)

if not DONE:
    ck('1.1 R14_COMMON 里 2.169 是末节（末句含 G1=ok/G2=ok/G3=ok）',
       'G1=ok/G2=ok/G3=ok' in o['rc'].decode('utf-8').rstrip().split('\n')[-1])
    ck('1.2 台账里 §1219 是末节（末句含本轮「落盘」关键词）',
       '**落盘' in o['led'].decode('utf-8').rstrip().split('\n')[-1]
       or '落盘' in o['led'].decode('utf-8').rstrip().split('\n')[-1])
    ck('1.3 LEAD_LOCK 里 OU 段是末段（末句含 G1=ok G2=ok G3=ok）',
       'G1=ok G2=ok G3=ok' in o['lock'].decode('utf-8').rstrip().split('\n')[-1])
    ck('1.4 看板首节是第 164 轮', o['brd'].decode('utf-8').startswith('## 🟢 R17 第 164 轮'))

    # 每件：追加在「本轮新增段末尾」
    new = {}
    new['rc'] = o['rc'].decode('utf-8').rstrip('\n') + '\n\n' + NOTE + '\n'
    new['led'] = o['led'].decode('utf-8').rstrip('\n') + '\n\n' + NOTE + '\n'
    new['lock'] = o['lock'].decode('utf-8').rstrip('\n') + '\n\n' + NOTE + '\n'
    brd_t = o['brd'].decode('utf-8')
    idx = brd_t.find('\n## 🟢 R17 第 163 轮')
    ck('2.0 看板里能定位第 163 轮段起点（新段插在它之前）', idx > 0, idx)
    # 看板：本轮的 NOTE 要在「第 164 轮」段内，也就是插在 163 轮段之前
    brd_new = brd_t[:idx].rstrip('\n') + '\n\n' + NOTE.strip() + '\n' + brd_t[idx:]
    new['brd'] = brd_new

    for k, txt in new.items():
        if k == 'brd':
            # 看板是「在 164 轮段内插入一句」⇒ 旧文不是新文的子串；改为逐段可复原检查
            _ot = o['brd'].decode('utf-8')
            # 插入点前后各多一个空行 ⇒ 复原时要把「NOTE + 其后的换行 + 一个多余空行」一起剥掉
            _r = txt.replace('\n\n' + NOTE.strip() + '\n', '\n', 1)
            ck('2.%s 旧文去掉插入点后可由新文复原（无原地改写）' % k, _r == _ot,
               (len(txt) - len(_ot), len(_r) - len(_ot)))
        else:
            ck('2.%s 旧文仍是新文的真子串（纯追加，无原地改写）' % k, o[k].decode('utf-8') in txt)
        ck('2.%s 无 CR 引入' % k, '\r' not in NOTE)
    ck('2.5 R14_COMMON 追加后 CR 仍 1081', new['rc'].encode().count(b'\r') == 1081,
       new['rc'].encode().count(b'\r'))
    ck('2.6 台账追加后 CR 仍 337', new['led'].encode().count(b'\r') == 337,
       new['led'].encode().count(b'\r'))
    ck('2.7 LEAD_LOCK 追加后 CR 仍 137', new['lock'].encode().count(b'\r') == 137,
       new['lock'].encode().count(b'\r'))
    ck('2.8 看板追加后 CR 0 / 行数 <= 300',
       new['brd'].encode().count(b'\r') == 0 and new['brd'].encode().count(b'\n') <= 300,
       new['brd'].encode().count(b'\n'))
    ck('2.9 看板新段仍在第 1 节（164 轮打头）', new['brd'].startswith('## 🟢 R17 第 164 轮'))

    for k, p in (('rc', RC), ('led', LED), ('lock', LOCK), ('brd', BRD)):
        ck('3.%s 写前 sha 未变' % k, sha(rb(p)) == sha(o[k]))
        b = bak(p, k)
        ck('3.%s 备份逐字节相同' % k, rb(b) == o[k], os.path.basename(b))
        with open(p, 'wb') as f:
            f.write(new[k].encode('utf-8'))
        ck('3.%s 回读一致' % k, rb(p).decode('utf-8') == new[k])
else:
    print('  [idempotent] 已补写过，转终态校验')

print('== 4 · 终态 ==')
f = {k: rb(p) for k, p in (('rc', RC), ('led', LED), ('lock', LOCK), ('brd', BRD))}
ck('4.1 R14_COMMON CR 1081 且含门禁节', f['rc'].count(b'\r') == 1081
   and '门禁 R163 → R164' in f['rc'].decode('utf-8'))
ck('4.2 台账 CR 337 且含门禁节', f['led'].count(b'\r') == 337
   and '门禁 R163 → R164' in f['led'].decode('utf-8'))
ck('4.3 LEAD_LOCK CR 137 且含门禁节', f['lock'].count(b'\r') == 137
   and '门禁 R163 → R164' in f['lock'].decode('utf-8'))
ck('4.4 看板 CR 0 / <=300 行 / 首节 164 轮 / 含门禁节',
   f['brd'].count(b'\r') == 0 and f['brd'].count(b'\n') <= 300
   and f['brd'].decode('utf-8').startswith('## 🟢 R17 第 164 轮')
   and '门禁 R163 → R164' in f['brd'].decode('utf-8'), f['brd'].count(b'\n'))

print('\n== 结果 ==')
print('FAIL = %d' % len(fails))
if fails:
    for x in fails:
        print('  FAILED: ' + x)
    sys.exit(1)
print('[exit 0]')
sys.exit(0)
