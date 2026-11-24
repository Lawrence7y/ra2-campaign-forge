#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""write_r120b_amend.py —— 审计复核后对 LEDGER / LEAD_LOCK / STATUS_BOARD 的就地更正。"""
import hashlib
import io
import os
import subprocess
import sys
import time

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
STAMP = time.strftime('%Y%m%d_%H%M%S')
T = {
    'LEDGER': (os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md'), 337),
    'LEAD_LOCK': (os.path.join(ROOT, 'lead', 'LEAD_LOCK'), 137),
    'STATUS_BOARD': (os.path.join(R14, 'STATUS_BOARD.md'), 0),
}

SEG_LEDGER = """- **跨家族审计后两处就地更正（hy4 task 224，7 条全成立，`_r120/r120f` 7/7 PASS）**：① 我原写「三种边界判据在 60 站点上无一相同（60/60 分歧）」——**撤回**：两两矩阵实测 int3pad 与另两者各 0/60，而 **calltarget 与 nearest_entry 60/60 完全相同**，分歧全由「整段 vs 子函数」的粒度差驱动；「对判据敏感」仍成立，但支撑量是函数数 55 vs 74、占比 100% vs 93.24%。② 我原把 Fisher **双尾 0.05456** 读成「无判别力」——**过强**：单尾（右）**0.03116**，方向有利于「专门用该接口」，改为「方向性但不显著」。
- **审计给出我没找到的量，我复算 60/60 成立并再加一量**：站点后 10 字节 COM 虚调用模板，0x7f7c80 **60/60** 命中、11 个 IID 中**唯一**（0x7f7c90 0/56、0x818858 0/16、0x817bc0 1/9）；再加虚表槽量：60 个站点**全部** `call [ecx]` = **槽 0（QueryInterface）**，站点 +1 处起算解析出 **0/60**（反控）。⇒ L3 表述由「未排除且零独立支撑」升级为「**未排除，但有两条不依赖函数边界的方向性证据**」。
- **C17 的边界（审计 A2/A3/A4/A5）**：A2 误伤面真实存在（跨轮汇总表 / 追溯补跑产物会落在高轮次目录却诚实声称低轮次）；A3 C17b 命中的 {3,22,27,28} ⊆ C17a 的 {3,4,22,27,28} ⇒ 本盘**冗余**（同证据二次编码），误伤成本真实；A4 PIN sha 可复现 ⇒ 同改 PIN+sha+行可无声通过，**C17 弱于 C14**（C14 绑原文，C17 绑派生集合）；A5 三类异常不崩溃但「跳过的行」只经集合变小间接体现，可观测性不足未修。
"""

SEG_LOCK = """
EM13. **跨家族审计（hy4 task 224，54 回合 / 4.9 分钟 / 无 OVERTIME）7 条全成立**，`_r120/r120f_recompute_audit.py` **7/7 PASS** 逐条复算。两条直接推翻我上面的文字，**已就地改写 §2.124.4 而不是只在末尾记一笔**：

- **更正 A（B1）**：我写「三种判据 60/60 分歧」——撤回。两两矩阵：int3pad vs afterterm 0/60、int3pad vs calltarget 0/60、int3pad vs nearest 0/60、afterterm vs calltarget 2/60、afterterm vs nearest 2/60、**calltarget vs nearest 60/60 相同**。⇒ 分歧全由 int3pad 这个「整段」判据驱动，我把它当成了统计量不稳健。**这是本轮最严重的一条自错（S-85：把自己的两个细粒度判据之一误当第三方反证）。**
- **更正 B（B2）**：双尾 p=0.05456 读成「无判别力」过强；单尾（右）**0.03116**，方向有利于「专门接口」。改为「方向性但不显著」。

EM14. **审计 B3 给了我没找到的量，我复算成立，并再加一个量**（`_r120/r120g_slot_census.py` 4/4 PASS）：① 站后 10 字节 COM 虚调用模板：0x7f7c80 **60/60**（37 个 `push; push eax; mov ecx,[eax]; call [ecx]` + 23 个顺序互换），11 个 IID 中**唯一**全中（0x7f7c90 0/56、0x818858 0/16、0x820270 0/8、0x817bc0 1/9、0x87da00 0/1）。② 虚表槽：60 个站点**全部** `call dword ptr [ecx]` = **槽 0 = QueryInterface**，解不出 0 个；对照 0x7f7c90 的 56 站点里解出槽的仅 1 个（且是 IAT 直调 0x7e15fc，非虚表）。反控：imm32 逐个核对 0 个不符；站点 +1 处起算模板解析 **0/60**。⇒ **两条都不依赖函数边界**。但**仍不排除通用包装器**（包装器也能用同一模板对一组 IID 发 QI）⇒ L3 表述由「未排除且零独立支撑」改为「**未排除，但有两条方向性证据**」。

EM15. **C17 的四处限制（审计 A2/A3/A4/A5 成立，本轮不修，如实登记）**：A2 误伤面真实 —— 跨轮汇总表或追溯补跑产物会落在高轮次目录却诚实声称低轮次（本盘 5 条经 R90 独立证据判为复制粘贴，不属此列）；A3 C17b 命中的 id {3,22,27,28} ⊆ C17a {3,4,22,27,28} ⇒ **本盘冗余**（同证据二次编码），规则层面不冗余但误伤成本真实；A4 `C17_PIN_SHA256` 可用「排序三元组换行拼接」复现 ⇒ 同改 PIN+sha+行可无声通过，**C17 弱于 C14**（C14 绑自由文本原文）；A5 三类异常不崩溃（`isfile`+`continue`、`errors='replace'`），但「跳过的行」只经集合变小间接体现 —— 可观测性不足，未修。

EM16. **自错再添 3 条（S-82..S-84）**：S-82 `r120g` 只取站点后 3 条指令而模板是 4 条 ⇒ 60/60 假「解不出」；S-83 `r120e` 的 S3 把「分歧数 >= 30」写成**要满足的条件**，方向反了（该现象正是要被推翻的）；S-84 我在审计卡 B3 里默认写「找不到就写找不到」，预设了结论，而它实际找到了。**累计本轮自错 15 条（S-70..S-84）**。

EM17. **轮末断言总数更新**：r120a 9 / r120b 6 / r120c 10（连跑两次一致）/ r120d 11 / r120e 8 / r120f 7 / r120g 4 = **55 项全 PASS**。五项 CR 全绿；`check_disc.py` exit 0（GATE_VER=R120，C16 已按设计重钉 §2.124：9,325→15,096 B，floor 2,331 B，sha `d12079c2bf623622`）。
"""

SEG_BOARD = """
### 八 · 跨家族审计后两处就地更正（hy4 task 224 · 7 条全成立 · `r120f` 7/7 PASS）

| 我原写 | 复算结果 | 处置 |
|---|---|---|
| 「三种边界判据在 60 站点上无一相同（60/60 分歧）」 | 两两矩阵：int3pad 与另两者各 **0/60**；**calltarget 与 nearest_entry 60/60 相同** | **撤回**，已改 §2.124.4；「对判据敏感」改由函数数 55 vs 74、占比 100% vs 93.24% 支撑 |
| 「Fisher p=0.0546 ⇒ 无判别力」 | 双尾 0.054562、**单尾（右）0.031160**，方向有利于专门接口 | 改为「**方向性但不显著**」 |
| 「没找到第二个不依赖函数边界的量」 | 审计给出站后模板量：0x7f7c80 **60/60**、11 个 IID 中唯一 | 复算成立，再加虚表槽量 |

**再加一个量（不依赖函数边界）**：60 个站点**全部**是 `call dword ptr [ecx]` = **槽 0 = QueryInterface**；站点 +1 处起算解析出 **0/60**（反控非恒真）。

⇒ L3 由「未排除且零独立支撑」改为「**未排除，但有两条方向性证据**」。仍**不排除**通用包装器（包装器也能用同一模板发 QI）。

### 九 · C17 的四处限制（审计 A2/A3/A4/A5，成立但本轮不修）

- A2 误伤面真实：跨轮汇总表 / 追溯补跑产物会落在高轮次目录却诚实声称低轮次。
- A3 C17b 命中的 {3,22,27,28} ⊆ C17a 的 {3,4,22,27,28} ⇒ **本盘冗余**（同证据二次编码），规则层面不冗余但误伤成本真实。
- A4 `C17_PIN_SHA256` 可复现 ⇒ 同改 PIN+sha+行可无声通过；**C17 弱于 C14**（C14 绑原文，C17 绑派生集合）。
- A5 三类异常不崩溃（`isfile`+`continue`、`errors='replace'`），但「跳过了哪些行」只经集合变小间接体现，可观测性不足。

**自错再添 S-82..S-84（累计 S-70..S-84 共 15 条）**：S-82 只取站后 3 条指令而模板 4 条；S-83 把「要被推翻的现象」写成要满足的断言；S-84 审计卡预设「找不到」。**断言总数 55 项全 PASS。**
"""


def main():
    for k, (p, cr) in T.items():
        b = io.open(p, 'rb').read()
        assert b.count(b'\r\n') == cr, (k, b.count(b'\r\n'), cr)
        dst = os.path.join(BASE, '%s.before_R120_amend_%s.bak' % (os.path.basename(p), STAMP))
        with io.open(dst, 'xb') as f:
            f.write(b)
        assert hashlib.sha256(io.open(dst, 'rb').read()).hexdigest() == hashlib.sha256(b).hexdigest()
        print('backup', os.path.basename(dst))
    for name, seg, cr in (('LEDGER', SEG_LEDGER, 337), ('LEAD_LOCK', SEG_LOCK, 137),
                          ('STATUS_BOARD', SEG_BOARD, 0)):
        p = T[name][0]
        old = io.open(p, encoding='utf-8', newline='').read()
        assert '\r' not in seg
        new = old + seg
        io.open(p, 'w', encoding='utf-8', newline='').write(new)
        got = io.open(p, encoding='utf-8', newline='').read()
        assert got == new
        crn = io.open(p, 'rb').read().count(b'\r\n')
        assert crn == cr, (name, crn, cr)
        print('%s +%d B CR=%d lines=%d' % (name, len(seg.encode()), crn, len(got.split('\n'))))
    r = subprocess.run([sys.executable, os.path.join(R14, 'check_disc.py')], cwd=R14,
                       capture_output=True, text=True, timeout=300)
    print('gate exit', r.returncode)
    assert r.returncode == 0, (r.stdout or '')[-1200:]


if __name__ == '__main__':
    main()
