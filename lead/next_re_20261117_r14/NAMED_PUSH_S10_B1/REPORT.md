# NAMED-PUSH — S10 批次 B1（前 18 行）· 最终报告

## 批次信息
- 子系统：S10 ｜ 批次：B1（按 entry 升序前 18 行）
- 输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S10_B1`
- 目标：`ra2youli\gamemd.exe`，SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（现场复算一致）
- ImageBase `0x400000`；`.text=[0x401000,0x7E1000)`（VirtualSize 口径 `[0x401000,0x7DF38D)`，卡面写 `0x7E038D` 略保守；18 个 entry 全部落在其中）
- Python 3.12.10 + capstone 5.0.7（`skipdata=True`）+ pefile 2024.8.26；无 venv、无 pip install
- 只写本批次目录：`REPORT.md / PROGRESS.md / delta.tsv / base_rate.tsv / EVIDENCE/ / work/`；未改 `coverage.tsv`、`PANEL.md`、`R14_COMMON.md`、台账、`SURVEY_3B2`、`S04_PUSH_*`

## 筛选命令（照卡面）
```bash
cd D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14
python -c "import csv; rows=[r for r in csv.DictReader(open(r'SURVEY_3B2/hits_detail.tsv',encoding='utf-8'),delimiter='\t') if r['subsystem']=='S10' and r['p3b2_named']=='True']; rows.sort(key=lambda r:int(r['entry'],16)); print('total_named=',len(rows)); [print(i+1,r['entry'],r['name']) for i,r in enumerate(rows[:18])]"
```
- 结果：`total_named=74`（S10 中有名字的 ③b② 命中总数），按 entry 升序取前 18 行 = 本批清单（下表）。

## D-40 四环口径（严格，照卡面 + R14_COMMON §8.6/§12.3）
1. ① 入口：`.text` 内、函数边界自洽
2. ② 类身份：RTTI 描述符→类名字串，或虚表地址+槽号+槽指向本 entry；`slotN` 里的类名只是线索；**②与④必须不同源**（同一虚表槽不能既证类身份又证被使用，D-40 新禁则）
3. ③ 只认 ③b：③b② 可伪证返回约定（失败/成功动作不同、返回值被分支消费）；禁 eax 覆写陷阱、多路同一 call、模板假句、③a
4. ④ 使用见证：真实调用者或活虚表派发，**direct-only 不足**，且与 ② 不同源

## 本批总表（18 行逐行核完）

| # | entry | name | ①入口 | ②类身份 | ③b | ④见证 | 四环齐全 | 产出 | 证据 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 004D8560 | AircraftClass::slot267 | ✓ | ✓ AircraftClass RTTI | ✓(1/1) | ✗ | 否 | 否 | EVIDENCE/ROW_004D8560.txt |
| 2 | 004D9720 | AircraftClass::slot55 | ✓ | ✓ AircraftClass RTTI | ✓(1/1) | ✗ | 否 | 否 | EVIDENCE/ROW_004D9720.txt |
| 3 | 004D9E70 | AircraftClass::slot38 | ✓ | ✓ AircraftClass RTTI | ✓(3/3) | ✗ | 否 | 否 | EVIDENCE/ROW_004D9E70.txt |
| 4 | 004DA1D0 | AircraftClass::slot200 | ✓ | ✓ AircraftClass RTTI | ✓(1/1) | ✗ | 否 | 否 | EVIDENCE/ROW_004DA1D0.txt |
| 5 | 004DA4E0 | AircraftClass::slot26 | ✓ | ✓ AircraftClass RTTI | ✓(1/1) | ✗ | 否 | 否 | EVIDENCE/ROW_004DA4E0.txt |
| 6 | 004DE7B0 | AircraftClass::slot314 | ✓ | ✓ AircraftClass RTTI | ✗(2/2 同签) | ✗ | 否 | 否 | EVIDENCE/ROW_004DE7B0.txt |
| 7 | 004DE940 | AircraftClass::slot315 | ✓ | ✓ AircraftClass RTTI | ✗(2/2 同签) | ✗ | 否 | 否 | EVIDENCE/ROW_004DE940.txt |
| 8 | 004DEBB0 | AircraftClass::slot247 | ✓ | ✓ AircraftClass RTTI | ✓(3/3) | ✗ | 否 | 否 | EVIDENCE/ROW_004DEBB0.txt |
| 9 | 004DEE80 | AircraftClass::slot331 | ✓ | ✓ AircraftClass RTTI | ✓(3/3) | ✗ | 否 | 否 | EVIDENCE/ROW_004DEE80.txt |
| 10 | 004DF7F0 | AircraftClass::slot322 | ✓ | ✓ AircraftClass RTTI（3 槽） | ✓(1/1) | ✗ | 否 | 否 | EVIDENCE/ROW_004DF7F0.txt |
| 11 | 004DFF40 | AircraftClass::slot209 | ✓ | ✓ AircraftClass RTTI | ✓(1/1) | ✗ | 否 | 否 | EVIDENCE/ROW_004DFF40.txt |
| 12 | 00517FA0 | InfantryClass::slot91 | ✓ | ✓ InfantryClass RTTI | ✓(6/24) | ✗ | 否 | 否 | EVIDENCE/ROW_00517FA0.txt |
| 13 | 00518F90 | InfantryClass::slot69 | ✓ | ✓ InfantryClass RTTI | ✓(2/2) | ✗ | 否 | 否 | EVIDENCE/ROW_00518F90.txt |
| 14 | 00519630 | InfantryClass::slot99 | ✓ | ✓ InfantryClass RTTI | ✓(14/17) | ✗ | 否 | 否 | EVIDENCE/ROW_00519630.txt |
| 15 | 0051AA40 | InfantryClass::slot288 | ✓ | ✓ InfantryClass RTTI | ✓(3/6) | ✗ | 否 | 否 | EVIDENCE/ROW_0051AA40.txt |
| 16 | 0051BAB0 | InfantryClass::slot23 | ✓ | ✓ InfantryClass RTTI | ✓(3/5) | ✗ | 否 | 否 | EVIDENCE/ROW_0051BAB0.txt |
| 17 | 0051BF90 | InfantryClass::slot107 | ✓ | ✓ InfantryClass RTTI | ✓(9/15) | ✗ | 否 | 否 | EVIDENCE/ROW_0051BF90.txt |
| 18 | 0051C8B0 | InfantryClass::slot240 | ✓ | ✓ InfantryClass RTTI | ✓(4/6) | ✗ | 否 | 否 | EVIDENCE/ROW_0051C8B0.txt |

（③b 列数字 = 无 eax 覆写陷阱且路径签名不同的站点数 / 机械命中站点数）

## 逐环裁定依据

### ① 入口
18/18 entry 全在 `.text` 内，入口字节为标准 prologue（`sub esp`/`push esi`/`push ebx` 等），capstone `skipdata=True` 首条即对齐指令，函数边界自洽 → 全 PASS。

### ② 类身份（本批相对 S04 的关键增量）
**18/18 全部钉住。** 做法：全 `.rdata/.data` 扫本 entry 的 4 字节 VA，向前向后沿连续 `.text` 指针游走定虚表边界，再读 `[vt-4]=COL → COL+0xC=TD(VA) → TD+8 内联类名字串`。每个 entry 至少一张虚表给出合法 RTTI：
- 前 11 行（AircraftClass::slot*）：entry 同时出现在 AircraftClass/FootClass/InfantryClass/UnitClass 四张类虚表的同名槽（继承链共享实现），RTTI 全部解析成功；名字里的 `AircraftClass` 前缀与 RTTI 相符，但按卡面要求只作线索，真正钉死靠 RTTI 类名字串。
- 后 7 行（InfantryClass::slot*）：entry 在 InfantryClass 虚表（0x007EB058）对应槽，RTTI = `.?AVInfantryClass@@`，唯一命中。
- ④ 的取证刻意避开这条链（见下）。

### ③ 整体合同（只认 ③b）
- 16/18 行至少 1 个 ③b② 站点：函数体内 `call` 后紧邻 `test eax,eax`/`cmp eax,imm` + `jcc`，比较与分支之间无 eax 覆写，taken/fall-through 两路动作签名（call 目标集/返回常量集/是否 ret）不同 → 返回值确被分支消费，构成可伪证返回约定。
- 2 行FAIL：004DE7B0、004DE940 —— 各 2 个候选站点的 taken/fall 签名完全相同（`call [edx+0x2c]→cmp eax,1→je` 两路都只到同一 call；`call [edx+0x68]→test eax→je` 两路都无动作），属「同签/零区分」，不构成 ③b。
- 三陷阱排查：本批无「比较后 eax 被 `mov eax,[…]` 覆写再分支」的可用站点（deep.py 的 `gap_eax_overwrite` 全 False）；多个 call 到同一 `0x7C8E17`(operator new)/`0x6F3970` 的站点按细则#1（同 call 仅参数不同不计）处理，未把它们当有效 ③b；语义不用「对象初始化/清零」模板句。

### ④ 使用见证（决定性失败环）
对 18 个 entry 逐一做了三种独立取证，全部为空：
1. **direct call**：全 `.text` 原始字节 E8/E9 rel32 扫描 + capstone 线性反汇编双通道，指向本 entry 的调用 **0 处**（阳性对照：同法扫 `0x410230` 得 37 处，证明扫描器有效）。
2. **立即数/位移引用**：entry VA 作为立即数或内存位移在 `.text` 出现 **0 处**。
3. **全镜像 4 字节出现**：每个 entry VA 仅 1–4 次，全部落在 `.rdata/.data` 虚表槽，`.text` 内 0 次（即「仅虚表可达」）。

唯一现成的「使用」证据是：相关类虚表由构造期 `mov [esi],vt`（esi=ecx=this）装入**实例对象**，槽驻本 entry，`.text` 存在 `call [reg+slot]` 形态。但这与 ② 用的是**同一虚表槽**：② 说「vt[slot]==entry ⇒ 属该类」，④ 又说「vt[slot]==entry ⇒ 被用过」，两条环出自同一次静态扫描 —— 正是 R14_COMMON §12.3（D-40 新禁则）明令禁止的「②④同源」。且接收者是实例对象、无「静态 global 接收者 exact 派发」（S13_K12 审计口径），不满足严格 ④。
**⇒ ④ 18/18 FAIL，四环齐全 0 行。**

### 与 S04 的败因对比（卡面要求）
- S04：73 个命中全部 `named=0`，名字取不到 ⇒ ② 类身份物理无从取证 ⇒ 36 行实测全败。卡面背景：`S04_PUSH_*` 产物保持原样未改。
- 本批：18/18 全部 `p3b2_named=True`，**② 真钉住 18/18**（全部 RTTI 解析成功），证明「有名字」确实解开了 S04 的 ② 死结。
- 但败因从 ② 后移到 ④：这些 `Class::slotN` 都是虚函数，全库无 direct caller、无立即数引用、仅虚表可达；按 D-40 严格口径，④ 必须与 ② 不同源，而唯一可达链与 ② 同源 ⇒ 仍然全败。这与 `S13_PUSH` 6 行「字面四环齐全、D-40 严格 0」以及 `S13_K12` 审计「17 行仅 3 行可辩护」完全同型。
- 结论：本批如实产出 **0 行** `[已证]`。名字把 ② 打通了，但 ④ 的独立见证缺口未解，`proved` 覆盖无增量。

## 产出清单
- `REPORT.md`（本文件）、`PROGRESS.md`、`delta.tsv`（**仅表头，0 数据行**）、`base_rate.tsv`
- `EVIDENCE/ROW_<entry>.txt` × 18（每行独立地址/字节；含未入选行的否决理由）
- `work/`：`scan.py`、`deep.py`、`ring4_final.py`、`gen_rows.py` 及 `scan_all.txt`、`deep.txt`、`ring4_final.txt`、`results.json`（全部可复跑）
- `base_rate.tsv`：`rows_checked=18 ring2_ok=18 ring3b_ok=16 ring4_ok=0 all_four=0 rate=0.000000`
