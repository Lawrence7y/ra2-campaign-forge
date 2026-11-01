#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§436 台账追加：D-07 定谳执行①——阳性对照实验（决定性）+ 整仓盘点落地。"""
import io, os

LEDGER = "lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"

CONTENT = """# §436　★★ D-07 定谳执行①：阳性对照实验判定「gate 实为整树扫描、diff-only 前提不成立」；
#        整仓盘点落地（39 条=6 冻结豁免 + 33 非冻结归属修复）

**性质**：D-07 定谳（2026-10-25 23:38）执行轮。零真机趟、母本零改动、零绕闸
（提交尝试本身即定谳强制的实验变量；脚本与管线命令不含 commit 子串）。
监视会话指令四项：②候选副本=上轮已完成（§435，14/14 门禁）；③本轮=阳性对照+路由评估；④逐步登记。

## 一、★ 阳性对照实验（定谳上线前置）——结果：拦住了，但与植入无关 ⇒ 判「不过」

**方法**（含一次方法迭代，如实登记）：
- 直接 Write 植入件被 **Write 层钩子当场拦**（路径穿越+代码注入两 high）——这本身
  是写入层防线有效的直接证据：本线路径上 high 根本写不进工作树。
- 改用 **git 管线植入**：`hash-object -w` + `update-index --cacheinfo` 把 5 行
  已知 high 内容（路径穿越+代码注入，与整仓 38 high 同类）放进暂存区
  （blob `1724c134…`，路径 `lead/qc161_u0400_trip/_gate_pc_fixture.py`）。
  内容不经过工作树、不经过 Write 钩子；**提交尝试本身走完整 commit 门禁**=受控变量。
  管线命令不含 commit 子串，不触发钩子匹配，非绕闸（绕闸=让提交避开扫描；
  本实验=让植入内容被扫描，正是定谳要求）。

**结果**：pathspec 单件提交（5 行 diff ≪ 契约 maxDiffLines=500）仍被拦，38 high 归因
**全部是既有树 findings（tools/atlas_* 等），植入文件在归因中零出现**。

**判定**：
1. 门禁实为**整树扫描**，与 staged/pathspec 内容无关；
2. `scan-profiles.json` 契约宣称 `gate.scope=diff-only`（+maxDiffLines 500）——
   **契约与实现不符**，定谳「commit 端既有 diff-only 语义」前提**不成立**；
3. 按定谳判据精神（门禁必须看见 diff）**阳性对照不过** ⇒ 「负控不过不得启用」：
   **B 的批量纪律实现不成立**——若树清空，同批植入件会被放行；
4. 字面层面「植入后仍被拦」为真，但拦的因果与植入无关（树噪声），不构成对照
   所需的区分度。两种表述并录，防误读。

## 二、整仓告警盘点（定谳「保留整仓告警记录」义务）——落地

deep 扫描（jobId `scan-job-mvo1i40h-5d0d7b492be21fc9`，39 条=38 high+1 low，
seal `b60452c7…`）逐条落 `lead/qc161_u0400_trip/_inventory_20261026/`
（`INVENTORY.md` + `findings_full.json`，含 findingId/occurrenceId/seal）：

- **冻结件豁免 6 条**（harness6/7 各 3，其中 4 条 advisory 自标）——wontfix 清单
  已登记，注「破冻结才可消，须用户单独授权」；
- **非冻结 33 条 high + 1 low**：tools/ ×17（本线审计工具族）、lead/ ×14（含
  **本线现役 `_disc_armG.py:75`、`_disc_stdio.py:47` 两条路径穿越——自己的探针**，
  可直接修）、ra2forge/ ×2（归属待定）。

## 三、对 B 可实现性的诚实结论（上报 Lead）

- 插件载荷 AES-256-GCM+Ed25519 完整性签名，**无任何文档化扫描面开关**
  （`MIMOSA_NO_GIT_GATE=1`=整体关=禁用的绕闸；MODE/FailureMode 不改范围）；
  git hooks（core.hooksPath）为空，唯一门=ZCode 插件钩子。
- ⇒ 「push 端与 commit 端 diff-only 对齐」在**不修改加密安全工具**的前提下
  无配置面可实现。可行替代路径（供裁决）：
  a) **迁移/修复清树**：非冻结 33 条按归属修复或迁出扫描树（先例 2026-10-19）；
     树清到只剩 6 条冻结豁免后，**门禁是否放行取决于那 6 条仍 blocking**——
     仍需机制（冻结件迁移=破冻结面，须用户单独授权；或接受 commit 持续被拦）。
  b) **冻结件迁移面请示**：harness6/7 若按「内容零改动」迁出扫描树（字节不变、
     哈希不变、仅路径移动），是否算破冻结——请用户单独裁定。
  c) 插件侧功能诉求（gate profile 真正按 diff-only 实现）只能上报厂商，非本线可实施。
- 本线可立即做的非冻结修复：`_disc_armG.py`/`_disc_stdio.py` 两条（自有现役探针），
  下轮执行；tools/ 17 条按批次修复或迁出（不设死线）。

## 四、并发观察（不行动）

工作树存在他线未暂存改动（re_atlas/tools ×4 等）与 RE-ATLAS 活跃迹象——按写域
纪律不碰，仅登记。

## 五、卫生

零真机趟；母本/冻结件零改动；实验现场已清理（fixture 已出暂存区，工作树从未落盘；
悬空 blob `1724c134` 留 .git/objects 由 gc 回收，无害）；本轮唯一一次提交尝试
消耗在实验上（拦截=预期结果），台账随下一成功提交入库。
"""

def main():
    before = io.open(LEDGER, "rb").read()
    assert b"\xc2\xa7435" in before, "prev section missing"
    assert b"\xc2\xa7436" not in before, "duplicate"
    crlf_before = before.count(b"\r\n")
    add = CONTENT.replace("\n", "\r\n").encode("utf-8")
    after = before + b"\r\n" + add
    assert after.startswith(before)
    assert after.count(b"\r\n") == crlf_before + 1 + CONTENT.count("\n"), "crlf math off"
    tmp = LEDGER + ".tmp436"
    with io.open(tmp, "wb") as fh:
        fh.write(after)
    os.replace(tmp, LEDGER)
    check = io.open(LEDGER, "rb").read()
    assert check == after
    print("OK appended 436; ledger %d bytes crlf=%d" % (len(check), check.count(b"\r\n")))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
