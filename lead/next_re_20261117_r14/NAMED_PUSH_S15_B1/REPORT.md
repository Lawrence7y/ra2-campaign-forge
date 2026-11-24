# REPORT — NAMED-PUSH S15 B1

> 状态：**已完成**（10/10 行核完；本文件整体重写，取代上一轮中断遗留的骨架占位）
> 卡片：`lead\next_re_20261117_r14\_cards\NAMED-PUSH.md`（80 行全文读完）
> 输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S15_B1\`

## 1 · 身份 / 目标 / 环境

| 项 | 值 |
|---|---|
| 批次 | `S15_B1`（子系统 S15，唯一一批：候选全 10 行，不足 18 按实际） |
| 二进制 | `D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe` |
| SHA-256（现场 `Get-FileHash`） | `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` ✅ 与卡面逐字一致 |
| ImageBase | `0x400000` |
| `.text` | `[0x401000, 0x7E038D)`（实测 `TEXT_VA=00401000`、`VirtualSize=0x3DF38D`） |
| 段 | `.text 00401000+3DF38D`、`.rdata 007E1000+30074`、`.data 00812000+367BE4` |
| 工具 | Python 3.12.10 + capstone 5.0.7（**`skipdata=True`**）+ pefile 2024.8.26；无 venv、未 pip install、未用 Ghidra |
| 只读输入 | `SURVEY_3B2\hits_detail.tsv`（仅当线索）、`W130_atlas\function_atlas.tsv`（仅取函数边界）、`COVERAGE\coverage.tsv`（只读核现状） |
| 写域 | 仅本批目录（`delta.tsv` / `base_rate.tsv` / `REPORT.md` / `PROGRESS.md` / `EVIDENCE\` / `_work\`） |

**未改** `coverage.tsv` / `PANEL.md` / `R14_COMMON.md` / 台账 / `SURVEY_3B2` / `S04_PUSH_*`。

## 2 · 筛选命令（卡面要求写进报告）

```powershell
$p    = "D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv"
$rows = Import-Csv $p -Delimiter "`t"
# ① 本子系统 ② p3b2_named == True ③ 排除地址式伪名 fn_XXXXXXXX / sub_XXXXXXXX ④ entry 升序
$sel  = $rows | Where-Object {
            $_.subsystem -eq 'S15' -and
            $_.p3b2_named -eq 'True' -and
            $_.name -notmatch '^(fn|sub)_[0-9A-Fa-f]{8}$'
        } | Sort-Object { [Convert]::ToInt32($_.entry, 16) }
$sel | Format-Table entry,name,grade,size,n_insn,n_call -AutoSize
```

实测读数：`hits_detail.tsv` 全表 **1,733** 行；`subsystem==S15` **12** 行；其中 `p3b2_named==True` **10** 行；
10 行里 `fn_`/`sub_` 伪名 **0** 行（S15 无地址式伪名）⇒ **入选 10 行 = 全部**，候选池已耗尽。
与卡面背景「S15 有名字命中 **10**」一致。

## 3 · 候选表（按 entry 升序，name 原样）

| # | entry | name | hits grade | size | 本行形态（本次实测） |
|---:|---|---|---|---:|---|
| 1 | 006E3E30 | TActionClass::slot6 | [静态推断] | 29 | slot6 流写出转交（写包装 00410320） |
| 2 | 006E57A0 | TagClass::slot6 | [静态推断] | 29 | 同上 |
| 3 | 006E6470 | TagTypeClass::slot6 | [静态推断] | 29 | 同上 |
| 4 | 0071F930 | TEventClass::slot6 | [静态推断] | 29 | 同上 |
| 5 | 0071FA80 | TEventClass::slot8 | [静态推断] | 287 | **删除析构器**（容器摘除压缩） |
| 6 | 00726860 | TriggerClass::slot5 | [静态推断] | 111 | slot5 流读入 + 就地构造（读包装 00410380） |
| 7 | 007268D0 | TriggerClass::slot6 | [静态推断] | 29 | slot6 流写出转交 |
| 8 | 00726950 | TriggerClass::slot8 | [静态推断] | 287 | **删除析构器** |
| 9 | 00727BF0 | TriggerTypeClass::slot5 | [静态推断] | 137 | slot5 流读入 + 就地构造 |
| 10 | 00727C80 | TriggerTypeClass::slot6 | [静态推断] | 29 | slot6 流写出转交 |

盘上现状（只读核 `coverage.tsv`）：10 行**全部仍是 `[静态推断]`**，语义栏仍是
「`<Class> 虚表槽 N(+0x..)：触发器/Tag/TEvent/TAction 方法（槽语义未证）`」——即 `R14_COMMON` §8.1 错源 ㉘
所指的「只证了名字」零行为模板。**本批 delta 对 10 行都是真实增量。**

## 4 · 判定口径（严格 D-40 / D-42 / ㉓，宁严不宽）

1. **① 入口**：entry 在 `.text` 内、atlas size 反汇编全覆盖（末条 `addr+size-entry == atlas size`）、`skipdata` 命中 0 条、收尾为 `ret`。
2. **② 类身份**：`u32(vt+4N)==entry` → `u32(vt-4)=COL` → `COL+0xC`=pTD → **TD+8 内联装饰名**；
   要求 `COL.sig==0`、槽号与名字里 `slotN` 自洽、**slot0==00410260 判主虚表**（避开「小成员表」陷阱③）。
   **技术条已按卡面执行**：pTD/pCHD 存**绝对 VA**（非 RVA）；TD+8 是**内联串本体**（不是指针，故 `TD+0` 是 type_info 的 pVFTable、`TD+4` 为 spare，名串自 `TD+8` 起）。
3. **③ 整体合同**：只认 **③b②**——可伪证的错误码/返回约定，且**本行真的拿它分支**、两路动作不同。
   - SAVE/LOAD 行：`call 00410320/00410380 → test eax,eax → jl`，失败落点**保留 eax**（负码原样透出）、成功路 `xor eax,eax` 返 0。此形态与 `R14_COMMON` §12.2 判 **③b② 成立**的 `Save_VectorBlock` 族逐字同构。
   - FIND 行：`call [edx+0x10] → cmp eax,-1 → je`，卡面明列「Find 返 -1 下标约定算」。
   - 排除 ③a：本批无「单调用+单写」「清零+置默认」「无分支直线」形态；「纯转发」一项单列见 §7.5 披露。
4. **④ 使用见证**：**行外构造器**在 `.text` 的 `mov [reg],vt` 装表点；宿主须满足「装表前有基类构造调用 + 返回 this」、非 atexit、装表点在**行体之外**。
   **㉓ 按 `R14_COMMON` §13.5 逐表执行**：全镜像扫该表基址 imm32 → 定位承载指令 → 分类，
   排除 (a) `push <fn>; call 0x7C978A` 的 atexit 全局析构器体内写、(b) 删除析构器体内写
   （特征 `test byte ptr [esp+X],1` + `call 0x7C8B3D` + `ret 4`），另按卡面「④ 锚点落析构器判 FAIL」排除一切析构器装表点。
5. **三陷阱逐行排查**：eax 覆写（`test`/`cmp` 与 `jcc` 之间 0 条指令，逐行核过）、多路同一 call（每行站点互异，FIND 行 3 站点指向不同容器全局）、模板假句（语义栏一律写具体站点、字节与返回约定）。

## 5 · 四环总表

| # | entry | name | ① | ② | ③b | ④ | 四环齐全 | 产出 |
|---:|---|---|:-:|:-:|:-:|:-:|:-:|:-:|
| 1 | 006E3E30 | TActionClass::slot6 | OK | OK | ③b② OK | OK | **是** | **[已证]** |
| 2 | 006E57A0 | TagClass::slot6 | OK | OK | ③b② OK | OK | **是** | **[已证]** |
| 3 | 006E6470 | TagTypeClass::slot6 | OK | OK | ③b② OK | OK | **是** | **[已证]** |
| 4 | 0071F930 | TEventClass::slot6 | OK | OK | ③b② OK | OK | **是** | **[已证]** |
| 5 | 0071FA80 | TEventClass::slot8 | OK | OK | ③b② OK | OK | **是** | **[已证]** |
| 6 | 00726860 | TriggerClass::slot5 | OK | OK | ③b② OK | OK | **是** | **[已证]** |
| 7 | 007268D0 | TriggerClass::slot6 | OK | OK | ③b② OK | OK | **是** | **[已证]** |
| 8 | 00726950 | TriggerClass::slot8 | OK | OK | ③b② OK | OK | **是** | **[已证]** |
| 9 | 00727BF0 | TriggerTypeClass::slot5 | OK | OK | ③b② OK | OK | **是** | **[已证]** |
| 10 | 00727C80 | TriggerTypeClass::slot6 | OK | OK | ③b② OK | OK | **是** | **[已证]** |

## 6 · 逐行锚点（每行独立地址，无整批共用 reason）

| entry | ② 锚点（.rdata） | ③b 站点锚（本行体内） | ④ 锚点（行外构造器 + 装表点） |
|---|---|---|---|
| 006E3E30 | vt=007F443C slot#6 @007F4454=006E3E30；COL=0080BAF0→TD=00842B78→`.?AVTActionClass@@` | `call 00410320`@006E3E3F / `test`@006E3E44 / `jl`@006E3E46→006E3E4A / `xor eax,eax`@006E3E48 | ctor **006DD000**（`call 00410170`@006DD004）→ `006DD036 c7 06 3c 44 7f 00` |
| 006E57A0 | vt=007F44E0 slot#6 @007F44F8；COL=0080BBA0→TD=008249E8→`.?AVTagClass@@` | `call 00410320`@006E57AF / `test`@006E57B4 / `jl`@006E57B6→006E57BA / `xor`@006E57B8 | ctor **006E4DE0**（`call 00410170`@006E4DE5）→ `006E4E07 c7 06 e0 44 7f 00` |
| 006E6470 | vt=007F45C4 slot#6 @007F45DC；COL=0080BCF0→TD=00842CB0→`.?AVTagTypeClass@@` | `call 00410320`@006E647F / `test`@006E6484 / `jl`@006E6486→006E648A / `xor`@006E6488 | ctor **006E5B60**（`call 00410800`@006E5B6C）→ `006E5B8E c7 45 00 c4 45 7f 00` |
| 0071F930 | vt=007F5578 slot#6 @007F5590；COL=0080C5E0→TD=008446F8→`.?AVTEventClass@@` | `call 00410320`@0071F93F / `test`@0071F944 / `jl`@0071F946→0071F94A / `xor`@0071F948 | ctor **0071E6A0**（`call 00410170`@0071E6A4）→ `0071E6C1 c7 06 78 55 7f 00` |
| 0071FA80 | vt=007F5578 slot#8 @007F5598；同上 RTTI | 3 站点 `call [edx+0x10]`@0071FABA/0071FB03/0071FB4C；`cmp eax,-1`@0071FABD/0071FB06/0071FB4F；`je`→0071FAEF/0071FB38/0071FB81；压缩写 `mov [ecx+eax*4-4],edx`@0071FAE1 | ctor **0071E6A0** → `0071E6C1`（与本行同表另一槽；**本行自身 0071FA86 是删除析构器写点，已排除**） |
| 00726860 | vt=007F5858 slot#5 @007F586C；COL=0080C968→TD=00842CE8→`.?AVTriggerClass@@` | `call 00410380`@0072686B / `test`@00726870 / `jl`@00726872→007268CB（`pop esi`+`ret 8`，eax 保留） | ctor **00725FA0**（`call 00410170`@00725FA4）→ `00725FCE c7 06 58 58 7f 00`（**本行自身 00726884 是 Load 就地构造写点，已排除**） |
| 007268D0 | vt=007F5858 slot#6 @007F5870；同上 RTTI | `call 00410320`@007268DF / `test`@007268E4 / `jl`@007268E6→007268EA / `xor`@007268E8 | ctor **00725FA0** → `00725FCE` |
| 00726950 | vt=007F5858 slot#8 @007F5878；同上 RTTI | 3 站点 @0072698A/007269D3/00726A1C（`call [edx+0x10]`）；`cmp eax,-1`@0072698D/007269D6/007269D9+；`je`→007269BF/00726A08/00726A51 | ctor **00725FA0** → `00725FCE`（**本行自身 00726956 是删除析构器写点，已排除**） |
| 00727BF0 | vt=007F5904 slot#5 @007F5918；COL=0080CA20→TD=00842D08→`.?AVTriggerTypeClass@@` | `call 00410380`@00727BFB / `test`@00727C00 / `jl`@00727C02→00727C75（`pop esi`+`ret 8`，eax 保留） | ctor **00726C80**（`call 00410800`@00726C89）→ `00726CD2 c7 06 04 59 7f 00`（**本行自身 00727C14 是 Load 就地构造写点，已排除**） |
| 00727C80 | vt=007F5904 slot#6 @007F591C；同上 RTTI | `call 00410320`@00727C8F / `test`@00727C94 / `jl`@00727C96→00727C9A / `xor`@00727C98 | ctor **00726C80** → `00726CD2` |

### 6.1 被调方约定落到字节（③b② 不止「调用点看起来像」）

- **写/读包装**（SAVE/LOAD 行共用）：`00410320` / `00410380` 体内
  `0041032B b8 03 40 00 80 → EAX=0x80004003`（E_POINTER，空入参）、`00410389` 同；
  且包装内部 `0041034D 7c 23 jl 0x410372`、`00410364 7c 0c jl 0x410372`、`004103A3 7c 31 jl 0x4103D6`
  把**内层** `[vt+0x10]/[vt+0xC]` 调用的负 HRESULT **原样透出** ⇒ 返回值确为多值。
- **容器 Find**（FIND 行）：每个容器全局的 vptr 由 `.text` 静态装表 → 容器虚表 → 槽 4(+0x10) = Find 真身，
  10 个实现（5 全局 × 2 变体）**全部**在未命中处以 `or eax,0xFFFFFFFF` 收尾：

| 容器全局 | 装表点 → 容器 vt | Find 真身 | `or eax,-1` 站点 |
|---|---|---|---|
| 00B0F658 / 00B0F670 / 00B0F708 | 007255ED → 007E91EC | 004E0550 | 004E056F |
| 同上（第二变体） | 00725618 → 007E920C | 004E0440 | 004E046C |
| 00B0F1A0 | 0071E63D → 007F550C | 0071FE30 | 0071FE4F |
| 00B0F1A0（第二变体） | 0071E668 → 007F552C | 0071FD20 | 0071FD4C |
| 00A8EAE8 | 004E65FD → 007E9BE4 | 004EA650 | 004EA66F |
| 00A8EAE8（第二变体） | 004E6628 → 007E9C04 | 004EA540 | 004EA56C |

Find 体形状（以 004E0550 为例）：`mov edx,[ecx+0x10]`(Count) / `xor eax,eax` / 循环
`cmp [ecx],esi` → `je` 命中返回下标 / `inc eax; add ecx,4; cmp eax,edx; jl` / 未命中 `or eax,0xFFFFFFFF`。

## 7 · 风险与披露（必须与结论同读，不折进结论）

### 7.1 ②④ 枢轴共用（与 `R14_COMMON` §12.3 / D-47 的张力）——10 行全部适用

字面口径：② 锚 `.rdata` 的 COL/TD/RTTI 字节链，④ 锚 `.text` 的构造器装表指令 ⇒ artifact 不同 ⇒ `same_source=no`。
但须承认：④ 成立需两个命题 ——(i)「该表是活表（构造器装入对象）」确属独立（`.text`，② 不用）；
(ii)「entry 正占该表第 N 槽」必须读 `.rdata` 的 `[vt+4N]==entry`，而 ② 判「属此类」用的**正是同一条**。
⇒ `vt[slot]==entry` 这一枢轴仍被 ② 与 ④ 共同消费；按 §12.3 字面判**同源**，按 D-43(A) 宽读法 ④ 形式合格。
**现行处置**：Lead 采 **D-43(A) 先行、§12.3 让位**（`R14_COMMON` §13.4；`COVERAGE\PANEL.md:160–166` 已逐字披露），
盘上已有 16 行按此口径 `[已证]`。本批与之同口径，并在每份 EVIDENCE 内逐行写明上文 (i)(ii)。

### 7.2 同一装表点被多行共用（`R14_COMMON` §8.6 条 1「site 不共用」的已知限制）

10 行只落在 **6 条装表指令**上，3 组共用：

| 装表点 | 共用行 | 说明 |
|---|---|---|
| `006DD036` | 006E3E30 | 独用 |
| `006E4E07` | 006E57A0 | 独用 |
| `006E5B8E` | 006E6470 | 独用 |
| `0071E6C1` | **0071F930 + 0071FA80** | 同表 slot6/slot8 共用，两行仅槽号可区分 |
| `00725FCE` | **00726860 + 007268D0 + 00726950** | 同表 slot5/slot6/slot8 三行共用 |
| `00726CD2` | **00727BF0 + 00727C80** | 同表 slot5/slot6 两行共用 |

这正是 `NAMED_PUSH_AUDIT16` §3.2 对 S13_B1 记的「(i) 是两行共享的同一个命题 ⇒ 只剩槽号可区分」同型限制。
**取 S13_B1 先例（AUDIT16 6/6 PASS、Lead 已并）**：本批不因共用而减行，但在此显式披露。
**若 Lead 改采更严读法（每装表点只许支撑 1 行）**：按组各留 1 行 ⇒ delta 降为 **6 行**
（006E3E30 / 006E57A0 / 006E6470 / 0071F930 或 0071FA80 / 00726860 或 007268D0 或 00726950 / 00727BF0 或 00727C80），
`base_rate` 变 `10 10 10 10 6 0.6000`。

### 7.3 主体本身是析构器的 2 行（0071FA80 / 00726950）

两行是各自类的**删除析构器**（`test byte[esp+0xc],1` + `call 0x7C8B3D` + `ret 4`）。
卡面 ㉓ 只禁止**把析构器当 ④ 锚点**，未禁止析构器作**主体**；两行的 ④ 已另取本类构造器（非本行），符合卡面。
但若 Lead 认为「析构器不宜作已证主体」，扣掉这 2 行 ⇒ 8 行。
（语义栏已写明「删除析构器」，不掩盖。）

### 7.4 主体是 slot5「就地构造」的 2 行（00726860 / 00727BF0）

这两行自身也会 `mov [esi],vt` 重装虚表（slot5 的读入-重构语义）。按「④ 写点须在行体外」，其**自身写点未被采用**，
④ 取本类构造器（00725FA0 / 00726C80）。已逐行在 EVIDENCE 标注 `★本行体内` 并排除。

### 7.5 SAVE 行是薄适配器（6 行）—— ③b② 的最强反对意见与答复

6 行 SAVE（29 B：`mov×3/push×3/call/test/jl/xor/ret`）整函数就是一个转交 + 返回归一，**天然接近「纯转发」**。
判其 ③b② 成立的依据（不是宽松，是可复核的）：
1. 被调方**不是归一化桩**：`00410320` 明确返回 `0x80004003`（空入参）**并原样透出内层负码**（§6.1 三条 `jl` 字节）⇒ 返回值是多值的，本行 `jl` 真的在区分；
2. 两路**返回值不同**（负码原样 vs `xor eax,eax` 归零），不是同一结果的两条到达路径；
3. `R14_COMMON` §12.2 已把**逐字同构**的 `test eax,eax / jl 失败落点保留 eax / 成功 xor eax,eax` 形态判 **③b② 成立（全族 yes）**；
4. 盘上先例：同形状的 `0075E0C0` / `0075E2C0` / `00772CD0` / `00772EB0`（S13_B1，同两个包装）已由 `NAMED_PUSH_AUDIT16` 6/6 PASS 并并表为 `[已证]`。
**对照**：S13 的 `0046C730`（同为 29 B slot6）被判 ③a 纯转发，原因是其被调 `005F9950` **只返 0**（已归一化、本行再幂等归一，无可伪证差值）——被调方是否多值，正是两案的分界。
若 Lead 采取「29 B 转交一律算 ③a」的更严口径，则扣 6 行 ⇒ delta 降为 4 行（0071FA80 / 00726860 / 00726950 / 00727BF0）。

### 7.6 缺口与未能取到的部分

- `fn_`/`sub_` 伪名：S15 **0 个**，本批无「② 物理不可得」类行。
- ② 未用 YRpp 通道（不需要，RTTI 通道对 10 行全部可用）。
- ④ 未使用 direct call 通道（S15 这 10 行 direct caller 全为 0，符合 D-39「虚函数 direct call 恒 0」）。

## 8 · 基础率

```
batch     rows_checked  ring2_ok  ring3b_ok  ring4_ok  all_four  rate
S15_B1    10            10        10         10        10        1.0000
```

`ring2_ok=10` / `ring3b_ok=10` / `ring4_ok=10`，其中 `ring4_ok` 是「形格合格（行外构造器 + 非析构 + 非 atexit）」，
**不含**§7.1 枢轴级同源的判罚（该判罚属 D-47 待裁，本批按现行 D-43(A) 处置计 10）。若按 §7.2 严读 ring4=6、按 §7.1 严读 ring4=0。

## 9 · 与 S04 败因对比

卡面背景：**S04 的 73 个 ③b② 命中全部无名字（named=0）**，36 行实测全败，根因是 **② 类身份取不到**（② 是硬约束）。

本批 S15 的对比读数：

| 维度 | S04 | S15_B1（本批） |
|---|---|---|
| named 命中 | 0 / 73 | 10 / 10 |
| ② 是否钉住 | **0**（无 vtable slot / 无 RTTI，物理不可得） | **10 / 10**：全部可由 `[vt-4]→COL(sig=0)→TD→TD+8 内联名` 独立钉死，且槽号与 `slotN` 自洽 |
| 主要淘汰环节 | ②（物理不可得 ⇒ 全败） | 无环节淘汰；**风险在口径**（§7.1 枢轴共用 / §7.2 装表点共用），不在取证 |
| 结论 | 「② 拿不到 ⇒ 必败」 | 「② 是最容易的一环；S15 的 named 候选几乎全部自带主虚表 + RTTI」 |

**本批 ② 真正钉住 10 / 10 行**（100%）。与 S04 相反：S15 这 10 个命中全是 `Class::slotN` 形态且落在**主虚表**
（`slot0==00410260`），没有一个是 `fn_`/`sub_` 伪名，也没有「只有 direct call、无虚表」的行。
真正的把关点因此从 ② 移到了 ③b 的**可伪证性**与 ④ 的**㉓ 排除**——这两项本批已逐行落到字节。

## 10 · 两处技术条自查（卡面点名）

1. **pTD/pCHD 存绝对 VA 不是 RVA**：本批按绝对 VA 读取，`COL+0xC`=TD（如 `00842B78`）、`COL+0x10`=CHD（如 `0080BAE0`），
   落在 `.rdata 007E1000+30074` 区间内，与「若当 RVA 解则越界」互证。
2. **装饰名在 TD+8 是内联串不是指针**：`TD+0`=pVFTable（如 `007F9594`）、`TD+4`=spare(`0`)、`TD+8` 起直接是 `2e 3f 41 56 ...` = `.?AV<Class>@@`；
   若按「TD+8 取指针」读会得到空串或垃圾（`NAMED_PUSH_AUDIT16` 亦独立记录同一更正）。

## 11 · 产出清单

| 文件 | 内容 |
|---|---|
| `delta.tsv` | **10 数据行**（四环齐全；`entry` 大写无 `0x`；`grade=[已证]`；`name`/`subsystem` 原样） |
| `base_rate.tsv` | `S15_B1  10  10  10  10  10  1.0000` |
| `EVIDENCE\ROW_<entry>.txt` | **10 份**，逐行四环地址+字节（含 ② RTTI 原始字节、③b 站点与被调方字节、④ ㉓ 全写点枚举表、②④ 同源逐行结论） |
| `PROGRESS.md` | 步骤与每 5 行落盘记录 |
| `REPORT.md` | 本文件（整体重写，10 行全部核完并落盘） |
| `_work\` | 自写脚本与中间输出：`recore.py`/`core2.py`（基座）、`ring4_exhaust2.py`（㉓ 全枚举）、`find_callee2.py`（Find 真身）、`gen_evidence2.py`（证据生成）、`write_tsv.py`、`facts_*.txt`、`dump_body.txt`、`vtslot_*.txt` |

未触碰 `coverage.tsv`、`PANEL.md`、`R14_COMMON.md`、台账、`SURVEY_3B2`、`S04_PUSH_*`；只写本批目录。
