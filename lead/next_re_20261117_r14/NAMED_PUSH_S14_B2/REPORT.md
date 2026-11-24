# NAMED-PUSH — S14 B2 批次（有名字的 ③b② 候选，攻 proved 增量）

> 状态：**完成**。执行纪律已遵：先建目录 → 先写 REPORT 骨架 → 逐行核完即落 `EVIDENCE/`；`PROGRESS.md` 每 5 行追加。
> 卡片：`lead\next_re_20261117_r14\_cards\NAMED-PUSH.md`（73 行全文读完）
> 本批：**B2** = `SURVEY_3B2\hits_detail.tsv` 中 `subsystem==S14` AND `p3b2_named==True`，按 entry 升序取**第 19..36 个**（切片 `[18:36]`）。
> 输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S14_B2\`（卡片 `<你的子系统>`=S14、`<你的目录>`=本目录）。

## 材料自校验
- 目标：`ra2youli\gamemd.exe`；现场 `Get-FileHash -Algorithm SHA256` = `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` ⇒ **与卡片期望逐字一致**。
- ImageBase `0x400000`；`.text = [0x401000, 0x7E038D)`。
- Python 3.12.10 / capstone 5.0.7（**skipdata=True**）/ pefile 2024.8.26；无 venv、未 pip install、未用 Ghidra。
- 只读输入：`SURVEY_3B2\hits_detail.tsv`（仅当线索）、`W130_atlas\function_atlas.tsv`（仅取函数边界）。未改 `coverage.tsv` / `PANEL.md` / `R14_COMMON.md` / 台账 / `SURVEY_3B2` / `S04_PUSH_*`。写域仅本目录。

## 筛选命令（得到本批 18 个 entry）

```powershell
$p = "D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv"
$rows = Import-Csv $p -Delimiter "`t"
$sel  = $rows | Where-Object { $_.subsystem -eq 'S14' -and $_.p3b2_named -eq 'True' } |
        Sort-Object { [Convert]::ToInt32($_.entry,16) }
$b2 = $sel[18..35]   # 第 19..36 个
$b2 | Format-Table entry,subsystem,name,grade,size,n_call,n_site,n_valid,p3b2_named -AutoSize
```

结果：S14 `p3b2_named=True` 共 **51** 行（卡片记 51，一致）；B2 = 升序第 19..36 行 = `00691DE0 … 006ED200`。等价脚本落盘 `_work/filter_b2.py`（`sel.sort(key=int(entry,16))[18:36]`）。

## 判定口径（严格 D-40 / D-43，宁严不宽）

1. **①入口**：entry 在 `.text` 内、atlas 边界自洽、`skipdata=0`、末条为 `ret`/`jmp`。
2. **②类身份**：`.rdata` 中 entry 作 4B VA 的槽 → 回扫 `[vt-4]=COL(sig=0)` → `[COL+0xC]=TD` → `TD+8` 名串；并要求 `slot_off/4 == 线索槽号`。`Class::` 部分仅作线索，不参与判定。
3. **③整体合同**：只认 ③b。本批实际用到的两种形态：
   - **③b②**：站点 `call` → `test/cmp eax` → `jcc`，被调**返回约定可从字节伪证**，且调用方真的拿它分支、两路动作真不同；`test` 与 `jcc` 之间无 eax 覆写；单 call 非多路同一 call。
   - **③b①**：跳转表 + 越界检查，逐项目标可单独验证。
4. **④使用见证**：活虚表形态——`vt[slot]==entry` + **行外、非 atexit** 的构造安装点（`mov [reg], vt`，且安装函数先调基类 ctor 再装本类表）。
5. **②④不同源**：② 锚 `.rdata` 的 RTTI 描述符字节，④ 锚 `.text` 的构造安装指令字节；段/地址/产物类型均不同，不复用同一虚表槽。
6. 三陷阱逐行排查：eax 覆写、多路同一 call、模板假句。

> 关于本批一个**方法上的增量**：B1 待裁 #2 是「`call [reg+0x10]` 的 -1 约定，被调经虚派发无法定位 ⇒ 判 FAIL」。本批把这类站点**钉死了被调**，且用两道互相独立的证据：
> 1. **虚表链**：该 `[reg+0x10]` 的 `reg` 来自**全局静态容器对象**（如 `mov edx,[0x8872B0]; call [edx+0x10]`），而该全局首 dword 的 vptr 由 `.text` 构造期指令安装（`0x40E78D: mov dword ptr [0x8872B0], 0x7E1B24`），于是 vt 静态确定 → `vt[#4]` 是可读函数体（`0x40EA80`）→ `or eax,-1` + `ret 4` 使 **-1/下标约定字节可伪证**。
> 2. **this 与字段偏移自洽**：站点前有 `mov ecx,<容器地址>`（如 `0x691F11: b9 b0 72 88 00`）⇒ 本次 call 的 this 即该容器实例；而 Find 体内读 `[ecx+0x10]`/`[ecx+4]`，与本函数压缩移除代码使用的计数 `0x8872C0`/向量 `0x8872B4` 逐字段对应。
> 两路证据都不依赖「多站点同口径」这种弱伪证。本批 4 行靠此成立。

## 基础率（诚实报数）

| 档 | 行数 | 口径 |
|---|---:|---|
| 本批行数 | **18** | S14 named=True 升序第 19..36 |
| ①入口 PASS | **18** | 全部在 `.text`、`skipdata=0`、末条 ret/jmp |
| ②类身份钉住 | **13** | 13/13 的 `Class::slotN` 行全钉住；5 个 `fn_*` 行**物理不可得**（见下） |
| ③b 成立 | **6** | 5×③b② + 1×③b① |
| ④使用见证成立 | **13** | 13 个虚表行均有行外非 atexit 构造安装点；5 个 `fn_*` 行只有 direct 调用者（D-40『direct-only 不足』）⇒ 不成立 |
| **四环齐全** | **6** | rate = 6/18 = **0.3333** |

`base_rate.tsv`：`S14_B2  18  13  6  13  6  0.3333`

## 本批 18 行总表

| # | entry | name(原样) | ① | ② | ③ | ④ | ②④不同源 | 裁定 | 产出 |
|---:|---|---|---|---|---|---|---|---|---|
| 19 | 00691DE0 | ScriptTypeClass::slot6 | PASS | PASS(.?AVScriptTypeClass@@) | FAIL(③a 纯转发) | PASS(0x6916D1) | 是 | 不成立 | 否 |
| 20 | 00691E30 | ScriptTypeClass::slot10 | PASS | PASS(.?AVScriptTypeClass@@) | FAIL(p3=0；只测类型枚举 0x23) | PASS(0x6916D1) | 是 | 不成立 | 否 |
| 21 | 00691EE0 | ScriptClass::slot8 | PASS | PASS(.?AVScriptClass@@) | **PASS(③b② Find -1)** | PASS(0x6913DD) | 是 | **成立** | **是** |
| 22 | 00691FA0 | ScriptTypeClass::slot8 | PASS | PASS(.?AVScriptTypeClass@@) | **PASS(③b② Find -1)** | PASS(0x6916D1) | 是 | **成立** | **是** |
| 23 | 006A48A0 | SideClass::slot6 | PASS | PASS(.?AVSideClass@@) | **PASS(③b② E_POINTER + 流读循环)** | PASS(0x6A4597) | 是 | **成立** | **是** |
| 24 | 006A4930 | SideClass::slot8 | PASS | PASS(.?AVSideClass@@) | **PASS(③b② Find -1)** | PASS(0x6A4597) | 是 | **成立** | **是** |
| 25 | 006E8420 | TaskForceClass::slot25 | PASS | PASS(.?AVTaskForceClass@@) | FAIL(零/长度判断 jle) | PASS(0x6E7EAD) | 是 | 不成立 | 否 |
| 26 | 006E8680 | TaskForceClass::slot6 | PASS | PASS(.?AVTaskForceClass@@) | FAIL(③a 纯转发) | PASS(0x6E7EAD) | 是 | 不成立 | 否 |
| 27 | 006E86A0 | TaskForceClass::slot5 | PASS | PASS(.?AVTaskForceClass@@) | FAIL(模板假句：装表+构造成员) | PASS(0x6E7EAD) | 是 | 不成立 | 否 |
| 28 | 006E87F0 | TaskForceClass::slot8 | PASS | PASS(.?AVTaskForceClass@@) | **PASS(③b② Find -1)** | PASS(0x6E7EAD) | 是 | **成立** | **是** |
| 29 | 006E9140 | TeamClass::slot23 | PASS | PASS(.?AVTeamClass@@) | **PASS(③b① 65 路跳表)** | PASS(0x6E8B32) | 是 | **成立** | **是** |
| 30 | 006EB490 | fn_006EB490 | PASS | **FAIL**(全镜像 0 引用) | 未计入 | FAIL(仅 direct) | – | 不成立 | 否 |
| 31 | 006EBAD0 | fn_006EBAD0 | PASS | **FAIL**(全镜像 0 引用) | 未计入(机械站点是 eax 覆写假阳) | FAIL(仅 direct) | – | 不成立 | 否 |
| 32 | 006EC450 | TeamClass::slot5 | PASS | PASS(.?AVTeamClass@@) | FAIL(模板假句：装表+构造成员×11) | PASS(0x6E8B32) | 是 | 不成立 | 否 |
| 33 | 006EC540 | TeamClass::slot6 | PASS | PASS(.?AVTeamClass@@) | FAIL(③a 纯转发) | PASS(0x6E8B32) | 是 | 不成立 | 否 |
| 34 | 006EC9A0 | fn_006EC9A0 | PASS | **FAIL**(全镜像 0 引用) | 未计入(被调 0x6E9050 是 void) | FAIL(仅 direct) | – | 不成立 | 否 |
| 35 | 006ECA70 | fn_006ECA70 | PASS | **FAIL**(全镜像 0 引用) | 未计入(被调 0x6E9050 是 void) | FAIL(仅 direct) | – | 不成立 | 否 |
| 36 | 006ED200 | fn_006ED200 | PASS | **FAIL**(全镜像 0 引用) | 未计入(只测类型枚举) | FAIL(仅 direct) | – | 不成立 | 否 |

## 逐行裁定依据（每行自身地址锚；字节见 `EVIDENCE/ROW_<entry>.txt`）

**② 13/13（`Class::slotN` 行全数钉住，槽号被字节复算而非反推）**
`00691DE0` 槽 `007F1020`=`e0 1d 69 00`(vt `007F1008`+0x18，slot#6)→COL `00808F38`(sig `00 00 00 00`)→TD `0083E6E8`→`.?AVScriptTypeClass@@`；`00691E30` 槽 `007F1030`(slot#10)→同一 vt；`00691EE0` 槽 `007F0F98`(vt `007F0F78`+0x20，slot#8)→`00808F38`/`0083E6E8`→`.?AVScriptClass@@`；`00691FA0` 槽 `007F1028`(slot#8)；`006A48A0` 槽 `007F2ED8`(vt `007F2EC0`+0x18，slot#6)→`.?AVSideClass@@`；`006A4930` 槽 `007F2EE0`(slot#8)；`006E8420` 槽 `007F46E4`(vt `007F4680`+0x64，slot#25)→`.?AVTaskForceClass@@`；`006E8680`/`006E86A0`/`006E87F0` 槽 `007F4698`/`007F4694`/`007F46A0`(slot#6/#5/#8)；`006E9140` 槽 `007F478C`(vt `007F4730`+0x5C，slot#23)→`.?AVTeamClass@@`；`006EC450`/`006EC540` 槽 `007F4744`/`007F4748`(slot#5/#6)。

**② 5 行 FAIL（`fn_*` 是地址式标签，不是类身份）**
`006EB490`/`006EBAD0`/`006EC9A0`/`006ECA70`/`006ED200`：全镜像（`.text`/`.rdata`/`.data` 全段）以 4B VA 搜索 **0 命中**，函数体内也没有把带 RTTI 的虚表写入 `[mem]` 的指令 ⇒ 既无虚表槽也无 RTTI 描述符链，② 物理不可得。它们只因为 `p3b2_named` 的机械口径（`name` 非空且不以 `sub_`/`::sub_` 开头）被计为「有名字」。

**③ 成立 6 行（各自独立站点与语义）**
- `00691EE0` ScriptClass::slot8：站点 `0x691F1A` `ff 52 10`(call [edx+0x10])；`0x691F1D` `83 f8 ff`(cmp eax,-1)；`0x691F20` `74 2d`(je→0x691F4F)。被调经容器 `[0x8872B0]`→vt `007E1B24`(`.?AV?$DynamicVectorClass@PAVScriptClass@@@@`，安装点 `0x40E78D: c7 05 b0 72 88 00 24 1b 7e 00`)→`vt[#4]=0x40EA80`(Find)，其 `0x40EA9F` `83 c8 ff` 后 `0x40EAA3` `c2 04 00` ⇒ **-1/下标可伪证**。命中路 `0x691F22..0x691F4D` 把 `[0x8872C0]` 计数减一并前移压缩数组；未命中直接跳 `0x691F4F` 走基类析构 `0x4101F0`，再 `0x691F56` `f6 44 24 0c 01`(test byte [esp+0xC],1) / `0x691F5E` call `0x7C8B3D` 条件释放。
- `00691FA0` ScriptTypeClass::slot8：站点 `0x691FDA`/`0x691FDD` `83 f8 ff`/`0x691FE0` `74 2d`；容器 `0x8B41C8`→vt `007EA124`(`DynamicVectorClass<ScriptTypeClass*>`，安装 `0x4E717D`)→`vt[#4]=0x4ED110`(Find，`0x4ED12F` `83 c8 ff`)；压缩数组在 `0x8B41D8`/`0x8B41CC`，基类析构 `0x4109C0`(其内部亦为同型 Find 摘链)，条件释放 `0x69201E` call `0x7C8B3D`。
- `006A48A0` SideClass::slot6：站点 `0x6A48B1` `e8 6a ba d6 ff`(→`0x410320`)；`0x6A48B6` `85 c0`；`0x6A48B8` `7c 42`(jl→`0x6A48FC` 原样返负 HRESULT)。被调空参返回字节 `0x41032B` `b8 03 40 00 80`=**E_POINTER 0x80004003**；成功路 `0x6A48C3..0x6A48D1` 读 4B 计数、`0x6A48DE..0x6A48F7` 对 `+0x9C` 数组逐元素读 4B（`ff 51 10`），末尾 `0x6A48F9` `33 c0` 返 0。
- `006A4930` SideClass::slot8：站点 `0x6A496A` `ff 52 10`/`0x6A496D` `83 f8 ff`/`0x6A4970` `74 2d`；容器 `0x8B4120`→vt `007EA024`(`DynamicVectorClass<SideClass*>`，安装 `0x4E6F7D`)→`vt[#4]=0x4EC790`(Find，`0x4EC7AF` `83 c8 ff`)；另有 `0x6A49AF` 判 `[esi+0x9C]` 非空且 `[esi+0xA5]` 标志才 `0x6A49BE` call `0x7C8B3D` 释放自有缓冲，再 `0x6A49E3` 调基类析构 `0x4109C0`。
- `006E87F0` TaskForceClass::slot8：站点 `0x6E882A` `ff 52 10`/`0x6E882D` `83 f8 ff`/`0x6E8830` `74 2d`；容器 `0xA8E8D0`→vt `007EA0A4`(`DynamicVectorClass<TaskForceClass*>`，安装 `0x4E707D`)→`vt[#4]=0x4ECC50`(Find，`0x4ECC6F` `83 c8 ff`)；压缩数组 `0xA8E8E0`/`0xA8E8D4`，基类析构 `0x4109C0`，条件释放 `0x6E886E` call `0x7C8B3D`。
- `006E9140` TeamClass::slot23（**③b①**）：`0x6E944B` `83 f8 40`(cmp eax,0x40) + `0x6E9455` `0f 87 50 01 00 00`(ja→`0x6E95AB` 默认收尾) + `0x6E945B` `ff 24 85 74 9f 6e 00`(jmp [eax*4+`0x6E9F74`])。表在 `.text` 内 `0x6E9F74`，65 项**全部**读出（slot `006E9F74..006EA074`），**65 个目标互不相同且全在 `.text`**；逐路可单独验证——每块以 `ret`/`jmp` 收尾并各自调用独立 handler（case0→`0x6ED090`、case1→`0x6EC9A0`、case3→`0x6EC7D0`、case9→`0x6ED4D0`、case10→`0x6EDB50`、case14→`0x6ED200`、case17→`0x6EC9A0`… `0x6E9783` 等），清单见 `_work/jt_006E9140.txt`。

**③ FAIL 7 行（逐行独立理由）**
- ③a 纯转发壳（单 call + 两路只差返回值常量）：`00691DE0`（`0x691DEF` call `0x410320`；`0x691DF4` `85 c0`；`0x691DF6` `7c 02`；成功路仅 `0x691DF8` `33 c0` 即 `ret 0xc`）、`006E8680`（`0x6E868F`/`0x6E8694`/`0x6E8696`/`0x6E8698`）、`006EC540`（`0x6EC54F`/`0x6EC554`/`0x6EC556`/`0x6EC558`）。
- 模板假句（E_POINTER 早退结构合格，但成功路只是装虚表 + 构造成员，语义只能落「校验后初始化对象」式）：`006E86A0`（`0x6E86C4..0x6E86D8` 装 4 表 + `0x6E86F1` 处 call `0x6CF240` 在 `edi=6` 循环里构造 6 轮）、`006EC450`（`0x6EC485..0x6EC499` 装 4 表 + `0x6EC4A9..0x6EC535` **11** 次 `0x6CF240`）。与 B1 的 `0041E540`/`00691630`/`00691D90` 同一形态。
- 零/长度判断（非错误码，D-46(A)）：`006E8420`（`0x6E847F` call `0x528A10`；`0x6E8484` `85 c0`；`0x6E8486` `7e 3f`；被调出口为 `0x528BC0` `33 c0` 返 0 与 `0x528BF4` 返串长 ⇒ 判据是 ≤0 而非失败码）。
- 无可伪证站点（p3=0）：`00691E30`（唯一分支 `0x691E46` `83 f8 23` 比较虚派发返回的**类型枚举** 0x23，被调不可定位）。

**④ 13/13（虚表行）**：每行都有**行外、`atexit=False`** 的构造安装点，且安装函数形态为「先调基类 ctor 再装本类 vt」：`00691EE0`→`0x6913DD`(in `006913C0`，先 call `0x410170`)；`00691DE0`/`00691E30`/`00691FA0`→`0x6916D1`(in `006916B0`，先 call `0x410800`)；`006A48A0`/`006A4930`→`0x6A4597`(in `006A4550`，先 call `0x410800`)；`006E8420`/`006E8680`/`006E86A0`/`006E87F0`→`0x6E7EAD`(in `006E7E80`，先 call `0x410800`)；`006E9140`/`006EC450`/`006EC540`→`0x6E8B32`(in `006E8A90`，先 call `0x410170`)。全部逐点核过 `push <fn>; call 0x7C978A`（㉓）排除 atexit。

## 与 S04 的败因对比（本批有多少行 ② 真的钉住了）

- **S04**：73 个 ③b② 机械命中 `p3b2_named=0`（全无名字）——entry 作 4B VA 镜像 0 命中、无虚表槽、无可回扫 RTTI 链 ⇒ **② 物理不可得**，30+ 行实测全败。
- **本批 S14 B2**：18 行里 **13 行 ② 被 RTTI + 虚表独立钉死**，且 13/13 的 `slot offset/4` 与线索槽号逐行自洽（槽号由字节复算）。若只看 `Class::slotN` 行，② 是 **13/13 = 100%**。
- **但「有名字」在机械口径下掺了水**：18 行里 5 行（`006EB490`/`006EBAD0`/`006EC9A0`/`006ECA70`/`006ED200`）名字是 `fn_XXXX` 地址式标签，全镜像 0 引用 ⇒ ② 与 S04 同样**物理不可得**。这不是判定问题，是候选池问题。
- **更大范围的同一问题**：S14 的 51 个 `p3b2_named=True` 里 **16 个是 `fn_` 式**（B1 段 0 个、B2 段 5 个、**其余 11 个全在后 15 行**）；已逐条复算，这 16 个 **全部** `refs=0` ⇒ 若开 B3 批（第 37..51 行），② 将 **0/15 全败**。建议 Lead 在 B3 前先按「名字是否 `Class::slotN`」再筛一次，或把 B3 记为 `named=False` 处理。
- 结论：**② 从 S04 的 0 → 本批 13/18（slotN 行 13/13）**；瓶颈已不是取身份，而是 ③——13 个有 ② 的行里 7 行 ③ 不成立（3 行纯转发、2 行模板假句、1 行零值判断、1 行无站点）。

## 待裁（3 项，未擅自扩面）

1. **析构行是否算「整体合同」**：本批 4 个 ③ 成立行（`00691EE0`/`00691FA0`/`006A4930`/`006E87F0`）是**标量析构**，其 ③ 靠「全局容器 `Find` 返 -1（字节可伪证）→ 命中才压缩移除 / 未命中跳过 → 基类析构 → 按 delete 标志释放」的分支。我判成立（契约有真实可分辨的两路动作，且 -1 由被调字节证明）。若 Lead 认为析构类语义不计，则本批 **-4 → 2/18**（`006A48A0`、`006E9140` 不受影响）。
2. **③b① 是否接受在 ③b② 候选行上得分**：`006E9140` 是按 ③b② 机械筛出的行，但函数内是 65 路跳转表（③b①）。卡片 ③ 只要求「只认 ③b」并列出四种形态，故我判成立。若要求「必须是筛出时那一路形态」，则 **-1 → 5/18**。
3. **低档两例**：`006E8420` 的 6 轮循环 I/O 有无可能落 ③b④（循环体内确有非栈写 `[esi+ecx*8+0xA4]`，但**下标的容量边界检查缺失**，只有固定 6 次迭代）——我判不成立；若 Lead 认「固定迭代次数」即满足「带边界检查」，可 +1。`006E86A0`/`006EC450` 的「E_POINTER 早退 + 纯装表构造」与 B1 待裁 #1 同类，若该类可算 ③b②，可 +2。

## 汇总

- rows_checked：**18**
- ② 钉住行数：**13**（`Class::slotN` 行 13/13；5 个 `fn_*` 行物理不可得）
- ③b 成立行数：**6**（5×③b② + 1×③b①）
- ④ 成立行数：**13**（虚表行全成立；5 个 `fn_*` 行只有 direct 调用者，按 D-40『direct-only 不足』判不成立）
- all_four_rings（严格 D-40/D-43）：**6**，rate = **0.3333**
- delta 产出：**6 行**（`00691EE0` / `00691FA0` / `006A48A0` / `006A4930` / `006E87F0` / `006E9140`）

## 输出清单

- `REPORT.md`（本文件）、`PROGRESS.md`、`base_rate.tsv`、`delta.tsv`（6 行）
- `EVIDENCE/ROW_<entry>.txt` × 18（逐行四环地址与字节，每行独立锚点）
- `_work/`：`filter_b2.py`（筛选）、`recore.py`/`core2.py`（PE/capstone/RTTI 底座）、`analyze.py`（四环初筛）、`refs.py`（全镜像 dword 引用+槽解析）、`ring4.py`（安装点与 atexit 索引）、`helper.py`（helper/容器虚表取证）、`dump_rows.py`（逐行反汇编）、`jt.py`（跳表逐路核验）、`gen_evidence.py`（产物生成）+ 中间 JSON/TXT（`analysis.json`/`refs.json`/`ring4.json`/`dump_*.txt`/`jt_006E9140.txt`），全部只读目标、可复算。
