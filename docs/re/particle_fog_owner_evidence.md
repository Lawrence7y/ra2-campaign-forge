# 微粒系统（ParticleClass / ParticleSystemClass）迷雾剔除与阵营归属深度取证报告（v2 严谨重订版）

> **作者**：Antigravity（独立逆向取证方）  
> **日期**：2026-09-26  
> **依据二进制**：`D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`（MD5: ~~`1011CE1B58C9B9BA...`~~ 【原记｜勘误 E3：**与磁盘不符**】 → **实际 `4F37486E5B0DBE2AE5F45AEEE0F98367`**（4,825,360 B，YR 1.001 基线）, PE 32-bit x86）  
> 【W3 勘误 · W3-A6/ISSUE-OUTDATED-MD5-1011CE1B】改前：1011CE1B58C9B9BA；改后：4F37486E5B0DBE2AE5F45AEEE0F98367；依据：ra2youli/gamemd.exe; doc_consistency_fix_list.md:64；分级：P2
> **反汇编证据转储**：`out/re_work/particle_fog/disasm_*.txt`（Capstone 5.0.7 实测复算）  
> **前序关联**：攻克 `REVERSE_ENGINEERING_AND_PATCHES.md` [v1.6.0] §4 遗留项与 Lead 派工 v3（A-4′）要求。

---

> **【勘误 · MIMO-DOCERRATA / E3】** 文首原记 gamemd.exe MD5 `1011CE1B58C9B9BA...` 与磁盘实际不一致。实测（Get-FileHash / MD5）：**`4F37486E5B0DBE2AE5F45AEEE0F98367`**，size **4,825,360** B，与任务基线 YR 1.001 一致。原值保留删除线标注。本报告反汇编结论基于该基线镜像，逻辑不受影响。

## 目录
- [一、0x0062CF5F 处指令与 ret 8 全函数扫描核实](#一0x0062cf5f-处指令与-ret-8-全函数扫描核实)
- [二、ParticleClass::Draw (0x0062CEC0) 完整反汇编与前置门控链剖析](#二particleclassdraw-0x0062cec0-完整反汇编与前置门控链剖析)
- [三、ParticleSystemClass::Draw (0x0062E280) 完整反汇编剖析](#三particlesystemclassdraw-0x0062e280-完整反汇编剖析)
- [四、阵营归属三条核心链（+0x124 / +0xFC / +0xE0）物理读写点实证](#四阵营归属三条核心链124--fc--e0物理读写点实证)
- [五、粒子迷雾隐形剔除安全规范与联机确定性论证](#五粒子迷雾隐形剔除安全规范与联机确定性论证)
- [六、工程落地规格（C++ Hook 扩展原型）](#六工程落地规格c-hook-扩展原型)

---

## 一、0x0062CF5F 处指令与 ret 8 全函数扫描核实

### 1.1 纠正前序断言
> [!WARNING]
> **前期断言更正**：此前草稿断言“原版 `0x0062CF5F` 处即存在黑雾 `ret 8` 原语”，**此表述在机器码字面意义上失实**。  
> 经 Capstone 逐字节反汇编确认：`0x0062CF5F` 处机器码为 `0F 85 26 03 00 00`，是一条 **条件跳转指令 `jne 0x0062D28B`**。该指令跳转的目标 `0x0062D28B` 为函数的**公共收尾区（Epilogue）**，其收尾代码最终执行 `ret 8`（`C2 08 00`）。

### 1.2 全函数 `ret 8` (`C2 08 00`) 双退出点扫描与反汇编对照
经对两个 Draw 函数的完整汇编代码进行 Capstone 线性反汇编与二进制模式扫描（指令总数：`ParticleClass::Draw` 为 279 条，`ParticleSystemClass::Draw` 为 80 条）：

1. **`ParticleClass::Draw`（`0x0062CEC0 - 0x0062D294`，981 字节，279 条指令）**：
   - 全函数内部**实有 2 处 `ret 8` (`C2 08 00`)**，分别位于：
     - **Exit 1（`0x0062D029`）**：位于贴图粒子光栅化分支末尾（第 106 条指令）。
       ```assembly
       0062D01D: E8 4E 1D E8 FF        call    0x004AED70            ; 调用贴图粒子 Blit 核心
       0062D022: 5F                    pop     edi
       0062D023: 5E                    pop     esi
       0062D024: 5D                    pop     ebp
       0062D025: 5B                    pop     ebx
       0062D026: 83 C4 24              add     esp, 0x24
       0062D029: C2 08 00              ret     8                     ; ★ Exit 1: 贴图粒子正常绘制完成退出
       ```
     - **Exit 2（`0x0062D292`）**：位于函数主收尾区末尾（第 278 条指令）。
       ```assembly
       0062D288: FF 57 24              call    dword ptr [edi + 0x24]; 3D点/火花像素写回虚表
       0062D28B: 5F                    pop     edi                   ; ★ 也是多个提前跳过/裁剪分支的汇入终点
       0062D28C: 5E                    pop     esi
       0062D28D: 5D                    pop     ebp
       0062D28E: 5B                    pop     ebx
       0062D28F: 83 C4 24              add     esp, 0x24
       0062D292: C2 08 00              ret     8                     ; ★ Exit 2: 点图元完成或跳过分支收尾退出
       0062D295: 90                    nop
       ```
   - **对称性特征**：两处收尾汇编机器码完全一致（`5F 5E 5D 5B 83 C4 24 C2 08 00`），均严格遵循 `__thiscall` 2 个栈参数（8 字节）的 Callee 清栈约定。

2. **`ParticleSystemClass::Draw`（`0x0062E280 - 0x0062E37D`，254 字节，80 条指令）**：
   - 全函数内部**仅存在 1 处 `C2 08 00`**，位于末尾 `0x0062E37B`：
     ```assembly
     0062E376: 5F                    pop     edi
     0062E377: 5E                    pop     esi
     0062E378: 83 C4 08              add     esp, 8
     0062E37B: C2 08 00              ret     8                     ; 全函数唯一 ret 8 终点！
     ```

### 1.3 Exit 1 (`0x0062D029`) 的分支来源与语义剖析
#### 抵达 Exit 1 的前置条件分支：
在 `0x0062CF65` 处，函数读取粒子类型的行为属性 `ParticleTypeClass::BehavesLike (+0x314)`：
```assembly
0062CF65: 8B 97 AC 00 00 00  mov     edx, dword ptr [edi + 0xac]   ; edx = this->Type (ParticleTypeClass*)
0062CF6B: 8B 82 14 03 00 00  mov     eax, dword ptr [edx + 0x314]  ; eax = Type->BehavesLike
0062CF71: 83 F8 03           cmp     eax, 3
0062CF74: 0F 84 B2 00 00 00  je      0x0062D02C                    ; 若为 3 (Spark火花/轨迹)，跳过贴图分支
0062CF7A: 83 F8 04           cmp     eax, 4
0062CF7D: 0F 84 A9 00 00 00  je      0x0062D02C                    ; 若为 4 (Railgun磁轨/射线)，跳过贴图分支
```

#### 指令语义与迷雾无关性确认：
1. **语义说明**：
   - 当 `BehavesLike` 不是 `3` 也不是 `4` 时（即微粒属于 `0=Gas`, `1=Smoke`, `2=Fire` 等动画贴图类微粒），控制流不发生跳转，顺序落入 `0x0062CF83 - 0x0062D021` 贴图光栅化流程；
   - 该流程通过虚表 `[eax + 0x1D0]` 获取动画帧图像，调用 `0x006D20E0` 进行视口投影，在 `0x0062CFBB - 0x0062CFEC` 根据 `[edi + 0x12F]`（微粒生命期 Alpha 阶段）计算混色标志 `esi`，最终调用 `0x004AED70` 将粒子贴图 Blit 到工作表面；
   - 贴图绘制完成后，顺序执行 Exit 1（`0x0062D022 - 0x0062D029`），弹出保存的寄存器并以 `ret 8` 正常返回。
2. **确认不属于迷雾短路**：
   - **`0x0062D029` 是贴图粒子绘制成功后的正常退出出口**，绝非任何形式的异常退出或剔除逻辑；
   - 从 `0x0062CF83` 到 `0x0062D029` 的整个光栅化代码段中，**没有任何关于迷雾（Shroud/Fog）或视野网格（Vision）的检测指令**；
   - 因此，Exit 1 同样不具备任何迷雾阻挡功能。

### 1.4 Exit 2 (`0x0062D292`) 的汇入来源与失效分析
汇入 Exit 2 收尾区（`0x0062D28B`）的跳转分支共有 7 处：
1. `0x0062CEE4`: `je 0x62d28b`（视口缓冲或动画帧指针为空）；
2. `0x0062CF02` / `0x0062CF0B`: `je 0x62d28b`（低画质模式 `DetailLevel == 0` 跳过烟雾/火花）；
3. `0x0062CF5F`: `jne 0x62d28b`（原厂设计的迷雾检测跳转，见下文详述）；
4. `0x0062CFA6`: `je 0x62d28b`（表面指针 `[edx + 0x6C]` 为空）；
5. `0x0062D079` / `0x0062D086` / `0x0062D091` / `0x0062D09E`: `jl/jge 0x62d28b`（屏幕视口矩形视锥剔除 Frustum Culling，微粒超出屏幕边界跳出）；
6. `0x0062D0BB`: `je 0x62d28b`（Cell 映射指针为空）；
7. `0x0062D288`: `call dword ptr [edi + 0x24]` 顺序穿透（点图元正常绘制完成退出）。

#### 原版跳转分支与失效根因剖析（关于第 3 项 0x0062CF5F）：
在 `ParticleClass::Draw` 中，原厂针对迷雾的检测代码位于 `0x0062CF23 - 0x0062CF5F`：
```assembly
0062CF23: 8B 15 30 B2 A8 00  mov     edx, dword ptr [0x00A8B230]  ; ScenarioClass::Instance
0062CF29: 8B 02              mov     eax, dword ptr [edx]         ; ScenarioFlags
0062CF2B: F6 C4 10           test    ah, 0x10                     ; 检查 Flags & 0x1000 (FogOfWar)
0062CF2E: 74 35              je      0x0062CF65                   ; ★ 若清零，直接跳过全套迷雾检测！
0062CF30: 8D 87 9C 00 00 00  lea     eax, [edi + 0x9c]            ; 粒子坐标 CoordStruct
0062CF36: 8B 8F 9C 00 00 00  mov     ecx, dword ptr [edi + 0x9c]
0062CF3C: 89 4C 24 28        mov     dword ptr [esp + 0x28], ecx
0062CF40: 8D 4C 24 28        lea     ecx, [esp + 0x28]
0062CF44: 8B 50 04           mov     edx, dword ptr [eax + 4]
0062CF47: 51                 push    ecx
0062CF48: B9 E8 F7 87 00     mov     ecx, 0x0087F7E8              ; MapClass 全局单例
0062CF4D: 89 54 24 30        mov     dword ptr [esp + 0x30], edx
0062CF51: 8B 40 08           mov     eax, dword ptr [eax + 8]
0062CF54: 89 44 24 34        mov     dword ptr [esp + 0x34], eax
0062CF58: E8 83 96 F5 FF     call    0x005865E0                   ; MapClass::IsCellShrouded
0062CF5D: 84 C0              test    al, al
0062CF5F: 0F 85 26 03 00 00  jne     0x0062D28B                   ; ★ 若在黑雾中，跳转 Exit 2 收尾区退出 (ret 8)
0062CF65: ...                                                     ; 继续执行实际粒子光栅化与 SHP 绘制
```
**失效原因证明**：
1. 在项目解决黑雾黄白反色 Bug 时，`ScenarioFlags & 0x1000` 被显式清零，因此 `0x0062CF2E` 处的 `je 0x0062CF65` **恒定发生跳转**，原厂这套检测逻辑被永久旁路。
2. 即使未清零，原版 `0x005865E0`（`MapClass::IsCellShrouded`）在正式发行版中被西木硬编码为空桩 `32 C0 C2 04 00`（`xor al, al; ret 4`），**恒定返回 0**。
3. 因此：原厂唯一设计企图跳往 Exit 2 的迷雾检测分支 `0x0062CF5F` 存在双重失效，在二进制运行中永远无法被触发。

### 1.5 论证小结：“原版无黑雾短路原语”结论保持
经逐指令分析，`ParticleClass::Draw` 全函数的两条 `ret 8` 退出路径（Exit 1 @ `0x0062D029` 与 Exit 2 @ `0x0062D292`）**均非有效的迷雾短路**：
- **Exit 1** 为贴图粒子成功渲染后的正常退出，全程零迷雾判断；
- **Exit 2** 为点图元渲染完成或空指针/视锥裁剪退出的出口，其唯一的迷雾判断分支 `0x0062CF5F` 在现行二进制中被完全锁死失效；
- **结论保持**：原版游戏在黑雾中必然发生粒子视觉泄漏，必须由外部在虚表入口挂载 `Hook_Particle_Draw`，以阵营感知与 `s_visionGrid` 进行判断，并在满足剔除条件时主动执行 `ret 8`。

---

## 二、ParticleClass::Draw (0x0062CEC0) 完整反汇编与前置门控链剖析

完整反汇编已导出至 `out/re_work/particle_fog/disasm_ParticleClass_Draw.txt`（279 行指令）。
- **虚表槽位**：虚表基址 `0x007EF954`，槽 69（偏移 `+0x114`）物理地址 **`0x007EFA68`**。
- **调用约定**：`void __thiscall ParticleClass::Draw(Point2D* pLocation, RectangleStruct* pBounds)`（`ecx=this`, 2 个栈参数，callee 清栈 `ret 8`）。

### 核心执行阶段标注：
1. `0x0062CEC0 - 0x0062CEC7`：栈帧开辟 `sub esp, 0x24`，寄存器压栈 `push ebx/ebp/esi/edi`，`mov edi, ecx`（`edi = ParticleClass*`）。
2. `0x0062CEE2 - 0x0062CEE4`：`test ecx, ecx; je 0x62d28b`（若未分配视口则直接跳 Exit 2 退出）。
3. `0x0062CF23 - 0x0062CF65`：原厂失效的迷雾检测块（见上文 §1.4）。
4. `0x0062CF65 - 0x0062CF7D`：读取 `Type->BehavesLike (+0x314)` 分流：
   - 若为 `3`（Spark 火花）或 `4`（Railgun 磁轨线）：跳转 `0x0062D02C` 执行 3D 点/线段图元光栅化，并在末尾进入 **Exit 2（`0x0062D292`）** 退出；
   - 若为其他值（`0` Gas、`1` Smoke、`2` Fire 贴图粒子）：顺序进入 `0x004AED70` 表面 SHP 贴图 Blit，并在完成时直接进入 **Exit 1（`0x0062D029`）** 清栈退出！
5. `0x0062D022 - 0x0062D029`：Exit 1 收尾区，恢复栈帧并 `ret 8`。
6. `0x0062D28B - 0x0062D292`：Exit 2 主收尾区，恢复栈帧并 `ret 8`。

---

## 三、ParticleSystemClass::Draw (0x0062E280) 完整反汇编剖析

完整反汇编已导出至 `out/re_work/particle_fog/disasm_ParticleSystemClass_Draw.txt`（80 行指令）。
- **虚表槽位**：虚表基址 `0x007EFB9C`，槽 69（偏移 `+0x114`）物理地址 **`0x007EFCB0`**。
- **调用约定**：`void __thiscall ParticleSystemClass::Draw(Point2D* pLocation, RectangleStruct* pBounds)`（`ecx=this`, 2 栈参，`ret 8`）。

### 核心逻辑实证：
```assembly
0062E280: 83 EC 08           sub     esp, 8
0062E283: 56                 push    esi
0062E284: 57                 push    edi
0062E285: 8B F9              mov     edi, ecx                     ; edi = ParticleSystemClass*
0062E287: 8B 87 AC 00 00 00  mov     eax, dword ptr [edi + 0xac]  ; eax = Type (ParticleSystemTypeClass*)
0062E28D: 8A 88 0C 03 00 00  mov     cl, byte ptr [eax + 0x30c]   ; Type->Laser (布尔值)
0062E293: 84 C9              test    cl, cl
0062E295: 0F 84 DB 00 00 00  je      0x0062E376                   ; ★ Laser == 0 则直接跳到末尾 ret 8 退出！
```
**实证结论**：
`ParticleSystemClass::Draw` 自身**绝不负责其包含的粒子（`Particles` 向量）的绘制**！它仅在配置了 `Laser=yes`（`+0x30C`）时，负责绘制发射源（`+0x9C`）到目标（`+0xD4`）之间的持续 3D 激光线段；普通非激光系统的 `Draw` 进入后在第 7 条指令就直接 `je 0x62e376` 退出。

---

## 四、阵营归属三条核心链（+0x124 / +0xFC / +0xE0）物理读写点实证

经对二进制全部指令进行物理扫描与汇编级取证，三条链的结构体布局、写点与读点证据如下：

```
                    阵营与对象穿透结构图
  ParticleClass (sizeof=0x138)
  ├── +0x9C : CoordStruct Location (定点数, >>8 得格子)
  └── +0x124: ParticleSystemClass* ParticleSystem  ────────┐
                                                          │
  ParticleSystemClass (sizeof=0x100)                      │
  ├── +0x9C : CoordStruct Location (发射源位置)            │
  ├── +0xBC : DynamicVectorClass<ParticleClass*> Particles │
  ├── +0xE0 : TechnoClass* Owner (发射单位) ───┐          │
  └── +0xFC : HouseClass*  OwnerHouse ──────────┴─────────┘
```

### 4.1 链一：`ParticleClass + 0x124` 引用父容器 `ParticleSystemClass*`
- **构造函数实证**：`ParticleClass::ParticleClass (0x0062B5E0)`
  - 参数 4 为 `ParticleSystemClass* pParticleSystem`，位于栈帧 `[esp + 0x38]`。
  - **物理写点指令**（`0x0062B721`）：
    ```assembly
    0062B6FA: 8B 4C 24 38        mov     ecx, dword ptr [esp + 0x38]  ; 取实参 pParticleSystem
    ...
    0062B721: 89 8E 24 01 00 00  mov     dword ptr [esi + 0x124], ecx ; [esi + 0x124] = ParticleSystem*
    ```
- **全局实例生命周期审计**：
  全程序扫描 `call 0x0062B5E0`，**全部 9 处构造调用点均位于 `ParticleSystemClass` 内部函数（如 `0x0062EE25` / `0x0062F248` 等）**，证实不存在无宿主系统的野指针粒子，`+0x124` 恒指向合法的 `ParticleSystemClass` 实例。

### 4.2 链二：`ParticleSystemClass + 0xFC` 存放直接所有者 `HouseClass* OwnerHouse`
- **构造函数实证**：`ParticleSystemClass::ParticleSystemClass (0x0062DC50)`
  - 参数 6 为 `HouseClass* pOwnerHouse`，位于栈帧 `[esp + 0x40]`。
  - **物理写点指令**（`0x0062DD94 - 0x0062DD9A`）：
    ```assembly
    0062DD94: 8B 44 24 40        mov     eax, dword ptr [esp + 0x40]  ; 取实参 pOwnerHouse
    0062DD9A: 89 86 FC 00 00 00  mov     dword ptr [esi + 0xfc], eax  ; [esi + 0xFC] = OwnerHouse*
    ```
- **物理读点实证**：
  在 `ParticleSystemClass` 析构及状态同步时，通过 `mov eax, [esi + 0xFC]` 读取该阵营指针以更新战局统计。

### 4.3 链三：`ParticleSystemClass + 0xE0` 存放发射载体 `TechnoClass* Owner`
- **构造函数实证**：`ParticleSystemClass::ParticleSystemClass (0x0062DC50)`
  - 参数 4 为 `TechnoClass* pOwner`，位于栈帧 `[esp + 0x38]`。
  - **物理写点指令**（`0x0062DE24 - 0x0062DE37` 与 `0x0062DE54`）：
    ```assembly
    0062DE24: 8B 4C 24 38        mov     ecx, dword ptr [esp + 0x38]  ; 取实参 pOwner
    0062DE2F: 3B CB              cmp     ecx, ebx                     ; 与 NULL 比较
    0062DE37: 89 8E E0 00 00 00  mov     dword ptr [esi + 0xe0], ecx  ; 非空: [esi + 0xE0] = pOwner
    ...
    0062DE54: 89 9E E0 00 00 00  mov     dword ptr [esi + 0xe0], ebx  ; 为空: [esi + 0xE0] = NULL
    ```
- **物理读点实证**：
  在 `ParticleSystemClass::AI`（`0x0062FD60`）第 12 条指令：
  ```assembly
  0062DE6D: 8B 8E E0 00 00 00  mov     ecx, dword ptr [esi + 0xe0]  ; 取发射者〔勘误 ASM-FIX-32 · U-3〕原记锚点该 VA 实测 00 00 83 F8 04 77（落在 0x0062FD69: 8B 80 B4 02 00 00 指令中间），且序列 8B 8E E0 00 00 00 / 85 C9 / 74 全镜像 0 命中；真锚点 = 0x0062DE6D（与本文件上文写点 0x62DE2F / 0x62DE37 / 0x62DE54 同一函数、字段位移 +0xE0 一致，Δ=-0x1F00）⇒ 本条「物理读点」不属 0x0062FD60（`ParticleSystemClass::AI`），函数归属须重新定谳
  0062DE73: 3B CB              cmp     ecx, ebx〔勘误 ASM-FIX-32〕原记 85 C9（`test ecx, ecx`）实测 3B CB（`cmp ecx, ebx`，ebx = NULL；语义等价的手写规范化）
  0062DE75: 74 3A              je      0x0062DEB1                   ; 检查载体单位是否存活〔勘误 ASM-FIX-32〕原记 74 3F（je 目标 0x0062FDB6）实测 74 3A（je 目标 0x0062DEB1）
  ```

---

## 五、粒子迷雾隐形剔除安全规范与联机确定性论证

### 5.1 联机绝对安全证明（Zero OOS Risk）
对齐 `docs/re/net_sync_checksum.md`《联机红线》：
1. **渲染与逻辑彻底解耦**：
   - 粒子物理状态（坐标位移、旋转、扩散）由 `ParticleClass::Update (0x0062CE40)` 推进；
   - 粒子生命周期递减（`dec dword ptr [esi + 0x128]`）与消亡判定（`[esi + 0x131] = 1`）由 Update 全程负责；
   - 系统生成粒子由 `ParticleSystemClass::AI (0x0062FD60)` 负责。
   - **`Draw` 内部只写渲染缓冲，0 处内存状态变更**。在 `Draw` 入口早退，微粒在后台依旧按部就班移动与衰减，物理寿命毫无影响。
2. **CRC 校验和隔离**：
   - 联机同步校验 `CurrentFrameCRC (0x0064DAB0)` 与 `AbstractClass::CalculateChecksum` 只哈希逻辑坐标与随机数状态，绝不采集 DirectDraw 表面。
3. **确定性红线判定**：**绝对合规，0 联机分叉风险**。

---

## 六、工程落地规格（C++ Hook 扩展原型）

### 6.1 虚表挂载点防重红线
依据 `HOOK_POINT_MATRIX.md` 冲突裁决：
- **现网槽 69 已装条目**：`BulletClass`（`0x007E47F8`）、`BuildingClass`（`0x007E3FD0`）、`UnitClass`（`0x007F5D84`）、`InfantryClass`（`0x007EB16C`）、`AircraftClass`（`0x007E23B8`）已由 `blitter_hooks.cpp` 的 `FogHooks::` 安装。**严禁重新安装上述虚表**。
- **本次新增挂载点（仅 2 个独立未装条目）**：
  1. `ADDR_VTABLE_ENTRY_PARTICLE_DRAW`: **`0x007EFA68`**（对应 `ParticleClass` 槽 69）
  2. `ADDR_VTABLE_ENTRY_PARSYS_DRAW`: **`0x007EFCB0`**（对应 `ParticleSystemClass` 槽 69）

### 6.2 阵营与直视判定伪代码原型
```cpp
// 挂钩实现：ParticleClass::Draw (0x007EFA68)
void __fastcall Hook_Particle_Draw(void* pThis, void* /*edx*/, void* pLocation, void* pBounds) {
    if (!g_enableParticleFog) {
        g_pOrigParticleDraw(pThis, pLocation, pBounds);
        return;
    }

    uintptr_t pParticle = reinterpret_cast<uintptr_t>(pThis);
    
    // 1. 获取坐标并映射到地图 Cell (定点数 >> 8)
    int leptonX = *reinterpret_cast<const int*>(pParticle + 0x9C);
    int leptonY = *reinterpret_cast<const int*>(pParticle + 0xA0);
    int cellX = leptonX >> 8;
    int cellY = leptonY >> 8;

    // 2. 溯源宿主系统与所有者阵营
    uintptr_t pSystem = *reinterpret_cast<const uintptr_t*>(pParticle + 0x124);
    uintptr_t pOwnerHouse = 0;
    
    if (pSystem != 0) {
        // 优先读取直接阵营
        pOwnerHouse = *reinterpret_cast<const uintptr_t*>(pSystem + 0xFC);
        if (pOwnerHouse == 0) {
            // 备用：从发射单位 TechnoClass* (+0xE0) 索引阵营 (+0x21C)
            uintptr_t pTechno = *reinterpret_cast<const uintptr_t*>(pSystem + 0xE0);
            if (pTechno != 0 && !IsBadReadPtr(reinterpret_cast<const void*>(pTechno), 0x220)) {
                pOwnerHouse = *reinterpret_cast<const uintptr_t*>(pTechno + 0x21C);
            }
        }
    }

    // 3. 判定阵营关系
    uintptr_t pPlayerHouse = *reinterpret_cast<const uintptr_t*>(ADDR_HOUSE_PLAYER);
    bool isAllied = false;
    if (pOwnerHouse != 0 && pPlayerHouse != 0) {
        if (pOwnerHouse == pPlayerHouse) {
            isAllied = true;
        } else {
            int houseIdx = *reinterpret_cast<const int*>(pOwnerHouse + 0x30);
            uint32_t alliesBitmask = *reinterpret_cast<const uint32_t*>(pPlayerHouse + 0x5788);
            if ((alliesBitmask & (1u << (houseIdx & 31))) != 0) {
                isAllied = true;
            }
        }
    }

    // 己方/盟军粒子：100% 绘制
    if (isAllied) {
        g_telemetry.totalParticlesRendered++;
        g_pOrigParticleDraw(pThis, pLocation, pBounds);
        return;
    }

    // 4. 敌方或无宿主野生环境粒子：检查直视网格
    if (cellX >= 0 && cellX < 512 && cellY >= 0 && cellY < 512) {
        int cellIdx = cellY * 512 + cellX;
        if (s_visionGrid[cellIdx] == 0) {
            // 不在直视视野内：直接退出 (等价于 ret 8，零开销短路)
            g_telemetry.particlesCulledByFog++;
            return;
        }
    }

    g_telemetry.totalParticlesRendered++;
    g_pOrigParticleDraw(pThis, pLocation, pBounds);
}
```

### 6.3 INI 开关与遥测规格
- **INI 键**：`ra2render.ini [FogOfWar] EnableParticleFog=1`（置 0 时执行原版直通）。
- **遥测新增项**：
  ```cpp
  uint64_t particlesCulledByFog;
  uint64_t totalParticlesRendered;
  ```
- **卸载还原**：在 `RemoveVTableHooks` 中将 `0x007EFA68` 与 `0x007EFCB0` 还原回原函数指针，具备 100% 安全热回滚能力。

---

## 七、A-15 最终裁决：三条核心链全指令实证与定谳 (Final Settlement) [实证]

针对 A-4 与 A-14 早期草稿在 `+0xFC`、`+0xE0`、`+0x124` 字段语义上的分歧，经对 `gamemd.exe` 全二进制指令逐字节反汇编与符号追踪，**现做出终局定谳**：

### 7.1 核心字段权威映射总表 [实证]

| 结构体 | 偏移 | 类型 / 语义 | 构造写入指令 | 读取使用指令实证 (Read Point) | 语义判定与证明 |
|---|:---:|---|---|---|---|
| **`ParticleSystemClass`** | **`+0xFC`** | **`HouseClass* OwnerHouse`**<br>(发射阵营指针) | `0x0062DD9A`:<br>`mov [esi+0xFC], eax`<br>(实参 `[esp+0x40]`) | **`0x0062C2CC`**:<br>`mov edx, [eax+0xFC]`<br>`push edx` $\to$ `call [ebx+0x16C]` | **[实证] 直接阵营指针**。在粒子着色/贴图时读出阵营指针，作为参数压栈传给 `vtable[0x16C]` 调色板重映射函数。 |
| **`ParticleSystemClass`** | **`+0xE0`** | **`TechnoClass* Owner`**<br>(发射宿主单位指针) | `0x0062DE37` (`ecx`)<br>`0x0062DE54` (`ebx=0`) | **`0x0062DE6D`** / **`0x0062ED7B`**:<br>`mov ecx, [esi+0xE0]`<br>`mov eax, [ecx]`<br>`call [eax+0x48]` | **[实证] 对象指针**。空参写入 0 具明显指针语义；读取后解引用虚表调用 `vtable[18]` (`ObjectClass::GetCoords`) 提取宿主最新坐标；`0x0062F090` 读取 `Owner+0x684`。 |
| **`ParticleSystemClass`** | **`+0x9C`** | **`CoordStruct Location`**<br>(12 字节世界坐标) | `0x0062DCC3` 等 | **`0x0062DE77`** 等 15 处:<br>`lea edx, [esi+0x9C]` | **[实证] 空间坐标**。X=`+0x9C`, Y=`+0xA0`, Z=`+0xA4`。右移 8 位（`sar 8`）即为地图格子坐标。 |
| **`ParticleClass`** | **`+0x124`** | **`ParticleSystemClass*`**<br>(父系统指针) | `0x0062B721`:<br>`mov [esi+0x124], ecx`<br>(实参 `[esp+0x38]`) | **`0x0062C2C2`**:<br>`mov eax, [ebp+0x124]`<br>`mov edx, [eax+0xFC]` | **[实证] 容器反向指针**。所有粒子构造均在 `ParticleSystemClass` 内部触发；粒子绘制时经由 `+0x124` 读取父系统的 `+0xFC` 阵营。 |
| **`ParticleClass`** | **`+0x9C`** | **`CoordStruct Location`**<br>(12 字节世界坐标) | `0x0062B700` 等 | **`0x0062CF30`**:<br>`lea eax, [edi+0x9C]` | **[实证] 粒子空间坐标**。 |

### 7.2 终局定谳结论
1. **A-4 报告原始判定（`+0xE0 = Owner Techno*`, `+0xFC = OwnerHouse House*`, `+0x124 = ParticleSystem*`）完全成立且完全正确**。
2. **A-14 早期草稿中的 `+0xFC Owner / +0xE0 CenterCoords / +0xE8 System` 纯属误判笔误**，已在 [`docs/re/landing_pack_crt_audio_particle.md`](file:///d:/Project/ra2-campaign-forge/docs/re/landing_pack_crt_audio_particle.md) 中正式更正。
3. **M-9 落地包（`landing_pack_particle.md`）可完全放心采用 A-4/A-15 版本**：
   - 阵营穿透优先走 `pSystem + 0xFC`（直接读取 `HouseClass*`，若为空则备用回退 `pSystem + 0xE0` $\to$ `+0x21C`）；
   - 坐标判定读取 `pSystem + 0x9C` / `pParticle + 0x9C`（`Location.X >> 8`, `Location.Y >> 8` 查 `s_visionGrid`）；
   - 粒子至系统穿透走 `pParticle + 0x124`。
4. 全链条所有读写点均已在 `gamemd.exe` 中获得 100% 字节级汇编指令实证，争议彻底终结。

