# NAMED-PUSH — S06 B1 批次（有名字的 ③b② 候选，攻 proved 增量）

> 状态：**完成**。执行纪律已遵：先建目录 → 先写 REPORT 骨架 → 逐行核完即落 `EVIDENCE/`；每 5 行追加 `PROGRESS.md`。
> 卡片：`lead\next_re_20261117_r14\_cards\NAMED-PUSH.md`（全文 80 行读完）
> 本批：**B1** = `SURVEY_3B2\hits_detail.tsv` 中 `subsystem==S06` AND `p3b2_named==True`，**排除 `fn_XXXXXXXX` / `sub_XXXXXXXX` 伪名**，按 entry 升序取**前 18 行**。
> 输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S06_B1\`（卡片 `<你的子系统>`=S06、`<你的目录>`=本目录）。

## 材料自校验
- 目标：`ra2youli\gamemd.exe`；现场 `Get-FileHash -Algorithm SHA256` = `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` ⇒ **与卡片期望逐字一致**。
- ImageBase `0x400000`；`.text=[0x401000,0x7E038D)`（VirtualSize=0x3DF38D）。
- Python 3.12.10 / capstone 5.0.7（**skipdata=True**）/ pefile 2024.8.26；无 venv、未 pip install。
- 只读输入：`SURVEY_3B2\hits_detail.tsv`（仅当线索）、`W130_atlas\function_atlas.tsv`（仅取函数边界）。未改 `coverage.tsv` / `PANEL.md` / `R14_COMMON.md` / 台账 / `SURVEY_3B2` / `S04_PUSH_*`。写域仅本目录。

## 筛选命令（得到本批 18 个 entry）

```powershell
$p = "D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv"
$rows = Import-Csv $p -Delimiter "`t"
$sel = $rows | Where-Object {
    $_.subsystem -eq 'S06' -and $_.p3b2_named -eq 'True' -and
    $_.name -notmatch '^(fn|sub)_[0-9A-Fa-f]{8}$'
}
$b1 = $sel | Sort-Object { [Convert]::ToInt32($_.entry,16) } | Select-Object -First 18
$b1 | Format-Table entry,subsystem,name,grade,size,n_call,n_site,n_valid,p3b2_named -AutoSize
```

结果：S06 `p3b2_named=True` 共 **46** 行（卡片记 46，一致），其中 `fn_`/`sub_` 伪名 **0** 行 ⇒ 剔后 46 行全是 `Class::slotN` 形态；B1 = entry 升序前 18 行。等价 Python 落盘于 `_work/filter_b1.py`（`sorted(sel, key=int(entry,16))[:18]`）。

## 判定口径（严格 D-40，宁严不宽；并纳入 S14 两条被否教训）
1. **①入口**：entry 在 `.text` 内、atlas 边界自洽、反汇编 `skipdata=0`。
2. **②类身份**：`.rdata` 中 entry 作 4B VA 命中的槽 → 回扫 `[vt-4]=COL(sig=0)` → `[COL+0xC]=TD` → `TD+8` 名串，且 `slot offset/4 == 线索槽号`。`Class` 部分仅作线索，钉不死判 FAIL。高槽号（slot54/73）须把回扫上限从 40 提到 130 才命中 COL，已逐行核实。
3. **③整体合同**：只认 ③b②——被调返回约定**可从字节伪证**（imm 哨兵/错误码；bool 0/1 与零判断不算，D-46(A)）+ **调用方真的拿它分支** + 两路动作真不同 + test 与 jcc 之间无 eax 覆写 + 单 call 非多路同一 call。禁止把「被调用者内部的写」当循环内非栈写；禁止 ③a 形态（单调用+单写、纯转发、零+默认、无分支直线）。
4. **④使用见证**：活 vtable 槽位形态 = 构造器装的活表 + `vt[slot]==entry` + **写点在行外** + site 不共用；`atexit` 析构器写的表不算活 vptr（**㉓ 成对陷阱**：④ 锚点若落在析构器里判 FAIL）。逐点用字节区分构造器（base-ctor call + field init + vptr install）与析构器（全局表注销 / `push 1; call [vtable slot0]` 成员析构）。
5. **②④不同源**：② 锚在 `.rdata` 的 RTTI 描述符字节链，④ 锚在 `.text` 的构造安装指令字节；两者地址与段均不同，不共用 site。
6. **三陷阱**逐行排查：eax 覆写、多路同一 call、模板假句。
7. **读写方向**（S14 被否教训）：`call 0x410380` 经 `[eax+0xC]`（Read 槽）= **流读入**；`call 0x410320` 经 `[eax+0x10]`（Write 槽）= **流写出**；one_line_semantics 必须与实际字节方向一致，写反判 FAIL。本批两条 E_POINTER 行方向已逐字节核定，未写反。

## 基础率（诚实报数）

| 档 | 行数 | 口径 |
|---|---:|---|
| 本批行数 | 18 | S06 named=True 剔伪名后 entry 升序前 18 |
| ①入口 PASS | 18 | 全部 in_text、skipdata=0、atlas 边界自洽 |
| ②类身份钉住 | **18** | 18/18 均有 RTTI 名串与线索类名一致、`slot offset/4 == 线索槽号`、槽值==entry |
| ③③b② 成立 | **4** | 004839F0 / 00483C10 / 005F92D0 / 005FC570 |
| ④使用见证成立 | **18** | 18/18 均有行外非析构器构造器安装点写本 vt |
| **四环齐全** | **4** | 上列 4 行，rate = 4/18 = 0.2222 |

`base_rate.tsv`：`B1  18  18  4  18  4  0.2222`

## 本批 18 行总表（entry / ②③④ / 是否产出）

| # | entry | name(原样) | ①入口 | ②类身份 | ③③b | ④使用见证 | ②④不同源 | 裁定 | 产出 |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | 004839F0 | CellClass::slot5 | PASS | PASS(.?AVCellClass@@) | **PASS(③b② E_POINTER 判负，流读入)** | PASS(活vt 行外 0047BD5C) | 是 | **成立** | **是** |
| 2 | 00483C10 | CellClass::slot6 | PASS | PASS(.?AVCellClass@@) | **PASS(③b② E_POINTER 判负，流写出)** | PASS(活vt 行外 0047BD5C) | 是 | **成立** | **是** |
| 3 | 00543330 | IsometricTileClass::slot73 | PASS | PASS(.?AVIsometricTileClass@@) | FAIL(间接虚调用 call [eax+0x6c]+零判断) | PASS(活vt 行外 005439B7) | 是 | 不成立 | 否 |
| 4 | 005439F0 | IsometricTileClass::slot6 | PASS | PASS(.?AVIsometricTileClass@@) | FAIL(③a 纯转发：29B 仅 xor eax,eax) | PASS(活vt 行外 005439B7) | 是 | 不成立 | 否 |
| 5 | 00543B10 | IsometricTileClass::slot8 | PASS | PASS(.?AVIsometricTileClass@@) | FAIL(间接 call [edx+0x10]，-1 不可伪证) | PASS(活vt 行外 005439B7) | 是 | 不成立 | 否 |
| 6 | 00549AA0 | IsometricTileTypeClass::slot32 | PASS | PASS(.?AVIsometricTileTypeClass@@) | FAIL(0x7C8E17 分配包装+零判断) | PASS(活vt 行外 00544A42) | 是 | 不成立 | 否 |
| 7 | 00549AE0 | IsometricTileTypeClass::slot35 | PASS | PASS(.?AVIsometricTileTypeClass@@) | FAIL(零判断 test/je) | PASS(活vt 行外 00544A42) | 是 | 不成立 | 否 |
| 8 | 00549C80 | IsometricTileTypeClass::slot5 | PASS | PASS(.?AVIsometricTileTypeClass@@) | FAIL(chA p3=0，无可伪证站点) | PASS(活vt 行外 00544A42) | 是 | 不成立 | 否 |
| 9 | 00549D70 | IsometricTileTypeClass::slot6 | PASS | PASS(.?AVIsometricTileTypeClass@@) | FAIL(chA p3=0 薄封装) | PASS(活vt 行外 00544A42) | 是 | 不成立 | 否 |
| 10 | 00589A60 | T_DynamicVectorClass_USubzoneTrackingStruct__::slot2 | PASS | PASS(.?AV?$DynamicVectorClass@USubzoneTrackingStruct@@@@) | FAIL(0x7C8E17 分配零判断+模板假句) | PASS(活vt 行外 005650CD) | 是 | 不成立 | 否 |
| 11 | 005F3E70 | IsometricTileClass::slot23 | PASS | PASS(.?AVIsometricTileClass@@，5 槽共享) | FAIL(间接虚调用+零判断) | PASS(活vt 行外 005439B7) | 是 | 不成立 | 否 |
| 12 | 005F92D0 | IsometricTileTypeClass::slot25 | PASS | PASS(.?AVIsometricTileTypeClass@@) | **PASS(③b② Find -1 哨兵)** | PASS(活vt 行外 00544A42) | 是 | **成立** | **是** |
| 13 | 005FC570 | OverlayClass::slot73 | PASS | PASS(.?AVOverlayClass@@) | **PASS(③b② Find -1 哨兵)** | PASS(活vt 行外 005FC38F) | 是 | **成立** | **是** |
| 14 | 005FD270 | OverlayClass::slot54 | PASS | PASS(.?AVOverlayClass@@) | FAIL(零判断 test/je 0x47C550) | PASS(活vt 行外 005FC38F) | 是 | 不成立 | 否 |
| 15 | 005FDF70 | OverlayClass::slot8 | PASS | PASS(.?AVOverlayClass@@) | FAIL(间接 call [edx+0x10]，-1 不可伪证) | PASS(活vt 行外 005FC38F) | 是 | 不成立 | 否 |
| 16 | 005FE530 | OverlayTypeClass::slot32 | PASS | PASS(.?AVOverlayTypeClass@@) | FAIL(0x7C8E17 分配零判断) | PASS(活vt 行外 005FE2F1) | 是 | 不成立 | 否 |
| 17 | 005FE570 | OverlayTypeClass::slot35 | PASS | PASS(.?AVOverlayTypeClass@@) | FAIL(0x7C8E17 分配零判断) | PASS(活vt 行外 005FE2F1) | 是 | 不成立 | 否 |
| 18 | 005FE770 | OverlayTypeClass::slot25 | PASS | PASS(.?AVOverlayTypeClass@@) | FAIL(0x528A10 失败返 0 零判断) | PASS(活vt 行外 005FE2F1) | 是 | 不成立 | 否 |

## 逐行裁定依据（每行自身地址锚；字节见 `EVIDENCE/ROW_<entry>.txt`）

**② 18/18 全数钉住**（与 S04 相反，见下节）：每行 entry 作 4B VA 在 `.rdata` 命中唯一槽，回扫 `[vt-4]=COL(sig=0)`、`[COL+0xC]=TD`、`TD+8` 名串，`slot offset/4 == 线索槽号`，槽值==entry。例：`004839F0` 槽 `007E4F00`(vt `007E4EEC`+0x14，slot#5)→COL `007FD078`→TD `0081CD70`→`.?AVCellClass@@`；高槽号 `00543330`(slot#73)、`005FC570`(slot#73) 的 COL 距槽 292B，需把回扫上限设到 130 槽才命中，已逐行核实名串与槽号自洽。所有 18 行的 `Class` 名均来自 RTTI 名串而非 `slotN` 字面。

**③ 成立 4 行（各自独立站点与语义）**
- `004839F0` CellClass::slot5（流读入）：call `0x410380`@`0x4839FF`；`xor ebx,ebx`@`0x483A04`（不碰 eax）；`cmp eax,ebx`@`0x483A06`；`jl 0x483C00`@`0x483A08`。被调 `0x410380` 空参 `0x410389 mov eax,0x80004003`=E_POINTER，正路 `0x41039E call [eax+0xc]`=Read 槽 ⇒ 失败返负 HRESULT、成功返 0。失败路 `0x483C00` 弹栈 ret 8（跳过 `0x483BFE xor eax,eax`）原样返 HRESULT；成功路 `0x483A84`/`0x483AAB call [reg+0xc]` 逐项读入。语义方向与 `[eax+0xc]` Read 槽一致（未写反）。
- `00483C10` CellClass::slot6（流写出）：call `0x410320`@`0x483C22`；`test eax,eax`@`0x483C27`；`jl 0x483C79`@`0x483C29`。被调 `0x410320` 空参 `0x41032B mov eax,0x80004003`=E_POINTER，正路 `0x410348 call [eax+0x10]`=Write 槽。失败路原样返 HRESULT；成功路 `0x483C45`/`0x483C67 call [reg+0x10]` 写计数与逐元素。语义方向与 `[eax+0x10]` Write 槽一致（未写反）。
- `005F92D0` IsometricTileTypeClass::slot25（Find -1）：call `0x7514D0`@`0x5F93B5`；`cmp eax,-1`@`0x5F93BA`(83 f8 ff)；`je`@`0x5F93BD`(74 02)。被调未命中 `0x751516 or eax,-1`(83 c8 ff) 返 -1、命中 `0x75151B mov eax,esi` 返下标。je 命中保留旧值、否则 `0x5F93D5 mov [ebx+0x1f0],edi` 落库。
- `005FC570` OverlayClass::slot73（Find -1）：call `0x485010`@`0x5FD1BB`（转发到 `0x5FDD20`）；`cmp eax,-1`@`0x5FD1C0`；`je`@`0x5FD1C3`。被调未命中 `0x5FDDD8 or eax,-1` 返 -1、命中 `0x5FDDC1 xor eax,eax`(33 c0) 后 `ret@0x5FDDC8` 返 0。je 命中跳过、否则 `0x5FD1CB mov eax,[edx+eax*4]` 取项并 `0x5FD1E7 mov [esi+0xd4],eax` 落库。
- 这两行 Find -1 属「模板级低信息量 ③b②」（与 S14 B1 `0041F580` 同型），严格符合卡面「失败返什么/成功返什么/调用方拿它分支」的字面要求；被调 -1 返值均在被调侧 `or eax,-1` 字节伪证（非仅 call-site 哨兵）。

**③ 失败 14 行**（各自独立理由，详见 EVIDENCE）：间接虚调用返回约定不可伪证（00543330/00543B10/005FDF70）；③a 纯转发（005439F0/00549D70）；分配包装零判断（00549AA0/00589A60/005FE530/005FE570）；零值判断 D-46(A)（00549AE0/005FD270/005FE770）；chA p3=0（00549C80）；间接+零判断混合（005F3E70）。

**④ 18/18 全数成立**：每行 vtable 均有行外非析构器构造器安装点。构造器判据=base-ctor call + field init + vptr install、atexit=False。CellClass/IsometricTileClass/OverlayClass/OverlayTypeClass 的构造器安装点分别为 `0047BD5C`/`005439B7`/`005FC38F`/`005FE2F1`；IsometricTileTypeClass 用 `00544A42`（func `00544A00`，`call 0x5f7320`@`00544A08`，`ret 4`@`00544A60`）——该 vtable 的另两处 `00544A77`/`00549D02` 是全局表注销/成员析构的析构器安装点，按 ㉓ 排除。㉓ 成对陷阱逐点排查：无一行 ④ 锚落在析构器。

## 与 S04 的败因对比（本批有多少行 ② 真的钉住了）

- S04 的 73 个命中**全部无名字（named=0）**，② 类身份取不到 ⇒ 36 行实测全败。
- 本批 18 行**全部有名字（`Class::slotN`）**，且经独立 RTTI 取证，**② 真钉住 18/18（100%）**——与 S04 的 0/36 形成鲜明对照。这印证了卡片「② 是硬约束、本卡只打有名字候选」的前提。
- 但 ② 全钉住并不保证整体成立：③b② 只成立 4/18（22.22%），败因集中在「间接虚调用不可伪证」「分配包装零判断 D-46(A)」「③a 纯转发/模板假句」三类，属 ③ 的固有门槛，非身份问题。
- ②④ 不同源 18/18（②=.rdata RTTI 数据链，④=.text 构造安装指令）。

## 执行纪律留痕
- 先建目录、先写 REPORT 骨架 ✓
- 每核完一行立刻落盘 ✓（18 份 `EVIDENCE/ROW_<entry>.txt`，delta/base_rate/PROGRESS 同步）
- 每 5 行追加 `PROGRESS.md` ✓（1–5 / 6–10 / 11–15 / 16–18 四段）
- 单行取证克制，只取四环锚点 ✓；每行独立 reason（无整批共用）✓
- 读写方向逐行核对（未写反）✓；㉓ 析构器锚点逐点排除 ✓
