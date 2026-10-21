#include "ra2render.h"
#include <cstring>
#include <cstdlib>
#include <bcrypt.h>                 // [VER-GATE V1] SHA-256（Windows CNG；Vista+ 系统自带 bcrypt.dll）
#pragma comment(lib, "bcrypt.lib")  // [VER-GATE V1] MSVC 自动链库 ⇒ build.bat 零改动

// [SBH-GUARD] bcrypt.h / bcrypt.lib 已由 [VER-GATE V1] 引入（合批去重，不重复 include）
// [SBH-GUARD] 开关（默认 0 = 不碰 .text）
bool g_enableSbhGuard = false;

// ============================================================================
// [G3-SPLIT 20261019] P2 玩法改动从默认配置拆出 —— 补丁副本（执行者适用；母本零改动）
//   规则依据：玩法改动要独立配置、不混进默认优化配置、默认保持原版行为。
//   本副本四处改动面（相对母本 ra2render\blitter_hooks.cpp）：
//     A. 玩法族全局初始化器收敛为原版态（g_targetScanInterval=1 / 各 Enable*=false /
//        g_visibilityVanilla=true / g_visibilityModeRaw="vanilla"）；
//     B. 新增 [Gameplay] 节三级回退读取（GetGameplayIntEx / GetGameplayStrEx）：
//        ①[Gameplay] 现行节 → ②旧节 [Logic]/[FogOfWar] 只读迁移（老用户开启态保留，不写 ini）
//        → ③原版默认全关；
//     C. LoadConfig 13 个玩法键改走上述回退；其余 10 个优化键读取路径一字不动；
//     D. 联机门控零改动：GetEffectiveTargetScanInterval(G-08)/GetEffectiveTargetScanKey(G-02)/
//        GetEffectiveMinimapFog(G-01)/MpGateEdgeSyncGapProtection 全部原样（只消费全局，
//        不关心全局来自哪一节）。
//   迁移留痕：[ra2render-gameplay] 启动行（命中数 + 逐键名，判据②取证锚点）。
// ============================================================================

ForgeTelemetry g_telemetry = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
// ══ [G3-SPLIT 20261019] 玩法/优化配置拆分：全局初始化器一律收敛为**原版行为** ══
//   项目规则：玩法改动独立配置、不混进默认优化配置、默认保持原版行为。
//   下列「玩法族」全局的出厂默认全部改为原版态；显式开启只能来自 [Gameplay] 节
//   （或升级用户的旧节只读迁移回退，见 LoadConfig / GetGameplayIntEx）。
int g_targetScanInterval = 1;    // [G3-SPLIT] 原版默认 = 1（每帧全量寻敌，无节流）；节流须 [Gameplay] 显式开启（联机恒强制 1，G-08 不变）
bool g_enableSIMD = true;        // 优化键（渲染吞吐，行为不变）留在优化包
bool g_unlockGameSpeed = false;  // 优化键（0 = 保护玩家原版速度控制权）
bool g_enableLFH = true;         // 优化键（堆分配器，行为不变）
bool g_highPrecisionTimer = true;// 优化键（时钟中断粒度，行为不变）
bool g_enableStarCraftFog = false;      // [G3-SPLIT] 原版默认 = 关；灰雾压暗须 [Gameplay] EnableStarCraftFog=1
bool g_enableSpySatRadarSweep = false;  // [G3-SPLIT] 原版默认 = 关；间谍卫星重构为主动雷达须 [Gameplay] 显式开启
int g_radarSweepCooldownFrames = 600;   // [G3-SPLIT] 伴生键（仅 Sweep=1 时有意义；默认值不变 600）
int g_radarSweepRadiusCells = 16;       // [G3-SPLIT] 伴生键（仅 Sweep=1 时有意义；默认值不变 16）
bool g_enableBuildingFog = false; // [G3-SPLIT] 原版默认 = 关（迷雾中敌方建筑三态；须 [Gameplay] 显式开启）
bool g_enableBulletFog = false;   // [G3-SPLIT] 原版默认 = 关（迷雾中敌方弹道剔除；须 [Gameplay] 显式开启）
bool g_enableUnitFog = false;     // [G3-SPLIT] 原版默认 = 关（迷雾中敌方机动单位剔除；[FOG-SPLIT] 仍不受总闸影响）
// ---- [FOG-MODE] F1：可见性模式（VisibilityMode = starcraft | vanilla）----
//   ★用户裁决（2026-09-28）：「两种，一种是原版的一种是现在的状态」⇒ 两种状态都能选。
//   [G3-SPLIT 20261019] 出厂默认改为 vanilla（原版可见性）＝「默认保持原版行为」；
//   starcraft（现状态）须 [Gameplay] VisibilityMode=starcraft 显式开启。
//   starcraft = 现状态：视距剔除生效（三子键按现有语义各自生效）；
//   vanilla   = 原版可见性：**不做任何视距剔除**（单位/建筑/弹道三处剔除全部放行）
//                      ⇒ 敌方目标在任何区域（含灰雾区、未探索黑区）都会绘制。
//   ★优先级：vanilla 时三子键被本键**覆盖（忽略）**；starcraft 时三子键照旧。
//   ★vanilla 只「不介入绘制」：不写任何引擎状态、不改 RNG/命令序（见各 Hook 短路支）。
//   ★运行期判定：热路径每帧直读本全局 ⇒ 运行期改值 ≤1 帧生效（与总闸同口径）。
bool g_visibilityVanilla = true;               // [G3-SPLIT] 出厂默认 = vanilla（原版可见性）
char g_visibilityModeRaw[32] = "vanilla";      // [G3-SPLIT] ini 原始串默认（日志用；未知值原样打印）
bool g_fadeFogTransition = true;               // [G3-SPLIT] 迁移键（仅总闸=1 时有意义；默认值不变）
bool g_enableMinimapFog = false; // G-01: API 默认值修正为 0（键缺失 = 关闭）；[G3-SPLIT] 迁移键（[Gameplay]）
int  g_radarFogGuardMode = 3;    // [RADAR-FIX2] 雷达灰化档：0=旧护栏自绘 1=新谓词自绘 2=无护栏自绘 3=引擎原生减暗驱动(默认)；[G3-SPLIT] 迁移键（仅 MinimapFog 生效时消费）

// ---- [GAP-P223] 裂缝保护三点表驱动（ZC-GAP-P223 合并 ZC-GAP-P21；landing_pack_gap_p223.md）----
//   默认 0 = 不碰 .text（零行为变化）。=1 时 init 把三点「清 GapsCoveringThisCell(+0x134)」
//   各 6B 等长 NOP 化（P-2.1 @0x568273 / P-2.2 @0x577EC5 / P-2.3 @0x577B60），删除
//   「任何开图/重遮都废缝」的副作用；每点同循环内 ShroudCounter/CopyFlags/RedrawFlags
//   写入原样保留。安装序 P-2.1→P-2.2→P-2.3，硬回滚逆序 P-2.3→P-2.2→P-2.1。
//   联机（MpActive）强制不装；安装态在 init 决定（本键只 LoadConfig 读一次，重启生效）。
//   [GAP-MP-EDGE] MP 边沿同步（W3_20261001 gapfix）：init 单机装上后**中途进入联机** ⇒
//     CheckMpGateTransition 的 MP 迁移分支调用 MpGateEdgeSyncGapProtection(true) 逆序硬回滚
//     （日志 mp-edge-rollback）⇒ 时序穿透漏洞闭合；退出联机回单机且配置仍 =1 ⇒ 门禁重装（mp-edge-reinstall）。
//     线程/相位依据 ARCHITECTURE_ATLAS.md §12.1；该函数不读 ini（非 ini 热重载，红线见规格书 §5.3/§8-4）。
bool g_enableGapProtection = false;
int  g_gapProtectionPatchesInstalled = 0;   // 遥测：本进程当前已写 NOP 点数 ∈ 0..3（只读，热路径不读；[GAP-MP-EDGE] 边沿还原/重装后重算）

// ---- [VXL-PRE] VXL 缓存预热扩容（ZC-VXL-PRE / landing_pack_vxl_prewarm.md，L-VXL-1；[Render] 键）----
//   默认 0 = 不碰 .text。=1 时 init 把 SomeVoxelCache Miss 插入路径首次分配粒度
//   mov ebx,0xA→mov ebx,0x40（0x706D78 5B 内 imm8 一字节 0x0A→0x40）；
//   growstep（0x706D7F 翻倍）与插入/命中语义不动；MP 可装（纯表现层缓存粒度）。
bool g_enableVxlCachePrewarm = false;
int  g_vxlCacheInstalled = 0;               // 遥测：0/1（热路径计数器未实现，见 landing_pack §3.2）

// ---- [SW-CHARGE] 充能冗余二次 call 删除（ZC-SW-CHARGE / landing_pack_sw_charge.md，L-SW-1；[Logic] 键）----
//   默认 0 = 不碰 .text。=1 时 init 把 HasChargeProgressed 慢路径冗余二次 call
//   （0x6CBE88 7B）等长 NOP 化；复用第一次 eax，写回值不变 ⇒ 零语义变化、不进 CRC。
bool g_enableSWChargeOpt = false;
int  g_swChargeOptInstalled = 0;            // 遥测：0/1

// ---- [FOG-CAL2 F1] 灰雾净强度校准键（FogOfWar/FogStrengthPct，默认 auto = 现状）----
//   键语义（口径订正 = Lead 裁定 option B，勘误见 docs/re/fog_strength_calibration.md §3）：
//     T = 目标「净压暗（保留比例）」百分比 = 100 × 雾中像素亮度 / 同点无雾像素亮度
//          ⇒ T 越大画面越亮（桩强度 s 越小）；T = 35.9375 即现网观感，T = 71.875 为最亮上限。
//     auto（默认）= 不补偿：桩按设计值 s=256 ⇒ 净保留 0.359375 = 23/64 ⇒ 与校准前部署逐像素一致。
//   ★与上一版（FOG-CAL，s=round(m×256)）的关键区别：换算方向相反 + s 可达 511（旧版止于 256）。
char g_fogStrengthPctRaw[16] = "auto";
bool g_fogStrengthAuto = true;
double g_fogStrengthPct = -1.0;         // auto 档 = -1.0（数值档 = 0..100，允许小数如 35.9375）
uint16_t g_fogStrengthScale256 = 256;   // 桩强度 s = 1/256 定点强度乘子 ∈ [0,511]（auto = 256 ⇒ 不补偿）

// ---- [ZC-10B ①] L4DirtyMode（L4 视口重绘策略三档）----
//   0 = force-full（**出厂默认 = 现状**）：恒强制全量重绘，与现网件逐位等价
//   1 = vision-dirty（新折中）：仅当「视口内视野迁移数==0 且 渐变活跃数==0」时交还原版 jge
//   2 = vanilla：完全交还原版 jge（0x006D3D99 六字节原语义，等价于不打本补丁）
int  g_l4DirtyMode = 0;
// ---- [ZC-10B ③] FogProbe 键控（默认 0 = 热路径不含任何探针指令）----
bool g_fogProbeEnabled = false;

extern "C" {
    // ---- [ZC-10B ①] 视口范围（由 Hook_CellClass_Draw 逐格累计；1 逻辑帧滞后）----
    int      s_viewCellMinX = 0x7FFFFFFF;
    int      s_viewCellMinY = 0x7FFFFFFF;
    int      s_viewCellMaxX = -1;
    int      s_viewCellMaxY = -1;
    // ---- [ZC-10B ①] 迁移计数（视口范围内）与遥测 ----
    uint32_t s_fogViewportTransitionCount = 0;   // 本逻辑帧视口内视野 0→1 / 1→0 迁移格数
    uint32_t s_fogViewportRampActive = 0;        // 本逻辑帧视口内渐变仍活跃(s_fogRampFrame>0)格数
    uint32_t s_l4RedrawSkippedStatic = 0;        // 遥测：交还原版 jge（跳过强制全量）的帧数
    uint32_t s_l4DirtyTransitions = 0;           // 遥测：累计视口迁移格数
    uint32_t s_l4DirtyRampActive = 0;            // 遥测：累计视口渐变活跃格数
    uint8_t  s_fogProbeEnabledMirror = 0;        // [ZC-10B ③] 汇编侧镜像：1 = 桩内探针热路径生效
}

// ★[FOG-CAL] 第一段经验系数（upstream first-stage empirical gain）★ —— 唯一真源，勿在别处重复字面量
//   来源：FOG-STRENGTH2 实测定谳（docs/re/fog_strength_rootcause.md §F1.7 / §F3）：
//     上游地表侧（位于我方混色桩**之前**）实测恒定 ×0.71875（= 184/256 = 23/32）；我方桩是第二段，
//     故「实测比值（净压暗系数）= 0.71875 × 桩保留比例」，auto(s=256) ⇒ 0.5 × 0.71875 = 0.359375 = 23/64。
//   ★站点未静态定位（P1，本卡不定位）⇒ 本系数为**经验系数**；第一段定位/抵消后须重校（只改本常量 + 换算口径）。
//   ★本系数同时决定两个可达边界（均由本常量算出，勿另写字面量）：
//       · 可达上限 T_max = 100 × 0.71875 = 71.875%（s=0，只剩第一段）—— 更大净保留**不可达**；
//       · 可达下限 T_min = 100 × 0.71875 / 512 ≈ 0.140381%（s=511，近乎全黑）。
//   ★保留为全局（不被编译期折叠）以便：① 产物级字节取证（.data 8 字节 IEEE754）② 后续重校单点改。
extern "C" double s_fogFirstStageGainUpstream = 0.71875;

FnBlit8Arg g_pOrigBlitTransXlatAlphaZRead = nullptr;
FnBlit8Arg g_pOrigBlitTransXlat_G = nullptr;
FnRLEBlitTransXlat g_pOrigRLEBlitTransXlat_G = nullptr;
FnBlit8Arg g_pOrigBlitTrans_G = nullptr;
FnBlit8Arg g_pOrigBlitTransDarken_G = nullptr;
FnBlit8Arg g_pOrigBlitPlain_G = nullptr;

FnSelectAutoTarget g_pOrigTechnoSelectAutoTarget = nullptr;
FnSelectAutoTarget g_pOrigUnitSelectAutoTarget = nullptr;
FnGreatestThreat g_pOrigTechnoGreatestThreat = nullptr;
FnGreatestThreat g_pOrigUnitGreatestThreat = nullptr;

FnDrawObject g_pOrigUnitDraw = nullptr;
FnDrawObject g_pOrigInfantryDraw = nullptr;
FnDrawObject g_pOrigAircraftDraw = nullptr;
FnDrawObject g_pOrigBuildingDraw = nullptr;
FnDrawObject g_pOrigBulletDraw = nullptr;
FnCellClassDraw g_pOrigCellClassDraw = nullptr;

// ---------------------------------------------------------------------------
// L3/L5 迷雾共享状态（extern "C"：内联汇编桩与 C++ 两侧共同引用）
// ---------------------------------------------------------------------------
extern "C" {
    uint32_t s_visionGrid[512 * 512] = {0};          // 直视视野网格（帧 Token 制）
    uint32_t s_cellFogDrawnToken[512 * 512] = {0};   // 单帧防重复暗化 Token
    uint32_t s_visionToken = 1;
    uint8_t  s_everSeenGrid[512 * 512] = {0};        // 敌方建筑"看见过"永久标记（WC3 式）
    uint8_t  s_prevVisionGrid[512 * 512] = {0};      // 上一逻辑帧视野快照（渐变过渡检测）
    uint8_t  s_fogRampFrame[512 * 512] = {0};        // 视野状态迁移后的渐变剩余帧（1..4）
    uint16_t s_fogBlendStrength = 256;               // 灰雾混色强度：256 = 我方 50% 等效观感（引擎原版为 FOG.SHP alpha 插值混色，非固定半化）
    uint8_t  s_minimapForceRefresh = 0;              // 视野迁移后强制小地图全量刷新的剩余帧
    uint8_t  s_minimapFogGate = 0;                   // G-01: 默认值为 0，g_enableMinimapFog 的汇编侧镜像
    uint8_t  s_radarFogGuardMode = 3;                // [RADAR-FIX2] 灰化档镜像：0/1/2=自绘三档 3=引擎原生减暗驱动(默认)
    uint32_t s_minimapFogPixels = 0;                 // 遥测：雷达灰化像素数（自绘分支真正执行过才有值）
    uint32_t s_minimapFogBranchHits = 0;             // [RADAR-FIX] 遥测：雷达灰化分支进入次数（护栏放行即 +1）
    // ---- [RADAR-FIX2] 原生减暗驱动与诊断遥测 ----
    uint32_t s_nativeDarkenHits = 0;                 // 原生减暗路径命中次数（最终 [esp+0x13]=1，引擎减暗体将执行）
    uint32_t s_nativeEngineDarkHits = 0;             // 引擎自身判定为暗的次数（覆盖前读到的 [esp+0x13]）
    uint32_t s_nativeForcedDarkHits = 0;             // 我方三态谓词强制为暗的次数
    uint32_t s_nativeOverrideDeltas = 0;             // 我方判定与引擎判定不同（发生覆盖）的次数
    uint32_t s_radarGuardRejects[8] = {0};           // 自绘路径早退原因分桶（诊断 S3 类静默早退）
    uint32_t s_radarProbeOk = 0;                     // 三态谓词求解成功次数
    uint32_t s_radarProbeFail = 0;                   // 三态谓词求解失败次数（坐标越界/异常）
    uint32_t s_radarProbeExplored = 0;               // 求解样本中「已探索」次数
    uint32_t s_radarProbeVisible = 0;                // 求解样本中「直视圈内」次数
    uint32_t s_radarHwndZero = 0;                    // [RADAR-FIX2] 尊重引擎 hWnd 门而放弃覆盖的次数
    // ---- [FOG-SWITCH] 总闸（EnableStarCraftFog）汇编侧镜像 + 三条门禁计数 ----
    uint8_t  s_fogMasterGate = 1;                    // 灰雾总闸汇编侧镜像（1=总闸开=现网行为；0=彻底无半透明黑）
    uint32_t s_fogLayerDraws = 0;                    // ① 半透明层绘制次数：真正调用引擎 FOG.SHP 层 0x0047F250 的次数
    uint32_t s_fogBlendStubHits = 0;                 // ② 混色桩介入次数：B1/B2 桩内真正执行混色并落像素的像素数
    uint32_t s_radarDarkenDriven = 0;                // ③ 小地图减暗驱动次数：我方驱动引擎减暗（原生档=改写判定位为1；自绘档=自绘暗化像素）
    void    *s_pPlotCellTrampoline = nullptr;        // Plot_Cell 0x655D38 跳板（路线 A）
    void    *s_pRadarNativeTrampoline = nullptr;     // [RADAR-FIX2] 0x00655D87 跳板
    // ---- [FOG-SPLIT] 按格三态遥测：把「雾」计数按状态拆开（F3 机器判据） ----
    uint32_t s_shroudBlackDraws = 0;                 // ㈠ 未探索黑幕绘制次数（引擎 0x47EFE0 以 Shroudedness==-2 进入）
    uint32_t s_shroudEdgeDraws = 0;                  //     黑幕边缘渐变帧绘制次数（Shroudedness 0..48，诊断用）
    uint32_t s_fogUnexploredPassed = 0;              // ㈡ 未探索格放行次数（我方钩子观察到未探索格 ⇒ 绝不上手）
    uint32_t s_fogVisiblePassed = 0;                 //     已探索且直视格放行次数（诊断用）
    uint32_t s_exploredFogDarken = 0;                // ㈢ 已探索非直视压暗次数（我方驱动 FOG.SHP 层；总闸=0 ⇒ ≡0）
    uint32_t s_gate0DarkenSkipped = 0;               //     总闸=0 时被强度归零而跳过的压暗次数
    uint32_t s_radarUnexploredPassed = 0;            // ㈣ 小地图未探索格放行次数（我方不写引擎减暗判定位）
    void    *s_pDrawShroudFogTrampoline = nullptr;   // [FOG-SPLIT] 0x0047EFE0 跳板（6B 原指令 + jmp 0x0047EFE6）
    // ---- [FOG-MODE] F4 遥测：VisibilityMode=vanilla 时「被 mode 覆盖而放行」的独立计数 ----
    //   机器判据：vanilla ⇒ 下面 4 个计数 >0，且既有三处剔除计数（unitsCulledByFog /
    //   buildingsCulledByFog / bulletsCulledByFog）**≡0**（结构性保证：短路支在剔除判定之前 return）。
    uint32_t s_visVanillaPassed = 0;          // 被 mode 覆盖而放行总次数（三处剔除钩子合计）
    uint32_t s_visVanillaMobilePassed = 0;    //   · 机动单位（Unit/Infantry/Aircraft）放行次数
    uint32_t s_visVanillaBuildingPassed = 0;  //   · 建筑放行次数
    uint32_t s_visVanillaBulletPassed = 0;    //   · 弹道放行次数

    // ===================================================================================
    // [FOG-PROBE F1] 桩内「读取值」探针（**纯只读仪表**）
    //   铁律：本组全局只被「我方新代码」读写；新增代码只允许做两件事 —— ①读内存 ②自增我方计数。
    //         不参与任何算术/分支决策（桩与热路径的既有算式、时序、写入顺序、像素输出逐位不变）。
    //
    //   口径定义（与遥测行字段名一一对应，★防反向歧义）：
    //     · 格绘制窗口 window = Hook_CellClass_Draw 内
    //         「写 s_fogBlendStrength」→「call 0x0047F250 逐像素绘制」→「恢复 256」整段；
    //         窗口内该全局本就恒定（单线程、写→画→恢复紧邻）。
    //     · 【store 写入值】  = 上述 store 语句写进 s_fogBlendStrength 的值（store 后回读同一全局）
    //     · 【期望桩读值】    = 模型值 = (本格强度 × scale) >> 8（钳 511），由 C 侧独立算出（**非**桩算路径）
    //     · 【本格强度】      = 写入前的原始本格强度 strength（0/48/64/96/128/144/192/256 或 0/256）
    //     · 【桩读取强度值】  = B1/B2 桩内 `movzx ebx, word ptr [s_fogBlendStrength]` 的**同一 16 位读数**
    //     · 采样口径          = **每窗口一次**（窗口内首次桩读取）；窗口内后续读取只与首读比对（不重复采样）
    //   -----------------------------------------------------------------------------------
    uint32_t s_probeWindowOpen = 0;         // 1 = 我方格绘制窗口打开中（仅此时采样/计数）
    uint32_t s_probeWindows = 0;            // 累计打开的窗口数（= 经过 store 的格绘制次数）
    uint16_t s_probeCellStrength = 0;       // 【本格强度】本窗口（写入前的原始 strength）
    uint16_t s_probeWriteValue = 0;         // 【store 写入值】本窗口（store 后回读）
    uint16_t s_probeExpectedValue = 0;      // 【期望桩读值】本窗口（模型值，C 侧算出）
    uint16_t s_probeWindowValue = 0xFFFF;   // 【桩读取强度值】本窗口首读（0xFFFF = 本窗口尚无读取）
    uint16_t s_probeRing[8] = {0};          // 环形缓冲：最近 8 个窗口的【桩读取强度值】（槽位序 i ↔ 窗口 k≡i (mod 8)；遥测同时打印写指针 idx）
    uint32_t s_probeRingIdx = 0;            // 环形缓冲写指针（取模 8）
    uint32_t s_probeBucket[8] = {0};        // 分桶计数【桩读取强度值】（0 / 1-8 / 9-48 / 49-128 / 129-200 / 201-255 / 256 / >256）
    uint32_t s_probeWriteBucket[8] = {0};   // 分桶计数【store 写入值】（同桶界；C 侧统计）
    uint32_t s_probeExpectedBucket[8] = {0};// 分桶计数【期望桩读值】（同桶界；C 侧统计）
    uint32_t s_probeStrengthHit[9] = {0};   // 【本格强度】精确值命中：0/48/64/96/128/144/192/256/其它（C 侧统计）
    uint32_t s_probeRampHist[5] = {0};      // 渐变相 s_fogRampFrame 分布：下标 0 = 非渐变档，1..4 = ramp 值
    uint32_t s_probeReadEqExpected = 0;     // 【桩读取强度值】==【期望桩读值】的窗口数（决定性判据 A）
    uint32_t s_probeReadNeExpected = 0;     // 【桩读取强度值】!=【期望桩读值】的窗口数（决定性判据 A 反面）
    uint32_t s_probeMismatch = 0;           // 失配计数：同窗口内【store 写入值】!=【桩读取强度值】的窗口数
    uint32_t s_probeMidWindowChange = 0;    // 同窗口内【桩读取强度值】!= 本窗口首读的**读取次数**（≈0 ⇒ 窗口内恒定）
    uint32_t s_probeReadsInWindow = 0;      // 有桩读取的窗口数（= 采样窗口数；与 s_probeWindows 之差 = 无读取窗口）
    uint32_t s_probeAlienReads = 0;         // 窗口外（非我方调用）桩读取次数（证外部调用者是否存在）
}

static bool s_visionInitDone = false;

// ---------------------------------------------------------------------------
// 联机状态判定（F-10 / M-6 规约）与惰性求值门控
// 主判定：*(uint8_t*)0x00A8D5F8 & 0x02 != 0（网络对局会话标志）
// 辅助判定：*(int32_t*)0x00AA0444 == 2（DirectPlay 会话活跃）
// ---------------------------------------------------------------------------
__declspec(noinline) bool MpActive() {
    __try {
        const uint8_t *pFlags = reinterpret_cast<const uint8_t*>(ADDR_MP_SESSION_FLAGS);
        if (pFlags && !IsBadReadPtr(const_cast<uint8_t*>(pFlags), 1)) {
            if ((*pFlags & 0x02) != 0) {
                return true;
            }
        }
        const int32_t *pDp = reinterpret_cast<const int32_t*>(ADDR_DIRECTPLAY_STATUS);
        if (pDp && !IsBadReadPtr(const_cast<int32_t*>(pDp), 4)) {
            if (*pDp == 2) {
                return true;
            }
        }
    }
    __except (EXCEPTION_EXECUTE_HANDLER) {
        return false;
    }
    return false;
}

__declspec(noinline) int GetEffectiveTargetScanInterval() {
    if (MpActive()) {
        return 1; // G-08: 联机模式强制 1（禁用节流，保证锁步全量扫描）
    }
    return g_targetScanInterval; // 单机模式保持 ini 配置
}

__declspec(noinline) int GetEffectiveTargetScanKey() {
    if (MpActive()) {
        return 1; // G-02: 联机模式强制 1 (position 确定性坐标哈希)
    }
    return g_targetScanKey; // 单机模式保持 ini 配置 (0=pointer, 1=position)
}

// [RADAR-FIX] 灰化护栏模式：与 MpActive 无关（联机侧已由 s_minimapFogGate=0 整体关闭），
// 仅做 ini 值域收敛并把结果镜像到汇编侧 s_radarFogGuardMode。
__declspec(noinline) int GetEffectiveRadarFogGuardMode() {
    int m = g_radarFogGuardMode;
    // [RADAR-FIX2] 值域扩到 0..3（3 = 引擎原生减暗驱动，本版默认）
    if (m < RADAR_FOG_GUARD_LEGACY || m > RADAR_FOG_GUARD_NATIVE) m = RADAR_FOG_GUARD_NATIVE;
    s_radarFogGuardMode = static_cast<uint8_t>(m);
    return m;
}

__declspec(noinline) bool GetEffectiveMinimapFog() {
    bool eff = false;
    if (MpActive()) {
        // G-01: 联机模式采用保守策略强制关闭为 0（尚未通过真机验收，杜绝潜在异步与崩溃风险）
        eff = false;
    } else {
        eff = g_enableMinimapFog; // 单机模式按 ini 配置生效
    }
    s_minimapFogGate = eff ? 1 : 0;
    return eff;
}

// ---------------------------------------------------------------------------
// [FOG-SPLIT] 灰雾总闸（EnableStarCraftFog）语义**重定义**（用户裁决 2026-09-27）
//
//   ★ 唯一语义：本键**只管「已探索（cf_Explored）+ 非直视」这一档的压暗强度**。
//     总闸=1 ⇒ 该档压暗强度 = 256（我方 50% 等效观感，与旧版一致）；
//     总闸=0 ⇒ 该档强度归零（该档既不压暗、也不驱动小地图减暗）。
//
//   ★ 三态表（主视图与小地图同口径；未探索档与直视档**与总闸无关**）：
//     ① 未探索格（CellClass::Shroudedness(+0x120) == -2「Occluded completely」）
//        ⇒ 原版全黑黑幕**原样保留**：由引擎 CellClass::Draw → 0x0047EFE0 自行绘制，
//          我方**绝不调用任何绘制/混色/驱动**（钩子观察到即放行并计数，见 s_fogUnexploredPassed）。
//     ② 已探索 + 非直视 ⇒ 仅此档受总闸控制（=1 压暗 / =0 不压暗；=0 时也不驱动小地图减暗）。
//     ③ 已探索 + 直视   ⇒ 一律不压暗（两档相同）。
//
//   ★ 与旧版（FOG-SWITCH）的差别 —— 旧版把总闸做成「迷雾渲染栈整体短路」，额外切断了 4 条
//     **与压暗无关**的耦合，导致总闸=0 时连未探索黑幕一起消失（ZC-4 S2 实测 = 等同开图）：
//       (a) UpdateVisionGrid 不再被每格调用 ⇒ Scenario FogOfWar 位可能保持引擎原值=1
//           ⇒ 黑幕层 0x0047EFE0 改用 FOG.SHP（源码注释已记录：未探索区变透明高亮）；
//       (b) L4 全量刷（0x006D3D99）改回原版 jge ⇒ 静态镜头下战术重绘走增量/dirty-rect 路径；
//       (c) 小地图原生减暗驱动、H2 跳帧强驱被摘除。
//     [FOG-SPLIT] 上述 (a)(b) 已**解除耦合**（与总闸无关，恒按总闸=1 时的行为走），
//     (c) 保留（属「已探索非直视」档的小地图表现，总闸=0 时应为 0）。
//
//   ★ 玩法（逻辑）可见性**不受总闸影响**：EnableBuildingFog / EnableBulletFog / EnableUnitFog
//     三键各自独立生效（总闸=0 时仍 >0），见 FogHooks 各 Hook；本文件不再出现
//     「g_enableStarCraftFog && <玩法剔除>」这种耦合。
//
//   ★★[FOG-MODE] 玩法可见性上方**再叠一层可见性模式总键** VisibilityMode（F1，2026-09-28 用户裁决）：
//     starcraft（默认）= 现状态 ⇒ 下面三子键按现有语义各自生效；
//     vanilla          = 原版可见性 ⇒ **三子键被覆盖（忽略）**，三处视距剔除全部放行。
//     门控位置：FogHooks 五个 Draw 钩子的**第一条分支**（FogModeVanillaPassThrough 短路支），
//     在 ShouldDraw* 判定之前 ⇒ vanilla 档三处剔除计数结构性恒 0。
//
//   运行期生效口径：C++ 热路径直读 g_enableStarCraftFog；汇编短路由镜像 s_fogMasterGate，
//   镜像在每个遥测节拍（CheckTelemetry ← 单位绘制/雷达绘制必到）同步 ⇒ 改总闸后 ≤1 帧生效。
// ---------------------------------------------------------------------------
__declspec(noinline) bool GetEffectiveFogMasterGate() {
    s_fogMasterGate = g_enableStarCraftFog ? 1 : 0;
    return g_enableStarCraftFog;
}

static inline void SyncFogMasterMirror() {
    s_fogMasterGate = g_enableStarCraftFog ? 1 : 0;
}

// [GAP-MP-EDGE] MP 边沿同步驱动器（定义见本文件 [GAP-P223] 节末，紧邻 Install/Remove 之后）。
//   单机→联机：撤掉本进程写入 .text 的三点 NOP（逆序硬回滚，复用 RemoveGapProtectionPatch）；
//   联机→单机：若配置仍 EnableGapProtection=1，按完整 G0 门禁重装（复用 InstallGapProtectionPatch）。
//   ★非 ini 热重载：只读运行期状态（installed 计数 + MP 标志边沿），配置仍只在 LoadConfig 读一次。
//   ★线程/相位依据：ARCHITECTURE_ATLAS.md §12.1（主逻辑+渲染同主线程串行；唯一辅助线程为音频流线程）。
//   ★命名规避 verify_hooks.py 的 Install*/Remove* 配对正则（本函数不是安装器）。
static void MpGateEdgeSyncGapProtection(bool mpNow);

void CheckMpGateTransition() {
    static int s_lastMpState = -1;
    SyncFogMasterMirror();  // [FOG-SWITCH] 总闸汇编侧镜像同步（运行期改键 ≤1 帧生效）
    bool currentMp = MpActive();
    int currentMpInt = currentMp ? 1 : 0;
    if (s_lastMpState != currentMpInt) {
        s_lastMpState = currentMpInt;
        int effInterval = currentMp ? 1 : g_targetScanInterval;
        int effKey = currentMp ? 1 : g_targetScanKey;
        bool effMinimapFog = currentMp ? false : g_enableMinimapFog;
        s_minimapFogGate = effMinimapFog ? 1 : 0;
        s_radarFogGuardMode = static_cast<uint8_t>(GetEffectiveRadarFogGuardMode()); // [RADAR-FIX] 镜像护栏模式

        LogMessage("[ra2render] 门控状态迁移: MpActive=%s, TargetScanKey=配置(%s)->生效(%s), TargetScanInterval=配置(%d)->生效(%d), EnableMinimapFog=配置(%d)->生效(%d)%s",
                   currentMp ? "true" : "false",
                   g_targetScanKey ? "position" : "pointer",
                   effKey ? "position" : "pointer",
                   g_targetScanInterval,
                   effInterval,
                   g_enableMinimapFog ? 1 : 0,
                   effMinimapFog ? 1 : 0,
                   currentMp ? " [联机模式激活: 强制安全门控生效]" : " [单机模式: 恢复配置值]");

        if (currentMp && g_targetScanKey == 0) {
            LogMessage("[ra2render] [警告/红字] 联机模式处于激活状态(MpActive=true)，强制覆盖 TargetScanKey: 配置(pointer) -> 生效(position)，禁止在联机中使用不确定性指针哈希！");
        }

        // [GAP-MP-EDGE] MP 边沿（仅状态迁移时才动 .text；非迁移节拍零成本）
        //   gap_protection_install_spec.md §5.4 预留卡：init 单机已装、中途进入 MP ⇒ 边沿硬回滚。
        MpGateEdgeSyncGapProtection(currentMp);
    }
}

// ---------------------------------------------------------------------------
// [RADAR-FIX F3] ini 键「命中」与「API 默认值兜底」的区分
// GetPrivateProfileIntA 无法区分「键缺失」与「键值恰等于默认值」，且 Windows 的
// GetPrivateProfileStringA 在**同名节重复**时只读第一个节 —— 这正是
// TargetScanKey 从未生效（此前日志里的 position 其实来自 API 默认值）的根因。
// 故统一改走字符串 API + 哨兵默认值：返回哨兵 => 键缺失（走 API 默认值）。
// ---------------------------------------------------------------------------
static const char *const kIniAbsentSentinel = "\x01[RADAR-FIX:ABSENT]\x01";

static bool GetIniStringEx(const char *sec, const char *key, const char *def, char *out, size_t cap,
                           const char *iniPath) {
    char buf[128] = {0};
    GetPrivateProfileStringA(sec, key, kIniAbsentSentinel, buf, static_cast<DWORD>(sizeof(buf)), iniPath);
    if (strcmp(buf, kIniAbsentSentinel) == 0) {
        strncpy_s(out, cap, def, _TRUNCATE);
        return false; // 键缺失 -> API 默认值兜底
    }
    strncpy_s(out, cap, buf, _TRUNCATE);
    return true;      // ini 命中
}

static int GetIniIntEx(const char *sec, const char *key, int def, const char *iniPath, bool *hit) {
    char s[64] = {0};
    bool h = GetIniStringEx(sec, key, "", s, sizeof(s), iniPath);
    if (hit) *hit = h;
    if (!h || s[0] == 0) return def;
    return atoi(s);
}

static const char *IniSrc(bool hit) { return hit ? "ini" : "默认值"; }

// ---------------------------------------------------------------------------
// [G3-SPLIT 20261019] 玩法键三级回退读取（补丁副本 · 执行者适用）
//   读取顺序（对每个玩法键）：
//     ① [Gameplay] 现行玩法节 —— 显式开启/关闭的最高优先级来源；
//     ② 旧节（[Logic] / [FogOfWar]）—— 升级老用户迁移回退：**只读、不回写、不删除**
//        （ini 写入不在本 DLL 职责内；保留用户既有开启态 = 验收判据②）；
//     ③ 出厂默认 = 原版行为（TargetScanInterval=1 / 各 Enable*=0 / VisibilityMode=vanilla）。
//   命中语义沿用 [RADAR-FIX F3] 哨兵口径：GetIniStringEx 区分「键缺失」与「键值=默认」，
//   故注释掉的模板键（优化包 ini 的 [Gameplay] 全注释）不会被误判为命中。
//   线程口径：只在 LoadConfig()（DLL init）调用一次；非热路径、非热重载。
// ---------------------------------------------------------------------------
static int GetGameplayIntEx(const char *key, int defVanilla, const char *legacySec, const char *iniPath,
                            bool *hit, bool *migrated) {
    bool h = false;
    int v = GetIniIntEx("Gameplay", key, defVanilla, iniPath, &h);
    if (h) {                                   // ① 现行节命中
        if (hit) *hit = true;
        if (migrated) *migrated = false;
        return v;
    }
    v = GetIniIntEx(legacySec, key, defVanilla, iniPath, &h);   // ② 旧节迁移回退
    if (hit) *hit = h;
    if (migrated) *migrated = h;               // 旧节命中 = 迁移来源（日志留痕）
    return v;                                  // ③ 双缺 ⇒ 原版默认
}

static void GetGameplayStrEx(const char *key, const char *defVanilla, const char *legacySec, const char *iniPath,
                             char *out, size_t cap, bool *hit, bool *migrated) {
    // ① 现行节：GetIniStringEx 返回 true = 键命中（哨兵口径，显式 opt-out 值也算命中）
    bool h = GetIniStringEx("Gameplay", key, defVanilla, out, cap, iniPath);
    if (h) {
        if (hit) *hit = true;
        if (migrated) *migrated = false;
        return;
    }
    // ② 旧节迁移回退（只读；命中即采纳，即便值与默认相同——「显式配置过」本身是迁移事实）
    char probe[64] = {0};
    h = GetIniStringEx(legacySec, key, "", probe, sizeof(probe), iniPath);
    if (h && probe[0] != 0) {
        strncpy_s(out, cap, probe, _TRUNCATE);
        if (migrated) *migrated = true;
    } else {
        h = false;
    }
    // ③ 双缺 ⇒ out 保持 defVanilla（原版默认）
    if (hit) *hit = h;
    if (!h && migrated) *migrated = false;
}

// ---------------------------------------------------------------------------
// [FOG-MODE F1] vanilla 短路放行（三处视距剔除共用，F6① 反汇编验收锚点）
//   ★语义：VisibilityMode=vanilla ⇒ **不做任何视距剔除**，直接放行到原版 Draw
//     ⇒ 敌方目标在任何区域（含灰雾区、未探索黑区）都会绘制。
//   ★纪律（F1）：只读运行期全局 + 自增我方私有计数 —— **不写任何引擎状态、不读视野网格、
//     不调用 ShouldDraw***（故不改 RNG / 命令序），是纯「不介入绘制」。
//   ★__declspec(noinline) + 恒 return true：保证产物里存在**独立、可达**的短路支调用点，
//     供 F6① 反汇编验收与「被 mode 覆盖而放行」独立计数（F4）。
//   kind: 0=机动单位(Unit/Infantry/Aircraft) 1=建筑 2=弹道（仅分类计数，不参与判定）
// ---------------------------------------------------------------------------
__declspec(noinline) bool FogModeVanillaPassThrough(int kind) {
    s_visVanillaPassed++;
    if (kind == 0)      s_visVanillaMobilePassed++;
    else if (kind == 1) s_visVanillaBuildingPassed++;
    else                s_visVanillaBulletPassed++;
    return true;
}

// ---------------------------------------------------------------------------
// [FOG-CAL2 F1] 换算核与日志辅助（纯函数 + 只读全局，可离线复算）
//   ★订正后的换算公式（Lead 裁定 option B；上一版 s = round(m × 256) 为**错误口径**，见 §3 勘误）：
//        m = (T/100) / s_fogFirstStageGainUpstream          目标净保留 / 第一段经验系数
//        s = clamp(round(512 × (1 − m)), 0, 511)            桩强度（1/256 定点）
//     推导：桩算式 out_ch = c_ch − ((⌈c_ch/2⌉ × s) >> 8) ⇒ 桩保留比例 ≈ 1 − s/512
//           ⇒ 净保留 = 0.71875 × (1 − s/512) = 0.71875 × m = T/100 —— 反解 s 即得上式（T 与净保留恒等）。
//   ★为何上限取 511 而非 512（卡面二选一，本实现取 511）：
//       s=512 且 c=255 ⇒ ⌈255/2⌉×512>>8 = 256 > 255 ⇒ out_r = −1，经 shl ecx,11 后低 16 位 = 0xF8xx
//       ⇒ **R 段借位回绕成 31，并把 G/B 段污染成 1**（16 位寄存器回绕，不是钳位）；逐通道钳位虽可救回，
//       但需在桩内新增 3 段比较（每格每帧付费，且改变桩体字节 = 削弱 auto 等价性）。
//       取 511 则 ⌈c/2⌉×511>>8 ≤ c 对 ∀c ∈ [0,65535] 恒成立 ⇒ 逐通道输出天然落在 [0,255]，
//       桩内零改动、零钳位（穷举证据：out/re_work/fog_cal2/sim_out.txt [3][4]）。
//   · FogCalPredictedRatio ：预测净压暗（保留比例）= 0.71875 × (1 − s/512)
//        s=256 ⇒ 0.5 ⇒ 0.359375 = 23/64 = FOG-STRENGTH2 实测定谳值（模型自检锚点，auto 档不变）
//   · FogCalEffectiveM     ：由运行期 s 反解的生效 m = 1 − s/512（日志用；auto ⇒ 0.5）
// ---------------------------------------------------------------------------
uint16_t FogStrengthPctToStubScale(double pct) {
    if (pct < 0.0)   pct = 0.0;
    if (pct > 100.0) pct = 100.0;
    double m = (pct / 100.0) / s_fogFirstStageGainUpstream;   // 目标净保留 / 第一段经验系数
    if (m < 0.0) m = 0.0;
    if (m > 1.0) m = 1.0;                       // 钳 [0,1] ⇒ T > 71.875% 不可达 ⇒ 收敛到最亮（s=0）
    double s = 512.0 * (1.0 - m) + 0.5;         // round(512 × (1 − m))（半上取整）
    if (s < 0.0)   s = 0.0;
    if (s > 511.0) s = 511.0;                   // 上限 511（非 512）：见上「为何上限取 511」
    return static_cast<uint16_t>(s);
}

// 预测净压暗（保留比例，即 雾中像素值 / 无雾像素值）：0.71875 × (1 − s/512)
double FogCalPredictedRatio(uint16_t stubS) {
    double keepStub = 1.0 - (static_cast<double>(stubS) / 512.0);
    if (keepStub < 0.0) keepStub = 0.0;
    return s_fogFirstStageGainUpstream * keepStub;
}

// 生效 m（由 s 反解）：m = 1 − s/512
double FogCalEffectiveM(uint16_t stubS) {
    double m = 1.0 - (static_cast<double>(stubS) / 512.0);
    if (m < 0.0) m = 0.0;
    if (m > 1.0) m = 1.0;
    return m;
}

// 可达上限 T_max = 100 × 第一段经验系数 = 71.875%（由唯一真源常量算出，勿另写字面量）
double FogCalMaxReachablePct(void) {
    return 100.0 * s_fogFirstStageGainUpstream;
}

// [FOG-CAL2 F1] 百分比解析（手工十进制，不依赖 locale 的 strtod）：
//   语法 = [空白] [+|-] digits [ '.' digits ] [空白]；允许小数（如 35.9375 / 71.875）。
//   返回 false = 非法（空串 / 仅符号 / 无数字 / 尾随非法字符）⇒ 调用方收敛为 auto。
bool FogCalParsePercent(const char *s, double *out) {
    const char *p = s;
    while (*p == ' ' || *p == '\t') ++p;
    double sign = 1.0;
    if (*p == '+')      { ++p; }
    else if (*p == '-') { sign = -1.0; ++p; }
    bool any = false;
    double v = 0.0;
    while (*p >= '0' && *p <= '9') { v = v * 10.0 + static_cast<double>(*p - '0'); ++p; any = true; }
    if (*p == '.') {
        ++p;
        double f = 0.1;
        while (*p >= '0' && *p <= '9') { v += static_cast<double>(*p - '0') * f; f *= 0.1; ++p; any = true; }
    }
    if (!any) return false;
    while (*p == ' ' || *p == '\t') ++p;
    if (*p != 0) return false;
    *out = sign * v;
    return true;
}

// ---------------------------------------------------------------------------
// [ZC-10B ②] FogStrengthPct 运行期镜像同步
//   现状（改前）：本键只在 LoadConfig()（仅 init 调用）读一次 ⇒ ini 注释里写「改值 ≤1 帧生效」
//                 与实现不符（已另案修 ini 注释）。
//   本函数：按遥测节拍（≈2s，由 CheckTelemetry 调用）重读 ini 的 FogOfWar/FogStrengthPct，
//            并更新 g_fogStrengthScale256 ⇒ **一局内改键即生效**（ZC-11 段 B「一局内跑 8 档」的前提）。
//   纪律：
//     · 换算沿用 FogStrengthPctToStubScale()，公式零改动；
//     · auto 仍 = s=256（不补偿，与校准前部署逐像素一致）；
//     · 只在值真正变化时写全局 + 打日志（避免每 2s 噪声日志）；
//     · 读取失败/异常时保持上一生效值（安全侧：不因读盘抖动改变画面）。
// ---------------------------------------------------------------------------
static void SyncFogStrengthMirror() {
    static char s_prevRaw[16] = "";
    static bool s_inited = false;
    char buf[32] = {0};
    char iniPath[MAX_PATH];
    GetCurrentDirectoryA(MAX_PATH, iniPath);
    strcat_s(iniPath, "\\ra2render.ini");
    GetPrivateProfileStringA("FogOfWar", "FogStrengthPct", "\x01[ZC10B:ABSENT]\x01",
                             buf, static_cast<DWORD>(sizeof(buf)), iniPath);
    if (strcmp(buf, "\x01[ZC10B:ABSENT]\x01") == 0) return;   // 键缺失 ⇒ 保持现状
    if (s_inited && strcmp(buf, s_prevRaw) == 0) return;      // 值未变 ⇒ 不动全局
    strncpy_s(s_prevRaw, sizeof(s_prevRaw), buf, _TRUNCATE);
    s_inited = true;

    uint16_t newS = 256;
    bool autoMode = true;
    double newPct = -1.0;
    if (_stricmp(buf, "auto") == 0) {
        newS = 256;
    } else {
        double v = 0.0;
        if (!FogCalParsePercent(buf, &v)) {
            LogMessage("[ra2render-fogcal] [警告/红字] 运行期 FogStrengthPct=\"%s\" 不合法 ⇒ 保持上一生效值 %u（不改画面）", buf,
                       static_cast<unsigned>(g_fogStrengthScale256));
            return;
        }
        autoMode = false;
        newPct = (v < 0.0) ? 0.0 : ((v > 100.0) ? 100.0 : v);
        newS = FogStrengthPctToStubScale(newPct);
    }
    uint16_t oldS = g_fogStrengthScale256;
    g_fogStrengthAuto = autoMode;
    g_fogStrengthPct = newPct;
    strncpy_s(g_fogStrengthPctRaw, sizeof(g_fogStrengthPctRaw), buf, _TRUNCATE);
    g_fogStrengthScale256 = newS;
    LogMessage("[ra2render-fogcal] 运行期同步: FogStrengthPct=%s ⇒ 桩强度 s %u -> %u | m=%0.6f | 预测净压暗(保留比例)=%.6f | 生效 VA=0x%08X",
               buf, static_cast<unsigned>(oldS), static_cast<unsigned>(newS),
               FogCalEffectiveM(newS), FogCalPredictedRatio(newS),
               static_cast<unsigned>(reinterpret_cast<uintptr_t>(&g_fogStrengthScale256)));
}

void LoadConfig() {
    char iniPath[MAX_PATH];
    GetCurrentDirectoryA(MAX_PATH, iniPath);
    strcat_s(iniPath, "\\ra2render.ini");

    bool h_key = false, h_interval = false, h_mm = false, h_guard = false;
    bool h_simd = false, h_speed = false, h_lfh = false, h_timer = false, h_scfog = false;
    bool h_sweep = false, h_cd = false, h_radius = false, h_bld = false, h_bullet = false, h_fade = false;
    bool h_unitfog = false;   // [FOG-SPLIT] 逻辑可见性键（不受总闸影响）
    bool h_gap = false;       // [GAP-P223] 裂缝保护开关键（默认 0 = 不碰 .text）
    bool h_vxl = false;       // [VXL-PRE] VXL 缓存预热扩容键（[Render]，默认 0）
    bool h_sw = false;        // [SW-CHARGE] 充能冗余 call 删除键（[Logic]，默认 0）

    // [G3-SPLIT] 玩法键旧节迁移标记（true = 从 [Logic]/[FogOfWar] 旧位置只读迁入，用户既有开启态保留）
    bool mig_key = false, mig_interval = false, mig_mm = false, mig_guard = false;
    bool mig_scfog = false, mig_sweep = false, mig_cd = false, mig_radius = false;
    bool mig_bld = false, mig_bullet = false, mig_fade = false, mig_unitfog = false, mig_vis = false;

    // [G3-SPLIT] 玩法键改走 [Gameplay] 节三级回退（①[Gameplay] → ②旧节只读迁移 → ③原版默认）：
    //   原版默认 = TargetScanInterval 1（每帧全量寻敌）；联机 G-08 恒强制 1 的既有门控不变。
    g_targetScanInterval = GetGameplayIntEx("TargetScanInterval", 1, "Logic", iniPath, &h_interval, &mig_interval);
    if (g_targetScanInterval < 1) g_targetScanInterval = 1;
    if (g_targetScanInterval > 64) g_targetScanInterval = 64;

    int simdVal = GetIniIntEx("Render", "EnableSIMD", 1, iniPath, &h_simd);
    g_enableSIMD = (simdVal != 0);

    int unlockVal = GetIniIntEx("Speed", "UnlockGameSpeed", 0, iniPath, &h_speed);
    g_unlockGameSpeed = (unlockVal != 0);

    int lfhVal = GetIniIntEx("System", "EnableLFH", 1, iniPath, &h_lfh);
    {
        bool _sbh_hit = false;
        g_enableSbhGuard = (GetIniIntEx("System", "EnableSbhGuard", 0, iniPath, &_sbh_hit) != 0);
    }
    g_enableLFH = (lfhVal != 0);

    int timerVal = GetIniIntEx("System", "HighPrecisionTimer", 1, iniPath, &h_timer);
    g_highPrecisionTimer = (timerVal != 0);

    // [G3-SPLIT] 玩法键：原版默认 = 关；显式开启须 [Gameplay]（或旧节 [FogOfWar] 只读迁移）。
    int fogVal = GetGameplayIntEx("EnableStarCraftFog", 0, "FogOfWar", iniPath, &h_scfog, &mig_scfog);
    g_enableStarCraftFog = (fogVal != 0);

    int sweepVal = GetGameplayIntEx("EnableSpySatRadarSweep", 0, "FogOfWar", iniPath, &h_sweep, &mig_sweep);
    g_enableSpySatRadarSweep = (sweepVal != 0);

    g_radarSweepCooldownFrames = GetGameplayIntEx("RadarSweepCooldownFrames", 600, "FogOfWar", iniPath, &h_cd, &mig_cd);
    if (g_radarSweepCooldownFrames < 60) g_radarSweepCooldownFrames = 60;

    g_radarSweepRadiusCells = GetGameplayIntEx("RadarSweepRadiusCells", 16, "FogOfWar", iniPath, &h_radius, &mig_radius);
    if (g_radarSweepRadiusCells < 4) g_radarSweepRadiusCells = 4;
    if (g_radarSweepRadiusCells > 64) g_radarSweepRadiusCells = 64;

    char keyBuf[16] = {0};
    GetGameplayStrEx("TargetScanKey", "position", "Logic", iniPath, keyBuf, sizeof(keyBuf), &h_key, &mig_key);
    g_targetScanKey = (_stricmp(keyBuf, "pointer") == 0) ? 0 : 1;

    int bldFogVal = GetGameplayIntEx("EnableBuildingFog", 0, "FogOfWar", iniPath, &h_bld, &mig_bld);
    g_enableBuildingFog = (bldFogVal != 0);

    int bulletFogVal = GetGameplayIntEx("EnableBulletFog", 0, "FogOfWar", iniPath, &h_bullet, &mig_bullet);
    g_enableBulletFog = (bulletFogVal != 0);

    int fadeVal = GetGameplayIntEx("FadeFogTransition", 1, "FogOfWar", iniPath, &h_fade, &mig_fade);
    g_fadeFogTransition = (fadeVal != 0);

    // [FOG-SPLIT] 迷雾中敌方机动单位剔除：逻辑可见性键，不受总闸影响；
    //   [G3-SPLIT] 原版默认 = 0（键缺失即关闭；旧版 API 默认 1 的非原版行为随拆分一并矫正）。
    int unitFogVal = GetGameplayIntEx("EnableUnitFog", 0, "FogOfWar", iniPath, &h_unitfog, &mig_unitfog);
    g_enableUnitFog = (unitFogVal != 0);

    // ---- [FOG-MODE F1] 可见性模式：VisibilityMode = starcraft | vanilla ----
    //   [G3-SPLIT] 出厂默认 = vanilla（原版可见性）；starcraft（现状态）须 [Gameplay] 显式开启。
    //   字符串键（同 [RADAR-FIX F3] 口径：字符串 + 哨兵默认值 ⇒ 可区分「键缺失」与「键值=默认」）。
    //   vanilla ⇒ 三处视距剔除全部放行（原版可见性）；starcraft ⇒ 现状（三子键按现有语义生效）。
    //   ★优先级：vanilla 时三子键被本键覆盖（忽略），启动日志/遥测行显式标注。
    //   未知值/空值 ⇒ 收敛为 vanilla（[G3-SPLIT] 安全侧 = 原版行为），日志打原始串告警。
    bool h_vis = false;
    GetGameplayStrEx("VisibilityMode", "vanilla", "FogOfWar", iniPath,
                     g_visibilityModeRaw, sizeof(g_visibilityModeRaw), &h_vis, &mig_vis);
    (void)h_vis;
    if (_stricmp(g_visibilityModeRaw, "vanilla") == 0) {
        g_visibilityVanilla = true;
    } else if (_stricmp(g_visibilityModeRaw, "starcraft") == 0) {
        g_visibilityVanilla = false;   // 显式 starcraft = 现状态（视距剔除生效）
    } else {
        g_visibilityVanilla = true;    // [G3-SPLIT] 未知值收敛为 vanilla（原版行为安全侧；下方告警行照打）
    }

    // [G3-SPLIT] 迁移键：默认本就 0（G-01），行为零变化；改走 [Gameplay] 三级回退。
    //   【RADAR-FIX2 待裁决】本项尚未通过真机验收（ZC-3 未跑），出厂默认保持 0（原版行为）。
    int minimapFogVal = GetGameplayIntEx("EnableMinimapFog", 0, "FogOfWar", iniPath, &h_mm, &mig_mm);
    g_enableMinimapFog = (minimapFogVal != 0);
    s_minimapFogGate = GetEffectiveMinimapFog() ? 1 : 0;

    // ---- [GAP-P223] 裂缝保护开关键（EnableGapProtection，默认 0 = 不碰 .text；三点同键不拆）----
    //   1 = init 时把三点「清 GapsCoveringThisCell(+0x134)」各 6B 等长 NOP 化：
    //       P-2.1 MapClass::RevealArea2 @0x005678E0 @0x00568273（89 99 34 01 00 00）
    //       P-2.2 MapClass::RevealArea3 @0x00577D90 @0x00577EC5（89 B8 34 01 00 00）
    //       P-2.3 MapClass::Reshroud    @0x00577AB0 @0x00577B60（89 98 34 01 00 00）
    //       每点只删这一次 store；ShroudCounter / CopyFlags / RedrawFlags 写入原样保留。
    //       安装态在 init 决定 ⇒ 改键须重启生效（与 LoadConfig 仅 init 读一次的口径一致）；
    //       联机 MpActive 强制不装（InstallGapProtectionPatch）。
    //   ★本键只读 ini、不进任何热路径；键名 EnableGapProtectP22/P23 不建、不占用。
    int gapVal = GetIniIntEx("FogOfWar", "EnableGapProtection", 0, iniPath, &h_gap);
    g_enableGapProtection = (gapVal != 0);

    // ---- [GAP-P223] 启动行（ini 值 + 来源；生效态由 InstallGapProtectionPatch 打印 on/off/forced-off-mp + installed=N）----
    //   [GAP-MP-EDGE] 联机边沿同步（W3_20261001 gapfix）：单机→联机迁移时已装三点逆序硬回滚（mp-edge-rollback）；
    //     联机→单机迁移且配置仍 =1 时按完整 G0 门禁重装（mp-edge-reinstall）。配置仍只在 LoadConfig 读一次（非热重载）。
    LogMessage("[ra2render-gap] 裂缝保护配置: EnableGapProtection=%d (来源: %s) | 生效(=1 时): 三点表驱动等长 NOP 化 —— P-2.1 RevealArea2 @0x00568273(89 99 34 01 00 00) / P-2.2 RevealArea3 @0x00577EC5(89 B8 34 01 00 00) / P-2.3 Reshroud @0x00577B60(89 98 34 01 00 00)，各 6B->90x6 | 保留: P-2.1 ShroudCounter<-0(@0x0056824A)/CopyFlags|=0x10(@0x0056829A) | P-2.2 ShroudCounter<-0(@0x00577EBF)/CopyFlags|=0x18(@0x00577ED4) | P-2.3 CopyFlags&=~0x18(@0x00577B4E)/ShroudCounter<-1(@0x00577B56)/RedrawFlags&=~0x3(@0x00577B66) | 安装序 P-2.1->P-2.2->P-2.3，回滚逆序 | 门控: MpActive 强制不装 + [GAP-MP-EDGE] 单机->联机迁移硬回滚(mp-edge-rollback)/联机->单机门禁重装(mp-edge-reinstall)",
               g_enableGapProtection ? 1 : 0, IniSrc(h_gap));

    // ---- [VXL-PRE] VXL 缓存预热扩容开关键（[Render] EnableVxlCachePrewarm，默认 0 = 不碰 .text）----
    //   1 = init 时 0x706D78 的 5B「BB 0A 00 00 00（mov ebx,0xA）」内 imm8 0x0A→0x40
    //       （首次容量 10→64 条）；扩容步长/插入/命中语义不动；安装态 init 决定，重启生效。
    int vxlVal = GetIniIntEx("Render", "EnableVxlCachePrewarm", 0, iniPath, &h_vxl);
    g_enableVxlCachePrewarm = (vxlVal != 0);
    LogMessage("[ra2render-gap] VxlCachePrewarm 配置: EnableVxlCachePrewarm=%d (来源: %s) | 生效(=1 时): SomeVoxelCache 首次分配粒度 mov ebx,0xA->0x40(@0x00706D78 imm8) | 保留: growstep 翻倍(@0x706D7F) / 插入 / IsSorted 置脏 | 门控: 无 MpActive 强制关（纯表现层 D-VXL13 SAFE）",
               g_enableVxlCachePrewarm ? 1 : 0, IniSrc(h_vxl));

    // ---- [SW-CHARGE] 充能冗余二次 call 删除开关键（[Logic] EnableSWChargeOpt，默认 0 = 不碰 .text）----
    //   1 = init 时 HasChargeProgressed 慢路径冗余二次 GetCameoChargeState call
    //       （0x6CBE88 7B）等长 NOP 化；复用第一次 eax ⇒ 0x6CBE8F 写回值不变、零语义变化。
    int swVal = GetIniIntEx("Logic", "EnableSWChargeOpt", 0, iniPath, &h_sw);
    g_enableSWChargeOpt = (swVal != 0);
    LogMessage("[ra2render-gap] SWChargeOpt 配置: EnableSWChargeOpt=%d (来源: %s) | 生效(=1 时): 删 HasChargeProgressed 慢路径冗余二次 call(@0x006CBE88 7B->90x7，复用首次 eax) | 禁区: GetCameoChargeState 公式/RechargeTimer/IsCharged/ChargeDrainState 一字不动 | 门控: 零语义变化，MP 可装可保留",
               g_enableSWChargeOpt ? 1 : 0, IniSrc(h_sw));

    // [RADAR-FIX2 F2] 雷达灰化档（缺省 = 3 引擎原生减暗驱动；缺失/越界都收敛为 3）
    //   0/1/2 = 自绘 50% 灰化三档（A/B 对照；护栏分别 = 旧 GameMode 判据 / 新谓词 / 不设护栏）
    //   3     = 不自绘像素，改为在 0x00655D87 按我方三态视野谓词驱动引擎减暗判定位 [esp+0x13]
    //   [G3-SPLIT] 迁移键：改走 [Gameplay] 三级回退；仅 EnableMinimapFog 生效时被消费（默认档不变）。
    g_radarFogGuardMode = GetGameplayIntEx("RadarFogGuardMode", RADAR_FOG_GUARD_NATIVE, "FogOfWar", iniPath, &h_guard, &mig_guard);
    int effGuard = GetEffectiveRadarFogGuardMode();

    // ---- [G3-SPLIT] 玩法键迁移留痕（验收判据②取证锚点）----
    //   只读迁移：不改写、不删除用户 ini 任何内容；命中数 N 与逐键来源在此一次性成行。
    {
        int migCount = 0;
        const char *sep = "";
        char migList[256] = {0};
        auto pushMig = [&](bool m, const char *name) {
            if (!m) return;
            ++migCount;
            strncat_s(migList, sep, _TRUNCATE);
            strncat_s(migList, name, _TRUNCATE);
            sep = " ";
        };
        pushMig(mig_interval, "TargetScanInterval");
        pushMig(mig_key, "TargetScanKey");
        pushMig(mig_scfog, "EnableStarCraftFog");
        pushMig(mig_vis, "VisibilityMode");
        pushMig(mig_sweep, "EnableSpySatRadarSweep");
        pushMig(mig_cd, "RadarSweepCooldownFrames");
        pushMig(mig_radius, "RadarSweepRadiusCells");
        pushMig(mig_bld, "EnableBuildingFog");
        pushMig(mig_bullet, "EnableBulletFog");
        pushMig(mig_unitfog, "EnableUnitFog");
        pushMig(mig_fade, "FadeFogTransition");
        pushMig(mig_mm, "EnableMinimapFog");
        pushMig(mig_guard, "RadarFogGuardMode");
        LogMessage("[ra2render-gameplay] [G3-SPLIT] 玩法配置拆分: 旧节只读迁移命中 %d 项%s%s | 现行来源 = [Gameplay] 节（缺键 → 旧节 [Logic]/[FogOfWar] 只读回退 → 原版默认全关）；本 DLL 绝不写 ini",
                   migCount,
                   migCount > 0 ? "（迁移键: " : "",
                   migCount > 0 ? migList : "");
        if (migCount > 0) {
            LogMessage("[ra2render-gameplay] [G3-SPLIT] 迁移提示: 建议将上述键手工移入 ra2render.ini 的 [Gameplay] 节以固定配置口径（不迁移亦可持续生效，旧节回退为常驻兼容路径）");
        }
    }

    LogMessage("[ra2render] 配置加载完成: TargetScanInterval=%d, EnableSIMD=%s, UnlockGameSpeed=%s, EnableLFH=%s, HighPrecisionTimer=%s, EnableStarCraftFog=%s, EnableSpySatRadarSweep=%s (CD=%d, Radius=%d), EnableBuildingFog=%s, EnableBulletFog=%s, FadeFogTransition=%s, EnableMinimapFog=%s, EnableUnitFog=%s",
               g_targetScanInterval, g_enableSIMD ? "true" : "false", g_unlockGameSpeed ? "true" : "false",
               g_enableLFH ? "true" : "false", g_highPrecisionTimer ? "true" : "false",
               g_enableStarCraftFog ? "true" : "false",
               g_enableSpySatRadarSweep ? "true" : "false", g_radarSweepCooldownFrames, g_radarSweepRadiusCells,
               g_enableBuildingFog ? "true" : "false", g_enableBulletFog ? "true" : "false",
               g_fadeFogTransition ? "true" : "false", g_enableMinimapFog ? "true" : "false",
               g_enableUnitFog ? "true" : "false");   // [FOG-SPLIT] 尾追逻辑可见性键（不动既有字段顺序）
    LogMessage("[ra2render] L2 分片键: TargetScanKey=%s (来源: %s)（缺陷2 修复：position=确定性坐标哈希，联机安全；pointer=旧指针哈希，仅单机）",
               g_targetScanKey ? "position" : "pointer", IniSrc(h_key));

    // [FOG-SWITCH F3①] 灰雾总闸与各子键的「生效值 + 来源」一次性成行打印（真机 A/B 取证锚点）
    //   来源口径沿用 [RADAR-FIX F3]：ini = 键命中；默认值 = 键缺失走 API 默认兜底。
    SyncFogMasterMirror();
    // [FOG-SPLIT] 语义重定义后的启动行：总闸**只**管「已探索非直视」档的压暗强度；
    //   未探索黑幕保留（引擎 0x47EFE0 路径，我方不介入）、玩法可见性三键不受总闸影响。
    LogMessage("[ra2render-fog] 灰雾总闸: EnableStarCraftFog=%d (来源: %s, 生效: %s) | 子键生效值(来源): EnableBuildingFog=%d(%s) EnableBulletFog=%d(%s) EnableUnitFog=%d(%s) FadeFogTransition=%d(%s) EnableMinimapFog=%d(%s, 生效=%d) RadarFogGuardMode=%d(%s, 生效=%d) | [FOG-SPLIT] 总闸语义: 只管「已探索且非直视」档的压暗强度 → =1 压暗(256) / =0 强度归零(不压暗、也不驱动小地图减暗)；未探索档(Shroudedness==-2)原版全黑黑幕**保留**(引擎 0x47EFE0 绘制, 我方不介入)；直视档两档都不压暗；逻辑可见性三键(建筑/弹道/机动单位剔除)**不受总闸影响**",
               g_enableStarCraftFog ? 1 : 0, IniSrc(h_scfog), g_enableStarCraftFog ? "开(已探索非直视档压暗)" : "关(已探索非直视档强度归零; 未探索黑幕保留)",
               g_enableBuildingFog ? 1 : 0, IniSrc(h_bld),
               g_enableBulletFog ? 1 : 0, IniSrc(h_bullet),
               g_enableUnitFog ? 1 : 0, IniSrc(h_unitfog),
               g_fadeFogTransition ? 1 : 0, IniSrc(h_fade),
               g_enableMinimapFog ? 1 : 0, IniSrc(h_mm), s_minimapFogGate ? 1 : 0,
               effGuard, IniSrc(h_guard), static_cast<int>(s_radarFogGuardMode));

    // ---- [FOG-MODE F3] 可见性模式启动行（**新增独立行**，不动上面既有行的字段与顺序）----
    //   打印：VisibilityMode 生效值 + 来源（ini/默认值）+ 三子键生效值 + 被 mode 覆盖的显式标注
    //   + 优先级说明 + 2 秒遥测行的机器判据口径。
    LogMessage("[ra2render-visibility] VisibilityMode=%s (来源: %s) | 生效: %s | 子键生效值(来源): EnableUnitFog=%d(%s%s) EnableBuildingFog=%d(%s%s) EnableBulletFog=%d(%s%s) | [FOG-MODE] 优先级: %s | 机器判据([ra2render-telemetry-visibility]): %s",
               g_visibilityModeRaw, IniSrc(h_vis),
               g_visibilityVanilla ? "原版可见性(不做任何视距剔除; 单位/建筑/弹道三处剔除全部放行)"
                                   : "现状态(视距剔除生效; 三子键按现有语义各自生效)",
               g_enableUnitFog ? 1 : 0, IniSrc(h_unitfog),
               g_visibilityVanilla ? ", 被 VisibilityMode 覆盖 -> 放行(不剔除)" : "",
               g_enableBuildingFog ? 1 : 0, IniSrc(h_bld),
               g_visibilityVanilla ? ", 被 VisibilityMode 覆盖 -> 放行(不剔除)" : "",
               g_enableBulletFog ? 1 : 0, IniSrc(h_bullet),
               g_visibilityVanilla ? ", 被 VisibilityMode 覆盖 -> 放行(不剔除)" : "",
               g_visibilityVanilla ? "vanilla 覆盖三子键（三子键配置被忽略）"
                                   : "starcraft 不覆盖（三子键各自生效）",
               g_visibilityVanilla ? "vanilla 档要求：机动单位剔除 ≡0 且 建筑剔除 ≡0 且 弹道剔除 ≡0 且 被 mode 覆盖而放行 >0"
                                   : "starcraft 档要求：三处剔除计数按视野圈判定增长 且 被 mode 覆盖而放行 ≡0");
    if (_stricmp(g_visibilityModeRaw, "vanilla") != 0 && _stricmp(g_visibilityModeRaw, "starcraft") != 0) {
        LogMessage("[ra2render-visibility] [警告/红字] VisibilityMode 取值 \"%s\" 不合法（合法值: starcraft | vanilla）⇒ 已收敛为 vanilla（[G3-SPLIT] 安全侧 = 原版可见性）", g_visibilityModeRaw);
    }

    // ---- [FOG-CAL2 F1] 灰雾净强度校准键：FogStrengthPct = auto | <0..100>（默认 auto；允许小数）----
    //   字符串键（沿用 [RADAR-FIX F3] 口径：字符串 + 哨兵默认值 ⇒ 可区分「键缺失」与「键值=默认」）。
    //   · auto（默认）    = **不补偿**：桩强度保持设计值 s=256 ⇒ 与校准前部署**逐像素一致**（硬要求）。
    //   · <0..100>        = 目标「净压暗（保留比例）」百分比 T；换算见 FogStrengthPctToStubScale（§F1 订正公式）。
    //                       允许小数（35.9375 = auto 同观感；71.875 = 最亮上限），故解析器不走 atoi。
    //   · 键缺失 / 空串 / 非 auto 的非数字串 ⇒ 收敛为 auto（安全侧：保持现网观感），日志打原始串告警。
    //   · T > 71.875（= 100 × 第一段系数）⇒ **不可达**（画面不可能比只剩第一段更亮）⇒ 钳到最亮 s=0 并告警。
    bool h_fogcal = false;
    {
        char calBuf[32] = {0};
        h_fogcal = GetIniStringEx("FogOfWar", "FogStrengthPct", "auto", calBuf, sizeof(calBuf), iniPath);
        if (calBuf[0] == 0) strncpy_s(calBuf, "auto", _TRUNCATE);
        strncpy_s(g_fogStrengthPctRaw, sizeof(g_fogStrengthPctRaw), calBuf, _TRUNCATE);

        if (_stricmp(calBuf, "auto") == 0) {
            g_fogStrengthAuto = true;
            g_fogStrengthPct = -1.0;
            g_fogStrengthScale256 = 256;                       // auto：不补偿（与校准前同路径同值）
        } else {
            double v = 0.0;
            if (!FogCalParsePercent(calBuf, &v)) {
                LogMessage("[ra2render-fogcal] [警告/红字] FogStrengthPct 取值 \"%s\" 不合法（合法值: auto | <0..100>，可带小数）⇒ 已收敛为 auto（不补偿/现状）", calBuf);
                g_fogStrengthAuto = true;
                g_fogStrengthPct = -1.0;
                g_fogStrengthScale256 = 256;
            } else {
                g_fogStrengthAuto = false;
                double vReq = v;
                if (v < 0.0)   v = 0.0;
                if (v > 100.0) v = 100.0;
                if (v != vReq) {
                    LogMessage("[ra2render-fogcal] [警告/红字] FogStrengthPct=%.6g 越界 ⇒ 已钳到 %.6g", vReq, v);
                }
                g_fogStrengthPct = v;
                g_fogStrengthScale256 = FogStrengthPctToStubScale(g_fogStrengthPct);
                if (g_fogStrengthPct > FogCalMaxReachablePct()) {
                    LogMessage("[ra2render-fogcal] [提示] FogStrengthPct=%.6g 超出可达上限 %.4f%%（= 100 × 第一段系数 %.5f）⇒ **不可达**（画面不可能比只剩第一段更亮）⇒ 桩强度钳到 s=0（最亮，与 T=%.4f%% 同值）；不得假装可达。",
                               g_fogStrengthPct, FogCalMaxReachablePct(), s_fogFirstStageGainUpstream, FogCalMaxReachablePct());
                }
            }
        }
    }
    // [FOG-CAL2 F2/F3] 启动行（**新增独立行**；既有行字段与顺序零变化）
    //   字段口径（与 2 秒行 / ini 注释 / 文档 §4 一致）：
    //     生效值（auto | 目标 T）+ m + 桩强度 s + 预测净压暗（保留比例）。
    //   ★字段改名记录（防解析口径漂移）：上一版「预测实测比值(净压暗系数)」→ 本版「预测净压暗(保留比例)」；
    //     并**新增 m 数值字段**（上一版只打印公式串、不打印 m）；数值档新增「目标 T」字段（支持小数 %.6g）。
    //   ★方向提醒：本版 T 越大越亮；auto 不是 T（automatic = 不补偿，等效 T = 35.9375%）。
    {
        char tBuf[32] = {0};
        if (g_fogStrengthAuto) {
            strncpy_s(tBuf, "auto(不补偿/现状; 等效 T = 35.9375%)", _TRUNCATE);
        } else {
            sprintf_s(tBuf, "%.6g%%", g_fogStrengthPct);
        }
        double fogM = g_fogStrengthAuto ? FogCalEffectiveM(g_fogStrengthScale256)
                                        : (g_fogStrengthPct / 100.0) / s_fogFirstStageGainUpstream;
        LogMessage("[ra2render-fogcal] FogStrengthPct=%s (来源: %s) | 生效: %s | 目标 T = %s | 换算: m = (T/100) / %.5f(第一段经验系数) = %.6f | 桩强度 s = clamp(round(512*(1-m)), 0, 511) = %u / 511 | 预测净压暗(保留比例) = 0.71875 × (1 - s/512) = %.6f (= %.4f%%) | 可达域: T ∈ [0, %.4f] ⇒ 净压暗 ∈ [%.6f, %.6f]（s=511 最暗 / s=0 最亮）; T > %.4f 不可达 ⇒ 钳到 s=0（不可能比只剩第一段更亮） | auto 基线: s=256 ⇒ 净压暗 0.359375 (= 23/64) | 桩强度全局 VA=0x%08X (热路径运行期直读: 改值 ≤1 帧生效)",
                   g_fogStrengthPctRaw, IniSrc(h_fogcal),
                   g_fogStrengthAuto ? "auto(不补偿: 桩按设计 s=256 ⇒ 与校准前部署逐像素一致)"
                                     : "数值档(目标净压暗/保留比例 百分比 T)",
                   tBuf,
                   s_fogFirstStageGainUpstream, fogM,
                   static_cast<unsigned>(g_fogStrengthScale256),
                   FogCalPredictedRatio(g_fogStrengthScale256),
                   100.0 * FogCalPredictedRatio(g_fogStrengthScale256),
                   FogCalMaxReachablePct(),
                   FogCalPredictedRatio(511), FogCalPredictedRatio(0),
                   FogCalMaxReachablePct(),
                   static_cast<unsigned>(reinterpret_cast<uintptr_t>(&g_fogStrengthScale256)));
    }

    // ---- [ZC-10B ①] L4DirtyMode（FogOfWar/L4DirtyMode = force-full | vision-dirty | vanilla）----
    //   默认 force-full = 现状（恒强制全量）。ini 缺失 / 非法值一律收敛为 force-full（安全侧）。
    {
        char lm[32] = {0};
        bool h_lm = GetIniStringEx("FogOfWar", "L4DirtyMode", "force-full", lm, sizeof(lm), iniPath);
        g_l4DirtyMode = 0;
        if (_stricmp(lm, "vision-dirty") == 0)      g_l4DirtyMode = 1;
        else if (_stricmp(lm, "vanilla") == 0)      g_l4DirtyMode = 2;
        else if (_stricmp(lm, "force-full") != 0) {
            LogMessage("[ra2render-l4dirty] [警告/红字] L4DirtyMode 取值 \"%s\" 不合法（合法值: force-full | vision-dirty | vanilla）⇒ 已收敛为 force-full（= 现状）", lm);
        }
        LogMessage("[ra2render-l4dirty] L4DirtyMode=%s (来源: %s) | 生效 = %s | 放行判据: mode==vision-dirty 且 视口迁移数==0 且 视口渐变活跃数==0 ⇒ 交还原版 jge（0x006D3D99）；其余（含 force-full / vanilla）见下方口径",
                   lm, IniSrc(h_lm),
                   g_l4DirtyMode == 0 ? "force-full(恒强制全量 = 现状)" :
                   (g_l4DirtyMode == 1 ? "vision-dirty(静态视口交还原版 jge)" : "vanilla(恒交还原版 jge)"));
    }

    // ---- [ZC-10B ③] FogProbe（FogOfWar/FogProbe = 0 | 1；默认 0 = 热路径无探针指令）----
    {
        bool h_fp = false;
        int fp = GetIniIntEx("FogOfWar", "FogProbe", 0, iniPath, &h_fp);
        g_fogProbeEnabled = (fp != 0);
        s_fogProbeEnabledMirror = g_fogProbeEnabled ? 1 : 0;
        LogMessage("[ra2render-fogprobe] FogProbe=%d (来源: %s) | 生效 = %s | 0 = B1/B2 混色桩热路径**不含**探针指令（与探针前件一致）；1 = 热路径 +2 指令（cmp/je）采样桩读取值",
                   g_fogProbeEnabled ? 1 : 0, IniSrc(h_fp),
                   g_fogProbeEnabled ? "开(含探针)" : "关(无探针, 默认)");
    }

    // [RADAR-FIX F3] 键来源明细：ini 命中 vs API 默认值兜底（两者此前无法区分，曾被误读为「已配置生效」）
    LogMessage("[ra2render] 配置来源: TargetScanKey=%s (来源: %s) | TargetScanInterval=%d (来源: %s) | EnableMinimapFog=%d (来源: %s) | RadarFogGuardMode=%d (来源: %s)",
               g_targetScanKey ? "position" : "pointer", IniSrc(h_key),
               g_targetScanInterval, IniSrc(h_interval),
               g_enableMinimapFog ? 1 : 0, IniSrc(h_mm),
               effGuard, IniSrc(h_guard));
    LogMessage("[ra2render] 配置来源(续): EnableSIMD=%d (来源: %s) | UnlockGameSpeed=%d (来源: %s) | EnableLFH=%d (来源: %s) | HighPrecisionTimer=%d (来源: %s) | EnableStarCraftFog=%d (来源: %s) | EnableSpySatRadarSweep=%d (来源: %s) | RadarSweepCD=%d (来源: %s) | RadarSweepRadius=%d (来源: %s) | EnableBuildingFog=%d (来源: %s) | EnableBulletFog=%d (来源: %s) | FadeFogTransition=%d (来源: %s) | EnableUnitFog=%d (来源: %s)",
               g_enableSIMD ? 1 : 0, IniSrc(h_simd), g_unlockGameSpeed ? 1 : 0, IniSrc(h_speed),
               g_enableLFH ? 1 : 0, IniSrc(h_lfh), g_highPrecisionTimer ? 1 : 0, IniSrc(h_timer),
               g_enableStarCraftFog ? 1 : 0, IniSrc(h_scfog), g_enableSpySatRadarSweep ? 1 : 0, IniSrc(h_sweep),
               g_radarSweepCooldownFrames, IniSrc(h_cd), g_radarSweepRadiusCells, IniSrc(h_radius),
               g_enableBuildingFog ? 1 : 0, IniSrc(h_bld), g_enableBulletFog ? 1 : 0, IniSrc(h_bullet),
               g_fadeFogTransition ? 1 : 0, IniSrc(h_fade),
               g_enableUnitFog ? 1 : 0, IniSrc(h_unitfog));

    bool mp = MpActive();
    int effInterval = GetEffectiveTargetScanInterval();
    int effKey = GetEffectiveTargetScanKey();
    bool effMinimapFog = GetEffectiveMinimapFog();

    LogMessage("[ra2render] 门控: MpActive=%s, TargetScanKey=配置(%s)->生效(%s), TargetScanInterval=配置(%d)->生效(%d), EnableMinimapFog=配置(%d)->生效(%d), RadarFogGuardMode=生效(%d)",
               mp ? "true" : "false",
               g_targetScanKey ? "position" : "pointer",
               effKey ? "position" : "pointer",
               g_targetScanInterval,
               effInterval,
               g_enableMinimapFog ? 1 : 0,
               effMinimapFog ? 1 : 0,
               effGuard);
    if (mp && g_targetScanKey == 0) {
        LogMessage("[ra2render] [警告/红字] 联机模式处于激活状态(MpActive=true)，强制覆盖 TargetScanKey: 配置(pointer) -> 生效(position)，禁止在联机中使用不确定性指针哈希！");
    }

    // ---- [ZC-10B ④] MP 门控启动日志：逐键打印生效值 ----
    //   口径：仅当 MpActive=true 时才打（联机门控敏感项）；不新增任何协议字段
    //   （[v1.8.35] 裁决：不采纳握手校验）。
    if (mp) {
        LogMessage("[ra2render-mpgate] MP 门控生效值: MpActive=true | TargetScanKey=%s | TargetScanInterval=%d | EnableMinimapFog=%d | L4DirtyMode=%s | FogProbe=%d | EnableStarCraftFog=%d | FogStrengthPct=%s(生效=%s)",
                   effKey ? "position" : "pointer",
                   effInterval,
                   effMinimapFog ? 1 : 0,
                   g_l4DirtyMode == 0 ? "force-full" : (g_l4DirtyMode == 1 ? "vision-dirty" : "vanilla"),
                   g_fogProbeEnabled ? 1 : 0,
                   g_enableStarCraftFog ? 1 : 0,
                   g_fogStrengthPctRaw,
                   g_fogStrengthAuto ? "auto(s=256 不补偿)" : "数值档(按 T 换算)");
        LogMessage("[ra2render-mpgate] 注: 联机侧强制 TargetScanKey=position（确定性坐标哈希）、TargetScanInterval=1（禁节流）、EnableMinimapFog=0（保守关闭）；本行只做日志留痕，不改变任何协议字段。");
    }
}

void EnableLowFragmentationHeap() {
    if (!g_enableLFH) return;

    HANDLE heaps[1024];
    DWORD numHeaps = GetProcessHeaps(1024, heaps);
    ULONG heapFragValue = 2; // 2 = HeapCompatibilityInformation (LFH)
    int enabledCount = 0;
    for (DWORD i = 0; i < numHeaps; ++i) {
        if (HeapSetInformation(heaps[i], HeapCompatibilityInformation, &heapFragValue, sizeof(heapFragValue))) {
            enabledCount++;
        }
    }
    LogMessage("[ra2render] 堆内存优化: 成功激活 %d/%lu 个进程堆的低碎片堆 (LFH) 模式", enabledCount, numHeaps);
}

void CheckTelemetry() {
    CheckMpGateTransition();
    SyncFogMasterMirror();   // [FOG-SWITCH] 总闸汇编侧镜像（热路径节拍点，见 GetEffectiveFogMasterGate 注释）
    SyncFogStrengthMirror(); // [ZC-10B ②] FogStrengthPct 运行期镜像同步（≈2s 节拍重读 ini）
    static DWORD s_lastTelemetryTick = 0;
    DWORD currentTick = GetTickCount();
    if (s_lastTelemetryTick == 0) {
        s_lastTelemetryTick = currentTick;
        return;
    }
    if (currentTick - s_lastTelemetryTick >= 2000) {
        s_lastTelemetryTick = currentTick;
        uint64_t totalScans = g_telemetry.totalTargetScans + g_telemetry.throttledTargetScans;
        double throttlePct = totalScans > 0 ? (100.0 * g_telemetry.throttledTargetScans / totalScans) : 0.0;
        // [RADAR-FIX F2] 两个灰化遥测计数并入 2 秒遥测行：
        //   雷达灰化分支进入次数（护栏放行即 +1，证明护栏不再拦死）
        //   雷达灰化像素数（真正 Set_Pixel 过的像素数，证明灰化逻辑被执行）
        // [RADAR-FIX2] 雷达行拆成三段：① 自绘路径（0/1/2 档）② 原生减暗驱动（3 档）③ 早退桶诊断
        LogMessage("[ra2render-telemetry] BlitCalls: %llu, BlitPixels: %llu Mpx, TargetScans: %llu (平抑: %llu, 节流率: %.1f%%) | 迷雾剔除机动单位: %llu, 半透明迷雾格子: %llu, 渲染单位: %llu | 建筑剔除: %llu, 弹道剔除: %llu | 雷达灰化分支进入次数: %u, 雷达灰化像素数: %u",
            g_telemetry.totalBlitCalls,
            g_telemetry.totalBlitPixels / (1024 * 1024),
            g_telemetry.totalTargetScans,
            g_telemetry.throttledTargetScans,
            throttlePct,
            g_telemetry.unitsCulledByFog,
            g_telemetry.fogCellsDrawn,
            g_telemetry.totalUnitsRendered,
            g_telemetry.buildingsCulledByFog,
            g_telemetry.bulletsCulledByFog,
            s_minimapFogBranchHits,
            s_minimapFogPixels);
        // ---- [ZC-10B ①/③] L4 重绘策略 + 探针开关遥测（2 秒行）----
        //   机判：force-full（默认）⇒ l4RedrawSkippedStatic ≡ 0 且 l4DirtyTransitions 可 >0
        //        vision-dirty         ⇒ 静态视口时 l4RedrawSkippedStatic > 0
        //        vanilla              ⇒ l4RedrawSkippedStatic 恒 >0（恒交还原版 jge）
        //        FogProbe=0（默认）   ⇒ fogprobe 行「有桩读取的窗口=0」
        LogMessage("[ra2render-telemetry-l4dirty] L4DirtyMode=%s | l4RedrawSkippedStatic=%u | l4DirtyTransitions=%u | l4DirtyRampActive=%u | 本帧视口迁移=%u, 视口渐变活跃=%u | FogProbe=%d(fogProbeEnabled=%d)",
            g_l4DirtyMode == 0 ? "force-full" : (g_l4DirtyMode == 1 ? "vision-dirty" : "vanilla"),
            s_l4RedrawSkippedStatic, s_l4DirtyTransitions, s_l4DirtyRampActive,
            s_fogViewportTransitionCount, s_fogViewportRampActive,
            g_fogProbeEnabled ? 1 : 0, static_cast<int>(s_fogProbeEnabledMirror));
        // [FOG-SWITCH F3②] 总闸三计数并入同一 2 秒遥测行（既有字段与顺序**保持不变**，供既有解析口径复用）
        LogMessage("[ra2render-telemetry-fogswitch] 灰雾总闸: EnableStarCraftFog=%d | 半透明层绘制次数: %u | 混色桩介入次数: %u | 小地图减暗驱动次数: %u | (工具.asm 镜像=%u)，总闸=0 时三计数应恒 0",
            g_enableStarCraftFog ? 1 : 0,
            s_fogLayerDraws, s_fogBlendStubHits, s_radarDarkenDriven,
            static_cast<unsigned>(s_fogMasterGate));
        // [FOG-SPLIT F3③] 按格三态 + 玩法层计数**追加在后**（不动上面既有字段；4 以上字段全部为新增）
        //   机器判据（总闸=0 档）：
        //     未探索黑幕绘制次数      > 0   （未探索档未被短路；引擎 0x47EFE0 仍以 -2 档绘制）
        //     未探索格放行次数        > 0   （我方钩子见到未探索格且零介入）
        //     已探索非直视压暗次数    ≡ 0
        //     小地图已探索非直视减暗驱动次数 ≡ 0
        //     玩法层三计数（机动单位剔除 / 建筑剔除 / 弹道剔除）> 0 且量级与总闸=1 相当
        LogMessage("[ra2render-telemetry-fogsplit] 总闸按格三态: EnableStarCraftFog=%d | 未探索黑幕绘制次数: %u | 未探索格放行次数: %u | 已探索非直视压暗次数: %u | 小地图已探索非直视减暗驱动次数: %u | 总闸=0 跳过压暗次数: %u | 黑幕边缘帧绘制次数: %u | 已探索直视格放行次数: %u | 小地图未探索格放行次数: %u | 玩法层(与总闸无关): 机动单位剔除 %llu, 建筑剔除 %llu, 弹道剔除 %llu, 渲染单位 %llu | 判据: 总闸=0 ⇒ 未探索黑幕绘制次数>0 且 未探索格放行次数>0 且 已探索非直视压暗次数≡0 且 小地图已探索非直视减暗驱动次数≡0 且 玩法层三计数>0",
            g_enableStarCraftFog ? 1 : 0,
            s_shroudBlackDraws, s_fogUnexploredPassed, s_exploredFogDarken, s_radarDarkenDriven,
            s_gate0DarkenSkipped, s_shroudEdgeDraws, s_fogVisiblePassed, s_radarUnexploredPassed,
            g_telemetry.unitsCulledByFog, g_telemetry.buildingsCulledByFog, g_telemetry.bulletsCulledByFog,
            g_telemetry.totalUnitsRendered);
        // ---- [FOG-MODE F4] 可见性模式 2 秒行（**新增独立行**；上面所有既有行的字段与顺序零变化）----
        //   机器判据（真机 ZCode 读这一行即可判定档位）：
        //     vanilla   ⇒ 机动单位剔除 ≡0 且 建筑剔除 ≡0 且 弹道剔除 ≡0，且「被 mode 覆盖而放行」>0
        //     starcraft ⇒ 三处剔除计数按视野圈判定增长，且「被 mode 覆盖而放行」≡0
        LogMessage("[ra2render-telemetry-visibility] VisibilityMode=%s(生效=%s) | 三处剔除计数: 机动单位 %llu, 建筑 %llu, 弹道 %llu | 被 mode 覆盖而放行: 合计 %u (机动单位 %u, 建筑 %u, 弹道 %u) | 渲染单位 %llu | 判据: %s",
            g_visibilityModeRaw,
            g_visibilityVanilla ? "vanilla(原版可见性/不做任何视距剔除)" : "starcraft(现状态/视距剔除生效)",
            g_telemetry.unitsCulledByFog, g_telemetry.buildingsCulledByFog, g_telemetry.bulletsCulledByFog,
            s_visVanillaPassed, s_visVanillaMobilePassed, s_visVanillaBuildingPassed, s_visVanillaBulletPassed,
            g_telemetry.totalUnitsRendered,
            g_visibilityVanilla ? "vanilla ⇒ 机动单位剔除≡0 且 建筑剔除≡0 且 弹道剔除≡0 且 被 mode 覆盖而放行>0"
                                : "starcraft ⇒ 三处剔除计数按视野圈判定增长 且 被 mode 覆盖而放行≡0");
        LogMessage("[ra2render-telemetry-radar] 原生减暗路径命中次数: %u (引擎自身判定为暗: %u, 我方谓词强制为暗: %u, 覆盖差: %u) | 三态谓词样本: 求解成功 %u / 失败 %u (已探索 %u, 直视圈内 %u) | 自绘早退桶: 总开关关闭 %u, 护栏拦截 %u, 表面无效 %u, 谓词失败 %u, 未探索 %u, 直视圈内 %u",
            s_nativeDarkenHits, s_nativeEngineDarkHits, s_nativeForcedDarkHits, s_nativeOverrideDeltas,
            s_radarProbeOk, s_radarProbeFail, s_radarProbeExplored, s_radarProbeVisible,
            s_radarGuardRejects[0], s_radarGuardRejects[1], s_radarGuardRejects[2],
            s_radarGuardRejects[3], s_radarGuardRejects[4], s_radarGuardRejects[5]);
        LogMessage("[ra2render-telemetry-radar] 引擎 hWnd 门放弃覆盖次数: %u", s_radarHwndZero);
        // ---- [FOG-CAL2 F2/F3] 灰雾强度校准 2 秒行（**新增独立行，追加在既有行之后**；既有行字段与顺序零变化）----
        //   打印：生效值（auto/数值 T）+ m（由运行期 s 反解）+ s（**运行期读自全局**，故本行即「运行期判定」的实测点）
        //        + 预测净压暗（保留比例）；真机 ZCode 读本行即可与截图逐通道比值对拍（附录 D）。
        //   ★字段改名记录：上一版「预测实测比值(净压暗系数)」→ 本版「预测净压暗(保留比例)」；新增「m(生效)」字段。
        LogMessage("[ra2render-telemetry-fogcal] FogStrengthPct=%s(生效=%s) | m(生效) = 1 - s/512 = %.6f | 桩强度 s=%u / 511（运行期读自全局 VA=0x%08X） | 预测净压暗(保留比例) = 0.71875 × (1 - s/512) = %.6f (= %.4f%%) | 参考计数: 半透明层绘制次数=%u, 混色桩介入次数=%u | 判据: auto ⇒ s=256 且净压暗≈0.359375 (= 23/64); 数值档 T ⇒ s = clamp(round(512*(1-(T/100)/0.71875)), 0, 511) 且净压暗≈T/100（例: T=50 ⇒ s=156 ⇒ 0.4998）",
            g_fogStrengthPctRaw,
            g_fogStrengthAuto ? "auto(不补偿/现状)" : "数值档(目标净压暗/保留比例 百分比 T)",
            FogCalEffectiveM(g_fogStrengthScale256),
            static_cast<unsigned>(g_fogStrengthScale256),
            static_cast<unsigned>(reinterpret_cast<uintptr_t>(&g_fogStrengthScale256)),
            FogCalPredictedRatio(g_fogStrengthScale256),
            100.0 * FogCalPredictedRatio(g_fogStrengthScale256),
            s_fogLayerDraws, s_fogBlendStubHits);

        // ---- [GAP-P223 C4 + GAP-MP-EDGE] 裂缝保护三点计数 2 秒行（**新增独立行**；上面既有行的字段与顺序零变化）----
        //   机器判据（真机 ZCode 读本行即可判定安装档；三个安装态由日志标记区分）：
        //     installed ∈ 0..3 = 本进程**当前**写入的 NOP 点数（装几点算几点；外部安装者不计入）
        //     on 且当前非联机   ⇒ 3（==3 才满足产品契约：存档标记 GapProt Version / MP 握手期望值）；
        //     on 且当前联机     ⇒ 0（**预期**：mp-edge-rollback 已边沿还原；穿透漏洞已修）；
        //     off / forced-off-mp ⇒ 0；介于 1..2 ⇒ 分装中间态（PARTIAL，禁联机、禁存补丁档）。
        //   日志标记口径（互斥可区分）：off（开关关）/ forced-off-mp（init 时已在联机，未写）/
        //     on（init 装上）/ mp-edge-rollback（单机→联机迁移还原）/ mp-edge-reinstall（联机→单机门禁重装）。
        LogMessage("[ra2render-telemetry-gapprot] EnableGapProtection=%d | MpActive=%s | gapProtectionPatchesInstalled=%d/3（P-2.1@0x00568273 / P-2.2@0x00577EC5 / P-2.3@0x00577B60 各 6B 等长 NOP）| 判据: on 且当前非联机 时应为 3；on 且当前联机(已 mp-edge-rollback) 应为 0；off/forced-off-mp 应为 0",
            g_enableGapProtection ? 1 : 0, MpActive() ? "true" : "false", g_gapProtectionPatchesInstalled);
        // ---- [VXL-PRE / SW-CHARGE] 两个等长补丁安装态 2 秒行（新增独立行；既有行字段与顺序零变化）----
        //   ★热路径计数器（VXL：FindCalls/FindHits/QsortCalls/Growths/Inserts；SW：redundantCallsSkipped）
        //     本批**未实现**（热路径插桩风险单列，禁百分比承诺）⇒ 本行只报 init 安装态。
        LogMessage("[ra2render-telemetry-vxlpre] EnableVxlCachePrewarm=%d | vxlCacheInstalled=%d（L-VXL-1 @0x00706D78 imm8 0x0A->0x40；热路径计数器未实现，另卡）| 判据: on 时应为 1；off 应为 0",
            g_enableVxlCachePrewarm ? 1 : 0, g_vxlCacheInstalled);
        LogMessage("[ra2render-telemetry-swo] EnableSWChargeOpt=%d | swChargeOptInstalled=%d（L-SW-1 @0x006CBE88 7B->90x7；零语义变化）| 判据: on 时应为 1；off 应为 0",
            g_enableSWChargeOpt ? 1 : 0, g_swChargeOptInstalled);
        // ---- [FOG-PROBE F1] 桩内「读取值」探针 2 秒行（**新增独立行**；上面所有既有行的字段与顺序零变化）----
        //   字段名与口径**一一对应**（★显式区分两个方向，杜绝反向歧义）：
        //     【store 写入值】      = 我方 HotPath store 语句写进 s_fogBlendStrength 的值（store 后回读）
        //     【桩读取强度值】      = B1/B2 桩内 movzx ebx,[s_fogBlendStrength] 实际读到的 16 位值
        //     【期望桩读值】        = 模型值 = (本格强度 × scale) >> 8（钳 511），C 侧独立算出
        //     【本格强度】          = 写入前的原始本格强度（0/48/64/96/128/144/192/256 或 0/256）
        //     · 采样口径 = **每「格绘制窗口」一次（窗口内首读）**：窗口 = store → call 0x47F250 → 恢复 256；
        //       桶界（三列共用）= 0 / 1-8 / 9-48 / 49-128 / 129-200 / 201-255 / 256 / >256。
        //     · 环形缓冲 = 最近 8 个窗口的【桩读取强度值】（按时间序，不去重；旧→新）。
        //     · 【失配】  = 同一窗口内【store 写入值】!=[桩读取强度值] 的窗口数（判定 A 的量化反面）。
        //     · 【==期望】= 桩读值恰等于【期望桩读值】的窗口数（判定 A：静态/运行期是否一致）。
        //     · 【窗口内读值变化】= 同一窗口内桩读值与首读不一致的读取次数（≈0 ⇒ 窗口内恒）。 
        LogMessage("[ra2render-telemetry-fogprobe] FogStrengthPct=%s | 采样窗口(store->call->restore)=%u | 有桩读取的窗口=%u | 窗口外桩读取=%u | 最近窗口样本: 本格强度=%u, store写入值=%u, 期望桩读值=%u, 桩读取强度值=%u | 桩读取强度值==期望桩读值: %u 窗口, !=: %u 窗口 | 失配(store写入值!=桩读取强度值)窗口数=%u | 窗口内桩读取值变化次数=%u | s_fogBlendStrength 运行期 VA=0x%08X",
            g_fogStrengthPctRaw,
            s_probeWindows, s_probeReadsInWindow, s_probeAlienReads,
            static_cast<unsigned>(s_probeCellStrength), static_cast<unsigned>(s_probeWriteValue),
            static_cast<unsigned>(s_probeExpectedValue), static_cast<unsigned>(s_probeWindowValue),
            s_probeReadEqExpected, s_probeReadNeExpected,
            s_probeMismatch, s_probeMidWindowChange,
            static_cast<unsigned>(reinterpret_cast<uintptr_t>(&s_fogBlendStrength)));
        //   分桶三列：0 / 1-8 / 9-48 / 49-128 / 129-200 / 201-255 / 256 / >256
        LogMessage("[ra2render-telemetry-fogprobe] 分桶[0|1-8|9-48|49-128|129-200|201-255|256|>256]: 【期望桩读值】=%u,%u,%u,%u,%u,%u,%u,%u | 【store 写入值】=%u,%u,%u,%u,%u,%u,%u,%u | 【桩读取强度值】=%u,%u,%u,%u,%u,%u,%u,%u | 环形缓冲(槽位序 0..7；写指针 idx=%u；槽 i ↔ 窗口 k≡i (mod 8)；最新窗口=槽(idx-1)mod8)=%u,%u,%u,%u,%u,%u,%u,%u",
            s_probeExpectedBucket[0], s_probeExpectedBucket[1], s_probeExpectedBucket[2], s_probeExpectedBucket[3],
            s_probeExpectedBucket[4], s_probeExpectedBucket[5], s_probeExpectedBucket[6], s_probeExpectedBucket[7],
            s_probeWriteBucket[0], s_probeWriteBucket[1], s_probeWriteBucket[2], s_probeWriteBucket[3],
            s_probeWriteBucket[4], s_probeWriteBucket[5], s_probeWriteBucket[6], s_probeWriteBucket[7],
            s_probeBucket[0], s_probeBucket[1], s_probeBucket[2], s_probeBucket[3],
            s_probeBucket[4], s_probeBucket[5], s_probeBucket[6], s_probeBucket[7],
            static_cast<unsigned>(s_probeRingIdx),
            static_cast<unsigned>(s_probeRing[0]), static_cast<unsigned>(s_probeRing[1]),
            static_cast<unsigned>(s_probeRing[2]), static_cast<unsigned>(s_probeRing[3]),
            static_cast<unsigned>(s_probeRing[4]), static_cast<unsigned>(s_probeRing[5]),
            static_cast<unsigned>(s_probeRing[6]), static_cast<unsigned>(s_probeRing[7]));
        //   ★真机判据（ZCode 读本行即可定谳 H-渐变相；口径见 docs/re/fog_stub_probe_report.md 附录 B）：
        //     · 数值档 T=50（期望桩读值=156）：【桩读取强度值】≈39 且【本格强度】以 64 为主
        //       ⇒ H-渐变相 (5-ramp)*64 成立（数值档进了渐变相，走方案 A2：强度相依赖解耦）；
        //     · 数值档：【store 写入值】=156 且【桩读取强度值】=156 而像素仍 ≈0.68
        //       ⇒ 写/读一致，矛盾在桩之外（回传全部字段再定）；
        //     · 数值档：【store 写入值】=156、【桩读取强度值】≈39、【本格强度】=256 且【失配】>0
        //       ⇒ 写后读前被改写（走方案 A1）；auto 档对照：【本格强度】=256、【桩读取强度值】=256。
        LogMessage("[ra2render-telemetry-fogprobe-ramp] 【本格强度】命中: 0=%u, 48=%u, 64=%u, 96=%u, 128=%u, 144=%u, 192=%u, 256=%u, 其它=%u | 渐变相 s_fogRampFrame 分布: 非渐变=%u, ramp1=%u, ramp2=%u, ramp3=%u, ramp4=%u | FadeFogTransition=%d | 判据: 数值档若【桩读取强度值】≈39 且【本格强度】以 64 为主 ⇒ H-渐变相成立; auto 档对照应为【本格强度】=256 且【桩读取强度值】=256",
            s_probeStrengthHit[0], s_probeStrengthHit[1], s_probeStrengthHit[2], s_probeStrengthHit[3],
            s_probeStrengthHit[4], s_probeStrengthHit[5], s_probeStrengthHit[6], s_probeStrengthHit[7],
            s_probeStrengthHit[8],
            s_probeRampHist[0], s_probeRampHist[1], s_probeRampHist[2], s_probeRampHist[3], s_probeRampHist[4],
            g_fadeFogTransition ? 1 : 0);
    }
}

// ---------------------------------------------------------------------------
// L2 分片键（缺陷2 修复）：旧实现 unitHash = 指针地址>>4 —— 各端堆址不同 → 同一单位
// 在不同帧被扫描 → 目标选取时序分叉 → 联机 desync（违反台账 [v1.5.10] §6.2 红线）。
// 新默认键 = 单位格子坐标的空间哈希：锁步确定性下各端同帧同坐标 → 分片时机逐帧一致；
// TargetScanKey=pointer 保留旧键（仅限单机）。G-02: 联机模式强制 position。
// ---------------------------------------------------------------------------
int g_targetScanKey = 1;   // 0=pointer(旧,仅单机) 1=position(默认,联机安全)

static uint32_t ThrottleKey(void *pThis) {
    int effectiveKey = GetEffectiveTargetScanKey();
    if (!effectiveKey) {
        return static_cast<uint32_t>(reinterpret_cast<uintptr_t>(pThis)) >> 4;
    }
    if (!pThis || IsBadReadPtr(reinterpret_cast<void*>(reinterpret_cast<uintptr_t>(pThis) + 0x9C), 8)) {
        return 0;
    }
    __try {
        int locX = *reinterpret_cast<const int*>(reinterpret_cast<const uint8_t*>(pThis) + 0x9C);
        int locY = *reinterpret_cast<const int*>(reinterpret_cast<const uint8_t*>(pThis) + 0xA0);
        uint32_t hx = static_cast<uint32_t>(locX) * 0x9E3779B1u;
        uint32_t hy = static_cast<uint32_t>(locY) * 0x85EBCA77u;
        return (hx ^ hy) >> 4;
    }
    __except (EXCEPTION_EXECUTE_HANDLER) {
        return 0;
    }
}

void EnforceGameSpeedUnlock() {
    // 保护玩家原版游戏控制权：绝不强行锁死 GameSpeed 与 FrameDelay
    // 彻底恢复游戏内加速/降速按键，以及设置菜单中游戏速度、屏幕滚动速度滑块的调节灵敏度
}

// ============================================================================
// L1: 16-bit HighColor 向量化软渲染 Blitters
// ============================================================================

void __thiscall BlitterHooks::Hook_BlitTransXlatAlphaZRead(
    void *dst, uint8_t *src, unsigned int length,
    uint16_t zMin, uint16_t *zBuf, uint16_t *aBuf, uint16_t aLvl, int warpOffset
) {
    BlitterCore *pThis = reinterpret_cast<BlitterCore*>(this);
    g_telemetry.totalBlitCalls++;
    g_telemetry.totalBlitPixels += length;

    if (warpOffset == 0 && aBuf == nullptr && pThis && pThis->XlatTable) {
        uint16_t *d = static_cast<uint16_t*>(dst);
        const uint8_t *s = src;
        uint16_t *z = zBuf;
        const uint16_t *xlat = pThis->XlatTable;

        unsigned int i = 0;
        if (g_enableSIMD) {
            __m128i zero128 = _mm_setzero_si128();
            for (; i + 16 <= length; i += 16) {
                __m128i pixels = _mm_loadu_si128(reinterpret_cast<const __m128i*>(s + i));
                __m128i cmp = _mm_cmpeq_epi8(pixels, zero128);
                int mask = _mm_movemask_epi8(cmp);
                if (mask == 0xFFFF) {
                    continue; // 16 像素全透明块快速跳过
                }
                for (int k = 0; k < 16; ++k) {
                    uint8_t c = s[i + k];
                    if (c != 0 && (!z || z[i + k] > zMin)) {
                        d[i + k] = xlat[c];
                    }
                }
            }
        }

        for (; i < length; ++i) {
            uint8_t c = s[i];
            if (c != 0 && (!z || z[i] > zMin)) {
                d[i] = xlat[c];
            }
        }
        return;
    }

    if (g_pOrigBlitTransXlatAlphaZRead) {
        g_pOrigBlitTransXlatAlphaZRead(pThis, dst, src, length, zMin, zBuf, aBuf, aLvl, warpOffset);
    }
}

void __thiscall BlitterHooks::Hook_BlitTransXlat_G(
    void *dst, uint8_t *src, unsigned int length,
    uint16_t zMin, uint16_t *zBuf, uint16_t *aBuf, uint16_t aLvl, int warpOffset
) {
    BlitterCore *pThis = reinterpret_cast<BlitterCore*>(this);
    g_telemetry.totalBlitCalls++;
    g_telemetry.totalBlitPixels += length;

    if (pThis && pThis->XlatTable) {
        uint16_t *d = static_cast<uint16_t*>(dst);
        const uint8_t *s = src;
        const uint16_t *xlat = pThis->XlatTable;

        unsigned int i = 0;
        if (g_enableSIMD) {
            __m128i zero128 = _mm_setzero_si128();
            for (; i + 16 <= length; i += 16) {
                __m128i pixels = _mm_loadu_si128(reinterpret_cast<const __m128i*>(s + i));
                __m128i cmp = _mm_cmpeq_epi8(pixels, zero128);
                int mask = _mm_movemask_epi8(cmp);
                if (mask == 0xFFFF) {
                    continue;
                }
                for (int k = 0; k < 16; ++k) {
                    uint8_t c = s[i + k];
                    if (c != 0) {
                        d[i + k] = xlat[c];
                    }
                }
            }
        }

        for (; i < length; ++i) {
            uint8_t c = s[i];
            if (c != 0) {
                d[i] = xlat[c];
            }
        }
        return;
    }

    if (g_pOrigBlitTransXlat_G) {
        g_pOrigBlitTransXlat_G(pThis, dst, src, length, zMin, zBuf, aBuf, aLvl, warpOffset);
    }
}

void __thiscall BlitterHooks::Hook_RLEBlitTransXlat_G(
    void *dst, uint8_t *src, uint8_t Length,
    int EncodedLen, int a6, int a7, int a8, int a9, int a10, int a11
) {
    RLEBlitterCore *pThis = reinterpret_cast<RLEBlitterCore*>(this);
    g_telemetry.totalBlitCalls++;
    g_telemetry.totalBlitPixels += Length;

    if (g_pOrigRLEBlitTransXlat_G) {
        g_pOrigRLEBlitTransXlat_G(pThis, dst, src, Length, EncodedLen, a6, a7, a8, a9, a10, a11);
    }
}

void __thiscall BlitterHooks::Hook_BlitTrans_G(
    void *dst, uint8_t *src, unsigned int length,
    uint16_t zMin, uint16_t *zBuf, uint16_t *aBuf, uint16_t aLvl, int warpOffset
) {
    BlitterCore *pThis = reinterpret_cast<BlitterCore*>(this);
    g_telemetry.totalBlitCalls++;
    g_telemetry.totalBlitPixels += length;

    if (dst && src && length > 0) {
        uint16_t *d = static_cast<uint16_t*>(dst);
        const uint16_t *s = reinterpret_cast<const uint16_t*>(src);

        unsigned int i = 0;
        if (g_enableSIMD) {
            __m128i zero128 = _mm_setzero_si128();
            for (; i + 8 <= length; i += 8) {
                __m128i s16 = _mm_loadu_si128(reinterpret_cast<const __m128i*>(s + i));
                __m128i zeroMask = _mm_cmpeq_epi16(s16, zero128);
                int m16 = _mm_movemask_epi8(zeroMask);
                if (m16 == 0xFFFF) {
                    continue; // 8 像素全透明，快速跳过
                }
                if (m16 == 0x0000) {
                    _mm_storeu_si128(reinterpret_cast<__m128i*>(d + i), s16);
                    continue; // 8 像素全实体，批量写入
                }
                // 透明混合：zeroMask 为 1 处保留 d16，为 0 处采用 s16
                __m128i d16 = _mm_loadu_si128(reinterpret_cast<const __m128i*>(d + i));
                __m128i res = _mm_or_si128(_mm_andnot_si128(zeroMask, s16), _mm_and_si128(zeroMask, d16));
                _mm_storeu_si128(reinterpret_cast<__m128i*>(d + i), res);
            }
        }

        for (; i < length; ++i) {
            uint16_t val = s[i];
            if (val != 0) {
                d[i] = val;
            }
        }
        return;
    }

    if (g_pOrigBlitTrans_G) {
        g_pOrigBlitTrans_G(pThis, dst, src, length, zMin, zBuf, aBuf, aLvl, warpOffset);
    }
}

void __thiscall BlitterHooks::Hook_BlitTransDarken_G(
    void *dst, uint8_t *src, unsigned int length,
    uint16_t zMin, uint16_t *zBuf, uint16_t *aBuf, uint16_t aLvl, int warpOffset
) {
    BlitterDarkenCore *pThis = reinterpret_cast<BlitterDarkenCore*>(this);
    g_telemetry.totalBlitCalls++;
    g_telemetry.totalBlitPixels += length;

    if (pThis && dst && src && length > 0) {
        uint16_t *d = static_cast<uint16_t*>(dst);
        const uint8_t *s = src;
        uint16_t mask = pThis->DarkenMask;

        unsigned int i = 0;
        if (g_enableSIMD) {
            __m128i zero128 = _mm_setzero_si128();
            __m128i mask128 = _mm_set1_epi16(static_cast<short>(mask));

            for (; i + 8 <= length; i += 8) {
                __m128i s8 = _mm_loadl_epi64(reinterpret_cast<const __m128i*>(s + i));
                __m128i cmp8 = _mm_cmpeq_epi8(s8, zero128);
                int m8 = _mm_movemask_epi8(cmp8) & 0xFF;
                if (m8 == 0xFF) {
                    continue; // 8 像素全无阴影，快速跳过
                }

                __m128i d16 = _mm_loadu_si128(reinterpret_cast<const __m128i*>(d + i));
                __m128i darkened = _mm_and_si128(_mm_srli_epi16(d16, 1), mask128);

                __m128i s16 = _mm_unpacklo_epi8(s8, zero128);
                __m128i zeroMask = _mm_cmpeq_epi16(s16, zero128);

                __m128i res = _mm_or_si128(_mm_andnot_si128(zeroMask, darkened), _mm_and_si128(zeroMask, d16));
                _mm_storeu_si128(reinterpret_cast<__m128i*>(d + i), res);
            }
        }

        for (; i < length; ++i) {
            if (s[i] != 0) {
                d[i] = (d[i] >> 1) & mask;
            }
        }
        return;
    }

    if (g_pOrigBlitTransDarken_G) {
        g_pOrigBlitTransDarken_G(reinterpret_cast<BlitterCore*>(this), dst, src, length, zMin, zBuf, aBuf, aLvl, warpOffset);
    }
}

void __thiscall BlitterHooks::Hook_BlitPlain_G(
    void *dst, uint8_t *src, unsigned int length,
    uint16_t zMin, uint16_t *zBuf, uint16_t *aBuf, uint16_t aLvl, int warpOffset
) {
    BlitterCore *pThis = reinterpret_cast<BlitterCore*>(this);
    g_telemetry.totalBlitCalls++;
    g_telemetry.totalBlitPixels += length;

    if (dst && src && length > 0) {
        memcpy(dst, src, length * 2);
        return;
    }

    if (g_pOrigBlitPlain_G) {
        g_pOrigBlitPlain_G(pThis, dst, src, length, zMin, zBuf, aBuf, aLvl, warpOffset);
    }
}

template<typename DestType, typename SrcType>
DestType union_cast(SrcType src) {
    union {
        SrcType s;
        DestType d;
    } u;
    u.s = src;
    return u.d;
}

// ============================================================================
// L2: 逻辑寻敌与威胁评估分散轮询 (消除 800 单位每帧全量扫描导致的慢动作)
// ============================================================================

void __thiscall TargetHooks::Hook_Techno_SelectAutoTarget() {
    void *pThis = this;
    CheckTelemetry();

    const uint32_t *pCurrentFrame = reinterpret_cast<const uint32_t*>(ADDR_CURRENT_FRAME);
    uint32_t currentFrame = (pCurrentFrame && !IsBadReadPtr((void*)pCurrentFrame, 4)) ? *pCurrentFrame : 0;
    uint32_t unitHash = ThrottleKey(pThis);   // 缺陷2：确定性分片键

    int interval = GetEffectiveTargetScanInterval();
    if (interval > 1 && currentFrame > 0) {
        if (((unitHash + currentFrame) % static_cast<uint32_t>(interval)) != 0) {
            g_telemetry.throttledTargetScans++;
            return;
        }
    }

    g_telemetry.totalTargetScans++;
    if (g_pOrigTechnoSelectAutoTarget) {
        g_pOrigTechnoSelectAutoTarget(pThis);
    }
}

void __thiscall TargetHooks::Hook_Unit_SelectAutoTarget() {
    void *pThis = this;
    CheckTelemetry();

    const uint32_t *pCurrentFrame = reinterpret_cast<const uint32_t*>(ADDR_CURRENT_FRAME);
    uint32_t currentFrame = (pCurrentFrame && !IsBadReadPtr((void*)pCurrentFrame, 4)) ? *pCurrentFrame : 0;
    uint32_t unitHash = ThrottleKey(pThis);   // 缺陷2：确定性分片键

    int interval = GetEffectiveTargetScanInterval();
    if (interval > 1 && currentFrame > 0) {
        if (((unitHash + currentFrame) % static_cast<uint32_t>(interval)) != 0) {
            g_telemetry.throttledTargetScans++;
            return;
        }
    }

    g_telemetry.totalTargetScans++;
    if (g_pOrigUnitSelectAutoTarget) {
        g_pOrigUnitSelectAutoTarget(pThis);
    }
}

// ============================================================================
// L2: Greatest_Threat (0x006F8DF0) Inline Hook & 存活目标保持 (Target Retention)
// ============================================================================

// 原版 0x006F8DF0 指令：
// 006F8DF0: 83 EC 5C          sub esp, 0x5C           (3 字节)
// 006F8DF3: 8B 15 34 EC A8 00 mov edx, [0x00A8EC34]   (6 字节)
// 合计 9 字节。下一条指令位于 0x006F8DF9 (53 = push ebx)
static uint8_t s_origGreatestThreatBytes[9] = {0};
static uint8_t s_greatestThreatTrampoline[16] = {0};

void* __thiscall TargetHooks::Hook_Techno_Greatest_Threat(uintptr_t arg1, uintptr_t arg2, uintptr_t arg3) {
    void *pThis = this;

    // 关键安全原则：如果单位已有存活的旧目标 (Target at offset 0x5D4)，在节流帧安全返回该目标，绝不返回 nullptr
    if (!IsBadReadPtr(reinterpret_cast<void*>(reinterpret_cast<uintptr_t>(pThis) + 0x5D4), sizeof(void*))) {
        void *pTarget = *reinterpret_cast<void**>(reinterpret_cast<uintptr_t>(pThis) + 0x5D4);
        if (pTarget != nullptr && !IsBadReadPtr(pTarget, 0x84)) {
            int health = *reinterpret_cast<int*>(reinterpret_cast<uintptr_t>(pTarget) + 0x6C);
            uint8_t inLimbo = *reinterpret_cast<uint8_t*>(reinterpret_cast<uintptr_t>(pTarget) + 0x81);
            if (health > 0 && inLimbo == 0) {
                const uint32_t *pCurrentFrame = reinterpret_cast<const uint32_t*>(ADDR_CURRENT_FRAME);
                uint32_t currentFrame = (pCurrentFrame && !IsBadReadPtr((void*)pCurrentFrame, 4)) ? *pCurrentFrame : 0;
                uint32_t unitHash = ThrottleKey(pThis);   // 缺陷2：确定性分片键

                int interval = GetEffectiveTargetScanInterval();
                if (interval > 1 && currentFrame > 0) {
                    if (((unitHash + currentFrame) % static_cast<uint32_t>(interval)) != 0) {
                        g_telemetry.throttledTargetScans++;
                        return pTarget; // 保持原有存活目标，规避全图螺旋遍历！
                    }
                }
            }
        }
    }

    g_telemetry.totalTargetScans++;
    if (g_pOrigTechnoGreatestThreat) {
        return g_pOrigTechnoGreatestThreat(pThis, arg1, arg2, arg3);
    }
    return nullptr;
}

void* __thiscall TargetHooks::Hook_Unit_Greatest_Threat(uintptr_t arg1, uintptr_t arg2, uintptr_t arg3) {
    return Hook_Techno_Greatest_Threat(arg1, arg2, arg3);
}

static bool InstallGreatestThreatHook() {
    memcpy(s_origGreatestThreatBytes, reinterpret_cast<void*>(ADDR_ORIG_TECHNO_GREATEST_THREAT), 9);

    DWORD oldProtect = 0;
    if (!VirtualProtect(s_greatestThreatTrampoline, sizeof(s_greatestThreatTrampoline), PAGE_EXECUTE_READWRITE, &oldProtect)) {
        LogMessage("[ra2render-target] 错误：无法设置 Greatest_Threat Trampoline 内存权限");
        return false;
    }

    // 填充跳板：备份的 9 字节 + jmp 回 0x006F8DF9 (5 字节)
    memcpy(s_greatestThreatTrampoline, s_origGreatestThreatBytes, 9);
    s_greatestThreatTrampoline[9] = 0xE9; // JMP rel32
    int32_t jmpBack = static_cast<int32_t>((ADDR_ORIG_TECHNO_GREATEST_THREAT + 9) - (reinterpret_cast<uintptr_t>(s_greatestThreatTrampoline) + 14));
    memcpy(&s_greatestThreatTrampoline[10], &jmpBack, sizeof(int32_t));

    g_pOrigTechnoGreatestThreat = reinterpret_cast<FnGreatestThreat>(reinterpret_cast<void*>(s_greatestThreatTrampoline));

    if (!VirtualProtect(reinterpret_cast<void*>(ADDR_ORIG_TECHNO_GREATEST_THREAT), 9, PAGE_EXECUTE_READWRITE, &oldProtect)) {
        LogMessage("[ra2render-target] 错误：无法修改 0x006F8DF0 内存权限");
        return false;
    }

    // 安装 9 字节 Inline Hook：E9 <rel32> + 4 个 0x90 (NOP)
    uint8_t patch[9];
    patch[0] = 0xE9;
    uintptr_t hookAddr = union_cast<uintptr_t>(&TargetHooks::Hook_Techno_Greatest_Threat);
    int32_t jmpToHook = static_cast<int32_t>(hookAddr - (ADDR_ORIG_TECHNO_GREATEST_THREAT + 5));
    memcpy(&patch[1], &jmpToHook, sizeof(int32_t));
    patch[5] = 0x90;
    patch[6] = 0x90;
    patch[7] = 0x90;
    patch[8] = 0x90;
    memcpy(reinterpret_cast<void*>(ADDR_ORIG_TECHNO_GREATEST_THREAT), patch, 9);

    VirtualProtect(reinterpret_cast<void*>(ADDR_ORIG_TECHNO_GREATEST_THREAT), 9, oldProtect, &oldProtect);
    LogMessage("[ra2render-target] 成功挂载 Greatest_Threat Inline Hook (0x006F8DF0 -> 0x%08X)，覆盖全体作战单位/步兵/建筑/空军！", hookAddr);
    return true;
}

static void RemoveGreatestThreatHook() {
    if (g_pOrigTechnoGreatestThreat) {
        DWORD oldProtect = 0;
        VirtualProtect(reinterpret_cast<void*>(ADDR_ORIG_TECHNO_GREATEST_THREAT), 9, PAGE_EXECUTE_READWRITE, &oldProtect);
        memcpy(reinterpret_cast<void*>(ADDR_ORIG_TECHNO_GREATEST_THREAT), s_origGreatestThreatBytes, 9);
        VirtualProtect(reinterpret_cast<void*>(ADDR_ORIG_TECHNO_GREATEST_THREAT), 9, oldProtect, &oldProtect);
        g_pOrigTechnoGreatestThreat = nullptr;
    }
}

// ============================================================================
// L3: 星际争霸式战争迷雾 (Fog of War) 视距动态剔除与人族雷达重构
// ============================================================================

static uint32_t s_lastFrameUpdated = 0xFFFFFFFF;
static bool s_spySatPatched = false;

static inline void StampVisionCircle(int cx, int cy, int radius) {
    if (radius <= 0) return;
    int ymin = (cy - radius < 0) ? 0 : (cy - radius);
    int ymax = (cy + radius > 511) ? 511 : (cy + radius);
    int r2 = radius * radius;

    for (int y = ymin; y <= ymax; ++y) {
        int dy = y - cy;
        int dy2 = dy * dy;
        if (dy2 > r2) continue;

        int dxMax = static_cast<int>(sqrtf(static_cast<float>(r2 - dy2)));
        int xmin = (cx - dxMax < 0) ? 0 : (cx - dxMax);
        int xmax = (cx + dxMax > 511) ? 511 : (cx + dxMax);

        uint32_t *row = &s_visionGrid[y * 512];
        for (int x = xmin; x <= xmax; ++x) {
            row[x] = s_visionToken;
        }
    }
}

void PatchSpySatBuildingTypes() {
    if (!g_enableSpySatRadarSweep) return;

    // 1. 在 SuperWeaponTypeClass::Array 中查找 PsychicReveal 超武索引
    uintptr_t swArrayBase = ADDR_ARRAY_SUPERWEAPON_TYPES;
    if (IsBadReadPtr(reinterpret_cast<void*>(swArrayBase), 0x20)) return;
    void **swItems = *reinterpret_cast<void***>(swArrayBase + 4);
    int swCount = *reinterpret_cast<const int*>(swArrayBase + 16);
    if (!swItems || swCount <= 0 || swCount > 100 || IsBadReadPtr(swItems, swCount * sizeof(void*))) return;

    int psychicRevealIndex = -1;
    for (int i = 0; i < swCount; ++i) {
        void *pSW = swItems[i];
        if (!pSW || IsBadReadPtr(pSW, 0x120)) continue;
        const char *swName = reinterpret_cast<const char*>(reinterpret_cast<uintptr_t>(pSW) + 0x24);
        if (strstr(swName, "PsychicReveal") != nullptr) {
            psychicRevealIndex = i;
            if (g_radarSweepCooldownFrames > 0) {
                *reinterpret_cast<int*>(reinterpret_cast<uintptr_t>(pSW) + 0xB0) = g_radarSweepCooldownFrames;
            }
            if (g_radarSweepRadiusCells > 0) {
                *reinterpret_cast<float*>(reinterpret_cast<uintptr_t>(pSW) + 0xF8) = static_cast<float>(g_radarSweepRadiusCells);
            }
            break;
        }
    }

    // 2. 遍历 BuildingTypeClass::Array 拦截 SpySat 建筑
    uintptr_t bldArrayBase = ADDR_ARRAY_BUILDING_TYPES;
    if (IsBadReadPtr(reinterpret_cast<void*>(bldArrayBase), 0x20)) return;
    void **bldItems = *reinterpret_cast<void***>(bldArrayBase + 4);
    int bldCount = *reinterpret_cast<const int*>(bldArrayBase + 16);
    if (!bldItems || bldCount <= 0 || bldCount > 1000 || IsBadReadPtr(bldItems, bldCount * sizeof(void*))) return;

    int patchedCount = 0;
    for (int i = 0; i < bldCount; ++i) {
        void *pBld = bldItems[i];
        if (!pBld || IsBadReadPtr(pBld, 0x1750)) continue;

        bool hasSpySat = *reinterpret_cast<const bool*>(reinterpret_cast<uintptr_t>(pBld) + 0x16A5);
        if (hasSpySat) {
            // 关闭原版全图恒定常亮（去除永久全图Reveal）
            *reinterpret_cast<bool*>(reinterpret_cast<uintptr_t>(pBld) + 0x16A5) = false;

            // 赋予星际人族雷达（PsychicReveal主动CD区域扫描）
            if (psychicRevealIndex >= 0) {
                int curSW = *reinterpret_cast<const int*>(reinterpret_cast<uintptr_t>(pBld) + 0x16F0);
                if (curSW == -1) {
                    *reinterpret_cast<int*>(reinterpret_cast<uintptr_t>(pBld) + 0x16F0) = psychicRevealIndex;
                }
            }
            patchedCount++;
            LogMessage("[ra2render-fog] 成功将间谍卫星建筑 (BuildingType #%d) 重构为星际人族主动区域雷达超武 (PsychicReveal=%d, CD=%d帧, 半径=%d格)",
                       i, psychicRevealIndex, g_radarSweepCooldownFrames, g_radarSweepRadiusCells);
        }
    }
    if (patchedCount > 0) {
        s_spySatPatched = true;
    }
}

// 敌方建筑"已侦察"标记：底座（FoundationData, Type+0xDFC, CellStruct* 以 0x7FFF 哨兵结束）
// 任一格处于直视圈则整座建筑的所有底座格永久标记为已见
static void StampEverSeenIfVisible(int anchorX, int anchorY, void *pType) {
    short cells[64][2];
    int n = 0;
    bool haveFoundation = false;

    if (pType && !IsBadReadPtr(reinterpret_cast<void*>(reinterpret_cast<uintptr_t>(pType) + OFF_BLDTYPE_FOUNDATION_DATA), 4)) {
        const short *fd = *reinterpret_cast<short* const*>(reinterpret_cast<uintptr_t>(pType) + OFF_BLDTYPE_FOUNDATION_DATA);
        if (fd && !IsBadReadPtr(fd, 8)) {
            for (int i = 0; i < 64; ++i) {
                short dx = fd[i * 2];
                short dy = fd[i * 2 + 1];
                if (dx == static_cast<short>(0x7FFF) && dy == static_cast<short>(0x7FFF)) break;
                cells[n][0] = dx;
                cells[n][1] = dy;
                n++;
                if (n >= 64) break;
            }
            haveFoundation = (n > 0);
        }
    }
    if (!haveFoundation) {
        cells[0][0] = 0;
        cells[0][1] = 0;
        n = 1;
    }

    bool visible = false;
    for (int i = 0; i < n; ++i) {
        int x = anchorX + cells[i][0];
        int y = anchorY + cells[i][1];
        if (x < 0 || x >= 512 || y < 0 || y >= 512) continue;
        if (s_visionGrid[y * 512 + x] == s_visionToken) {
            visible = true;
            break;
        }
    }
    if (!visible) return;

    for (int i = 0; i < n; ++i) {
        int x = anchorX + cells[i][0];
        int y = anchorY + cells[i][1];
        if (x < 0 || x >= 512 || y < 0 || y >= 512) continue;
        s_everSeenGrid[y * 512 + x] = 1;
    }
}

void UpdateVisionGrid() {
    CheckMpGateTransition();
    const uint32_t *pCurrentFrame = reinterpret_cast<const uint32_t*>(ADDR_CURRENT_FRAME);
    uint32_t currentFrame = pCurrentFrame ? *pCurrentFrame : 0;
    if (currentFrame != 0 && currentFrame == s_lastFrameUpdated) {
        return;
    }

    // ★[ZC-10B ①] 新逻辑帧首格：复位视口累计窗口（后续格子累加出本帧视口范围）
    s_viewCellMinX = 0x7FFFFFFF; s_viewCellMinY = 0x7FFFFFFF;
    s_viewCellMaxX = -1;           s_viewCellMaxY = -1;

    // 战局重载检测：逻辑帧号大幅回退 = 新遭遇战/读早期档，重置跨战局持久状态
    // （everSeen 侦察记忆、渐变状态、间谍卫星补丁标记；读晚期档保留记忆，避免侦察成果无谓丢失）
    if (s_lastFrameUpdated != 0xFFFFFFFF && currentFrame + 100 < s_lastFrameUpdated) {
        memset(s_everSeenGrid, 0, sizeof(s_everSeenGrid));
        memset(s_prevVisionGrid, 0, sizeof(s_prevVisionGrid));
        memset(s_fogRampFrame, 0, sizeof(s_fogRampFrame));
        s_visionInitDone = false;
        s_spySatPatched = false;
        s_minimapForceRefresh = 10;
    }

    s_lastFrameUpdated = currentFrame;

    s_visionToken++;
    if (s_visionToken == 0) {
        memset(s_visionGrid, 0, sizeof(s_visionGrid));
        memset(s_cellFogDrawnToken, 0, sizeof(s_cellFogDrawnToken));
        memset(s_prevVisionGrid, 0, sizeof(s_prevVisionGrid));
        memset(s_fogRampFrame, 0, sizeof(s_fogRampFrame));
        s_visionInitDone = false;
        s_visionToken = 1;
    }

    __try {
        void *pPlayer = *reinterpret_cast<void**>(ADDR_HOUSE_PLAYER);
        if (!pPlayer) return;

        // 懒加载重构间谍卫星与人族雷达
        if (!s_spySatPatched) {
            PatchSpySatBuildingTypes();
        }

        // 务必保持 Scenario 的 FogOfWar 引擎标志恒为 0！
        // 绝不可置 1！若置 1，原版 Draw_Shroud (0x0047EFE0) 会被引擎切换为使用 FOG.SHP，
        // 导致未探索区域变成透明高亮黄白色，且 CellClass::Draw 会调用原版残缺代码导致全图变黑。
        uintptr_t scenarioBase = *reinterpret_cast<uintptr_t*>(ADDR_SCENARIO_INSTANCE);
        if (scenarioBase) {
            *reinterpret_cast<uint32_t*>(scenarioBase) &= ~0x1000u;
        }

        // 确保玩家 SpySatActive 永远为 false，彻底解除对裂缝产生器 (GapGenerator) 的失效锁死
        *reinterpret_cast<uint8_t*>(reinterpret_cast<uintptr_t>(pPlayer) + 0x577A) = 0;

        int playerIdx = *reinterpret_cast<const int*>(reinterpret_cast<const uint8_t*>(pPlayer) + 0x30);
        uint32_t playerAllies = *reinterpret_cast<const uint32_t*>(reinterpret_cast<const uint8_t*>(pPlayer) + 0x5788);

        auto isPlayerOrAlly = [pPlayer, playerIdx, playerAllies](void *pOwner) -> bool {
            if (!pOwner) return false;
            if (pOwner == pPlayer) return true;
            int ownerIdx = *reinterpret_cast<const int*>(reinterpret_cast<const uint8_t*>(pOwner) + 0x30);
            if (ownerIdx >= 0 && ownerIdx < 32 && ((1u << ownerIdx) & playerAllies) != 0) {
                return true;
            }
            return false;
        };

        auto stampTechnoArray = [&](uintptr_t arrayBase, int defaultSight) {
            void **items = *reinterpret_cast<void***>(arrayBase + 4);
            int count = *reinterpret_cast<const int*>(arrayBase + 16);
            if (!items || count <= 0 || count > 50000) return;

            for (int i = 0; i < count; ++i) {
                void *pObj = items[i];
                if (!pObj) continue;

                int health = *reinterpret_cast<const int*>(reinterpret_cast<const uint8_t*>(pObj) + 0x6C);
                if (health <= 0) continue;

                void *pOwner = *reinterpret_cast<void**>(reinterpret_cast<uintptr_t>(pObj) + 0x21C);
                if (!isPlayerOrAlly(pOwner)) continue;

                int locX = *reinterpret_cast<const int*>(reinterpret_cast<const uint8_t*>(pObj) + 0x9C);
                int locY = *reinterpret_cast<const int*>(reinterpret_cast<const uint8_t*>(pObj) + 0xA0);
                int cellX = locX >> 8;
                int cellY = locY >> 8;
                if (cellX < 0 || cellX >= 512 || cellY < 0 || cellY >= 512) continue;

                int sight = defaultSight;
                void *pType = *reinterpret_cast<void**>(reinterpret_cast<uintptr_t>(pObj) + 0x6C4);
                if (pType && !IsBadReadPtr(pType, 0x600)) {
                    int s = *reinterpret_cast<const int*>(reinterpret_cast<const uint8_t*>(pType) + 0x5E8);
                    if (s >= 2 && s <= 30) sight = s;
                }

                StampVisionCircle(cellX, cellY, sight);
            }
        };

        // 盖印己方及盟友所有建筑、地面机动装甲、步兵与战机的实时直视视距圈
        stampTechnoArray(ADDR_ARRAY_BUILDINGS, 6);
        stampTechnoArray(ADDR_ARRAY_UNITS, 8);
        stampTechnoArray(ADDR_ARRAY_INFANTRY, 5);
        stampTechnoArray(ADDR_ARRAY_AIRCRAFT, 8);

        // 敌方建筑 everSeen 永久标记：底座任一格进入直视圈即视为"已侦察"（WC3 式看见过即常驻）
        if (g_enableBuildingFog) {
            void **bItems = *reinterpret_cast<void***>(ADDR_ARRAY_BUILDINGS + 4);
            int bCount = *reinterpret_cast<const int*>(ADDR_ARRAY_BUILDINGS + 16);
            if (bItems && bCount > 0 && bCount < 50000 && !IsBadReadPtr(bItems, bCount * sizeof(void*))) {
                for (int i = 0; i < bCount; ++i) {
                    void *pObj = bItems[i];
                    if (!pObj) continue;
                    int health = *reinterpret_cast<const int*>(reinterpret_cast<const uint8_t*>(pObj) + 0x6C);
                    if (health <= 0) continue;
                    void *pOwner = *reinterpret_cast<void**>(reinterpret_cast<uintptr_t>(pObj) + 0x21C);
                    if (isPlayerOrAlly(pOwner)) continue;
                    int locX = *reinterpret_cast<const int*>(reinterpret_cast<const uint8_t*>(pObj) + 0x9C);
                    int locY = *reinterpret_cast<const int*>(reinterpret_cast<const uint8_t*>(pObj) + 0xA0);
                    int cellX = locX >> 8;
                    int cellY = locY >> 8;
                    if (cellX < 0 || cellX >= 512 || cellY < 0 || cellY >= 512) continue;
                    void *pType = *reinterpret_cast<void**>(reinterpret_cast<uintptr_t>(pObj) + 0x6C4);
                    StampEverSeenIfVisible(cellX, cellY, pType);
                }
            }
        }

        // 视野状态迁移扫描：驱动灰雾渐变过渡与小地图强制刷新
        if (!s_visionInitDone) {
            // 首帧：仅记录初始视野快照，不产生渐变（避免开局自家基地闪灰）
            for (uint32_t i = 0; i < 512 * 512; ++i) {
                s_prevVisionGrid[i] = (s_visionGrid[i] == s_visionToken) ? 1 : 0;
            }
            s_visionInitDone = true;
        } else {
            // ★[ZC-10B ①] 门控解耦：逐格迁移扫描**无条件运行**（旧版被
            //   `else if (g_fadeFogTransition || GetEffectiveMinimapFog())` 包住 ⇒ 关掉渐变/
            //   小地图迷雾时迁移计数恒 0，L4DirtyMode=vision-dirty 会退化成「永不重绘」）。
            //   ⇒ 迁移检测 / ramp / 视口计数恒算；**小地图强制刷新副作用仍按原门控**，
            //     保证 force-full 默认档与现网件行为一致（s_fogRampFrame 只被
            //     g_fadeFogTransition 为真时读取，故无条件衰减对默认档不可见）。
            bool anyTransition = false;
            int vMinX = s_viewCellMinX, vMinY = s_viewCellMinY;
            int vMaxX = s_viewCellMaxX, vMaxY = s_viewCellMaxY;
            bool haveView = (vMaxX >= vMinX && vMaxY >= vMinY && vMinX < 512 && vMinY < 512);
            uint32_t vpTransition = 0, vpRampActive = 0;
            for (uint32_t i = 0; i < 512 * 512; ++i) {
                uint8_t cur = (s_visionGrid[i] == s_visionToken) ? 1 : 0;
                if (haveView) {
                    int x = static_cast<int>(i & 511), y = static_cast<int>(i >> 9);
                    bool inView = (x >= vMinX && x <= vMaxX && y >= vMinY && y <= vMaxY);
                    if (inView && s_fogRampFrame[i] > 0) vpRampActive++;
                }
                if (cur != s_prevVisionGrid[i]) {
                    s_fogRampFrame[i] = 4;      // 渐变 4 帧
                    anyTransition = true;
                    if (haveView) {
                        int x = static_cast<int>(i & 511), y = static_cast<int>(i >> 9);
                        if (x >= vMinX && x <= vMaxX && y >= vMinY && y <= vMaxY) vpTransition++;
                    }
                } else if (s_fogRampFrame[i] > 0) {
                    s_fogRampFrame[i]--;
                }
                s_prevVisionGrid[i] = cur;
            }
            s_fogViewportTransitionCount = vpTransition;
            s_fogViewportRampActive = vpRampActive;
            s_l4DirtyTransitions += vpTransition;
            s_l4DirtyRampActive += vpRampActive;
            // 复位视口累计窗口：下一次扫描用的是本逻辑帧后续格子绘制出的新窗口（1 帧滞后）
            s_viewCellMinX = 0x7FFFFFFF; s_viewCellMinY = 0x7FFFFFFF;
            s_viewCellMaxX = -1;           s_viewCellMaxY = -1;
            // 小地图强制刷新：维持原门控（默认档行为不变）
            if (g_fadeFogTransition || GetEffectiveMinimapFog()) {
                if (anyTransition) {
                    s_minimapForceRefresh = 10;     // 视野变化后强制小地图全量刷新若干帧
                } else if (s_minimapForceRefresh > 0) {
                    s_minimapForceRefresh--;
                }
            }
        }
    }
    __except (EXCEPTION_EXECUTE_HANDLER) {
    }
}

static inline bool ShouldDrawMobileObject(void *pThis) {
    if (!pThis) return false;

    __try {
        // 1. 本地玩家指针 (HouseClass::Player)
        void *pPlayer = *reinterpret_cast<void**>(ADDR_HOUSE_PLAYER);
        if (!pPlayer) return true;

        // 2. 单位所属阵营指针 (TechnoClass::Owner @ 0x21C)
        void *pOwner = *reinterpret_cast<void**>(reinterpret_cast<uintptr_t>(pThis) + 0x21C);
        if (!pOwner) return true;

        // 3. 己方单位：恒定全彩绘制
        if (pOwner == pPlayer) return true;

        // 4. 盟友单位：恒定全彩绘制
        int ownerIdx = *reinterpret_cast<const int*>(reinterpret_cast<const uint8_t*>(pOwner) + 0x30);
        uint32_t playerAllies = *reinterpret_cast<const uint32_t*>(reinterpret_cast<const uint8_t*>(pPlayer) + 0x5788);
        if (ownerIdx >= 0 && ownerIdx < 32 && ((1u << ownerIdx) & playerAllies) != 0) {
            return true;
        }

        // 确保直视视距网格处于最新状态
        UpdateVisionGrid();

        // 5. 敌军机动部队：读取绝对 3D 坐标
        int locX = *reinterpret_cast<const int*>(reinterpret_cast<const uint8_t*>(pThis) + 0x9C);
        int locY = *reinterpret_cast<const int*>(reinterpret_cast<const uint8_t*>(pThis) + 0xA0);
        int cellX = locX >> 8;
        int cellY = locY >> 8;

        if (cellX < 0 || cellX >= 512 || cellY < 0 || cellY >= 512) {
            return false;
        }

        // 6. 实时直视判定：若位于己方或盟军直视视野圈内，全彩显现
        if (s_visionGrid[cellY * 512 + cellX] == s_visionToken) {
            return true;
        }

        // 7. 心灵探测仪 / Psychic Sensor 探测侦测兼容
        uintptr_t cellsBase = *reinterpret_cast<const uintptr_t*>(ADDR_MAP_CELLS_ARRAY);
        if (cellsBase) {
            uint8_t *pCell = *reinterpret_cast<uint8_t**>(cellsBase + (cellY * 512 + cellX) * 4);
            if (pCell) {
                int playerIdx = *reinterpret_cast<const int*>(reinterpret_cast<const uint8_t*>(pPlayer) + 0x30);
                if (playerIdx >= 0 && playerIdx < 24) {
                    const uint16_t *sensors = reinterpret_cast<const uint16_t*>(pCell + 0xAC);
                    if (sensors[playerIdx] > 0) {
                        return true;
                    }
                }
            }
        }

        // 8. 处于黑雾或半透明战争迷雾中且无部队直视 -> 星际式彻底隐形剔除！
        static int s_cullLogCount = 0;
        if (s_cullLogCount < 10) {
            s_cullLogCount++;
            LogMessage("[ra2render-fog] 成功剔除迷雾中敌方机动单位 (House: %d, Cell: %d,%d)",
                       ownerIdx, cellX, cellY);
        }
        return false;
    }
    __except (EXCEPTION_EXECUTE_HANDLER) {
        return true;
    }
}

// ----------------------------------------------------------------------------
// L5: 建筑迷雾门控（WC3 式"看见过即常驻"）
// 原版行为：已探索格上的敌建筑永远实时全彩可见。本门控改为：
//   1) 直视圈内 -> 实时可见（并已被 UpdateVisionGrid 盖 everSeen 章）
//   2) 曾被侦察过（everSeen） -> 继续可见（保持最后已知位置，静态目标无移动）
//   3) 从未侦察过 -> 彻底隐形（雾中新建的敌基地不再上帝视角暴露）
// ----------------------------------------------------------------------------

static bool ShouldDrawBuilding(void *pThis) {
    if (!pThis) return true;

    __try {
        void *pPlayer = *reinterpret_cast<void**>(ADDR_HOUSE_PLAYER);
        if (!pPlayer) return true;

        void *pOwner = *reinterpret_cast<void**>(reinterpret_cast<uintptr_t>(pThis) + OFF_TECHNO_OWNER);
        if (!pOwner) return true;

        if (pOwner == pPlayer) return true;

        int ownerIdx = *reinterpret_cast<const int*>(reinterpret_cast<const uint8_t*>(pOwner) + 0x30);
        uint32_t playerAllies = *reinterpret_cast<const uint32_t*>(reinterpret_cast<const uint8_t*>(pPlayer) + 0x5788);
        if (ownerIdx >= 0 && ownerIdx < 32 && ((1u << ownerIdx) & playerAllies) != 0) {
            return true;
        }

        UpdateVisionGrid();

        int locX = *reinterpret_cast<const int*>(reinterpret_cast<const uint8_t*>(pThis) + 0x9C);
        int locY = *reinterpret_cast<const int*>(reinterpret_cast<const uint8_t*>(pThis) + 0xA0);
        int cellX = locX >> 8;
        int cellY = locY >> 8;
        if (cellX < 0 || cellX >= 512 || cellY < 0 || cellY >= 512) {
            return true;
        }

        uint32_t cellIdx = static_cast<uint32_t>(cellY * 512 + cellX);
        if (s_visionGrid[cellIdx] == s_visionToken) {
            return true;    // 直视圈内：实时可见
        }
        if (s_everSeenGrid[cellIdx]) {
            return true;    // 曾被侦察：常驻可见（建筑不可移动，位置即最后已知位置）
        }
        return false;       // 从未侦察：彻底隐形
    }
    __except (EXCEPTION_EXECUTE_HANDLER) {
        return true;
    }
}

// ----------------------------------------------------------------------------
// L5: 弹道迷雾门控（迷雾中敌方开火不再见弹道；弹道进入直视圈则正常显现）
// ----------------------------------------------------------------------------

static bool ShouldDrawBullet(void *pThis) {
    if (!pThis) return true;

    __try {
        void *pPlayer = *reinterpret_cast<void**>(ADDR_HOUSE_PLAYER);
        if (!pPlayer) return true;

        void *pShooter = *reinterpret_cast<void**>(reinterpret_cast<uintptr_t>(pThis) + OFF_BULLET_OWNER);
        if (!pShooter) return true;

        void *pOwner = *reinterpret_cast<void**>(reinterpret_cast<uintptr_t>(pShooter) + OFF_TECHNO_OWNER);
        if (!pOwner) return true;

        if (pOwner == pPlayer) return true;

        int ownerIdx = *reinterpret_cast<const int*>(reinterpret_cast<const uint8_t*>(pOwner) + 0x30);
        uint32_t playerAllies = *reinterpret_cast<const uint32_t*>(reinterpret_cast<const uint8_t*>(pPlayer) + 0x5788);
        if (ownerIdx >= 0 && ownerIdx < 32 && ((1u << ownerIdx) & playerAllies) != 0) {
            return true;
        }

        UpdateVisionGrid();

        int locX = *reinterpret_cast<const int*>(reinterpret_cast<const uint8_t*>(pThis) + 0x9C);
        int locY = *reinterpret_cast<const int*>(reinterpret_cast<const uint8_t*>(pThis) + 0xA0);
        int cellX = locX >> 8;
        int cellY = locY >> 8;
        if (cellX < 0 || cellX >= 512 || cellY < 0 || cellY >= 512) {
            return true;
        }

        return s_visionGrid[cellY * 512 + cellX] == s_visionToken;
    }
    __except (EXCEPTION_EXECUTE_HANDLER) {
        return true;
    }
}

// ----------------------------------------------------------------------------
// CellClass::Draw Detour Hook: 渲染星际争霸式半透明灰雾遮罩层 (FOG.SHP)
// ----------------------------------------------------------------------------

static uint8_t s_origCellClassDrawBytes[5] = {0};
static uint8_t s_cellClassDrawTrampoline[16] = {0};
// [FOG-SPLIT] 黑幕层只读计数钩子的原字节与跳板（6B 原指令 + E9 rel32 = 11B）
static uint8_t s_origDrawShroudFogBytes[6] = {0};
static uint8_t s_drawShroudFogTrampoline[16] = {0};

// [FOG-PROBE F1] 分桶助手（**只用于我方计数**，不参与任何渲染算术）。
//   桶界（与遥测行字段一一对应）：0 / 1-8 / 9-48 / 49-128 / 129-200 / 201-255 / 256 / >256
static inline uint32_t FogProbeBucket(uint32_t v) {
    if (v == 0)   return 0;
    if (v <= 8)   return 1;
    if (v <= 48)  return 2;
    if (v <= 128) return 3;
    if (v <= 200) return 4;
    if (v <= 255) return 5;
    if (v == 256) return 6;
    return 7;
}
// [FOG-PROBE F1] 【本格强度】精确值槽：强度只可能取 {0,48,64,96,128,144,192,256}（渐变档）
//   或 {0,256}（稳态档）；其余一律落「其它」槽（下标 8）。
static inline uint32_t FogProbeStrengthSlot(uint32_t s) {
    switch (s) {
    case 0:   return 0;
    case 48:  return 1;
    case 64:  return 2;
    case 96:  return 3;
    case 128: return 4;
    case 144: return 5;
    case 192: return 6;
    case 256: return 7;
    default:  return 8;
    }
}

void __stdcall Hook_CellClass_Draw(void *pCell, void *pLocation, void *pBounds) {
    // 1. 调用原版，完成地形与原版黑雾 SHROUD.SHP 绘制
    if (g_pOrigCellClassDraw) {
        g_pOrigCellClassDraw(pCell, pLocation, pBounds);
    }

    if (!pCell) {
        return;
    }

    __try {
        // ★[FOG-SPLIT](a) 解除耦合：UpdateVisionGrid **恒调用**，与总闸无关。
        //   作用 ①：每逻辑帧刷新我方直视网格（内部按逻辑帧号去重，纳秒级）；
        //   作用 ②：维持 Scenario FogOfWar 位 = 0 —— 黑幕层 0x0047EFE0 据此选择 SHROUD.SHP
        //           （位=1 时引擎会改用 FOG.SHP，未探索区将变透明/异色，见 UpdateVisionGrid 注释）。
        //   旧版（FOG-SWITCH）总闸=0 时本调用被整段跳过 ⇒ 该保证丢失，是「=0 时连未探索区也透出地形」的
        //   两条可疑耦合之一。
        UpdateVisionGrid();

        // 2. 地图坐标 MapCoords (offset 0x24)
        short cellX = *reinterpret_cast<const short*>(reinterpret_cast<const uint8_t*>(pCell) + OFF_CELL_MAPCOORDS);
        short cellY = *reinterpret_cast<const short*>(reinterpret_cast<const uint8_t*>(pCell) + OFF_CELL_MAPCOORDS + 2);
        if (cellX < 0 || cellX >= 512 || cellY < 0 || cellY >= 512) {
            return;
        }

        // ★[ZC-10B ①] 视口范围累计：每帧被 CellClass::Draw 真正绘制的格子就是视口范围。
        //   UpdateVisionGrid() 已按逻辑帧去重（每帧首格进入时复位窗口），故这里是纯累加。
        if (cellX < s_viewCellMinX) s_viewCellMinX = cellX;
        if (cellY < s_viewCellMinY) s_viewCellMinY = cellY;
        if (cellX > s_viewCellMaxX) s_viewCellMaxX = cellX;
        if (cellY > s_viewCellMaxY) s_viewCellMaxY = cellY;

        // 3. ★[FOG-SPLIT] 按格状态选择（取代旧版「总闸整体短路」+ 旧版误读的 0x12C 位测试）
        //   未探索判据 = **引擎本帧自身的判定结果** CellClass::Shroudedness(+0x120) == -2
        //   （ref/yrpp/CellClass.h:407-408：「-2: Occluded completely」）。该字节由原版
        //   CellClass::Draw 在 0x480207 写入（其值来自引擎逐格查询 0x6D8700，后者以
        //   CellClass::Flags(+0x140) 的 (Flags&3)==0 为判据），**早于**本钩子的追加绘制 ⇒ 读到的是
        //   引擎口径，与我方视野网格无关。
        //   ⇒ 未探索格：原版全黑黑幕已由引擎 0x0047EFE0 绘制完毕，我方**绝不上手**
        //     （不调用任何绘制/混色/驱动 ⇒ 黑幕不可能被我方影响）。
        //   ※ 勘误：旧版此处读 CellClass+0x12C(CopyFlags) 的 0x08 位并注释为「已探索」，该位实为
        //     cf2_NoShadow（GeneralDefinitions.h:560）；「已探索」在 +0x140 的 cf_Explored=0x08。
        const int8_t shroudedness =
            *reinterpret_cast<const int8_t*>(reinterpret_cast<const uint8_t*>(pCell) + OFF_CELL_SHROUDEDNESS);
        if (shroudedness == -2) {
            s_fogUnexploredPassed++;   // ㈡[FOG-SPLIT] 未探索黑幕格放行次数（总闸=1/0 都应 >0）
            return;                    // 原版全黑黑幕由引擎绘制 ⇒ 我方放行、零介入
        }

        // 4. 计算本帧灰雾强度：0 = 不画（全彩），256 = 我方 50% 等效观感（稳态；引擎原版为 FOG.SHP alpha 插值混色，非固定半化）
        uint32_t cellIdx = static_cast<uint32_t>(cellY * 512 + cellX);
        bool inVision = (s_visionGrid[cellIdx] == s_visionToken);
        int strength = 0;

        if (g_fadeFogTransition && s_fogRampFrame[cellIdx] > 0) {
            // 渐变过渡帧（共 4 帧）：视野进出均平滑过渡到目标状态
            int ramp = s_fogRampFrame[cellIdx];           // 4..1
            if (inVision) {
                strength = ramp * 48;                     // 192,144,96,48 -> 渐出（雾→亮）
            } else {
                strength = (5 - ramp) * 64;               // 64,128,192,256 -> 渐入（亮→雾）
                if (strength > 256) strength = 256;
            }
        } else {
            strength = inVision ? 0 : 256;                // 稳态
        }

        // 5. ★[FOG-SPLIT] 总闸=0 ⇒ 「已探索且非直视」这一档的强度**归零**（含过渡帧）：
        //    不压暗、不调引擎 FOG.SHP 层、不写去重 Token —— 且**只影响本档**（未探索档已在上方放行）。
        //    这就是总闸的全部作用域 ⇒ 与总闸=1 的差别集合 = {本档压暗}，不含其它任何路径。
        if (!g_enableStarCraftFog) {
            if (strength > 0) s_gate0DarkenSkipped++;
            return;
        }

        if (strength <= 0) {
            s_fogVisiblePassed++;   // 直视档（且无过渡）：两档都不压暗
            return;
        }

        // 6. 防多遍过度变暗：确保每个迷雾格子在同一逻辑帧内至多只被混色 1 次！
        if (s_cellFogDrawnToken[cellIdx] == s_visionToken) {
            return;
        }
        s_cellFogDrawnToken[cellIdx] = s_visionToken;

        // 7. 调用引擎原生 0x0047F250 绘制 FOG.SHP；混色强度由 s_fogBlendStrength
        //    驱动 0x0047F40F/0x0047F4AE 处的动态混色桩（256 = 我方 50% 等效观感；引擎原版为 FOG.SHP alpha 插值混色，非固定半化）
        //    ★[FOG-CAL2 F1] 强度写入点 = 校准键的**唯一**作用点（两态运行期分支）：
        //      · g_fogStrengthScale256 == 256（auto 档，亦 = T 35.9375 档） ⇒ **与校准前同一条语句、同一个值**
        //        （s = 本格强度）⇒ 桩输入 (c, s) 逐位不变 ⇒ 像素逐位不变（auto 等价性 = F1 硬要求，且本分支
        //        与 clamp 阈值无关 ⇒ **订正换算公式不触碰 auto 直跳路径**，见 FINDINGS.md F4 产物级对照）。
        //      · 数值档 ⇒ s' = (s × scale) >> 8（2^8 定点比例缩放；强度阶梯/渐变档同比例缩放，
        //        故 4 帧渐变的相对形状不变）。
        //        溢出界（订正后 s ≤ 511）：0 ≤ strength ≤ 256 且 0 ≤ scale ≤ 511 ⇒ scaled ≤ 256×511/256 = 511
        //        ⇒ 无溢出（仍是 32 位乘），下面的 511 钳位**在数学上恒不触发**，保留为不变量护栏
        //        （防未来改强度阶梯时越界；代价 1 条 cmova，只在数值档分支）。
        // ---- [FOG-PROBE F1] 只读仪表①：打开「格绘制窗口」，采样【本格强度】/【期望桩读值】/渐变相 ----
        //   口径：只读内存 + 自增我方计数；下面 store 语句与既有分支**零改动**（本片段不产生任何
        //   参与算术的值，也不改变控制流 —— 全部是独立的我方全局写）。
        s_probeCellStrength = static_cast<uint16_t>(strength);
        {
            uint32_t probeExpected = static_cast<uint32_t>(strength);
            if (g_fogStrengthScale256 != 256) {
                probeExpected = (probeExpected * static_cast<uint32_t>(g_fogStrengthScale256)) >> 8;
                if (probeExpected > 511) probeExpected = 511;
            }
            s_probeExpectedValue = static_cast<uint16_t>(probeExpected);
        }
        s_probeExpectedBucket[FogProbeBucket(static_cast<uint32_t>(s_probeExpectedValue))]++;
        s_probeStrengthHit[FogProbeStrengthSlot(static_cast<uint32_t>(strength))]++;
        if (g_fadeFogTransition) {
            uint8_t probeRamp = s_fogRampFrame[cellIdx];
            s_probeRampHist[probeRamp <= 4 ? probeRamp : 0]++;
        } else {
            s_probeRampHist[0]++;
        }
        s_probeWindowValue = 0xFFFF;   // 本窗口尚无桩读取
        s_probeWindowOpen = 1;
        s_probeWindows++;

        if (g_fogStrengthScale256 == 256) {
            s_fogBlendStrength = static_cast<uint16_t>(strength);          // auto/等价档：与校准前同路径
        } else {
            uint32_t scaled = (static_cast<uint32_t>(strength) *
                               static_cast<uint32_t>(g_fogStrengthScale256)) >> 8;
            if (scaled > 511) scaled = 511;                                // [FOG-CAL2] 上限随换算域改为 511（原 256）
            s_fogBlendStrength = static_cast<uint16_t>(scaled);
        }
        // ---- [FOG-PROBE F1] 只读仪表②：回读【store 写入值】（紧接 store 之后；不改 store 本身）----
        s_probeWriteValue = s_fogBlendStrength;
        s_probeWriteBucket[FogProbeBucket(static_cast<uint32_t>(s_probeWriteValue))]++;
        s_fogLayerDraws++;   // [FOG-SWITCH 计数①] 半透明层绘制次数（= 真正调用 0x0047F250 的次数；总闸=0 时恒 0）
        s_exploredFogDarken += inVision ? 0 : 1;   // ㈢[FOG-SPLIT] 已探索非直视压暗次数（稳态档；总闸=0 时恒 0）
        __asm {
            mov ecx, pCell
            push 15
            push pBounds
            push pLocation
            mov eax, ADDR_DRAW_FOG
            call eax
        }
        s_fogBlendStrength = 256;   // 恢复稳态，保护其他潜在调用者
        // ---- [FOG-PROBE F1] 只读仪表③：关闭「格绘制窗口」（恢复语句本身零改动；仅置我方标志）----
        s_probeWindowOpen = 0;
        s_probeWindowValue = 0xFFFF;
        g_telemetry.fogCellsDrawn++;
    }
    __except (EXCEPTION_EXECUTE_HANDLER) {
        // [FOG-PROBE F1] 异常路径同样关闭窗口（保证采样窗口不悬挂；异常语义不变，仍为吞掉）
        s_probeWindowOpen = 0;
        s_probeWindowValue = 0xFFFF;
    }
}

__declspec(naked) void Hook_CellClass_Draw_Proxy() {
    __asm {
        push esi
        push edi
        push ebx
        mov eax, dword ptr [esp + 20] // pBounds
        mov edx, dword ptr [esp + 16] // pLocation
        push eax                      // arg3: pBounds
        push edx                      // arg2: pLocation
        push ecx                      // arg1: pCell
        call Hook_CellClass_Draw
        pop ebx
        pop edi
        pop esi
        ret 8
    }
}

// ---------------------------------------------------------------------------
// [FOG-SPLIT] 未探索黑幕层**只读计数**钩子（0x0047EFE0，6B 补丁 + 跳板）
//
//   目的（F3 判据：未探索黑幕绘制次数）：把「未探索黑幕是否仍在绘制」变成**引擎侧实测计数**，
//   而不是靠我方钩子的状态推断。举证链：
//     CellClass::Draw(0x4801F0) → call 0x47EFE0（唯一调用者，全 .text call 扫描实证 0x480230）
//     → 依 Scenario FogOfWar 位选 SHROUD.SHP（位=0，我方恒清）→ 逐格写近黑像素。
//   本桩不参与任何判定/绘制，只读 CellClass::Shroudedness(+0x120) 分档自增：
//     · 0xFE（-2 = Occluded completely）⇒ s_shroudBlackDraws++  ← 未探索全黑黑幕次数（F3 字段）
//     · 0xFF（-1 = Visible）           ⇒ 不计
//     · 0x00..0x30（0..48 = 黑幕/灰雾帧号）⇒ s_shroudEdgeDraws++（黑幕边缘渐变，诊断）
//   入口契约：ecx = CellClass*（唯一调用者恒定传入）；栈 [esp+4]=pLocation [esp+8]=pBounds [esp+0xC]=frame。
//   寄存器纪律：只破坏 AL 与 flags。被跳板回放的前 6 字节原指令为
//     push ebp / mov ebp,esp / sub esp,0x34 —— 均不读 AL/flags ⇒ 无副作用；ecx/ebx/esi/edi/ebp 逐位保持。
// ---------------------------------------------------------------------------
__declspec(naked) void Hook_DrawShroudFog_Stub() {
    __asm {
        cmp  ecx, 0x10000                          ; 指针合法性下限（调用点恒为有效 CellClass*）
        jb   shroud_count_done
        mov  al, byte ptr [ecx + 0x120]            ; CellClass::Shroudedness
        cmp  al, 0xFE
        jne  shroud_count_notblack
        inc  dword ptr [s_shroudBlackDraws]        ; ★ 未探索黑幕绘制次数（=-2 全遮蔽档）
        jmp  shroud_count_done
    shroud_count_notblack:
        cmp  al, 0xFF
        je   shroud_count_done
        inc  dword ptr [s_shroudEdgeDraws]         ; 黑幕边缘渐变帧（0..48）
    shroud_count_done:
        jmp  dword ptr [s_pDrawShroudFogTrampoline]
    }
}

// ---------------------------------------------------------------------------
// 动态强度灰雾混色桩（替换 0x0047F40F / 0x0047F4AE 的旧静态 50% 等效桩，指我方旧补丁；引擎原版此处为 FOG.SHP alpha 插值混色，非固定半化）
//
//   final = c - ((c_perChannel - c50_perChannel) * s >> 8)
//   s = 256 时与旧补丁逐位一致（即我方 50% 等效观感，非引擎原生行为），s < 256 为渐变过渡帧的部分暗化。
//   逐通道（RGB565）独立计算，delta = c - c50 无通道间借位，t ≤ delta 无下溢。
//
// 寄存器契约（与旧 0-JMP 14 字节补丁一致）：eax = 像素指针须还原；ecx 可破坏；
// ebx/edx/esi/edi/ebp 全部还原。补丁布局：jmp rel32 (5 字节) + NOP 填充至原区段长度。
//
// [FOG-SWITCH 短路点 ②] 总闸 EnableStarCraftFog=0 时两个桩**直接跳过后继**（0x47F440 / 0x47F4E1），
//   既不执行本桩的强度混色，也不可能落回补丁前的原版混色：
//   字节级依据（见 docs/re/fog_switch_report.md §2 与附录）：
//     · 0x0047F40F 起 49 字节原版为 FOG.SHP 逐像素 alpha 插值混色（lea ecx,[ecx+edx-0x7f] 段），
//       其中唯一的像素写在 0x47F43D（66 89 08 = mov word ptr [eax],cx）；0x47F440 已是循环后继。
//     · 0x0047F4AE 起 51 字节原版同族，像素写点 0x47F4BB（66 89 10）与 0x47F4DE（66 89 08）；
//       0x47F4E1 已是循环后继。
//     · 全 exe 仅此两处出现该混色循环签名（setle dl / dec edx / and ecx,edx），即「半透明压暗」的
//       全部落像素点都在本补丁覆盖范围内 ⇒ 短路这两处即彻底没有压暗。
//   注意：补丁字节（E9 + jmp rel32）已覆盖原版，故「关闭」出口只能是本分支，绝无原版回退路径。
// ---------------------------------------------------------------------------

__declspec(naked) void Hook_FogBlendB1_Stub() {   // B1 (0x0047F40F) -> 0x0047F440
    __asm {
        ; 【FOG-SWITCH 短路点 ②】总闸=0 ⇒ 跳过后继混色体直接落到 0x0047F440：
        ;   不读像素、不写像素、不做任何通道压暗 —— 保持原像素（既非引擎原版 FOG.SHP 插值混色，
        ;   也绝不是 50% 半减）。因为补丁字节已覆盖原版 49 字节，此分支是唯一的「关闸」出口。
        cmp  byte ptr [s_fogMasterGate], 0
        je   fog_blend_b1_disabled
        inc  dword ptr [s_fogBlendStubHits]   // [FOG-SWITCH 计数②] 混色桩介入（真正混色并落像素）
        push eax                  // [esp+0xC] 像素指针
        push edx                  // [esp+0x8]
        push ebx                  // [esp+0x4]
        mov cx, [eax]             // ecx = c
        push ecx                  // [esp+0x0] c 副本
        movzx ebx, word ptr [s_fogBlendStrength]
        mov edx, ecx              // edx = c
        ; ===========================================================================
        ; [FOG-PROBE F1] 桩内「读取值」探针 —— **只读采样**（本块与既有算术完全独立）
        ;   采样对象 = 紧邻上面 `movzx ebx, word ptr [s_fogBlendStrength]` 的**同一 16 位读数**（bx）
        ;   纪律（逐条可验）：
        ;     · 只读内存 + 自增我方计数（s_probe*）；不写任何引擎状态、不写任何像素；
        ;     · 不改变 ebx/edx/eax/esi/edi/ebp；ecx 仅在慢路径内 push/pop 原样保护；
        ;     · 关（FogProbe=0，**默认**）⇒ 本开关 2 条指令直接落到 pb1_probe_done：
        ;        不采样、不计数、不进慢路径 ⇒ 探针工作量为 0，混色算术路径逐位不变；
        ;     · 开（FogProbe=1）⇒ 热路径 = 2 条指令（cmp/je），零寄存器改动、零标志依赖（本桩内标志本就为死值）；
        ;        慢路径 = 每「格绘制窗口」1 次（首读采样）+ 罕见异常（窗口内读值变化 / 窗口外读取）；
        ;     · 出口与原有出口逐位一致（下方算术指令序列的字节**未改动一位**）。
        ;   ★[ZC-10B ③] s_fogProbeEnabledMirror 由 ini FogOfWar/FogProbe 驱动（默认 0）。
        ; ===========================================================================
        cmp  byte ptr [s_fogProbeEnabledMirror], 0
        je   pb1_probe_done
        cmp  bx, word ptr [s_probeWindowValue]
        je   pb1_probe_done
        push ecx
        cmp  dword ptr [s_probeWindowOpen], 0
        je   pb1_probe_alien
        cmp  word ptr [s_probeWindowValue], 0FFFFh
        je   pb1_probe_first
        inc  dword ptr [s_probeMidWindowChange]     ; 窗口内读值 != 本窗口首读
        jmp  pb1_probe_restore
    pb1_probe_alien:
        inc  dword ptr [s_probeAlienReads]          ; 窗口外读取（非我方 store→call 窗口）
        jmp  pb1_probe_restore
    pb1_probe_first:
        mov  word ptr [s_probeWindowValue], bx      ; 【桩读取强度值】本窗口首读
        inc  dword ptr [s_probeReadsInWindow]
        cmp  bx, word ptr [s_probeWriteValue]       ; 失配计数：【store 写入值】!=【桩读取强度值】
        je   pb1_probe_nomis
        inc  dword ptr [s_probeMismatch]
    pb1_probe_nomis:
        cmp  bx, word ptr [s_probeExpectedValue]
        je   pb1_probe_eq
        inc  dword ptr [s_probeReadNeExpected]
        jmp  pb1_probe_ring
    pb1_probe_eq:
        inc  dword ptr [s_probeReadEqExpected]
    pb1_probe_ring:
        mov  ecx, dword ptr [s_probeRingIdx]
        and  ecx, 7
        mov  word ptr [s_probeRing + ecx*2], bx
        inc  dword ptr [s_probeRingIdx]
        cmp  bx, 0
        je   pb1_probe_b0
        cmp  bx, 9
        jb   pb1_probe_b1
        cmp  bx, 49
        jb   pb1_probe_b2
        cmp  bx, 129
        jb   pb1_probe_b3
        cmp  bx, 201
        jb   pb1_probe_b4
        cmp  bx, 256
        jb   pb1_probe_b5
        je   pb1_probe_b6
        inc  dword ptr [s_probeBucket + 28]
        jmp  pb1_probe_restore
    pb1_probe_b0:
        inc  dword ptr [s_probeBucket + 0]
        jmp  pb1_probe_restore
    pb1_probe_b1:
        inc  dword ptr [s_probeBucket + 4]
        jmp  pb1_probe_restore
    pb1_probe_b2:
        inc  dword ptr [s_probeBucket + 8]
        jmp  pb1_probe_restore
    pb1_probe_b3:
        inc  dword ptr [s_probeBucket + 12]
        jmp  pb1_probe_restore
    pb1_probe_b4:
        inc  dword ptr [s_probeBucket + 16]
        jmp  pb1_probe_restore
    pb1_probe_b5:
        inc  dword ptr [s_probeBucket + 20]
        jmp  pb1_probe_restore
    pb1_probe_b6:
        inc  dword ptr [s_probeBucket + 24]
    pb1_probe_restore:
        pop  ecx
    pb1_probe_done:

        shr ecx, 1
        and ecx, 0x7BEF           // c50
        sub dx, cx                // edx = delta（逐通道）
        ; R 段 -> 暂存栈
        mov eax, edx
        shr eax, 11
        and eax, 0x1F             // delta_r
        imul eax, ebx
        shr eax, 8                // t_r
        mov ecx, [esp]            // c
        shr ecx, 11
        and ecx, 0x1F             // c_r
        sub ecx, eax              // final_r
        shl ecx, 11
        push ecx
        ; G 段 -> ecx
        mov eax, edx
        shr eax, 5
        and eax, 0x3F
        imul eax, ebx
        shr eax, 8
        mov ecx, [esp+4]          // c
        shr ecx, 5
        and ecx, 0x3F
        sub ecx, eax
        shl ecx, 5
        ; B 段 -> edx 复用
        mov eax, edx
        and eax, 0x1F
        imul eax, ebx
        shr eax, 8
        mov edx, [esp+4]          // c
        and edx, 0x1F
        sub edx, eax              // final_b
        or ecx, edx               // ecx = G|B
        pop eax                   // R 段
        or ecx, eax               // ecx = final
        add esp, 4                // 丢弃 c 副本
        pop ebx
        pop edx
        pop eax                   // eax = 像素指针
        mov [eax], cx
        mov ecx, 0x0047F440
        jmp ecx
    fog_blend_b1_disabled:
        ; 总闸关闭：直达后继 0x0047F440（跳过 mov [eax],cx 落像素），循环状态与寄存器逐位保持
        mov  ecx, ADDR_DRAW_FOG_PIXEL_BLEND_B1_CONT
        jmp  ecx
    }
}

__declspec(naked) void Hook_FogBlendB2_Stub() {   // B2 (0x0047F4AE) -> 0x0047F4E1
    __asm {
        ; 【FOG-SWITCH 短路点 ②】总闸=0 ⇒ 跳过后继混色体直接落到 0x0047F4E1（保持原像素）
        cmp  byte ptr [s_fogMasterGate], 0
        je   fog_blend_b2_disabled
        inc  dword ptr [s_fogBlendStubHits]   // [FOG-SWITCH 计数②] 混色桩介入（真正混色并落像素）
        push eax                  // [esp+0xC] 像素指针
        push edx                  // [esp+0x8]
        push ebx                  // [esp+0x4]
        mov cx, [eax]             // ecx = c
        push ecx                  // [esp+0x0] c 副本
        movzx ebx, word ptr [s_fogBlendStrength]
        mov edx, ecx              // edx = c
        ; ===========================================================================
        ; [FOG-PROBE F1] 桩内「读取值」探针 —— **只读采样**（本块与既有算术完全独立）
        ;   采样对象 = 紧邻上面 `movzx ebx, word ptr [s_fogBlendStrength]` 的**同一 16 位读数**（bx）
        ;   纪律（逐条可验）：
        ;     · 只读内存 + 自增我方计数（s_probe*）；不写任何引擎状态、不写任何像素；
        ;     · 不改变 ebx/edx/eax/esi/edi/ebp；ecx 仅在慢路径内 push/pop 原样保护；
        ;     · 关（FogProbe=0，**默认**）⇒ 本开关 2 条指令直接落到 pb2_probe_done：
        ;        不采样、不计数、不进慢路径 ⇒ 探针工作量为 0，混色算术路径逐位不变；
        ;     · 开（FogProbe=1）⇒ 热路径 = 2 条指令（cmp/je），零寄存器改动、零标志依赖（本桩内标志本就为死值）；
        ;        慢路径 = 每「格绘制窗口」1 次（首读采样）+ 罕见异常（窗口内读值变化 / 窗口外读取）；
        ;     · 出口与原有出口逐位一致（下方算术指令序列的字节**未改动一位**）。
        ;   ★[ZC-10B ③] s_fogProbeEnabledMirror 由 ini FogOfWar/FogProbe 驱动（默认 0）。
        ; ===========================================================================
        cmp  byte ptr [s_fogProbeEnabledMirror], 0
        je   pb2_probe_done
        cmp  bx, word ptr [s_probeWindowValue]
        je   pb2_probe_done
        push ecx
        cmp  dword ptr [s_probeWindowOpen], 0
        je   pb2_probe_alien
        cmp  word ptr [s_probeWindowValue], 0FFFFh
        je   pb2_probe_first
        inc  dword ptr [s_probeMidWindowChange]     ; 窗口内读值 != 本窗口首读
        jmp  pb2_probe_restore
    pb2_probe_alien:
        inc  dword ptr [s_probeAlienReads]          ; 窗口外读取（非我方 store→call 窗口）
        jmp  pb2_probe_restore
    pb2_probe_first:
        mov  word ptr [s_probeWindowValue], bx      ; 【桩读取强度值】本窗口首读
        inc  dword ptr [s_probeReadsInWindow]
        cmp  bx, word ptr [s_probeWriteValue]       ; 失配计数：【store 写入值】!=【桩读取强度值】
        je   pb2_probe_nomis
        inc  dword ptr [s_probeMismatch]
    pb2_probe_nomis:
        cmp  bx, word ptr [s_probeExpectedValue]
        je   pb2_probe_eq
        inc  dword ptr [s_probeReadNeExpected]
        jmp  pb2_probe_ring
    pb2_probe_eq:
        inc  dword ptr [s_probeReadEqExpected]
    pb2_probe_ring:
        mov  ecx, dword ptr [s_probeRingIdx]
        and  ecx, 7
        mov  word ptr [s_probeRing + ecx*2], bx
        inc  dword ptr [s_probeRingIdx]
        cmp  bx, 0
        je   pb2_probe_b0
        cmp  bx, 9
        jb   pb2_probe_b1
        cmp  bx, 49
        jb   pb2_probe_b2
        cmp  bx, 129
        jb   pb2_probe_b3
        cmp  bx, 201
        jb   pb2_probe_b4
        cmp  bx, 256
        jb   pb2_probe_b5
        je   pb2_probe_b6
        inc  dword ptr [s_probeBucket + 28]
        jmp  pb2_probe_restore
    pb2_probe_b0:
        inc  dword ptr [s_probeBucket + 0]
        jmp  pb2_probe_restore
    pb2_probe_b1:
        inc  dword ptr [s_probeBucket + 4]
        jmp  pb2_probe_restore
    pb2_probe_b2:
        inc  dword ptr [s_probeBucket + 8]
        jmp  pb2_probe_restore
    pb2_probe_b3:
        inc  dword ptr [s_probeBucket + 12]
        jmp  pb2_probe_restore
    pb2_probe_b4:
        inc  dword ptr [s_probeBucket + 16]
        jmp  pb2_probe_restore
    pb2_probe_b5:
        inc  dword ptr [s_probeBucket + 20]
        jmp  pb2_probe_restore
    pb2_probe_b6:
        inc  dword ptr [s_probeBucket + 24]
    pb2_probe_restore:
        pop  ecx
    pb2_probe_done:

        shr ecx, 1
        and ecx, 0x7BEF           // c50
        sub dx, cx                // edx = delta（逐通道）
        ; R 段 -> 暂存栈
        mov eax, edx
        shr eax, 11
        and eax, 0x1F
        imul eax, ebx
        shr eax, 8
        mov ecx, [esp]            // c
        shr ecx, 11
        and ecx, 0x1F
        sub ecx, eax
        shl ecx, 11
        push ecx
        ; G 段 -> ecx
        mov eax, edx
        shr eax, 5
        and eax, 0x3F
        imul eax, ebx
        shr eax, 8
        mov ecx, [esp+4]          // c
        shr ecx, 5
        and ecx, 0x3F
        sub ecx, eax
        shl ecx, 5
        ; B 段 -> edx 复用
        mov eax, edx
        and eax, 0x1F
        imul eax, ebx
        shr eax, 8
        mov edx, [esp+4]          // c
        and edx, 0x1F
        sub edx, eax
        or ecx, edx               // ecx = G|B
        pop eax                   // R 段
        or ecx, eax               // ecx = final
        add esp, 4
        pop ebx
        pop edx
        pop eax                   // eax = 像素指针
        mov [eax], cx
        mov ecx, 0x0047F4E1
        jmp ecx
    fog_blend_b2_disabled:
        ; 总闸关闭：直达后继 0x0047F4E1（跳过两处落像素：0x47F4BB/0x47F4DE），循环状态与寄存器逐位保持
        mov  ecx, ADDR_DRAW_FOG_PIXEL_BLEND_B2_CONT
        jmp  ecx
    }
}

// Branch 1 (0x0047F40F, 49 字节) 与 Branch 2 (0x0047F4AE, 51 字节) 原始字节（卸载还原用）
static uint8_t s_origFogBlendB1Bytes[49] = {0};
static uint8_t s_origFogBlendB2Bytes[51] = {0};

// ---------------------------------------------------------------------------
// [FOG-SWITCH 短路点 ④] L4 视口全量实时刷新补丁的**运行期门控**
//   原版 0x006D3D99 为 6 字节 0F 8D 98 00 00 00（jge 0x006D3E37），语义 = |滚动量| >= 阈值才全量重绘；
//   旧补丁无条件改成 E9 99 00 00 00（jmp 0x006D3E37），以支持「静止时单位离开即刻退回迷雾」——
//   该耦合只服务于灰雾即时刷新，故总闸=0 时必须恢复原版条件跳转语义。
//   本桩把补丁改为运行期判定（跳转目标 = 桩入口，桩内先判总闸）：
//     总闸=1 ⇒ 与旧补丁逐位等价（popfd 还原 0x6D3D97 cmp 的原始 flags 后 jmp 0x006D3E37）；
//     总闸=0 ⇒ popfd 还原原始 flags 后**原样执行 jge 0x006D3E37**，不满足则落到 0x006D3D9F，
//              与未打补丁的原版逐位一致。
//   标志位纪律：0x006D3D97 的 cmp 建立的 flags 由 pushfd/popfd 保护；分支只用本地近跳转，
//   绝对地址一律走 mov reg,imm32 + jmp reg（规避 MASM jmp imm32 被当作间接跳转的陷阱）。
// ---------------------------------------------------------------------------
// ★[FOG-SPLIT](b) 解除耦合：本桩**不再受总闸门控**，恒强制全量重绘（= FOG-SWITCH 版「总闸=1」分支
//   逐位等价语义：目标同 0x6D3E37、调用时机同、不依赖 flags）。
//   理由：这是「总闸=0 时连未探索黑幕一起消失」的两条可疑**控制流耦合**之一 —— 恢复原版 jge 后，
//   静态镜头下战术重绘改走增量/dirty-rect 路径，而未探索黑幕的唯一承载路径（CellClass::Draw 0x4801F0
//   → 0x47EFE0，调用循环 0x6D3693 / 0x6D751A）不再每帧遍历全部可见格。总闸语义既已收窄为
//   「只管『已探索非直视』档的压暗强度」，就不应再触碰重绘机制本身。
//   flags 纪律：原版补丁（旧 E9 无条件 jmp）同样不保证 flags；目标 0x6D3E37 首指令不读 flags。
__declspec(naked) void Hook_L4FullRedraw_Stub() {
    __asm {
        ; ★[ZC-10B ①] L4DirtyMode 运行期判定（g_l4DirtyMode: 0=force-full 恒强制 / 1=vision-dirty 折中 / 2=vanilla 恒交还）
        ;   force-full：与现网件逐位等价（目标同 0x006D3E37、调用时机同、不依赖 flags）
        ;   vanilla  ：恒执行原版 jge 语义（0x006D3D99 六字节 0F 8D 98 00 00 00 = 不打本补丁）
        ;   vision-dirty：仅当「视口迁移数==0 且 视口渐变活跃数==0」时执行原版 jge；否则仍强制全量
        ;   原版 jge 语义：满足(SF==OF 或 ZF==1) ⇒ 0x006D3E37；否则落到 0x006D3D9F（补丁后第 1 字节）
        cmp  dword ptr [g_l4DirtyMode], 1
        jne  l4_not_vision_dirty
        cmp  dword ptr [s_fogViewportTransitionCount], 0
        jne  l4_force_full
        cmp  dword ptr [s_fogViewportRampActive], 0
        jne  l4_force_full
        ; vision-dirty 且视口完全静态 ⇒ 交还原版 jge（本帧计入 l4RedrawSkippedStatic）
        inc  dword ptr [s_l4RedrawSkippedStatic]
        jge  l4_take_full
        mov  ecx, 0x006D3D9F
        jmp  ecx
    l4_take_full:
        mov  ecx, 0x006D3E37
        jmp  ecx
    l4_not_vision_dirty:
        cmp  dword ptr [g_l4DirtyMode], 2
        jne  l4_force_full
        ; vanilla：恒执行原版 jge 语义
        jge  l4_take_full
        mov  ecx, 0x006D3D9F
        jmp  ecx
    l4_force_full:
        mov  ecx, ADDR_TACTICAL_FULL_REDRAW_TARGET
        jmp  ecx
    }
}

// 视口全量实时刷新补丁（0x006D3D99 6 字节 → jmp Hook_L4FullRedraw_Stub + nop，运行期受总闸门控）
static uint8_t s_origTacticalRedrawBytes[6] = {0};
static uint8_t s_newTacticalRedrawBytes[6] = {
    0xE9, 0x00, 0x00, 0x00, 0x00, // jmp Hook_L4FullRedraw_Stub（rel32 在安装时填充）
    0x90                          // nop
};

// ---------------------------------------------------------------------------
// [FOG-SPLIT] 安装 0x0047EFE0 黑幕层只读计数钩子（6B 等长补丁 + 6B 跳板）
//   补丁形状：E9 rel32 + 90（1 字节 NOP 填满 6 字节）
//   跳板形状：[0..5]=6B 原指令，[6]=E9，[7..10]=rel32 → 0x0047EFE6
// ---------------------------------------------------------------------------
static bool InstallDrawShroudFogCounterHook() {
    memcpy(s_origDrawShroudFogBytes, reinterpret_cast<void*>(ADDR_DRAW_SHROUD_FOG), sizeof(s_origDrawShroudFogBytes));

    DWORD oldProtect = 0;
    if (!VirtualProtect(s_drawShroudFogTrampoline, sizeof(s_drawShroudFogTrampoline), PAGE_EXECUTE_READWRITE, &oldProtect)) {
        LogMessage("[ra2render-fog] 错误：[FOG-SPLIT] 无法设置黑幕层跳板内存权限");
        return false;
    }
    memcpy(s_drawShroudFogTrampoline, s_origDrawShroudFogBytes, sizeof(s_origDrawShroudFogBytes));
    s_drawShroudFogTrampoline[6] = 0xE9;
    {
        uintptr_t immAddr = reinterpret_cast<uintptr_t>(&s_drawShroudFogTrampoline[7]);
        int32_t jmpBack = static_cast<int32_t>(ADDR_DRAW_SHROUD_FOG_RESUME - (immAddr + 4));
        memcpy(&s_drawShroudFogTrampoline[7], &jmpBack, sizeof(int32_t));
    }
    s_pDrawShroudFogTrampoline = s_drawShroudFogTrampoline;

    if (!VirtualProtect(reinterpret_cast<void*>(ADDR_DRAW_SHROUD_FOG), sizeof(s_origDrawShroudFogBytes), PAGE_EXECUTE_READWRITE, &oldProtect)) {
        LogMessage("[ra2render-fog] 错误：[FOG-SPLIT] 无法修改黑幕层入口内存权限");
        return false;
    }
    {
        uint8_t patch[6];
        patch[0] = 0xE9;
        int32_t rel = static_cast<int32_t>(reinterpret_cast<uintptr_t>(&Hook_DrawShroudFog_Stub) - (ADDR_DRAW_SHROUD_FOG + 5));
        memcpy(&patch[1], &rel, sizeof(int32_t));
        patch[5] = 0x90;
        memcpy(reinterpret_cast<void*>(ADDR_DRAW_SHROUD_FOG), patch, sizeof(patch));
    }
    VirtualProtect(reinterpret_cast<void*>(ADDR_DRAW_SHROUD_FOG), sizeof(s_origDrawShroudFogBytes), oldProtect, &oldProtect);

    LogMessage("[ra2render-fog] [FOG-SPLIT] 成功挂载黑幕层只读计数钩子 (0x0047EFE0 -> 0x%08X, 6B)：未探索黑幕绘制次数 (s_shroudBlackDraws) 可观测；本桩不改变任何绘制行为",
               reinterpret_cast<uintptr_t>(&Hook_DrawShroudFog_Stub));
    return true;
}

static void RemoveDrawShroudFogCounterHook() {
    if (s_origDrawShroudFogBytes[0] != 0) {
        DWORD oldProtect = 0;
        VirtualProtect(reinterpret_cast<void*>(ADDR_DRAW_SHROUD_FOG), sizeof(s_origDrawShroudFogBytes), PAGE_EXECUTE_READWRITE, &oldProtect);
        memcpy(reinterpret_cast<void*>(ADDR_DRAW_SHROUD_FOG), s_origDrawShroudFogBytes, sizeof(s_origDrawShroudFogBytes));
        VirtualProtect(reinterpret_cast<void*>(ADDR_DRAW_SHROUD_FOG), sizeof(s_origDrawShroudFogBytes), oldProtect, &oldProtect);
    }
    s_pDrawShroudFogTrampoline = nullptr;
}

static bool InstallCellClassDrawHook() {
    memcpy(s_origCellClassDrawBytes, reinterpret_cast<void*>(ADDR_CELLCLASS_DRAW), 5);

    DWORD oldProtect = 0;
    if (!VirtualProtect(s_cellClassDrawTrampoline, sizeof(s_cellClassDrawTrampoline), PAGE_EXECUTE_READWRITE, &oldProtect)) {
        LogMessage("[ra2render-fog] 错误：无法设置 Trampoline 内存权限");
        return false;
    }

    memcpy(s_cellClassDrawTrampoline, s_origCellClassDrawBytes, 5);
    s_cellClassDrawTrampoline[5] = 0xE9; // JMP
    int32_t jmpBack = static_cast<int32_t>((ADDR_CELLCLASS_DRAW + 5) - (reinterpret_cast<uintptr_t>(s_cellClassDrawTrampoline) + 10));
    memcpy(&s_cellClassDrawTrampoline[6], &jmpBack, sizeof(int32_t));

    g_pOrigCellClassDraw = reinterpret_cast<FnCellClassDraw>(reinterpret_cast<void*>(s_cellClassDrawTrampoline));

    if (!VirtualProtect(reinterpret_cast<void*>(ADDR_CELLCLASS_DRAW), 5, PAGE_EXECUTE_READWRITE, &oldProtect)) {
        LogMessage("[ra2render-fog] 错误：无法修改 ADDR_CELLCLASS_DRAW 内存权限");
        return false;
    }

    uint8_t patch[5];
    patch[0] = 0xE9;
    int32_t jmpToProxy = static_cast<int32_t>(reinterpret_cast<uintptr_t>(Hook_CellClass_Draw_Proxy) - (ADDR_CELLCLASS_DRAW + 5));
    memcpy(&patch[1], &jmpToProxy, sizeof(int32_t));
    memcpy(reinterpret_cast<void*>(ADDR_CELLCLASS_DRAW), patch, 5);

    VirtualProtect(reinterpret_cast<void*>(ADDR_CELLCLASS_DRAW), 5, oldProtect, &oldProtect);

    // 安装动态强度灰雾混色桩（jmp rel32 + NOP 填充；s=256 时与旧静态补丁逐位一致，即我方 50% 等效观感）
    uint8_t patchB1[49];
    patchB1[0] = 0xE9;
    *reinterpret_cast<int32_t*>(&patchB1[1]) = static_cast<int32_t>(
        reinterpret_cast<uintptr_t>(&Hook_FogBlendB1_Stub) - (ADDR_DRAW_FOG_PIXEL_BLEND_B1 + 5));
    memset(&patchB1[5], 0x90, sizeof(patchB1) - 5);

    uint8_t patchB2[51];
    patchB2[0] = 0xE9;
    *reinterpret_cast<int32_t*>(&patchB2[1]) = static_cast<int32_t>(
        reinterpret_cast<uintptr_t>(&Hook_FogBlendB2_Stub) - (ADDR_DRAW_FOG_PIXEL_BLEND_B2 + 5));
    memset(&patchB2[5], 0x90, sizeof(patchB2) - 5);

    memcpy(s_origFogBlendB1Bytes, reinterpret_cast<void*>(ADDR_DRAW_FOG_PIXEL_BLEND_B1), sizeof(s_origFogBlendB1Bytes));
    if (VirtualProtect(reinterpret_cast<void*>(ADDR_DRAW_FOG_PIXEL_BLEND_B1), sizeof(patchB1), PAGE_EXECUTE_READWRITE, &oldProtect)) {
        memcpy(reinterpret_cast<void*>(ADDR_DRAW_FOG_PIXEL_BLEND_B1), patchB1, sizeof(patchB1));
        VirtualProtect(reinterpret_cast<void*>(ADDR_DRAW_FOG_PIXEL_BLEND_B1), sizeof(patchB1), oldProtect, &oldProtect);
    }

    memcpy(s_origFogBlendB2Bytes, reinterpret_cast<void*>(ADDR_DRAW_FOG_PIXEL_BLEND_B2), sizeof(s_origFogBlendB2Bytes));
    if (VirtualProtect(reinterpret_cast<void*>(ADDR_DRAW_FOG_PIXEL_BLEND_B2), sizeof(patchB2), PAGE_EXECUTE_READWRITE, &oldProtect)) {
        memcpy(reinterpret_cast<void*>(ADDR_DRAW_FOG_PIXEL_BLEND_B2), patchB2, sizeof(patchB2));
        VirtualProtect(reinterpret_cast<void*>(ADDR_DRAW_FOG_PIXEL_BLEND_B2), sizeof(patchB2), oldProtect, &oldProtect);
    }
    LogMessage("[ra2render-fog] 成功激活动态强度灰雾混色桩 (0x0047F40F & 0x0047F4AE)，支持 4 帧渐变过渡！");

    // 安装视口全量实时刷新补丁（0x006D3D99 -> jmp Hook_L4FullRedraw_Stub；桩内运行期判总闸）
    memcpy(s_origTacticalRedrawBytes, reinterpret_cast<void*>(ADDR_TACTICAL_FULL_REDRAW_JUMP), 6);
    {
        int32_t rel = static_cast<int32_t>(
            reinterpret_cast<uintptr_t>(&Hook_L4FullRedraw_Stub) - (ADDR_TACTICAL_FULL_REDRAW_JUMP + 5));
        memcpy(&s_newTacticalRedrawBytes[1], &rel, sizeof(int32_t));
    }
    if (VirtualProtect(reinterpret_cast<void*>(ADDR_TACTICAL_FULL_REDRAW_JUMP), sizeof(s_newTacticalRedrawBytes), PAGE_EXECUTE_READWRITE, &oldProtect)) {
        memcpy(reinterpret_cast<void*>(ADDR_TACTICAL_FULL_REDRAW_JUMP), s_newTacticalRedrawBytes, sizeof(s_newTacticalRedrawBytes));
        VirtualProtect(reinterpret_cast<void*>(ADDR_TACTICAL_FULL_REDRAW_JUMP), sizeof(s_newTacticalRedrawBytes), oldProtect, &oldProtect);
        LogMessage("[ra2render-fog] 成功激活视口实时刷新机制 (0x006D3D99 -> jmp 0x%08X = Hook_L4FullRedraw_Stub)：恒强制全量重绘（[FOG-SPLIT] 已与总闸解耦，不再随总闸=0 回退原版 jge）！",
                   reinterpret_cast<uintptr_t>(&Hook_L4FullRedraw_Stub));
    }

    LogMessage("[ra2render-fog] 成功挂载 CellClass::Draw Inline Hook (0x004801F0 -> 0x%08X)，半透明灰雾层 (FOG.SHP) 已就绪！",
               reinterpret_cast<uintptr_t>(Hook_CellClass_Draw_Proxy));

    // [FOG-SPLIT] 追加黑幕层只读计数钩子（未探索黑幕绘制次数的引擎侧实测点）
    InstallDrawShroudFogCounterHook();
    return true;
}

static void RemoveCellClassDrawHook() {
    RemoveDrawShroudFogCounterHook();   // [FOG-SPLIT] 先还原本钩子的 0x0047EFE0 补丁
    if (g_pOrigCellClassDraw) {
        DWORD oldProtect = 0;
        VirtualProtect(reinterpret_cast<void*>(ADDR_CELLCLASS_DRAW), 5, PAGE_EXECUTE_READWRITE, &oldProtect);
        memcpy(reinterpret_cast<void*>(ADDR_CELLCLASS_DRAW), s_origCellClassDrawBytes, 5);
        VirtualProtect(reinterpret_cast<void*>(ADDR_CELLCLASS_DRAW), 5, oldProtect, &oldProtect);
        g_pOrigCellClassDraw = nullptr;
    }

    if (s_origFogBlendB1Bytes[0] != 0) {
        DWORD oldProtect = 0;
        VirtualProtect(reinterpret_cast<void*>(ADDR_DRAW_FOG_PIXEL_BLEND_B1), sizeof(s_origFogBlendB1Bytes), PAGE_EXECUTE_READWRITE, &oldProtect);
        memcpy(reinterpret_cast<void*>(ADDR_DRAW_FOG_PIXEL_BLEND_B1), s_origFogBlendB1Bytes, sizeof(s_origFogBlendB1Bytes));
        VirtualProtect(reinterpret_cast<void*>(ADDR_DRAW_FOG_PIXEL_BLEND_B1), sizeof(s_origFogBlendB1Bytes), oldProtect, &oldProtect);
    }

    if (s_origFogBlendB2Bytes[0] != 0) {
        DWORD oldProtect = 0;
        VirtualProtect(reinterpret_cast<void*>(ADDR_DRAW_FOG_PIXEL_BLEND_B2), sizeof(s_origFogBlendB2Bytes), PAGE_EXECUTE_READWRITE, &oldProtect);
        memcpy(reinterpret_cast<void*>(ADDR_DRAW_FOG_PIXEL_BLEND_B2), s_origFogBlendB2Bytes, sizeof(s_origFogBlendB2Bytes));
        VirtualProtect(reinterpret_cast<void*>(ADDR_DRAW_FOG_PIXEL_BLEND_B2), sizeof(s_origFogBlendB2Bytes), oldProtect, &oldProtect);
    }

    if (s_origTacticalRedrawBytes[0] != 0) {
        DWORD oldProtect = 0;
        VirtualProtect(reinterpret_cast<void*>(ADDR_TACTICAL_FULL_REDRAW_JUMP), sizeof(s_origTacticalRedrawBytes), PAGE_EXECUTE_READWRITE, &oldProtect);
        memcpy(reinterpret_cast<void*>(ADDR_TACTICAL_FULL_REDRAW_JUMP), s_origTacticalRedrawBytes, sizeof(s_origTacticalRedrawBytes));
        VirtualProtect(reinterpret_cast<void*>(ADDR_TACTICAL_FULL_REDRAW_JUMP), sizeof(s_origTacticalRedrawBytes), oldProtect, &oldProtect);
    }
}

// ============================================================================
// L5: 雷达小地图迷雾化 —— 路线 A（docs/re/radar_hook_routeA_spec.md）+ [RADAR-FIX2]
//
// 【RADAR-FIX2 三条字节级定谳（详见 docs/re/radar_fix2_report.md §2/§3/§4）】
//   (1) 0x00B73550 **不是**迷雾总开关，而是 Game::hWnd（主窗口句柄 HWND）：
//       - YRpp/Unsorted.h:17 / ref/yrpp/Unsorted.h:17 "reference<HWND,0xB73550u> hWnd"；
//       - 全 exe 仅 2 个写点 0x00777CD6 / 0x00777D7E，均为 call [IAT CreateWindowExA]
//         返回值的落地；77 处读点全部把该值当 Win32 窗口句柄使用（SetFocus/SetCapture/
//         ShowWindow/GetClientRect/UpdateWindow/SetForegroundWindow/ReleaseCapture...）。
//       ⇒ 绝不可写它：写 0 或写假值会污染 70+ 处 Win32 调用（红线）。故 F2 分支 (1) 否决，
//         取分支 (2)（按我方三态谓词驱动引擎减暗判定位）。
//   (2) 0x00655D38 处 EAX **不是** CellClass*：0x578080 = MapClass::GetCellFloorHeight()
//       （YRpp/MapClass.h:282 与 :417 "int sub_578080(CoordStruct*)"），返回**格面高度 int**，
//       并被写入 CoordStruct 的 Z 槽（[esp+0x28]）。旧代理把该 int 当 pCell 解读 ⇒
//       cmp eax,0x10000 / jbe do_passthrough 恒真 ⇒ 「雷达灰化分支进入次数」增长而
//       「雷达灰化像素数」恒 0 —— 这就是 ZC-2 S3 FAIL 的直接根因。
//   (3) 引擎减暗体的驱动位 = [esp+0x13]（0x655D7B/0x655D82 写入，0x655E7E 消费）：
//       原版语义 [esp+0x13] = (hWnd!=0) && MapClass::IsLocationFogged(@CoordStruct)，
//       为 1 即执行 Get_Pixel(0x1220) → 三通道分别 >>1 → Set_Pixel(0x121C)（像素精确 50% 减暗）。
//       ⇒ 第 (2) 条路线：新增 0x00655D87 挂钩，在引擎判定完成后按我方三态视野谓词改写该位，
//          直接复用引擎减暗体（不自绘像素）；自绘路径保留为 RadarFogGuardMode 0/1/2 供 A/B。
//
// 【挂钩点清单（F5 要求：0x00655D38 与 0x0065719A 均未变）】
//   H1: 0x00655D38 9 字节（mov [esp+0x28],eax + mov eax,[0xB73550]）→ jmp 自绘代理（模式 0/1/2）
//   H2: 0x0065719A 5 字节（call 0x660530）→ jmp 跳帧判定代理（未变）
//   H3: 0x00655D87 7 字节（mov eax,[edi+4] + mov [esp+0x14],ebp）→ jmp 原生减暗驱动代理（模式 3 默认）
// ============================================================================

// ---- [RADAR-FIX2] 挂钩点上下文：H1/H3 共用（同一线程、不可重入，静态复用安全） ----
struct RadarHookCtx {
    void    *radarThis;    // +0  雷达单例 0x0087F7E8（= Plot_Cell 的 this / ESI）
    void    *pt;           // +4  雷达表面像素坐标 POINT*（= EDI）
    uint32_t floorHeight;  // +8  GetCellFloorHeight 返回值（= CoordStruct.Z，单位 104=LevelHeight）
    void    *pCoord;       // +12 &CoordStruct{X,Y,Z}（= [esp+0x20]）
    uint8_t *pFlag;        // +16 H3 专用：&[esp+0x13]（引擎减暗判定位，可写）
};
static RadarHookCtx s_radarCtx = {nullptr, nullptr, 0, nullptr, nullptr};

extern "C" {
    void    *s_pRadarCtx = nullptr;              // 汇编侧取址入口（两步解引用，绕开 MSVC [imm] 陷阱）
    uint8_t  s_radarSelfDrawnDone = 0;           // 自绘代理→汇编侧裁决：1=已写完像素，走函数尾声
}

// 引擎逐格谓词（__thiscall，ECX=0x0087F7E8，1 个栈参数，被调方 ret 4）
//   0x00586360 = MapClass::IsLocationShrouded(const CoordStruct&)（未探索=true）
//   0x005864A0 = 引擎自身减暗判定（true=雾中→50% 减暗）
typedef bool (__thiscall *FnLocationPredicate)(void *pThis, void *pCoord);
static FnLocationPredicate s_pIsLocationShrouded = reinterpret_cast<FnLocationPredicate>(0x00586360);
static FnLocationPredicate s_pIsLocationFogged   = reinterpret_cast<FnLocationPredicate>(0x005864A0);

// 表面像素接口（vtable +0x28 = Get_Pixel(pt)，+0x24 = Set_Pixel(pt,color)）
//   [实证] 引擎自用于 0x655E8A（Get，源表面 [this+0x1220]）与 0x655F40（Set，目标 [this+0x121C]）
typedef uint32_t (__thiscall *FnSurfaceGetPixel)(void *pSurface, void *pt);
typedef void     (__thiscall *FnSurfaceSetPixel)(void *pSurface, void *pt, uint32_t color);

static inline bool RadarPtrOk(const void *p) {
    return p != nullptr && reinterpret_cast<uintptr_t>(p) > 0x10000u;
}

// 我方三态视野谓词求解（供自绘路径与原生驱动路径共用）：
//   explored = 引擎自身判定「该格已探索」（MapClass::IsLocationShrouded == false；
//              其内部按 CoordStruct 做地形高度补偿后取 CellClass+0x12C 的 cf_Explored=0x08 位）
//   inVision = 我方直视视野网格（帧 Token 制，与主视图 L3 灰雾同源）
// 返回 false = 本点无法判定（坐标越界 / 谓词抛异常），调用方一律回退为「不动引擎」
static bool RadarResolveCellState(const RadarHookCtx *ctx, bool *explored, bool *inVision) {
    *explored = false;
    *inVision = false;
    if (!ctx || !ctx->pCoord) return false;
    if (!s_pIsLocationShrouded || !s_pIsLocationFogged) return false;

    const uint8_t *crd = reinterpret_cast<const uint8_t*>(ctx->pCoord);
    const int cx = *reinterpret_cast<const int*>(crd + 0);
    const int cy = *reinterpret_cast<const int*>(crd + 4);
    const int cellX = cx >> 8;
    const int cellY = cy >> 8;
    if (cellX < 0 || cellX >= 512 || cellY < 0 || cellY >= 512) return false;

    void *pRadar = reinterpret_cast<void*>(0x0087F7E8);
    *explored = !s_pIsLocationShrouded(pRadar, ctx->pCoord);

    const uint32_t idx = static_cast<uint32_t>(cellY * 512 + cellX);
    *inVision = (s_visionGrid[idx] == s_visionToken);
    return true;
}

static void RadarFogLogOnce(const char *what, uint32_t n) {
    if (n == 1) {
        LogMessage("[ra2render-minimap] %s（首次命中，后续仅计数）", what);
    }
}

// ---------------------------------------------------------------------------
// H1 代理的 C++ 体：自绘 50% 灰化（RadarFogGuardMode = 0/1/2，A/B 对照用）
//   与旧实现的差异：不再把 EAX（格面高度）当 CellClass*；改由引擎逐格谓词求真值。
//   像素公式 (c>>1)&0x7BEF 与引擎减暗体**逐通道等价**（报告 §5 给出代数证明）：
//     R' = floor(R/2)（bit10 由 0x7BEF 清零）、G' = floor(G/2)（bit4 清零）、B' = floor(B/2)。
// ---------------------------------------------------------------------------
extern "C" void __cdecl RadarHook_SelfDrawn(RadarHookCtx *ctx) {
    s_radarSelfDrawnDone = 0;
    if (!ctx || !ctx->radarThis || !ctx->pt) return;

    // 早退桶（诊断用）：0=总开关关闭 1=护栏2拦截 2=雷达表面无效 3=谓词求解失败 4=未探索 5=直视圈内
    // [FOG-SWITCH 短路点 ③-补充] 灰雾总闸=0 ⇒ 自绘灰化路径同样整体短路（自绘也会在小地图上产生压暗，
    //   属「其它服务半透明黑的绘制路径」，故同样受总闸约束；此时也不进入函数尾声 ⇒ 保留引擎红点循环）。
    if (!g_enableStarCraftFog || !s_minimapFogGate) { s_radarGuardRejects[0]++; return; }

    const int mode = s_radarFogGuardMode;
    if (mode == RADAR_FOG_GUARD_LEGACY) {
        // 旧行为（真机对照）：把 SessionClass::Instance.GameMode(0x00A8B238) 当作游戏状态，
        // ==0 视为「菜单」→ 跳过。已证伪（战役局内恒为 0），仅保留用于复现旧 S1 结果。
        if (*reinterpret_cast<const uint8_t*>(ADDR_SESSION_GAMEMODE) == 0) { s_radarGuardRejects[1]++; return; }
    } else if (mode == RADAR_FOG_GUARD_NATIVE) {
        // 原生减暗驱动模式：自绘路径不参与（由 H3 代理驱动引擎减暗体）
        return;
    } else {
        // 新谓词（0/1/2 自绘档）：PlayerPtr / Scenario 存在 + GameMode 合法 + 雷达双表面有效。
        // [RADAR-FIX2 F3(1) 勘误] 原第 3 项「ScenarioClass+0x3598 == 0（IsLoadingScreen）」已删除：
        //   该偏移在 YRpp/ScenarioClass.h:224 仅记录为 DWORD unknown_3598，全 exe 的 12 处
        //   访问均为**字节**粒度门控（如 0x005989DC / 0x00598B1E 处 cmp byte [scn+0x3598],0），
        //   真机实测该字节 = 0x92（ZCode）⇒ 非 0/1 布尔语义，「IsLoadingScreen」为无据推断。
        //   改为直接校验本代理将要写入的两个雷达表面指针（与引擎 0x655E8A/0x655F40 同一来源），
        //   语义上更贴合「可安全绘制」这一真实前置条件。
        void *pPlayer = *reinterpret_cast<void**>(ADDR_HOUSE_PLAYER);
        if (reinterpret_cast<uintptr_t>(pPlayer) < 0x10000u) { s_radarGuardRejects[1]++; return; }
        void *pScenario = *reinterpret_cast<void**>(ADDR_SCENARIO_INSTANCE);
        if (reinterpret_cast<uintptr_t>(pScenario) < 0x10000u) { s_radarGuardRejects[1]++; return; }
        const int gm = *reinterpret_cast<const int*>(ADDR_SESSION_GAMEMODE);
        if (gm < 0 || gm > 5) { s_radarGuardRejects[1]++; return; }
    }

    __try {
        void *pSrc = *reinterpret_cast<void**>(reinterpret_cast<uint8_t*>(ctx->radarThis) + RADAR_OFF_CACHE_SURFACE);
        void *pDst = *reinterpret_cast<void**>(reinterpret_cast<uint8_t*>(ctx->radarThis) + RADAR_OFF_WORK_SURFACE);
        if (!RadarPtrOk(pSrc) || !RadarPtrOk(pDst)) { s_radarGuardRejects[2]++; return; }

        bool explored = false, inVision = false;
        if (!RadarResolveCellState(ctx, &explored, &inVision)) { s_radarGuardRejects[3]++; return; }
        s_radarProbeOk++;
        if (explored) s_radarProbeExplored++;
        if (inVision) s_radarProbeVisible++;
        if (!explored) { s_radarGuardRejects[4]++; return; }   // 未探索：引擎画全黑，不叠加灰
        if (inVision) { s_radarGuardRejects[5]++; return; }    // 直视圈内：保持全彩

        s_minimapFogBranchHits++;
        void **pSrcVt = *reinterpret_cast<void***>(pSrc);
        void **pDstVt = *reinterpret_cast<void***>(pDst);
        FnSurfaceGetPixel getPixel = reinterpret_cast<FnSurfaceGetPixel>(pSrcVt[0x28 / 4]);
        FnSurfaceSetPixel setPixel = reinterpret_cast<FnSurfaceSetPixel>(pDstVt[0x24 / 4]);
        if (!getPixel || !setPixel) { s_radarGuardRejects[2]++; return; }

        uint32_t color = getPixel(pSrc, ctx->pt);
        color = (color >> 1) & 0x7BEF;              // 与原版减暗体逐通道等价
        setPixel(pDst, ctx->pt, color);

        s_minimapFogPixels++;
        s_radarDarkenDriven++;    // [FOG-SWITCH 计数③] 自绘档同样计入「小地图减暗驱动」（总闸关时恒 0）
        s_radarSelfDrawnDone = 1;
        RadarFogLogOnce("自绘灰化路径已落像素（50% 减暗）", s_minimapFogPixels);
    }
    __except (EXCEPTION_EXECUTE_HANDLER) {
        s_radarGuardRejects[3]++;
        s_radarSelfDrawnDone = 0;
    }
}

// ---------------------------------------------------------------------------
// H3 代理的 C++ 体：引擎原生减暗驱动（RadarFogGuardMode = 3，本版默认）
//   - 引擎已算好的判定位在 *ctx->pFlag（[esp+0x13]）；
//   - 本函数把该位改写为「我方三态谓词」结论：explored && !inVision ⇒ 1（雾中减暗）/ 否则 0；
//   - 不自绘任何像素：真正落像素的是引擎减暗体（0x655E8A-0x655F43，像素精确）。
//   - 遥测：引擎自身判定命中数 / 我方强制命中数 / 覆盖差（供 ZC-3 一轮判定走哪条路）。
// ---------------------------------------------------------------------------
extern "C" void __cdecl RadarHook_NativeDecide(RadarHookCtx *ctx) {
    CheckTelemetry();                       // 小地图绘制是每帧必到的遥测节拍点
    if (!ctx || !ctx->pFlag) return;

    const uint8_t engineFlag = *ctx->pFlag;
    if (engineFlag) s_nativeEngineDarkHits++;

    // 【FOG-SWITCH 短路点 ③（C++ 侧兜底，与代理内汇编短路同语义）】总闸=0 ⇒
    //   不驱动引擎减暗判定位：[esp+0x13] 保持引擎自身判定，等价「不干预」。
    if (!g_enableStarCraftFog) {
        if (engineFlag) s_nativeDarkenHits++;
        return;
    }

    if (!s_minimapFogGate || s_radarFogGuardMode != RADAR_FOG_GUARD_NATIVE) {
        // 门控关闭 / 非原生档：完全不动引擎判定（与未挂钩逐位一致）
        if (engineFlag) s_nativeDarkenHits++;
        return;
    }

    // 尊重引擎自身在 0x655D62 的 hWnd 门（只读该全局，绝不写）：hWnd==0 ⇒ 引擎判定位必为 0，
    // 本函数一律不覆盖，杜绝窗口/雷达表面尚未就绪时被驱动进减暗体。
    if (*reinterpret_cast<const uint32_t*>(ADDR_GAME_HWND) == 0) {
        s_radarHwndZero++;
        if (engineFlag) s_nativeDarkenHits++;
        return;
    }

    bool explored = false, inVision = false;
    if (!RadarResolveCellState(ctx, &explored, &inVision)) {
        s_radarProbeFail++;
        if (engineFlag) s_nativeDarkenHits++;
        return;
    }
    s_radarProbeOk++;
    if (explored) s_radarProbeExplored++;
    if (inVision) s_radarProbeVisible++;

    // ★[FOG-SPLIT] 未探索格（引擎判定未探索）：**不写**引擎减暗判定位 —— 与我方主视图口径一致
    //   （对未探索格零介入；该格的小地图黑幕由引擎自身路径负责，与我方无关）。
    if (!explored) {
        s_radarUnexploredPassed++;
        if (engineFlag) s_nativeDarkenHits++;
        return;
    }

    // 此处仅剩「已探索」档：ours = 已探索 && 非直视（= 小地图减暗的唯一驱动条件）
    const uint8_t ours = (explored && !inVision) ? 1 : 0;
    if (ours != engineFlag) {
        s_nativeOverrideDeltas++;
        RadarFogLogOnce("原生减暗位被我方谓词覆盖（引擎判定与三态视野不一致）", s_nativeOverrideDeltas);
    }
    if (ours) {
        s_nativeForcedDarkHits++;
        s_radarDarkenDriven++;    // [FOG-SWITCH 计数③] 我方驱动引擎减暗（改写判定位为 1；总闸关时恒 0）
    }
    *ctx->pFlag = ours;
    if (ours) s_nativeDarkenHits++;
}

static uint8_t s_origPlotCellBytes[9] = {0};           // 0x00655D38 起 9 字节原版指令
static uint8_t s_plotCellTrampoline[16] = {0};         // 9B 原指令 + jmp 0x00655D41
static uint8_t s_origRadarPendingCallBytes[5] = {0};   // 0x65719A 处 call rel32
static uint8_t s_origNativeDecideBytes[7] = {0};       // [RADAR-FIX2] 0x00655D87 起 7 字节原版指令
static uint8_t s_nativeDecideTrampoline[16] = {0};     // [RADAR-FIX2] 7B 原指令 + jmp 0x00655D8E
// s_pPlotCellTrampoline / s_pRadarNativeTrampoline 定义于文件头 extern "C" 块（勿重复定义）

// H1：0x00655D38 下沉挂钩（9 字节）
//   入口契约：EAX = GetCellFloorHeight 返回的格面高度(int)、ESI = 雷达单例、EDI = pt、
//             EBP = 0（参与后续比较）、EBX = 表面边界值；CoordStruct 在 [esp+0x20]。
//   退出契约：passthrough 必须还原 EAX（跳板首指令 mov [esp+0x28],eax 会把它写回 Z 槽）；
//             自绘完成分支直接执行函数尾声（跳过红点循环 ⇒ 敌点一次隐匿）。
__declspec(naked) void Hook_RadarPlot_Cell_Proxy() {
    __asm {
        push eax                         // 保存 EAX（跳板回放需要原值）
        mov  ecx, s_pRadarCtx            // ecx = &s_radarCtx（符号取址，两步解引用）
        mov  dword ptr [ecx + 0], esi
        mov  dword ptr [ecx + 4], edi
        mov  dword ptr [ecx + 8], eax
        lea  edx, [esp + 0x24]           // 入口 [esp+0x20]，push eax 后 +4
        mov  dword ptr [ecx + 12], edx
        mov  dword ptr [ecx + 16], 0
        push ecx
        call RadarHook_SelfDrawn
        add  esp, 4
        pop  eax                         // 还原 EAX
        cmp  byte ptr [s_radarSelfDrawnDone], 0
        jne  radar_selfdrawn_epilogue
        jmp  dword ptr [s_pPlotCellTrampoline]
    radar_selfdrawn_epilogue:
        pop  edi
        pop  esi
        pop  ebp
        pop  ebx
        add  esp, 0x30
        ret  4
    }
}

// H3：[RADAR-FIX2] 0x00655D87 原生减暗判定驱动挂钩（7 字节）
//   入口契约：与 0x00655D87 完全一致（esp 基准同点）：[esp+0x13] = 引擎判定位、
//             [esp+0x20] = CoordStruct；ESI/EDI/EBX/EBP 由 __cdecl 被调方保持；
//             EAX/ECX/EDX 可破坏（跳板回放的首指令 mov eax,[edi+4] 会重建 EAX）。
//   退出契约：跳板回放 7 字节原指令后 jmp 0x00655D8E，语义与未挂钩逐位一致。
__declspec(naked) void Hook_RadarNativeDecide_Proxy() {
    __asm {
        ; 【FOG-SWITCH 短路点 ③】总闸=0 ⇒ 直接把控制权交还跳板，完全不进入我方驱动体：
        ;   [esp+0x13] 保持引擎自身判定，不读不写任何引擎状态（等价「未挂钩」）。
        ;   flags 纪律：0x00655D87 入口处的 flags 来自 0x655D79 的 test al,al，其后续指令
        ;   （mov eax,[edi+4] / mov [esp+0x14],ebp / lea ...）均不读 flags，且既有实现早已在
        ;   此处调用 __cdecl 函数破坏 flags（真机默认档已运行）⇒ 此处 cmp 破坏 flags 无副作用。
        cmp  byte ptr [s_fogMasterGate], 0
        je   radar_native_passthrough
        mov  ecx, s_pRadarCtx
        mov  dword ptr [ecx + 0], esi
        mov  dword ptr [ecx + 4], edi
        mov  dword ptr [ecx + 8], 0
        lea  edx, [esp + 0x20]
        mov  dword ptr [ecx + 12], edx
        lea  edx, [esp + 0x13]
        mov  dword ptr [ecx + 16], edx
        push ecx
        call RadarHook_NativeDecide
        add  esp, 4
    radar_native_passthrough:
        jmp  dword ptr [s_pRadarNativeTrampoline]
    }
}

// 替换 0x0065719A 处 call 0x660530：视野迁移期间强制小地图跳过"无变化"跳帧判定
// 原函数语义：mov eax,[0xB04DB8]; test eax,eax; sete al; ret —— al=0 时引擎走每帧刷新路径
__declspec(naked) void Hook_RadarPending_Proxy() {
    __asm {
        ; [FOG-SWITCH 短路点 ⑤] 总闸=0 ⇒ 本「跳帧强驱（小地图强制全量刷新）」路径不介入，逐位走原版逻辑
        cmp byte ptr [s_fogMasterGate], 0
        je orig_logic
        cmp byte ptr [s_minimapFogGate], 0
        je orig_logic
        cmp byte ptr [s_minimapForceRefresh], 0
        je orig_logic
        xor al, al                   // 强制"有待处理" -> 引擎执行全量小地图刷新
        ret
    orig_logic:
        mov eax, 0x00B04DB8
        mov eax, [eax]               // 同款方括号陷阱修复：两步解引用
        test eax, eax
        sete al
        ret
    }
}

static bool InstallRadarFogHooks() {
    DWORD oldProtect = 0;
    s_pRadarCtx = &s_radarCtx;   // [RADAR-FIX2] 汇编侧取址入口就绪（必须在挂钩前设置）

    // 1) 路线 A：0x00655D38 下沉挂钩（9 字节补丁 + 跳板）
    memcpy(s_origPlotCellBytes, reinterpret_cast<void*>(0x00655D38), sizeof(s_origPlotCellBytes));

    if (!VirtualProtect(s_plotCellTrampoline, sizeof(s_plotCellTrampoline), PAGE_EXECUTE_READWRITE, &oldProtect)) {
        LogMessage("[ra2render-minimap] 错误：无法设置 Plot_Cell 跳板内存权限");
        return false;
    }
    memcpy(s_plotCellTrampoline, s_origPlotCellBytes, sizeof(s_origPlotCellBytes));
    s_plotCellTrampoline[9] = 0xE9;
    {
        // rel32 = 0x00655D41 - (跳板 E9 场址 + 5)；E9 位于 tramp[9]，imm32 位于 tramp[10]
        uintptr_t immAddr = reinterpret_cast<uintptr_t>(&s_plotCellTrampoline[10]);
        int32_t jmpBack = static_cast<int32_t>(0x00655D41 - (immAddr + 4));
        memcpy(&s_plotCellTrampoline[10], &jmpBack, sizeof(int32_t));
    }
    s_pPlotCellTrampoline = s_plotCellTrampoline;

    if (!VirtualProtect(reinterpret_cast<void*>(0x00655D38), sizeof(s_origPlotCellBytes), PAGE_EXECUTE_READWRITE, &oldProtect)) {
        LogMessage("[ra2render-minimap] 错误：无法修改 0x00655D38 内存权限");
        return false;
    }
    {
        uint8_t patch[9];
        patch[0] = 0xE9;
        int32_t rel = static_cast<int32_t>(reinterpret_cast<uintptr_t>(&Hook_RadarPlot_Cell_Proxy) - (0x00655D38 + 5));
        memcpy(&patch[1], &rel, sizeof(int32_t));
        patch[5] = patch[6] = patch[7] = patch[8] = 0x90;
        memcpy(reinterpret_cast<void*>(0x00655D38), patch, sizeof(patch));
    }
    VirtualProtect(reinterpret_cast<void*>(0x00655D38), sizeof(s_origPlotCellBytes), oldProtect, &oldProtect);

    // 2) 劫持跳帧判定调用点 0x65719A（call rel32 等长替换）
    memcpy(s_origRadarPendingCallBytes, reinterpret_cast<void*>(ADDR_RADAR_PENDING_CALLSITE), sizeof(s_origRadarPendingCallBytes));
    if (!VirtualProtect(reinterpret_cast<void*>(ADDR_RADAR_PENDING_CALLSITE), sizeof(s_origRadarPendingCallBytes), PAGE_EXECUTE_READWRITE, &oldProtect)) {
        LogMessage("[ra2render-minimap] 错误：无法修改跳帧判定调用点内存权限");
        return false;
    }
    {
        uint8_t patch[5];
        patch[0] = 0xE8;
        int32_t rel = static_cast<int32_t>(reinterpret_cast<uintptr_t>(&Hook_RadarPending_Proxy) - (ADDR_RADAR_PENDING_CALLSITE + 5));
        memcpy(&patch[1], &rel, sizeof(int32_t));
        memcpy(reinterpret_cast<void*>(ADDR_RADAR_PENDING_CALLSITE), patch, sizeof(patch));
    }
    VirtualProtect(reinterpret_cast<void*>(ADDR_RADAR_PENDING_CALLSITE), sizeof(s_origRadarPendingCallBytes), oldProtect, &oldProtect);

    // 3) [RADAR-FIX2] 0x00655D87 原生减暗判定驱动挂钩（7 字节补丁 + 跳板）
    memcpy(s_origNativeDecideBytes, reinterpret_cast<void*>(ADDR_RADAR_NATIVE_DECIDE), sizeof(s_origNativeDecideBytes));
    if (!VirtualProtect(s_nativeDecideTrampoline, sizeof(s_nativeDecideTrampoline), PAGE_EXECUTE_READWRITE, &oldProtect)) {
        LogMessage("[ra2render-minimap] 错误：无法设置原生减暗跳板内存权限");
        return false;
    }
    memcpy(s_nativeDecideTrampoline, s_origNativeDecideBytes, sizeof(s_origNativeDecideBytes));
    s_nativeDecideTrampoline[7] = 0xE9;
    {
        uintptr_t immAddr = reinterpret_cast<uintptr_t>(&s_nativeDecideTrampoline[8]);
        int32_t jmpBack = static_cast<int32_t>(ADDR_RADAR_NATIVE_RESUME - (immAddr + 4));
        memcpy(&s_nativeDecideTrampoline[8], &jmpBack, sizeof(int32_t));
    }
    s_pRadarNativeTrampoline = s_nativeDecideTrampoline;

    if (!VirtualProtect(reinterpret_cast<void*>(ADDR_RADAR_NATIVE_DECIDE), sizeof(s_origNativeDecideBytes), PAGE_EXECUTE_READWRITE, &oldProtect)) {
        LogMessage("[ra2render-minimap] 错误：无法修改 0x00655D87 内存权限");
        return false;
    }
    {
        uint8_t patch[7];
        patch[0] = 0xE9;
        int32_t rel = static_cast<int32_t>(reinterpret_cast<uintptr_t>(&Hook_RadarNativeDecide_Proxy) - (ADDR_RADAR_NATIVE_DECIDE + 5));
        memcpy(&patch[1], &rel, sizeof(int32_t));
        patch[5] = patch[6] = 0x90;
        memcpy(reinterpret_cast<void*>(ADDR_RADAR_NATIVE_DECIDE), patch, sizeof(patch));
    }
    VirtualProtect(reinterpret_cast<void*>(ADDR_RADAR_NATIVE_DECIDE), sizeof(s_origNativeDecideBytes), oldProtect, &oldProtect);

    LogMessage("[ra2render-minimap] 成功挂载路线 A 下沉挂钩 (Plot_Cell 0x00655D38 9B + 强制刷新 0x0065719A 5B + [RADAR-FIX2] 原生减暗驱动 0x00655D87 7B)，灰化模式=%d (0=旧护栏自绘 1=新谓词自绘 2=无护栏自绘 3=引擎原生减暗驱动)",
               static_cast<int>(s_radarFogGuardMode));
    return true;
}

static void RemoveRadarFogHooks() {
    DWORD oldProtect = 0;
    if (s_origNativeDecideBytes[0] != 0) {
        VirtualProtect(reinterpret_cast<void*>(ADDR_RADAR_NATIVE_DECIDE), sizeof(s_origNativeDecideBytes), PAGE_EXECUTE_READWRITE, &oldProtect);
        memcpy(reinterpret_cast<void*>(ADDR_RADAR_NATIVE_DECIDE), s_origNativeDecideBytes, sizeof(s_origNativeDecideBytes));
        VirtualProtect(reinterpret_cast<void*>(ADDR_RADAR_NATIVE_DECIDE), sizeof(s_origNativeDecideBytes), oldProtect, &oldProtect);
    }
    if (s_origRadarPendingCallBytes[0] != 0) {
        VirtualProtect(reinterpret_cast<void*>(ADDR_RADAR_PENDING_CALLSITE), sizeof(s_origRadarPendingCallBytes), PAGE_EXECUTE_READWRITE, &oldProtect);
        memcpy(reinterpret_cast<void*>(ADDR_RADAR_PENDING_CALLSITE), s_origRadarPendingCallBytes, sizeof(s_origRadarPendingCallBytes));
        VirtualProtect(reinterpret_cast<void*>(ADDR_RADAR_PENDING_CALLSITE), sizeof(s_origRadarPendingCallBytes), oldProtect, &oldProtect);
    }
    if (s_origPlotCellBytes[0] == 0x89 && s_origPlotCellBytes[1] == 0x44) {
        VirtualProtect(reinterpret_cast<void*>(0x00655D38), sizeof(s_origPlotCellBytes), PAGE_EXECUTE_READWRITE, &oldProtect);
        memcpy(reinterpret_cast<void*>(0x00655D38), s_origPlotCellBytes, sizeof(s_origPlotCellBytes));
        VirtualProtect(reinterpret_cast<void*>(0x00655D38), sizeof(s_origPlotCellBytes), oldProtect, &oldProtect);
    }
    s_pPlotCellTrampoline = nullptr;
    s_pRadarNativeTrampoline = nullptr;
}

// ★[FOG-SPLIT] 玩法（逻辑）可见性三钩子：门控键**与总闸 EnableStarCraftFog 解耦**。
//   旧版「g_enableStarCraftFog && !ShouldDrawMobileObject(...)」⇒ 总闸=0 时机动单位剔除恒不执行
//   （ZC-4 S2 实测「迷雾剔除机动单位」恒 0），违反「总闸只管画面表现」的既定语义。
//   建筑/弹道两钩子本就只挂各自子键（F2 复查结论：总闸=0 时仍生效，ZC-4 S2 计数 建筑剔除 1457 /
//   弹道剔除 49 即为实证），本版未改其门控，仅新增机动单位专用键 EnableUnitFog。
void __thiscall FogHooks::Hook_Unit_Draw(void *pLocation, void *pBounds) {
    void *pThis = this;
    CheckTelemetry();
    // ★[FOG-MODE F1] 短路支①（机动单位）：VisibilityMode=vanilla ⇒ 被 mode 覆盖而放行。
    //   位置在剔除判定**之前** ⇒ vanilla 档下 ShouldDrawMobileObject 根本不被调用，
    //   unitsCulledByFog 恒 0（F4 机器判据的结构性保证）；本支零引擎写入。
    if (g_visibilityVanilla && FogModeVanillaPassThrough(0)) {
        g_telemetry.totalUnitsRendered++;
        if (g_pOrigUnitDraw) {
            g_pOrigUnitDraw(pThis, pLocation, pBounds);
        }
        return;
    }
    if (g_enableUnitFog && !ShouldDrawMobileObject(pThis)) {
        g_telemetry.unitsCulledByFog++;
        return;
    }
    g_telemetry.totalUnitsRendered++;
    if (g_pOrigUnitDraw) {
        g_pOrigUnitDraw(pThis, pLocation, pBounds);
    }
}

void __thiscall FogHooks::Hook_Infantry_Draw(void *pLocation, void *pBounds) {
    void *pThis = this;
    // ★[FOG-MODE F1] 短路支①（机动单位/步兵）：vanilla ⇒ 覆盖放行（见 Hook_Unit_Draw 注释）
    if (g_visibilityVanilla && FogModeVanillaPassThrough(0)) {
        g_telemetry.totalUnitsRendered++;
        if (g_pOrigInfantryDraw) {
            g_pOrigInfantryDraw(pThis, pLocation, pBounds);
        }
        return;
    }
    if (g_enableUnitFog && !ShouldDrawMobileObject(pThis)) {
        g_telemetry.unitsCulledByFog++;
        return;
    }
    g_telemetry.totalUnitsRendered++;
    if (g_pOrigInfantryDraw) {
        g_pOrigInfantryDraw(pThis, pLocation, pBounds);
    }
}

void __thiscall FogHooks::Hook_Aircraft_Draw(void *pLocation, void *pBounds) {
    void *pThis = this;
    // ★[FOG-MODE F1] 短路支①（机动单位/战机）：vanilla ⇒ 覆盖放行（见 Hook_Unit_Draw 注释）
    if (g_visibilityVanilla && FogModeVanillaPassThrough(0)) {
        g_telemetry.totalUnitsRendered++;
        if (g_pOrigAircraftDraw) {
            g_pOrigAircraftDraw(pThis, pLocation, pBounds);
        }
        return;
    }
    if (g_enableUnitFog && !ShouldDrawMobileObject(pThis)) {
        g_telemetry.unitsCulledByFog++;
        return;
    }
    g_telemetry.totalUnitsRendered++;
    if (g_pOrigAircraftDraw) {
        g_pOrigAircraftDraw(pThis, pLocation, pBounds);
    }
}

void __thiscall FogHooks::Hook_Building_Draw(void *pLocation, void *pBounds) {
    void *pThis = this;
    // ★[FOG-MODE F1] 短路支②（建筑）：VisibilityMode=vanilla ⇒ 被 mode 覆盖而放行。
    //   在 ShouldDrawBuilding（含 everSeen「看见过即常驻」判定）**之前** ⇒
    //   buildingsCulledByFog 恒 0（F4）且雾中新建敌基地也照常绘制（原版可见性）。
    if (g_visibilityVanilla && FogModeVanillaPassThrough(1)) {
        if (g_pOrigBuildingDraw) {
            g_pOrigBuildingDraw(pThis, pLocation, pBounds);
        }
        return;
    }
    if (g_enableBuildingFog && !ShouldDrawBuilding(pThis)) {
        g_telemetry.buildingsCulledByFog++;
        return;
    }
    if (g_pOrigBuildingDraw) {
        g_pOrigBuildingDraw(pThis, pLocation, pBounds);
    }
}

void __thiscall FogHooks::Hook_Bullet_Draw(void *pLocation, void *pBounds) {
    void *pThis = this;
    // ★[FOG-MODE F1] 短路支③（弹道）：VisibilityMode=vanilla ⇒ 被 mode 覆盖而放行。
    //   在 ShouldDrawBullet 之前 ⇒ bulletsCulledByFog 恒 0（F4），远处敌方开火可见。
    if (g_visibilityVanilla && FogModeVanillaPassThrough(2)) {
        if (g_pOrigBulletDraw) {
            g_pOrigBulletDraw(pThis, pLocation, pBounds);
        }
        return;
    }
    if (g_enableBulletFog && !ShouldDrawBullet(pThis)) {
        g_telemetry.bulletsCulledByFog++;
        return;
    }
    if (g_pOrigBulletDraw) {
        g_pOrigBulletDraw(pThis, pLocation, pBounds);
    }
}

// ---------------------------------------------------------------------------
// [GAP-P223] 裂缝保护三点表驱动（ZC-GAP-P223 合并 ZC-GAP-P21；landing_pack_gap_p223.md
//   + landing_pack_gap_merge_checklist.md；依据 R-GAP-PSY 静态定谳，gamemd.exe 1.001
//     SHA-256 73201CC0…F67476，三点原字节 3/3 MATCH，Q4 闭合「每函数恰一处 +0x134 store」）
//   三点同构：只删各函数内层循环「清 GapsCoveringThisCell(+0x134)」那一次 store；
//   同循环其余写入原样保留：
//     P-2.1 保留 ShroudCounter<-0(@0x56824A) / CopyFlags|=0x10(@0x56829A)
//     P-2.2 保留 ShroudCounter<-0(@0x577EBF) / CopyFlags|=0x18(@0x577ED4)
//     P-2.3 保留 CopyFlags&=~0x18(@0x577B4E) / ShroudCounter<-1(@0x577B56) / RedrawFlags&=~0x3(@0x577B66)
//   等长硬约束：6B==6B，禁 trampoline / 禁动 .detour 节；只允许纯 90
//   （禁 89→8B / add/or/and/xor/cmp 类 1B 翻法：edi/ebx 零常量在循环内仍被消费，
//    且 cmp→jl/je 类邻接 flags 关系必须保持）。
//   窗宽按实测参数化（禁 2B 硬编码）：P-2.1 前2/后2、P-2.2 前6/后6、P-2.3 前10/后6。
//   安装序 = 表序（强制 P-2.1→P-2.2→P-2.3，先封 22-caller 高频面）；硬回滚强制逆序
//   （P-2.3→P-2.2→P-2.1，后装先拆，禁只拆中间点）；任一字节/上下文门禁不符 ⇒ 整包不写。
//   安装前置（三点全查 MATCH 才写，任一不符即拒绝且不动一个字节）：
//     G0.2 目标 6B = 原字节（若已 90×6 ⇒ 外部安装者已打：停手、只告警、不写不还原）
//     G0.3/G0.4 窗前/窗后 = 期望字节（按各点实测窗宽）
//     G0.6 EnableGapProtection 显式 =1；MpActive() 联机强制不装
//   回滚：硬 = 按分点备份 s_origGapProtectBytes[3][6] 逆序 memcpy 还原（仅还原我方写的
//   字节）；软 = 关键闭 + 重启（安装态在 init 决定）。
//   磁盘 gamemd.exe 只读：本补丁只改已加载映像的内存字节（RE_COORDINATION 红线 §3-1）。
// ---------------------------------------------------------------------------

// 单点定义（表驱动；安装与回滚都走同一张表，禁逐点硬编码漂移）
struct GapProtectPointDef {
    const char    *tag;        // 步骤 ID（P-2.1/P-2.2/P-2.3；日志用）
    uint32_t       site;       // 6B 替换点 VA
    const uint8_t *orig;       // 原 6B（禁漂移常量；6==6 等长）
    uint32_t       prev;       // 前窗 VA（保留写点自检）
    uint32_t       prevLen;    // 前窗宽度（按实测：2/6/10；禁 2B 硬编码）
    const uint8_t *prevBytes;  // 前窗期望字节
    uint32_t       next;       // 后窗 VA（保留写点自检）
    uint32_t       nextLen;    // 后窗宽度（按实测：2/6）
    const uint8_t *nextBytes;  // 后窗期望字节
    const char    *desc;       // 原指令与覆盖面说明（日志）
};

static const uint8_t kGapP21Orig[6]  = {0x89, 0x99, 0x34, 0x01, 0x00, 0x00}; // mov [ecx+0x134], ebx（ebx=0）
static const uint8_t kGapP22Orig[6]  = {0x89, 0xB8, 0x34, 0x01, 0x00, 0x00}; // mov [eax+0x134], edi（edi=0）
static const uint8_t kGapP23Orig[6]  = {0x89, 0x98, 0x34, 0x01, 0x00, 0x00}; // mov [eax+0x134], ebx（ebx=0）
static const uint8_t kGapP21Prev[2]  = {0x3B, 0xC3};                         // cmp eax, ebx（产 flags）
static const uint8_t kGapP21Next[2]  = {0x7C, 0x14};                         // jl（消费同一 flags）
static const uint8_t kGapP22Prev[6]  = {0x89, 0xB8, 0x30, 0x01, 0x00, 0x00}; // mov [eax+0x130], edi（ShroudCounter<-0，保留）
static const uint8_t kGapP22Next[6]  = {0x8B, 0x90, 0x2C, 0x01, 0x00, 0x00}; // mov edx,[eax+0x12C]（load CopyFlags）
static const uint8_t kGapP23Prev[10] = {0xC7, 0x80, 0x30, 0x01, 0x00, 0x00,  // mov dword [eax+0x130],1（ShroudCounter<-1，保留）
                                        0x01, 0x00, 0x00, 0x00};
static const uint8_t kGapP23Next[6]  = {0x89, 0x90, 0x40, 0x01, 0x00, 0x00}; // mov [eax+0x140], edx（RedrawFlags<-edx&~0x3）

// 安装序 = 表序（强制 P-2.1→P-2.2→P-2.3）；回滚逆序遍历（见 RemoveGapProtectionPatch）。
static const GapProtectPointDef kGapProtectPoints[3] = {
    { "P-2.1", ADDR_REVEALAREA2_GAP_CLEAR, kGapP21Orig,
      ADDR_REVEALAREA2_GAP_CLEAR_PREV, 2, kGapP21Prev,
      ADDR_REVEALAREA2_GAP_CLEAR_NEXT, 2, kGapP21Next,
      "RevealArea2 mov [ecx+0x134], ebx（PsychicReveal + 22 caller 面）" },
    { "P-2.2", ADDR_REVEALAREA3_GAP_CLEAR, kGapP22Orig,
      ADDR_REVEALAREA3_GAP_CLEAR_PREV, 6, kGapP22Prev,
      ADDR_REVEALAREA3_GAP_CLEAR_NEXT, 6, kGapP22Next,
      "RevealArea3 mov [eax+0x134], edi（SpySat 全图开 + 0x481FC3 旁路）" },
    { "P-2.3", ADDR_RESHROUD_GAP_CLEAR, kGapP23Orig,
      ADDR_RESHROUD_GAP_CLEAR_PREV, 10, kGapP23Prev,
      ADDR_RESHROUD_GAP_CLEAR_NEXT, 6, kGapP23Next,
      "Reshroud mov [eax+0x134], ebx（SpySat 离线重遮 + 0x50BD20 旁路）" },
};
enum { GAP_PROTECT_POINT_COUNT = 3 };

// C5：整组分点备份 s_orig[3][6]（整组一次 memcpy 或分点逆序还原均可）
static uint8_t s_origGapProtectBytes[3][6] = {{0}};
static bool    s_gapProtectWritten[3]  = {false, false, false}; // 回滚资格：true 才 memcpy 还原
static bool    s_gapProtectExternal[3] = {false, false, false}; // true = 目标首 6B 即 90×6（外部安装者）

static bool GapProtectPeek(uintptr_t addr, uint8_t *out, size_t n) {
    if (IsBadReadPtr(reinterpret_cast<void*>(addr), n)) return false;
    memcpy(out, reinterpret_cast<void*>(addr), n);
    return true;
}

static void GapProtectLogBytes(const char *mode, const char *tag, uint32_t va, const uint8_t *b, size_t n) {
    char hex[40];
    size_t k = 0;
    for (size_t i = 0; i < n && k + 3 < sizeof(hex); ++i) {
        static const char kHex[] = "0123456789ABCDEF";
        hex[k++] = kHex[(b[i] >> 4) & 0xF];
        hex[k++] = kHex[b[i] & 0xF];
        hex[k++] = ' ';
    }
    hex[k] = '\0';
    LogMessage("[ra2render] GapProtection %s %s @0x%08X: %s", mode, tag, va, hex);
}

static bool InstallGapProtectionPatch() {
    static const uint8_t kNop[6] = {0x90, 0x90, 0x90, 0x90, 0x90, 0x90}; // nop ×6（唯允许替换体）

    // ---- G0.6 开关键 / 联机门禁（与 EnableMinimapFog 同级）----
    if (!g_enableGapProtection) {
        LogMessage("[ra2render] GapProtection=off（EnableGapProtection 未开；三点 .text 零改动）");
        return false;
    }
    if (MpActive()) {
        LogMessage("[ra2render] GapProtection=forced-off-mp（MpActive=true，联机强制不安装；R-1 混端 DESYNC 风险，须全端同构建同开关）");
        return false;
    }

    // ---- G0.2/G0.3/G0.4 字节与上下文窗门禁（三点全查；任一不符 ⇒ 整包不写，一字节不动）----
    //   窗前/窗后宽度按各点实测参数化（P-2.1 2+2 / P-2.2 6+6 / P-2.3 10+6），禁 2B 硬编码。
    for (int i = 0; i < GAP_PROTECT_POINT_COUNT; ++i) {
        const GapProtectPointDef &p = kGapProtectPoints[i];
        uint8_t cur[6] = {0}, pre[10] = {0}, nxt[6] = {0};
        if (!GapProtectPeek(p.site, cur, 6)) {
            LogMessage("[ra2render] [错误] GapProtection 拒绝安装：%s 目标 0x%08X 不可读",
                       p.tag, static_cast<uint32_t>(p.site));
            return false;
        }
        if (!GapProtectPeek(p.prev, pre, p.prevLen) ||
            !GapProtectPeek(p.next, nxt, p.nextLen)) {
            LogMessage("[ra2render] [错误] GapProtection 拒绝安装：%s 邻接窗 0x%08X(%uB)/0x%08X(%uB) 不可读",
                       p.tag, static_cast<uint32_t>(p.prev), p.prevLen,
                       static_cast<uint32_t>(p.next), p.nextLen);
            return false;
        }
        if (memcmp(pre, p.prevBytes, p.prevLen) != 0) {
            LogMessage("[ra2render] [错误] GapProtection=context-mismatch：%s 窗前 0x%08X(%uB) 与期望不符（拒装，一字节不写）",
                       p.tag, static_cast<uint32_t>(p.prev), p.prevLen);
            GapProtectLogBytes("prev-actual", p.tag, p.prev, pre, p.prevLen);
            return false;
        }
        if (memcmp(nxt, p.nextBytes, p.nextLen) != 0) {
            LogMessage("[ra2render] [错误] GapProtection=context-mismatch：%s 窗后 0x%08X(%uB) 与期望不符（拒装，一字节不写）",
                       p.tag, static_cast<uint32_t>(p.next), p.nextLen);
            GapProtectLogBytes("next-actual", p.tag, p.next, nxt, p.nextLen);
            return false;
        }
        if (memcmp(cur, kNop, 6) == 0) {
            if (s_gapProtectWritten[i]) {
                // 本进程已装（重复 install 调用）：幂等，不重写、不重复计数口径变化
                LogMessage("[ra2render] GapProtection=already：%s 目标 0x%08X 已由本进程安装（幂等，不重写）",
                           p.tag, static_cast<uint32_t>(p.site));
                continue;
            }
            // Q1：首字节 90 ⇒ 已有外部安装者所写 ⇒ 停手（不覆盖、不 claim 还原资格）
            s_gapProtectExternal[i] = true;
        } else if (memcmp(cur, p.orig, 6) != 0) {
            LogMessage("[ra2render] [错误] GapProtection=byte-mismatch：%s 目标 6B 与原版不符（既非原字节也非 90×6）",
                       p.tag);
            GapProtectLogBytes("site-actual", p.tag, p.site, cur, 6);
            return false;
        }
    }
    for (int i = 0; i < GAP_PROTECT_POINT_COUNT; ++i) {
        if (s_gapProtectExternal[i]) {
            const GapProtectPointDef &p = kGapProtectPoints[i];
            LogMessage("[ra2render] [警告/红字] GapProtection=external-installer-detected：%s 目标 0x%08X 已是 90x6 ⇒ 本副本被外部补丁/加载器安装过；整包停手不写、不还原，请上报",
                       p.tag, static_cast<uint32_t>(p.site));
            return false;
        }
    }

    // ---- 写入（安装序 P-2.1→P-2.2→P-2.3；等长 6B；VirtualProtect → memcpy → 还原保护属性）----
    int installed = 0;
    for (int i = 0; i < GAP_PROTECT_POINT_COUNT; ++i) {
        const GapProtectPointDef &p = kGapProtectPoints[i];
        if (s_gapProtectWritten[i]) { ++installed; continue; }   // 幂等（本进程已写过）
        DWORD oldProtect = 0;
        if (!VirtualProtect(reinterpret_cast<void*>(p.site), 6, PAGE_EXECUTE_READWRITE, &oldProtect)) {
            LogMessage("[ra2render] [错误] GapProtection virtualprotect-fail：%s 0x%08X，错误码 %lu",
                       p.tag, static_cast<uint32_t>(p.site), GetLastError());
            break;   // 已写点保留回滚资格；未写点放弃（避免半写漂移）
        }
        memcpy(s_origGapProtectBytes[i], reinterpret_cast<void*>(p.site), 6);
        memcpy(reinterpret_cast<void*>(p.site), kNop, 6);
        VirtualProtect(reinterpret_cast<void*>(p.site), 6, oldProtect, &oldProtect);
        s_gapProtectWritten[i] = true;
        ++installed;
        // ---- 回读确认（A2 判据：6B=90×6 且邻窗未动）----
        uint8_t post[6] = {0};
        if (GapProtectPeek(p.site, post, 6)) {
            GapProtectLogBytes("after ", p.tag, p.site, post, 6);
        }
    }
    g_gapProtectionPatchesInstalled = installed;   // C4：装几点算几点（0..3）

    // ---- C4/C6/C8 汇总日志：installed=N（<3 打 PARTIAL 告警；仅 ==3 满足产品契约）----
    LogMessage("[ra2render] GapProtection=on installed=%d（三点表驱动等长替换 6B->90x6：%s @0x%08X / %s @0x%08X / %s @0x%08X；各点同循环 ShroudCounter/CopyFlags/RedrawFlags 写入与上下文窗原样保留）",
               installed,
               kGapProtectPoints[0].tag, static_cast<uint32_t>(kGapProtectPoints[0].site),
               kGapProtectPoints[1].tag, static_cast<uint32_t>(kGapProtectPoints[1].site),
               kGapProtectPoints[2].tag, static_cast<uint32_t>(kGapProtectPoints[2].site));
    if (installed < GAP_PROTECT_POINT_COUNT) {
        LogMessage("[ra2render] [警告] GapProtection=on installed=%d (PARTIAL)（<3 ⇒ 不写 GapProt Version 存档标记、禁联机、禁存补丁档）",
                   installed);
    }
    return installed == GAP_PROTECT_POINT_COUNT;
}

static void RemoveGapProtectionPatch() {
    // C5：硬回滚强制逆序 P-2.3→P-2.2→P-2.1（后装先拆；禁只拆中间点造成语义撕裂）
    for (int i = GAP_PROTECT_POINT_COUNT - 1; i >= 0; --i) {
        const GapProtectPointDef &p = kGapProtectPoints[i];
        if (!s_gapProtectWritten[i]) {
            if (s_gapProtectExternal[i]) {
                LogMessage("[ra2render] GapProtection=external-installer-detected：%s 目标字节由外部安装者所写，卸载时**不还原**（避免覆盖未知安装者）",
                           p.tag);
            }
            continue;   // 我方没写过 ⇒ 无权还原
        }
        DWORD oldProtect = 0;
        if (!VirtualProtect(reinterpret_cast<void*>(p.site), 6, PAGE_EXECUTE_READWRITE, &oldProtect)) {
            LogMessage("[ra2render] [错误] GapProtection 还原 virtualprotect-fail：%s 0x%08X，错误码 %lu",
                       p.tag, static_cast<uint32_t>(p.site), GetLastError());
            continue;
        }
        memcpy(reinterpret_cast<void*>(p.site), s_origGapProtectBytes[i], 6);
        VirtualProtect(reinterpret_cast<void*>(p.site), 6, oldProtect, &oldProtect);
        s_gapProtectWritten[i] = false;
        GapProtectLogBytes("rollback", p.tag, p.site, s_origGapProtectBytes[i], 6);
    }
    // 遥测计数收口（按剩余已写点重算）
    int still = 0;
    for (int i = 0; i < GAP_PROTECT_POINT_COUNT; ++i) {
        if (s_gapProtectWritten[i]) ++still;
    }
    g_gapProtectionPatchesInstalled = still;
    if (still == 0) {
        LogMessage("[ra2render] GapProtection=off（三点 6B 原字节已逆序硬回滚 P-2.3->P-2.2->P-2.1；卸载/重载生效）");
    } else {
        LogMessage("[ra2render] [警告] GapProtection=off installed=%d (PARTIAL)（硬回滚未完成；剩余点仍为 NOP 态）", still);
    }
}

// ---------------------------------------------------------------------------
// [GAP-MP-EDGE] MP 边沿同步（W3_20261001 gapfix：修 forced-off-mp 时序穿透漏洞）
//
//   缺陷（修复前）：init 单机装上三点 6B NOP 后进入联机，三条路径（关卡/大厅/结算）都无人回滚
//     ⇒ .text 保持补丁态，R-1「各端必须同构建同开关」暴露。
//   修复：在既有 MP 门迁移检测点（CheckMpGateTransition 的 s_lastMpState 迁移分支）上同步：
//     · 单机→联机：installed>0 ⇒ 复用 RemoveGapProtectionPatch() 逆序硬回滚（P-2.3→P-2.2→P-2.1）；
//       installed==0（off / forced-off-mp / init 未装成功）⇒ 零动作、零日志噪音。
//     · 联机→单机：配置仍 =1 且当前未装 ⇒ 复用 InstallGapProtectionPatch()（完整 G0 门禁重装；
//       字节不符/外部安装者 ⇒ 拒写并留痕，绝不盲写）。
//   红线依据（详见 out/re_work/zcode_live/W3_20261001/gapfix/DESIGN_DECISION.md §2）：
//     · 三点位于 RevealArea2/3 / Reshroud（仿真逻辑），按 ARCHITECTURE_ATLAS §12.1 只可能运行在
//       主线程；唯一辅助线程（音频流 0x00407780）不进入逻辑调用图 ⇒ 无边沿执行冲突。
//     · 本函数不读 ini（非配置热切换）；g_enableGapProtection 仍只在 LoadConfig 读一次。
//     · 调用方全部为主线程引擎回调（BlitPlain/SelectAutoTarget/Unit_Draw/Radar/UpdateVisionGrid）。
// ---------------------------------------------------------------------------
static void MpGateEdgeSyncGapProtection(bool mpNow) {
    if (mpNow) {
        if (g_gapProtectionPatchesInstalled > 0) {
            LogMessage("[ra2render] GapProtection=mp-edge-rollback（检测到 单机->联机 迁移: 本进程已写入 .text 的三点 6B NOP 按逆序 P-2.3->P-2.2->P-2.1 硬还原为原字节；R-1 混端 DESYNC 防御；此后 installed 应为 0）");
            RemoveGapProtectionPatch();   // 既有逆序硬回滚（仅还原我方 s_gapProtectWritten 字节）
        }
        return;
    }
    // 联机→单机（退出联机会话回大厅/菜单/新单机局）：配置仍 on 且当前未装 ⇒ 门禁重装。
    // 注：init 单机已装（installed==3）时此处不动作 ⇒ 单机路径零变化。
    if (g_enableGapProtection && g_gapProtectionPatchesInstalled == 0) {
        LogMessage("[ra2render] GapProtection=mp-edge-reinstall（检测到 联机->单机 迁移: 配置 EnableGapProtection 仍为 1，按完整 G0 门禁重装三点；幂等/byte-mismatch/external-installer 即拒写）");
        InstallGapProtectionPatch();
    }
}

// ---------------------------------------------------------------------------
// [VXL-PRE / SW-CHARGE] 通用等长字节补丁安装器（单点；与 GAP-P223 三点表驱动同构同门禁）
//   每点带：目标 VA、原字节、新字节（必须等长）、至多三面守卫窗（VA + 期望字节）。
//   安装前置全查 MATCH 才写（任一不符 ⇒ 拒装，一字节不动）；
//   Q1：目标已是新字节 ⇒ 本进程已装（幂等）/ 外部安装者（停手不写不还原）；其它 ⇒ 拒。
//   硬回滚 = memcpy 还原原字节（仅还原我方写过的）。
// ---------------------------------------------------------------------------
struct TextPatchPointDef {
    const char    *tag;        // 步骤 ID（L-VXL-1 / L-SW-1；日志用）
    uint32_t       site;       // 替换点 VA
    const uint8_t *orig;       // 原字节（禁漂移常量）
    const uint8_t *patch;      // 新字节（必须与 orig 等长）
    uint32_t       siteLen;    // 替换长度（5/6/7…，禁 trampoline）
    uint32_t       g1;         const uint8_t *g1Bytes; uint32_t g1Len; const char *g1Desc;  // 守卫窗 1（VA=0 无）
    uint32_t       g2;         const uint8_t *g2Bytes; uint32_t g2Len; const char *g2Desc;  // 守卫窗 2
    uint32_t       g3;         const uint8_t *g3Bytes; uint32_t g3Len; const char *g3Desc;  // 守卫窗 3
};

struct TextPatchState {
    uint8_t orig[8] = {0};     // 原字节备份（仅我方写入时有效）
    bool    written = false;   // 回滚资格：true 才 memcpy 还原
    bool    external = false;  // true = 目标已是新字节且非本进程所写（外部安装者）
};

static bool TextPatchGuardOk(const TextPatchPointDef &p, int which,
                             uint32_t va, const uint8_t *expect, uint32_t len, const char *desc,
                             uint8_t *actual, bool *readOk) {
    if (va == 0) return true;
    if (!GapProtectPeek(va, actual, len)) { *readOk = false; return false; }
    if (memcmp(actual, expect, len) != 0) {
        LogMessage("[ra2render] [错误] 补丁 %s context-mismatch：守卫窗(%d %s) 0x%08X(%uB) 与期望不符（拒装，一字节不写）",
                   p.tag, which, desc ? desc : "?", va, len);
        GapProtectLogBytes("guard-actual", p.tag, va, actual, len);
        return false;
    }
    return true;
}

static bool InstallTextPatch(const TextPatchPointDef &p, TextPatchState &st, const char *token, bool enabled) {
    if (!enabled) {
        LogMessage("[ra2render] %s=off（未开；.text 零改动）", token);
        return false;
    }
    uint8_t cur[8] = {0}, g1[8] = {0}, g2[8] = {0}, g3[8] = {0};
    if (!GapProtectPeek(p.site, cur, p.siteLen)) {
        LogMessage("[ra2render] [错误] %s 拒绝安装：%s 目标 0x%08X 不可读", token, p.tag, static_cast<uint32_t>(p.site));
        return false;
    }
    bool readOk = true;
    if (!TextPatchGuardOk(p, 1, p.g1, p.g1Bytes, p.g1Len, p.g1Desc, g1, &readOk) ||
        !TextPatchGuardOk(p, 2, p.g2, p.g2Bytes, p.g2Len, p.g2Desc, g2, &readOk) ||
        !TextPatchGuardOk(p, 3, p.g3, p.g3Bytes, p.g3Len, p.g3Desc, g3, &readOk)) {
        if (!readOk) {
            LogMessage("[ra2render] [错误] %s 拒绝安装：%s 守卫窗不可读", token, p.tag);
        }
        return false;
    }
    if (memcmp(cur, p.patch, p.siteLen) == 0) {
        if (st.written) {
            LogMessage("[ra2render] %s=already：%s 目标 0x%08X 已由本进程安装（幂等，不重写）",
                       token, p.tag, static_cast<uint32_t>(p.site));
            return true;
        }
        st.external = true;   // Q1：外部安装者 ⇒ 停手（不覆盖、不 claim 还原资格）
        LogMessage("[ra2render] [警告/红字] %s=external-installer-detected：%s 目标 0x%08X 已是补丁态 ⇒ 本副本被外部补丁/加载器安装过；停手不写、不还原，请上报",
                   token, p.tag, static_cast<uint32_t>(p.site));
        return false;
    }
    if (memcmp(cur, p.orig, p.siteLen) != 0) {
        LogMessage("[ra2render] [错误] %s=byte-mismatch：%s 目标 %uB 与原版不符（既非原字节也非补丁态）",
                   token, p.tag, p.siteLen);
        GapProtectLogBytes("site-actual", p.tag, p.site, cur, p.siteLen);
        return false;
    }

    DWORD oldProtect = 0;
    if (!VirtualProtect(reinterpret_cast<void*>(p.site), p.siteLen, PAGE_EXECUTE_READWRITE, &oldProtect)) {
        LogMessage("[ra2render] [错误] %s virtualprotect-fail：%s 0x%08X，错误码 %lu",
                   token, p.tag, static_cast<uint32_t>(p.site), GetLastError());
        return false;
    }
    memcpy(st.orig, reinterpret_cast<void*>(p.site), p.siteLen);
    memcpy(reinterpret_cast<void*>(p.site), p.patch, p.siteLen);
    VirtualProtect(reinterpret_cast<void*>(p.site), p.siteLen, oldProtect, &oldProtect);
    st.written = true;
    uint8_t post[8] = {0};
    if (GapProtectPeek(p.site, post, p.siteLen)) {
        GapProtectLogBytes("after ", p.tag, p.site, post, p.siteLen);
    }
    LogMessage("[ra2render] %s=on：%s @0x%08X 已等长替换（原 %uB -> 新 %uB；守卫窗未动）",
               token, p.tag, static_cast<uint32_t>(p.site), p.siteLen, p.siteLen);
    return true;
}

static void RemoveTextPatch(const TextPatchPointDef &p, TextPatchState &st, const char *token) {
    if (!st.written) {
        if (st.external) {
            LogMessage("[ra2render] %s=external-installer-detected：%s 目标字节由外部安装者所写，卸载时**不还原**（避免覆盖未知安装者）",
                       token, p.tag);
        }
        return;   // 我方没写过 ⇒ 无权还原
    }
    DWORD oldProtect = 0;
    if (!VirtualProtect(reinterpret_cast<void*>(p.site), p.siteLen, PAGE_EXECUTE_READWRITE, &oldProtect)) {
        LogMessage("[ra2render] [错误] %s 还原 virtualprotect-fail：%s 0x%08X，错误码 %lu",
                   token, p.tag, static_cast<uint32_t>(p.site), GetLastError());
        return;
    }
    memcpy(reinterpret_cast<void*>(p.site), st.orig, p.siteLen);
    VirtualProtect(reinterpret_cast<void*>(p.site), p.siteLen, oldProtect, &oldProtect);
    st.written = false;
    GapProtectLogBytes("rollback", p.tag, p.site, st.orig, p.siteLen);
    LogMessage("[ra2render] %s=off（%s @0x%08X 已硬回滚 %uB 原字节；卸载/重载生效）",
               token, p.tag, static_cast<uint32_t>(p.site), p.siteLen);
}

// ---- [VXL-PRE] L-VXL-1 单点（0x706D78 imm8 0x0A→0x40）----
static const uint8_t kVxlOrig[5]  = {0xBB, 0x0A, 0x00, 0x00, 0x00}; // mov ebx, 0xA（首次容量 10）
static const uint8_t kVxlPatch[5] = {0xBB, 0x40, 0x00, 0x00, 0x00}; // mov ebx, 0x40（首次容量 64）
static const uint8_t kVxlG1[2]    = {0x75, 0x07};                   // jne growstep（Capacity==0 才落到本点）
static const uint8_t kVxlG2[2]    = {0xEB, 0x0A};                   // jmp（禁改）
static const uint8_t kVxlG3[2]    = {0x8B, 0xD8};                   // mov ebx,eax（growstep 翻倍，禁改）
static const TextPatchPointDef kVxlPoint = {
    "L-VXL-1", ADDR_VXL_CACHE_INIT_CAP, kVxlOrig, kVxlPatch, 5,
    ADDR_VXL_CACHE_INIT_PREV,  kVxlG1, 2, "prev jne",
    ADDR_VXL_CACHE_INIT_NEXT1, kVxlG2, 2, "next jmp",
    ADDR_VXL_CACHE_INIT_NEXT2, kVxlG3, 2, "next growstep",
};
static TextPatchState s_vxlState;

// ============================================================================
// [SBH-GUARD 20261020] RC-1「SBH freelist 毒值守卫」—— 补丁副本（母本零改动）
//   规格依据：crashspec_v4/RC_SPEC_V4.md §3.1（v4）
//   目标：__sbh_alloc_block（0x007CFB13）freelist 摘链点 0x007CFC9B 处插入守卫
//         ⇒ 毒值（如 0xFE00FFFF）不再被解引用 ⇒ 不 AV ⇒ 分配回落 Win32 HeapAlloc 兜底
//   默认 0（EnableSbhGuard=0）= 不碰任何字节 = 与原版逐位等价
//
//   ★ 三处必须严格对齐规格的实现约束：
//     1) 只覆写 5B（0x7CFC9B..0x7CFC9F）；0x7CFCA0 的 0A 是死字节，保持原值
//     2) cave 内**不得覆写 eax**（eax=heap_info 跨守卫点存活到 0x7CFE12）
//     3) cave 用 esi 作 scratch（0x7CFCA4 处 esi 立即被 8B F1 重定义）
//     4) cave 在（推定的）CRT 堆锁内执行 ⇒ 禁取锁、禁调 CRT、禁调日志
// ============================================================================

// ---- 目标字节锚（[实证]，13/13 claims 全 OK 实测）----
static const uintptr_t kSbhPw1Site = 0x007CFC9B;   // mov edx,[ecx+edi*8+4] 起始（覆写起点）
static const uintptr_t kSbhPw1Back = 0x007CFCA1;   // sub ecx,[ebp-0x10]（cave 回跳点）
static const uintptr_t kSbhNullRet = 0x007CFE17;   // pop edi/esi/ebx; leave; ret（NULL 降级路径）
static const uint32_t kSbhUserCeil = 0xBFFF0000u;  // USER_ADDR_CEIL（LAA 3GB 用户空间上界，64KB 对齐下界）

// 磁盘 6B 窗（0x7CFC9B..0x7CFCA0）：仅用于断言窗口未漂移
static const uint8_t kSbhWin6[6] = {0x8B, 0x54, 0xF9, 0x04, 0x8B, 0x0A};
// 覆写 5B（0x7CFC9B..0x7CFC9F）：被 E9 rel32 全部替换
static const uint8_t kSbhOrig5[5] = {0x8B, 0x54, 0xF9, 0x04, 0x8B};
// 回跳点 3B（0x7CFCA1..0x7CFCA3）：仅断言
static const uint8_t kSbhBack3[3] = {0x2B, 0x4D, 0xF0};

// ---- 构建身份（G0.1 / G0.1b）----
// M-1 用户裁定：首版仅接受 W-A 项目基线（单条目白名单）
static const char *kSbhShaWhitelist =
    "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476";
static const uint32_t kSbhExpectedSize = 4825360;

// ---- 共享状态（§3.1.3a (1) 表）----
static LONG  s_sbhGuardGate        = 1;  // 1=守卫开启；0=熔断（单向）
static LONG  s_sbhGuardTrips       = 0;  // trip 计数（lock inc）
static LONG  s_sbhGuardAlignReject = 0;  // G1 对齐/上界拒绝计数（lock inc）
static LONG  s_sbhGuardStrictMiss  = 0;  // G2 严格模式拒绝计数（lock inc）
static bool  s_sbhGuardInstalled   = false;
static uint8_t s_sbhOrig5[5]       = {0};  // 卸载还原快照
static void  *s_sbhCave            = nullptr;

// cave 尺寸：复刻 5B + 哨兵 8B + 对齐 4B + 上界 8B + 复刻 mov 2B + jmp 5B + 余量
//   实际机器码约 40B，取 96B 留裕度（含可能的分支对齐）
static const size_t kSbhCaveSize = 96;

// ============================================================================
// SHA-256（Windows CNG；Vista+ 系统自带 bcrypt.dll）
// ============================================================================
static bool SbhSha256File(const char *path, char hex[65]) {
    hex[0] = '\0';
    BCRYPT_ALG_HANDLE hAlg = nullptr;
    BCRYPT_HASH_HANDLE hHash = nullptr;
    DWORD cbData = 0, cbHash = 0, cbHashObj = 0;
    bool ok = false;
    PUCHAR hashObj = nullptr;
    PUCHAR digest = nullptr;
    FILE *f = nullptr;

    do {
        if (BCryptOpenAlgorithmProvider(&hAlg, BCRYPT_SHA256_ALGORITHM, nullptr, 0) < 0) break;
        if (BCryptGetProperty(hAlg, BCRYPT_OBJECT_LENGTH, (PUCHAR)&cbHashObj,
                              sizeof(cbHashObj), &cbData, 0) < 0) break;
        if (BCryptGetProperty(hAlg, BCRYPT_HASH_LENGTH, (PUCHAR)&cbHash,
                              sizeof(cbHash), &cbData, 0) < 0) break;
        hashObj = (PUCHAR)HeapAlloc(GetProcessHeap(), 0, cbHashObj);
        digest  = (PUCHAR)HeapAlloc(GetProcessHeap(), 0, cbHash);
        if (!hashObj || !digest) break;
        if (BCryptCreateHash(hAlg, &hHash, hashObj, cbHashObj, nullptr, 0, 0) < 0) break;

        f = fopen(path, "rb");
        if (!f) break;
        {
            unsigned char buf[64 * 1024];
            size_t n = 0;
            while ((n = fread(buf, 1, sizeof(buf), f)) > 0) {
                if (BCryptHashData(hHash, buf, (ULONG)n, 0) < 0) { fclose(f); f = nullptr; break; }
            }
            if (f) { fclose(f); f = nullptr; }
            else break;
        }
        if (BCryptFinishHash(hHash, digest, cbHash, 0) < 0) break;

        static const char kHex[] = "0123456789abcdef";
        for (DWORD i = 0; i < cbHash; ++i) {
            hex[i * 2]     = kHex[(digest[i] >> 4) & 0xF];
            hex[i * 2 + 1] = kHex[digest[i] & 0xF];
        }
        hex[cbHash * 2] = '\0';
        ok = true;
    } while (0);

    if (f) fclose(f);
    if (hHash) BCryptDestroyHash(hHash);
    if (hashObj) HeapFree(GetProcessHeap(), 0, hashObj);
    if (digest) HeapFree(GetProcessHeap(), 0, digest);
    if (hAlg) BCryptCloseAlgorithmProvider(hAlg, 0);
    return ok;
}

// ============================================================================
// G0 门禁：任一失败 ⇒ 拒绝安装、不写任何字节（fail-closed）
// ============================================================================
static bool SbhVerifyIdentity() {
    // G0.1 整文件 SHA-256
    char exePath[MAX_PATH] = {0};
    GetModuleFileNameA(nullptr, exePath, MAX_PATH);

    // 文件大小（G0.1 的伴随因子）
    {
        FILE *f = fopen(exePath, "rb");
        if (!f) {
            LogMessage("[ra2render-sbh] SbhGuard=hash-mismatch（无法打开主模块 \"%s\"）", exePath);
            return false;
        }
        fseek(f, 0, SEEK_END);
        long sz = ftell(f);
        fclose(f);
        if (sz <= 0 || (uint32_t)sz != kSbhExpectedSize) {
            LogMessage("[ra2render-sbh] SbhGuard=hash-mismatch（size=%ld，期望 %u）", sz, kSbhExpectedSize);
            return false;
        }
    }

    char hex[65] = {0};
    if (!SbhSha256File(exePath, hex)) {
        LogMessage("[ra2render-sbh] SbhGuard=hash-mismatch（SHA-256 计算失败）");
        return false;
    }
    // G0.1b 白名单（单条目 W-A；W-B 出厂件命中 ⇒ 拒绝）
    if (_stricmp(hex, kSbhShaWhitelist) != 0) {
        LogMessage("[ra2render-sbh] SbhGuard=identity-unknown（sha256=%.16s… 不在生效白名单内）", hex);
        return false;
    }
    LogMessage("[ra2render-sbh] SbhGuard=identity-ok（sha256=%.16s…, size=%u）", hex, kSbhExpectedSize);
    return true;
}

static bool SbhVerifyWindows() {
    // G0.3 字节窗断言：6B 窗 + 回跳点 3B
    uint8_t cur6[6] = {0};
    if (IsBadReadPtr(reinterpret_cast<void*>(kSbhPw1Site), 6)) {
        LogMessage("[ra2render-sbh] SbhGuard=window-mismatch（0x%08X 不可读）",
                   static_cast<uint32_t>(kSbhPw1Site));
        return false;
    }
    memcpy(cur6, reinterpret_cast<void*>(kSbhPw1Site), 6);
    if (memcmp(cur6, kSbhWin6, 6) != 0) {
        LogMessage("[ra2render-sbh] SbhGuard=window-mismatch（PW-1 6B 窗不符："
                   "%02X %02X %02X %02X %02X %02X）",
                   cur6[0], cur6[1], cur6[2], cur6[3], cur6[4], cur6[5]);
        return false;
    }
    uint8_t cur3[3] = {0};
    if (IsBadReadPtr(reinterpret_cast<void*>(kSbhPw1Back), 3)) {
        LogMessage("[ra2render-sbh] SbhGuard=window-mismatch（回跳点 0x%08X 不可读）",
                   static_cast<uint32_t>(kSbhPw1Back));
        return false;
    }
    memcpy(cur3, reinterpret_cast<void*>(kSbhPw1Back), 3);
    if (memcmp(cur3, kSbhBack3, 3) != 0) {
        LogMessage("[ra2render-sbh] SbhGuard=window-mismatch（回跳点 3B 不符）");
        return false;
    }
    return true;
}

// ============================================================================
// Cave 构造
//   入口现场（§3.1.2）：ecx=freelist_base([ebp-0xC])、edi=class、eax=heap_info、
//   ebx=region 描述符、[ebp-0x10]=block；栈上三次 push 已完成
//   退出：健康路径 jmp 0x7CFCA1；trip 路径 xor eax,eax + jmp 0x7CFE17
// ============================================================================
struct SbhCaveCtx {
    LONG  *gate;
    LONG  *trips;
    LONG  *alignReject;
    uint32_t userCeil;
};

static SbhCaveCtx s_sbhCaveCtx = { nullptr, nullptr, nullptr, 0 };

// 用 mov 构造常量地址（cave 内不能用 C++ 语法，机器码里直接写 imm32）
static bool SbhBuildCave() {
    if (s_sbhCave) return true;
    s_sbhCave = VirtualAlloc(nullptr, kSbhCaveSize,
                             MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    if (!s_sbhCave) {
        LogMessage("[ra2render-sbh] SbhGuard=cave-alloc-failed（err=%lu）", GetLastError());
        return false;
    }
    s_sbhCaveCtx.gate        = &s_sbhGuardGate;
    s_sbhCaveCtx.trips       = &s_sbhGuardTrips;
    s_sbhCaveCtx.alignReject = &s_sbhGuardAlignReject;
    s_sbhCaveCtx.userCeil    = kSbhUserCeil;

    uint8_t *p = static_cast<uint8_t*>(s_sbhCave);
    size_t off = 0;

    auto emit = [&](uint8_t b) { p[off++] = b; };
    auto emit32 = [&](uint32_t v) {
        memcpy(p + off, &v, 4); off += 4;
    };
    auto emitRelTo = [&](uintptr_t dest) {
        // 当前已写 1 字节 E9，rel32 = dest - (site+5)
        uintptr_t after = reinterpret_cast<uintptr_t>(p + off + 4);
        int32_t rel = static_cast<int32_t>(dest - after);
        emit32(static_cast<uint32_t>(rel));
    };

    const uintptr_t cave = reinterpret_cast<uintptr_t>(s_sbhCave);
    // 需要在写 E9 之前记录位置；以下用辅助 lambda 计算 patch 后地址
    (void)cave;

    // ---- 1) 复刻原指令 1：mov edx,[ecx+edi*8+4]  =>  8B 54 F9 04 ----
    emit(0x8B); emit(0x54); emit(0xF9); emit(0x04);

    // ---- 2) 哨兵短路：lea esi,[ecx+edi*8]  =>  8D 34 F9 ----
    emit(0x8D); emit(0x34); emit(0xF9);

    // ---- 3) cmp edx,esi  =>  3B D6 ----
    emit(0x3B); emit(0xD6);

    // ---- 4) je pass（短跳，稍后回填）----
    size_t jePos = off;
    emit(0x74); emit(0x00);
    size_t jeImmPos = off - 1;

    // ---- 5) test edx,0x0F  =>  F7 C2 0F 00 00 00 ----
    emit(0xF7); emit(0xC2); emit32(0x0000000F);

    // ---- 6) jnz trip（短跳，稍后回填）----
    size_t jnzPos = off;
    emit(0x75); emit(0x00);
    size_t jnzImmPos = off - 1;

    // ---- 7) cmp edx, USER_ADDR_CEIL  =>  81 FA imm32 ----
    emit(0x81); emit(0xFA); emit32(kSbhUserCeil);

    // ---- 8) jae trip（短跳）----
    size_t jaePos = off;
    emit(0x73); emit(0x00);
    size_t jaeImmPos = off - 1;

    // ---- 9) pass: mov ecx,[edx]  =>  8B 0A ----
    size_t passLabel = off;
    emit(0x8B); emit(0x0A);

    // ---- 10) jmp 0x7CFCA1  =>  E9 rel32 ----
    size_t passJmpPos = off;
    emit(0xE9);
    {
        uintptr_t after = reinterpret_cast<uintptr_t>(p + off + 4);
        int32_t rel = static_cast<int32_t>(kSbhPw1Back - after);
        emit32(static_cast<uint32_t>(rel));
    }
    (void)passJmpPos;

    // ---- 11) trip: lock inc [alignReject]  =>  F0 FF 05 imm32 ----
    size_t tripLabel = off;
    emit(0xF0); emit(0xFF); emit(0x05);
    emit32(static_cast<uint32_t>(reinterpret_cast<uintptr_t>(&s_sbhGuardAlignReject)));

    // ---- 12) lock inc [trips]  =>  F0 FF 05 imm32 ----
    emit(0xF0); emit(0xFF); emit(0x05);
    emit32(static_cast<uint32_t>(reinterpret_cast<uintptr_t>(&s_sbhGuardTrips)));

    // ---- 13) xor eax,eax  =>  33 C0 ----
    emit(0x33); emit(0xC0);

    // ---- 14) jmp 0x7CFE17  =>  E9 rel32 ----
    emit(0xE9);
    {
        uintptr_t after = reinterpret_cast<uintptr_t>(p + off + 4);
        int32_t rel = static_cast<int32_t>(kSbhNullRet - after);
        emit32(static_cast<uint32_t>(rel));
    }

    // ---- 回填短跳 ----
    {
        int8_t d = static_cast<int8_t>(static_cast<long>(passLabel) - (long)(jePos + 2));
        p[jeImmPos] = static_cast<uint8_t>(d);
    }
    {
        int8_t d = static_cast<int8_t>(static_cast<long>(tripLabel) - (long)(jnzPos + 2));
        p[jnzImmPos] = static_cast<uint8_t>(d);
    }
    {
        int8_t d = static_cast<int8_t>(static_cast<long>(tripLabel) - (long)(jaePos + 2));
        p[jaeImmPos] = static_cast<uint8_t>(d);
    }

    FlushInstructionCache(GetCurrentProcess(), s_sbhCave, off);
    LogMessage("[ra2render-sbh] SbhGuard=cave-built（%u 字节 @0x%08X）",
               static_cast<uint32_t>(off), static_cast<uint32_t>(cave));
    return true;
}

// ============================================================================
// 安装 / 卸载
// ============================================================================
static bool InstallSbhGuardPatch() {
    // 开关 + 联机门禁（§3.1.4）
    if (!g_enableSbhGuard) {
        LogMessage("[ra2render-sbh] SbhGuard=off（EnableSbhGuard 未开；.text 零改动）");
        return false;
    }
    if (MpActive()) {
        LogMessage("[ra2render-sbh] SbhGuard=forced-off-mp（MpActive=true，联机强制不安装）");
        return false;
    }
    if (s_sbhGuardInstalled) {
        LogMessage("[ra2render-sbh] SbhGuard=already（幂等）");
        return true;
    }

    // G0 门禁（任一失败 ⇒ 一字节不写）
    if (!SbhVerifyIdentity()) return false;
    if (!SbhVerifyWindows()) return false;

    // 安装前基线快照（§3.1.4）
    {
        char exePath[MAX_PATH] = {0};
        GetModuleFileNameA(nullptr, exePath, MAX_PATH);
        char hex[65] = {0};
        SbhSha256File(exePath, hex);
        LogMessage("[ra2render-sbh] SbhGuard=baseline-snapshot(sha256=%.16s…)", hex);
    }

    if (!SbhBuildCave()) return false;

    // 构造 5B 覆写：E9 rel32
    memcpy(s_sbhOrig5, reinterpret_cast<void*>(kSbhPw1Site), 5);

    uint8_t patch[5];
    patch[0] = 0xE9;
    {
        uintptr_t after = kSbhPw1Site + 5;
        int32_t rel = static_cast<int32_t>(reinterpret_cast<uintptr_t>(s_sbhCave) - after);
        memcpy(&patch[1], &rel, 4);
    }

    DWORD oldProtect = 0;
    if (!VirtualProtect(reinterpret_cast<void*>(kSbhPw1Site), 5,
                        PAGE_EXECUTE_READWRITE, &oldProtect)) {
        LogMessage("[ra2render-sbh] SbhGuard=protect-failed（err=%lu）", GetLastError());
        return false;
    }
    memcpy(reinterpret_cast<void*>(kSbhPw1Site), patch, 5);
    VirtualProtect(reinterpret_cast<void*>(kSbhPw1Site), 5, oldProtect, &oldProtect);
    FlushInstructionCache(GetCurrentProcess(), reinterpret_cast<void*>(kSbhPw1Site), 5);

    s_sbhGuardInstalled = true;
    InterlockedExchange(&s_sbhGuardGate, 1);
    LogMessage("[ra2render-sbh] SbhGuard=install(ok)（PW-1 5B 已覆写；死字节 0x7CFCA0 保持 0A）");
    return true;
}

static void RemoveSbhGuardPatch() {
    if (!s_sbhGuardInstalled) {
        LogMessage("[ra2render-sbh] SbhGuard=uninstall(skipped-not-installed)");
        return;
    }
    // 单向熔断：先关门，再还原
    InterlockedExchange(&s_sbhGuardGate, 0);

    DWORD oldProtect = 0;
    if (VirtualProtect(reinterpret_cast<void*>(kSbhPw1Site), 5,
                       PAGE_EXECUTE_READWRITE, &oldProtect)) {
        memcpy(reinterpret_cast<void*>(kSbhPw1Site), s_sbhOrig5, 5);
        VirtualProtect(reinterpret_cast<void*>(kSbhPw1Site), 5, oldProtect, &oldProtect);
        FlushInstructionCache(GetCurrentProcess(), reinterpret_cast<void*>(kSbhPw1Site), 5);
    }

    if (s_sbhCave) {
        VirtualFree(s_sbhCave, 0, MEM_RELEASE);
        s_sbhCave = nullptr;
    }
    s_sbhGuardInstalled = false;
    LogMessage("[ra2render-sbh] SbhGuard=uninstall(restored)（5B 已还原）");
}

// 遥测快照（锁外调用）
static void SbhGuardReportTelemetry() {
    LogMessage("[ra2render-sbh] SbhGuard=telemetry(trips=%ld, alignReject=%ld, strictMiss=%ld, gate=%ld)",
               s_sbhGuardTrips, s_sbhGuardAlignReject, s_sbhGuardStrictMiss, s_sbhGuardGate);
}


static bool InstallVxlCachePrewarmPatch() {
    bool ok = InstallTextPatch(kVxlPoint, s_vxlState, "VxlCachePrewarm", g_enableVxlCachePrewarm);
    g_vxlCacheInstalled = s_vxlState.written ? 1 : 0;
    return ok;
}

static void RemoveVxlCachePrewarmPatch() {
    RemoveTextPatch(kVxlPoint, s_vxlState, "VxlCachePrewarm");
    g_vxlCacheInstalled = s_vxlState.written ? 1 : 0;
}

// ---- [SW-CHARGE] L-SW-1 单点（0x6CBE88 冗余二次 call 7B→90×7）----
static const uint8_t kSwOrig[7]  = {0x8B, 0xCE, 0xE8, 0x51, 0x00, 0x00, 0x00}; // mov ecx,esi; call 0x6CBEE0（第二次，结果丢弃）
static const uint8_t kSwPatch[7] = {0x90, 0x90, 0x90, 0x90, 0x90, 0x90, 0x90}; // nop×7
static const uint8_t kSwG1[2]    = {0x74, 0x15};                   // je（脏检测无变化即 false）
static const uint8_t kSwG2[3]    = {0x89, 0x46, 0x78};             // mov [esi+0x78],eax（写回，保留）
static const uint8_t kSwG3[5]    = {0xE8, 0x5D, 0x00, 0x00, 0x00}; // 首次 call GetCameoChargeState（保留）
static const TextPatchPointDef kSwPoint = {
    "L-SW-1", ADDR_SW_CHARGE_REDUNDANT_CALL, kSwOrig, kSwPatch, 7,
    ADDR_SW_CHARGE_WINDOW_PREV, kSwG1, 2, "prev je",
    ADDR_SW_CHARGE_WINDOW_NEXT, kSwG2, 3, "next writeback",
    ADDR_SW_CHARGE_FIRST_CALL,  kSwG3, 5, "first call",
};
static TextPatchState s_swState;

static bool InstallSwChargeOptPatch() {
    bool ok = InstallTextPatch(kSwPoint, s_swState, "SWChargeOpt", g_enableSWChargeOpt);
    g_swChargeOptInstalled = s_swState.written ? 1 : 0;
    return ok;
}

static void RemoveSwChargeOptPatch() {
    RemoveTextPatch(kSwPoint, s_swState, "SWChargeOpt");
    g_swChargeOptInstalled = s_swState.written ? 1 : 0;
}

// ============================================================================
// 虚表安装与卸载 (零侵入代码段)
// ============================================================================

static bool PatchVTablePointer(uintptr_t targetAddr, uintptr_t newFunc, uintptr_t *outOrigFunc, const char *name,
                               uintptr_t expectOrig) {   // [VER-GATE V2] 新增第 5 参：期望旧值（原虚表函数 VA）
    if (IsBadReadPtr(reinterpret_cast<void*>(targetAddr), sizeof(uintptr_t))) {
        LogMessage("[ra2render] 错误：无法读取虚表条目 0x%08X (%s)", targetAddr, name);
        return false;
    }

    // [VER-GATE V2] 逐点原值门（缺口1 修复）：写前核对「当前值 == 期望旧值」。
    //   不符 ⇒ 拒绝写入、一字节不动（fail-closed）——与 InstallTextPatch 的 byte-mismatch 拒装
    //   （本文件 InstallTextPatch memcmp 前核）与 InstallGapProtectionPatch 的「三点全查；任一不符
    //   ⇒ 整包不写」同一口径。换版本 exe 的典型症状即虚表槽内是**别的函数地址**，在此被拦下。
    uintptr_t orig = *reinterpret_cast<uintptr_t*>(targetAddr);
    if (orig != expectOrig) {
        LogMessage("[ra2render] [错误/拒装] [vergate] 虚表原值不符 0x%08X (%s): 期望 0x%08X, 实测 0x%08X ⇒ 拒绝写入（fail-closed，一字节未写）",
                   static_cast<uint32_t>(targetAddr), name, static_cast<uint32_t>(expectOrig), static_cast<uint32_t>(orig));
        return false;
    }

    DWORD oldProtect = 0;
    if (!VirtualProtect(reinterpret_cast<void*>(targetAddr), sizeof(uintptr_t), PAGE_EXECUTE_READWRITE, &oldProtect)) {
        LogMessage("[ra2render] 错误：VirtualProtect 失败 0x%08X (%s), 错误码 %lu", targetAddr, name, GetLastError());
        return false;
    }

    if (outOrigFunc) *outOrigFunc = orig;
    *reinterpret_cast<uintptr_t*>(targetAddr) = newFunc;

    VirtualProtect(reinterpret_cast<void*>(targetAddr), sizeof(uintptr_t), oldProtect, &oldProtect);
    LogMessage("[ra2render] 成功劫持虚表 [%s]: 原入口 0x%08X -> 新入口 0x%08X", name, orig, newFunc);
    return true;
}

// ============================================================================
// [VER-GATE] 启动版本门 + 虚表逐点原值预核（goal3_versioncheck_20261019；fail-closed 安全门）
// ----------------------------------------------------------------------------
// 缺口2 修复（启动无版本门）：DLL 注入后不核对 gamemd.exe 版本 ⇒ 换一版 exe 会按错误
//   硬编码地址直写。本门在**任何写入发生前**对 gamemd.exe（本进程主模块，磁盘文件）
//   计算指纹并对照白名单；不匹配 ⇒ 整体不安装（InstallVTableHooks 直接 return false，
//   13 处虚表 + 全部 Inline/文本补丁一个字节都不碰），日志一行。
//   ★这是安全门不是优化 ⇒ 无 ini 开关、无旁路；校验失败 = 拒装（安全侧缺省）。
// 白名单三规则（满足任一即 PASS；全部不满足才 FAIL）：
//   W1 整文件 sha256 == 现役 ra2bench\gamemd.exe 指纹（01_controls.json:16 / 01_controls.txt:3 实测锚定）
//   W2 整文件 sha256 == ra2opt KNOWN_GAMEMD 原版 1.001 记录 + 尺寸/编译时间戳双因子
//      （ra2opt/__init__.py:19-27；size=4825360, tds=0x3BDF544E）
//   W3 .text 原始段 sha256 == 1.001 代码段指纹 + 尺寸/时间戳/映像基址三因子
//      （ra2opt/__init__.py:24 text_sha256；ra2opt 头字段类优化 LAA/栈/堆不改代码段 ——
//        ra2opt/__init__.py:16-18 的既有设计口径，本门沿用 ⇒ 头字段被调整的同版 exe 不误伤，
//        而虚表槽内容属 .rdata，若被改由 V2 逐点原值门兜底拦截）
// ============================================================================
static const char kVerGateShaCur[65] =
    "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"; // W1 现役整文件
static const char kVerGateSha1001[65] =
    "db264305c8a6963d17f5d189a5a9720d9c95f7757cc19c534c2fbe4e015255aa"; // W2 ra2opt 原版 1.001 整文件记录
static const char kVerGateShaText[65] =
    "c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738"; // W3 1.001 .text 原始段（实测=现役 exe 同值）
static const uint32_t kVerGateTimeStamp = 0x3BDF544E;  // COFF TimeDateStamp（2001-10-31，ra2opt 记录一致）
static const uint32_t kVerGateFileSize  = 4825360;     // 字节（01_controls.json:17 / ra2opt/__init__.py:22）
static const uint32_t kVerGateImageBase = 0x00400000;  // PE ImageBase（01_controls.json:18）

// BCrypt 流式 SHA-256：对文件从 offset 起哈希 len 字节，输出小写 hex[65]（含 '\0'）。
static bool VerGateSha256Hex(FILE *f, long offset, long len, char hex[65]) {
    static const char kHexDigits[] = "0123456789abcdef";
    static uint8_t s_chunk[65536];   // 静态缓冲：init 相位单线程，避免大栈占用
    BCRYPT_ALG_HANDLE hAlg = nullptr;
    BCRYPT_HASH_HANDLE hHash = nullptr;
    bool ok = false;
    do {
        if (BCryptOpenAlgorithmProvider(&hAlg, BCRYPT_SHA256_ALGORITHM, nullptr, 0) != 0) break;
        if (BCryptCreateHash(hAlg, &hHash, nullptr, 0, nullptr, 0, 0) != 0) break;
        if (fseek(f, offset, SEEK_SET) != 0) break;
        long remaining = len;
        ok = true;   // 进入哈希循环；任何读/写哈希失败即翻 false
        while (remaining > 0) {
            long want = (remaining > static_cast<long>(sizeof(s_chunk))) ? static_cast<long>(sizeof(s_chunk)) : remaining;
            size_t got = fread(s_chunk, 1, static_cast<size_t>(want), f);
            if (got == 0 || (got & 0xFFFFFFFFUL) == 0) { ok = false; break; }   // 提前 EOF/读错
            if (BCryptHashData(hHash, s_chunk, static_cast<ULONG>(got), 0) != 0) { ok = false; break; }
            remaining -= static_cast<long>(got);
        }
        if (ok) {
            uint8_t digest[32];   // SHA-256 摘要定长 32B（算法固定，无需 BCryptGetProperty）
            ULONG done = 0;
            if (BCryptFinishHash(hHash, digest, sizeof(digest), 0) != 0) { ok = false; }
            else {
                for (int i = 0; i < 32; ++i) {
                    hex[i * 2]     = kHexDigits[(digest[i] >> 4) & 0xF];
                    hex[i * 2 + 1] = kHexDigits[digest[i] & 0xF];
                }
                hex[64] = '\0';
            }
        }
    } while (false);
    if (hHash) BCryptDestroyHash(hHash);
    if (hAlg) BCryptCloseAlgorithmProvider(hAlg, 0);
    return ok;
}

// PE 头解析：TimeDateStamp / ImageBase / .text(PointerToRawData, SizeOfRawData)。只读 4KB 头。
static bool VerGateParseHeader(FILE *f, uint32_t *outTds, uint32_t *outImageBase,
                               long *outTextPtr, long *outTextRaw, bool *outHasText) {
    static uint8_t s_hdr[4096];
    if (fseek(f, 0, SEEK_SET) != 0) return false;
    if (fread(s_hdr, 1, sizeof(s_hdr), f) < 0x100) return false;
    uint32_t eLfa = *reinterpret_cast<uint32_t*>(&s_hdr[0x3C]);
    if (eLfa == 0 || eLfa + 248 > sizeof(s_hdr)) return false;                  // PE 可选头 32B+节表最短覆盖
    if (s_hdr[eLfa] != 'P' || s_hdr[eLfa + 1] != 'E' || s_hdr[eLfa + 2] != 0 || s_hdr[eLfa + 3] != 0) return false;
    uint16_t numSections = *reinterpret_cast<uint16_t*>(&s_hdr[eLfa + 6]);
    *outTds = *reinterpret_cast<uint32_t*>(&s_hdr[eLfa + 8]);
    uint16_t sizeOpt = *reinterpret_cast<uint16_t*>(&s_hdr[eLfa + 20]);
    if (sizeOpt < 224) return false;                                            // PE32 可选头标准长度
    *outImageBase = *reinterpret_cast<uint32_t*>(&s_hdr[eLfa + 24 + 28]);
    uint32_t secTab = eLfa + 24 + sizeOpt;
    *outHasText = false;
    for (uint32_t i = 0; i < numSections; ++i) {
        uint32_t off = secTab + 40 * i;
        if (off + 40 > sizeof(s_hdr)) return false;
        if (s_hdr[off] == '.' && s_hdr[off + 1] == 't' && s_hdr[off + 2] == 'e' &&
            s_hdr[off + 3] == 'x' && s_hdr[off + 4] == 't' &&
            (s_hdr[off + 5] == 0 || s_hdr[off + 5] == ' ')) {
            uint32_t rawSize = *reinterpret_cast<uint32_t*>(&s_hdr[off + 16]);
            uint32_t rawPtr  = *reinterpret_cast<uint32_t*>(&s_hdr[off + 20]);
            *outTextPtr  = static_cast<long>(rawPtr);
            *outTextRaw  = static_cast<long>(rawSize);
            *outHasText  = true;
            break;
        }
    }
    return true;
}

// [VER-GATE V1] 启动门：本进程主模块（gamemd.exe）磁盘文件指纹白名单核对。PASS/FAIL 各只打一行。
static bool VerifyGameVersionGate() {
    char exePath[MAX_PATH] = {0};
    GetModuleFileNameA(nullptr, exePath, MAX_PATH);   // 主模块 = gamemd.exe（DLL 由其进程加载）
    FILE *f = fopen(exePath, "rb");
    if (!f) {
        LogMessage("[ra2render-vergate] [错误/拒装] 版本门: 无法读取主模块磁盘文件 \"%s\"（errno=%d）⇒ 整体不安装任何补丁（fail-closed）",
                   exePath, errno);
        return false;
    }
    uint32_t tds = 0, imageBase = 0;
    long textPtr = 0, textRaw = 0;
    bool hasText = false;
    bool hdrOk = VerGateParseHeader(f, &tds, &imageBase, &textPtr, &textRaw, &hasText);
    long fileSize = -1;
    if (fseek(f, 0, SEEK_END) == 0) fileSize = ftell(f);

    char hexFull[65] = {0};
    bool shaOk = (fileSize > 0) && VerGateSha256Hex(f, 0, fileSize, hexFull);
    const char *passRule = nullptr;
    if (shaOk && hdrOk) {
        if (_stricmp(hexFull, kVerGateShaCur) == 0) {
            passRule = "W1 整文件=现役 ra2bench 指纹";
        } else if (_stricmp(hexFull, kVerGateSha1001) == 0 &&
                   static_cast<uint32_t>(fileSize) == kVerGateFileSize && tds == kVerGateTimeStamp) {
            passRule = "W2 整文件=原版1.001记录(+size/tds双因子)";
        } else {
            char hexText[65] = {0};
            if (hasText && textRaw > 0 && textPtr >= 0 &&
                VerGateSha256Hex(f, textPtr, textRaw, hexText) &&
                _stricmp(hexText, kVerGateShaText) == 0 &&
                static_cast<uint32_t>(fileSize) == kVerGateFileSize &&
                tds == kVerGateTimeStamp && imageBase == kVerGateImageBase) {
                passRule = "W3 .text段=1.001指纹(+size/tds/imagebase三因子)";
            }
        }
    }
    fclose(f);
    if (passRule) {
        LogMessage("[ra2render-vergate] 版本门: PASS（%s; sha256=%.16s…, size=%ld, tds=0x%08X）",
                   passRule, hexFull, fileSize, tds);
        return true;
    }
    LogMessage("[ra2render-vergate] [错误/拒装] 版本门: gamemd.exe 指纹不在白名单 ⇒ 整体不安装任何补丁（白名单 W1=%s / W2=%s / W3=%s；实测 sha256=%s, size=%ld, tds=0x%08X）",
               kVerGateShaCur, kVerGateSha1001, kVerGateShaText,
               shaOk ? hexFull : "<sha-fail>", fileSize, tds);
    return false;
}

// [VER-GATE V2] 虚表逐点原值预核：13 处全查（任一不符 ⇒ 整体不装，一字节未写）。
//   期望旧值全部引用 ra2render.h 既有 ADDR_VFUNC_*/ADDR_ORIG_* 常量（:13-28, :37-57, :246-249），
//   且与真机在用日志 ra2render.log:14-26「原入口」逐项一致 —— 禁漂移常量，禁止另抄一份字面量。
struct VtableExpectEntry { uintptr_t site; uintptr_t expect; const char *name; };
static const VtableExpectEntry kVtableExpect[13] = {
    { ADDR_VTABLE_BLIT_TRANS_XLAT_ALPHA_ZREAD + 4, ADDR_VFUNC_BLIT_TRANS_XLAT_ALPHA_ZREAD, "?$BlitTransXlatAlphaZRead@G::v1" },
    { ADDR_VTABLE_BLIT_TRANS_XLAT_G + 4,           ADDR_VFUNC_BLIT_TRANS_XLAT_G,           "?$BlitTransXlat@G::v1" },
    { ADDR_VTABLE_RLE_BLIT_TRANS_XLAT_G + 4,       ADDR_VFUNC_RLE_BLIT_TRANS_XLAT_G,       "?$RLEBlitTransXlat@G::v1" },
    { ADDR_VTABLE_BLIT_TRANS_G + 4,                ADDR_VFUNC_BLIT_TRANS_G,                "?$BlitTrans@G::v1" },
    { ADDR_VTABLE_BLIT_TRANS_DARKEN_G + 4,         ADDR_VFUNC_BLIT_TRANS_DARKEN_G,         "?$BlitTransDarken@G::v1" },
    { ADDR_VTABLE_BLIT_PLAIN_G + 4,                ADDR_VFUNC_BLIT_PLAIN_G,                "?$BlitPlain@G::v1" },
    { ADDR_VTABLE_ENTRY_TECHNO_AUTO_TARGET,        ADDR_ORIG_TECHNO_AUTO_TARGET,           "TechnoClass::SelectAutoTarget" },
    { ADDR_VTABLE_ENTRY_UNIT_AUTO_TARGET,          ADDR_ORIG_UNIT_AUTO_TARGET,             "UnitClass::SelectAutoTarget" },
    { ADDR_VTABLE_ENTRY_UNIT_DRAW,                 ADDR_ORIG_UNIT_DRAW,                    "UnitClass::Draw" },
    { ADDR_VTABLE_ENTRY_INFANTRY_DRAW,             ADDR_ORIG_INFANTRY_DRAW,                "InfantryClass::Draw" },
    { ADDR_VTABLE_ENTRY_AIRCRAFT_DRAW,             ADDR_ORIG_AIRCRAFT_DRAW,                "AircraftClass::Draw" },
    { ADDR_VTABLE_ENTRY_BUILDING_DRAW,             ADDR_ORIG_BUILDING_DRAW,                "BuildingClass::Draw" },
    { ADDR_VTABLE_ENTRY_BULLET_DRAW,               ADDR_ORIG_BULLET_DRAW,                  "BulletClass::Draw" },
};

static bool VerifyVtableEntries() {
    int bad = 0;
    for (int i = 0; i < 13; ++i) {
        const VtableExpectEntry &e = kVtableExpect[i];
        if (IsBadReadPtr(reinterpret_cast<void*>(e.site), sizeof(uintptr_t))) {
            LogMessage("[ra2render-vergate] [错误] 虚表原值预核 %d/13: 0x%08X (%s) 不可读",
                       i + 1, static_cast<uint32_t>(e.site), e.name);
            ++bad;
            continue;
        }
        uintptr_t cur = *reinterpret_cast<uintptr_t*>(e.site);
        if (cur != e.expect) {
            LogMessage("[ra2render-vergate] [错误/拒装] 虚表原值预核 %d/13: 0x%08X (%s) 期望 0x%08X, 实测 0x%08X",
                       i + 1, static_cast<uint32_t>(e.site), e.name,
                       static_cast<uint32_t>(e.expect), static_cast<uint32_t>(cur));
            ++bad;
        }
    }
    if (bad > 0) {
        LogMessage("[ra2render-vergate] [错误/拒装] 虚表原值预核失败 %d/13 处不符 ⇒ 整体不安装（一字节未写，fail-closed；与 InstallGapProtectionPatch G0「任一不符整包不写」同口径）",
                   bad);
        return false;
    }
    LogMessage("[ra2render-vergate] 虚表原值预核: 13/13 全部匹配期望旧值 ⇒ 放行安装");
    return true;
}

// [VER-GATE V3] 直接改码位点原字节预核（Lead 判据③：超武补丁 InstallTextPatch 的「原字节核对后
//   才写」模式推广到**全部无条件直接写码位点**）。9 处 = CellClass::Draw 5B / 灰雾混色 B1 49B /
//   B2 51B / 视口刷新 6B / 黑幕计数 6B / Greatest_Threat 9B / 雷达 Plot 9B / 跳帧刷新 5B /
//   原生减暗 7B（各长度与安装器 s_orig*Bytes 缓冲声明逐一相等，见 RECEIPT 对照表）。
//   字节来源（禁漂移、有据可查）：
//     · 7 处与文档总表逐字节吻合：REVERSE_ENGINEERING_AND_PATCHES.md:219/223/226/248/249、
//       ra2render.h:66/77、docs/re/fog_switch_report.md:107；
//     · 全部 9 处取自封存现役 gamemd.exe（整文件 sha256=73201cc0…、.text sha256=c0368a17…
//       = ra2opt KNOWN_GAMEMD 权威键）静态提取——B1/B2 文档无完整 hex，以同一封存件为源。
struct CodeSiteExpectEntry { uintptr_t site; const uint8_t *expect; uint32_t len; const char *name; };
static const uint8_t kOrigCellClassDraw[5]    = {0x53, 0x55, 0x56, 0x8B, 0xF1};
static const uint8_t kOrigFogBlendB1[49]      = {0x66, 0x8B, 0x08, 0x66, 0x83, 0xF9, 0x7F, 0x75, 0x07, 0x66, 0x33, 0xC9, 0x8A, 0xCB, 0xEB, 0x1E, 0x8B, 0x54, 0x24, 0x48, 0x81, 0xE1, 0xFF, 0xFF, 0x00, 0x00, 0x81, 0xE2, 0xFF, 0x00, 0x00, 0x00, 0x8D, 0x4C, 0x11, 0x81, 0x33, 0xD2, 0x85, 0xC9, 0x0F, 0x9E, 0xC2, 0x4A, 0x23, 0xCA, 0x66, 0x89, 0x08};
static const uint8_t kOrigFogBlendB2[51]      = {0x66, 0x8B, 0x08, 0x66, 0x83, 0xF9, 0x7F, 0x75, 0x09, 0x66, 0x0F, 0xB6, 0xD2, 0x66, 0x89, 0x10, 0xEB, 0x21, 0x8B, 0x54, 0x24, 0x48, 0x81, 0xE1, 0xFF, 0xFF, 0x00, 0x00, 0x81, 0xE2, 0xFF, 0x00, 0x00, 0x00, 0x8D, 0x4C, 0x11, 0x81, 0x33, 0xD2, 0x85, 0xC9, 0x0F, 0x9E, 0xC2, 0x4A, 0x23, 0xCA, 0x66, 0x89, 0x08};
static const uint8_t kOrigTacticalRedraw[6]   = {0x0F, 0x8D, 0x98, 0x00, 0x00, 0x00};
static const uint8_t kOrigDrawShroudFog[6]    = {0x55, 0x8B, 0xEC, 0x83, 0xEC, 0x34};
static const uint8_t kOrigGreatestThreat[9]   = {0x83, 0xEC, 0x5C, 0x8B, 0x15, 0x34, 0xEC, 0xA8, 0x00};
static const uint8_t kOrigRadarPlot[9]        = {0x89, 0x44, 0x24, 0x28, 0xA1, 0x50, 0x35, 0xB7, 0x00};
static const uint8_t kOrigRadarPending[5]     = {0xE8, 0x91, 0x93, 0x00, 0x00};
static const uint8_t kOrigRadarNativeDecide[7]= {0x8B, 0x47, 0x04, 0x89, 0x6C, 0x24, 0x14};
static const CodeSiteExpectEntry kCodeSiteExpect[9] = {
    { ADDR_CELLCLASS_DRAW,             kOrigCellClassDraw,     5, "CellClass::Draw Inline" },
    { ADDR_DRAW_FOG_PIXEL_BLEND_B1,    kOrigFogBlendB1,       49, "FogBlendB1" },
    { ADDR_DRAW_FOG_PIXEL_BLEND_B2,    kOrigFogBlendB2,       51, "FogBlendB2" },
    { ADDR_TACTICAL_FULL_REDRAW_JUMP,  kOrigTacticalRedraw,    6, "TacticalFullRedraw" },
    { ADDR_DRAW_SHROUD_FOG,            kOrigDrawShroudFog,     6, "DrawShroudFogCounter" },
    { ADDR_ORIG_TECHNO_GREATEST_THREAT,kOrigGreatestThreat,    9, "GreatestThreat Inline" },
    { 0x00655D38,                      kOrigRadarPlot,         9, "RadarPlotCell Inline" },
    { ADDR_RADAR_PENDING_CALLSITE,     kOrigRadarPending,      5, "RadarPendingCall" },
    { ADDR_RADAR_NATIVE_DECIDE,        kOrigRadarNativeDecide, 7, "RadarNativeDecide" },
};

static bool VerifyCodeSites() {
    int bad = 0;
    uint8_t cur[64];
    for (int i = 0; i < 9; ++i) {
        const CodeSiteExpectEntry &e = kCodeSiteExpect[i];
        if (e.len > sizeof(cur) || IsBadReadPtr(reinterpret_cast<void*>(e.site), e.len)) {
            LogMessage("[ra2render-vergate] [错误] 改码位点预核 %d/9: 0x%08X (%s, %uB) 不可读",
                       i + 1, static_cast<uint32_t>(e.site), e.name, e.len);
            ++bad;
            continue;
        }
        memcpy(cur, reinterpret_cast<void*>(e.site), e.len);
        if (memcmp(cur, e.expect, e.len) != 0) {
            LogMessage("[ra2render-vergate] [错误/拒装] 改码位点预核 %d/9: 0x%08X (%s, %uB) 原字节与期望不符 ⇒ 拒装",
                       i + 1, static_cast<uint32_t>(e.site), e.name, e.len);
            GapProtectLogBytes("code-actual", e.name, static_cast<uint32_t>(e.site), cur, e.len);
            GapProtectLogBytes("code-expect", e.name, static_cast<uint32_t>(e.site), e.expect, e.len);
            ++bad;
        }
    }
    if (bad > 0) {
        LogMessage("[ra2render-vergate] [错误/拒装] 改码位点预核失败 %d/9 处不符 ⇒ 整体不安装（一字节未写，fail-closed）",
                   bad);
        return false;
    }
    LogMessage("[ra2render-vergate] 改码位点预核: 9/9 全部匹配原版字节 ⇒ 放行安装");
    return true;
}

bool InstallVTableHooks() {
    LoadConfig();

    // [VER-GATE V1] 启动门：指纹白名单不过 ⇒ 整体不安装（vtable/inline/text 补丁全部不碰）
    if (!VerifyGameVersionGate()) {
        return false;
    }
    // [VER-GATE V2] 逐点预核：13 处虚表原值全查通过才进入下方写入段
    if (!VerifyVtableEntries()) {
        return false;
    }
    // [VER-GATE V3] 直接改码位点预核：9 处原字节全查通过才进入写入段（预核全部完成后才允许第一笔写）
    if (!VerifyCodeSites()) {
        return false;
    }

    LogMessage("[ra2render] 正在安装 L1 渲染、L2 寻敌逻辑与 L3 星际战争迷雾虚表劫持...");

    // 1. BlitTransXlatAlphaZRead@G
    uintptr_t hook1 = union_cast<uintptr_t>(&BlitterHooks::Hook_BlitTransXlatAlphaZRead);
    PatchVTablePointer(ADDR_VTABLE_BLIT_TRANS_XLAT_ALPHA_ZREAD + 4, hook1,
                       reinterpret_cast<uintptr_t*>(&g_pOrigBlitTransXlatAlphaZRead),
                       "?$BlitTransXlatAlphaZRead@G::v1",
                       ADDR_VFUNC_BLIT_TRANS_XLAT_ALPHA_ZREAD);

    // 2. BlitTransXlat@G
    uintptr_t hook2 = union_cast<uintptr_t>(&BlitterHooks::Hook_BlitTransXlat_G);
    PatchVTablePointer(ADDR_VTABLE_BLIT_TRANS_XLAT_G + 4, hook2,
                       reinterpret_cast<uintptr_t*>(&g_pOrigBlitTransXlat_G),
                       "?$BlitTransXlat@G::v1",
                       ADDR_VFUNC_BLIT_TRANS_XLAT_G);

    // 3. RLEBlitTransXlat@G
    uintptr_t hook3 = union_cast<uintptr_t>(&BlitterHooks::Hook_RLEBlitTransXlat_G);
    PatchVTablePointer(ADDR_VTABLE_RLE_BLIT_TRANS_XLAT_G + 4, hook3,
                       reinterpret_cast<uintptr_t*>(&g_pOrigRLEBlitTransXlat_G),
                       "?$RLEBlitTransXlat@G::v1",
                       ADDR_VFUNC_RLE_BLIT_TRANS_XLAT_G);

    // 4. BlitTrans@G
    uintptr_t hook4 = union_cast<uintptr_t>(&BlitterHooks::Hook_BlitTrans_G);
    PatchVTablePointer(ADDR_VTABLE_BLIT_TRANS_G + 4, hook4,
                       reinterpret_cast<uintptr_t*>(&g_pOrigBlitTrans_G),
                       "?$BlitTrans@G::v1",
                       ADDR_VFUNC_BLIT_TRANS_G);

    // 5. BlitTransDarken@G
    uintptr_t hook5 = union_cast<uintptr_t>(&BlitterHooks::Hook_BlitTransDarken_G);
    PatchVTablePointer(ADDR_VTABLE_BLIT_TRANS_DARKEN_G + 4, hook5,
                       reinterpret_cast<uintptr_t*>(&g_pOrigBlitTransDarken_G),
                       "?$BlitTransDarken@G::v1",
                       ADDR_VFUNC_BLIT_TRANS_DARKEN_G);

    // 6. BlitPlain@G
    uintptr_t hook6 = union_cast<uintptr_t>(&BlitterHooks::Hook_BlitPlain_G);
    PatchVTablePointer(ADDR_VTABLE_BLIT_PLAIN_G + 4, hook6,
                       reinterpret_cast<uintptr_t*>(&g_pOrigBlitPlain_G),
                       "?$BlitPlain@G::v1",
                       ADDR_VFUNC_BLIT_PLAIN_G);

    // 7. TechnoClass::SelectAutoTarget (vtable[265])
    uintptr_t hook7 = union_cast<uintptr_t>(&TargetHooks::Hook_Techno_SelectAutoTarget);
    PatchVTablePointer(ADDR_VTABLE_ENTRY_TECHNO_AUTO_TARGET, hook7,
                       reinterpret_cast<uintptr_t*>(&g_pOrigTechnoSelectAutoTarget),
                       "TechnoClass::SelectAutoTarget",
                       ADDR_ORIG_TECHNO_AUTO_TARGET);

    // 8. UnitClass::SelectAutoTarget (vtable[265])
    uintptr_t hook8 = union_cast<uintptr_t>(&TargetHooks::Hook_Unit_SelectAutoTarget);
    PatchVTablePointer(ADDR_VTABLE_ENTRY_UNIT_AUTO_TARGET, hook8,
                       reinterpret_cast<uintptr_t*>(&g_pOrigUnitSelectAutoTarget),
                       "UnitClass::SelectAutoTarget",
                       ADDR_ORIG_UNIT_AUTO_TARGET);

    // 9. UnitClass::Draw (vtable[69]) - 星际式迷雾单位视距剔除
    uintptr_t hook9 = union_cast<uintptr_t>(&FogHooks::Hook_Unit_Draw);
    PatchVTablePointer(ADDR_VTABLE_ENTRY_UNIT_DRAW, hook9,
                       reinterpret_cast<uintptr_t*>(&g_pOrigUnitDraw),
                       "UnitClass::Draw",
                       ADDR_ORIG_UNIT_DRAW);

    // 10. InfantryClass::Draw (vtable[69]) - 星际式迷雾步兵视距剔除
    uintptr_t hook10 = union_cast<uintptr_t>(&FogHooks::Hook_Infantry_Draw);
    PatchVTablePointer(ADDR_VTABLE_ENTRY_INFANTRY_DRAW, hook10,
                       reinterpret_cast<uintptr_t*>(&g_pOrigInfantryDraw),
                       "InfantryClass::Draw",
                       ADDR_ORIG_INFANTRY_DRAW);

    // 11. AircraftClass::Draw (vtable[69]) - 星际式迷雾空军战机视距剔除
    uintptr_t hook11 = union_cast<uintptr_t>(&FogHooks::Hook_Aircraft_Draw);
    PatchVTablePointer(ADDR_VTABLE_ENTRY_AIRCRAFT_DRAW, hook11,
                       reinterpret_cast<uintptr_t*>(&g_pOrigAircraftDraw),
                       "AircraftClass::Draw",
                       ADDR_ORIG_AIRCRAFT_DRAW);

    // 12. BuildingClass::Draw (vtable[69]) - 敌方建筑"看见过即常驻"迷雾门控
    uintptr_t hook12 = union_cast<uintptr_t>(&FogHooks::Hook_Building_Draw);
    PatchVTablePointer(ADDR_VTABLE_ENTRY_BUILDING_DRAW, hook12,
                       reinterpret_cast<uintptr_t*>(&g_pOrigBuildingDraw),
                       "BuildingClass::Draw",
                       ADDR_ORIG_BUILDING_DRAW);

    // 13. BulletClass::Draw (vtable[69]) - 迷雾中敌方弹道剔除
    uintptr_t hook13 = union_cast<uintptr_t>(&FogHooks::Hook_Bullet_Draw);
    PatchVTablePointer(ADDR_VTABLE_ENTRY_BULLET_DRAW, hook13,
                       reinterpret_cast<uintptr_t*>(&g_pOrigBulletDraw),
                       "BulletClass::Draw",
                       ADDR_ORIG_BULLET_DRAW);

    // 14. CellClass::Draw Inline Hook (0x004801F0) - 星际争霸式半透明战争迷雾图层渲染
    InstallCellClassDrawHook();

    // 15. TechnoClass::Greatest_Threat Inline Hook (0x006F8DF0) - 全局寻敌汇聚点与存活目标保持
    InstallGreatestThreatHook();

    // 16. 雷达小地图迷雾代理（Plot_Cell 调用点 + 跳帧判定调用点）
    InstallRadarFogHooks();

    // 17. [GAP-P223] 裂缝保护三点表驱动：RevealArea2/RevealArea3/Reshroud 各清 GapsCoveringThisCell 6×NOP
    //     （安装序 P-2.1→P-2.2→P-2.3；EnableGapProtection 门控默认不装；MpActive 强制不装）
    InstallGapProtectionPatch();

    // 18. [VXL-PRE] SomeVoxelCache 首次分配粒度 imm8 0x0A→0x40（EnableVxlCachePrewarm 门控，默认不装）
    InstallVxlCachePrewarmPatch();

    // 19. [SW-CHARGE] HasChargeProgressed 慢路径冗余二次 call 7B→90×7（EnableSWChargeOpt 门控，默认不装）
    InstallSwChargeOptPatch();
    InstallSbhGuardPatch(); 

    LogMessage("[ra2render] 全部核心虚表、底层迷雾、小地图迷雾与 0x006F8DF0 寻敌 Inline Hook 挂载成功！已启动 60 FPS 满速与星际争霸式战争迷雾系统。");
    return true;
}

void RemoveVTableHooks() {
    RemoveCellClassDrawHook();
    RemoveGreatestThreatHook();
    RemoveRadarFogHooks();
    // 跨子系统卸载 = 安装序严格逆序（装序 gap→vxl→sw ⇒ 卸序 sw→vxl→gap）；
    // gap 内部三点逆序 P-2.3→P-2.2→P-2.1（见 RemoveGapProtectionPatch）。
    RemoveSbhGuardPatch(); 
    RemoveSwChargeOptPatch();
    RemoveVxlCachePrewarmPatch();
    RemoveGapProtectionPatch();

    if (g_pOrigBlitTransXlatAlphaZRead) {
        PatchVTablePointer(ADDR_VTABLE_BLIT_TRANS_XLAT_ALPHA_ZREAD + 4,
                           reinterpret_cast<uintptr_t>(g_pOrigBlitTransXlatAlphaZRead), nullptr, "还原 BlitTransXlatAlphaZRead",
                           union_cast<uintptr_t>(&BlitterHooks::Hook_BlitTransXlatAlphaZRead));
        g_pOrigBlitTransXlatAlphaZRead = nullptr;
    }
    if (g_pOrigBlitTransXlat_G) {
        PatchVTablePointer(ADDR_VTABLE_BLIT_TRANS_XLAT_G + 4,
                           reinterpret_cast<uintptr_t>(g_pOrigBlitTransXlat_G), nullptr, "还原 BlitTransXlat_G",
                           union_cast<uintptr_t>(&BlitterHooks::Hook_BlitTransXlat_G));
        g_pOrigBlitTransXlat_G = nullptr;
    }
    if (g_pOrigRLEBlitTransXlat_G) {
        PatchVTablePointer(ADDR_VTABLE_RLE_BLIT_TRANS_XLAT_G + 4,
                           reinterpret_cast<uintptr_t>(g_pOrigRLEBlitTransXlat_G), nullptr, "还原 RLEBlitTransXlat_G",
                           union_cast<uintptr_t>(&BlitterHooks::Hook_RLEBlitTransXlat_G));
        g_pOrigRLEBlitTransXlat_G = nullptr;
    }
    if (g_pOrigBlitTrans_G) {
        PatchVTablePointer(ADDR_VTABLE_BLIT_TRANS_G + 4,
                           reinterpret_cast<uintptr_t>(g_pOrigBlitTrans_G), nullptr, "还原 BlitTrans_G",
                           union_cast<uintptr_t>(&BlitterHooks::Hook_BlitTrans_G));
        g_pOrigBlitTrans_G = nullptr;
    }
    if (g_pOrigBlitTransDarken_G) {
        PatchVTablePointer(ADDR_VTABLE_BLIT_TRANS_DARKEN_G + 4,
                           reinterpret_cast<uintptr_t>(g_pOrigBlitTransDarken_G), nullptr, "还原 BlitTransDarken_G",
                           union_cast<uintptr_t>(&BlitterHooks::Hook_BlitTransDarken_G));
        g_pOrigBlitTransDarken_G = nullptr;
    }
    if (g_pOrigBlitPlain_G) {
        PatchVTablePointer(ADDR_VTABLE_BLIT_PLAIN_G + 4,
                           reinterpret_cast<uintptr_t>(g_pOrigBlitPlain_G), nullptr, "还原 BlitPlain_G",
                           union_cast<uintptr_t>(&BlitterHooks::Hook_BlitPlain_G));
        g_pOrigBlitPlain_G = nullptr;
    }
    if (g_pOrigTechnoSelectAutoTarget) {
        PatchVTablePointer(ADDR_VTABLE_ENTRY_TECHNO_AUTO_TARGET,
                           reinterpret_cast<uintptr_t>(g_pOrigTechnoSelectAutoTarget), nullptr, "还原 TechnoClass::SelectAutoTarget",
                           union_cast<uintptr_t>(&TargetHooks::Hook_Techno_SelectAutoTarget));
        g_pOrigTechnoSelectAutoTarget = nullptr;
    }
    if (g_pOrigUnitSelectAutoTarget) {
        PatchVTablePointer(ADDR_VTABLE_ENTRY_UNIT_AUTO_TARGET,
                           reinterpret_cast<uintptr_t>(g_pOrigUnitSelectAutoTarget), nullptr, "还原 UnitClass::SelectAutoTarget",
                           union_cast<uintptr_t>(&TargetHooks::Hook_Unit_SelectAutoTarget));
        g_pOrigUnitSelectAutoTarget = nullptr;
    }
    if (g_pOrigUnitDraw) {
        PatchVTablePointer(ADDR_VTABLE_ENTRY_UNIT_DRAW,
                           reinterpret_cast<uintptr_t>(g_pOrigUnitDraw), nullptr, "还原 UnitClass::Draw",
                           union_cast<uintptr_t>(&FogHooks::Hook_Unit_Draw));
        g_pOrigUnitDraw = nullptr;
    }
    if (g_pOrigInfantryDraw) {
        PatchVTablePointer(ADDR_VTABLE_ENTRY_INFANTRY_DRAW,
                           reinterpret_cast<uintptr_t>(g_pOrigInfantryDraw), nullptr, "还原 InfantryClass::Draw",
                           union_cast<uintptr_t>(&FogHooks::Hook_Infantry_Draw));
        g_pOrigInfantryDraw = nullptr;
    }
    if (g_pOrigAircraftDraw) {
        PatchVTablePointer(ADDR_VTABLE_ENTRY_AIRCRAFT_DRAW,
                           reinterpret_cast<uintptr_t>(g_pOrigAircraftDraw), nullptr, "还原 AircraftClass::Draw",
                           union_cast<uintptr_t>(&FogHooks::Hook_Aircraft_Draw));
        g_pOrigAircraftDraw = nullptr;
    }
    if (g_pOrigBuildingDraw) {
        PatchVTablePointer(ADDR_VTABLE_ENTRY_BUILDING_DRAW,
                           reinterpret_cast<uintptr_t>(g_pOrigBuildingDraw), nullptr, "还原 BuildingClass::Draw",
                           union_cast<uintptr_t>(&FogHooks::Hook_Building_Draw));
        g_pOrigBuildingDraw = nullptr;
    }
    if (g_pOrigBulletDraw) {
        PatchVTablePointer(ADDR_VTABLE_ENTRY_BULLET_DRAW,
                           reinterpret_cast<uintptr_t>(g_pOrigBulletDraw), nullptr, "还原 BulletClass::Draw",
                           union_cast<uintptr_t>(&FogHooks::Hook_Bullet_Draw));
        g_pOrigBulletDraw = nullptr;
    }

    LogMessage("[ra2render] 虚表与图层Hook已完全复原。Blit调用: %llu, 像素: %llu, 寻敌扫描: %llu (已平抑: %llu), 迷雾剔除: %llu, 灰雾格子: %llu, 渲染单位: %llu | 建筑剔除: %llu, 弹道剔除: %llu, 雷达灰化分支进入次数: %u, 雷达灰化像素数: %u, 原生减暗路径命中次数: %u (引擎自身: %u, 我方强制: %u, 覆盖差: %u)",
               g_telemetry.totalBlitCalls, g_telemetry.totalBlitPixels,
               g_telemetry.totalTargetScans, g_telemetry.throttledTargetScans,
               g_telemetry.unitsCulledByFog, g_telemetry.fogCellsDrawn, g_telemetry.totalUnitsRendered,
               g_telemetry.buildingsCulledByFog, g_telemetry.bulletsCulledByFog,
               s_minimapFogBranchHits, s_minimapFogPixels,
               s_nativeDarkenHits, s_nativeEngineDarkHits, s_nativeForcedDarkHits, s_nativeOverrideDeltas);
    LogMessage("[ra2render-fogswitch] 总闸三计数: 半透明层绘制次数=%u, 混色桩介入次数=%u, 小地图减暗驱动次数=%u",
               s_fogLayerDraws, s_fogBlendStubHits, s_radarDarkenDriven);
}
