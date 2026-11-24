# R16-D1-WIDE-B1 执行报告

> 角色：执行器 · 卡号 R16-D1-WIDE-B1 · 日期 2026-11-21（R16 第 22 轮起）
> 写域：`lead\next_re_20261117_r14\R16_D1_WIDE_B1\`（仅此目录）；**未写 `COVERAGE\coverage.tsv`**；`gamemd.exe` 仅只读打开（`pefile.PE(..., fast_load=True)` + `open('rb')`）。
> 披露指针：每行 ④ 自带 D-47 披露并指向 **§12.6**（`见 R14_COMMON §12.6 与 PANEL 对应披露`）。

## 0. 一句话结论
**只补第 4 列 ④ 成文、未改 grade/判定、未并表。** 本批 18 行全部取得完整 ④ 数据（vt/slot/装表点/宿主/RTTI/装配形态），
6 项字节复核全通过；盘上复核无已含 ④ 行（无 SKIP-ALREADY）；18 行净新增写入 `delta.tsv`。

## 1. 批次派生
| 阶段 | 行数 | 说明 |
|---|---:|---|
| sieve_all.tsv（D-52 宽读集合） | 81 | 判据 S1–S7 在 `R16_SIEVE_D1_WIDE/sieve.py`，直接采用，未重筛 |
| 其中 has_ring4_on_disk==是（盘上已有 ④，跳过） | 16 | 不重做 |
| 待做 | 65 | 81 − 16 |
| 按 entry 升序第 1–18 行（本批 B1） | 18 | 本卡范围 |

## 2. 盘上现值复核（SKIP-ALREADY）
逐行读当前 `coverage.tsv` 第 4 列：`含④` 行数 = **0**，无 ④ 行数 = **18**。
无并发并表覆盖本批行 ⇒ 无 `SKIP-ALREADY`，18 行全部净新增。

## 3. 装配形态分类计数（D-50）
| install_form | 行数 | 判据 |
|---|---:|---|
| mov_abs | 8 | 装表指令 `mov [abs], vt`（写入静态 global） |
| ctor_body | 10 | 装表指令 `mov [reg], vt`（构造器/工厂体内写对象 vptr） |
| reg | 0 | 非构造器的寄存器形态 |
| other | 0 | 其余 |

## 4. 逐行状态计数
| status | 行数 |
|---|---:|
| OK | 18 |
| SKIP-ALREADY | 0 |
| SKIP | 0 |
| CLASS_FIX | 0 |

## 5. 六项字节复核结果
18 行逐行回 `gamemd.exe`（只读）复算 6 项：① `u32(vt+slot*4)==entry` ② COL sig==0 ③ COL offset==0 
④ `TD=u32(COL+12)`、`cstr(TD+8)` 以 `.?A` 开头 ⑤ 装表点在 entry 体外 ⑥ vt 取得。
**18/18 × 6 项全 True**（all_chk6=True）。vt 取得行数 = 18/18。

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

- **mov_abs** `0040B880`（DynamicVectorClass<BombClass*>::SetCapacity）：
  ```
④ 活表槽位见证：DynamicVectorClass<BombClass*>::slot2（vt=007E17CC，槽 2 值=0040B880，COL=007FA6A8 offset=0，RTTI=00816918→.?AV?$DynamicVectorClass@PAVBombClass@@@@；装表点 0040B563 位于 0040B540 体内，装配方式=mov_abs（mov [abs], vt；实测指令 mov dword ptr [0x87f5d8], 0x7e17cc），entry 体外） ④升级句：DynamicVectorClass<BombClass*>::slot2（④ 表属类与行名类一致，均为 DynamicVectorClass<BombClass*>；该槽即其 vt=007E17CC 表 slot2，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```
- **ctor_body** `00413F80`（AircraftClass::vslot9）：
  ```
④ 活表槽位见证：AircraftClass::slot9（vt=007E22A4，槽 9 值=00413F80，COL=007FB4C0 offset=0，RTTI=00817B90→.?AVAircraftClass@@；装表点 00413D87 位于 00413D20 体内，装配方式=ctor_body（构造器体内 mov [reg], vt；实测指令 mov dword ptr [esi], 0x7e22a4），entry 体外） ④升级句：AircraftClass::slot9（④ 表属类与行名类一致，均为 AircraftClass；该槽即其 vt=007E22A4 表 slot9，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```

## 9. 产物清单
- `delta.tsv`（18 净新增行） / `fields.tsv`（18 行） / `REPORT.md` / `derive_raw.py` / `raw_dump.json` / `generate.py`

**只补 ④ 成文、未改 grade/判定、未并表。**
