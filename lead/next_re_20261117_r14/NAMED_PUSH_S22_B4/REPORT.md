# NAMED-PUSH — S22 B4 批次（有名字的 ③b② 候选，攻 proved 增量）

> 状态：**完成（按范围 A：13 行工厂族）**。执行纪律已遵：先建目录 → 先写 REPORT 骨架 → 逐行核完即落 `EVIDENCE/`；13 行一次性核完（不足 5 行/批的收口段，逐行落盘记录见 `PROGRESS.md`）。
> 卡片：`lead\next_re_20261117_r14\_cards\NAMED-PUSH.md`（全文 80 行读完）。
> 本批：**B4** = `SURVEY_3B2\hits_detail.tsv` 中 `subsystem==S22` AND `p3b2_named==True`，排除 `fn_XXXXXXXX`/`sub_XXXXXXXX` 伪名后，按 entry 升序「减去 NAMED_PUSH_S22_B1（行 1..18）、B2（行 19..36）、B3（行 37..49）已核」后的剩余行。**S22 具名池最后一批。**
> 输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S22_B4\`。
> **本批特殊约束（任务下发，与 B3 同）**：① ② 必须用**体内新建对象的主虚表（slot0 = `00410260`）**，不得用小成员表；② ④ 锚点落在析构器里判 `FAIL`（㉓）。

## 范围澄清（重要）

筛选得 B4 剩余 **22 行**（B3 REPORT 记 S22 named=71，71−49=22），比任务预估「约 13 行」多。22 行分两族：
- **工厂族（13 行，**本批已完成**）**：`006C3E90 … 006C6110`，全部 `T_TClassFactory_V*::slot3`，与本批 C1/C2 约束（体内 new 对象主虚表 slot0=00410260、④ 锚点非析构器）完全对应 —— 即任务所指「约 13 行」。
- **vector 族（9 行，未核，待 lead 裁定范围）**：`007642E0 … 0076BA70`，`DynamicVectorClass/VectorClass<…>::slot2`，形态完全不同（无体内 new 对象主虚表 slot0=00410260 特征）。

22 行超卡片「每批 ≤18」上限。已就此询问 lead（选项 A 只做前 13 行 / B 做满 18 / C 做全部 22）；**按 A 做完工厂族 13 行并全部落盘**。本 REPORT 统计口径为 13 行；若 lead 改判 B/C，vector 族另行续做（脚本 `make_rows.py` 的 `B4_END` 环境变量已预留扩展到 71）。

## 材料自校验
- 目标：`ra2youli\gamemd.exe`；现场 `Get-FileHash -Algorithm SHA256` = `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` ⇒ **与卡片期望逐字一致**。
- ImageBase `0x400000`；`.text = [0x401000, 0x7E038D)`（VirtualSize）。
- Python 3.12.10 / capstone 5.0.7（**skipdata=True**）/ pefile 2024.8.26；无 venv、未 pip install。
- 只读输入：`SURVEY_3B2\hits_detail.tsv`（仅线索）、`W130_atlas\function_atlas.tsv`（仅函数边界）。写域仅本目录。
- 判据先例：`S1040.md`（B2 审计口径）、`M65-MERGE.md`（FAIL：内嵌成员表误当主虚表）、`S1039.md`（`00414290` 含 `~AircraftClass` ㉓ 脏锚）——均沿用 B3。

## 筛选命令（得到本批候选）

```powershell
$p = "D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv"
$rows = Import-Csv $p -Delimiter "`t"
$sel = $rows | Where-Object {
  $_.subsystem -eq 'S22' -and $_.p3b2_named -eq 'True' -and
  ($_.name -notmatch '^fn_[0-9A-Fa-f]{8}$') -and ($_.name -notmatch '^sub_[0-9A-Fa-f]{8}$')
} | Sort-Object { [Convert]::ToInt32($_.entry,16) }
# B1=$sel[0..17]  B2=$sel[18..35]  B3=$sel[36..48]
$b4 = $sel[49..]   # 剩余 22 行；本批按 A 核工厂族 $sel[49..61]（13 行）
$b4 | Format-Table entry,subsystem,name,grade,size,n_call,n_site -AutoSize
```

等价 Python 落盘 `work/filter_b4.py` + `work/make_rows.py`（`sel.sort(key=int(entry,16))[49:end]`，`end` 默认 62，环境变量 `B4_END` 可改）。结果：S22 `p3b2_named=True` 共 **71** 行；fn_/sub_ 伪名 **0** 行；排除后 **71** 行；B1/B2/B3 共 49 行已核；B4 剩余 **22** 行，本批核工厂族 13 行 `006C3E90 … 006C6110`（均 `TClassFactory::slot3`，工厂虚表槽 `007F3C6C..007F3E94`，每 0x18 一张表，紧接 B3 的 `007F3C54`）。

## 判定口径（严格 D-40，宁严不宽，沿用 B3）
1. **①入口**：entry 在 `.text` 内、atlas 边界自洽、`skipdata=0`、末条 `ret 0x10`。
2. **②类身份**：RTTI 描述符→类名字串 + 工厂虚表槽号独立钉死；**C1 硬约束**：③b② 被调必须是新建对象主虚表 slot0=`00410260`，不得用小成员子对象表（`vt[0]=004105E0` 等 10B stub）；非 `00410260` 判 ② FAIL。
   - ②④不同源：② 锚 `.rdata` RTTI 链；④ 锚 `.text` 分配/装表/注册指令。
3. **③整体合同**：只认 ③b②：`call [eax]`(主 vt slot0=QI)→`mov edi,eax`→`test edi,edi`→`jge`；被调须返回可伪证 HRESULT 三态 `{0,0x80004002,0x80004003}`，调用方真分支、失败 `call [edx+0x20]` 带 delete 标志释放、成功回传 HRESULT。三陷阱逐行排查。
4. **④使用见证**：活 COM 类对象（8B 工厂实例堆分配→行外 ctor 装本类 vt→`ole32!CoRegisterClassObject` 以 CLSID 注册），direct-only 不足；**C2 硬约束**：④ 锚点不得落析构器（㉓），落析构器判 FAIL。

## 基础率（诚实报数）

分母 = 本批 13 行工厂族。

| 档 | 行数 | 口径 |
|---|---:|---|
| 本批行数 | **13** | B4 工厂族（切片 [49:62]） |
| ①入口 PASS | **13** | 全在 `.text`、`skipdata=0`、末条 `ret 0x10`、atlas 边界自洽 |
| ② RTTI 钉住 | **13** | 13 行 entry 均作唯一 4B VA 落在工厂虚表槽，`COL sig=0→TD→名串` 完整，slot#3 自洽 |
| ② 含 C1（主虚表 slot0=00410260） | **11** | 006C3E90(004F6830)、006C4190(0054DC60) 不满足 ⇒ FAIL |
| ③b 成立 | **12** | 12×③b②（QI HRESULT）；006C4190 被调仅两态 `{0,80004002}`、无 80004003 ⇒ FAIL |
| ④使用见证成立（含 C2） | **13** | 13 行均为活 COM 类对象，④ 锚点全在 host `006BB9A0`、host/fc atexit 均空 ⇒ 无锚落析构器（㉓ 排除） |
| **四环齐全（严格 D-40）** | **11** | rate = 11/13 = **0.8462** |

`base_rate.tsv`：`S22_B4  13  11  12  13  11  0.8462`

## 本批 13 行总表（entry / ②③④ / 是否产出）

| # | entry | name(原样) | ①入口 | ② RTTI | ② C1 主vt槽0 | ③b | ④使用见证 | ②④不同源 | 裁定 | 产出 |
|---:|---|---|---|---|---|---|---|---|---|---|
| 1 | 006C3E90 | T_TClassFactory_VHouseClass__::slot3 | PASS | PASS | **FAIL(004F6830)** | PASS(③b②) | PASS(活COM) | 是 | **不成立** | 否 |
| 2 | 006C4190 | T_TClassFactory_VJumpjetLocomotionClass__::slot3 | PASS | PASS | **FAIL(0054DC60)** | **FAIL(仅两态)** | PASS(活COM) | 是 | **不成立** | 否 |
| 3 | 006C5210 | T_TClassFactory_VFactoryClass__::slot3 | PASS | PASS | PASS(00410260) | PASS(③b②) | PASS(活COM) | 是 | **成立** | **是** |
| 4 | 006C5390 | T_TClassFactory_VWarheadTypeClass__::slot3 | PASS | PASS | PASS(00410260) | PASS(③b②) | PASS(活COM) | 是 | **成立** | **是** |
| 5 | 006C5510 | T_TClassFactory_VWeaponTypeClass__::slot3 | PASS | PASS | PASS(00410260) | PASS(③b②) | PASS(活COM) | 是 | **成立** | **是** |
| 6 | 006C5690 | T_TClassFactory_VParticleClass__::slot3 | PASS | PASS | PASS(00410260) | PASS(③b②) | PASS(活COM) | 是 | **成立** | **是** |
| 7 | 006C5810 | T_TClassFactory_VParticleTypeClass__::slot3 | PASS | PASS | PASS(00410260) | PASS(③b②) | PASS(活COM) | 是 | **成立** | **是** |
| 8 | 006C5990 | T_TClassFactory_VParticleSystemClass__::slot3 | PASS | PASS | PASS(00410260) | PASS(③b②) | PASS(活COM) | 是 | **成立** | **是** |
| 9 | 006C5B10 | T_TClassFactory_VParticleSystemTypeClass__::slot3 | PASS | PASS | PASS(00410260) | PASS(③b②) | PASS(活COM) | 是 | **成立** | **是** |
| 10 | 006C5C90 | T_TClassFactory_VAITriggerTypeClass__::slot3 | PASS | PASS | PASS(00410260) | PASS(③b②) | PASS(活COM) | 是 | **成立** | **是** |
| 11 | 006C5E10 | T_TClassFactory_VNeuronClass__::slot3 | PASS | PASS | PASS(00410260) | PASS(③b②) | PASS(活COM) | 是 | **成立** | **是** |
| 12 | 006C5F90 | T_TClassFactory_VFoggedObjectClass__::slot3 | PASS | PASS | PASS(00410260) | PASS(③b②) | PASS(活COM) | 是 | **成立** | **是** |
| 13 | 006C6110 | T_TClassFactory_VAlphaShapeClass__::slot3 | PASS | PASS | PASS(00410260) | PASS(③b②) | PASS(活COM) | 是 | **成立** | **是** |

## 逐行裁定依据（每行自身地址锚，完整字节见 `EVIDENCE/ROW_<entry>.txt`）

**① 13/13**：全部 entry 在 `.text`，`skipdata=0`，atlas size 自洽，末条 `ret 0x10`（`__stdcall` + 4 dword，对上 `IClassFactory::CreateInstance`，遵 `S1040` 不留痕）。

**② RTTI 13/13 钉住 + C1 主虚表槽0 逐行实测**：
- 13 行 entry 作 4B VA 在 `.rdata` 各唯一命中一张工厂虚表槽（`007F3C6C..007F3E94`，每 0x18 一张表），`slot_off=0xC/4=3` 与 `slot3` 逐行自洽；RTTI 链 `COL(sig=0)→TD→名串` 给出 `.?AV?$TClassFactory@V<T>@@@@`。槽号由 offset/4 复算，非拿名字当已证。
- C1（本批重点）：对象 ctor 写 `[this]` 的主 vt 槽0 逐行复算：
  - **11 行 = `00410260`**（多行有内嵌成员表 `vt[0]=004105E0`/`00410580`/`00410590` 或 `007EB6D4`(slot0=`524FC0`) 等 10B stub，均已正确排除，未踩 `M65` 陷阱）。例：`006C5210` 对象 ctor `004C98B0` 写主表 `007E88D0`(slot0=`00410260`)，成员表 `007E88B4`(slot0=`004105E0`) 未误取；`006C5390` 对象 ctor `0075CEC0` 写 esi 成员表 `007EB6D4`/`007E4DD8`、主表写 ebp[0]=`007F6B30`(slot0=`00410260`)。
  - **006C3E90（HouseClass）**：主 this=esi 写的表 slot0 分别 `004EF530`/`004EF5D0`/`005100E0`/`004EF670`/`004A0E60`（均非 HRESULT 三态）；唯一 HRESULT 三态表 `007EA8A0` 写在 `[ebp]`（局部/子对象槽）且 slot0=`004F6830`(≠00410260)。按 C1 硬地址约束 FAIL，详见待裁。
  - **006C4190（JumpjetLocomotionClass）**：对象 ctor `0054AC40` 仅 3 张写表，slot0 分别 `0054DC60`/`0054DFF0`/`0054E020`，无 `00410260`；被调 `0054DC60` 只返回 `{0,80004002}`（缺 80004003）、nret=2，连 ③b 三态都不满足 ⇒ C1 FAIL + ③b FAIL。

**③ 成立 12 行（12×③b②，QI HRESULT 分支；逐行独立地址锚）**：
以 `006C5210` 为样板（各行 QI 站点/对象 ctor/主 vt/CLSID 互不相同，见锚点表与各行 EVIDENCE）：三道 imm 错误码守卫 `mov eax,0x80070057`@`006C521B` / `0x80040110`@`006C5233` / `0x8007000e`@`006C5258`；主站点 `006C526A ff 10`(call [eax]=主 vt slot0 QI `00410260`) → `006C526C 8b f8`(mov edi,eax) → `006C526E 85 ff`(test edi,edi) → `006C5270 7d 09`(jge)；失败路 `006C5278 ff 52 20`(call [edx+0x20]，delete 标志=1)，成功路 `mov eax,edi; ret 0x10`。被调 `00410260` 返回 `{0,0x80004002,0x80004003}`（3 处 `ret 0xc`，`c2 0c 00`），HRESULT 可伪证（非 bool 0/1）。返回值在 edi、`test`/`jge` 零间隔无 eax 覆写；本体内 QI call 仅 1 处（非多路同一 call）；非 ③a/模板假句。语义方向：写出接口指针到 ppvOut，未写反。
**③ FAIL 1 行（006C4190）**：被调 `0054DC60` 只有 2 处 ret，返回常量集 `{0,0x80004002}`（缺 `0x80004003`），不满足 ③b② 可伪证 HRESULT 三态；EVIDENCE 已逐字节登记。

**④ 13/13 成立（每行自身安装/注册锚，非同一锚复用、非析构器；C2 通过）**：
工厂实例是活 COM 类对象：host 初始化函数 `006BB9A0`（size 10256、非 atexit）内对 13 个工厂逐一 `push 8; call 0x7C8E17`(分配 8B 实例) → `call <工厂ctor>`（ctor 写本类 vt 到 [this]）→ `push <CLSID>; push 1; push 1; call esi`，`esi=[0x7E15D8]` = ole32!CoRegisterClassObject。13 行 `host_atexit=[]`、`fc_atexit=[]`、`anchor_in_dtor=False`（㉓ 排除；**④ 锚点均未落析构器**）。各行 alloc/ctor_call/reg_call/CLSID 地址互不相同（见锚点表），非整批共用一段证据。全镜像 direct call 者=0（纯虚派发，非 direct-only）。

**②④不同源（13/13 是）**：② 锚 `.rdata` RTTI 描述符链 + 工厂虚表槽；④ 锚 `.text` 堆分配 + ctor 装表 + CoRegisterClassObject 注册指令 —— 段不同、地址不同、产物类型不同，非同一虚表槽既证身份又证使用。

**每行自身四环锚点表**（②槽/主vt槽0；③QI站点/被调/常量集；④HOST，各行 ctor_call/reg/CLSID 互异见 EVIDENCE）：

| # | entry | ② 槽 / 主vt槽0 | ③ QI站点 / 被调 / 常量集 | ④ alloc / ctor_call / reg / CLSID / host |
|---:|---|---|---|---|
| 1 | 006C3E90 | 007F3C6C / **004F6830(FAIL)** | 006C3EEF / 004F6830 / {0,80004002,80004003} | 006BD0FB / 006BD109 / 006BD123 / 007E9560 / 006BB9A0 |
| 2 | 006C4190 | 007F3C9C / **0054DC60(FAIL)** | 006C41ED / 0054DC60 / **{0,80004002} 两态** | 006BD175 / 006BD183 / 006BD19D / 007E9AC0 / 006BB9A0 |
| 3 | 006C5210 | 007F3DA4 / 00410260 | 006C526A / 00410260 / {0,80004002,80004003} | 006BD414 / 006BD422 / 006BD43C / 007E9820 / 006BB9A0 |
| 4 | 006C5390 | 007F3DBC / 00410260 | 006C53EF / 00410260 / {0,80004002,80004003} | 006BD451 / 006BD45F / 006BD479 / 007E9840 / 006BB9A0 |
| 5 | 006C5510 | 007F3DD4 / 00410260 | 006C556F / 00410260 / {0,80004002,80004003} | 006BD48E / 006BD49C / 006BD4B6 / 007E9830 / 006BB9A0 |
| 6 | 006C5690 | 007F3DEC / 00410260 | 006C56ED / 00410260 / {0,80004002,80004003} | 006BD4CB / 006BD4D9 / 006BD4F3 / 007E9700 / 006BB9A0 |
| 7 | 006C5810 | 007F3E04 / 00410260 | 006C586F / 00410260 / {0,80004002,80004003} | 006BD508 / 006BD516 / 006BD530 / 007E9710 / 006BB9A0 |
| 8 | 006C5990 | 007F3E1C / 00410260 | 006C59ED / 00410260 / {0,80004002,80004003} | 006BD545 / 006BD553 / 006BD56D / 007E96C0 / 006BB9A0 |
| 9 | 006C5B10 | 007F3E34 / 00410260 | 006C5B6F / 00410260 / {0,80004002,80004003} | 006BD582 / 006BD590 / 006BD5AA / 007E96D0 / 006BB9A0 |
| 10 | 006C5C90 | 007F3E4C / 00410260 | 006C5CEF / 00410260 / {0,80004002,80004003} | 006BD5BF / 006BD5CD / 006BD5E7 / 007E9960 / 006BB9A0 |
| 11 | 006C5E10 | 007F3E64 / 00410260 | 006C5E6A / 00410260 / {0,80004002,80004003} | 006BD5FC / 006BD60A / 006BD624 / 007E9980 / 006BB9A0 |
| 12 | 006C5F90 | 007F3E7C / 00410260 | 006C5FEA / 00410260 / {0,80004002,80004003} | 006BD639 / 006BD647 / 006BD661 / 007E9990 / 006BB9A0 |
| 13 | 006C6110 | 007F3E94 / 00410260 | 006C616A / 00410260 / {0,80004002,80004003} | 006BD676 / 006BD684 / 006BD69E / 007E99A0 / 006BB9A0 |

## 与 S04 的败因对比（本批有多少行 ② 真的钉住）

- **S04**：73 个 ③b② 机械命中全 `p3b2_named=0`（无名字）——entry 作 4B VA 全镜像 0 命中、无虚表槽、无可回扫 RTTI 链 ⇒ **② 物理不可得**，30+ 行实测全败。
- **本批 S22 B4**：**RTTI 类身份 13/13 全数钉住**（工厂虚表槽 + COL→TD→名串），与 S04「② 物理不可得」完全对照 —— 卡片的「② 是硬约束」在类身份层面 100% 满足。**但按本批 C1 硬约束（对象主虚表 slot0 必须 = 00410260），只有 11/13 满足**：006C3E90（004F6830，写在 [ebp] 非主 this，兼 HRESULT 三态但地址非规范）与 006C4190（0054DC60，仅两态）被否。这与 B3「11/13、2 FAIL」完全同构：B3 FAIL 的是 006C3710(00414290)/006C3D10(005125A0)，本批 FAIL 的是 006C3E90(004F6830)/006C4190(0054DC60)——均为工厂族的末段/杂类掺入非规范 QI。
- **与 S14 的差异**：S14 named 池掺 16 个 `fn_` 地址式伪名（② 不可得）；本批 S22 named 池 0 个 fn_/sub_ 伪名，筛无需剔除。
- **与 a-S22（B1）审计 FAIL 的对照**：M65 记 B1 两行因「内嵌成员表误当主虚表」被否；本批多行（如 006C5210/006C5390/006C5510）同样有 ctor 多次写成员表（`007E88B4` slot0=`004105E0`、`007EB6D4` slot0=`524FC0`），但已正确排除、取 slot0=`00410260` 的主表，**未踩该陷阱**。
- 结论：**② RTTI 从 S04 的 0 → 本批 13/13；C1 主虚表规范地址 11/13**；四环齐全 11/13 = 0.8462。

## 待裁（2 项，均不擅自判成立）

1. **006C3E90（HouseClass）：主虚表 slot0=`004F6830` 是否接受为规范 QI**。该 QI 字节结构与 `00410260` 同构（`mov eax,[esp+0xc]`→`80004003`/`80004002`、3×`ret 0xc`、常量集 `{0,80004002,80004003}`），工厂行本身 ③b②/④ 全成立；缺的是「slot0 地址恰为 00410260」这一条（且唯一三态表写在 `[ebp]` 而非主 this=esi）。本批按任务硬约束「② 必须用主虚表（slot0=00410260）」从严判 **② FAIL、整行不产出**。若 Lead 认为「同构 HRESULT 三态 QI 即等价主虚表、地址不必精确等于 00410260」，此行可翻为成立（四环 12/13）——特此登记待裁，不自行放宽。（与 B3 的 006C3D10 待裁同类。）
2. **006C4190（JumpjetLocomotionClass）**：无 00410260 主表，且被调 `0054DC60` 只返回 `{0,80004002}`（缺 80004003、nret=2）——即使放宽 C1 地址约束，③b 三态亦不成立 ⇒ **无论 C1 口径如何均不成立**，无需待裁，仅登记。

## 汇总

- rows_checked：**13**
- ①入口 PASS：**13**
- ② RTTI 钉住行数：**13**
- ② 含 C1（主虚表 slot0=00410260）成立行数：**11**
- ③b 成立行数：**12**（12×③b② QI HRESULT；006C4190 不可伪证三态）
- ④ 成立行数：**13**（活 COM 类对象，④ 锚点全在 host 006BB9A0、非 atexit 非析构，㉓ 排除）
- all_four_rings（严格 D-40 + C1/C2）：**11**，rate = **0.8462**
- delta 产出：**11 行**（006C5210 / 006C5390 / 006C5510 / 006C5690 / 006C5810 / 006C5990 / 006C5B10 / 006C5C90 / 006C5E10 / 006C5F90 / 006C6110）
- FAIL 2 行：006C3E90、006C4190（均不产出，理由见上）
- **池状态**：S22 具名池工厂族已耗尽（B1+B2+B3+B4 = 18+18+13+13 = 62 行工厂族全部核完）；另有 vector 族 9 行（007642E0..0076BA70）属本批筛选剩余但形态不同，未核，待 lead 裁定是否纳入。

## 输出清单
- `REPORT.md`（本文件）、`PROGRESS.md`、`base_rate.tsv`、`delta.tsv`（11 行）
- `EVIDENCE/ROW_<entry>.txt` × 13（逐行四环地址与字节，每行自身锚点；含 2 个 FAIL 行）
- `work/`：`filter_b4.py`/`make_rows.py`（筛选）、`recore.py`/`core2.py`（PE/capstone/RTTI 底座，复制自 B3）、`analyze.py`（四环初筛）、`gather.py`（QI/ctor/主vt/注册点取证）、`ring4.py`（④锚点非析构校验）、`probe_mainvt.py`（主虚表识别探针）、`finalize_b4.py`（含 C1/C2 的裁定）、`gen_outputs_b4.py`/`report_table_b4.py`（产物生成）+ 中间 JSON（`b4_rows.json`/`analysis.json`/`gather.json`/`ring4.json`/`verdicts.json`），全部只读目标、可复算。
