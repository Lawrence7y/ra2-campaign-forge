#!/usr/bin/env python3
# R142 F: 事故留痕 + 勘误（追加式，全部 CR 不变）
#   OA12  -> LEAD_LOCK   记两次事故（看板超限被回退 / 新节 unpinned 后按设计重钉 C16）
#   §1197 -> LEDGER      勘误：R141 §1195 的「v5.34 起是 33」机制描述需补一层
#   §2.147-> R14_COMMON  同上，且记「先数余量再写篇幅」这条操作纪律
import hashlib
import io
import json
import os
import time

ROOT = '/home/t628/projects/ra2-campaign-forge'
BASE = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BL = os.path.join(BASE, 'R17_LEAD_BASELINE')
F_LCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
F_LED = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
F_R14 = os.path.join(BASE, 'R14_COMMON.md')
OUT = os.path.join(ROOT, '_r142', 'r142f_erratum.json')

cc, cc_n = [], 0


def ck(name, cond, detail=''):
    global cc_n
    cc_n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond:
        cc.append(name)


def append(path, text, tag, expect_cr):
    old = open(path, 'rb').read()
    before = dict(cr=old.count(b'\r'), lf=old.count(b'\n'), bytes=len(old),
                  sha=hashlib.sha256(old).hexdigest())
    ck('[%s] 写前 CR == %d' % (tag, expect_cr), before['cr'] == expect_cr, before['cr'])
    # wx 独占备份
    dst = os.path.join(BL, '%s.before_%s_%s.bak'
                       % (os.path.basename(path), tag, time.strftime('%Y%m%d_%H%M%S')))
    with io.open(dst, 'xb') as f:
        f.write(old)
    ck('[%s] 备份 wx 独占且逐字节相同' % tag, open(dst, 'rb').read() == old,
       os.path.basename(dst))
    data = old + text.encode('utf-8')
    with io.open(path, 'wb') as f:
        f.write(data)
    back = open(path, 'rb').read()
    after = dict(cr=back.count(b'\r'), lf=back.count(b'\n'), bytes=len(back))
    ck('[%s] 回读 == 期望' % tag, back == data)
    ck('[%s] 纯追加' % tag, back.startswith(old))
    ck('[%s] CR 保持 %d' % (tag, expect_cr), after['cr'] == expect_cr, after['cr'])
    return before, after


LCK = """
OA12. 🔴 **本轮两次事故都留痕，且都不是「判据错了」（收口后补记）.** ① **看板超限被回退**：首版第 142 轮条目 **83 行**，225 + 83 = **308 > 300**，写入后回读断言当场 FAIL，文件保持 225 行、sha `8124bdcb` **未变**（没有留半截状态）；后来我实测自己的精简版是 **74 行**（225 + 74 = **299**），而我当时在正文里写成「压到 50 行内」—— 这句错在收口复查时被抓出并已就地改正（看板第 282 行现为「本版实测 74 行」）。**教训不是「要写短」，是顺序反了：应先知余量（300 − 当前行数）再定篇幅，我是写完才数。** ② **新节 unpinned 后按设计重钉**：加 §2.146 后 C16 报 `unpinned 1` —— 表外新节默认吃 `C16_NEW_MIN=0`，等于白得一张永久免检票（与 C11 的 claims-none 同构）。补 `146: 8400`（实测该节 **8,421 B**，留 21 B 余量）后 C16d 立刻报 `TAMPERED`，**这正是它该有的行为**；我按设计重钉 `C16_FLOORS_SHA256` 为 `546dbdf7947b6ecc…`。**重钉前先验证方法能复现旧值**：把 146 项去掉重算得 `4e1c4e32a323af20`，与旧常量逐字符相同 ⇒ 我改的是钉、不是判据。两次事故**都由断言/门禁当场抓住**，没有一条进结论。
"""

LED = """
## §1197 R142 勘误 · §1195 那句「v5.34 起是 33」的机制描述缺一层：F35 不是从无到有，是从「全失联桶」跳进「部分失联桶」（v530..v533 的 partial 恰等于外部 32 条，而全失联是 2 条）

对 §1195（R141）的一条**加强兼勘误**，不是推翻。**加强**：R141 只有「外部用 v5.33 所以给 32」这一条推断，R142 把盘上**全部 10 版**（v530..v539）逐一重算，观测到 partial 计数序列 **32,32,32,32,33,33,33,33,33,33** —— **只有 1 个跳变点**（v533→v534、+1），集合差**进入 {F35}、退出 0 条**，故「v5.34 起是 33」这个时间点**实测成立**。**勘误**：R141 把 F35 的迁移叙述成「补成 5 条后变部分失联」，读者会以为它此前不在任何桶里；实测 F35 在 v530..v533 属**全失联桶**（`evidence_paths` 仅 1 条且该条不在盘），v534 补成 5 条（4 在盘）后才**从全失联跳进部分失联** ⇒ 漂移的是**分界**：全失联 **2→1**、部分失联 **32→33** **同步移动**、全活恒 **20** 不动、三桶合计恒 **54**。⇒ 引用纪律因此要成对写：**「部分失联 33」与「全失联只有 F23」都只在 ≥v5.34 成立**（盘上 10 版有 4 版给 32，且那 4 版的全失联是 `[F23, F35]`）。另：本轮未改 §1195 一字，勘误以本节追加方式存在。
"""

R14 = """
## 2.147 R142 勘误 · §2.146 第四节那句「从无到有」需改成「从全失联桶跳进部分失联桶」；并立一条操作纪律「先数余量再写篇幅」

**一 · 勘误对象与方法。** §2.146 第四节已写「F35 在 v530..v533 不是不存在，而是在全失联桶里」，但同节把漂移概括为「不是『F35 从无到有』」时**没有给出那 4 个版本的全失联计数**，读者无法自证。本节补齐可复算的一行：v530..v533 的 **partial 恰 32、全失联 2（`[F23, F35]`）、全活 20**；v534..v539 的 **partial 33、全失联 1（`[F23]`）、全活 20**。三桶合计**恒 54**（54 行全部有路径，无 no-paths 行）⇒ **漂移的量只在「全失联」与「部分失联」之间的那一条分界上，两条各移动 1、方向相反**。

**二 · 为什么这条值得单列一节。** 因为它是**唯一一处「R141 的结论方向对、机制描述不全」**的地方，而这类误差最容易在下游被放大：若有人照 §2.146 的旧说法理解为「F35 是新增的失联件」，就会去追一个不存在的「删除动作」；实测它一直有 1 条路径声明，只是那条路径不在盘。⇒ **失联件的「新增」与「改档」必须分开叙述**，这也是本轮 S-288 那条自错的来源（我断言「全失联恒 `[F23]`」，实测是 `[F23, F35]`，是断言把这条挖出来的）。

**三 · 操作纪律（本轮事故 1 的产物，可复用）。** 写看板段之前**先算余量**：`余量 = 300 − 当前行数`，再按余量定篇幅；不要写完再数。本轮首版条目 83 行、225 + 83 = **308 > 300**，被回读断言当场拦下并回退（sha `8124bdcb` 未变，无半截状态），精简版实测 **74 行**（225 + 74 = **299**）。同一条纪律对四件套里任何有行数上限的文件都适用（`STATUS_BOARD` <= 300 是硬红线，`BOARD_ARCHIVE` 无上限但 CR 必须是 2952）。

**四 · 未改动的部分。** §2.146 的 T1/T2 判别力结论（18/32 与确定性基线 18.0 相等、p=1.0000；T2 24/32、p<0.0001、残余 8 条）、路径层 131 条全对账、F39/F49 决定性反例、`lost_primary` 列不完整这四项**逐字不动**，本节只补第四节的一层机制与一条纪律。
"""

b1, a1 = append(F_LCK, LCK, 'r142F_LEADLOCK_OA12', 137)
lck = open(F_LCK, 'rb').read()
ck('LEAD_LOCK 含 OA12', b'OA12.' in lck)

b2, a2 = append(F_LED, LED, 'r142F_LEDGER_1197', 337)
led = open(F_LED, 'rb').read()
ck('LEDGER 含 §1197', '§1197'.encode() in led)
ck('LEDGER 仍含 §1196', '§1196'.encode() in led)

b3, a3 = append(F_R14, R14, 'r142F_R14_2_147', 1081)
r14 = open(F_R14, 'rb').read()
ck('R14_COMMON 含 2.147', '## 2.147'.encode() in r14)
ck('R14_COMMON 仍含 2.146', '## 2.146'.encode() in r14)
ck('R14_COMMON 仍含 2.145', '## 2.145'.encode() in r14)

json.dump(dict(lead_lock=[b1, a1], ledger=[b2, a2], r14=[b3, a3],
               cc_checks=cc_n, cc_fails=cc),
          io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n=== 收口：正控 %d 项 / FAIL %d ===' % (cc_n, len(cc)))
if cc:
    print('FAILS:', cc)
