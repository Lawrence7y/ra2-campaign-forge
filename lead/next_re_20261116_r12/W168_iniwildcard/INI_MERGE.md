# W168 · `BATTLE*.INI` / `RULE*.INI` 通配合并机制与查找顺序 — INI_MERGE

> 卡号 W168｜R12 逆向卡｜工作域 `lead\next_re_20261116_r12\W168_iniwildcard\`｜2026-11-16
> 目标：`ra2youli\gamemd.exe` SHA-256 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`（已复核，见 `EVIDENCE\byte_verify.txt`）
> 全部结论带 `[已证]`/`[静态推断]`/`[未证]`；命令与原始输出见 `work\`、`EVIDENCE\`。

## 5 行摘要

1. `[已证]` 两个通配符各只有 **1 处**代码引用，都是 `push` 给 `FindFirstFileA`：`BATTLEMD*.INI`@`0x8261A8` → `0x52CBA0`（fn `0x52CB90`）；`RULEMD*.INI`@`0x82626C` → `0x52CD97`（fn `0x52CD70`）——字节全节扫描 + Ghidra `getReferencesTo` 双通道一致。
2. `[已证]` 枚举 API = `FindFirstFileA@IAT 0x7E1208` → `FindNextFileA@0x7E120C` → `FindClose@0x7E1300`（pefile 解析导入表确认），属性掩码 `0x116` 跳过 目录/隐藏/系统/临时 条目。
3. `[已证]` **BATTLE 合并顺序 = FindNextFileA 返回序（文件系统序）**，枚举循环内**无 sort/比较插入**；`BATTLEMD.INI` 只用一个 bool 保证"必被读一次"，不插队。
4. `[已证]` 键冲突 = **按战役名（`[Battles]` 的值）查全局表、复用同名对象、逐键覆盖**：`FUN_0046CE10` 用 `stricmp(obj+0x24, value)` 复用对象，`FUN_0046CCD0` 以当前字段值为默认值读 `CD`/`FinalMovie`/`Scenario`/`Description` ⇒ **后处理的文件只在它定义了该键时才覆盖，未定义的键保留先值**；"后" = 枚举序，**不保证字典序** ⇒ 任何"98 必覆盖官方/官方必覆盖 98"都无静态依据。
5. `[已证]` 枚举只走 Win32 文件系统 ⇒ **不看 MIX 内条目**；DLC 应放散装 `BATTLEMD<后缀>.INI`、只写新 id/新段、不重定义官方键；`ra2youli` 现有 `.bak` 不匹配 `BATTLEMD*.INI`（结尾是 `.bak`）不参与；`BATTLEMD98.INI` 只加 id 15，与官方 1–14 无键冲突。

---

## Q1 · 谁引用这两个通配符字符串

### 双通道 xref（穷举性结论，通道 B 不依赖 atlas）

- **通道 A — Ghidra `getReferencesTo`**（脚本 `work/W168Main.java`，输出 `EVIDENCE/w168main.clean.txt:47-68`）：
- **通道 B — 全 `.text` 逐字节扫 4 字节小端字面量 + capstone `skipdata=True` 从已知入口验证边界**（`work/byte_verify.py` / `work/boundary_check.py`，输出 `EVIDENCE/byte_verify.txt`、`EVIDENCE/boundary_check.txt`）。

| 字符串 | VA | 字节复核 | Ghidra xref | 字节通道命中（=立即数起点） | 指令（边界已验） | 所属函数 entry |
|---|---|---|---|---|---|---|
| `BATTLEMD*.INI` | `0x008261A8` | `42 41 54 54 4C 45 4D 44 2A 2E 49 4E 49 00` = `BATTLEMD*.INI\0` | 1 处 `ref@0x52cba0` type=DATA | 1 处 `0x52cba1`（`a8 61 82 00`） | `0x52CBA0 push 0x8261a8` | `0x0052CB90`（473 B） |
| `RULEMD*.INI` | `0x0082626C` | `52 55 4C 45 4D 44 2A 2E 49 4E 49 00` = `RULEMD*.INI\0` | 1 处 `ref@0x52cd97` type=DATA | 1 处 `0x52cd98`（`6c 62 82 00`） | `0x52CD97 push 0x82626c` | `0x0052CD70`（1728 B） |

复跑命令：
```bash
# 通道 A
analyzeHeadless.bat ...\_ghidra\W168 gamemd_auto -process gamemd.exe -noanalysis \
  -scriptPath ...\W168_iniwildcard\work -postScript W168Main.java *> EVIDENCE\w168main.log
# 通道 B
python work\byte_verify.py        # §4 full .text scan + §5 capstone skipdata sweep
python work\boundary_check.py     # §A boundary from function entry 0x52CB90/0x52CD70
```
- `[已证]` 边界校验（从函数入口线性反汇编，capstone `skipdata=True`）逐条命中：
  `0x52CBA0 push 0x8261a8 bytes=68a8618200 size=5`（命中在指令内偏移 +1）；
  `0x52CD97 push 0x82626c bytes=686c628200 size=5`（+1）。
  全节线性 sweep 会把这些立即数报成 "not instruction start" —— 这是**预期**（立即数不是指令首字节），不能据以否证；正确做法是从函数入口反汇编，见 `R12_FACTS §3/§6.2`。
- `[已证]` 用途判定：`push <字符串>` 紧接 `call [IAT FindFirstFileA]`，两处都是 **FindFirstFileA 的搜索模板**（不是 INI 段名/错误消息）。依据反汇编 `0x52CBA0 push → 0x52CBA9 call [0x7E1208]`、`0x52CD97 push → 0x52CDAC call [0x7E1208]`（`EVIDENCE/disasm_battle.txt`、`w168main.clean.txt:71-72`）。
- `[已证]` 区分：base 字符串引用是**2 处**（`BATTLEMD.INI`@`0x52CC4E`/`0x52CCCD`；`RULESMD.INI`@`0x52CE23`/`0x52CF38`），分别用于"枚举中遇到 base 则记标志"与"枚举没遇到 base 则显式加载 base"。这是 fallback，不是通配符。

> 注：派发提示词说"两者在 `.data` 里各出现两次"。字节实测（`byte_verify.txt §2`）：每个通配符**字面串各 1 次**（`0x4261A8` / `0x42626C`）；只有子串 `BATTLEMD` 出现 2 次（`BATTLEMD.INI`@`0x426198` 与 `BATTLEMD*.INI`@`0x4261A8`），`RULEMD` 子串 1 次。按字节实测为准，见 `DISAGREE.md`。

---

## Q2 · 枚举与合并的代码路径

### 2.1 导入表确认（不是靠猜）

`pefile` 解析 `pe.DIRECTORY_ENTRY_IMPORT`（`work/byte_verify.py §6`，`EVIDENCE/byte_verify.txt`）：

| IAT VA | 导入 | 本卡路径上的 call 站点 |
|---|---|---|
| `0x007E1208` | `KERNEL32!FindFirstFileA` | `0x52CBA9`（BATTLE）、`0x52CDAC`（RULE） |
| `0x007E120C` | `KERNEL32!FindNextFileA` | `0x52CCAB`（BATTLE）、`0x52CF19`（RULE） |
| `0x007E1300` | `KERNEL32!FindClose` | `0x52CCBA`（BATTLE）、`0x52CF28`（RULE） |
| `0x007E12E4` | `KERNEL32!GetFileAttributesA` | **仅 1 处** `0x7D53C6`，不在 BATTLE/RULE 路径上（本路径用 `WIN32_FIND_DATAA.dwFileAttributes`，不调 GetFileAttributes） |

- `[已证]` 未导入 `FindFirstFileW` / `FindNextFileW` / `GetFileAttributesW` —— 全用 ANSI 版。
- `[已证]` 属性过滤 `test dword [esp+0x84],0x116 ; jne skip`（`0x52CBBF/0x52CBCA`）⇒ 掩码 `0x116 = 0x2|0x4|0x10|0x100` = HIDDEN|SYSTEM|DIRECTORY|TEMPORARY；命中即跳过该条目。

### 2.2 枚举逐跳地址（`fn 0x52CB90` BATTLE；`fn 0x52CD70` RULE 同构）

以 BATTLE 为例（`EVIDENCE/disasm_battle.txt`，全指令边界有效）：

```
0052CB90  sub esp,0x1B4                     ; WIN32_FIND_DATAA 在栈
0052CBA0  push 0x8261A8                     ; "BATTLEMD*.INI"
0052CBA9  call dword ptr [0x7E1208]         ; FindFirstFileA
0052CBB1  cmp esi,-1 / je 0x52CCCD          ; 无匹配 → 显式加载 base
0052CBBF  test dword [esp+0x84],0x116       ; 属性过滤（隐藏/系统/目录/临时跳过）
0052CBCA  jne 0x52CCA2
0052CBF6  call 0x4739F0                     ; 设置 INI 文件名（ecx=结构, push=文件名）
0052CBFB  push 0x58 / call 0x7C8E17         ; operator new(0x58) —— 每个文件一个 INI 对象
0052CC49  call 0x4741F0                     ; 把该文件读进 INI 对象（ecx=对象）
0052CC54  push 0x826198 / push ebp / call 0x7C8D20  ; stricmp(文件名,"BATTLEMD.INI")
0052CC60  mov byte [esp+0x13],1             ; 若相等：bVar2=true（只记 bool，不插队）
0052CC67  call 0x46CE10                     ; ★ 合并：把该 INI 的 [Battles] 并入全局战役表（ecx=INI 对象）
0052CC76  call [edx] (push 1)               ; 析构该 INI 对象
0052CCAB  call dword ptr [0x7E120C]         ; FindNextFileA → 回到 0x52CBBF
0052CCBA  call dword ptr [0x7E1300]         ; FindClose
0052CCC5  cmp al,bl / jne 0x52CD5F          ; bVar2==true ⇒ return
0052CCCD  push 0x826198 / ... / call 0x46CE10 ; 否则显式加载 BATTLEMD.INI 并合并（0x52CD2C）
```
RULE 同构（`FUN_0052CD70`）：`0x52CDAC` FindFirstFileA、`0x52CF19` FindNextFileA、`0x52CF28` FindClose；base `RULESMD.INI` 引用在 `0x52CE23`/`0x52CF38`。

### 2.3 合并顺序 = 文件系统返回序，`[已证]`

- `[已证]` **无排序**：`fn 0x52CB90` 全部 139 条指令（`EVIDENCE/boundary_check.txt`）与 RULE 的 443 条里，循环体（0x52CBBF–0x52CCAB）**没有任何 sort/qsort/lstrcmp 比较插入**；合并调用 `0x46CE10` 在循环里按到达顺序逐个执行。（`EVIDENCE/disasm_battle.txt`、`w168main.clean.txt:141-344`）
- `[已证]` BATTLE 路径**没有"base 插到索引 0"**：`0x52CC54 stricmp` 结果只写 `bVar2` bool（`0x52CC60`），不是插入位置；base 若被枚举到就在它本来的位置合并，若没被枚举到则在枚举结束后 fallback 合并（最后）。
- `[静态推断]` 对比 RULE 路径：`FUN_0052CD70` 里 stricmp(base) 命中时会 `FUN_007ca090(local_304+1,local_304,...)` 右移 + `*local_304=puVar3` **把 RULESMD.INI 插到数组 0**（`w168main.clean.txt:472-476,550-554`），且 >1 个规则文件时弹 `DialogBoxParamA(...,0x93,...,&LAB_0052d430,...)` 让用户**选一个**（`:590,596,606`），最终只用 `DAT_00887048 = local_304[iVar4]` —— 所以 **RULE 是"选择+base 优先"，BATTLE 是"全部并入+到达序"**，两者语义不同，不可混为一谈。（这里只把 RULE 作为对照，DLC 结论针对 BATTLE。）
- `[已证]` 结论：同一目录里 `BATTLEMD.INI` 与 `BATTLEMD98.INI` 谁先被读，**取决于 `FindNextFileA` 的返回顺序**（NTFS 通常近似字典序但不是引擎保证）。台账 §910-3 同结论，本卡独立复核一致。

### 2.4 键冲突语义 = 按战役名复用对象 + 逐键"后写覆盖"，`[已证]`

合并函数 `FUN_0046CE10`（`EVIDENCE/w168run2.clean.txt:43-184`）：
```
0046CE10  iVar2 = FUN_00526960("[Battles]")        ; 键数
          for i in 0..iVar2-1:
            uVar3 = FUN_00526cc0("[Battles]",i)     ; 取第 i 个键（战役 id，如 "15"）
            FUN_00528a10("[Battles]",uVar3,..,local_20,0x20) ; 取该键的值（战役名，如 "RA2F1"）
            for j in 0..DAT_00A83D08-1:
              if stricmp( *(DAT_00A83CFC + j*4) + 0x24, local_20 ) == 0:  ; ★ 按"战役名"查全局表
                 piVar5 = *(DAT_00A83CFC + j*4); goto LAB_0046CF60       ; 复用已存在对象
            piVar5 = operator_new(0x3a0); ... append to DAT_00A83CFC ...  ; 否则新建
          LAB_0046CF60:
            call [ *piVar5 + 100 ](param_1=INI对象)  ; ★ 把该 INI 的该段写进战役对象
```
`call [*piVar5+100]` 的目标 = vtable `0x7E4A28+0x64` = **`FUN_0046CCD0`**（`vtable` 读取命令见下；`EVIDENCE/w168run3.clean.txt:43-185`）：
```
0046CCD0  cVar2 = FUN_00410a60(param_2)     ; 取当前段名（战役名）；取不到则返回
          iVar5 = param_1 + 0x24            ; 战役对象的名字段（与 0x46CF00 比对一致）
          uVar3 = FUN_005276d0(iVar5,"CD",     *(param_1+0x98)); *(param_1+0x98)=uVar3
          uVar3 = FUN_004757d0(iVar5,"FinalMovie",*(param_1+0x29c)); *(param_1+0x29c)=uVar3
          FUN_00528a10(iVar5,"Scenario",param_1+0x9c,param_1+0x9c,0x200)   ; 原地读进字段缓冲
          cVar2 = FUN_005295f0(iVar5,"DebugOnly",0)
          if (!cVar2) FUN_00529160(iVar5,"Description",param_1+0x2a0,0x80)
```
- `[已证]` **以当前字段值为"默认值"读入**（`*(param_1+0x98)` / `*(param_1+0x29c)` 作第 3 参数；`Scenario`/`Description` 原地写字段缓冲）⇒ 某键在本文件里不存在时，保留先前文件留下的值；存在时覆盖。这就是"**后到者逐键覆盖**"的字节依据。
- `[已证]` 复用对象是 `goto LAB_0046CF60`（`0x46CFxx`，`EVIDENCE/w168run2.clean.txt:100-170`），不是新建 ⇒ 同名战役的多份数据落在同一个对象上。
- `[静态推断]` "后"= 枚举到达序（`FUN_0046CE10` 在 `0x52CC67` 的循环内逐文件调用）。因此**没有引擎保证的"官方赢/98 赢"**；要靠不冲突的 id/段名规避。
- 复跑命令：`W168Run2.java`（dump `0x46CE10`）、`W168Run3.java`（dump `0x46CCD0`）；vtable 读取：
  ```bash
  python -c "import pefile,struct; d=open(r'...\gamemd.exe','rb').read(); p=pefile.PE(r'...\gamemd.exe',fast_load=False); o=p.get_offset_from_rva(0x7E4A28+0x64-0x400000); print(hex(struct.unpack('<I',d[o:o+4])[0]))"  # -> 0x46ccd0
  ```

### 2.5 栈参数纪律（R12_FACTS §10.3）

本卡不主张"某值是栈参数"。唯一涉及 `[esp+N]` 的判断是 `test dword [esp+0x84],0x116`（`0x52CBBF`）——它是 **WIN32_FIND_DATAA.dwFileAttributes 的栈内字段**，不是函数入参：
- `fn 0x52CB90` 入口 `sub esp,0x1B4`，其后 `push ebx/esi/edi` 与 FindFirstFileA 的 2 个 push；FindFirstFileA 出参 `&local_140` 由 `lea eax,[esp+0x7c]; push eax` 给出，即 finddata 起点约 `esp+0x7c`（调用后相对 esp 漂移）;属性字段在结构 +0 ⇒ `[esp+0x84]` 落在该结构内。
- 该 fn 内出现的 `[esp+N]` **取值集合**（`EVIDENCE/disasm_battle.txt` 全量正则 `[esp + 0x?]`）：`{0x10, 0x13, 0x14, 0x17, 0x18, 0x1C, 0x6C, 0x70, 0x78, 0x7C, 0x84, 0xB0, 0x1B4}`，**最大值 `0x1B4`** = 栈帧大小（`sub esp,0x1B4`）；`0x84` 落在 `[0x10,0x1B4]` 内 ⇒ 是帧内局部变量，不是传入参数（`ret` 无立即数，函数签名 void(void)，无栈入参）。⇒ `[esp+0x84]` 是 WIN32_FIND_DATAA 结构内的 `dwFileAttributes` 字段，符合 §10.3（集合与上界已给）。

---

## Q3 · 与 MIX 的关系（DLC 第 3 行"查找与覆盖顺序"）

- `[已证]` **通配枚举只枚举散装目录**：`FindFirstFileA("BATTLEMD*.INI")` / `FindFirstFileA("RULEMD*.INI")` 是 Win32 文件系统 API，模板是**相对文件名**（无路径前缀）⇒ 扫描进程当前工作目录（CWD）的文件系统条目，**不可能返回 MIX 档案内的条目**（MIX 条目要经过 Westwood 自己的 MIX 索引解码，不是 Win32 文件）。`FindNextFileA` 同理。依据 `EVIDENCE/disasm_battle.txt` + 导入表（`EVIDENCE/byte_verify.txt`）。
- `[已证]` 属性掩码 `0x116` 跳过 HIDDEN/SYSTEM/DIRECTORY/TEMPORARY ⇒ 隐藏的覆盖件不会被枚举（DLC 文件不要设 hidden）。
- `[已证]` 按文件名打开走的是 `FUN_004739F0` → `FUN_0047AE10`（`EVIDENCE/w168run2.clean.txt:186-361`）：先 `FUN_00431E80(filename)` 直接设名、`FUN_00431F10(0)` 测存在；不存在时遍历 `DAT_0089E410` 搜索路径链表（把 path + filename 拼接后重试）。这是**按显式文件名**的查找层（与通配枚举是两条不同路径）。
- `[已证]` exists 原语 `FUN_0065CBF0`（`FUN_00431F10` 调用，`EVIDENCE/w168run4.clean.txt:43-140`）：先 `vtable[+0x18]()` 问文件对象自身 → 返回非 0 即"存在"；否则回落到对真实文件名 `CreateFileA(GENERIC_READ,share=1,OPEN_EXISTING,...)`。对象 vtable `0x7E16B0+0x18 = 0x473CD0`（`0x473CD0` 检查 `[ecx+0x58]` 非空则直接返回 1，否则 `jmp 0x431F30`）。
  - `[未证]` `vtable[+0x18]` 是否就是 "MIX/档案层存在性检查"——其身份未钉死（`0x473CD0` 只查对象 `+0x58` 字段），**不据此下"MIX 先于散装"或反之的结论**；通用文件层的散装/MIX 优先级本卡不裁决。
  - **本卡问题不受影响**：通配枚举（`FindFirstFileA`）这条路径**先于且独立于**上述按名查找层，它只枚举散装文件系统，不查 MIX。
  - **通配枚举这条路径不查 MIX**，散装 `BATTLEMD.INI` 被删后不会有 MIX 副本被这条路径发现 ⇒ 机制层印证 `docs/DESIGN.md:211` 勘误（删散装 `BATTLEMD.INI` 不回退到 MIX；文件层 mixlib 扫描已由 Lead 做，本卡不重复）。
  - `[未证]` 引擎是否另有一条完全独立的"从 MIX 内读 BATTLE*.INI"路径（本卡未发现；两个通配符字面串各只有 1 处代码引用且都在散装枚举函数里，是强反证，但不是全路径穷举）。
- `[已证]` BATTLE 与 RULE 的相对顺序：同在 init 函数 `FUN_0052BA60` 中，`0x52C605 call 0x52cb90` 前打 `Init Campaigns\n`（`0x825F10`），`0x52C95C call 0x52cd70` 前打 `Init Rules\n`（`0x825D38`）⇒ **先枚举 BATTLE 战役表，后初始化 RULE 规则**。（`EVIDENCE/disasm_init_order.txt` + 字符串读取命令见 `work/`。）

---

## Q4 · 判决与对 DLC 的可操作结论

### 一句话判决（DLC 第 3 行的机制层答案）

`[已证]` **DLC 新增战役应放一个散装文件 `BATTLEMD<后缀>.INI`（如 `BATTLEMD98.INI`）到游戏 CWD，里面只写新增的 `[Battles] <新id>=<新关卡名>` 与对应的 `[<新关卡名>]` 段；它与官方 `BATTLEMD.INI` 会被通配枚举"全部并入"，按 `FindNextFileA` 返回序逐键处理，同名战役名复用同一对象、后处理者覆盖它定义的键——只要新 id/段名不与官方 1–14 / ALL*/SOV* 重名就不会冲突，谁先谁后都正确。**

### `ra2youli\` 现有三个文件的实际行为

| 文件 | 大小 / SHA-256 前缀 | 是否匹配 `BATTLEMD*.INI` | 实际发生什么 |
|---|---|---|---|
| `BATTLEMD.INI`（官方） | 2733 B / `7e40691a…0791` | 是（`*` 匹配空串；也是 base） | 被枚举并合并：`[Battles] 1..14` + `[ALL1]/[SOV1]/[ALL02..SOV07]` 全部 14 个战役对象入表。 |
| `BATTLEMD98.INI`（DLC） | 453 B / `4e341756…c74` | 是（`*` 匹配 `98`） | 被枚举并合并：只加 `[Battles] 15=RA2F1` + `[RA2F1]` 段（`Scenario=ECH01.MAP`）。**与官方 1–14 无键冲突**（新 id 15、新段 RA2F1）。顺序上无论它先于/后于官方，15 号战役都成立。 |
| `BATTLEMD.INI.ra2forge.bak`（旧版备份） | 241 B / `9f804531…412` | **否** —— 模式要求以 `.INI` 结尾，该名以 `.bak` 结尾 | **不被引擎枚举、不参与合并**；它里面的 `1=ALL1/2=SOV1` 覆盖和 `[SOV1] Scenario=ECH01.MAP` 是死数据（对通配路径无影响）。 |

文件哈希复跑：`Get-FileHash -Algorithm SHA256 -LiteralPath <file>`（`EVIDENCE/` 中另有内容 dump）。

### 冲突时谁赢——字节级依据（回应任务 Q4 的 ⚠️）

- **不做"98 必覆盖官方"或"官方必覆盖 98"的承诺** —— 顺序由 `FindNextFileA` 决定，引擎无排序（§2.3）。若两者定义同一战役名，`FUN_0046CE10` 的 `stricmp(obj+0x24,value)==0 ⇒ goto LAB` 复用同一对象，后处理者的 `FUN_0046CCD0` 以自己文件里的键覆盖字段（`CD/FinalMovie/Scenario/Description` 读入即写回字段）；先处理者未定义、后处理者定义的键则由后处理者写入。
- 若一定要一个"谁赢"的函数级判据：**"最后被枚举到且定义了该键的文件赢"**（`0x46CF60` call `[vptr+100]` = `0x46CCD0` 逐键写回），但"最后"是文件系统序，**不可静态固定**。当前 `ra2youli` 三文件之间无同名战役名冲突，故该不定性不影响现有包。

### 操作清单（给 DLC 工具链）

1. 用 `BATTLEMD98.INI`（或任意 `BATTLEMD*.INI` 后缀）作为新增载体，**散装放在游戏目录**；不要隐藏它（掩码 `0x116` 过滤 HIDDEN）。
2. 只写**新**战役 id（当前官方占 1–14，包已用 15）与**新**关卡段；**不要**在覆盖件里重定义 `[Battles] 1/2` 或 `[ALL1]/[SOV1]` 等官方键。
3. 不要依赖 id 数字排序或文件名排序来决定覆盖——引擎不排序。
4. 备份文件用 `.bak` 等不以 `.INI` 结尾的扩展名，天然不会被通配枚举（现有 `.ra2forge.bak` 已是此类）。
5. 删除/替换散装 `BATTLEMD.INI` 不会触发 MIX 回退（机制层本卡已证；文件层见 `docs/DESIGN.md:211`）。

---

## LEAD_AUDIT（核心可抽验数字，地址 + 复跑命令）

1. **字符串地址与唯一引用**：`BATTLEMD*.INI`@`0x8261A8` 唯一 xref `0x52CBA0`（push 0x8261a8）；`RULEMD*.INI`@`0x82626C` 唯一 xref `0x52CD97`。
   复跑：`python work\byte_verify.py`（§1/§2/§4，1 hit each）；`analyzeHeadless ... -postScript W168Main.java`（XREFSTO 段，1 ref each）；`python work\boundary_check.py`（§A，指令边界 `68 a8 61 82 00` / `68 6c 62 82 00`）。
2. **API call 站点**：`FindFirstFileA` IAT `0x7E1208`，BATTLE `0x52CBA9` / RULE `0x52CDAC`；`FindNextFileA` IAT `0x7E120C`，`0x52CCAB` / `0x52CF19`；`FindClose` IAT `0x7E1300`，`0x52CCBA` / `0x52CF28`。
   复跑：`python work\byte_verify.py`（§6 IAT + §7 `FF 15` 扫描，全部 boundary=True）；`W168Main.java` XREFSTO IAT 段。
3. **顺序/冲突判定依据**：合并函数 `0x46CE10` 中 `stricmp(obj+0x24, value)` 复用对象 + `call [vptr+100]`；vtable `0x7E4A28+0x64 = 0x46CCD0` 逐键以当前值为默认值写回；枚举循环 BATTLE 无 sort；init 顺序 `0x52C605`(Init Campaigns) < `0x52C95C`(Init Rules)。
   复跑：`W168Run2.java`（FN 0x46ce10）、`W168Run3.java`（FN 0x46ccd0）、`python work\disasm_battle.py`（139 指令无 sort）、`python work\disasm_init_order.py` + 字符串读取（Init Campaigns/Init Rules）。

---

## 未证 / 排除 / 下一步（`UNKNOWNS.md` 摘要）

- `[未证]` 引擎是否另有从 MIX 内读 BATTLE*.INI 的独立路径（无字面串 xref 支持，但不做全路径穷举）。
- `[未证]` 通用文件层"散装 vs MIX 同名条目"的优先级（本卡只证通配枚举不查 MIX；`FUN_0065CBF0` 等 MIX 原语未展开）。
- `[已排除]` 枚举循环内排序（BATTLE 全部 139 指令审查）；BATTLE base 插队（只有 bool 标志）；隐藏覆盖件被读（掩码 0x116）；`.bak` 被读（不匹配 `*.INI`）。

交付清单：`INI_MERGE.md`（本文件）、`PROGRESS.md`、`UNKNOWNS.md`、`DISAGREE.md`、`work\*.py|*.java`、`EVIDENCE\*.txt|*.log`。未改任何游戏文件、未改主台账、未 git commit。
