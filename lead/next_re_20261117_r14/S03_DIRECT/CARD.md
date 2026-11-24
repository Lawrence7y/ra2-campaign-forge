# S03-DIRECT · S03（文件系统/CRT 邻域）纯 direct 通道升格

## 盘上现态（Lead 实测，atlas∩coverage；与你自己复算不符就停下报告）
`S03`：**n=194、named=125**（门槛 175，**差 50**）、**proved=18**（门槛 97，**差 79**）、`[静态推断]` **108 行（全部已有名字）**、`[未证]` 68。
⇒ **本卡只做 proved**（108 条 `[静态推断]` 是工作面；named 另有卡在处理）。

## 🔴 唯一判据：direct call（本段已证这是唯一稳定通道）
`E8 rel32` 必须同时满足：
1. 在 **capstone 指令边界**上（`skipdata=True` 线性反汇编所得边界集）；
2. **`site + 5 + rel32 == entry`**（逐字节核）；
3. **调用者 ≠ 本行体内**（防自环：caller 区间不包含 entry）。

## ⛔ 严禁（本项目已因此 FAIL 4 次，每次都造成整批作废）
- `atexit` 析构器装的虚表（`push <dtor>; call 0x7C978A`）—— **不是活 vptr**；
- 「entry 在自己虚表里是第 K 槽」的**槽号匹配**；
- `exact` 派发除非满足「接收者是静态 global + 该 global 的 vptr 由**构造器**安装 + `vt[slot]==entry` + 该 site 不被多行共用」；
- slot-baseline；用「恰命中 N / P=R=100%」当证据（**可能是判据自证**）。

## 强制自证（审计会照这几条打回）
1. **扫描必须覆盖 `.text` 100%**（全扫基准 **1,392,592 条指令 / 68,253 个 `E8`@边界 / raw E8 81,715**），**报告你的实测值**，且**交付的每个站点必须落在自报范围内**（上一张卡自报仅 `.text` 11.13% 却交了范围外站点）。
2. **⑲ 自检**：capstone 5.0.7 的 x86 操作数**无 `op.index`**（index 在 `op.mem.index`，无 index 返 **0 非 None**）。先打一条已知阳性 call 自检。
3. **⑨ 停机核验**：盘上 S03 = 194 行 / named 125 / proved 18 / `[静态推断]` 108，自己重算。
4. **⑱ 按 entry 地址查全库冲突**（`docs\re\` + `re_atlas\kb\` + 台账 + `COVERAGE\`）—— 只报不改名。
5. **基线 + 差分**：给随机抽样基线；⚠️ 新错源 B：**随机基线对同源系统性错误零鉴别力**，须补**差分检验**（同一批行 × 弱/强判据取差集）。

## 交付（绝对路径，只写这里）
`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S03_DIRECT\`
`PROGRESS.md`（≤50 行，**第一行写「direct 升了几行 / 最多几行」**）/ `UNKNOWNS.md` / `DISAGREE.md` / `EVIDENCE\` / `work\`
`coverage_delta.tsv`：8 列 `entry, subsystem(S03), name, one_line_semantics, grade, evidence_path, name_kind, 旧grade→新grade`（**只放 direct 行；只动 grade，名字不动**）
`VIRTUAL_SKIPPED.tsv`：只靠虚表可达的行（**不升格**）
**开工 10 分钟内先落 PROGRESS 骨架；每完成 3–5 行增量落盘。严禁建 venv / pip install / import 其他卡 work 代码。**

## 核心数字
① direct 升 `[已证]` 行数 ② 扫描规模（指令数 / E8 数 / `.text` 覆盖率 %）③ 基线 + 差分 ④ `VIRTUAL_SKIPPED` 行数 ⑤ 并入后 S03 proved 实测值