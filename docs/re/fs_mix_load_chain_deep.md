# 任务 FSMIX：文件系统与 MIX 加载链专章深潜

> **交付范围**：本文件为本任务**唯一新增文档**；全部脚本、反汇编 dump 与字节断言在 ~BT~out/re_work/fs_mix_deep/~BT~。
> 既有资产 ~BT~out/re_work/fs_mix/~BT~（RE-C 冲刺）与 ~BT~docs/re/fs_mix_load_chain.md~BT~ **只读复用**，未改动。

- **目标二进制**：~BT~ra2youli/gamemd.exe~BT~（MD5 4f37486e5b0dbe2ae5f45aeee0f98367，官方 1.001，ImageBase 0x400000）
- **地址映射**：.text / .rdata / .data 三段均满足 **FileOffset = VA − 0x400000**（用 ~BT~tools/audit_bytes.py --selftest~BT~ 口径核验）；正文每条证据给出 VA，可按此式换算 FileOffset
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
- **证据等级**：~BT~[实证]~BT~ = VA + 原始机器码 + Capstone 反汇编（可用 ~BT~python tools/audit_bytes.py out/re_work/fs_mix_deep/claims.txt~BT~ 逐条复算，本任务 **190/190 OK**）；~BT~[推演]~BT~ = 由已实证代码结构推定；~BT~[待实测]~BT~ = 需运行/动态调试定论
- **只读纪律**：全程静态分析，未写盘篡改、未注入、未启动游戏；未改动 ra2render 目录、顶层台账、其它既有 docs/re 文档、ra2youli 安装目录
- **门禁实跑**（见 §9）：~BT~tools/verify_anchors.py~BT~ → **323/323 PASS**（.text raw SHA-256 与基线一致）；~BT~tools/audit_bytes.py out/re_work/fs_mix_deep/claims.txt~BT~ → **190/190 OK**

---

## 0. 必答项结论速览

| # | 问题 | 结论（一句话） | 等级 | 关键代码点 |
|---|---|---|---|---|
| 1 | 加载优先级 / 搜索顺序 | **散装文件（相对 CWD=游戏目录的 CreateFileA）优先于一切 MIX**；MIX 内部按**先装载者优先**（FIFO 链表）。序列：langmd.mix → language.mix → expandmd99 → … → expandmd00 → ra2md.mix → ra2.mix → cachemd.mix → cache.mix → localmd.mix → local.mix → ecache*.mix → elocal*.mix →（次级）conqmd … movies* | [实证]（分支/序列表）；端到端 [待实测] | 0x473D2D / 0x473D68、0x5301A0、0x530000、0x530460、0x6BD7EF、0x5B3DE2 / 0x5B44A1 |
| 1b | expandmd01/98/99 序号语义 | 由 sprintf("EXPANDMD%02d.MIX") **两位补零**生成，循环 **99→0 递减**：序号大者**先装载 ⇒ 优先级高**。故 expandmd99 > expandmd98 > … > expandmd01 > expandmd00 | [实证] | 0x5301BA（mov edi,0x63）、0x5301C4、0x530289 |
| 2 | BATTLEMD*.INI 通配与回退 | 通配走 **KERNEL32!FindFirstFileA（纯文件系统，相对 CWD，不递归）**；句柄无效时才用 CCFileClass("BATTLEMD.INI") 回退（该路 mix 感知）；多文件按 [Battles] 条目名 _stricmp 归并进全局表 0xA83CF8，同 ID **后装载者覆写** | [实证]（路径/归并）；枚举顺序决定胜者 [待实测] | 0x52CBA0 / 0x52CBA9 / 0x52CBB8 / 0x52CCC7 / 0x52CCCD / 0x46CE10 |
| 3 | **MIX 内 INI 是否被读** | **BATTLEMD98.INI 放进 MIX 永不加载 [实证]**：全 exe 只有 "BATTLEMD*.INI"（通配，FS-only）与 "BATTLEMD.INI"（回退，显式名）两个字面量，**不存在 "BATTLEMD98.INI"**；通配是 Win32 API，结构上看不到 MIX 条目。**但**官方名 BATTLEMD.INI 若只在 MIX 内、且散装 BATTLEMD*.INI 一个都没有，则**会被读** | [实证] | 0x52CBA9、0x52CCCD–0x52CD2C；对照 0x52C6E4 / 0x52C8BE（显式名走 CCFileClass） |
| 4 | [CD] / CDPath / InstallPath 是否进入搜索链 | **不进入散装/MIX 查找链**。字符串 [CD] / CDPath / InstallPath 全 exe **0 命中**；注册表只有 SOFTWARE\Westwood\Yuri's Revenge（WOL/序列号用，非安装路径）。CD 子系统进入的是**门禁**（每个 MIX 装载前的 CD_Check + 文件缺失时的 CCFileClass::CDCheck 虚函数）与**次级装载器的二次通配**（CD 路径 + MAPS*/MOVIES*/MOVMD* 通配），二者都不改变散装/MIX 优先级 | [实证]（−CD 路径的运行期实读为 [推演]） | 0x52C3A8、0x52F7A0–0x52F7B6、0x4790E0、0x5B3C58、0x473AB0、0x47AF70 / 0x47B020 |
| 5 | 文件打开失败的字符串与分支 | "Failed to initialize bootstrap mixfiles!" 分支**只由 operator new 失败 / 空指针检查触发**（"预载门槛" 0x5B43E0 是恒真桩）；且该分支的打印目标是**单条 ret 的调试桩** 0x4068E0 / 0x4A4AC0 ⇒ **1.001 不输出这些消息**。用户可见失败只有：CD 初始化失败（返回 1）、LANGUAGE.MIX 后字符串表自检失败 → MessageBoxA、CD 插入对话框取消 | [实证] | 0x52BB69–0x52BB87、0x4068E0、0x4A4AC0、0x5B43E0、0x52C3ED、0x6BD85C–0x6BD869 |
| 6 | 对 ra2forge 的可操作结论 | **散装 BATTLEMD98.INI（游戏目录，exe 同级）是唯一可靠通道**；把 INI 打进 MIX 只在"官方名 BATTLEMD.INI + 目标机无任何散装 BATTLEMD*.INI"时成立；expandmd98.mix 仍适合放**非 INI 资源**（地图/资产），但**不可覆盖 langmd.mix / language.mix 的同名条目** | [实证]（机制）+ [推演]（装机形态影响） | §6 对照表 |

---

## 1. 必答项 1：加载通道与优先级

### 1.1 三条独立通道（先分清通道，再谈顺序）

| 通道 | 机制 | 可见范围 | 优先级地位 |
|---|---|---|---|
| A. 散装文件 | CreateFileA(原始名)，相对 **CWD**（= exe 所在目录，启动时 SetCurrentDirectoryA 设定） | 仅游戏目录（若名字里带则含 MIXFILES 子目录） | **最高**（同一 CCFileClass 请求内先于 MIX） |
| B. MIX 条目 | MixFileClass::Find 遍历全局优先级链表（CRC32 二分） | 全部已装载 MIX | 低于 A，按装载先后 FIFO |
| C. CD 路径 | 仅 0x47AF70 的**二次 FindFirstFileA** 尝试 CD 路径 + 通配 | 仅 CD 盘（−CD 路径参数 或交互式 CD 初始化登记） | 仅在**次级装载器的通配**里、且在 A 之后 |

### 1.2 通道 A 优先于 B：字节证据

CCFileClass::Get_File（vtable 0x7E16B0 slot +0x1C）= **0x473D10**（FileOffset 0x73D10）：

    0x473D1D  F6 44 24 20 02          test byte [esp+0x20],2      ; mode & 2（只读写盘）
    0x473D22  0F 85 11 01 00 00       jne  0x473E39              ; → 直接走磁盘
    0x473D2D  E8 DE E1 FB FF          call 0x431F10              ; ★先试磁盘（散装）
    0x473D32  84 C0                   test al,al
    0x473D34  0F 85 FF 00 00 00       jne  0x473E39              ; 成功 → 磁盘读
    0x473D68  E8 C3 06 14 00          call 0x5B4430              ; ★失败才回落 MixFileClass::Find
    0x473D6F  0F 84 AF 00 00 00       je   0x473E24              ; MIX 也未命中 → 失败返回

磁盘支路 **0x431F10**（FileOffset 0x31F10）：

    0x431F10  8A 41 29                mov  al,[ecx+0x29]         ; 已开/就绪标志
    0x431F1C  6A 00                   push 0
    0x431F1E  E8 CD AC 22 00          call 0x65CBF0              ; RawFileClass::Open(0)

RawFileClass::Open = **0x65CBF0**（FileOffset 0x25CBF0）：**名字原样使用，无任何路径/盘符前缀**：

    0x65CBF4  8B 46 18                mov  eax,[esi+0x18]        ; FileName
    0x65CC43  8B 56 18                mov  edx,[esi+0x18]
    0x65CC4D  6A 03                   push 3                     ; OPEN_EXISTING
    0x65CC59  FF 15 BC 11 7E 00       call [0x7E11BC]            ; = KERNEL32!CreateFileA

IAT 槽实证（out/re_work/fs_mix_deep/s28_bytes.py 解析导入表）：
[0x7E11BC]=0x0040F9D0 指向 "CreateFileA"、[0x7E1208]=0x0040F844 指向 "FindFirstFileA"、[0x7E120C] 指向 "FindNextFileA"、[0x7E1300] 指向 "FindClose"、[0x7E1148] 指向 "SetCurrentDirectoryA"、[0x7E11A8] 指向 "GetModuleFileNameA"。

**CWD 的确立**：启动模块 0x6BBFDB call [0x7E11A8]（GetModuleFileNameA）→ 取目录 → 0x6BC07C call [0x7E1148]（SetCurrentDirectoryA）。
⇒ **"散装文件" = exe 所在目录下的文件名**；这也是 FindFirstFileA("BATTLEMD*.INI") 的搜索目录。

> 结论 [实证]（分支顺序 + 名字原样 + CWD 来源）。"先试磁盘一定赢" 的**端到端**结论为 [待实测]：需在 0x473D2D 与 0x473D68 处下断，构造同名散装/MIX 条目对照观察。

### 1.3 通道 B 的装载顺序（主序列 0x5301A0 / 通配 0x530000 / 次级 0x530460）

入口：Init = **0x52BA60**（由 0x48CCC0+0xCF 调用），关键装载调用点：

| # | 调用点 | 目标 | 内容（按地址序 / 字符串引用序实证） |
|---|---|---|---|
| 0 | 0x6BD7EF / 0x6BD81F | 0x5B3C20 | **LANGMD.MIX**、**LANGUAGE.MIX**（Startup 阶段，**早于 Init**，见 §1.6） |
| 1 | 0x52BB64 → 0x5301A0 | 主 MIX | EXPANDMD99…00.MIX（99→0 递减）、RA2MD.MIX、RA2.MIX、CACHEMD.MIX、CACHE.MIX、LOCALMD.MIX、LOCAL.MIX |
| 2 | 0x52C307 → 0x530000 | 通配 MIX | ECACHE*.MIX（先）、ELOCAL*.MIX |
| 3 | （Init 内 CD 块） | 0x47AB10 等 | 交互式 CD 初始化 / −CD 分支（不装载 MIX，见 §4） |
| 4 | 0x52C59C → 0x530460 | 次级 MIX | CONQMD.MIX、GENERMD.MIX、GENERIC.MIX、ISOGENMD.MIX、ISOGEN.MIX、CONQUER.MIX、CAMEOMD.MIX、CAMEO.MIX、MAPSMD*.MIX、MAPS*.MIX、MAPSMD%02d.MIX、MAPS%02d.MIX、MULTIMD.MIX、THEMEMD.MIX、THEME.MIX、MOVMD*.MIX、MOVIES01.MIX、MOVIES*.MIX、MIXFILES 子目录下的 MOVIES01/MOVIES*/MOVMD01/MOVMD*/MOVMD03 系列、MOVMD%02d.MIX、MOVIES%02d.MIX |
| 5 | 0x52C5F3 → 0x5312A0 | 资源 | GLSMD.PAL、GLSSMD.SHP、GLSLMD.SHP（**非 MIX**） |
| 6 | 0x52C605 → 0x52CB90 | INI | BATTLEMD*.INI（§2） |

序号语义（**expandmd01/98/99 的含义**）—— 0x5301A0 主循环原文：

    0x5301BA  BF 63 00 00 00          mov  edi,0x63              ; 99（上界）
    0x5301C4  68 8C 66 82 00          push 0x82668C              ; "EXPANDMD%02d.MIX"
    0x5301CA  E8 25 8D 29 00          call 0x7C8EF4              ; sprintf（%02d = 两位补零）
    0x5301DB  E8 A0 C8 12 00          call 0x65CA80              ; RawFileClass ctor(名字)
    0x5301E7  FF 52 14                call [edx+0x14]            ; RawFileClass::Open(0) 存在性探测
    0x530289  4F                      dec  edi
    0x53028A  0F 89 2F FF FF FF       jns  0x5301BF              ; 99→0 递减

- 合法名字 = EXPANDMD00.MIX … EXPANDMD99.MIX（**两位、补零**）。expandmd1.mix（一位）不会被找到。
- **序号越大越先装载 ⇒ 优先级越高**：expandmd99 > expandmd98 > … > expandmd01 > expandmd00；全部高于 ra2md.mix。
- 存在性探测失败（文件不存在）→ 跳过，不报错；对象创建失败同样静默跳过。
- 通配装载（0x530000）同样走文件系统：0x53001A call ebx（ebx = [0x7E1208] FindFirstFileA），0x53002D test [esp+0x10],0x116 属性过滤，0x5300DB 再枚举 ELOCAL*.MIX。

### 1.4 通道 B 的覆盖规则：**先装载者优先**（FIFO）

**插入 = 尾插**（MixFileClass::MixFileClass 内联，0x5B3C20）：

    0x5B3DE2  8B 3D F0 EF AB 00       mov  edi,[0xABEFF0]        ; = 尾哨兵.Prev = 当前最后节点
    0x5B3E00  89 77 04                mov  [edi+4],esi           ; edi->Next = this  ★挂到尾部

**查找 = 从最早装载者向后，第一个命中即返回**（MixFileClass::Find = 0x5B4430）：

    0x5B44A1  8B 2D E0 EF AB 00       mov  ebp,[0xABEFE0]        ; = 头哨兵.Next = 最早装载的 MIX
    0x5B44FD  8B 6C 24 14             mov  ebp,[esp+0x14]        ; ebp = ebp->Next（更晚装载者）

链表哨兵布局（由上述两段 + 0x5B3AC0 静态初始化推定）：节点为 {+4:Next, +8:Prev}；0xABEFDC 为头哨兵（0xABEFE0=Head.Next）、0xABEFE8 为尾哨兵（0xABEFF0=Tail.Prev）。这两个哨兵落在 .data 的**零填充虚拟尾区**，运行时才初始化，故不可做文件字节断言（[实证] 仅限装载/查找代码本身）。

⇒ **同名条目（CRC32 ID 相同）时，先装载的 MIX 赢**。expandmd98.mix 可覆盖 ra2md.mix / ra2.mix 官方条目；会被 expandmd99.mix 覆盖；会被散装文件覆盖。

### 1.5 完整优先级链图（高 → 低）

    【通道 A 散装文件】游戏目录（CWD）下的原始文件名
            ▲ 单个 CCFileClass 请求内最先尝试（0x473D2D）；mode&2（只读写盘）时跳过 MIX
    【通道 B MIX 优先级链表（0xABEFD8，Head→Tail = 早→晚）】
       1. langmd.mix                 ← Startup 0x6BD7EF（★先于 Init）
       2. language.mix               ← Startup 0x6BD81F
       3. expandmd99.mix             ← Init 0x5301A0 循环首轮（edi=99）
       4. expandmd98.mix … expandmd01.mix
       5. expandmd00.mix
       6. ra2md.mix   (0x884DF8)
       7. ra2.mix     (0x884DFC)
       8. cachemd.mix (0x884E48)
       9. cache.mix   (0x884E4C)
      10. localmd.mix (0x884E50)
      11. local.mix  (0x884E54)
      12. ecache*.mix（FindFirstFileA 枚举序，0x530000）
      13. elocal*.mix（同上）
      14. conqmd / germd / isogenmd / isogen / conquer / cameomd / cameo
          mapsmd* / maps* / mapsmd%02d / maps%02d
          multimd / thememd / theme
          movmd* / movies01 / movies* / mixfiles 子目录系列（0x530460，含 CD 感知通配）
      15. （0x5312A0 只装 GLS* 资源，不新增 MIX）
    【通道 C CD 路径（不属于上面两张表）】
      仅次级装载器的通配二次尝试：CD 路径 + MAPSMD*/MAPS*/MOVMD*/MOVIES*/MIXFILES 系列（0x47AF70 → 0x47B020）

### 1.6 勘误：langmd.mix / language.mix 位于链表**头部**（不是尾部）

docs/re/fs_mix_load_chain.md §3.1 把 LANGMD.MIX / LANGUAGE.MIX 排在最末。本轮字节证据表明它们在 **Startup 阶段就已创建**，因而是**最高优先级**：

    0x6BD7C5  8B 35 D0 C1 81 00       mov  esi,[0x81C1D0]        ; 保存 CD 状态
    0x6BD7CB  B9 FE FF FF FF          mov  ecx,0xFFFFFFFE        ; −2 = 无需 CD
    0x6BD7D0  E8 DB B8 DB FF          call 0x4790B0              ; 写 CD 状态=−2（使 MIX ctor 的 CD 门禁短路）
    0x6BD7E8  68 5C 0D 84 00          push 0x840D5C              ; "LANGMD.MIX"
    0x6BD7EF  E8 2C 64 EF FF          call 0x5B3C20              ; ★MixFileClass ctor ⇒ 尾插链表
    0x6BD7F4  A3 04 4E 88 00          mov  [0x884E04],eax
    0x6BD818  68 4C 0D 84 00          push 0x840D4C              ; "LANGUAGE.MIX"（紧接着同样创建）
    ...
    0x6BE041  E8 7A EC DC FF          call 0x48CCC0              ; → 0x48CCCF call 0x52BA60 = Init()  ★晚于上面
    0x6BE061  E8 5A EC DC FF          call 0x48CCC0              ; 第二处调用点

证据链：① 两个 MIX 在 Startup.CPP 的同一段代码内以 MixFileClass ctor 创建（该段含字符串 "Init Encryption Keys." / "Init_Keys - Load" / "LANGMD.MIX" / "LANGUAGE.MIX"，__FILE__ = 0x840E0C 即 D:\ra2mdpost\Startup.CPP），ctor 必然尾插同一张全局链表（0x5B3DE2）；② 自 0x6BD6E0 起同步线性反汇编至 0x6BE080，期间唯一 ret 在 0x6BD881 / 0x6BD8A1（前者是同一函数的早退分支），**无函数边界**；③ 全镜像扫描：0x6BD6E0–0x6BE060 区间**没有任何外部 call/jmp 入口**，只能由该函数线性流程到达；④ 调用 Init() 的 0x6BE041 在同一线性流程中、地址序**晚于** 0x6BD7EF。

⇒ [实证]：**先建 langmd.mix / language.mix，后跑 Init 的 expandmd* 序列**。[推演]：这是设计意图——语言包必须能覆盖官方条目。
**产品含义**：expandmd99.mix **无法**覆盖 langmd.mix / language.mix 内的同名（CRC 相同）条目；要覆盖这类条目只能靠**散装文件**。

---

## 2. 必答项 2：BATTLEMD*.INI 通配、回退与合并

函数体 **0x52CB90**（FileOffset 0x12CB90），调用点 4 处：0x52C605（Init）、0x52DF25、0x52E0C4、0x685609（运行期重读，例如返回/重开战役界面）。

### 2.1 通配枚举（文件系统，非 MIX）

    0x52CBA0  68 A8 61 82 00          push 0x8261A8              ; "BATTLEMD*.INI"
    0x52CBA9  FF 15 08 12 7E 00       call [0x7E1208]            ; ★KERNEL32!FindFirstFileA（纯文件系统）
    0x52CBB1  83 FE FF                cmp  esi,-1
    0x52CBB8  0F 84 0F 01 00 00       je   0x52CCCD              ; INVALID_HANDLE_VALUE → 回退分支
    0x52CBBF  F7 84 24 84 00 00 00 16 01 00 00   test [esp+0x84],0x116   ; 属性过滤 DIRECTORY|HIDDEN|SYSTEM|TEMPORARY
    0x52CBF6  E8 F5 6D F4 FF          call 0x4739F0              ; CCFileClass ctor(枚举到的名字)
    0x52CBFB  6A 58                   push 0x58
    0x52CBFD  E8 15 C2 29 00          call 0x7C8E17              ; new(0x58) = CCINIClass
    0x52CC36  C7 06 F4 1A 7E 00       mov  [esi],0x7E1AF4        ; CCINIClass vftable
    0x52CC49  E8 A2 75 F4 FF          call 0x4741F0              ; INIClass::Load(file,0,0)
    0x52CC4E  68 98 61 82 00          push 0x826198              ; "BATTLEMD.INI"
    0x52CC54  E8 C7 C0 29 00          call 0x7C8D20              ; _stricmp(枚举名, "BATTLEMD.INI")
    0x52CC60  C6 44 24 13 01          mov  byte [esp+0x13],1     ; 置"已见过基准名"标志
    0x52CC67  E8 A4 01 F4 FF          call 0x46CE10              ; ★归并进全局 Battle 表
    0x52CCAB  FF 15 0C 12 7E 00       call [0x7E120C]            ; FindNextFileA（循环回 0x52CBBF）
    0x52CCBA  FF 15 00 13 7E 00       call [0x7E1300]            ; FindClose
    0x52CCC5  3A C3                   cmp  al,bl
    0x52CCC7  0F 85 92 00 00 00       jne  0x52CD5F              ; ★已见过 BATTLEMD.INI → 跳过回退

要点（全部 [实证]）：
- 通配是 **Win32 FindFirstFileA**，参数是**相对名** ⇒ 只搜 **CWD = 游戏目录**，**不递归子目录**（子目录里的 BATTLEMD98.INI 不会被枚举）。
- 通配**看不到 MIX 内部条目**（API 层面不可能）。
- 属性过滤 0x116 = DIRECTORY|HIDDEN|SYSTEM|TEMPORARY。
- 每个匹配文件用 CCFileClass（**mix 感知**，但名字来自枚举结果，等价散装路径）+ 临时 CCINIClass，装载后立即析构；数据只经 0x46CE10 落到全局表。
- 另注：每轮装载后（0x52CC7C 起）还会构造一个 CCFileClass 栈对象并把 vtable 从 0x7E16B0 改成 0x7E1668（CDFileClass）再析构 —— CDFileClass 在继承链上位于 CCFileClass 之下（YRpp/CCFileClass.h：FileClass → RawFileClass → BufferIOFileClass → CDFileClass → CCFileClass），此序列为对象清理/类型切换，不影响装载语义。

### 2.2 回退分支（BATTLEMD.INI，这一路 mix 感知）

    0x52CCCD  68 98 61 82 00          push 0x826198              ; "BATTLEMD.INI"
    0x52CCD6  E8 15 6D F4 FF          call 0x4739F0              ; ★CCFileClass ctor（磁盘优先 + MIX 回落）
    0x52CD25  E8 C6 74 F4 FF          call 0x4741F0              ; INIClass::Load
    0x52CD2C  E8 DF 00 F4 FF          call 0x46CE10              ; 同一归并函数

**触发条件**：仅当 FindFirstFileA("BATTLEMD*.INI") 返回 INVALID_HANDLE_VALUE（目录里**一个** BATTLEMD*.INI 都没有）。
⇒ 目录里存在**任意** BATTLEMD*.INI（含 BATTLEMD.INI 自己）时，回退被 0x52CCC7 跳过 → **此时 MIX 内的 BATTLEMD.INI 不会被读**。
⇒ 只有目录里完全没有 BATTLEMD*.INI 时，回退才生效 → **这是 MIX 内 BATTLEMD.INI 唯一可能被读到的情况**。

### 2.3 多文件合并语义（0x46CE10 + 全局表）

    0x46CE17  68 D8 B1 81 00          push 0x81B1D8              ; 段名 "Battles"
    0x46CE5A  A1 08 3D A8 00          mov  eax,[0xA83D08]        ; 全局 Battle 表 Count
    0x46CE97  68 A0 03 00 00          push 0x3A0                 ; 新战斗对象 928 字节
    0x46CF1F  8B 0D 08 3D A8 00 8B C1  mov ecx,[0xA83D08]; mov eax,ecx   ; Count++ / push_back
    0x46CF60  8B 16 57 8B             mov edx,[esi]; 然后 call [edx+0x64]   ; 用本 INI 覆写该对象字段

- 归并键 = [Battles] 段的**条目名**（战斗 ID，如 ALL1 / SOV1），比较用 _stricmp（不分大小写）。
- 同名条目 → **复用同一对象**，再 vtbl+0x64(ini) 覆写字段 ⇒ 跨文件"**后装载者赢**"；不同名 → 追加新对象。
- 全局表：DynamicVectorClass 基址 0xA83CF8，Count = 0xA83D08，元素 0x3A0 字节，名字在 +0x24。
- 跨文件先后 = **目录枚举顺序**（FindFirstFileA / FindNextFileA；NTFS 上通常近似字母序，但**引擎不保证**）。同目录下 BATTLEMD.INI < BATTLEMD01.INI < … < BATTLEMD98.INI 一般后者靠后 → 通常 98 胜出 [推演] / [待实测]。

### 2.4 "找不到"的行为

- 通配 0 命中且 BATTLEMD.INI 也不存在（散装与 MIX 都没有）→ CCFileClass::Open 返回 false、INIClass::Load 返回 0，**无任何错误提示、无 MessageBox、无断言**；0x46CE10 用空 INI 归并 = 空循环。
- 结果：全局 Battle 表**保持为空** ⇒ 战役列表为空。玩家可见后果 [待实测]。

---

## 3. 必答项 3（关键问题）：MIX 内部的 INI 是否被读取

### 3.1 通道对照（同一引擎内的两种 INI 装载范式）

| 范式 | 名字来源 | 装载 API | MIX 内可读？ | 实例（代码点） |
|---|---|---|---|---|
| **通配** | 字面量通配串 | FindFirstFileA（FS-only） | **否** | BATTLEMD*.INI（0x52CBA0）、RULEMD*.INI（0x52CD97） |
| **显式名** | 字面量完整名 | CCFileClass(name) + Open（磁盘优先 → MIX 回落） | **是** | SOUNDMD.INI（0x52C6E4）、EVAMD.INI（0x52C7B4）、THEMEMD.INI（0x52C8BE）、RULESMD.INI 回退（0x52CF41）、BATTLEMD.INI 回退（0x52CCD6） |

显式名范式原文（三者完全同构，以 THEMEMD.INI 为例）：

    0x52C8B9  68 94 5D 82 00          push 0x825D94              ; "THEMEMD.INI"
    0x52C8BE  E8 2D 71 F4 FF          call 0x4739F0              ; ★CCFileClass ctor(name) —— mix 感知
    0x52C8CB  E8 80 73 F4 FF          call 0x473C50              ; CCFileClass::Open → 磁盘优先，失败回落 MIX
    0x52C8D0  84 C0                   test al,al
    0x52C8D2  7512                    jne  0x52C8E6              ; 成功 → 解析 INI
    0x52C8D4  68 74 5D 82 00          push 0x825D74              ; 失败 → 仅（桩）打印后跳过

⇒ **结论：MIX 内的 INI 可以被读，但只对"用完整字面量名字请求"的那些文件成立**（THEMEMD.INI / EVAMD.INI / SOUNDMD.INI / RULESMD.INI / BATTLEMD.INI 等）。反过来，通配通道的文件**只存在于散装文件系统**。

### 3.2 定谳：expandmd98.mix 里的 BATTLEMD98.INI **永不加载** [实证]

三条相互独立的字节级证据：

1. **字符串表只有两个 BATTLEMD 字面量**：全镜像扫描命中 0x826198 "BATTLEMD.INI" 与 0x8261A8 "BATTLEMD*.INI"（复算：out/re_work/fs_mix_deep/s01_recon.py、s14_ini_wildcards.py），**不存在 "BATTLEMD98.INI"**。而 MixFileClass::Find（0x5B4430）只按 **CRC32(大写名)** 查条目 —— 要让 MIX 内的 BATTLEMD98.INI 被命中，必须有人**用这个名字**去请求；exe 里没有任何这样的请求点。名字表（XCC 的 local mix database.dat）也帮不上忙：MIX 查找不读名字表。
2. **唯一可能命中 BATTLEMD98.INI 的通道是通配**：0x52CBA9 call [0x7E1208] = **KERNEL32!FindFirstFileA**（IAT 槽 0x7E1208 内容 0x0040F844 指向导入名 "FindFirstFileA"，导入表解析闭合）。Win32 API 不感知 MIX，**结构上不可能**返回 MIX 内部条目；属性过滤（0x52CBBF）与 FindNextFileA 循环（0x52CCAB）都只作用于该 FS 句柄。
3. **唯一 mix 感知的 BATTLEMD 路是回退路，且它请求的是官方名 "BATTLEMD.INI"**（0x52CCCD），并且当目录里存在任意 BATTLEMD*.INI 时被 0x52CCC7 jne 0x52CD5F 跳过。

⇒ **项目文档"「MIX 内 BATTLEMD98.INI 永不加载」"成立**，且原因不是"INI 都从散装读"，而是"**该文件名只可能经通配到达，而通配是 FS-only**"。

### 3.3 必须一起记住的反例（同一问题上最容易踩的坑）

- 把 **BATTLEMD.INI**（官方名，不带数字后缀）打进 MIX，且目标机**一个散装 BATTLEMD*.INI 都没有** ⇒ **会被读到**（0x52CCCD → 0x52CCD6 的 CCFileClass 是 mix 感知的）。
- 但只要目标机上存在**任意** BATTLEMD*.INI（例如玩家自己放了一个 BATTLEMD98.INI，或安装包同时投了散装 BATTLEMD.INI），MIX 内那份就被跳过（0x52CCC7）。
- 同一通配渠道对 **RULEMD*.INI** 完全同构（0x52CD97 / 0x52CDAC / 0x52CDEC / 0x52CE29 + 回退 0x52CF38 / 0x52CF41）⇒ 规则可外推：**任何"通配式 .INI 扩展名"方案都必须散装投递**。

---

## 4. 必答项 4：[CD] / CDPath / InstallPath 复核

前序结论为"0 命中、证据不足"。本轮复核结论：**不进入文件搜索链**（除下述受限的二次通配），并给出 CD 子系统的完整定位。

### 4.1 字符串层面（复算脚本 s01_recon.py）

| 检索项 | 结果 |
|---|---|
| InstallPath | **0 命中** |
| CDPath | **0 命中** |
| 方括号 CD 段名 | **0 命中** |
| CDROM | 0x825FDC "Failed to initialize CDROM access!"、0x826040 "Init CDROM" |
| −CD 参数 | 0x8265A8 "-CD" |
| 注册表键 | 0x8313B0 "SOFTWARE\Westwood\Yuri's Revenge"、0x84964C "Software\Westwood\Yuri's Revenge"、0x849690 同键 + "\URL"、0x849640 "HTMLPath"、0x84A944 "RegPath"（**全部为 WOL/序列号/URL 用途**，无安装路径读写点） |

⇒ RA2MD.INI / 注册表里**不存在**"安装路径"或"CD 路径"键的读取点。[实证]
（RA2MD.INI 的引用点 0x52F594 / 0x6BC0A8 / 0x5D8FF5 等均用于其它段：端口、显示、WOL 等。）

### 4.2 −CD 参数链（CD 路径唯一的注册入口）

    0x52F79A  68 A8 65 82 00          push 0x8265A8              ; "-CD"
    0x52F7A0  E8 0B AD 29 00          call 0x7CA4B0              ; strstr(cmdline,"-CD")
    0x52F7A8  85 C0 / 74 14           test eax,eax; je 0x52F7C0  ; 未命中 → 看别的参数
    0x52F7AC  8D 4E 03                lea  ecx,[esi+3]           ; "-CD" 之后紧跟的字符串 = 路径
    0x52F7AF  C6 05 A0 E3 89 00 01    mov  byte [0x89E3A0],1     ; ★置"强制无 CD"字节
    0x52F7B6  E8 55 B3 F4 FF          call 0x47AB10              ; ★把该路径登记为 CD 路径

0x47AB10（CD_Set_Paths(const char*)）把参数按分号（0x81C8FC）切分、做尾部规范化，写入串缓冲 0x89E41C 与链表 0x89E410；0x47AA50 用模板 0x81C8F0（内容为 问号 + 冒号 + 反斜杠 + 星点星，即 "?:\\*.*" 之于 FindFirstFileA 的盘符探测式）+ 0x47AA62 add cl,0x41 逐盘符探测存在性（0x47AA85 FindFirstFileA）。

### 4.3 CD 路径的**唯一消费者**：次级装载器的二次通配

    0x47AFCF  FF 15 08 12 7E 00       call FindFirstFileA(通配串，原样)          ; 先按原样（相对 CWD）
    0x47AFDA  74 44                   je   0x47B020                            ; 未命中 → 试 CD 路径
    0x47B020  8B 1D 10 E4 89 00       mov  ebx,[0x89E410]                    ; ★CD 路径链表头（唯一读点）
    0x47B08A  FF 15 08 12 7E 00       call FindFirstFileA(CD路径 + 通配串)
    0x47B012  89 15 EC C8 81 00       mov  [0x81C8EC],edx                    ; 保存枚举句柄

- 调用者只有次级装载器：0x5307E0 / 0x53091F / 0x530F3A（配 0x47B0C0 = FindNext、0x47B130 = Close）。
- 涉及通配：MAPSMD*.MIX、MAPS*.MIX、MOVMD*.MIX、MOVIES*.MIX、MIXFILES 子目录下的 MOVIES*/MOVMD* 通配。
- [0x89E410] 的**全部** 15 处引用都在 CD.CPP（0x47AAC0–0x47B020）内，外加 Init 的一处读（0x52C3A8，仅用于判断"是否需要交互式 CD 初始化"）。**没有任何 CCFileClass::Get_File / RawFileClass::Open / MixFileClass::Find 路径引用它。** [实证]

### 4.4 CD 的另一副面孔：**门禁**（不影响优先级）

    MixFileClass::MixFileClass:
    0x5B3C58  A1 D0 C1 81 00          mov  eax,[0x81C1D0]        ; CD 状态
    0x5B3C66  FF 15 30 4C 7E 00       call [0x7E4C30]            ; ★每个 MIX 装载前的 CD 检查
    0x5B3C6E  75 0F                   jne  0x5B3C7F             ; 通过 → 继续构造
    0x5B3C70  E8 EB AF 10 00          call 0x6BEC60              ; 失败/取消 → 终止路径
    0x5B3C7A  E8 D1 AF 10 00          call 0x6BEC50

    CCFileClass::CDCheck（FileClass 纯虚实现，vtable 0x7E4C30 的 slot0 = 0x4790E0）:
    0x473AB0  8A 41 04 83 EC 08 84 C0 75 18   mov al,[ecx+4]（SkipCDCheck）; test; jne 跳过
    0x473ABA  A1 D0 C1 81 00                  mov eax,[0x81C1D0]
    0x473ACC  FF 15 30 4C 7E 00               call [0x7E4C30]        ; → 0x4790E0
    0x4790E4  83 F8 FE                      cmp eax,-2
    0x4790E9  B0 01 C2 04 00                mov al,1; ret 4        ; 状态=−2（无 CD）→ 直接真
    0x479104  E8 67 F1 02 00               call 0x4A8270          ; 否则 Force_CD_Available（唯一调用者）

- **LANGMD.MIX / LANGUAGE.MIX 创建时显式把状态压成 −2**（0x6BD7CB / 0x6BD7D0），绕开 CD 门禁；0x5301A0 进入/退出时保存/恢复该状态（入口 A1 D0 C1 81 00；0x53043E + 0x530445）。
- CD_Check 的语义是**"需不需要 CD"**（状态 −2 = 全本地；[0x89E3A0]=1 = −CD 强制无 CD → 直接返真），不是"去哪里找文件"。

### 4.5 结论

- **[CD] / CDPath / InstallPath 不进入散装文件搜索链，也不进入 MIX 优先级链。** 前序"0 命中"的判断在**字符串/键名层面成立**，本轮给出**机制层面的完整解释**：CD 子系统只提供 (a) 装载门禁、(b) 次级装载器里对 6 个 MAPS*/MOVIES*/MOVMD* 通配的一次额外尝试（且排在"游戏目录原样尝试"之后）。
- 唯一残留 [推演]：−CD 路径参数在**真实运行**中的行为（本文档只做静态链推导）；已列入 §8 未闭环。

---

## 5. 必答项 5：文件打开失败的字符串与错误分支

### 5.1 Init 的失败分支表（0x52BA60）

| 分支 | 代码点 | 字符串 | 后果 | 触发条件（本轮实证） |
|---|---|---|---|---|
| 主 MIX 装载失败 | 0x52BB69 → 0x52BB6B | 0x826100 "Failed to initialize bootstrap mixfiles!"、0x8260E4 " ..Failed to bootstrap!" | 打印（**桩，实际不输出**）+ 0x52BB87 or eax,-1 → Init 返回 −1 | **仅 operator new 失败 / 空指针检查命中**（见 5.3） |
| CD 初始化失败 | 0x52C3DE / 0x52C3ED | 0x825FDC "Failed to initialize CDROM access!"、0x826000 "Failed to find disk (user cancel)!" | 打印（桩）+ 0x52C3FA mov eax,1 → 返回 1 | 交互式 CD 初始化被用户取消/失败（且未给 −CD） |
| 次级装载失败 | 0x52C5A1 / 0x52C5A5 | 0x825F70 " ...Failed!!!" | 打印（桩）+ 提前返回 | 0x530460 返回 false |
| MIX ctor 内部失败 | 0x5B3CDF → 0x5B3D9A | 无字符串 | **不注册**：跳过条目表读取与链表尾插（0x5B3DE2），但**仍返回非空 this**（0x5B3E7D mov eax,esi + 0x5B3E88 ret 8） | 文件打不开 / 头解析失败 / new(条目表) 失败 |

### 5.2 关键**桩函数**：字符串存在 ≠ 会输出

| 桩 | 字节 | 含义 |
|---|---|---|
| 0x4068E0 | C3（单条 ret） | Init 内所有 call 0x4068E0 的调试打印（含上面两条 bootstrap 串、"Init Secondary Mixfiles....."、"Init Campaigns"、"Init Heaps" 等）**在 1.001 里是空操作** |
| 0x4A4AC0 | C3（单条 ret） | 同类打印/日志桩（含 " ..Failed to bootstrap!"、" ...Failed!!!"、" %s" 逐 MIX 日志） |

⇒ 通过字符串搜索"找到 Failed to initialize bootstrap mixfiles!" **不能**推出用户会看到该提示；1.001 下这些消息**不会出现在任何日志/对话框**。[实证]

### 5.3 "预载门槛"也是桩 ⇒ bootstrap 门禁实际很弱

在创建 CACHEMD.MIX / CACHE.MIX / LOCALMD.MIX / LOCAL.MIX 之后各有一次 call 0x5B43E0 + test al,al + je 0x5302E4：

    0x53033B  E8 A0 40 08 00          call 0x5B43E0
    0x530340  84 C0                   test al,al
    0x530342  74 A0                   je   0x5302E4              ; 失败 → 判定"缺少 bootstrap MIX"
    ...
    0x5B43E0  B0 01 C3                mov  al,1 ; ret  —— ★恒真桩

⇒ 该检查**恒不触发**。结合 5.1，Init 返回 −1 的**实际可达路径只有 operator new 失败**；文件缺失（ra2md.mix 不在、MIX 打不开）**不会**走这条分支 —— 它会创建一个**空壳 MixFileClass**（不在优先级链表里），继续启动，之后在具体资源找不到时才暴露（经 CCFileClass::CDCheck → Force_CD_Available 或其它资源失败路径）。
这是对前序文档 §3.1 "（失败即 0x52BB6B 打印 并中止）" 的**勘误**：字符串引用正确，但打印是桩、门禁是桩、且分支条件不是"文件存在性"。

### 5.4 其它用户可见失败（MessageBoxA 路径）

LANGUAGE.MIX 创建后（0x6BD818）立即做一次语言/字符串表自检（0x6BD83C call 0x7C978A、0x6BD849 call 0x7B84F0、0x6BD853 call 0x7346A0(名称 0x840D40 = "ra2md.str")）：

    0x6BD858  85 C0                   test eax,eax
    0x6BD85A  75 28                   jne  0x6BD884              ; 成功 → 继续启动
    0x6BD85C  6A 10                   push 0x10                 ; MB_ICONERROR
    0x6BD85E  68 34 0D 84 00          push 0x840D34             ; "Red Alert 2"（标题）
    0x6BD863  68 58 0C 84 00          push 0x840C58             ; "Unable to initialize 'ra2.csf', please reinstall Red Alert."
    0x6BD868  50                      push eax(0)               ; hWnd=0
    0x6BD869  FF 15 60 14 7E 00       call [0x7E1460]           ; ★MessageBoxA
    0x6BD881  C2 10 00                ret  0x10                 ; 启动失败返回

⇒ 这是"**语言包/字符串表在 LANGUAGE.MIX 内或磁盘上必须存在**"的硬门禁 [实证]（提示文本写的是 ra2.csf，实际检查名是 ra2md.str）。此外 Init 内还有 TXT_INSERT_CD_DIALOG / TXT_CD_DIALOG_1 / TXT_CANCEL 的 CD 插入对话框路径（0x479113、0x52C512–0x52C572）。

---

## 6. 对 ra2forge 的可操作结论

### 6.1 散装 vs 打包 MIX：风险对照

| 目标 | 散装（游戏目录） | 打包进 expandmd98.mix | 结论 |
|---|---|---|---|
| 新增/覆写**战役条目**（BATTLEMD98.INI） | ✅ **可靠**（通配唯一的可见域） | ❌ **永不加载**（§3.2 三条证据） | **必须散装** |
| 覆写官方战役条目（用官方名 BATTLEMD.INI） | ✅ 可靠（且会**屏蔽** MIX 内那份） | ⚠️ 只在目标机**无任何**散装 BATTLEMD*.INI 时被读到（0x52CCC7） | **优先散装** |
| 覆盖官方 MIX 内**同名资源**（CRC 相同） | ✅ 最高优先级（散装 > 所有 MIX） | ⚠️ 只赢过比它晚装载的 MIX（ra2md.mix 及以后）；**赢不过 langmd.mix / language.mix**（§1.6） | 散装最稳；要压官方 MIX 用 expandmd99 |
| 与其它 mod 共存（同名包号冲突） | 直接文件冲突 | expandmd99 压 expandmd98；两者都存在时 **98 先装载 ⇒ 98 赢**（方向与直觉相反） | 自家包抢**大**号 |
| 语言/字符串资源 | ✅ | ✅（但注意 §5.4 的字符串表门禁） | 别覆盖 langmd/language 内条目 |
| 地图（ECH01.MAP 等） | ✅ | ✅（ra2forge 现有做法；MIX 能被 ra2md.mix 之后的所有请求读到） | 保持现状 |

### 6.2 安装包形态建议（[推演]，但基于已实证机制）

1. **BATTLEMD98.INI 一律散装投递**到游戏目录（exe 同级）。这是唯一"跨版本、跨 MIX 配置都成立"的通道。
2. 若**同时**投含 BATTLEMD.INI 的 expandmd98.mix：确认安装包里**不要**再放散装 BATTLEMD.INI，否则 MIX 内那份是死代码（可接受，但别指望它生效）。
3. 战役 INI 的**同一战斗 ID 不要跨多个 BATTLEMD*.INI 重复**（胜者取决于目录枚举顺序，[待实测]）；最省事：只放一个 BATTLEMD98.INI。
4. 需要**压倒其它 mod**的自定义资源用 EXPANDMD99.MIX（数字大者先装载、先命中）；**不要**用 expandmd01.mix 这类小号（优先级低）。
5. −CD 路径参数与 CD 段名配置**都不要**依赖：CD 子系统只做门禁与 6 个 MOVIES*/MAPS* 通配的二次尝试，对 INI 完全不生效；且 −CD 会把 [0x89E3A0] 置 1，使 Init 跳过 CD 初始化。
6. 卸载/回滚：散装 INI 是**同目录同名替换**语义（无优先级层），安装包应记录并恢复原文件。

### 6.3 对既有工具链的核对

- ra2forge/mixlib.py 的 crc_hash = crc32(name.upper()) 与引擎 MixFileClass::Find（0x5B4430）一致（前序已闭环，本轮未改动该结论）。
- 本轮的**新增可用约束**：写进 expandmd*.mix 的文件名必须**两位补零**（EXPANDMD%02d），否则整包不会被装载（0x5301C4）。

---

## 7. 与 docs/re/fs_mix_load_chain.md 的差异（勘误登记，不改动原文）

| # | 前序表述 | 本轮实证 | 处置 |
|---|---|---|---|
| E1 | §3.1 / §3.2 把 LANGMD.MIX / LANGUAGE.MIX 列在装载序列**末尾**（优先级最低） | 两者在 **Startup 阶段**（0x6BD7EF / 0x6BD818）先于 Init（0x6BE041 → 0x52BA60）创建，尾插同一链表 ⇒ **最高优先级** | 以本文档 §1.6 为准；前序文档不改（只读参考） |
| E2 | §3.1 "失败即 0x52BB6B 打印 Failed to initialize bootstrap mixfiles! 并中止" | 打印目标是**单条 ret 桩** 0x4068E0；"CACHEMD/CACHE 预载门槛" 0x5B43E0 是**恒真桩**；Init 返回 −1 的实际可达路径是 operator new 失败 | §5.2 / §5.3 |
| E3 | §8 未闭环 2："MixFileClass::Cache() 填充函数未定位" | 本轮定位到 0x5B43E0（被 0x53033B / 0x5303A3 调用的"预载"入口）**是恒真桩**；MIX 整包缓存填充点仍未闭环（见 §8 未闭环 1） | §8 未闭环 1 |
| E4 | §8 未闭环 4："RA2MD.INI 的 CD 路径如何进入搜索链：未定位" | 结论升级为**不进入**：CD 段名 / CDPath / InstallPath 字符串 0 命中；CD 路径只用于 0x47AF70 的二次通配；−CD 路径参数是把路径写进 [0x89E41C] / [0x89E410] | §4 |
| E5 | §1.3 "散装文件优先于任何 MIX 条目 [待实测]（分支顺序）" | 分支顺序 [实证]（0x473D2D 早于 0x473D68），端到端仍 **[待实测]** | 本文档保持相同分级 |
| E6 | §3.1 次级装载清单（fn_530460_secondary_mix.txt） | 本轮用**字符串引用地址序**独立复算，清单**一致**，并补充 GENERMD.MIX、ISOGENMD.MIX、CAMEOMD.MIX、MAPSMD*.MIX / MAPS*.MIX、MOVMD*.MIX / MOVIES*.MIX、MIXFILES 子目录系列等条目 | §1.3 表 |

---

## 8. 未闭环清单（附下一步取证方法）

| # | 未闭环项 | 现状（为什么没闭环） | 下一步取证方法（可执行） |
|---|---|---|---|
| 1 | MixFileClass::Cache() 把整包解密进 +0x24 的**填充点** | 本轮确认 0x5B43E0（唯一"预载"调用目标）是 mov al,1; ret 桩；对 +0x24 的写点仍未见 | 静态：在 0x5B4430 内对 [ebp+0x24] 非零分支的上游回溯调用者，并反汇编 0x5B3E90（sub esp,0x304 + 读 [0xABEFE0] 的链表遍历函数，疑似 Cache / Free_All_Memory 家族）；动态：对 MixFileClass+0x12（缓冲归属字节）与 +0x24 设**写 watch** |
| 2 | "散装文件一定压过 MIX"的**端到端**验证 | 只有分支顺序实证 | 放同名 RULESMD.INI（散装 + expandmd98.mix 内各一份，内容不同），在 0x473D2D / 0x473D68 下断或比对全局表内容 |
| 3 | 多 BATTLEMD*.INI 冲突时**谁最终赢**（目录枚举顺序） | FindFirstFileA 顺序在 NTFS 上近似字母序但引擎不保证 | 投 BATTLEMD01.INI / BATTLEMD02.INI 同 ID 不同 Description；对 0x46CF60（call [edx+0x64]）下断观察覆写次序 |
| 4 | −CD 路径参数的真实运行语义 | 静态链完整，无运行验证 | 带 −CD 加某目录启动，在 0x47AFCF / 0x47B08A 下断，观察 FindFirstFileA 的实际模式串 |
| 5 | 0x479113（CD 插入对话框）与 0x52C512 分支的完整交互路径 | 只读到调用/字符串，未逐分支展开 | dump 0x479113–0x4791F0 与 0x52C4C0–0x52C580 全文，并对 0x623CD0（对话框执行）交叉引用 |
| 6 | 0x52CD70 之后（0x52D0xx–0x52D3xx）各 INI 装载点的完整清单与段名 | 本轮验证了与 BATTLEMD 同构的四点与显式名三点，其余因名字在变量里（%s / ecx）未提取 | 把 s16_order.py 扩展为"追踪 mov ecx,imm + push imm 双模式"，对 0x52CD70–0x52D400 重扫 |
| 7 | 0x4793B1 / 0x4794E4 处的 MAIN.MIX / MULTI.MIX（CD 版次级装载）是否与 0x530460 并行生效 | 只见到字符串与 ctor 调用，未确认调用条件 | 反汇编 0x479110–0x479700，确认它是"仅 CD 模式下的 set"还是 0x530460 的重复实现；并在 Init 里定位是否存在调用它的分支 |

---

## 9. 改动文件与门禁输出

### 9.1 新增文件（全部为本任务产物）

    docs/re/fs_mix_load_chain_deep.md            本文件（唯一新增文档）
    out/re_work/fs_mix_deep/
      rlib.py                只读逆向工具箱（段映射/反汇编/字符串/IAT/xref/claims）
      s01_recon.py           字符串与导入槽侦察（CD / InstallPath / 关键串）
      s02_cd.py              CD 相关调用点与字符串 xref
      s03_outline.py         区域"标注大纲"（调用/字符串/导入）生成器
      s04_cdinit.py          Init 的 CD 块与 −CD 分支原文
      s05_cdmod.py           CD.CPP 模块大纲（并生成 dump_cd_cpp.txt）
      s06_cdglobals.py       CD 全局变量与字符串 xref
      s07_cdfileclass.py     CDFileClass ctor 与 CD 路径登记
      s08_cdxref.py          全部 CD 全局的全体引用扫描
      s09_cdchain.py         CCFileClass / MixFileClass / Startup 中的 CD 集成点
      s10_q4.py              CD / 注册表 / CWD / 散装打开批量探针
      s11_q1.py              Init 调用图 + 通配 MIX 装载
      s12_langmd.py          LANGMD / LANGUAGE 与 ECACHE / ELOCAL 原文
      s13_cdfuncs.py         CD.CPP 函数起点与外部调用枚举
      s14_ini_wildcards.py   INI 通配全景 + ctor 失败路径
      s15_cd_enum.py         CD 感知 FindFirst 与 [0x89E410] 消费者
      s16_order.py           装载器字符串引用序（= 装载顺序证据）
      s17_ini_channels.py    INI 通道对照 + RawFileClass::Open
      s18_errors.py          错误字符串全景 + RULEMD 回退
      s19_bootstrap.py       bootstrap 门禁与预载桩
      s20_langmd_order.py    LANGMD 装载点定位
      s21_order_proof.py     LANGMD 早于 Init 的函数边界证明
      s22_startup_graph.py   Startup 模块调用图
      s23_langmd_tail.py     LANGMD 块尾与全局指针
      s24_sync_flow.py       同步线性控制流扫描
      s25_langmd_strings.py  Startup.CPP 字符串（语言表门禁）
      s26_csf.py             语言表装载点排查
      s27_explicit_ini.py    显式名 INI 三点对照
      s28_bytes.py           断言字节批量取值（含 IAT 解析）
      claims.txt             190 条字节级断言
      dump_cd_cpp.txt        CD.CPP 全文反汇编（1563 条）
      dump_init_sequence.txt Init 主序列全文（802 条）
      dump_530000_wildcard_mix.txt   ECACHE* / ELOCAL* 通配装载全文（139 条）

**未改动**：ra2render 目录全部文件、REVERSE_ENGINEERING_AND_PATCHES.md、其它既有 docs/re 下 md 文档（含 fs_mix_load_chain.md）、ra2youli 安装目录、out/re_work/fs_mix 既有资产（只读复用）。

### 9.2 门禁实跑输出

    PS D:\Project\ra2-campaign-forge> python tools/verify_anchors.py
    ===================================================================================================================
      RA2/YR 二进制决定性锚点自动化回归测试套件 (verify_anchors.py)
    ===================================================================================================================
    目标文件 : D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe (大小: 4,825,360 字节, ImageBase: 0x400000)
    断言文件 : D:\Project\ra2-campaign-forge\docs\re\anchor_claims.txt
    反汇编器 : Capstone x86-32 引擎已就绪
    -------------------------------------------------------------------------------------------------------------------
    [基线完整性审计]
      [PASS] .text 原始段哈希: c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738 (口径: raw(SizeOfRawData=0x3E0000))
      [INFO] PE头特征判定 : RA2OPT_PERF_APPLIED (0xAE=0x20, Stack=4MB, .text未变) (DllChar: 0x20, StackReserve: 0x400000)
      [PASS] .detour 原生签名: 40 00 00 00 44 74 72 00 (VA 0xb93000) -> 严禁写入/注入原则确立
    -------------------------------------------------------------------------------------------------------------------
    回归汇总 : 断言总数 323 条 | PASS: 323 (100.00%) | FAIL: 0 | NOREAD: 0
    ★ 最终裁决 : [100% ALL PASS] 全库决定性锚点与二进制基线完全一致，生产环境可安全放行！
    ===================================================================================================================
    PS D:\Project\ra2-campaign-forge> python tools/audit_bytes.py out/re_work/fs_mix_deep/claims.txt
    ...（逐条 OK，尾部汇总）...
    --------------------------------------------------------------------------------------------------------------
    合计 190 条：OK=190  MISMATCH/NOREAD=0

### 9.3 复算命令

    cd D:\Project\ra2-campaign-forge
    python tools/verify_anchors.py                                  # 期望 323/323 PASS
    python tools/audit_bytes.py out/re_work/fs_mix_deep/claims.txt  # 期望 190/190 OK
    python out/re_work/fs_mix_deep/s11_q1.py                        # 主/通配/次级装载顺序
    python out/re_work/fs_mix_deep/s28_bytes.py                     # 全部关键字节与 IAT 解析
    python out/re_work/fs_mix_deep/s21_order_proof.py               # LANGMD 早于 Init 的函数边界证明
    python out/re_work/fs_mix_deep/s17_ini_channels.py              # 通配 vs 显式名通道对照
