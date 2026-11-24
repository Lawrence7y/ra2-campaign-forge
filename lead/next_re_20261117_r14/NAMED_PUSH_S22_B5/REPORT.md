# NAMED-PUSH — S22 B5 批次（S22 named 池最后 9 行 vector 族，核完）

> 状态：**完成**。执行纪律已遵：先建目录 → 先写 REPORT 骨架 → 逐行核完即落 `EVIDENCE/`；`PROGRESS.md` 每 5 行追加。
> 卡片：`lead\next_re_20261117_r14\_cards\NAMED-PUSH.md`（全文 80 行读完）。
> 本批：**B5** = `SURVEY_3B2\hits_detail.tsv` 中 `subsystem==S22` AND `p3b2_named==True`，排除 `fn_/sub_` 伪名后，按 entry 升序取「减去 B1(0..17)、B2(18..35)、B3(36..48)、B4(49..61) 已核」后的**最后 9 行**（切片 `[62:71]`），即整个 S22 named 池的最后一批、也是最末的 vector 族。
> 输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S22_B5\`。

> **本批特殊判据（任务下发，与工厂族 B2/B3/B4 完全不同）**：
> - 这 9 行是 **vector 族**（`DynamicVectorClass<T>::slot2` / `VectorClass<T>::slot2`），**不得套用工厂族 C1 判据**（体内 new 对象主虚表 slot0=00410260）。
> - **②**：容器自身虚表 + RTTI 名（`DynamicVectorClass<T>`/`VectorClass<T>` 的实际元素类型）+ 槽号（slot2，slot_off/4==2），三者钉住即成立，钉不住判不成立。
> - **④**：独立判，锚点落在析构器里判 FAIL（㉓）。
> - **③ 可伪证性**：多值状态码 / Find 返 -1 下标约定算；{0,1} 布尔不算。

## 材料自校验
- 目标：`ra2youli\gamemd.exe`；现场 `Get-FileHash -Algorithm SHA256` = `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` ⇒ **与卡片期望逐字一致**。
- ImageBase `0x400000`；`.text = [0x401000, 0x7E038D)`（VirtualSize）。
- Python 3.12.10 / capstone 5.0.7（**skipdata=True**）/ pefile 2024.8.26；无 venv、未 pip install。
- 只读输入：`SURVEY_3B2\hits_detail.tsv`（仅线索）、`W130_atlas\function_atlas.tsv`（仅函数边界）。写域仅本目录。

## 筛选命令（得到本批 9 个 entry）

```powershell
$p = "D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv"
$rows = Import-Csv $p -Delimiter "`t"
$sel = $rows | Where-Object {
  $_.subsystem -eq 'S22' -and $_.p3b2_named -eq 'True' -and
  ($_.name -notmatch '^fn_[0-9A-Fa-f]{8}$') -and ($_.name -notmatch '^sub_[0-9A-Fa-f]{8}$')
} | Sort-Object { [Convert]::ToInt32($_.entry,16) }
$b5 = $sel[62..70]   # B1=[0:18] B2=[18:36] B3=[36:49] B4=[49:62]；最后 9 行 vector 族
$b5 | Format-Table entry,subsystem,name,grade,size,n_call,n_site -AutoSize
```

等价 Python 落盘 `work/filter_b5.py`（`sel.sort(key=int(entry,16))[62:71]`）。
结果：S22 `p3b2_named=True` 共 **71** 行；fn_/sub_ 伪名 **0** 行；排除后 71 行；B1+B2+B3+B4 = 62 行已核；B5 = 升序第 63..71 行 = `007642E0 … 0076BA70`，9 行全部为 vector 族 `slot2`（5 个 `DynamicVectorClass<T>` + 4 个 `VectorClass<T>`）。

## 判定口径（严格 D-40 + 任务本批特化）

1. **①入口**：entry 在 `.text` 内、atlas 边界自洽、`skipdata=0`、末条 `ret 8`（`__stdcall` 两参）。
2. **②类身份（本批特化，不套工厂 C1）**：`dword[slot_va]==entry` 在 `.rdata` 命中容器虚表槽 → 回扫 `[vt-4]=COL(sig=0)` → `[COL+0xC]=TD` → `TD+8` 名串；并复算 `slot_off/4==2`（slot2），RTTI 名中的容器类与实际元素类型与 entry 名逐字对照。三者钉死即 PASS。**②④不同源**：② 锚 `.rdata` RTTI 数据链。
   - 注：通用 `resolve_slot`(k=0..40) 因这些 vector 虚表的槽排布回扫窗口不足漏检；本批用 wide COL 扫描（k=0..0x80）定位，逐行给出 `col/td/name_va` 字节链（见各行 EVIDENCE）。
3. **③整体合同（只认 ③b）**：本批任务规则——**多值状态码 / Find 返 -1 下标约定算；{0,1} 布尔不算**。逐行核出口返回点与 chA 机器命中站点。
4. **④使用见证**：纯虚派发（direct callers=0，非 direct-only），靠 vtable 装表锚点；**锚点落析构器/atexit 清理器判 FAIL（㉓）**；与 ② 不同源。

## 基础率（诚实报数）

分母 = 本批 9 行。

| 档 | 行数 | 口径 |
|---|---:|---|
| 本批行数 | **9** | S22 named 去伪名升序 [62:71]，vector 族 |
| ①入口 PASS | **9** | 全在 `.text`、`skipdata=0`、末条 `ret 8`、atlas 边界自洽 |
| ② 容器虚表+RTTI+slot2 钉住 | **9** | 9 行 entry 作唯一 4B VA 落 `.rdata` 虚表槽 slot2；COL(sig=0)→TD→名串给出容器类与实际元素类型；slot_off/4==2 逐行复算 |
| ③b 成立 | **0** | 9 行出口全为 `{0,1}` AL 布尔（`mov al,1`/`xor al,al`/`sete`）；唯一 chA 站点是 `operator new`(0x7C8E17) 空判断（callee consts=[]、返回指针）→ 按任务规则不计 |
| ④ 成立（非析构） | **5** | 5 个 DynamicVectorClass 行有 ctor/global-init 非析构装表锚；4 个 VectorClass 行只有 ~VectorClass 析构器/atexit 装表锚 → ㉓ FAIL |
| **四环齐全（严格）** | **0** | 瓶颈在 ③b（全 bool）⇒ rate = 0/9 = **0.0000** |

`base_rate.tsv`：`S22_B5  9  9  0  5  0  0.0000`

## 本批 9 行总表（entry / ②③④ / 是否产出）

| # | entry | name(原样) | ①入口 | ②容器vtable/RTTI/slot2 | ③b | ④使用见证 | 四环齐全 | 产出 |
|---:|---|---|---|---|---|---|---|---|
| 1 | 007642E0 | T_DynamicVectorClass_VWaypointClass__::slot2 | PASS | PASS(`DynamicVectorClass<WaypointClass>` slot2) | FAIL(bool) | PASS(ctor) | NO | 否 |
| 2 | 00765840 | T_VectorClass_VT_rc_ptr_VConflict_WorldDominationTour____::slot2 | PASS | PASS(`VectorClass<rc_ptr<Conflict>>` slot2) | FAIL(bool) | FAIL(dtor ㉓) | NO | 否 |
| 3 | 007659F0 | T_DynamicVectorClass_VT_rc_ptr_VConflict_WorldDominationTour____::slot2 | PASS | PASS(`DynamicVectorClass<rc_ptr<Conflict>>` slot2) | FAIL(bool) | PASS(ctor) | NO | 否 |
| 4 | 00766C10 | T_VectorClass_VT_rc_ptr_VGameOption_WorldDominationTour____::slot2 | PASS | PASS(`VectorClass<rc_ptr<GameOption>>` slot2) | FAIL(bool) | FAIL(atexit/dtor ㉓) | NO | 否 |
| 5 | 00766DC0 | T_DynamicVectorClass_VT_rc_ptr_VGameOption_WorldDominationTour____::slot2 | PASS | PASS(`DynamicVectorClass<rc_ptr<GameOption>>` slot2) | FAIL(bool) | PASS(global-init) | NO | 否 |
| 6 | 00769E30 | T_VectorClass_VT_rc_ptr_VTerritory_WorldDominationTour____::slot2 | PASS | PASS(`VectorClass<rc_ptr<Territory>>` slot2) | FAIL(bool) | FAIL(dtor ㉓) | NO | 否 |
| 7 | 00769FE0 | T_DynamicVectorClass_VT_rc_ptr_VTerritory_WorldDominationTour____::slot2 | PASS | PASS(`DynamicVectorClass<rc_ptr<Territory>>` slot2) | FAIL(bool) | PASS(ctor) | NO | 否 |
| 8 | 0076B8C0 | T_VectorClass_VT_rc_ptr_VWDTTerritory____::slot2 | PASS | PASS(`VectorClass<rc_ptr<WDTTerritory>>` slot2) | FAIL(bool) | FAIL(dtor ㉓) | NO | 否 |
| 9 | 0076BA70 | T_DynamicVectorClass_VT_rc_ptr_VWDTTerritory____::slot2 | PASS | PASS(`DynamicVectorClass<rc_ptr<WDTTerritory>>` slot2) | FAIL(bool) | PASS(ctor) | NO | 否 |

## 逐行裁定依据（每行自身地址锚，完整字节见 `EVIDENCE/ROW_<entry>.txt`）

### ① 9/9 PASS
全部 entry 在 `.text`；atlas size/n_instr 与 survey size/n_call 自洽；capstone(skipdata=True) 逐行 skipdata=0（无边界破碎）；末条均 `c2 08 00`（`ret 8`，两参数 `__stdcall`，对应 `VectorClass::slot2` 的 `this + count/初值`）。示例 007642E0：size=306 / 121 insn / skipdata=0 / 末条 `0076440F c20800`。

### ② 9/9 钉住（容器虚表 + RTTI 名 + slot2，独立于工厂 C1）
每行 `dword[slot_va]` = entry（唯一命中 `.rdata`）；回扫 `col_word → COL(sig=0) → TD → TD+8 名串`，RTTI 名逐行给出容器类**与实际元素类型**，`(slot_va - vtable_base)/4 == 2` 复算得 slot2，且 `vtable[2]` 字节 = entry。逐行锚点：

| entry | slot_va | vtable_base | COL→TD | RTTI 名 | slot_no |
|---|---|---|---|---|---|
| 007642E0 | 007F6EDC | 007F6ED4 | 0080D518→00847F78 | `DynamicVectorClass<WaypointClass>` | 2 |
| 00765840 | 007F6F84 | 007F6F7C | 0080D820→00848020 | `VectorClass<rc_ptr<Conflict,WorldDominationTour>>` | 2 |
| 007659F0 | 007F6F54 | 007F6F4C | 0080D6B0→00848068 | `DynamicVectorClass<rc_ptr<Conflict,WDT>>` | 2 |
| 00766C10 | 007F6FFC | 007F6FF4 | 0080D9A0→008482C0 | `VectorClass<rc_ptr<GameOption,WDT>>` | 2 |
| 00766DC0 | 007F6FDC | 007F6FD4 | 0080D970→00848310 | `DynamicVectorClass<rc_ptr<GameOption,WDT>>` | 2 |
| 00769E30 | 007F718C | 007F7184 | 0080DEF8→00848818 | `VectorClass<rc_ptr<Territory,WDT>>` | 2 |
| 00769FE0 | 007F716C | 007F7164 | 0080DE10→00848868 | `DynamicVectorClass<rc_ptr<Territory,WDT>>` | 2 |
| 0076B8C0 | 007F7238 | 007F7230 | 0080E088→00848C18 | `VectorClass<rc_ptr<WDTTerritory>>` | 2 |
| 0076BA70 | 007F7268 | 007F7260 | 0080E0F0→00848C50 | `DynamicVectorClass<rc_ptr<WDTTerritory>>` | 2 |

RTTI 名中的容器类（DynamicVectorClass / VectorClass）与元素类型（WaypointClass、rc_ptr<Conflict/GameOption/Territory/WDTTerritory>）与 entry 名逐字对应，非拿 `slot2` 类名当已证。**② 从 S04 的 0 → 本批 9/9**，硬约束满足。

### ③b 0/9 FAIL（唯一瓶颈：全为 `{0,1}` 布尔）
逐行反汇编（见各行 EVIDENCE + `work/dis_full.py` 输出）证明这 9 个 `slot2` 都是同一套 `VectorClass::Add/Reserve` 模板：入口算 `count*elemsize` → `call 0x7C8E17`(operator new) → `test eax,eax; je`（分配空判断）→ 逐元素构造 / `rc_ptr` 自增拷贝（0x65D480=`rc_ptr::operator=`，ret 4，返回指针）→ 更新 `[this+4]` 缓冲 / `[this+8]` 计数 / `[this+0xc]` 标志 → 出口 `mov al,1`（成功）/ `xor al,al`（失败）/ `sete al`。

- **出口常量集 = {0,1} AL bool**（每行列于 EVIDENCE「③b 返回点」）。按任务本批规则「{0,1} 布尔不算」，可伪证性不成立。
- chA 机械命中唯一站点是 `operator new` 空判断：`callee 0x7C8E17 consts=[]`（返回内存指针，非状态码）、`call_site_falsy=0x0`（指针 null 探测），失败路 AL=0 / 成功路 AL=1。非多值状态码、非 Find -1 下标。
- 0x65D480 / 0x65D430 / 0x65D460 是 `rc_ptr` 引用计数赋值/构造/析构助手（ret 4、写 vtable 0x7F094C、inc/dec refcount），返回指针或 void；附近的 `cmp/jl` 是 `inc esi; cmp esi,ebp; jl` 循环计数，不是对返回值的可伪证分支。
- 三陷阱：无 `eax` 覆写陷阱（返回值在 AL，且 test 紧邻分支）；无多路同一 call；属「分配空判断 + bool 出口」模板假句 → 触 D-46(A)。与 S22 B1 两行 Wstring vector slot2（0069C9C0/0069CBC0）被否口径完全一致。

### ④ 5/9 PASS / 4/9 FAIL（独立于 ②；锚点落析构器判 ㉓）
9 行 direct callers 全为 0（纯虚派发，非 direct-only），④ 靠 vtable 装表锚点。全镜像 `.text` 扫 vtable 立即数写点，逐点判 ctor / dtor / atexit（见 `work/ring4_final.py` 与各 EVIDENCE）：

- **PASS 5 行（DynamicVectorClass，非析构装表锚）**：
  - 007642E0：`0x7F6ED4` 由 ctor 函数 00763C70 在 `00763CEA` 写入（该函数自身是 WaypointPathClass 虚表 007F6E70 的 slot，即活虚方法；无 operator delete）。
  - 007659F0：`0x7F6F4C` 由 ctor 00764B90 在 `00764BF9` 写入（caller 00764B67，无 operator delete）。
  - 00766DC0：`0x7F6FD4` 由全局初始化函数 00766070 在 `0076608D` 写入（`mov [0xB72760],0x7F6FD4`；该函数入口在 .data CRT init 表 0081587C，全局 0xB72760 有 16 处读点 ⇒ 活全局对象）。
  - 00769FE0：`0x7F7164` 由 ctor 00768000 在 `00768052` 写入（caller 00767FD4，无 operator delete）。
  - 0076BA70：`0x7F7260` 由 ctor 0076ABE0 在 `0076AC12` 写入成员子对象（非析构，无 operator delete）。
- **FAIL 4 行（VectorClass 基类，装表锚只在析构器/atexit，㉓）**：
  - 00765840：`0x7F6F7C` 两处写点 00765B68/00765C28 均在 74B 的 `~VectorClass`（00765B60/00765C20，体内 `call 0x7C8B3D` operator delete）→ ㉓。
  - 00766C10：`0x7F6FF4` 写点 007660BF 在 atexit 清理器 007660B0（由 00766072 `push 0x7660B0` + `call 0x7C978A`=atexit 注册），另两处在 ~VectorClass 00766FC0/00767080 → ㉓。
  - 00769E30：`0x7F7184` 写点 0076A5C8/0076A688 均在 ~VectorClass（operator delete）→ ㉓。
  - 0076B8C0：`0x7F7230` 写点 0076BBC8/0076BC18 均在 ~VectorClass（operator delete）→ ㉓。
- **结构性根因**：这 4 行是基类 `VectorClass<T>`，其虚表在活对象里被派生 `DynamicVectorClass<T>` 覆盖（如 0x7F6FF4 基类表只在 atexit/析构时回写，活全局 0xB72760 装的是派生表 0x7F6FD4），因此基类 slot2 的装表锚只能落在析构路径 ⇒ 按 ㉓ 判 FAIL。5 个派生类行的虚表由真实构造器/全局初始化安装 ⇒ PASS。
- **②④不同源**：② 锚 `.rdata` RTTI 链 + 虚表槽；④ 锚 `.text` 装表指令 —— 段/地址/产物类型均不同，非同一虚表槽既证身份又证使用。

## 与 S04 的败因对比（本批有多少行 ② 真的钉住）

- **S04**：73 个 ③b② 机械命中全 `p3b2_named=0`（无名字）——entry 作 4B VA 全镜像 0 命中、无虚表槽、无可回扫 RTTI 链 ⇒ **② 物理不可得**，30+ 行实测全败。
- **本批 S22 B5**：**② 9/9 全数钉住**（容器虚表槽 + COL→TD→名串，给出 `DynamicVectorClass<T>`/`VectorClass<T>` 及实际元素类型，slot_no=2 逐行复算）。与 S04「② 物理不可得」完全对照——卡片的「② 是硬约束」在本批 vector 族 100% 满足，且**未套用工厂 C1 判据**，改用任务指定的容器虚表+RTTI+槽号口径。
- **与 S14 的差异**：S14 named 池掺 16 个 `fn_` 地址式伪名（② 不可得）；本批 0 个 fn_/sub_ 伪名。
- **与 S22 B1 两行 Wstring vector 的对照**：B1 的 0069C9C0/0069CBC0（`DynamicVectorClass<Wstring>::slot2`）因「malloc 空判断 + `{0,1}` bool 出口」被否；本批 9 行同形态，③b 同一口径全否。区别仅在本批额外完成 ②（RTTI/槽号）与 ④（ctor vs dtor 分类）的独立取证。
- **瓶颈位置**：② 不是瓶颈（9/9）；④ 有 4 行因 ㉓ 落败；但决定性瓶颈是 ③b（9/9 为 bool）⇒ 四环齐全 0/9。

## 关于「S22 named 池是否彻底清空」

**是。** S22 `p3b2_named=True`（去 fn_/sub_ 伪名）共 71 行；核完分布：B1=18、B2=18、B3=13、B4=13、B5=9，合计 18+18+13+13+9 = **71 = 全池**。本批 B5 处理的正是 B4 REPORT 中登记的「vector 族 9 行（007642E0..0076BA70，未核，待裁定）」，至此 S22 named 池每一行都已被逐行核过，无遗留。

## 汇总

- rows_checked：**9**
- ①入口 PASS：**9**
- ② 容器虚表+RTTI+slot2 钉住行数：**9**
- ③b 成立行数：**0**（9× FAIL：{0,1} AL bool，按任务规则不计）
- ④ 成立行数：**5**（5 个 DynamicVectorClass 非析构装表锚；4 个 VectorClass 仅析构/atexit 锚 → ㉓ FAIL）
- all_four_rings：**0**，rate = **0.0000**
- delta 产出：**0 行**（表头保留；卡片允许 0 行，不为凑数虚报）

## 输出清单
- `REPORT.md`（本文件）、`PROGRESS.md`、`base_rate.tsv`、`delta.tsv`（0 行数据）
- `EVIDENCE/ROW_<entry>.txt` × 9（逐行四环地址与字节，每行自身锚点）
- `work/`：`filter_b5.py`（筛选）、`recore.py`/`core2.py`（PE/capstone/RTTI 底座，复制自 B4）、`dump_all.py`/`probe_rtti.py`/`dis_full.py`/`ring_analysis.py`/`probe_ring4.py`/`probe_final.py`/`ring4_final.py`（②/③b/④ 取证探针）、`gen_evidence.py`（EVIDENCE 生成）+ 中间 JSON（`b5_rows.json`/`dump.json`/`ring_analysis.json`），全部只读目标、可复算。
