#pragma once

#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <timeapi.h>
#include <cstdint>
#include <cstdio>
#include <emmintrin.h> // SSE2
#include <cmath>

// 16-bit HighColor Blitter VTables
#define ADDR_VTABLE_BLIT_TRANS_XLAT_ALPHA_ZREAD 0x007E56F0
#define ADDR_VFUNC_BLIT_TRANS_XLAT_ALPHA_ZREAD   0x00494B60

#define ADDR_VTABLE_RLE_BLIT_TRANS_XLAT_G       0x007E55C0
#define ADDR_VFUNC_RLE_BLIT_TRANS_XLAT_G         0x004960A0

#define ADDR_VTABLE_BLIT_TRANS_XLAT_G           0x007E5A20
#define ADDR_VFUNC_BLIT_TRANS_XLAT_G             0x004912B0

#define ADDR_VTABLE_BLIT_TRANS_G                0x007F7BF4
#define ADDR_VFUNC_BLIT_TRANS_G                  0x007BC890

#define ADDR_VTABLE_BLIT_TRANS_DARKEN_G         0x007E59F0
#define ADDR_VFUNC_BLIT_TRANS_DARKEN_G           0x00492670

#define ADDR_VTABLE_BLIT_PLAIN_G                0x007F7BC4
#define ADDR_VFUNC_BLIT_PLAIN_G                  0x007BC7F0

// Target Scanning VTables
// TechnoClass vtable: 0x007F4960
// Index 241 (Greatest_Threat): 0x007F4960 + 241 * 4 = 0x007F4D24 -> 0x006F8DF0
// Index 265 (SelectAutoTarget): 0x007F4960 + 265 * 4 = 0x007F4D84 -> 0x006FB010
#define ADDR_VTABLE_ENTRY_TECHNO_GREATEST_THREAT 0x007F4D24
#define ADDR_ORIG_TECHNO_GREATEST_THREAT         0x006F8DF0

#define ADDR_VTABLE_ENTRY_TECHNO_AUTO_TARGET     0x007F4D84
#define ADDR_ORIG_TECHNO_AUTO_TARGET             0x006FB010

// UnitClass vtable: 0x007F5C70
// Index 241 (Greatest_Threat): 0x007F5C70 + 241 * 4 = 0x007F6034 -> 0x00743190
// Index 265 (SelectAutoTarget): 0x007F5C70 + 265 * 4 = 0x007F6094 -> 0x00736CA0
#define ADDR_VTABLE_ENTRY_UNIT_GREATEST_THREAT   0x007F6034
#define ADDR_ORIG_UNIT_GREATEST_THREAT           0x00743190

#define ADDR_VTABLE_ENTRY_UNIT_AUTO_TARGET       0x007F6094
#define ADDR_ORIG_UNIT_AUTO_TARGET               0x00736CA0

// StarCraft-style Fog of War: Unit Draw VTables (Index 69)
#define ADDR_VTABLE_ENTRY_UNIT_DRAW              0x007F5D84
#define ADDR_ORIG_UNIT_DRAW                      0x0073CEC0

#define ADDR_VTABLE_ENTRY_INFANTRY_DRAW          0x007EB16C
#define ADDR_ORIG_INFANTRY_DRAW                  0x00518F90

#define ADDR_VTABLE_ENTRY_AIRCRAFT_DRAW          0x007E23B8
#define ADDR_ORIG_AIRCRAFT_DRAW                  0x004144B0

// StarCraft-style Fog of War: CellClass::Draw and Draw_Fog
#define ADDR_CELLCLASS_DRAW                      0x004801F0
#define ADDR_DRAW_FOG                            0x0047F250
#define ADDR_DRAW_FOG_PIXEL_BLEND_B1             0x0047F40F
#define ADDR_DRAW_FOG_PIXEL_BLEND_B1_CONT        0x0047F440
#define ADDR_DRAW_FOG_PIXEL_BLEND_B2             0x0047F4AE
#define ADDR_DRAW_FOG_PIXEL_BLEND_B2_CONT        0x0047F4E1
#define ADDR_TACTICAL_FULL_REDRAW_JUMP           0x006D3D99  // 原版 6B: 0F 8D 98 00 00 00 (jge 0x006D3E37)
#define ADDR_TACTICAL_FULL_REDRAW_TARGET         0x006D3E37  // jge 命中/旧补丁 jmp 的目标（全量重绘）
#define ADDR_TACTICAL_FULL_REDRAW_FALLTHROUGH    0x006D3D9F  // 原版 jge 不命中时的落点（0x6D3D99 + 6）

// ---------------------------------------------------------------------------
// [FOG-SPLIT] 引擎原版「黑幕/灰雾层」绘制入口 = 未探索全黑黑幕的**唯一**承载函数
//   · 全 .text call 扫描实证：唯一调用者 = CellClass::Draw 内 0x00480230（早于 FogOfWar 位门 0x00480251）
//   · 图像二选一（本函数首部 0x0047F01F）：Scenario FogOfWar 位=1 ⇒ FOG.SHP；位=0 ⇒ SHROUD.SHP
//     （[0x89E790]=FOG.SHP 句柄、[0x89E794]=SHROUD.SHP 句柄，均在本函数内懒加载）
//   · ecx = CellClass*（本函数自身不用，但调用点 0x0048022E 恒定传入）⇒ 可只读 [ecx+0x120] 判黑幕档
//   · 栈参（进入时）：[esp+4]=pLocation  [esp+8]=pBounds  [esp+0xC]=frame（-2⇒0xF / -1⇒0 / 其它原值）
//   · 前 6 字节 = 55 8B EC 83 EC 34（push ebp / mov ebp,esp / sub esp,0x34）⇒ 6B 补丁 + 跳板回 0x0047EFE6
//   · [FOG-SPLIT] 本版新增「只读计数」钩子（未探索黑幕绘制次数），不改变任何绘制行为
// ---------------------------------------------------------------------------
#define ADDR_DRAW_SHROUD_FOG                     0x0047EFE0
#define ADDR_DRAW_SHROUD_FOG_RESUME              0x0047EFE6

// [FOG-SPLIT] CellClass 迷雾三态字段（ref/yrpp/CellClass.h:407-408 / :414 / :421 逐字段实证）
#define OFF_CELL_SHROUDEDNESS                    0x120  // CellClass::Shroudedness
                                                        //   -2 = Occluded completely（未探索 ⇒ 原版全黑黑幕）
                                                        //   -1 = Visible；0..48 = 黑幕/灰雾帧号
#define OFF_CELL_FOGGEDNESS                      0x121  // CellClass::Foggedness（同值域；本版仅遥测用）
#define OFF_CELL_FLAGS_140                       0x140  // CellClass::Flags（引擎 0x6D8700 以 (Flags&3)==0 判 -2）
#define CELL_CF_EXPLORED                         0x08   // cf_Explored「this means no shroud」（GeneralDefinitions.h:549）

// ---------------------------------------------------------------------------
// [GAP-P223] 裂缝保护三点表驱动（ZC-GAP-P223 合并 ZC-GAP-P21；landing_pack_gap_p223.md
//   + landing_pack_gap_merge_checklist.md，依据 R-GAP-PSY 静态定谳）
//   三个函数内层循环各含**恰好一次**「清 GapsCoveringThisCell(+0x134)」store（Q4 闭合，
//   无第 4 处）；三点同构等长 NOP 化 = 一个保护包：
//     P-2.1  MapClass::RevealArea2 @0x005678E0  0x00568273  mov [ecx+0x134], ebx（ebx=0）
//     P-2.2  MapClass::RevealArea3 @0x00577D90  0x00577EC5  mov [eax+0x134], edi（edi=0）
//     P-2.3  MapClass::Reshroud    @0x00577AB0  0x00577B60  mov [eax+0x134], ebx（ebx=0）
//   每点只删这一次 store；同循环内其余写入原样保留：
//     P-2.1 保留 ShroudCounter<-0(@0x56824A) / CopyFlags|=0x10(@0x56829A)
//     P-2.2 保留 ShroudCounter<-0(@0x577EBF) / CopyFlags|=0x18(@0x577ED4)
//     P-2.3 保留 CopyFlags&=~0x18(@0x577B4E) / ShroudCounter<-1(@0x577B56) / RedrawFlags&=~0x3(@0x577B66)
//   副作用链：清零使 CellClass::ReshroudCell(0x487690) 把 ShroudCounter 钳位到 0
//   ⇒ 敌方 GapGenerator 覆盖区在开图/重遮后**永久静默失能**（RevealArea2 有 22 个 E8 caller：
//   PsychicReveal 双调 0x6CD773/0x6CD79C + 超武/任务脚本等；CreateGap/DestroyGap 不自愈）。
//   等长硬约束：6B==6B，禁 trampoline / 禁动 .detour 节；只允许纯 90
//   （禁 89→8B / add/or/and/xor/cmp 类翻法：零点常量寄存器 ebx/edi 在循环内仍被消费，
//    且 cmp→jl 类邻接 flags 关系必须保持）。
//   窗宽按实测参数化（禁 2B 硬编码）：P-2.1 前2/后2、P-2.2 前6/后6、P-2.3 前10/后6。
//   门控：EnableGapProtection=1 才安装（默认 0 = 零行为变化）；MpActive() 联机强制不装。
//   只改**已加载映像内存字节**：磁盘 gamemd.exe 只读不改（RE_COORDINATION 红线 §3-1）。
// ---------------------------------------------------------------------------
#define ADDR_REVEALAREA2_GAP_CLEAR               0x00568273  // P-2.1 原 6B: 89 99 34 01 00 00
#define ADDR_REVEALAREA2_GAP_CLEAR_PREV          0x00568271  // 2B: 3B C3 (cmp eax, ebx)
#define ADDR_REVEALAREA2_GAP_CLEAR_NEXT          0x00568279  // 2B: 7C 14 (jl ...)
#define ADDR_REVEALAREA3_GAP_CLEAR               0x00577EC5  // P-2.2 原 6B: 89 B8 34 01 00 00
#define ADDR_REVEALAREA3_GAP_CLEAR_PREV          0x00577EBF  // 6B: 89 B8 30 01 00 00 (ShroudCounter<-0，保留)
#define ADDR_REVEALAREA3_GAP_CLEAR_NEXT          0x00577ECB  // 6B: 8B 90 2C 01 00 00 (load CopyFlags，保留)
#define ADDR_RESHROUD_GAP_CLEAR                 0x00577B60  // P-2.3 原 6B: 89 98 34 01 00 00
#define ADDR_RESHROUD_GAP_CLEAR_PREV            0x00577B56  // 10B: C7 80 30 01 00 00 01 00 00 00 (ShroudCounter<-1，保留)
#define ADDR_RESHROUD_GAP_CLEAR_NEXT            0x00577B66  // 6B: 89 90 40 01 00 00 (RedrawFlags<-edx&~0x3，保留)

#ifdef GAPFIX_HOSTTEST
// ---------------------------------------------------------------------------
// [GAP-MP-EDGE 宿主单元测试注入] 仅当以 /DGAPFIX_HOSTTEST 编译（W3_20261001 gapfix 宿主负控制
//   out/re_work/zcode_live/W3_20261001/gapfix/hosttest/edge_hosttest.cpp）时生效：把三点表
//   VA 改指到宿主 VirtualAlloc 的模拟映像（0x3000xxxx 段内预布原字节+前后窗），令
//   Install/RemoveGapProtectionPatch 与 CheckMpGateTransition→MpGateEdgeSyncGapProtection
//   **按生产代码原样**在宿主进程内执行。生产构建不定义该宏 ⇒ 零影响、零字节差异。
// 布局（每点 0x100 槽）：+0x00 前窗(≤10B) / +0x20 站点 6B / +0x28 后窗(≤6B)。
// 注：经 HOSTTEST_ADDR_* 中转（而非裸 0x 字面量），避免污染 verify_hooks 的
//     `#define\s+(ADDR_\w+)\s+(0x…)` 地址提取正则。
// ---------------------------------------------------------------------------
#undef ADDR_REVEALAREA2_GAP_CLEAR
#undef ADDR_REVEALAREA2_GAP_CLEAR_PREV
#undef ADDR_REVEALAREA2_GAP_CLEAR_NEXT
#undef ADDR_REVEALAREA3_GAP_CLEAR
#undef ADDR_REVEALAREA3_GAP_CLEAR_PREV
#undef ADDR_REVEALAREA3_GAP_CLEAR_NEXT
#undef ADDR_RESHROUD_GAP_CLEAR
#undef ADDR_RESHROUD_GAP_CLEAR_PREV
#undef ADDR_RESHROUD_GAP_CLEAR_NEXT
static const uint32_t HOSTTEST_ADDR_P21      = 0x30001020u;
static const uint32_t HOSTTEST_ADDR_P21_PREV = 0x30001000u;
static const uint32_t HOSTTEST_ADDR_P21_NEXT = 0x30001028u;
static const uint32_t HOSTTEST_ADDR_P22      = 0x30001120u;
static const uint32_t HOSTTEST_ADDR_P22_PREV = 0x30001100u;
static const uint32_t HOSTTEST_ADDR_P22_NEXT = 0x30001128u;
static const uint32_t HOSTTEST_ADDR_P23      = 0x30001220u;
static const uint32_t HOSTTEST_ADDR_P23_PREV = 0x30001200u;
static const uint32_t HOSTTEST_ADDR_P23_NEXT = 0x30001228u;
#define ADDR_REVEALAREA2_GAP_CLEAR            HOSTTEST_ADDR_P21      // hosttest: P-2.1 站点（模拟映像）
#define ADDR_REVEALAREA2_GAP_CLEAR_PREV       HOSTTEST_ADDR_P21_PREV
#define ADDR_REVEALAREA2_GAP_CLEAR_NEXT       HOSTTEST_ADDR_P21_NEXT
#define ADDR_REVEALAREA3_GAP_CLEAR            HOSTTEST_ADDR_P22      // hosttest: P-2.2 站点（模拟映像）
#define ADDR_REVEALAREA3_GAP_CLEAR_PREV       HOSTTEST_ADDR_P22_PREV
#define ADDR_REVEALAREA3_GAP_CLEAR_NEXT       HOSTTEST_ADDR_P22_NEXT
#define ADDR_RESHROUD_GAP_CLEAR               HOSTTEST_ADDR_P23      // hosttest: P-2.3 站点（模拟映像）
#define ADDR_RESHROUD_GAP_CLEAR_PREV          HOSTTEST_ADDR_P23_PREV
#define ADDR_RESHROUD_GAP_CLEAR_NEXT          HOSTTEST_ADDR_P23_NEXT
#endif // GAPFIX_HOSTTEST

// ---------------------------------------------------------------------------
// [VXL-PRE] VXL 缓存预热扩容（ZC-VXL-PRE / landing_pack_vxl_prewarm.md，L-VXL-1）
//   Draw_A_VXL 核 @0x00706640 内 SomeVoxelCache Miss 插入路径：首次分配粒度
//     mov ebx, 0xa（10 条）→ mov ebx, 0x40（64 条 ≈ 32 朝向 × 2 帧）。
//   只改 5B 指令内的 imm8 一字节（0x0A→0x40）；扩容步长（0x706D7F mov ebx,eax 翻倍）、
//   拷贝/插入/IsSorted 置脏/LastFoundEntry 清空全部不动；禁改 EB 0A(0x706D7D)/8B D8(操作码 BB 同禁)。
//   门控：EnableVxlCachePrewarm=1 才安装（默认 0）；MP 可装（D-VXL13 SAFE，纯表现层缓存粒度）。
// ---------------------------------------------------------------------------
#define ADDR_VXL_CACHE_INIT_CAP                  0x00706D78  // 5B: BB 0A 00 00 00 → BB 40 00 00 00
#define ADDR_VXL_CACHE_INIT_PREV                 0x00706D76  // 2B: 75 07 (jne growstep；Capacity==0 才落到本点)
#define ADDR_VXL_CACHE_INIT_NEXT1                0x00706D7D  // 2B: EB 0A (jmp，禁改)
#define ADDR_VXL_CACHE_INIT_NEXT2                0x00706D7F  // 2B: 8B D8 (mov ebx,eax growstep 翻倍，禁改)

// ---------------------------------------------------------------------------
// [SW-CHARGE] 充能冗余二次 call 删除（ZC-SW-CHARGE / landing_pack_sw_charge.md，L-SW-1）
//   SuperClass::HasChargeProgressed @0x006CBCA0 慢路径：对纯函数 GetCameoChargeState
//   (0x6CBEE0) 的**冗余二次 call**（mov ecx,esi; call）7B → 90×7，复用第一次结果 eax。
//   语义等价（纯读函数 + cmp/je 不改 eax ⇒ 0x6CBE8F 写回值不变）；充能链其余副作用一字不动。
//   门控：EnableSWChargeOpt=1 才安装（默认 0）；零语义变化 ⇒ MP 可装可保留（不强制关）。
// ---------------------------------------------------------------------------
#define ADDR_SW_CHARGE_REDUNDANT_CALL            0x006CBE88  // 7B: 8B CE E8 51 00 00 00 → 90×7
#define ADDR_SW_CHARGE_FIRST_CALL                0x006CBE7E  // 5B: E8 5D 00 00 00（第一次 call，保留）
#define ADDR_SW_CHARGE_WINDOW_PREV               0x006CBE86  // 2B: 74 15 (je，脏检测无变化即 false)
#define ADDR_SW_CHARGE_WINDOW_NEXT               0x006CBE8F  // 3B: 89 46 78 (mov [esi+0x78],eax 写回，保留)

#define ADDR_SCENARIO_INSTANCE                   0x00A8B230
#define ADDR_RULES_INSTANCE                      0x008871E0
#define ADDR_GAME_STATE                          0x00A8B238

// 联机状态判定与门控（F-10 / M-6 规约）
#define ADDR_MP_SESSION_FLAGS                    0x00A8D5F8  // bit1 (& 0x02) != 0 -> 联机网络对局
#define ADDR_DIRECTPLAY_STATUS                   0x00AA0444  // == 2 -> DirectPlay 会话活跃

#ifdef GAPFIX_HOSTTEST
// [GAP-MP-EDGE 宿主单元测试注入] MpActive 读的两个引擎标志位重指模拟映像（同 0x3000xxxx 段）。
//   注：二者在头文件中后定义，故守卫块置于其后；生产构建不定义 GAPFIX_HOSTTEST ⇒ 零影响。
//   同样经 HOSTTEST_ADDR_* 中转，规避 verify_hooks 的 ADDR_ 地址提取正则。
#undef ADDR_MP_SESSION_FLAGS
#undef ADDR_DIRECTPLAY_STATUS
static const uint32_t HOSTTEST_ADDR_MP_SESSION_FLAGS  = 0x30001300u;
static const uint32_t HOSTTEST_ADDR_DIRECTPLAY_STATUS = 0x30001310u;
#define ADDR_MP_SESSION_FLAGS                     HOSTTEST_ADDR_MP_SESSION_FLAGS   // hosttest: 会话标志 bit1
#define ADDR_DIRECTPLAY_STATUS                    HOSTTEST_ADDR_DIRECTPLAY_STATUS  // hosttest: DP 状态（恒 0）
#endif // GAPFIX_HOSTTEST

// L5 雷达小地图（PowerClass/RadarClass/Sidebar 单例 0x0087F7E8）
#define ADDR_RADAR_PLOT                          0x00655C50  // RadarClass::Plot_Cell(POINT*)
#define ADDR_RADAR_PLOT_CALLSITE                 0x006574C3  // 0x00656EC0 主循环内 call 0x655C50
#define ADDR_RADAR_PENDING_CALLSITE              0x0065719A  // 0x656EC0 内 call 0x660530（跳帧判定）
#define ADDR_RADAR_PENDING_ORIG                  0x00660530  // mov eax,[0xB04DB8]; test; sete al; ret
#define ADDR_RADAR_NATIVE_DECIDE                 0x00655D87  // [RADAR-FIX2] Plot_Cell 内减暗判定位写入后的 7B 区
                                                             //   (mov eax,[edi+4] + mov [esp+0x14],ebp)
#define ADDR_RADAR_NATIVE_RESUME                 0x00655D8E  // [RADAR-FIX2] 上述 7B 区之后的回跳点
#define ADDR_GAME_HWND                           0x00B73550  // [RADAR-FIX2 定谳] Game::hWnd（主窗口句柄 HWND）
                                                             //   ★ 只读、绝不写：全 exe 有 77 处读点把它当 Win32 窗口句柄
                                                             //     （SetFocus/SetCapture/ShowWindow/GetClientRect/...），
                                                             //     写它会污染 70+ 处 Win32 调用；仅 2 处写点 0x777CD6/0x777D7E
                                                             //     （CreateWindowExA 返回值落地）。
#define ADDR_RADAR_PENDING_PENDINGVAR            0x00B04DB8
#define RADAR_OFF_WORK_SURFACE                   0x121C      // RadarClass+0x121C 工作表面
#define RADAR_OFF_CACHE_SURFACE                  0x1220      // RadarClass+0x1220 BSurface 地形缓存

// ---------------------------------------------------------------------------
// [RADAR-FIX] 局内判据（护栏 2）—— 全部为只读引擎全局，不写、不进同步路径
//   0x00A83D4C  HouseClass::Player 指针（YRpp HouseClass.h:145 = reference<HouseClass*,0xA83D4Cu>）
//               【本判据 = 引擎自身对该路径的判据】RadarClass::Plot_Cell 函数头
//               0x00655C62 即 'je 0x00656138'（cmp eax,ebp 在 0x00655C5D）—— PlayerPtr==0 直接 return，
//               故本钩子被调用时 PlayerPtr!=0 是引擎已经做出的事实判定。
//   0x00A8B230  ScenarioClass::Instance（堆实例指针；0x52BA94 赋值 / 0x52BAB6,0x6BEB7D 清零）
//   +0x3598     ScenarioClass::IsLoadingScreen（加载进度屏；0x48D001/0x48D0EF 读）
//   0x00A8B238  SessionClass::Instance.GameMode（YRpp SessionClass.h:54/56 = reference<SessionClass,0xA8B238u>,
//               首成员 GameMode）—— 枚举 {0=Campaign, 3=LAN, 4=Internet, 5=Skirmish}
//               （ref/yrpp/GeneralDefinitions.h:670-675）；值域<=5 用作合法性上界。
// ---------------------------------------------------------------------------
#define ADDR_SESSION_GAMEMODE                    0x00A8B238  // SessionClass::Instance.GameMode（非"菜单状态"）
#define OFF_SCENARIO_ISLOADING                   0x3598      // ScenarioClass::IsLoadingScreen
#define ADDR_RADAR_PLOT_ENTRY_GATE               0x00655C62  // Plot_Cell 自身 PlayerPtr 门（0x655C5D cmp eax,ebp / 0x655C62 je 0x656138）
#define RADAR_FOG_GUARD_LEGACY                   0           // 旧行为自绘：[0xA8B238]==0 视为菜单（真机对照）
#define RADAR_FOG_GUARD_NEW                      1           // 新谓词自绘（A/B 对照档）
#define RADAR_FOG_GUARD_OFF                      2           // 不设护栏自绘（A/B 对照档）
#define RADAR_FOG_GUARD_NATIVE                   3           // [RADAR-FIX2] 引擎原生减暗驱动（本版默认）

// L5 建筑与弹道迷雾 Hook（虚表槽 69）
#define ADDR_VTABLE_ENTRY_BUILDING_DRAW          0x007E3FD0
#define ADDR_ORIG_BUILDING_DRAW                  0x0043D290
#define ADDR_VTABLE_ENTRY_BULLET_DRAW            0x007E47F8
#define ADDR_ORIG_BULLET_DRAW                    0x00468090

// 结构偏移（YRpp + 反汇编实证）
#define OFF_TECHNO_OWNER                         0x21C  // TechnoClass::Owner (HouseClass*)
#define OFF_TECHNO_TYPE                          0x6C4  // TechnoClass::TechnoTypeClass*
#define OFF_BULLET_OWNER                         0xB0   // BulletClass::Owner (TechnoClass*)
#define OFF_BLDTYPE_FOUNDATION_DATA              0xDFC  // BuildingTypeClass::FoundationData (CellStruct*, 0x7FFF 哨兵)
#define OFF_CELL_MAPCOORDS                       0x24
#define OFF_CELL_FLAGS                           0x12C  // CellClass::CopyFlags
                                                        //   ★[FOG-MODE F7① 勘误·就地订正 2026-09-28] **本偏移的 bit3(0x08) = cf_Explored（已探索）**，
                                                        //     原始注释「bit3 = 已探索」是对的。二进制**读写双向**证据（UNIT-VIS）：
                                                        //       · 读点 0x005863F2  F6 81 2C 01 00 00 08   test byte ptr [ecx+0x12C],8
                                                        //         （位于引擎黑幕谓词 MapClass::IsLocationShrouded 0x00586360 内；
                                                        //          0x00586483 mov al,1 / 0x0058648C xor al,al ⇒ 位清 = 未探索）
                                                        //       · 写点 0x004A98E6  8B 85 2C 01 00 00      mov eax,[ebp+0x12C]
                                                        //               0x004A98EC  0C 08                  or  al,8      （CopyFlags |= cf_Explored）
                                                        //               0x004A98F0  89 85 2C 01 00 00      mov [ebp+0x12C],eax
                                                        //       锚点文件：out/re_work/unit_vis/*（UNIT-VIS 交付）；文本见
                                                        //       docs/re/unit_visibility_mechanism.md:158/167-170 与 §[3] E1。
                                                        //   【原记（FOG-SPLIT 勘误 E3，★已作废，勿再引用）】
                                                        //     「+0x12C 是 CopyFlags…其 0x08 = cf2_NoShadow、0x02 = cf2_ContainsBuilding
                                                        //      （ref/yrpp/GeneralDefinitions.h:557-560）；『已探索』位 cf_Explored = 0x08
                                                        //      在 +0x140 = CellClass::Flags（同文件 :549「this means no shroud」）」
                                                        //     ⇒ 「旧注释已被证伪」这个**证伪本身**已被 UNIT-VIS 双向证据反向证伪：
                                                        //       cf2_NoShadow 属另一族命名，不能据以否证 +0x12C 的「已探索」语义。
                                                        //   ※ 实现口径**不变**（零行为影响，纯注释）：本版钩子仍读引擎自身判定
                                                        //     CellClass::Shroudedness(+0x120) == -2（更贴近引擎每帧口径，
                                                        //     见 OFF_CELL_SHROUDEDNESS / OFF_CELL_FLAGS_140 与 Hook_CellClass_Draw 注释）。

// Map and House globals
#define ADDR_HOUSE_PLAYER                        0x00A83D4C
#define ADDR_MAP_CELLS_ARRAY                     0x0087F924

// Object Arrays
#define ADDR_ARRAY_UNITS                         0x008B4108
#define ADDR_ARRAY_INFANTRY                      0x00A83DE8
#define ADDR_ARRAY_AIRCRAFT                      0x00A8E390
#define ADDR_ARRAY_BUILDINGS                     0x00A8EB40
#define ADDR_ARRAY_BUILDING_TYPES                0x00A83C68
#define ADDR_ARRAY_SUPERWEAPON_TYPES             0x00A8E330

// Global CurrentFrame and Timing Engine Pointers
#define ADDR_CURRENT_FRAME                       0x00A8ED84
#define ADDR_GAME_SPEED_SETTING                  0x00A8EB60
#define ADDR_SKIRMISH_GAME_SPEED                 0x00A8B268
#define ADDR_ACTIVE_FRAME_DELAY                  0x00887350

class BlitterCore {
public:
    virtual ~BlitterCore() = default;
    virtual void __thiscall Blit(void *dst, uint8_t *src, unsigned int length, uint16_t zMin, uint16_t *zBuf, uint16_t *aBuf, uint16_t aLvl, int warpOffset) = 0;
    virtual void __thiscall CallBlit0(void *dst, uint8_t *src, unsigned int length, uint16_t zMin, uint16_t *zBuf, uint16_t *aBuf, uint16_t aLvl, uint16_t arg, uint32_t useless) = 0;
    virtual void __thiscall CallBlit1(void *dst, uint8_t *src, unsigned int length, uint16_t zMin, uint16_t *zBuf, uint16_t *aBuf, uint16_t aLvl) = 0;
    virtual void __thiscall CallBlit2(void *dst, uint8_t *src, unsigned int length, uint16_t zMin, uint16_t *zBuf, uint16_t *aBuf, uint16_t aLvl, uint32_t useless) = 0;

    uint16_t *XlatTable;      // +0x04
    void *AlphaTable;         // +0x08
};

class RLEBlitterCore {
public:
    virtual ~RLEBlitterCore() = default;
    virtual void __thiscall Blit(void *dst, uint8_t *src, uint8_t Length, int EncodedLen, int a6, int a7, int a8, int a9, int a10, int a11) = 0;
    virtual void __thiscall CallBlit0(void *dst, uint8_t *src, uint8_t Length, int EncodedLen, int a6, int a7, int a8, int a9, int a10, int a11, uint32_t useless) = 0;

    uint16_t *XlatTable;      // +0x04
};

class BlitterDarkenCore {
public:
    virtual ~BlitterDarkenCore() = default;
    virtual void __thiscall Blit(void *dst, uint8_t *src, unsigned int length, uint16_t zMin, uint16_t *zBuf, uint16_t *aBuf, uint16_t aLvl, int warpOffset) = 0;
    virtual void __thiscall CallBlit0(void *dst, uint8_t *src, unsigned int length, uint16_t zMin, uint16_t *zBuf, uint16_t *aBuf, uint16_t aLvl, uint16_t arg, uint32_t useless) = 0;
    virtual void __thiscall CallBlit1(void *dst, uint8_t *src, unsigned int length, uint16_t zMin, uint16_t *zBuf, uint16_t *aBuf, uint16_t aLvl) = 0;
    virtual void __thiscall CallBlit2(void *dst, uint8_t *src, unsigned int length, uint16_t zMin, uint16_t *zBuf, uint16_t *aBuf, uint16_t aLvl, uint32_t useless) = 0;

    uint16_t DarkenMask;      // +0x04
};

typedef void (__thiscall *FnBlit8Arg)(
    BlitterCore *pThis, void *dst, uint8_t *src, unsigned int length,
    uint16_t zMin, uint16_t *zBuf, uint16_t *aBuf, uint16_t aLvl, int warpOffset
);

typedef void (__thiscall *FnRLEBlitTransXlat)(
    RLEBlitterCore *pThis, void *dst, uint8_t *src, uint8_t Length,
    int EncodedLen, int a6, int a7, int a8, int a9, int a10, int a11
);

typedef void (__thiscall *FnSelectAutoTarget)(void *pThis);
typedef void* (__thiscall *FnGreatestThreat)(void *pThis, uintptr_t arg1, uintptr_t arg2, uintptr_t arg3);
typedef void (__thiscall *FnDrawObject)(void *pThis, void *pLocation, void *pBounds);
typedef void (__thiscall *FnDrawFog)(void *pCell, void *pLocation, void *pBounds, int frame);
typedef void (__thiscall *FnCellClassDraw)(void *pCell, void *pLocation, void *pBounds);

struct ForgeTelemetry {
    uint64_t totalBlitCalls;
    uint64_t totalBlitPixels;
    uint64_t totalTargetScans;
    uint64_t throttledTargetScans;
    uint64_t totalUnitsRendered;
    uint64_t unitsCulledByFog;
    uint64_t fogCellsDrawn;
    uint64_t buildingsCulledByFog;
    uint64_t bulletsCulledByFog;
    uint64_t minimapFogPixels;
};

extern ForgeTelemetry g_telemetry;
extern int g_targetScanInterval; // Default = 8 (联机模式强制 1)
extern int g_targetScanKey;      // 0=pointer(旧,仅单机) 1=position(默认,联机安全,联机强制1)
extern bool g_enableSIMD;        // Default = true
extern bool g_unlockGameSpeed;   // Default = false
extern bool g_enableLFH;         // Default = true
extern bool g_highPrecisionTimer;// Default = true
extern bool g_enableStarCraftFog;// Default = true
extern bool g_enableSpySatRadarSweep;// Default = true
extern int  g_radarSweepCooldownFrames;// Default = 600 (40s at 15fps)
extern int  g_radarSweepRadiusCells;   // Default = 16
extern bool g_enableBuildingFog; // Default = true  敌方建筑"看见过即常驻"(WC3式)
extern bool g_enableBulletFog;   // Default = true  迷雾中敌方弹道剔除
extern bool g_enableUnitFog;     // Default = true  [FOG-SPLIT] 迷雾中敌方机动单位剔除
                                 //   ★[FOG-SPLIT] 逻辑可见性键：**不受** EnableStarCraftFog 总闸影响
                                 //     （旧版误挂总闸 ⇒ 总闸=0 时"迷雾剔除机动单位"恒 0，违反玩法可见性语义）
extern bool g_visibilityVanilla; // [FOG-MODE] Default = false（= VisibilityMode=starcraft 现状态）
                                 //   true  = VisibilityMode=vanilla ⇒ **原版可见性**：三处视距剔除
                                 //           （机动单位 / 建筑 / 弹道）全部放行；三子键被本键**覆盖（忽略）**。
                                 //   ★只「不介入绘制」：不写引擎状态、不改 RNG/命令序（见 FogModeVanillaPassThrough）。
// [FOG-MODE] VisibilityMode 原始串（starcraft|vanilla；未知值原样保留供日志告警，生效值收敛为 starcraft）
extern char g_visibilityModeRaw[32];
extern bool g_fadeFogTransition; // Default = true  灰雾4帧渐变过渡
extern bool g_enableMinimapFog;  // Default = false 雷达小地图迷雾化（G-01: API默认改0，联机保守强制0）
extern int  g_radarFogGuardMode; // [RADAR-FIX] 雷达灰化护栏模式: 0=旧行为 1=新谓词(默认) 2=无护栏

// ---- [GAP-P223] 裂缝保护（ZC-GAP-P223；三点表驱动 P-2.1+P-2.2+P-2.3）----
extern bool g_enableGapProtection;  // [GAP-P223] Default = false 裂缝保护开关键（同键不拆）
                                    //   1 = init 时把三点「清 GapsCoveringThisCell(+0x134)」的 6B 等长 NOP 化
                                    //   （每点只删这一次 store；ShroudCounter/CopyFlags/RedrawFlags 写入原样保留）
                                    //   0 = 不碰 .text（默认，零行为变化）；安装态在 init 决定，重启生效
extern int  g_gapProtectionPatchesInstalled;  // [GAP-P223] 遥测（只读计数）∈ 0..3：
                                    //   本进程**实际写入**的 NOP 点数（装几点算几点；外部安装者不计）
                                    //   ==3 才满足产品契约（存档标记 GapProt Version / MP 握手期望值）

// ---- [VXL-PRE] VXL 缓存预热扩容（ZC-VXL-PRE，L-VXL-1；[Render] 键，默认 0）----
extern bool g_enableVxlCachePrewarm;  // 1 = init 时 0x706D78 imm8 0x0A→0x40（首次容量 10→64）
extern int  g_vxlCacheInstalled;      // 遥测：0/1（本进程是否由我方安装；热路径计数器未实现，另卡）

// ---- [SW-CHARGE] 充能冗余二次 call 删除（ZC-SW-CHARGE，L-SW-1；[Logic] 键，默认 0）----
extern bool g_enableSWChargeOpt;      // 1 = init 时 0x6CBE88 7B→90×7（删冗余二次 call，零语义变化）
extern int  g_swChargeOptInstalled;   // 遥测：0/1

// ---- [FOG-CAL2 F1] 灰雾净强度校准键 FogStrengthPct（auto | <0..100>，默认 auto；允许小数）----
//   auto  = 不补偿：桩按设计 s=256 ⇒ 与校准前部署**逐像素一致**（硬要求，见 docs/re/fog_strength_calibration.md §5）
//   <0..100> = 目标「净压暗（保留比例）」百分比 T（= 100 × 雾中/无雾 亮度比；**越大越亮**）；
//              内部换算 m = (T/100) / 0.71875（钳到 [0,1]）⇒ 桩强度 s = clamp(round(512 × (1 − m)), 0, 511)
//              ⇒ 净保留 = 0.71875 × (1 − s/512) ≈ T/100。可达域 T ∈ [0, 71.875]（越大越亮）。
extern char g_fogStrengthPctRaw[16];    // ini 原始串（"auto" 或数值串；启动/遥测日志用）
extern bool g_fogStrengthAuto;          // true = auto（默认；桩强度 = 256）
extern double g_fogStrengthPct;         // 数值档目标百分比 T ∈ [0,100]（auto 档 = -1.0；允许小数）
extern uint16_t g_fogStrengthScale256;  // 换算出的桩强度 s ∈ [0,511]（auto = 256；运行期全局，热路径直读）

extern FnBlit8Arg g_pOrigBlitTransXlatAlphaZRead;
extern FnBlit8Arg g_pOrigBlitTransXlat_G;
extern FnRLEBlitTransXlat g_pOrigRLEBlitTransXlat_G;
extern FnBlit8Arg g_pOrigBlitTrans_G;
extern FnBlit8Arg g_pOrigBlitTransDarken_G;
extern FnBlit8Arg g_pOrigBlitPlain_G;

extern FnSelectAutoTarget g_pOrigTechnoSelectAutoTarget;
extern FnSelectAutoTarget g_pOrigUnitSelectAutoTarget;
extern FnGreatestThreat g_pOrigTechnoGreatestThreat;
extern FnGreatestThreat g_pOrigUnitGreatestThreat;

extern FnDrawObject g_pOrigUnitDraw;
extern FnDrawObject g_pOrigInfantryDraw;
extern FnDrawObject g_pOrigAircraftDraw;
extern FnDrawObject g_pOrigBuildingDraw;
extern FnDrawObject g_pOrigBulletDraw;
extern FnCellClassDraw g_pOrigCellClassDraw;

class BlitterHooks {
public:
    void __thiscall Hook_BlitTransXlatAlphaZRead(
        void *dst, uint8_t *src, unsigned int length,
        uint16_t zMin, uint16_t *zBuf, uint16_t *aBuf, uint16_t aLvl, int warpOffset
    );

    void __thiscall Hook_BlitTransXlat_G(
        void *dst, uint8_t *src, unsigned int length,
        uint16_t zMin, uint16_t *zBuf, uint16_t *aBuf, uint16_t aLvl, int warpOffset
    );

    void __thiscall Hook_RLEBlitTransXlat_G(
        void *dst, uint8_t *src, uint8_t Length,
        int EncodedLen, int a6, int a7, int a8, int a9, int a10, int a11
    );

    void __thiscall Hook_BlitTrans_G(
        void *dst, uint8_t *src, unsigned int length,
        uint16_t zMin, uint16_t *zBuf, uint16_t *aBuf, uint16_t aLvl, int warpOffset
    );

    void __thiscall Hook_BlitTransDarken_G(
        void *dst, uint8_t *src, unsigned int length,
        uint16_t zMin, uint16_t *zBuf, uint16_t *aBuf, uint16_t aLvl, int warpOffset
    );

    void __thiscall Hook_BlitPlain_G(
        void *dst, uint8_t *src, unsigned int length,
        uint16_t zMin, uint16_t *zBuf, uint16_t *aBuf, uint16_t aLvl, int warpOffset
    );
};

class TargetHooks {
public:
    void __thiscall Hook_Techno_SelectAutoTarget();
    void __thiscall Hook_Unit_SelectAutoTarget();
    void* __thiscall Hook_Techno_Greatest_Threat(uintptr_t arg1, uintptr_t arg2, uintptr_t arg3);
    void* __thiscall Hook_Unit_Greatest_Threat(uintptr_t arg1, uintptr_t arg2, uintptr_t arg3);
};

class FogHooks {
public:
    void __thiscall Hook_Unit_Draw(void *pLocation, void *pBounds);
    void __thiscall Hook_Infantry_Draw(void *pLocation, void *pBounds);
    void __thiscall Hook_Aircraft_Draw(void *pLocation, void *pBounds);
    void __thiscall Hook_Building_Draw(void *pLocation, void *pBounds);
    void __thiscall Hook_Bullet_Draw(void *pLocation, void *pBounds);
};

void EnforceGameSpeedUnlock();
void EnableLowFragmentationHeap();
void CheckTelemetry();
bool InstallVTableHooks();
void RemoveVTableHooks();
extern "C" void UpdateVisionGrid();   // 供内联汇编桩直接调用（帧守卫）
void PatchSpySatBuildingTypes();
void LoadConfig();
void LogMessage(const char *fmt, ...);
bool MpActive();
int  GetEffectiveTargetScanInterval();
int  GetEffectiveTargetScanKey();
bool GetEffectiveMinimapFog();
void CheckMpGateTransition();
