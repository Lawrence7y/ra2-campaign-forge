# NAMED-PUSH — S14 B1 批次（有名字的 ③b② 候选，攻 proved 增量）

> 状态：**完成**。执行纪律已遵：先建目录 → 先写 REPORT 骨架 → 逐行核完即落 `EVIDENCE/`；每 5 行追加 `PROGRESS.md`。
> 卡片：`lead\next_re_20261117_r14\_cards\NAMED-PUSH.md`（全文 73 行读完）
> 本批：**B1** = `SURVEY_3B2\hits_detail.tsv` 中 `subsystem==S14` AND `p3b2_named==True`，按 entry 升序取**前 18 行**。
> 输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S14_B1\`（卡片 `<你的子系统>`=S14、`<你的目录>`=本目录）。

## 材料自校验
- 目标：`ra2youli\gamemd.exe`；现场 `Get-FileHash -Algorithm SHA256` = `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` ⇒ **与卡片期望逐字一致**。
- ImageBase `0x400000`；`.text=[0x401000,0x7E038D)`（VirtualSize=0x3DF38D）。
- Python 3.12.10 / capstone 5.0.7（**skipdata=True**）/ pefile 2024.8.26；无 venv、未 pip install、未用 Ghidra。
- 只读输入：`SURVEY_3B2\hits_detail.tsv`（仅当线索）、`W130_atlas\function_atlas.tsv`（仅取函数边界）。未改 `coverage.tsv` / `PANEL.md` / `R14_COMMON.md` / 台账 / `SURVEY_3B2` / `S04_PUSH_*`。写域仅本目录。

## 筛选命令（得到本批 18 个 entry）

```powershell
$p = "D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv"
$rows = Import-Csv $p -Delimiter "`t"
$b1 = $rows | Where-Object { $_.subsystem -eq 'S14' -and $_.p3b2_named -eq 'True' } |
      Sort-Object { [Convert]::ToInt32($_.entry,16) } | Select-Object -First 18
$b1 | Format-Table entry,subsystem,name,grade,size,n_call,n_site,n_valid,p3b2_named -AutoSize
```

结果：S14 `p3b2_named=True` 共 **51** 行（卡片记 51，一致）；B1 = entry 升序前 18 行。等价 Python 落盘于 `_work/filter_b1.py`（`sorted(sel, key=int(entry,16))[:18]`）。

## 判定口径（严格 D-40 / D-43，宁严不宽）
1. **①入口**：entry 在 `.text` 内、atlas 边界自洽、反汇编 `skipdata=0`。
2. **②类身份**：`.rdata` 中 entry 作 4B VA 命中的槽 → 回扫 `[vt-4]=COL(sig=0)` → `[COL+0xC]=TD` → `TD+8` 名串，且 `slot offset/4 == 线索槽号`。`Class` 部分仅作线索。
3. **③整体合同**：只认 ③b②——被调返回约定**可从字节伪证**（imm 哨兵/错误码；bool 0/1 与零判断不算，D-46(A)）+ **调用方真的拿它分支** + 两路动作真不同 + test 与 jcc 之间无 eax 覆写 + 单 call 非多路同一 call。
4. **④使用见证**：按 D-40 第 594 行「两种形态」与 **D-43(A)**——活 vtable 槽位形态 = 构造器装的活表 + `vt[slot]==entry` + **写点在行外** + site 不共用，**不要求真实 `call [reg+disp]` 派发点**；`atexit` 析构器写的表不算活 vptr（㉓，已用 `push <fn>; call 0x7C978A` 逐点排除）。
5. **②④不同源**：② 锚在 `.rdata` 的 RTTI 描述符字节（COL/TD/名串），④ 锚在 `.text` 的构造安装指令字节；两者地址与段均不同，不共用 site。
6. **三陷阱**逐行排查：eax 覆写、多路同一 call、模板假句。

## 基础率（诚实报数）

| 档 | 行数 | 口径 |
|---|---:|---|
| 本批行数 | 18 | S14 named=True 中 entry 升序前 18 |
| ①入口 PASS | 18 | 全部在 `.text`、`skipdata=0`、atlas 边界自洽 |
| ②类身份钉住 | **18** | 18/18 均有 RTTI 名串且 `slot offset/4 == 线索槽号` |
| ③③b② 成立 | **5** | 0041F580 / 00503040 / 00512290 / 00512480 / 0065AC40 |
| ④使用见证成立 | **18** | 18/18 均有行外非 atexit 构造安装点写本 vt |
| **四环齐全** | **5** | 上列 5 行，rate = 5/18 = 0.2778 |

`base_rate.tsv`：`B1  18  18  5  18  5  0.2778`

## 本批 18 行总表（entry / ②③④ / 是否产出）

| # | entry | name(原样) | ①入口 | ②类身份 | ③③b | ④使用见证 | ②④不同源 | 裁定 | 产出 |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | 0041E540 | AITriggerTypeClass::vslot5 | PASS | PASS(.?AVAITriggerTypeClass@@) | FAIL(成功路=纯构造初始化→模板假句) | PASS(活vt 行外 0041E401) | 是 | 不成立 | 否 |
| 2 | 0041E5C0 | AITriggerTypeClass::vslot6 | PASS | PASS(.?AVAITriggerTypeClass@@) | FAIL(③a 纯转发：两路仅 eax 常量差) | PASS(活vt) | 是 | 不成立 | 否 |
| 3 | 0041F580 | AITriggerTypeClass::vslot25 | PASS | PASS(.?AVAITriggerTypeClass@@) | **PASS(③b② -1 未命中哨兵)** | PASS(活vt 行外 0041E401) | 是 | **成立** | **是** |
| 4 | 0041FFF0 | AITriggerTypeClass::vslot8 | PASS | PASS(.?AVAITriggerTypeClass@@) | FAIL(间接被调 `call [edx+0x10]`，返回约定不可伪证) | PASS(活vt) | 是 | 不成立 | 否 |
| 5 | 004FB9B0 | HouseClass::slot10 | PASS | PASS(.?AVHouseClass@@) | FAIL(9 站全为间接 `call [reg+0x10]`) | PASS(活vt 行外 004F5457) | 是 | 不成立 | 否 |
| 6 | 005024F0 | HouseClass::slot3 | PASS | PASS(.?AVHouseClass@@) | FAIL(被调 14B thunk 返回源不可定/零判断) | PASS(活vt 行外 004F5480) | 是 | 不成立 | 否 |
| 7 | 00503040 | HouseClass::slot5 | PASS | PASS(.?AVHouseClass@@) | **PASS(③b② E_POINTER 早退)** | PASS(活vt 行外 004F5457) | 是 | **成立** | **是** |
| 8 | 00504080 | HouseClass::slot6 | PASS | PASS(.?AVHouseClass@@) | FAIL(p3=0：34 站无一可伪证) | PASS(活vt) | 是 | 不成立 | 否 |
| 9 | 00511850 | HouseTypeClass::slot25 | PASS | PASS(.?AVHouseTypeClass@@) | FAIL(零值判断 `test/je`，0x528A10 失败返 0) | PASS(活vt 行外 00511572) | 是 | 不成立 | 否 |
| 10 | 00512290 | HouseTypeClass::slot5 | PASS | PASS(.?AVHouseTypeClass@@) | **PASS(③b② E_POINTER 早退)** | PASS(活vt 行外 00511572) | 是 | **成立** | **是** |
| 11 | 00512480 | HouseTypeClass::slot6 | PASS | PASS(.?AVHouseTypeClass@@) | **PASS(③b② E_POINTER 早退)** | PASS(活vt 行外 00511572) | 是 | **成立** | **是** |
| 12 | 00512760 | HouseTypeClass::slot8 | PASS | PASS(.?AVHouseTypeClass@@) | FAIL(间接 `call [edx+0x10]`) | PASS(活vt) | 是 | 不成立 | 否 |
| 13 | 0065AB80 | RadioClass::slot5 | PASS | PASS(.?AVRadioClass@@) | FAIL(p3=0) | PASS(活vt 行外 0065A798 + direct 0070BF5C) | 是 | 不成立 | 否 |
| 14 | 0065AC40 | RadioClass::slot6 | PASS | PASS(.?AVRadioClass@@) | **PASS(③b② E_POINTER 早退)** | PASS(活vt 行外 0065A798 + direct 0070C25F) | 是 | **成立** | **是** |
| 15 | 00691630 | ScriptClass::slot5 | PASS | PASS(.?AVScriptClass@@) | FAIL(成功路=基类构造+装表→模板假句) | PASS(活vt 行外 006913DD) | 是 | 不成立 | 否 |
| 16 | 00691690 | ScriptClass::slot6 | PASS | PASS(.?AVScriptClass@@) | FAIL(③a 纯转发) | PASS(活vt) | 是 | 不成立 | 否 |
| 17 | 006918A0 | ScriptTypeClass::slot25 | PASS | PASS(.?AVScriptTypeClass@@) | FAIL(零/负值判断 `test/jle`) | PASS(活vt 行外 006916D1) | 是 | 不成立 | 否 |
| 18 | 00691D90 | ScriptTypeClass::slot5 | PASS | PASS(.?AVScriptTypeClass@@) | FAIL(成功路=基类构造+装表→模板假句) | PASS(活vt 行外 006916D1) | 是 | 不成立 | 否 |

## 逐行裁定依据（每行自身地址锚；字节见 `EVIDENCE/ROW_<entry>.txt`）

**② 18/18 全数钉住**（与 S04 相反，见下节）：每行 entry 作 4B VA 在 `.rdata` 命中**唯一**槽，回扫 `[vt-4]=COL(sig=0)`、`[COL+0xC]=TD`、`TD+8` 名串，`slot offset/4 == 线索槽号`。例：`0041F580` 槽 `007E2AB4`=`80 f5 41 00`（vt `007E2A50`+0x64，slot#25）→ COL `007FB7B0`（sig `00 00 00 00`）→ TD `00818140` → `.?AVAITriggerTypeClass@@`；`005024F0` 槽 `007EA800`（vt `007EA7F4`+0x0C，slot#3）→ `.?AVHouseClass@@`；`0065AC40` 槽 `007F0520`（vt `007F0508`+0x18，slot#6）→ `.?AVRadioClass@@`。

**③ 成立 5 行（各自独立站点与语义）**
- `0041F580` AITriggerTypeClass::vslot25：站点 `0x41F783` `e8 08 45 10 00`→`0x523C90`，`0x41F788` `83 f8 ff` cmp eax,-1，`0x41F78B` `74 0b` je→`0x41F798`。被调约定可字节伪证：未命中 `0x523CE7` `83 c8 ff`(or eax,-1) 后 ret 返 **-1**；命中 `0x523CEC` `8b c6`(mov eax,esi) 返**下标**。命中路 `0x41F78D` `8b 0d 4c e3 a8 00` + `0x41F793` `8b 34 81` 用下标取表项；未命中路 `0x41F798` 转 `call 0x747370` 查下一张表（后接 `0x41CAA0`/`0x45E7B0` 四级链）。语义：**按名字在类型名表查下标，-1 即逐表回退，命中存 this+0xD8**。
- `00503040` HouseClass::slot5：站点 `0x5031C9` `e8 b2 d1 f0 ff`→`0x410380`（空参 `0x410389` `b8 03 40 00 80`=E_POINTER），`0x5031D0` `0f 8c …` jl→`0x504069`（`5f 5e 5d 5b 83 c4 10 c2 08 00` 原样返负 HRESULT）；成功路 `0x5031E1` call `0x4F5190`、`0x5031F4` `ff 11` 派发 +0x5700 子对象、`0x5031FD..0x503281` 连续 12 次 `call 0x49FBE0` 于 +0x5500 起 stride 0x14 逐容器读入、`0x50328F` 起 `0x6CF240` 构造。语义：**流读入（12 个并行容器逐一 Load）**。
- `00512290` HouseTypeClass::slot5：站点 `0x5122D0`→`0x410380`，`0x5122D7` `0f 8c 90 01 00 00` jl→`0x51246D`（`5f 5e 5d 5b 59 c2 08 00` 原样返）；成功路四次 `call [reg+0xC]` 读 4B 计数（`0x51230E/0x51232D/0x51236F/0x5123BB`）、三处循环逐元素（`0x512337/0x512392/0x5123DE`）、三段 `0x6CF240`（`0x512405/0x512430/0x51245B`）。语义：**流读入 + 逐元素构造 +0x150/+0x16C/+0x188 三数组**。
- `00512480` HouseTypeClass::slot6：站点 `0x512491`→`0x410320`（空参 `0x41032B` `b8 03 40 00 80`），`0x512498` `0f 8c be 00 00 00` jl→`0x51255C`（`5f 5e c2 0c 00` 原样返）；成功路三次 `call [reg+0x10]` 写计数（`0x5124B5/0x5124F3/0x512531`）+ 三循环逐元素写 4B（`0x5124D3/0x512511/0x51254F`）。语义：**流写出三数组**。
- `0065AC40` RadioClass::slot6：站点 `0x65AC52`→`0x410320`，`0x65AC59` `7c 4a` jl→`0x65ACA5`（`5f 5e 5b c2 0c 00` 原样返）；成功路 `0x65AC71` `ff 52 10` 读 4B 计数入 +0xE8、`0x65AC76` `7c 4a` 再判负同 epilogue、`0x65AC93` `ff 51 10` 循环逐 4B 读入 +0xE4 数组、`0x65ACA3` `33 c0` 返 0。语义：**流读入计数 + 逐 4B 填充 +0xE4 数组**。

**③ FAIL 13 行（逐行独立理由，详见各自 EVIDENCE）**
- 模板假句（成功路仅装虚表/构造成员，语义只能落「对象初始化」式）：`0041E540`（`0x41E564/6A/71/78` 装 4 张子对象 vt + 三次 `0x6CF240`）、`00691630`（`0x691654/5A/61/68` + `0x6CF240(esi+0x24)`）、`00691D90`（`0x691DB4/BA/C1/C8`）。**结构上站点合格、仅形态不合格**——3 行见「待裁」。
- ③a 纯转发（两路只差 eax 常量）：`0041E5C0`（`0x41E5D8 33 c0` 与失败路在 `0x41E5DA c2 0c 00` 汇合）、`00691690`（`0x6916A8 33 c0` 与 `0x6916AA c2 0c 00` 汇合）。
- 间接被调、返回约定物理不可伪证：`0041FFF0`（`0x420023 ff 52 10`）、`004FB9B0`（9 站 `ff 52 10`/`ff 50 10`）、`00512760`（`0x51279A ff 52 10`）。
- 零值/负值判断而非错误码：`00511850`（7 站 `test eax,eax; je`，`0x528A10` 失败返 0 于 `0x528BC0 33 c0`）、`006918A0`（`0x69190D 85 c0` + `0x69190F 7e 3c` jle）、`005024F0`（`call 0x7C8E17` 为 14B thunk `6a 01 ff 74 24 08 e8 20 06 00 00 59 59 c3`→`0x7C9442`，返回源不可定）。
- 无可伪证站点（`p3=0`）：`00504080`（34 站两路动作不同但无被调侧约定）、`0065AB80`（4 站同因）。

**④ 18/18 成立**：每行 vtable 都在 `.text` 有**行外**、`atexit=False` 的构造安装点（`mov dword ptr [reg], vt`），逐点核过 `push <fn>; call 0x7C978A` 排除（㉓）。例：`0041F580`→`0x41E401`(in 0041E350)；`00503040`→`0x4F5457`(004F5190)；`0065AC40`→`0x65A798`(0065A750)+direct `0x70C25F`。与 ② 不同源（`.text` 指令 vs `.rdata` RTTI 数据）。

## 与 S04 的败因对比（本批有多少行 ② 真的钉住）

- **S04**：73 个 ③b② 机械命中 `p3b2_named=0`（全无名字）——entry 作 4B VA 全镜像 **0 命中**、无虚表槽、无可安装 RTTI 链 ⇒ **② 物理不可得**（D-41 情形），36 行实测全败、B1/B2 四环 0。
- **本批 S14**：18 行 **② 全部被 RTTI + 虚表独立钉死（18/18）**，且 18/18 的 `slot offset/4` 与线索槽号逐行自洽（不是拿名字反推槽号，而是槽号被字节复算）。这是 S04 完全不具备的条件。
- **但 ② 不是本批瓶颈**：S04 死在 ②，本批死在 ③。18 行里 13 行的 ③ 不成立，其中 8/13 是「间接 `call [reg+0x10]` 被调不可定位 ⇒ 返回约定无法从字节伪证」，3/13 是「成功路只是装虚表+构造 ⇒ 语义只能写成对象初始化式（模板假句）」，2/13 是「纯转发壳」。
- 结论：**② 从 S04 的 0/18 → 本批 18/18；四环齐全从 0 → 5**。瓶颈已从「取不到身份」转为「有名字也拿不到可伪证的 ③b② 整体合同」。

## 待裁（2 项，未擅自并入 delta）
1. **3 行「结构合格 / 形态不合格」**：`0041E540`、`00691630`、`00691D90` 的站点确实是「call→`test eax,eax`→`jl`→失败原样返负 HRESULT / 成功继续」，被调 `0x410380` 的 E_POINTER 哨兵也已字节核到；唯一问题是**成功路内容全部是装虚表 + 构造成员**，one_line_semantics 只能落到「校验后初始化对象」式，正撞卡片『模板假句』禁令。若 Lead 裁定该类可算 ③b②，本批可 +3（→8/18）。
2. **间接 `call [reg+0x10]` 的 -1 约定**：`0041FFF0`、`004FB9B0`、`00512760` 的调用点全按 `cmp eax,-1` 分支（HouseClass 族 9 个站点口径一致，强烈提示被调是「Find→下标或 -1」虚方法），但被调经虚派发无法定位到函数体 ⇒ 按 D-40「可伪证」判 FAIL。若允许「多站点同口径」作弱伪证，可再 +3。

## 汇总
- rows_checked：**18**
- ② 钉住行数：**18**
- ③b② 成立行数：**5**
- ④ 成立行数：**18**
- all_four_rings（严格 D-40/D-43）：**5**
- delta 产出：**5 行**（0041F580 / 00503040 / 00512290 / 00512480 / 0065AC40）

## 输出清单
- `REPORT.md`（本文件）、`PROGRESS.md`、`base_rate.tsv`、`delta.tsv`（5 行）
- `EVIDENCE/ROW_<entry>.txt` × 18（逐行四环地址与字节）
- `_work/`（filter_b1 / recore / core2 / analyze / dump_sites / sites_summary / verify_callees / ring4_index / install_ctx / site_bytes / gen_evidence / write_delta + 中间 JSON/TXT，全部只读目标、可复算）
