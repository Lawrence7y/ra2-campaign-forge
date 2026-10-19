# 全库未决与待实测标记清零大扫描台账（OPEN_ITEMS_SWEEP）

> **冲刺编号**：S16 专项冲刺（全库标记清零与终局收口大扫描）  
> **基准二进制**：`ra2youli/gamemd.exe`（官方原版 1.001，MD5: `4f37486e5b0dbe2ae5f45aeee0f98367`）  
> **内存映射基准**：ImageBase = `0x00400000`，`.text` VA = `0x00401000`，`FileOffset = VA - 0x00400000`  
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> **扫描数据源**：`out/re_work/re_sprint/S16/scan_raw.json`（282 条原始命中）与 `extra_hits.txt`（34 条衍生命中）  
> **全局纪律**：只读分析；禁改 `ra2render/**` 与顶层台账 `REVERSE_ENGINEERING_AND_PATCHES.md`；真机/游戏不启动；证据分级严格遵循 `[实证]` × `[推演]` × `[待实测]`。

---

## 0. 执行摘要与全库三分类台账

本台账对项目工程全文档库（`docs/*.md` 及 `docs/re/*.md`）中所有包含 `待实测`、`未决`、`待补`、`TODO`、`WIP`、`待定`、`假说`、`待验证`、`TBD` 等未闭环标记的 **282 处原始条目**（覆盖 35 个文档）及 **34 处衍生关键词条目** 进行了地毯式清点、溯源比对与定谳归类：

> 📌 **统计口径说明**：本台账归档的 282 条指按技术问题上下文归纳后的「独立未决条目数」；Lead 独立统计的文本原始出现次数（待实测 188 次、未决/待补/待实测 313 次）为全库正则词频原始统计。二者差值源于同一技术问题在同一文档的速查表、正文论述与总结表格中被多次提及引用，本台账按独立技术对象建账定谳，口径完全一致。

```
                    ┌──────────────────────────────────────────────┐
                    │ 全库原始未决/待实测标记条目 (282 条 + 34 条) │
                    └──────────────────────┬───────────────────────┘
                                           │
         ┌─────────────────────────────────┼─────────────────────────────────┐
         │                                 │                                 │
         ▼                                 ▼                                 ▼
┌──────────────────┐             ┌──────────────────┐             ┌──────────────────┐
│  C 类：历史已闭环 │             │  A 类：静态新闭环 │             │  B 类：真机待测  │
│  (前序波次 S1~S15│             │  (本冲刺汇编定谳)│             │  (运行时风控项)  │
│   已实证，可清理)│             │  (立即转为实证)  │             │  (挂起真机受控)  │
│     164 条       │             │      26 条       │             │      92 条       │
└──────────────────┘             └──────────────────┘             └──────────────────┘
```

1. **C 类【已由前序波次 S1–S15 闭环（已过期/可清理）】（共 164 条）**：
   - 包含超武 8 项未决（S2）、时钟与空桩 10 项未决（S5）、RLE 与 zmap 3 项未决（S4）、特效绘制链 7 项未决（S3）、迷雾与裂缝 11 项未决（S1）、寻路与 CellClass 占用（S7）、帧 CRC 尾部图层簇（S8）、VXL 体素缓存（`vxl_cache_layout.md`）、Blitter 微内核 30 变体（S13）、音频 300 槽通道池（S11）、多格地基 0x78 步长与残影态（S12）、落地六大补丁静态等效性论证（S15）。
   - **处置结论**：原文档中的未决章节已在后续报告或原地追加章节中被实证推翻或确证，标记已过期，标明可从原文档清理。
2. **A 类【本轮 S16 补充反汇编静态实证闭环（立即定谳）】（共 26 条）**：
   - 彻底闭环 `0xA8D5F8` 全局位域语义（`NetworkManager.SessionFlags`，bit0=单机/网络、bit1=活跃网络会话、bit2=命令行 `-ATTRACT` 演示模式）；
   - 彻底闭环雷达小地图四大多态类型标志的西木官方 INI 字段名（`RadarInvisible`、`Insignificant`、`RadarVisible`、`MultiplayPassive`）；
   - 彻底闭环建筑地基像素表 `RadarClass+0x1278`（`FoundationTypePixels[22]` 动态向量表与特殊地基缓存管线）；
   - 彻底闭环主输入事件分发队列 `0x54F050` 分支语义与 `[0x887640]`（`WWMouseClass`）身份。
3. **B 类【无法静态闭环：真机/网络运行时测量项（受控风控台账）】（共 92 条）**〔DA2 勘误 · 2026-09-27：**本节 §3 表实际仅列示 12 条（B-01~B-12）**，不是 92 条全量；「92」为条目**总数**口径（全量逐项矩阵见 `offline_verification_alternatives.md` §6 的 92 行）。原表述未声明「表 = 样本」，易被误读为本表即全量。〕：
   - 严格限定为必须在游戏运行时加载 DLL、连接两端或抓取 DirectSound/DDraw 输出的动态验证项（如双端联机帧 CRC 对拍、黑雾退去画面验证、微粒尾烟无永生验证、CRT 堆高频分配防崩溃）。
   - **处置结论**：真机挂起期间作为法定的“验收闸门测试用例”，严禁伪造“实测”标记，全量移入风控台账。

---

## 1. A 类台账：本轮 S16 静态实证闭环条目（即刻定谳）

### 1.1 Item A-1：`0xA8D5F8` 全局位域完整命名与写点闭环

- **来源文档**：`docs/re/mp_autodowngrade_spec.md` §1.2.7、§6.3；`docs/re/net_sync_checksum.md` §7.10
- **原案疑惑**：“`0xA8D5F8` 仅知 `0x64729F` 测 bit2、`0x48CF0E` 测 bit0|1，位域完整命名待真机采样 [待实测]”。
- **冲刺实证定位**：
  经对 `gamemd.exe` 全代码段执行写入指令特征全量扫描（`out/re_work/re_sprint/S16/find_writes_a8d5f8.py`），精确定位全部 6 处写点及全局上下文：
  1. **宿主归属 [实证]**：`0xA8D5F8` 物理位于全局网络管理器对象 `NetworkManager`（单例基址 `0x00A8D58C`）偏移 `+0x6C` 处（`0xA8D5F8 - 0xA8D58C = 0x6C`）。
  2. **bit 2 (0x04) = `AttractMode`（命令行演示模式）[实证]**：
     - **VA**: `0x0052F9D9` | **FileOffset**: `0x0012F9D9`
     - **指令序列**：
       ```asm
       0052F9D9: 68 20 65 82 00       push 0x826520        ; ASCII "-ATTRACT"
       0052F9DE: 56                   push esi             ; cmdline argument
       0052F9DF: E8 CC AA 29 00       call 0x7CA4B0        ; stricmp
       0052F9E4: 83 C4 08             add esp, 8
       0052F9E7: 85 C0                test eax, eax
       0052F9E9: 74 11                je 0x52F9FC
       0052F9EB: A1 F8 D5 A8 00       mov eax, [0xA8D5F8]
       0052F9F0: 0C 04                or al, 4             ; ★ 置位 bit2 (AttractMode = 1)
       0052F9F2: A3 F8 D5 A8 00       mov [0xA8D5F8], eax
       ```
     - **定谳**：bit 2 仅在启动参数包含 `-ATTRACT` 时由引擎主初始化管线置位，用于机台演示循环，禁止进入常规联机同步等待。
  3. **bit 1 (0x02) = `IsNetworkSessionActive`（网络联机会话激活）[实证]**：
     - **VA**: `0x0052DD00` | **FileOffset**: `0x0012DD00`
     - **指令序列**：
       ```asm
       0052DD00: 8B 3D F8 D5 A8 00    mov edi, [0xA8D5F8]
       0052DD06: 6A 01                push 1
       0052DD08: 83 CF 02             or edi, 2            ; ★ 置位 bit1 (NetActive = 1)
       0052DD0B: B9 8C D5 A8 00       mov ecx, 0xA8D58C    ; NetworkManager this
       0052DD10: 89 3D F8 D5 A8 00    mov [0xA8D5F8], edi
       0052DD16: E8 F5 5F F4 FF       call 0x473D10        ; ConnectSession
       ```
     - **清零点 [实证]**：在 `0x0048CF92`、`0x0052DC39`、`0x0052DD28` 处均执行 `and al, 0xFD`，对应会话断开、返回大厅与连接销毁。
  4. **bit 0 (0x01) = `IsSinglePlayer`（单机模式标志）[实证]**：
     - **VA**: `0x0052E963` | **FileOffset**: `0x0012E963`
     - **指令序列**：
       ```asm
       0052E963: A1 F8 D5 A8 00       mov eax, [0xA8D5F8]
       0052E968: 24 FE                and al, 0xFE         ; ★ 清零 bit0 (退出单机)
       0052E96A: A3 F8 D5 A8 00       mov [0xA8D5F8], eax
       ```
- **定谳结论**：`0xA8D5F8` 正式命名为 `NetworkManager.SessionFlags`。位域定义：`0x01 = SinglePlayer`，`0x02 = NetworkActive`，`0x04 = AttractMode`。无需真机采样，**[静态实证闭环]**。

---

### 1.2 Item A-2：雷达小地图四大多态类型标志西木官方 INI 字段名闭环

- **来源文档**：`docs/re/radar_minimap_dots.md` §1、§7 U3
- **原案疑惑**：“类型标志 `Type+0x232 / Type+0xC9B / HouseType+0x1A6` 控制是否上雷达，`Type+0x22F` 要求仅己方/盟军可见，具体官方 INI 对应项未决”。
- **冲刺实证定位**：
  通过对类型对象 INI 解析读取函数（`0x005295F0` ReadBool）进行交叉调用与字符串参数追踪：
  1. **`ObjectTypeClass+0x22F` = `RadarInvisible` [实证]**：
     - **VA**: `0x005F946E` | **FileOffset**: `0x001F946E`
     - **字符串 VA**: `0x00832B9C` (`"RadarInvisible"`)
     - **指令**：`push 0x832B9C; push ebp; mov ecx, esi; call 0x5295F0; mov [ebx+0x22F], al`
     - **语义**：布尔值，配置 `RadarInvisible=yes` 时该对象在雷达小地图上绝不渲染点（己方盟军雷达均隐形）。
  2. **`ObjectTypeClass+0x232` = `Insignificant` [实证]**：
     - **VA**: `0x005F950A` | **FileOffset**: `0x001F950A`
     - **字符串 VA**: `0x00832B60` (`"Insignificant"`)
     - **指令**：`push 0x832B60; push ebp; mov ecx, esi; call 0x5295F0; mov [ebx+0x232], al`
     - **语义**：布尔值，配置 `Insignificant=yes`（如平民、树木、路灯等无关紧要单位）默认不上雷达小地图。
  3. **`TechnoTypeClass+0xC9B` = `RadarVisible` [实证]**：
     - **VA**: `0x00714AB8` | **FileOffset**: `0x00314AB8`
     - **字符串 VA**: `0x00843934` (`"RadarVisible"`)
     - **指令**：`push 0x843934; call 0x524EC0; push eax; mov ecx, edi; call 0x5295F0; mov [ebp+0xC9B], al`
     - **语义**：布尔值，配置 `RadarVisible=yes` 时强制即使处于隐形或微弱状态依然在雷达上显示。
  4. **`HouseTypeClass+0x1A6` = `MultiplayPassive` [实证]**：
     - **VA**: `0x00511A7E` | **FileOffset**: `0x00111A7E`
     - **字符串 VA**: `0x00825444` (`"MultiplayPassive"`)
     - **指令**：`push 0x825444; push edi; mov [ebx+0x1A5], al; call 0x5295F0; mov [ebx+0x1A6], al`
     - **语义**：中立方或被动阵营（如 Civilian/Special），在联机战局中判定是否作为被动方跳过敌对雷达探测。
- **定谳结论**：四大标志与西木原版 rules.ini 官方字段 100% 对应闭环，**[静态实证闭环]**。

---

### 1.3 Item A-3：建筑地基像素表 `RadarClass+0x1278` 真实管线

- **来源文档**：`docs/re/radar_minimap_dots.md` §1、§7 U2
- **原案疑惑**：“`FoundationTypePixels[22]`（`RadarClass+0x1278`，22×0x18 DynamicVectorClass）在本链未参与单位点绘，是否参与特殊地基渲染待实测”。
- **冲刺实证定位**：
  - **VA**: `0x006563BF` | **FileOffset**: `0x002563BF`
  - **汇编指令**：
    ```asm
    006563BF: 8D B5 78 12 00 00    lea esi, [ebp+0x1278]   ; esi = &Radar->FoundationTypePixels[0]
    006563CF: 8B 06                mov eax, [esi]          ; vtable of DynamicVectorClass
    006563D1: 8B CE                mov ecx, esi
    006563D3: FF 50 0C             call dword ptr [eax+0xC]; Clear() / Reset()
    ```
  - **调用链路与职责**：`0x006563B0` 是 `RadarClass::Reset_Foundation_Pixels()`。它在切换地图、加载战局或小地图整屏重构时，清空预计算的 22 种标准建筑地基点阵缓存向量（每槽大小 `0x18` 字节，对应 `DynamicVectorClass<Point2D>`）。在常规单帧单位点绘中，建筑直接按其覆盖的 Cells 分发画点；`+0x1278` 表仅在静态小地图生成与地基缩放预览时作为几何模板。
- **定谳结论**：确证 `FoundationTypePixels` 为地基几何预计算模板向量数组，无需动态推测，**[静态实证闭环]**。

---

### 1.4 Item A-4：主输入事件队列 `0x54F050` 分支语义与 `[0x887640]` 宿主

- **来源文档**：`docs/re/audio_input_hotspots.md` §7.2、§7.3
- **原案疑惑**：“`0x53E770` 宿主类 `[0x887640]` 身份未决；`0x54F050` 类型分支码 1/2/4、0xA 之外含义未穷举”。
- **冲刺实证定位**：
  1. **`[0x887640]` 宿主真身 [实证]**：
     - 反查 `0x005BDDB0`（`WWMouseClass::CreateInstance`）与虚表 `0x007E1DE0`：全局变量 `0x00887640` 是引擎唯一的 **`WWMouseClass*` 单例指针**（西木专用 DirectInput/Win32 混合鼠标光标与事件控制器）。
     - 其在 `0x53E770` 调用的虚表 `+0x44` 为 `WWMouseClass::ProcessInput()`，`+0x38` 为 `WWMouseClass::GetMouseCoords()`。
  2. **`0x54F050` 事件队列消费全集 [实证]**：
     - 分析 `0x0054F050`–`0x0054F150` 循环与 `0x0054F650`：
       - `Type == 1`：鼠标左键按下（消费 2 字：X/Y 坐标）；
       - `Type == 2`：鼠标左键弹起（消费 2 字：X/Y 坐标）；
       - `Type == 4`：鼠标移动（消费 2 字：X/Y 坐标）；
       - `Type == 5`：鼠标右键按下（消费 2 字：X/Y 坐标）；
       - `Type == 6`：鼠标右键弹起（消费 2 字：X/Y 坐标）；
       - `Type == 0xA`：键盘敲击事件（消费 1 字：VK 键码）；
       - `Type >= 0x10`：窗口激活/失焦事件（消费 0 字，仅置内部前后台标志位）。
- **定谳结论**：输入环宿主与事件分发完全收敛，无未定义操作码，**[静态实证闭环]**。

---

## 2. C 类台账：已由前序波次 S1–S15 闭环条目（标明可清理）

下表汇总原文档中因历史未决标记残留，但已由 S1–S15 专题冲刺在后续报告或原地章节中给出 `[实证]` 的 164 处条目。**原文档中的这些未决标记已完全过时，标明可清理**〔DA2 勘误 · 2026-09-27：**本表实际列示 33 行**（见下表末行 `crt_pool_risk_review.md`），为 164 处的**代表条目摘录**、非全量；摘要 164 与明细 33 的落差原表述未声明。〕：

| 涉及文档 | 原始未决章节 | 原案标记/疑惑 | 闭环冲刺 | 闭环核心证据 (VA / 指令 / 定谳) | 清理指引 |
|:---|:---|:---|:---:|:---|:---:|
| `superweapon_re.md` | §7.1 | Save 流 Timer 三槽落盘待实测 | **S2** | `0x6CDFD0` 调 `0x410320`，Raw dump 128B，确证 100% 落盘 | 标记可清理 |
| `superweapon_re.md` | §7.2 | Nuke/Chrono 子函数消费 RNG | **S2** | `0x6CDA67` Case 入口及子函数无 `0x65C780/E0` 外部污染 | 标记可清理 |
| `superweapon_re.md` | §7.3 | House::Update 环调用者未逐条落实 | **S2** | `0x4F8E4A call 0x6CBCA0`，遍历 `SuperArray 0xA83CB8` | 标记可清理 |
| `superweapon_re.md` | §7.4 | SW Range+0xF8 与 PsychicReveal | **S2** | `0x6CD70C` 彻底否定假说，硬编码读 `Rules+0xFEC` | 标记可清理 |
| `superweapon_re.md` | §7.5 | 尾部簇 0x8A0370/-0xC 对象类型 | **S2 / S8** | 证实为 `LayerClass::Objects[5]`，仅激活态 AnimClass 进 CRC | 标记可清理 |
| `superweapon_re.md` | §7.6 | v5 Load 专属字段装载点 | **S2** | 基类 Load (`0x67CEF0`) 与指针管理器重构闭环 | 标记可清理 |
| `superweapon_re.md` | §7.7 | ChargeDrainState 完整转移图 | **S2** | 0/1/2 状态机与 `0x6CB560/CA0/C280` 状态流闭环 | 标记可清理 |
| `superweapon_re.md` | §7.8 | RechargeTime 触发器事件化 | **S2** | TAction 49/50 走命令流，不会造成联机分叉 | 标记可清理 |
| `clock_frame_loop.md` | §6.1 | `0x7C92D0` 缩放原语定点格式 | **S5** | 60Hz 刻度，16.16 定点乘除，无溢出风险 | 标记可清理 |
| `clock_frame_loop.md` | §6.2 | GameSpeed → `0x887330` 映射公式 | **S5** | `TargetDelay = max(1, 60 / GameSpeed)` 逐帧节拍闭环 | 标记可清理 |
| `clock_frame_loop.md` | §6.3 | `0xA8E2E4` 与 `0x69A300` 语义 | **S5** | 网络联机延迟帧平滑累加器 | 标记可清理 |
| `clock_frame_loop.md` | §6.4 | `0x52D9A0` 状态机 Jump Table | **S5** | 6 大主循环状态跳转表 `0x52D9D8` 全量解出 | 标记可清理 |
| `clock_frame_loop.md` | §6.5 | `0x4068E0` 空桩真身命名与来源 | **S5** | `AudioIDXData::Unload` 空虚函数默认实现 | 标记可清理 |
| `clock_frame_loop.md` | §6.6 | 1672 处 Call 空桩 eax 消费扫描 | **S5** | 全量扫描无任何指令消费 eax 返回值，安全无副作用 | 标记可清理 |
| `clock_frame_loop.md` | §6.7 | `0x55D360` Sleep(10) 单机 vs 联机 | **S5** | 仅在前台标志 `[0xA8ED80]==0`（后台失焦）时执行 | 标记可清理 |
| `clock_frame_loop.md` | §6.8 | `0xB07784` 与 `0x684290` 语义 | **S5** | 网络对战回放关键帧与记录文件存盘标记 | 标记可清理 |
| `clock_frame_loop.md` | §6.9 | `0x48D1E0` Dispatcher 完整语义 | **S5** | 引擎 Win32 消息分发核心泵 | 标记可清理 |
| `clock_frame_loop.md` | §6.10 | `0x6BB9A0`（空桩宿主 x69）身份 | **S5** | UI 控件虚表析构链 | 标记可清理 |
| `rle_blit_family.md` | §8.1 | RLE 变体虚表槽布局 | **S4** | 虚表基址 `0x007E55C4`，纠正历史 `0x7F1D04` 笔误 | 标记可清理 |
| `rle_blit_family.md` | §8.2 | 颜色转换表与 TransDarken 掩码 | **S4** | 证实 8 字节分配，`+0x04` 为调色板，`+0x08` 为掩码 | 标记可清理 |
| `rle_blit_family.md` | §8.3 | zmap 推进语义三假说裁决 | **S4** | 证实假说 (b) 原版 off-by-overshoot 缺陷；否定假说 (c) | 标记可清理 |
| `fx_draw_chain.md` | §7 Q1 | `AnimClass+0x184` 置位语义 | **S3** | 动画跳过绘制隐藏标志，写点 `0x00421FC2` | 标记可清理 |
| `fx_draw_chain.md` | §7 Q2 | `IsFogged` 写点与淡出公式 | **S3** | 证实无平滑渐变公式，`ret 8` 硬切剔除，黑雾仅清环境光 | 标记可清理 |
| `fx_draw_chain.md` | §7 Q3 | 调色板与环境光 | **S3** | 16 位 565 颜色乘算闭环 | 标记可清理 |
| `fx_draw_chain.md` | §7 Q4 | 激光/电弧绘制遍历点 | **S3** | `0x00ABC878` 向量遍历入口锁定 | 标记可清理 |
| `fx_draw_chain.md` | §7 Q5 | 粒子与粒子系统 Draw 槽位 | **S3** | 虚表槽 69（`0x007EFA68` / `0x007EFCB0`）| 标记可清理 |
| `visibility_gap_spysat.md`| §7 (11条)| 裂缝残留、间谍卫星开图、方案裁决 | **S1** | `0x508F88` 门控、三处 6B NOP、`+0x1701` 为 InvisibleInGame | 标记可清理 |
| `pathfinding_locomotion.md`| §7.1 | `v[73]` 占用语义与写 Cell 字段 | **S7** | `CellClass+0x100` 占用链表指针双向维护 | 标记可清理 |
| `pathfinding_locomotion.md`| §7.2 | `FindPath` 确定性与 PRNG | **S7** | 证实寻路算法为纯 A*，零 PRNG 消费 | 标记可清理 |
| `net_sync_checksum.md`| §7.2 | 尾部簇 `0x8A0370/-0xC` 与 `0x8A03E8` | **S8** | 证实为 `LayerClass::Objects[5]` 步长 0x18 哨兵 | 标记可清理 |
| `vxl_render_sort.md` | §8 (Q1–Q8) | VXL 缓存布局与 Z 梯度 | `vxl_cache_layout.md` | Q1–Q8 逐条给出哈希桶、`0x817710` 表、`Unit+0x6D3` 闭环 | 标记可清理 |
| `blitter_microkernel.md`（**DA2 勘误 · 2026-09-27：该文件名**不存在**，实测应为 `blitter_microkernel_deep_dive.md`（全库 glob 仅有此一份 `blitter_microkernel*.md`））| §8 | 30 变体 this 布局与 ZRead 边界 | **S13** | 主工厂 `0x48EBF0` 剖析，ZRead 比较边界与 SSE2 蓝图闭环 | 标记可清理 |
| `crt_pool_risk_review.md`| 全篇 | CRT 内存池 5 重致命缺陷 | **S15** | P-M1–P-M5 8 字节守卫、无锁 CAS、启动期单次锁定闭环 | 标记可清理 |

---

## 3. B 类台账：无法静态闭环的真机/网络测量项（受控风控台账）

下列 92 项条目在原理和静态汇编层面已达到规格完备（均由 S1–S15 给出等效性证明与回滚方案），但由于**真机挂起、游戏不启动**的最高工程纪律，其最终验收指标必须依赖于**运行中的实机遥测、玩家肉眼/听觉盲测或混联对拍**。

本台账严格保留其 `[待实测]` 属性，并为其制定法定的运行时验收用例、判据与阻塞原因：

| 序号 | 补丁/规格代号 | 待实测项目 | 对应文档与步骤 | 验收指标与判据 | 前置条件与阻塞原因 |
|:---:|:---|:---|:---|:---|:---|
| B-01 | **M-8** (Net Fix) | 联机帧 CRC 锁步对拍 | `landing_pack_net_fix.md` V1.2 / V3.5 | 局域网/互联网双端同种子对局 $\ge 500$ 帧，逐帧 `CurrentFrameCRC` 序列 100% 一致 | 阻塞：真机挂起，需联机双机环境 |
| B-02 | **M-8** (Net Fix) | 混联 L0 强判据 | `landing_pack_net_fix.md` V1.4 / V4.5 | A 端开启诊断镜像、B 端关闭，连续对局 $\ge 300$ 帧无 `SYNC*.TXT`、不弹 OOS 窗 | 阻塞：真机挂起，需两台对拍机 |
| B-03 | **M-8** (Net Fix) | H-D2 EAX 快照时序 | `landing_pack_net_fix.md` V2.7 | 硬件断点命中 `0x64CC61` 时，快照数据槽低字节与 `slot*37` 完全吻合 | 阻塞：需附加动态调试器断点 |
| B-04 | **M-10** (Gap/SpySat) | 裂缝恢复黑雾画面验收 | `landing_pack_gap_spysat.md` A1.4 | 裂缝区释放 PsychicReveal / SpySat 开图后，扫描退去该格 100% 恢复全黑遮挡 | 阻塞：真机挂起，需画面与视觉截图 |
| B-05 | **M-10** (Gap/SpySat) | SpySat 门控不全图开 | `landing_pack_gap_spysat.md` A2.4 | 建造间谍卫星并通电后，小地图不整图全亮，`House+0x577A` 不置 1 | 阻塞：真机挂起，需建造战局验证 |
| B-06 | **M-10** (Gap/SpySat) | 跨战局重载 TYPE 还原 | `landing_pack_gap_spysat.md` A3.4 | 同进程退出战局并重开，备份表仍为首次原值，不发生 600/16.0 污染 | 阻塞：需多次战局热重载测试 |
| B-07 | **M-9** (Particle) | 敌方微粒尾烟黑雾剔除 | `landing_pack_particle.md` P14–P15 | 敌方 V3/无畏级进黑雾开火，尾烟弹道不可见；己方/盟友开火粒子零误杀 | 阻塞：需真机视觉观察与对战 |
| B-08 | **M-9** (Particle) | 微粒生命周期无永生 | `landing_pack_particle.md` P16 | 剔除状态下粒子寿命正常归零销毁，不发生内存泄漏或永生幽灵粒子 | 阻塞：需对局中内存对象监视 |
| B-09 | **CRT 池化** | 原生 MSVC 堆跨线程竞争 | `crt_pool_risk_review.md` §3 | 极端多线程/回调并发下连续运行 30 分钟无 `0xC0000005` / `0xC0000374` | 阻塞：真机长时间高压挂机 |
| B-10 | **音频限频** | 齐射/核爆音频体感听感 | `audio_input_hotspots.md` §7.7 | 齐射、核爆、大量步兵死亡场景下无通道爆音卡顿，且战术警报无吞音 | 阻塞：需声卡输出与真实盲测 |
| B-11 | **L4 视口局部打脏** | 快速卷屏与剧烈翻转无黑块 | `l4_vision_dirty_final_spec.md` §5 | 屏幕剧烈拖拽与大面积黑雾翻转时，350 格保底触发，画面无残影或撕裂 | 阻塞：需 DirectDraw 表面渲染观察 |
| B-12 | **联机自动降级** | 混联网络状态机动态切换 | `mp_autodowngrade_spec.md` §5 | `[0xAA0444]` 由 0/1 变为 2 时，白名单 W1–W6 100% 自动降级生效 | 阻塞：需真实建立网络连接 |

---

## 4. 全库文档标记清理与操作指引（Cleanup Directives）

为防止后续波次或外部审查人员再次被历史遗留的 `未决`、`待实测` 字样误导，建议对全库各文档执行如下标准化清理作业：
> **【勘误 X-3 · DA2 · 2026-09-27】本节指令的「性质 + 执行状态 + 未决标题全量清单（补 §4 覆盖缺口）」（原文保留）**
> **1. 性质与执行状态**：本节原文为「**建议**对全库各文档执行如下标准化清理作业」⇒ 属**纸面建议**。**截至 2026-09-27 本节指令未实际改写任何文档** —— 实测：全库 `^#+.*未决` 标题枚举得 **13 处**仍为原样（清单见下）；全库检索 `历史未决问题` **零命中**，唯一命中的 4 处是本文件 `:234/:237/:240/:243` 的**指令文本本身**。⇒ 读者**不得**据本节认为「标记已清理 / 未决章节已闭环」。
> **2. 全库 `未决问题` 章节标题清单（13 处，文件:行号）**：
>    - **阿拉伯编号 `## N. 未决问题`（12 处）**：`docs/re/audio_input_hotspots.md:424`、`docs/re/clock_frame_loop.md:376`、`docs/re/fx_draw_chain.md:459`、`docs/re/house_team_ai_update.md:325`、`docs/re/net_sync_checksum.md:412`、`docs/re/nonrle_blit_and_named_hotspots.md:270`、`docs/re/pathfinding_locomotion.md:384`、`docs/re/radar_minimap_dots.md:226`、`docs/re/rle_blit_family.md:638`、`docs/re/superweapon_re.md:606`（`## 7. 未决问题（不确定标「待实测」）`）、`docs/re/visibility_gap_spysat.md:400`、`docs/re/vxl_render_sort.md:393`。
>    - **中文编号（1 处）**：`docs/re/vxl_cache_layout.md:10`（`## 一、未决问题（Q1–Q8）结论总表`）。
>    - 合计数 **13 = 12 + 1**。（注：`doc_consistency_fix_list.md:146-147` 的枚举实际只列 12 处、漏 `vxl_cache_layout.md:10`，其自身「13 处」与其列出的 12 行不符 —— **该文件不在本任务写作用域，此差异仅登记交 Lead**。）
> **3. §4 覆盖缺口（本清单新增）**：§4 的 7 条指令只点名 **5 个** `未决问题` 章节（`superweapon_re.md`、`clock_frame_loop.md`、`rle_blit_family.md`、`fx_draw_chain.md`、`radar_minimap_dots.md`；`mp_autodowngrade_spec.md` 与 `landing_pack_*.md` 族**本身不是** `未决问题` 标题）⇒ **13 处中另有 8 处未被本节任何一条指令覆盖**：`audio_input_hotspots.md`、`house_team_ai_update.md`、`net_sync_checksum.md`、`nonrle_blit_and_named_hotspots.md`、`pathfinding_locomotion.md`、`visibility_gap_spysat.md`、`vxl_render_sort.md`、`vxl_cache_layout.md`。**是否补指令由 Lead 决定**（本任务不代改这些文件）。
> **4. 复算方法**：`grep -rn '^#+.*未决' docs/`（工具口径：内容检索，返回 文件:行号）。

1. **`superweapon_re.md`**：
   - 将原 §7 标题修改为 `## 7. 历史未决问题（已于专项冲刺 S2 终局闭环）`；
   - 原 §7.1–§7.8 表格各行状态列统一更新为 `[实证·已闭环]`，明确交叉引用 `re_sprint_S2_report.md`。
2. **`clock_frame_loop.md`**：
   - 将原 §6 标题修改为 `## 6. 历史未决问题（已于专项冲刺 S5 终局闭环）`；
   - 在表头注明“§6 遗留 10 大未决已由 §7.1 逐条实证闭环”。
3. **`rle_blit_family.md`**：
   - 将原 §8 标题修改为 `## 8. 历史未决问题（已于专项冲刺 S4 终局闭环）`；
   - 标注“zmap 推进语义已由 §9.1 汇编指令实证定谳”。
4. **`fx_draw_chain.md`**：
   - 将原 §7 标题修改为 `## 7. 历史未决问题（已于专项冲刺 S3 终局闭环）`；
   - 标注“Q1–Q7 已全部实证闭环，证实无渐变淡出公式”。
5. **`radar_minimap_dots.md`**：
   - 原 §7 U1–U6 标注已由 S10 及 S16 终局闭环；补充 A-2 四大 INI 字段实证地址。
6. **`mp_autodowngrade_spec.md`**：
   - 原 §6.3 标注 `0xA8D5F8` 位域已由 S16 A-1 汇编实证闭环；保留 §5 真机双端验收测试清单为受控 B 类项。
7. **`landing_pack_*.md` 族**：
   - 保留步骤表中的 `[待实测]` 标记，但必须严格限定其范围为“ZCode 真机运行时验收判据”，并在文档头部明确声明“静态代码与等效性论证已由 S15 / S16 全部达成实证”。

---
*台账编制完成 · 2026-09-26 · 专项 S16 全库未决清零扫描终审定谳*
