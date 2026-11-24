# NAMED-PUSH — S06 B3 批次（有名字的 ③b② 候选，攻 proved 增量）

> 状态：**完成**。执行纪律已遵：先建目录 → 先写 REPORT 骨架 → 逐行核完即落 `EVIDENCE/`；每 5 行追加 `PROGRESS.md`（#37–#41 / #42–#46 两段）。
> 卡片：`lead\next_re_20261117_r14\_cards\NAMED-PUSH.md`（全文 80 行读完）
> 本批：**B3** = `SURVEY_3B2\hits_detail.tsv` 中 `subsystem==S06` AND `p3b2_named==True`，**排除 `fn_XXXXXXXX` / `sub_XXXXXXXX` 伪名**，按 entry 升序取**第 37 到第 54 行**。
> 输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S06_B3\`（卡片 `<你的子系统>`=S06、`<你的目录>`=本目录）。
> **范围说明**：S06 `p3b2_named=True` 剔伪名后总数 **46**，故第 37–54 行实际只落到第 **37–46** 行 = **10 行**（卡片每批 ≤18 行，B3 为末批不满 18）。

## 材料自校验
- 目标：`ra2youli\gamemd.exe`；现场 `Get-FileHash -Algorithm SHA256` = `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` ⇒ **与卡片期望逐字一致**。
- ImageBase `0x400000`；`.text=[0x401000,0x7E038D)`。
- Python 3.12.10 / capstone 5.0.7（**skipdata=True**）/ pefile 2024.8.26；无 venv、未 pip install（现场核验）。
- 只读输入：`SURVEY_3B2\hits_detail.tsv`（仅当线索）。未改 `coverage.tsv` / `PANEL.md` / `R14_COMMON.md` / 台账 / `SURVEY_3B2` / `S04_PUSH_*`。写域仅本目录。

## 筛选命令（得到本批 entry）

```powershell
$p = "D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv"
$rows = Import-Csv $p -Delimiter "`t"
$sel = $rows | Where-Object {
    $_.subsystem -eq 'S06' -and $_.p3b2_named -eq 'True' -and
    $_.name -notmatch '^(fn|sub)_[0-9A-Fa-f]{8}$'
}
$sorted = $sel | Sort-Object { [Convert]::ToInt32($_.entry,16) }
$b3 = $sorted | Select-Object -Skip 36 -First 18   # 第37..54，实际只到第46
$b3 | Format-Table entry,subsystem,name,grade,size,n_call,n_site,n_valid,p3b2_named -AutoSize
```

等价 Python 落盘于 `_work/filter_b3.py`（`sorted(sel, key=int(entry,16))[36:54]`）。
结果：S06 `p3b2_named=True` 共 **46** 行（卡片记 46，一致），其中 `fn_`/`sub_` 伪名 **0** 行 ⇒ 剔后 46 行；B3 = entry 升序第 37–46 行（0-based `[36:46]`），共 **10 行**。

## 本批候选（entry 升序 #37–#46）

| # | entry | name(原样) | grade | size | n_call | n_site | n_valid |
|---:|---|---|---|---:|---:|---:|---:|
| 37 | 0071E1D0 | TerrainTypeClass::slot5 | [静态推断] | 105 | 4 | 1 | 1 |
| 38 | 0071E240 | TerrainTypeClass::slot6 | [静态推断] | 29 | 1 | 1 | 1 |
| 39 | 0071E360 | TerrainTypeClass::slot8 | [静态推断] | 172 | 5 | 1 | 1 |
| 40 | 007220A0 | TiberiumClass::slot7 | [静态推断] | 47 | 1 | 1 | 1 |
| 41 | 007220D0 | TiberiumClass::slot6 | [静态推断] | 97 | 3 | 1 | 1 |
| 42 | 007281A0 | TubeClass::slot5 | [静态推断] | 64 | 2 | 1 | 1 |
| 43 | 007281E0 | TubeClass::slot6 | [静态推断] | 29 | 1 | 1 | 1 |
| 44 | 00728710 | TubeClass::slot8 | [静态推断] | 214 | 5 | 2 | 1 |
| 45 | 00763D90 | WaypointPathClass::slot6 | [静态推断] | 109 | 3 | 3 | 3 |
| 46 | 00763E20 | WaypointPathClass::slot8 | [静态推断] | 200 | 5 | 1 | 1 |

## 判定口径（严格 D-40，宁严不宽；沿用 S06 B1/B2 同套方法）
1. **①入口**：entry 在 `.text` 内、函数边界自洽、反汇编 `skipdata=True`。
2. **②类身份**：`.rdata` 中 entry 作 4B VA 命中的槽 → 回扫 `[vt-4]=COL(sig=0)` → `[COL+0xC]=TD` → `TD+8` 名串，且 `slot offset/4 == 线索槽号`。`Class` 部分仅作线索，钉不死判 FAIL。**不当小成员表 vtable 当对象主虚表**（真主虚表槽 0 常见 00410260）。
3. **③整体合同**：只认 ③b②——被调返回约定**可从字节伪证**（imm 哨兵/错误码；bool 0/1 与零判断不算 D-46(A)）+ **调用方真的拿它分支** + 两路动作真不同 + test 与 jcc 之间无 eax 覆写 + 单 call 非多路同一 call。禁止把「被调用者内部的写」当循环内非栈写；禁止 ③a 形态。
4. **④使用见证**：活 vtable 槽位形态 = 构造器装的活表 + `vt[slot]==entry` + 写点在行外 + site 不共用；**㉓ 成对陷阱：④ 锚点若落在析构器里判 FAIL**。
5. **②④不同源**：② 锚在 `.rdata` 的 RTTI 描述符字节链，④ 锚在 `.text` 的构造安装指令字节，不共用 site。
6. **三陷阱**逐行排查：eax 覆写、多路同一 call、模板假句。
7. **读写方向**：`call 0x410380` 经 `[eax+0xC]`（Read 槽）= 流读入；`call 0x410320` 经 `[eax+0x10]`（Write 槽）= 流写出；one_line_semantics 必须与实际字节方向一致，**不许写反**。

## 基础率（诚实报数）

| 档 | 行数 | 口径 |
|---|---:|---|
| 本批行数 | 10 | S06 named=True 剔伪名后 entry 升序第 37–46（第 47–54 不存在，S06 仅 46 行） |
| ①入口 PASS | 10 | 全部 in_text、skipdata=0、atlas 边界自洽、末 ret |
| ②类身份钉住 | **10** | 10/10 均有 RTTI 名串与线索类名一致、slot offset/4 == 线索槽号、槽值==entry；并核过 vtable slot0=00410260/slot1=00410300 ⇒ 真主虚表，非小成员表 |
| ③③b② 成立 | **5** | 0071E1D0 / 007220A0 / 007220D0 / 007281A0 / 00763D90 |
| ④使用见证成立 | **10** | 10/10 均有行外非析构器构造器安装点，atexit=False、site 不共用 |
| **四环齐全** | **5** | 上列 5 行，rate = 5/10 = 0.5000 |

`base_rate.tsv`：`B3	10	10	5	10	5	0.5000`

## 本批逐行总表（entry / ②③④ / 是否产出）

| # | entry | name(原样) | ①入口 | ②类身份 | ③③b | ④使用见证 | ②④不同源 | 裁定 | 产出 |
|---:|---|---|---|---|---|---|---|---|---|
| 37 | 0071E1D0 | TerrainTypeClass::slot5 | PASS | PASS(.?AVTerrainTypeClass@@) | **PASS(③b② E_POINTER 判负，流读入)** | PASS(活vt 行外 0071DAF7) | 是 | **成立** | **是** |
| 38 | 0071E240 | TerrainTypeClass::slot6 | PASS | PASS(.?AVTerrainTypeClass@@) | FAIL(29B 薄转发 ③a，callee 仅返 0) | PASS(活vt 行外 0071DAF7) | 是 | 不成立 | 否 |
| 39 | 0071E360 | TerrainTypeClass::slot8 | PASS | PASS(.?AVTerrainTypeClass@@) | FAIL(间接 virtual call [edx+0x10] + cmp -1 不可字节伪证) | PASS(活vt 行外 0071DAF7) | 是 | 不成立 | 否 |
| 40 | 007220A0 | TiberiumClass::slot7 | PASS | PASS(.?AVTiberiumClass@@) | **PASS(③b② E_POINTER 判负，[vt+0x30] 取指针非流 I/O)** | PASS(活vt 行外 007217A6) | 是 | **成立** | **是** |
| 41 | 007220D0 | TiberiumClass::slot6 | PASS | PASS(.?AVTiberiumClass@@) | **PASS(③b② E_POINTER 判负，流写出)** | PASS(活vt 行外 007217A6) | 是 | **成立** | **是** |
| 42 | 007281A0 | TubeClass::slot5 | PASS | PASS(.?AVTubeClass@@) | **PASS(③b② E_POINTER 判负，流读入)** | PASS(活vt 行外 00727FFD) | 是 | **成立** | **是** |
| 43 | 007281E0 | TubeClass::slot6 | PASS | PASS(.?AVTubeClass@@) | FAIL(29B 薄转发 ③a，与 B2 005FEC10 同型) | PASS(活vt 行外 00727FFD) | 是 | 不成立 | 否 |
| 44 | 00728710 | TubeClass::slot8 | PASS | PASS(.?AVTubeClass@@) | FAIL(间接 virtual call [edx+0x10] + cmp -1 不可字节伪证) | PASS(活vt 行外 00727FFD) | 是 | 不成立 | 否 |
| 45 | 00763D90 | WaypointPathClass::slot6 | PASS | PASS(.?AVWaypointPathClass@@) | **PASS(③b② E_POINTER 判负，流写出)** | PASS(活vt 行外 0076375F) | 是 | **成立** | **是** |
| 46 | 00763E20 | WaypointPathClass::slot8 | PASS | PASS(.?AVWaypointPathClass@@) | FAIL(间接 virtual call [edx+0x10] + cmp -1 不可字节伪证) | PASS(活vt 行外 0076375F) | 是 | 不成立 | 否 |

## 逐行裁定依据（每行自身地址锚；字节见 `EVIDENCE/ROW_<entry>.txt`）

**② 10/10 全数钉住**：每行 entry 作 4B VA 在 `.rdata` 命中唯一槽，回扫 `[vt-4]=COL(sig=0)`、`[COL+0xC]=TD`、`TD+8` 名串，`slot offset/4 == 线索槽号`，槽值==entry。逐行另核各 vtable 的 slot0=`60 02 41 00`=0x00410260、slot1=`00 03 41 00`=0x00410300 ⇒ 确为对象主虚表，**未把小成员表 vtable 当主虚表**（陷阱③）。`Class` 名均来自 RTTI 名串而非 `slotN` 字面。

**③ 成立 5 行（各自独立站点、独立语义、独立 reason）**
- `0071E1D0` TerrainTypeClass::slot5（**流读入**）：call 0x5f9720@0x0071E1DB；test@0x0071E1E0；jl@0x0071E1E2；被调 0x5F9720 内 0x5F9847 call 0x410380（Read 槽）、0x5F984C cmp eax,ebx、0x5F984E jl 0x5F993E 失败原样返负 HRESULT，底层 0x00410389 mov eax,0x80004003=E_POINTER，成功 0x5F993C xor eax,eax 返 0；失败 pop esi;ret 8 早退，成功装 vt 0x7f5458 + 3 子表并逐项读入后返 0。与 B2 005FEAF0 同型。
- `007220A0` TiberiumClass::slot7（**非流 I/O，取数组指针**）：call 0x4103E0@0x007220AC；test@0x007220B1；jl@0x007220B3；被调 0x004103E0 空出参返 E_POINTER（0x004103E9）、正路 0x004103F8 call [eax+0x30] 取指针 +4 写回、0x00410407 xor eax,eax 返 0；正路本函数 mov [edi+0xd4]、lea ecx,[eax*4+4]、add/mov [esi] 前移指针后返 0，失败路原样返错误码。语义经 [vt+0x30] 而非流槽，**无读入/写出方向问题**（不会写反）。
- `007220D0` TiberiumClass::slot6（**流写出**）：call 0x410320@0x007220E1；test@0x007220E6；jl@0x007220E8；被调 0x00410320 的 0x0041032B mov eax,0x80004003=E_POINTER、0x00410348 call [eax+0x10]（Write 槽）；正路 0x00722101 call [edx+0x10] 写计数 + 0x0072210E 循环 0x0072211F call [ecx+0x10] 逐元素写 + 0x00722129 xor 返 0，失败路原样返错误码。与 B1 00483C10 同型。
- `007281A0` TubeClass::slot5（**流读入**）：call 0x410380@0x007281AB；test@0x007281B0；jl@0x007281B2；被调 0x00410380 的 0x00410389 E_POINTER、0x0041039E call [eax+0xc]（Read 槽）；正路 0x007281BA call 0x410170 base ctor + 0x007281BF 装 vt 0x7f59b0 + 3 子表 + 0x007281DA xor 返 0，失败路原样返错误码。
- `00763D90` WaypointPathClass::slot6（**流写出**）：call 0x410320@0x00763DA3；test@0x00763DA8；jl@0x00763DAA；正路 0x00763DBF call [edx+0x10] 写头（0x00763DC2 test/jl 二次校验）+ 0x00763DE1 call [ecx+0x10] 逐 0xc 字节写路点（0x00763DE4 test/jl 三次校验）+ 0x00763DF4 xor 返 0，失败路 0x00763DF6 弹栈原样返错误码。三处 call→test→jcc 目标各不同（直接 0x410320 + 两个不同间接写点），非「多路同一 call」。

**③ 失败 5 行（各自独立理由）**
- `0071E240` TerrainTypeClass::slot6：29B/11 insn 薄转发（call 0x5f9950; test; jl; xor eax,0; ret），零+默认 ③a；被调 profile 仅 consts={0}/n_rets=1，无可伪证错误码。与 B2 005FEC10 同型。
- `0071E360` TerrainTypeClass::slot8：站点 `call dword [edx+0x10]`@0x0071E3B9 为**间接虚调用**，callee=None，cmp eax,-1@0x0071E3BC 不可字节伪证被调返回约定；与 B2 005FEF30/006B4FA0/006B6160 同型。
- `007281E0` TubeClass::slot6：29B 薄转发 ③a（call 0x410320; test; jl; xor eax,0; ret），虽被调有 E_POINTER profile 但本行无实质分支动作。
- `00728710` TubeClass::slot8：间接 `call dword [edx+0x10]`@0x00728793 + cmp -1@0x00728796，不可字节伪证；cmp -1 后操作全局表 0x8b4148/0x8b413c 索引，非本对象错误码分支。
- `00763E20` WaypointPathClass::slot8：间接 `call dword [edx+0x10]`@0x00763E5A + cmp -1@0x00763E5D，不可字节伪证；后接全局表 0xb72618/0xb7260c 索引整理。

**读写方向核对（陷阱①）**：5 条成立行中 2 条是流读入（0071E1D0 经 0x5f9720→0x410380 的 [eax+0xc] Read 槽、007281A0 经 0x410380 的 [eax+0xc] Read 槽）、2 条是流写出（007220D0/00763D90 经 0x410320 的 [eax+0x10] Write 槽）、1 条（007220A0）非流 I/O（经 [vt+0x30] 取指针）——逐字节核定，未把流读入与流写出写反。

**④ 10/10 全数成立**：每行 vtable 均有行外非析构器构造器安装点，atexit=False、site 不共用。各安装点：TerrainTypeClass 0x7f5458→0071DAF7（ctor 0071DA80，base ctor 0x5f7090@0071DA89）；TiberiumClass 0x7f5728→007217A6（ctor 007216C0，base ctor 0x410800@007216CA）；TubeClass 0x7f59b0→00727FFD（ctor 00727FD0，base ctor 0x410170@00727FD5）；WaypointPathClass 0x7f6e70→0076375F（ctor 00763730，base ctor 0x410170@00763733）。㉓ 成对陷阱逐点排查：行内装载点（如 0071E1F4/007281BF/00763E26）与析构器写点均未用作 ④ 锚点。

## 与 S04 的败因对比（本批有多少行 ② 真的钉住了）

- S04 的 73 个命中**全部无名字（named=0）**，② 类身份取不到 ⇒ 36 行实测全败。
- 本批 10 行**全部有名字**（`Class::slotN`），经独立 RTTI 取证，**② 真钉住 10/10（100%）**——与 S04 的 0/36 形成鲜明对照，印证卡片「② 是硬约束、只打有名字候选」的前提。
- 但 ② 全钉住并不保证整体成立：③b② 成立 5/10（50%），败因集中在「29B 薄转发 ③a」「间接虚调用 + cmp -1 不可字节伪证」两类，属 ③ 的固有门槛，非身份问题。
- ②④ 不同源 10/10（②=.rdata RTTI 数据链，④=.text 构造安装指令）。

## 执行纪律留痕
- 先建目录、先写 REPORT 骨架 ✓
- 每核完一行立刻落盘 ✓（10 份 `EVIDENCE/ROW_<entry>.txt`，delta/base_rate/PROGRESS 同步）
- 每 5 行追加 `PROGRESS.md` ✓（#37–#41 / #42–#46 两段）
- 单行取证克制，只取四环锚点 ✓；每行独立 reason（无整批共用）✓
- 读写方向逐行核对（未写反）✓；小成员表 vtable 陷阱逐行排除（slot0=00410260）✓；㉓ 析构器锚点逐点排除 ✓
