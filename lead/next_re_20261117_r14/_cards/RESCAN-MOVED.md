# RESCAN-MOVED — 验证 1,733 是下界：补扫「返回值搬移后比较」形态

## 背景

`SURVEY_3B2-GLOBAL` 的 ③b② 机械口径是「`call` 之后**紧邻** `test eax,eax` / `cmp eax,<常量>` / `or eax,eax`」。

`S12-B1` 执行器报了一个**漏站**：

- 存在「返回值先搬进别的寄存器再判」的形态，例如 `mov ebx,eax; cmp ebx,8`、`mov ebp,eax; test ebp,ebp`
- 实例：`00447210` 的被调 `006FFEC0` 返回**多值状态码** {0,4,5,7,8,0x1A,0x37}，调用方按码分派 8/4/5/默认；原机械口径扫不到，补扫后从 FAIL 改判 PASS
- ⇒ **1,733 可能只是下界，不是可证池全集**

本卡要把这件事测准：**补扫这种形态，能多出多少候选、分布在哪些子系统。**

## 输入

- `lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv`（现有 1,733 个命中，含 entry / subsystem / name / grade）
- `lead\next_re_20261117_r14\COVERAGE\coverage.tsv`（18,498 行、8 列；第 2 列 subsystem、第 3 列 name、第 5 列 grade）
- `lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv`（12,916 行；**`entry` 小写，须归一**）
- `D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`，期望 SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`
- ImageBase `0x400000`；`.text = [0x401000, 0x7E038D)`
- capstone 5.0.7（**必须 `skipdata=True`**）

## 要扫的形态（必须一起认）

对池中每个 entry 反汇编，判定是否存在下列**任一**形态：

- **M0（现有口径）**：`call` 后 ≤2 条无关指令内出现 `test eax,eax` / `cmp eax,<imm>` / `or eax,eax`，且**紧跟条件跳转**
- **M1（搬移后比较）**：`call` 后先 `mov r,eax`（r ∈ {ebx, ebp, esi, edi, ecx, edx}）或 `push eax; …; pop r`，随后对该寄存器 `test r,r` / `cmp r,<imm>`，且**紧跟条件跳转**
- **M2（存栈后比较）**：`call` 后 `mov [ebp-x],eax` / `mov [esp+x],eax`，随后对该栈槽 `cmp`/`test` 且紧跟条件跳转

**三形态共同的排除项（不许放宽）**：

- 比较之后、分支之前，被比较的寄存器/栈槽**被覆写** ⇒ 不算（`eax` 覆写陷阱的推广）
- 两条路径**动作相同**（同一处 `call` 只差参数）⇒ 不算
- 成功/失败**汇合到同一处**且只差写入值 ⇒ 不算

## 池的定义

**池 = 所有 `grade != [已证]` 且 entry 在 atlas 内的行**（与 `SURVEY_3B2` 同池，约 11,426 行）。

## 要产出的表

`rescan.tsv`，22 行：

```
subsystem  pool  m0  m1  m2  m0m1m2_union  new_vs_1733  named_in_new  delta_pct
```

- `m0`：该子系统按 M0 命中的行数（应与 `SURVEY_3B2\survey.tsv` 的 `p3b2` 列**一致**；不一致要报告差异并解释）
- `new_vs_1733`：`m0m1m2_union − m0`，即**补扫新增**的行数
- `named_in_new`：新增行里名字非空且**非 `fn_`/`sub_` 伪名**的行数（这才是真正可能证成的增量）

## 抽样验证（必须做，不许只报计数）

从 `m1`、`m2` 新增命中里各抽 **5 行**，共 10 行，逐行实际反汇编确认：

1. 该形态真实存在（给地址与字节）
2. 被比较的值确实是 `call` 的返回值（给出搬移链：`call` → `mov r,eax` → `cmp r,imm` 三条指令的地址）
3. 失败路径与成功路径**动作确实不同**（给两条路径的首几条指令）
4. **可伪证性**：被调函数的返回码是**多值集合**还是 `{0,1}` 布尔？

   - 多值集合 ⇒ 可作 ③b②（给集合元素）
   - `{0,1}` 布尔 ⇒ **不算**（与 D-46(A) 一致）

   给每行结论。

## 输出

- `RESCAN_MOVED\rescan.tsv`（22 行，表头如上）
- `RESCAN_MOVED\REPORT.md`：
  - 全表合计：`m0` / `m1` / `m2` / 并集 / 新增 / 新增里"真名"数
  - **明确回答：1,733 是下界还是全集？下界的话，真实下界是多少？**
  - 抽样 10 行的逐行结论（含多值 vs 布尔的判定）
  - **明确回答：新增命中里，有几个子系统的新增量足以改变"proved 可达性"结论？**（对每个子系统算 `proved_now + m0 + new_named` 与门槛比）
- `RESCAN_MOVED\samples.tsv`：表头 `entry	subsystem	m_form	call_at	mov_at	cmp_at	paths_differ	retcode_kind	verdict`
- `RESCAN_MOVED\rescan.py`：可复跑

## 纪律

- **只读**。不许改 `coverage.tsv`、`PANEL.md`、`R14_COMMON.md`、台账、`SURVEY_3B2` 与任何 `NAMED_PUSH_*`；只写 `RESCAN_MOVED\`。
- `m0` 与 `SURVEY_3B2` 的 `p3b2` 若有差异，**必须解释**（可能是我方口径复现问题，也可能是原卡算错）。
- 布尔返回一律不算可伪证，**不许为了增加量而放宽**。
- 22 行一行不许跳，池为 0 的子系统照写 0。
