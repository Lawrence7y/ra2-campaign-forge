# 卡 R17-R28-R12-REPAIR · 量化并修复 R12 的「宿主归因」缺陷（C3 假阳性）

纯静态、只读、有界。镜像钉死：`ra2youli\gamemd.exe` sha256 `73201CC0…F67476`；**报告第一行写实际路径与 sha256**。

## 〇、已确认的缺陷（Lead 亲核字节）
`R17_R12_VT_OFFSET\hits.tsv` 有 354 数据行，列含 `site / class / disp / bytes / host / fn_end / base_reg / position_assert / disasm / base_source / verdict`。
**它的 host / fn_end / verdict 三列不可靠**，根因是用**按字节扫 `C3`/`C2`** 判定函数入口：
- 实测反例：site `0x5A6860` 被记 `host=0x5A6810`，但 `0x5A6810` **不是入口** ——
  其前字节 `0F BF C3`（`movsx eax,bx`）的 **`C3` 是 modrm 字节**，被误当成 `ret`；
  真 host 是 `0x5A6510`（`83 EC 70` 序言）、真 fn_end 是 `0x5A691C`（其后 `90 90 90 90`）。
- 该行的 `verdict` 也错：判 `NON_TARGET(base from stack)`，而实际基址来自 `mov ebp,eax`（构造出的对象）。

## 一、要做的事
**Q1 · 量化缺陷规模**
 对全部 **354** 行，用**可信入口集**（`.rdata` 全部 vtable 槽值 ≈14,044 个函数入口 + 已知 ctor 入口；**不要**再用字节扫 `C3`）重新归因 host 与 fn_end，统计：
 - host 与原记录**不同**的行数；
 - fn_end 与原记录**不同**的行数；
 - 重新归因后 `position_assert` 由 True 变 False（或反之）的行数；
 - 按 `class`（call/mov/stack_ff5424/other_*）分组的差异分布。

**Q2 · 判定 `verdict` 列有多少条受影响**
 `verdict` 依赖 `base_reg` 与 `base_source`。统计：
 - `base_source` 为空或明显未解的条数；
 - `verdict = NON_TARGET(base from stack)` 的条数，其中**实际 base_source 显示来自对象/寄存器传递**的条数（即可能误判）。
 本轮已知 `0x5A6860` 是误判样本；请找出同类。

**Q3 · 产出可替换的修正表**
 逐行给：site \t class \t disp \t 旧host \t 新host \t 旧fn_end \t 新fn_end \t 旧verdict \t 建议verdict \t 变更原因。
 **不要改 `hits.tsv` 本身**（证据件只留勘误）。

**Q4 · 对计数的影响（重要）**
 明确回答：**Q1 的 host 修正是否改变 R12 报的 267 / 86 / 70 / 9 / 7 / 1 这些"形态命中数"？**
 （预期：不改变，因为那是**字节形态扫描**的计数，与 host 归因无关 —— 但必须由你核实并说明依据，不能只是断言。）

## 二、铁律
1. 报告第一行写实际路径与 sha256；不符即作废。
2. **入口判定禁止按字节扫 `C3`/`C2`**；必须用可信入口集或严格解码（含指令边界校验）。
3. 有界：数据扫描限 `.rdata`/`.data`；反汇编只在必要处。**声明扫描字节数**。
4. 只读；不建进程、不调试、不启动 gamemd；**不得修改 `R17_R12_VT_OFFSET` 下任何文件**；产物只写本卡目录。
5. 中间结果先落盘，严格 **8 分钟**预算。
6. 取不到写「未取得」，严禁编造。

## 三、产物（只写本目录）
`lead\next_re_20261117_r14\R17_R28_R12_REPAIR\`
- `REPORT.md` —— 第一行镜像+sha256；Q1–Q4
- `host_fix.tsv` —— Q3 的逐行修正表
- `stats.tsv` —— Q1/Q2 的统计
- `work.py` —— 可复跑