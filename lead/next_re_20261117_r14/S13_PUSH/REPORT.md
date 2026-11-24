# S13-PUSH — 攻 S13 的 proved 缺口

## 材料自校验
- 卡片：`lead\next_re_20261117_r14\_cards\S13-PUSH.md`（全文 70 行读完）
- `gamemd.exe` SHA-256 = `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（现场复算一致）
- Python 3.12.10 / capstone 5.0.7（skipdata=True）/ pefile 2024.8.26；ImageBase=0x400000，`.text=[0x401000,0x7E038D)`（VirtualSize）
- coverage.tsv sha256 = `FA5637DF6C87F0327C91770FF8E478378ACDDB1E3C5E6F157B033DE11AFC3836`
- function_atlas.tsv sha256 = `4527079B8E1556F0F34BC2C16068DDAEF7681EE2B6A5E1F2AADC61A73653DB69`
- 账面/筛选/取证脚本全在 `work/`（ledger.py → extract_pool.py → recore.py+screen.py → witness_core.py+witness.py → gen_row_evidence.py → gen_outputs.py）；未改 coverage.tsv / PANEL.md / R14_COMMON.md / 台账。

---

## 第一步 · S13 的 DoD 账面（先算，不采用卡片印象值）

源：盘上 `coverage.tsv` ∩ `function_atlas.tsv`，entry 大小写归一为大写 8 位；口径逐条对齐 `RULING_R15/work/strict_panel.py` 与 `COVERAGE/PANEL.md` 表头。

| 量 | 值 | 门槛 | 差距 |
|---|---:|---:|---:|
| `n`（S13 且 entry 在 atlas 内） | **240** | — | — |
| `named_L` | 216 | — | — |
| `named_S(R14)`（DoD 判定列） | **216** | ceil(0.9×240)=**216** | **0（恰好达标，零余量）** |
| `named_strict`（参考列） | 108 | 216 | 108 |
| `proved` | **100** | ceil(0.5×240)=**120** | **20** |
| `proved_strict` | 99 | 120 | 21 |

- S13 coverage 总行数 240，atlas 外 0。
- `proved_strict`(99) 比 `proved`(100) 少 1：该 1 行 `[已证]` 的语义栏含子串 `[未证]`。
- 结论：**S13 现在只差 proved 一项**（名义差 20、严格差 21）；named_S(R14) 恰好命中门槛，零余量。卡片给的印象值（proved 100 / strict 99 / 差 20）与盘上自算一致，但我独立复算得来。
- 由于 named_S(R14)=216 已达门槛，卡片第四步的触发条件「若 named_S(R14) 也不够」**不成立**，本卡不攻 named，产出空 `S13_named_delta.tsv`（仅表头）。

---

## 第二步 · 两通道基础率（诚实报数）

池 = S13 中 grade∈{[静态推断] 115, [未证] 25} 且 entry 在 atlas 内 = **140 行**。

机械筛选判据：
- **通道 A（③b② 可伪证错误码/返回约定）**：函数体内 `call` 后 4 条内出现 `test eax,eax`/`or eax,eax`/`cmp eax,imm`，其后 2 条内紧跟条件跳转；taken 与 fallthrough 的动作签名（直接 call 目标集/返回常量集/是否 ret/末端 eax）真正不同；并可伪证（call 站点哨兵 0/-1/1/0x8000xxxx，或被调静态可解析且有失败常量 ret + 另一 ret 原点）。分母=池=140。
- **通道 B（③b① 跳转表）**：`jmp dword ptr [reg*4 + disp]` 形式的间接跳表 + 前序边界 cmp/ja + 逐项目标可单独验证。分母=池=140。

基础率：

| channel | pool | hits | defensible | rate |
|---|---:|---:|---:|---:|
| A_③b②_raw（机械命中） | 140 | 13 | 13 | 0.0929 |
| A_③b②_no_eax_trap（剔 eax 覆写陷阱后真③b②） | 140 | 9 | 9 | 0.0643 |
| A_③b②_four_rings_literal（本卡字面四环齐全） | 140 | 9 | 6 | 0.0429 |
| A_③b②_four_rings_D40_strict（D-40 严格口径） | 140 | 9 | **0** | 0.0000 |
| B_③b①_jumptable | 140 | 0 | 0 | 0.0000 |

通道 A 机械命中 13 个 entry：`004251F0 00438A90 004684E0 006294D0 00629FD0 0062AC30 006FD460 00708080 0070FEE0 0075E0C0 0075E2C0 00772CD0 00772EB0`。通道 B 命中 0（池内无 `call/jmp [reg*4+disp]` 跳表形态，已用宽松 scale∈{2,4,8} 复扫确认 0）。

> 基础率诚实说明：机械命中率仅 9.29%；按卡片明列的 eax 覆写陷阱剔除后真③b② 9 行（6.43%）；再按本卡字面四环筛至 6 行（4.29%）；若按项目 D-40 严格口径（环④须独立于环②），可辩护行数 **0**。通道 B 对 S13 池无贡献。

---

## 第三步 · 逐行取证四环

13 个通道 A 命中逐个核完、每核完即落 `EVIDENCE/ROW_<entry>.txt`。四环判定摘要：

| # | entry | name | ①入口 | ②类身份 | ③③b②形态/地址锚 | ④使用见证 | 裁定 |
|---|---|---|---|---|---|---|---|
| 1 | 004251F0 | sub_004251F0 | ✓ | 未取得 | call 00489280 后 `mov eax,[0xA8B238]` 覆写 | direct-only | **③陷阱否决** |
| 2 | 00438A90 | BombClass::vslot13 | ✓ | BombClass vt+0x34 | call 004A1D50 后 `mov eax,[esi+0x24]` 覆写 | ctor vt | **③陷阱否决**（正是卡片 `[esi+0x??]` 形态） |
| 3 | 004684E0 | BulletClass::slot10 | ✓ | BulletClass vt+0x28 | `call [eax+0x10]@46862A → cmp eax,-1@46862D → je@468630 → fail 46865F` | ctor vt 466425/466566/46AEB5 | **本卡四环齐全（D40争议）** |
| 4 | 006294D0 | ParasiteClass::slot13 | ✓ | ParasiteClass vt+0x34 | call 00410410 后 `mov eax,[esi+0x44]` 覆写 | ctor vt | **③陷阱否决** |
| 5 | 00629FD0 | ParasiteClass::slot23 | ✓ | ParasiteClass vt+0x5C | `call 7C8E17(new)@62A0D8 → test eax,eax@62A0E0 → je@62A0E2 → fail 62A108`（另 2 站点覆写剔除） | ctor vt 629231/6292D8/6295FA/62AF7A | **本卡四环齐全（D40争议）** |
| 6 | 0062AC30 | sub_0062AC30 | ✓ | 未取得 | `call [edx+0x2c] → cmp eax,1 → jne` | 仅 1 direct | **④不合格**（direct-only） |
| 7 | 006FD460 | sub_006FD460 | ✓ | 未取得 | `call 7C8E17(new) → test eax,eax → je` | 3 direct | **④不合格**（direct-only） |
| 8 | 00708080 | death_handler | ✓ | 未取得 | `call [edx+0x2c] → cmp eax,1 → jne` | 3 direct | **④不合格**（direct-only） |
| 9 | 0070FEE0 | sub_0070FEE0 | ✓ | 未取得 | call [edx+0x480] 后 `mov eax,[esi+0x2ac]` 覆写 | direct | **③陷阱否决** |
| 10 | 0075E0C0 | WarheadTypeClass::slot5 | ✓ | WarheadTypeClass vt+0x14 | `call 410380@75E0F0 → test eax@75E0F5 → jl@75E0F7 → fail 75E2AE`（失败常量 0x80004003） | ctor vt 75E13E/75E516 | **本卡四环齐全（D40争议）** |
| 11 | 0075E2C0 | WarheadTypeClass::slot6 | ✓ | WarheadTypeClass vt+0x18 | `call 410320@75E2D1 → test eax@75E2D6 → jl@75E2D8 → fail 75E39C` | ctor vt 75E13E/75E516 | **本卡四环齐全（D40争议）** |
| 12 | 00772CD0 | WeaponTypeClass::slot5 | ✓ | WeaponTypeClass vt+0x14 | `call 410380@772CFD → test eax@772D02 → jl@772D04 → fail 772EA6`（第2站点 6CF240 被覆写剔除） | ctor vt 771E77/771F28/7730F7 | **本卡四环齐全（D40争议）** |
| 13 | 00772EB0 | WeaponTypeClass::slot6 | ✓ | WeaponTypeClass vt+0x18 | `call 410320@772EC1 → test eax@772EC6 → jl@772EC8 → fail 772F8C` | ctor vt 771E77/771F28/7730F7 | **本卡四环齐全（D40争议）** |

### 关键裁定依据
1. **eax 覆写陷阱（卡片明列，硬性）**：4 行（004251F0/00438A90/006294D0/0070FEE0）在 `call` 后、`test/cmp` 前立即 `mov eax,[mem]`，检查的是被覆写后的字段/全局，不是被调返回值 —— 不算③b②。00438A90 正是卡片点名的 `mov eax,[esi+0x??]` 形态。
2. **④ 的 direct-only 排除**：0062AC30/006FD460/00708080 无 vtable 槽，只有 E8 direct caller；卡片明写「direct-only 不足」，且 R14_COMMON §1 D-40「不得再据 direct call 单独升 [已证]」，环④不成立。
3. **6 行入选行的 ③b② 都是真形态**：失败/成功路径动作签名不同（HRESULT 失败 ret 原点是 `mov eax,0x80004003`、成功原点不同；allocation 失败 ret null），返回值真被 `test/cmp + jcc` 消费，无覆写。
4. **⚠ 环④ D-40 争议（必须正面回答）**：这 6 行的环④「活虚表派发」与环②「类身份」共用同一 vtable 槽。前序卡 `S13_KPROVED2`（46 行，四环 0）、`S13_K12` 审计、`SURVEY_RING24` 按 D-40 严格口径（环④须有「静态 global 接收者 exact 派发」或 direct call，不能与②同源）对同类行判环④ FAIL。本卡按卡片字面判据「真实调用者或活虚表派发」接受「ctor 装活 vt + 槽驻 + 派发站点」为活虚表派发，故列入 delta，但在每行 EVIDENCE 与本报告中明确标记：若审计采 D-40 严格口径，这 6 行应全部剔除（delta 变 0）。

### delta 产出
- `S13_delta.tsv`：**6 行**（本卡字面四环齐全）；entry 已核为大写十六进制、无 `0x` 前缀；6 列表头同 coverage.tsv 前 6 列；grade `[静态推断]→[已证]`。
- 每行一段自身地址锚的 one_line_semantics，未使用「循环内非栈写」、未整族共用 reason、未编造类名。

---

## 第四步 · named 通道（本卡不触发）

第一步账面 `named_S(R14)=216 = 门槛 ceil(0.9×240)=216`，named 已达标（零余量），卡片第四步触发条件「若 named_S(R14) 也不够」不成立，故：
- 不攻 named；`S13_named_delta.tsv` 仅表头、0 数据行。
- 备注：named 零余量是风险点 —— 任何一行 `Class::xxx` 被降名或回退 `sub_` 都会使 named 跌破门槛（参照 COMMON-R8 对 `00773030` 的裁定：降级会 216→215=89.58% 跌破）。本卡未改动任何名字。

---

## 明确回答：按本次产出，S13 还差多少行、能不能达标

现状（盘上自算）：`proved=100`，门槛 `ceil(0.5×240)=120`，**差 20 行**；`named_S(R14)=216` 恰达门槛。

按本卡 delta（6 行，`[静态推断]→[已证]`）全部并入后：

| 口径 | 现 proved | 本卡可并 | 并入后 | 门槛 | 达标? | 仍差 |
|---|---:|---:|---:|---:|---|---:|
| **本卡字面四环**（接受活虚表派发） | 100 | +6 | **106** | 120 | **否** | **14** |
| **D-40 严格口径**（同类行前卡判 0） | 100 | +0 | **100** | 120 | **否** | **20** |

**结论：无论按哪种口径，S13 靠本通道都不能达标。** 乐观口径 100→106 仍差 14 行；严格口径一行都并不进、仍差 20 行。通道 A 池内机械命中上限只有 13 行（去陷阱 9 行、四环 6 行），通道 B 为 0 —— 可辩护增量远小于所需的 20 行。

**缺口性质**：S13 的剩余 `[静态推断]/[未证]` 池（140 行）里，能过 ③b② 真形态的已基本挖尽（本卡 6 行均为 Warhead/Weapon/Bullet/Parasite 的 HRESULT / allocation-null 模板族，与 K9/K8RECHK 已并的 11+11 行同源），剩下的卡在环④：无 direct caller、无可独立于环②的活虚表派发证据。要补满 14–20 行须换通道 —— 例如 ③b④ 有界循环（但本项目已裁定「循环内非栈写」在本镜像普遍不成立，禁用）、③a 语义直接证据、或新的独立使用见证通道；继续在同族模板里筛不会产生达标级增量。

---

## 附：输出清单
- `REPORT.md`（本文件）
- `S13_delta.tsv`（6 行）、`S13_named_delta.tsv`（0 行）
- `base_rate.tsv`、`PROGRESS.md`、`LEDGER.txt`
- `EVIDENCE/ROW_<entry>.txt` × 13（含未入选行的否决理由）
- `work/`（全部复算脚本与中间 JSON/TXT）
