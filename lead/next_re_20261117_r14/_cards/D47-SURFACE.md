# D47-SURFACE — D-47 影响面逐行测量（只测量，不裁决）

## 背景

`R14_COMMON` §13.4 已把 **D-47** 立为待裁项：**D-43(A)** 把 `vt[slot] == entry` 写进了 **④ 使用见证** 的定义，而 **§12.3** 禁止 **②（类身份）与 ④（使用见证）共用同一虚表槽**。凡「活 vtable 槽位」形态的 ④，必然同时满足一条、违反另一条。

`PANEL.md` 的 M74 披露已写「受影响 ≥37 行」，但那是个**估数**。本卡把它变成**逐行精确清单**。

**本卡不做裁决。** 只回答「若 §12.3 胜出，会翻转哪些行；若 D-43(A) 胜出，会翻转哪些行」。

## 输入（全部只读）

- `lead\next_re_20261117_r14\COVERAGE\coverage.tsv`（18,498 行、8 列；第 2 列 subsystem、第 4 列语义、第 5 列 grade、第 6 列 evidence_path）
- `lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv`（`entry` 小写须归一）
- 各审计表：`NAMED_PUSH_AUDIT*\verdict.tsv`（8 列，含 `ring2_at` / `same_source` / `ring4_at` 列）
- 各执行器 delta：`NAMED_PUSH_*\delta.tsv`、`S04_PUSH_*\delta.tsv`
- `lead\next_re_20261117_r14\R14_COMMON.md` §13.4（D-47 定义）

## 要做的事

### 第 1 步 · 圈定「活 vtable 槽位形态」的行

对 `coverage.tsv` 中 **grade == `[已证]`** 的全部行（当前 1,654 行），按**证据来源**判定其 ④ 属于哪一类。分类必须互斥且可核：

- **F1 · 槽位-安装型**：④ 的证据链依赖「该 entry 占某虚表第 N 槽」+「该表由构造器在 `.text` 内安装」。这是**共用枢轴**的形态
- **F2 · 可见派发型**：④ 有独立于槽位的派发点（如 `call [reg+0xNN]` 且能钉到本类实例、或有真实调用者且非 direct-only）
- **F3 · 仅 direct-only**：只有静态调用者
- **F4 · 其它/无法归类**

判定依据：优先用审计表的 `same_source` 与 `ring4_at` 列；审计表没有的行，用 `evidence_path` 指向的 VERDICT 文件里的 ④ 描述。

### 第 2 步 · 逐行清单

对**全部 F1 行**给出：`entry / subsystem / evidence_path / ④ 锚点 / 该行是否已在某条披露里被点名`。

### 第 3 步 · 两个读法的翻转量

- **若 §12.3 胜出**（②④ 不得共用槽）：F1 行**全部**翻为不成立 ⇒ 给出翻转行数与逐子系统分布
- **若 D-43(A) 胜出**（槽位安装即可作 ④）：F1 行全部保持 ⇒ 翻转 0 行；但须列出「D-43(A) 胜出后仍不满足的其它环」有哪些（应为空，需验证）

### 第 4 步 · 对达标判定的影响

逐个回答：

- 两种读法下，**名义达标数与严格达标数各是多少**？（当前名义 3/22、严格 1/22）
- **若 §12.3 胜出，S17 还达标吗？**（S17 是最脆弱的达标者，必须单独算：它的 proved 56 / strict 55 里有几行属 F1）
- **若 §12.3 胜出，S15 的 strict 从 63 降到多少？**（门槛 79）

## 输出

- `D47_SURFACE\surface.tsv`：表头 `entry	subsystem	grade	f_form	ring4_anchor	named_in_disclosure	evidence_path`，**只放 F1 行**
- `D47_SURFACE\distribution.tsv`：表头 `subsystem	F1	F2	F3	F4	total_proved`
- `D47_SURFACE\REPORT.md`：第 1–4 步的结论，必须包含
  - F1 总行数与逐子系统分布
  - 两读法下 F1 的翻转量与名义/严格达标数
  - **S17 单列分析**：F1 行数、两读法下 proved/strict 各为多少、是否仍达标
  - **S15 单列分析**：同上
  - 一句明确结论：**「§12.3 胜出的代价是 N 行、影响 M 个子系统、涉及达标翻转 X 个」**
- `D47_SURFACE\surface.py`：可复跑

## 纪律

- **只读**。不许改 `coverage.tsv`、`PANEL.md`、`R14_COMMON.md`、台账、任何 `NAMED_PUSH_*` / `AUDIT*` / `INVENTORY*` / `PROBE*`；只写 `D47_SURFACE\`。
- **不许做裁决**：不要写「应取 D-43(A)」或「应取 §12.3」，只报数。
- 分类拿不准的行**归入 F4 并在报告单列**，不要硬塞进 F1 或 F2 —— F1 多算会夸大影响面，少算会低估代价，两者都是误导。
- 1,654 行不必全部重读字节：本卡是**证据来源分类**，以 `evidence_path` 与审计表为准；只有分类矛盾的才回二进制。
