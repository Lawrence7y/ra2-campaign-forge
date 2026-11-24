# S06-K3 PROGRESS（卡号 S06-K3）

目标 `ra2youli\gamemd.exe` SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（自算一致，4,825,360 B）｜静态卡，未跑真机｜写域仅 `S06-K3\`。Python 3.12.10 + capstone 5.0.7(skipdata=True) + pefile 2024.8.26。

## 一句话结论
双支撑 **17/63 → 19/63**（+`+0x3C`/`+0x11C`，cell 数组基址第三访问形式）；S06 proved **103 → 104**（0x721A50 升 `[已证]`）；**矿石经济链打通**（规则 `Value=`→+0xB8→每帧 0x485020）。

## 纪律 9 停机核验（派卡数字 vs 盘上现值）
派卡给 atlas 850/named 385(45.29%)/proved 96(11.29%)；**盘上实测 atlas_n=848/named_L=384(45.28%)/named_S=383(45.17%)/proved=103(12.15%)**，与 PANEL.md:38 逐字自洽。按派卡口径警告以盘上现值为准，未凑派卡数。50% 门槛=424，差 **321** 个 proved（量大，本卡以立方法为主）。见 `DISAGREE.md` D1。

## 结论表
| 项 | 结论 | 级 | 证据 |
|---|---|---|---|
| T1 靶子 | 848 行 S06∩atlas → TARGETS.tsv；named_S 383；proved 103 | 已证 | `EVIDENCE/t1_stats.txt`、`TARGETS.tsv` |
| T2 方法集口径 | **42 函数**（32 虚槽+10 非虚）；方法集内虚调用 **43**；全 .text `call/jmp [reg+disp]` **18,949**（审计 18,946，差 3，见 D2） | 已证 | `EVIDENCE/k3_methodset.txt` |
| T2 双支撑 | **19/63**：审计 17 + 新增 `+0x3C`(W2/R7)、`+0x11C`(W2/R4)。读点 provenance 均经 `mov reg,[0x87F924]→[reg+idx*4]` 取 cell*，字节级确凿 | 已证/静态推断 | `EVIDENCE/k3_fieldscan2.tsv`、`k3_diag_3c.py`、`k3_diag_11c.py` |
| T2 强口径 | W≥1&R≥3 全表 14 个（12∈审计17 + 3C/11C）；其余 44 字段多为 ctor 只写、无 CellClass 读点，不凑数 | 已证 | `EVIDENCE/k3_fieldscan2.txt` |
| T3 MapClass 定界 | vtable `0x7ED404` **30 槽**；COL `0x8054C8`→TD `0x816BC0`→名 `.?AVMapClass@@`（RTTI 实测，§958 一致）；槽后 `0x7ED47C`=`0x8055E0`(COL) | 已证 | `EVIDENCE/k3_t3_mapslots.txt`、`k3_t4_rtti_full.txt` |
| T3 `0x87F924` | MapClass+0x13C 指针字段：**全镜像 0 绝对写 / 399 绝对读**（与 S06-K2 一致） | 已证 | `EVIDENCE/k3_t3_87f924.txt` |
| T3 滚动原点 | 全镜像绝对寻址写：`0x886FA0` **2 写**(0x40DA2C,0x4A8987)、`0x886FA4` **2 写**(0x40DA31,0x4A8990)。支持 §4.4「各2写」，a-W177-G「各1写」为限定范围，见 D3 | 已证 | `EVIDENCE/k3_t3_scroll.txt`、`k3_t4_b8_scroll.py` |
| T4 矿石表 | vftable `0x7F56BC`→名 `.?AV?$DynamicVectorClass@PAVTiberiumClass@@@@`，元素类 **TiberiumClass**；静态初始化 `0x721640`(写 vt/Count=0/Growth=10) | 已证 | `EVIDENCE/k3_t4_rtti_full.txt`、`t34_console.txt` |
| T4 +0xB8 价值 | `0x721A50` 内 `0x721B0C`：`CCINIClass::ReadInteger('Value'@0x8448EC)`→`[type+0xB8]`；'Power'→+0xBC。atlas strings 证 Resource 类型字段集 | 已证 | `EVIDENCE/k3_t4_final.txt`、`k3_callers.py` |
| T4 调用点全集 | `0x485020` 直接 E8 调用 **20 处 / 7 调用者函数**：AnimClass::vslot23、AircraftClass::slot206、BuildingClass::slot206、sub_4DD2F0、sub_568BB0、sub_684C30、sub_6D7840 | 已证 | `EVIDENCE/k3_t4_ore_calls.txt`、`k3_t4_final.py` |
| T4 链 | 地图/规则加载→`0x721A50` 读 Value→+0xB8→每帧 `0x485020` 读 cell+0x44/0x11E/+0xB8→价值×(密度+1) | 静态推断 | `LAYOUT.md` §T4 |

## 给审计员的 3 个可复算数字
1. `python work/k3_methodset.py` → 42 方法 / 43 方法集虚调用 / 18949 全扫。
2. `python work/k3_fieldscan2.py` → STRONG 14；+0x3C W2/R7、+0x11C W2/R4。
3. `python work/k3_t34_collect.py` + `k3_t4_rtti.py` + `k3_t4_final.py` → 30 槽 / 各2写 / RTTI 名 / Value→+0xB8。

## 交付
`TARGETS.tsv`(848)、`LAYOUT.md`、`PROBE_OFFSETS.md`、`UNKNOWNS.md`、`DISAGREE.md`、`EVIDENCE/`(15 文件)、`work/`(14 脚本)、`coverage_delta.tsv`(2 行)。未写台账、未改主 coverage、未改游戏文件、未 git commit、未跑真机。
