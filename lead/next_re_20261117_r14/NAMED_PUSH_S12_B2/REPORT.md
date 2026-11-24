# NAMED-PUSH — S12 B2 批次（有名字的 ③b② 候选，攻 proved 增量）

> 状态：**完成**。执行纪律已遵：先建目录 → 先写 REPORT 骨架 → 逐行核完即落 `EVIDENCE/`；`PROGRESS.md` 每 5 行追加。
> 卡片：`lead\next_re_20261117_r14\_cards\NAMED-PUSH.md`（80 行全文读完）
> 本批：**B2** = `SURVEY_3B2\hits_detail.tsv` 中 `subsystem==S12` AND `p3b2_named==True`，排除 `fn_XXXXXXXX`/`sub_XXXXXXXX` 伪名后按 entry 升序取**第 19..36 个**。
> 实际取到：候选池共 **33** 行（伪名 0 行），第 19..36 个只有 **15** 行存在 ⇒ 本批 **15 行**（`0044EFB0 … 00705CA0`）。这是候选池上界，不是擅自缩量。
> 输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S12_B2\`

## 一、材料自校验

| 项 | 值 | 校验 |
|---|---|---|
| `ra2youli\gamemd.exe` | 期望 `73201CC0…F67476` | 实测 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` ⇒ **逐字一致** |
| ImageBase / `.text` | `0x400000` / `[0x401000, 0x7E038D)` | 与卡面一致 |
| 段表 | `.text 00401000+3E0000` / `.rdata 007E1000+31000` / `.data 00812000+367BE4` / `.rsrc` / `.detour` | pefile 实测；**`.data` rawlen 仅 0x6C000（< VirtualSize）⇒ 尾部是未初始化区，全局 dword 必须靠 `.text` 静态初始化器取，不能直接读文件** |
| 环境 | Python 3.12.10 / capstone 5.0.7（**skipdata=True**）/ pefile 2024.8.26 | 无 venv、未 pip install |

只读输入：`SURVEY_3B2\hits_detail.tsv`（仅当线索）、`W130_atlas\function_atlas.tsv`（仅取函数边界）。写域仅本目录；未改 `coverage.tsv` / `PANEL.md` / `R14_COMMON.md` / 台账 / `SURVEY_3B2` / `S04_PUSH_*`。

## 二、筛选命令（得到本批 15 个 entry）

```powershell
$p = "D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv"
$rows = Import-Csv $p -Delimiter "`t"
$sel  = $rows | Where-Object {
    $_.subsystem -eq 'S12' -and $_.p3b2_named -eq 'True' -and
    $_.name -notmatch '^(fn_|sub_)[0-9A-Fa-f]{8}$' -and $_.name -notmatch '::(fn_|sub_)[0-9A-Fa-f]{8}$'
} | Sort-Object { [Convert]::ToInt32($_.entry,16) }
$b2 = $sel[18..35]   # 第 19..36 个（1-based）；实际只有 15 个可用
$b2 | Format-Table entry,subsystem,name,grade,size,n_call,n_site,n_valid,p3b2_named -AutoSize
```

等价脚本 `_work/filter_b2.py`（`sel[18:36]`，落盘 `_work/rows_b2.json`）。实测：S12 `p3b2_named=True` **33** 行（卡片记 33，一致）；`fn_`/`sub_` 伪名 **0** 行；排除后仍 **33** 行 ⇒ 第 19..33 共 **15** 行入选，第 34..36 个不存在。

## 三、先钉死各对象的「主虚表」（陷阱③ 主动排查）

本批**跨 4 个类**（B1 只有 BuildingClass），所以先把 4 张主表的身份逐张定死，否则 15 行的 ② 会整批走偏。

| 类 | 主虚表 base | 槽 0 | 槽数 | COL | TD | RTTI 名 |
|---|---|---:|---:|---|---|---|
| BuildingClass | `0x007E3EBC` | **`0x00410260`** | 322 | `0x007FC360` | `0x00818D60` | `.?AVBuildingClass@@` |
| BuildingTypeClass | `0x007E4570` | **`0x00410260`** | 49 | `0x007FC618` | `0x008193A8` | `.?AVBuildingTypeClass@@` |
| CaptureManagerClass | `0x007E4B40` | **`0x00410260`** | 24 | `0x007FCB60` | `0x0081B6C8` | `.?AVCaptureManagerClass@@` |
| FactoryClass | `0x007E88D0` | **`0x00410260`** | 24 | `0x00800610` | `0x00822290` | `.?AVFactoryClass@@` |

**同族小表（陷阱③的陷阱）**：每个类另有 3 张「成员/次基类子对象」表，各仅 1/1/6 槽、slot0 为 `00410590/00410580/004105E0`：

- BuildingClass：`0x7E3E90` / `0x7E3E98` / `0x7E3EA0`
- BuildingTypeClass：`0x7E4544` / `0x7E454C` / `0x7E4554`
- CaptureManagerClass：`0x7E4B14` / `0x7E4B1C` / `0x7E4B24`
- FactoryClass：`0x7E88A4` / `0x7E88AC` / `0x7E88B4`

12 张小表逐张核对：**15 行的槽一个都不在这些小表里**，全部落在 slot0=`00410260` 的主表上（`_work/selfcheck.py` 第 1 段对 12×6 个槽位做了显式「不等于 entry」断言）。

## 四、判定口径（严格 D-40 / D-43，宁严不宽）

1. **① 入口**：entry 在 `.text` 内、atlas 边界自洽、`skipdata` 计数、末条指令形态。
2. **② 类身份**：**独立取证**——entry 作 4B VA 所在槽 → 回扫 `[vt-4]=COL(sig=0)` → `[COL+0xC]=TD` → `TD+8` 名串 `.?AV…@@`；并同时要求 (a) RTTI 名与线索类一致、(b) **槽号 = 槽偏移/4 等于线索 N（由字节复算，不反推）**、(c) 该表是对象主虚表（槽 0 = `00410260`）。线索里的 `Class` 只作对照。
3. **③ 整体合同**：只认 ③b。本批实际检验 **③b②**（call → test/cmp 判据寄存器 → jcc，被调返回约定可伪证、调用方真的拿它分支、两路动作真不同、比较与跳转间无判据寄存器覆写、单 call 非多路同一 call）。禁 ③a（纯转发/单调用+单写/**零+默认**/无分支直线）与模板假句。
4. **④ 使用见证**：活虚表派发 —— 构造期 `.text` 安装点（`mov [mem], vt`）把主表写入活对象，**行外、非 atexit**；direct-only 不足。**与 ② 不同源**：② 锚 `.rdata` RTTI 数据链 + 槽值 4B，④ 锚 `.text` 构造安装指令字节。
5. **三陷阱逐行排查**：eax/判据寄存器覆写 / 多路同一 call / 模板假句。
6. **㉓ 成对陷阱（本批**必须**处理，因为两行的 entry 本身就是析构器）**：④ 锚点若落在析构器（atexit 表或删除式析构签名）内 ⇒ 该锚点弃用。本批 8 个构造安装点 atexit 全空、均带构造器特征；4 个**析构器重装点**已识别并排除（见 §七 ④）。

### 判号线（与 D-46(A) 一致）

- 接受：**容器 `Find` 的「未命中 = -1 / 命中 = 下标」**（字节 `or eax,0xFFFFFFFF; ret 4`）；**具名 HRESULT**（如 `0x80004003` E_POINTER；失败 = 负、成功 = 0/非负，落点不碰 eax）；**可枚举多值状态码集合**。
- 不接受：`{0,1}` 布尔主输出；**NULL 判空**（任何 `new`/分配都满足，区分力为零）；**`零+默认`**（`if (找不着/为 0) 用原值`）；数值范围/几何阈值；状态/类型常量比较。

**③b①/③b③/③b④ 全批不存在（实测，非假设）**：对 15 行逐一跑 `core.jumptables()`（`jmp [table+idx*4]` + 前置 `cmp idx,imm` 形态）⇒ **15/15 全为 0 张跳转表**，故本批不存在可计入 ③b① 的形态；亦无内存形状断言（③b③）与带非栈写的完整循环 I/O（③b④）被用作成立通道。

## 五、基础率（诚实报数）

| 档 | 行数 | 口径 |
|---|---:|---|
| 本批行数 | **15** | S12 named=True 排除伪名后升序第 19..33（池上界） |
| ① 入口 PASS | **15** | 全部在 `.text`；atlas 边界逐行对齐到指令末，`skipdata=0` 15/15 |
| ② 类身份钉住 | **15** | 15/15 槽号 == 线索 N 且槽值 == entry，RTTI = 线索类，主表槽 0 = `00410260` |
| ③b 成立 | **6** | 全为 ③b② |
| ④ 使用见证成立 | **15** | 15 行槽均位于由构造器装入活对象的主虚表内；8 处构造安装点 atexit 全空 |
| **四环齐全** | **6** | rate = 6/15 = **0.4000** |

`base_rate.tsv`：`S12_B2	15	15	6	15	6	0.4000`

## 六、本批 15 行总表

| # | entry | name（原样） | ① | ② | ③ | ④ | ②④不同源 | 裁定 | 产出 |
|---:|---|---|---|---|---|---|---|---|---|
| 19 | 0044EFB0 | BuildingClass::vslot309 | PASS | PASS | FAIL | PASS | 是 | 不成立 | 否 |
| 20 | 00453E20 | BuildingClass::vslot5 | PASS | PASS | **PASS(③b②)** | PASS | 是 | **成立** | **是** |
| 21 | 00454190 | BuildingClass::vslot6 | PASS | PASS | FAIL | PASS | 是 | 不成立 | 否 |
| 22 | 00456750 | BuildingClass::vslot76 | PASS | PASS | FAIL | PASS | 是 | 不成立 | 否 |
| 23 | 0045E800 | BuildingTypeClass::slot32 | PASS | PASS | FAIL | PASS | 是 | 不成立 | 否 |
| 24 | 0045E880 | BuildingTypeClass::slot35 | PASS | PASS | FAIL | PASS | 是 | 不成立 | 否 |
| 25 | 0045EBD0 | BuildingTypeClass::slot30 | PASS | PASS | FAIL | PASS | 是 | 不成立 | 否 |
| 26 | 0045F040 | BuildingTypeClass::slot39 | PASS | PASS | FAIL | PASS | 是 | 不成立 | 否 |
| 27 | 0045FE50 | BuildingTypeClass::slot25 | PASS | PASS | FAIL | PASS | 是 | 不成立 | 否 |
| 28 | 00465300 | BuildingTypeClass::slot6 | PASS | PASS | **PASS(③b②)** | PASS | 是 | **成立** | **是** |
| 29 | 004728E0 | CaptureManagerClass::slot6 | PASS | PASS | **PASS(③b②)** | PASS | 是 | **成立** | **是** |
| 30 | 004729C0 | CaptureManagerClass::slot8 | PASS | PASS | **PASS(③b②)** | PASS | 是 | **成立** | **是** |
| 31 | 004CA3C0 | FactoryClass::slot6 | PASS | PASS | **PASS(③b②)** | PASS | 是 | **成立** | **是** |
| 32 | 004CA770 | FactoryClass::slot8 | PASS | PASS | **PASS(③b②)** | PASS | 是 | **成立** | **是** |
| 33 | 00705CA0 | BuildingClass::slot267 | PASS | PASS | FAIL | PASS | 是 | 不成立 | 否 |

## 七、逐行裁定依据（每行自身地址锚；字节见 `EVIDENCE/ROW_<entry>.txt`）

### ② 15/15（槽号与槽值均由字节复算，非反推）

| # | entry | 类 | 主表 vt | 槽 VA | 槽内 4 B | slot# | 与线索 N | RTTI 名 |
|---:|---|---|---|---|---|---:|---|---|
| 19 | 0044EFB0 | BuildingClass | 007E3EBC | 007E4390 | `b0 ef 44 00` | 309 | ✔ | .?AVBuildingClass@@ |
| 20 | 00453E20 | BuildingClass | 007E3EBC | 007E3ED0 | `20 3e 45 00` | 5 | ✔ | 同上 |
| 21 | 00454190 | BuildingClass | 007E3EBC | 007E3ED4 | `90 41 45 00` | 6 | ✔ | 同上 |
| 22 | 00456750 | BuildingClass | 007E3EBC | 007E3FEC | `50 67 45 00` | 76 | ✔ | 同上 |
| 23 | 0045E800 | BuildingTypeClass | 007E4570 | 007E45F0 | `00 e8 45 00` | 32 | ✔ | .?AVBuildingTypeClass@@ |
| 24 | 0045E880 | BuildingTypeClass | 007E4570 | 007E45FC | `80 e8 45 00` | 35 | ✔ | 同上 |
| 25 | 0045EBD0 | BuildingTypeClass | 007E4570 | 007E45E8 | `d0 eb 45 00` | 30 | ✔ | 同上 |
| 26 | 0045F040 | BuildingTypeClass | 007E4570 | 007E460C | `40 f0 45 00` | 39 | ✔ | 同上 |
| 27 | 0045FE50 | BuildingTypeClass | 007E4570 | 007E45D4 | `50 fe 45 00` | 25 | ✔ | 同上 |
| 28 | 00465300 | BuildingTypeClass | 007E4570 | 007E4588 | `00 53 46 00` | 6 | ✔ | 同上 |
| 29 | 004728E0 | CaptureManagerClass | 007E4B40 | 007E4B58 | `e0 28 47 00` | 6 | ✔ | .?AVCaptureManagerClass@@ |
| 30 | 004729C0 | CaptureManagerClass | 007E4B40 | 007E4B60 | `c0 29 47 00` | 8 | ✔ | 同上 |
| 31 | 004CA3C0 | FactoryClass | 007E88D0 | 007E88E8 | `c0 a3 4c 00` | 6 | ✔ | .?AVFactoryClass@@ |
| 32 | 004CA770 | FactoryClass | 007E88D0 | 007E88F0 | `70 a7 4c 00` | 8 | ✔ | 同上 |
| 33 | 00705CA0 | BuildingClass | 007E3EBC | 007E42E8 | `a0 5c 70 00` | 267 | ✔ | .?AVBuildingClass@@ |

15/15 全部 `[-4] = COL(sig=0)`、`[COL+0xC] = TD` → 名串与线索类一致，**15/15 钉住**。

### ③ 成立 6 行（各自独立站点与语义）

- **`00453E20` BuildingClass::vslot5 — 建筑对象从存档流载入（③b②）**
  站点 `0x453EB3` `e8 98 80 2b 00` = `call 0x70BF50`；`0x453EB8` `3b c3` = `cmp eax,ebx`（`ebx` 由 `0x453E46` `33 db` = `xor ebx,ebx` 置 0，即 `cmp eax,0`）；`0x453EBA` `89 44 24 10` 只把 hr 存栈（**不是 eax 覆写**）；`0x453EBE` `0f 8c ba 02 00 00` = `jl 0x45417E`。
  - 失败落点 `0x45417E` 是纯收尾 `pop edi; pop esi; pop ebp; pop ebx; pop ecx; c2 08 00`(ret 8)，**不碰 eax** ⇒ 负 HRESULT 原样上抛；成功路径跑到 `0x454170` `8b 44 24 10` 返回同一个 hr（≥0）。
  - 被调 `0x70BF50` 的约定同样字节可读：`0x70BF5C call 0x65AB80` → `0x70BF61 33 db` → `0x70BF63 3b c3` → `0x70BF65 0f 8c de 02 00 00` jl `0x70C249`（收尾不碰 eax）；成功尾部 `0x70C246 8b c3` = `mov eax,ebx`(=0) → `0x70C24B c2 08 00` —— **失败负值 / 成功 0**。
  - 两路动作完全不同：失败直接跳过整段反序列化（成员向量、指针数组、15+3+8 个成员指针的读回全不做）；成功逐段 `call [ecx+0xc]` 读回后返回 0。
  - 另三站点 `0x453FED` / `0x45407A` / `0x45409C` 的 `test eax,eax; jl 0x45417E` 是同一函数的次要出口、同落点。

- **`00465300` BuildingTypeClass::slot6 — 建筑类型副本从存档流载入（③b②）**
  站点 `0x465313` `e8 a8 1a 2b 00` = `call 0x716DC0`；`0x465318` `85 c0` = `test eax,eax`；`0x46531A` `7c 4e` = `jl 0x46536A`。失败落点 `0x46536A` 是收尾 `pop edi; pop esi; pop ebp; pop ebx; c2 0c 00`（不碰 eax ⇒ 负值原样返回）；成功走到 `0x465368` `33 c0` = `xor eax,eax` 再落同一收尾 ⇒ 返回 0。
  - 被调 `0x716DC0`：`0x716DD1 call 0x5F9950` → `0x716DD6 85 c0` → `0x716DD8 0f 8c b6 02 00 00` jl `0x717094`（该路径因 `ebx` 尚未 push 而合法跳过 `0x717093 pop ebx`，落点不碰 eax）；成功侧 `0x717091 33 c0` → `0x717096 c2 0c 00` ⇒ **成功 0 / 失败负值**。
  - 两路动作不同：失败跳过整段记录读取（`[+0x178C]` 计数与 `[+0x1788]+i*0xC` 记录数组全不读）；成功读回后返回 0。
  - 另两站点 `0x465332` / `0x465355` 为 `call [edx+0x10]` 流 Read 后的 `test eax,eax; jl 0x46536A`，同落点。

- **`004728E0` CaptureManagerClass::slot6 — 从流载入（③b②，具名 HRESULT）**
  站点 `0x4728F3` `e8 28 da f9 ff` = `call 0x410320`；`0x4728F8` `8b f8` = `mov edi,eax`；`0x4728FA` `85 ff` = `test edi,edi`；`0x4728FC` `89 7c 24 18` 只把 hr 存栈；`0x472900` `7c 54` = `jl 0x472956`；落点 `0x472956` `8b c7` = `mov eax,edi` → `0x47295C c2 0c 00` ⇒ **负 HRESULT 原样上抛**。
  - 被调 `0x410320`（87 B）返回集字节可枚举：`0x41032B` `b8 03 40 00 80` = `mov eax,0x80004003`（**E_POINTER**）→ `0x410331 c2 0c 00`；成功侧 `0x410374 c2 0c 00` ret 0xc 不碰 eax，原样传出内层 COM 调用 HRESULT；入口 `0x410325 85 f6` / `0x410327 75 0a` jne 把空指针引到 E_POINTER 出口。
  - 两路动作不同：失败直接返回错误码并跳过整个读循环；成功继续 `call [edx+0x10]` 读回计数与每项两个 dword。另两站点 `0x472915` / `0x472942` 为流 Read 的 `test eax,eax; jl 0x472958`。

- **`004729C0` CaptureManagerClass::slot8 — 删除式析构器，全局容器 Find(-1) + 压缩移除（③b②）**
  站点 `0x4729F3` `ff 52 10` = `call dword ptr [edx+0x10]`；`edx` 由 `0x4729E8` `8b 15 f0 e0 89 00` = `mov edx,[0x89E0F0]`（全局容器 vptr），this 由 `0x4729C8` `b9 f0 e0 89 00` 传入；`0x4729F6` `83 f8 ff` = `cmp eax,-1`；`0x4729F9` `74 2d` = `je 0x472A28`。
  - 被调可字节钉死：全局 `0x89E0F0` 的**静态初始化器** `0x47176D` `c7 05 f0 e0 89 00 d4 4a 7e 00` 写入 vtable `0x007E4AD4`（`.data` raw 不够长时这是唯一可取法）；`[-4] @0x7E4AD0 = 0x007FCA18`（COL, sig=0）→ TD `.?AV?$DynamicVectorClass@PAVCaptureManagerClass@@@@`；slot4（`0x7E4AE4` = `+0x10`）= `0x00472FD0` = Find，其 `0x472FEF` `83 c8 ff` = `or eax,0xFFFFFFFF`、`0x472FF3 c2 04 00` = `ret 4` ⇒ **未命中 = -1、命中 = 下标**。
  - 两路动作真不同：未命中跳 `0x472A28` 跳过整段移除；命中则 `0x472A05 49`(dec ecx) / `0x472A08 89 0d 00 e1 89 00` 回写计数、`0x472A17 8b 14 81` / `0x472A1A 89 54 81 fc` 前移压缩（**写全局数组，非栈写**）。

- **`004CA3C0` FactoryClass::slot6 — 从流载入（③b②，具名 HRESULT）**
  站点 `0x4CA3D2` `e8 49 5f f4 ff` = `call 0x410320`；`0x4CA3D7` `85 c0` = `test eax,eax`；`0x4CA3D9` `7c 44` = `jl 0x4CA41F`；失败落点 `0x4CA41F` 是收尾（不碰 eax ⇒ 负值原样上抛）；成功走到 `0x4CA41D` `33 c0` = `xor eax,eax` 再落同一收尾 ⇒ 返回 0。
  - 被调 `0x410320` 同上（E_POINTER `0x80004003` / 成功 ≥0）。
  - 另两站点 `0x4CA3EE` / `0x4CA40D` 是流 Read 的 `test eax,eax; jl`——其中 `0x4CA40D` 跳 `0x4CA41D` 走 `xor eax,eax`（**吞错返 0**），这正反证只有 `0x4CA3D9` 那条是上抛路径，两路差别是实质的而非同一落点。

- **`004CA770` FactoryClass::slot8 — 删除式析构器，两个不同全局容器的 Find(-1) + 压缩移除（③b②，双站点）**
  - 站点一 `0x4CA7AA` `ff 52 10`，`edx` 由 `0x4CA796` `8b 15 30 3e a8 00` = `mov edx,[0xA83E30]`，this 由 `0x4CA7A1 b9 30 3e a8 00` 传入；`0x4CA7AD` `83 f8 ff` cmp -1 / `0x4CA7B0` `74 2d` je `0x4CA7DF`。该全局初始化器 `0x4E6E7D` `c7 05 30 3e a8 00 a4 9f 7e 00` 写 vtable `0x007E9FA4`；`[-4] @0x7E9FA0 = 0x00801610`（sig=0）→ `.?AV?$DynamicVectorClass@PAVFactoryClass@@@@`；slot4（`0x7E9FB4`）= `0x004EC2D0` = Find（`0x4EC2EF` `83 c8 ff` / `0x4EC2F3 c2 04 00`）。
  - 站点二 `0x4CA803` `ff 52 10`，`edx` 由 `0x4CA7EF` `8b 15 20 f7 b0 00` = `mov edx,[0xB0F720]`；`0x4CA806` `83 f8 ff` / `0x4CA809` `74 2d` je `0x4CA838`。该全局初始化器 `0x7252ED` `c7 05 20 f7 b0 00 ec 91 7e 00` 写 vtable `0x007E91EC`；`[-4] @0x7E91E8 = 0x008009B0`（sig=0）→ `.?AV?$DynamicVectorClass@PAVAbstractClass@@@@`；slot4（`0x7E91FC`）= `0x004E0550` = Find（`0x4E056F 83 c8 ff` / `0x4E0573 c2 04 00`）。
  - 两站点同构：未命中跳过该容器移除；命中则回写计数 + 全局数组前移压缩（**非栈写**）。

### ③ 不成立 9 行（逐行独立理由，各自站点地址）

| # | entry | 站点（行内地址） | 不成立原因 |
|---:|---|---|---|
| 19 | 0044EFB0 | `0x44F3CD call 0x45EC90` → `0x44F3D2 cmp eax,-1` / `0x44F3D5 jl 0x44F4A7`；`0x44F4C3 call 0x45ECA0` → `0x44F4C8 cmp eax,-1` / `0x44F4CB jl 0x44F59F`；另 12 处 `call [edi+0x1ac]` 后 `test eax,eax` | 两个直接被调只有 14 B / 61 B，纯全局表取值（`[eax*4+0x8192B8]`、`[eax*4+0x819310]+1`），**无返回常量、无错误码**；同函数 `0x44F49A call 0x45EC90` 后 `0x44F49F cmp ebp,eax` / `0x44F4A1 jle` 自证它是**循环上界**；其余是外来对象 slot 107 后的非空早退 |
| 21 | 00454190 | `0x4541A3 call 0x70C250` → `0x4541A8 mov ebp,eax` / `0x4541AA test ebp,ebp` / `0x4541AC jl 0x454242`；另 4 处 `call [edx+0x10]` 后 `test eax,eax; jl 0x454244` | **被调 `0x70C250` 仅 25 B，尾 `0x70C264 33 c0` = `xor eax,eax` / `0x70C266 c2 0c 00`，唯一返回路径恒返 0 ⇒ 该 `jl` 是死分支**（不构成「调用方真的拿它分支」）；其余为运行期流对象间接调用，被调类不可静态定 |
| 22 | 00456750 | `0x456757 call 0x4566B0` → `0x45675C test eax,eax` / `0x45675E jle 0x456962` | 被调 5 条返回路径全是业务数值 getter（`movsx eax,cl` 取 `[Type+0xCD3]`/`[CD2]`/`[1707]`、`([edi+0xB4]>>8)`、0），返回集「若干业务量 ∪ 0」，`jle` 是数值判定 ⇒ ③a 零+默认家族 |
| 23 | 0045E800 | `0x45E80B call 0x7C8E17` → `0x45E813 test eax,eax` / `0x45E815 je 0x45E86D`；`0x45E81F call 0x43B740` → `0x45E824 test eax,eax` / `0x45E826 je 0x45E86D` | 分配结果判空 + 构造器返回 this 的指针判空，落点 `0x45E86D 32 c0` 返回 false —— bool 主输出（D-46(A) 不算） |
| 24 | 0045E880 | `0x45E888 call 0x7C8E17` → `0x45E890 test eax,eax` / `0x45E892 je 0x45E8A5` | 43 B 的 new+construct 薄壳，`0x45E8A5 33 c0` 分配失败返 NULL，纯指针判空 |
| 25 | 0045EBD0 | `0x45EBD5 call [eax+0x9c]`(slot 39 = `0045F040`) → `0x45EBDB test eax,eax` / `0x45EBDD je 0x45EC02` | 被调返回「指针或 0」，此处判指针是否为空；两路只是「复制 16 B」与「写 0」的默认值分支 ⇒ ③a 零+默认 |
| 26 | 0045F040 | `0x45F093 call 0x4A3890` → `0x45F098 test eax,eax` / `0x45F0A0 je 0x45F0AB`；`0x45F0DF call 0x4A3890` → `0x45F0E4 test eax,eax` / `0x45F0EC je 0x45F0F5` | 被调 56 B 全部汇到 `0x4A38C2 8b c7` 返回分配到的指针或 0 ⇒ NULL 判空；非零路 `0x45F0A2 c6 86 a8 00 00 00 01` 只是置成功标志位 |
| 27 | 0045FE50 | 28 站点：`call 0x528A10`×17、`call 0x7514D0`×7、`call 0x5276D0`×3、`call 0x474DA0`×1 | ①`0x528A10` 返「0 或正长度」（`0x528BC0 33 c0` / `0x528BF4 8b c1`），判翻译串是否为空；②`0x7514D0` Find(-1) 后 `0x460770 75 02` jne 与 `0x460772 8b c7` 之间**只差一条默认值回填** ⇒ ③a 零+默认；③配置量解析/名字查表返回「旧默认值或解析值」，`0x464743 0f 8e` jle 是数值范围判定 |
| 33 | 00705CA0 | `0x705CA8 call [eax+0x184]`(slot 97) → `0x705CAE cmp eax,1` / `0x705CB1 jne 0x705CE6`；`0x705CB9 test ecx,ecx` / `0x705CBB je 0x705CE6` | slot 97 是字段 getter（`[this+0xAC]`，-1 时取 `[this+0xB4]`），`cmp eax,1` 比**建筑状态常量**；后者是对 `[esi+0x2B4]` 的指针判空。两路只是「从子对象取 12 B」与「从 this+0x9C 取 12 B」|

### ④ 15/15（活虚表派发，行外、非 atexit，且已剔析构器锚点）

**8 个构造安装点**（`mov [mem],vt`，atexit 全空）：

| 类 | 安装点 | in_func | 字节 | 构造器判据 |
|---|---|---|---|---|
| BuildingClass | `0x0043B71F` | `0043B680` | `c7 06 bc 3e 7e 00` | 收尾 `mov eax,esi; pop esi; ret 4` 返 this |
| BuildingClass | `0x0043B9FA` | `0043B740` | `c7 06 bc 3e 7e 00` | 收尾 `mov eax,esi; …; ret 8` 返 this |
| BuildingTypeClass | `0x0045E2CD` | `0045DD90` | `c7 06 70 45 7e 00` | `ret 4`，函数体无 free、无基类析构调用 |
| BuildingTypeClass | `0x0045E558` | `0045E520` | `c7 06 70 45 7e 00` | 收尾 `mov eax,esi; pop esi; ret 4` 返 this |
| CaptureManagerClass | `0x00471807` | `004717D0` | `c7 06 40 4b 7e 00` | 收尾把 this 挂进全局表 `0x89E0F4` 后 `mov eax,esi; ret 0xc` |
| CaptureManagerClass | `0x004718BC` | `00471890` | `c7 06 40 4b 7e 00` | 收尾 `mov eax,esi; ret` 返 this |
| FactoryClass | `0x004C991A` | `004C98B0` | `c7 06 d0 88 7e 00` | 收尾把 this 挂进容器后 `mov eax,esi; ret`，函数体无 free |
| FactoryClass | `0x004CA2C7` | `004CA270` | `c7 07 d0 88 7e 00` | 在调用方给的 `[edi]` 处实地构造并写两张子表，无 free/基类析构 |

**4 个析构器重装点 —— 按 ㉓ 一律弃用**（本批两行的 entry 本身就是析构器，所以这条必须处理）：

| 类 | 安装点 | in_func | 析构器判据 |
|---|---|---|---|
| BuildingClass | `0x0043BCFD` | `0043BCF0` | 返回 void（`pop ecx; ret`）+ 2 处 `call 0x7C8B3D`(free) + 尾部 `call 0x6F4500` 基类析构 |
| BuildingTypeClass | `0x0045E58D` | `0045E580` | 返回 void + 8 处 `call 0x7C8B3D` + 尾部 `call 0x711AE0` 基类析构 |
| CaptureManagerClass | `0x004729CD` | `004729C0` | `test byte ptr [esp+0xc],1` + 2 处 free + `call 0x4101F0` ⇒ 删除式析构器 |
| FactoryClass | `0x004CA776` | `004CA770` | `test byte ptr [esp+0xc],1` + 2 处 free + `call 0x4101F0` ⇒ 删除式析构器 |

⇒ **㉓ 成对陷阱已排除**：15 行的 ④ 全部锚在构造安装点；`004729C0` / `004CA770` 两行虽自身是析构器，其 ④ 改锚同类构造器（`0x471807` / `0x4C991A`），未用自身重装点。

直接调用者：仅 `00705CA0` 有 1 个（`0x004D85A6`），其余 14 行 0 个——但 ④ 不靠 direct，靠**活虚表链**，故不触「direct-only 不足」。

> 说明（诚实标注）：本批按 ②④ 不同源 + 槽在已安装主表内 的口径判 ④，与 B1 一致。我另外扫了「`call [reg+disp]` 且 disp = 4*slot」的真实派发站点，但**disp 存在跨类碰撞**（如 disp `0x18` 全镜像 365 处、涉及大量非本类对象），单凭 disp 无法把派发点归属到本类，故不作为 ④ 主证。个别行可指认（如 `00456750` slot 76 disp `0x130` 仅 2 处：`0x6DBE69` / `0x6DC194`，均在 `006DBE20` 内；`00705CA0` slot 267 disp `0x42C` 仅 2 处：`0x63B94F` / `0x63C25D`），但因未钉死调用点对象的静态类型，仍不升格为证据。

## 八、与 S04 的败因对比（本批有多少行 ② 真的钉住了）

- **S04**：73 个 ③b② 机械命中 **`p3b2_named = 0`**（全无名字）——entry 作 4B VA 全镜像 0 命中、无虚表槽、无可回扫 RTTI 链 ⇒ **② 物理不可得**，36 行实测全败。
- **本批 S12 B2**：15 行里 **15 行 ② 全部被 RTTI + 主虚表独立钉死（15/15 = 100%）**，槽号由字节复算后与线索 `slotN`/`vslotN` 的 N **逐行相等**。本批 **0 行** 落入「② 物理不可得」。
- **候选池质量**：S12 的 33 个 named 候选**全部是 `Class::slotN` / `Class::vslotN` 形态**，`fn_`/`sub_` 伪名 **0 个**（对比 S14 的 51 个里有 16 个 `fn_`）⇒ ② 在 S12 不是瓶颈。
- **瓶颈仍是 ③**：15 行里 ② 15/15、④ 15/15，但 ③ 只有 **6/15（40.0%）**。9 行 ③ 失败的分布：**3 行**「NULL 判空 / 分配失败返回 NULL」（`0045E800`/`0045E880`/`0045F040`）、**2 行**「指针非空 + 零默认」（`0045EBD0`/`0044EFB0` 的 indirect 站群）、**1 行**「被调恒返 0 ⇒ 死分支」（`00454190`）、**1 行**「数值 getter + 范围判定」（`00456750`）、**1 行**「配置量查表 + 默认值回填」（`0045FE50`）、**1 行**「状态常量比较 + 空指针」（`00705CA0`）。
- 与 B1 的 0.2222 相比本批 **0.4000 明显更高**，原因是**样本性质变了**：B1 的 18 行全是 `BuildingClass` 的谓词型实例方法（查状态/查类型后早退，天生缺可伪证错误码）；B2 的 15 行里出现了 **save/load 序列化对**（`00453E20`/`00454190`、`00465300`、`004728E0`、`004CA3C0`）和 **删除式析构器**（`004729C0`/`004CA770`）——这两类正是产生「HRESULT 上抛」与「容器 Find(-1) + 压缩移除」的富矿。B1 已指出 4 个成立行里 2 个是 Find 型、2 个是状态码型；本批 6 个成立行是 **4 个 HRESULT 型 + 2 个 Find 型**。

## 九、待裁（3 项，未擅自扩面）

1. **HRESULT `test/jl` 形态是否计入 ③b②（影响 ±4 行）**：本批 4 个成立行（`00453E20`/`00465300`/`004728E0`/`004CA3C0`）走的是「被调返回负 HRESULT = 失败、0/非负 = 成功；失败落点不碰 eax 原样上抛」。这与 `R14_COMMON.md` 记的 ENGFAM 先例（「失败落点 eax 原样返回（不清零）；成功路径 `xor eax,eax` 返回 0」已判 ③b② 成立）同形，且 `004728E0`/`004CA3C0` 的被调 `0x410320` 有**具名常量** `0x80004003` E_POINTER，`0x70BF50`/`0x716DC0` 有「成功 0」字节。若 Lead 认定「必须是可枚举小常量集合、负 HRESULT 不算」，则 **−4 → 2/15（0.1333）**；我判成立，理由是 D-46(A) 的反面是「bool 主输出」，而 HRESULT 的失败/成功是**两值之外的符号分区 + 具名错误码**，且两路动作实质不同（失败跳过整段序列化）。
2. **`00454190` 的间接流 Read `test/jl` 是否间接地算（影响 ±1 行）**：该行 4 个站点都是 `call [edx+0x10]`（COM IStream::Read 式）后 `test eax,eax; jl 0x454244`，落点不碰 eax ⇒ 若「间接调用的 HRESULT 约定」可按接口惯例认定，本行也成立（+1 → 7/15 = 0.4667）。我**未计**，因为被调对象是运行期传入、静态不可钉死，与 `00453E20` 有**直接**被调 `0x70BF50` 可读字节的情况不可同日而语——这一行恰好是对偶对里「被调恒返 0」的那一半（`0x70C250` 25 B 尾部 `xor eax,eax; ret 0xc`），是本批最干净的一条负结果。
3. **两个析构器行（`004729C0`/`004CA770`）的 ③ 是否受「④ 落在析构器」牵连**：卡面 ㉓ 只说「④ 锚点落在析构器里判 FAIL」。这两行的 **entry 本身**就是删除式析构器，我把 ④ 改锚到同类**构造器**安装点（`0x471807`/`0x4C991A`），未用自身 vptr 重装点，故判 ④=PASS、四环齐全。若 Lead 认为「entry 是析构器 ⇒ 整行不予 proved」（即便 ④ 另锚），则 **−2 → 4/15（0.2667）**。我按字面口径判成立。

## 十、汇总

- rows_checked：**15**（S12 named=True 排除伪名后升序第 19..33，池上界）
- ② 钉住行数：**15**（15/15；槽号字节复算，4 张主表 slot0 均 `00410260`，小表 12 张逐张排除）
- ③b 成立行数：**6**（全为 ③b②：`00453E20` / `00465300` / `004728E0` / `004729C0` / `004CA3C0` / `004CA770`）
- ④ 成立行数：**15**（8 个构造安装点、atexit 全空；4 个析构器重装点按 ㉓ 排除）
- all_four_rings（严格 D-40/D-43）：**6**，rate = **0.4000**
- delta 产出：**6 行**，entry 大写十六进制无 `0x`，每行独立 reason（脚本校验 6 列 / 无重复 reason / 证据文件均存在）

## 十一、输出清单

- `delta.tsv`（6 行 / 6 列）、`base_rate.tsv`（`S12_B2 15 15 6 15 6 0.4000`）、`PROGRESS.md`、`REPORT.md`（本文件）
- `EVIDENCE/ROW_<entry>.txt` × 15（逐行四环地址与字节，每行独立锚点）
- `_work/`：`core.py`（PE/capstone/RTTI/安装点/atexit/③b②/跳表）、`filter_b2.py` + `rows_b2.json`（筛选）、`prep.py`（材料校验 + 4 类 COL/vtable 全扫）、`rings124.py` + `rings12.json`（① ② ④ 底账 + 安装点）、`ring4.py` + `ring4.json`（安装点构造器/atexit 判定 + disp 派发站点扫描 + direct callers）、`ring3_scan.py` + `ring3_sites.json`（机械 ③b② 站点）、`ring3_broad.py` + `ring3_broad.json`（**广义复扫：直接+间接 call、`cmp r,reg` 与 `mov r,eax` 搬移形态**）、`ctx.py` + `body_*.txt`（逐行反汇编）、`gen_evidence.py`（产物生成）、`selfcheck.py`（**产物自校验：15 行 ② 槽值/COL/TD/RTTI/槽0、8 个构造安装点、6 个成立行站点字节与被调落点不写 eax、产物一致性与格式**，当前全绿 0 失败）、`indep_check.py`（**独立复核：不用 core.py 任何辅助，自己用 pefile 段表做 VA→文件偏移换算，重读 15 行槽字节 / 4 个类 RTTI 名串 / 6 行关键站点字节 / 8 个安装点立即数 / 3 个全局容器静态初始化器**，当前全绿 0 失败——用以排除辅助层系统性错误）
- 全部只读目标，可复算；未触碰 `coverage.tsv` / `PANEL.md` / `R14_COMMON.md` / 台账 / `SURVEY_3B2` / `S04_PUSH_*`。
