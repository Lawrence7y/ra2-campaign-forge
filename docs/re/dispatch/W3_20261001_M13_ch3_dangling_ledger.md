# W3-M13 派工单 · **§3 单位机动与寻路：519 个悬空 VA 的字节建账（首批 120 项）**

> 工作目录 `D:\Project\ra2-campaign-forge` · 本卡只做这一包，先整篇读卡。

## 0. 一句话背景

`out/re_work/qc/W3_20261001/scope/atlas_game/` 的交叉核对给出：
```
atlas 唯一 VA 2538 ｜ 已覆盖且通过 1118 ｜ 已覆盖但不通过 2 ｜ 未覆盖 1418 ｜ 冲突 0
其中 §3「单位机动与寻路系统」：612 个 VA 里只有 93 个有断言支撑，519 个未覆盖（全库最多的一章）
```
Qoder 已把这 519 项落成清单：**`scope/atlas_game/dangling_ch3_locomotion.json`**（190,663 B，519 条，每条带 `va` / `atlas_lines` / `subsection` / `line_text_first` / `n_refs`）。
**⇒ 你的任务 = 给这批 VA 补"字节级证词"，让 `已覆盖` 上升。**

## 1. 纪律（先读，逐条遵守）

1. **只做"建账"，不做"推断"**：只报**从二进制里读到的字节与指令**；**任何语义命名若来自 `YRpp` 声明，必须标 `[推演]` 并注明"名据 YRpp 声明"**。
2. **判据锚定行首/字段**，不得"关键词出现即算"。
3. **空结果必须报 `未命中 / INSTRUMENT_FAILED`**，并附**判据与扫描范围**；**不得报"无"或 `0`**。
4. **任何提取类工具必须带物理边界断言**（尺寸/数量/范围）。
5. **`None` / `[]` / `not_attempted` / 数值 —— 四种输出必须可区分。**
6. **FileOffset 用段映射**（`E-W3-01`）：`.text`/`.rdata`/`.data` = `VA−0x400000`；**`.rsrc`/`.detour` = `VA−0x6FC000`**。
7. **不确定就写"不确定 + 缺什么证据"，禁止圆。**
8. 🔴 **只读**：`ra2youli/**`、`ra2bench/**`、`ra2render/**`、`tools/**`、`docs/**`、`out/re_work/qc/**`、`out/re_work/zcode_live/**`。
   **`ra2youli/`、`ra2bench/`、`ra2render/` 是现网目录 —— 一律只读，不得写入一个字节。**
9. **不得启动游戏 / 注入 / 调试 / 改任何二进制。**

## 2. 基准（**你仍要自己各算一次**）
| 件 | sha256 | 大小 |
|---|---|---|
| `ra2youli/game.exe` | `c4bf2a57a80ff8d1aa9fbc77f6095c385c1b2ca274ba3f5a4a44aa7446caea5b` | 4,497,680 B |
| `ra2youli/gamemd.exe` | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` | 4,825,360 B |

**本卡只对 `game.exe` 建账**（§3 的 ATLAS 是 game 侧 ATLAS）。

## 3. 做什么

### 3.1 读清单，取**前 120 项**（按清单顺序，**不要重排、不要抽样**）
输入：`out/re_work/qc/W3_20261001/scope/atlas_game/dangling_ch3_locomotion.json` → `items[0..119]`

### 3.2 对每个 VA 建账（字段如下）
```json
{
  "va": "0x0041b360",
  "atlas_lines": [1033, 1529],
  "atlas_subsection": "…（来自清单）",
  "in_text": true,
  "file_offset": "0x0001B360",
  "first_16_bytes": "56 8b f1 83 ec 10 …",
  "is_function_entry": true,
  "disasm_first_6": ["push esi", "mov esi, ecx", "…"],
  "target_of": ["0x0041b2a0", "…"],          // 若它出现在某处的 call/jmp 目标
  "callers_sample": ["0x004xxxxx", "…"],      // 最多 5 条，**须给命令**
  "vtable_membership": ["0x0079xxxx@v_main[12]", "…"],  // 若是虚表槽目标
  "evidence_tier": "实证|推演|待实测",
  "notes": ""
}
```
**硬要求**：
- **`first_16_bytes` 必须是该 VA 在文件里的真实字节**（按段映射算 FileOffset，**贴出算式**）
- **`disasm_first_6` 必须是解出来的指令原文**（不是助记符猜测）
- **每个数字都要能复算** ⇒ 报告里贴**命令 + 原文输出**
- **做不到的字段写 `not_attempted` + 原因**，**不要留空、不要用 `null` 代替"未做"**

### 3.3 统计与产物
- `M13_REPORT.md`（§A 十节骨架）：**`[0]` 直答**：
  1. **120 项里有多少项成功建账**（`ok` / `not_attempted` / `INSTRUMENT_FAILED` 各多少）
  2. **这批 VA 的形态分布**：函数入口 / 表内槽目标 / 数据 / 无法判定 各多少
  3. **有没有"整段连续 VA"**（若是，说明 ATLAS 是按区间批量引用的 —— **这是对 §3 悬空的解释，比逐项建账更重要**）
  4. **能否把 `game.exe` 侧与 `gamemd.exe` 侧对上**（同 VA 是否都在 `.text`、是否是同类函数）
  5. **`atlas_lines` 指到的原文**是什么（给 3 条样例）
- `m13_ledger.json`（机读，120 条）
- `verify_m13.py`（**EXIT=0**，三断言：①120 条均有结论 ②报告引用的字节/指令能在 `raw/` 逐字检出 ③两侧 exe 哈希与 §2 一致）
- `raw/stepNN_*.txt`（**按步命名，禁止同名覆盖**）

## 4. 门禁与回报
**开工先跑** `python tools\verify_anchors.py`（须 **323/323 PASS**，末尾原文贴进报告）。
**并跑** `python tools\audit_bytes.py <你的 claims 文件>`（若有），贴出 `OK/MISMATCH` 计数。

**回报 `[0]`（逐条，不许省略）**：
1. 120 项的建账成功率（`ok` / `not_attempted` / `INSTRUMENT_FAILED`）
2. **形态分布**（函数入口 / 表内槽目标 / 数据 / 无法判定）
3. **有没有"整段连续 VA"**（若有，给出区间的起止与长度）
4. 能否与 `gamemd.exe` 侧对上
5. `atlas_lines` 的 3 条样例原文

**底线**：**宁可交"120 项里 60 项未完成 + 原因"，也不要交"120 项看起来都齐"。**
**本卡的价值不在"把 519 项都建账"（那是后续批次的事），而在"搞清这 519 项到底是什么形态"—— 如果它们是整段区间，那 §3 的悬空性质就变了。**
