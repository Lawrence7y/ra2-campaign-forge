# NAMED-PUSH — S22 B3 批次（有名字的 ③b② 候选，攻 proved 增量）

> 状态：**完成**。执行纪律已遵：先建目录 → 先写 REPORT 骨架 → 逐行核完即落 `EVIDENCE/`；`PROGRESS.md` 每 5 行追加。
> 卡片：`lead\next_re_20261117_r14\_cards\NAMED-PUSH.md`（全文 80 行读完）。
> 本批：**B3** = `SURVEY_3B2\hits_detail.tsv` 中 `subsystem==S22` AND `p3b2_named==True`，排除 `fn_XXXXXXXX`/`sub_XXXXXXXX` 伪名后，按 entry 升序取「减去 NAMED_PUSH_S22_B1（行 1..18）与 NAMED_PUSH_S22_B2（行 19..36）已核过的行」后的**前 13 个**（切片 `[36:49]`，即第 37..49 行）。
> 输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S22_B3\`。
> **本批特殊约束（任务下发）**：① ② 必须用**主虚表**（slot0 = `00410260`），不得用小成员表；② ④ 锚点落在析构器里判 `FAIL`（㉓）。13 行全部为同族 `TClassFactory<T>::slot3` 模板行。

## 材料自校验
- 目标：`ra2youli\gamemd.exe`；现场 `Get-FileHash -Algorithm SHA256` = `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` ⇒ **与卡片期望逐字一致**。
- ImageBase `0x400000`；`.text = [0x401000, 0x7E038D)`（VirtualSize）。
- Python 3.12.10 / capstone 5.0.7（**skipdata=True**）/ pefile 2024.8.26；无 venv、未 pip install。
- 只读输入：`SURVEY_3B2\hits_detail.tsv`（仅当线索）、`W130_atlas\function_atlas.tsv`（仅取函数边界）。写域仅本目录。
- 关键既有裁决（作为判据，非照抄结论）：`S1040.md` 记 a-S22B2 审计口径「逐行重算主虚表 `vt[0]` 均为 `00410260`」；`M65-MERGE.md` 记 FAIL 先例「把内嵌成员表误当对象主虚表，其所谓 QueryInterface 实为析构式函数、不返回 HRESULT 三态」；`S1039.md` 记 `00414290` 内含 `~AircraftClass`（㉓ 脏锚）。

## 筛选命令（得到本批 13 个 entry）

```powershell
$p = "D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv"
$rows = Import-Csv $p -Delimiter "`t"
$sel = $rows | Where-Object {
  $_.subsystem -eq 'S22' -and $_.p3b2_named -eq 'True' -and
  ($_.name -notmatch '^fn_[0-9A-Fa-f]{8}$') -and ($_.name -notmatch '^sub_[0-9A-Fa-f]{8}$')
} | Sort-Object { [Convert]::ToInt32($_.entry,16) }
$b1 = $sel[0..17]    # B1 已核：0069C9C0 .. 006C0E90
$b2 = $sel[18..35]   # B2 已核：006C1010 .. 006C2990
$b3 = $sel[36..48]   # 本批：剩下的前 13 个
$b3 | Format-Table entry,subsystem,name,grade,size,n_call,n_site -AutoSize
```

等价 Python 落盘 `work/filter_b3.py` + `work/make_rows.py`（`sel.sort(key=int(entry,16))[36:49]`）。
结果：S22 `p3b2_named=True` 共 **71** 行；fn_/sub_ 伪名 **0** 行（本子系统 named 行无地址式伪名），排除后仍 **71** 行；B1=[0:18]、B2=[18:36] 共 36 行已核；B3 = 升序第 37..49 行 = `006C2B10 … 006C3D10`，13 行**全部**为 `TClassFactory<T>::slot3`（工厂虚表槽 `007F3B34..007F3C54`，紧接 B2 的 `007F3B1C`）。

## 判定口径（严格 D-40，宁严不宽）

1. **①入口**：entry 在 `.text` 内、atlas 边界自洽、`skipdata=0`、末条 `ret 0x10`。
2. **②类身份**：RTTI 描述符 → 类名字串 + 工厂虚表槽号独立钉死（`slot_off/4==3`），名字中 `Class` 部分仅作线索。
   - **本批 C1 硬约束**：③b② 的被调必须是**新建对象主虚表的 slot0 = 00410260**。判法：对象 ctor 写 `[this]`（esi/ebp/edi 主指针、disp=0）的那张 vt，取 `vt[0]`；逐行实测是否为 `00410260`。小成员子对象表（`vt[0]=004105E0` 等 10B stub）不得顶替。非 `00410260` 判 ② FAIL。
   - **②④不同源**：② 锚 `.rdata` RTTI 数据链；④ 锚 `.text` 分配/装表/注册指令。
3. **③整体合同**：只认 ③b。工厂行走 ③b②：`call [eax]`(主 vt slot0 = QI) → `mov edi,eax` → `test edi,edi` → `jge`；被调须返回**可伪证 HRESULT 三态** `{0,0x80004002,0x80004003}`（非 bool、非 esi 指针），调用方真分支、失败 `call [edx+0x20]` 带 delete 标志释放、成功回传 HRESULT。三陷阱逐行排查。
4. **④使用见证**：活 COM 类对象（8B 工厂实例堆分配 → 行外 ctor 装本类 vt → `ole32!CoRegisterClassObject` 以 CLSID 注册），direct-only 不足。
   - **本批 C2 硬约束**：④ 锚点不得落在析构器（㉓）——逐个核 host 函数与工厂 ctor 的 atexit 注册均为空、锚点地址在 `006BB9A0`（非 atexit 初始化函数）内。落析构器判 FAIL。

## 基础率（诚实报数）

分母 = 本批 13 行。

| 档 | 行数 | 口径 |
|---|---:|---|
| 本批行数 | **13** | S22 named=True（去伪名）减去 B1/B2 后前 13 |
| ①入口 PASS | **13** | 全在 `.text`、`skipdata=0`、末条 `ret 0x10`、atlas 边界自洽 |
| ② RTTI 钉住 | **13** | 13 行 entry 均作唯一 4B VA 落在工厂虚表槽，COL sig=0→TD→名串完整，slot#3 自洽 |
| ② 含 C1（主虚表 slot0=00410260） | **11** | 006C3710(slot0=00414290)、006C3D10(slot0=005125A0) 不满足 ⇒ FAIL |
| ③b 成立 | **12** | 12×③b②（QI HRESULT 三态）；006C3710 被调返回 esi、无可伪证常量 ⇒ FAIL |
| ④使用见证成立 | **13** | 13 行均为活 COM 类对象，④ 锚点全在 host `006BB9A0`、host/fc atexit 均空 ⇒ 无锚落析构器（㉓ 排除） |
| **四环齐全（严格 D-40）** | **11** | rate = 11/13 = **0.8462** |

`base_rate.tsv`：`S22_B3  13  11  12  13  11  0.8462`

## 本批 13 行总表（entry / ②③④ / 是否产出）

| # | entry | name(原样) | ①入口 | ② RTTI | ② C1 主vt槽0 | ③b | ④使用见证 | ②④不同源 | 裁定 | 产出 |
|---:|---|---|---|---|---|---|---|---|---|---|
| 1 | 006C2B10 | T_TClassFactory_VAircraftTypeClass__::slot3 | PASS | PASS | PASS(00410260) | PASS(③b②) | PASS(活COM) | 是 | **成立** | **是** |
| 2 | 006C2C90 | T_TClassFactory_VInfantryTypeClass__::slot3 | PASS | PASS | PASS(00410260) | PASS(③b②) | PASS(活COM) | 是 | **成立** | **是** |
| 3 | 006C2E10 | T_TClassFactory_VBulletTypeClass__::slot3 | PASS | PASS | PASS(00410260) | PASS(③b②) | PASS(活COM) | 是 | **成立** | **是** |
| 4 | 006C2F90 | T_TClassFactory_VIsometricTileTypeClass__::slot3 | PASS | PASS | PASS(00410260) | PASS(③b②) | PASS(活COM) | 是 | **成立** | **是** |
| 5 | 006C3110 | T_TClassFactory_VOverlayTypeClass__::slot3 | PASS | PASS | PASS(00410260) | PASS(③b②) | PASS(活COM) | 是 | **成立** | **是** |
| 6 | 006C3290 | T_TClassFactory_VSmudgeTypeClass__::slot3 | PASS | PASS | PASS(00410260) | PASS(③b②) | PASS(活COM) | 是 | **成立** | **是** |
| 7 | 006C3410 | T_TClassFactory_VUnitClass__::slot3 | PASS | PASS | PASS(00410260) | PASS(③b②) | PASS(活COM) | 是 | **成立** | **是** |
| 8 | 006C3590 | T_TClassFactory_VBuildingClass__::slot3 | PASS | PASS | PASS(00410260) | PASS(③b②) | PASS(活COM) | 是 | **成立** | **是** |
| 9 | 006C3710 | T_TClassFactory_VAircraftClass__::slot3 | PASS | PASS | **FAIL(00414290)** | **FAIL(无HRESULT三态)** | PASS(活COM) | 是 | **不成立** | 否 |
| 10 | 006C3890 | T_TClassFactory_VInfantryClass__::slot3 | PASS | PASS | PASS(00410260) | PASS(③b②) | PASS(活COM) | 是 | **成立** | **是** |
| 11 | 006C3A10 | T_TClassFactory_VAnimClass__::slot3 | PASS | PASS | PASS(00410260) | PASS(③b②) | PASS(活COM) | 是 | **成立** | **是** |
| 12 | 006C3B90 | T_TClassFactory_VAnimTypeClass__::slot3 | PASS | PASS | PASS(00410260) | PASS(③b②) | PASS(活COM) | 是 | **成立** | **是** |
| 13 | 006C3D10 | T_TClassFactory_VHouseTypeClass__::slot3 | PASS | PASS | **FAIL(005125A0)** | PASS(③b②) | PASS(活COM) | 是 | **不成立** | 否 |

## 逐行裁定依据（每行自身地址锚，完整字节见 `EVIDENCE/ROW_<entry>.txt`）

**① 13/13**：全部 entry 在 `.text`，`skipdata=0`，atlas size 自洽，末条 `ret 0x10`（`__stdcall` + 显式 this 的 4 dword，与 `IClassFactory::CreateInstance` 对上，遵 `S1040` 不留痕「不按 3 参/ret 0xC 否这些行」）。

**② RTTI 13/13 钉住 + C1 主虚表槽0 逐行实测**：
- 13 行 entry 作 4B VA 在 `.rdata` 各唯一命中一张工厂虚表槽（`007F3B34..007F3C54`，每 0x18 一张表），`slot_off=0xC/4=3` 与 `slot3` 逐行自洽；RTTI 链 `COL(sig=0)→TD→名串` 给出 `.?AV?$TClassFactory@V<T>@@@@`。槽号由 offset/4 复算，非拿名字当已证。
- C1（本批重点）：对象 ctor 写 `[this]` 的主 vt 槽0 逐行复算：
  - **11 行 = `00410260`**（含 `006C2C90` 双 offset0 写表：ctor `005236A0` 先三次写 edi 成员表 `007EB6D4`(slot0=`524FC0`)/`007E4DD8`，主表是写 esi 的 `007EB610`，slot0=`00410260`；遵 `M65` FAIL 先例未误取成员表）。
  - **006C3710**：主 vt `007E22A4` slot0=`00414290`（≠00410260），成员表 `007E2288` slot0=`0041C640`。`00414290` 内含 `~AircraftClass`（`S1039` ㉓ 脏锚），返回 `esi`、无 HRESULT 三态常量 ⇒ C1 FAIL。
  - **006C3D10**：主 vt `007EAB58` slot0=`005125A0`（≠00410260）；该 QI 结构同 `00410260`（同样在 +0x9/+0xF/+0x26/+0x2C 处返回 `80004003`/`80004002`、3 处 `ret 0xc`），另三张 `[edi]` 写表 `007EAC08/007EABE8/007EABC8` slot0=`5129F0/512A40/512A90`（`ret 4` 非 COM）。按 C1 硬地址约束判 FAIL，详见待裁。

**③ 成立 12 行（12×③b②，QI HRESULT 分支；逐行独立地址锚）**：
以 `006C2B10` 为样板（各行 QI 站点/对象 ctor/主 vt/CLSID 互不相同，见下表与各行 EVIDENCE）：三道 imm 错误码守卫 `mov eax,0x80070057`@`006C2B1B` / `0x80040110`@`006C2B33` / `0x8007000e`@`006C2B5D`；主站点 `006C2B6F ff 10`(call [eax]=主 vt slot0 QI `00410260`) → `006C2B71 8b f8`(mov edi,eax) → `006C2B73 85 ff`(test edi,edi) → `006C2B75 7d 09`(jge)；失败路 `006C2B7D ff 52 20`(call [edx+0x20]，delete 标志=1)，成功路 `mov eax,edi; ret 0x10`。被调 `00410260` 返回 `{0,0x80004002,0x80004003}`（3 处 ret，`c2 0c 00`），HRESULT 可伪证（非 bool 0/1）。返回值在 edi、`test`/`jge` 零间隔无 eax 覆写；本体内 QI call 仅 1 处（非多路同一 call）；非 ③a/模板假句。语义方向：写出接口指针到 ppvOut，未写反。
**③ FAIL 1 行（006C3710）**：被调 `00414290` 只在 `004142A2` 调一次 `00410260`，其 2 处 ret（`004142D7`/`004142EC`）均为 `mov eax,esi; ret 0xc`（返回对象指针、非 HRESULT），`callee_return_profile` 可伪证常量集为空 ⇒ 不满足 ③b②「可伪证错误码/返回约定」。

**④ 13/13 成立（每行自身安装/注册锚，非同一锚复用、非析构器；C2 通过）**：
工厂实例是活 COM 类对象：host 初始化函数 `006BB9A0`（size 10256、非 atexit）内对 13 个工厂逐一 `push 8; call 0x7C8E17`(分配 8B 实例) → `call <工厂ctor>`（ctor 写本类 vt 到 [this]）→ `push <CLSID>; push 1; push 1; call esi`，`esi=[0x7E15D8]@006BC43F = ole32!CoRegisterClassObject`。13 行 `host_atexit=[]`、`fc_atexit=[]`（均空）、`anchor_in_dtor=False`（㉓ 排除；**④ 锚点均未落析构器**）。全部 13 个 entry 全镜像 direct call 者=0（纯虚派发，非 direct-only）。每行 alloc/ctor_call/reg_call/CLSID 地址互不相同（见下表），非整批共用一段证据。

**②④不同源（13/13 是）**：② 锚 `.rdata` RTTI 描述符链 + 工厂虚表槽；④ 锚 `.text` 堆分配 + ctor 装表 + CoRegisterClassObject 注册指令 —— 段不同、地址不同、产物类型不同，非同一虚表槽既证身份又证使用。

**每行自身四环锚点表**（entry 后：②槽/主vt槽0；③QI站点/被调/常量集；④alloc/ctor_call/reg_call/CLSID/host-atexit）：

| # | entry | ② 槽 / 主vt槽0 | ③ QI站点 / 被调 / 常量集 | ④ alloc / ctor_call / reg / CLSID / host |
|---:|---|---|---|---|
| 1 | 006C2B10 | 007F3B34 / 00410260 | 006C2B6F / 00410260 / {0,80004002,80004003} | 006BCDE2 / 006BCDF0 / 006BCE0A / 007E95B0 / 006BB9A0 |
| 2 | 006C2C90 | 007F3B4C / 00410260 | 006C2CEF / 00410260 / {0,80004002,80004003} | 006BCE1F / 006BCE2D / 006BCE47 / 007E95A0 / 006BB9A0 |
| 3 | 006C2E10 | 007F3B64 / 00410260 | 006C2E6F / 00410260 / {0,80004002,80004003} | 006BCE5C / 006BCE6A / 006BCE84 / 007E95D0 / 006BB9A0 |
| 4 | 006C2F90 | 007F3B7C / 00410260 | 006C2FF7 / 00410260 / {0,80004002,80004003} | 006BCE99 / 006BCEA7 / 006BCEC1 / 007E95F0 / 006BB9A0 |
| 5 | 006C3110 | 007F3B94 / 00410260 | 006C316F / 00410260 / {0,80004002,80004003} | 006BCED6 / 006BCEE4 / 006BCFFE / 007E9600 / 006BB9A0 |
| 6 | 006C3290 | 007F3BAC / 00410260 | 006C32EF / 00410260 / {0,80004002,80004003} | 006BCF13 / 006BCF21 / 006BCF3B / 007E9610 / 006BB9A0 |
| 7 | 006C3410 | 007F3BC4 / 00410260 | 006C3471 / 00410260 / {0,80004002,80004003} | 006BCF50 / 006BCF5E / 006BCF78 / 007E96F0 / 006BB9A0 |
| 8 | 006C3590 | 007F3BDC / 00410260 | 006C35F1 / 00410260 / {0,80004002,80004003} | 006BCF8D / 006BCF9B / 006BCFB5 / 007E96A0 / 006BB9A0 |
| 9 | 006C3710 | 007F3BF4 / **00414290(FAIL)** | 006C3771 / 00414290 / **{} FAIL** | 006BCFCA / 006BCFD8 / 006BCFF2 / 007E9660 / 006BB9A0 |
| 10 | 006C3890 | 007F3C0C / 00410260 | 006C38F1 / 00410260 / {0,80004002,80004003} | 006BD007 / 006BD015 / 006BD02F / 007E9680 / 006BB9A0 |
| 11 | 006C3A10 | 007F3C24 / 00410260 | 006C3A6D / 00410260 / {0,80004002,80004003} | 006BD044 / 006BD052 / 006BD06C / 007E9670 / 006BB9A0 |
| 12 | 006C3B90 | 007F3C3C / 00410260 | 006C3BEF / 00410260 / {0,80004002,80004003} | 006BD081 / 006BD08F / 006BD0A9 / 007E9620 / 006BB9A0 |
| 13 | 006C3D10 | 007F3C54 / **005125A0(FAIL)** | 006C3D6F / 005125A0 / {0,80004002,80004003} | 006BD0BE / 006BD0CC / 006BD0E6 / 007E9630 / 006BB9A0 |

## 与 S04 的败因对比（本批有多少行 ② 真的钉住）

- **S04**：73 个 ③b② 机械命中全 `p3b2_named=0`（无名字）——entry 作 4B VA 全镜像 0 命中、无虚表槽、无可回扫 RTTI 链 ⇒ **② 物理不可得**，30+ 行实测全败。
- **本批 S22 B3**：**RTTI 类身份 13/13 全数钉住**（工厂虚表槽 + COL→TD→名串），与 S04「② 物理不可得」完全对照 —— 卡片的「② 是硬约束」在类身份层面 100% 满足。**但按本批额外 C1 硬约束（对象主虚表 slot0 必须 = 00410260），只有 11/13 满足**：006C3710（00414290，兼 ㉓ 脏锚、③b 不可伪证）与 006C3D10（005125A0，HRESULT 三态同构但地址非规范）被否。这正是本批与 B2「18/18 全过」的差别：B2 段全为主表 00410260，本段末段掺入 2 行非规范 QI 地址。
- **与 S14 的差异**：S14 named 池掺 16 个 `fn_` 地址式伪名（② 不可得）；本批 S22 named 池 0 个 fn_/sub_ 伪名，筛无需剔除。
- **与 a-S22（B1）审计 FAIL 的对照**：M65 记 B1 两行因「内嵌成员表误当主虚表」被否；本批 `006C2C90` 同样有 ctor 多次写 edi 成员表（`007EB6D4`，slot0=`524FC0` 析构式），但已正确取写 esi 的主表 `007EB610`（slot0=`00410260`），**未踩该陷阱**。
- 结论：**② RTTI 从 S04 的 0 → 本批 13/13；C1 主虚表规范地址 11/13**；四环齐全 11/13 = 0.8462。

## 待裁（2 项，均不擅自判成立）

1. **006C3D10（HouseTypeClass）：主虚表 slot0=`005125A0` 是否接受为规范 QI**。该 QI 字节结构与 `00410260` 完全同构（同样 `mov eax,[esp+0xc]`→`mov eax,80004003`/`80004002`、3×`ret 0xc`、常量集 `{0,80004002,80004003}`），工厂行本身 ③b②/④ 全成立，缺的只是「slot0 地址恰为 00410260」这一条。本批按任务硬约束「② 必须用主虚表（slot0=00410260）」从严判 **② FAIL、整行不产出**。若 Lead 认为「同构 HRESULT 三态 QI 即等价主虚表、地址不必精确等于 00410260」，此行可翻为成立（四环 12/13）——特此登记待裁，不自行放宽。
2. **同族模板级 ③b② 低信息量**：11 个成立行语义同族（仅创建类不同），逐行 QI 站点/对象 ctor/主 vt/工厂 vt/COL/TD/CLSID/注册点均各自独立（见锚点表与各行 EVIDENCE），非同一段 reason 复用；但契约形态同源（IClassFactory 模板级）。与 B1/B2/M65 既有账口径一致（Lead 已裁定接受该形态并标注「模板级低信息量 ③b②」），本批照此计入并标明同族属性。

## 汇总

- rows_checked：**13**
- ①入口 PASS：**13**
- ② RTTI 钉住行数：**13**
- ② 含 C1（主虚表 slot0=00410260）成立行数：**11**
- ③b 成立行数：**12**（12×③b② QI HRESULT 分支；006C3710 不可伪证）
- ④ 成立行数：**13**（活 COM 类对象，④ 锚点全在 host 006BB9A0、非 atexit 非析构、非 direct-only；㉓ 排除）
- all_four_rings（严格 D-40 + C1/C2）：**11**，rate = **0.8462**
- delta 产出：**11 行**（006C2B10 / 006C2C90 / 006C2E10 / 006C2F90 / 006C3110 / 006C3290 / 006C3410 / 006C3590 / 006C3890 / 006C3A10 / 006C3B90）
- FAIL 2 行：006C3710、006C3D10（均不产出，理由见上）

## 输出清单
- `REPORT.md`（本文件）、`PROGRESS.md`、`base_rate.tsv`、`delta.tsv`（11 行）
- `EVIDENCE/ROW_<entry>.txt` × 13（逐行四环地址与字节，每行自身锚点；含 2 个 FAIL 行）
- `work/`：`filter_b3.py`/`make_rows.py`（筛选）、`recore.py`/`core2.py`（PE/capstone/RTTI 底座，复制自 B2）、`analyze.py`（四环初筛）、`gather.py`（QI/ctor/主vt/注册点取证）、`ring4.py`（④锚点非析构校验）、`probe_ambig.py`/`probe_mainvt.py`/`probe_facvt.py`（主虚表识别探针）、`finalize_b3.py`（含 C1/C2 的裁定）、`gen_outputs_b3.py`/`report_table_b3.py`（产物生成）+ 中间 JSON（`b3_rows.json`/`analysis.json`/`gather.json`/`ring4.json`/`verdicts.json`），全部只读目标、可复算。
