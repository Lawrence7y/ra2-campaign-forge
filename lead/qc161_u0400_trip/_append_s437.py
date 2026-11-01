#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§437 台账追加：D-07 B 案 git 层落地 + 双对照实证 diff-only + 外层残墙上报。"""
import io, os

LEDGER = "lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"

CONTENT = """# §437　★★ D-07 B 案落地：原生 git 门禁（pre-commit/pre-push）双对照实证 diff-only；
#        ZCode Bash 层钩子=唯一残墙（整树扫描不让位，上报插件侧/用户）

**性质**：D-07 定谳执行②（监督会话重启令后继续；上轮被 GLM 限流中断 35 分钟）。
零真机趟、母本/冻结件零改动、零绕闸（本轮唯一提交尝试=外层行为验证，被拦=预期）。

## 一、配置面探查结论（三层全查）

1. **README 文档化 env**：`MIMOSA_NO_GIT_GATE=1`=整体关（禁用的绕闸，不采用）；
   MODE/FailureMode 只改处置不改扫描面——**无扫描面开关**。
2. **git hooks**：`core.hooksPath` 空、`.git/hooks` 仅 sample——门禁唯一载体=ZCode 插件钩子。
3. **★ CLI 命令面**（`payload/dist/cli.js --help`，README 未载）：`git-gate <install|status|uninstall>`
   （原生 Git 门禁）、`policy <init|check>`（项目安全策略）、`ledger <record|list|show>`
   （跨会话 finding 状态）、`scan --json-batch`（**增量 gate 批处理**）。
   - `policy init` 生成 `.mimosa/security-policy.json`=**被扫代码的威胁模型语义**
     （allowedWriteRoots 等），非扫描面路由；init 后 gate 计数 38→40
     （VERIFY_A8 每处被「代码注入+Shell 执行策略违反」双规则各计）。
   - ledger 不跳过 deny（文档明示「不会跳过本轮扫描或写入前 deny」）——挂账≠放行。

## 二、★ B 案落地：`mimosa git-gate install`

安装 `.git/hooks/pre-commit|pre-push`（bash 包装器 → `cli.js git-gate run --hook …
--repo … --mode deny`；高危阻断模式；已有 hook 先行保留）。status 由「·」转「✓」。

## 三、判别实验 + 双对照（全部直接 `git-gate run`，不消耗提交尝试）

| 实验 | 暂存集 | 结果 | 判定 |
|---|---|---|---|
| 判别 | 227 件（含 2 件真实 high） | **仅归因 2 件**（`_disc_armG.py:75`/`_disc_stdio.py:47`），树 38 条不可见 | **真 diff-only**（只扫 staged diff） |
| 阳性（拦对） | 同上 | rc=2，归因恰为暂存中的 high 两件 | **植入/暂存 high 必现于归因** ✓（复跑可重复） |
| 阴性（放行） | 2 件出暂存 | 127 个变更源码文件全查、零阻断、rc=0 | 干净暂存集放行 ✓ |
| pre-push（push 端） | 待推提交 diff | 扫 **6 个变更源码文件**（当前两笔未推提交内容），放行 rc=0 | push 端扫待推 diff，与 commit 端对齐 ✓ |

⇒ **B 案在 git 层完整落地**：扫描面=staged 集（commit）/待推 diff（push），
「被拦≠拦对」判据（补释③）满足——归因含植入/暂存 high 本体。

## 四、外层残墙（上报插件侧/用户）

ZCode Bash 层 PreToolUse 钩子（加密 git-gate-hook.mjs）**仍整树扫描且不让位**：
本轮提交尝试（pathspec=两件历史探针，预期被原生层拦对）仍被外层以 40 high 拦下
（=树 findings，与暂存无关）。载荷 AES-256-GCM+Ed25519 密封、无扫描面配置。
⇒ 本线经 ZCode 的提交暂仍被外层拦；**git 层已就绪**——外层解除（插件侧关停该
PreToolUse 钩子、或厂商让 host 钩子 defer 原生门禁）后即全通，无需再改任何东西。
附：RE-ATLAS §409 口径「commit 走 diff-only、push 走整仓」与本线 ZCode 层三实验
（commit/push 皆树扫）不一致——两层混测所致，本节以直接 `git-gate run` 判别实验为准。

## 五、D-06/D-07 收尾（监督令）

- PENDING 条目已删（D-06/D-07），「已裁决记录」区补两条登记语（D-07=执行详情+残项
  上报；D-06=C 归 RE-ATLAS 线，本线零动作）；两条 SYNCPOINT 历史信标保留。
- 删除+登记按协议应同提交入库——外层残墙在，落工作树随首个成功提交。

## 六、卫生

零真机趟；冻结件/母本零改动；本轮无提交尝试消耗（gate 实验全是直接 CLI 调用）；
工作树中 `_disc_armG.py`/`_disc_stdio.py` 两件保持暂存（真实交付件，其 high 为
真实历史探针模式，归属线修复/迁出时按补释②办理）。
"""

def main():
    before = io.open(LEDGER, "rb").read()
    assert b"\xc2\xa7436" in before, "prev section missing"
    assert b"\xc2\xa7437" not in before, "duplicate"
    crlf_before = before.count(b"\r\n")
    add = CONTENT.replace("\n", "\r\n").encode("utf-8")
    after = before + b"\r\n" + add
    assert after.startswith(before)
    assert after.count(b"\r\n") == crlf_before + 1 + CONTENT.count("\n"), "crlf math off"
    tmp = LEDGER + ".tmp437"
    with io.open(tmp, "wb") as fh:
        fh.write(after)
    os.replace(tmp, LEDGER)
    check = io.open(LEDGER, "rb").read()
    assert check == after
    print("OK appended 437; ledger %d bytes crlf=%d" % (len(check), check.count(b"\r\n")))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
