#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R175 N：把「2 B = raw[913237] 的 } + raw[17624354] 的 }」这句错误指认在四件套里改正，
并把 V557→V558 的订正、指针与 C16 的最终状态登记进去。

为什么必须改：r175l **25 断言 0 FAIL** 证明 913,237 = 9 + dumps(calls) 913,228 **已含 raw[913237] 那个 `}`**，
它不可能同时又是「净额之外多出的 2 B」。正解：2 B = raw[0] 的 `{` 与 raw[17624354] 的 `}`。
四件套里共 4 处（R14 3 处含一处是**正确**的「末字节就是 calls 收尾」表述、LEDGER 1、BOARD 1、LOCK 1 散文写法）。
本脚本只改**错误指认**那 4 处（R14 的 2 处 + LEDGER 1 + BOARD 1 + LOCK 1），并各自追加一段订正登记。
CR 不变量：R14_COMMON 1081 / LEDGER 337 / LEAD_LOCK 137 / BOARD 0。
"""
import hashlib, io, json, os, sys, time
ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
F1 = os.path.join(TIER, 'R14_COMMON.md')
F2 = os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md')
F3 = os.path.join(ROOT, 'lead/LEAD_LOCK')
F4 = os.path.join(TIER, 'STATUS_BOARD.md')
BASE = os.path.join(TIER, 'R17_LEAD_BASELINE')
OUT = os.path.join(ROOT, '_r175/r175n_fix2b.json')
stamp = time.strftime('%Y%m%d_%H%M%S')
EXP_CR = {F1: 1081, F2: 337, F3: 137, F4: 0}
fails, n = [], 0
def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)

blobs = {p: io.open(p, 'rb').read() for p in (F1, F2, F3, F4)}
for p, exp in EXP_CR.items():
    ck('A1 %s CR == %d' % (os.path.basename(p), exp), blobs[p].count(b'\r') == exp, blobs[p].count(b'\r'))

# 四件里那句错误指认的四种写法
WRONG = {
    F1: '，2 = `raw[913237]` 的 calls 收尾 `}` 与 `raw[17624354]` 的文档收尾 `}` 各 1 B，14 = 12 + 2。',
    F2: '；**2** = `raw[913237]`（calls 收尾 `}`）与 `raw[17624354]`（文档收尾 `}`）各 1 B；**14** = 12 + 2。',
    F3: '，2 = calls 收尾 `}` 与文档收尾 `}` 各 1 B，14 = 12 + 2。',
    F4: '；2 = `raw[913237]`（calls 收尾 `}`）与 `raw[17624354]`（文档收尾 `}`）各 1 B；14 = 12 + 2。',
}
RIGHT = {
    F1: '，2 = **`raw[0]` 的 `{` 与 `raw[17624354]` 的 `}`**（**R175 订正**：原写 `raw[913237]` 的 calls 收尾 `}` —— 错，913,237 = 9 + dumps(calls) 913,228 **已含那个 `}`**），14 = 12 + 2 = 1 + 12 + 1。',
    F2: '；**2** = **`raw[0]` 的 `{` 与 `raw[17624354]` 的 `}`**（**R175 订正**：原写 `raw[913237]` —— 错，913,237 已含该 `}`）；**14** = 12 + 2 = 1 + 12 + 1。',
    F3: '，2 = **`raw[0]` 的 `{` 与 `raw[17624354]` 的 `}`**（**R175 订正**：原写「calls 收尾 `}`」—— 错，913,237 已含该 `}`），14 = 12 + 2 = 1 + 12 + 1。',
    F4: '；2 = **`raw[0]` 的 `{` 与 `raw[17624354]` 的 `}`**（**R175 订正**：原写 `raw[913237]` —— 错，913,237 已含该 `}`）；14 = 12 + 2 = 1 + 12 + 1。',
}
for p in (F1, F2, F3, F4):
    t = blobs[p].decode('utf-8')
    ck('B1 %s 错误指认句恰 1 次' % os.path.basename(p), t.count(WRONG[p]) == 1, t.count(WRONG[p]))
    ck('B2 %s 订正后句 0 次（防重复改）' % os.path.basename(p), t.count(RIGHT[p]) == 0, t.count(RIGHT[p]))

N1 = '''

**十一 · R175 收口时的自我订正（S-634）：那 2 B 我写错了，V557 → V558 改正.** 上文第一节我写「2 = `raw[913237]` 的 calls 收尾 `}` 与 `raw[17624354]` 的文档收尾 `}` 各 1 B」。`r175l` **25 断言 0 FAIL** 把它测反：**913,237 已把那一个 `}` 计入**（913,237 = `len(b'"calls": ')` 9 + `dumps(calls)` 913,228，末字节偏移恰 913,237），故它不可能是「净额之外多出的 2 B」的一员。**两条互斥账**钉死正解：(a) 删成员后 **913,239 = 913,238 + 1**（913,238 段 + 文档末字节 `}`）；(b) 净额 **913,237 = 913,239 − 2** ⇒ 多出的 2 B 是**首字节 `{`（raw[0]）与末字节 `}`（raw[17624354]）**。等价 14 B 分解：**1(`{`) + 12(`, "bounds": `) + 1(`}`) = 14**，逐字节 = `raw[0:1] + raw[913238:913250] + raw[17624354:17624355]`（C8 断言实测拼接相等）。三段穷尽账：913,238 + 16,711,116 + 1 = 17,624,355（C1/C2/C3）。**落盘订正**：V557 → **V558**（`r175m` **22 断言 0 FAIL**，只改 F24.limitations 这 1 处、变化单元 {4}、其余 53 行 × 5 列逐字节相同、母本一字未改）；V558 = **128,835 B** / sha256 **157996aa5da193d3ac254c9d6026343050b23f969793f83433469d5520bd8aa5** / 55 行 5 列 / CR 0，limitations **35,453 → 35,925 B**。门禁二轮重钉：`MASTER_SHA256` `e5cb63ff…` → **`b82b978aa1759520…`**（facts 差异 5 行、gate_runner 1 行，同样以「旧常量复算旧 MASTER 命中旧 pin」作硬闸），三段实跑仍全 ok、`GATE_VER` 仍 **R166**。指针同步到 **V558**（`r175h` **14 断言 0 FAIL**），并**第二次订正**其声明依据：R175 当日已在 R128 下产生 **V556/V557/V558 三份**，原「R128 下只有这一个目录」彻底失效。**S-634 的族谱**：属「把心里以为的对称当实测」—— 我按「{ ... }」的外形假设两个收尾花括号对称，而清单的净额口径**只保留 calls 成员**，根本不含外层 `{`。
'''

N2 = '''

**八 · R175 收口订正（S-634）：那 2 B 是外层 `{` 与 `}`，不是 calls 的收尾 `}`.** 上文第一节写「2 = `raw[913237]` 的 calls 收尾 `}` 与 `raw[17624354]` 的文档收尾 `}`」被我自己的 `r175l` **25 断言 0 FAIL** 测反：913,237 = 9 + `dumps(calls)` 913,228 **已含 raw[913237] 那个 `}`**。两条互斥账：删成员后 **913,239 = 913,238 + 1**；净额 **913,237 = 913,239 − 2** ⇒ 2 B = `raw[0]` 的 `{` 与 `raw[17624354]` 的 `}`。等价 14 B = 1 + 12 + 1，逐字节 `raw[0:1] + raw[913238:913250] + raw[17624354:17624355]`；三段穷尽账 913,238 + 16,711,116 + 1 = 17,624,355。落盘：V557 → **V558**（`r175m` **22 断言 0 FAIL**，只改 F24.limitations 1 处）；V558 = **128,835 B** / **`157996aa5da193d3…`** / limitations **35,453 → 35,925 B**；门禁 `MASTER_SHA256` → **`b82b978aa1759520…`**，三段实跑全 ok、`GATE_VER` 仍 R166；指针同步 V558 并第二次订正其声明依据（R128 下现有三份）。
'''

N3 = '''

PF10. 🔴 **交付七（收口订正 S-634）：那 2 B 是外层 `{` 与 `}`，不是 calls 的收尾 `}`；V557 → V558.** 上面 PF1 我写「2 = calls 收尾 `}` 与文档收尾 `}` 各 1 B」，`r175l` **25 断言 0 FAIL** 把它测反：**913,237 已把那一个 `}` 计入**（= 9 + `dumps(calls)` 913,228，末字节偏移恰 913,237），故它不可能是「净额之外多出的 2 B」。两条互斥账：(a) 删成员后 **913,239 = 913,238 + 1**；(b) 净额 **913,237 = 913,239 − 2** ⇒ 2 B = **`raw[0]` 的 `{` 与 `raw[17624354]` 的 `}`**。等价 14 B = 1 + 12 + 1，逐字节 `raw[0:1] + raw[913238:913250] + raw[17624354:17624355]`；三段穷尽账 913,238 + 16,711,116 + 1 = 17,624,355。落盘：**V558** = **128,835 B** / **`157996aa5da193d3…`** / limitations **35,453 → 35,925 B**（`r175m` 22 断言，只改 F24.limitations 1 处、变化单元 {4}）；门禁 `MASTER_SHA256` **`e5cb63ff…` → `b82b978aa1759520…`**（facts 5 行 / gate_runner 1 行，旧常量复算旧 MASTER 作硬闸），三段实跑全 ok、`GATE_VER` 仍 **R166**；指针同步 **V558** 并**第二次订正**其声明依据（R128 下现有 V556/V557/V558 三份）。**自错族谱**：S-634 属「把心里以为的对称当实测」—— 我按 `{ … }` 的外形假设两个收尾花括号对称，而净额口径只保留 calls 成员、**根本不含外层 `{`**。
'''

N4 = '''
**收口订正（S-634，同轮第四段）**：上文「判据一」里我写 2 B = `raw[913237]`（calls 收尾 `}`）+ `raw[17624354]`（文档收尾 `}`），被 `r175l` **25 断言 0 FAIL** 测反 —— **913,237 已含 raw[913237] 那个 `}`**（= 9 + `dumps(calls)` 913,228）。两条互斥账：删成员后 **913,239 = 913,238 + 1**、净额 **913,237 = 913,239 − 2** ⇒ 2 B = **`raw[0]` 的 `{` 与 `raw[17624354]` 的 `}`**；等价 14 B = 1(`{`) + 12(`, "bounds": `) + 1(`}`)，逐字节 `raw[0:1] + raw[913238:913250] + raw[17624354:17624355]`，三段穷尽账 913,238 + 16,711,116 + 1 = 17,624,355。落盘 **V558** = **128,835 B** / `157996aa5da193d3…` / limitations 35,453 → 35,925 B（只改 F24.limitations 1 处），门禁 `MASTER_SHA256` → `b82b978aa1759520…`，三段实跑全 ok、`GATE_VER` 仍 R166；指针同步 V558（R128 下现有三份，其「只有这一个目录」的旧依据第二次订正）。**族谱**：「把心里以为的对称当实测」。
'''

new = {}
new[F1] = blobs[F1].decode('utf-8').replace(WRONG[F1], RIGHT[F1]) + N1
new[F2] = blobs[F2].decode('utf-8').replace(WRONG[F2], RIGHT[F2]) + N2
new[F3] = blobs[F3].decode('utf-8').replace(WRONG[F3], RIGHT[F3]) + N3
new[F4] = blobs[F4].decode('utf-8').replace(WRONG[F4], RIGHT[F4]) + N4
for p in (F1, F2, F3, F4):
    ck('C1 %s 改后错误句 0 次' % os.path.basename(p), new[p].count(WRONG[p]) == 0, new[p].count(WRONG[p]))
    ck('C2 %s 改后订正句恰 1 次' % os.path.basename(p), new[p].count(RIGHT[p]) == 1, new[p].count(RIGHT[p]))
for p, exp in EXP_CR.items():
    ck('C3 %s 新 CR 仍 %d' % (os.path.basename(p), exp), new[p].encode('utf-8').count(b'\r') == exp,
       new[p].encode('utf-8').count(b'\r'))
ck('C4 看板新行数 < 260', new[F4].count('\n') < 260, new[F4].count('\n'))
# ★ 自错 S-635：本轮是「中段 1 处替换 + 末尾追加」，故 new 不再是 old 的**前缀**
#   （前几轮全是纯追加，我把那个性质当应然沿用）。有判别力的判据是：改点之前与之后除该点外逐字不变。
for _p, _tag in ((F1, 'R14'), (F2, 'LEDGER'), (F3, 'LOCK')):
    _o = blobs[_p].decode('utf-8')
    _i = _o.index(WRONG[_p])
    ck('C5 %s 改点之前逐字节相同（前 %d 字符）' % (_tag, _i), new[_p][:_i] == _o[:_i], _i)
    _tail = _o[_i + len(WRONG[_p]):]
    ck('C5b %s 改点之后原有内容逐字节仍在（作为 new 的中段）' % _tag,
       _tail and _tail in new[_p], len(_tail))
ck('C6 看板订正段落在末尾', new[F4].endswith(N4), True)

if fails:
    print('★ fail-closed：%d 条未过，不写盘' % len(fails))
    io.open(OUT, 'w', encoding='utf-8').write(json.dumps({'fails': fails}, ensure_ascii=False, indent=1))
    sys.exit(1)

for p in (F1, F2, F3, F4):
    raw = blobs[p]
    osha = hashlib.sha256(raw).hexdigest()
    bak = os.path.join(BASE, '%s.before_r175n_%s.bak' % (os.path.basename(p), stamp))
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(raw)
    ck('D1 %s 备份 sha 命中旧 sha' % os.path.basename(p),
       hashlib.sha256(io.open(bak, 'rb').read()).hexdigest() == osha, os.path.basename(bak))
    io.open(p, 'w', encoding='utf-8', newline='').write(new[p])
    back = io.open(p, 'rb').read()
    ck('D2 %s 回读一致' % os.path.basename(p), back == new[p].encode('utf-8'), len(back))
    ck('D3 %s 回读 CR == 期望' % os.path.basename(p), back.count(b'\r') == EXP_CR[p], back.count(b'\r'))
    print('     %-22s %d -> %d B / %d 行 / CR %d / sha %s' %
          (os.path.basename(p), len(raw), len(back), back.count(b'\n'), back.count(b'\r'),
           hashlib.sha256(back).hexdigest()[:16]))
io.open(OUT, 'w', encoding='utf-8').write(json.dumps({'fails': fails, 'assertions': n}, ensure_ascii=False, indent=1))
print('\n== %d 断言, %d FAIL ==' % (n, len(fails)))
sys.exit(1 if fails else 0)
