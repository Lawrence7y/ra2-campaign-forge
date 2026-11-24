# NAMED-PUSH — S16 + S21 B1 批次（有名字的 ③b② 候选，攻 proved 增量）

> 状态：**完成**（7/7 行全部核完；产出 3 行）。
> 卡片：`lead\next_re_20261117_r14\_cards\NAMED-PUSH.md`（全文 80 行读完）。
> 本批：`subsystem ∈ {S16, S21}` AND `p3b2_named == True`，**再排除地址式伪名 `fn_XXXXXXXX` / `sub_XXXXXXXX`**，按 entry 升序全取。
> S16 named=True **4** 行、S21 named=True **3** 行；**伪名 0 个** ⇒ 本批 **7 行全取**（池很小，宁严不宽，不为凑数放宽判据）。
> 输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S16S21_B1\`。

## 材料自校验
- 目标：`ra2youli\gamemd.exe`；现场复算 SHA-256 = `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（与期望值一致）。
- ImageBase `0x400000`；`.text = [0x401000, 0x7E038D)`（VirtualSize `0x3DF38D`）。
- capstone 5.0.7（**`skipdata=True`**）+ pefile 2024.8.26 / Python 3.12.10；无 venv、未 pip install、未用 Ghidra。
- 只读输入：`SURVEY_3B2\hits_detail.tsv`、`W130_atlas\function_atlas.tsv`（仅取函数边界）。未修改
  `coverage.tsv` / `PANEL.md` / `R14_COMMON.md` / 台账 / `SURVEY_3B2` / `S04_PUSH_*`；写域仅本批目录。

## 筛选命令（得到本批 7 个 entry）

```python
import csv
p = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv"
rows, dropped = [], []
with open(p, encoding="utf-8-sig") as f:
    for row in csv.DictReader(f, delimiter="\t"):
        if row["subsystem"] in ("S16", "S21") and row["p3b2_named"] == "True":
            n = row["name"]
            if n.startswith("fn_") or n.startswith("sub_"):   # 排除地址式伪名（② 物理不可得）
                dropped.append(row); continue
            rows.append(row)
rows.sort(key=lambda x: (x["subsystem"], int(x["entry"], 16)))
# 结果：named=True 共 7 行（S16 4 + S21 3），伪名 0 个 ⇒ 7 行全取（≤18 行配额）。
```

落盘 `work/filter_b1.py`（含候选回显）。候选 7 行：

| # | entry | sub | name（原样） | grade（原样） | size | n_insn |
|--:|---|---|---|---|---:|---:|
| 1 | 0046D000 | S21 | CampaignClass::slot5 | [静态推断] | 69 | 21 |
| 2 | 0046D050 | S21 | CampaignClass::slot6 | [静态推断] | 29 | 11 |
| 3 | 0046D090 | S21 | CampaignClass::slot8 | [静态推断] | 141 | 42 |
| 4 | 0053AE50 | S16 | PsyDom::Start | [静态推断] | 227 | 59 |
| 5 | 006CEF80 | S16 | SuperWeaponTypeClass::slot27 | [静态推断] | 94 | 35 |
| 6 | 0071A760 | S16 | TemporalClass::slot23 | [静态推断] | 944 | 323 |
| 7 | 0071B1B0 | S16 | TemporalClass::slot8 | [静态推断] | 134 | 40 |

## 判定口径（严格 D-40 / ㉓，宁严不宽）
1. **① 入口**：entry 在 `.text` 内、atlas 边界自洽、`skipdata` 空洞 = 0、末条 `ret`/`jmp` 落函数体内且末字节 == atlas_end。
2. **② 类身份**：独立取证——`.rdata` 中 entry 作 4B VA 的槽 → `[vt-4] = COL(sig=0)` → `[COL+0xC] = pTD`（**绝对 VA，非 RVA**）→ `TD+8` **内联**装饰名串（**非指针**）；要求 `(槽 - vt)/4 == 线索槽号`，且 vt[0] = `00410260`（主表判据）。`slotN` 的类名只是线索，钉不死判 FAIL。
3. **③ 整体合同**：只认 **③b**。本批成立形态均为 **③b②**：`call → test/cmp eax → jcc`，被调**静态钉死**，失败/成功返回可从字节伪证为**多值状态码**或 **Find 的 −1 下标约定**（`{0,1}` 布尔不算），调用方真拿它分支、两路动作真不同、`test` 与 `jcc` 间无 `eax` 覆写、非多路同一 call、非模板假句。
4. **④ 使用见证**：活虚表派发（构造器装的活表 + `vt[slot] == entry`），direct-only 不足，且**与 ② 不同源**。**㉓ 强制检查**：判 ④ 前**枚举该虚表全部 imm32 写点**，排除 (a) `push <fn>; call 0x7C978A`（atexit）注册的全局析构器体内的写、(b) 删除析构器体内的写（特征 `test byte ptr [esp+X],1` + `call 0x7C8B3D`）。
5. **三陷阱逐行排查**：`eax` 覆写 / 多路同一 call / 模板假句。

## 本批 7 行总表（entry / ②③④ / 是否产出）

| # | entry | sub | name（原样） | ① | ② | ③b | ④ | ②④独立 | 裁定 | 产出 |
|--:|---|---|---|---|---|---|---|---|---|---|
| 1 | 0046D000 | S21 | CampaignClass::slot5 | PASS | **PASS**(`.?AVCampaignClass@@`, slot#5) | **PASS**(③b② HRESULT/E_POINTER) | **PASS**(构造器 0046CB70) | 是 | **成立** | **是** |
| 2 | 0046D050 | S21 | CampaignClass::slot6 | PASS | PASS(同上, slot#6) | FAIL(纯转发+零默认 ⇒ ③a) | PASS | 是 | 不成立 | 否 |
| 3 | 0046D090 | S21 | CampaignClass::slot8 | PASS | **PASS**(slot#8) | **PASS**(③b② Find −1 下标) | **PASS**(构造器 0046CB70；㉓ 排除自身写点 0046D096) | 是 | **成立** | **是** |
| 4 | 0053AE50 | S16 | PsyDom::Start | PASS | **FAIL**(全镜像 4B 引用 0) | FAIL(malloc 空判断 ⇒ ③a) | FAIL(仅 1 direct caller，direct-only) | – | 不成立 | 否 |
| 5 | 006CEF80 | S16 | SuperWeaponTypeClass::slot27 | PASS | **PASS**(`.?AVSuperWeaponTypeClass@@`, slot#27) | FAIL(类型标签判定；两路均可返 0x46；被调未钉死) | PASS(构造器 006CE717；㉓ 排除 006CEFED) | 是 | 不成立 | 否 |
| 6 | 0071A760 | S16 | TemporalClass::slot23 | PASS | **PASS**(`.?AVTemporalClass@@`, slot#23) | FAIL(全函数无多值错误码约定) | PASS(构造器 0071A467；㉓ 排除 0071B1BD) | 是 | 不成立 | 否 |
| 7 | 0071B1B0 | S16 | TemporalClass::slot8 | PASS | **PASS**(slot#8) | **PASS**(③b② Find −1 下标) | **PASS**(构造器 0071A467；㉓ 排除自身写点 0071B1BD) | 是 | **成立** | **是** |

## 基础率（诚实报数）

分母 = 本批 7 行（S16/S21 的 named=True 且非伪名全部候选）。

| 档 | 行数 | 口径与行 |
|--:|---:|---|
| rows_checked | **7** | 全取 |
| ① 入口 PASS | **7** | 全部 `.text` 内、skipdata 空洞 0、末字节 == atlas_end |
| ② 类身份钉住 | **6** | 0046D000 / 0046D050 / 0046D090 / 006CEF80 / 0071A760 / 0071B1B0（均 RTTI 名串 + 槽号自洽 + 主表 vt[0]=00410260）；0053AE50 无虚表槽 |
| ③③b 成立 | **3** | 0046D000（HRESULT 判负）/ 0046D090、0071B1B0（Find −1 下标） |
| ④ 使用见证成立 | **6** | 有 ② 的 6 行均有非 atexit / 非删除析构器的构造器活表安装点；0053AE50 无表 ⇒ direct-only 不足 |
| **四环齐全** | **3** | rate = 3/7 = **0.4286** |

`base_rate.tsv`：`B1	7	6	3	6	3	0.4286`

## 逐行裁定依据（每行自身地址锚；完整字节见 `EVIDENCE/ROW_<entry>.txt`）

### 产出 3 行

**`0046D000` CampaignClass::slot5 —— ③b②（HRESULT/E_POINTER 判负）**
- ② 槽 `007E4A3C` = `00 D0 46 00` = 0046D000（vt `007E4A28` + 0x14 = slot#5，与线索 slot5 一致）→ `[vt-4]` `007E4A24` = COL `007FC920`（sig 0）→ pTD `0081B170`（绝对 VA）→ TD+8 内联串 `0081B178` = `.?AVCampaignClass@@`；vt[0] = `00410260` 主表。
- ③ `0046D00B e8 70 33 fa ff` call 0x410380 → `0046D010 85 c0` test eax,eax → `0046D012 7c 2d` jl 0x46D041。被调 `00410389 b8 03 40 00 80` = **E_POINTER 0x80004003**；`0041039E ff 50 0c` = IStream::Read 槽；`004103A3 7c 31` jl → `004103D6` 原样携负 HRESULT，成功路 `004103CD ff 55 0c` 的返回值即 eax ⇒ 失败负 HRESULT / 成功 0，**多值非布尔**。失败路 `0046D041 5e; c2 08 00` 原样返回不构造；成功路 `0046D01F e8 3c 39 fa ff` call 0x410960（基类构造）+ `0046D024 c7 06 28 4a 7e 00` 起装 4 张表，`0046D03F 33 c0` 返 0。两路动作真不同、无 eax 覆写、单一 call 站点。
- ④ 该表 5 个写点全部枚举：`0046CB70`(构造器 0046CB60) / `0046CC16`(0046CC0C) / `0046CEC6`(0046CE10 创建例程) / `0046D024`(本行自身体内，不可自证) / `0046D096`(删除析构器 0046D090 体内，㉓ 排除)。取 `0046CB70`——构造器 `0046CB60` 由 `006C02D1` 在 `006C02C1 call 0x7c8e17`(operator new 0x3a0) 后调用 ⇒ 堆活对象上装活表。②∥④ 不同源。

**`0046D090` CampaignClass::slot8 —— ③b②（容器 FindIndex 的 −1 下标哨兵）**
- ② 槽 `007E4A48` = `90 D0 46 00`（vt + 0x20 = slot#8）→ 同 COL/TD → `.?AVCampaignClass@@`，主表。
- ③ `0046D0CA ff 52 10` call [edx+0x10]（edx 取自全局容器 `00A83CF8` 的活 vptr）→ `0046D0CD 83 f8 ff` cmp eax,−1 → `0046D0D0 74 2d` je 0x46D0FF。**被调静态钉死**：`00A83CF8` 的 vptr 写点全镜像仅 2 处——`004E6EFD` 装 `007E9FE4`（RTTI `.?AV?$DynamicVectorClass@PAVCampaignClass@@@@`，活表），`004E6F28` 装 `007EA004`（RTTI `.?AV?$VectorClass@PAVCampaignClass@@@@`，位于 `004E6F20` 体内，而 `004E6EE2 push 0x4E6F20` + `004E6F16 call 0x7C978A` = atexit ⇒ **死表，㉓ 排除**）。活表 slot#4 = `004EC530`，体内 `004EC54F 83 c8 ff` = `or eax,0xffffffff` ⇒ 未找到 −1 / 找到返下标，**多值可伪证**。未找到路跳过搬移，找到路 `0046D0DF` 计数减一 + `0046D0F1 89 54 81 fc` 数组前移（非栈写）循环。
- ④ 该表 5 写点同上枚举；**本行入口自身即删除析构器**（`0046D106 test byte [esp+0xc],1` + `0046D10E call 0x7c8b3d` + `ret 4`），其体内写点 `0046D096` 按 ㉓ 排除；④ 锚点取行外构造器 `0046CB70`（operator new 0x3a0 后构造）⇒ ④ 成立且不触 ㉓。

**`0071B1B0` TemporalClass::slot8 —— ③b②（容器 FindIndex 的 −1 下标哨兵）**
- ② 槽 `007F51A0` = `B0 B1 71 00`（vt `007F5180` + 0x20 = slot#8）→ `[vt-4]` `007F517C` = COL `0080C328` → pTD `008445C8` → TD+8 `008445D0` = `.?AVTemporalClass@@`；vt[0] = `00410260`。
- ③ `0071B1E3 ff 52 10` → `0071B1E6 83 f8 ff` → `0071B1E9 74 2d` je。被调钉死：`00B0EC60` 的 vptr 写点仅 `0071A3ED`（活表 `007F5114` = `.?AV?$DynamicVectorClass@PAVTemporalClass@@@@`）与 `0071A418`（死表 `007F5134`，在 `0071A410` 体内，`0071A3D2 push 0x71A410` + `0071A406 call 0x7C978A` = atexit ⇒ ㉓ 排除）。活表 slot#4 = `0071B4D0`，`0071B4EF 83 c8 ff` ⇒ −1 哨兵。找到路 `0071B1F8` 计数减一 + `0071B20A 89 54 81 fc` 前移循环；未找到路跳过。
- ④ 该表 6 写点全部枚举：`0071A467`(构造器 0071A450) / `0071A501`(0071A4E0) / `0071A5AD`·`0071A5DD`(0071A4DA) / `0071A687`(0071A660) / `0071B1BD`(本行删除析构器体内，㉓ 排除)。取 `0071A467`——构造器由 `006C074C` 在 `006C073E call 0x7c8e17`(operator new 0x50) 后调用 ⇒ 堆活对象装活表。

### 不成立 4 行（逐行独立理由）

- **`0046D050` slot6 —— ② PASS / ③ FAIL**：本体仅 `0046D05F e8 bc 32 fa ff` call 0x410320 → `0046D064 85 c0` test → `0046D066 7c 02` jl → `0046D068 33 c0` xor eax,eax → `0046D06A c2 0c 00` ret。被调 0x410320 确有 E_POINTER(`0041032B b8 03 40 00 80`)/成功 0，但**本函数成功路只做 `xor eax,eax; ret`**，除归一化返回值外无任何动作 ⇒ 命中卡片禁用的 **③a「纯转发 + 零+默认」**。对照 S06_B1 `00483C10 CellClass::slot6`（同为 call 0x410320 判负）之所以成立，是其成功路 `00483C2B` 起经 Write 槽真写计数与逐元素；本行无此实质，故判 FAIL（不为凑数放宽）。
- **`0053AE50` PsyDom::Start —— ②③④ 全 FAIL**：全镜像以 4B VA 搜索 **0 命中**，无虚表槽、无可回扫 RTTI 链，名字为自由/静态函数名（非 `slotN`，无 Class 部分可钉）⇒ ② 物理不可得（与 S04 同类）。③ 唯一分支对是 `0053AEC4 e8 4e df 28 00` call `0x7C8E17`(operator new 0x1c8) → `0053AECC 85 c0` test → `0053AECE 74 21` je，即 **malloc 空判断（③a 明列禁用）**，非 ③b②。④ 仅 1 个 direct caller `006CCDE2`，无活虚表 ⇒ direct-only 不足。
- **`006CEF80` SuperWeaponTypeClass::slot27 —— ② PASS / ③ FAIL**：② 槽 `007F40FC`（vt `007F4090` + 0x6C = slot#27）→ COL `0080B6C8` → pTD `00842600` → `.?AVSuperWeaponTypeClass@@`，槽号与线索一致。③ 唯一分支对 `006CEF99 ff 50 2c` call [eax+0x2c] → `006CEF9C 83 f8 06` cmp eax,6 → `006CEF9F 75 28` jne：被调是**入参对象的未钉死虚调用**，`==6` 是**类型标签判定**而非错误码；且两路都能返回 `0x46`（`006CEFCA b8 46 00 00 00` 与 `006CEFD3` 起经 `[edi+0xbc]` 之后仍有 0x46 出口），返回约定不可伪证 ⇒ 不构成 ③b②。④ 该表 4 写点枚举（`006CE717` 在构造器 `006CE700`：`mov esi,ecx` + `call 0x410960` 基类构造 + 装 3 张表；`006CE74D`；`006CE83B` 在 `006CE800`；`006CEFED` 在删除析构器 `006CEFE0` ⇒ ㉓ 排除），无 atexit 写点 ⇒ ④ 成立（附注：构造器 `006CE700` 本身无 direct caller，活对象来源未在本批进一步钉死）。
- **`0071A760` TemporalClass::slot23 —— ② PASS / ③ FAIL**：② 槽 `007F51DC`（vt `007F5180` + 0x5C = slot#23）→ COL `0080C328` → `.?AVTemporalClass@@`。③ 全函数 323 条内所有「call → test/cmp eax → jcc」对逐条核过：`0071A985 83 f8 06`（类型标签）/ `0071A9A0 85 c0` jle（返回值计数）/ `0071A83B 3b c2` jle（GetTickCount 时间比较）/ `0071A8CA 3b c3` je 与 `0071A9C9 3b c3` je（operator new 与 Find 的空指针判断）/ `0071A88D 3b c3` jg（计时算术）——**无一为可伪证的多值错误码/返回约定**，故 ③ FAIL。④ 该表写点含构造器 `0071A467`（operator new 0x50 后）⇒ ④ 成立。

## 与 S04 的败因对比（本批有多少行 ② 真的钉住）

- **S04**：73 个 ③b② 机械命中 `p3b2_named = 0`（全无名字）——entry 作 4B VA 全镜像 0 命中、无虚表槽、无可回扫 RTTI 链 ⇒ **② 物理不可得**，36 行实测全败。② 是硬约束。
- **本批 S16+S21**：7 行里 **6 行 ② 被 RTTI + 虚表独立钉住**（槽号 100% 由字节复算并与线索 `slotN` 自洽：slot5/slot6/slot8/slot8/slot27/slot23），与 S04 的决定性差异完整复现（② 从 0 → **6/7 = 0.857**）。
- 差异去向：本批瓶颈**不在 ② 而在 ③**——有 ② 的 6 行里 3 行 ③ FAIL（1 行 ③a 纯转发、1 行类型标签判定、1 行全无错误码约定）；另 1 行（`0053AE50`）② 与 ③ 双双物理不可得，与 S04 同类。
- 结论：**② 真钉住 6 行，四环齐全 3 行（rate 0.4286）**。S21 三行全部 ② 钉住、2 行产出；S16 四行 3 行 ② 钉住、1 行产出。

## 方法学收获（可复用，供后续批次）
- **容器族 ③b② 的正确链**：`call [reg+0x10]` 先由全局容器地址（`00A83CF8` / `00B0EC60`）反查 vptr 写点，用 **㉓ 判活/死表**（活表在模块静态初始化函数里 `mov [global], vt`；死表在 `push <fn>; call 0x7C978A` 注册的全局析构器里）选出活表，再取 `vt[4]` 得 `FindIndex`，其 `or eax,0xffffffff` 就是 −1 下标约定的字节证据。两条候选表（派生/基类）在未找到时都返 −1，结论稳健。
- **`0x410380` / `0x410320` 家族**：`IStream::Read`(0xc) / `Write`(0x10) 槽 + 空参 E_POINTER `0x80004003` 的 HRESULT 助手；判 ③b② 时**必须核成功路是否除归一化外还有实质动作**——只在返回值上做 `xor eax,eax` 的是 ③a。

## 输出清单
- `REPORT.md`（本文件）、`PROGRESS.md`、`base_rate.tsv`、`delta.tsv`（**3 行**）
- `EVIDENCE/ROW_0046D000.txt`、`EVIDENCE/ROW_0046D090.txt`、`EVIDENCE/ROW_0071B1B0.txt`
- `work/`：`np_core.py`（复制自 S17_B1，SHA/`.text` 自校验通过）、`filter_b1.py`、`candidates.json`、`pass1.py`+`pass1.txt`、
  `vtables.py`+`vtables.txt`、`helpers.py`+`helpers.txt`、`callees.py`+`callees.txt`、`write_sites.py`+`write_sites.txt`、
  `ctxt.py`+`ctxt.txt`、`global_ctor.py`+`global_ctor.txt`、`sw_check.py`、`ring3_dump.py`、`gen_facts.py`+`facts_*.txt`、
  `write_delta.py`、`dis_<entry>.txt` × 7（全部只读目标、可复算）
