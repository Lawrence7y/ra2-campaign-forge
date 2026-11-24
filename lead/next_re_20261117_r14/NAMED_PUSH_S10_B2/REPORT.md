# NAMED-PUSH — S10 批次 B2（第 19–36 行）· 最终报告

## 批次信息
- 子系统：S10 ｜ 批次：B2（按 entry 升序第 19–36 行，共 18 行）
- 输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S10_B2`
- 目标：`ra2youli\gamemd.exe`，SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（现场复算一致）
- ImageBase `0x400000`；section 口径 `.text=[0x401000,0x7E1000)`（VirtualSize `[0x401000,0x7DF38D)`，卡面 `0x7E038D` 落在其内；18 个 entry 全部落在 `.text`）
- Python 3.12.10 + capstone 5.0.7（`skipdata=True`）+ pefile 2024.8.26；无 venv、无 pip install
- 只写本批次目录：`REPORT.md / PROGRESS.md / delta.tsv / base_rate.tsv / EVIDENCE/ / work/`；未改 `coverage.tsv`、`PANEL.md`、`R14_COMMON.md`、台账、`SURVEY_3B2`、`S04_PUSH_*`

## 筛选命令（照卡面）
```bash
cd D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14
python -c "import csv; rows=[r for r in csv.DictReader(open(r'SURVEY_3B2/hits_detail.tsv',encoding='utf-8'),delimiter='\t') if r['subsystem']=='S10' and r['p3b2_named']=='True']; rows.sort(key=lambda r:int(r['entry'],16)); print('total_named=',len(rows)); [print(i+1,r['entry'],r['name']) for i,r in enumerate(rows[18:36],start=18)]"
```
- 结果：`total_named=74`（S10 中有名字的 ③b② 命中总数），按 entry 升序取第 19–36 行 = 本批清单（下表）。与 B1（前 18 行）不重叠。

## D-40 四环口径（严格，照卡面 + R14_COMMON §8.6/§12.3）
1. ① 入口：`.text` 内、函数边界自洽
2. ② 类身份：RTTI 描述符链 `[vt-4]=COL → [COL+0xC]=TD → TD+8 类名字串` 且 `vt[slot]==entry`；`slotN` 的类名只是线索；**②与④必须不同源**
3. ③ 整体合同：只认 ③b（本批命中全为 ③b②：call→test/cmp→jcc，返回约定可伪证、调用方真分支）；禁 eax 覆写陷阱、多路同一 call、模板假句、③a
4. ④ 使用见证：真实调用者或活虚表派发，**direct-only 不足**，且与 ② 不同源
   - **本批特别注意（用户交办）**：同子系统 B1 批 18 行里 ③b 16 行成立、但 ④ 18 行全灭（只有 direct-only）。本批如实核 ④，绝不把 direct-only 或「与②同源的虚表槽」算成使用见证。
   - 操作化：活虚表派发须「构造器装**静态 global 接收者** + `vt[slot]==entry` + site 不共用 + 与②不同源」（R14_COMMON §12.3、S13_K12 审计口径）；direct E8 caller 单独不足，只有带体内虚表派发+活链的「真实调用者」（S17_ENGFAM 型）才升为合法环④。

## 本批总表（18 行逐行核完）

| # | entry | name | ①入口 | ②类身份 | ③b | ④见证 | 四环齐全 | 产出 | 证据 |
|---|---|---|---|---|---|---|---|---|---|
| 19 | 0051CBA0 | InfantryClass::slot289 | ✓ | ✓ .?AVInfantryClass@@ | ✓(4/8) | ✗ | 否 | 否 | EVIDENCE/ROW_0051CBA0.txt |
| 20 | 0051CDB0 | InfantryClass::slot286 | ✓ | ✓ .?AVInfantryClass@@ | ✓(1/2) | ✗ | 否 | 否 | EVIDENCE/ROW_0051CDB0.txt |
| 21 | 0051DBD0 | InfantryClass::slot319 | ✓ | ✓ .?AVInfantryClass@@ | ✓(1/1) | ✗ | 否 | 否 | EVIDENCE/ROW_0051DBD0.txt |
| 22 | 0051E140 | InfantryClass::slot241 | ✓ | ✓ .?AVInfantryClass@@ | ✓(2/2) | ✗ | 否 | 否 | EVIDENCE/ROW_0051E140.txt |
| 23 | 0051E3B0 | InfantryClass::slot29 | ✓ | ✓ .?AVInfantryClass@@ | ✓(13/19) | ✗ | 否 | 否 | EVIDENCE/ROW_0051E3B0.txt |
| 24 | 0051F620 | InfantryClass::slot135 | ✓ | ✓ .?AVInfantryClass@@ | ✓(1/1) | ✗ | 否 | 否 | EVIDENCE/ROW_0051F620.txt |
| 25 | 0051F640 | InfantryClass::slot136 | ✓ | ✓ .?AVInfantryClass@@ | ✓(1/1) | ✗ | 否 | 否 | EVIDENCE/ROW_0051F640.txt |
| 26 | 0051F800 | InfantryClass::slot28 | ✓ | ✓ .?AVInfantryClass@@ | ✓(1/1) | ✗ | 否 | 否 | EVIDENCE/ROW_0051F800.txt |
| 27 | 00521B60 | InfantryClass::slot128 | ✓ | ✓ .?AVInfantryClass@@ | ✓(2/3) | ✗ | 否 | 否 | EVIDENCE/ROW_00521B60.txt |
| 28 | 00521DD0 | InfantryClass::slot317 | ✓ | ✓ .?AVInfantryClass@@ | ✓(1/1) | ✗ | 否 | 否 | EVIDENCE/ROW_00521DD0.txt |
| 29 | 00522700 | InfantryClass::slot283 | ✓ | ✓ .?AVInfantryClass@@ | ✓(1/1) | ✗ | 否 | 否 | EVIDENCE/ROW_00522700.txt |
| 30 | 00522BC0 | InfantryClass::slot225 | ✓ | ✓ .?AVInfantryClass@@ | ✓(1/2) | ✗ | 否 | 否 | EVIDENCE/ROW_00522BC0.txt |
| 31 | 00523250 | InfantryClass::slot44 | ✓ | ✓ .?AVInfantryClass@@ | ✓(1/1) | ✗ | 否 | 否 | EVIDENCE/ROW_00523250.txt |
| 32 | 005F5B90 | AircraftClass::slot66 | ✓ | ✓ .?AVAircraftClass@@（17 表共享） | ✓(1/1) | ✗ | 否 | 否 | EVIDENCE/ROW_005F5B90.txt |
| 33 | 005F5E80 | MissionClass::slot5 | ✓ | ✓ .?AVMissionClass@@（3 表） | ✓(1/1) | ✗(direct-only 12 caller) | 否 | 否 | EVIDENCE/ROW_005F5E80.txt |
| 34 | 0065A970 | AircraftClass::slot159 | ✓ | ✓ .?AVAircraftClass@@（7 表） | ✓(1/1) | ✗ | 否 | 否 | EVIDENCE/ROW_0065A970.txt |
| 35 | 006B1300 | SlaveManagerClass::slot6 | ✓ | ✓ .?AVSlaveManagerClass@@ | ✓(2/3) | ✗ | 否 | 否 | EVIDENCE/ROW_006B1300.txt |
| 36 | 006B80B0 | SpawnManagerClass::slot6 | ✓ | ✓ .?AVSpawnManagerClass@@ | ✓(2/3) | ✗ | 否 | 否 | EVIDENCE/ROW_006B80B0.txt |

（③b 列数字 = 无 eax 覆写陷阱且两路动作签名不同的站点数 / 机械命中站点数，逐行独立，见各行 EVIDENCE。）

## 逐环裁定依据

### ① 入口
18/18 entry 全在 `.text` 内，入口字节为标准 prologue（`push`/`mov`/`sub esp` 等），capstone `skipdata=True` 首条即对齐指令，函数边界自洽 → 全 PASS（逐行字节见各行 EVIDENCE ①）。

### ② 类身份（本批 18/18 真钉住）
做法：全 `.rdata/.data` 扫本 entry 的 4 字节 VA，向前向后沿连续 `.text` 指针游走定虚表边界，再读 `[vt-4]=COL → [COL+0xC]=TD → TD+8` 内联类名字串。每行至少一张虚表给出合法 RTTI：
- 前 13 行（InfantryClass::slot*）：entry 落在 InfantryClass 虚表 `0x007EB058` 对应槽，`RTTI='.?AVInfantryClass@@'`。
- 005F5B90（AircraftClass::slot66）/ 0065A970（AircraftClass::slot159）：entry 同时出现在 AircraftClass/FootClass/InfantryClass/UnitClass 等 17/7 张类虚表（继承链共享实现），RTTI 全部解析成功，名字前缀与之一致但仅作线索。
- 005F5E80（MissionClass::slot5）：3 张表 MissionClass/ObjectClass/VeinholeMonsterClass，`RTTI='.?AVMissionClass@@'`。
- 006B1300 / 006B80B0：各自唯一类虚表 `0x007F31C8`/`0x007F3650`，RTTI 分别为 SlaveManagerClass / SpawnManagerClass。
- ④ 取证刻意避开这条 RTTI/虚表数据链（见下）。

### ③ 整体合同（本批 18/18 成立，全为 ③b②）
- 18/18 行至少 1 个 ③b② 站点：函数体内 `call` 后 ≤3 条内 `test eax,eax`/`cmp eax,imm` + `jcc`，比较与分支之间无 eax 覆写，taken/fall 两路动作签名（call 目标集 / 返回常量集 / 是否 ret / 末端 eax）不同 ⇒ 返回值确被分支消费，构成可伪证返回约定。
- 本批比 B1（③b 16/18）多 2 行：0051F620/0051F640 的 `call 0x521320 → cmp eax,-1 → jne` 与 006B1300/006B80B0 的 `call 0x410320 → test eax → jl` 等均给出清晰的 -1/负值哨兵两路分化。
- 三陷阱排查：比较后 `mov eax,[…]` 覆写再分支的站点在有效站点中均未出现（`eax覆写陷阱=False`）；多处 `call [eax+0x184]`/`[edx+0x2c]`（如 0051CBA0/0051E3B0）只对「两路签名确实不同」的站点计数，同签站点已剔除，未把「多路同一 call 仅参数不同」当有效 ③b；语义不用「对象初始化/清零」模板句。逐站点字节见各行 EVIDENCE ③。

### ④ 使用见证（决定性失败环，18/18 FAIL — 如实核）
对 18 个 entry 逐行做了独立取证，三种候选全部不足以构成合法环④：

1. **direct E8/E9 caller（capstone 线性反汇编 + 原始字节双通道；阳性对照 `callers[0x410230]=37` 证明扫描器有效）**：
   - **17 行 = 0 处** direct caller、0 处立即数/位移引用、entry VA 全镜像 dword 只落 `.rdata` 虚表槽（`.text` 内 0 次）⇒ 仅虚表可达，与 B1 完全同型。
   - **唯一例外 005F5E80（MissionClass::slot5）= 12 处真实 E8 caller**：逐点经 capstone 指令边界核实（raw@site=e8，如 `0x42528c/0x43695c/…`），且每个调用点紧接 `mov reg,eax; test reg,reg; jl` 消费返回（负值错误码分支）。但该行 **body 内间接 call（虚表派发）数 = 0**，vptr 安装点全为实例 `this`（`mov [esi],vt`），无静态 global 接收者，12 个 caller 函数中仅 5/12 从 PE 入口 `0x7CD80F` 正向可达。对照可接受的「真实调用者」范例 S17_ENGFAM（1 E8 调用点 + body 内 3 处虚表派发 + PE 入口 3 根全达 + 反向 RTTI 闭包 81 成员），本行属 **direct-only 死链形态**。按卡面「direct-only 不足」与 D-40「不得据 direct call 单独升 [已证]」**不计环④**（详见 `EVIDENCE/ROW_005F5E80.txt` 与 `work/ring4_final.txt` §D、`work/ring4_row15_final.txt`）。

2. **活虚表派发**：候选只有「构造器 `mov [esi]/[edi]/[ebp],vt` 装实例 this + `vt[slot]==entry`」。该链与 ② 用的是**同一虚表槽**：② 说 `vt[slot]==entry ⇒ 属该类`，④ 又说 `vt[slot]==entry ⇒ 被用过`，出自同一次静态扫描 ⇒ 违反 R14_COMMON §12.3「②④不同源」。且接收者是实例对象、**静态 global 接收者 0 处**（逐行 EVIDENCE ④），不满足 S13_K12 审计「活 vptr + 静态 global 接收者 + site 不共用」的严格口径。
   ⇒ **④ 18/18 FAIL，四环齐全 0 行。**

### 与 S04 的败因对比（卡面要求）
- S04：73 个命中全部 `p3b2_named=0`，名字取不到 ⇒ ② 类身份物理无从取证 ⇒ 两批 36 行实测全败。卡面背景：`S04_PUSH_*` 产物保持原样未改。
- 本批：18/18 全部 `p3b2_named=True`，**② 真钉住 18/18**（全部 RTTI 解析成功，含三张新类 SlaveManagerClass/SpawnManagerClass/MissionClass），证明「有名字」确实解开了 S04 的 ② 死结；③b 本批 18/18 也全部成立（高于 B1 的 16/18）。
- 但败因同 B1 一样后移到 ④：这些 `Class::slotN` 都是虚函数，17 行全库无 direct caller、无立即数引用、仅虚表可达；唯一有 12 个 direct caller 的 005F5E80 也因「direct-only（body 内虚表派发=0、无静态 global 接收者）」不合格。按 D-40 严格口径，④ 必须与 ② 不同源，而唯一可达链与 ② 同源或仅 direct-only ⇒ 仍然全败。这与 `S13_PUSH` 6 行「字面四环齐全、D-40 严格 0」以及 `S13_K12` 审计「17 行仅 3 行可辩护」完全同型。
- 结论：本批如实产出 **0 行** `[已证]`。名字把 ② 打通了（18/18），③b 也全过（18/18），但 ④ 的独立见证缺口未解，`proved` 覆盖无增量。虚报不可接受，0 行可接受。

## 汇总
- rows_checked：**18**
- ② 类身份钉住：**18**
- ③b 成立：**18**
- ④ 独立见证成立：**0**（17 行仅虚表可达；1 行 005F5E80 为 direct-only）
- 四环齐全（严格 D-40）：**0**
- delta 产出：**0 行**（`delta.tsv` 仅表头）

## 产出清单
- `REPORT.md`（本文件）、`PROGRESS.md`、`delta.tsv`（**仅表头，0 数据行**）、`base_rate.tsv`
- `EVIDENCE/ROW_<entry>.txt` × 18（每行独立地址/字节/否决理由，含 005F5E80 的 12 caller 逐点）
- `work/`：`scan.py`、`deep.py`、`ring4_final.py`、`ring4_row15_final.py`、`gen_rows.py` 及 `scan_all.txt`、`deep.txt`、`ring4_final.txt`、`ring4_row15_final.txt`、`results.json`（全部只读目标、可复跑）
- `base_rate.tsv`：`rows_checked=18 ring2_ok=18 ring3b_ok=18 ring4_ok=0 all_four=0 rate=0.000000`
