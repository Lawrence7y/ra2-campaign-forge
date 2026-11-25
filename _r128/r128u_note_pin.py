# -*- coding: utf-8 -*-
"""R128u：把「收口期追加：C16 重钉 2.132 + 看板归档」如实补进四件套（不改上文）。

R127 已建立的规矩：收口期确实动了门禁就必须单独记一段，不能靠改上文掩盖。
本轮除 r128j/r128k 记的 C11 真修与 GATE_VER 升级外，收口时还做了两件事：
  一 看板写入后 284 行超 300 上限，按阈值把第 125、126 两轮整段搬进 BOARD_ARCHIVE
  二 新增 2.132 后 C16 表外未钉节数变 1，按半量规则补钉 132（11997 B -> 5998），重算摘要
两件都带反控（r128r / r128s / r128t）。
"""
import io, os, hashlib, datetime
ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BK = os.path.join(R14, 'R17_LEAD_BASELINE')
RC = os.path.join(R14, 'R14_COMMON.md')
LED = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
BRD = os.path.join(R14, 'STATUS_BOARD.md')
TS = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
EXPECT = {RC: 1081, LED: 337, LOCK: 137, BRD: 0}

def sha16(b): return hashlib.sha256(b).hexdigest()[:16]

def do(path, tag, new_text, marker=None):
    assert '`' not in new_text
    old = io.open(path, 'rb').read()
    dst = os.path.join(BK, 'r128_note_%s.%s.bak' % (tag, TS))
    fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    try: os.write(fd, old)
    finally: os.close(fd)
    want = EXPECT[path]
    assert old.count(b'\r') == want
    nb = (old.decode('utf-8').rstrip('\n') + '\n' + new_text).encode('utf-8')
    io.open(path, 'wb').write(nb)
    rb = io.open(path, 'rb').read()
    assert rb == nb and rb.count(b'\r') == want
    if marker: assert marker.encode() in rb
    print('  WROTE %-13s %s -> %s  CR=%d  LF=%d' % (tag, sha16(old), sha16(rb),
                                                    rb.count(b'\r'), rb.count(b'\n')))

RC_NOTE = '''
**十三 · 收口期追加（如实记，不改上文）。** 除第九条之外，收口时还动了三处，全部带反控，方向都是收紧。

其一，看板归档。写入第 128 轮段后看板达 284 行，越过了 300 行上限，按阈值把最早的**第 125 轮与第 126 轮**两段整段搬进 BOARD_ARCHIVE（108 行）：搬前归档 993936 B / 6630 行 / CR=2952，搬后 1007724 B / 6738 行 / **CR 仍 2952**；看板 284 行降到 **176 行**、CR 仍 **0**。归档是纯 LF 追加，不引入任何 CR —— 这是 CR 不变量的关键，若用 Windows 默认换行写就会把归档 CR 从 2952 顶上去。两份正本都先做了 wx 独占备份。

其二，C16 重钉 2.132。新增 2.132 后 C16 的表外未钉节数从 0 变成 1。按半量规则把 132 纳进 C16_FLOORS：实测正文 **11997 B**，取半 **5998**。表条目从 125 涨到 **126**，逐 id:floor 规范化串的摘要从 a87a240c10947077 改为 **2c6db9b43151f7ff**。重钉后 C16 五项全清：pinned 126、hollow 0、missing 0、unpinned **0**、min margin 1155。

其三，收尾反控 r128t 共 6 项全 PASS，用的是「正本改名藏起 + 改过的副本放到正本路径 + finally 恢复并断言 sha」（沿用 r128k 已修好的做法，不再踩 R126 S-161 的临时目录陷阱）：正控 exit 0 且 C10 显示 ok(R128)、C16 显示 unpinned 0 与 pinned 126；GATE_VER 改回 R127 而第 20 行仍登记 R128 -> exit 1 命中 C10；把 132 的下界改成 1000 而不改摘要 -> exit 1 命中 C16d（NOTE 行显示 TAMPERED，FAIL 行报 38b283096f1326ba != 2c6db9b43151f7ff）；把 2.132 正文清成只剩标题行 -> exit 1 命中 C16 并报 **(132, 185, 5998)**。收尾断言 check_disc.py（fefe48219c8ed9b0）与 R14_COMMON.md（9ae35ee2281c6384）的字节都回到改动完成时的值。

终态：check_disc.py **exit 0**、C10 显示 **ok(R128)**、C16 unpinned 0。本轮动门禁共三处（C11 claims-none 真修、GATE_VER R127->R128 并同步第 20 行、C16 重钉 126 条），三处都有反控，没有一处是放松。
'''

LED_NOTE = '''
**K. 收口期追加（如实记，不改上文）。** 收口时另动三处，均带反控、方向收紧：① 看板写入后达 284 行越 300 上限，按阈值把第 125、126 两轮整段搬进 BOARD_ARCHIVE（108 行，纯 LF 追加，归档 CR 仍 2952、看板 284 降到 176 行、CR 仍 0）；② 新增 2.132 使 C16 表外未钉节数变 1，按半量规则补钉 132（实测 11997 B 取 5998），表条目 125 -> 126，摘要 a87a240c10947077 -> 2c6db9b43151f7ff，重钉后 pinned 126 / hollow 0 / missing 0 / unpinned 0 / min margin 1155；③ 收尾反控 r128t 6/6 PASS —— 正控 exit 0 + ok(R128) + unpinned 0；GATE_VER 不同步命中 C10；改 132 下界不改摘要命中 C16d（TAMPERED）；清空 2.132 正文命中 C16 报 (132, 185, 5998)；收尾断言两份正本字节回到改动完成时的值。本轮动门禁共三处（C11 claims-none 真修、GATE_VER 升级并同步第 20 行、C16 重钉 126 条），三处都有反控，无一处放松。终态 exit 0、C10 ok(R128)、C16 unpinned 0。
'''

LOCK_NOTE = '''
HK. 收口期追加（如实记，不改上文）：本轮动门禁共三处，全部带反控、方向都是收紧。其一 C11 的 claims-none 从免检改成可失败（r128j 8 项 + r128k 6 项反控）；其二 GATE_VER 由 R127 升到 R128 并同步 DISC_RECHECK 第 20 行登记式（C10 门自检要求二者一致，而本轮确实动了门禁脚本）；其三新增 2.132 后 C16 表外未钉节数变 1，按半量规则补钉 132（实测 11997 B 取 5998），表条目 125 -> 126、摘要 a87a240c10947077 -> 2c6db9b43151f7ff，重钉后 pinned 126 / hollow 0 / missing 0 / unpinned 0 / min margin 1155。另看板写入后达 284 行越 300 上限，按阈值把第 125、126 两轮整段搬进 BOARD_ARCHIVE（108 行，纯 LF 追加，搬前归档 CR=2952、搬后仍 2952，看板 284 降到 176 行、CR 仍 0）。收尾反控 r128t 6/6 PASS：正控 exit 0 且 C10 显示 ok(R128)、C16 显示 unpinned 0 与 pinned 126；GATE_VER 改回 R127 -> exit 1 命中 C10；改 132 下界不改摘要 -> exit 1 命中 C16d 并显示 TAMPERED；清空 2.132 正文 -> exit 1 命中 C16 报 (132, 185, 5998)。三份正本字节在收尾断言中回到改动完成时的值（check_disc.py fefe48219c8ed9b0、R14_COMMON.md 9ae35ee2281c6384）。终态 check_disc.py exit 0、C10 ok(R128)。
'''

BRD_NOTE = '''
### 十二 · 收口期追加（如实记，不改上文）

写入本节后看板达 284 行，越过了 300 行上限。按阈值把最早的**第 125 轮与第 126 轮**两段整段搬进 BOARD_ARCHIVE（108 行）。归档是纯 LF 追加、不引入任何 CR —— 搬前归档 993936 B / CR=2952，搬后 1007724 B / **CR 仍 2952**；看板 284 行降到 **176 行**、CR 仍 **0**。若用 Windows 默认换行写归档，CR 会被顶到 2952 以上而破坏不变量，这一点必须盯住。

新增 2.132 后 C16 的表外未钉节数从 0 变 1。按半量规则把 132 纳进 C16_FLOORS：实测正文 11997 B 取半 5998，表条目 125 涨到 126，摘要 a87a240c10947077 改为 2c6db9b43151f7ff。重钉后 C16 五项全清：pinned 126、hollow 0、missing 0、unpinned **0**、min margin 1155。

收尾反控 r128t 共 6 项全 PASS：正控 exit 0 且 C10 显示 ok(R128)；GATE_VER 改回 R127 -> exit 1 命中 C10；把 132 的下界改成 1000 而不改摘要 -> exit 1 命中 C16d 并显示 TAMPERED；把 2.132 正文清成只剩标题行 -> exit 1 命中 C16 并报 (132, 185, 5998)；收尾断言两份正本字节回到改动完成时的值。

**本轮动门禁共三处**（C11 claims-none 真修、GATE_VER R127->R128 并同步第 20 行、C16 重钉 126 条），三处都有反控，没有一处是放松。终态 check_disc.py exit 0、C10 显示 ok(R128)、C16 unpinned 0；五项 CR 全绿 1081/137/337/0/2952。
'''

do(RC, 'R14_COMMON.md', RC_NOTE, marker='十三 · 收口期追加')
do(LED, 'LEDGER', LED_NOTE, marker='K. 收口期追加')
do(LOCK, 'LEAD_LOCK', LOCK_NOTE, marker='HK. 收口期追加')
do(BRD, 'STATUS_BOARD', BRD_NOTE, marker='十二 · 收口期追加')

for p, tag, want in ((RC, 'R14_COMMON', 1081), (LED, 'LEDGER', 337),
                     (LOCK, 'LEAD_LOCK', 137), (BRD, 'STATUS_BOARD', 0)):
    b = io.open(p, 'rb').read()
    print('  CHECK %-13s CR=%d (want %d) lines=%d' % (tag, b.count(b'\r'), want, b.count(b'\n')))
    assert b.count(b'\r') == want
    assert b.count(b'\n') <= 300 if tag == 'STATUS_BOARD' else True
