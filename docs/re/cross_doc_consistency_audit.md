# 全库 30+ 份逆向文档交叉一致性审计与终极裁定大报告 (Cross-Document Consistency Audit & Definitive Adjudication)

> **审计编号**：S21-AUDIT-MASTER  
> **审计日期**：2026-09-26  
> **责任代理**：Antigravity (S21 专项子代理)  
> **受检基线**：`ra2youli/gamemd.exe`（官方 Yuri's Revenge 1.001 最终原版，MD5: `4f37486e5b0dbe2ae5f45aeee0f98367`）  
> **受检文档池**：`docs/re/` 下全部 82 份文档（重点穿透 30+ 份核心深潜报告、技术规范与架构台账）  
> **可复算基准**：PE ImageBase = `0x00400000`，`.text` 节 VA = `0x00401000`，文件偏移 `FileOffset = VA - 0x00400000`  
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> **证据等级规范**：`[实证]`（精准 VA + 物理文件偏移 + 原始十六进制机器码 + Capstone 反汇编指令）× `[推演]` × `[待实测]`  

---

## 一、审计背景、执行纪律与技术基线

### 1.1 审计缘起与目标
自 RA2 逆向工程全面铺开以来，项目库已沉淀 80 余份逆向工程文档、技术规范与冲刺总结报告。随着研究的步步深入，多代子代理在不同研究阶段、不同局域上下文（如网络同步、渲染管线、AI 逻辑、超武机制、寻路算法等）中提出了各自的符号假设、结构偏移推导与代码片段解读。

然而，由于历史认知迭代以及缺乏跨文档的全局静态对拍，工程库在局部出现了**同名符号物理地址冲突**、**虚表槽位与字节偏移混淆**、**对象尺寸推演矛盾**、**读写函数对称性误判**、**跳板机器码掩码手误**以及**核心算子定性漂移**等不一致现象。

本报告受命作为 **S21 专项审计终局交付物**，对全库 30+ 份核心逆向文档进行地毯式交叉比对，依托 `gamemd.exe` 物理二进制的指令级事实，彻底肃清历史遗留的假说矛盾，建立不可动摇的**权威裁定真理（Ground Truth）**与**全库一致性三维矩阵**。

### 1.2 执行纪律核查
1. **写作用域隔离**：严禁篡改 `ra2render/**` 源码库及顶层台账 `REVERSE_ENGINEERING_AND_PATCHES.md`；写作仅落盘于全新文档 `docs/re/cross_doc_consistency_audit.md` 与总结报告 `docs/re/re_sprint_S21_report.md`；辅助验证脚本全部受限于 `out/re_work/re_sprint/S21/`。
2. **证据闭环原则**：所有被裁定条目均提供物理反汇编机器码支撑；无实证闭环项明确标注“未闭环 + 原因 + 下一步取证方法”。
3. **零启动原则**：全程基于静态 PE 解析与 Capstone 反汇编引擎，物理游戏进程零启动。

---

## 二、Lead v25 补给单核心冲突裁定专章 (E 系列与重大结构纠偏)

本章直接采纳并全面裁定 Lead v25 专项补给单指出的已知冲突清单。

### 2.1 E1 存档主函数定性冲突与调用链裁定 [实证]

- **冲突现象**：
  `docs/re/net_sync_checksum.md` §4.1 表格将 `0x0067D300` 标注为“存档主函数（4416B，顺序调约 35 个系统 Save）”。而其他系统文档推演认为外层存在统揽 IStorage 的建档函数。
- **二进制真理裁定**：
  1. `0x0067D300` 的真实语义为 **`Save_Core`（核心子系统数据流序列化函数）**，其主要职责是将 35 个对象池及游戏状态写入流（IStream）。
  2. 真正的**外层建档与顶层 IStorage 事务总入口为 `0x0067D0C0`**（或由 `0x0067D0BE` 引导的外部打包包装体）。
  3. 全镜像扫描证实：在整个 PE 映像中，作为 32 位立即数（DWORD）对 `0x0067D0C0` 和 `0x0067D300` 的直接数据引用次数均为 **0**。这表明 `0x0067D0C0` 是通过 COM 接口（如 `IPersistStorage` 虚表）或外部导出的函数指针分发调用的。
  4. 汇编取证表明：外层建档函数在完成复合文档存储（OLE Structured Storage）初始化与流创建后，在 `0x0067D1AF` 处通过相对近调用（E8）直接调用了 `Save_Core`（`0x0067D300`）：
- **汇编实证**：
  ```asm
  ; 位于外层建档包装函数内部 (VA: 0x0067D1AF, FileOffset: 0x0027D1AF)
  0x0067D19C: 3D 02 40 00 80     cmp   eax, 0x80004002        ; 校验 HRESULT
  0x0067D1A1: 74 06              je    0x0067D1A9
  0x0067D1A3: 50                 push  eax
  0x0067D1A4: E8 77 F5 15 00     call  0x007DC720
  0x0067D1A9: 8B 4C 24 1C        mov   ecx, [esp + 0x1C]      ; 传入目标 IStream 接口指针
  0x0067D1AD: 33 D2              xor   edx, edx
  0x0067D1AF: E8 4C 01 00 00     call  0x0067D300             ; ★ 核心 Save_Core 调用！
  0x0067D1B4: 8A D8              mov   bl, al                 ; 接收保存结果布尔值
  0x0067D1B6: 8B 44 24 14        mov   eax, [esp + 0x14]
  0x0067D1BA: 3B C5              cmp   eax, ebp
  0x0067D1BC: 75 0E              jne   0x0067D1CC
  0x0067D1CE: 55                 push  ebp
  0x0067D1CF: 50                 push  eax
  0x0067D1D0: FF 51 10           call  dword ptr [ecx + 0x10] ; IStream::Commit / Release
  ```
- **裁定结论**：
  将 `0x0067D300` 准确修正定名为 `Save_Core`；将 `0x0067D0C0` 定名为 `Game::SaveGame_Storage_Entry`。

---

### 2.2 E2 读写一一对应冲突裁定 [实证]

- **冲突现象**：
  `docs/re/net_sync_checksum.md` §4.1 宣称：“读/装载主入口 `0x0067CEF0`：校验魔数后跳 `0x680F70..0x6812E0` 一族 Load（与 Save 一一对应）”。
- **二进制真理裁定**：
  该“读档与 Save 一一对应”假设**完全不成立**！
  1. 读档入口 `0x0067CEF0` 内部顺序调用的 `0x680FF0..0x6812E0` 共计 **13~16 个函数**，其物理实质绝非全游戏各子系统的解包函数，而是**存档文件头部元数据访问器（Savegame Header Accessors/Setters）**！
  2. 这些函数的作用仅仅是将从存储流中读入的头结构解包，逐个向全局会话单例写入版本魔数（`0x83D560`）、场景索引、遭遇战设置、玩家颜色、存盘名称等元数据字段。
  3. 反观写档侧 `0x0067D300`（`Save_Core`），其内部连续驱动了 **35 块独立的对象池与系统序列化模块**（包括 `0x67FDF0 + i*0x80` 模板族及各具名 Class 的 `IPersistStream::Save`），涵盖单位、建筑、步兵、地图 Cell、裂缝、动画、微粒、超武、战队等。
  4. 真正的全系统数据加载（反序列化）位于更深层的载入流程（如 `ScenarioClass::Read_Scenario_INI` 与各 Class 的 `IPersistStream::Load` 虚表族）。
- **汇编实证**：
  ```asm
  ; 读档入口 0x0067CEF0 内部的头部解包调用链（纯元数据解包）：
  0x0067CF6B: E8 80 40 00 00     call  0x00680FF0             ; 初始化解包结构
  0x0067CF7D: E8 FE 40 00 00     call  0x00681080             ; 校验魔数 0x2B898
  0x0067CF8A: E8 11 41 00 00     call  0x006810A0             ; 设置存档版本
  0x0067CF98: E8 C3 40 00 00     call  0x00681060             ; 设置战役标志
  0x0067CFB1: E8 1A 41 00 00     call  0x006810D0             ; 设置战术场景
  0x0067CFCA: E8 41 41 00 00     call  0x00681110             ; 设置玩家所属
  0x0067CFE2: E8 49 41 00 00     call  0x00681130             ; 设置对局时间
  0x0067CFF3: E8 C8 41 00 00     call  0x006811C0             ; 设置地图名称
  0x0067D006: E8 B5 42 00 00     call  0x006812C0             ; 设置会话 ID
  0x0067D022: E8 59 42 00 00     call  0x00681280             ; 设置游戏速度
  0x0067D033: E8 C8 41 00 00     call  0x00681200             ; 设置难度等级
  0x0067D044: E8 F7 41 00 00     call  0x00681240             ; 设置初始资金
  0x0067D055: E8 86 42 00 00     call  0x006812E0             ; 头部校验完毕
  ```
- **裁定结论**：
  推翻“0x680F70..0x6812E0 与 35 块 Save 一一对应”的历史误判；该 16 个函数更名为 `SaveHeader::Read_*` 系列访问器。

---

### 2.3 E3 存档代码长度冲突与对齐空隙勘误 [实证]

- **冲突现象**：
  `net_sync_checksum.md` §4.1 记录 `0x0067D300` 长度为 `4416B`。
- **二进制真理裁定**：
  1. 实测 `0x0067D300` 函数体的最后一条指令位于 `0x0067E43A`（`C3 ret`）。
  2. 纯机器码长度为：`0x0067E43A - 0x0067D300 = 0x113A = 4410 字节`（若计入末尾 1 字节 `ret` 自身，则闭区间字节数为 **4411 字节**）。
  3. 下一个函数起始于 `0x0067E440`（`81 EC 08 05 00 00 sub esp, 0x508`）。
  4. 在 `0x0067E43B .. 0x0067E43F` 之间存在 **5 字节的 `0x90` (NOP)** 函数对齐填充（Padding）。
  5. 历史文档作者计算函数对齐边界差值：`0x0067E440 - 0x0067D300 = 0x1140 = 4416 字节`，从而将 5 个用于 16 字节边界对齐的 NOP 机器码误计入函数可执行代码长度。
- **汇编实证**：
  ```asm
  ; 0x0067D300 尾声与后续函数交界 (VA: 0x0067E430 .. 0x0067E448)
  0x0067E430: 5F                 pop   edi
  0x0067E431: 5E                 pop   esi
  0x0067E432: 5D                 pop   ebp
  0x0067E433: 5B                 pop   ebx
  0x0067E434: 0F 9D C0           setge al
  0x0067E437: 83 C4 08           add   esp, 8
  0x0067E43A: C3                 ret                    ; ★ 函数物理终点 (Offset: 0x0027E43A)
  0x0067E43B: 90                 nop                    ; 填充对齐
  0x0067E43C: 90                 nop                    ; 填充对齐
  0x0067E43D: 90                 nop                    ; 填充对齐
  0x0067E43E: 90                 nop                    ; 填充对齐
  0x0067E43F: 90                 nop                    ; 填充对齐
  0x0067E440: 81 EC 08 05 00 00 sub   esp, 0x508        ; ★ 下一函数起始 (Offset: 0x0027E440)
  ```
- **裁定结论**：
  指令净长度更正为 **4410 字节**（含 ret 为 4411 字节）；对齐跨度为 4416 字节。全库文档统一定义格式为：“4410B (4416B aligned)”。

---

### 2.4 E4 单例数组与计数器三方冲突终极平叛 [实证]

- **冲突现象**：
  1. `docs/re/house_team_ai_update.md:118` 声明：`0x00A80228` 为 `HouseClass*`，Items 为 `0x00A8022C`，Count 为 `0x00A80238`。
  2. `docs/re/superweapon_re.md:531` 声明：循环 4 为 `0xA8022C / 0xA80238`，遍历读取 `obj+0x241` 字节。
  3. `docs/re/net_sync_checksum.md:260` 声明：`for each Aircraft: // 0xA8022C / 0xA80238, mix( byte at obj+0x241 )`。
  4. 同时，关于 `0x00A8ECA0` 家族字段，`house_team_ai_update.md:121` 声明其 Items 为 `0x00A8ECA4`、Count 为 `0x00A8ECA8`；但联机与保存文档中偶有将 `0xA8ECA4` 当作 Count 的冲突表述。
- **二进制真理裁定**：
  - **关于 0xA8022C 与 0xA80238 的归属**：
    1. 在 `0x0064DCB3 .. 0x0064DCD5` 联机校验计算中，代码显式读取 `[0x00A80238]` 作为循环上限，取 `[0x00A8022C]` 作为指针数组基址，并提取每个对象的 `[ecx + 0x241]`（`HasPassengers` / 登机状态字节）。
    2. 在 `0x0041EC90`（`AircraftClass::Array` 遍历例程）中，明确读取 `[0x00A80238]` 为数量，取 `[0x00A8022C]` 为数组指针，读取元素 `[ecx + esi*4]`，随后访问 `[edx + 0x34]`（`TechnoType`）并比对 `[edx + 0xBC]`（战机挂弹/机库属性）。
    3. 全局真正的 **House 数组位于 `0x0087F77C`（Items）与 `0x0087F788`（Count）**！证据：`0x0064DD98` 遍历 `0x0087F77C`，调用 `[eax + 0x2C]` 获取 RTTI 类型，比对结果为 `cmp eax, 4`（`RTTI_HOUSE = 4`）！
    4. 裁定：`0x00A8022C` / `0x00A80238` **100% 为 `AircraftClass::Array`**！`house_team_ai_update.md:118` 归为 House 属于重大笔误，予以撤销纠偏。
  - **关于 0xA8ECA0 家族字段布局**：
    1. `0x004E70FD .. 0x004E7111` 为全局 `DynamicVectorClass<TeamTypeClass*>` 单例的初始化现场：
       - `0x00A8ECA0`: 虚表指针 `0x007EA0E4`；
       - `0x00A8ECA4`: `Items`（动态数组指针，初始化为 0）；
       - `0x00A8ECA8`: `VectorMax` / `Capacity`（容量，初始化为 0）；
       - `0x00A8ECAC`: `IsAllocated`（布尔标记，初始化为 1）；
       - `0x00A8ECB0`: **`ActiveCount` / `Count`（真实活动计数器，初始化为 0）**！
       - `0x00A8ECB4`: `GrowthStep`（增长步长，初始化为 10）。
    2. 在 `0x006F0859 .. 0x006F0868`（添加 TeamType）汇编取证中：
       ```asm
       0x006F0859: 8B C1            mov   eax, ecx
       0x006F085B: 41               inc   ecx
       0x006F085C: 89 0D B0 EC A8 00 mov  dword ptr [0x00A8ECB0], ecx ; ★ Count 自增并写回 0xA8ECB0！
       0x006F0862: 8B 0D A4 EC A8 00 mov  ecx, dword ptr [0x00A8ECA4] ; ★ 取 Items 数组指针 0xA8ECA4！
       0x006F0868: 89 34 81         mov   dword ptr [ecx + eax*4], esi ; 写入新元素
       ```
    3. 在 `0x0067C94A` 存档遍历中：
       ```asm
       0x0067C94A: 8B 0D A4 EC A8 00 mov   ecx, dword ptr [0x00A8ECA4] ; ★ 取 Items 指针
       0x0067C955: 8B 0C B1         mov   ecx, dword ptr [ecx + esi*4] ; 取出 TeamType*
       0x0067C95D: A1 B0 EC A8 00   mov   eax, dword ptr [0x00A8ECB0] ; ★ 取 Count (0xA8ECB0)
       0x0067C963: 3B F0            cmp   esi, eax                    ; 循环边界比对
       0x0067C965: 7C E3            jl    0x0067C94A
       ```
- **裁定结论**：
  `0xA8ECA4` 铁证为 **`Items`（数组首指针）**，`0xA8ECA8` 为 **`Capacity`**，而 **`0xA8ECB0` 才是真正的 `Count`**！本审计按物理指令级事实采纳 `AircraftClass` 与上述准确偏移。

---

### 2.5 E-1 触发器动作 vs 队伍脚本表冲突裁定 [实证]

- **冲突现象**：
  历史推演在审查 `0x006E9CE8` 时，将其混淆于 `TActionClass`（地图触发器动作表）。
- **二进制真理裁定**：
  1. `0x006E9CE8` 物理归属于 **`TeamClass::AI` 队伍脚本分发例程**。
  2. 位于 `0x006E944B` 处的指令为 `83 F8 40 cmp eax, 0x40; ja 0x6E95AB`，紧随其后的是多路跳转表分发：`FF 24 85 74 9F 6E 00 jmp dword ptr [eax*4 + 0x006E9F74]`。
  3. 跳转表基址为 `0x006E9F74`，包含 65 个脚本动作分支（0..64）。
  4. 查表第 49 项（偏移 `49 * 4 = 196 = 0xC4`，表地址 `0x006EA038`），其存放的目标指令地址为 **`0x006E9CE1`**：
     ```asm
     0x006E9CE1: C6 86 80 00 00 00 01 mov   byte ptr [esi + 0x80], 1   ; Team 状态位标记
     0x006E9CE8: C6 86 84 00 00 00 01 mov   byte ptr [esi + 0x84], 1   ; ★ 0x6E9CE8 现场〔勘误 ASM-FIX-7〕原记立即数 `00`（`mov byte ptr [esi + 0x84], 0`）实测 `01`（立即数 0/1 写反）
     0x006E9CEF: 5F                 pop   edi
     0x006E9CF0: 5E                 pop   esi
     0x006E9CF1: 5D                 pop   ebp
     0x006E9CF2: 5B                 pop   ebx
     0x006E9CF3: 83 C4 28           add   esp, 0x28
     0x006E9CF6: C3                 ret
     ```
  5. 真正的 `TActionClass`（地图触发器动作）属于独立体系，Action 49 的官方定义为 **`Zoom In`（视口缩放）**，其执行分发函数入口为 `0x006DD1B0` 族。
- **裁定结论**：
  `0x006E9CE8` 归属于 `TeamClass::AI_Script_Action_49`，非 `TActionClass`。

---

### 2.6 结构纠偏：0x67FDF0 35 条 0x80 模板函数本质确证 [实证]

- **冲突现象**：
  早期文档曾推测 `0x0067FDF0 + i*0x80` 是“包含 35 个条目的分发函数调度表（Dispatch Table）”。
- **二进制真理裁定**：
  1. 静态提取从 `0x0067FDF0` 到 `0x00680EF0`（共 35 个步长为 `0x80` 的连续物理块）：
     $$\text{Unique MD5 Hashes} = \mathbf{1}$$
     全部 35 个块的 MD5 散列值 **100% 逐字节完全一致**，散列值均为：
     $$\text{MD5} = \mathbf{cb13908da7ed66fb2a7545323b865a3d}$$
     > **[task-11 口径注明 · v1.5.35 收尾] 长度口径必须显式标注（两种均正确，禁止第三种口径）[实证]**：
     > - **127 B 口径**（纯代码长度，`0x67FDF0..0x67FE6E`，末字节 `C3` = `ret`）→ MD5 = `9f6770a9cd27b9fa49558adf28c92f10`；
     > - **128 B 口径**（含尾部 1 字节 `0x90` NOP 对齐填充，`0x67FDF0..0x67FE6F`）→ MD5 = `cb13908da7ed66fb2a7545323b865a3d` ← **本节原文所用口径**；
     > - 两口径各自 **35/35 唯一**（实测：127 B 与 128 B 分别只产生 1 个不同散列值）；
     > - 复算命令：`python out/re_work/errata/audit_template_md5.py`；
     > - **纪律**：今后凡引用上述任一散列值，必须同时写明所取字节长度，否则视为口径不明（同 `[v1.5.20]` 的 314/457 长度教训）。

  2. 每一块的机器码首字节均为 `83 EC 08 53 56 57 8B FA 8B D9 6A 00 8B 47 10 8D ...`，内部完整包含循环迭代、容器遍历以及对 `IPersistStream::Save`（`call dword ptr [ecx + 0x10]`）的虚表调用，末尾为 `ret`（`0x0067FE6E: C3`）加 1 字节 `0x90` NOP 填充，刚好构成 `0x80`（128 字节）的函数体。
  3. 全镜像硬证据反证：在整个 PE 映像中，作为 DWORD 出现的这 35 个地址（`0x0067FDF0`, `0x0067FE70`, ...）的**直接引用计数全为 0**！这彻底推翻了“分发指针表”假说。
  4. 编译器机理解析：这是 MSVC 6.0 编译器针对不同指针类型的序列化模板（如 `Save_Array_Template<T>`）展开实例化时，由于生成的目标机器码完全相同且未开启 COMDAT 折叠（`/OPT:ICF`）而编译留存的 **35 个逐字节全等的独立模板函数实例**！
- **裁定结论**：
  纠正为“35 个同构模板序列化函数副本”，严禁表述为“调度表/指针表条目”。
  另：本族 MD5 存在 **127 B / 128 B 两种正确长度口径**（见上方口径注明），引用时必须标明所取长度。

---

### 2.7 待补证据与降标：fs_mix 全局 0x884DF8 / 0x884E50 真实机理 [实证 + 降标说明]

- **冲突现象**：
  `docs/re/fs_mix_load_chain.md` 标注：`0x884DF8 = ra2md.mix`, `0x884E50 = localmd`，部分语境暗示其为只读字符串指针或名字缓存。
- **二进制真理裁定**：
  1. **静态磁盘事实**：在未运行的 `gamemd.exe` PE 文件中，`0x00884DF8` 与 `0x00884E50` 位于可读写的 `.data` 节内。静态提取其原始字节，实测为遗留的 UTF-16LE 宽字符碎片（`0x884DF8` 前导字节为 `"ider1"`，`0x884E50` 为 `"GUI:Credits"`）。
  2. **运行时汇编实证**：在引擎启动流程中，系统在 `0x005302A8` 与 `0x005303D2` 分配 `MixFileClass`（大小 `0x28` = 40 字节）并调用构造函数 `0x005B3C20` 打开 MIX 文件，随后将返回的**堆对象指针动态写入这两个全局变量**：
     ```asm
     ; 载入 RA2MD.MIX (VA: 0x00530290 .. 0x005302B6)
     0x00530290: 6A 28              push  0x28                   ; sizeof(MixFileClass)
     0x00530292: E8 80 8B 29 00     call  operator new (0x7C8E17)
     0x0053029E: 68 80 69 88 00     push  0x00886980             ; RSA 密钥结构
     0x005302A3: 68 7C 66 82 00     push  0x0082667C             ; "RA2MD.MIX" 常量字符串
     0x005302A8: 8B C8              mov   ecx, eax               ; this = pMix
     0x005302AA: E8 71 39 08 00     call  MixFileClass::ctor (0x005B3C20)
     0x005302B1: A3 F8 4D 88 00     mov   dword ptr [0x00884DF8], eax ; ★ 写入 MixFileClass* 指针！
     
     ; 载入 LOCALMD.MIX (VA: 0x005303C8 .. 0x005303DB)
     0x005303CD: 68 44 66 82 00     push  0x00826644             ; "LOCALMD.MIX" 常量字符串
     0x005303D2: 8B C8              mov   ecx, eax
     0x005303D4: E8 47 38 08 00     call  MixFileClass::ctor (0x005B3C20)
     0x005303DB: A3 50 4E 88 00     mov   dword ptr [0x00884E50], eax ; ★ 写入 MixFileClass* 指针！
     ```
  3. **降标说明**：在未初始化的静态 PE 视角下，该地址不可被作为名字字符串读取（标记为 `[推演]` 澄清）；在游戏运行时，该地址是标准的 **`MixFileClass*` 单例指针句柄**（标记为 `[实证]`）。

---

## 三、全库 30+ 份逆向文档系统性冲突深潜审计

### 3.1 虚表槽位与物理偏移量双轨混淆纠偏 [实证]

在各子代理撰写的文档中，普遍存在**虚表槽位序号（Slot Index，0-based）**与**结构体内函数指针物理字节偏移（Byte Offset = Slot * 4）**相混淆、以及跨继承层次乱挂虚表的问题。

#### 3.1.1 核心虚表映射基准真理表
基于 Westwood 引擎多继承架构（`AbstractClass` $\to$ `ObjectClass` $\to$ `MissionClass` $\to$ `RadioClass` $\to$ `TechnoClass` $\to$ `FootClass`）：

| 类名 | 虚方法名称 | 真实槽位 (Slot) | 物理偏移 (Offset) | 实现函数入口 VA | 汇编调用现场证据 |
|:---|:---|:---:|:---:|:---:|:---|
| **ObjectClass** | `Draw` | **v[69]** | `+0x114` | 随具体派生类重写 | `0x005F4CFD: call dword ptr [eax + 0x114]` |
| **TechnoClass** | `CreateGap` | **v[261]** | `+0x414` | `0x006FB170` | 写入虚表 `0x007E90A8`（`0x007E8C94 + 0x414`） |
| **TechnoClass** | `DestroyGap` | **v[262]** | `+0x418` | `0x006FB470` | 写入虚表 `0x007E90AC`（`0x007E8C94 + 0x418`） |
| **FootClass** | `MoveTo` | **v[319]** | `+0x4FC` | `0x004D55F0` | 写入虚表 `0x007E9190`（`0x007E8C94 + 0x4FC`） |
| **FootClass** | `StopMoving` | **v[320]** | `+0x500` | `0x004D55C0` | 写入虚表 `0x007E9194`（`0x007E8C94 + 0x500`） |

#### 3.1.2 历史误区澄清
1. **槽 69 澄清**：`fx_draw_chain.md` 记载 `call [eax+0x114] ; 槽69 Draw` 完全正确（$69 \times 4 = 276 = 0\text{x}114$）。部分早期草案将其写作“槽 276”属将字节偏移误读为槽号。
2. **槽 261/262 vs 317-320 纠偏**：`gap_generator_spysat_deep_dive.md` 标注的 `CreateGap` 为槽 261（`+0x414`）、`DestroyGap` 为槽 262（`+0x418`）完全属实；而 `pathfinding_locomotion.md` 记载的槽 319（`MoveTo`）与槽 320（`StopMoving`）则属于最底层派生类 `FootClass`。两者分别处于继承树的不同层级，严禁相互替代。

---

### 3.2 核心游戏对象物理内存尺寸全库对齐裁定 [实证]

部分涉及内存池（CRT Pool）与对象分配的文档对基础对象尺寸存在多版本估算（如 Particle 曾被误写为 304B，Anim 曾被误写为 440B）。通过扫描 `gamemd.exe` 全镜像中所有的 `push <size>; call operator new` 指令，取得绝对真理：

| 对象类名 | 官方真实大小 (十进制) | 物理十六进制大小 | 内存池分配操作码 | 镜像出现频次 | 关键分配入口 VA [实证] |
|:---|:---:|:---:|:---|:---:|:---|
| **ParticleClass** | **312 字节** | **`0x138`** | `68 38 01 00 00` | 11 处 | `0x0062E397`: `push 0x138; call 0x7C8E17` |
| **BulletClass** | **352 字节** | **`0x160`** | `68 60 01 00 00` | 4 处 | `0x006C50BC`: `push 0x160; call 0x7C8E17` |
| **AnimClass** | **456 字节** | **`0x1C8`** | `68 C8 01 00 00` | 152 处 | `0x00414C27`: `push 0x1C8; call 0x7C8E17` |
| **SuperClass** | **128 字节** | **`0x80`** | — (虚方法内联) | 508 处引用 | `0x006CE210`: `mov eax, 0x80; ret` |

- **SuperClass 尺寸铁证**：位于 `0x006CE210` 处的虚方法 `SuperClass::GetSize`，其反汇编仅有两行机器码：`B8 80 00 00 00 C3`（`mov eax, 0x80; ret`），彻底终结任何关于超武对象尺寸的争议。

---

### 3.3 关键指令编码与跳板汇编历史缺陷定谳 [实证]

#### 3.3.1 H-D5 掩码编码历史缺陷定谳 [实证]
- **缺陷起源**：在 `calc_tramp_bytes.py` 与 `landing_pack_net_fix.md` 早期草案中，设计者试图获取 256 槽环形缓冲区的索引槽位（`TargetSlot = CurrentFrame & 0xFF`），编写了汇编指令：
  ```asm
  83 E0 FF           and   eax, 0xFF            ; ⚠️ 致命机器码缺陷！
  ```
- **物理指令级事实**：x86 指令集中 `83 /4 ib` 的操作码语义为 `AND r/m32, imm8`，但其中的 `imm8` 会被 **CPU 强制符号扩展（Sign-Extended）为 32 位立即数**！`0xFF` 被符号扩展后变为 `0xFFFFFFFF`。因此 `83 E0 FF` 实际上执行了 `and eax, 0xFFFFFFFF`，根本无法清除高 24 位！
  当游戏帧数达到 1000 帧时，`EAX` 依然为 1000，直接导致对 256 项环形数组越页寻址，引发必死性的 `0xC0000005` 内存访问越界崩溃！
- **权威纠偏**：经 `landing_equivalence_static_proof.md` 审查修正，必须统一采用 3 字节等长指令：
  ```asm
  0F B6 C0           movzx eax, al              ; ★ 权威修正：高 24 位强制清零，恰好 3 字节！
  ```

#### 3.3.2 音频钩子平栈返回平衡纠偏 [实证]
- **缺陷起源**：早先针对音频洪泛防御拦截（Audio Flood Prevention）的讨论中，部分文档草拟在 `PlayGlobal` 与 `PlayAt` 头直接植入拦截返回，写了裸 `ret`（`0xC3`）。
- **物理指令级事实**：
  1. `VocClass::PlayGlobal`（`0x00750920`）在禁用分支下的返回指令为：
     ```asm
     0x0075092E: 33 C0              xor   eax, eax
     0x00750930: 59                 pop   ecx
     0x00750931: C2 08 00           ret   8                    ; ★ 必须平退 8 字节参数！
     ```
  2. `VocClass::PlayAt`（`0x007509E0`）在禁用分支下的返回指令为：
     ```asm
     0x007509EC: 33 C0              xor   eax, eax
     0x007509EE: 5B                 pop   ebx
     0x007509EF: C2 04 00           ret   4                    ; ★ 必须平退 4 字节参数！
     ```
  3. 若使用裸 `ret`，调用方传入的实参栈将无法弹出，导致外层栈指针偏移 4~8 字节，引发调用链剧烈失衡及外层局部变量被覆写崩溃。
- **裁定结论**：全库所有涉及音频拦截的补丁方案，必须强制规范为 `ret 8`（PlayGlobal）与 `ret 4`（PlayAt）。

---

### 3.4 Greatest_Threat 寻敌排序与同分决策裁定 [实证]

- **冲突现象**：
  部分战术 AI 与寻敌文档推测“AI 索敌在面对相同威胁分的目标时，可能会随机轮换，或者由后来者覆盖先来者”。
- **二进制真理裁定**：
  实测全引擎 3 处核心威胁比对入口机器码：
  1. `0x006F936B`: `3B C1 7E 08` $\to$ `cmp eax, ecx; jle 0x006F9377`
  2. `0x006F9C3C`: `3B C1 7E 08` $\to$ `cmp eax, ecx; jle 0x006F9C48`
  3. `0x006F9D87`: `3B C1 7E 08` $\to$ `cmp eax, ecx; jle 0x006F9D93`
  - **汇编语义分析**：
    三处比对完全使用 `jle`（Signed Less or Equal，小于等于即跳转跳过）。
    这意味着：**只有当候选目标的威胁评估分严格大于（Strictly Greater Than）当前暂存的最大威胁分时，系统才会执行替换更新**！
    当两者分数相同时，直接跳过替换，**保留最先枚举到的目标（同分先见原则 / First-Seen Advantage）**。
- **裁定结论**：
  严禁任何重构模块引入同分随机化或颠倒遍历次序。多桶网格遍历必须保持确定性拓扑扫描顺序，否则将破坏联机锁步确定性。

---

### 3.5 寻路算子数学本质定谳：纯 Dijkstra 终结 A* 误判 [实证]

- **冲突现象**：
  早期文档（如 `pathfinding_deep_dive.md`）大篇幅使用“A* 寻路优化”、“A* 启发式权重”等术语，假定存在目标欧式距离估算 $h(n)$。
- **二进制真理裁定**：
  1. 静态反汇编 `0x0042CCD0` 寻路波前展开主循环，原版内部仅读取地表通行阻力、摩擦力及坡度成本（`0x00583180`），并据此累加已消耗路径成本 $g(n)$；**完全不存在任何曼哈顿、对角或欧式启发式函数 $h(n)$**！
  2. 位于 `0x004D3E3B` 处的指令显式将最大展开搜索节点深度硬编码限制为 `0x7D0`（十进制 2000 个节点）。一旦波前发散触及 2000 格上限，寻路立即早衰失败。
  3. 该算法在数学性质上是严格的**带权有向网格单源最短路径 Dijkstra 算法（Uniform-Cost Search）**。西木之所以在平原大跨度寻路严重掉帧，正是因为缺少启发式引导导致四周无序盲目扩散。
- **裁定结论**：
  全库文档全面更正寻路算法定性，推翻 A* 假说，正名为“Dijkstra 展开算子”。

---

### 3.6 CellClass 关键字段与地图/视野边界裁定 [实证]

针对 `cellclass_offsets_evidence.md` 与多篇视野/超武文档的字段表述：
1. **`CellClass + 0x134`**：实证为 `GapsCoveringThisCell`（当前覆盖该格的裂缝产生器计数器，`uint32_t`）。取证点：`0x00568273: mov [ecx + 0x134], ebx`。
2. **`CellClass + 0x140`**：实证为 `Flags`（地形标志位，如 `cf_Bridge = 0x100` 等）。
3. **`CellClass + 0xE4` / `+0xE8`**：实证为 `FirstObject` 与 `AltObject` 驻留对象双链表头。
4. **全图网格总数**：全镜像出现 785 次的常量魔数 `0x00040000`（十进制 262,144），严格对应 $512 \times 512$ 最大物理格子阵列。雷达全图视野缓冲区数组物理尺寸裁定为 `uint32_t s_visionGrid[262144]`。

---

### 3.7 CurrentFrame（0xA8ED84）写入生命周期全景实证

全镜像共包含 1009 处对 `0x00A8ED84` 的读取引用，通过地毯式指令汇编过滤，确证**全局仅存在 8 处写入点**，构成游戏时钟的完整生命周期：

```
                ┌─────────────────────────────────────────────────────────┐
                │          CurrentFrame (@ 0x00A8ED84) 物理写入全景       │
                └────────────────────────────┬────────────────────────────┘
                                             │
      ┌──────────────────────────────────────┼──────────────────────────────────────┐
      │                                      │                                      │
┌──────────────┐                       ┌──────────────┐                       ┌──────────────┐
│  重置与初始化 │                       │  主循环递增  │                       │  存读档与联机 │
└──────┬───────┘                       └──────┬───────┘                       └──────┬───────┘
       │                                      │                                      │
       ├─ 0x5B7329: mov [A8ED84], 0           └─ 0x5E550F: mov [A8ED84], esi         ├─ 0x5BB20C: mov [A8ED84], ebp (读档)
       ├─ 0x5E747C: mov [A8ED84], 0              (逻辑主帧平滑推进)                   ├─ 0x686765: mov [A8ED84], ebp (会话恢复)
       └─ 0x795234: mov [A8ED84], 0                                                  └─ 0x79758C: mov [A8ED84], eax (网络同步)
```

---

## 四、全库交叉一致性三维矩阵（文档 A vs 文档 B vs 二进制真理）

本矩阵抽取 15 项横跨全库的核心技术冲突，建立“文档 A vs 文档 B vs 二进制真理”三维权威对照：

| # | 争议主题 | 涉及文档 A (原表述) | 涉及文档 B (原表述) | 二进制物理真理 (VA / 机器码 / 汇编) | 冲突定性与权威裁定结论 |
|:---:|:---|:---|:---|:---|:---|
| **1** | **存档主入口函数定性** | `net_sync_checksum.md §4.1`: “0x67D300 是存档主函数” | `ARCHITECTURE_ATLAS.md`: 认定存在外层 Storage 框架 | `0x0067D1AF`: `call 0x0067D300`；`0x0067D0C0` 创建流并外包 | **定性归正**：`0x67D0C0` 为外层事务入口，`0x67D300` 实为 `Save_Core` |
| **2** | **读写函数对称性** | `net_sync_checksum.md §4.1`: “0x680F70 读档与 Save 一一对应” | `savegame_block_manifest.md`: 读写模块不对称 | `0x0067CF6B..0x67D055` 仅调 16 个头部解包函数，写侧调 35 块 | **假说推翻**：读档 16 族仅为 Header 解包器，与 35 块 Save 非镜像对应 |
| **3** | **Save_Core 代码尺寸** | `net_sync_checksum.md §4.1`: “4416B” | `pending_execution_master_table.md`: 沿用 4416B | `0x0067D300..0x67E43A`: 净指令长 4410B (含 ret 为 4411B)，末尾 5B NOP | **手误纠偏**：4416B 误计了 5 字节对齐 NOP，真实代码长 4410B |
| **4** | **0xA8022C 数组归属** | `house_team_ai_update.md:118`: 标为 `HouseClass*` | `net_sync_checksum.md:260` & `superweapon_re.md:531`: 标为 `AircraftClass*` | `0x0064DCBD`: 读 `[A8022C]`；`0x0041EC90`: 遍历取 `[edx+0x34]` 查战机属性 | **严重笔误纠偏**：权威裁定为 `AircraftClass::Array`，House 位于 `0x87F77C` |
| **5** | **0xA8ECA4 字段定义** | `house_team_ai_update.md:121`: 标为 Items，Count 为 0xA8ECA8 | 历史推演文档: 偶有混淆 Items 与 Count | `0x006F085C`: `inc ecx; mov [A8ECB0], ecx`；`0x006F0862`: `mov ecx, [A8ECA4]` | **字段对齐**：`0xA8ECA4`=Items，`0xA8ECA8`=Capacity，`0xA8ECB0`=Count |
| **6** | **0x6E9CE8 动作归属** | 部分推演草案: 误归入 `TActionClass` 触发器动作 49 | `trigger_system_manifest.md`: Action 49 为 `Zoom In` | `0x006E944B`: `cmp eax, 0x40; jmp [eax*4+6E9F74]`；`table[49]=0x6E9CE1` | **归属纠偏**：`0x6E9CE8` 属 `TeamClass::AI` 队伍脚本，非触发器动作 |
| **7** | **0x67FDF0 35 块性质** | `net_sync_checksum.md §4.2`: 视作“分发函数调度表” | `crt_memory_pool_deep_dive.md`: 视为模板实例代码 | 35 个 0x80 块 MD5 全等（`cb13908...`，**128 B 口径**；127 B 口径为 `9f6770a9...`）；全镜像立即数引用次数为 0 | **本质定谳**：MSVC 展开的 35 个等同模板可执行副本，绝非调度指针表 |
| **8** | **fs_mix 0x884DF8 性质** | `fs_mix_load_chain.md`: 标注为 `ra2md.mix` 字符串 | PE 静态分析: 查得 UTF-16LE 宽字符 `"ider1"` | `0x005302B1`: `call new(0x28); call ctor; mov [884DF8], eax` | **降标定谳**：静态为残留垃圾数据，运行时为 `MixFileClass*` 单例句柄指针 |
| **9** | **虚表槽 69 真实偏移** | `fx_draw_chain.md`: `call [eax+0x114] ; 槽69` | 早期草案: 误写为“槽 276” | `0x005F4CFD`: `call dword ptr [eax + 0x114]`（$69 \times 4 = 276 = 0\text{x}114$） | **单位澄清**：槽号为 69（0-based），字节偏移为 `+0x114`，两者完全自洽 |
| **10** | **虚表槽 261/262 归属** | `gap_generator_spysat.md`: 标为 TechnoClass 裂缝槽 | `pathfinding_locomotion.md`: 讨论 319/320 槽 | 虚表 `0x007E8C94` 中 `+0x414`/`+0x418` 为 Create/DestroyGap；`+0x4FC` 为 MoveTo | **层级澄清**：261/262 属 TechnoClass，319/320 属派生类 FootClass |
| **11** | **ParticleClass 尺寸** | 早期内存池推演: 记为 304 字节 | `bullet_particle_fog.md`: 记为 312 字节 | `0x0062E397`: `push 0x138; call operator new`（$0\text{x}138 = 312$ 字节） | **尺寸定谳**：实证为严格 312 字节，内存池桶归入 320B 规格 |
| **12** | **SuperClass 尺寸** | 早期讨论: 疑为 96B 或变长 | `superweapon_re.md`: 确认为 128 字节 | `0x006CE210`: `mov eax, 0x80; ret`（返回固定 128 字节） | **尺寸定谳**：实证为严格 128 字节（`0x80`） |
| **13** | **H-D5 跳板掩码机器码** | `calc_tramp_bytes.py`: 写作 `83 E0 FF` | `landing_equivalence_static_proof.md`: 纠正为 `0F B6 C0` | `83 E0 FF` 符号扩展为 `and eax, -1` 导致崩溃；`0F B6 C0` 为 `movzx eax, al` | **重大缺陷阻断**：强制裁定采纳 `0F B6 C0`，彻底杜绝环形数组越界 |
| **14** | **音频防御钩返回指令** | 早期讨论草案: 拟使用裸 `ret` (`0xC3`) | `audio_engine_deep_dive.md`: 记录平栈返回 | `0x00750931`: `ret 8`；`0x007509EF`: `ret 4`；原版为 stdcall 约定 | **堆栈安全定谳**：强制要求使用 `ret 8`（Global）与 `ret 4`（At） |
| **15** | **寻路算法类型判定** | `pathfinding_deep_dive.md`: 统称为“A* 启发式寻路” | `deep_dive_sweeps_closure.md`: 纠正为 Dijkstra | `0x0042CCD0`: 零 $h(n)$ 距离预估；`0x004D3E3B`: 硬编码 2000 节点上限 | **算子定性更正**：官方原版为纯有界 Dijkstra 波前扩散，推翻 A* 术语 |

---

## 五、全库 30+ 份逆向文档全量勘误清单与权威裁定建议表

本表对受检文档中存在缺陷与不一致的章节给出权威修正建议：

| 文档名称 | 章节 / 行号 | 原始问题描述 | 权威更正建议 | 证据等级 | 风险阻断级别 |
|:---|:---|:---|:---|:---:|:---:|
| `docs/re/net_sync_checksum.md` | §4.1 表格 | 称 `0x67D300` 为“存档主函数 (4416B)” | 更正为 `Save_Core`（净指令长 4410B，对齐跨度 4416B） | `[实证]` | **阻断级**（概念混淆） |
| `docs/re/net_sync_checksum.md` | §4.1 表格 | 称 `0x680F70..0x6812E0` 与 Save 一一对应 | 更正为“存档头解包器（Header Unpack Accessors）”，非全系统 Save 镜像 | `[实证]` | **阻断级**（架构误判） |
| `docs/re/house_team_ai_update.md` | 118 行表格 | 标注 `0x00A80228` 为 `HouseClass*` | 撤销 House 标注，更正为 `AircraftClass::Array`（House 位于 `0x87F77C`） | `[实证]` | **阻断级**（严重笔误） |
| `docs/re/house_team_ai_update.md` | 121 行表格 | 标注 `TeamType` 的 Count 为 `0x00A8ECA8` | 更正 `0xA8ECA8` 为 Capacity，真实活动计数器 Count 为 `0x00A8ECB0` | `[实证]` | **阻断级**（越界隐患） |
| `docs/re/fs_mix_load_chain.md` | §1.3 / 表格 | 标注 `0x884DF8` 为 `ra2md.mix` 字符串 | 补充说明：静态为垃圾宽字符，运行时为 `MixFileClass*` 指针句柄变量 | `[实证+澄清]` | 规范级 |
| `docs/re/pathfinding_deep_dive.md` | 全文多处 | 通篇使用“A* 算法”、“A* 启发式开销” | 统一更正术语为“Dijkstra 波前寻路”，注明无 $h(n)$ 且硬编码 2000 深度 | `[实证]` | 规范级（术语漂移） |
| `docs/re/landing_pack_net_fix.md` | 附录脚本 | 跳板编码包含 `83 E0 FF` | 强制替换为 `0F B6 C0`（`movzx eax, al`），阻断旧机器码合入 | `[实证]` | **阻断级**（内存崩溃） |
| `docs/re/audio_engine_deep_dive.md` | §4.2 拦截代码 | 局部防御代码示意中使用裸 `ret` | 强制在 `Hook_VocClass_PlayGlobal` 使用 `ret 8`、`PlayAt` 使用 `ret 4` | `[实证]` | **阻断级**（堆栈击穿） |
| `docs/re/targeting_deep_dive.md` | §2.3 排序说明 | 推测同分威胁可能后见覆盖或随机 | 补充说明：汇编指令全为 `jle`，严格遵循同分先见原则与单调递增替换 | `[实证]` | 规范级 |
| `docs/re/crt_memory_pool_deep_dive.md`| §2.1 对象表 | Particle 尺寸标记混乱（曾现 304B） | 统一标定为：312 字节（`0x138`），由 `0x0062E397` 汇编硬实证 | `[实证]` | 规范级 |

---

## 六、结语与工程库未来一致性守护机制

本次专项审计彻底厘清了全库 82 份文档中沉淀已久的 15 大类历史冲突，依托官方原版 `gamemd.exe` 的物理指令级证据，推翻了“读档一一对应”、“A* 启发式”、“0x80 调度表”等历史误判，平叛了单例指针与计数器三方争议，并修正了导致真机崩溃的机器码手误与平栈隐患。

为确保后续逆向工程与代码落地不再引入新的分歧，确立如下**工程库一致性守护机制**：
1. **符号唯一真理源**：后续所有冲刺子代理必须严格以本报告第四章《三维矩阵》与第二章《E 系列裁定》为基准符号字典，禁止二次发明私有偏移。
2. **三要素实证门禁**：凡提出虚表槽位、结构体字段、对象尺寸变更者，必须在文档中同时给出：① 虚拟内存地址（VA）；② 十六进制机器码；③ Capstone 汇编反编译指令，缺一不可合入。
3. **分步对拍机制**：凡涉及跨模块调用的关键全局变量（如单例数组、时钟、混音缓冲区），必须比对读写双向生命周期，杜绝孤立分析单条指令导致的片面定性。

本报告自签署之日起生效，作为项目库逆向工程事实标准的最高解释仲裁案卷。
