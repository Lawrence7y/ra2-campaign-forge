# NAMED-PUSH — S05 B1 批次（有名字的 ③b② 候选，攻 proved 增量）

> 状态：**完成**。执行纪律已遵：先建目录、先写骨架、逐行核完即落盘 EVIDENCE；每 5 行追加 PROGRESS。
> 卡片：`lead\next_re_20261117_r14\_cards\NAMED-PUSH.md`（全文 73 行读完）
> 本批：**B1** = `SURVEY_3B2\hits_detail.tsv` 中 `subsystem==S05` AND `p3b2_named==True` 的行按 entry 升序取**前 18 行**。
> 输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S05_B1\`（卡片中 `<你的子系统>`=S05、`<你的目录>`=本目录）。

## 材料自校验
- 目标：`ra2youli\gamemd.exe`，期望 SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`；现场 `Get-FileHash` 复算一致。
- ImageBase `0x400000`；`.text=[0x401000,0x7E038D)`（VirtualSize）。
- Python 3.12.10 / capstone 5.0.7（**skipdata=True**）/ pefile 2024.8.26；无 venv、未 pip install。
- 只读输入：`SURVEY_3B2\hits_detail.tsv`（仅当线索）。未改 coverage.tsv / PANEL.md / R14_COMMON.md / 台账 / SURVEY_3B2 下任何产物。写域仅本目录。

## 筛选命令（得到本批 18 个 entry）

PowerShell（在 R14 目录下执行）：

```powershell
$hits = "SURVEY_3B2\hits_detail.tsv"
Import-Csv -Path $hits -Delimiter "`t" |
  Where-Object { $_.subsystem -eq 'S05' -and $_.p3b2_named -eq 'True' } |
  Sort-Object { [Convert]::ToInt32($_.entry,16) } |
  Select-Object -First 18 |
  Format-Table entry,subsystem,name,grade,size,n_insn,n_call,n_site -AutoSize
```

等价 Python 落盘于 `work/filter_b1.py`。结果：S05 named=True 共 **39** 行；B1 = 前 18 行（entry 升序）。18 个 entry：

| # | entry | name(原样) | grade | size |
|---:|---|---|---|---:|
| 1 | 00410380 | AbstractClass | [静态推断] | 90 |
| 2 | 00410C30 | AbstractTypeClass::vslot8 | [静态推断] | 134 |
| 3 | 00414290 | AircraftClass::vslot0 | [静态推断] | 95 |
| 4 | 00414BB0 | AircraftClass::vslot23 | [静态推断] | 1544 |
| 5 | 004176F0 | AircraftClass::vslot289 | [静态推断] | 1210 |
| 6 | 00417CC0 | AircraftClass::vslot29 | [静态推断] | 692 |
| 7 | 004190B0 | AircraftClass::vslot101 | [静态推断] | 1147 |
| 8 | 004196B0 | AircraftClass::vslot107 | [静态推断] | 261 |
| 9 | 0041A9E0 | AircraftClass::vslot240 | [静态推断] | 159 |
| 10 | 0041AA80 | AircraftClass::vslot288 | [静态推断] | 831 |
| 11 | 0041B890 | AircraftClass::vslot311 | [静态推断] | 103 |
| 12 | 0041BBD0 | AircraftClass::vslot330 | [静态推断] | 96 |
| 13 | 0041CB20 | AircraftTypeClass::vslot35 | [静态推断] | 43 |
| 14 | 0041CC20 | AircraftTypeClass::vslot25 | [静态推断] | 388 |
| 15 | 0041CE20 | AircraftTypeClass::vslot5 | [静态推断] | 100 |
| 16 | 0041CE90 | AircraftTypeClass::vslot6 | [静态推断] | 29 |
| 17 | 0041CFE0 | AircraftTypeClass::vslot8 | [静态推断] | 141 |
| 18 | 00450630 | fn_00450630 | [静态推断] | 915 |

## 判定口径（严格 D-40，宁严不宽）
1. **①入口**：entry 在 `.text` 内、函数边界自洽（atlas size + 反汇编连贯，skipdata=0 全 18 行）。
2. **②类身份**：必须独立取证——`[vt-4]=COL(sig=0)→[COL+0xC]=TD→TD+8 名串` 且 `vt[slot]==entry`。
   - 注意：同批复用脚本 `witness_core.resolve_slot` 的回扫窗口仅 k=0..40，对高 vslot 号（101/107/240/288/289/311/330）会误报 rtti=None。
   - 本卡用扩展回扫 `work/resolve_rtti_ext.py`（kmax=400）把它们全部钉死：如 004176F0 槽 0x7E2728 - vt 0x7E22A4 = 0x484 = 289×4、名串 .?AVAircraftClass@@；0041BBD0 槽 0x7E27CC - vt 0x7E22A4 = 0x528 = 330×4。全部 slot offset/4 == 名字线索槽号，**不是拿 slotN 类名当已证**。
   - ② 与 ④ 不同源：② 走 `.rdata` RTTI 数据链，④ 走 `.text` 构造安装/派发链。
3. **③整体合同**：只认 ③b。bool 0/1 不算 ③b②（D-46(A)）；禁被调用者内部写充循环非栈写；禁 ③a（纯转发/getter/malloc 模板假句/无分支直线）；跳表须每路可单独验证。
4. **④使用见证**：真实调用者或活虚表派发，direct-only 不足，且与 ② 不同源。
5. **三陷阱**：eax 覆写、多路同一 call、模板假句——逐行排查（本批 3 条 PASS 行 eax 覆写均为 0）。

## 基础率（诚实报数）

分母 = 本批 18 行。

| 档 | 行数 | 口径 |
|---|---:|---|
| 本批行数 | 18 | S05 named=True 候选 asc 前 18 |
| ①入口 PASS | 18 | 全部在 .text、反汇编连贯（skipdata=0） |
| ②类身份取得（RTTI 独立钉死） | **16** | 16 行虚表槽驻留+RTTI 名串+slot 号自洽；00410380/00450630 无槽无 RTTI -> FAIL |
| ③③b 成立 | **3** | 00410C30、00414290、0041CFE0（③b②）；余为 bool/枚举/unknown 返回/模板假句/状态机不可逐路验 |
| ④独立使用见证（活虚表派发） | **16** | 16 行均有构造安装点 + [reg+off] 派发链；2 个无槽行 direct-only 不足 |
| **四环齐全（严格 D-40）** | **3** | 00410C30、00414290、0041CFE0 |

## 本批 18 行总表（entry / ②③④ / 是否产出）

| # | entry | name(原样) | ①入口 | ②类身份 | ③③b | ④使用见证 | ②④独立 | 裁定 | 产出 |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | 00410380 | AbstractClass | PASS | FAIL(无槽无RTTI) | FAIL(p3=0 转发桩) | FAIL(direct-only) | n/a | 不成立 | 否 |
| 2 | 00410C30 | AbstractTypeClass::vslot8 | PASS | PASS(.?AVAbstractTypeClass@@ slot8) | **PASS(③b② -1哨兵+非栈写循环)** | PASS(活vt+派发) | 是 | **成立** | **是** |
| 3 | 00414290 | AircraftClass::vslot0 | PASS | PASS(.?AVAircraftClass@@ slot0) | **PASS(③b② HRESULT E_POINTER/NOINTERFACE)** | PASS(活vt+派发) | 是 | **成立** | **是** |
| 4 | 00414BB0 | AircraftClass::vslot23 | PASS | PASS(.?AVAircraftClass@@ slot23) | FAIL(间接/malloc/unknown+跳表仅2目标) | PASS(活vt+派发) | 是 | 不成立 | 否 |
| 5 | 004176F0 | AircraftClass::vslot289 | PASS | PASS(.?AVAircraftClass@@ slot289 扩展钉死) | FAIL(imm=1布尔+间接+跳表3目标) | PASS(活vt+派发) | 是 | 不成立 | 否 |
| 6 | 00417CC0 | AircraftClass::vslot29 | PASS | PASS(.?AVAircraftClass@@ slot29) | FAIL(p3=0) | PASS(活vt+派发) | 是 | 不成立 | 否 |
| 7 | 004190B0 | AircraftClass::vslot101 | PASS | PASS(.?AVAircraftClass@@ slot101 扩展钉死) | FAIL(枚举{0xA,0x14}+双跳表状态机) | PASS(活vt+派发) | 是 | 不成立 | 否 |
| 8 | 004196B0 | AircraftClass::vslot107 | PASS | PASS(.?AVAircraftClass@@ slot107 扩展钉死) | FAIL(p3=0) | PASS(活vt+派发) | 是 | 不成立 | 否 |
| 9 | 0041A9E0 | AircraftClass::vslot240 | PASS | PASS(.?AVAircraftClass@@ slot240 扩展钉死) | FAIL(串比较{0}+TEST_EAX布尔探测) | PASS(活vt+派发) | 是 | 不成立 | 否 |
| 10 | 0041AA80 | AircraftClass::vslot288 | PASS | PASS(.?AVAircraftClass@@ slot288 扩展钉死) | FAIL(imm=1布尔+间接/unknown) | PASS(活vt+派发) | 是 | 不成立 | 否 |
| 11 | 0041B890 | AircraftClass::vslot311 | PASS | PASS(.?AVAircraftClass@@ slot311 扩展钉死) | FAIL(p3=0) | PASS(活vt+派发) | 是 | 不成立 | 否 |
| 12 | 0041BBD0 | AircraftClass::vslot330 | PASS | PASS(.?AVAircraftClass@@ slot330 扩展钉死) | FAIL(cmp eax,1布尔+getter缓存) | PASS(活vt+派发) | 是 | 不成立 | 否 |
| 13 | 0041CB20 | AircraftTypeClass::vslot35 | PASS | PASS(.?AVAircraftTypeClass@@ slot35) | FAIL(malloc+构造模板假句) | PASS(活vt+派发) | 是 | 不成立 | 否 |
| 14 | 0041CC20 | AircraftTypeClass::vslot25 | PASS | PASS(.?AVAircraftTypeClass@@ slot25) | FAIL(空判+对象初始化模板假句) | PASS(活vt+派发) | 是 | 不成立 | 否 |
| 15 | 0041CE20 | AircraftTypeClass::vslot5 | PASS | PASS(.?AVAircraftTypeClass@@ slot5) | FAIL(p3=0) | PASS(活vt+派发) | 是 | 不成立 | 否 |
| 16 | 0041CE90 | AircraftTypeClass::vslot6 | PASS | PASS(.?AVAircraftTypeClass@@ slot6) | FAIL(p3=0 极小函数) | PASS(活vt+派发) | 是 | 不成立 | 否 |
| 17 | 0041CFE0 | AircraftTypeClass::vslot8 | PASS | PASS(.?AVAircraftTypeClass@@ slot8) | **PASS(③b② -1哨兵+非栈写循环)** | PASS(活vt+派发) | 是 | **成立** | **是** |
| 18 | 00450630 | fn_00450630 | PASS | FAIL(无槽无RTTI) | FAIL(p3=0) | FAIL(direct-only) | n/a | 不成立 | 否 |

## 逐行裁定依据（每行自身地址锚，见 `EVIDENCE/ROW_<entry>.txt`）

- **② 钉住 16/18**：每行 entry 作为 4B VA 在 `.rdata` 命中虚表槽，回扫 `[vt-4]=COL(sig=0)→[COL+0xC]=TD→TD+8` 得 RTTI 名串，与名字线索类名逐字一致，且 `slot offset/4 == 线索槽号`（如 004176F0 offset+1156=slot289、0041BBD0 offset+1320=slot330）。高槽号行因复用脚本回扫窗口不足原报 rtti=None，本卡用 `work/resolve_rtti_ext.py`（kmax=400）补齐钉死。00410380/00450630 全镜像槽 0 命中，② 不可得。
- **③ 成立仅 3 行**（各行理由独立、地址独立，详见各 EVIDENCE ③ 节）：
  - **00410C30**：`call [edx+0x10]@0x00410C63 → cmp eax,-1@0x00410C66 → je@0x00410C69`；-1 哨兵 falsifiable；je 路 base-dtor+ret，非 je 路含边界检查+数组前移循环 `mov [ecx+eax*4-4],edx`（循环体非栈写）；两路真不同、0 eax 覆写。
  - **00414290**：`call 0x00410260@0x004142A2 → test eax,eax@0x004142A7 → jge@0x004142A9`；被调确认返回 HRESULT {0,0x80004002,0x80004003}（非 bool 错误码）；S_OK 路直接 ret 0xC，错误码路 GUID 比较+写_OUT+Release；两路真不同、0 eax 覆写。与 S15S16 已过审的 call-0x410380→jl 模式同构。
  - **0041CFE0**：`call [edx+0x10]@0x0041D01A → cmp eax,-1@0x0041D01D → je@0x0041D020`；与 00410C30 同构但独立的全局对象 0xA8B218、vt 007E2868 slot8、安装点 0041C900/0041CE44/0041CFE6。
- **③ 其余 15 行 FAIL 分类**（每行详见自身 EVIDENCE，理由逐行独立）：
  - p3=0 无可伪证站点：00410380、00417CC0、004196B0、0041B890、0041CE20、0041CE90、00450630。
  - bool/imm=1 布尔态（D-46(A)）：004176F0、004190B0(部分站点)、0041AA80、0041BBD0(cmp eax,1)。
  - 被调返回源 unknown / 仅常量 0 / 枚举值非错误码：00414BB0、004190B0(0x4D8FB0→{0xA,0x14})、0041A9E0(0x6FC0B0→{0})、0041BBD0(0x65AAA0)、0041CC20(0x528A10→{0})。
  - malloc/对象初始化模板假句：00414BB0(部分)、0041CB20、0041CC20。
  - 跳表仅少数目标可达、非每路可验：00414BB0(table 0x4151B8,2目标)、004176F0(table 0x417BAC,3目标)、004190B0(双表大型状态机)。
- **④ 16 行成立但不足以单独升级**：16 行均有非 atexit 构造安装点写 vt 入活对象 + `[reg+off]` 派发链（.text），与 ② 的 .rdata RTTI 链不同源。00410380（direct 42）/00450630（direct 1）无虚表槽、无派发链，direct-only 不足 -> ④ FAIL。

## 与 S04 的败因对比（本批有多少行 ② 真的钉住）

- S04 的 73 个命中 `p3b2_named=0`（全无名字）：entry 作为 4B VA 全镜像 0 命中、无虚表槽、无可安装 RTTI 链 ⇒ **② 物理不可得**，36 行实测全败、B1/B2 共 36 行四环 0。
- 本批 S05 named=True：名字来自既有 coverage 的 `Class::slotN`（线索），但按 D-40 须独立取证——本批 **16/18 行的 ② 被 RTTI 描述符链独立钉死**（含 7 个高 vslot 号由扩展回扫 kmax=400 补齐），这是 S04 完全不具备的条件。2 行（00410380/00450630）本身无虚表槽，② 不可得。
- 结论：② 从 S04 的 0/18 变为本批的 **16/18**；proved 增量最终受 ③ 限制——只有 3 行的 ③b② 满足「可伪证错误码/哨兵 + 两路动作真不同 + 无 eax 覆写」。本批 ② 真钉住 16 行，四环齐全 3 行。

## 汇总
- rows_checked：**18**
- ② 钉住行数：**16**
- ③b 成立行数：**3**
- ④ 成立行数：**16**
- all_four_rings（严格 D-40）：**3**
- delta 产出：**3 行**（00410C30、00414290、0041CFE0）
- 结论：本批 16 行 ② 钉住（S04 败因在此批基本不复现），③ 成为决定性瓶颈；按「宁严不宽、虚报不可接受」如实交 3 行。

## 输出清单
- `REPORT.md`（本文件）、`PROGRESS.md`、`base_rate.tsv`、`delta.tsv`
- `EVIDENCE/ROW_<entry>.txt` × 18（每行自身地址与字节）
- `work/`（filter/analyze/resolve_rtti_ext/resolve_callee/site_paths/disasm_full/verify_pass/gen_evidence 等脚本与中间 JSON/probe，全部只读目标、可复算）
