# -*- coding: utf-8 -*-
"""Append §551: model-routing error correction (idempotency-guarded)."""
import subprocess
import sys

LEDGER = r"D:/Project/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md"
REPO = r"D:/Project/ra2-campaign-forge"
TAG = "## \u00a7551"

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
## §551 · 派发纪律事故：用错 GLM 供应商一整天（2026-11-05）

> **本节的地位**：**用户指正后的错误登记**，不是自我发现。
> 本节记的是**派发层的纪律错误**，不是分析结论错误——它不影响 §545–§550 的任何数据，
> 但影响「这些结论由谁产出、花了谁的额度」。

### 一、错在哪

用户 2026-11-04 指定「推进任务首选 = Star Plan 的 GLM 5.3 Flash」。
我从 2026-11-04 夜间到 2026-11-05 上午，**所有推进工作流都派到了 `new-provider-2/glm-5.3-flash`——那是 MUZE 供应商**，
不是 Star Plan。

**根因**：`ListModels` 里两个模型名字几乎一样，我只看了模型名没看供应商前缀：

| 我用的（错） | 应该用的（对） |
|---|---|
| `new-provider-2/glm-5.3-flash` — **muze** | `account:bigmodel-start-plan/GLM-5.3-Flash` — **Start Plan** |

**我甚至在自己的定时任务提示词里把它写成了「`new-provider-2/glm-5.3-flash`（Star Plan / MUZE）」**——
把两个供应商写进同一个括号里，说明我当时就没分清，还把混淆**固化进了指令**。

### 二、连带犯的第二个错：定时点选在限时窗关闭时刻

Star Plan 是**限时套餐，只在每天 23:00–次日 09:00 可用**。
我把每日定时任务设在 **09:00** ——**正好是窗口关闭那一刻**。
即使供应商 ID 写对了，这个任务也永远跑不起来。

已于 2026-11-05 改为 **`0 23 * * *`**（窗口开启时刻），并在提示词里写明窗口约束。

### 三、造成的实际损失

| 项 | 数量 |
|---|---|
| 用错供应商的推进工作流 | `dwfrun-72de3cd1`（1h38m，8,373,384 tokens，MUZE 额度） |
| 卡死 44 分钟零产出的推进工作流 | `dwfrun-6d377b41`（0 tokens，模型未响应） |
| Star Plan 额度被正确使用 | **0** |

`dwfrun-72de3cd1` 的**产出是有效的**（26 条主张 CONFIRMED，§548 已采信），
但**花的是 MUZE 的额度，不是用户指定的 Star Plan**。

### 四、订正后的模型分工（写死，不得自行更改）

```
推进首选 : account:bigmodel-start-plan/GLM-5.3-Flash     ← 仅 23:00–09:00
推进备选 : magpie/antigravity/gemini-3.8-flash
         → new-provider/cn:deepseek-v4.1-flash           （ListModels 标 disabled 则跳过）
仅裁决   : magpie/codex/gpt-6.1-sol
禁止派发 : magpie/qoder-cn/qfmodel
           magpie/antigravity/gemini-4-argon
           magpie/antigravity/claude-opus-5-5
           magpie/antigravity/claude-sonnet-5-5
           new-provider-2/*（MUZE 系，含 glm-5.3-flash / glm-5.3-flashx）
           new-provider/cn:glm-5.3-flash
```

**新增铁律**：工作流里模型一旦报错，**立刻换模型重派**，不等、不重试同一模型、不空等退避。
（§548 那次 1h38m 的 `server_error` 空等，就是这条缺失的直接后果。）

### 五、已做的处置

1. `automation-2e18874e`：`cron` 由 `0 9 * * *` 改为 **`0 23 * * *`**；提示词重写，
   写明两个 GLM 的供应商区别、Star Plan 时间窗、以及「报错即换模型」铁律。
2. `dwfrun-6d377b41`（卡死 44 分钟零产出）已 `AmendWorkflow` 停掉，
   重派为 `dwfrun-65734a63`，模型由用户在确认窗改为 `magpie/antigravity/gemini-3.8-flash`（备选 1）。
3. 本节即为此事的台账登记。

### 六、诚实账

1. 这个错误是**用户指出**的，不是我自查发现。我连续两天没有核对过供应商前缀。
2. 我此前在每次汇报里都写「GLM-5.3-Flash」，**从未写供应商前缀**——
   这种省略让错误在汇报层看不见，也让用户无法从我的汇报里发现它。
   **今后汇报必须带完整模型 ID（含供应商）。**
3. 本节**未 commit**；**零真机**；**未改任何母本**。
4. §545–§550 的**分析结论不受影响**（供应商用错不改变数据与推理），但**产出归属的额度归属要更正**：
   它们由 MUZE 的 GLM 生成，不是 Star Plan。
"""

with open(LEDGER, "ab") as f:
    f.write(SECTION.encode("utf-8"))
print("appended %d bytes" % len(SECTION.encode("utf-8")))
