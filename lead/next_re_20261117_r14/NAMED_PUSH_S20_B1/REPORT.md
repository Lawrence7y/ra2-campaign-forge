# NAMED-PUSH — S20 B1 批次（有名字的 ③b② 候选，攻 proved 增量）

> 状态：**完成**。执行纪律已遵：先建目录 → 先写 REPORT 骨架 → 每核完一行立即落 `EVIDENCE/`；`PROGRESS.md` 每 5 行追加。
> 卡片：`lead\next_re_20261117_r14\_cards\NAMED-PUSH.md`（80 行全文读完）
> 子系统 **S20**；批次 **B1**。
> 本批 = `SURVEY_3B2\hits_detail.tsv` 中 `subsystem==S20` 且 `p3b2_named==True`、**排除 `fn_XXXXXXXX`/`sub_XXXXXXXX` 伪名**，按 entry 升序取**前 18 个**。
> 输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S20_B1\`

## 材料自校验

- 目标：`D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`
- SHA-256 实测：`73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` ⇒ **与卡片期望逐字一致**
- ImageBase `0x400000`；`.text = [0x401000, 0x7E038D)`（用 **VirtualSize** `0x3DF38D` 作逻辑边界，不是 raw size `0x3E0000` —— 见 `_work/core.py` 的 `TEXT_END`）
- Python 3.12.10 / capstone 5.0.7（**skipdata=True**）/ pefile 2024.8.26；无 venv、未 pip install、未用 Ghidra
- 只读输入：`SURVEY_3B2\hits_detail.tsv`（仅当线索）、`W130_atlas\function_atlas.tsv`（仅取函数边界）。
  未改 `coverage.tsv` / `PANEL.md` / `R14_COMMON.md` / 台账 / `SURVEY_3B2` / `S04_PUSH_*`。写域仅本目录。

## 筛选命令

```powershell
$p = "D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv"
$rows = Import-Csv $p -Delimiter "`t"
$sel  = $rows | Where-Object { $_.subsystem -eq 'S20' -and $_.p3b2_named -eq 'True' } |
        Sort-Object { [Convert]::ToInt32($_.entry,16) }
# 排除 fn_XXXXXXXX / sub_XXXXXXXX（含 Class::fn_/Class::sub_ 形式）
$clean = $sel | Where-Object { $_.name -notmatch '^(?:[A-Za-z0-9_<>@$?]*::)?(?:fn|sub)_[0-9A-Fa-f]{8}$' }
$b1 = $clean[0..17]   # 升序前 18
```

结果：S20 共 43 行，其中 `p3b2_named=True` **38** 行（卡片记 38，一致）；
`fn_`/`sub_` 伪名 **0** 行（S20 的 38 个 named 全是 `Class::slotN` / `Class::vslotN` 占位名形态，**没有一个**是 S14 那种地址式伪名）
⇒ `clean` 仍 38 行，B1 = 升序第 1..18 行。等价脚本落盘 `_work/filter_b1.py`（输出 `_work/b1_rows.json`）。

**B1 的 18 个 entry（升序）**：

```
00423AC0  00427B50  00427D00  00428800  00428970  00428C30
00428EA0  004A7340  004A7C90  004C5A30  004C5A80  004C5AC0
005F44A0  005F4870  005F5390  005F5940  005F9970  0062D7A0
```

## 判定口径（严格 D-40 / D-42 / D-46 / ㉓ / §12.3，宁严不宽）

1. **① 入口**：entry 在 `.text` 内、atlas 边界自洽、`skipdata=0`、末条为 `ret`/`jmp`。
2. **② 类身份**（独立取证）：**整表枚举** `.rdata` 里所有「`[p]=COL → vt=p+4 → 连续 .text 指针」的虚表
   （共 **1,212** 张），再按 RTTI 类名挑出与 `name` 栏同族那张，要求 `vt[slot] == entry`。
   `Class::slotN` 的类名部分**只作线索**，钉不死判 FAIL。
   > 方法更正（对比前批）：**不能靠「回扫 vt-4..vt-N」猜槽号**。S20 有 slot84/75/91 这类大槽号，回扫窗口一截断就会误判「无 RTTI 槽」（我第一版按 k≤64 回扫，`005F44A0`/`005F4870`/`005F5390` 三个 ② 全被误判为 0）。改成整表枚举后 18/18 全部钉住。
3. **③ 整体合同**：**只认 ③b**。本批成文并逐行照用的判据：
   - **③b② 成立** = 被调返回约定**字节可伪证**（失败常量直接可见：`or eax,-1` / `mov eax,0x80004003` / 负 HRESULT）
     **且**该失败路径**可达**（不是死分支）**且**两路**动作不止返回值不同**（构造 / 压缩写 / 释放 / 循环）
     **且** `test|cmp` 与 `jcc` **零间隔**（无 eax 覆写）。
   - **纯「参数转发 + 返回归一化」**（函数体只有 arg shuffle + `call` + `test/jcc` + `xor eax,eax` + `ret`）判 **③a**（卡面禁「纯转发」）。
   - **指针 NULL / bool 主输出**一律不计（D-46(A)「bool 主输出不算」的同类）。
   - ③b① 跳表：本批 18 行 **0 个**（`_work/loops.py` 全扫，`jmp [reg*4+disp]` 零命中）。
4. **④ 使用见证**：活虚表形态 —— `vt[slot]==entry` + **构造器**安装点（`mov [reg], vt`；宿主首条出向调用是基类构造）。
   - ㉓：`push <f>; call 0x7C978A` 的 atexit 析构器写的表**不算**活表。本批逐行核过每个宿主，`atexit` 全 `False`。
   - **锚点落在本行体内 ⇒ 不算**（写点须在行外）。本批 **6** 行的行体内确有自装表
     （`00428831`/`00428EAD`/`004A7C9D`/`004C5A54`/`004C5AC4`/`0062D7C4`，各属第 4/7/9/10/12/18 行），
     全部**已按 `in_self=True` 排除**，另取行外构造点。
   - direct-only 不足：本批 7 个产出行里 5 行 direct call = 0（纯虚派发），不靠 direct。
5. **②④ 不同源**（§12.3）：② 锚 `.rdata` 的 COL/TD 描述符与槽内 4B 值；④ 锚 `.text` 的装表指令字节。段与产物都不同，不复用同一槽值顶两环。
6. **流方向**：`0x410320` = **写出**（内部 `00410348`/`0041035E ff5010 call [eax+0x10]`）、
   `0x410380` = **读入**（内部 `0041039E ff500c call [eax+0xC]`）、`0x4103E0` = 记录流位置（`call [eax+0x30]` 后写 `dest[0]=tell+4`）。
   **逐行按实际槽位复算，未照抄前批结论**（S14 那两行就栽在这）。
7. 三陷阱逐行排查：`eax` 覆写、多路同一 call（细则#1）、模板假句。

## 基础率（诚实报数）

| 档 | 行数 | 口径 |
|---|---:|---|
| 本批行数 | **18** | S20 named=True 升序前 18 |
| ① 入口 PASS | **18** | 全部在 `.text`、`skipdata=0`、末条 `ret/jmp` |
| ② 类身份钉住 | **18** | 18/18 全是真虚表槽（整表枚举 + RTTI 名与 name 栏同族 + 槽号自洽） |
| ③b 成立 | **7** | 6×③b② + 1×③b④ |
| ④ 使用见证成立 | **18** | 18/18 都有行外、非 atexit、构造器装的活表安装点 |
| **四环齐全** | **7** | rate = 7/18 = **0.3889** |

`base_rate.tsv`：`S20_B1	18	18	7	18	7	0.3889`

## 本批 18 行总表

| # | entry | name(原样) | ① | ② | ③ | ④ | ②④不同源 | 裁定 | 产出 |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | 00423AC0 | AnimClass::vslot23 | PASS | PASS(slot#23 .?AVAnimClass@@) | **PASS(③b④ 半径双层循环)** | PASS(0042201C) | 是 | **成立** | **是** |
| 2 | 00427B50 | AnimTypeClass::vslot40 | PASS | PASS(slot#40) | FAIL(仅指针 NULL + `cmp eax,6` 状态枚举) | PASS(00427731) | 是 | 不成立 | 否 |
| 3 | 00427D00 | AnimTypeClass::vslot25 | PASS | PASS(slot#25) | FAIL(26 站点全为 new/free 指针 NULL；3 个循环仅栈写) | PASS(00427731) | 是 | 不成立 | 否 |
| 4 | 00428800 | AnimTypeClass::vslot5 | PASS | PASS(slot#5) | FAIL(被调 `005F9720` 单出口恒 0，`jl` 失败路**静态不可达**) | PASS(00427731) | 是 | 不成立 | 否 |
| 5 | 00428970 | AnimTypeClass::vslot6 | PASS | PASS(slot#6) | 待裁(29 B 纯转发 + 返回归一化) | PASS(00427731) | 是 | 不成立(从严) | 否 |
| 6 | 00428C30 | AnimTypeClass::vslot39 | PASS | PASS(slot#39) | FAIL(`004A3890` 返 0/指针，指针 NULL 判；两 cmp 汇入同一 call 仅参数不同) | PASS(00427731) | 是 | 不成立 | 否 |
| 7 | 00428EA0 | AnimTypeClass::vslot8 | PASS | PASS(slot#8) | **PASS(③b② Find -1 ×2)** | PASS(00427731) | 是 | **成立** | **是** |
| 8 | 004A7340 | DiskLaserClass::slot23 | PASS | PASS(slot#23 .?AVDiskLaserClass@@) | FAIL(倒计时 + 几何 + 状态枚举，无返回码；无循环) | PASS(004A7A3A) | 是 | 不成立 | 否 |
| 9 | 004A7C90 | DiskLaserClass::slot8 | PASS | PASS(slot#8) | **PASS(③b② Find -1)** | PASS(004A7A3A) | 是 | **成立** | **是** |
| 10 | 004C5A30 | EMPulseClass::slot5 | PASS | PASS(slot#5 .?AVEMPulseClass@@) | **PASS(③b② E_POINTER + 构造)** | PASS(004C537D) | 是 | **成立** | **是** |
| 11 | 004C5A80 | EMPulseClass::slot6 | PASS | PASS(slot#6) | 待裁(29 B 纯转发 + 返回归一化) | PASS(004C537D) | 是 | 不成立(从严) | 否 |
| 12 | 004C5AC0 | EMPulseClass::slot8 | PASS | PASS(slot#8) | **PASS(③b② Find -1)** | PASS(004C537D) | 是 | **成立** | **是** |
| 13 | 005F44A0 | AnimClass::slot84 | PASS | PASS(slot#84 .?AVAnimClass@@) | **PASS(③b② Find -1 + 注销管理器)** | PASS(0042201C) | 是 | **成立** | **是** |
| 14 | 005F4870 | AnimClass::slot75 | PASS | PASS(slot#75) | FAIL(取包围盒；`test esi,esi`/`cmp eax,6` 均 NULL/枚举) | PASS(0042201C) | 是 | 不成立 | 否 |
| 15 | 005F5390 | AnimClass::slot91 | PASS | PASS(slot#91) | FAIL(返回状态枚举 0..4/5；多路全汇入同一 `0x6E53A0` 仅事件号不同) | PASS(0042201C) | 是 | 不成立 | 否 |
| 16 | 005F5940 | AnimClass::slot58 | PASS | PASS(slot#58) | FAIL(主输出 `al` bool，D-46(A) 明示不算) | PASS(0042201C) | 是 | 不成立 | 否 |
| 17 | 005F9970 | AnimTypeClass::slot7 | PASS | PASS(slot#7) | 待裁(24 B 纯转发 + 返回归一化) | PASS(00427731) | 是 | 不成立(从严) | 否 |
| 18 | 0062D7A0 | ParticleClass::slot5 | PASS | PASS(slot#5 .?AVParticleClass@@) | **PASS(③b② E_POINTER + 构造)** | PASS(0062B767) | 是 | **成立** | **是** |

## 逐行裁定依据（每行用自己的地址锚；字节见 `EVIDENCE/ROW_<entry>.txt`）

### ② 18/18 —— 槽号由整表枚举复算，RTTI 名与 name 栏逐行一致

| entry | vt | 槽地址 | slot# | COL | TD | TD+8 名串 |
|---|---|---|---|---|---|---|
| 00423AC0 | 007E3354 | 007E33B0 | 23 | 007FBA60 | 008182C8 | `.?AVAnimClass@@` |
| 00427B50 | 007E3608 | 007E36A8 | 40 | 007FBBB0 | 00818330 | `.?AVAnimTypeClass@@` |
| 00427D00 | 007E3608 | 007E366C | 25 | 007FBBB0 | 00818330 | 同上 |
| 00428800 | 007E3608 | 007E361C | 5 | 007FBBB0 | 00818330 | 同上 |
| 00428970 | 007E3608 | 007E3620 | 6 | 007FBBB0 | 00818330 | 同上 |
| 00428C30 | 007E3608 | 007E36A4 | 39 | 007FBBB0 | 00818330 | 同上 |
| 00428EA0 | 007E3608 | 007E3628 | 8 | 007FBBB0 | 00818330 | 同上 |
| 004A7340 | 007E5FB8 | 007E6014 | 23 | 007FFBF0 | 0081FF90 | `.?AVDiskLaserClass@@` |
| 004A7C90 | 007E5FB8 | 007E5FD8 | 8 | 007FFBF0 | 0081FF90 | 同上 |
| 004C5A30 | 007E87A8 | 007E87BC | 5 | 008004D8 | 008208D0 | `.?AVEMPulseClass@@` |
| 004C5A80 | 007E87A8 | 007E87C0 | 6 | 008004D8 | 008208D0 | 同上 |
| 004C5AC0 | 007E87A8 | 007E87C8 | 8 | 008004D8 | 008208D0 | 同上 |
| 005F44A0 | 007E3354 | 007E34A4 | 84 | 007FBA60 | 008182C8 | `.?AVAnimClass@@`（共驻 21 表） |
| 005F4870 | 007E3354 | 007E3480 | 75 | 007FBA60 | 008182C8 | 同上（共驻 19 表） |
| 005F5390 | 007E3354 | 007E34C0 | 91 | 007FBA60 | 008182C8 | 同上（共驻 13 表） |
| 005F5940 | 007E3354 | 007E343C | 58 | 007FBA60 | 008182C8 | 同上（共驻 20 表） |
| 005F9970 | 007E3608 | 007E3624 | 7 | 007FBBB0 | 00818330 | `.?AVAnimTypeClass@@`（共驻 10 表） |
| 0062D7A0 | 007EF954 | 007EF968 | 5 | 00807BE8 | 008366E8 | `.?AVParticleClass@@` |

每行 `vt[slot]` 的 4B 值逐字回读，等于该行 entry（证据文件里给出**槽内 4B 原始字节**与 `[vt-4]` COL 的 16 字节）。

### ④ 18/18 —— 行外、非 atexit、构造器安装

| entry | 采用锚 | 宿主 | 宿主首条基类构造 | 同表其它安装点 |
|---|---|---|---|---|
| 00423AC0 / 005F44A0 / 005F4870 / 005F5390 / 005F5940 | 0042201C | 00421EA0 | 00421EAE `call 0x5F3900` | 00422847/004228EB/004252BB |
| 00427B50 / 00427D00 / 00428800 / 00428970 / 00428C30 / 00428EA0 / 005F9970 | 00427731 | 00427530 | 0042753A `call 0x5F7090` | 0042785D/0042788D/00428831(行4体内)/00428EAD(行7体内) |
| 004A7340 / 004A7C90 | 004A7A3A | 004A7A30 | 004A7A33 `call 0x410170` | 004A7ADD/004A7B0D/004A7BB7(流构造)/004A7C9D(行9体内) |
| 004C5A30 / 004C5A80 / 004C5AC0 | 004C537D | 004C5370 | 004C5373 `call 0x410170` | 004C52DA/004C53BD/004C53E4/004C5A54(行10体内)/004C5AC4(行12体内) |
| 0062D7A0 | 0062B767 | 0062B5E0 | 0062B5E9 `call 0x5F3900` | 0062BC4A/0062BCC4/0062D7C4(行18体内)/0062D9A4 |

- 每个宿主都核了 `push <宿主>; call 0x7C978A` ⇒ **atexit 全 False**（㉓ 成对陷阱不踩）。
- 6 处「行体内自装表」（`00428831`/`00428EAD`/`004A7C9D`/`004C5A54`/`004C5AC4`/`0062D7C4`）**全部显式排除**，没有一行拿自己当 ④。- **本批一处 ㉓ 成对已辨（写进证据）**：`005F44A0` 的容器 `0xA8ECB8`。init `004E7D40` 在 `004E7D5D` 装**活表 `007E4F64`**，**之后**才 `004E7D76 push 0x4E7D80; call 0x7C978A` 注册 dtor；该 dtor `004E7D80` 在 `004E7D88` 装的是**死表 `007E192C`**。本行取活表；两只表的 `vt[#4]` 恰好都是 `or eax,-1`+`ret 4` 的 FindItemIndex，所以 -1 约定不受影响。

### ③ 成立 7 行（各自独立站点与语义）

- **`00423AC0` AnimClass::vslot23（③b④）**：半径 `[Type+0x33C]` 的双层扫描。外/内层回边
  `00424269 0f8e9dfdffff jle 0x42400C` / `0042424C 0f8ed8fdffff jle 0x42402A`；边界检查
  `00424051 cmp eax,[edx+0x33C]` → `00424057 jg 0x424235`（越界跳过本格）；
  **循环体内非栈写** `00424155 88871e010000 mov byte ptr [edi+0x11E], al`（写进被查到的对象，不是栈槽，也不是被调内部的写）。
  读（`004240BB call 0x5657A0` 取格内对象）→ 判（`004240CB test al,al`）→ 写 → 推进（`0042423F inc eax` / `0042424A cmp eax,edx`）齐备。
- **`00428EA0` AnimTypeClass::vslot8（③b②）**：两个注册表各一个 Find 站点，
  `00428ED6 cmp eax,-1`→`00428ED9 je`（容器 `0xB0F670`，活表 `007E91EC`，`vt[#4]=004E0550`，
  未命中 `004E056F 83c8ff or eax,-1` + `004E0573 ret 4`）；命中路 `00428EE8` 计数减一 + `00428EFA` 压缩写 + `00428F06 jl` 回边，未命中直接跳；第二站点 `00428F1F/00428F22`（容器 `0x8B4150`，活表 `007EA2E4`，`vt[#4]=004EE1B0`，`004EE1CF 83c8ff`）。
- **`004A7C90` DiskLaserClass::slot8（③b②）**：`004A7CC6 cmp eax,-1`→`004A7CC9 je`（容器 `0x8A0208`，活表 `007E5EDC`，`vt[#4]=004A7FB0`，`004A7FCF 83c8ff` + `004A7FD3 ret 4`）；命中路 `004A7CEA` 压缩写；收尾 `004A7CFA call 0x4101F0` + `004A7CFF test byte [esp+0xC],1` + `004A7D07 call 0x7C8B3D`。
- **`004C5A30` EMPulseClass::slot5（③b②，流读入）**：`004C5A3B call 0x410380`（**读**封装，内部 `0041039E ff500c` 走 +0xC）；失败常量 `00410389 b803400080` = **E_POINTER 0x80004003**；`004C5A40 test`/`004C5A42 jl` 零间隔；成功路 `004C5A4F call 0x4101C0` 构基类子对象 + `004C5A54..004C5A68` 装 4 表 → `004C5A6F` 返 0。
- **`004C5AC0` EMPulseClass::slot8（③b②）**：`004C5B0D cmp eax,-1`→`004C5B10 je`（容器 `0x8A3870`）；命中路 `004C5B1F` 计数减一 + `004C5B31` 压缩写 + `004C5B3D jl`；收尾 `004C5B41 call 0x4101F0` + `004C5B46 test byte [esp+0xC],1` + `004C5B4E call 0x7C8B3D`。
- **`005F44A0` AnimClass::slot84（③b②，非析构）**：守卫 `0045F44A4 mov al,[esi+0x83]`；`005F44C5 cmp eax,-1`→`005F44C8 je`（容器 `0xA8ECB8`，**活表 `007E4F64`**，`vt[#4]=0040CF00`，`0040CF1F or eax,-1` + `0040CF23 ret 4`）；命中路 `005F44D7` 计数减一 + `005F44E9` 压缩写 + `005F44F5 jl`；随后 `005F44FC` 清标志、`005F4503 call 0x4AEB10` 读管理器当前对象、`005F4508 cmp eax,esi` / `005F4513 call 0x4AEB30` 命中则清空。
- **`0062D7A0` ParticleClass::slot5（③b②，流读入构造）**：`0062D7AB call 0x5F5E80`，其首条 `005F5E8B call 0x410380`（**读**），失败路 `005F5E92 jl` 原样抛（空参 E_POINTER `00410389`）；`0062D7B0 test`/`0062D7B2 jl` 零间隔；成功路 `0062D7BF call 0x5F3B50` 构基类 + `0062D7C4` 装 4 表 + 两次 `0x6CF240` 构成员 → `0062D801` 返 0。

### ③ FAIL / 待裁 11 行（逐行独立理由）

- **`00428800`（第 4 行）—— 本批最有价值的一条负结果**：站点 `00428814 call 0x5F9720`，随后 `00428819 85c0 test` / `0042881B 0f8c… jl 0x428957`。
  但我把被调 `005F9720`（atlas size=555，157 条指令）逐条走完：**全函数只有 1 个 `ret`**（`005F9948 c20800`），
  且紧邻其前是 `005F993C 33c0 xor eax,eax` ⇒ **该函数恒返 0，永不返负**。
  于是 `jl` 这条「失败路」**静态不可达**，返回约定**不可伪证**（不是「没找到证据」，是字节证明它不会失败）⇒ ③ 不成立。
  这正是卡面点名的 `eax` 覆写陷阱的变体：**判的是返回值，但返回值域里根本没有失败值**。
- `00427B50`：唯一的分支判据是 `00427BF0` 前后 `test eax,eax` + `mov [esi+0xA4],eax` + `jne`（`0x5B40B0` 返 0/名字指针）
  与 `00427C2D` 的 `cmp eax,6` 状态枚举；指针 NULL / bool 类不计（D-46(A)），无错误码约定。
  （另：`00427B71 call 0x5F9070` 后的 `test eax,eax` 是假阳 —— `00427B7B mov eax,[esi+0xA4]` 把 eax 覆写了，机械筛会误收。）
- `00427D00`：26 个站点全部是 `0x528A10`（容器查找）与 `0x7C8D20`（free）的指针 NULL 判定；3 个 14 条循环体内**只有栈写**，不够 ③b④。
- `00428970` / `004C5A80` / `005F9970`（**待裁**）：都是 24–29 字节的转发壳 —— 3 参数 shuffle → `call` → `test|jl` → `xor eax,eax` → `ret N`。
  被调确实是错误码封装（`0x410320` 写 / `0x410380` 读 / `0x4103E0` 记录位置，空参都返 E_POINTER 0x80004003），
  「失败原样返回 / 成功归一化为 0」也字面可证；但函数体**除返回归一化外没有任何自己的动作**，按卡面「禁止 ③a 纯转发」判不成立。
  **前例冲突已记**：`NAMED_PUSH_AUDIT2` 对同形 `005F9950`（29 B，同样是转发 + `负→原样/非负→0`）判 **PASS**，
  理由写的是「不是 ③a 纯转发桩」。⇒ 这 3 行若 Lead 采纳该前例，本批为 **10/18**（0.5556），我未擅自计入。
- `00428C30`：站点是 `00428D04 call 0x4739F0` → `00428D0D call 0x4A3890` → `00428D12 test eax,eax` / `00428D1A je`。
  `0x4A3890` 体（56 B）只有 1 个 `ret`，返 `eax = edi`（`004A38B9..004A38BF` new + `call [eax+0x24]`，失败留 `edi=0`）⇒ **指针 NULL 判**，非错误码。
  另两处 `0x4739F0`/`0x4A3890` 组合（`00428D3D`/`00428D46`）是同一对被调、只换参数 ⇒ 触「多路同一 call」细则#1。
- `004A7340`：主体是倒计时（`004A7349 mov eax,[esi+0x30]` / `test` / `jge` / `jle` / `dec`）+ 向量几何 + `call [edx+0x2c]` → `cmp eax,6` 状态；
  伤害超阈值走 `call 0x4A7FE0` 爆炸。全程无错误码/返回约定，`_work/loops.py` 复核**该行 0 条回边**（无循环）⇒ ③b 四形态皆不达。
- `005F4870`：取包围盒（`call [edx+0xAC]` / `0x6D2140` / `call [edx+0x88]` / `call [edx+0x9C]`），
  `005F48AF test esi,esi` 是指针 NULL、`005F48EF cmp eax,6` 是状态枚举；结果是写回 4 dword 矩形，不是错误码。
- `005F5390`：返回 `[esp+0x10]` 的状态枚举（0..4）或 `005F5841 mov eax,5`；分支全是 `cmp ebp,2`/`cmp ebp,3` 状态与 `test al,al` 谓词；
  多路全部汇入**同一个** `0x6E53A0`，只有事件号 `0x27/0x2a/0x28/0x2b/0x26/0x29/0x06/0x2c` 不同 ⇒ 触「多路同一 call」细则#1。
- `005F5940`：主输出是 `al`（`005F5B38 mov al,1` / `005F5B43 xor al,al`），D-46(A) 明示 **bool 主输出不算**；
  内部 `call [edx+0x2c]` 后 `cmp eax,8` 也是状态枚举。`0x7C8E17`（operator new）的 NULL 判属分配检查，不作合同。

## 与 S04 的败因对比（这批有多少行 ② 真的钉住了）

- **S04**：73 个 ③b② 机械命中 **`p3b2_named=0`（全无名字）** —— entry 作 4B VA 镜像 0 命中、无虚表槽、无可回扫 RTTI 链
  ⇒ **② 物理不可得**，36 行实测全败。S04 的问题在**候选池**（名字都拿不到），不在判定。
- **本批 S20 B1**：38 个 named 候选里 **0 个** `fn_`/`sub_` 伪名（对比 S14 的 51 个 named 里 16 个是 `fn_`），
  18 行逐行整表枚举后 **② 18/18 全部钉住**，且 18/18 的 `slot_no` 与 `name` 栏槽号**逐行自洽**。
  ⇒ **② 从 S04 的 0 变成 18/18**。本批不需要「名字可信度」这层折扣。
- **所以瓶颈完全移到 ③**：18 行里 11 行 ③ 不成立（4 行只有指针 NULL/bool 判据、1 行被调恒不失败、
  1 行状态机无返回约定、1 行取矩形、1 行状态枚举 + 多路同一 call、3 行待裁转发壳）。
- **②的坑也换了一种**：S20 的难点不是「没有名字」，而是**槽号大**（84/75/91）。
  用「回扫 vt-4..vt-N」当 ② 的实现会在大槽号上静默失败（我第一版就踩了，3 行被误判成「无 RTTI 槽」）。
  整表枚举（1,212 张）才可靠 —— 建议后续卡把这条写成 ② 的实现硬要求。

## 待裁（3 项，未擅自扩面）

1. **3 行转发壳的 ③ 归属（影响 ±3）**：`00428970` / `004C5A80` / `005F9970`。
   卡面明文「禁止 ③a 纯转发」⇒ 我判不成立；但 `NAMED_PUSH_AUDIT2` 对**同形**的 `005F9950` 判 PASS（理由：返回归一化不算纯转发桩）。
   我按从严处理，未计入 delta。若 Lead 采纳 AUDIT2 前例 ⇒ **10/18（0.5556）**，3 份证据已在目录中就位，可直接回填。
2. **②与④共用同一张虚表是否算「不同源」（影响 0，但要成文）**：本批 7 个产出行里，② 用 `vt[slot]`、④ 用**同一张 vt 的构造装表指令**（段不同、产物不同）。
   §12.3 禁的是「同一个虚表槽既证类身份又证被使用」——我用的是「槽值」证 ②、「装表指令字节」证 ④，不是同一条证据。
   与 AUDIT2 已 PASS 的 10 行同型。若 Lead 认为「同表即同源」，本批产出 → **0**，需先成文再回溯处理既有同型 `[已证]`。
3. **③b④ 的判读（影响 ±1）**：`00423AC0` 我按「完整循环 I/O 带边界检查 + 循环体内非栈写」判成立。
   若 Lead 认为「按半径扫描格子」不算 I/O（尽管有 `call 0x5657A0` 读对象、`mov [edi+0x11E],al` 写对象、`inc/cmp/jle` 推进），
   则本批 **-1 → 6/18**。

## 汇总

- rows_checked：**18**
- ① 入口 PASS：**18/18**
- ② 钉住行数：**18/18**（S20 的 named 全是真虚表槽，无伪名）
- ③b 成立行数：**7**（6×③b② + 1×③b④）；另有 3 行待裁不成立
- ④ 成立行数：**18/18**
- all_four_rings（严格 D-40/D-43）：**7**，rate = **0.3889**
- delta 产出：**7 行**（`00423AC0` / `00428EA0` / `004A7C90` / `004C5A30` / `004C5AC0` / `005F44A0` / `0062D7A0`）

## 输出清单

- `REPORT.md`（本文件）、`PROGRESS.md`、`base_rate.tsv`、`delta.tsv`（7 行）
- `EVIDENCE/ROW_<entry>.txt` × 7（逐行四环地址 + 原始字节 + 语义栏引用地址逐条字节）
- `_work/`：`filter_b1.py`（筛选）、`core.py`（PE/RTTI/**虚表整表枚举**/装表点/③站点/容器 Find）、
  `survey.py`（18 行初筛 → `survey.json`/`survey.txt`）、`containers.py`（容器族 Find 取证）、
  `hosts.py`（④ 宿主分类）、`loops.py`（跳表/回边扫描）、`dump_rows.py`（逐行 dump）、
  `gen_evidence.py`（证据生成）、`gen_delta.py`（delta/base_rate 生成，语义唯一真源）、
  `selfcheck.py`（交付自检：格式/引用地址同数/reason 不共用/四环标题/base_rate 自洽 → FAIL 计数 0）
