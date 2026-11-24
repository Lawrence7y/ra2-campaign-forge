# W29 · 纯静态定谳：引擎的资源覆盖顺序（散装文件 vs MIX 内同名文件）

- run_id：`NEXT_RE_20261112_R02` ｜ 交付目录：`lead/next_re_20261112_r02/W29_override_order/`
- 目标二进制：`D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe`
  - 4,825,360 B；MD5 `4f37486e5b0dbe2ae5f45aeee0f98367`；SHA256 `73201cc0…dc22e9ae16c7e7365354b65f3fcf67476`
  - `ImageBase=0x400000`，`Characteristics=0x32F`（`RELOCS_STRIPPED`），`DllCharacteristics=0x20`
  - `.text` RVA=FOFF=0x1000（故 `.text` 内 **FOFF = VA − 0x400000 = RVA**）；`.text` raw SHA256
    `c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738`
  - 与 `docs/re/fs_mix_load_chain*.md` 所分析的 `ra2youli/gamemd.exe` **MD5 / .text 哈希完全一致** ⇒ 同一镜像，地址可直接复用；但本卡所有关键指令均在本文件上**逐字节独立复核**（见 `EVIDENCE/override_order_stdout.txt`，60/60 断言 OK，exit 0）。
- **纪律**：纯静态只读。未启动游戏、未 attach、未读活进程、未注入、未写 `ra2youli`、未改他人目录、无 `git` 写操作。
- **红线遵守**：`ra2forge/mixlib.py` **未被导入、未被当作引擎行为证据**。CRC32 只用 `zlib.crc32` 直接计算，并与既有**真实 MIX 产物**的实测 id 交叉核对（见 §5）。

---

## 0 · 结论速览（先看这个）

| # | T2 问题 | 结论 | 等级 |
|---|---|---|---|
| Q1 | 散装 `ra2md.csf` 与 MIX 内同名条目同时存在，取哪个？ | **取散装**。引擎 `CCFileClass::Get_File` 先 `CreateFileA` 试磁盘，成功即**跳过** `MixFileClass::Find`；MIX 只是失败后的回落。且 CSF 加载器 `0x7346A0` **确实**经 `Get_File` 打开运行时构造出的 `ra2md.csf` | 分支顺序 **[本次实测]**；端到端 **[待运行验证]** |
| Q2 | 前缀 / 目录如何处理 | **名字原样、相对 CWD（= 游戏目录 / exe 同级）**，无盘符/子目录前缀、**不递归**；`MIXFILES\` 只是少数次级 MIX 字面量名字的一部分，不是通用搜索路径；`[CD]/CDPath/InstallPath` 全镜像 0 命中 | **[本次实测]**（GetFileName / CreateFileA / IAT / CWD 设置）+ **[静态推断-强]**（CWD=游戏目录） |
| Q3 | 是否有"优先级表 / 扩展名特例" | **有表，但只是 MIX 间 FIFO 链表** `List<MixFileClass*>` @ `0xABEFD8`（先装载者优先）；**没有按扩展名的优先级表**。唯一"特例"是 `Get_File` 的 `mode&2` 位（强制只走磁盘），与扩展名无关 | **[本次实测]**（无扩展名分支/字面量 xref）+ **[静态推断-强]**（有界搜索，非全称证明） |
| Q4 | `BATTLEMD*.INI` 加载顺序 | **都加载并合并**，不是二选一：先 `FindFirstFileA("BATTLEMD*.INI")` 通配枚举（纯 FS、看不到 MIX）逐个 `Load`+归并；再按 `[Battles]` 条目名 `_stricmp` 合并到全局表 `0xA83CF8`，同 ID **后装载者覆写**。回退分支（`CCFileClass("BATTLEMD.INI")`，mix 感知）**仅在目录里一个 `BATTLEMD*.INI` 都没有时**才执行 | 路径/合并 **[本次实测]**；枚举顺序决定的最终胜者 **[静态推断-弱]** / **[待运行验证]** |

> **对 C 线（DLC）的直接含义**：候选 1「放散装 `ra2md.csf` 覆盖 MIX 内同名」在**资源查找顺序上成立**，且比"覆盖"更强 —— 磁盘一旦命中，MIX 内那份**根本不会被查询**，散装文件**不需要 MIX 里有同名条目**即可独立生效。
> **但有两个硬约束**：(a) 散装 CSF 必须是**完整合法 CSF**（含全部官方标签 + 自定义标签），否则 `0x734799` 的 `" FSC"` 魔数检查失败 → `0x6BD85A` 分支弹出 `Unable to initialize 'ra2.csf'` 并**启动失败**；(b) `Description=` 是 CSF 标签位，自定义简介必须以 CSF 标签（如 `DESC:MYCAMP`）提供，纯文本仍显示 `MISSING:'…'`。

---

## 1 · T1：定位到的资源查找 / 打开路径

### 1.1 主查找链（`CCFileClass`，vtable `0x7E16B0`）

`EVIDENCE/override_order_stdout.txt` 中每个地址都给出 VA / RVA / FOFF / 原始字节 / Capstone 反汇编。核心：

```
CCFileClass::Get_File  = 0x473D10   (vtable 0x7E16B0 +0x1C)   ← 取数主路径
 0x473D1D  F6 44 24 20 02        test byte [esp+0x20],2      ; mode & 2
 0x473D22  0F 85 11 01 00 00     jne  0x473E39                ; mode&2 → 只走磁盘，连 MIX 都不查
 0x473D2D  E8 DE E1 FB FF        call 0x431F10                ; ★ 先试磁盘（散装）
 0x473D32  84 C0                 test al,al
 0x473D34  0F 85 FF 00 00 00     jne  0x473E39                ; ★ 磁盘命中 → 跳到磁盘读，跳过 MIX
 0x473D3A..0x473D66              准备 out 参数 + call [vtbl+4] (GetFileName)
 0x473D68  E8 C3 06 14 00        call 0x5B4430                ; ★ 失败才回落 MixFileClass::Find
 0x473D6D  84 C0                 test al,al
 0x473D6F  0F 84 AF 00 00 00     je   0x473E24                ; MIX 也未命中 → 尾部路径
 0x473D75..0x473DDF              MIX 命中：已缓存→BufferClass；未缓存→用容器名重开+Seek
 0x473E39  8B 54 24 20 ... E8 6B 6C 00 00   call 0x47AAB0     ; 磁盘读路径
```

**顺序证据（指令级，非"线性计数"）**：
- 磁盘尝试的 **call site `0x473D2D`** 在控制流上先于 MIX 查找的 **call site `0x473D68`**；
- `0x473D34` 的 `jne` 目标 `0x473E39` **大于 `0x473D68`**，即磁盘成功时**直接越过**整个 MIX 分支；
- `0x473D22`（`mode&2`）同样直达 `0x473E39`，是更强的"磁盘独占"。
- ⇒ 回退条件 = **`0x431F10` 返回 false**（磁盘文件不存在/打不开）；且 `mode&2 == 0`。
- 脚本 `override_order.py` 把上述关系编码为 `ORDER_OK`（见 `EVIDENCE/override_order_stdout.txt` 的 "DECODED CONTROL-FLOW RELATIONS"），`--selftest` 的 **N2 反例**专门反证"MIX 优先"假设。

磁盘支路（名字原样）：
```
0x431F10  8A 41 29              mov al,[ecx+0x29]
0x431F1E  E8 CD AC 22 00       call 0x65CBF0   ; RawFileClass::Open(0)
0x65CBF4  8B 46 18             mov eax,[esi+0x18]   ; FileName
0x65CC58  52                   push edx             ; 名字原样
0x65CC59  FF 15 BC 11 7E 00    call [0x7E11BC] = KERNEL32!CreateFileA
```
IAT 由 `pefile.DIRECTORY_ENTRY_IMPORT` 独立解析：`[0x7E11BC]=CreateFileA`、`[0x7E1208]=FindFirstFileA`、`[0x7E120C]=FindNextFileA`、`[0x7E1300]=FindClose`、`[0x7E1148]=SetCurrentDirectoryA`、`[0x7E11A8]=GetModuleFileNameA`、`[0x7E1460]=MessageBoxA`。

`GetFileName`（vtable+4 = `0x401940`）= `8B 41 18 C3` (`mov eax,[ecx+0x18]; ret`) —— **只返回原始名字指针，不做任何路径/盘符/扩展名改写**。这是 Q2 的关键硬证据。

### 1.2 MIX 内条目查找（`MixFileClass::Find = 0x5B4430`）

```
0x5B4470  E8 4F 8B 22 00     call 0x7DCFC4    ; strupr（已复核：sub cl,0x20 小写→大写）
0x5B449C  E8 3F D9 EE FF     call 0x4A1DE0    ; CRC32(大写名)
0x5B44A1  8B 2D E0 EF AB 00  mov ebp,[0xABEFE0]   ; Head.Next = 最早装载的 MIX
0x5B44D5..0x5B44F9           条目表二分（entry = {u32 id; u32 offset; u32 size}）
0x5B4507  8B 6C 24 14        mov ebp,[esp+0x14]   ; = node->Next，前进到更新的 MIX
0x5B450B  EB 9C              jmp 0x5B44A9          ; 循环；首个命中在 0x5B450D 返回
```
⇒ **MIX 间 FIFO / 先装载者优先**。优先级表 = `List<MixFileClass*>` @ `0xABEFD8`（Head.Next `0xABEFE0`，Tail.Prev `0xABEFF0`）。`--selftest` 的 **N3 反例**验证起点是 `0xABEFE0` 而非 `0xABEFF0`（后者会意味着 LIFO）。

> 补充（**有符号排序**）：`ra2bench/langmd.mix` 未加密，其 10 个条目的 id 按**有符号 32 位**升序（本卡独立复算，`EVIDENCE/override_order_stdout.txt` 尾部），与引擎二分使用有符号跳转相容；按无符号看会误判为"未排序"。

### 1.3 MIX 头魔数 / 加密判定（`MixFileClass` ctor `0x5B3C20`）

```
0x5B3CED  ... push 4 ... call [edx+8]     ; 读明文 4 字节头
0x5B3CF7  66 39 5C 24 28     cmp word [esp+0x28],bx   ; word0 == 0 → TS/RA2 新头
0x5B3CFC  75 51              jne 0x5B3D4F             ; word0 != 0 → 老式 C&C 头
0x5B3D02..0x5B3D0E          flags: bit0→[esi+0x10], bit1(加密)→[esi+0x11]
0x5B3D11  74 2C              je 0x5B3D3F              ; 未加密旁路（跳过 PKStraw/RSA）
0x5B3D3F  ... push 6 ... call [edx+8]     ; 读 numFiles(u16)+bodySize(u32)
0x5B3D8A  new(numFiles*12) → 条目表
```
MIX 扩展名字符串：`.MIX` 字面量 67 处（装载器名字，如 `EXPANDMD%02d.MIX` @ `0x82668C`、`RA2MD.MIX` @ `0x82667C`、`LANGMD.MIX` @ `0x840D5C`、`LANGUAGE.MIX` @ `0x840D4C`），`.mix` 小写 0 命中。**没有 MIX 魔数常量比较**（只有 `word0==0` 的格式判别）。

### 1.4 ⚠️ 必须一起记住的陷阱：`Open` 与 `Get_File` 顺序**相反**

```
CCFileClass::Open = 0x473C50 (vtable +0x14)
 0x473C69  call [eax+0x18]      ; Is_Available
 0x473C84  call [edx+4]         ; GetFileName
 0x473C8B  E8 A0 07 14 00      call 0x5B4430   ; ★ MIX 存在性探测（无输出参数, edx=0）
 0x473C94  ...                  ; 命中 → [esi+0x68]=1, return true
 0x473CA2  E8 69 E2 FB FF      call 0x431F10   ; ★ 磁盘 Open（在 MIX 探测之后）
```
**若只盯 `Open`，会得出"MIX 优先"的相反结论。** 但 `Open` 里的 `0x5B4430` 是**可用性探测**：命中只置 `[esi+0x68]=1`，**不装载数据、不设置 `[esi+0x58]` 内存缓冲**。实际取数由 `Get_File`（`0x473D10`）/ `Read`（`0x473B10`）决定，而它们的回落顺序是磁盘优先。本卡以 `Get_File` 为准，并明确标注此差异。

### 1.5 CSF 具体落地：`0x7346A0` 把 `"ra2md.str"` 变成 `"ra2md.csf"` 再走 `Get_File`

这是本卡相对既有研究**新增闭环**的一环（`docs/re/fs_mix_load_chain_deep.md` §5.4 只提到 `"ra2md.str"` 与 MessageBox，未展开文件名构造与取数通道）：

```
Startup 0x6BD84E  B9 40 0D 84 00   mov ecx,0x840D40   ; "ra2md.str"
        0x6BD853  E8 48 6E 07 00   call 0x7346A0      ; 装载字符串表
        0x6BD85A  75 28             jne 0x6BD884        ; 成功
        0x6BD863  68 58 0C 84 00   push 0x840C58       ; "Unable to initialize 'ra2.csf'..." (三语文案)
        0x6BD869  FF 15 60 14 7E 00 call [0x7E1460]    ; MessageBoxA → 启动失败

0x7346A0  (参数 ecx = 基名)
 0x7346F7  6A 2E                push 0x2E             ; '.'
 0x734702  68 B0 3E B1 00       push 0xB13EB0         ; 名字缓冲
 0x734713  E8 18 68 09 00       call 0x7CAF30         ; strchr(buf,'.')
 0x73471F  C6 00 00             mov byte[eax],0       ; 截断扩展名
 0x734722  BF EC 57 84 00       mov edi,0x8457EC      ; ".csf" (独立字面量, 全 exe 唯一代码引用)
 0x73474B  F3 A5                rep movsd             ; strcat(".csf") ⇒ "ra2md.csf"
 0x734758  E8 93 F2 D3 FF       call 0x4739F0         ; CCFileClass ctor("ra2md.csf")
 0x734764  E8 E7 F4 D3 FF       call 0x473C50         ; Open(0)
 0x734771  6A 01                push 1                ; mode=1 (bit1=0 → 允许回落 MIX)
 0x734777  E8 94 F5 D3 FF       call 0x473D10         ; ★★ Get_File：散装优先
 0x73478F  E8 7C F3 D3 FF       call 0x473B10         ; Read(0x18) CSF 头
 0x734799  81 7C 24 08 20 46 53 43  cmp [esp+8],0x43534620  ; " FSC" 魔数
 0x7348BC  B9 B0 3E B1 00       mov ecx,0xB13EB0      ; ★同一个名字缓冲
 0x7348C1  E8 CA 00 00 00       call 0x734990         ; 第二阶段读同一 CSF（全 exe 唯一调用点）
```

- ⇒ 引擎**运行时拼接** `ra2md.csf`；静态搜 `ra2md.csf` 字面量 **0 命中是必然的**（`"ra2.csf"` 的 3 处命中全部是**过时 MessageBox 文案**，不是请求名）。零命中纪律见 §4。
- ⇒ `E8` 原始扫描：`0x734777` 与 `0x7349C2` 是 `Get_File` 的调用点，且都属 CSF 装载家族（`0x734990` 由 `0x7348C1` 以**同一文件名**调用）⇒ **字符串表单一来源，无第二 CSF 兜底**。
- ⇒ **若游戏目录存在散装 `ra2md.csf`，`0x473D2D` 的 `CreateFileA` 成功，`0x473D68` 的 MIX 查找被 `0x473D34` 跳过** —— MIX 内的 CSF 完全不参与。

---

## 2 · T2 逐条回答

### Q1 · 散装 vs MIX 同名条目，谁优先？

**答：散装文件优先**（`[本次实测]` 指令级；端到端 `[待运行验证]`）。

依据（三条互不依赖）：
1. **分支顺序**：`Get_File` 的 `0x473D2D`（磁盘）在 `0x473D68`（MIX）之前；`0x473D34 jne 0x473E39` 的目标 `0x473E39 > 0x473D68`，磁盘成功即跳过 MIX。`mode&2` 时 `0x473D22` 更是直达磁盘、连 MIX 探测都不做。
2. **回退条件**：只有 `0x431F10`（→ `RawFileClass::Open` → `CreateFileA`）返回 false 才执行 `MixFileClass::Find`；MIX 再未命中走 `0x473E24` 尾部。
3. **CSF 通道直接证据**：`0x7346A0` 明确以 `mode=1` 调 `Get_File(0x473D10)` 打开 `ra2md.csf`（§1.5）。不是"推测 CSF 也走 CCFileClass"，而是**逐字节看到** ctor→Open→Get_File→Read→`" FSC"` 魔数检查。

**"覆盖"其实更强**：磁盘命中时 MIX 内同名条目**根本不会被查询**，故散装 CSF 不依赖 MIX 内是否存在同名条目。同理适用于任何经 `CCFileClass` 请求的资源（INI/SHP/…）。

**未能静态定谳的部分**：`0x473E24`（MIX 未命中后的尾部）与 `0x473E39`（磁盘读）都 `call 0x47AAB0`，其精确语义（是否某些 mode 下二次尝试磁盘）未逐分支展开 → 列入 `UNKNOWNS.md`。这不改变"磁盘优先"的分支顺序结论。

### Q2 · 前缀 / 目录如何处理？

**答：名字原样、相对 CWD（游戏目录）、不递归子目录**（`[本次实测]` + `[静态推断-强]`）。

- `GetFileName`（`0x401940`）= `mov eax,[ecx+0x18]; ret`，**无前缀/盘符/子目录/扩展名改写**；`RawFileClass::Open` 把 `[esi+0x18]` 原样压栈给 `CreateFileA`（`0x65CC58/0x65CC59`）。
- **CWD = exe 所在目录**：`0x6BBFDB call [0x7E11A8]` = `GetModuleFileNameA`，`0x6BC07C call [0x7E1148]` = `SetCurrentDirectoryA`（IAT 已解析）。`CreateFileA` / `FindFirstFileA` 用相对名 ⇒ 解析到 CWD。
- **不递归**：`FindFirstFileA("BATTLEMD*.INI")`（`0x52CBA9`）只枚举 CWD 一层；属性过滤 `0x116`（`0x52CBBF`）。
- `MIXFILES` 字面量 5 处（`@0x8266A0` 等）是**次级 MIX 装载器里若干具体文件名的一部分**（`MIXFILES\MOVIES01.MIX` 等），不是通用搜索路径；它不参与 `CCFileClass` 的名字解析。
- `[CD]` / `CDPath` / `InstallPath`：全镜像 **0 命中**（ASCII 精确 / 大小写不敏感 / UTF-16LE 三编码）。`-CD` 参数只登记 CD 路径列表（`0x89E410`），其唯一消费者是次级装载器的二次 `FindFirstFileA` 通配（MAPS*/MOVIES* 系列），**不进散装/MIX 查找链**。
- ⇒ 结论里的"散装文件"= **游戏目录（exe 同级）下的原始文件名**。

### Q3 · 是否存在列出优先级的表（含扩展名特例）？

**答：有表，但只是 MIX 间的 FIFO 链表；没有按扩展名的优先级表**（`[本次实测]` 有界搜索 + `[静态推断-强]`）。

- **有**：`List<MixFileClass*>` @ `0xABEFD8`，`Find` 自 `Head.Next=0xABEFE0` 起、`node->Next` 前进（`0x5B44A1/0x5B4507/0x5B450B`）⇒ **先装载者优先**。既有研究给出完整序列（`docs/re/fs_mix_load_chain_deep.md` §1.5，本卡只复核了关键指令与 langmd/language 的 Startup 装载点 `0x6BD7EF/0x6BD81F`）：
  `散装 > langmd.mix > language.mix > expandmd99 > … > expandmd00 > ra2md.mix > ra2.mix > cachemd > cache > localmd > local > ecache* > elocal* > 次级(CONQMD…MOVIES*)`。
- **没有扩展名特例表**：
  - 全文件扫描扩展名字面量（ASCII 精确 / 大小写不敏感 / UTF-16LE）：`.csf` 4 命中中**只有 1 处是代码引用** —— `0x734723 mov edi,0x8457EC`，用途是**拼接 CSF 文件名**，不是优先级判定；`.CSF`/`.STR` 0 命中；`.INI` 36 处与 `.MIX` 67 处均为具体文件名/通配模式。
  - `GetFileName` 不检查扩展名；`MixFileClass::Find` 只 `strupr` + `CRC32`，无扩展名分支；`CCFileClass` 方法族（`0x4739F0`–`0x473F00`）未见按扩展名分派。
  - 唯一"模式特例"是 `Get_File` 的 **`mode&2`**（`0x473D1D/0x473D22`）→ 强制只走磁盘；以及 `CCFileClass::Open` 的存在性探测顺序差异（§1.4）。二者都是**调用参数/阶段**，不是按扩展名的表。
- **有界声明**：以上是"在 4,825,360 B 全文件、三种编码、字面量与 imm32 xref、关键函数体"范围内的搜索结论，**不是运行期全称证明**；脚本 `--selftest` 的 N6/N7 用已知存在/不存在的串做正控，证明扫描器未失效。

### Q4 · `BATTLEMD*.INI` 加载顺序（`BATTLEMD.INI` vs `BATTLEMD98.INI`，谁先 / 是否合并）

**答：都加载、按 `[Battles]` 条目名合并；不是二选一。同 ID 后装载者覆写；跨文件先后 = 目录枚举顺序**（路径/合并 `[本次实测]`，枚举胜者 `[静态推断-弱]`/`[待运行验证]`）。

```
LoadBattleMdIni = 0x52CB90 (callers: 0x52C605 Init, 0x52DF25, 0x52E0C4, 0x685609 运行期重读)
 0x52CBA0  68 A8 61 82 00       push 0x8261A8        ; "BATTLEMD*.INI"
 0x52CBA9  FF 15 08 12 7E 00    call [0x7E1208]      ; FindFirstFileA（纯 FS / CWD / 不递归 / 看不到 MIX）
 0x52CBB8  0F 84 0F 01 00 00    je 0x52CCCD          ; INVALID_HANDLE_VALUE → 回退
 0x52CBBF  F7 84 24 84 00 00 00 16 01 00 00  test [esp+0x84],0x116   ; 属性过滤
 0x52CBF6  E8 F5 6D F4 FF       call 0x4739F0        ; CCFileClass ctor(枚举到的名字)
 0x52CC49  E8 A2 75 F4 FF       call 0x4741F0        ; INIClass::Load
 0x52CC4E  68 98 61 82 00       push 0x826198        ; "BATTLEMD.INI"
 0x52CC54  E8 C7 C0 29 00       call 0x7C8D20        ; _stricmp → 置"已见基准名"
 0x52CC60  C6 44 24 13 01       mov byte[esp+0x13],1
 0x52CC67  E8 A4 01 F4 FF       call 0x46CE10        ; ★ 归并进全局 Battle 表
 0x52CCAB  FF 15 0C 12 7E 00    call [0x7E120C]      ; FindNextFileA → 循环
 0x52CCC7  0F 85 92 00 00 00    jne 0x52CD5F         ; 已见 BATTLEMD.INI → 跳过回退
 -- 回退（仅当目录里一个 BATTLEMD*.INI 都没有）--------------------------------
 0x52CCCD  68 98 61 82 00       push 0x826198        ; "BATTLEMD.INI"（显式名）
 0x52CCD6  E8 15 6D F4 FF       call 0x4739F0        ; CCFileClass ctor（mix 感知）
 0x52CD2C  E8 DF 00 F4 FF       call 0x46CE10        ; 同一个归并函数
```

合并实现 `0x46CE10`：`0x46CE17 push 0x81B1D8`（段名 `"Battles"`）→ 枚举段内条目名 → 与全局表 `0xA83CF8`（Items `0xA83CFC`，Count `0xA83D08`，元素 0x3A0 B，名字在 `+0x24`）用 `_stricmp` 比对 → **同名复用同一对象再 `vtbl+0x64(ini)` 覆写字段**（per-key last-write-wins），不同名追加新对象。

要点：
- `BATTLEMD.INI` 与 `BATTLEMD98.INI` **都会被枚举并合并**；通常字母序下 `BATTLEMD98.INI` 靠后 ⇒ 同 ID 时它覆写官方值（**[静态推断-弱]**：`FindFirstFileA` 顺序引擎不保证，NTFS 近似字母序）。
- 全镜像只有 `"BATTLEMD.INI"`（`0x826198`）和 `"BATTLEMD*.INI"`（`0x8261A8`）两个字面量，**没有 `"BATTLEMD98.INI"`**（`--selftest` N6 正控）。⇒ **MIX 内 `BATTLEMD98.INI` 永不加载**（通配走 Win32 API，结构上不可能看到 MIX 条目）。
- MIX 内官方名 `BATTLEMD.INI` 只在**目录里没有任何散装 `BATTLEMD*.INI`** 时经回退分支被读到（该路 `CCFileClass` 是 mix 感知的）；一旦存在任一散装 `BATTLEMD*.INI`，`0x52CCC7` 跳过回退。
- **对 C 线**：要"用自己的战役覆盖官方位置"，可靠通道是**游戏目录散装 `BATTLEMD98.INI`**：用相同战斗 ID（如 `ALL1`）覆写，或用新 ID 追加；不要指望把它打进 MIX。

---

## 3 · T3 结论分级总表

| 编号 | 结论 | 等级 | 依据 |
|---|---|---|---|
| C1 | 目标二进制与既有研究镜像同一（MD5/.text hash） | **[本次实测]** | `override_order.py` stdout，MD5 + SHA256 + 段表 |
| C2 | `Get_File` 磁盘先于 MIX、磁盘成功跳过 MIX、`mode&2` 独占磁盘 | **[本次实测]** | 60/60 字节断言 + `ORDER_OK` 结构判据；`EVIDENCE/override_order_stdout.txt` |
| C3 | 磁盘路径 = 名字原样 `CreateFileA`；`GetFileName` 不改写 | **[本次实测]** | `0x401940`/`0x65CBF4`/`0x65CC59` + IAT 解析 |
| C4 | MIX 间 FIFO 先装载者优先（`0xABEFD8`） | **[本次实测]** | `0x5B44A1/0x5B4507/0x5B450B` + N3 反例 |
| C5 | MIX 头 `word0==0` 判别 + flags bit1 加密旁路 | **[本次实测]** | `0x5B3CF7/0x5B3CFC/0x5B3D0E/0x5B3D11` |
| C6 | CSF 加载器把 `"ra2md.str"` 拼成 `"ra2md.csf"` 并走 `Get_File`，单一来源 | **[本次实测]** | `0x7346F7`–`0x7348C1` 全部字节断言；`0x8457EC`/`0x840D40` xref |
| C7 | `"ra2.csf"` 只是过时 MessageBox 文案，不是请求名 | **[本次实测]** | C 字符串上下文（`EVIDENCE/recon2_stdout.txt`）+ 三编码 0 命中 |
| C8 | CWD = 游戏目录（exe 同级） | **[静态推断-强]** | `0x6BBFDB GetModuleFileNameA` + `0x6BC07C SetCurrentDirectoryA` 均实测命中，但"取目录部分"的中间代码未逐条展开 |
| C9 | `[CD]/CDPath/InstallPath` 不进查找链 | **[静态推断-强]** | 三编码全文件 0 命中 + 既有 deep 文档机制解释（`docs/re/fs_mix_load_chain_deep.md` §4） |
| C10 | 无按扩展名的优先级表 | **[静态推断-强]** | 有界搜索 + N6/N7 正控；**不是运行期全称证明** |
| C11 | `BATTLEMD*.INI` 通配枚举 + 按 `[Battles]` 名合并 + 回退条件 | **[本次实测]** | `0x52CBA0`–`0x52CD2C` 全部字节断言 + `0x46CE17` |
| C12 | 同目录多 `BATTLEMD*.INI` 的最终胜者 = 枚举顺序（通常 98 靠后） | **[静态推断-弱]** / **[待运行验证]** | 引擎不保证 `FindFirstFileA` 顺序 |
| C13 | **散装 `ra2md.csf` 端到端真的被游戏采用、UI 显示自定义简介** | **[待运行验证]** | 静态只到分支顺序；见 §4 最小实验 |
| C14 | `langmd.mix` 内确有 CSF（`" FSC"` 魔数）但 CRC 名 ≠ `RA2MD.CSF`；`language.mix` 加密 | **[本次实测]** | `EVIDENCE/override_order_stdout.txt` 尾部 + `EVIDENCE/recon6_stdout.txt` |
| C15 | 引擎 CRC32 = `zlib.crc32(name.upper())` | **[本次实测]** | `zlib.crc32("BATTLEMD.INI")=0x07E280DD`、`ECH01.MAP=0x8067D343` 与既有真实 MIX 产物实测 id 一致（**未用 mixlib**） |

---

## 4 · 最小真机实验设计（交下一张真机卡）

**为什么仍需要**：C2/C6 只定谳了**分支顺序与调用链**；"游戏真的用散装 CSF、并因此改变了 UI 文本"是端到端命题（C13），静态不足以定谳。以下实验**不依赖任何调试器/注入**，只用文件投放 + 启动观察，判据干净。

**前置（每个实验都做）**
- 用 `ra2bench` 的**隔离副本**（复制整个游戏目录到临时载体），记录基线文件哈希；实验后逐字节还原并实算自证。
- 串行执行，一次只改一个变量；不 `taskkill` 生产进程。
- 确认副本里**没有**散装 `*.csf`/`*.str`（本卡实测 `ra2bench` 确无）。

**实验 A —— 强判据：证明"散装优先"，无需观察 UI 文本**
1. 在副本游戏目录放一个**故意损坏**的散装 `ra2md.csf`：内容 = 4 字节 `XXXX`（非 CSF 魔数）。
2. 启动 `gamemd.exe`（正常启动参数，不加 `-CD`）。
3. **观察**：是否弹出 `Unable to initialize 'ra2.csf', please reinstall Red Alert.` 并退出。
4. **判据**：
   - 弹框/启动失败 ⇒ 引擎**优先读了散装** `ra2md.csf`（`0x473D2D` 命中、`0x734799` 魔数检查失败、`0x6BD85A` 分支），MIX 内完好的 CSF 被忽略 → **C13 前半定谳**。
   - 正常启动 ⇒ 散装未被优先读取（与 C2 矛盾，需回查 `mode`/CWD/`-CD` 路径），**立即上报**。
5. **对照 A0**：删除该文件后启动，应正常进入主菜单（证明基线可用）。

**实验 B —— C 线目标判据：自定义简介真的显示**
1. 从 MIX 提取**完整官方 CSF**（或复用任一已验证的完整 `ra2md.csf`），用 CSF 工具追加一个自定义标签 `DESC:MYCAMP`，值设为可辨识文本（如 `W29_LIVE_OK`）。
2. 把该**完整** CSF 作为散装 `ra2md.csf` 放入副本游戏目录。
3. 在游戏目录放散装 `BATTLEMD98.INI`，`[Battles]` 用官方 ID（如 `ALL1`）或新 ID，`Description=DESC:MYCAMP`。
4. 启动 → 打开战役选择界面，观察该战役条简介。
5. **判据**：显示 `W29_LIVE_OK`（而非 `MISSING:'…'`）⇒ 散装 CSF 覆盖生效、CSF 标签位可用、候选 1 落地成立。
6. **负控 B0**：把 `Description=` 改成纯文本 `W29_LIVE_OK`（无 `DESC:` 前缀）→ 应显示 `MISSING:'W29_LIVE_OK'`，证明显示差异来自 CSF 而非 INI 纯文本。

**实验 C —— 目录/前缀边界（可选，验证 Q2）**
1. 把同一个散装 `ra2md.csf` 放到**子目录**（如 `MIXFILES\`）而非游戏目录根，根目录不放。
2. **判据**：实验 A 的弹框**不出现**（正常启动）⇒ 证实"不递归子目录、名字原样相对 CWD"。

**还原**：删除实验投放文件，逐字节核对基线哈希并写入实验回执。

---

## 5 · 零命中纪律 / 负控 / 反例（脚本 `--selftest`）

- **零命中说明**：`"ra2md.csf"` 在**整个 4,825,360 B 文件**、三种编码（ASCII 精确、ASCII 大小写不敏感、UTF-16LE）下均 **0 命中**；但 `0x840D40="ra2md.str"` 与 `0x8457EC=".csf"` 各 **1 个 imm32 代码引用**（`0x6BD84F` / `0x734723`），且 `0x7346F7`–`0x73474B` 的 `strchr`+截断+`strcat` 序列 ⇒ **运行时拼接**。**零命中 ≠ 引擎不请求该文件**（N5 反例）。
- **`--selftest` 8/8 PASS**（`EVIDENCE/selftest_stdout.txt`，exit 0）：
  - **N1/N1b 负控**：故意把 `0x473D2D` 的期望字节改成"MIX-first"形态 → `check()` 必须报 MISMATCH（证明断言器不会假通过）。
  - **N2 反例**：反证"MIX 优先"假设（用 call site 地址与 `jne` 目标判定）。
  - **N3 反例**：`Find` 起点必须是 `0xABEFE0` 而非 `0xABEFF0`。
  - **N4 反例**：从 `0x6BD840` 线性反汇编会失同步（本会话实际踩到：`add al,ch` / `inc esp` 乱码），从正确边界 `0x6BD835` 同步 → 呼应"不要用不回同步的线性反汇编当事实"。
  - **N5 反例**：零命中 ≠ 不存在。
  - **N6/N7 正控**：`"BATTLEMD98.INI"` 应 0 命中、`"BATTLEMD*.INI"` 应 1 命中（证明扫描器有效）。
- **未用整段线性反汇编计数当事实**：所有反汇编块都从**已知可靠边界**（函数起点 / vtable 槽 / 已知 call 目标）开始，仅作证据展示；分支关系由**立即数/rel32 解码**判定。
- **未把 `ret` 当函数结束判据**，未把等距指针表当 vtable。

---

## 6 · 复算方法

```powershell
cd D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W29_override_order
python override_order.py            # 60/60 断言 + 结构判据 PASS，exit 0 → EVIDENCE/override_order_stdout.txt
python override_order.py --selftest # 8/8 PASS，exit 0 → EVIDENCE/selftest_stdout.txt
```
`EVIDENCE/` 另含探索期 stdout：`recon_stdout.txt`（PE/字符串/E8 原始扫描/首轮反汇编）、`recon2_stdout.txt`（C 字符串上下文/IAT/CSF 加载器）、`recon3_stdout.txt`（vtable/GetFileName/MIX 头/CWD/扩展名清单）、`recon4_stdout.txt`（E8 调用点/MIX 头 flags）、`recon6_stdout.txt`（MIX 全文魔数搜索）。`recon*.py` 为同目录的只读探索脚本，可重跑。

---

## 7 · 引用到的既有研究（只读复核，未改动）

- `docs/re/fs_mix_load_chain.md`（RE-C）：§1.2 `CCFileClass` 方法槽、§1.3 搜索顺序、§3 装载/覆盖、§4 INI 追加、§6 mixlib 交叉验证。
- `docs/re/fs_mix_load_chain_deep.md`（FSMIX）：§1.2 通道 A/B 字节证据、§1.5 优先级链、§2 BATTLEMD 通配/回退、§3 MIX 内 INI、§4 CD、§5.4 字符串表门禁。
- 本卡**独立复核**了上述全部关键地址在 `ra2bench/gamemd.exe` 上的字节；差异与澄清见 `DISAGREE.md`，未闭环见 `UNKNOWNS.md`。
