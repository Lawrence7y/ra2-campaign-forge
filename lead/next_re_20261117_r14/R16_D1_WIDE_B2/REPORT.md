# R16-D1-WIDE-B2 执行报告

> 角色：执行器 · 卡号 R16-D1-WIDE-B1（批次 B2）· 日期 2026-11-21（R16 第 22 轮起）
> 写域：`lead\next_re_20261117_r14\R16_D1_WIDE_B2\`（仅此目录）；**未写 `COVERAGE\coverage.tsv`**；`gamemd.exe` 仅只读打开。
> 披露指针：每行 ④ 自带 D-47 披露并指向 **§12.6**（`见 R14_COMMON §12.6 与 PANEL 对应披露`）。

## 0. 一句话结论
**只补第 4 列 ④ 成文、未改 grade/判定、未并表。** 本批 18 行全部取得完整 ④ 数据（vt/slot/装表点/宿主/RTTI/装配形态），
6 项字节复核全通过；盘上复核无已含 ④ 行（无 SKIP-ALREADY）。其中 13 行用 final.tsv 决定性表判 OK，
5 行按卡面 §3.4 类一致优先另取行名类自己的活表判 CLASS_FIX；18 行净新增写入 `delta.tsv`。

## 1. 批次派生
| 阶段 | 行数 | 说明 |
|---|---:|---|
| sieve_all.tsv（D-52 宽读集合） | 81 | 判据 S1–S7 在 `R16_SIEVE_D1_WIDE/sieve.py`，直接采用，未重筛 |
| 其中 has_ring4_on_disk==是（盘上已有 ④，跳过） | 16 | 不重做 |
| 待做 | 65 | 81 − 16 |
| 按 entry 升序第 19–36 行（本批 B2） | 18 | `no_rows[18:36]`；与 B1 前 18 行 entry 集合交集 = 0（已 assert） |

## 2. 盘上现值复核（SKIP-ALREADY）
逐行读当前 `coverage.tsv` 第 4 列：`含④` 行数 = **0**，无 ④ 行数 = **18**。
无并发并表覆盖本批行 ⇒ 无 `SKIP-ALREADY`，18 行全部净新增。

## 3. 装配形态分类计数（D-50）
| install_form | 行数 | 判据 |
|---|---:|---|
| mov_abs | 4 | 装表指令 `mov [abs], vt`（写入静态 global） |
| ctor_body | 14 | 装表指令 `mov [reg], vt`（构造器/工厂体内写对象 vptr） |
| reg | 0 | 非构造器的寄存器形态 |
| other | 0 | 其余 |

## 4. 逐行状态计数
| status | 行数 |
|---|---:|
| OK | 13 |
| SKIP-ALREADY | 0 |
| SKIP | 0 |
| CLASS_FIX | 5 |

## 4.1 CLASS_FIX 明细（卡面 §3.4 类一致优先）
final.tsv（`R16_PROBE_4FINAL`，取 ext[0] 决定性表）对下列 5 行选中的表，其 RTTI 类与行名类不符；
按卡面 §3.4「按类一致优先另取该行名类自己的活表」改取行名类本表，并在 fields.tsv 标 CLASS_FIX 逐字披露。
改取表均：同址持有该 entry、COL offset=0、有体外装表点、6 项字节复核全真、槽值==entry。

| entry | 行名类 | 原决定性表(vt/RTTI) | 改取行名类本表(vt/RTTI) | 装表点/宿主 | 装配形态 |
|---|---|---|---|---|---|
| 004A8960 | TabClass | 007E1964 / .?AVMouseClass@@ | 007EDFB4 / .?AVTabClass@@ | 005BE9C7 / 005BE9B0 | ctor_body |
| 004A9840 | TabClass | 007E1964 / .?AVMouseClass@@ | 007EDFB4 / .?AVTabClass@@ | 005BE9C7 / 005BE9B0 | ctor_body |
| 004AAD30 | TabClass | 007E6114 / .?AVDisplayClass@@ | 007EDFB4 / .?AVTabClass@@ | 005BE9C7 / 005BE9B0 | ctor_body |
| 004AAE90 | TabClass | 007E1964 / .?AVMouseClass@@ | 007EDFB4 / .?AVTabClass@@ | 005BE9C7 / 005BE9B0 | ctor_body |
| 004AB9B0 | DisplayClass | 007E1964 / .?AVMouseClass@@ | 007E6114 / .?AVDisplayClass@@ | 004A8830 / 004A8730 | ctor_body |

`0054E890`/`0054EA70` 行名 `T_DynamicVectorClass_PAUKamikazeControl__` 为模板伪名，
RTTI `.?AV?$DynamicVectorClass@PAUKamikazeControl@@@@` 为同名模板展开（token 命中，B1 `0040F870` 同口径），
判同类、**不**标 CLASS_FIX，已在 fields.tsv note 披露。

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

- **mov_abs** `004F4320`（MouseClass::slot9）：
  ```
④ 活表槽位见证：MouseClass::slot9（vt=007E1964，槽 9 值=004F4320，COL=007FAB38 offset=0，RTTI=00816C90→.?AVMouseClass@@；装表点 0040D1B2 位于 0040D1B0 体内，装配方式=mov_abs（mov [abs], vt；实测指令 mov dword ptr [0x87f7e8], 0x7e1964），entry 体外） ④升级句：MouseClass::slot9（④ 表属类与行名类一致，均为 MouseClass；该槽即其 vt=007E1964 表 slot9，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```
- **ctor_body** `0046C890`（BulletTypeClass::slot8_deleting_dtor）：
  ```
④ 活表槽位见证：BulletTypeClass::slot8（vt=007E4948，槽 8 值=0046C890，COL=007FC868 offset=0，RTTI=0081AFB0→.?AVBulletTypeClass@@；装表点 0046BCE6 位于 0046BBC0 体内，装配方式=ctor_body（构造器体内 mov [reg], vt；实测指令 mov dword ptr [esi], 0x7e4948），entry 体外） ④升级句：BulletTypeClass::slot8（④ 表属类与行名类一致，均为 BulletTypeClass；该槽即其 vt=007E4948 表 slot8，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
  ```

## 9. 产物清单
- `delta.tsv`（18 净新增行） / `fields.tsv`（18 行） / `REPORT.md` / `derive_raw.py` / `raw_dump.json` / `classfix_scan.py` / `classfix_scan.json` / `generate.py`

**只补 ④ 成文、未改 grade/判定、未并表。**
