# -*- coding: utf-8 -*-
"""Append §553: hy4free promoted to top of the backup chain (guarded)."""
import subprocess
import sys

LEDGER = r"D:/Project/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md"
REPO = r"D:/Project/ra2-campaign-forge"
TAG = "## \u00a7553"

head = subprocess.run(
    ["git", "show", "HEAD:lead/GOAL_THREE_TARGETS_20261018.md"],
    cwd=REPO, capture_output=True).stdout.replace(b"\r\n", b"\n")
wt = open(LEDGER, "rb").read()
if TAG.encode("utf-8") in wt:
    print("REFUSE: %s already present" % TAG)
    sys.exit(1)
if not wt.startswith(head):
    print("REFUSE: not a prefix extension of HEAD")
    sys.exit(1)
print("guards OK; head=%d wt=%d" % (len(head), len(wt)))

SECTION = """
## §553 · 备选链补入 hy4free 并置于最高优先级（2026-11-05 用户令·补述）

> **本节的地位**：用户 2026-11-05 补述，**取代 §552 的二路表述**。
> §552 写的「备选只有 gemini 与 deepseek 两条」**不完整**，本节补正为三路。

### 一、用户令原文

> 「推进任务的模型还可以使用 HY 4 free 这个优先级比其他两个高一点，
> 用完这个之后再用 Gemini 和 DeepSeek。」

### 二、订正后的完整回退链

```
推进首选 : account:bigmodel-start-plan/GLM-5.3-Flash      ← 仅 23:00–09:00
备选 1   : magpie/work/cn:hy4free                          ← ★ 优先级最高（本节新增）
备选 2   : magpie/antigravity/gemini-3.8-flash
备选 3   : new-provider/cn:deepseek-v4.1-flash             （disabled 则跳过）
仅裁决   : magpie/codex/gpt-6.1-sol
```

**纪律（沿用 §552，扩为三路）**：
1. **严格按优先级回退**：hy4free 能用就用 hy4free，不可用才降 gemini，再降 deepseek。
2. **串行不并发**：同一时刻只允许一个推进工作流在飞。
3. **报错即换下一路**，不等退避、不重试同一模型。
4. **降档后高档恢复，下一轮回到最高可用档**。
5. 三路全不可用 → **停下列给用户**，不自行换被禁模型。
6. 裁决工作流（`magpie/codex/gpt-6.1-sol`）不受串行限制。

### 三、为什么 §552 漏了它

我在 §552 把「备选只有两条」写成了定论，依据是**我自己上一轮实际用过的通道**，
而不是「用户授权可用的通道全集」。
这是**把「我用过的」当成「可用的」**——与 §551 同类的方法错误：
拿现状当规范，不去核用户原始授权。

**订正**：`magpie/work/cn:hy4free` 其实早就在 `ListModels` 在册，
而且 **2026-11-04 就用它跑过 `dwfrun-5e41dc78`（D-15/D-13 落实，21,101,230 tokens）**——
它是本线**跑过最大产出**的一路推进通道，我却在新纪律里把它漏掉了。

### 四、当前在飞（本节落笔时，未受本节影响）

| run | 完整模型 ID | 通道位次 | 状态 |
|---|---|---|---|
| `dwfrun-65734a63` | `magpie/antigravity/gemini-3.8-flash$high` | 备选 2 | running（N16-4，已过目视阶段 6.16M tokens） |

**该趟不打断**——它已经跑过目视阶段并产出 25 行表，中途换模型会丢掉工作。
**下一轮新派任务起，按本节的新优先级选通道。**

### 五、诚实账

1. 这是**用户第三次订正我的派发层配置**（供应商 §551 / 并发 §552 / 优先级 §553）。
   三次都是同一类问题：**我拿现状或我的理解当规范，没有回原始授权核对**。
2. 本节**未 commit**；**零真机**；**未改任何母本**。
3. 已在飞的一趟不重启——纪律是「下一轮用新规则」，不是「立刻推翻在跑的工作」。
"""

with open(LEDGER, "ab") as f:
    f.write(SECTION.encode("utf-8"))
print("appended %d bytes" % len(SECTION.encode("utf-8")))
