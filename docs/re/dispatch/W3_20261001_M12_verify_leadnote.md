# W3-M12 派工单 · **独立复核 Lead 的 YR 增量裁定备忘录**（Antigravity）

> ⚠️⚠️ **卡面更正（2026-10-02 01:56，Lead · 立刻生效）—— 本卡 §2 基准事实与任务 A1 含一条被实测否掉的错误前提**
>
> **错误前提**：本卡原写「两侧各有 **21 对** `primary + ILocomotion` 结构」。
> **实测否证**（ZCode S7 会话 `step04`，用 `COL+0x0C → TD → TD+8` 装饰名逐行读出）：
> ```
> row  0 iloco=55 prim= 7  name=.?AVMouseClass@@
> row  1 iloco=49 prim= 7  name=.?AVBuildingTypeClass@@
> row  7 iloco=48 prim= 7  name=.?AVInfantryTypeClass@@
> row  9 iloco=51 prim= 7  name=.?AVListClass@@
> row 11 iloco=45 prim= 7  name=.?AVMPCooperative@@            ← 45→52 争议行
> row 12 iloco=45 prim= 9  name=.?AVUnholyAlliance@@           ← 45→52 争议行
> row 13 iloco=45 prim= 7  name=.?AVMultiplayerGameMode@@      ← 45→52 争议行
> row 16 iloco=48 prim= 7  name=.?AVTechnoTypeClass@@
> row 20 iloco=48 prim= 9  name=.?AV$CComObject@VCChatEventSink@@@ATL@@
> ```
> ⇒ **那 "21 对" 里只有 12 个是真的 Locomotion 类**（`primary_slots ∈ {10,12}`，即 `Drive/DropPod/Fly/Hover/LocomotionClass/Jumpjet/Mech/Rocket/Ship/Teleport/Tunnel/Walk`），
> **另外 9 个是恰好拥有 45–55 槽次表的无关类**（`MouseClass`/`BuildingTypeClass`/`InfantryTypeClass`/`ListClass`/`MPCooperative`/`UnholyAlliance`/`MultiplayerGameMode`/`TechnoTypeClass`/`CComObject@VCChatEventSink`）。
> **⇒ 任务 A1 请改按「12 个 Locomotion 类（按 RTTI 名判定）」核，而不是「21 对」；并请把"9 个无关类"作为一条**独立发现**核实（它们的 45–55 槽次表是什么？为何与 ILocomotion 槽数撞车？）。**
> **⇒ 这条错误前提出自 Lead（`E-W3-21`）。凡本卡与它冲突处，一律以实测为准。**

> 工作目录 `D:\Project\ra2-campaign-forge` · 本卡只做这一包，先整篇读卡。

## 0. 一句话背景

Lead 今晚出具了一份**裁定性备忘录** `out/re_work/_lead_baseline/W3/LEAD_NOTE_yr_delta8_state.md`，把"RA2→YR 结构增量（`+8 字节`）"这个问题分成 **§1 已确立** / **§2 未闭合** / **§3 下游口径** 三栏，目的是**让下游能安全引用**。

**但 Lead 今晚已经自错 17 次**（`E-W3-01`…`E-W3-17`，其中 `E-W3-17` 是"拿一个切片的口径外推全库"，危害面最广）。**这份备忘录目前正被下游当作依据使用。**

**⇒ 你的任务 = 去证明它是错的。** 不是"检查一下格式"，而是**逐条尝试证否**。

## 1. 纪律（**最重要的一节，先读**）

1. **Lead 的转述一律不是判据。** 凡本卡或备忘录里出现的数字，你都要**回到原始产物/二进制**核对。
2. **判据锚定行首/字段**，不得用"关键词出现即算"（`E-W3-12`）。
3. **"没找到" ≠ "不存在"**：任何空结果必须报 `未命中 / INSTRUMENT_FAILED`，**并附你的判据与扫描范围**（今晚已发生 10 次"空扫描被当成结论"）。
4. **任何提取类工具必须带物理边界断言**（尺寸/数量/范围），否则不得引用其输出。
5. **`None` / `[]` / `not_attempted` / 数值 —— 四种输出必须可区分。**
6. **FileOffset 用段映射**（`E-W3-01`）：`.text/.rdata/.data` = `VA−0x400000`；**`.rsrc/.detour` = `VA−0x6FC000`**。
7. **不确定就写"不确定 + 缺什么证据"，禁止圆。**
8. **只读**：`ra2youli/**`、`ra2bench/**`、`ra2render/**`、`tools/**`、`docs/**`、`out/re_work/qc/**`、`out/re_work/zcode_live/**`。
   **`ra2youli/**`、`ra2bench/**`、`ra2render/**` 三处是现网目录，一律只读，不得写入一个字节。**
9. **不得启动游戏 / 注入 / 调试 / 改任何二进制。**

## 2. 基准事实（Lead 已验，**你仍要自己各算一次**）

| 件 | sha256 | 大小 |
|---|---|---|
| `ra2youli/game.exe` | `c4bf2a57a80ff8d1aa9fbc77f6095c385c1b2ca274ba3f5a4a44aa7446caea5b` | 4,497,680 B |
| `ra2youli/gamemd.exe` | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` | 4,825,360 B |

**段表（Lead 实测，你可复算）**
```
gamemd  .text VA 0x401000 VSize 0x3DF38D FO 0x1000 ｜ .rdata VA 0x7E1000 ｜ .data VA 0x812000 ｜ .rsrc VA 0xB7A000 ｜ .detour VA 0xB93000
game    .text VA 0x401000 VSize 0x3985CD FO 0x1000 ｜ .rdata VA 0x79A000 ｜ .data VA 0x7C9000 ｜ .rsrc VA 0xB2D000 ｜ .detour VA 0xB43000
```

## 3. 要你做的三件事（**逐条作答，落到字节/地址**）

### 任务 A · **逐条尝试证否 §1「已确立」**
备忘录 §1 列了四条**已确立**结论。**对每一条，独立地从两个二进制出发复核，并明确给出「成立 / 不成立 / 证据不足」三选一**：

| # | 备忘录的断言 | 你要独立核什么 |
|---|---|---|
| A1 | 两侧各有 **21 对** `primary + ILocomotion` 结构；主表槽数分布 `10/7/9/12`；次表 `game 49` vs `gamemd 50`；`gap = 4*slots+4` | 自己写扫描器数一遍（**不要复用 `out/re_work/zcode_live/W3_20261001/yr_delta8/` 里的脚本**，它的作者是执行方；你可以**读它的输出**作为对照，但结论要来自你自己的扫描） |
| A2 | `Size()` 常量仅 **2 类**不同：`JumpjetLocomotionClass` 144→152、`RocketLocomotionClass` 88→96，其余 10 类相同 | 从两侧 vtable 里**自己找到 `Size()`（返回尺寸常量的那个函数）**并读出立即数。**注意 Qoder 说 `Size()` 在 `v_main[9]`、`GetSizeMax` 在 `v_main[7]` —— 你要独立确认哪个槽返回对象尺寸** |
| A3 | `Rocket` 的成员访问 `+0x4C`（game）↔ `+0x50`（gamemd），即**同一字段移了 +4** | 独立反汇编两侧 `Rocket` 相关函数，核对这两个偏移的**指令原文** |
| A4 | `[this+0x94]` 是**在析构里被 `Release` 的 COM 接口指针**（`Jumpjet`） | 独立反汇编 `Jumpjet` 析构，核对是否存在"读出→判空→`call [reg+8]`"这一形态。**只描述观察到的行为，禁止推测接口类型** |

### 任务 B · **检查 §2「未闭合」是否其实已经闭合**
备忘录列了 U1–U6 六项未闭合。**逐项检查现有产物里是否已有能闭合它的证据**（Lead 可能漏看）：
- **U1** `Rocket` 尺寸 +8 但成员只移 +4 ⇒ 另 4 字节在哪？
- **U2** 次表增量是否所有类都 +1？（S7 的位置对齐表显示 18/21 位为 0 或 +1，唯独 3 个连续位 `45→52`）
- **U3** `+8` 是否由次表新增 1 槽**引起**（因果，不是相关）
- **U4** 为何恰是 `Jumpjet` 与 `Rocket` 这两类
- **U5** `Jumpjet` 的 `+0x4C` 与 `Rocket` 的 `0x4C→0x50` 是否同源
- **U6** 🔴 **`idx 43`（台账 R56 的"跨类求交唯一插入点"）是否成立** —— Lead 说它**与后续数据冲突**（暗示插入索引按类不同 46/44）。**请你判死**：若 R56 结论确实错了，**明确说"台账 R56 应更正"并给出应改成什么。**

### 任务 C · **检查 §3「下游口径」是否每条都有据**
备忘录 §3 给了 5 条口径（引用 `v[N]` 必须写明主/次表 · 说"次表 49→50"必须带作用域 · 可以说"+8"但不可以说"因为多了一个槽" · `+0x94` 是 COM 指针可引用但不得推测类型 · 数字必须带作用域）。
**逐条给出：这条口径被什么证据支持？有没有哪条其实**没有**证据？**
⚠️ 特别注意：Lead 已自认 `E-W3-17`（"全库默认 = 次表"）是错的，正确说法见 `out/re_work/qc/W3_20261001/scope/vfunc_slots/_caliber/CALIBER_CHECK.md` §1.5 —— **备忘录里若还残留旧口径，请指出具体行号。**

## 4. 交付（**写域仅此一处**）

`out/re_work/agy/W3_20261001/m12_verify_leadnote/`
- `M12_REPORT.md` —— §A 十节骨架（`docs/re/AGENT_DELIVERY_FORMAT.md`），**`[0]` 必须直接回答**：
  1. §1 四条**逐条**「成立 / 不成立 / 证据不足」
  2. §2 六项**逐项**「已闭合（谁闭合的）/ 仍未闭合」
  3. §3 五条**逐条**「有据 / 无据 / 表述不准（给行号）」
  4. **R56（`idx 43`）应否更正？改成什么？**
  5. **总体：这份备忘录可否被下游引用？哪些条目必须先改？**
- `m12_verify.json` —— 机读，每问一字段；**每条结论带 `verdict ∈ {HOLDS, FALSIFIED, INSUFFICIENT}` + `evidence`（地址/字节/文件行号）**
- `verify_m12.py` —— **EXIT=0**，三断言：①A/B/C 三任务每项均有结论 ②报告里引用的原文能在 `raw/` 里逐字检出 ③两侧二进制哈希与 §2 基线一致
- `raw/stepNN_*.txt` —— **按步命名，禁止同名覆盖**（今晚已发生多次归档覆盖事故）

## 5. 门禁与回报

**开工先跑** `python tools\verify_anchors.py`（须 **323/323 PASS**，末尾原文贴进报告）。

**回报 `[0]`（逐条，不许省略）**：
1. §1 四条各自：**成立 / 不成立 / 证据不足**（各一句 + 一个地址）
2. §2 六项各自：**已闭合 / 仍未闭合**
3. §3 五条各自：**有据 / 无据 / 表述不准（行号）**
4. **R56 该不该改？**
5. **这份备忘录现在能不能被下游引用？**

**底线**：**宁可交"六项里三项我查不动"，也不要交"六项看起来都对"。** 你的价值在于**找出 Lead 错的地方**，不在于确认它对。
