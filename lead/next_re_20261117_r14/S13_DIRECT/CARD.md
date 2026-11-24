# S13-DIRECT · 纯 direct 通道升格（**不碰虚派发**）

## 盘上现态（Lead 实测 2026-11-18 15:3x，atlas∩coverage；与你自己复算不符就停下报告）
`S13`：**n = 240、proved = 89**、门槛 **120** ⇒ **差 31**；`[静态推断]` **129 行**。
named 侧已达标 ⇒ **本卡只动 grade，不动名字、不动 subsystem**。

## 🔴 本卡只做一件事：**direct call 通道**
本项目已实证：**虚派发式环④（exact）在 1 小时内被审计拦下 3 次**（S20 12/40、S13-K12 14/17 FAIL、S10 6/12），
根因是「活 vptr（构造器装）vs atexit 析构器装」跨表混淆；全库 `[已证]` 里虚派发型**只有 25 行**可用。
⇒ **本卡一律不碰虚派发**。凡环④ 只能靠「虚表可达」的行，**列出但不升格**。

### 唯一可升格判据（direct call）
`E8 rel32` 必须同时满足：
1. 落在**指令边界**上（capstone `skipdata=True` 线性反汇编所得边界集）；
2. `site + 5 + rel32 == entry`（**逐字节核**，不取近似）；
3. **调用者 ≠ 本行体内**（防自环：caller 的地址区间必须不含 entry）；
4. 该 caller 最好本身是 `[已证]`（有则加分并写明，无则不勉强）。

## 强制自证
- **扫描规模必须自洽（新错源 D）**：报告「解出多少条指令 / 多少条 `E8` / 覆盖 `.text` 的百分比」，
  且**你交付的每个站点地址都必须落在自报覆盖范围内**。上一张卡自报 155,215 条（仅 `.text` 11.13%）却交了 `0x741689` 的站点，口径自相矛盾。
  **本卡要求覆盖 `.text` 100%**（本项目全扫基准：**1,392,592 条指令 / 68,253 个 `E8`**）。
- **⑲ 自检**：capstone 5.0.7 的 x86 操作数**无 `op.index`**（index 在 `op.mem.index`，无 index 返 **0 非 None**）。
- **⑨ 停机核验**：盘上 n / proved 自己重算，与卡面不符即停下报告。
- **⑱ 按 entry 地址查全库冲突**（`docs\re\` + `re_atlas\kb\` + 台账 + `COVERAGE\`）—— 只报不改名。
- **基线**：给「随机抽同样多行、用 direct 判据会误命中多少」。
  ⚠️ 注意新错源 B：**随机基线对同源系统性错误零鉴别力**。若你的行都是同一成因，请补**差分检验**（同一批行 × 弱/强判据取差集）。

## 交付（绝对路径，只写这里）
`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_DIRECT\`
`PROGRESS.md`（≤50 行）/ `UNKNOWNS.md` / `DISAGREE.md` / `EVIDENCE\` / `work\`
`coverage_delta.tsv`：8 列 `entry, subsystem(S13), name, one_line_semantics, grade, evidence_path, name_kind, 旧grade→新grade`（**只放 direct 行**）
`VIRTUAL_SKIPPED.tsv`：只靠虚表可达、本卡不升格的行（entry + 现有 ①②③ + 说明「环④缺」）
**每完成 3–5 行就增量落盘 PROGRESS.md。严禁建 venv / pip install / import 其他卡 work 代码。**

## 核心数字（给审计员复算）
① direct 升 `[已证]` 行数 ② 扫描规模（指令数 / E8 数 / `.text` 覆盖率 %）③ 基线误命中数 ④ 逐行 grade 对照 ⑤ 并入后 S13 proved 实测值 ⑥ `VIRTUAL_SKIPPED` 行数