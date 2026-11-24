# S03-DIRECT · DISAGREE.md

## D1 — ⑱ 按 entry 地址查全库冲突（只报不改名，0 排除）
31 个候选逐地址扫 `docs/re/` + `re_atlas/kb/` + 台账 + `COVERAGE/`，除 coverage 自身外命中 3 例，**均非语义冲突**，不触发排除：
- `00431F10`：`docs/re/ARCHITECTURE_ATLAS.md:3510/3522/3674`、`docs/re/atlas_rev/R6_weapons_mix.md:303/312` 记 `0x00473D2D E8 DE E1 FB FF call 0x00431F10`（散装文件→RawFileClass::Open 链），**与 coverage 名 `CDFileClass::vslot5` 及 direct site 正证据一致**，属文件系统邻域，不冲突。
- `004325A0`：台账 `LEDGER:34457` 记 S03-ADJ 曾误称「两种独立定界通道」把 `0x46EFA6/0x5CE4F4/0x5FA080` 划入该区间（区间不可能含这些地址）。这是**旧卡函数边界口径告诫**，不否定该 entry 为真入口；本卡 direct site `0x473C48` 落在体外、caller 区间不含 entry，成立。
- `006C9890`：台账 `LEDGER:20586` `File_Stream_Crypto | 0x006C9890` 表项，与 S03「文件系统/压缩加密」一致，不冲突。

## D2 — 基线 / 差分（错源 B / ㉔，随机基线零鉴别力已补差分）
- 随机 .text 地址 1000：强/弱判据命中均 3/1000（0.30%）；随机 atlas 入口 11 个命中 7/11。direct 判据对「是否真实函数」非特异，**不据此作区分度声明**。
- 差集检验（同批 108 行 × 弱/强）：`weak_hits=31, strong_hits=31, weak_only=0`。弱判据未产生伪命中，31 行全部由强判据命中；与 S11_DIRECT 的 `weak_only=0` 结论一致。
- 说明：本卡弱判据=raw E8 窗口（无边界/自环约束），强判据=边界+rel32+非自环；差集 0 表明本批行不存在「忽略边界/自环即凑上」的系统性错误。

## D3 — 与 Lead 盘面数字的差异（已消解）
- 纯 `coverage.tsv` S03=196/named127，与卡面 194/125 差 2 行（`004A2780`/`0065C590` 不在 atlas）。按卡面 `atlas∩coverage` 口径复算 =194/125/18/108/68，与卡面逐字一致，工作面取 108 条 [静态推断]。无遗留分歧。
