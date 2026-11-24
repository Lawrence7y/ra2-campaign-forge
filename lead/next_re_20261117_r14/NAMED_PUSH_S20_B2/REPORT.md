# NAMED-PUSH — S20 B2 批次（有名字的 ③b② 候选，攻 proved 增量）

> 状态：**完成**。执行纪律已遵：先建目录 → 先写 REPORT 骨架 → 每核完一行立即落 `EVIDENCE/`；`PROGRESS.md` 每 5 行追加。
> 卡片：`lead\next_re_20261117_r14\_cards\NAMED-PUSH.md`（80 行全文读完）
> 子系统 **S20**；批次 **B2**（升序**第 19..36 个**，共 18 行，含两端）。
> 输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S20_B2\`

## 材料自校验

- 目标：`D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`
- SHA-256 实测：`73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` ⇒ **与卡片期望逐字一致**
- ImageBase `0x400000`；`.text = [0x401000, 0x7E038D)`（VirtualSize 逻辑边界）
- Python 3.12.10 / capstone 5.0.7（**skipdata=True**）/ pefile 2024.8.26；无 venv、未 pip install、未用 Ghidra
- 只读输入：`SURVEY_3B2\hits_detail.tsv`（仅当线索）、`W130_atlas\function_atlas.tsv`（仅取函数边界）。
  未改 `coverage.tsv` / `PANEL.md` / `R14_COMMON.md` / 台账 / `SURVEY_3B2` / `S04_PUSH_*`。写域仅本目录。

## 筛选命令

```powershell
$p = "D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv"
$rows = Import-Csv $p -Delimiter "`t"
$sel  = $rows | Where-Object { $_.subsystem -eq 'S20' -and $_.p3b2_named -eq 'True' } |
        Sort-Object { [Convert]::ToUInt32($_.entry,16) }
# 排除 fn_XXXXXXXX / sub_XXXXXXXX（含 Class::fn_/Class::sub_ 形式）
$clean = $sel | Where-Object { $_.name -notmatch '^(?:[A-Za-z0-9_<>@$?]*::)?(?:fn|sub)_[0-9A-Fa-f]{8}$' }
$b2 = $clean[18..35]   # 升序第 19..36 个（0-based 18..35），共 18
```

等价脚本落盘 `_work/filter_b2.py`（输出 `_work/b2_rows.json` / `b2_entries.txt`）。

结果：S20 共 43 行，其中 `p3b2_named=True` **38** 行（卡片记 38，一致）；`fn_`/`sub_` 伪名 **0** 行（S20 的 38 个 named 全是 `Class::slotN`/`Class::vslotN` 与真名，**没有一个**是 S14 那种地址式伪名）⇒ `clean` 仍 38 行，B2 = 升序第 19..36 行。

**B2 的 18 个 entry（升序）**：

```
0062D830  0062D9A0  0062E070  0062FE90  00630090  006447E0
00644960  00644F50  006457A0  00645950  006BF090  00749F30
0074B050  0074B810  0074B8D0  0074BA30  0074CE50  0075F7D0
```

## 判定口径（严格 D-40 / D-42 / D-46 / ㉓ / §12.3，宁严不宽）

1. **① 入口**：entry 在 `.text` 内、atlas 边界自洽、`skipdata=0`、末条 `ret`/`jmp`。
2. **② 类身份**（独立取证）：**整表枚举** `.rdata` 里所有「`[p]=COL → vt=p+4 → 连续 .text 指针」的虚表（共 1,212 张），按 RTTI 类名挑出与 `name` 栏同族那张，要求 `vt[slot] == entry`。`Class::slotN` 的类名只作线索，钉不死判 FAIL。**必须整表枚举，不能靠「回扫 vt-4..vt-N」猜槽号**（本批 slot122 大槽号，回扫窗口截断会静默误判）。
3. **③ 整体合同**：只认 ③b。③b② = 被调返回约定字节可伪证（`or eax,-1` / `mov eax,0x80004003` E_POINTER 等失败常量直接可见）**且**失败路径可达**且**两路动作不止返回值不同**且** `test|cmp` 与 `jcc` 零间隔（无 eax 覆写）；③b④ = 完整循环 + 边界检查 + 循环体内**非栈写**（禁止把被调内部的写当循环内非栈写）；③b① 跳表须每路可单独验证；③b③ 内存形状断言。禁 ③a 纯转发 / 单调用+单写 / 零+默认 / 无分支直线。指针 NULL / bool 主输出 / `operator new` 分配检查不计（D-46(A)）。
4. **④ 使用见证**：构造器安装的活表写点、行外、非 atexit（㉓ 成对陷阱）、与 ② 不同源；direct-only 不足。锚点落析构器判 FAIL。
5. **三陷阱**：eax 覆写、多路同一 call（细则#1）、模板假句，逐行排查。
6. **三已知陷阱（本批重点，逐行主动排查）**：
   - ① **流方向**：`0x410320` = **写出**（内部 `00410348`/`0041035E ff5010 call [eax+0x10]` = Write）、`0x410380` = **读入**（内部 `0041039E ff500c call [eax+0xC]` = Read）；本批 00630090/006457A0 逐字复算为**写出**，未照抄 B1 的「读入」结论。
   - ② **④ 锚落析构器判 FAIL**：8 个产出行 ④ 锚全部在构造器（宿主首条出向调用为基类构造 0x5F3900/0x5F7090），`atexit=False`、`in_self=False`，非 atexit 死表。
   - ③ **小成员表 vtable 不得当主虚表**：本批主虚表 slot0 普遍为 `00410260`（真主虚表标志）；唯一例外 `007F3780`（ClassFactory 5 槽真接口，slot0=006BEFD0）经核为独立工厂接口而非某对象的小成员表，其行（006BF090）③ 仍 FAIL，未误计。

## 基础率（诚实报数）

| 档 | 行数 | 口径 |
|---|---:|---|
| 本批行数 | **18** | S20 named=True 升序第 19..36 |
| ① 入口 PASS | **18** | 全部在 `.text`、`skipdata=0`、末条 `ret/jmp` |
| ② 类身份钉住 | **17** | 17/18 真虚表槽（整表枚举 + RTTI 名同族 + 槽号自洽）；第 21 行 Update_B 真名但 **0 虚表槽命中** |
| ③b 成立 | **8** | 7×③b② + 1×③b④ |
| ④ 使用见证成立 | **17** | 随 ②；17 行均有行外、非 atexit、构造器装的活表安装点 |
| **四环齐全** | **8** | rate = 8/18 = **0.4444** |

`base_rate.tsv`：`S20_B2	18	17	8	17	8	0.4444`

## 本批 18 行总表

| # | entry | name(原样) | ① | ② | ③ | ④ | ②④不同源 | 裁定 | 产出 |
|---:|---|---|---|---|---|---|---|---|---|
| 19 | 0062D830 | ParticleClass::slot122 | PASS | PASS(slot#123表内slot#122) | FAIL(方向枚举 0..7 switch；eax 覆写) | PASS(0062B767) | 是 | 不成立 | 否 |
| 20 | 0062D9A0 | ParticleClass::slot8 | PASS | PASS(slot#8 .?AVParticleClass@@) | **PASS(③b② Find -1 析构)** | PASS(0062B767) | 是 | **成立** | **是** |
| 21 | 0062E070 | ParticleSystemClass::Update_B | PASS | **FAIL(0 虚表槽，direct-only)** | —(②已败) | N/A | — | 不成立 | 否 |
| 22 | 0062FE90 | ParticleSystemClass::slot10 | PASS | PASS(slot#10) | **PASS(③b② 成员容器 Find -1)** | PASS(0062DD16) | 是 | **成立** | **是** |
| 23 | 00630090 | ParticleSystemClass::slot6 | PASS | PASS(slot#6) | **PASS(③b② 流写出 E_POINTER)** | PASS(0062DD16) | 是 | **成立** | **是** |
| 24 | 006447E0 | ParticleSystemTypeClass::slot5 | PASS | PASS(slot#5) | FAIL(被调 0x5F9720 恒返 0，jl 失败路不可达) | PASS(0064419C) | 是 | 不成立 | 否 |
| 25 | 00644960 | ParticleSystemTypeClass::slot8 | PASS | PASS(slot#8) | **PASS(③b② Find -1 析构)** | PASS(0064419C) | 是 | **成立** | **是** |
| 26 | 00644F50 | ParticleTypeClass::slot25 | PASS | PASS(slot#25) | FAIL(配置装载：指针 NULL/分配判 + bool 输出；3 循环 0 非栈写) | PASS(00644CF4) | 是 | 不成立 | 否 |
| 27 | 006457A0 | ParticleTypeClass::slot6 | PASS | PASS(slot#6) | **PASS(③b② 流写出 E_POINTER)** | PASS(00644CF4) | 是 | **成立** | **是** |
| 28 | 00645950 | ParticleTypeClass::slot8 | PASS | PASS(slot#8) | **PASS(③b② 双注册表 Find -1)** | PASS(00644CF4) | 是 | **成立** | **是** |
| 29 | 006BF090 | T_TClassFactory_VWaveClass__::slot3 | PASS | PASS(slot#3 ClassFactory 真接口) | FAIL(COM CreateInstance：NULL/状态/分配检查) | PASS(006BEFC9) | 是 | 不成立 | 否 |
| 30 | 00749F30 | VoxelAnimClass::slot23 | PASS | PASS(slot#23 .?AVVoxelAnimClass@@) | **PASS(③b④ 8 邻域循环+非栈写)** | PASS(00749434) | 是 | **成立** | **是** |
| 31 | 0074B050 | VoxelAnimTypeClass::slot25 | PASS | PASS(slot#25) | FAIL(配置装载：指针 NULL/分配判；0 回边) | PASS(0074AE6B) | 是 | 不成立 | 否 |
| 32 | 0074B810 | VoxelAnimTypeClass::slot5 | PASS | PASS(slot#5) | FAIL(被调 0x5F9720 恒返 0，jl 失败路不可达) | PASS(0074AE6B) | 是 | 不成立 | 否 |
| 33 | 0074B8D0 | VoxelAnimTypeClass::slot6 | PASS | PASS(slot#6) | FAIL(29B 纯转发壳，仅返回归一化 ⇒ ③a) | PASS(0074AE6B) | 是 | 不成立 | 否 |
| 34 | 0074BA30 | VoxelAnimTypeClass::slot8 | PASS | PASS(slot#8) | **PASS(③b② 双注册表 Find -1)** | PASS(0074AE6B) | 是 | **成立** | **是** |
| 35 | 0074CE50 | VeinholeMonsterClass::slot23 | PASS | PASS(slot#23) | FAIL(状态机 4 路跳转表各路不可单独验证 + 数量判) | PASS(0074C443) | 是 | 不成立 | 否 |
| 36 | 0075F7D0 | WaveClass::slot6 | PASS | PASS(slot#6) | FAIL(首 stream-write 返回值未测/被覆写；循环写由被调完成) | PASS(0075EA3F) | 是 | 不成立 | 否 |

## 逐行裁定依据（每行用自己的地址锚；字节见 `EVIDENCE/ROW_<entry>.txt`）

### ② 17/18 —— 槽号由整表枚举复算，RTTI 名与 name 栏逐行一致

| entry | vt | 槽地址 | slot# | COL | TD | TD+8 名串 |
|---|---|---|---|---|---|---|
| 0062D830 | 007EF954 | 007EFB3C | 122 | 00807BE8 | 008366E8 | `.?AVParticleClass@@`（123 槽表） |
| 0062D9A0 | 007EF954 | 007EF974 | 8 | 00807BE8 | 008366E8 | 同上 |
| 0062E070 | — | — | — | — | — | **0 命中**（真名但非虚表槽） |
| 0062FE90 | 007EFB9C | 007EFBC4 | 10 | 00807CA0 | 00836748 | `.?AVParticleSystemClass@@` |
| 00630090 | 007EFB9C | 007EFBB4 | 6 | 00807CA0 | 00836748 | 同上 |
| 006447E0 | 007F00A8 | 007F00BC | 5 | 00808238 | 00836F18 | `.?AVParticleSystemTypeClass@@` |
| 00644960 | 007F00A8 | 007F00C8 | 8 | 00808238 | 00836F18 | 同上 |
| 00644F50 | 007F0188 | 007F01EC | 25 | 008082F0 | 008370D0 | `.?AVParticleTypeClass@@` |
| 006457A0 | 007F0188 | 007F01A0 | 6 | 008082F0 | 008370D0 | 同上 |
| 00645950 | 007F0188 | 007F01A8 | 8 | 008082F0 | 008370D0 | 同上 |
| 006BF090 | 007F3780 | 007F378C | 3 | 00809CB8 | 00840F98 | `.?AV?$TClassFactory@VWaveClass@@@@`（5 槽真接口） |
| 00749F30 | 007F6318 | 007F6374 | 23 | 0080CDF8 | 00845E50 | `.?AVVoxelAnimClass@@` |
| 0074B050 | 007F6548 | 007F65AC | 25 | 0080CEB0 | 00845E70 | `.?AVVoxelAnimTypeClass@@` |
| 0074B810 | 007F6548 | 007F655C | 5 | 0080CEB0 | 00845E70 | 同上 |
| 0074B8D0 | 007F6548 | 007F6560 | 6 | 0080CEB0 | 00845E70 | 同上 |
| 0074BA30 | 007F6548 | 007F6568 | 8 | 0080CEB0 | 00845E70 | 同上 |
| 0074CE50 | 007F66A8 | 007F6704 | 23 | 0080D048 | 008460E8 | `.?AVVeinholeMonsterClass@@` |
| 0075F7D0 | 007F6BF4 | 007F6C0C | 6 | 0080D418 | 00847EB0 | `.?AVWaveClass@@` |

每行 `vt[slot]` 的 4B 值逐字回读 = entry（EVIDENCE 内给出槽内 4B 原始字节与 `[vt-4]` COL 的 16 字节）。

### ④ 17/18 —— 行外、非 atexit、构造器安装

| entry | 采用锚 | 宿主 | 宿主首条基类构造 | 行内自装表（已排除） |
|---|---|---|---|---|
| 0062D830 / 0062D9A0 | 0062B767 | 0062B5E0 | 0062B5E9 `call 0x5F3900` | 0062D9A4 |
| 0062FE90 / 00630090 | 0062DD16 | 0062DC50 | 0062DC59 `call 0x5F3900` | — |
| 006447E0 / 00644960 | 0064419C | 006440A0 | 006440A9 `call 0x5F7090` | 00644804 / 00644966 |
| 00644F50 / 006457A0 / 00645950 | 00644CF4 | 00644BE0 | 00644BEB `call 0x5F7090` | 00645956 |
| 006BF090 | 006BEFC9 | 006BEFC0 | （工厂 ctor，4 条指令，首条 mov [eax+4],0） | — |
| 00749F30 | 00749434 | 007493B0 | 007493BE `call 0x5F3900` | — |
| 0074B050 / 0074B810 / 0074B8D0 / 0074BA30 | 0074AE6B | 0074AD80 | 0074AD89 `call 0x5F7090` | 0074BA36 |
| 0074CE50 | 0074C443 | 0074C420 | 构造器 | — |
| 0075F7D0 | 0075EA3F | 0075E950 | 构造器 | — |

- 每个宿主都核了 `push <宿主>; call 0x7C978A` ⇒ **atexit 全 False**（㉓ 成对陷阱不踩）。
- 5 处「行体内自装表」（0062D9A4 / 00644804 / 00644966 / 00645956 / 0074BA36）**全部显式排除**，没有一行拿自己当 ④。
- 第 21 行 Update_B 因 ② 为 0，④ N/A。

### ③ 成立 8 行（各自独立站点与语义）

- **`0062D9A0` ParticleClass::slot8（③b②）**：`0062D9EB call [0xA83DC8+0x10]` → `0062D9EE cmp eax,-1` / `0062D9F1 je`（零间隔）；命中路 `0062DA12 mov [ecx+eax*4-4],edx` 压缩 + `0062DA1E jl` 回边；`or eax,-1`@004E9F2C + `ret 4`@004E9F30；收尾 `call 0x5F3B80` 基类析构 + delete 标志释放。
- **`0062FE90` ParticleSystemClass::slot10（③b②）**：成员容器 `[this+0xBC]`（vtable 007E9D84 于 0062E244 装入）`0062FEBB call [edx+0x10]` → `0062FEBE cmp eax,-1` / `0062FEC1 je`（零间隔）+ 压缩写 `0062FED9` + `0062FEE2 jl`；`or eax,-1`@004E9F2C。
- **`00630090` ParticleSystemClass::slot6（③b②，流写出）**：`006300A2 call 0x410320`（内部 ff5010=Write；空参 0041032B E_POINTER 0x80004003）→ `006300A7 test` / `006300A9 jl`（零间隔）；失败带错误码收尾，成功路按 [edi+0xCC] 逐元素 `call [ecx+0x10]` 写出（`add`/`cmp`/`jl` 回边）。
- **`00644960` ParticleSystemTypeClass::slot8（③b②）**：容器 0xA83D68 `0064499A call [edx+0x10]` → `0064499D cmp eax,-1` / `006449A0 je`（零间隔）+ 压缩 `006449C1` + `jl`；`or eax,-1`@004EF00F；`call 0x5F7400` + delete 释放。
- **`006457A0` ParticleTypeClass::slot6（③b②，流写出）**：`006457B3 call 0x5F9950`（→0x410320 Write，空参 E_POINTER）→ `006457B8 test` / `006457BA jl`（零间隔）；成功路按 [ebx+0x2C8] 一次写出 + [ebx+0x2BC] 每 3 字节逐条 `call [ecx+0x10]`（`add edi,3`/`jl` 回边）。
- **`00645950` ParticleTypeClass::slot8（③b②，双注册表）**：0xB0F670 / 0xA83D98 各一个 Find -1 站点（`0064598D` / `006459D6` 零间隔）+ 压缩写 + `jl`；`or eax,-1`@004E056F/004EEDAF；基类析构 + delete 释放。
- **`00749F30` VoxelAnimClass::slot23（③b④）**：8 邻域扫描——读 `0074A385 call 0x5657A0`→判 `0074A395 test al`（0x4838E0）→**循环体内非栈写** `0074A48F c6861e01000000 mov byte [esi+0x11E],0`（堆对象，非栈槽/非被调内写）→推进 `0074A56A inc edi` / `0074A56B cmp edi,8` / `0074A572 jl 0x74A329` 带边界检查。读→判→写→推进齐备。
- **`0074BA30` VoxelAnimTypeClass::slot8（③b②，双注册表）**：0xB0F670 / 0xA8EB28 各一个 Find -1 站点（`0074BA6D` / `0074BAB6` 零间隔）+ 压缩写 + `jl`；`or eax,-1`@004E056F/004EE8EF；`call 0x5F7400` + delete 释放。

### ③ FAIL 10 行（逐行独立理由）

- `0062D830`：分支全是对 `0x75F230` 返回的方向枚举（0..7，`cmp eax,2/6/4/3/7`）做 switch，无错误码/失败常量；`0x6D2140` 的 al 未测且 eax 被下一 call 覆写（eax 覆写陷阱）。
- `0062E070`：② 已败（真名但 0 虚表槽，direct-only 方法）。
- `006447E0` / `0074B810`：`call 0x5F9720` 被调全函数 1 个 ret、ret 前 `005F993C xor eax,eax` ⇒ 恒返 0，`jl` 失败路静态不可达（同 S20_B1 的 00428800 负结果）。
- `00644F50` / `0074B050`：配置装载函数，站点全是 `0x528A10`/`0x7C8D20`/`0x7C8E17`/`0x514D0` 的指针 NULL、分配检查；00644F50 主输出 `al` bool（D-46(A)）；循环 0 非栈写；0074B050 0 回边。
- `006BF090`：COM CreateInstance——NULL 出参 `0x80070057`/状态 `0x80040110`/`0x7C8E17` 的 operator new 分配 NULL 判（B1 明示分配检查不作合同）；`call [eax]` 的 HRESULT 判无可伪证常量路径。
- `0074B8D0`：29B 纯转发壳（call 0x5F9950 → test/jl → xor eax,eax/ret），除返回归一化外无自身动作 ⇒ 卡面禁 ③a 纯转发（同 S20_B1 待裁行）。
- `0074CE50`：状态机——4 路跳转表（`jmp [eax*4+0x74D414]`）各例是状态转移，不满足「每路可单独验证」的可伪证合同；唯一站点 `call 0x426630` 返回剩余计数（非失败常量），`test/jne` 是数量判；2 个 jmp 驱动循环无「读→判→非栈写→推进」齐备。
- `0075F7D0`：`0075F7E2 call 0x410320`（写出）返回值未测——紧接 `mov ecx,[edi+0x200]` 后进入 `call [edx+0x10]`，机械筛把后续虚拟写的 test/jl 误当站点；首写出无零间隔判据；循环写由被调完成（0 非栈写）。

## 与 S04 的败因对比（这批有多少行 ② 真的钉住了）

- **S04**：73 个 ③b② 机械命中 **`p3b2_named=0`（全无名字）**——entry 作 4B VA 镜像 0 命中、无虚表槽、无可回扫 RTTI 链 ⇒ **② 物理不可得**，36 行实测全败。问题在候选池，不在判定。
- **本批 S20 B2**：38 个 named 候选里 **0 个** `fn_`/`sub_` 伪名；本批 18 行逐行整表枚举后 **② 17/18 钉住**（第 21 行 Update_B 是真名但不是虚表槽，0 命中），17 行的 `slot_no` 与 name 栏槽号**逐行自洽**。⇒ **② 从 S04 的 0 变成 17/18**。
- **瓶颈仍在 ③**：18 行里 10 行 ③ 不成立（2 行无槽/被调恒返 0 失败路不可达、2 行配置装载指针 NULL+bool、1 行 COM 分配检查、1 行纯转发壳、1 行状态机跳转表、1 行流写出返回值未测、1 行方向枚举 switch）。
- **② 的坑换了形态**：S20 难点是大槽号（本批 slot122）与「真名但非虚表槽」（Update_B）。整表枚举（1,212 张）才可靠；`Class::slotN` 之 `Class` 只作线索，RTTI 钉不死或 0 槽命中即 FAIL。

## 汇总

- rows_checked=18；①18/18；②**17**/18；③b 成立 **8**（7×③b② + 1×③b④）；④**17**/18；四环齐全 **8**（行 20/22/23/25/27/28/30/34），rate **8/18=0.4444**。
- 与 S20_B1（②18/18、③b7、四环 7）相比：B2 多一行无虚表槽（Update_B），③b 由 7 升至 8。
- `delta.tsv` 8 行，entry 大写 8 位十六进制无 `0x`，grade 全 `[已证]`，每行独立语义与证据路径；`selfcheck.py` 五项（格式/地址引用/reason 去重/四环标题/base_rate 自洽）**全通过，FAIL=0**。

## 输出清单

- `delta.tsv`（8 行四环齐全）
- `base_rate.tsv`（`S20_B2 18 17 8 17 8 0.4444`）
- `REPORT.md`（本文件）
- `PROGRESS.md`（每 5 行推进）
- `EVIDENCE/ROW_<entry>.txt` × 8（0062D9A0 / 0062FE90 / 00630090 / 00644960 / 006457A0 / 00645950 / 00749F30 / 0074BA30）
- `_work/`（filter_b2.py / core.py / survey.py / dump_rows.py / hosts.py / loops.py / containers.py / gen_evidence.py / gen_delta.py / selfcheck.py 及各中间产物）
