# D37-CENSUS PROGRESS — 执行 D-37(D)

目标 `ra2youli\gamemd.exe` SHA-256 `73201CC0...F67476`（全程只读，未写内存/注入/改文件）；环境 Python 3.12.10 + capstone 5.0.7 + pefile 2024.8.26。未建 venv、未 pip install、未 git commit、未写 `COVERAGE\` 或其它卡目录、未改台账/R14_COMMON.md。

## 第一步 · 复算 S22 规模（coverage.tsv 盘上实读 18,498 数据行）
- subsystem=S22 **10,237 行** = atlas 内 **4,851** + atlas 外 **5,386**。
- 裁决「4,851 行 / 37.5%」= **atlas 内**子集（4,851/12,916=A 分母=37.56%）；全 S22 桶实为 10,237 行。§9.1 早已记 S22「垃圾桶」不得参与百分比排名。
- grade：`[已证]` **56** / `[静态推断]` **1,473** / `[未证]` **8,708**（和=10,237）。

## 第二步 · 「S22 内多少行类名可由 RTTI 定出」（裁决前置问题）
- 判据：entry 作为 RTTI 可解虚表槽值出现（`[vt-4]=COL → [COL+0xC]=TD → TD+8` 以 `.?AV`/`.?AU` 开头）且 `vt[slot]==entry`。
- **可定名 1,966 / 10,237 = 19.20%**；不可定名 8,271 = 80.80%。atlas 内 1,744/4,851=35.95%，atlas 外 222/5,386=4.12%。
- 可定类名共 490 类；Top20 全为容器模板（`T_DynamicVectorClass`/`T_VectorClass`/`T_TypeList` 等，每类 7 行）。
- **RTTI 自证**：虚表定界只从 `.rdata` 做（COL/TD/表间边界），**未用** `function_atlas.tsv` 的 entry+size 反推（错源⑦）→ **1,214 表 / 14,044 槽**，与 §8.1① 基准完全吻合；distinct 槽值 6,692。

## 第三步 · 按 class_to_sub 全表改归前后对照
- 规则源 `coverage_README.md:14-18`（原文见 `EVIDENCE/RULE_SOURCE.txt`）：关键词族 + 容器模板→S22 + 映射不出→S22。仅用**明文写出**的关键词，不把「等」扩写成自造规则；错源⑯多表行按 fail-closed 保留原归属。
- BEFORE 指标逐格复现 `RULING_R15/work/strict_panel.tsv`（**MATCH**）。
- 全表改归 **841 行**（atlas 内 840）= 840 行容器模板→S22 + 1 行 `HouseClass::Update` S16→S14；其中 **S13→S22 93 行**（裁决称 92，见 DISAGREE.md）。
- 达标双映射（判据 `named_n_S(R14)≥ceil(.9n)` 且 `proved_n≥ceil(.5n)`）：
  - 名义：**前 S15/S16/S17 → 后 S15/S17**（S16 掉出：atlas 90→77，named 余量 0 被 13 行容器迁出打破）
  - 严格：**前 S17 → 后 S17**（不变）
- **没有任何子系统因改归而达标**；唯一达标变化是 S16 名义达标被撤销。**改归不产生任何达标，仅作数据卫生**——与裁决 D-37(D)「改归不得作为达标手段」一致。S13 改归后 123/147=83.67%<门槛 133、proved 74/147=50.34% 过线，复现裁决「换分母净收益 0」。

## 交付与自证
- `S22_CENSUS.tsv` 10,237 行；`REATTRIB_MATRIX.tsv` 22 子系统×双映射；`FULL_REATTRIB.tsv` 841 行逐行审计。
- 两次运行三份 TSV sha256 逐字节相同（`EVIDENCE/DETERMINISM.txt`）。
- 输入指纹：coverage `C2FB3E52...`；gamemd `73201CC0...F67476`。
