# S03-C4 PROGRESS — D-40 补救线索 7 行补 ③b + ②

# 状态：完成（2026-11-19）。只读 gamemd.exe（SHA-256 73201CC0…F67476）；仅写本卡目录；未建 venv / 未 pip / 未 import 他卡 work / 未改游戏文件 / 未 git commit。
# 必读已核：R14_COMMON §1/§6/§7/§8.1/§8.5/§8.6 六条；R14_CARDS；PENDING D-40 / D-42 全条（含 D-42 细则1/2/3）。
# 本卡 7 个 entry（D-40 补救线索原文，不得增删）：0065CAC0 004324B0 00552490 006C9890 00631CC0 0065D150 00431E80
# 工具：python 3.12.10 + capstone 5.0.7 (skipdata=True, detail=True) + pefile 2024.8.26；.text 全扫 1,392,592 指令 / 68,253 E8@边界 / 81,715 raw E8（EVIDENCE/scan_scale.json）。

## 结论表（每行 ①②③④ 四环 + 分级 + 证据）
| entry | name（盘上不动） | ② RTTI/类属 | ③b 档位（现场偏移见证据） | ④ direct 站点数/地址 | 四环 | 分级 | 证据 |
|---|---|---|---|---|---|---|---|
| 0065CAC0 | RawFileClass::slot2 | [已证] `.?AVRawFileClass@@` vt 007F0904 slot2 | [已证] ③b② 可证伪返回/错误约定（+0x2C NULL→0；+0x51 fopen 失败→v+0x40 报错→0；成功→句柄） | 3：431B01/431EF2/6C77CF | ✅ | [已证] | EVIDENCE/THREE_B_DETERMINATION.md §1 |
| 004324B0 | CDFileClass::vslot10 | [已证] `.?AVCDFileClass@@` vt 007E1668 slot10（+ BufferIOFile 共享链） | [已证] ③b① origin 三路 switch + 双向夹紧（+0x1A/+0x1F/+0x4A/+0x57） | 1：473BF3 | ✅ | [已证] | EVIDENCE/THREE_B_DETERMINATION.md §2 |
| 00552490 | LCWStraw::slot2 | [已证] `.?AVLCWStraw@@` vt 007ECF44 slot2 | [已证] ③b④ 完整 I/O 循环带三重边界（+0x30 循环 /+0x6A memmove /+0xA7 头==4 /+0x13D 回跳） | 10：56B62F…5FD615 | ✅ | [已证] | EVIDENCE/THREE_B_DETERMINATION.md §3 |
| 006C9890 | FileStraw::slot1 | [已证] `.?AVFileStraw@@` vt 007E4D90 slot1（+8 共享链） | [已证] ③b① 幂等闸+解绑+双向绑定守卫链（+0x0B/+0x1C/+0x2D/+0x3B） | 9：56B5C1…641C29 | ✅ | [已证] | EVIDENCE/THREE_B_DETERMINATION.md §4 |
| 00631CC0 | FilePipe::slot3 | [已证] `.?AVFilePipe@@` vt 007E4DA0 slot3（+7 共享链） | [已证] ③b① 对称守卫链，解绑走 vt+0xC + 旧 straw 虚通知（+0x1C/+0x39/+0x43） | 10：527035…64197C | ✅ | [已证] | EVIDENCE/THREE_B_DETERMINATION.md §5 |
| 0065D150 | CDFileClass::slot3 | [已证] `.?AVCDFileClass@@` vt 007E1668 slot3（+3 共享链） | [已证] ③b② bool 返回约定（+0x0E seek-to-end；+0x13 失败→0；+0x2D 成功→1） | 11：7650AF…77A10E | ✅ | [已证] | EVIDENCE/THREE_B_DETERMINATION.md §6 |
| 00431E80 | BufferIOFileClass::vslot2 | [已证] `.?AVBufferIOFileClass@@` vt 007E3A2C slot2 | [已证] ③b① 三路守卫+逐字节 strcmp 三值（+0x0F/+0x16/+0x4D sbb /+0x66 重开） | 4：47AE21/47AEB4/47AED7/47AF56 | ✅ | [已证] | EVIDENCE/THREE_B_DETERMINATION.md §7 |

## 核心数字（供审计复算）
1. **② 成立数 = 7/7**（RTTI 链 `[vt-4]=COL → [COL+0xC]=TD → TD+8 内联名串` 全读通，`vt[slot]==entry` 成立，无 fail-closed）。
2. **③b 成立数 = 7/7**（档位：② / ① / ④ / ① / ① / ② / ①；逐档现场偏移见 EVIDENCE/THREE_B_DETERMINATION.md）。
3. **四环齐全数 = 7/7**（①②③④ 全齐；coverage_delta.tsv 只含这 7 行）。
4. **7 行 direct 站点数 = 3 / 1 / 10 / 9 / 10 / 11 / 4，合计 48**（EVIDENCE/direct_sites.json；均 E8@边界、site+5+rel32==entry、函数体外、非自环）。
5. **随机基线**：同子系统 S03 [静态推断] 池 N=111；seed 20261119，2,000 次每次取 7 行；判据 ④∧③b 命中 K=21，base rate p=21/111=0.1892，解析期望 E[7]=7p=**1.3243**，MC 实测均值 **1.311**（EVIDENCE/random_baseline.json）。

## 复算方法
- ②：`python work/verify_rtti.py` → EVIDENCE/rtti_chains.json（按 entry 扫全镜像 4 字节槽命中，回溯 vt 基址读 COL/TD/名串，fail-closed）。
- ③b：`work/dump_funcs.py` 出 EVIDENCE/dis_full.txt + offset_map.txt；档位判据见 EVIDENCE/THREE_B_DETERMINATION.md 逐行「现场偏移」。
- ④：`python work/scan_sites.py` → EVIDENCE/direct_sites.json（全 .text 逐指令 E8@边界，target==entry，排除自环）。
- 基线：`python work/baseline.py` → EVIDENCE/random_baseline.json（池=coverage.tsv 中 S03∧[静态推断]；③b 检测器见脚本 detect_3b()；无放回抽样 2,000 次）。口径为「同子系统随机取同样多行」，**非**「随机 VA 命中 target」地址算术（§8.6 条4 固化该测法错误）。
- liveness（纪律10/错源㉓）：`python work/check_liveness.py` → EVIDENCE/liveness.json；7 行主 vt 均有非 atexit 构造写点（0x65CA00/0x401950/0x5523E0/0x4741F0/0x4741F0/0x401950/0x431A30 等）。

## 严禁项自查
- 语义栏全部重写（未沿用 direct-call delta 旧栏）；未以 direct call 单独升 grade（每行齐 ①②③④）；③a 未计 ③b；未用 atexit 析构器表；未做槽号匹配/slot-baseline；基线未用地址算术口径；未写台账；未改 coverage.tsv（只交 coverage_delta.tsv）。

## 交付
- PROGRESS.md / UNKNOWNS.md / DISAGREE.md / coverage_delta.tsv / EVIDENCE\\ / work\\。
