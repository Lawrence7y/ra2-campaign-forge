# S09-KPROVED7 PROGRESS — RA2 逆向执行员 卡号 S09-KPROVED7

- 目标: ra2youli\gamemd.exe 只读；SHA-256 `73201CC0...F67476` 现场复算一致（4,825,360 B）。
- 开工: 先落本骨架，后读 R14_COMMON §1/§6/§7/§8.1/§8.5/§8.6六条/§8.7九条、D-40/41/42、SURVEY_RING24\PROGRESS.md。
- 环境: Python 3.12.10 + capstone 5.0.7 + pefile 2024.8.26；未建 venv、未 pip install；未改 coverage.tsv / 台账 / 游戏文件。
- 写域: 仅 S09_KPROVED7\ 与 work/EVIDENCE；未写 _audit\ / COVERAGE / 其它卡目录。

## 1. 排除集与选题
- S09 A 集合(②RTTI × ④严格档, SURVEY_RING24 classification.tsv) = **103 行**（本卡 A 集合总行数）。
- 排除集 = 六张 KPROVED 卡 coverage_delta 全部 43 entry + SEMFIX_SLOTS2/3 属 S09 的 8 行(与 KPROVED5 重合) + 黑名单 00654320(③a)/0069DEB0(细则#1不达) ⇒ 44 个唯一地址；余 59 候选。
- 59 候选逐行反汇编 + 全表枚举后，按四环严格筛选，取 8 行入 delta；其余 51 行不成立理由见 UNKNOWNS.md。

## 2. 交付 8 行（四环齐全 8/8）
| entry | name | ② 持有表→归属 | ③b 档 | ④ direct 站点数 |
|---|---|---|---|---|
| 004E2580 | GaugeClass::slot34 | GaugeClass+TriColorGaugeClass→GaugeClass | ②写时变更布尔返回 | 1 |
| 004E1530 | GadgetClass::slot31 | Gadget/StaticButton/TextLabel→GadgetClass | ②门控置位布尔返回 | 3 |
| 004E1550 | GadgetClass::slot27 | Gadget/RTactical/SBGadget/Tactical→GadgetClass | ②双闸或清除布尔返回 | 4 |
| 0048E5A0 | ControlClass::slot31 | ControlClass(单表) | ①多闸位掩码汇总 | 15 |
| 004F4450 | GScreenClass::slot13 | 9张UI表→GScreenClass | ②两段虚分派布尔返回 | 7 |
| 00557AC0 | ListClass::slot40 | ColorList+List→ListClass | ②边界钳制返回 | 10 |
| 004E19F0 | GadgetClass::slot22 | 20张Gadget族表→GadgetClass | ②焦点恒等谓词返回 | 1 |
| 00557AE0 | ListClass::slot39 | ColorList+List→ListClass | ②界内判定返回 | 1 |

## 3. 判据落实
- M1: 全 1214 张 RTTI 可解表枚举每 entry 的全部同槽持有表；≥2 表按错源⑯归基类级，name 栏同类（判据1/2）。
- M3: 「K=行数×均值」是恒等式，未作校验。
- M4: 0048E5A0 ③b① 各闸动作各异(清0/置0x80/置0x40/两种相异调用)，非汇入同一 call；00557F40 两滚动闸汇入同一 [vptr+0xc0] 已剔除。
- M5: 正文锚偏移全部入口相对 +0xNN，逐字符与 EVIDENCE\DISASM_*.txt 对齐（selfcheck 0 fail）。
- M6/M7: delta 8 行 = 自报 8 行；无 ③b④ 循环主张，故无栈累加/寄存器推进问题。
- M8: 语义栏按契约写「③b档 + 整体合同一句话 + 入口锚」；无「未证/未定/弱信号/线索/槽语义」字样（selfcheck 0 fail）。
- ④: 全部 direct，E8@指令边界 + site+5+rel32==entry + 体外(CFG 区间包含) + 非自环（68,253 个 E8 全扫）。

## 4. 核心数字
- 四环齐全行数: **8**（8 行中四环齐全 8 行）。
- S09 A 集合总行数: **103**。
- ③b 基率(seed 20261119, N=8, 2000 次, 全 103 A 行抽样): strict **0.5083**（8133/16000）；loose **0.7464**（11943/16000）。两档操作化见 work\baseline_3b.json。非「K=行数×均值」。

## 5. 交付物
- coverage_delta.tsv（8 行）；UNKNOWNS.md；DISAGREE.md；EVIDENCE\(VTABLES_ALL8.tsv / DIRECT_SITES_8.tsv / DISASM_* / ANCHOR_*)；work\(s1–s4, dump/filter, pool/features/rings8/baseline/selfcheck)。
