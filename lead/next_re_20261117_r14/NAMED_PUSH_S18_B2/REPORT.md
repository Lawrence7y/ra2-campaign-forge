# NAMED-PUSH — S18 B2 批次（有名字的 ③b② 候选，攻 proved 增量）

> 状态：**完成**。执行纪律已遵：先建目录、先写骨架、逐行核完即落盘 EVIDENCE；每 5 行追加 PROGRESS。
> 卡片：`lead\next_re_20261117_r14\_cards\NAMED-PUSH.md`（全文 73 行读完）
> 本批：**B2** = `SURVEY_3B2\hits_detail.tsv` 中 `subsystem==S18` AND `p3b2_named==True` 的行按 entry 升序取**第 19 到第 36 个**（1-based，共 18 行）。
> 输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S18_B2\`（卡片中 `<你的子系统>`=S18、`<你的目录>`=本目录）。

## 材料自校验
- 目标：`ra2youli\gamemd.exe`，期望 SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`；现场 `Get-FileHash` 复算一致（2026-11-20）。
- ImageBase `0x400000`；`.text=[0x401000,0x7E038D)`（VirtualSize）。
- Python 3.12.10 / capstone 5.0.7（**skipdata=True**）/ pefile 2024.8.26；无 venv、未 pip install、未用 Ghidra。
- 只读输入：`SURVEY_3B2\hits_detail.tsv`（仅当线索）。未改 coverage.tsv / PANEL.md / R14_COMMON.md / 台账 / SURVEY_3B2 下任何产物。写域仅本目录。

## 筛选命令（得到本批 18 个 entry）

PowerShell（在 R14 目录下执行）：

```powershell
$p = "SURVEY_3B2\hits_detail.tsv"
$rows = Import-Csv $p -Delimiter "`t"
$b2 = $rows | Where-Object { $_.subsystem -eq 'S18' -and $_.p3b2_named -eq 'True' } |
      Sort-Object { [Convert]::ToInt32($_.entry,16) } |
      Select-Object -Skip 18 -First 18        # 第 19..36 个（1-based）
$b2 | Format-Table entry,subsystem,name,grade,size,n_call,n_site,n_valid,p3b2_named -AutoSize
```

结果：S18 named=True 共 **82** 行；B2 = 第 19..36 个（entry 升序），共 18 行。等价 Python 落盘于 `work/filter_b2.py`（`sorted([...], key=lambda x:int(x['entry'],16))[18:36]`）。

## 判定口径（严格 D-40，宁严不宽；参考同子系统 B1：②18/18、④18/18、③b 仅 1/18）
1. **①入口**：entry 在 `.text` 内、函数边界自洽（atlas size + 反汇编连贯，skipdata=0）。本批 18/18 满足。
2. **②类身份**：RTTI 描述符链 `[vt-4]=COL→[COL+0xC]=TD→TD+8 名串` 且 `vt[slot]==entry`；`Class::slotN` 的 `Class` 仅作线索；真名/ctor 同样须 RTTI+虚表槽独立钉死。**重要修正**：B1 复用的 `witness_core.resolve_slot` 回扫上限 k≤40，会漏掉 slot 号 >40 的槽；本批 slot41/43/44/50 四行在 `work/resolve_wide.py` 扩到 k≤128 后 RTTI 全部钉住（并已同步修正 B2 副本 `witness_core.py` 上限、重跑 `analyze.py`）。
3. **③整体合同**：只认 ③b。逐行核 ③b②（可伪证 imm 错误码/返回约定，**bool 0/1 与 null 探测不算** D-46(A)）、③b①（跳转表+边界检查+每路可单独验证）、③b④（完整循环 I/O + 循环体内非栈写）。禁 ③a、模板假句（malloc+对象初始化）、多路同一 call、eax 覆写。
4. **④使用见证**：真实调用者或活虚表派发，direct-only 不足，且与 ② 不同源（②=RTTI 数据链，④=.text 构造安装/派发链）。
5. **三陷阱**：eax 覆写、多路同一 call、模板假句——逐行排查。

## 基础率（诚实报数）

分母 = 本批 18 行。

| 档 | 行数 | 口径 |
|---|---:|---|
| 本批行数 | 18 | S18 named=True 第 19..36 |
| ①入口 PASS | 18 | 全部在 .text、反汇编连贯（skipdata=0） |
| ②类身份取得（RTTI 独立钉死） | **15** | 含 slot>40 四行扩回扫后钉住；3 个真名普通函数无虚表槽，② 取不到 |
| ③③b 成立 | **2** | 005C46E0（③b① 双跳转表）、0071F8C0（③b② E_POINTER 错误码） |
| ④独立使用见证 | **15** | 有 RTTI 虚表槽者均有 .text 构造安装 + [reg+off] 派发；3 个真名函数仅 direct-only |
| **四环齐全（严格 D-40）** | **2** | 005C46E0、0071F8C0 |

## 本批 18 行总表（entry / ②③④ / 是否产出）

| # | entry | name(原样) | ① | ② | ③③b | ④ | ②④独立 | 裁定 | 产出 |
|---:|---|---|---|---|---|---|---|---|---|
| 19 | 005C2A60 | MPCooperative::slot29 | PASS | PASS(.?AVMPCooperative@@ slot29) | FAIL(被调0x7C9CC2/0x7C9B72 origins=unknown；bool/imm=1探测) | PASS | 是 | 不成立 | 否 |
| 20 | 005C2CB0 | MPCooperative::slot31 | PASS | PASS(slot31) | FAIL(0x775940 返回0/unknown，null探测) | PASS | 是 | 不成立 | 否 |
| 21 | 005C3710 | MPCooperative::slot40 | PASS | PASS(slot40) | FAIL(0x7CA610 origins=unknown) | PASS | 是 | 不成立 | 否 |
| 22 | 005C3B10 | MPCooperative::slot19 | PASS | PASS(slot19) | FAIL(0x7C8E17=malloc 模板假句) | PASS | 是 | 不成立 | 否 |
| 23 | 005C3F80 | MPCooperative::slot36 | PASS | PASS(slot36) | FAIL(0x7C8D20 CRT unknown；两路call重合) | PASS | 是 | 不成立 | 否 |
| 24 | 005C4110 | MPCooperative::slot37 | PASS | PASS(slot37) | FAIL(0x7C8E17=malloc 模板假句) | PASS | 是 | 不成立 | 否 |
| 25 | 005C44E0 | MPCooperative::slot41 | PASS | PASS(slot41 扩k钉住) | FAIL(malloc/间接 origins=[call]；多路同一call) | PASS | 是 | 不成立 | 否 |
| 26 | 005C46E0 | MPCooperative::slot43 | PASS | PASS(slot43 扩k钉住) | **PASS(③b① 双跳转表)** | PASS | 是 | **成立** | **是** |
| 27 | 005C4CA0 | MPCooperative::slot44 | PASS | PASS(slot44 扩k钉住) | FAIL(0x7DD0F8 origins=[call]) | PASS | 是 | 不成立 | 否 |
| 28 | 005CAAC0 | MultiplayerSiege::slot50 | PASS | PASS(.?AVMultiplayerSiege@@ slot50 扩k) | FAIL(0x7C8E17=malloc 模板假句) | PASS | 是 | 不成立 | 否 |
| 29 | 005D8170 | T_Initializer_VMultiplayerBattle___MultiplayerGameMode::slot1 | PASS | PASS(Initializer slot1) | FAIL(0x7C8E17=malloc 模板假句) | PASS | 是 | 不成立 | 否 |
| 30 | 0064A0C0 | Receive_Packet | PASS | **FAIL**(真名普通函数，无虚表槽) | FAIL(间接call cmp-1不可独立伪证；0x540FC0 null探测) | FAIL(direct-only) | n/a | 不成立 | 否 |
| 31 | 0064DEA0 | SyncReport | PASS | **FAIL**(真名普通函数) | FAIL(间接call 无返回profile/哨兵) | FAIL(direct-only) | n/a | 不成立 | 否 |
| 32 | 006516F0 | SyncDump | PASS | **FAIL**(真名普通函数) | FAIL(间接call 无返回profile/哨兵) | FAIL(direct-only) | n/a | 不成立 | 否 |
| 33 | 0071F8C0 | TEventClass::ctor | PASS | PASS(.?AVTEventClass@@ slot5) | **PASS(③b② E_POINTER 0x80004003)** | PASS | 是 | **成立** | **是** |
| 34 | 00773BC0 | WebBrowser::slot14 | PASS | PASS(slot14) | FAIL(p3=0 无站点) | PASS | 是 | 不成立 | 否 |
| 35 | 00774410 | WinModemClass::slot1 | PASS | PASS(slot1) | FAIL(间接call 无哨兵) | PASS | 是 | 不成立 | 否 |
| 36 | 00774900 | WinModemClass::slot4 | PASS | PASS(slot4) | FAIL(p3=0 无站点) | PASS | 是 | 不成立 | 否 |

## 逐行裁定依据（每行自身地址锚，详见 `EVIDENCE/ROW_<entry>.txt`）

- **② 钉住 15/18**：14 行为 `Class::slotN`（slot offset/4 == 线索槽号，RTTI 名与类名逐字一致；其中 slot41/43/44/50 四行 slot 号 >40 被 B1 旧脚本 k≤40 上限漏掉，扩到 k≤128 后 COL/TD/名串全部命中，如 005CAAC0: vt=007EE6FC, off=200→slot50, COL=00806498→TD=0082FEC8→`.?AVMultiplayerSiege@@`）；1 行为 `TEventClass::ctor`（RTTI `.?AVTEventClass@@` + 虚表槽 slot5 值=entry 独立钉死类身份）。另 3 个真名普通函数（Receive_Packet/SyncReport/SyncDump）`find_dword_refs=[]`，entry 非任何虚表槽值、无 RTTI，② 物理取不到。
- **③ 唯一两行成立**（重点核 ③b，宁严不宽）：
  - **0071F8C0（③b②）**：`call 0x00410380@0x0071F8CB(e8 b0 0a cf ff)` → 零间隔 `test eax,eax@0x0071F8D0(85 c0)` → `jl@0x0071F8D2(7c 57)->0x0071F92B`。被调 `0x00410389 mov eax,0x80004003(b8 03 40 00 80); ret 8@0x0041038F`——失败返回 E_POINTER（HRESULT 负值错误码，**非 bool 0/1**），jl 有符号<0 真拿它分支；T 路 `pop esi;ret 8` 直接返回错误，F 路 `0x0071F8D4` 起继续构造并在 `0x0071F8E4/EA/F1/F8` 安装 TEventClass vtable——两路动作真不同，0 处 eax 覆写，非 getter/malloc 模板/多路同一 call。
  - **005C46E0（③b①）**：两个标准间接跳转表，均有边界检查且每路可单独验证——跳表1 `jmp [eax*4+0x5C4C6C]@0x005C49B0`（`cmp eax,5;ja@0x005C49AA`，6 路各写不同配置常量 `[a8b550]/[a8b570]/[a8b554]`，写指令全在函数体内 0x005C49B7..0x005C4A3B）；跳表2 `jmp [eax*4+0x5C4C84]@0x005C4B3A`（`cmp eax,3;ja`，4 路各算不同 ecx 后 `mul 0xcccccccd` 写 `[a8b56c]`）。写目标为全局内存（非栈）、写指令在函数体内而非被调用者内部，非 ③a 直线。
- **③ 其余 16 行 FAIL 分类**（逐行理由各自独立，见自身 EVIDENCE）：
  - bool/null 探测无错误码：005C2CB0、005C2A60、005C3F80、005C4CA0、00774410。
  - 被调 origins=[unknown]/单 ret 无 imm 哨兵：005C3710。
  - malloc 空判断 + 对象初始化模板假句（同 B1 005C18A0/005C1DC0）：005C3B10、005C4110、005CAAC0、005D8170、005C44E0(部分)。
  - 多路同一 call（细则#1）：005C44E0 site1（两路同含 call 0x7C7C2D）。
  - p3=0 无 ③b 站点：00773BC0、00774900。
  - 真名普通函数 ② 取不到 + 间接 call 不可独立伪证：0064A0C0、0064DEA0、006516F0。注：0064A0C0 的 `cmp eax,-1` 形态虽似 B1 的 005414C0，但被调是间接虚调用（callee=None），无法解析到返回 imm -1 的被调体，不能独立伪证失败返回，故不判 ③b 成立。
- **④ 15 行成立但多不足以单独升级**：15 行有 RTTI 虚表槽者均有非 atexit 构造安装点（如 0071F8C0 的 0071F8E4、005C46E0 的 005C164A）+ `[reg+off]` 派发链；3 个真名函数仅 2 个 direct caller，direct-only 不足判 FAIL。②④ 来源不同（②=.data RTTI 链；④=.text 构造安装/派发链）。

## 与 S04 的败因对比（本批有多少行 ② 真的钉住）

- S04 的 73 个命中 `p3b2_named=0`（全无名字）：entry 作为 4B VA 全镜像 0 命中、无虚表槽、无可安装 RTTI 链 ⇒ ② 物理不可得，36 行实测全败（B1/B2 共 36 行四环 0）。
- 本批 S18 named=True：**15/18 行的 ② 被 RTTI 描述符链独立钉死**（含 4 行 slot>40 经扩回扫后钉住），仅 3 个真名普通函数无虚表槽取不到。这是与 S04 的决定性差异。
- 结论：② 从 S04 的 0/18 变为本批 15/18；proved 增量最终仍受 ③ 限制——本批 ③b 成立 2 行（1 行 ③b② + 1 行 ③b①），四环齐全 2 行。本批 ② 真钉住 15 行。

## 汇总
- rows_checked：**18**
- ② 钉住行数：**15**
- ③b 成立行数：**2**（0071F8C0=③b②、005C46E0=③b①）
- ④ 成立行数：**15**
- all_four_rings（严格 D-40）：**2**
- delta 产出：**2 行**（005C46E0、0071F8C0）
- 结论：本批 ② 15/18 钉住（S04 败因不复现），③ 为决定性瓶颈；按「宁严不宽、虚报不可接受」如实交 2 行。

## 输出清单
- `REPORT.md`（本文件）、`PROGRESS.md`、`base_rate.tsv`、`delta.tsv`
- `EVIDENCE/ROW_<entry>.txt` × 18（每行自身地址与字节）
- `work/`（取证脚本 filter_b2/analyze/recore/witness_core/resolve_wide/compact3/ch3_deep/deep/verify_b2/dump_jmptbl/check_vt/ch3_summary/gen_evidence_b2 与中间 JSON/TXT，全部只读目标、可复算）
