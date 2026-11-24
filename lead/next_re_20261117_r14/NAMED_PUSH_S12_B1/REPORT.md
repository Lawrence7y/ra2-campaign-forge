# NAMED-PUSH — S12 B1 批次（有名字的 ③b② 候选，攻 proved 增量）

> 状态：**完成**。执行纪律已遵：先建目录 → 先写 REPORT 骨架 → 逐行核完即落 `EVIDENCE/`；`PROGRESS.md` 每 5 行追加。
> 卡片：`lead\next_re_20261117_r14\_cards\NAMED-PUSH.md`（80 行全文读完）
> 本批：**B1** = `SURVEY_3B2\hits_detail.tsv` 中 `subsystem==S12` AND `p3b2_named==True`，排除 `fn_XXXXXXXX`/`sub_XXXXXXXX` 伪名后按 entry 升序取**前 18 个**。
> 输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S12_B1\`（卡片 `<你的子系统>`=S12、`<你的目录>`=本目录）。

## 一、材料自校验

| 项 | 值 | 校验 |
|---|---|---|
| `ra2youli\gamemd.exe` | 期望 `73201CC0…F67476` | 实测 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` ⇒ **逐字一致** |
| ImageBase / `.text` | `0x400000` / `[0x401000, 0x7E038D)` | 与卡面一致 |
| 段表 | `.text 00401000+3E0000` / `.rdata 007E1000+31000` / `.data 00812000+367BE4` / `.rsrc` / `.detour` | 由 pefile 实测 |
| 环境 | Python 3.12.10 / capstone 5.0.7（**skipdata=True**）/ pefile 2024.8.26 | 无 venv、未 pip install |

只读输入：`SURVEY_3B2\hits_detail.tsv`（仅当线索）、`W130_atlas\function_atlas.tsv`（仅取函数边界）。写域仅本目录；未改 `coverage.tsv` / `PANEL.md` / `R14_COMMON.md` / 台账 / `SURVEY_3B2` / `S04_PUSH_*`。

## 二、筛选命令（得到本批 18 个 entry）

```powershell
$p = "D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv"
$rows = Import-Csv $p -Delimiter "`t"
$sel  = $rows | Where-Object {
    $_.subsystem -eq 'S12' -and $_.p3b2_named -eq 'True' -and
    $_.name -notmatch '^(fn_|sub_)[0-9A-Fa-f]{8}$' -and $_.name -notmatch '::(fn_|sub_)[0-9A-Fa-f]{8}$'
} | Sort-Object { [Convert]::ToInt32($_.entry,16) }
$b1 = $sel[0..17]   # 前 18 个
$b1 | Format-Table entry,subsystem,name,grade,size,n_call,n_site,n_valid,p3b2_named -AutoSize
```

结果：S12 `p3b2_named=True` 共 **33** 行（卡片记 33，**一致**）；其中 `fn_` / `sub_` 地址式伪名 **0 行** ⇒ 排除后仍 **33** 行，本批取升序前 18 个（`0043C2D0 … 0044EBF0`）。等价脚本 `_work/filter_b1.py`（`rows.sort(key=int(entry,16))[:18]`，`rows_b1.json` 落盘）。

> **与 S14 B2 的一个重要差别**：S14 的 51 个 named 候选里 16 个是 `fn_` 伪名；S12 的 33 个 named 候选中**一个都没有**——全部是 `Class::vslotN` 形态。所以本批不存在「② 物理不可得」的整段空白，② 的可用率来自结构本身。

## 三、先钉死「对象主虚表」（陷阱③ 主动排查）

任务卡点名：**不要把「小成员表的 vtable」当对象主虚表，真主虚表槽 0 常见 `00410260`**。S12 的 `vslotN` 到底指哪张表，必须先定死，否则 18 行的 ② 会全体走偏。

`.rdata` 里 `. ?AVBuildingClass@@` 共有 **4 个 COL** ⇒ 4 张表（多继承子对象布局）：

| vtable base | 槽 0 | 判定 |
|---|---|---|
| **`0x007E3EBC`** | **`0x00410260`** | **对象主虚表**（与卡面锚一致） |
| `0x007E3E90` | `0x00410590` | 小子表（成员/次基类子对象） |
| `0x007E3E98` | `0x00410580` | 小子表 |
| `0x007E3EA0` | `0x004105E0` | 小子表 |

主表 `[-4] @0x007E3EB8 = 0x007FC360`（COL，sig=0），`[COL+0xC] @0x007FC36C = 0x00818D60`（TD），`TD+8 = .?AVBuildingClass@@`；主表从 `0x007E3EBC` 起连续 **322** 个 `.text` 槽（slot 0..321），表末 `0x007E43C4`。

**结论**：18 行的线索槽号 N 与主表实际槽号**逐行相等**，且槽内 4 字节即 entry——无一行落在小子表里。这一步先做，直接避免了把小子表当主表的整批误判。

（同法确认 `BuildingTypeClass` 主表 = `0x007E4570`（槽 0 = `00410260`，COL `0x007FC618`）。这与第 8 行的裁定有关：`[this+0x520]` 是 **Type** 指针，不是本对象，容易误当 BuildingClass 主表。）

## 四、判定口径（严格 D-40 / D-43，宁严不宽）

1. **① 入口**：entry 在 `.text` 内、atlas 边界自洽、`skipdata` 计数、末条指令形态。
2. **② 类身份**：**独立取证**——`.rdata` 中 entry 作 4B VA 的槽 → 回扫 `[vt-4]=COL(sig=0)` → `[COL+0xC]=TD` → `TD+8` 名串 `.?AV…@@`；并同时要求 (a) RTTI 名与线索类一致、(b) **槽号 = 槽偏移/4 等于线索 N（由字节复算，不反推）**、(c) 该表是对象主虚表（槽 0 = `00410260`）。
3. **③ 整体合同**：只认 ③b。本批实际逐一检验了 **③b②**（call → test/cmp eax(或等价的返回值寄存器) → jcc，被调返回约定可伪证、调用方真的拿它分支、两路动作真不同、比较与跳转之间无返回值覆写、单 call 非多路同一 call）与 **③b①**（跳转表 + 每路可单独验证）。禁 ③a（纯转发/单调用+单写/零+默认/无分支直线）与模板假句。
4. **④ 使用见证**：活虚表派发 —— 构造期 `.text` 安装点（`mov [mem], vt`）把主表写入活对象，**行外、非 atexit**；direct-only 不足。**与 ② 不同源**：② 锚 `.rdata` RTTI 数据链，④ 锚 `.text` 构造安装指令字节。
5. **三陷阱逐行排查**：eax 覆写 / 多路同一 call / 模板假句。
6. **㉓ 成对陷阱**：④ 锚点若落在析构器（`push <fn>; call 0x7C978A` 的 atexit 表）内 ⇒ FAIL。本批 4 安装点全部 `atexit=False`，且 `0043B680`/`0043B740` 收尾 `mov eax,esi` 返 `this` ⇒ 构造器，非析构器。

## 五、基础率（诚实报数）

| 档 | 行数 | 口径 |
|---|---:|---|
| 本批行数 | **18** | S12 named=True 排除伪名后升序前 18 |
| ① 入口 PASS | **18** | 全部在 `.text`；16 行边界完全自洽，2 行（`00443C60`/`00448260`）atlas 长度短 3~4 B 截断在指令中间（见待裁 #4） |
| ② 类身份钉住 | **18** | 18/18 槽号 == 线索 N 且槽值 == entry，RTTI = `.?AVBuildingClass@@`，主表槽 0 = `00410260` |
| ③b 成立 | **4** | 4×③b②（`00442230` / `00447210` / `00447F10` / `0044E8F0`） |
| ④ 使用见证成立 | **18** | 18 行槽均位于由构造器装入活对象的主虚表内；3 处安装点均非 atexit |
| **四环齐全** | **4** | rate = 4/18 = **0.2222** |

`base_rate.tsv`：`S12_B1	18	18	4	18	4	0.2222`

## 六、本批 18 行总表

| # | entry | name（原样） | ① | ② | ③ | ④ | ②④不同源 | 裁定 | 产出 |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | 0043C2D0 | BuildingClass::vslot101 | PASS | PASS | FAIL | PASS | 是 | 不成立 | 否 |
| 2 | 0043D030 | BuildingClass::vslot70 | PASS | PASS | FAIL | PASS | 是 | 不成立 | 否 |
| 3 | 0043D290 | BuildingClass::vslot69 | PASS | PASS | FAIL | PASS | 是 | 不成立 | 否 |
| 4 | 0043FB20 | BuildingClass::vslot23 | PASS | PASS | FAIL | PASS | 是 | 不成立 | 否 |
| 5 | 00440580 | BuildingClass::vslot54 | PASS | PASS | FAIL | PASS | 是 | 不成立 | 否 |
| 6 | 004415F0 | BuildingClass::vslot315 | PASS | PASS | FAIL | PASS | 是 | 不成立 | 否 |
| 7 | 00442230 | BuildingClass::vslot91 | PASS | PASS | **PASS(③b②)** | PASS | 是 | **成立** | **是** |
| 8 | 00442C40 | BuildingClass::vslot9 | PASS | PASS | FAIL | PASS | 是 | 不成立 | 否 |
| 9 | 00443C60 | BuildingClass::vslot64 | PASS* | PASS | FAIL | PASS | 是 | 不成立 | 否 |
| 10 | 004456D0 | BuildingClass::vslot312 | PASS | PASS | FAIL | PASS | 是 | 不成立 | 否 |
| 11 | 00445F80 | BuildingClass::vslot311 | PASS | PASS | FAIL | PASS | 是 | 不成立 | 否 |
| 12 | 00447110 | BuildingClass::vslot104 | PASS | PASS | FAIL | PASS | 是 | 不成立 | 否 |
| 13 | 00447210 | BuildingClass::vslot29 | PASS | PASS | **PASS(③b②)** | PASS | 是 | **成立** | **是** |
| 14 | 00447F10 | BuildingClass::vslot240 | PASS | PASS | **PASS(③b②)** | PASS | 是 | **成立** | **是** |
| 15 | 00448260 | BuildingClass::vslot245 | PASS* | PASS | FAIL | PASS | 是 | 不成立 | 否 |
| 16 | 0044E8F0 | BuildingClass::vslot10 | PASS | PASS | **PASS(③b②)** | PASS | 是 | **成立** | **是** |
| 17 | 0044EB10 | BuildingClass::vslot195 | PASS | PASS | FAIL | PASS | 是 | 不成立 | 否 |
| 18 | 0044EBF0 | BuildingClass::vslot55 | PASS | PASS | FAIL | PASS | 是 | 不成立 | 否 |

`PASS*` = 入口在 `.text`、自入口线性解码自洽，但 atlas 给出的长度截断在一条指令中间（短 3~4 B），真实函数体更长；行内所有 ③/④ 锚点距尾部 > 0x100 B，裁定不受影响。

### 一条方法学增量（建议 Lead 转给其它批次）

SURVEY_3B2 的机械 ③b② 口径只认 `test/cmp **eax**`。但编译器在「返回值先搬进别的寄存器再判」时会漏掉：`call X; mov ebx,eax; cmp ebx,8; jne …`（本批 `00447210` 的 `0x44726C`）或 `call X; mov ebp,eax; test ebp,ebp; jne …`（本批 `00447F10` 的 `0x447FD9`）。

本批结论是：这类站点**真实存在且能成立**——`00447210` 就是被这条口径漏掉后，由我补的「返回值搬移形态」扫描（`_work/sweep_mv.py`、`_work/sweep_all.py`）捞回来的。也就是说 **1,733 个机械命中是 ③b② 的下界，不是全集**：真正的 ③b② 站点还有一批散落在「搬移后比较」的形态里。

补扫方式：对每个直接调用取 `atlas` 边界内的被调返回常量集合；若含 0 且另有 ≥1 个小常量（或为多值状态码集合），再看调用点后 1~3 条内是否有 `test/cmp <reg>`（`reg` = eax 或紧随的 `mov reg,eax`）与条件跳转，且中间无该寄存器覆写。建议其它批次照此复扫一遍。

## 七、逐行裁定依据（每行自身地址锚；字节见 `EVIDENCE/ROW_<entry>.txt`）

### ② 18/18（槽号与槽值均由字节复算，非反推）

| # | entry | 槽 VA | 槽内 4 B | slot# | 与线索 N | RTTI 名 |
|---:|---|---|---|---:|---|---|
| 1 | 0043C2D0 | 007E4050 | `d0 c2 43 00` | 101 | ✔ | .?AVBuildingClass@@ |
| 2 | 0043D030 | 007E3FD4 | `30 d0 43 00` | 70 | ✔ | 同上 |
| 3 | 0043D290 | 007E3FD0 | `90 d2 43 00` | 69 | ✔ | 同上 |
| 4 | 0043FB20 | 007E3F18 | `20 fb 43 00` | 23 | ✔ | 同上 |
| 5 | 00440580 | 007E3F94 | `80 05 44 00` | 54 | ✔ | 同上 |
| 6 | 004415F0 | 007E43A8 | `f0 15 44 00` | 315 | ✔ | 同上 |
| 7 | 00442230 | 007E4028 | `30 22 44 00` | 91 | ✔ | 同上 |
| 8 | 00442C40 | 007E3EE0 | `40 2c 44 00` | 9 | ✔ | 同上 |
| 9 | 00443C60 | 007E3FBC | `60 3c 44 00` | 64 | ✔ | 同上 |
| 10 | 004456D0 | 007E439C | `d0 56 44 00` | 312 | ✔ | 同上 |
| 11 | 00445F80 | 007E4398 | `80 5f 44 00` | 311 | ✔ | 同上 |
| 12 | 00447110 | 007E405C | `10 71 44 00` | 104 | ✔ | 同上 |
| 13 | 00447210 | 007E3F30 | `10 72 44 00` | 29 | ✔ | 同上 |
| 14 | 00447F10 | 007E427C | `10 7f 44 00` | 240 | ✔ | 同上 |
| 15 | 00448260 | 007E4290 | `60 82 44 00` | 245 | ✔ | 同上 |
| 16 | 0044E8F0 | 007E3EE4 | `f0 e8 44 00` | 10 | ✔ | 同上 |
| 17 | 0044EB10 | 007E41C8 | `10 eb 44 00` | 195 | ✔ | 同上 |
| 18 | 0044EBF0 | 007E3F98 | `f0 eb 44 00` | 55 | ✔ | 同上 |

全部 `[-4] = 0x007FC360`（COL, sig=0）、`[COL+0xC] = 0x00818D60`（TD）→ `.?AVBuildingClass@@`。**18/18 钉住**。

### ③ 成立 4 行（各自独立站点与语义）

- **`00442230` BuildingClass::vslot91（③b②）**：站点 `0x4424BB` `ff 52 10` = `call dword ptr [edx+0x10]`，`edx` 为栈上临时向量的 vptr（`0x442481` 处 `mov [esp+0x14], 0x7E180C`；同族路径 `0x4422E1` 写 `0x7E17AC`），`0x4424B7 lea ecx,[esp+0x18]` 在 `push eax` 之后正好指向对象首址。`0x4424BE` `83 f8 ff` = `cmp eax,-1`；`0x4424C1` `74 25` = `je 0x4424E8`。
  - 被调约定两条可能 vptr 下**一致**：`0x7E180C` → `[-4]=COL 007FA6D8` → `.?AV?$VectorClass@PAVTechnoClass@@@@` → slot4（`0x7E181C`）= `0x0040BA80`，其 `0x40BAAC` `or eax,0xFFFFFFFF`、`0x40BAB0` `ret 4`；`0x7E17AC` → `COL 007FA640` → `.?AV?$DynamicVectorClass@PAVTechnoClass@@@@` → slot4（`0x7E17BC`）= `0x0040BB90`，其 `0x40BBAF` `or eax,0xFFFFFFFF`、`0x40BBB3` `ret 4`。**未找到 = -1、命中 = 下标，字节可伪证。**
  - 两路动作真不同：未命中跳 `0x4424E8` 跳过整段；命中则 `0x4424CE` 回写 count-1，`0x4424D9` `mov edx,[ecx+eax*4]` / `0x4424DC` `mov [ecx+eax*4-4],edx` 前移压缩（**非栈写**）。
  - `cmp` 与 `je` 之间无 eax 覆写；单 call，非多路同一 call。
  - **语义**：在栈上临时 `TechnoClass*` 向量中 `Find` 目标（-1 = 未命中），命中则按下标做压缩移除，未命中跳过。
- **`00447210` BuildingClass::vslot29（③b②）**：站点 `0x447267` `e8 54 8c 2b 00` = `call 0x6FFEC0`（direct，this = esi，两参数）；`0x44726C` `8b d8` = `mov ebx,eax`；`0x44726E` `83 fb 08` = `cmp ebx,8`；`0x447271` `75 09` = `jne 0x44727C`。
  - 被调返回约定字节可伪证（12 个 `ret`，11 个带常量，一律 `ret 0xc`）：`0x7000E8`/`0x700169`/`0x70018E mov eax,4`、`0x700110 mov eax,8`、`0x6FFF8A`/`0x7005E3 mov eax,7`、`0x700569 mov eax,5`、`0x7001E6 mov eax,0x1A`、`0x6FFFD8`/`0x700003 mov eax,0x37`、`0x7005EF xor eax,eax`(0)。是**多值状态码集合** {0,4,5,7,8,0x1A,0x37}，不是 0/1 布尔。
  - 各路动作真不同：`rc==8` → `0x447279 pop esi; pop ebp; pop ebx; add esp,0xC; ret 8` 把 8 **原样上抛**、不再做事；`rc!=8` → `0x44727C cmp ebx,4` / `0x447280 jne 0x447366`，`rc==4` 进 `0x447286` 读 `[Type+0xCD1]`、比对 `[this+0x21C]` 与全局 `0xA83D4C` 等实质工作；`rc!=4` → `0x447366 cmp ebx,5` / `0x447369 jne 0x4473C7`，`rc==5` 进 `0x44736B push 0; mov ecx,esi; call [edx+0x3F8]`，其余落默认 `0x4473C7`。
  - 比较与跳转之间无 `ebx` 覆写；单 call，非多路同一 call。
  - **语义**：建筑动作分派——先调 `0x6FFEC0` 取动作/状态码（0/4/5/7/8/0x1A/0x37），按码分支：8 直接上抛返回，4 与 5 各走一条实质处理分支，其余落默认。
  - 注：本行另有一个 `0x44723C call [edx+0x2C]`（槽 11，主表实现 `00459EC0 = mov eax,6; ret`）后 `cmp eax,6` 的站点，那是类类型常量比较，**不**作为 ③ 依据。
- **`00447F10` BuildingClass::vslot240（③b②）**：站点 `0x447FD4` `e8 …` = `call 0x6FC0B0`（direct，this = esi，三参数）；`0x447FD9` `8b e8` = `mov ebp,eax`；`0x447FDB` `85 ed` = `test ebp,ebp`；`0x447FDD` `75 73` = `jne 0x448052`。
  - 被调返回约定字节可伪证（按 atlas 边界对齐解码，32 个 `ret` 一律 `ret 0xC`）：`0x6FCD20` `xor eax,eax`（`33 c0`）→ `0x6FCD26` ret = **成功 0**；失败出口逐条带常量，如 `0x6FCD11 mov eax,8` / `0x6FCD1A` ret、`0x6FCD2C mov eax,6` / `0x6FCD35` ret、`0x6FCBA1`/`0x6FCBC1`/`0x6FCBDA`/`0x6FCC51`/`0x6FCCB1`/`0x6FCCE2 mov eax,5`，另有 `mov eax,3`（7 处）、`mov eax,1`、`mov eax,9`。
  - 两路动作真不同：非零路 `0x448052` `pop edi; mov eax,ebp; pop esi; pop ebp; ret 0xC` **把错误码原样上抛**；零路继续 `0x447FE3 call [edx+0x3FC]`(slot 255)、`0x447FF8 call [eax+0x4E8]`(slot 314) 等后续判定。
  - 判的是 `ebp`，eax 未被覆写；单 call，非多路同一 call。
  - **语义**：建造/放置合法性判定——先查占位与类型状态，再调 `0x6FC0B0` 做放置判定并把其错误码原样上抛（0 = 成功；1/3/5/6/8/9 = 各类失败），自身另返回 2/3/5/6 表示不同拒绝原因（`0x448049`=2、`0x447FBA`=3、`0x44805C`=5、`0x447F66`/`0x447FA5`=6）。
- **`0044E8F0` BuildingClass::vslot10（③b②）**：站点 `0x44EA8F` `ff 52 10` = `call dword ptr [edx+0x10]`，`edx` = `[esi+0x66C]` 的成员向量 vptr，`0x44EA7E lea edi,[esi+0x66C]` 即 this；`0x44EA92` `83 f8 ff` = `cmp eax,-1`；`0x44EA95` `74 21` = `je 0x44EAB8`。
  - 成员 vptr 由本类构造器安装：`0x43B6DB` `c7 86 6c 06 00 00 c8 43 7e 00` = `mov dword ptr [esi+0x66C], 0x7E43C8`；`0x7E43C8` → `[-4]=COL 007FC298` → `.?AV?$DynamicVectorClass@PAVInfantryClass@@@@` → slot4（`0x7E43D8`）= `0x0045A610`（`mov edx,[ecx+0x10]` 取计数、`mov ecx,[ecx+4]` 取数组、逐个比较），其 `0x45A62F` `or eax,0xFFFFFFFF`、`0x45A633` `ret 4` ⇒ **未找到 = -1、命中 = 下标**。
  - 两路动作真不同：未命中跳 `0x44EAB8` 跳过；命中则 `0x44EA9E` `dec ecx`、`0x44EAA1` `mov [edi+0x10],ecx` 回写计数，`0x44EAAA`/`0x44EAAD` `mov edx,[ecx+eax*4]; mov [ecx+eax*4-4],edx` 前移压缩（**非栈写**）。
  - `cmp` 与 `je` 之间无 eax 覆写；同函数内 `0x44EAD9` 是对**另一成员容器** `this+0x684`（vptr 由 `0x43B709` 安装同一 `0x7E43C8`）的独立 Find，非多路同一 call。
  - **语义**：对本对象内成员 `DynamicVectorClass<InfantryClass*>`（`this+0x66C` 与 `+0x684`）虚派发 `Find` 目标（-1 = 未命中），命中则 count-- 并把后续元素前移一格压缩移除，未命中直接跳过。

### ③ 不成立 14 行（逐行独立理由，各自站点地址）

| # | entry | 站点（行内地址） | 不成立原因 |
|---:|---|---|---|
| 1 | 0043C2D0 | `0x43C32A` `call [eax+0x184]`→主表 slot 97 = `005B3040`（字段 getter，返回 `[this+0xAC]`，为 -1 时改取 `[this+0xB4]`），后接 `0x43C330 cmp eax,0x12` / `0x43C343 cmp eax,0x13`；`0x43C943 call 0065AD30`（数组元素 getter `mov eax,[ecx+0xE4]; mov eax,[eax+ecx*4]; ret 4`）后 `test eax,eax`；`0x43CDB9 call 007C5F00`（`_ftol`）后 `cmp eax,0x180; jge` | 全行只在比「虚取值出来的状态/类型常量」或「取值/分配得到的指针是否为空」；无失败/成功错误码约定 |
| 2 | 0043D030 | `0x43D079` / `0x43D09B` 同一 slot 97 getter，后接 `cmp eax,0x18` / `cmp eax,0x10` | 两站点均比建筑类型常量，非错误码 |
| 3 | 0043D290 | `0x43D2B2 call [eax+0x6C]`→slot 27 = `004513D0`，该函数尾部为 `jmp [Type vtbl+0x9C]` / `jmp [Type vtbl+0xC0]` 尾转；其余 `0x43D2C9 cmp eax,6`、`0x43D2DF/0x43D6DF cmp eax,0x13/0x12`、`0x43D33F/0x43D696 cmp eax,0x10`、`0x43D548 cmp eax,0x18` | 唯一 test-eax 站点的返回值来源静态不可定 ⇒ 约定不可伪证；其余全是状态/类型常量比较 |
| 4 | 0043FB20 | `0x43FB39`/`0x43FB48` slot 97 getter 后 `cmp eax,0x12/0x13`；`0x440499`/`0x440511 call 007C8E17`（= `push 1; push size; call 007C9442`，calloc(n,1) 薄壳）后 `test eax,eax; je` | 前者类型常量；后者是分配结果判空，且两路只是「构造对象」与「置 0」 |
| 5 | 00440580 | **eax 覆写**：`0x440720 call 004FCE80` 的返回值被 `0x440727 call 0047C520` 覆盖，`0x44072C test eax,eax` 测的是后者；`0047C520` 在 `[ecx+0xE4]` 链表上找 type==6，返对象指针或 NULL。另 `0x4407A0 call [edi+0x1AC]`（外来对象 slot 107）、`0x440409A3 call 007C8D20`（strcmp）、`0x441178 call 007C8E17`（calloc） | 两类：指针非空判断 + strcmp 比较结果；另两处被调类不可静态定 ⇒ 约定不可伪证 |
| 6 | 004415F0 | `0x441779 call 00750E20`（返回值随即被 `0x441784 call 0045EC90` 覆盖）、`0x441784`/`0x4417AD call 0045EC90`、`0x441799`/`0x4417DF call 0045ECA0` 后 `cmp eax,2; jl/jle`；`0x441C3D` slot 97 `cmp eax,0x13`；`0x441E51 call [eax+0x1C8]`(slot 114) `cmp eax,-0xA` | 帧计数与坐标阈值的范围检查，非失败/成功错误码 |
| 8 | 00442C40 | `0x442CB2 call [eax+0xC0]`，但 `eax` 取自 `[ecx]`、`ecx = [esi+0x520]` ⇒ 是 **BuildingTypeClass** 的 vptr，实为 BT 主表 `007E4570` 的 slot 48 = `00465960`（size ≥ 0x1200、57 个 ret，返回常量多为不可判定） | 被调无「失败=N / 成功=0」约定可伪证；两路动作虽不同（`0x442CBC` 置 `+0x6DC`=0 vs `0x442CCF` 置 `+0x6E9`=1），但只能是布尔/状态位 |
| 9 | 00443C60 | **eax 覆写**：`0x444322 call 005657A0` 返回常量 `0x00ABE4D0` 只被 `0x444327 mov ecx,eax` 用作下一调用的 this，`0x444329 call 0047C3D0` 覆盖 eax，`0x44432E test eax,eax` 测的是后者（内部 `and esp,-8` + x87 计算）；`0x444DC3/0x444DE8` 槽 158/11 后 `cmp eax,1` | 真正被测的是浮点换算结果；其余为类型常量比较 |
| 10 | 004456D0 | `0x445758`/`0x44579D`/`0x4457DE`/`0x44581E` 四处 `call 004F7870`（11 个 ret，常量集合仅 {0,1}）后 `test eax,eax; je`，非零路只 `push id; mov ecx,0x87F7E8; call 006A6300`（日志，id = 7/0x28/0x10/3） | 0/1 是布尔命中标记，不是失败/成功错误码；未命中路唯一差别是一条日志调用 |
| 11 | 00445F80 | **eax 覆写**：`0x445FF1 call 007C5F00`（`_ftol`）覆盖 `0x445FEC call 006C9650` 的返回值，`0x445FF6 test eax,eax; je` 为「为 0 则跳过除法直接置 0」的**零+默认**；`0x44692E call 0049FAE0` 后 `cmp eax,9; ja` + 跳表；`0x446B68`/`0x446F28 call 007C8E17`（calloc 判空） | 零值默认（③a 形态）+ 状态跳表 + 分配判空，均非错误码 |
| 12 | 00447110 | `0x447135`/`0x447158` 均 `call [..+0x184]`（slot 97 getter）后 `cmp eax,0x13`；`0x447169` 第三次调用后 `cmp eax,0x13; setne al` | 判据是建筑类型是否等于 0x13，非错误码 |
| 15 | 00448260 | `0x448644 call 0041C380`（三条 `fild/fmul` 求和后 `call 004CAC40`、再 `jmp 007C5F00`(`_ftol`)，返回整数距离）后 `0x448649 cmp eax,0x40; jge` | 与 64 比较的是**地图像素距离**（几何量），非失败/成功错误码 |
| 17 | 0044EB10 | `0x44EB2C call 0065C7E0`；该被调以 `mov eax,[esp+4]` + 状态数组 `[edx+ecx*4+0xC]` + `cmp eax,0xFA` 构成 MSVC `rand` 的 LCG，后接 `0x44EB31 cmp eax,0x19; jge` | 对伪随机数取阈，非错误码 |
| 18 | 0044EBF0 | `0x44EC8C`/`0x44ED0D`/`0x44ED8E`/`0x44EE0F`/`0x44EE90` 五处 `call [edx+0x94]`，其 `edx = [edi]`、`edi = 0x44EC59 call 004CA160` 的返回对象 ⇒ 运行时未知类的 slot 37；`0x44EEF7 call 00500510` 内部是 `dec eax; cmp eax,0x27; ja` + 字节索引表 + 40 路跳表，各 case 返回 `[ecx+0x53B0/0x53B4/0x53B8]` 等**对象指针** | 被调类不可静态定 ⇒ 返回约定不可伪证；另一处返回的是对象指针而非错误码 |

### ④ 18/18（活虚表派发，行外非 atexit）

主虚表 `0x007E3EBC` 在 `.text` 的构造期安装点共 **3 处**（`c7 06 bc 3e 7e 00` = `mov dword ptr [esi], 0x7E3EBC`）：

- `0x0043B71F`（在函数 `0043B680` 内，192 B）：先 `call 006F4300` 基类构造，收尾 `mov eax,esi; ret 4` **返 this** ⇒ 构造器。
- `0x0043B9FA`（在函数 `0043B740` 内，1456 B）：先 `call 006F2B40` 基类构造，收尾 `mov eax,esi; ret 8` **返 this** ⇒ 构造器。
- `0x0043BCFD`（在函数 `0043BCF0` 内，986 B）：本类构造器变体（先装表再构造成员）。

三处 `push <func>` + `call 0x7C978A`(atexit) 均为 **否** ⇒ **㉓ 成对陷阱排除：④ 锚点不在析构器 / atexit 表里**。每行的槽 VA 各不相同（表见 §七 ② 表），落在该已安装主表内 ⇒ 构造完成后 `[obj+0]` 派发可达本 entry。

直接调用者：仅 `00442C40` 有 1 个（`0x0043BB29`），其余 17 行 0 个——但 ④ 不靠 direct，靠**活虚表链**，故不触「direct-only 不足」。

## 八、与 S04 的败因对比（本批有多少行 ② 真的钉住了）

- **S04**：73 个 ③b② 机械命中 **`p3b2_named = 0`**（全无名字）——entry 作 4B VA 全镜像 0 命中、无虚表槽、无可回扫 RTTI 链 ⇒ **② 物理不可得**，30+ 行实测全败。
- **本批 S12 B1**：18 行里 **18 行 ② 全部被 RTTI + 主虚表独立钉死（18/18 = 100%）**，且槽号由字节复算后与线索 `vslotN` 的 N **逐行相等**。本批 **0 行** 落入「② 物理不可得」。
- **候选池质量**：S12 的 33 个 named 候选**全部是 `Class::vslotN`**，`fn_`/`sub_` 伪名 **0 个**（对比 S14 的 51 个里有 16 个是 `fn_`）⇒ 若开 B2 批（第 19..33 行，15 行），② 预期同样接近 100%，② 不再是瓶颈。
- **瓶颈已彻底转成 ③**：18 行里 ② 18/18、④ 18/18，但 ③ 只有 **4/18（22.2%）**。14 行 ③ 失败的分布是：**8 行**「比虚取值出来的状态/类型常量」（`0043C2D0`/`0043D030`/`0043D290`/`0043FB20`/`004415F0`/`00443C60`/`00447110`/`00447210` 的*另一*站点）、**3 行**「eax 覆写陷阱污染站点」（`00440580`/`00443C60`/`00445F80`）、**2 行**「calloc 判空 / 指针非空」（`0043FB20`/`00445F80`）、**1 行**「零+默认」（`00445F80`）、**1 行**「被调是 rand」（`0044EB10`）、**1 行**「几何距离阈值」（`00448260`）、**1 行**「被调其实属于 BuildingTypeClass 且无约定」（`00442C40`）、**1 行**「被调类为运行时未知类」（`0044EBF0`）。即：**S12 这批的建筑类方法大量是「查状态/查类型后早退」的谓词，天生缺少可伪证错误码**。
- 与 S14 的 0.3333 相比本批 0.2222 偏低，原因不是取证能力，而是**样本性质**：S14 的成立行多数是标量析构里的「全局容器 Find(-1) + 压缩移除」，S12 这批的 18 行里只有 2 行含同类 Find 模式（`00442230`/`0044E8F0`，且都在**成员/栈局部**容器上，不是全局容器），二者均成立；另 2 行（`00447210`/`00447F10`）靠的是「被调返回多值状态码 + 调用方按码分派/上抛」。

## 九、待裁（4 项，未擅自扩面）

1. **`00447F10` / `00447210` 的 ③ 站点形态**：这两行成立靠的是「被调返回错误/状态码，调用方把返回值搬进另一个寄存器再判」——`00447F10` 是 `mov ebp,eax; test ebp,ebp`（`0x447FD9`/`0x447FDB`），`00447210` 是 `mov ebx,eax; cmp ebx,8`（`0x44726C`/`0x44726E`）。D-40 ③b② 的措辞是「可伪证错误码/返回约定（失败返回什么、成功返回什么、调用方真的拿它分支）」，二者完全满足；但它们**不是 SURVEY_3B2 机械口径筛出的那个站点**（机械口径只认 `test/cmp **eax**`）。若 Lead 认定「③ 必须由机械 p3b2 那一站点本身成立」，则 **−2 → 2/18（0.1111）**。我判成立，理由是卡面 ③ 判的是函数整体合同，机械命中只是候选生成器。
2. **③b① 是否计入本批**：逐行解析了全部间接跳转表——`0043C2D0` 19 项→**10** 互异目标、`00443C60` 15 项→**4**、`004456D0` 38 项→**5**、`00445F80` 10 项→**7**、`00442230` 4 项→4。前四者的目标**大量合并**、且各块终止于 `jcc` 直接落入共享代码，「每路可单独验证」不成立，故我一律不计 ③b①。若 Lead 认为「目标合并的开关仍算 ③b①」（`004456D0` 的 5 个分支确实各自扫描不同全局数组并打不同日志 id，`00445F80` 的 7 个分支块形态各异），可 **+2 → 5/18（0.2778）**；若连 `00443C60`/`0043C2D0` 也认，可 **+4 → 7/18（0.3889）**。我不主动加，因为合并目标下「单独验证」的判据会被稀释。
3. **`004456D0` 的 0/1 布尔约定**：被调 `004F7870` 返回集仅 {0,1}，非零路只多一次日志调用。我按「bool 主输出不算错误码」判 FAIL。若 Lead 认「命中即告警」这种两路动作差够 ③b②，可 **+1 → 5/18**。同类还有 `00440580`（对象指针非空 + 构造）、`00443C60`、`00445F80`、`0043FB20` 的 calloc 判空站点——若「分配失败返回 NULL」也算可伪证返回约定，可再 +4。我一律未计，因为这类约定任何一段 `new` 代码都满足，区分力接近零（与卡面「模板假句」禁令同源）。**判号线**：我接受 `00447210` 的多值状态码集合 {0,4,5,7,8,0x1A,0x37}，但不接受 {0,1} 布尔——理由是前者是可枚举的多态返回约定、后者的两个值只表达真/假，与 D-46(A)「bool 不算」同源。
4. **atlas 长度截断（①）**：`00443C60`（size 6672）与 `00448260`（size 4051）的 atlas size 停在一条指令中间（`skipdata` 分别为 1/2），自 `0x44566F` / `0x44922F` 继续解码仍是合法代码（`lea edi,[ecx+eax+0x10]` / `mov al,[ecx+0x16CB]`），即真实函数体比 atlas 长 3~4 B。我判 ①=PASS（带注记），因入口地址本身在 `.text` 内、自入口线性解码自洽，且行内所有 ③/④ 锚点距尾部 > 0x100 B。若 Lead 要求「atlas size 必须精确等于函数体」，这两行 ① 应记 FAIL（但两行 ③ 本已 FAIL，对产出无影响）。

## 十、汇总

- rows_checked：**18**
- ② 钉住行数：**18**（18/18；槽号由字节复算，主表槽 0 = `00410260`，RTTI = `.?AVBuildingClass@@`）
- ③b 成立行数：**4**（全为 ③b②：`00442230` / `00447210` / `00447F10` / `0044E8F0`）
- ④ 成立行数：**18**（活虚表派发，3 处构造安装点均非 atexit，㉓ 已排除）
- all_four_rings（严格 D-40/D-43）：**4**，rate = **0.2222**
- delta 产出：**4 行**（`00442230` / `00447210` / `00447F10` / `0044E8F0`），entry 大写十六进制无 `0x`，每行独立 reason，已脚本校验 6 列 / 无重复 reason / 证据文件均存在

## 十一、输出清单

- `delta.tsv`（4 行 / 6 列）、`base_rate.tsv`（`S12_B1 18 18 4 18 4 0.2222`）、`PROGRESS.md`、`REPORT.md`（本文件）
- `EVIDENCE/ROW_<entry>.txt` × 18（逐行四环地址与字节，每行独立锚点）
- `_work/`：`core.py`（PE/capstone/RTTI/安装点/atexit/③b② 机械筛/跳表，本目录自建）、`filter_b1.py`（筛选）、`rows_b1.json`（18 行候选）、`rtti_scan.py`（全镜像 COL/TD 对 + 各表槽 0）、`vt_dump.py`（主虚表布局）、`ring2.py`（槽号自洽）、`ring4.py`（安装点 / atexit）、`ring3_scan.py` + `sites_ctx.txt`（③b② 站点上下文）、`dump.py` + `body_*.txt`（逐行反汇编）、`callee.py`（被调返回约定）、`sweep_err.py`（错误码型直接调用补扫）、`sweep_mv.py` / `sweep_all.py`（**返回值搬移形态与全部返回值测试站点补扫**——`00447210` 靠此捞回）、`jt_check.py`（③b① 跳表逐路核验）、`rings124.py` + `rings124.json`（① ② ④ 全量底账）、`gen_evidence.py` / `gen_tsv.py`（产物生成）、`selfcheck.py`（**产物自校验：把 REPORT ② 表 18 格 + delta + base_rate + 3 安装点全部回到二进制复算**，当前全绿）。
- 全部只读目标，可复算；未触碰 `coverage.tsv` / `PANEL.md` / `R14_COMMON.md` / 台账 / `SURVEY_3B2` / `S04_PUSH_*`。
