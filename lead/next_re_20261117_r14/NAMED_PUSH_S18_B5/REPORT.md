# NAMED-PUSH — S18 B5 REPORT（最终交付，状态：完成）

批次：S18 B5。范围：S18 中 `p3b2_named==True` 且名字非 `fn_`/`sub_` 伪名、且未被 NAMED_PUSH_S18_B1/B2/B3/B4 核过的剩余候选，按 entry 升序取全部（收尾批，10 行）。
输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S18_B5`

> 残留处置：上一轮中断留下的骨架 REPORT（含未完成占位）已被本文件**整体重写**；delta.tsv / base_rate.tsv / PROGRESS.md / EVIDENCE/ 均为本次基于实际逐行复核重新落盘，最终交付为完整成品、不含任何未完成占位。

## 材料自校验

- 目标 `ra2youli\gamemd.exe`，现场 `Get-FileHash` 复算 SHA-256=`73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`，与卡片期望一致。
- ImageBase=0x400000；`.text=[0x401000,0x7E038D)`（VirtualSize 口径）。
- Python 3.12.10 / capstone 5.0.7（**skipdata=True**）/ pefile 2024.8.26；无 venv、未 pip install。
- 只读输入：`SURVEY_3B2\hits_detail.tsv` 仅作线索；未改 `coverage.tsv`/`PANEL.md`/`R14_COMMON.md`/台账/`SURVEY_3B2`/`S04_PUSH_*`；写域仅本批次目录。

## 判据（D-40，严格）

1. **① 入口**：entry 在 `.text` 内、函数边界自洽。
2. **② 类身份**：独立取证——RTTI 描述符链 `[vt-4]=COL → [COL]=sig(0) → [COL+0xC]=TD → TD+8 内联装饰名串`，且 `vt[slot]==entry`。`Class::slotN` 的 `Class` 仅线索，须由 RTTI/虚表钉死；钉不死判 FAIL。
3. **③ 整体合同**：只认 ③b。③b② 可伪证错误码/返回约定（失败返什么、成功返什么、调用方真拿它分支）；{0,1} 布尔不算可伪证（卡明确）；多值状态码 / Find 返 -1 下标约定算。
4. **④ 使用见证**：真实调用者或活虚表派发，direct-only 不足，且与 ② 不同源。㉓：④ 锚点落析构器判 FAIL，须枚举该虚表全部写点并排除 atexit 注册的全局析构器与删除析构器两类。

技术条：RTTI pTD/pCHD 存绝对 VA 非 RVA；装饰名在 TD+8 是内联串非指针。
三陷阱：eax 覆写（test/cmp 后、分支前 eax 被改写使返回值未被消费）、多路同一 call、模板假句。
小成员表陷阱：小成员表 vtable 不是主虚表（主表 slot0 常见 00410260；本批主表 slot0=007B1790/007B2780/007B4170，均不在小成员表签名集合 `{00410260,004105E0,00410580,00410590}`，是带 RTTI 的主虚表）。

## 筛选命令

完整可复现脚本 `work/filter_b5.py`，等价逻辑：

```python
# 读 SURVEY_3B2/hits_detail.tsv，逐行：
#   subsystem == "S18" and p3b2_named == "True"
#   and not name.startswith(("fn_", "sub_"))        # 排除地址式伪名
# checked = 所有 NAMED_PUSH_S18_B{1,2,3,4}/EVIDENCE/ROW_*.txt 的 entry（共 72）
# rows = [r for r in rows if r["entry"] not in checked]
# rows.sort(key=lambda x: int(x["entry"],16))        # 按 entry 升序取全部剩余
# ⇒ 10 行候选（B5 收尾批）
```

实测（`work/b5_filter.txt`）：`all=82 checked=72 remaining=10 selected=10`。10 行全部为 `IPXInterfaceClass::slotN` / `UDPInterfaceClass::slotN`，无 `fn_`/`sub_` 伪名：

| # | entry | name |
|---:|---|---|
| 1 | 007B13D0 | IPXInterfaceClass::slot16 |
| 2 | 007B1BC0 | IPXInterfaceClass::slot7 |
| 3 | 007B2630 | IPXInterfaceClass::slot10 |
| 4 | 007B26D0 | IPXInterfaceClass::slot17 |
| 5 | 007B30B0 | UDPInterfaceClass::slot23 |
| 6 | 007B31E0 | UDPInterfaceClass::slot26 |
| 7 | 007B3450 | UDPInterfaceClass::slot15 |
| 8 | 007B36C0 | UDPInterfaceClass::slot3 |
| 9 | 007B3890 | UDPInterfaceClass::slot7 |
| 10 | 007B3AA0 | UDPInterfaceClass::slot16 |

## 本批 10 行逐行总表

| 序 | entry | name | ① | ② | ③③b | ④ | 四环齐全 | 产出 |
|---:|---|---|---|---|---|---|---|---|
| 1 | 007B13D0 | IPXInterfaceClass::slot16 | PASS | PASS | PASS(③b② sendto/recvfrom -1) | PASS | 是 | delta 1 行 |
| 2 | 007B1BC0 | IPXInterfaceClass::slot7 | PASS | PASS | PASS(③b② WSAAsyncSelect -1) | PASS | 是 | delta 1 行 |
| 3 | 007B2630 | IPXInterfaceClass::slot10 | PASS | PASS | PASS(③b② setsockopt -1) | PASS | 是 | delta 1 行 |
| 4 | 007B26D0 | IPXInterfaceClass::slot17 | PASS | PASS | PASS(③b② gethostname -1) | PASS | 是 | delta 1 行 |
| 5 | 007B30B0 | UDPInterfaceClass::slot23 | PASS | PASS | PASS(③b② socket/bind -1) | PASS | 是 | delta 1 行 |
| 6 | 007B31E0 | UDPInterfaceClass::slot26 | PASS | PASS | PASS(③b② bind -1) | PASS | 是 | delta 1 行 |
| 7 | 007B3450 | UDPInterfaceClass::slot15 | PASS | PASS | PASS(③b② socket/bind -1) | PASS | 是 | delta 1 行 |
| 8 | 007B36C0 | UDPInterfaceClass::slot3 | PASS | PASS | FAIL({0,1} 布尔) | PASS | 否 | 无 |
| 9 | 007B3890 | UDPInterfaceClass::slot7 | PASS | PASS | PASS(③b② WSAAsyncSelect -1) | PASS | 是 | delta 1 行 |
| 10 | 007B3AA0 | UDPInterfaceClass::slot16 | PASS | PASS | PASS(③b② sendto -1) | PASS | 是 | delta 1 行 |

逐行地址、字节、RTTI 链、写点枚举与陷阱排查见 `EVIDENCE/ROW_<entry>.txt`（10 份，每份含本行自身锚点，无整批共用 reason）。

## 关键裁定依据（汇总）

### ② 类身份 10/10 全数钉住
每行 entry 作为 4B VA 在 `.rdata` 命中虚表槽，`[vt-4]=COL(sig=0)→[COL+0xC]=TD→TD+8` 得 RTTI 名串，与名字类名字逐字一致；且 `slot_offset/4 == 名字槽号`：
- IPX 主虚表 `007F794C`（COL=0080EA60→TD=0084D8F8→`.?AVIPXInterfaceClass@@`）：slot16→+0x40、slot7→+0x1C、slot10→+0x28、slot17→+0x44。
- UDP 主虚表 `007F7A6C`（COL=0080EBE0→TD=0084E1C0→`.?AVUDPInterfaceClass@@`）：slot23→+0x5C、slot26→+0x68、slot15→+0x3C、slot3→+0x0C、slot7→+0x1C、slot16→+0x40。
- 继承层次旁证：部分 IPX entry 同时出现在 WinsockInterfaceClass(007F79BC)/UDPInterfaceClass(007F7A6C) 同号槽（如 007B2630/007B26D0），但 ② 主锚取与名字类名字一致的虚表。

### ③b 9/10：Winsock SOCKET_ERROR/INVALID_SOCKET=-1 可伪证约定
Winsock thunk 经 IAT 解析（`work/iat_b5.txt`）：0x7C899E=socket、0x7C8998=bind、0x7C89A4=setsockopt、0x7C89B0=sendto、0x7C89AA=recvfrom、0x7C89BC=WSAAsyncSelect、0x7C89CE=gethostname、0x7C897A=WSAGetLastError。
9 行均为 `call → cmp eax,-1 → jcc → 两路动作真不同`：失败路取 WSAGetLastError+日志串+xor al,al/继续重试，成功路继续建链/组包/入列；失败返 -1、成功返字节数/0/句柄，**调用方真拿 -1 分支**。属「Find 返 -1 / 多值状态码」可伪证类，与 B1 005414C0、B4 007B10C0 同构。

**唯一 FAIL = 007B36C0（UDPInterfaceClass::slot3）**：唯一站点 `call 0x0053EE00@0x007B36CE → test eax,eax@0x007B36D3 → je@0x007B36D5`。被调 `0053EE00` 返回常量集恰为 `{0,1}`（类型/状态布尔探测），卡明定「{0,1} 布尔不算可伪证」；通道B(③b①) 站点=0，无 ③b③/③b④，属 ③a 布尔探测+派发，故 ③ 不成立。

三陷阱核查：
- eax 覆写陷阱：10 行 chA_eax_trap 全部 `eax_overwritten=[]`；cmp 与 jcc 之间的间隙仅为 `mov [mem],eax`（只写内存不改 eax/标志）或 `pop`（不写 eax），返回值确被 jcc 消费。
- 多路同一 call：无（各行站点为不同 call 地址）。
- 模板假句：007B3450 的 `call 0x4068E0`(WWDebug_Printf 空 stub, ret 即返, eax 未定义)→test→je 属布尔不计，已明确排除；该行另由 socket/bind 两站点独立满足 ③b②。

### ④ 使用见证 10/10，㉓ 析构器锚点排除
②④ 不同源：② 走 `.rdata` RTTI 数据链；④ 走 `.text` 构造器安装活虚表 + `call [reg+disp]` 派发链。

**㉓ 枚举每个虚表全部写点并分类**（`work/verify_independent.py` + `work/classify_funcs.py`）：
- IPX `007F794C`：1 处写点 `007B0DA4 ∈ 007B0D90`，类别=**构造器**（call 基类构造 007B19C0、ret、返回 this；direct callers=5，活），atexit=False。
- Winsock `007F79BC`：3 处写点——`007B1A20 ∈ 007B19C0`=**构造器**（direct=2，活）；`007B1ABC ∈ 007B1AB0`=非删除析构（调 WSACleanup + 删除器链）；`007B278C ∈ 007B2780`=**标量删除析构**（vt slot0、`ret 4`）。
- UDP `007F7A6C`：3 处写点——`007B2E2D ∈ 007B2DB0`=**构造器**（direct=1，活）；`007B2E56 ∈ 007B2E50`=非删除析构；`007B4176 ∈ 007B4170`=**标量删除析构**（vt slot0、`ret 4`）。

删除析构器（slot0 `ret 4`）与非删除析构两类均已枚举并排除；atexit 注册的全局析构器 = 0；④ 锚点只取**被实际调用的构造器**写点，不落析构器，㉓ 通过。构造器活性实测：007B0D90 direct=5、007B19C0 direct=2、007B2DB0 direct=1。007B1BC0 另有 direct caller 007B3895，007B2630 另有 4 个 direct caller（007B13AB/007B31BC/007B32EA/007B36A1），均非 direct-only 判据来源。

## 与 S04 的败因对比（本批有多少行 ② 真的钉住了）

- S04 的 73 个命中 `p3b2_named=0`（全无名字）：entry 作为 4B VA 全镜像 0 命中、无虚表槽、无可安装 RTTI 链 ⇒ **② 物理不可得**，36 行实测全败。
- 本批 10 行来自 `p3b2_named==True` 且有真名（`IPXInterfaceClass/UDPInterfaceClass::slotN`），**② 10/10 全部由 RTTI 描述符链独立钉死**（虚表槽驻留本 entry + RTTI 名串逐字一致 + slot_offset/4 == 名字槽号 + 主虚表非小成员表）。S04 的败因在本批复现率为 0。
- 但 proved 增量的决定性瓶颈是 ③：10 行中 9 行有可伪证 -1 哨兵、1 行（007B36C0）是 {0,1} 布尔不成立。④ 10/10 成立但不足以单独升级。

## 计数（base_rate.tsv 为准）

| batch | rows_checked | ring2_ok | ring3b_ok | ring4_ok | all_four | rate |
|---|---:|---:|---:|---:|---:|---:|
| NAMED_PUSH_S18_B5 | 10 | 10 | 9 | 10 | 9 | 0.9000 |

- delta 产出 9 行（007B13D0/007B1BC0/007B2630/007B26D0/007B30B0/007B31E0/007B3450/007B3890/007B3AA0），grade 均 `[已证]`，evidence_path 指向各自 `EVIDENCE/ROW_<entry>.txt`。
- 007B36C0 因 ③b 为 {0,1} 布尔不成立，四环不齐，不入 delta。
- 如实交 9 行；不凑数、不虚报。

## 输出清单

- `REPORT.md`（本文件，整体重写）、`PROGRESS.md`、`delta.tsv`、`base_rate.tsv`
- `EVIDENCE/ROW_<entry>.txt` × 10（逐行自身地址与字节）
- `work/`：筛选/分析/复核/生成脚本与中间 JSON、日志（filter_b5.py / analyze_b5.py / recore.py / witness_core.py / verify_b5.py / verify_independent.py / classify_funcs.py / finalize_final.py 等），全部只读目标、可复算。
