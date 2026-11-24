# NAMED-PUSH — S22 B1 批次（有名字的 ③b② 候选，攻 proved 增量）

> 状态：**完成**。执行纪律已遵：先建目录 → 先写 REPORT 骨架 → 逐行核完即落 `EVIDENCE/`；`PROGRESS.md` 每 5 行追加。
> 卡片：`lead\next_re_20261117_r14\_cards\NAMED-PUSH.md`（全文 80 行读完）。
> 本批：**B1** = `SURVEY_3B2\hits_detail.tsv` 中 `subsystem==S22` AND `p3b2_named==True`，排除 `fn_XXXXXXXX`/`sub_XXXXXXXX` 伪名后，按 entry 升序取**前 18 行**。
> 输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S22_B1\`（卡片 `<你的子系统>`=S22、`<你的目录>`=本目录）。

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
$sel | Select-Object -First 18 | Format-Table entry,name,grade,size,n_insn,n_call,n_site -AutoSize
```

结果：S22 `p3b2_named=True` 共 **71** 行；应用 fn_/sub_ 排除后仍 **71** 行（本子系统 named 行无一条是地址式伪名，**因此不像 S14 那样需要从候选里剔 fn_ 行**）；B1 = 升序**前 18 行** = `0069C9C0 … 006C0E90`。等价脚本落盘 `work/filter_b1.py`（`sel.sort(key=int(entry,16))[:18]`）。18 行由 2 个容器槽 + 16 个 `TClassFactory<T>::slot3` 组成（后者为 COM `IClassFactory::CreateInstance`）。

## 判定口径（严格 D-40/D-43，宁严不宽）

1. **①入口**：entry 在 `.text` 内、atlas 边界自洽、`skipdata=0`、末条为 `ret`/`ret-imm`。
2. **②类身份**：必须独立取证——`.rdata` 中 entry 作 4B VA 的唯一槽 → 回扫 `[vt-4]=COL(sig=0)` → `[COL+0xC]=TD` → `TD+8` 名串；并要求 `slot_off/4 == 名字线索槽号`。`Class::` 部分仅作线索，不参与判定；钉不死判 FAIL。**②④不同源**：② 锚 `.rdata` RTTI 数据链。
3. **③整体合同**：只认 ③b。本批实际命中两种：
   - **③b②（工厂行）**：COM `CreateInstance` 的 `call [eax]`(slot0=QueryInterface) → `mov edi,eax` → `test edi,edi` → `jge`；被调 QI 返回常量 `{0, 0x80004002, 0x80004003}`（S_OK / E_NOINTERFACE / E_POINTER，**非 bool 0/1**），字节可伪证；调用方真拿它分支、两路动作真不同（失败路 `call [edx+0x20]` 带 delete 标志释放新建对象，成功路直接回传 HRESULT）；无 eax 覆写（返回值在 edi）、唯一路径进 QI call（非多路同一 call）、非 ③a/模板假句。
   - **③a 否决（Vector 行）**：本体唯一可伪证站点是 `call 0x7C8E17`(operator new) + `test eax,eax; je` 的**分配空判断**，且出口是 `al=0/1` bool 返回 —— 撞 D-46(A)「null 探测/bool 不算」+「malloc 空判断模板假句」双禁。
   - 禁被调用者内部写充循环非栈写；禁 ③a（清零/对象初始化模板假句/纯转发/无分支直线）；三陷阱（eax 覆写、多路同一 call、模板假句）逐行排查。
4. **④使用见证**：真实调用者或活虚表派发，direct-only 不足，且与 ② 不同源。**本批工厂行走活 COM 类对象**：8 字节工厂实例 `push 8; call 0x7C8E17` 堆分配 → 行外 ctor（如 `006BF740`）把本类 vt 写入实例 → `ole32!CoRegisterClassObject` 以 CLSID(GUID) 注册为活类对象（`mov esi,[0x7E15D8]@006BC43F` = CoRegisterClassObject，实参 `push <factory>; push <CLSID>; push 1; push 1`）。宿主 `006BB9A0` 为非 atexit 初始化函数（非析构器），ctor 亦非 atexit 注册 ⇒ **㉓ 成对陷阱已排除**；工厂 entry 全镜像 direct call 者=0（纯虚派发，非 direct-only）。④ 锚在 `.text` 分配/装表/注册指令，与 ② 的 `.rdata` RTTI 链不同源。

## 基础率（诚实报数）

分母 = 本批 18 行。

| 档 | 行数 | 口径 |
|---|---:|---|
| 本批行数 | **18** | S22 named=True（去伪名）升序前 18 |
| ①入口 PASS | **18** | 全部在 `.text`、`skipdata=0`、末条 ret/ret-imm、边界自洽 |
| ②类身份钉住 | **18** | 18 行 entry 均作唯一 4B VA 落在 `.rdata` 虚表槽，RTTI 链（COL sig=0→TD→名串）完整，槽号与线索自洽 |
| ③b 成立 | **16** | 16 个 `TClassFactory<T>::slot3`（③b② QI HRESULT 分支）；2 个 Vector slot2 不成立 |
| ④使用见证成立 | **16** | 16 个工厂行均为活 COM 类对象（堆分配+ctor 装表+CoRegisterClassObject），非 atexit/非析构、非 direct-only；2 个 Vector 行 ③ 已 FAIL 故 ④ 不作升级依据 |
| **四环齐全（严格 D-40）** | **16** | rate = 16/18 = **0.8889** |

`base_rate.tsv`：`S22_B1  18  18  16  16  16  0.8889`

## 本批 18 行总表（entry / ②③④ / 是否产出）

| # | entry | name(原样) | ①入口 | ②类身份 | ③b | ④使用见证 | ②④不同源 | 裁定 | 产出 |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | 0069C9C0 | T_VectorClass_VWstring__::slot2 | PASS | PASS(.?AV?$VectorClass@VWstring@@@@ slot2) | FAIL(malloc 空判断模板假句 + bool 返回) | 未计入 | – | 不成立 | 否 |
| 2 | 0069CBC0 | T_DynamicVectorClass_VWstring__::slot2 | PASS | PASS(.?AV?$DynamicVectorClass@VWstring@@@@ slot2) | FAIL(malloc 空判断模板假句 + bool 返回) | 未计入 | – | 不成立 | 否 |
| 3 | 006BF810 | T_TClassFactory_VTactical__::slot3 | PASS | PASS(.?AV?$TClassFactory@VTactical@@@@ slot3) | **PASS(③b② QI HRESULT)** | PASS(活COM类对象) | 是 | **成立** | **是** |
| 4 | 006BF990 | T_TClassFactory_VCellClass__::slot3 | PASS | PASS(...CellClass slot3) | **PASS(③b② QI HRESULT)** | PASS(活COM类对象) | 是 | **成立** | **是** |
| 5 | 006BFB10 | T_TClassFactory_VEMPulseClass__::slot3 | PASS | PASS(...EMPulseClass slot3) | **PASS(③b② QI HRESULT)** | PASS(活COM类对象) | 是 | **成立** | **是** |
| 6 | 006BFC90 | T_TClassFactory_VLightSourceClass__::slot3 | PASS | PASS(...LightSourceClass slot3) | **PASS(③b② QI HRESULT)** | PASS(活COM类对象) | 是 | **成立** | **是** |
| 7 | 006BFE10 | T_TClassFactory_VSideClass__::slot3 | PASS | PASS(...SideClass slot3) | **PASS(③b② QI HRESULT)** | PASS(活COM类对象) | 是 | **成立** | **是** |
| 8 | 006BFF90 | T_TClassFactory_VTiberiumClass__::slot3 | PASS | PASS(...TiberiumClass slot3) | **PASS(③b② QI HRESULT)** | PASS(活COM类对象) | 是 | **成立** | **是** |
| 9 | 006C0110 | T_TClassFactory_VTubeClass__::slot3 | PASS | PASS(...TubeClass slot3) | **PASS(③b② QI HRESULT)** | PASS(活COM类对象) | 是 | **成立** | **是** |
| 10 | 006C0290 | T_TClassFactory_VCampaignClass__::slot3 | PASS | PASS(...CampaignClass slot3) | **PASS(③b② QI HRESULT)** | PASS(活COM类对象) | 是 | **成立** | **是** |
| 11 | 006C0410 | T_TClassFactory_VBuildingLightClass__::slot3 | PASS | PASS(...BuildingLightClass slot3) | **PASS(③b② QI HRESULT)** | PASS(活COM类对象) | 是 | **成立** | **是** |
| 12 | 006C0590 | T_TClassFactory_VWaypointPathClass__::slot3 | PASS | PASS(...WaypointPathClass slot3) | **PASS(③b② QI HRESULT)** | PASS(活COM类对象) | 是 | **成立** | **是** |
| 13 | 006C0710 | T_TClassFactory_VTemporalClass__::slot3 | PASS | PASS(...TemporalClass slot3) | **PASS(③b② QI HRESULT)** | PASS(活COM类对象) | 是 | **成立** | **是** |
| 14 | 006C0890 | T_TClassFactory_VAirstrikeClass__::slot3 | PASS | PASS(...AirstrikeClass slot3) | **PASS(③b② QI HRESULT)** | PASS(活COM类对象) | 是 | **成立** | **是** |
| 15 | 006C0A10 | T_TClassFactory_VSpawnManagerClass__::slot3 | PASS | PASS(...SpawnManagerClass slot3) | **PASS(③b② QI HRESULT)** | PASS(活COM类对象) | 是 | **成立** | **是** |
| 16 | 006C0B90 | T_TClassFactory_VSlaveManagerClass__::slot3 | PASS | PASS(...SlaveManagerClass slot3) | **PASS(③b② QI HRESULT)** | PASS(活COM类对象) | 是 | **成立** | **是** |
| 17 | 006C0D10 | T_TClassFactory_VCaptureManagerClass__::slot3 | PASS | PASS(...CaptureManagerClass slot3) | **PASS(③b② QI HRESULT)** | PASS(活COM类对象) | 是 | **成立** | **是** |
| 18 | 006C0E90 | T_TClassFactory_VDiskLaserClass__::slot3 | PASS | PASS(...DiskLaserClass slot3) | **PASS(③b② QI HRESULT)** | PASS(活COM类对象) | 是 | **成立** | **是** |

## 逐行裁定依据（每行自身地址锚，字节见 `EVIDENCE/ROW_<entry>.txt`）

**② 18/18 全数钉住，槽号由字节复算而非反推。**
每个 `T_TClassFactory_V<T>__::slot3` 行的 entry 作 4B VA 在 `.rdata` 唯一命中一个虚表槽（vt 从 `007F37F8` 到 `007F3960`，每 0x18 一张工厂表），`slot_off=0xC/4=3` 与线索 `slot3` 逐行自洽；RTTI 链 `COL(sig=0)→TD→名串` 给出 `.?AV?$TClassFactory@V<T>@@@@`（如 006BF810→`00809E48→00841098`→`.?AV?$TClassFactory@VTactical@@@@`）。两行 Vector：`0069C9C0` 槽 `007F129C`→`.?AV?$VectorClass@VWstring@@@@`、`0069CBC0` 槽 `007F12BC`→`.?AV?$DynamicVectorClass@VWstring@@@@`，`slot_off=8/4=2` 与 slot2 自洽。全部 18 行 slot 号由 offset/4 复算，非拿 `slotN` 类名当已证。

**③ 成立 16 行（16×③b②，QI HRESULT 分支；逐行独立地址锚）**
以 `006BF810` 为样板（每工厂行地址不同，见各行 EVIDENCE）：
- 三道 imm 错误码守卫：`test [ppvOut]; jne` → `mov eax,0x80070057`(E_INVALIDARG)；`test [pUnkOuter]; je` → `mov eax,0x80040110`(CLASS_E_NOAGGREGATION)；`call 0x7C8E17`+ctor 空 → `mov eax,0x8007000e`(E_OUTOFMEMORY)。
- 主 ③b② 站点 `0x6BF86D ff 10`(call [eax]，eax=[esi]=新建 Tactical 对象主 vt 0x7F4348 的 slot0=QueryInterface 0x410260) → `0x6BF86F 8b f8`(mov edi,eax) → `0x6BF871 85 ff`(test edi,edi) → `0x6BF873 7d 09`(jge)。被调 0x410260 返回常量 `{0,0x80004002,0x80004003}`（3 处 ret），失败 E_NOINTERFACE/E_POINTER、成功 S_OK，HRESULT 可伪证（非 bool 0/1）；调用方真拿它分支：失败路 `0x6BF875 mov edx,[esi]; push 1; 0x6BF87B ff 52 20`(call [edx+0x20]，标量删除析构/Release，delete 标志=1)，成功路直接 `mov eax,edi; ret 0x10` —— 两路动作真不同。`test edi,edi` 与 `jge` 零间隔、无 eax 覆写（返回值在 edi）；唯一路径进 QI call（三道守卫中途 return），非多路同一 call；不是纯转发/零+默认/无分支直线，非模板假句。
- 各工厂行的 QI 站点与对象 ctor 不同（如 006C0290 站点 `0x6C02EF`、对象 ctor `0x47BBF0`、主 vt `0x7E4EEC`；006C0E90 站点 `0x6C0EEA`、ctor `0x4A7A30`、主 vt `0x7E5FB8`），全部被调 slot0 = `0x410260` 或同类返回同 HRESULT 集；16 行 QI 返回约定逐行由 `obj_qi_verify.json` 校验（见 EVIDENCE）。**注意** `006BFF90`/`006C0A10` 的对象 ctor 有两处 offset0 写表：首写是成员子对象（edi），主表是写 [esi](this) 的末写（0x7F5728 / 0x7F3650），其 slot0=0x410260 ⇒ ③b② 仍成立。
- 语义方向：本族为**写出接口指针到 ppvOut**（CreateInstance 产出对象接口），非流读入；未把读入/写出写反（S14 曾因此被否两行，本批主动核方向）。

**③ FAIL 2 行（逐行独立理由）**
- `0069C9C0` T_VectorClass_VWstring__::slot2：函数体唯一可伪证站点 `0x69C9E7 call 0x7C8E17`(operator new) → `0x69C9EF test eax,eax` → `0x69C9F1 je`，是**分配空判断**（null 探测）；出口 `0x69CA54 xor al,al` / `0x69CAE8 mov al,1` 是 bool 返回。撞 D-46(A)「bool 0/1 与 null 探测不算 ③b②」+「malloc 空判断+对象初始化模板假句」双禁；主体语义是 `Resize(count, init)`（分配+逐元素 Wstring 构造/拷贝+旧缓冲释放），属模板假句。
- `0069CBC0` T_DynamicVectorClass_VWstring__::slot2：同构（`0x69CBE7 call 0x7C8E17`→`0x69CBEF test`→`0x69CBF1 je`，`xor al,al`/`mov al,1` bool 出口），同一否决口径。

**④ 16/16 工厂行成立（每行自身安装/注册锚，非同一锚复用、非析构器）**
工厂实例是活 COM 类对象：宿主初始化函数 `006BB9A0`（非 atexit）内对 16 个工厂逐一 `push 8; call 0x7C8E17`(分配 8B 实例) → `mov ecx,eax; call <工厂ctor>`（ctor 写本类 vt 到 [this]，如 006BF740 写 0x7F37F8）→ `push <factory>; push <CLSID GUID>; push 1; push 1; call esi`，其中 `mov esi,[0x7E15D8]@006BC43F = ole32!CoRegisterClassObject` ⇒ 实例以 CLSID 注册为活类对象。16 个工厂 ctor 逐一核过：atexit 注册均为空、ctor 体内无 `call 0x7C8B3D/0x7C93E8`（非 deleter）、宿主非 atexit ⇒ **㉓ 成对陷阱已排除**（④ 锚点不落在析构器）。全部 16 个 entry 全镜像 direct call 者=0（纯虚派发，D-40『direct-only 不足』的反面，此处靠活虚表派发）。每行的 ctor 调用点地址互不相同（006BC5D6 / 006BC613 / … / 006BC969），非整批共用一段证据。

**②④不同源（16/16 是）**：② 锚 `.rdata` 的 RTTI 描述符链 + 工厂虚表槽；④ 锚 `.text` 的堆分配 + ctor 装表 + CoRegisterClassObject 注册指令 —— 段不同、地址不同、产物类型不同，非同一虚表槽既证身份又证使用。

## 与 S04 的败因对比（本批有多少行 ② 真的钉住）

- **S04**：73 个 ③b② 机械命中 `p3b2_named=0`（全无名字）——entry 作 4B VA 全镜像 0 命中、无虚表槽、无可回扫 RTTI 链 ⇒ **② 物理不可得**，30+ 行实测全败。
- **本批 S22 B1**：18 行 **② 100% 钉住（18/18）**，且 16 个 `TClassFactory<T>::slot3` 由 RTTI 描述符独立给出模板工厂类身份（`.?AV?$TClassFactory@V<T>@@@@`），槽号由 offset/4 逐行复算。这与 S04「② 物理不可得」形成完全对照 —— 卡片的「② 是硬约束」在本批被满足。
- **与 S14 的差异**：S14 named 池掺了 16 个 `fn_` 地址式伪名（全镜像 0 引用、② 不可得）；本批 S22 named 池 **0 个 fn_/sub_ 伪名**（71 行全是 `T_…::slotN` 真模板槽名），因此筛选阶段无需再剔除，② 自然全数可得。
- **瓶颈位置转移**：本批 ② 不再是瓶颈（18/18），③ 成为唯一区分器 —— 16 个工厂行 ③b② 成立（QI HRESULT 真分支），2 个 Vector slot2 因「malloc 空判断 + bool 返回」撞 D-46(A)/模板假句被否。④ 在 16 个工厂行全部靠活 COM 类对象（CoRegisterClassObject）成立，非 direct-only、非 atexit/析构。最终 16/18 四环齐全。

## 待裁（2 项，未擅自扩面）

1. **工厂行以 QueryInterface 分支作 ③b②（16 行）**：机械 survey 在这些行命中的「call→test eax→je」是 `operator new` 空判断（按 S18_B2 应判模板假句）；本批改用**同一函数体内另一个真实可伪证站点** —— 新建对象的 `QueryInterface`（slot0=0x410260，HRESULT `{0,0x80004002,0x80004003}`，`test edi,edi; jge`，失败 Release / 成功回传，两路真不同）作为 ③b②。该被调与 S05_B1 已过审的 `00414290`（call 0x410260→test→jge，HRESULT 同集）同构。若 Lead 要求「③ 必须是 survey 命中的那一路站点」，则这 16 行应改判 ③ FAIL → 全批 0/18；本批按 D-40「只认 ③b、可伪证错误码/返回约定 + 调用方真分支」的字面口径判成立，特此登记待裁。
2. **工厂 CreateInstance 属「IClassFactory 模板级契约」**：16 行语义同族（仅创建类不同），每行的 QI 站点地址、对象 ctor、主 vt、CLSID、注册点均各自独立（见各行 EVIDENCE），非同一段 reason 复用；但契约形态同源。若 Lead 认为「同族模板级 ③b② 低信息量、不单独扩域」（AUDIT3 对析构自摘链 ③b② 曾有类似备注），可整体收紧；本批按卡片「逐行按 D-40 四环核、真成立即证」如实计入，并在此标明同族属性供裁。

## 汇总

- rows_checked：**18**
- ①入口 PASS：**18**
- ② 钉住行数：**18**（含 16 个工厂类 RTTI、2 个 Vector 类 RTTI）
- ③b 成立行数：**16**（16×③b② QI HRESULT 分支）
- ④ 成立行数：**16**（活 COM 类对象，非 atexit/非析构、非 direct-only）
- all_four_rings（严格 D-40/D-43）：**16**，rate = **0.8889**
- delta 产出：**16 行**（006BF810 / 006BF990 / 006BFB10 / 006BFC90 / 006BFE10 / 006BFF90 / 006C0110 / 006C0290 / 006C0410 / 006C0590 / 006C0710 / 006C0890 / 006C0A10 / 006C0B90 / 006C0D10 / 006C0E90）
- 本批 ② 从 S04 的 0 → 18/18；无 fn_ 伪名掺水；唯一分区来自 ③。

## 输出清单
- `REPORT.md`（本文件）、`PROGRESS.md`、`base_rate.tsv`、`delta.tsv`（16 行）
- `EVIDENCE/ROW_<entry>.txt` × 18（逐行四环地址与字节，每行自身锚点）
- `work/`：`filter_b1.py`（筛选）、`recore.py`/`core2.py`（PE/capstone/RTTI 底座）、`analyze.py`/`dump.py`/`probe*.py`/`qi_verify.py`/`obj_qi_verify.py`/`gather.py`/`gen_outputs.py` 与中间 JSON（只读目标、可复算）。
