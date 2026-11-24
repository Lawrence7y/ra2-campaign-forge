# W34 · `MAPSELMD.INI` 格式定谳（纯静态 / 纯离线）

> run_id `NEXT_RE_20261112_R02` ｜ 交付目录 `lead/next_re_20261112_r02/W34_mapselmd/`
> 目标镜像 `ra2bench/gamemd.exe`（4,825,360 B，SHA-256 `73201cc0…f67476`，`ImageBase=0x400000`，`.text` RVA=FOFF=0x1000 ⇒ **FOFF = VA − 0x400000**）`[本次实测]`
> 官方文件 `ra2bench/ra2md.mix` → 嵌套 `LOCALMD.MIX` → `MAPSELMD.INI`，5,573 B，SHA-256 `074ccccd9e156d586d0ed099ceab78b3d72384c808725d8b5bee2c9799691d52` `[本次实测]`
> 纪律：纯离线；未启动 `gamemd.exe`、未 attach、未写 `ra2youli`、未改 W21–W33 与仓库 `ra2forge/`；`ra2bench` 只读；git 只读；`ret` 未当函数结束判据；等距指针表未当 vtable。

---

## 0 · 结论分级与证据索引

| 等级 | 含义 |
|---|---|
| `[本次实测]` | 本卡脚本对二进制 / MIX 字节直接读出并断言 |
| `[本次读码]` | 本卡 Capstone 反汇编指令逐条读出（含 rel32/imm32 解码） |
| `[静态推断]` | 由多处读码结果组合推出，未做运行期观察 |
| `[转引]` | 来自 W29 / W33 / W30 的既有结论（关键处已复核） |
| `[待运行验证]` | 静态无法确定，必须真机验证；**本卡不做** |

| 脚本 | stdout | exit | 作用 |
|---|---|---|---|
| `EVIDENCE/step1_extract_mapsel.py` | `.stdout.txt` | 0 | 解码 `ra2md.mix`，复现坑，提取官方全文，32/32 断言 |
| `EVIDENCE/step2_disasm_mapsel.py` | `.stdout.txt` | 0 | 六个目标函数完整反汇编 + call 目标统计 |
| `EVIDENCE/step3_disasm_stage.py` | `.stdout.txt` | 0 | MapStage 构造、子项键循环、INI 行读取器、tolower，34/34 断言 |
| `EVIDENCE/step4_compat_sha256.py` | `.stdout.txt` | 0 | v10/v11 不启用开关时逐字节 SHA-256 对照 |

---

## 1 · 先解决「关键坑」：`get()` 为什么返回 `None`

`[本次实测]`（`EVIDENCE/step1_extract_mapsel.py`，32/32 断言 PASS，exit 0）

1. `mixlib.MixFile("ra2md.mix").get("MAPSELMD.INI") -> None`（实测）。
2. 对整份 204,527,696 B 流式裸搜 `struct.pack("<I", 0x922B8CE7)` → **0 命中**（实测）。
3. 但 `zlib.crc32("MAPSELMD.INI") == mixlib.crc_hash("MAPSELMD.INI") == 0x922B8CE7`（实测）。

**真正原因（本卡新结论，与 W33 卡面描述不同）**：

- `ra2md.mix` 顶层头 `first4 = 00 00 03 00` ⇒ `word0=0`（TS/RA2 新头）、`flags=0x3`（bit0 + **bit1=加密**）。条目表经 Blowfish 加密（W29 §1.3：`0x5B3CED..0x5B3D11`），因此明文 id 本就不会出现在裸字节里。
- 顶层 25 个条目中，**`0xFBE0D09D` 不是 MAPSELMD.INI 的「被异或的 id」**，而是**嵌套容器 `LOCALMD.MIX`** 的条目 id，且它用的是 Westwood 4 字节尾部填充哈希：`mixlib.ts_crc_hash("LOCALMD.MIX") = 0xFBE0D09D`；普通 `zlib.crc32("LOCALMD.MIX") = 0x3BF6887A`。`[本次实测]`
- 该容器条目 4,819,480 B，自身头 `00 00 03 00` 也是加密 TS/RA2 MIX（187 个条目）。**`MAPSELMD.INI` 在这第二级 MIX 里**，id 恰是普通 `crc32("MAPSELMD.INI")=0x922B8CE7`，size **5,573**。`[本次实测]`
- ⇒ 正确做法不是「扫 id 行」，而是**自己解码两级（可能加密的）条目表并递归**（W33 `step10_close_gaps.py::scan_mix_bytes` 已这么做，但卡面把标签里的容器 id 误读成了文件 id）。`EVIDENCE/step1_extract_mapsel.py::parse_mix_bytes/find_in_mix` 是本卡独立实现，输出 `EVIDENCE/MAPSELMD.OFFICIAL.INI`（官方 5,573 B 原样字节）。

官方全文（20 个段）`[本次实测]`：`GDI, GDISFX, Nod, NODSFX, Anims, ALL00..ALL07, Sov01..Sov07`；`[GDI] 1..7 = ALL01..ALL07`，`[Nod] 1..7 = Sov01..Sov07`；每个阶段段有 `Scenario=` / `Description=` / `VoiceOver=` / `MapVQ=` / `Overlays=` / `Targets=` / `ClickMap=` 以及一个数字子项键；**`ALL07` / `Sov07` 没有数字子项**（战役终点）。文件 **261 行全 CRLF**（`lone_LF=0`，`lone_CR=0`）。

---

## 2 · 引擎解析代码定谳（六函数 + 三个辅助体）

所有地址为 VA；`FOFF = VA − 0x400000`。`[本次读码]`

### 2.1 `0x005CEEF0` — 加载器（W33 称「MAPSELMD.INI loader」）

| 指令 | 语义 |
|---|---|
| `0x005CEF62 push 0x830370 ; 'MAPSELMD.INI'` | `CCFileClass` 构造文件名 |
| `0x005CEF6B call [eax+8]` / `0x005CEF78 call [edx+0x1c]` | `CCFileClass` vtable `0x7E16B0`：先磁盘后 MIX（W29 §1.1/§1.4）`[转引]` |
| `0x005CEF85 call 0x525A10` | `INIClass::Load`（`0x525A60` 逐行解析，行读取器 `0x65D5C0`） |
| `0x005CEF98 mov edi, 1` | **阵营段数字键循环从 `1` 开始** |
| `0x005CEFB1 mov edx, edi` → `0x005CEFB7 call 0x7B6290` | `0x7B6290` 是 `sprintf(str,"%d",int)`（`0x7B629A push 0x817F6C ; '%d'`），把序号转成键名字符串 |
| `0x005CEFC9 call 0x528C00` | `INIClass::Get_String(阵营段名, "<序号>", 输出)`（7 次同型调用） |
| `0x005CEFD4 sete bl` + `0x005CEFE7 jne 0x5CF073` | **查不到该序号即刻退出循环（首个缺口终止）** |
| `0x005CF04E inc edi` / `0x005CF04F cmp edi, 0x64` | **硬上限 100 个序号（1..100）** |
| `0x005CF007 call 0x5CF8E0` | 用读到的**阶段名**构造 `MapStage` 对象 |
| `0x005CF042 mov edx,[ebp+4]` / `0x005CF04B mov [edx+eax*4], esi` | 追加到 `DynamicVectorClass<MapStage*>`：`+4`=数组，`+0x10`=计数（RTTI 串 `.?AV?$DynamicVectorClass@PAVMapStage@@@@` @`0x830238` 佐证） |
| `0x005CF0E5 push 'Anims'` / `0x005CF13C push 'TextRect'` / `0x005CF25E push 'Palette'` / `0x005CF403 push 'Sounds'` | 另读 `[Anims]` / `[GDISFX]` / `[NODSFX]` 的 UI 配置（与本卡追加无关，但必须保留 → 这是「必须完整克隆」的又一硬理由） |

**阵营段的键是不是「阶段序号」？** —— **是**。`[本次读码]` 循环变量从 1 递增、用 `%d` 造键、遇首个缺失即停、上限 100；值是**阶段段名**（不是地图文件名）。官方正好 1..7 连续，故 v11 只能从 `8` 续接，不能跳号、不能重排。

### 2.2 `0x005CF8E0` + `0x005CFC80..0x005D006C` — `MapStage` 构造（读阶段段）

`[本次读码]`（`EVIDENCE/step3_disasm_stage.stdout.txt`）：

- `0x005CF9B0 call 0x7B4940` 把参数（阶段名）拷进 `[stage+0]` ⇒ **`[stage+0] = 阶段名**。
- `0x005CF9CA push 'Scenario'` → `0x005CF9F0 call 0x528C00` → `0x005CFA1D call 0x7B4940` 写入 `[stage+4]` ⇒ **`[stage+4] = Scenario= 值**。
- 依次读 `'Description'`、`'VoiceOver'`、`'MapVQ'`、`'Overlays'`、`'ClickMap'`、`'Targets'`、`Text1..Text7`（`0x005CFD4B call 0x7B6290` + `'Text'` 前缀，循环 1..7）。这些是 **MapSelect 界面资源**，不是推进链。
- **子项键循环**：`0x005CFF81 mov [esp+0x18], 0`（**从 0 开始**）→ `0x005CFFA6 call 0x7B6290`（`"%d"`）→ `0x005CFFB5 call 0x528C00`（读 `"0"`,`"1"`,…）→ `0x005CFFC0 setg bl`，缺失即 `0x005CFFD3 je` 跳过；`0x005CFFF1 mov al,[esp+0x18]` → `0x005CFFF5 mov [esi+4], al` ⇒ **数字键名被存成 1 字节的选择项编号**；`0x005D0037 cmp eax, 0x100` ⇒ **硬上限 256 个键（0..255）**；读到的**值**放入 `DynamicVectorClass<StringClass*>`（`+0x58` 数组 / `+0x64` 计数）。

**「候选子项」到底是阶段段里的哪些键？** —— **`0`..`255` 的纯数字键**（引擎按 `"%d"` 逐个查 INI，最多 256 个，遇缺失跳过继续；`Scenario`/`Description`/`MapVQ`/`Text1` 等非纯数字键永远不会被这个循环命中）。**值是「阶段名」**（`[stage+0]` 那一套名字），**不是 `.MAP` 文件名、不是 `NextScenario`**。`[本次读码]` 官方 `[ALL01] 2=ALL02` 即：颜色索引 2 的点击区域 → 名为 `ALL02` 的阶段。

**`N=名字` 是「下一阶段」吗？** —— **形式上是「候选子阶段名 + 点击图颜色索引」，在线性官方战役里恰好等于下一阶段**。`[本次读码]` `N` 是 ClickMap 的颜色号（`0x005CFFF5` 存成字节），值经 `0x005CF6B0` 反查成阶段对象；官方 `[ALL0i] (i+1)=ALL0(i+1)` 使 `N` 同时是下一关的阵营序号，但这是数据巧合，不是语法要求。最后一关（`ALL07`/`Sov07`）**没有数字子项**，与地图 `[Basic] EndOfGame=yes` 对应。

### 2.3 三个查找函数

| 函数 | 比对字段 | 证据 |
|---|---|---|
| `0x005CF6B0` | `[stage+0]` = **阶段名** | `0x005CF6E6 mov ecx,[eax+esi*4]`（无 `+4`） |
| `0x005CF760` | `[stage+4]` = **`Scenario=` 值（地图文件名）** | `0x005CF799 add ecx, 4` |
| `0x005CF810` | 按**序号**取 `stages[index]` | `and eax,0xffff`；`cmp [ecx+0x10],eax`；`mov eax,[ecx+eax*4]`（`0x005CF825/828`） |

两个字符串查找都遍历 `+4` 数组 / `+0x10` 计数，各自对**两个操作数**调用 `0x7B5B30` 归一化（共 4 次），再用 `0x7B4780` 比较（共 2 次）。`[本次读码]`

`0x005CF830` 是 `stages[i]->Get_Index()` 的薄封装（`call [eax+0x10]`），`0x005ADF20` 用它把新阶段序号写回 `[Scen+0x35A0]`。

### 2.4 `0x005AE220` — `SkipMapSelect=no` 路径（v10 生成的地图全是该值）

`[本次读码]`：`0x005AE2BE call 0x5CEEF0`（加载）→ `0x005AE2F5 add ebp,0x125c`（取当前地图名 `[Scen+0x125C]`）→ `0x005AE300 call 0x7B4630` → **`0x005AE30C call 0x5CF760`（按 `Scenario=` 反查当前阶段）** → 查不到则 `0x005AE320 push 0x82C134`（`"MapSelect: Invalid stage!\n"`）并失败弹 `MSG:UnableMapSelect`（W33 `[转引]`）。
⇒ 我方每张地图必须有一个 `Scenario=<当前地图名>` 的阶段段，否则第一关通关即报错。

### 2.5 `0x005ADF20` — `SkipMapSelect=yes` 路径

`[本次读码]`：`0x005ADFA0 call 0x5CEEF0` → `0x005ADFD7 mov ax,[ebp+0x35a0]` → `0x005ADFE1 call 0x5CF810`（当前阶段）→ `0x005AE018 mov eax,[ebx+0x64]`（子项数）、`0x005AE025 mov ecx,[ebx+0x58]`（子项名数组）→ 对每个名字 `0x005AE032 call 0x5CF6B0`（**按阶段名反查**）→ `0x005AE03D lea edx,[esi+4]`（命中阶段的 `Scenario=`）→ `0x005AE04A / 0x005AE061 call 0x7B5B30`（两边归一化）→ `0x005AE073 call 0x7B4780` 与传入的 `NextScenario` 比对 → 命中后 `0x005AE09B call 0x7B5440` + `0x005AE0A7 call 0x686700` 把**命中阶段的 `Scenario=`** 写入 `[Scen+0x125C]`，`0x005AE0AF call 0x5CF830` + `0x005AE0B8 mov [ebx+0x35a0],ax` 更新阶段序号。

⇒ 两条路径都要求 `MAPSELMD.INI` 认识我方地图（W33 判定成立 `[转引]`，本卡六函数逐条复核）。仅改 `SkipMapSelect` 或仅打包 MIX 都不修。`[静态推断]`

### 2.6 辅助体（决定大小写与换行）

- `0x7B5B30`：逐字节 `cmp dl,0x41 / cmp dl,0x5a`，仅对 `'A'..'Z'` 调 `0x7CAFF4`，后者 `add eax,0x20`（tolower）。**归一化方向是「转小写」，不是 W33 说的「转大写」**。`[本次读码]`
- `0x7B4780`：函数体内**无任何 `call`**，是一个大小写敏感的逐字节比较 ⇒ 值比对之所以不敏感，完全靠调用方先归一化。`[本次读码]`
- `0x65D5C0`（INI 行读取器）：`0x65D600 cmp al,0xa; je 0x65d634`（**LF 终止一行**）；`0x65D604 cmp al,0xd; je 0x65d616`（**CR 被跳过、再读下一字节，不终止**，`0x65D627 je 0x65d5f8` 回到循环）。`[本次读码]`

---

## 3 · 逐条回答卡面五问

| 问题 | 定谳 | 等级 |
|---|---|---|
| 阵营段 `[GDI]`/`[Nod]` 的键是阶段序号吗？ | **是**。从 `1` 起连续整数，`%d` 造键，**首个缺口即停**，硬上限 100；值是**阶段段名**。官方 `1..7`。 | `[本次读码]` |
| 阶段段里 `N=名字` 是「下一阶段」吗？ | **不是语法意义上的「下一关文件」**：`N` 是 ClickMap 颜色索引（`0..255`，存成 1 字节），值是**候选子阶段的段名**；官方线性战役中恰好指向下一阶段。最后一关无数字子项。 | `[本次读码]` |
| `SkipMapSelect=yes` 的「候选子项」是哪些键？ | 当前阶段段内 **纯数字键 `0..255`**（引擎按 `"%d"` 逐个 `Get_String`，遇缺失跳过继续，最多 256 个）；非数字键（`Scenario=`、`MapVQ=`、`Text1=` …）不参与。每个值经 `0x005CF6B0` 按阶段名反查，再取该阶段的 `Scenario=` 与 `NextScenario` 比对。 | `[本次读码]` |
| 大小写敏感性？ | **值比对大小写不敏感**，但机制是**两边先转小写**（`0x7B5B30`→`0x7CAFF4` 对 `'A'..'Z'` 加 `0x20`）再用大小写敏感的 `0x7B4780` 比较；W33「统一转大写」措辞有误。**INI 段名/键名未经归一化**（`0x4A1DE0` 是裸 CRC32，Load 路径只见 `0x727CF0` trim），故必须照抄官方拼写 `[GDI]`/`[Nod]`/`[ALL01]`/`[Sov01]`。 | `[本次读码]`（段名大小写敏感性为 `[静态推断]`，见 §5） |
| 行尾 CRLF/LF 影响解析吗？ | 官方文件 **261 行全 CRLF**（`[本次实测]`）。行读取器 **CRLF 可行**（CR 跳过、LF 终止）、**单 LF 亦可行**（直接终止）、**单 CR 不可行**（不终止，会吞掉下一行首字节）。v11 一律输出 CRLF。 | `[本次读码]` + `[本次实测]` |

---

## 4 · 严格语法规格（v11 生成契约）

```
; 文件整体 = 官方完整文件 + 追加，CRLF，Latin-1/ASCII，无 BOM/NUL

[<阵营段>]                    ; 官方只有 [GDI] (allied) 与 [Nod] (soviet)
Anims=<...>  Sounds=<...>     ; 官方 UI 配置，必须原样保留
1=<阶段段名>                  ; 从 1 起连续整数键；首个缺口终止加载
...                           ; 最多 100 个（引擎 cmp edi,0x64）
7=<阶段段名>
8=<追加阶段段名>              ; ← v11 按 design.campaign.side 追加到对应阵营段末尾
...

[<阶段段名>]                  ; 每个阶段段（官方 + 追加）
Scenario=<地图文件名.MAP>     ; [stage+4]，0x005CF760 / 0x005ADF20 用它比对
Description=<...>            ; UI：CSF 标签号或空
VoiceOver=<...>  MapVQ=<...> ; UI：资源名
Overlays=<...> Targets=<...> ; UI
ClickMap=<...>               ; UI：PCX
Text1..Text7=<...>           ; UI（可选，官方未填）
0..255=<候选子阶段段名>        ; 数字键 = ClickMap 颜色索引；值 = 阶段名
                              ; 最后一个阶段段不写数字键 ⇒ 战役终止侧
```

**v11 追加规则**（`ra2forge/mapselmd.py`）：

1. **必须克隆官方全文再追加**：`load_bundled_official()` 校验 bundled 资源 5,573 B / SHA-256 `074ccccd…`；`validate_official_base()` 还要求 20 个官方段、`[GDI]`/`[Nod]` 的 `1..7` 完整、14 个官方阶段段都有 `Scenario=`。**最小文件 / 部分文件一律 `MapselmdError` 硬拒绝**（与 W29 CSF 警告同类）。
2. **阵营映射**：`side=allied → [GDI]`，`side=soviet → [Nod]`；`side=yuri` 官方无对应段，**拒绝并报错**（不臆造 `[Yuri]`）。`[静态推断]` + `[待运行验证]`。
3. 追加键从现有最大序号 +1 开始（官方是 `8..`），连续、不跳号；总序号 ≤100。
4. 每张我方地图生成一个 `[RA2F_<任务名>_<8hex>]` 段，`Scenario=<MAP>.MAP`；UI 字段克隆该阵营官方最后一关（`ALL07`/`Sov07`）的值，保证引用的 VQA/SHP/PCX 都是真实存在的资源。
5. 非最后阶段写 **一个** `2=<下一阶段段名>`（颜色 2 在两阵营官方文件里都确证存在：`[ALL01] 2=ALL02`、`[Sov01] 2=Sov02`）；**最后阶段不写数字子项**，与 builder 写出的 `EndOfGame=yes` 对应。
6. 生成后**读回字节自检**：官方每一行按原序逐行存活、官方段/键零改动、追加键与子链接正确、末段无子项、100% CRLF。
7. 产物作为**散装 `MAPSELMD.INI`** 投放（W29 Q1：磁盘优先，MIX 内同名不再被查询）`[转引]`。

---

## 5 · 明确标为 `[待运行验证]` 的部分

1. **真机推进**：本卡只做离线实现与回归。`SkipMapSelect=no` 的交互式 MapSelect 界面在追加阶段上能否被玩家点选到下一关（ClickMap 颜色 2 的区域、`Targets=`、`MapVQ=`、`Description=791` 沿用官方最后一关文案）**未经真机验证**；本卡**不写「已修复战役推进」**。
2. **阵营段名的来源**：`0x005ADF40..0x005ADF7B` 从 `SideClass+0x24` 取名字传给加载器；官方文件用 `[GDI]`/`[Nod]`，但「Yuri 阵营究竟请求哪个段名」在 exe 中未找到独立 `Nod` 字面量（只有 `TXT_NOD`），故 v11 拒绝 yuri 而不猜。`[静态推断]` + `[待运行验证]`。
3. **INI 段名/键名大小写**：`INIClass::Get_String` 用 `0x4A1DE0`（裸 CRC32）哈希段名/键名，`Load` 路径只观察到 `0x727CF0`（trim）。由此静态推断「段名/键名应按官方原样拼写」，但**是否完全大小写敏感**未做运行期全称证明（W29 §3 同样是有界声明）。v11 一律照抄官方拼写。
4. **散装 `MAPSELMD.INI` 端到端覆盖 MIX 内同名**：W29 Q1 只定谳了分支顺序（磁盘优先），端到端为 `[待运行验证]` `[转引]`。
5. **追加阶段的 UI 表现**：`Description=791`（Sov07 的 CSF 标签号）等克隆值只保证结构合法，不保证文案正确；如需专属文案须另做 CSF 卡。

---

## 6 · 未改动项

- `verify.py` 与 v10 **逐字节相同**（`V11_FILES.sha256.txt`：`051c2e214b0d9862…`），既有语义未削弱。
- `install.py` 的 `TOOL_VERSION` 仍为 `1.0`（回归 P1/P2 断言该值），v11 只是目录版本号。
- 不启用 `--mapselmd` 时，构建产物与 v10 **7/7 文件 SHA-256 全同**（`out/SHA256_V10_V11.txt`、`EVIDENCE/step4_compat_sha256.stdout.txt`）。
