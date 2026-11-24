# R16-D1-WIDE-B3 执行报告

> 角色：执行器 · 卡号 R16-D1-WIDE-B1（批次 B3）· 日期 2026-11-21（R16 第 22 轮起）
> 写域：`lead\next_re_20261117_r14\R16_D1_WIDE_B3\`（仅此目录）；**未写 `COVERAGE\coverage.tsv`**；`gamemd.exe` 仅只读打开。
> 披露指针：每行 ④ 自带 D-47 披露并指向 **§12.6**（`见 R14_COMMON §12.6 与 PANEL 对应披露`）。

## 0. 一句话结论
**只补第 4 列 ④ 成文、未改 grade/判定、未并表。** 本批 18 行全部取得完整 ④ 数据；盘上复核无 SKIP-ALREADY；6 项字节复核 18/18×6 全通过；宿主身份校验（卡面三条教训）18/18 通过。其中 16 行 OK、2 行 CLASS_FIX；另 6 行按教训①②改取真构造器装表点（SITE_FIX，status 仍记 OK，类一致不变）。

## 1. 批次派生
| 阶段 | 行数 | 说明 |
|---|---:|---|
| sieve_all.tsv（D-52 宽读集合） | 81 | 判据 S1–S7 在 `R16_SIEVE_D1_WIDE/sieve.py`，直接采用，未重筛 |
| has_ring4_on_disk==是（盘上已有④，跳过） | 16 | 不重做 |
| 待做 | 65 | 81 − 16 |
| 按 entry 升序第 37–54 行（本批 B3） | 18 | `no_rows[36:54]`；与 B1/B2 entry 集合交集 = 0（assert） |

## 2. 盘上现值复核（SKIP-ALREADY）
逐行读当前 `coverage.tsv` 第 4 列：含④ 行数 = **0**，无④ 行数 = **18**；无并发并表覆盖 ⇒ 无 SKIP-ALREADY，18 行全净新增。

## 3. 装配形态分类计数（D-50，含宿主身份校验）
| install_form | 行数 | 判据 |
|---|---:|---|
| ctor_body | 13 | 写 this(disp0) 且宿主真构造器/工厂、无删除签名 |
| mov_abs | 4 | mov [abs],vt 且 abs 在 .data |
| reg | 1 | 写 this 但宿主为析构器（非构造器） |
| other | 0 | 其余 |

说明：`mov_abs` 4 行的目标 0xAC4910 / 0xB04BD0 均在 `.data`（静态 global），由 capstone 实测非栈槽、非堆。

## 4. 逐行状态计数
| status | 行数 |
|---|---:|
| OK | 16 |
| SKIP-ALREADY | 0 |
| SKIP | 0 |
| CLASS_FIX | 2 |

### 4.1 CLASS_FIX 明细（卡面 §3.4 类一致优先）
| entry | 行名类 | 原决定性表(vt/RTTI) | 改取行名类本表(vt/RTTI) | 装表点/宿主 | 形态 |
|---|---|---|---|---|---|
| 005F4B10 | ObjectClass | 见 fields.tsv note | 007EF060 / .?AVObjectClass@@ | 005F39BA / 005F3900 | ctor_body |
| 00631CC0 | FilePipe | 见 fields.tsv note | 007E4DA0 / .?AVFilePipe@@ | 007BA426 / 007BA420 | reg |

### 4.2 SITE_FIX 明细（教训①②：宿主身份校验 + 禁最低地址命中）
| entry | 原决定性装表点（缺陷） | 改取真构造器装表点/宿主 |
|---|---|---|
| 0065CAC0 | 见 fields.tsv note | 0065CAA8 / 0065CA80 |
| 0065CDD0 | 见 fields.tsv note | 0065CAA8 / 0065CA80 |
| 0065CF00 | 见 fields.tsv note | 0065CAA8 / 0065CA80 |
| 0065D0D0 | 见 fields.tsv note | 0065CAA8 / 0065CA80 |
| 0065D150 | 见 fields.tsv note | 0047AA3C / 0047AA30 |
| 0065D190 | 见 fields.tsv note | 0047AA3C / 0047AA30 |

## 5. 六项字节复核 + 宿主身份复核
18 行回 `gamemd.exe`（只读）复算六项：① `u32(vt+slot*4)==entry` ② COL sig==0 ③ COL offset==0 ④ TD/mangled 以 `.?A` 开头 ⑤ 装表点在 entry 体外 ⑥ vt 取得。
**18/18 × 6 项全 True**（all_chk6=True）；vt 取得行数 = 18/18；宿主身份校验（ctor_body 写 this@disp0 且真构造器无删除签名 / mov_abs 目标在 .data / reg 写 this 且宿主析构器）18/18 通过（all_hv=True）。

## 6. 行行不同自检（entry 归一后）
| 检查 | 结果 |
|---|---|
| 完整 ④ 正文 set() | 18/18 不同 |
| 8 位十六进制归一为 ENTRY 后 set() | 18/18 不同 |

## 7. 字节复核与哈希
| 项 | 值 |
|---|---|
| coverage.tsv 读入字节数 | 4097787 |
| coverage.tsv sha256（未改） | `412ED7E36BC1AD4907763FEBB3A68D5FDABB3F0D2C999800444B57098B1AB2E1` |
| gamemd.exe sha256（未改，只读打开） | `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` |
| 第 4 列严格前缀自检 | True |
| 第 1/2/3/5/6/7/8 列逐字节相同 | True |

## 8. 样例 ④（mov_abs / ctor_body 各一）

- **mov_abs** `0062B250`（DynamicVectorClass<ParasiteClass*>::SetCapacity）：
  ```
④ 活表槽位见证：DynamicVectorClass<ParasiteClass*>::slot2（vt=007EF824，槽 2 值=0062B250，COL=00807A50 offset=0，RTTI=00836608→.?AV?$DynamicVectorClass@PAVParasiteClass@@@@；装表点 006291AD 位于 00629190 体内，装配方式=mov_abs（mov [abs], vt；实测指令 mov dword ptr [0xac4910], 0x7ef824），entry 体外） ④升级句：DynamicVectorClass<ParasiteClass*>::slot2（④ 表属类与行名类一致，均为 DynamicVectorClass<ParasiteClass*>；该槽即其 vt=007EF824 表 slot2，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```

- **ctor_body** `005B3A60`（MissionClass::scalar_deleting_destructor）：
  ```
④ 活表槽位见证：MissionClass::slot8（vt=007EDCC0，槽 8 值=005B3A60，COL=00805D28 offset=0，RTTI=00817B18→.?AVMissionClass@@；装表点 005B2DE9 位于 005B2DA0 体内，装配方式=ctor_body（构造器体内 mov [reg], vt；实测指令 mov dword ptr [esi], 0x7edcc0），entry 体外） ④升级句：MissionClass::slot8（④ 表属类与行名类一致，均为 MissionClass；该槽即其 vt=007EDCC0 表 slot8，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```

## 9. 清单异常披露
`005F4B10` 在 `sieve_all.tsv` 的 `verdict_polarity=NEG`（唯一一行负极性），且其 ② 审计引用（C06_census）自述为「未复发」的全量普查；行名 `ObjectClass::DrawWrapper/DrawIfVisible` 与 final.tsv 决定性表类（AircraftClass）不符。本执行器未自行重筛（卡面 §2 要求直接用清单），照常补 ④ 并按 §3.4 标 CLASS_FIX 改取 ObjectClass 本表；**特别报出此行请合并员/审计员复核是否应从宽读集合剔除**。

## 10. 产物清单
- `delta.tsv`（18 净新增行） / `fields.tsv`（18 行） / `REPORT.md` / `raw_dump.json` / `derive.py`（本生成脚本）

**只补 ④ 成文、未改 grade/判定、未并表。**
