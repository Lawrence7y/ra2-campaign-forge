# 《红色警戒2：尤里的复仇》全项目 Hook 点冲突矩阵与唯一落地顺序表

> **RA2 / YR (gamemd.exe 1.001) Engine Hook Conflict Matrix & Canonical Landing Sequence**
> 
> **文档版本**：v1.0.0 · 架构规范级基准  
> **证据基准**：`gamemd.exe 1.001`（MD5: `9EB42F6EEB4E82A1A8E2E67F688B775C`）  
> **归属任务**：A-2（逆向工程架构梳理 · 挂钩冲突矩阵与落地时序裁决）  
> **关联档案**：覆盖 `docs/re/*.md` 全套 24 份专题逆向文档；交叉核验 `ra2render/blitter_hooks.cpp`（含 v1.6.0 落地项）  
> **硬约束准则**：任何情况下不得修改 `ra2render/**` 与顶层台账 `REVERSE_ENGINEERING_AND_PATCHES.md`；严禁违反《确定性红线》篡改锁步同步逻辑。

---

## 目录
- [一、架构总览与方法论](#一架构总览与方法论)
- [二、全项目 Hook 点地址聚类总表（带来源与行号）](#二全项目-hook-点地址聚类总表带来源与行号)
  - [2.1 L1 高位色软渲染 Blitter 族（Non-RLE & RLE）](#21-l1-高位色软渲染-blitter-族non-rle--rle)
  - [2.2 L2 寻敌逻辑与空间粗粒度网格](#22-l2-寻敌逻辑与空间粗粒度网格)
  - [2.3 L3/L5 星际争霸式战争迷雾与视距剔除（虚表槽 69 族）](#23-l3l5-星际争霸式战争迷雾与视距剔除虚表槽-69-族)
  - [2.4 L4 视口渲染与脏矩形系统](#24-l4-视口渲染与脏矩形系统)
  - [2.5 L5 雷达小地图与战地感知](#25-l5-雷达小地图与战地感知)
  - [2.6 裂缝产生器保护与间谍卫星超武](#26-裂缝产生器保护与间谍卫星超武)
  - [2.7 屏幕激光、电弧与全域特效链（FX）](#27-屏幕激光电弧与全域特效链fx)
  - [2.8 VXL 体素管线、朝向矩阵与阴影表](#28-vxl-体素管线朝向矩阵与阴影表)
  - [2.9 路径搜索与机动运动学（Locomotion）](#29-路径搜索与机动运动学locomotion)
  - [2.10 音频引擎并发削峰与输入热点](#210-音频引擎并发削峰与输入热点)
  - [2.11 内存分配器、CRT 堆与小对象池](#211-内存分配器crt-堆与小对象池)
  - [2.12 UI 侧边栏、框选与命令分发](#212-ui-侧边栏框选与命令分发)
- [三、核心冲突深度裁决详述（Core Conflict Arbitrations）](#三核心冲突深度裁决详述core-conflict-arbitrations)
  - [3.1 冲突一：0x73B0B0 / 0x73B470 / 0x73CEC0 / 0x6D8DB0（VXL 体素渲染 vs 特效绘制链双重建议冲突）](#31-冲突一0x73b0b0--0x73b470--0x73cec0--0x6d8db0vxl-体素渲染-vs-特效绘制链双重建议冲突)
  - [3.2 冲突二：虚表槽 69（ObjectClass::Draw 族多态拦截与生命周期安全）](#32-冲突二虚表槽-69objectclassdraw-族多态拦截与生命周期安全)
  - [3.3 冲突三：寻敌 0x006F8DF0（Greatest_Threat 9 字节 Inline Hook vs 原版虚表劫持）](#33-冲突三寻敌-0x006f8df0greatest_threat-9-字节-inline-hook-vs-原版虚表劫持)
  - [3.4 冲突四：视口刷新 0x006D3D99（jge 原版直通 vs RegisterCellAsVisible 局部打脏 vs jmp 0x6D3E37 全量刷新）](#34-冲突四视口刷新-0x006d3d99jge-原版直通-vs-registercellasvisible-局部打脏-vs-jmp-0x6d3e37-全量刷新)
  - [3.5 冲突五：小地图 0x00655F48（DrawCell 点过滤） vs 0x006574C3（RadarPlot_Cell 代理覆写）](#35-冲突五小地图-0x00655f48drawcell-点过滤-vs-0x006574c3radarplot_cell-代理覆写)
> 【W3 勘误 · W3-A6/ISSUE-DISAMBIG-RADAR-HOOK】改前：0x006574C3；改后：0x006574C3（RadarClass::Plot_Cell 主循环调用点，见 ra2render.h:158；实际补丁下沉点位于 0x00655D38，见 blitter_hooks.cpp:150, 3016）；依据：ra2render/ra2render.h:158; ra2render/blitter_hooks.cpp:150, 2711, 2920, 3016, 3090；分级：P2
  - [3.6 冲突六：裂缝产生器引用计数破坏 Bug（0x00568273 等）与超武雷达透缝](#36-冲突六裂缝产生器引用计数破坏-bug0x00568273-等与超武雷达透缝)
- [四、全项目唯一推荐落地顺序表（Canonical Landing Sequence）](#四全项目唯一推荐落地顺序表canonical-landing-sequence)
- [五、确定性与联机安全红线约束（Multiplayer Synchronization Redlines）](#五确定性与联机安全红线约束multiplayer-synchronization-redlines)

---

## 一、架构总览与方法论

在《红色警戒2：尤里的复仇》（1.001）底层现代化的长期推进过程中，项目先后输出了 24 份高质量专题逆向文档，涵盖软渲染加速、寻敌优化、三态战争迷雾、小地图感知、体素光栅化、音频降噪、路径搜索及联机确定性等各子系统。

然而，由于多智能体与工程师并行推演，不可避免地在多个核心子系统交汇处提出了**重叠挂载点、同地址多建议、虚表层级错位以及实现路线互斥**等隐性冲突。若缺乏全局顶层仲裁，盲目合并将直接导致：
1. **虚表跳板覆盖破坏**（多个功能覆写同一虚表槽，后挂者抹除先挂者）；
2. **绘制门控层级短路**（基类早退导致派生类状态机未执行，如建筑残影丢失）；
3. **联机与回放异步（OOS Desync）**（逻辑帧内随机数或命令执行顺序受渲染优化污染）；
4. **性能反向衰退**（重复打脏、死循环重绘或过度节流）。

本规范通过自动静态提取脚本（`tools/extract_hook_tables.py`）扫描全项目 24 份逆向文档，提取出 **515 处 Hook 与补丁建议**，经过严格地址与语义聚类，最终确立了全项目唯一的架构仲裁基准与七阶段落地顺序。

```
                         全项目 Hook 拓扑与分层仲裁架构
 ┌────────────────────────────────────────────────────────────────────────┐
 │                      Phase 0: 系统运行基座 (LFH / 调速保护 / 高精度时钟)           │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │
 ┌───────────────────────────────────▼────────────────────────────────────┐
 │  Phase 1: L1 16-bit 渲染微内核 (Non-RLE & RLE Blitter 向量化, 虚表 Slot 1)  │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │
 ┌───────────────────────────────────▼────────────────────────────────────┐
 │  Phase 2: L2 全局寻敌收敛 (0x006F8DF0 Inline Hook 独占 + SelectAutoTarget)   │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │
 ┌───────────────────────────────────▼────────────────────────────────────┐
 │  Phase 3: L3 星际三态迷雾基座 (CellClass::Draw 0x4801F0 + 0x6D3D99 视口保活) │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │
 ┌───────────────────────────────────▼────────────────────────────────────┐
 │  Phase 4: L5 战地感知与三态小地图 (虚表 Slot 69 单位/建筑 + 0x6574C3 雷达覆写)  │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │
 ┌───────────────────────────────────▼────────────────────────────────────┐
 │  Phase 5: 特效绘制链与微粒收口 (LaserDraw / EBolt / 粒子迷雾 / 裂缝 NOP 补丁)   │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │
 ┌───────────────────────────────────▼────────────────────────────────────┐
 │  Phase 6: 实验性深度优化 (L4 智能打脏 / VXL 缓存预热 / 音频并发限频 / 路径缓存)   │
 └────────────────────────────────────────────────────────────────────────┘
```

---

## 二、全项目 Hook 点地址聚类总表（带来源与行号）

本表收录 `tools/extract_hook_tables.py` 扫描提取的核心 Hook 建议，按子系统与物理地址聚类，并逐项交叉标注在现网 `ra2render/blitter_hooks.cpp` 中的实际落地状态：
- **【已装】**：已在现网代码中完整实现并生效（含 v1.6.0 新增项）；
- **【未装】**：理论可行、规格完备，待后续阶段按序落地；
- **【已合并】**：原有方案被更底层的统一方案（如 Inline Hook）替代合并；
- **【冲突废弃】**：存在多方案互斥，经架构裁决判定淘汰废弃；
- **【规划评估】**：涉及联机安全或性能平衡，处于纯调研状态。

### 2.1 L1 高位色软渲染 Blitter 族（Non-RLE & RLE）
| 目标符号 / 模板 | 虚表基址 | 虚表槽 / 挂载地址 | 原始函数入口 | 调用约定 | 来源文档与行号 | 现网状态 | 落地位置 / 说明 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `?$BlitTransXlatAlphaZRead@G` | `0x007E56F0` | `0x007E56F4` (+4) | `0x00494B60` | `__thiscall` (ret 0x20) | `blitter_microkernel_deep_dive.md:14` | **已装** | `blitter_hooks.cpp:164` (SSE2透明块加速) |
| `?$BlitTransXlat@G` | `0x007E5A20` | `0x007E5A24` (+4) | `0x004912B0` | `__thiscall` (ret 0x20) | `blitter_microkernel_deep_dive.md:15` | **已装** | `blitter_hooks.cpp:210` (SSE2向量化) |
| `?$RLEBlitTransXlat@G` | `0x007E55C0` | `0x007E55C4` (+4) | `0x004960A0` | `__thiscall` (ret 0x28) | `rle_blit_family.md:55` | **已装** | `blitter_hooks.cpp:252` (步兵本体主渲染) |
| `?$BlitTrans@G` | `0x007F7BF4` | `0x007F7BF8` (+4) | `0x007BC890` | `__thiscall` (ret 0x20) | `ra2render.h:21` | **已装** | `blitter_hooks.cpp:322` (基础透明软绘制) |
| `?$BlitTransDarken@G` | `0x007E59F0` | `0x007E59F4` (+4) | `0x00492670` | `__thiscall` (ret 0x20) | `blitter_microkernel_deep_dive.md:18` | **已装** | `blitter_hooks.cpp:358` (阴影变暗软渲染) |
| `?$BlitPlain@G` | `0x007F7BC4` | `0x007F7BC8` (+4) | `0x007BC7F0` | `__thiscall` (ret 0x20) | `ra2render.h:27` | **已装** | `blitter_hooks.cpp:394` (纯色填充复制) |
| `?$RLEBlitTransDarken@G` | `0x007E55A0` | `0x007E55A4` (+4) | `0x00496250` | `__thiscall` (ret 0x28) | `blitter_microkernel_deep_dive.md:17` | 未装 (P0) | 步兵地面影子绘制，纯 dst 读改写 |
| `?$RLEBlitTransXlatZRead@G` | `0x007E5560` | `0x007E5564` (+4) | `0x004965B0` | `__thiscall` (ret 0x28) | `rle_blit_family.md:57` | 未装 (P1) | 步兵重叠本体深度遮挡 |
| `?$RLEBlitTransDarkenZRead@G` | `0x007E5540` | `0x007E5544` (+4) | `0x00496820` | `__thiscall` (ret 0x28) | `blitter_microkernel_deep_dive.md:16` | 未装 (P1) | 步兵重叠影子深度遮挡 |
| `?$BlitTransXlatZRead@G` | `0x007E5978` | `0x007E597C` (+4) | `0x00492B00` | `__thiscall` (ret 0x20) | `nonrle_blit_and_named_hotspots.md:236` | 未装 (P1) | 载具重叠本体深度遮挡 |
| `?$BlitTransDarkenZRead@G` | `0x007E5948` | `0x007E594C` (+4) | `0x00492D20` | `__thiscall` (ret 0x20) | `nonrle_blit_and_named_hotspots.md:237` | 未装 (P1) | 载具/建筑投射阴影深度遮挡 |
| `?$RLEBlitTransLucent50@G` | `0x007E5580` | `0x007E5584` (+4) | `0x004963F0` | `__thiscall` (ret 0x28) | `rle_blit_family.md:59` | 未装 (P2) | 50% 半透明心灵/超时空特效 |
| `?$RLEBlitTransZRemapXlat@G` | `0x007E55B0` | `0x007E55B4` (+4) | `0x00496170` | `__thiscall` (ret 0x28) | `rle_blit_family.md:60` | 未装 (P2) | 深度重映射 + 阵营色映射 |

### 2.2 L2 寻敌逻辑与空间粗粒度网格
| 目标符号 / 方法 | 虚表基址 | 挂载地址 / 槽位 | 原始入口 | 调用约定 | 来源文档与行号 | 现网状态 | 落地位置 / 说明 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TechnoClass::SelectAutoTarget` | `0x007F4960` | `0x007F4D84` (v[265]) | `0x006FB010` | `__thiscall` | `targeting_deep_dive.md:386` | **已装** | `blitter_hooks.cpp:442` (帧间隔节流门控) |
| `UnitClass::SelectAutoTarget` | `0x007F5C70` | `0x007F6094` (v[265]) | `0x00736CA0` | `__thiscall` | `targeting_deep_dive.md:387` | **已装** | `blitter_hooks.cpp:448` (单位自动寻敌平抑) |
| `TechnoClass::Greatest_Threat` | `0x007F4960` | `0x007F4D24` (v[241]) | `0x006F8DF0` | `__thiscall` | `targeting_spatial.md:81` | **已合并** | 被 `0x006F8DF0` Inline Hook 取代 |
| `UnitClass::Greatest_Threat` | `0x007F5C70` | `0x007F6034` (v[241]) | `0x00743190` | `__thiscall` | `targeting_spatial.md:82` | **已合并** | 被 `0x006F8DF0` Inline Hook 取代 |
| `Greatest_Threat` 汇聚入口 | — | **`0x006F8DF0`** | `0x006F8DF0` | 9B Trampoline | `targeting_deep_dive.md:397` | **已装** | `blitter_hooks.cpp:486` (目标保持与全域平抑) |
| `SpatialBucket::InitQuery` | — | `0x00412B40` | `0x00412B40` | `__thiscall` | `targeting_spatial.md:400` | 规划评估 | 粗空间桶 `0x00887888` 邻域物化查询 |
| `SpatialBucket::Next` | — | `0x004137A0` | `0x004137A0` | `__thiscall` | `targeting_spatial.md:180` | 规划评估 | 空间网格候选目标弹出枚举 |

### 2.3 L3/L5 星际争霸式战争迷雾与视距剔除（虚表槽 69 族）
| 目标类与方法 | 虚表基址 | 挂载条目地址 | 原始入口 | 调用约定 | 来源文档与行号 | 现网状态 | 落地位置 / 说明 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `UnitClass::Draw` | `0x007F5C70` | `0x007F5D84` (v[69]) | `0x0073CEC0` | `__thiscall` (ret 8) | `vxl_render_sort.md:369` | **已装** | `blitter_hooks.cpp:1502` (战车/载具视距剔除) |
| `InfantryClass::Draw` | `0x007EB058` | `0x007EB16C` (v[69]) | `0x00518F90` | `__thiscall` (ret 8) | `visibility_gap_spysat.md:39` | **已装** | `blitter_hooks.cpp:1515` (步兵视距剔除) |
| `AircraftClass::Draw` | `0x007E22A4` | `0x007E23B8` (v[69]) | `0x004144B0` | `__thiscall` (ret 8) | `visibility_gap_spysat.md:39` | **已装** | `blitter_hooks.cpp:1527` (战机视距剔除) |
| `BuildingClass::Draw` | `0x007E3EBC` | `0x007E3FD0` (v[69]) | `0x0043D290` | `__thiscall` (ret 8) | `building_fog_residual_deep_dive.md:14` | **已装** (v1.6.0) | `blitter_hooks.cpp:1539` (50%残影与风机冻结) |
| `BulletClass::Draw` | `0x007E46E4` | `0x007E47F8` (v[69]) | `0x00468090` | `__thiscall` (ret 8) | `bullet_particle_fog_deep_dive.md:14` | **已装** (v1.6.0) | `blitter_hooks.cpp:1550` (敌方弹道视距剔除) |
| `ParticleClass::Draw` | `0x007EF954` | `0x007EFA68` (v[69]) | `0x0062CEC0` | `__thiscall` (ret 8) | `bullet_particle_fog_deep_dive.md:522` | 未装 (A-4) | 微粒绘制，归属待实证确认 |
| `ParticleSystemClass::Draw` | `0x007EFB9C` | `0x007EFCB0` (v[69]) | `0x0062E280` | `__thiscall` (ret 8) | `bullet_particle_fog_deep_dive.md:523` | 未装 (A-4) | 粒子发射器，尾迹剔除 |
| `AnimClass::Draw` | `0x007E3354` | `0x007E3468` (v[69]) | `0x00422CA0` | `__thiscall` (ret 8) | `fx_draw_chain.md:28` | 未装 | 爆炸动画，建议仅直视判定 |
| `WaveClass::Draw` | `0x007F6BF4` | `0x007F6D08` (v[69]) | `0x0075F9F0` | `__thiscall` (ret 8) | `fx_draw_chain.md:31` | 未装 | 磁暴波/声波，两端直视裁切 |
| `VoxelAnimClass::Draw` | `0x007F6318` | `0x007F642C` (v[69]) | `0x00749B70` | `__thiscall` (ret 8) | `fx_draw_chain.md:32` | 未装 | 体素碎块动画视距剔除 |
| `CellClass::Draw` | — | **`0x004801F0`** | `0x004801F0` | 5B Trampoline | `visibility_gap_spysat.md:367` | **已装** | `blitter_hooks.cpp:1220` (底层灰雾图层合成) |
| `Draw_Fog` 混色桩 B1 | — | **`0x0047F40F`** | `0x0047F40F` | 49B Patch | `visibility_gap_spysat.md:194` | **已装** | `blitter_hooks.cpp:1250` (4帧渐变动态过渡) |
| `Draw_Fog` 混色桩 B2 | — | **`0x0047F4AE`** | `0x0047F4AE` | 51B Patch | `visibility_gap_spysat.md:194` | **已装** | `blitter_hooks.cpp:1256` (4帧渐变动态过渡) |

### 2.4 L4 视口渲染与脏矩形系统
| 目标位置 / 符号 | 内存物理地址 | 原始指令 | 替换指令 / 行为 | 来源文档与行号 | 现网状态 | 落地位置 / 说明 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TacticalClass::Render` 决策点 | **`0x006D3D99`** | `0F 8D 98 00 00 00` (`jge 0x6D3E37`) | `E9 99 00 00 00 90` (`jmp 0x6D3E37; nop`) | `dirty_rect_l4.md:38` | **已装** | `blitter_hooks.cpp:1276` (视口实时保活，防迷雾停滞) |
| `TacticalClass::RegisterDirtyArea` | `0x006D2790` | 入口 | 原版脏矩形合并（58 处调用） | `dirty_rect_l4.md:52` | 未装 | 方案 A 局部打脏底层接口 |
| `CellClass::MarkForRedraw` | `0x00486E70` | 入口 | 格包围盒推入脏区队列 | `dirty_rect_l4.md:53` | 未装 | 方案 A 视野迁移触发打脏接口 |
| `TacticalClass::RegisterCellAsVisible` | `0x006DA7D0` | 入口 | 可见格登记与脏标注入 | `dirty_rect_l4.md:54` | 未装 | 替代全量刷新的局部刷新建议 |

### 2.5 L5 雷达小地图与战地感知
| 目标符号 / 机制 | 拦截地址 | 原始机器码 / 指令 | 目标替换 | 来源文档与行号 | 现网状态 | 落地位置 / 说明 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `RadarClass::Plot_Cell` 主调用点 | **`0x006574C3`** | `E8 88 E7 FF FF` (`call 0x655C50`) | `call Hook_RadarPlot_Callsite` | `radar_minimap_dots.md:12` | **已装** (v1.6.0) | `blitter_hooks.cpp:1449` (已探索半暗灰化+敌点抹除) |
| 雷达无变化跳帧判定调用点 | **`0x0065719A`** | `E8 91 93 00 00` (`call 0x660530`) | `call Hook_RadarPending_Callsite`| `radar_minimap_dots.md:184`| **已装** (v1.6.0) | `blitter_hooks.cpp:1463` (视野迁移强制小地图每帧重刷) |
| `RadarClass::Plot_Cell` 序言跳板 | **`0x00655C50`** | `A1 4C 3D A8 00` (`mov eax, [0xA83D4C]`) | 5B 偷取构造 Trampoline | `radar_minimap_dots.md:183` | **已装** (v1.6.0) | `blitter_hooks.cpp:1435` (供覆写桩尾调用原版) |
| `RadarClass::DrawCell` 内部过滤 | `0x00655F48` | `85 ED` (`test ebp, ebp`) | `jmp` 跳板短路点绘制 | `radar_minimap_dots.md:181` | **冲突废弃** | 被 `0x006574C3` 代理方案取代（见裁决五） |


> **[DA1 勘误 · 2026-09-27]** 本表 `0x006574C3` 行（第 1 行）与 `0x00655C50` 序言行（第 3 行）**已过期**：路线 A 落地后现网安装点为 **`0x00655D38`（9 字节）+ `0x0065719A`**，两个 5 字节备份变量已移除。`0x00655F48` / `0x00655DEB` 的「冲突废弃」结论**不变**。对照见文末 **§6.8**（本节 §2.5 表其余行不改）。

### 2.6 裂缝产生器保护与间谍卫星超武
| 补丁点名称 | 内存地址 (VA) | 原始指令与机器码 | 替换机器码 | 来源文档与行号 | 现网状态 | 落地说明 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `RevealArea2` 破坏裂缝计数写点 | **`0x00568273`** | `mov [ecx+0x134], ebx` (`89 99 34 01 00 00`) | `90 90 90 90 90 90` (6B NOP) | `gap_generator_spysat_deep_dive.md:513` | 未装 (P5) | 彻底保护局部扫图下的裂缝计数 |
| `RevealArea3` 破坏裂缝计数写点 | **`0x00577EC5`** | `mov [eax+0x134], edi` (`89 B8 34 01 00 00`) | `90 90 90 90 90 90` (6B NOP) | `gap_generator_spysat_deep_dive.md:514` | 未装 (P5) | 彻底保护全图开图下的裂缝计数 |
| `Reshroud` 破坏裂缝计数写点 | **`0x00577B60`** | `mov [eax+0x134], ebx` (`89 98 34 01 00 00`) | `90 90 90 90 90 90` (6B NOP) | `gap_generator_spysat_deep_dive.md:515` | 未装 (P5) | 彻底保护重新遮蔽下的裂缝计数 |
| 间谍卫星建筑类型实例阵列 | **`0x00A83C68`** | 建筑类型属性 `SpySat` 置 1 | 启动阶段遍历清零 `SpySat=0` | `gap_generator_spysat_deep_dive.md:650` | **已装** | `blitter_hooks.cpp:1175` (转为临时雷达扫图) |
| 心灵探测分支跳转 | `0x006CD70C` | `call 0x005678E0` | 注入临时全彩直视圆 | `visibility_gap_spysat.md:369` | **冲突废弃** | 侵入性过高，被 NOP 补丁替代 |

### 2.7 屏幕激光、电弧与全域特效链（FX）
| 特效函数符号 | 挂载地址 | 核心循环 / 机制 | 裁切与保护原则 | 来源文档与行号 | 现网状态 | 落地说明 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `LaserDrawClass::DrawAll` | **`0x00550240`** | 倒序遍历 `0x00ABC878` 向量 | 线段首尾格子均无直视时跳过绘制 | `fx_draw_chain.md:37` | 未装 (P5) | 纯表现层，不影响武器杀伤判定 |
| `EBolt::DrawAll` | **`0x004C2830`** | 遍历 `0x008A0E88` 电弧队列 | **必须保留 `Lifetime >>= 1` 衰减**，仅跳过像素 blit | `fx_draw_chain.md:38` | 未装 (P5) | 严禁跳过循环体，否则导致电弧死锁 |
| `RadBeam::DrawAll` | **`0x006591B0`** | 辐射光束循环绘制 | 按两端格子查 `s_visionGrid` 短路 | `fx_draw_chain.md:39` | 未装 (P5) | 纯表现层拦截 |
| `SpotlightClass::DrawAll`| **`0x005FFFA0`** | 探照灯遍历绘制 | 中心与锥形区无直视时跳过 | `fx_draw_chain.md:40` | 未装 (P5) | 性能优化类 |

### 2.8 VXL 体素管线、朝向矩阵与阴影表
| 核心方法 / 结构 | 关键地址 | 虚表槽位 | 规范职责与裁决 | 来源文档与行号 | 现网状态 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `UnitClass::DrawIfVisible` | `0x0073B0B0` | v[65] | **严禁在此做迷雾拦截**（见裁决一） | `vxl_render_sort.md:368` | **冲突废弃** |
| `ObjectClass::DrawIfVisible` | `0x005F4B10` | v[65] | **严禁在此做迷雾拦截**（见裁决一） | `vxl_render_sort.md:367` | **冲突废弃** |
| `DrawAsVXL` | `0x0073B470` | v[341] | **仅用于 VXL 缓存统计与 LOD 降采**，禁做迷雾剔除 | `vxl_render_sort.md:370` | 未装 (P6) |
| `TechnoClass::Draw_A_VXL` | `0x00706640` | — | 状态机/调色板绑定，可注入降分辨率光栅 | `vxl_render_sort.md:372` | 规划评估 |
| VXL 软件光栅核心 | `0x00707480` | — | 视锥包围盒分配与 `SelectRLEBlitter` 分发 | `vxl_render_sort.md:373` | 规划评估 |
| 视口对象 Y-Sort 排序序 | `0x006D8DB0` | — | **严禁打乱先影后体及 Y 序**，防止深度撕裂 | `vxl_render_sort.md:381` | **冲突废弃** |

### 2.9 路径搜索与机动运动学（Locomotion）
| 关键插桩点 | 内存地址 | 目标行为 | 风险判定与约束 | 来源文档与行号 | 现网状态 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `FootClass::UpdatePathfinding` | `0x004D3E4B` | `call 0x004CBBA0` 前做同源同目的地路径缓存短接 | 中：必须确保只对无碰撞动态路网生效 | `pathfinding_deep_dive.md:351` | 规划评估 |
| `WalkLocomotionClass::Process` | `0x0075AF65` | 重寻路触发限频与阶梯降频 | 高：改动步频会影响碰撞推进，须谨慎 | `pathfinding_locomotion.md:88` | 规划评估 |
| `PathFinder::FindPath` | `0x0042C900` | A* 算法单例入口，AStar 启发式剪枝 | 高：必须保持多客户端寻路确定性结果一致 | `pathfinding_deep_dive.md:382` | 规划评估 |

### 2.10 音频引擎并发削峰与输入热点
| 目标函数 | 内存地址 | 调用约定 | 优化方案与约束 | 来源文档与行号 | 现网状态 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `VocClass::PlayGlobal` | `0x00750920` | `__fastcall` | 基于 `(SoundID, FrameTimestamp)` 实施 80ms 跨单位削峰 | `audio_engine_deep_dive.md:14` | 未装 (P6) |
| `VocClass::PlayAt` | `0x007509E0` | `__fastcall` | 3D 空间音效按视口距离实施衰减与同频去重 | `audio_engine_deep_dive.md:15` | 未装 (P6) |
| `AudioFrameUpdate` | `0x00406F70` | `__cdecl` | 保持 33ms 节流节奏，防声卡 DirectSound 缓冲区爆满 | `audio_engine_deep_dive.md:16` | 保留基线 |

### 2.11 内存分配器、CRT 堆与小对象池
| 挂载点 | 内存地址 | 原始实现 | 改造规格与收益 | 来源文档与行号 | 现网状态 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Win32 LFH 激活 | Windows API | 系统默认堆 | 遍历 `GetProcessHeaps` 激活低碎片堆 (LFH) | `crt_memory_pool_deep_dive.md:733` | **已装** (`blitter_hooks.cpp:113`) |
| CRT `_new` 操作符 | `0x007C8E17` | `malloc` 封装 | 定向拦截 352B (`Bullet`) 与 312B (`Particle`) 定长池 | `crt_memory_pool_deep_dive.md:735` | 规划评估 |
| CRT `_delete` 操作符 | `0x007C8E3F` | `free` 封装 | 回收至对应定长小对象高速池 | `crt_memory_pool_deep_dive.md:735` | 规划评估 |

### 2.12 UI 侧边栏、框选与命令分发
| 涉及模块 | 关键地址 | 语义特征 | 约束与裁决 | 来源文档与行号 | 现网状态 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Cameo 图标绘制门控 | `0x006A9540` | `AllowedToDraw/NeedsRedraw` | 纯表现层，未展开前禁止绘制 | `sidebar_selection_ui.md:395` | 规划评估 |
| 框选对象线性扫描 | `0x006DA5C0` | `Tactical::ForEachInRect` | 仅在鼠标松开时触发，必须严格保持原枚举序 | `sidebar_selection_ui.md:397` | 规划评估 |
| 网络命令打包分发 | `0x0064C380` | `NetworkEvent` 环形缓冲 | **严禁拦截改写**，属于锁步核心通道 | `net_sync_checksum.md:232` | 严禁改动 |

---

## 三、核心冲突深度裁决详述（Core Conflict Arbitrations）

### 3.1 冲突一：0x73B0B0 / 0x73B470 / 0x73CEC0 / 0x6D8DB0（VXL 体素渲染 vs 特效绘制链双重建议冲突）
- **重叠点与争议**：
  * `vxl_render_sort.md` 提出了 `H-VXL1`（`0x005F4B10`）、`H-VXL2`（`0x0073B0B0`）、`H-VXL3`（`0x0073CEC0`）、`H-VXL4`（`0x0073B470`）及 `H-VXL15`（`0x006D8DB0`）等多处拦截建议。
  * `fx_draw_chain.md` 提出了 `H-FX1`（`0x005F4B10`），建议在基类 `ObjectClass::DrawIfVisible`（v[65]）统一加 `ShouldDrawEffect` 门控以通杀所有继承类。
- **深度根因分析**：
  1. **虚表调用链的先后关系**：原版引擎的渲染流水线严格遵循：  
     `TacticalClass::Render`  
     &emsp;└─ `0x006D8DB0`（对象排序）  
     &emsp;&emsp;└─ `call vtable[65]`（`DrawIfVisible` `0x005F4B10` / `0x0073B0B0`）  
     &emsp;&emsp;&emsp;└─（视口裁剪通过后）`call vtable[69]`（`Draw` `0x0073CEC0`）  
     &emsp;&emsp;&emsp;&emsp;└─（判断 `UnitType+0x236`）`call vtable[341]`（`DrawAsVXL` `0x0073B470`）
  2. **基类早退导致的残影破坏**：若在 v[65]（`0x005F4B10` 或 `0x0073B0B0`）处因“无直视”而直接 `ret`，则后续的 v[69]（`Draw`）**完全不会被执行**！然而，现网已落地的星际三态迷雾高度依赖在槽 69 中实现建筑的 50% 残影蒙版、雷达天线旋转暂停以及起火特效隐藏。如果在 v[65] 短路，不仅会破坏单位逻辑，还会把建筑残影机制彻底抹杀。
  3. **VXL 重复门控的冗余性**：`0x0073CEC0` 已经安装了 `Hook_Unit_Draw`，所有机动单位在未探明或失去直视时已被 100% 剔除。若在下游的 `0x0073B470`（`DrawAsVXL`）再加迷雾判断，属于无意义的重复计算。
  4. **重排序导致的穿模撕裂**：原版渲染器的大量 Blitter（如 `BlitTransDarkenZRead`）仅执行 `ZRead`（深度测试）而不执行 `ZWrite`（深度写入），完全依赖引擎在 `0x006D8DB0` 建立的稳定 Y-sort 序列。若为了 VXL 批量渲染而在 `0x006D8DB0` 重新排序，会导致地面阴影切断车体、建筑顶盖深度翻转等严重图形撕裂。
- **架构裁决结论**：
  > [!IMPORTANT]
  > **裁决结果**：
  > 1. **全面废弃 v[65]（`0x005F4B10` / `0x0073B0B0`）的迷雾短路建议**。迷雾视距门控必须且只能收口在虚表槽 69。
  > 2. **锁定 `0x0073CEC0` 为 Unit 唯一迷雾拦截点**。`0x0073B470`（`DrawAsVXL`）仅作为后续 VXL 缓存（`SomeVoxelCache`）命中率采样与降分辨率光栅化的专用接口，禁止注入迷雾逻辑。
  > 3. **严禁在 `0x006D8DB0` 打乱对象绘制顺序**。禁止重排任何 Y-sort 结构，确保深度遮挡绝对正常。

---

### 3.2 冲突二：虚表槽 69（ObjectClass::Draw 族多态拦截与生命周期安全）
- **重叠点与争议**：
  * 槽 69（偏移 `+0x114`）汇集了几乎所有可视游戏对象。`bullet_particle_fog_deep_dive.md`、`building_fog_residual_deep_dive.md`、`visibility_gap_spysat.md` 与 `fx_draw_chain.md` 针对槽 69 提出了多达 10 个派生类的挂接需求（`Unit`, `Infantry`, `Aircraft`, `Building`, `Bullet`, `Particle`, `ParticleSystem`, `Anim`, `Wave`, `VoxelAnim`）。
  * 严重风险：是否存在多模块重复 Patch 虚表指针的风险？各派生类生命周期与物理 Update 是否会被 Draw 误杀？
- **深度根因分析**：
  1. **虚表指针单写者原则**：同一虚表槽（例如 `BulletClass` 虚表条目 `0x007E47F8`）若被迷雾模块与特效模块重复覆写，会导致 Trampoline 链混乱，甚至造成解除挂钩（`RemoveVTableHooks`）时内存写飞。
  2. **纯表现层与确定性解耦**：
     - `BulletClass`：在游戏逻辑中，导弹飞行、碰撞判定由 `BulletClass::AI/Update`（槽 23 `0x007E4740`）与 `BulletClass::Detonate`（`0x004690B0`）驱动。只要**只拦截槽 69（Draw）**，未探索迷雾中的 V3 火箭虽然在本地屏幕上不可见，但物理飞行轨迹、命中逻辑与伤害结算 100% 正常推进，两端完全同步。
     - 若开发者误将拦截点前移至 `BulletClass::AI`，将直接引发联机致命 Desync（OOS）。
  3. **微粒（Particle）与微粒系统的从属缺失**：`BulletClass` 内部拥有明确的发射源指针 `Owner (+0xB0)`，可穿透查得所属阵营 `OwnerHouse (+0x21C)`。但 `ParticleClass`（`0x0062CEC0`）多由环境（如着火建筑、废墟、烟囱）生成，其内存结构中无标准化阵营指针，若贸然短路会导致己方基地着火烟雾被误杀。
- **架构裁决结论**：
  > [!IMPORTANT]
  > **裁决结果**：
  > 1. **槽 69 实行统一命名空间单点安装**：所有槽 69 的挂载必须严格收敛在 `ra2render/blitter_hooks.cpp` 的 `FogHooks::` 类中，严禁在其他模块二次篡改。
  > 2. **Bullet 拦截范围红线**：只允许劫持 `0x007E47F8`（Draw），严禁修改槽 23（Update）与 Detonate。
  > 3. **微粒拦截准入前置条件**：`ParticleClass`（`0x007EFA68`）与 `ParticleSystemClass`（`0x007EFCB0`）在任务 A-4 给出明确的宿主归属证据前，保持未装状态；落地时直接扩展现有的 `Hook_Bullet_Draw`，严禁多头安装。

---

### 3.3 冲突三：寻敌 0x006F8DF0（Greatest_Threat 9 字节 Inline Hook vs 原版虚表劫持）
- **重叠点与争议**：
  * 早期规范（v1.0.0）试图通过覆写 `TechnoClass` 虚表条目 `0x007F4D24` 与 `UnitClass` 虚表条目 `0x007F6034` 来实现 `Greatest_Threat` 拦截。
  * `targeting_spatial.md` 指出现网 `InstallVTableHooks` 遗漏了这两处挂钩，但在 `blitter_hooks.cpp:486` 却存在一个直接针对汇编入口 `0x006F8DF0` 的 9 字节 Inline Hook。
- **深度根因分析**：
  1. **C++ 虚表覆盖的局限性**：
     反汇编证实，`InfantryClass`（`0x007EB058`）、`BuildingClass`（`0x007E3EBC`）、`AircraftClass`（`0x007E22A4`）和 `FootClass`（`0x007E8C94`）各自拥有独立虚表，且虚表槽 241 分别指向 `0x0051E140`、`0x00445F00`、`0x004D9920`！
     如果仅挂 `TechnoClass`（`0x007F4D24`）和 `UnitClass`（`0x007F6034`），步兵、防御塔和空军的寻敌完全无法被平抑。
  2. **底层汇聚点的唯一性**：
     深入追踪上述派生类函数发现，它们在准备好参数后，最终全部通过 `call 0x006F8DF0` 调用全局共享的威胁评估扫描体！
  3. **9 字节 Inline Hook 的完备性**：
     `0x006F8DF0` 的函数序言为经典的 9 字节：`sub esp, 0x100` / `push ebx` 等。现网代码通过复制前 9 字节构建 14 字节 Trampoline，并打入 `jmp rel32 + nop`，一次性 100% 覆盖了全游戏所有作战单位、步兵、建筑与空军的寻敌入口。
- **架构裁决结论**：
  > [!IMPORTANT]
  > **裁决结果**：
  > 1. **裁定 0x006F8DF0 Inline Hook 为全游戏唯一合法寻敌挂钩点**。
  > 2. **虚表槽 `0x007F4D24` 与 `0x007F6034` 裁定为“已合并/淘汰废弃”（Merged/Superseded）**，无需在 `InstallVTableHooks()` 中补充挂接代码，避免重复多层开销。
  > 3. **枚举确定性红线**：原版打分函数 `0x006F7CA0` 在打分相同时遵循严格的原枚举顺序（`>` 严格大于）。寻敌 Hook 必须保持存活目标保持（Retention）与时间片平抑机制，严禁修改候选目标的枚举遍历顺序。

---

### 3.4 冲突四：视口刷新 0x006D3D99（jge 原版直通 vs RegisterCellAsVisible 局部打脏 vs jmp 0x6D3E37 全量刷新）
- **重叠点与争议**：
  * 原版 `0x006D3D99` 处的指令为 `0F 8D 98 00 00 00`（`jge 0x006D3E37`）。
  * 现网 v1.5.0–v1.6.0 落地项打入补丁 `E9 99 00 00 00 90`（`jmp 0x006D3E37; nop`），强制每帧全量重绘视口，彻底解决了静止视角下单位移动后迷雾不退回的恶性 Bug。
  * `dirty_rect_deep_dive.md` 指出全量重绘带来了额外的像素填充开销；同时深入反汇编揭示了关键真相：`CellClass::MarkForRedraw (0x00486E70)` 传递 `bFlag = false`，在 Pass 2（`0x006D3812`）直接被跳过，**无法驱动地表与灰雾瓦片重绘**；真正的 Westwood 原生迷雾打脏收口是 **`TacticalClass::RegisterCellAsVisible (0x006DA7D0)`**（置入 `VisibleCells[800]`，置 `Redrawing = 1`，完整驱动 Pass 1~8 全部渲染阶段）。
- **深度根因分析与折中推导**：
  1. **迷雾视觉正确性为第一优先级（零延迟退回）**：
     依据《确定性红线》第 4 条，静止视角迷雾零延迟退回是不可逾越的体验底线。但全量重绘每帧无条件刷新全视口（~800 格及全部物体），在 4K/高分辨率下吃满带宽。
  2. **基于 RegisterCellAsVisible 的局部打脏可行性**：
     在 `UpdateVisionGrid` 中对比本帧与上一帧的视野状态，双向精确收集翻转格（Visible→Fog 与 Fog→Visible），并**外扩 1 圈（3×3 邻域）**调用 `RegisterCellAsVisible (0x006DA7D0)`。当单帧翻转格超过安全阈值（>350 格，如核弹、心灵探测全图扫图）时，自动回退为全屏全量重绘，杜绝任何溢出或丢帧。
  3. **基线测量先决条件**：
     局部打脏能否显著降低 CPU 耗时且保持绝对画质无撕裂，依赖 Q1 可信基线（帧率、CPU0、TickMiss）的真实测量对比。
- **架构裁决结论（Lead 最新裁决）**：
  > [!IMPORTANT]
  > **裁决结果**：
  > 1. **`0x006D3D99` 确立为“可切换折中架构”**：不再绝对锁定为不可变更的全量刷新，也不过早降为边缘实验项，而是以配置开关形式引入两态切换通道（`[Render] L4DirtyMode = force-full | vision-dirty`）。
> 【W3 勘误 · W3-A6/ISSUE-SECTION-L4DIRTYMODE】改前：[Render] L4DirtyMode；改后：[FogOfWar] L4DirtyMode=force-full；依据：ra2render/blitter_hooks.cpp:757; ra2render/ra2render.ini:251；分级：P0
  > 2. **默认值策略**：当前暂以 `force-full`（现网全量刷）保持基线稳定性；待 Q1 基准 harness 完成 U200/U800 真机对比测量后，若 `vision-dirty`（调用 `0x006DA7D0`，外扩 1 圈，>350 格全屏保底）确证能带来正向收益且 0 瑕疵，则平滑升级为默认策略。
  > 3. **与各文档一致性**：本裁决与 `docs/re/dirty_rect_deep_dive.md` 结论完全自洽并取代早期的粗糙方案。

---

### 3.5 冲突五：小地图 0x00655F48（DrawCell 点过滤） vs 0x006574C3（RadarPlot_Cell 代理覆写）
- **重叠点与争议**：
  * 原版小地图在探索后的灰雾区泄漏敌方单位点。
  * `radar_minimap_dots.md` 提出了 P0 建议：在 `0x00655C50` 内层的 `0x00655F48`（`test ebp, ebp`）挂 Inline Hook 跳过点像素绘制。
  * 现网 v1.6.0 采用了全新方案：在 `0x00656EC0` 雷达主循环的调用点 `0x006574C3` 拦截 `call 0x00655C50`，先由原版画点，随后从地形表面缓存取色减半覆写；并拦截 `0x0065719A` 抑制跳帧。
- **深度根因分析**：
  1. **三态小地图的完整语义需求**：
     `0x00655F48` 方案只能过滤红点，**完全无法将小地图探索区的地形变暗**，小地图依然是全彩的，与主视口的灰雾完全脱节。
  2. **地形原色 50% 减半与敌点抹除的一体化**：
     现网 `0x006574C3` 方案通过读取 `RadarClass+0x1220`（`BSurface` 地形缓存）的未受污染原色，执行 `(color >> 1) & 0x7BEF` 减半后写回工作表面（`+0x121C`），**一次性把全彩地形降级为半透明灰雾，并将已经画下的敌方单位点彻底抹去**，视觉表现极其惊艳。
  3. **跳帧抑制的关键协同**：
     雷达存在“全局无变化即跳帧”的节流机制（`0x00660530`）。若只改点绘制，当敌人停步时小地图停止刷新，敌点无法实时退散。现网搭配劫持 `0x0065719A`，由 `s_minimapForceRefresh` 在视野变更时强刷小地图，解决了停步不刷新的死结。
- **架构裁决结论**：
  > [!IMPORTANT]
  > **裁决结果**：
  > 1. **裁定 0x006574C3（调用点覆写）+ 0x0065719A（跳帧抑制）为小地图唯一合法落地实现**。
  > 2. **裁定 0x00655F48 点过滤方案为“冲突废弃”（Conflict/Discarded）**。严禁在 `0x00655F48` 再挂任何钩子，避免引起双重分支破坏。

> **[路线 A 后订正 · 2026-09-27]** 现网安装点为 Plot_Cell 内部 **`0x00655D38`**（9 字节：`E9 rel32` + 4×`90`）+ **`0x0065719A`** 强刷（5 字节 `call` 等长）；`0x006574C3` / `0x00655C50` 仅存 `ra2render.h:76-77` 死宏（cpp 零引用）。原「唯一合法落地实现 = `0x006574C3`（调用点覆写）」的裁决**由本订正取代**；**`0x00655F48` 废弃结论不变**。详见文末 §6.8。

---

### 3.6 冲突六：裂缝产生器引用计数破坏 Bug（0x00568273 等）与超武雷达透缝
- **重叠点与争议**：
  * 原版西木在 `MapClass::RevealArea2`（`0x00568273`）、`RevealArea3`（`0x00577EC5`）与 `Reshroud`（`0x00577B60`）中，硬编码执行 `mov [cell+0x134], 0`，暴力抹杀了地块上的 `GapsCoveringThisCell` 裂缝覆盖计数！导致一旦玩家使用间谍卫星或超武心灵探测扫图后，敌方裂缝产生器永久失灵，再也无法遮蔽。
  * `visibility_gap_spysat.md` H10 建议在 `SuperClass::Launch`（`0x006CD70C`）重写分支。
  * `gap_generator_spysat_deep_dive.md` 提出了直接针对这三处破坏性写指令进行 6 字节 NOP（`90 90 90 90 90 90`）的热补丁方案。
- **深度根因分析**：
  1. **状态机脱节根因**：建筑自身持有 `BuildingClass::GeneratingGap` 状态位，由于建筑自检认为自己正在发电且状态为 true，因此绝不会重新调用 `CreateGap()`。地图格计数被归零后，后续即便调用遮蔽函数，由于引用计数为 0，地块永久裸露。
  2. **NOP 补丁的微创优势**：三处写点均是单条 6 字节指令（`89 99 34 01 00 00` 等），NOP 化后既阻止了对裂缝计数的破坏，又完全保留了开图函数的其他探索位（bit3）逻辑，改动最小且 100% 确定性安全。
- **架构裁决结论**：
  > [!IMPORTANT]
  > **裁决结果**：
  > 1. **采纳三处 6 字节 NOP 热补丁方案**，废弃重写 `SuperClass::Launch` 的高风险方案。
  > 2. **落地规格收敛**：在 Phase 5 中通过 VirtualProtect 将 `0x00568273`、`0x00577EC5`、`0x00577B60` 各替换为 6 个 `0x90`，并由 ini 键 `EnableGapProtection=1` 进行统一开关与干净回滚。
> 【W3 勘误 · W3-A6/ISSUE-DEFAULT-GAPPROTECTION】改前：EnableGapProtection=1；改后：EnableGapProtection=0  ; [代码/出厂默认0，安全侧；测试或启用时显式置1]；依据：ra2render/blitter_hooks.cpp:606; ra2render/ra2render.ini:199; config_key_matrix.md:109；分级：P0

---

## 四、全项目唯一推荐落地顺序表（Canonical Landing Sequence）

依据依赖拓扑、架构仲裁及系统风险等级，确立全项目唯一的唯一推荐落地顺序表。后续所有功能的开发、集成与验证必须严格依照此顺序推进，严禁跨阶段盲目合入。

| 阶段 (Phase) | 推荐落地项 / Hook 名称 | 核心内存地址 (VA) | 挂接机制类型 | 前置依赖项 | 互斥 / 冲突关系 | 对应 INI 独立开关键 | 回滚机制 (Rollback) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Phase 0**<br>系统环境基座 | LFH 低碎片堆激活 | Windows API | 系统 API 调用 | 无 | 无 | `[System] EnableLFH=1` | 设为 0 跳过调用 |
| | 高精度媒体定时器 | Windows API | `timeBeginPeriod` | 无 | 无 | `[System] HighPrecisionTimer=1` | `timeEndPeriod` 还原 |
| | 原版调速解绑保护 | `0x00A8EB60` / `0x00887350`| 纯只读保护 | 无 | 严禁强行锁死 GameSpeed | `[Speed] UnlockGameSpeed=0` | 默认保持原版控制权 |
| **Phase 1**<br>L1 渲染微内核 | 6 族基础 Non-RLE 虚表 | `0x007E56F4` 等 6 处 | 虚表 Slot 1 覆写 | Phase 0 | 无 | `[Render] EnableSIMD=1` | 还原原虚表条目指针 |
| | RLE 步兵本体绘制 | `0x007E55C4` | 虚表 Slot 1 覆写 | Phase 0 | 无 | `[Render] EnableSIMD=1` | 还原原虚表条目指针 |
| | RLE 步兵影子绘制 (P0) | `0x007E55A4` | 虚表 Slot 1 覆写 | Phase 1 基线 | 无 | `[Render] EnableSIMD=1` | 还原原虚表条目指针 |
| | RLE/Non-RLE 深度读写 (P1) | `0x007E5564` / `0x007E594C`| 虚表 Slot 1 覆写 | Phase 1 基线 | 无 | `[Render] EnableSIMD=1` | 还原原虚表条目指针 |
| **Phase 2**<br>L2 寻敌平抑 | `SelectAutoTarget` (Techno) | `0x007F4D84` (v[265]) | 虚表槽覆写 | Phase 0 | 无 | `[Logic] TargetScanInterval=8` | 还原原虚表条目指针 |
| | `SelectAutoTarget` (Unit) | `0x007F6094` (v[265]) | 虚表槽覆写 | Phase 0 | 无 | `[Logic] TargetScanInterval=8` | 还原原虚表条目指针 |
| | `Greatest_Threat` 汇聚入口 | **`0x006F8DF0`** | 9B Inline Hook | Phase 0 | **互斥并取代虚表 241** | 内部计数平抑门控 | 还原前 9 字节原始机器码 |
| **Phase 3**<br>L3 战争迷雾核心 | `CellClass::Draw` 灰雾合成 | **`0x004801F0`** | 5B Inline Hook | Phase 1 | 无 | `[FogOfWar] EnableStarCraftFog=1` | 还原前 5 字节原始机器码 |
| | 4 帧灰雾渐变混色桩 | `0x0047F40F` / `0x0047F4AE`| 49B/51B Patch | `0x004801F0` | 依赖 `s_visionGrid` | `[FogOfWar] FadeFogTransition=1` | 还原两处原始补丁机器码 |
| | 视口渲染保活强制跳转 | **`0x006D3D99`** | 6B Byte Patch | `0x004801F0` | **互斥并强制取代原版 jge** | `[FogOfWar] EnableStarCraftFog=1` | 还原 `0F 8D 98 00 00 00` |
| | 机动单位视距剔除 (Unit/Inf/Air)| `0x007F5D84` 等 3 槽 | 虚表槽 69 覆写 | `0x004801F0` | 无 | `[FogOfWar] EnableStarCraftFog=1` | 还原原虚表条目指针 |
| **Phase 4**<br>L5 战地感知进阶<br>(v1.6.0 基线) | 建筑 50% 残影与风机冻结 | `0x007E3FD0` (v[69]) | 虚表槽 69 覆写 | Phase 3 | **严禁在 v[65] 提前短路** | `[FogOfWar] EnableBuildingFog=1` | 还原原虚表条目指针 |
| | 敌方弹道视距隐形剔除 | `0x007E47F8` (v[69]) | 虚表槽 69 覆写 | Phase 3 | **严禁触碰 Update/Detonate**| `[FogOfWar] EnableBulletFog=1` | 还原原虚表条目指针 |
| | 雷达小地图主循环覆写 | **`0x006574C3`** | 5B Callsite Replace| Phase 3 | **互斥并废弃 0x655F48 点过滤** | `[FogOfWar] EnableMinimapFog=1` | 还原 `call 0x00655C50` |
| | 雷达跳帧抑制强刷判定 | **`0x0065719A`** | 5B Callsite Replace| `0x006574C3` | 无 | `[FogOfWar] EnableMinimapFog=1` | 还原 `call 0x00660530` |

> **[DA1 订正 · 2026-09-27]** 上两行（以及 §0 拓扑图 Phase 4 行的 `0x6574C3 雷达覆写`、§2.5 表、§3.5 裁决、§6.2 重复建议表的 `0x006574C3` 条目）中的**安装地址已过期**：现网（路线 A）为 `0x00655D38`（9 字节 `E9 rel32` + 4×`90`，跳板回 `0x00655D41`）+ `0x0065719A`（5 字节 `call` 等长）；`0x006574C3` 仅存 `ra2render.h:77` 死宏。**`0x00655F48` 废弃裁决与「互斥并废弃 0x655F48」结论不变。** 逐条对照见文末 **§6.8.4**。
| | 间谍卫星扫图状态机改造 | `0x00A83C68` 遍历 | 内存属性重置 | Phase 3 | 依赖 `s_radarSweepExpireFrame` | `[FogOfWar] EnableSpySatRadarSweep=1` | 启动时保持 SpySat 原值 |
| **Phase 5**<br>微粒与特效闭环 | 微粒与尾迹绘制剔除 (A-4) | `0x007EFA68` / `0x007EFCB0`| 虚表槽 69 覆写 | Phase 4 | 必须验证 Owner 偏移 | `[FogOfWar] EnableParticleFog=1` | 还原原虚表条目指针 |
| | 裂缝产生器 NOP 保护补丁 | `0x00568273` 等 3 处 | 3 × 6B NOP 补丁 | Phase 4 | **互斥并取代 SuperClass 覆写**| `[FogOfWar] EnableGapProtection=1` | 还原原始 `mov` 机器码 |
| | 激光与电弧直视裁剪 | `0x00550240` / `0x004C2830`| 内部遍历裁剪 | Phase 3 | **EBolt 必须保留 Lifetime 衰减** | `[Render] EnableFXFogCull=1` | 跳过遍历内短路分支 |
| **Phase 6**<br>实验性深度优化 | 视口局部打脏折中切换 | `0x006D3D99` + `0x006DA7D0`| 恢复 jge + 局部打标 | Phase 3/4 全通 | **必须外扩 1 圈，>350 格回退全屏**| `[Render] L4DirtyMode=force-full` | 默认全量刷，待 Q1 测量后裁定默认值 |
| | VXL 缓存与降采光栅 | `0x0073B470` / `0x00707480`| 函数包装 / 注入 | Phase 1 | **严禁打乱 0x6D8DB0 绘制序** | `[Render] EnableVXLCacheOpt=0` | 原样转入原版光栅流程 |
| | 智能音效并发削峰 | `0x00750920` / `0x007509E0`| `__fastcall` 包装 | Phase 0 | 无 | `[Audio] EnableSmartAudioLimit=1`| 原样放行所有 Play 调用 |
| | 路径搜索缓存加速 | `0x004D3E4B` | 调用点挂钩 | Phase 0 | **严禁改动 A* 启发式确定性** | `[Logic] EnablePathCache=0` | 原样调用 `0x004CBBA0` |

---

## 五、确定性与联机安全红线约束（Multiplayer Synchronization Redlines）

依照 `net_sync_checksum.md` 与总台账规范，全项目所有二进制修改必须严格遵守以下确定性分级契约，杜绝任何引发联机同步断开（SYNC%01d.TXT / Out of Sync）与存档损坏的隐患：

```
                              联机确定性红线隔离边界
 ┌────────────────────────────────────────────────────────────────────────┐
 │ 🔴 绝对红线 (严禁触碰/严格保持):                                           │
 │   - 逻辑主循环帧步进 (MainLogicFrame 0x0055D360 / 0x0055DE40)           │
 │   - 网络包执行器 (NetworkEvent 0x004C6CB0 / 0x0064C380)                 │
 │   - 随机数生成器 (局内 ScenarioClass::Random 0x00A8B230+0x218，禁改调用序) │
 │   - 帧 CRC 与对象 Checksum (CurrentFrameCRC 0x00AC51FC / v[13])         │
 │   - 单位动力学与杀伤更新 (Bullet::Update 0x4666E0 / Loco::Process)        │
 │   - 寻敌最高分平分时的原枚举序 (Greatest_Threat 遍历顺序)                   │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │ 物理/表现绝对隔离
 ┌───────────────────────────────────▼────────────────────────────────────┐
 │ 🟢 允许改造 (纯表现层安全 Hook):                                          │
 │   - 16-bit 软渲染像素混合 (Blitter / RLEBlitter SSE2 向量化)             │
 │   - 视口图层渲染与剔除 (ObjectClass::Draw 槽 69 视距裁剪)                 │
 │   - 屏幕后缓冲区脏矩形刷新 (TacticalClass::Render 视口保活)                │
 │   - 雷达小地图工作表面与地形缓存覆写 (RadarClass::Plot_Cell)               │
 │   - 屏幕激光/电弧表现层裁剪 (LaserDraw::DrawAll)                         │
 │   - 本地声卡混音并发削峰 (VocClass::PlayGlobal / PlayAt)                 │
 │   - 进程堆分配模式优化 (Windows Low Fragmentation Heap)                  │
 └────────────────────────────────────────────────────────────────────────┘
```

1. **绝对禁动区域（Bit 级锁步一致）**：
   - **严禁修改随机数消费次数与顺序**：局内随机数生成器仅此一家（`ScenarioInstance+0x218`），每逻辑帧在**帧 CRC 路径共消费 2 次**（`0x0064DE3F` 折叠抽取 + `0x0064DE70 → 0x00650A90` 帧尾抽取各 1 次）。〔勘误 ASM-FIX2-1：原记「固定消费 1 次」，其锚点 `0x0064DAD9` 已四重证伪（字节串全镜像 0 命中、非函数入口、非指令边界）；本行是门控决策依据，按实测更正后**约束更强** —— 两次都不能动。〕任何渲染剔除、音效播放、UI 点选逻辑严禁调用局内 Random。
   - **严禁修改命令队列与执行序**：网络命令在 `0x4C6CB0` 严格按到期帧回放，右键与点选必须入队回环，严禁在本地直接写死对象内部指令。
   - **严禁修改弹道与单位物理更新**：`BulletClass::Update`、`MoveTo`、`Detonate` 以及各 `LocomotionClass` 的 `Process` 决定弹药命中与碰撞，绝不可因迷雾视距不可见而跳过物理推进。
2. **安全改造准则（表现层解耦）**：
   - 所有的剔除必须发生在 `Draw`（虚表槽 69）或其下游光栅函数内部。本地屏幕不画，但内存中对象的位置、朝向、血量、存活状态完全保持不变。
   - 任何新增的 Hook 必须提供独立的 INI 开关、独立的遥测指标（Telemetry）、并在 DLL 卸载（`RemoveVTableHooks`）时能够逐字节无损还原至官方 1.001 机器码状态。


---

## 六、复审小节（2026-09-26 · Hook 冲突矩阵复审与落地缺口总表）

> **范围**：`docs/re/*.md` 全量 Hook 建议重抽取 × 现网 `ra2render/blitter_hooks.cpp` 已装点 ×
> `pending_execution_master_table.md` 18 项落地包 × 「审计结论 vs 现网源码」一致性核对。
> **红线**：只读 `gamemd.exe` / `ra2render/**` / 顶层台账；本文仅原地追加，不改 §一–§五。
> **产出**：`out/re_work/hook_matrix/`（抽取脚本、原始表、精分类、`claims.txt`）。
> **门禁**：`tools/verify_anchors.py` **323/323 PASS**；`tools/audit_bytes.py out/re_work/hook_matrix/claims.txt` **40/40 OK**。

### 6.0 勘误块（改前 → 改后）

| ID | 位置 | 改前（过期表述） | 改后（与现网源码对齐） | 依据 |
|---|---|---|---|---|
| **E-1** | `INSTALLED_HOOKS_AUDIT.md` §4-B1 / `MP_SAFETY_REVIEW.md` §0,#7/#8/#9 | 「三处 `unitHash = (uintptr_t)pThis >> 4`（:404/:425/:463）→ #7/#8/#9 = **VIOLATION**」 | **默认 `TargetScanKey=position` 已改为 ThrottleKey 坐标哈希**（`blitter_hooks.cpp:160-184`，调用点 :436/:457/:495）→ #7/#8/#9 在默认键下降为 **RISK（待对拍）**；仅 `TargetScanKey=pointer` 分支仍 **VIOLATION**。行号 404/425/463 **过期** | `blitter_hooks.cpp:160-184,436,457,495`；`hook_gate_gap_table.md:36,137-142` |
| **E-2** | `mp_release_safety_checklist.md` R-01 / 若干 dispatch | 「`EnableMinimapFog` 默认已置 0」 | **工作树未落地**：API 默认仍为 `1`（`blitter_hooks.cpp:103`），双份 ini 均 `EnableMinimapFog=1`（`ra2render.ini:45` / `ra2youli/ra2render.ini:45`） | 源码+ini 实测；`MP_SAFETY_REVIEW.md:464` 已有同款勘误 |
| **E-3** | `INSTALLED_HOOKS_AUDIT.md` §2.6 / 本文 §2.5（历史） | 雷达装在 `0x006574C3`（调用点）+ `0x00655C50` 序言 | **路线 A 下沉**：现网实际打 `0x00655D38`（9B）+ `0x0065719A`；`ADDR_RADAR_PLOT` / `ADDR_RADAR_PLOT_CALLSITE` 在 cpp 中零引用（死宏） | `blitter_hooks.cpp:1466-1515`；dispatch `2026-09-26_1852`「路线 A 下沉」 |
| **E-4** | `INSTALLED_HOOKS_AUDIT.md` 头注 / `MP_SAFETY_REVIEW.md` 头注 | 「`blitter_hooks.cpp`（1757 行）」及 :404/:425/:463 | 当前源文件 **1788 行**；节流三处现为 :436/:457/:495 | 文件行数与符号实测 |

### 6.1 抽取总数与四类分布

**工具**：`out/re_work/hook_matrix/extract_and_classify.py`（全量正则抽取）→ `hooks_raw.json`；
`out/re_work/hook_matrix/classify_core.py`（核心集精分类）→ `core_matrix.json` / `core_matrix.md`。

| 层级 | 数量 | 说明 |
|---|---|---|
| 全量抽取记录（去重后） | **2961** | 含正文提及、表格行、落地规范行 |
| 全量唯一地址 | **1198** | 含 caveat/cave 槽位 `0x01B0xxxx` 与数据地址噪声 |
| **核心集**（已装 ∪ 18 项 ∪ 六大冲突簇） | **53** | 本次四类裁决的权威口径 |

**核心集四类分布（53）**：

| 类 | 含义 | 数量 | 地址 |
|---|---|---:|---|
| **(a) 已装** | 现网 `blitter_hooks.cpp` 已写入 | **19** | 13 虚表槽 + 3 组 Inline/BytePatch 点 + 路线 A 双点（`0x00655D38`/`0x0065719A`）+ `0x006D3D99` |
| **(b) 已建议未装** | 有文档/落地包、现网未写 | **11** | P-1.1…P-1.5、P-4.1/2、P-5.1/2、P-6.2；另 `0x00A83C68` 见下注 |
| **(c) 重复建议** | 同地址多来源、语义一致 | **3** | 见 §6.2 |
| **(d) 冲突** | 同地址语义/补丁字节不一致，或与已装重叠 | **15** | 见 §6.2 |
| 合并/废弃 | 已合并或裁决废弃 | **5** | `0x007F4D24`/`0x007F6034`（已合并）、`0x00655F48`（冲突废弃）、`0x006574C3`/`0x00655C50`（已下沉） |

> **注**：`0x00A83C68`（`PatchSpySatBuildingTypes` 遍历基址）属 **非 Hook 状态写 S1**（`INSTALLED_HOOKS_AUDIT.md:121`），
> 严格说「已装」但类型是 `Memory_Patch` 而非 Hook；与 P-2.5 G-07 TYPE 还原直接重叠（见裁决 #3）。

### 6.2 冲突 / 重复条目表（带 file:line）

#### (d) 冲突（15）

| 地址 | 冲突双方 | 证据（file:line） | 性质 |
|---|---|---|---|
| **`0x006D3D99`** | 现网无条件 `jmp 0x6D3E37`（force-full） vs P-6.1 双模 `L4DirtyMode=force-full\|vision-dirty` | `blitter_hooks.cpp:1308-1311`；`pending_execution_master_table.md:55,359-363`；本文 §3.4 | **语义冲突**：现网已写入 Full；P-6.1 要求可切回 `jge` + 局部打脏 |
| **`0x007EFA68`** | P-3.1 Particle v[69] 覆写 vs 已装 Draw 槽 69 族（Unit/Inf/Air/Bld/Bullet） | `pending_execution_master_table.md:49,153`；`blitter_hooks.cpp:1670-1696` | **同族冲突**：必须统一 Owner 门控与 `ret 8` ABI，禁止两套 ShouldDraw 分叉 |
| **`0x007EFCB0`** | P-3.2 PSys v[69] 覆写 vs 同上 | `pending_execution_master_table.md:50,154` | 同上 |
| **`0x00568273`** | P-2.1 NOP×6 vs S1 SpySat TYPE 路径（`EnableSpySatRadarSweep`） | `pending_execution_master_table.md:44,145`；`INSTALLED_HOOKS_AUDIT.md:121` | **相邻冲突**：NOP 保护 `Cell+0x134` 与 S1 改 TYPE 是两条独立路径，混装需统一开关 |
| **`0x00577EC5`** | P-2.2 NOP×6 vs 同上 | `pending_execution_master_table.md:45` | 同上 |
| **`0x00577B60`** | P-2.3 NOP×6 vs 同上 | `pending_execution_master_table.md:46` | 同上 |
| **`0x00508F8F`** | P-2.4 `je→jmp` SpySat 门控 vs S1 直接改 TYPE（`+0x16A5=false`） | `pending_execution_master_table.md:47-48`；`INSTALLED_HOOKS_AUDIT.md:121` | **双路径冲突**：门控改代码、S1 改数据；同时生效语义重叠 |
| `0x0073B0B0` / `0x0073B470` / `0x0073CEC0` / `0x006D8DB0` | C1：VXL 体素渲染链 vs FX 特效绘制链双重建议 | 本文 §3.1；`fx_draw_chain.md` / `vxl_render_sort.md` 交叉 | 链路争用（历史冲突簇） |
| `0x005F4B10` / `0x004DAF10` / `0x006D97D0` / `0x006D9920` | C1 外围地址 | 本文 §3.1 | 同上 |

#### (c) 重复建议（同地址多来源，语义一致）

| 地址 | 来源数 | 代表来源（file:line） | 说明 |
|---|---:|---|---|
| `0x006F8DF0` | 43 | `ARCHITECTURE_ATLAS.md:685,746`；`HOOK_POINT_MATRIX.md:31`；`targeting_spatial.md` | Greatest_Threat 唯一合法挂点，多文档复述 |
| `0x00655C50` | 18 | `HOOK_POINT_MATRIX.md:152,302`；`radar_hook_routeA_spec.md:14` | Plot_Cell 入口；路线 A 后改为下沉点 |
| `0x006574C3` | 23 | `ARCHITECTURE_ATLAS.md:99,517`；`HOOK_POINT_MATRIX.md:151` | 历史调用点方案，已被下沉取代（并入合并/废弃） |

### 6.3 与 18 项落地包交叉（重叠 / 冲突）

| 落地包 | 地址 | 与已装关系 | 重叠/冲突裁决 |
|---|---|---|---|
| P-1.1…P-1.5（SyncDiag ×5） | `0x0064C6F2` 等 | **无重叠** | 纯待落地；原字节与文档 **逐条一致**（claims ✓） |
| P-2.1…P-2.3（Gap NOP×3） | `0x00568273`/`0x00577EC5`/`0x00577B60` | 未装 | 与 S1 TYPE 改写**相邻**；需与 P-2.4/P-2.5 同包裁决 |
| P-2.4（SpySat 门控） | `0x00508F8F` | 未装 | 与 S1 双路径冲突（见 §6.2） |
| P-2.5（G-07 TYPE 还原） | TYPE 内存区 | **直接补 S1 缺口** | 现网 `PatchSpySatBuildingTypes` **无 Remove 还原**（`INSTALLED_HOOKS_AUDIT.md:121,190` A8）；P-2.5 即为此而生 |
| P-3.1/2（粒子槽 69） | `0x007EFA68`/`0x007EFCB0` | 未装，但与已装 5 个 Draw v[69] **同族** | 必须复用 `ShouldDraw*` 门控哲学 + `ret 8` ABI |
| P-4.1/2（CRT 池） | `0x007C8E17`/`0x007C8B3D` | 未装 | 纯待落地；原字节 ✓ |
| P-5.1/2（音频限频） | `0x00750920`/`0x007509E0` | 未装 | 纯待落地；原字节 ✓；注意 `ret 8`/`ret 4` 平栈 |
| **P-6.1**（L4 双模） | **`0x006D3D99`** | **已装（force-full）** | **唯一「已装 × 落地包」地址级重叠**；见裁决 #1 |
| P-6.2（RegisterCellAsVisible） | `0x006DA7D0` | 未装（原生 API 驱动） | 纯待落地；依赖 P-6.1 切到 `vision-dirty` |

### 6.4 发布前必须裁决清单

| # | 地址/对象 | 冲突双方 | 证据来源（file:line） | 建议裁决 | 风险 |
|---|---|---|---|---|:---:|
| **1** | `0x006D3D99` | 现网 force-full `E9 99 00 00 00 90` vs P-6.1 双模 `L4DirtyMode` | `blitter_hooks.cpp:1308-1311`；`pending_execution_master_table.md:55,359-363`；本文 §3.4 | **接受现网 force-full 为默认基线**；P-6.1 落地时**必须**加独立 ini 键 `L4DirtyMode`（默认 `force-full`），`vision-dirty` 仅在 U200/U800 对比测量通过后开放。禁止无键切换 | **P1** |
| **2** | `EnableMinimapFog` 默认值 | R-01 裁定「API 默认=0」vs 工作树 API=1 / ini=1 | `blitter_hooks.cpp:103`；`ra2render.ini:45`；`mp_release_safety_checklist.md:21,62`；`MP_SAFETY_REVIEW.md:464` | **P0 立即改**：`GetPrivateProfileIntA` 第 4 参 `1→0`，双份 ini 同步；验收「删键启动 → 日志 `EnableMinimapFog=false`」 | **P0** |
| **3** | S1 TYPE 改写 × P-2.5 | S1 无 Remove 还原 vs G-07 备份还原规范 | `INSTALLED_HOOKS_AUDIT.md:121,190`；`pending_execution_master_table.md:48,132-145` | **采纳 P-2.5**：`PatchSpySatBuildingTypes` 写前备份 4 字段，`RemoveVTableHooks` 调 `RestoreSpySatBuildingTypes`；否则验收基线会被污染 | **P0** |
| **4** | `TargetScanKey` 联机强制 | R-02「联机禁 pointer」vs LoadConfig 无联机门控 | `blitter_hooks.cpp:91-92,168-169`；`mp_release_safety_checklist.md:22,63` | **P0 落地 R-02**：检测联机强制 `g_targetScanKey=1` + 红字日志；禁止 pointer 分支在联机生效 | **P0** |
| **5** | `TargetScanInterval` 联机强制 | R-03「联机 interval=1」vs 默认 8 且无强制 | `blitter_hooks.cpp:61-63,438,459,497`；`mp_release_safety_checklist.md:23,69` | **P0 落地 R-03**：联机无条件 `g_targetScanInterval=1`（与 ThrottleKey position 键叠加后仍存相位 RISK） | **P0** |
| **6** | #7/#8/#9 审计口径 | 文档 VIOLATION vs 源码 ThrottleKey 已修 | `INSTALLED_HOOKS_AUDIT.md:150,162`；`MP_SAFETY_REVIEW.md:19,54`；`blitter_hooks.cpp:160-184,436,457,495` | **文档改判**：默认 position 键 → **RISK（待对拍）**；pointer 分支保留 VIOLATION 标签。同步作废行号 404/425/463 | **P0**（文档） |
| **7** | 雷达挂点文档 | 审计写 `0x006574C3` vs 源码路线 A `0x00655D38` | `INSTALLED_HOOKS_AUDIT.md:111`；`blitter_hooks.cpp:1466-1515` | **文档改写安装点**；删除/标注死宏 `ADDR_RADAR_PLOT`/`ADDR_RADAR_PLOT_CALLSITE`；回滚手册改按 `0x00655D38` | **P1** |
| **8** | P-3 粒子 v[69] | 新槽 vs 已装 Draw 槽 69 族 | `pending_execution_master_table.md:49-50,153-161`；`blitter_hooks.cpp:1670-1696` | 落地前冻结 **统一 `ShouldDrawObject` 门控 + `ret 8` ABI 契约**；`EnableParticleFog` 默认 0（各端独立） | **P1** |
| **9** | C1 VXL/FX 链 | `0x0073B0B0`/`0x0073B470`/`0x0073CEC0`/`0x006D8DB0` 双建议 | 本文 §3.1 | 维持原裁决：**禁止双挂钩**；VXL 与 FX 各留单一挂点，落地前须 Lead 再确认顺序 | **P2** |

### 6.5 新发现的「文档 vs 源码」不一致（含已知 ThrottleKey）

除任务书点名的 **#7/#8/#9 指针哈希 → ThrottleKey** 以外，本次复审另发现：

| ID | 主题 | 文档说 | 源码/工作树实际 | 判定 | 风险 |
|---|---|---|---|---|:---:|
| **DS-1** | L2 节流键（缺陷2） | `INSTALLED_HOOKS_AUDIT.md:150` / `MP_SAFETY_REVIEW.md:19,54`：`unitHash=(uintptr_t)pThis>>4`，VIOLATION，行号 404/425/463 | `blitter_hooks.cpp:160-184` `ThrottleKey()` 默认 **position 坐标哈希**；`TargetScanKey` 双模（`:91-92`）；调用点 **:436/:457/:495** | **文档过期**（任务书已知） | P0 |
| **DS-2** | `EnableMinimapFog` 默认 | dispatch 多份「已置 0」；R-01 要求 0 | API 默认 **1**（`:103`）；双份 ini **1** | **裁定未落地** | P0 |
| **DS-3** | 雷达挂钩地址 | `0x006574C3` + `0x00655C50` | 路线 A：`0x00655D38`(9B) + `0x0065719A`；两宏 cpp 零引用 | **文档过期 + 死宏** | P1 |
| **DS-4** | 源码行号 | 「1757 行」；:404/:425/:463 | **1788 行**；:436/:457/:495 | **行号过期** | P2 |
| **DS-5** | R-03 联机 interval=1 | 裁定 P0 | LoadConfig 无联机检测，ini 仍 8 | **裁定未落地** | P0 |
| **DS-6** | R-02 联机强制 position | 裁定 P0 | 可配 pointer 回到指针哈希分支 | **裁定未落地** | P0 |

> **[DA1 订正 · 2026-09-27]** 本表 **DS-2 / DS-5 / DS-6 三行已消解**（`EnableMinimapFog` 默认改 0 @ `:182`、ini `:46`=0、联机强制 interval=1 @ `:82-87` 与 position @ `:89-94`）；**DS-4 再次过期**（源文件现 1892 行）；**DS-1 / DS-3 已由本批文档订正**。逐条状态见 **§6.8.3**。

### 6.6 门禁输出（实跑）

```
python tools/verify_anchors.py
  回归汇总 : 断言总数 323 条 | PASS: 323 (100.00%) | FAIL: 0 | NOREAD: 0
  ★ 最终裁决 : [100% ALL PASS]

python tools/audit_bytes.py out/re_work/hook_matrix/claims.txt
  合计 40 条：OK=40  MISMATCH/NOREAD=0
```

### 6.7 产出物索引

| 路径 | 说明 |
|---|---|
| `out/re_work/hook_matrix/extract_and_classify.py` | 全量抽取脚本 |
| `out/re_work/hook_matrix/classify_core.py` | 核心集精分类 + claims 生成 |
| `out/re_work/hook_matrix/hooks_raw.json` | 原始抽取表（2961 条） |
| `out/re_work/hook_matrix/hooks_classified.json` | 噪声级四类（供溯源） |
| `out/re_work/hook_matrix/core_matrix.json` / `core_matrix.md` | **权威**核心集四类矩阵 |
| `out/re_work/hook_matrix/pending_cross.json` | 18 项落地包交叉 |
| `out/re_work/hook_matrix/claims.txt` | 40 条原字节 claims（门禁用） |
| `out/re_work/hook_matrix/summary.md` | 抽取摘要 |

---

### 6.8 DA1 勘误 · §六 复审快照与 MPS 落地状态对齐（DSH 子代理 · 2026-09-27）

> **性质**：只**追加**本小节，**不改动 §6.0–§6.7 的矩阵与裁决**（L409-537 逐字保留）；本小节只做**勘误与管理状态更新**。
> **快照口径**：§六 复审快照 = `blitter_hooks.cpp` **1788 行**（2026-09-26，快照 A/B 之间，**早于 2026-09-27 的 MPS 落地**）；本节 = **1892 行 / 86,961 B**（2026-09-27 09:06:28）。
> **部署件**：`ra2render/ra2render.dll` ≡ `ra2youli/ra2render.dll` = 129,536 B，SHA-256 `E7FA669C85B5DA53C71898DC453AC35301EC55F1222D1D581BFAEAC105DCC7CA`；`ra2render.ini` ≡ `ra2youli/ra2render.ini` = 2,996 B / 14 键，SHA-256 `564A265291C3C6CAF0E15CE8CFF00360A0BBD28EAF2E57BA74D1E0E49C0EC64F`；基线 `ra2youli/gamemd.exe` MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367`（只读未变）。

#### 6.8.1 §6.0 勘误块 E-1 … E-4 的当前状态

| ID | §6.0 原结论（行号） | 当前状态（2026-09-27 09:06 快照） | 依据 |
|---|---|---|---|
| **E-1**（`L421`） | 「默认 `TargetScanKey=position` 已改为 ThrottleKey 坐标哈希（`blitter_hooks.cpp:160-184`）→ #7/#8/#9 默认键下降为 **RISK（待对拍）**；`pointer` 分支仍 VIOLATION」 | **维持成立**；仅行号更新：`ThrottleKey()` **`:264-282`**、调用点 **`:534` / `:556` / `:595`** | 源码逐行 |
| **E-2**（`L422`） | 「**工作树未落地**：API 默认仍为 `1`（`blitter_hooks.cpp:103`），双份 ini 均 `EnableMinimapFog=1`（`ra2render.ini:45`）」 | **本条已过期（已被 MPS 推翻）**：API 默认**已改 0**（`:182`）；`ra2render.ini:46` = **0**（含 `ra2youli` 副本，**同 SHA-256**）；静态初值 `g_enableMinimapFog=false`（`:16`）；联机另加保守强制关闭（`:96-106`）。**用户决策（2026-09-27）：保持默认关** | ini `:46`；源码 `:16` / `:182` / `:96-106`；ini 双副本 SHA-256 |
| **E-3**（`L423`） | 「路线 A 下沉：现网实际打 `0x00655D38`（9B）+ `0x0065719A`；`ADDR_RADAR_PLOT` / `ADDR_RADAR_PLOT_CALLSITE` 零引用（死宏）」 | **维持成立**；`InstallRadarFogHooks` 现为 **`:1570-1620`**，`RemoveRadarFogHooks` **`:1622-1635`**；#21 另增 `s_minimapFogGate` 前置门控（`:1555-1556`） | 源码逐行；`tools/verify_hooks.py` 死宏清单 |
| **E-4**（`L424`） | 「当前源文件 **1788 行**；节流三处现为 `:436/:457/:495`」 | **行数与前引行号再次过期**（本批二次漂移）：源文件 **1892 行 / 86,961 B**；节流三处 **`:534` / `:556` / `:595`**；`ThrottleKey()` `:264-282` | 文件 mtime/size 实测 + 源码逐行 |

#### 6.8.2 §6.4 发布前裁决清单的落地状态更新（裁决 2 / 4 / 5 / 6）

| # | §6.4 裁决（行号） | 当前落地状态 | 依据 |
|---|---|---|---|
| **2**（`L493`） | 「**P0 立即改**：`GetPrivateProfileIntA` 第 4 参 `1→0`，双份 ini 同步；验收『删键启动 → 日志 `EnableMinimapFog=false`』」 | **已落地**：`:182` 第 4 参 = `0`；双份 ini `:46` = `0`（同哈希）；门控日志 `:201` 打印 `EnableMinimapFog=配置(%d)->生效(%d)` ⇒ 删键启动时两值均为 0（静态可判）。真机验收仍 `[待实测]` | 源码 `:182` / `:201`；ini `:46` |
| **4**（`L495`） | 「**P0 落地 R-02**：检测联机强制 `g_targetScanKey=1` + 红字日志」 | **已落地**：`GetEffectiveTargetScanKey()`（`:89-94`）联机 `return 1`；红字告警 `:129-131`（状态迁移）/ `:209-211`（启动）。**残留**：**不回写 ini**（`g_targetScanKey` 仍持配置值，生效值由函数给出） | 源码逐行 |
| **5**（`L496`） | 「**P0 落地 R-03**：联机无条件 `g_targetScanInterval=1`」 | **已落地**：`GetEffectiveTargetScanInterval()`（`:82-87`）联机 `return 1`；三处调用点 `:536` / `:558` / `:597` | 源码逐行 |
| **6**（`L497`） | 「**文档改判**：默认 position 键 → RISK（待对拍）；pointer 分支保留 VIOLATION；同步作废行号 `404/425/463`」 | **本批已执行文档改判**：见 `INSTALLED_HOOKS_AUDIT.md §10.1`、`MP_SAFETY_REVIEW.md §9.2`、`hook_gate_gap_table.md §9.1`（行号 `:404/:425/:463` → `:534/:556/:595`） | 三份文档勘误块 |
| **1 / 3 / 7 / 8 / 9** | 其余裁决 | **7 已在本批执行**（`INSTALLED_HOOKS_AUDIT.md §10.2` 雷达挂点改写为 `0x00655D38`）；**1**（L4 双模键）、**3**（P-2.5 TYPE 还原）、**8**（粒子槽 69）、**9**（VXL/FX 单挂点）**仍待落地** | 源码 grep：`L4DirtyMode` / `RestoreSpySat` 均 0 命中 |
> 【W3 勘误 · W3-M6/ISSUE-STALE-L4-EXIST】改前：1（L4 双模键）仍待落地 | 源码 grep：L4DirtyMode 均 0 命中；改后：| **1 / 3 / 7 / 8 / 9** | 其余裁决 | **7 已执行**（雷达 0x00655D38）；**1 已入源码**（`L4DirtyMode` 见 `blitter_hooks.cpp:757` / ini 配置）；**3 / 8 / 9 仍待落地** | 源码 grep：`RestoreSpySat` 0 命中 |；依据：blitter_hooks.cpp:757 与 ini 配置；分级：P0

#### 6.8.3 §6.5「文档 vs 源码」不一致清单的当前状态（DS-1 … DS-6）

| ID | 当前状态 | 依据 |
|---|---|---|
| **DS-1**（L2 节流键） | 文档过期（本批已订正） | `INSTALLED_HOOKS_AUDIT.md §10.1` |
| **DS-2**（`EnableMinimapFog` 默认） | **已消解**：API 默认 0 @ `:182`；ini `:46` = 0；双副本同哈希 | 源码 + ini 实测 |
| **DS-3**（雷达挂钩地址） | 文档过期（本批已订正）；死宏仍在（`ra2render.h:76-77`） | `INSTALLED_HOOKS_AUDIT.md §10.2`；`verify_hooks.py` 死宏 27 条 |
| **DS-4**（源码行号 1788） | **再次过期**：现为 **1892 行** ⇒ §6.0 E-4 的「1788」亦随之中招 | 文件 size/mtime 实测 |
| **DS-5**（R-03 联机 interval=1） | **已消解**：`:82-87` 联机强制 1 | 源码逐行 |
| **DS-6**（R-02 联机强制 position） | **已消解**：`:89-94` + 告警 `:129-131` / `:209-211` | 源码逐行 |

#### 6.8.4 §2.5 / §3.5 雷达挂钩点的勘误（**不推翻矩阵与废弃裁决**）

| 位置 | 改前原文（逐字） | 改后表述 | 依据 |
|---|---|---|---|
| §2.5 表第 1 行（`L150`） | 「`RadarClass::Plot_Cell` 主调用点 ｜ **`0x006574C3`** ｜ `E8 88 E7 FF FF` (`call 0x655C50`) ｜ `call Hook_RadarPlot_Callsite` ｜ **已装** (v1.6.0) ｜ `blitter_hooks.cpp:1449`」 | **`0x00655D38`（9B：`E9 rel32` + 4×`90`）** ｜ 原字节 `89 44 24 28 A1 50 35 B7 00` ｜ `jmp Hook_RadarPlot_Cell_Proxy` ｜ **已装（路线 A）** ｜ 安装 `blitter_hooks.cpp:1570-1620`，代理定义 `:1476-1549` | 源码 + 字节断言（`out/re_work/da1/claims.txt`） |
| §2.5 表第 3 行（`L152`） | 「`RadarClass::Plot_Cell` 序言跳板 ｜ `0x00655C50` ｜ `A1 4C 3D A8 00` ｜ 5B 偷取构造 Trampoline ｜ `blitter_hooks.cpp:1435`」 | **该 5B 序言跳板已取消**：现为 `0x00655D38` 的 9B 偷取跳板 `s_plotCellTrampoline[16]`（9B 原指令 + `jmp 0x00655D41`），定义 `:1472`，构造 `:1579-1587`。`0x00655C50` 仍为 `Plot_Cell` 函数本体入口（原字节 `A1 4C 3D A8 00` 实测一致） | 源码 + 字节断言 |
| §2.5 表第 4/5 行（`L153` / `L154`） | 「`0x00655F48` / `0x00655DEB` 冲突废弃」 | **不变**（废弃结论维持，本批不触及） | — |
| §3.5 标题（`L299`） | 「冲突五：小地图 0x00655F48（DrawCell 点过滤） vs 0x006574C3（RadarPlot_Cell 代理覆写）」 | 标题保留原文（审计痕迹）；**实际对比对象已变为 `0x00655D38`**（该节末尾已追加订正块） | 同 §2.5 |
| §6.2「重复建议」表（本快照实测 `L475` / `L476`；该表未改动） | 「`0x00655C50` ｜ 18 ｜ …路线 A 后改为下沉点」／「`0x006574C3` ｜ 23 ｜ `ARCHITECTURE_ATLAS.md:99,517`；`HOOK_POINT_MATRIX.md:151` ｜ 历史调用点方案，已被下沉取代（并入合并/废弃）」 | **`0x006574C3` 的文档引用已在本批清退**：`ARCHITECTURE_ATLAS.md:99` / `:517-518` / `:1888` 三处已订正为 `0x00655D38`（见该文末「附录 DA1」）⇒ 该行后续复算时计数（23）会下降 | `ARCHITECTURE_ATLAS.md` 附录 DA1 |

#### 6.8.5 本节不改动的内容（纪律声明）

1. **§6.1 抽取统计**（2961 / 1198 / 53）与 **§6.3「18 项落地包」交叉** **不改**——其口径为「文档建议 × 现网已装」，MPS 落地不改变该映射（`0x00A83C68`、P-1.x 等结论均未受影响）。
2. **§6.2 (a)/(b)/(d) 三类矩阵** **不改**：`0x006D3D99`（force-full vs 双模）、`0x007EFA68` / `0x007EFCB0`（粒子槽 69）、`0x00568273` / `0x00577EC5` / `0x00577B60`（裂缝 NOP）、C1 VXL/FX 冲突簇**全部维持**。
3. **§6.6 门禁输出**为 §六 成文时的实跑记录，保留原文；本批实跑见下方 §6.8.6。

#### 6.8.6 本批门禁实跑输出（原文粘贴）

```text
python tools/verify_anchors.py
  回归汇总 : 断言总数 323 条 | PASS: 323 (100.00%) | FAIL: 0 | NOREAD: 0
  ★ 最终裁决 : [100% ALL PASS] 全库决定性锚点与二进制基线完全一致，生产环境可安全放行！

python tools/verify_hooks.py --json out/re_work/da1/verify_hooks_da1.json
  Hook 实现符号      : 21
  虚表安装 / 还原对  : 13 / 13
  Inline 备份变量    : 7
  ini 键 / LoadConfig: 14 / 13
  Install* / Remove* : 3 / 3
  [4] ini 提供但 LoadConfig 未读: [TargetScanKey]   ← 脚本假阳性（该键由 GetPrivateProfileStringA 读取，blitter_hooks.cpp:169-171）
  [6] 头文件 ADDR_* 死宏（cpp 未引用）: 27 条
  结论: FAIL（存在缺口/不对称，见上）——判词按上注读
```

> **说明**：`verify_hooks.py` 的 FAIL 为**脚本口径局限**（只扫 `GetPrivateProfileIntA`），非现网配置漏读；本批 `audit_bytes.py` 对 `out/re_work/da1/claims.txt` 全 OK（证据见 `docs/re/ARCHITECTURE_ATLAS.md` 附录 DA1 与本任务交付回报 [6]）。

---

## 七、状态注记（追加节 · 2026-10-01 · 工单 `T-W1-Q / PK-1`）

> **只追加、不删改**：§2.x 主表、§四 Phase 表、§六 复审（`:415` 起）、§6.8 DA1（`:549` 起）全部逐字保留。
> 本节把「六包 17 个地址」的**矩阵口径**更新到 2026-10-01 实测态；矩阵的行号引用基准仍是其自述快照（`blitter_hooks.cpp` 1892 行，`:552`），**现网该文件已 3833 行**（本次实测 `grep -c ""`），故本节只给「状态」不给「新行号」，行号刷新应另开「行号基线」任务（DA1 `:346` 已如此建议）。

### B-1 · `0x006D3D99`（P-6.1）：由「已装 force-full，但 `L4DirtyMode` 未落地」→ **三档已落地（代码轨）**

- **改前逐字**（`:572`，§6.8.2 裁决 1/3/8/9「仍待落地」条目内）：「`L4DirtyMode` 在 ini 与源码**均不存在**」同类表述，以及 `:491`「已装（force-full）｜唯一「已装 × 落地包」地址级重叠」。
- **改后表述**：`L4DirtyMode` **三档（force-full / vision-dirty / vanilla）已进源码并进 ini**；force-full 档与旧现网件行为等价（保持 §6.8 裁决 1「接受现网 force-full 为默认基线」不变）。**`vision-dirty` 与 `vanilla` 两档的真机像素等价性仍 `[待实测]`**，故本地址的矩阵状态写作：**已装（三档门控）· 默认档已验 · 放行档未验**。
- **实测依据**：`ra2render/blitter_hooks.cpp:65-69`（三档定义与注释）、`:753-767`（读键 + 非法值收敛 force-full + 红字告警）、`:2470`（原字节 `0F 8D 98 00 00 00` 注记）、`:2489-2501`（桩内三档判定与 `s_l4RedrawSkippedStatic` 计数）、`:882-884`（遥测行）；`ra2render/ra2render.ini:251`、`ra2bench/ra2render.ini:186`、`ra2youli/ra2render.ini:186` 均 = `L4DirtyMode=force-full`。收据侧：`out/re_work/zcode_live/RESULT_ZC10B.md:26-27`（默认档 SUCCESS，其余两档「未做真机验证」）、`RESULT_ZC11.md:38`（默认档等价 PASS）、`:43`（vanilla「未测」）。
- **同时失效的一条**：`docs/REVERSE_ENGINEERING_AND_PATCHES.md:2937` 的「`L4DirtyMode` 在 ini 与源码均不存在」与 `:2014` 的「grep 0 命中 ⇒ G-03/04/06/07/10 确未落地」中**关于 `L4DirtyMode` 的那一半**已过期（其余四项本次复算仍为 0 命中，成立）。顶层台账本工单禁改，仅在此登记。

### B-2 · `0x00568273` / `0x00577EC5` / `0x00577B60`（P-2.1/2/3）：由「未装 (P5) / 冲突」→ **已装（双轨）**

- **改前逐字**：`:161`「未装 (P5)」＋`:162`「未装 (P5)」＋`:163`「未装 (P5)」；`:367` Phase 5；`:465-467` (d) 冲突；`:485`「未装 | 与 S1 TYPE 改写相邻」。
- **改后表述**：三点已合入 `ra2render`（表驱动、逐点 context-mismatch 拒装、逆序还原、`MpActive` 强制不装、`installed` 计数 0..3），矩阵状态应读作 **已装 · 默认开关 0 · 行为验收未闭环（A3/A4/A5）**。§6.2 记的 (d) 冲突（与 S1 TYPE 改写同面）**并未因落地而消解**，仍需 Lead 裁决。
- **实测依据**：`ra2render/ra2render.h:113,116,119`；`ra2render/blitter_hooks.cpp:3273-3287`（`kGapProtectPoints[3]`，邻窗前/后 2/6/10B）、`:3313`（安装）、`:3332-3350`（不可读/context-mismatch 拒装）、`:3374`（外部安装者检测）、`:3402`（计数）、`:3417`（逆序还原）、`:3736`（调用）；`out/re_work/zcode_live/gap_p223/RESULT_GAP_P223.md:56-59`（A1/A2/C4/C5 PASS）。

### B-3 · P-2.4 / P-3 / P-4 / P-5 / P-6.2 的矩阵条目**仍成立**（本轮复算确认 0 命中）

| 地址 | 矩阵原判 | 本次实测（`grep ra2render/{blitter_hooks.cpp,ra2render.h,ra2render.ini}`） |
|---|---|---|
| `0x508F8F`（P-2.4 SpySat 门控） | `:468/:486` 冲突 / 未装 | **0 命中**（仅无关的 `EnableSpySatRadarSweep` 在 `:12,550,1442`）⇒ 维持未装；`je→jmp` vs S1 改 TYPE 的双路径冲突**仍未裁** |
| `0x7EFA68` / `0x7EFCB0`（P-3 槽 69 ×2） | `:130/:131` 未装 (A-4) | **0 命中**，且 `blitter_hooks.cpp` 内 "Particle" 一词 0 命中 ⇒ 维持未装；A-4 证据前置要求（`:255`）不变 |
| `0x7C8E17` / `0x7C8B3D`（P-4 CRT new/delete） | `:203/:204` 规划评估、`:489` 未装 | **0 命中** ⇒ 维持未装（跳板字节与槽位已在总表 §2.4.3 备好） |
| `0x750920` / `0x7509E0`（P-5 音频） | `:195/:196` 未装 (P6) | **0 命中** ⇒ 维持未装；卡面键名与总表键名不一致（详见 `docs/re/config_key_matrix.md`） |
| `0x6DA7D0`（P-6.2 `RegisterCellAsVisible`） | `:145` 未装、`:492` 依赖 P-6.1 | **0 命中** ⇒ 维持未装。注：**P-6.1 已落地但串行门槛未达**（`R_l4_merge/README.md:19`、`R_l4_resid/zcode_patch_list.md:127`：`ZC-P1+P2+P4` 全绿前不得开 `vision-dirty`）⇒ 本条依赖关系应改写为「**等 P-1/P-3/P-4 落地**」而非「等 P-6.1」 |

### B-4 · 本节自证

`grep` 命中/未命中为本次实跑；`gamemd.exe` 未被任何步骤以写方式打开（只读普查），三处 `ra2render.dll` sha256 复算 = `626f98b6d6327b10…`（与 `MASTER_STATUS.md:19` 最终构建一致）。全量普查见 `out/re_work/harness_survey/RE_PROGRESS_SURVEY.md` §6（D2）。本节**未删除或改写上文任何一行**。

### B-5 · ★终判回填（2026-10-01 13:15 之后追加）—— `0x568273/0x577EC5/0x577B60` 三点由「行为验收未闭环」升为 **A3 PASS（带窗口限定）**

B-2 写的「已装 · 默认开关 0 · 行为验收未闭环（A3/A4/A5，Track-C 进行中）」是 12:2x 时点。同日 T-Z1 收口后，矩阵上这三行应读作：

- **`0x00568273` / `0x00577EC5` / `0x00577B60`：已装（代码轨+二进制轨）· 默认开关 0 · 行为验收 A3=PASS（带窗口限定）· A4=未闭环 · A5=部分**。
- 数值与判据：on 档 3 会话 `gap_cells=663` kept=100.0%、缝环核心 12 格 12/12、三点 in-process `90×6`、遥测 `installed=3/3`；off 对照晚期 a5 `663→373→0`。证据 `out/re_work/zcode_live/gap_p21_a3/RESULT_GAP_P21_A3.md` §A3/§A4/§A5（13:11 终稿）与 `gap_p223/RESULT_GAP_P223.md:60-62`（12:44 终判行）。
- **判据口径修正（对本矩阵 §6.2 (d) 冲突条的含义）**：`C-J3` 在战役场景不成立（缝环格开局已 mapped ⇒ `RevealArea2` 清零分支不触发，off 清零来自晚时 reshroud/crate 面）。⇒ **P-2.1 与 S1 的「相邻/同面」关系未被证伪也未被证实为分叉源**，§6.2 记录的 (d) 冲突与 Lead 裁决（`g_r1_handshake_decision_memo.md` / `MASTER_STATUS.md` 缺裁决段）**仍然 open**，不可因 A3 PASS 而撤案。
- 另：`0x00508F8F`（P-2.4）与 TYPE 备份（P-2.5）状态**不受本次收口影响**，仍为 B-3 表的 0 命中。
