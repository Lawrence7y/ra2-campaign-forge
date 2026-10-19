# W3-M32R 派工单 · **§6（M29）的 8 条 FALSIFIED 归属独立复算（RTTI BCA/CHD）**（WorkBuddy）

> 工作目录 `D:\Project\ra2-campaign-forge` · 本卡只做这一包。
> **来源**：M32 审计 M29 得 `HOLDS 162 / FALSIFIED 8 / INSUFFICIENT 3`（of 173）。**8 条 FALSIFIED 全是 RTTI `BaseClassArray`/`CHD` 地址**，其原文判据：`claimed BCA address != my scan BCA，cell 实际是 TypeDescriptor 指针`。
> **教训（必须落实）**：**RTTI 基类数组地址必须核"cell 内容"（该 dword 指向的是 TypeDescriptor 还是 BCA），不能只核"文件里有这个地址"。**

## 🔴 铁律（先读）
1. **`out/re_work/agy/W3_20261001/m29_ch6_expand/**` 与 `out/re_work/zcode_live/W3_20261001/m32_m29_audit/**` 一律只读** —— 你产出**修正建议表**，不改别人的件（M29 归 Antigravity、M32 归 ZCode）。
2. **扫描对象**：`ra2youli/game.exe`（原版侧）。**段映射用 `E-W3-01` 规约**（`FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`；`.rsrc`/`.detour` 是 `VA − 0x6FC000`，**不是全段 `VA − 0x400000`**）。
3. **只读红线**：`gamemd.exe`/`game.exe`/现网三目录/`tools/**` **零写入**；开工先跑 `python tools\verify_anchors.py`（须 323/323）。
4. **空扫描必须报 `INSTRUMENT_FAILED`**（附扫描范围与判据）；**`[]`（扫了没有）与 `not_attempted`（没扫）必须是两种输出。**
5. **写域仅此一处**：`out/re_work/workbuddy/W3_20261002/m32r_rtti_bca/`

## 做什么（四件）

### ① 取证
从 `m32_m29_audit/` 抽出那 8 条 FALSIFIED：**逐条给出** claimed 地址 / M32 的复算值 / 涉及的类名与文件:行号。
（若 8 条不齐 ⇒ 如实报缺哪几条，**不要用别的条目凑数**。）

### ② 独立复算（**用与 M32 不同的路径**）
对每个争议地址，**自写解析**（禁止复用 `ra2re/rtti.py` / `rtti_diff` 结论）：
- 装饰名 `NUL` 终结校验 → `TD = strVA − 8` → `COL = A − 0x0C`（校验 `signature ∈ {0,1}`、`COL+0x0C == TD`）
- **关键一步**：读 `BaseClassArray` 链上每个 cell 的 **dword 内容**，判它是 **TD 指针**还是 **BCA 指针** ⇒ 这是本卡的核心判据。
- 每条输出：`raw bytes`（hex）+ 反汇编/结构解读 + 结论。

### ③ 判定与修正建议表
每条给 `verdict ∈ {CLAIM_WRONG, M32_WRONG, BOTH_PARTIAL, INSUFFICIENT}` + `evidence`：
- `CLAIM_WRONG` ⇒ 给**正确值**与**证据链**（供 Antigravity 恢复后回填 M29）
- `M32_WRONG` ⇒ 给反证（**不许为维持一致而弱化判据**）
- 查不出 ⇒ `INSUFFICIENT` + 说明卡在哪。

### ④ 反向验证（硬要求）
构造一个"应当失败"的对照并证明它失败：
- **例**：拿一个**已知是 TD 指针**的 cell 走你的判据 ⇒ 应当判 TD；拿一个**已知是 BCA 指针**的 ⇒ 应当判 BCA。
- **或**：故意用"只查地址存在性"的旧判据跑 8 条 ⇒ 应当**无法区分**（正是 M32 指出的缺陷）。
- 写明做了哪条 + 读数原文。

## 交付
- `M32R_REPORT.md`（§A 十节骨架；`[0]` 直答）
- `m32r_recheck.json`（逐条 8 项：claimed / m32_value / my_value / cell_content / verdict / evidence）
- `correction_table.md`（**可直接回填 M29 的修正建议**，只读来源 + 建议值）
- `verify_m32r.py`（**EXIT=0 + `verdict tally` 行**，注释 `# hard requirement: print verdict tally line`）
- `raw/stepNN_*.txt` + `raw/progress.log`（**尽早写部分产物**）

## 回报 `[0]`
① 8 条是否齐全 ② verdict 分布 ③ 每条一句话结论 ④ 反向验证做了哪条、结果 ⑤ `verdict tally` 原文

## 底线
> **宁可交"8 条里 3 条我判 CLAIM_WRONG、2 条 INSUFFICIENT"，也不要交"8 条全部确认 M32 正确"。**
> **你的价值是独立复算 —— 若你与 M32 全一致，必须给出你自己的 cell 内容证据，而不是引它的话。**
