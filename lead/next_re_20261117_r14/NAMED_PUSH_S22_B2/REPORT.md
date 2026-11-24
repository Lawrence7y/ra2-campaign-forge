# NAMED-PUSH — S22 B2 批次（有名字的 ③b② 候选，攻 proved 增量）

> 状态：**完成**。执行纪律已遵：先建目录 → 先写 REPORT 骨架 → 逐行核完即落 `EVIDENCE/`；`PROGRESS.md` 每 5 行追加。
> 卡片：`lead\next_re_20261117_r14\_cards\NAMED-PUSH.md`（全文 80 行读完）。
> 本批：**B2** = `SURVEY_3B2\hits_detail.tsv` 中 `subsystem==S22` AND `p3b2_named==True`，排除 `fn_XXXXXXXX`/`sub_XXXXXXXX` 伪名后，按 entry 升序取**第 19..36 个**（切片 `[18:36]`）。
> 输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S22_B2\`（卡片 `<你的子系统>`=S22、`<你的目录>`=本目录）。

## 材料自校验
- 目标：`ra2youli\gamemd.exe`；现场 `Get-FileHash -Algorithm SHA256` = `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` ⇒ **与卡片期望逐字一致**。
- ImageBase `0x400000`；`.text = [0x401000, 0x7E038D)`（VirtualSize）。
- Python 3.12.10 / capstone 5.0.7（**skipdata=True**）/ pefile 2024.8.26；无 venv、未 pip install、未用 Ghidra。
- 只读输入：`SURVEY_3B2\hits_detail.tsv`（仅当线索）、`W130_atlas\function_atlas.tsv`（仅取函数边界）。未改 `coverage.tsv` / `PANEL.md` / `R14_COMMON.md` / 台账 / `SURVEY_3B2` / `S04_PUSH_*`。写域仅本目录。

## 筛选命令（得到本批 18 个 entry）

```powershell
$p = "D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv"
$rows = Import-Csv $p -Delimiter "`t"
$sel = $rows | Where-Object {
  $_.subsystem -eq 'S22' -and $_.p3b2_named -eq 'True' -and
  ($_.name -notmatch '^fn_[0-9A-Fa-f]{8}$') -and ($_.name -notmatch '^sub_[0-9A-Fa-f]{8}$')
} | Sort-Object { [Convert]::ToInt32($_.entry,16) }
$b2 = $sel[18..35]   # 第 19..36 个
$b2 | Format-Table entry,subsystem,name,grade,size,n_call,n_site -AutoSize
```

等价 Python 落盘 `work/filter_b2.py` + `work/make_rows.py`（`sel.sort(key=int(entry,16))[18:36]`）。
结果：S22 `p3b2_named=True` 共 **71** 行；fn_/sub_ 伪名 **0** 行（本子系统 named 行无地址式伪名），排除后仍 **71** 行；B2 = 升序第 19..36 行 = `006C1010 … 006C2990`。18 行全部为 `TClassFactory<T>::slot3`（COM `IClassFactory::CreateInstance`）——是 S22 B1 已过的 16 个工厂行的**同族续段**（工厂虚表槽 `007F3984..007F3B1C`，紧接 B1 的 `007F37F8..007F3960`）。

## 判定口径（严格 D-40/D-43，宁严不宽）

1. **①入口**：entry 在 `.text` 内、atlas 边界自洽、`skipdata=0`、末条 `ret 0x10`。本批 18/18 全部 `skipdata=0`、末条 `ret 0x10`、`n_insn` 与 atlas size 自洽。
2. **②类身份**：必须独立取证——`.rdata` 中 entry 作 4B VA 的唯一槽 → 回扫 `[vt-4]=COL(sig=0)` → `[COL+0xC]=TD` → `TD+8` 名串；并要求 `slot_off/4 == 名字线索槽号`。`Class::` 部分仅作线索，不参与判定；钉不死判 FAIL。**②④不同源**：② 锚 `.rdata` RTTI 数据链。本批 18/18 slot_off=12 → slot#3 与线索 `slot3` 逐行字节复算自洽，RTTI 给出 `.?AV?$TClassFactory@V<T>@@@@`。
3. **③整体合同**：只认 ③b。本批 18 行全部命中 **③b②**：COM CreateInstance 内新建对象的 `QueryInterface`（`call [eax]`, slot0）返回 HRESULT，调用方 `mov edi,eax`/`test edi,edi`/`jge` 真分支——失败返 `0x80004002`/`0x80004003` 并 `call [edx+0x20]`（带 delete 标志=1）释放新建对象，成功返 0（S_OK）；被调 `0x410260` 出口 `{0,0x80004002,0x80004003}`、3 处 ret，HRESULT 可伪证（非 bool 0/1）。三陷阱（eax 覆写、多路同一 call、模板假句）逐行排查：返回值在 edi、`test` 与 `jge` 零间隔、本体内 QI call 仅 1 处、非 ③a/模板假句。语义方向为**写出接口指针到 ppvOut**，未写反。
4. **④使用见证**：真实调用者或活虚表派发，direct-only 不足，且与 ② 不同源。本批 18 行均为**活 COM 类对象**：堆分配 8B 工厂实例（`push 8; call 0x7C8E17`）→ 行外 ctor（如 `006C0F40`）把本类 vt 写入实例 → `push <CLSID>; push 1; push 1; call esi`（`esi = [0x7E15D8]@006BC43F = ole32!CoRegisterClassObject`）以 CLSID 注册为活类对象。宿主 `006BB9A0`（size 10256）为非 atexit 初始化函数、各工厂 ctor 亦非 atexit ⇒ **㉓ 成对陷阱已排除；④ 锚点未落在析构器**（卡片显式要求：④ 锚在析构器判 FAIL）。18 行 entry 全镜像 direct call 者=0（纯虚派发，非 direct-only）。④ 锚 `.text` 分配/装表/注册指令，与 ② 的 `.rdata` RTTI 链段不同、地址不同、产物类型不同。

## 基础率（诚实报数）

分母 = 本批 18 行。

| 档 | 行数 | 口径 |
|---|---:|---|
| 本批行数 | **18** | S22 named=True（去伪名）升序第 19..36 |
| ①入口 PASS | **18** | 全部在 `.text`、`skipdata=0`、末条 `ret 0x10`、边界自洽 |
| ②类身份钉住 | **18** | 18 行 entry 均作唯一 4B VA 落在 `.rdata` 虚表槽，RTTI 链（COL sig=0→TD→名串）完整，slot#3 与线索自洽 |
| ③b 成立 | **18** | 18×③b②（QI HRESULT 真分支，被调 0x410260 出口 {0,80004002,80004003}、3 ret） |
| ④使用见证成立 | **18** | 18 行均为活 COM 类对象（堆分配+ctor 装表+CLSID 注册），非 atexit/非析构、非 direct-only |
| **四环齐全（严格 D-40）** | **18** | rate = 18/18 = **1.0000** |

`base_rate.tsv`：`S22_B2  18  18  18  18  18  1.0000`

## 本批 18 行总表（entry / ②③④ / 是否产出）

| # | entry | name(原样) | ①入口 | ②类身份 | ③b | ④使用见证 | ②④不同源 | 裁定 | 产出 |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | 006C1010 | T_TClassFactory_VParasiteClass__::slot3 | PASS | PASS(.?AV?$TClassFactory@VParasiteClass@@@@ slot#3) | PASS(③b② QI HRESULT) | PASS(活COM类对象) | 是 | **成立** | **是** |
| 2 | 006C1190 | T_TClassFactory_VBombClass__::slot3 | PASS | PASS(...VBombClass@@@@ slot#3) | PASS(③b② QI HRESULT) | PASS(活COM类对象) | 是 | **成立** | **是** |
| 3 | 006C1310 | T_TClassFactory_VRadSiteClass__::slot3 | PASS | PASS(...VRadSiteClass@@@@ slot#3) | PASS(③b② QI HRESULT) | PASS(活COM类对象) | 是 | **成立** | **是** |
| 4 | 006C1490 | T_TClassFactory_VTEventClass__::slot3 | PASS | PASS(...VTEventClass@@@@ slot#3) | PASS(③b② QI HRESULT) | PASS(活COM类对象) | 是 | **成立** | **是** |
| 5 | 006C1610 | T_TClassFactory_VVoxelAnimTypeClass__::slot3 | PASS | PASS(...VVoxelAnimTypeClass@@@@ slot#3) | PASS(③b② QI HRESULT) | PASS(活COM类对象) | 是 | **成立** | **是** |
| 6 | 006C1790 | T_TClassFactory_VVoxelAnimClass__::slot3 | PASS | PASS(...VVoxelAnimClass@@@@ slot#3) | PASS(③b② QI HRESULT) | PASS(活COM类对象) | 是 | **成立** | **是** |
| 7 | 006C1910 | T_TClassFactory_VTActionClass__::slot3 | PASS | PASS(...VTActionClass@@@@ slot#3) | PASS(③b② QI HRESULT) | PASS(活COM类对象) | 是 | **成立** | **是** |
| 8 | 006C1A90 | T_TClassFactory_VTriggerClass__::slot3 | PASS | PASS(...VTriggerClass@@@@ slot#3) | PASS(③b② QI HRESULT) | PASS(活COM类对象) | 是 | **成立** | **是** |
| 9 | 006C1C10 | T_TClassFactory_VTriggerTypeClass__::slot3 | PASS | PASS(...VTriggerTypeClass@@@@ slot#3) | PASS(③b② QI HRESULT) | PASS(活COM类对象) | 是 | **成立** | **是** |
| 10 | 006C1D90 | T_TClassFactory_VScriptClass__::slot3 | PASS | PASS(...VScriptClass@@@@ slot#3) | PASS(③b② QI HRESULT) | PASS(活COM类对象) | 是 | **成立** | **是** |
| 11 | 006C1F10 | T_TClassFactory_VScriptTypeClass__::slot3 | PASS | PASS(...VScriptTypeClass@@@@ slot#3) | PASS(③b② QI HRESULT) | PASS(活COM类对象) | 是 | **成立** | **是** |
| 12 | 006C2090 | T_TClassFactory_VTagClass__::slot3 | PASS | PASS(...VTagClass@@@@ slot#3) | PASS(③b② QI HRESULT) | PASS(活COM类对象) | 是 | **成立** | **是** |
| 13 | 006C2210 | T_TClassFactory_VTagTypeClass__::slot3 | PASS | PASS(...VTagTypeClass@@@@ slot#3) | PASS(③b② QI HRESULT) | PASS(活COM类对象) | 是 | **成立** | **是** |
| 14 | 006C2390 | T_TClassFactory_VTeamClass__::slot3 | PASS | PASS(...VTeamClass@@@@ slot#3) | PASS(③b② QI HRESULT) | PASS(活COM类对象) | 是 | **成立** | **是** |
| 15 | 006C2510 | T_TClassFactory_VTeamTypeClass__::slot3 | PASS | PASS(...VTeamTypeClass@@@@ slot#3) | PASS(③b② QI HRESULT) | PASS(活COM类对象) | 是 | **成立** | **是** |
| 16 | 006C2690 | T_TClassFactory_VTaskForceClass__::slot3 | PASS | PASS(...VTaskForceClass@@@@ slot#3) | PASS(③b② QI HRESULT) | PASS(活COM类对象) | 是 | **成立** | **是** |
| 17 | 006C2810 | T_TClassFactory_VUnitTypeClass__::slot3 | PASS | PASS(...VUnitTypeClass@@@@ slot#3) | PASS(③b② QI HRESULT) | PASS(活COM类对象) | 是 | **成立** | **是** |
| 18 | 006C2990 | T_TClassFactory_VBuildingTypeClass__::slot3 | PASS | PASS(...VBuildingTypeClass@@@@ slot#3) | PASS(③b② QI HRESULT) | PASS(活COM类对象) | 是 | **成立** | **是** |

## 逐行裁定依据（每行自身地址锚，完整字节见 `EVIDENCE/ROW_<entry>.txt`）

**② 18/18 全数钉住，槽号由字节复算而非反推。**
每个 `T_TClassFactory_V<T>__::slot3` 行的 entry 作 4B VA 在 `.rdata` 唯一命中一个工厂虚表槽（vt 从 `007F3978` 到 `007F3B10`，每 0x18 一张工厂表；slot 从 `007F3984` 到 `007F3B1C`），`slot_off=0xC/4=3` 与线索 `slot3` 逐行自洽；RTTI 链 `COL(sig=0)→TD→名串` 给出 `.?AV?$TClassFactory@V<T>@@@@`。全部 18 行 slot 号由 offset/4 复算，非拿 `slotN` 类名当已证。

**③ 成立 18 行（18×③b②，QI HRESULT 分支；逐行独立地址锚）**
以 `006C1010` 为样板（每工厂行地址不同，下表与各行 EVIDENCE 给出自身锚）：
- 三道 imm 错误码守卫：`mov eax,0x80070057`(E_INVALIDARG, `@006C101B`) / `mov eax,0x80040110`(CLASS_E_NOAGGREGATION, `@006C1033`) / `mov eax,0x8007000e`(E_OUTOFMEMORY, `@006C1058`)。
- 主 ③b② 站点 `@006C106A ff 10`(call [eax]，eax=[esi]=新建 Parasite 对象主 vt `007EF890` 的 slot0=QueryInterface `0x410260`) → `@006C106C 8b f8`(mov edi,eax) → `@006C106E 85 ff`(test edi,edi) → `@006C1070 7d 09`(jge)；失败路 `@006C1078 ff 52 20`(call [edx+0x20]，标量删除析构/Release，delete 标志=1)，成功路 `mov eax,edi; ret 0x10`。被调 `0x410260` 返回常量 `{0,0x80004002,0x80004003}`（3 处 ret，字节 `@0041026F/@004102EC/@004102F8 c2 0c 00`），HRESULT 可伪证（非 bool 0/1）；调用方真拿返回值分支、两路动作真不同。返回值在 edi，`test`/`jge` 零间隔无 eax 覆写；本体内 QI call 仅 1 处（非多路同一 call）；非纯转发/零+默认/无分支直线，非模板假句。
- 被调定位链（不同源旁证）：工厂体内 `call 对象ctor 00629210` → 该 ctor `@00629231` 写主 vt `007EF890` → `vt[0]=0x410260`。
- **双 offset0 写表行**（`006C1610` VoxelAnimType、`006C1790` VoxelAnim、`006C2810` UnitType、`006C2990` BuildingType 等）：对象 ctor 首写是成员子对象、末写才是主表（写 `this`），本报告一律取 `vt[0]=0x410260` 的主表作 QI 被调——已逐行由字节确认，非取首个命中。
- 语义方向：写出接口指针到 ppvOut（CreateInstance 产出对象接口），未把读入/写出写反。

**④ 18/18 成立（每行自身安装/注册锚，非同一锚复用、非析构器）**
工厂实例是活 COM 类对象：宿主初始化函数 `006BB9A0`（size 10256，非 atexit）内对 18 个工厂逐一 `push 8; call 0x7C8E17`（分配 8B 实例）→ `mov ecx,eax; call <工厂ctor>`（ctor 写本类 vt 到 [this]）→ `push <CLSID>; push 1; push 1; call esi`，`esi=[0x7E15D8]@006BC43F = ole32!CoRegisterClassObject`。IAT 载入点 `006BC43F` 在宿主函数内唯一；18 行 `host_atexit=[]`、`fc_atexit=[]`（均空=非 atexit 表），**㉓ 成对陷阱已排除，④ 锚点未落在析构器**。全部 18 个 entry 全镜像 direct call 者=0（纯虚派发，非 direct-only）。每行的 alloc / ctor_call / reg_call / CLSID 地址互不相同（见下表与各行 EVIDENCE），非整批共用一段证据。

**②④不同源（18/18 是）**：② 锚 `.rdata` 的 RTTI 描述符链 + 工厂虚表槽；④ 锚 `.text` 的堆分配 + ctor 装表 + CoRegisterClassObject 注册指令 —— 段不同、地址不同、产物类型不同，非同一虚表槽既证身份又证使用。

**每行自身四环锚点表**（entry 后的三列依次为 ②槽/vt/COL→TD、③QI站点/对象ctor→主vt/release、④alloc/ctor_call/reg_call/CLSID/host-atexit）：

| # | entry | ② | ③ | ④ |
|---:|---|---|---|---|
| 1 | 006C1010 | 007F3984 / 007F3978 / 0080A348→008413C8 | 006C106A / 00629210→007EF890 / 006C1078 | 006BC998 / 006BC9A6 / 006BC9C0 / 007E98A0 / [] |
| 2 | 006C1190 | 007F399C / 007F3990 / 0080A398→008413F8 | 006C11EA / 004385D0→007E3D10 / 006C11F8 | 006BC9D5 / 006BC9E3 / 006BC9FD / 007E98B0 / [] |
| 3 | 006C1310 | 007F39B4 / 007F39A8 / 0080A3E8→00841428 | 006C136A / 0065B1E0→007F0810 / 006C1378 | 006BCA12 / 006BCA20 / 006BCA3A / 007E98C0 / [] |
| 4 | 006C1490 | 007F39CC / 007F39C0 / 0080A438→00841458 | 006C14EA / 0071E6A0→007F5578 / 006C14F8 | 006BCA4F / 006BCA5D / 006BCA77 / 007E9810 / [] |
| 5 | 006C1610 | 007F39E4 / 007F39D8 / 0080A488→00841488 | 006C166F / 0074AD80→007F6548 / 006C167D | 006BCA8C / 006BCA9A / 006BCAB4 / 007E9790 / [] |
| 6 | 006C1790 | 007F39FC / 007F39F0 / 0080A4D8→008414C0 | 006C17ED / 007498D0→007F6318 / 006C17FB | 006BCAC9 / 006BCAD7 / 006BCAF1 / 007E9650 / [] |
| 7 | 006C1910 | 007F3A14 / 007F3A08 / 0080A528→008414F0 | 006C196D / 006DD000→007F443C / 006C197B | 006BCB06 / 006BCB14 / 006BCB2E / 007E9800 / [] |
| 8 | 006C1A90 | 007F3A2C / 007F3A20 / 0080A578→00841520 | 006C1AEC / 00725FA0→007F5858 / 006C1AFA | 006BCB43 / 006BCB51 / 006BCB6B / 007E97E0 / [] |
| 9 | 006C1C10 | 007F3A44 / 007F3A38 / 0080A5C8→00841550 | 006C1C6F / 00726C80→007F5904 / 006C1C7D | 006BCB80 / 006BCB8E / 006BCBA8 / 007E97F0 / [] |
| 10 | 006C1D90 | 007F3A5C / 007F3A50 / 0080A618→00841588 | 006C1DEC / 006913C0→007F0F78 / 006C1DFA | 006BCBBD / 006BCBCB / 006BCBE5 / 007E97A0 / [] |
| 11 | 006C1F10 | 007F3A74 / 007F3A68 / 0080A668→008415B8 | 006C1F6F / 006916B0→007F1008 / 006C1F7D | 006BCBFA / 006BCC08 / 006BCC22 / 007E97B0 / [] |
| 12 | 006C2090 | 007F3A8C / 007F3A80 / 0080A6B8→008415F0 | 006C20EC / 006E4DE0→007F44E0 / 006C20FA | 006BCC37 / 006BCC45 / 006BCC5F / 007E97C0 / [] |
| 13 | 006C2210 | 007F3AA4 / 007F3A98 / 0080A708→00841620 | 006C226F / 006E5B60→007F45C4 / 006C227D | 006BCC74 / 006BCC82 / 006BCC9C / 007E97D0 / [] |
| 14 | 006C2390 | 007F3ABC / 007F3AB0 / 0080A758→00841650 | 006C23F3 / 006E8A90→007F4730 / 006C2401 | 006BCCB1 / 006BCCBF / 006BCCD9 / 007E9760 / [] |
| 15 | 006C2510 | 007F3AD4 / 007F3AC8 / 0080A7A8→00841680 | 006C256F / 006F06E0→007F47D0 / 006C257D | 006BCCEE / 006BCCFC / 006BCD16 / 007E9780 / [] |
| 16 | 006C2690 | 007F3AEC / 007F3AE0 / 0080A7F8→008416B0 | 006C26EF / 006E7E80→007F4680 / 006C26FD | 006BCD2B / 006BCD39 / 006BCD53 / 007E9770 / [] |
| 17 | 006C2810 | 007F3B04 / 007F3AF8 / 0080A848→008416E0 | 006C286F / 007470D0→007F6218 / 006C287D | 006BCD68 / 006BCD76 / 006BCD90 / 007E9590 / [] |
| 18 | 006C2990 | 007F3B1C / 007F3B10 / 0080A898→00841710 | 006C29EF / 0045DD90→007E4570 / 006C29FD | 006BCDA5 / 006BCDB3 / 006BCDCD / 007E95C0 / [] |

## 与 S04 的败因对比（本批有多少行 ② 真的钉住）

- **S04**：73 个 ③b② 机械命中 `p3b2_named=0`（全无名字）——entry 作 4B VA 全镜像 0 命中、无虚表槽、无可回扫 RTTI 链 ⇒ **② 物理不可得**，30+ 行实测全败。
- **本批 S22 B2**：18 行 **② 100% 钉住（18/18）**，且 18 个 `TClassFactory<T>::slot3` 由 RTTI 描述符独立给出模板工厂类身份（`.?AV?$TClassFactory@V<T>@@@@`），槽号由 offset/4 逐行复算。与 S04「② 物理不可得」形成完全对照 —— 卡片的「② 是硬约束」在本批被满足。
- **与 S14 的差异**：S14 named 池掺了 16 个 `fn_` 地址式伪名（全镜像 0 引用、② 不可得）；本批 S22 named 池 **0 个 fn_/sub_ 伪名**（71 行全是 `T_…::slotN` 真模板槽名），筛选阶段无需剔除，② 自然全数可得。
- **与 S22 B1 的关系**：B1 是同族前 18 行（16 工厂 slot3 全过 + 2 Vector slot2 因 malloc 空判断/bool 返回被否）；B2 这段 18 行**全部是工厂 slot3**（无 Vector 行），故 ③ 分区不再存在，18/18 全过。瓶颈位置：② 不是瓶颈（18/18），③/④ 也全数成立。
- 结论：**② 从 S04 的 0 → 本批 18/18**；本批无 fn_ 伪名掺水，四环齐全 18/18 = 1.0000。

## 待裁（2 项，未擅自扩面；与 S22 B1 同类）

1. **工厂行以 QueryInterface 分支作 ③b②（18 行）**：机械 survey 在这些行命中的「call→test eax→je」是 `operator new`(0x7C8E17) 空判断（按 S18_B2 应判模板假句）；本批改用**同一函数体内另一个真实可伪证站点** —— 新建对象的 `QueryInterface`（slot0=0x410260，HRESULT `{0,0x80004002,0x80004003}`，`mov edi,eax`/`test edi,edi`/`jge`，失败 Release / 成功回传，两路真不同）作为 ③b②。该被调与 S05_B1 已过审的 `00414290`、S22_B1 已过审的 16 行同构。若 Lead 要求「③ 必须是 survey 命中的那一路站点」，则这 18 行应改判 ③ FAIL → 全批 0/18；本批按 D-40「只认 ③b、可伪证错误码/返回约定 + 调用方真分支」的字面口径判成立，特此登记待裁。
2. **工厂 CreateInstance 属「IClassFactory 模板级契约」**：18 行语义同族（仅创建类不同），每行的 QI 站点地址、对象 ctor、主 vt、工厂 vt、COL/TD、CLSID、注册点均各自独立（见逐行锚点表与各行 EVIDENCE），非同一段 reason 复用；但契约形态同源。若 Lead 认为「同族模板级 ③b② 低信息量、不单独扩域」（AUDIT3 对析构自摘链 ③b② 曾有类似备注），可整体收紧；本批按卡片「逐行按 D-40 四环核、真成立即证」如实计入，并在此标明同族属性供裁。

## 汇总

- rows_checked：**18**
- ①入口 PASS：**18**
- ② 钉住行数：**18**（18 个工厂类 RTTI）
- ③b 成立行数：**18**（18×③b② QI HRESULT 分支）
- ④ 成立行数：**18**（活 COM 类对象，非 atexit/非析构、非 direct-only）
- all_four_rings（严格 D-40/D-43）：**18**，rate = **1.0000**
- delta 产出：**18 行**（006C1010 / 006C1190 / 006C1310 / 006C1490 / 006C1610 / 006C1790 / 006C1910 / 006C1A90 / 006C1C10 / 006C1D90 / 006C1F10 / 006C2090 / 006C2210 / 006C2390 / 006C2510 / 006C2690 / 006C2810 / 006C2990）
- 本批 ② 从 S04 的 0 → 18/18；无 fn_ 伪名掺水；无 FAIL 行。

## 输出清单
- `REPORT.md`（本文件）、`PROGRESS.md`、`base_rate.tsv`、`delta.tsv`（18 行）
- `EVIDENCE/ROW_<entry>.txt` × 18（逐行四环地址与字节，每行自身锚点）
- `work/`：`filter_b2.py` / `make_rows.py`（筛选）、`recore.py` / `core2.py`（PE/capstone/RTTI 底座，复制自 B1）、`analyze.py`（四环初筛）、`probe_struct.py`（结构探针）、`gather.py`（QI/ctor/注册点取证）、`ring4.py`（④锚点非析构校验）、`finalize.py`（verdict）、`gen_outputs.py`（产物生成）、`report_table.py`（锚点表）+ 中间 JSON（`b2_rows.json` / `analysis.json` / `gather.json` / `ring4.json` / `verdicts.json`），全部只读目标、可复算。
