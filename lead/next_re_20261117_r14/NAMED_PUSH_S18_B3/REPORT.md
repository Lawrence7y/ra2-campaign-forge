# NAMED-PUSH — S18 B3 批次（有名字的 ③b② 候选，攻 proved 增量）

> 状态：**完成**。执行纪律已遵：先建目录、先写骨架、逐行核完即落盘 EVIDENCE；每 5 行追加 PROGRESS。
> 卡片：`lead\next_re_20261117_r14\_cards\NAMED-PUSH.md`（全文 80 行读完）。
> 本批：**B3** = `SURVEY_3B2\hits_detail.tsv` 中 `subsystem==S18` AND `p3b2_named==True` AND 名字非 `fn_`/`sub_` 地址式伪名的行按 entry 升序取**第 37 到第 54 个**（1-based，共 18 行）。
> 输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S18_B3\`（卡片中 `<你的子系统>`=S18、`<你的目录>`=本目录）。

## 材料自校验
- 目标：`ra2youli\gamemd.exe`，期望 SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`；现场 `Get-FileHash` 复算一致（2026-11-20）。
- ImageBase `0x400000`；`.text=[0x401000,0x7E038D)`（VirtualSize）。
- Python 3.12.10 / capstone 5.0.7（**skipdata=True**）/ pefile 2024.8.26；无 venv、未 pip install、未用 Ghidra。
- 只读输入：`SURVEY_3B2\hits_detail.tsv`（仅当线索）。未改 coverage.tsv / PANEL.md / R14_COMMON.md / 台账 / SURVEY_3B2 与 S04_PUSH_* 下任何产物。写域仅本目录。

## 筛选命令（得到本批 18 个 entry）

在 R14 目录下执行 PowerShell：

```powershell
$p = "SURVEY_3B2\hits_detail.tsv"
$rows = Import-Csv $p -Delimiter "`t"
$named = $rows | Where-Object {
    $_.subsystem -eq 'S18' -and $_.p3b2_named -eq 'True' -and
    $_.name -notmatch '^(fn_|sub_)[0-9A-Fa-f]{8}$'
} | Sort-Object { [Convert]::ToInt32($_.entry,16) }
$b3 = $named | Select-Object -Skip 36 -First 18   # 第 37..54 个（1-based）
$b3 | Format-Table entry,subsystem,name,grade,size -AutoSize
```

等价 Python 落盘于 `work/filter_b3.py`。结果：S18 named=True 共 **82** 行，其中 `fn_`/`sub_` 地址式伪名 **0** 个（本子系统不需实际排除，但规则已写入筛选）；B3 = 第 37..54 个（entry 升序），共 18 行。

> 衔接核对：B1=第 1..18、B2=第 19..36（旧卡无伪名规则，S18 无伪名故集合一致），B3=第 37..54，无重叠。

## 本批 18 行候选（entry 升序）

| # | entry | name(原样) | size |
|---:|---|---|---:|
| 37 | 00774CD0 | WinModemClass::slot5 | 631 |
| 38 | 00774F50 | WinModemClass::slot6 | 434 |
| 39 | 00775110 | WinModemClass::slot7 | 900 |
| 40 | 007A3100 | T_CComObject_VCNetUtilEventSink___ATL::slot4 | 2600 |
| 41 | 007A3D90 | T_CComObject_VCNetUtilEventSink___ATL::slot6 | 732 |
| 42 | 007A4070 | T_CComObject_VCNetUtilEventSink___ATL::slot7 | 121 |
| 43 | 007A41C0 | T_CComObject_VCChatEventSink___ATL::slot3 | 2633 |
| 44 | 007A4C10 | T_CComObject_VCChatEventSink___ATL::slot4 | 681 |
| 45 | 007A5290 | T_CComObject_VCChatEventSink___ATL::slot6 | 823 |
| 46 | 007A55F0 | T_CComObject_VCChatEventSink___ATL::slot7 | 145 |
| 47 | 007A5690 | T_CComObject_VCChatEventSink___ATL::slot9 | 501 |
| 48 | 007A5890 | T_CComObject_VCChatEventSink___ATL::slot10 | 4678 |
| 49 | 007A7110 | T_CComObject_VCChatEventSink___ATL::slot15 | 2497 |
| 50 | 007A7EA0 | T_CComObject_VCChatEventSink___ATL::slot22 | 960 |
| 51 | 007A8260 | T_CComObject_VCChatEventSink___ATL::slot21 | 2874 |
| 52 | 007A8DA0 | T_CComObject_VCChatEventSink___ATL::slot16 | 297 |
| 53 | 007A8ED0 | T_CComObject_VCChatEventSink___ATL::slot40 | 239 |
| 54 | 007A8FC0 | T_CComObject_VCChatEventSink___ATL::slot17 | 322 |

（18/18 行为 `Class::slotN`：② 的类名部分仅作线索，须用 RTTI/虚表独立钉死。）

## 判定口径（严格 D-40）

1. **①入口**：entry 在 `.text` 内、函数边界自洽（atlas size + 反汇编连贯，skipdata 多为 0；007A5890 skipdata=2、007A7110 skipdata=1 属跳转表数据，不影响入口判定）。本批 18/18 满足。
2. **②类身份**：RTTI 描述符链 `[vt-4]=COL→[COL+0xC]=TD→TD+8 名串` 且 `vt[slot]==entry`（逐行复核槽值==entry）；`slotN` 的 `Class` 仅作线索，须独立钉死；② 与 ④ 不同源。
3. **③整体合同**：只认 ③b。③b②（可伪证 imm 错误码/返回约定且调用方真分支；**bool 0/1 与 null 探测不算** D-46(A)）、③b①（跳转表+边界检查+每路可单独验证）、③b④（完整循环 I/O + 循环体内非栈写）；禁 ③a（清零/初始化模板假句）、多路同一 call（细则#1）、eax 覆写、被调内写冒充循环内写。
4. **④使用见证**：真实调用者或活虚表派发，direct-only 不足，且与 ② 不同源（②=.data/.rdata RTTI 数据链；④=.text 构造安装 + [reg+off] 派发链）。
5. **三陷阱**：eax 覆写、多路同一 call、模板假句——逐行排查。

## 基础率（诚实报数）

分母 = 本批 18 行。

| 档 | 行数 | 口径 |
|---|---:|---|
| 本批行数 | 18 | S18 named=True 非伪名第 37..54 |
| ①入口 PASS | 18 | 全部在 .text、反汇编连贯 |
| ②类身份取得（RTTI 独立钉死） | **18** | 18 行 slotval==entry 且 RTTI 名与线索类名一致（含 ATL 双虚表 CComObject<EventSink> + EventSink 本体） |
| ③③b 成立 | **0** | 全为 NULL/布尔探测、多路同一 call、清零模板、或跳表各路同调仅参数不同 |
| ④独立使用见证 | **18** | 18 行均有活虚表派发（dispatch_sites 79..1525）+ .text 构造安装点；direct callers 全为 0（纯虚派发） |
| **四环齐全（严格 D-40）** | **0** | ③ 为决定性瓶颈 |

## 本批 18 行总表（entry / ②③④ / 是否产出）

| # | entry | name(原样) | ① | ② | ③③b | ④ | ②④独立 | 裁定 | 产出 |
|---:|---|---|---|---|---|---|---|---|---|
| 37 | 00774CD0 | WinModemClass::slot5 | PASS | PASS(.?AVWinModemClass@@ slot5) | FAIL(strchr/CRT NULL探测；CR/LF循环体无写) | PASS | 是 | 不成立 | 否 |
| 38 | 00774F50 | WinModemClass::slot6 | PASS | PASS(slot6) | FAIL(p3=0，无站点/跳表/循环) | PASS | 是 | 不成立 | 否 |
| 39 | 00775110 | WinModemClass::slot7 | PASS | PASS(slot7) | FAIL(0x7CA4B0 返回0/未知，bool小整数探测) | PASS | 是 | 不成立 | 否 |
| 40 | 007A3100 | T_CComObject_VCNetUtilEventSink___ATL::slot4 | PASS | PASS(ATL+CNetUtilEventSink slot4) | FAIL(CRT/NULL探测+数组清零③a) | PASS | 是 | 不成立 | 否 |
| 41 | 007A3D90 | T_CComObject_VCNetUtilEventSink___ATL::slot6 | PASS | PASS(slot6) | FAIL(0x5E2CD0/0x775940 NULL探测，多路同汇) | PASS | 是 | 不成立 | 否 |
| 42 | 007A4070 | T_CComObject_VCNetUtilEventSink___ATL::slot7 | PASS | PASS(slot7) | FAIL(0x775940 NULL探测) | PASS | 是 | 不成立 | 否 |
| 43 | 007A41C0 | T_CComObject_VCChatEventSink___ATL::slot3 | PASS | PASS(ATL+CChatEventSink slot3) | FAIL(10×0x7C9CC2 NULL探测多路同call；0x84583c哨兵与TEST不同源) | PASS | 是 | 不成立 | 否 |
| 44 | 007A4C10 | T_CComObject_VCChatEventSink___ATL::slot4 | PASS | PASS(slot4) | FAIL(NULL探测+CMP_IMM 7枚举判断) | PASS | 是 | 不成立 | 否 |
| 45 | 007A5290 | T_CComObject_VCChatEventSink___ATL::slot6 | PASS | PASS(slot6) | FAIL(跳表各路同调0x734E60仅参数不同=细则#1；写在被调内；恒返回0) | PASS | 是 | 不成立 | 否 |
| 46 | 007A55F0 | T_CComObject_VCChatEventSink___ATL::slot7 | PASS | PASS(slot7) | FAIL(0x7C9CC2 NULL探测) | PASS | 是 | 不成立 | 否 |
| 47 | 007A5690 | T_CComObject_VCChatEventSink___ATL::slot9 | PASS | PASS(slot9) | FAIL(0x775940/0x4068E0 NULL探测) | PASS | 是 | 不成立 | 否 |
| 48 | 007A5890 | T_CComObject_VCChatEventSink___ATL::slot10 | PASS | PASS(slot10) | FAIL(CRT NULL探测；0x889f64哨兵与TEST不同源；数组清零③a) | PASS | 是 | 不成立 | 否 |
| 49 | 007A7110 | T_CComObject_VCChatEventSink___ATL::slot15 | PASS | PASS(slot15) | FAIL(间接call+CRT NULL探测；0x889f64不同源) | PASS | 是 | 不成立 | 否 |
| 50 | 007A7EA0 | T_CComObject_VCChatEventSink___ATL::slot22 | PASS | PASS(slot22) | FAIL(0x7C8D20 NULL探测) | PASS | 是 | 不成立 | 否 |
| 51 | 007A8260 | T_CComObject_VCChatEventSink___ATL::slot21 | PASS | PASS(slot21) | FAIL(0x889f64哨兵与TEST不同源；0x7C9CC2 NULL探测，多路同汇) | PASS | 是 | 不成立 | 否 |
| 52 | 007A8DA0 | T_CComObject_VCChatEventSink___ATL::slot16 | PASS | PASS(slot16) | FAIL(3×0x775940/0x7C8D20 NULL探测) | PASS | 是 | 不成立 | 否 |
| 53 | 007A8ED0 | T_CComObject_VCChatEventSink___ATL::slot40 | PASS | PASS(slot40) | FAIL(0x775940 NULL探测，多路同汇) | PASS | 是 | 不成立 | 否 |
| 54 | 007A8FC0 | T_CComObject_VCChatEventSink___ATL::slot17 | PASS | PASS(slot17) | FAIL(0x775940 NULL探测，多路同汇) | PASS | 是 | 不成立 | 否 |

## 逐行裁定依据

每行自身地址锚与字节见 `EVIDENCE/ROW_<entry>.txt` × 18。③ 全部 FAIL，分类如下（逐行理由各自独立，已写入各行 EVIDENCE）：

- **NULL/布尔探测，无可伪证错误码（D-46(A)：bool 0/1 与 null 探测不算）**：占绝大多数。被调为 0x00775940、0x007C9CC2、0x007C8D20(CRT)、0x007CAF30/0x007CA4B0(strchr 类)、0x004068E0(空 thunk)、0x005E2CD0、0x007C8DF0 等，origins 多为 [unknown]/[imm0]/[call]，返回 0 或未知值；调用方 TEST_EAX→je/jne 或 CMP_IMM 1/7，均非域内可伪证 imm 错误码，无 signed HRESULT 分支（涉及行：00774CD0、00774F50、00775110、007A3D90、007A4070、007A41C0、007A4C10、007A55F0、007A5690、007A7EA0、007A8DA0、007A8ED0、007A8FC0）。
- **哨兵与 TEST 不同源（eax 覆写陷阱变体）**：0x889f64（0x007B5440/0x007B5400 GetAt 内部指针为 NULL 时的回退值）与 0x84583c（0x00734E60 GetErrorString 的回退值）看似错误码，但调用方 TEST_EAX 之前隔了一个 call（0x007C8D20/0x00775940/0x00775740），被测试的是后一个 CRT 调用返回值而非哨兵本身——哨兵未经调用方错误码分支消费（涉及行：007A41C0 site12、007A5890 site5、007A7110 site1、007A8260 site0）。
- **多路同一 call（细则#1）**：007A41C0 的 10 个站点全调 0x007C9CC2 仅参数不同；007A3D90/007A8ED0/007A8FC0/007A8260 相邻站点同汇一处 je。
- **③b① 跳表唯一候选 007A5290 不成立**：`cmp eax,0x10/ja@0x007A52C0` + `mov cl,[eax+0x7A55DC]` + `jmp [ecx*4+0x7A55C8]@0x007A52CE`，输入为 HRESULT(0x80040075..0x80040078)，按错误码选错误消息——语义是真的，但各路压不同消息号/ecx 后全部汇入同一批 call 0x00734E60/0x007CA489/[0x007E1234]（仅参数不同 ⇒ 细则#1 不计），真正的写发生在被调 0x00734E60 内（禁把被调内写当本函数写），本函数体无写指令，且自身恒 `xor eax,eax;ret 0xC`（无可伪证返回约定）。与 B2 通过的 005C46E0（各路在函数体内写不同配置常量到不同全局）决定性不同。
- **③b④ 循环不成立**：带非栈写的循环均为数组清零（`mov [edx+eax*4],0` @007A3100；`mov [esi],0` @007A5890），属 ③a 模板假句（明确禁作 ③b④）；00774CD0 的 0x00774EB7..0x00774EC2 剥 CR/LF 紧循环体内只有 inc esi 无写，0x00774E3B 的写置于循环外。
- **②/④ 全部钉住但不足以单独升级**：②④ 独立成立 18/18，但 ③ 全部 FAIL，按严格 D-40 四环齐全 0 行。

## 与 S04 的败因对比（本批有多少行 ② 真的钉住）

- S04 的 73 个命中 `p3b2_named=0`（全无名字）：entry 作为 4B VA 全镜像 0 命中、无虚表槽、无可安装 RTTI 链 ⇒ ② 物理不可得，36 行实测全败（四环 0）。
- 本批 S18 named=True 非伪名：**18/18 行的 ② 被 RTTI 描述符链独立钉死**（逐行复核槽值==entry；WinModemClass 3 行 RTTI 精确匹配 `WinModemClass`；ATL EventSink 15 行双虚表——`CComObject<VCNetUtilEventSink>/<VCChatEventSink>@@ATL` 包装类 + `CNetUtilEventSink/CChatEventSink` 本体，slot offset/4 == 线索槽号）。② 从 S04 的 0/36 变为本批 18/18，S04 败因不复现。
- ④ 亦 18/18 成立（活虚表派发 + .text 构造安装），与 ② 不同源。
- 结论：② 与 ④ 在本批均满分，proved 增量仍完全受 ③ 限制——本批 ③b 成立 0 行，四环齐全 0 行。与 B1（③b 1/18）、B2（③b 2/18）一致：本批全部为 ATL 事件接收器/调制解调器事件处理函数，其 contract 均为「NULL 探测 + 消息分派」模板，不具备可伪证 imm 错误码返回约定或体内非栈写的多路合同。

## 汇总
- rows_checked：**18**
- ② 钉住行数：**18**
- ③b 成立行数：**0**
- ④ 成立行数：**18**
- all_four_rings（严格 D-40）：**0**
- delta 产出：**0 行**
- 结论：② 18/18、④ 18/18 均钉住（S04 败因不复现），③ 为决定性瓶颈 0/18；按「宁严不宽、虚报不可接受」如实交 0 行。

## 输出清单
- `REPORT.md`（本文件）、`PROGRESS.md`、`base_rate.tsv`、`delta.tsv`（0 行，仅表头）
- `EVIDENCE/ROW_<entry>.txt` × 18（每行自身地址与字节）
- `work/`（取证脚本 filter_b3/analyze/recore/witness_core/deep_b3/final_b3/verify_b3/compact3/ch3_summary/gen_evidence_b3 与中间 JSON/TXT，全部只读目标、可复算）
