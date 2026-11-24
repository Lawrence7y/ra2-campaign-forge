# NAMED-PUSH — S06 B2 批次（有名字的 ③b② 候选，攻 proved 增量）

> 状态：**完成**。执行纪律已遵：先建目录 → 先写 REPORT 骨架 → 逐行核完即落 `EVIDENCE/`；每 5 行追加 `PROGRESS.md`。
> 卡片：`lead\next_re_20261117_r14\_cards\NAMED-PUSH.md`（全文 80 行读完）
> 本批：**B2** = `SURVEY_3B2\hits_detail.tsv` 中 `subsystem==S06` AND `p3b2_named==True`，**排除 `fn_XXXXXXXX` / `sub_XXXXXXXX` 伪名**，按 entry 升序取**第 19 到第 36 行**（18 行）。
> 输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S06_B2\`（卡片 `<你的子系统>`=S06、`<你的目录>`=本目录）。

## 材料自校验
- 目标：`ra2youli\gamemd.exe`；现场 `Get-FileHash -Algorithm SHA256` = `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` ⇒ **与卡片期望逐字一致**。
- ImageBase `0x400000`；`.text=[0x401000,0x7E038D)`（VirtualSize=0x3DF38D）。
- Python 3.12.10 / capstone 5.0.7（**skipdata=True**）/ pefile 2024.8.26；无 venv、未 pip install（现场核验）。
- 只读输入：`SURVEY_3B2\hits_detail.tsv`（仅当线索）、`W130_atlas\function_atlas.tsv`（仅取函数边界）。未改 `coverage.tsv` / `PANEL.md` / `R14_COMMON.md` / 台账 / `SURVEY_3B2` / `S04_PUSH_*`。写域仅本目录。

## 筛选命令（得到本批 18 个 entry）

```powershell
$p = "D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv"
$rows = Import-Csv $p -Delimiter "`t"
$sel = $rows | Where-Object {
    $_.subsystem -eq 'S06' -and $_.p3b2_named -eq 'True' -and
    $_.name -notmatch '^(fn|sub)_[0-9A-Fa-f]{8}$'
}
$sorted = $sel | Sort-Object { [Convert]::ToInt32($_.entry,16) }
$b2 = $sorted | Select-Object -Skip 18 -First 18
$b2 | Format-Table entry,subsystem,name,grade,size,n_call,n_site,n_valid,p3b2_named -AutoSize
```

等价 Python 落盘于 `_work/filter_b2.py`（`sorted(sel, key=int(entry,16))[18:36]`）。
结果：S06 `p3b2_named=True` 共 **46** 行（卡片记 46，一致），其中 `fn_`/`sub_` 伪名 **0** 行 ⇒ 剔后 46 行；B2 = entry 升序第 19–36 行（0-based `[18:36]`）。

## 本批 18 行（entry 升序 #19–#36）

| # | entry | name(原样) | grade | size | n_call | n_site | n_valid |
|---:|---|---|---|---:|---:|---:|---:|
| 19 | 005FEAF0 | OverlayTypeClass::slot5 | [静态推断] | 275 | 9 | 1 | 1 |
| 20 | 005FEC10 | OverlayTypeClass::slot6 | [静态推断] | 29 | 1 | 1 | 1 |
| 21 | 005FEF30 | OverlayTypeClass::slot8 | [静态推断] | 141 | 4 | 1 | 1 |
| 22 | 006B4FA0 | SmudgeClass::slot8 | [静态推断] | 167 | 5 | 1 | 1 |
| 23 | 006B5550 | SmudgeTypeClass::slot32 | [静态推断] | 105 | 2 | 2 | 1 |
| 24 | 006B55C0 | SmudgeTypeClass::slot35 | [静态推断] | 45 | 2 | 1 | 1 |
| 25 | 006B5850 | SmudgeTypeClass::slot5 | [静态推断] | 83 | 4 | 1 | 1 |
| 26 | 006B58B0 | SmudgeTypeClass::slot6 | [静态推断] | 29 | 1 | 1 | 1 |
| 27 | 006B6160 | SmudgeTypeClass::slot8 | [静态推断] | 172 | 5 | 1 | 1 |
| 28 | 006BF210 | T_TClassFactory_VTerrainTypeClass__::slot3 | [静态推断] | 119 | 4 | 1 | 1 |
| 29 | 006BF390 | T_TClassFactory_VTerrainClass__::slot3 | [静态推断] | 117 | 4 | 1 | 1 |
| 30 | 0071B920 | TerrainClass::slot91 | [静态推断] | 615 | 14 | 2 | 2 |
| 31 | 0071C1B0 | TerrainClass::slot69 | [静态推断] | 429 | 8 | 1 | 1 |
| 32 | 0071C730 | TerrainClass::slot23 | [静态推断] | 428 | 8 | 1 | 1 |
| 33 | 0071CDA0 | TerrainClass::slot5 | [静态推断] | 398 | 8 | 1 | 1 |
| 34 | 0071DDD0 | TerrainTypeClass::slot32 | [静态推断] | 49 | 2 | 2 | 1 |
| 35 | 0071DE10 | TerrainTypeClass::slot35 | [静态推断] | 43 | 2 | 1 | 1 |
| 36 | 0071DEA0 | TerrainTypeClass::slot25 | [静态推断] | 545 | 17 | 1 | 1 |

## 判定口径（严格 D-40，宁严不宽；沿用 S06 B1 同套方法）
1. **①入口**：entry 在 `.text` 内、atlas 边界自洽、反汇编 `skipdata=True`（skipdata=0 表示无数据字节被误当指令）。
2. **②类身份**：`.rdata` 中 entry 作 4B VA 命中的槽 → 回扫 `[vt-4]=COL(sig=0)` → `[COL+0xC]=TD` → `TD+8` 名串，且 `slot offset/4 == 线索槽号`。`Class` 部分仅作线索，钉不死判 FAIL。高槽号 slot91/slot69 须把回扫上限从 40 提到 140 才命中 COL，已逐行核实。
3. **③整体合同**：只认 ③b②——被调返回约定**可从字节伪证**（imm 哨兵/错误码；bool 0/1 与零判断不算，D-46(A)）+ **调用方真的拿它分支** + 两路动作真不同 + test 与 jcc 之间无 eax 覆写 + 单 call 非多路同一 call。禁止把「被调用者内部的写」当循环内非栈写；禁止 ③a 形态（薄转发/零+默认/模板假句）。
4. **④使用见证**：活 vtable 槽位形态 = 构造器装的活表 + `vt[slot]==entry` + 写点在行外 + site 不共用；`atexit` 析构器写的表不算活 vptr（㉓ 成对陷阱：④ 锚点若落在析构器里判 FAIL）。逐点用字节区分构造器（base-ctor call + field init）与析构器（全局表注销 / push 1;call [vtable]）。
5. **②④不同源**：② 锚在 `.rdata` 的 RTTI 描述符字节链，④ 锚在 `.text` 的构造安装指令字节；两者地址与段均不同，不共用 site。
6. **三陷阱**逐行排查：eax 覆写、多路同一 call、模板假句。
7. **读写方向**：`call 0x410380` 经 `[eax+0xC]`（Read 槽）= 流读入；`call 0x410320` 经 `[eax+0x10]`（Write 槽）= 流写出；one_line_semantics 必须与实际字节方向一致，写反判 FAIL。本批 3 条 PASS 均为流读入，方向已逐字节核对未写反。

## 基础率（诚实报数）

| 档 | 行数 | 口径 |
|---|---:|---|
| 本批行数 | 18 | S06 named=True 剔伪名后 entry 升序第 19–36 |
| ①入口 PASS | 18 | 全部 in_text、skipdata=0、atlas 边界自洽 |
| ②类身份钉住 | **18** | 18/18 均有 RTTI 名串与线索类名一致、`slot offset/4 == 线索槽号`、槽值==entry |
| ③③b② 成立 | **3** | 005FEAF0 / 006B5850 / 0071CDA0 |
| ④使用见证成立 | **18** | 18/18 均有行外非析构器构造器安装点 |
| **四环齐全** | **3** | 上列 3 行，rate = 3/18 = 0.1667 |

`base_rate.tsv`：`B2  18  18  3  18  3  0.1667`

## 本批 18 行总表（entry / ②③④ / 是否产出）

| # | entry | name(原样) | ①入口 | ②类身份 | ③③b | ④使用见证 | ②④不同源 | 裁定 | 产出 |
|---:|---|---|---|---|---|---|---|---|---|
| 19 | 005FEAF0 | OverlayTypeClass::slot5 | PASS | PASS(.?AVOverlayTypeClass@@) | **PASS(③b② E_POINTER 判负，流读入)** | PASS(活vt 行外 005FE2F1) | 是 | **成立** | **是** |
| 20 | 005FEC10 | OverlayTypeClass::slot6 | PASS | PASS(.?AVOverlayTypeClass@@) | FAIL(29B 薄转发 ③a) | PASS(活vt 行外 005FE2F1) | 是 | 不成立 | 否 |
| 21 | 005FEF30 | OverlayTypeClass::slot8 | PASS | PASS(.?AVOverlayTypeClass@@) | FAIL(call [edx+0x10] 间接，cmp -1 不可伪证) | PASS(活vt 行外 005FE2F1) | 是 | 不成立 | 否 |
| 22 | 006B4FA0 | SmudgeClass::slot8 | PASS | PASS(.?AVSmudgeClass@@) | FAIL(间接 call -1 不可伪证) | PASS(活vt 行外 006B4A5C) | 是 | 不成立 | 否 |
| 23 | 006B5550 | SmudgeTypeClass::slot32 | PASS | PASS(.?AVSmudgeTypeClass@@) | FAIL(0x7c8e17 分配零判断) | PASS(活vt 行外 006B529B) | 是 | 不成立 | 否 |
| 24 | 006B55C0 | SmudgeTypeClass::slot35 | PASS | PASS(.?AVSmudgeTypeClass@@) | FAIL(0x7c8e17 分配零判断) | PASS(活vt 行外 006B529B) | 是 | 不成立 | 否 |
| 25 | 006B5850 | SmudgeTypeClass::slot5 | PASS | PASS(.?AVSmudgeTypeClass@@) | **PASS(③b② E_POINTER 判负，流读入)** | PASS(活vt 行外 006B529B) | 是 | **成立** | **是** |
| 26 | 006B58B0 | SmudgeTypeClass::slot6 | PASS | PASS(.?AVSmudgeTypeClass@@) | FAIL(29B 薄转发 ③a) | PASS(活vt 行外 006B529B) | 是 | 不成立 | 否 |
| 27 | 006B6160 | SmudgeTypeClass::slot8 | PASS | PASS(.?AVSmudgeTypeClass@@) | FAIL(间接 call -1 不可伪证) | PASS(活vt 行外 006B529B) | 是 | 不成立 | 否 |
| 28 | 006BF210 | T_TClassFactory_VTerrainTypeClass__::slot3 | PASS | PASS(.?AV?$TClassFactory@VTerrainTypeClass@@@@) | FAIL(工厂 CreateInstance：分配零判断+QI 间接不可伪证) | PASS(活vt 行外 006BF149) | 是 | 不成立 | 否 |
| 29 | 006BF390 | T_TClassFactory_VTerrainClass__::slot3 | PASS | PASS(.?AV?$TClassFactory@VTerrainClass@@@@) | FAIL(工厂，同 006BF210) | PASS(活vt 行外 006BF2C9) | 是 | 不成立 | 否 |
| 30 | 0071B920 | TerrainClass::slot91 | PASS | PASS(.?AVTerrainClass@@，slot#91 扩展回扫) | FAIL(0x5f5390 cmp 5/4 状态分派+分配零判断) | PASS(活vt 行外 0071B7BC) | 是 | 不成立 | 否 |
| 31 | 0071C1B0 | TerrainClass::slot69 | PASS | PASS(.?AVTerrainClass@@，slot#69 扩展回扫) | FAIL(间接 call [edx+0x6c]+零判断) | PASS(活vt 行外 0071B7BC) | 是 | 不成立 | 否 |
| 32 | 0071C730 | TerrainClass::slot23 | PASS | PASS(.?AVTerrainClass@@) | FAIL(0x426630 返回 0/非0 零判断 D-46(A)) | PASS(活vt 行外 0071B7BC) | 是 | 不成立 | 否 |
| 33 | 0071CDA0 | TerrainClass::slot5 | PASS | PASS(.?AVTerrainClass@@) | **PASS(③b② E_POINTER 判负，流读入)** | PASS(活vt 行外 0071B7BC) | 是 | **成立** | **是** |
| 34 | 0071DDD0 | TerrainTypeClass::slot32 | PASS | PASS(.?AVTerrainTypeClass@@) | FAIL(0x7c8e17 分配零判断) | PASS(活vt 行外 0071DAF7) | 是 | 不成立 | 否 |
| 35 | 0071DE10 | TerrainTypeClass::slot35 | PASS | PASS(.?AVTerrainTypeClass@@) | FAIL(0x7c8e17 分配零判断) | PASS(活vt 行外 0071DAF7) | 是 | 不成立 | 否 |
| 36 | 0071DEA0 | TerrainTypeClass::slot25 | PASS | PASS(.?AVTerrainTypeClass@@) | FAIL(间接 call [edx+0x9c] 零判断 + 0x5f92d0 al bool D-46(A)) | PASS(活vt 行外 0071DAF7) | 是 | 不成立 | 否 |

## 逐行裁定依据（每行自身地址锚；字节见 `EVIDENCE/ROW_<entry>.txt`）

**② 18/18 全数钉住**（与 S04 相反，见下节）：每行 entry 作 4B VA 在 `.rdata` 命中唯一槽，回扫 `[vt-4]=COL(sig=0)`、`[COL+0xC]=TD`、`TD+8` 名串，`slot offset/4 == 线索槽号`，槽值==entry（verify_ring2.py 逐行核 MATCH）。高槽号 `0071B920`(slot#91, off +0x16c)、`0071C1B0`(slot#69, off +0x114) 的 COL 距槽 364B/276B，把回扫上限从默认 40 提到 140 才命中，已逐行核实名串 `.?AVTerrainClass@@` 与槽号自洽。所有 18 行的 `Class` 名均来自 RTTI 名串而非 `slotN` 字面。

**③ 成立 3 行（各自独立站点与语义）**
- `005FEAF0` OverlayTypeClass::slot5（流读入）：站点 call 0x5f9720@0x005FEB04；test eax,eax@0x005FEB09；jl@0x005FEB0B。被调 0x005F9720 0x005F9847 call 0x410380（Read 槽）、0x005F984C cmp eax,ebx(0)→0x005F984E jl 失败返负 HRESULT，成功 0x005F993C xor eax,eax 返 0，E_POINTER 约定字节伪证。失败 jl→弹栈 ret 8 原样返 HRESULT；成功装 vt 0x7ef600@0x005FEB21 + 真实装载 + xor 返 0。与 B1 004839F0 同型。
- `006B5850` SmudgeTypeClass::slot5（流读入）：站点 call 0x5f9720@0x006B585B；test@0x006B5860；jl@0x006B5862；被调同上；失败原样返 HRESULT，成功装 vt 0x7f3528@0x006B5874 + 装载 + xor 返 0。
- `0071CDA0` TerrainClass::slot5（流读入）：站点 call 0x5f5e80@0x0071CE79；mov edi,eax@0x0071CE7E；test edi,edi@0x0071CE80；jl@0x0071CE82。被调 0x005F5E80 0x005F5E8B call 0x410380、0x005F5E92 jl 失败返负 HRESULT，成功 0x005F5EF7 xor 返 0。失败 mov eax,edi 原样返；成功装 vt 0x7f522c@0x0071CE98 + ff 51 10（Read）读入 + 登记全局表 + 返 0。属「模板级低信息量 ③b②」，严格符合卡面「失败返什么/成功返什么/调用方拿它分支」的字面要求。
- 三条都是「被调内部经 0x410380 的 [eax+0xc] Read 槽读入、失败返负 HRESULT」——读写方向逐字节核定为流读入，未写反。

**③ 失败 15 行**（各自独立理由，详见 EVIDENCE）：29B 薄转发 ③a（005FEC10/006B58B0，与 B1 005439F0 同型）；间接虚调用 + cmp -1 不可伪证（005FEF30/006B4FA0/006B6160）；0x7c8e17 分配器零判断 D-46(A)（006B5550/006B55C0/0071DDD0/0071DE10）；COM 工厂 CreateInstance 无可伪证 callee 错误码（006BF210/006BF390）；状态码 5/4 分派非错误哨兵（0071B920）；间接 call + 零判断（0071C1B0）；0x426630 返回 0/非0 零判断（0071C730）；间接零判断 + 0x5f92d0 的 al 布尔 0/1（0071DEA0）。

**④ 18/18 全数成立**：每行 vtable 均有行外非析构器构造器安装点，atexit=False、site 不共用。各 vtable 安装点：OverlayTypeClass 0x7ef600→005FE2F1（ctor 005FE250，base ctor 0x5f7090@005FE259）；SmudgeClass 0x7f32fc→006B4A5C（ctor 006B4A50，base ctor 0x5f3900@006B4A53）；SmudgeTypeClass 0x7f3528→006B529B（ctor 006B5260，base ctor 0x5f7090@006B5269）；TClassFactory<VTerrainTypeClass> 0x7f3798→006BF149（ctor 006BF140）；TClassFactory<VTerrainClass> 0x7f37b0→006BF2C9（ctor 006BF2C0）；TerrainClass 0x7f522c→0071B7BC（ctor 0071B7B0，另有 0071BBFF/0071BE5A 带 base ctor 0x5f3900 佐证）；TerrainTypeClass 0x7f5458→0071DAF7（ctor 0071DA80，base ctor 0x5f7090@0071DA89）。㉓ 成对陷阱逐点排查：行内装载点（如 005FEB21/006B5874/006B616A）与析构器写点均未用作 ④ 锚点。

## 与 S04 的败因对比（本批有多少行 ② 真的钉住了）

- S04 的 73 个命中**全部无名字（named=0）**，② 类身份取不到 ⇒ 36 行实测全败。
- 本批 18 行**全部有名字**（`Class::slotN` 及 `T_TClassFactory_*`），经独立 RTTI 取证，**② 真钉住 18/18（100%）**——与 S04 的 0/36 形成鲜明对照，印证卡片「② 是硬约束、只打有名字候选」的前提。
- 但 ② 全钉住并不保证整体成立：③b② 只成立 3/18（16.67%），败因集中在「间接虚调用不可伪证」「29B 薄转发 ③a」「分配器/零判断 D-46(A)」「工厂/QI 返回约定不可字节伪证」四类，属 ③ 的固有门槛，非身份问题。
- ②④ 不同源 18/18（②=.rdata RTTI 数据链，④=.text 构造安装指令）。

## 执行纪律留痕
- 先建目录、先写 REPORT 骨架 ✓
- 每核完一行立刻落盘 ✓（18 份 `EVIDENCE/ROW_<entry>.txt`，delta/base_rate/PROGRESS 同步）
- 每 5 行追加 `PROGRESS.md` ✓（1–5 / 6–10 / 11–15 / 16–18 四段）
- 单行取证克制，只取四环锚点 ✓；每行独立 reason（无整批共用）✓
- 读写方向逐行核对（3 条 PASS 均为流读入，未写反）✓；㉓ 析构器锚点逐点排除 ✓
