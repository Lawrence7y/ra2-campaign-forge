# NAMED-PUSH — S09 B1 批次（有名字的 ③b② 候选，攻 proved 增量）

> 状态：**完成**。执行纪律已遵：先建目录 → 先写 REPORT 骨架 → 逐行核完即落 `EVIDENCE/`；`PROGRESS.md` 每 5 行追加。
> 卡片：`lead\next_re_20261117_r14\_cards\NAMED-PUSH.md`（80 行全文读完）
> 本批：**B1** = `SURVEY_3B2\hits_detail.tsv` 中 `subsystem==S09` AND `p3b2_named==True`，**再排除地址式伪名 `fn_XXXXXXXX` / `sub_XXXXXXXX`**，按 entry 升序取**第 1..18 个**。
> 输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S09_B1\`（卡片 `<你的子系统>`=S09、`<你的目录>`=本目录）。

## 材料自校验
- 目标：`ra2youli\gamemd.exe`；现场 `Get-FileHash -Algorithm SHA256` = `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` ⇒ **与卡片期望逐字一致**。
- ImageBase `0x400000`；`.text = [0x401000, 0x7E038D)`。
- Python 3.12.10 / capstone 5.0.7（**skipdata=True**）/ pefile 2024.8.26；无 venv、未 pip install、未用 Ghidra。
- 只读输入：`SURVEY_3B2\hits_detail.tsv`（仅当线索）、`W130_atlas\function_atlas.tsv`（仅取函数边界）。未改 `coverage.tsv` / `PANEL.md` / `R14_COMMON.md` / 台账 / `SURVEY_3B2` / `S04_PUSH_*`。写域仅本目录。

## 筛选命令（得到本批 18 个 entry）

```powershell
$p = "D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv"
$rows = Import-Csv $p -Delimiter "`t"
$sel = $rows | Where-Object {
  $_.subsystem -eq 'S09' -and
  $_.p3b2_named -eq 'True' -and
  ($_.name -notmatch '^(fn_|sub_)[0-9A-Fa-f]{8}$')
} | Sort-Object { [Convert]::ToUInt32($_.entry,16) }
$b1 = $sel[0..17]   # 第 1..18 个
$b1 | Format-Table entry,subsystem,name,grade,size,n_call,n_site -AutoSize
```

结果：S09 `p3b2_named=True` 共 **29** 行，其中 `fn_`/`sub_` 地址式伪名 **0** 个（29 个全是 `Class::slotN` / `Class::Method` 真名形态），排除后仍 **29** 行；本批取升序第 1..18 行 = `00478BA0 … 0069DEB0`。等价脚本落盘 `_work/filter_b1.py`（正则 `^(fn_|sub_)[0-9A-Fa-f]{8}$` 排除伪名后 `sort(key=int(entry,16))[0:18]`）。

## 判定口径（严格 D-40，宁严不宽）

1. **①入口**：entry 在 `.text` 内、atlas 边界自洽、`skipdata=0`、末条为 `ret`/`jmp`。
2. **②类身份**：数据段中 entry 作 4B VA 的槽 → 回扫 `[vt-4]=COL(sig=0)` → `[COL+0xC]=TD` → `TD+8` 名串；并要求 `slot_off/4 == 线索槽号`。`Class::` 部分仅作线索，不参与判定；钉不死判 FAIL。
   - **小成员表核对**：确认槽所属 vtable 的 `[vt-4]` 有 sig=0 的 COL + `.?AV` 名串、slot0 为类特有函数（非公共 00410260/QueryInterface），排除「小成员表冒充主虚表」。
   - 回扫深度 k≤400（core2 内置 k≤40 会漏 slot39/40/43/45 等高位槽；本批用 `_work/ring2_deep.py` 重算，**全部 18 行 slot 号与线索自洽**）。
3. **③整体合同**：只认 ③b。
   - **③b②**：站点 `call` → `test/cmp eax` → `jcc`，被调**返回约定可从字节伪证**（多值状态码 / Find 返 -1 下标约定算；**{0,1} 布尔不算**；0/指针空检查也不算错误码），且调用方真的拿它分支、两路动作真不同；`test` 与 `jcc` 之间无 eax 覆写；单 call 非多路同一 call。
   - **③b①**：跳转表 + 越界检查，逐项目标可单独验证。**③b③** 内存形状断言。**③b④** 完整循环 I/O 带边界检查且循环体内有非栈写（禁止把被调用者内部的写当循环内非栈写）。
   - **禁止** ③a 形态（单调用+单写、纯转发、零+默认、无分支直线）、模板假句（对象初始化/清零式）。
4. **④使用见证**：行外、非 atexit 的构造安装点（`mov [reg], vt`，写在 `.text` 构造函数体，㉓ 排除 atexit 注册的析构器），或真实直接调用者；**direct-only 不足**；且与 ② 不同源。
5. **②④不同源**：② 锚数据段的 RTTI/虚表槽字节，④ 锚 `.text` 的构造安装指令字节；段/地址/产物类型均不同。
6. 三陷阱逐行排查：eax 覆写、多路同一 call、模板假句。

> **本批方法增量**：机械 ③b② 屏幕（recore `channel_screen_A`）只追踪 `mov/xor eax` 的返回常量，会把 `or eax,-1`、`and eax,2` 这类多值状态码误判为无伪证常量（如 004A33A0 只报 `0x1`）。本批用 `_work/retprof.py` 逐 ret 跟踪 eax 来源，捕获 `or/and/neg/sbb` 形态，才把唯一真成立行的多值返回约定钉死。

## 基础率（诚实报数）

| 档 | 行数 | 口径 |
|---|---:|---|
| 本批行数 | **18** | S09 named=True 升序第 1..18（伪名 0 个） |
| ①入口 PASS | **18** | 全部在 `.text`、`skipdata=0`、末条 ret/jmp |
| ②类身份钉住 | **18** | 18/18 全数由 RTTI(COL→TD→.?AV 名串)+虚表槽独立钉死；slot 号字节复算与线索自洽 |
| ③b 成立 | **1** | 1×③b②（004F45B0），其余 17 行为 {0,1} 布尔 / null 指针检查 / 分类谓词 / 运行时对象虚调不可伪证 |
| ④使用见证成立 | **18** | 18 行均有行外、非 atexit 的构造安装点（活虚表派发），②④ 不同源 |
| **四环齐全** | **1** | rate = 1/18 = **0.0556** |

`base_rate.tsv`：`NAMED_PUSH_S09_B1  18  18  1  18  1  0.0556`

## 本批 18 行总表

| # | entry | name(原样) | ① | ② | ③ | ④ | ②④不同源 | 裁定 | 产出 |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | 00478BA0 | CCToolTip::slot1 | PASS | PASS(.?AVCCToolTip@@) | FAIL(虚调 [eax+0x28] 运行期对象，被调不可静态伪证) | PASS(0x7784A3) | 是 | 不成立 | 否 |
| 2 | 00479050 | CCToolTip::slot5 | PASS | PASS(.?AVCCToolTip@@) | FAIL(同上虚调 + ③a 转发壳) | PASS(0x7784A3) | 是 | 不成立 | 否 |
| 3 | 00488350 | CheckListClass::slot39 | PASS | PASS(.?AVCheckListClass@@) | FAIL(00557AE0 返 0/表项指针，null 检查) | PASS(0x4882D3) | 是 | 不成立 | 否 |
| 4 | 00488360 | CheckListClass::slot40 | PASS | PASS(.?AVCheckListClass@@) | FAIL(00557AC0 返 0/表项指针) | PASS(0x4882D3) | 是 | 不成立 | 否 |
| 5 | 00488380 | CheckListClass::slot43 | PASS | PASS(.?AVCheckListClass@@) | FAIL(strcmp 比较谓词 + 写在被调内) | PASS(0x4882D3) | 是 | 不成立 | 否 |
| 6 | 004883F0 | CheckListClass::slot45 | PASS | PASS(.?AVCheckListClass@@) | FAIL(同 slot43) | PASS(0x4882D3) | 是 | 不成立 | 否 |
| 7 | 004884A0 | CheckListClass::slot31 | PASS | PASS(.?AVCheckListClass@@) | FAIL(00557AC0 null 检查) | PASS(0x4882D3) | 是 | 不成立 | 否 |
| 8 | 004A57B0 | Dial8Class::slot27 | PASS | PASS(.?AVDial8Class@@) | FAIL(0048E620→004E1550 返 {0,1}) | PASS(0x4A53DA) | 是 | 不成立 | 否 |
| 9 | 004AC380 | DisplayClass::LMBDown | PASS | PASS(.?AVDisplayClass@@ 等 7 表 slot47) | FAIL(无单一可伪证返回约定) | PASS(0x40D295) | 是 | 不成立 | 否 |
| 10 | 004B5530 | DropListClass::slot42 | PASS | PASS(.?AVDropListClass@@) | FAIL(无 p3 站点) | PASS(0x4B55F9) | 是 | 不成立 | 否 |
| 11 | 004C3110 | DropListClass::slot27 | PASS | PASS(.?AVDropListClass@@) | FAIL(0048E620→{0,1}) | PASS(0x4B55F9) | 是 | 不成立 | 否 |
| 12 | 004C3420 | DropListClass::slot38 | PASS | PASS(.?AVDropListClass@@) | FAIL(CRT 分类位掩码按布尔消费) | PASS(0x4B55F9) | 是 | 不成立 | 否 |
| 13 | 004E2830 | GaugeClass::slot31 | PASS | PASS(.?AVGaugeClass@@) | FAIL(循环写但 I/O 经虚调不可逐路验证；返 1/0 布尔) | PASS(0x4E2533) | 是 | 不成立(边界，待裁) | 否 |
| 14 | 004E2B50 | TriColorGaugeClass::slot27 | PASS | PASS(.?AVTriColorGauge@@) | FAIL(004E2690 返 {0,1}) | PASS(0x4E2AD5) | 是 | 不成立 | 否 |
| 15 | 004F37A0 | GraphicMenuImageItem::slot3 | PASS | PASS(.?AVGraphicMenuImageItem@@) | FAIL(new/005CCC30 null 检查) | PASS(0x4F34B3) | 是 | 不成立 | 否 |
| 16 | 004F45B0 | MouseClass::slot17 | PASS | PASS(.?AVMouseClass@@) | **PASS(③b② 多值状态 {-1,1,2,0})** | PASS(0x40D295) | 是 | **成立** | **是** |
| 17 | 00557920 | CheckListClass::slot27 | PASS | PASS(.?AVCheckListClass@@) | FAIL(004E1550 {0,1} + 004A5A50 不可伪证) | PASS(0x4882D3) | 是 | 不成立 | 否 |
| 18 | 0069DEB0 | ShapeButtonClass::slot27 | PASS | PASS(.?AVShapeButtonClass@@) | FAIL(0048E620→{0,1}) | PASS(0x69DD23) | 是 | 不成立 | 否 |

## 逐行裁定依据（每行自身地址锚；字节见 `EVIDENCE/ROW_<entry>.txt`）

**② 18/18（RTTI + 虚表槽双证据，slot 号字节复算）**
`00478BA0` 槽 `007F74C8`=`b0 45 4f 00`(vt `007F74C4`+4，slot#1)→COL `0080E560`→TD `00849EE0`→`.?AVCCToolTip@@`；`00479050` 槽 `007F74D8`(slot#5)→同 COL；`00488350/360/380/3F0/004884A0` 槽 `007E5020/24/30/38/007E5000`(vt `007E4F84`，slot#39/40/43/45/31)→COL `007FD150`→TD `0081D128`→`.?AVCheckListClass@@`；`004A57B0` 槽 `007E5EA8`(slot#27)→`.?AVDial8Class@@`；`004AC380::LMBDown` 出现在 7 张表的 slot#47（含 `.?AVDisplayClass@@` vt `007E6114`）；`004B5530` 槽 `007E8074`(slot#42)→`.?AVDropListClass@@`；`004C3110/004C3420` 槽 `007E8038/64`(slot#27/38)→`.?AVDropListClass@@`（另见 EditClass 同槽）；`004E2830` 槽 `007E9400`(slot#31)→`.?AVGaugeClass@@`；`004E2B50` 槽 `007E949C`(slot#27)→`.?AVTriColorGaugeClass@@`；`004F37A0` 槽 `007EA680`(slot#3)→`.?AVGraphicMenuImageItem@@`；`004F45B0` 槽 `007E19A8`(slot#17)→`.?AVMouseClass@@`（另 8 张表同槽）；`00557920` 槽 `007E4FF0`(slot#27)→`.?AVCheckListClass@@`；`0069DEB0` 槽 `007E80F4`(slot#27)→`.?AVShapeButtonClass@@`。全部 sig=0、slot0 为类特有函数（如 CheckListClass slot0=004886E0、MouseClass slot0=004F4240），非小成员表。逐行字节见各 EVIDENCE。

**③ 成立 1 行**
- `004F45B0` MouseClass::slot17（**③b②**）：站点 `0x004F45EA` `e8 b1 ed fa ff`(call 004A33A0) → `0x004F45EF` `85 c0`(test eax,eax) → `0x004F45F1` `0f 85 4c 01 00 00`(jne→0x4F4743)，零 eax 覆写。被调 004A33A0 返回约定字节可伪证：`0x4A33BC` `83 c8 ff`(or eax,-1)→ret、`0x4A3465` `b8 01 00 00 00`(mov eax,1)→ret、`0x4A3581` `f7 d8 … 1b c0 … 83 e0 02`(neg/sbb/and eax,2)→ret、成功路 `0x4A3434` ret ⇒ 失败返多值 {-1,1,2}、成功返 0（多值状态码，非 {0,1} 布尔）。调用方 jne 路 `0x4F4743` 释放收尾；fall-through `0x4F45F7` 起二次校验 + 构造渐变色 + 多次 004A35A0/35F0/3840/3660 写显示状态，两路动作真不同。第二站点 `0x004F4602` 同型。非多路同一 call。

**③ FAIL 17 行（逐行独立理由，详见各 EVIDENCE）**
- 运行期对象虚调不可静态伪证：`00478BA0`/`00479050`（`call [eax+0x28]` on 全局指针 [0x887640]，静态值 0，vtable 运行期装入）；`004AC380`/`004B5530`（多处虚调/指针判断，无单一可伪证约定）。
- 0/表项指针 null 检查（非错误码）：`00488350`(00557AE0)、`00488360`/`004883F0`/`004884A0`(00557AC0)、`004F37A0`(new/005CCC30)。
- strcmp 比较谓词按布尔消费 + 写落在被调内：`00488380`/`004883F0`(007DD0F8 + 0057730/7C8B3D)。
- 被调返 {0,1} 布尔（明确不计）：`004A57B0`/`004C3110`/`0069DEB0`(0048E620→004E1550)、`004E2B50`(004E2690)、`00557920`(004E1550)。
- CRT 字符分类位掩码按布尔消费：`004C3420`(007C990E/007C9A31/007C9A8D/007C998C/toupper)。
- 其他：`00557920` 的 004A5A50 出口为 callret（非固定错误码）；`004E2830` 循环 I/O 经虚调不可逐路验证且返回 1/0（见待裁）。

**④ 18/18（全部行外、非 atexit 构造安装点）**
每行匹配 slot 的 vtable 均在 `.text` 构造函数体内被写入对象：`00478BA0`/`00479050`→`0x7784A3`(in 0x7784A0)；`00488350/360/380/3F0/004884A0/00557920`→`0x4882D3`(in 0x4882D0)及 `0x4886E3`；`004A57B0`→`0x4A53DA`；`004AC380`→`0x40D295`；`004B5530/004C3110/004C3420`→`0x4B55F9`(in 0x4B55F0)及 `0x4C30B3`；`004E2830`→`0x4E2533`；`004E2B50`→`0x4E2AD5`；`004F37A0`→`0x4F34B3`/`0x4F3607`/`0x4F3847`；`004F45B0`→`0x40D295`(in 0x40D290)与 `0x5BDA4A`(in 0x5BDA40，先 call 基类 ctor 0x692290 再装 vt)；`0069DEB0`→`0x69DD23` 等。全部逐点核过非 `push<fn>; call 0x7C978A`（`_work/atexit_check.py`），排除 ㉓ 析构器陷阱；②④ 段不同（.rdata vs .text），不同源。

## 与 S04 的败因对比（本批有多少行 ② 真的钉住了）

- **S04**：73 个 ③b② 机械命中 `p3b2_named=0`（全无名字）——entry 作 4B VA 镜像 0 命中、无虚表槽、无可回扫 RTTI 链 ⇒ **② 物理不可得**，30+ 行实测全败。
- **本批 S09 B1**：18 行里 **18 行 ② 被 RTTI + 虚表独立钉死**（18/18=100%），slot 号由字节复算与线索逐行自洽。S09 与 S14/S05 同类，`Class::slotN` 指向真实主虚表槽，② 完全可得。
- **注意 core2 k≤40 的假阴性**：若沿用 S14_B2 的 `resolve_slot`（回扫 k≤40），`00488350/360/380/3F0`（slot#39/40/43/45，off 156~180）会被误判为「无 RTTI 链」⇒ ② 会假败 4 行。本批用 k≤400 重算纠正，18/18 全中。建议后续批次统一用深回扫。
- **瓶颈在 ③ 不在 ②**：18 行有 ② 有 ④，但 ③b 只有 1 行成立。S09 是 UI 构件类（ToolTip/CheckList/DropList/Gauge/Mouse…），事件处理函数普遍是「取项 null 检查 / {0,1} 布尔谓词 / CRT 字符分类 / 运行期对象虚调」，缺少 S05/S14 抽象类型类那种 Find -1 / QueryInterface HRESULT 的可伪证多值返回约定。这是语义层面的稀缺，不是取证问题。
- 结论：**② 从 S04 的 0 → 本批 18/18**；但 proved 增量只有 **1 行**（MouseClass::slot17，唯一带多值状态码返回约定的行）。

## 待裁（2 项，未擅自扩面）

1. **`004E2830` GaugeClass::slot31 的 ③b④**：存在带边界检查的递减循环（`0x4E2902 test eax,eax / 0x4E2904 jle`，循环体 `0x4E2907 mov [esi+0x38],eax` 非栈写），但数据 I/O 经虚调 `[edx+0xa0]`/`[edx+0x8c]`（被调内写），无法逐路验证完整 I/O，且出口固定返 1/0。我判 FAIL。若 Lead 认「边界循环 + 体内非栈写」即满足 ③b④（放宽逐路 I/O 验证），可 +1 → 2/18。
2. **多值状态码是否需调用方按值区分**：`004F45B0` 的调用方是 `test eax,eax; jne`（0 vs 非 0）消费多值码 {-1,1,2,0}，未按具体值分别分支。我判成立（被调确实返回可被字节伪证的多值错误码，卡口径『失败返回什么/成功返回什么』满足）。若 Lead 要求调用方按每个失败码分别分支，则本批 -1 → 0/18。

## 汇总

- rows_checked：**18**
- ② 钉住行数：**18**（全部 RTTI+vtable 独立钉死，slot 号字节复算自洽）
- ③b 成立行数：**1**（1×③b②）
- ④ 成立行数：**18**（全部行外非 atexit 构造安装点，②④ 不同源）
- all_four_rings（严格 D-40）：**1**，rate = **0.0556**
- delta 产出：**1 行**（`004F45B0` MouseClass::slot17，`grade=[已证]`）

## 输出清单

- `REPORT.md`（本文件）、`PROGRESS.md`、`base_rate.tsv`、`delta.tsv`（1 行）
- `EVIDENCE/ROW_<entry>.txt` × 18（逐行四环地址与字节，每行独立锚点）
- `_work/`：`filter_b1.py`（筛选）、`recore.py`/`core2.py`（PE/capstone/RTTI 底座）、`ring2_deep.py`（k≤400 深回扫）、`ring4_deep.py`（④ 安装点+atexit）、`retprof.py`/`callee_scan.py`（返回约定多值伪证）、`atexit_check.py`（㉓）、`probe.py`/`dump.py`/`loopscan.py`/`inspect_va.py`（取证）、`analyze.py`/`summarize.py`/`gen_facts.py`/`gen_anchors.py`/`gen_outputs.py`（逐行事实与产物生成）+ 中间 JSON/TXT，全部只读目标、可复算。
