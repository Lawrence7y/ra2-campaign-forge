# FOG-SPLIT 交付报告 —— 总闸语义重定义：只去「已探索但离开后」的压暗，保留未探索黑幕 + 保留玩法可见性

> 任务号：**FOG-SPLIT** ｜ 执行方：**DSH 子代理** ｜ 工作区：`D:/Project/ra2-campaign-forge`（Windows）
> 基线（只读）：`ra2youli/gamemd.exe` MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367` / 4,825,360 B（开工=收工复算一致）
> 交付产物：`ra2render/ra2render.dll` ≡ `ra2youli/ra2render.dll` = **138,752 B** / MD5 `59671E8BC333A999820C788D76A5B375`
> 旧件备份：`out/re_work/fog_split/ra2render.dll.bak-491C25F9`（135,680 B / MD5 `491C25F9DE72E6A5EB3484E4CF154DA3`）、`ra2render.ini.bak-26E7297E`（7,047 B，= 开工时部署态）；另存 ZC-4 快照 `ra2render.ini.zc4-0DAD9A41`（7,001 B）
> 两份 ini 同步：**9,459 B** / SHA-256 `8D289390EEFF93BF115863461D43E8BD00FE5F6FA39E93C4BE2377384BB6C902`（`ra2render/` 与 `ra2youli/` 逐字节一致）

---

## [META]

| 字段 | 值 |
|---|---|
| task | FOG-SPLIT |
| executor | DSH 子代理（父 agent id `session-852a2193-df41-4859-b6f3-cd17f595410f` 的子代理；本任务以 FOG-SPLIT 作语义标识） |
| mode | accept-edits（仅在写作用域内） |
| scope_declared | 允许写 `ra2render/**`、`ra2youli/ra2render.{dll,ini}`、新建 `docs/re/fog_split_report.md`、`out/re_work/fog_split/**`；另按 **F8 明文要求**就地订正 `docs/re/fog_switch_report.md` 两处勘误 |
| 快照时点 | 开工时 `ra2render/blitter_hooks.cpp` = 118,290 B；`ra2render/ra2render.ini` = 7,047 B / SHA-256 `26E7297E…`（**与任务卡所述 7,001 B / `0DAD9A41…` 不同**：差 1 行注释，键与默认值零变化 —— 见 §[3] E0）。本会话内未见他人并发写入本任务文件 |
| 禁止事项遵守 | **未启动游戏、未注入、未改 exe、未伪造实测**（所有真机项一律 [待实测]） |

---

## [0] 结论摘要

1. **总闸语义已按用户裁决重定义并落地**：`EnableStarCraftFog` 现在**只管「已探索且当前无我方/盟友直视」这一档的压暗强度**（=1 压暗 256 / =0 强度归零）；实现改成 **按格三态判定**（未探索放行 / 已探索非直视受总闸控 / 直视不压暗），不再「整体短路迷雾渲染栈」。
2. **未探索黑幕保留（裁决①）**：未探索黑幕的唯一承载路径是引擎 `CellClass::Draw 0x4801F0` → `0x47EFE0`（全 .text call 扫描：**唯一调用者** `0x00480230`；FogOfWar 位=0 时选 SHROUD.SHP）。该调用点由我方跳板**恒定执行**，我方对其**零介入**（只读计数），且两条旧耦合 —— ①`UpdateVisionGrid` 跳呼、②L4 全量刷回退 —— **已解除** ⇒ 总闸=0 不再影响黑幕。
3. **玩法可见性与总闸解耦（裁决②）**：建筑/弹道两键**本就未受总闸影响**（ZC-4 S2 实测 建筑剔除 1,484 / 弹道剔除 49 均 >0 ⇒ **任务卡「计数全 0」的前提是误读，见 §[3] E1**）；真正违反语义的是**机动单位剔除**（旧版被总闸裹挟 ⇒ S2 恒 0），已独立成新键 `EnableUnitFog=1`（默认 1 = 旧行为）并解耦。
4. **遥测已按状态拆开**：新增 2 秒行 `[ra2render-telemetry-fogsplit]`（旧 `-fogswitch` 行字段与顺序**零变化**），提供「未探索黑幕绘制次数」（引擎 `0x47EFE0` 只读计数钩子的**实测**值）与「已探索非直视压暗次数」「小地图已探索非直视减暗驱动次数」及玩法层三计数。
5. **门禁全绿**：`verify_anchors.py` **323/323 PASS**；`audit_bytes.py` 引擎侧 **27/27 OK**、产物侧 **35/35 OK**（另按真实 ImageBase 独立复算 35 OK / 0 FAIL）。**最大风险**：真机 A/B 未跑（本任务禁止启动游戏/注入），未探索黑幕的**观感**判据交 ZCode（附录 C）。

---

## [1] 逐条必答项结论表

| # | 问题 | 结论 | 证据等级 | 证据锚点 |
|---|---|---|---|---|
| F1-1 | 总闸短路条件是否改为按格状态判定？ | **是**。`Hook_CellClass_Draw` 内新分支：`cmp byte ptr [esi+0x120],0xFE`（引擎 `CellClass::Shroudedness`==-2「Occluded completely」⇒ 未探索）→ 计数后 `jmp` 函数尾声（**零引擎调用**）；总闸判定 `cmp [g_enableStarCraftFog],0` **移到位图状态判定之后** ⇒ 只作用于「已探索非直视」档 | [实证] | 产物 RVA `0x2072`/`0x2079`/`0x207B`/`0x2081`；总闸 `0x2105`/`0x210C`/`0x2112`/`0x2118`（claims_dll.txt 35 条） |
| F1-2 | 未探索黑幕走哪条路径？ | `CellClass::Draw(0x4801F0)` → **恒定** `call 0x47EFE0`（`0x48022E` `mov ecx,esi` / `0x480230`）→ 依 Scenario FogOfWar 位选图（位=0 ⇒ **SHROUD.SHP**）→ 逐格不透明近黑拷贝（唯一落像素 `0x47F226` 段内 `66 89 07`，**无混色/无 alpha**） | [实证] | `0x47EFE0`/`0x47F01F`/`0x47F024`/`0x47F02F`/`0x47F226`/`0x48022E`/`0x480251`；xref：`callers(0x47EFE0)={0x480230}` |
| F1-3 | 该路径为何不受我方总闸影响？ | 三重保证：**①补丁面**——我方对 `0x47EFE0` 只装**只读计数桩**（`mov al,[ecx+0x120]` → 自增 DLL 私有计数 → `jmp [跳板]` 原样回放 6B 原指令）；**②耦合面**——旧版切断的两条非绘制耦合已解除（`UpdateVisionGrid` 恒调用 `RVA 0x2048`；L4 桩已无总闸分支 `RVA 0x2390`）；**③作用域面**——主视图绘制路径上总闸只剩 `RVA 0x2105` 一处判定，位于未探索/直视判定之后 ⇒ =0 的差值集合 = {已探索非直视档的 `Draw_Fog` 调用} | [实证] | 产物 RVA `0x21C0`–`0x21E4`（桩体）、`0x2048`、`0x2390`、`0x2105`；源码 `blitter_hooks.cpp` §FOG-SPLIT 注释块 |
| F1-4 | 小地图侧是否同样保留未探索黑幕？ | **是**。`RadarHook_NativeDecide` 新增：`explored==0` ⇒ 自增「小地图未探索格放行次数」后**直接返回**，**不写**引擎减暗判定位 `[esp+0x13]`（保持引擎自身判定） | [实证] | 产物 RVA `0x4926`（`test al,al`）/ `0x4928`（`jne`）/ `0x492A`（`inc [s_radarUnexploredPassed]`）/ `0x4930`（`jmp` 尾声，**不经过** `mov [eax],bh`） |
| F2-1 | `EnableBuildingFog`/`EnableBulletFog` 门控在总闸=0 时是否仍生效？ | **是，且原本就是**（无需修改）。两键各自独立门控（产物 `0x1002100D` / `0x1002100E`，与总闸无引用关系）；真机反证：ZC-4 S2（总闸=0）建筑剔除 337→**1,484**、弹道剔除 6→**49** 均 >0 ⇒ **任务卡「计数全 0」为误读**（§[3] E1） | [实证] | 产物 RVA `0x1F50`（building 门控）/ `0x1FA0`（bullet 门控）；ZC-4 原始日志 `out/re_work/zcode_live/zc4/evidence/logs/s2_master0_session.txt` |
| F2-2 | 旧版真正违反「玩法可见性不受总闸影响」的是哪一处？ | **迷雾剔除机动单位**。旧源码三处 `g_enableStarCraftFog && !ShouldDrawMobileObject(...)` ⇒ 总闸=0 时恒 0（S2 实测 0；S1 为 77→33225）。已改为新键 `EnableUnitFog`（默认 1），与总闸解耦 | [实证] | 产物 RVA `0x1950`/`0x2330`/`0x2608`（三处 `cmp byte ptr [g_enableUnitFog],0`）；S2/S1 日志计数 |
| F2-3 | 是否引入新键？默认值是否变化？ | 新增 **1 个子键** `EnableUnitFog=1`（API 默认值 1 = 键缺失即开启 = 旧行为）；**既有键与全部默认值零变化**（总闸 1 / 建筑 1 / 弹道 1 / 渐变 1 / 小地图 0 / 灰化档 3） | [实证] | ini 键值清单（§[5]）；`EnableUnitFog` 符号 `?g_enableUnitFog@@3_NA`（SECT4 +0x0F） |
| F3-1 | 未探索黑幕绘制次数（总闸=0 应 >0） | 已提供且为**引擎侧实测**：装 0x47EFE0 只读计数钩子，按 `Shroudedness` 分档自增 `s_shroudBlackDraws`（==-2）/ `s_shroudEdgeDraws`（0..48） | [实证] | 符号 `_s_shroudBlackDraws`=VA `0x102E1A4C`、`_s_shroudEdgeDraws`=`0x102E1A50`（obj SECT3 +0x2C00FC/+0x2C0100 ⇔ 产物 VA 相对偏移一致） |
| F3-2 | 已探索非直视压暗次数（总闸=0 应 ≡0） | 已提供：`s_exploredFogDarken`（增量点 `add [imm],eax`，仅稳态「非直视」档自增）；总闸=0 时该档在 `RVA 0x2112` 处分流返回 ⇒ 恒 0 | [实证] | 符号 `_s_exploredFogDarken`=VA `0x102E1A5C`；自增点 RVA `0x2145` |
| F3-3 | 小地图已探索非直视减暗驱动次数（总闸=0 应 ≡0） | 复用既有 `s_radarDarkenDriven`（`-fogswitch` 行的既有字段，口径不变）；新行以「小地图已探索非直视减暗驱动次数」复述并追加「小地图未探索格放行次数」 | [实证] | 符号 `_s_radarDarkenDriven`=VA `0x102E1A40`（与 FOG-SWITCH 版一致）；自增点 RVA `0x4967` |
| F3-4 | 玩法层计数与总闸无关（两档都 >0） | 三计数（机动单位剔除/建筑剔除/弹道剔除）已**追加进同一条 fogswitch/fogsplit 行**（旧字段顺序未动）；解耦后总闸两档都 >0 | [实证] 静态 + [待实测] 真机读数 | 遥测行 RVA `0x19050`（新行格式串）；计数 VA `0x10021980`/`0x10021990`/`0x10021998` |
| F4-1 | 两份 ini 注释是否与新语义逐条一致？ | **是**：总闸注释重写为「只管已探索非直视档」+ 三态表 + 「未探索黑幕保留」「玩法可见性不受影响」「小地图只关已探索非直视减暗」+ 三条解耦说明；新键 `EnableUnitFog` 注释标明「逻辑可见性键：不受总闸影响」 | [实证] | `ra2render/ra2render.ini` §[FogOfWar]（L29–L100）；两份 SHA-256 相同 |
| F4-2 | 总闸与各子键默认值是否改动？ | **未改动**（逐键比对见 §[5]） | [实证] | ini 键值清单 |
| F5-1 | 编译 / 备份 / 部署 | `cmd /c ra2render/build.bat` → `ALL BUILDS FINISHED SUCCESSFULLY`（无 error/warning）；旧件备份 `out/re_work/fog_split/ra2render.dll.bak-491C25F9` + `ra2render.ini.bak-26E7297E`；新件已部署 `ra2youli/` | [实证] | §[6] 原文 |
| F5-2 | 两份 ini 逐字节一致？ | **是**（9,459 B / SHA-256 `8D289390…` 两处相同） | [实证] | §[5] |
| F6-1 | ① 新的按状态判定分支 | 存在：RVA `0x2072` `80 BE 20 01 00 00 FE`（`cmp byte ptr [esi+0x120],0xFE`） | [实证] | claims_dll.txt 第 3–6 行 + 附录 B.1 |
| F6-2 | ② 未探索路径未被短路（仍可达） | 两条独立证据：**(a)** 未探索分支内**不含任何引擎调用**（`0x207B` inc → `0x2081` jmp 尾声），且原版调用（跳板）在其之前恒定执行（RVA `0x2023`–`0x2037`）；**(b)** 新装 0x47EFE0 计数桩**只读**，证明该函数仍被引擎每帧调用 | [实证] | 附录 B.1/B.2 |
| F6-3 | ③ 三个新计数符号齐备 | 齐备（obj 符号表实证）：`_s_shroudBlackDraws`、`_s_exploredFogDarken`（另 `_s_shroudEdgeDraws`/`_s_fogUnexploredPassed`/`_s_fogVisiblePassed`/`_s_gate0DarkenSkipped`/`_s_radarUnexploredPassed`/`_s_pDrawShroudFogTrampoline`） | [实证] | `out/re_work/fog_split/F6_obj_symbols.txt` + 附录 D |
| F6-4 | ④ 既有挂钩点未变 | **未变**：安装代码写入点 `0x655D38` `C6 05 38 5D 65 00 E9`（RVA `0x2B38`）、`0x65719A` `… E8`（RVA `0x2BA5`）、`0x655D87` `… E9`（RVA `0x2C72`）；另 `0x4801F0`（RVA `0x2798`）、`0x6F8DF0`（RVA `0x2ED1`）未变 | [实证] | claims_dll.txt + 附录 B.6 |
| F7 | 真机复验清单（交 ZCode） | 已产出：判据 ①–⑦（未探索仍全黑 / 已探索非直视与直视亮度一致 / 玩法三计数两档都 >0 / 压暗与小地图驱动 ≡0 / 黑幕绘制 >0 / 与 ZC-4 S1 同构 / 无崩溃+ini 还原）+ 亮度统计口径 | [纸面规格] | 附录 C + `out/re_work/fog_split/ZCODE_ACCEPTANCE_FOG_SPLIT.md` |
| F8-1 | 勘误①：启动日志行 RVA | 已就地订正为 **RVA `0x187F0`**（原文 `0x18D28` 以【原记】保留）：对 135,680 B 部署件按文本搜索实证 `[ra2render-fog] ` @ RVA `0x187F0`；RVA `0x18D28` = `[ra2render-telemetry] BlitCalls: …` | [实证] | `docs/re/fog_switch_report.md` §[1] F3-1、§附录 C.4、§[3] E5；`out/re_work/fog_split/rva_probe.py` 输出 |
| F8-2 | 勘误②：附录 C 的 inc 地址差 2 字节 | 已就地补口径说明（原文以【原记】保留）：`FF 05` 后 **imm32 起点 = 指令起点 +2**，两者是**同一条指令**的两种口径（非两条 inc） | [实证] | `docs/re/fog_switch_report.md` §[3] E6、§附录 C.4 末段 |

---

## [2] 关键证据块

### 2.1 引擎侧：未探索黑幕的完整路径（决定 F1 结论）

**调用链（三层，逐层有字节锚点）**

| 层 | VA | 原始字节 | Capstone | 作用 |
|---|---|---|---|---|
| 战术格绘制循环 | `0x006D3716` | `E8 D5 CA DA FF` | `call 0x4801F0` | 每可见格调用 `CellClass::Draw`（全局共 2 处调用点：`0x6D3716`、`0x6D751A`） |
| 单元格绘制 | `0x0048022E` | `8B CE E8 AB ED FF FF` | `mov ecx,esi` / `call 0x47EFE0` | **恒定**调用黑幕/灰雾层（早于第二道 FogOfWar 位门 `0x480251`） |
| 黑幕层 | `0x0047EFE0` | `55 8B EC 83 EC 34` | `push ebp` / `mov ebp,esp` / `sub esp,0x34` | 依 FogOfWar 位选 SHROUD.SHP / FOG.SHP 并逐格拷贝 |

**callers 全扫描实证**（.text 线性反汇编 + `E8 rel32` 目标比对）：

* `callers(0x0047EFE0) = { 0x00480230 }` —— **唯一调用者**（即上表第 2 层）
* `callers(0x0047F250) = { 0x480278, 0x480290 }`（引擎自身，FogOfWar 位=1 才可达）+ 我方钩子 1 处（产物 RVA `0x2156`/`0x215B`）
* `callers(0x004801F0) = { 0x6D3716, 0x6D751A }`

**图像选择（位=0 ⇒ 不透明黑幕）**

```text
0x0047F009 = A3 94 E7 89 00   mov [0x89E794],eax   ; SHROUD.SHP 句柄
0x0047F013 = A3 90 E7 89 00   mov [0x89E790],eax   ; FOG.SHP 句柄
0x0047F01F = F6 C5 10 74 0B   test ch,0x10 / je     ; Scenario FogOfWar 位（0x1000）
0x0047F024 = 8B 0D 90 E7 89 00 mov ecx,[0x89E790]  ; 位=1 => FOG.SHP
0x0047F02F = 8B 15 94 E7 89 00 mov edx,[0x89E794]  ; 位=0 => SHROUD.SHP ★未探索全黑
0x0047F226 = 33 C0 8A 06 46 3B 05 B8 4E 7E 00 74 03 66 89 07   ; 透明索引拷贝（无混色）
0x0047F24A = C2 0C 00 90 90   ret 0xc + NOP         ; 函数边界：0x47EFE0 与 0x47F250 是**两个**函数
```

我方 `UpdateVisionGrid()` 每逻辑帧执行 `*Scenario &= ~0x1000`（源码 `blitter_hooks.cpp:990`，注释见 :985-987）⇒ 位恒 0 ⇒ **恒走 SHROUD.SHP**。

**逐格是否画**：`CellClass::Draw` 先经引擎逐格查询 `0x6D8700` 决定遮蔽档（`0x006D8724`：读 `CellClass::Flags(+0x140)`，`(Flags&3)==0` ⇒ `-2`「Occluded completely」），结果写入 `CellClass+0x120 = Shroudedness`（`0x480207`），再由 `0x48020D` 映射为帧号（`-2 ⇒ 0xF`、`-1 ⇒ 0`）—— 引用口径：`ref/yrpp/CellClass.h:407-408`（`-2: Occluded completely / -1: Visible / 0..48: frame`）。

### 2.2 我方侧：旧版为何「连未探索黑幕一起消失」（对 ZC-4 S2 观测的机制解释）

**观测事实**：ZC-4 S2（总闸=0）三计数**恒 0**（`半透明层绘制次数=0`、`混色桩介入次数=0`、`小地图减暗驱动次数=0`），即**我方层零绘制**；然而主视图整图透出、S1 的「近黑」区（3.77%）不再存在。⇒ 差值**不可能来自我方绘制**，只能来自同档被一并切断的**非绘制耦合**。

**两条候选耦合（[推演]，静态无法定谳哪一条，故两条都解除）**：

| # | 旧版行为 | 后果链 | 本版处置 |
|---|---|---|---|
| (a) | `Hook_CellClass_Draw` 在总闸=0 时 **整段 return** ⇒ `UpdateVisionGrid` 不再被每格调用 | 该函数是「维持 Scenario FogOfWar 位=0」的常规执行点 ⇒ 位可能保持引擎原值=1 ⇒ `0x47EFE0` 改用 **FOG.SHP**（源码注释已记录该现象：「未探索区域变成透明高亮黄白色」） | **解除**：`UpdateVisionGrid` 恒调用（产物 RVA `0x2048`） |
| (b) | `Hook_L4FullRedraw_Stub` 在总闸=0 时恢复原版 `jge` | 静态镜头下战术重绘改走增量/dirty-rect 路径 ⇒ 黑幕唯一承载函数（`0x47EFE0`）的调用循环不再每帧遍历全部可见格 | **解除**：L4 桩**无**总闸分支（产物 RVA `0x2390` 起 7 字节仅 `mov ecx,0x6D3E37` / `jmp ecx`） |
| (c) | 小地图原生减暗驱动 / H2 跳帧强驱被摘除 | 仅影响小地图「已探索非直视」档表现（属总闸应管范围） | **保留**（总闸=0 时该档驱动次数应为 0，符合新语义） |

### 2.3 产物侧：总闸作用域收敛为「单点」（★F1 的结构性论证）

产品反汇编中 `g_enableStarCraftFog`（VA `0x1002100B`）的全部引用（6 处）：

| RVA | 用途 | 是否在绘制路径 |
|---|---|---|
| `0x13E1` / `0x14E8` | 启动日志（`EnableStarCraftFog=%d`）与镜像同步 | 否 |
| `0x3626` | `UpdateVisionGrid` 内（渐变过渡分支） | 否（不影响绘制） |
| **`0x2105`** | **主视图**：`cmp [g_enableStarCraftFog],0` → `jne` 继续；=0 则计数后返回 | **是（唯一）** |
| `0x48A3` | 小地图自绘档（mode 0/1/2，非默认档） | 小地图侧 |
| `0x49E9` | 小地图原生档驱动（mode 3） | 小地图侧 |

⇒ **主视图上总闸=0 与 =1 的差值集合 = {「已探索且非直视」档是否调用 `0x47F250`}**，未探索档与直视档在总闸判定**之前**就已分流完毕（`0x2072` 未探索 / `0x211E` 直视），二者**与总闸取值无关**。

### 2.4 产物侧：三处玩法门控已与总闸解耦

| 钩子 | 门控地址 | 产物 RVA | 备注 |
|---|---|---|---|
| `Hook_Unit_Draw` | `0x1002100F`（`g_enableUnitFog`） | `0x1950` | 旧版为 `g_enableStarCraftFog` |
| `Hook_Infantry_Draw` | `0x1002100F` | `0x2330` | 同上 |
| `Hook_Aircraft_Draw` | `0x1002100F` | `0x2608` | 同上 |
| `Hook_Building_Draw` | `0x1002100D`（`g_enableBuildingFog`） | `0x1F50` | **未变**（本就独立） |
| `Hook_Bullet_Draw` | `0x1002100E`（`g_enableBulletFog`） | `0x1FA0` | **未变**（本就独立） |

### 2.5 机器可读断言

* 引擎侧 27 条：`out/re_work/fog_split/claims_exe.txt`
* 产物侧 35 条：`out/re_work/fog_split/claims_dll.txt`（口径：VA' = 0x400000 + RVA）
* 独立复算脚本：`out/re_work/fog_split/verify_dll_bytes.py`（按 PE 头真实 ImageBase=0x10000000）

---

## [3] 勘误（本次新增，逐条给）

| # | 目标 | 改前原文 | 改后文本 | 理由 | 影响面 |
|---|---|---|---|---|---|
| **E0** | 任务卡 F5 基线描述 | 「两份 ini 均 `0DAD9A41…`（…7,001 B）」 | 开工时实测两份 ini = **7,047 B / SHA-256 `26E7297E0450F2E3B33CC81316F406EEC7D3F3755515DB7401B57DF1F5A47A6D`**；与 ZC-4 快照（`out/re_work/zcode_live/zc4/ra2render.ini.before`，7,001 B / `0DAD9A41…`）逐行 diff = **仅 1 行注释**（总闸 `=0` 语义那句措辞）不同；**全部键值与默认值零变化** | 会话快照口径（双快照声明，见 [META]） | 无（键值未变）；本版已重写 §[FogOfWar] 注释 ⇒ 以本版 9,459 B / `8D289390…` 为准 |
| **E1** | 任务卡 F2 前提 | 「ZC-4 实测 S2 中「迷雾剔除机动单位/半透明迷雾格子/建筑剔除」计数全 0」 | S2 原始日志实测：**建筑剔除 337→1,484、弹道剔除 6→49（均 >0）**；恒 0 的只有「迷雾剔除机动单位」与「半透明迷雾格子」 | 直接引用 ZC-4 日志原文（`s2_master0_session.txt`，44 条 telemetry 行一致） | **改变 F2 的修复面**：建筑/弹道**无需修**（本就生效）；真正需修的只有机动单位剔除（已修）。若按原前提去「修」建筑/弹道，会误改两条正常路径 |
| **E2** | 任务卡 F7 判据③ | 「建筑剔除/弹道剔除计数仍 >0 且量级与总闸=1 相当」 | 保留该判据，但**注明**：量级差异的主因是旧版「全量重绘」（L4）耦合解除前后**重绘频次**不同 —— S1（总闸=1，旧版）建筑剔除 24,542 vs S2（总闸=0，旧版）1,484 = 16.5× 差；本版两档**同为强制全量重绘** ⇒ 量级应可比 | 旧版重绘频次差异会污染「量级相当」判据 | 真机判据表述更严谨（以真机读数为准） |
| **E3** | 源码 `ra2render/ra2render.h` 旧宏注释 | `#define OFF_CELL_FLAGS 0x12C // bit3 = 已探索` | 「`+0x12C = CellClass::CopyFlags`；其 `0x08 = cf2_NoShadow`、`0x02 = cf2_ContainsBuilding`（`ref/yrpp/GeneralDefinitions.h:557-560`）；**已探索**位 `cf_Explored=0x08` 在 `+0x140 = CellClass::Flags`（同文件 :549「this means no shroud」）」 | 旧注释与 YRpp 定义冲突，且旧钩子据此做了错位的「未探索」判定 | **行为修正**：新钩子改用引擎口径 `Shroudedness(+0x120)==-2` ⇒ 我方对未探索格从「可能误上手」变为「结构性零介入」 |
| **E3·就地订正**（[FOG-MODE F7①] 2026-09-28，**保留原记**） | 本报告 §E3（上一行）与 §E4 的「判据」栏 | 【原记】「`+0x12C` 是 CopyFlags，其 `0x08 = cf2_NoShadow`…『已探索』位 `cf_Explored = 0x08` 在 `+0x140`；旧注释『bit3 = 已探索』已被证伪」 | **★改为**：「`CellClass::CopyFlags(+0x12C)` 的 **bit3(0x08) = `cf_Explored`（已探索）**」——UNIT-VIS **二进制读写双向**证据：读点 `0x005863F2  F6 81 2C 01 00 00 08  test byte ptr [ecx+0x12C],8`（位于引擎黑幕谓词 `MapClass::IsLocationShrouded 0x00586360` 内，`0x586483 mov al,1`/`0x58648C xor al,al`）；写点 `0x004A98E6 mov eax,[ebp+0x12C]` / `0x004A98EC **or al,8**` / `0x004A98F0 mov [ebp+0x12C],eax`（揭示路径） | 「旧注释已被证伪」这一**证伪本身**被反向证伪：`cf2_NoShadow` 属另一族命名，不能据以否证 +0x12C 的「已探索」语义（详见 `docs/re/unit_visibility_mechanism.md` §[2] F2-6 与 §[3] E1） | **零行为影响（纯文档/注释）**：本版钩子仍读引擎自身判定 `Shroudedness(+0x120)==-2`（更贴近引擎每帧口径），故 §E3 的「行为修正」结论不变；连带更正 §E4 中「原实现的 `CopyFlags & 0x08` 位与『已探索』**无**对应关系」一句 —— 该位**就是**「已探索」，改判据只为贴引擎口径，并非原判据错位 |
| **E4** | 旧版源码注释（`Hook_CellClass_Draw`） | 「黑雾检查：若未探索或被裂缝产生器覆盖，原版已画全黑，绝不再画灰雾」 | 同结论保留，但判据改为可实证的 `Shroudedness == -2`（原实现的 `CopyFlags & 0x08` 位与「已探索」无对应关系） | 同上 | 无（结论不变，判据变可证） |
| **E5** | `docs/re/fog_switch_report.md` §[1] F3-1 / §附录 C.4 | 「F3① 启动行 = `.rdata RVA 0x18D28`（引用点 `0x15FE`）」 | **RVA `0x187F0`**（VA `0x100187F0`）；`0x18D28` = 常规遥测行 | 【F8 要求·已就地订正，原记保留】对 135,680 B 件文本搜索实证 | 仅文档锚点（不影响行为结论） |
| **E6** | `docs/re/fog_switch_report.md` §附录 C 的 `inc` 地址 | 「`0x100020A3` 等（指令起点口径）」 | 补口径说明：**imm32 起点 = 指令起点 +2**，二者同一条指令 | 【F8 要求·已就地订正，原记保留】 | 无（同指令） |
| **E7** | 旧版源码注释（总闸 4 条短路说明）与 ini 旧注释 | 「总闸=0 ⇒ ①FOG.SHP 层不绘制 ②混色桩 B1/B2 不混色 ③小地图不驱动 ④L4 不触发」 | 重写为新三态语义（本轮 E5/E6 之外的旧描述在 `fog_switch_report.md` 正文中**保持原样**，仅追加一条指向本报告的说明） | 用户裁决重定义语义 | 产品语义变更（本报告为其实现与本版判据的权威口径） |

> 若需把 E0–E7 回填台账/他人文档，请由 Lead 处置（本任务写作用域不含台账与其它 docs，F8 两处除外）。

---

## [4] 未闭环清单

| # | 缺口 | 为何无法静态闭环 | 下一步取证方法 | 阻塞级别 |
|---|---|---|---|---|
| U1 | 未探索黑幕**观感**（总闸=0 时仍全黑）、已探索非直视与直视亮度一致 | 本任务**明令禁止启动游戏/注入**（真机交 ZCode） | 按附录 C 执行；产出截图 + 亮度直方图 + 两段日志（含 `[ra2render-telemetry-fogsplit]` 行） | **P0（验收）** |
| U2 | ZC-4 S2「整图透出」的**唯一**根因（(a) Scenario 位 vs (b) L4 重绘路径） | 无法运行游戏做单变量隔离；静态只能证明「两者都被旧版切断、且都在 `0x47EFE0` 的**上游**」 | 真机单变量：本版两档都保留黑幕 ⇒ 若新件两档都黑即闭环「已修复」；若仍异常，用 `s_shroudBlackDraws` 与 `[Scenario]&0x1000` 探针区分 (a)/(b) | **P1** |
| U3 | 建筑/弹道剔除计数的**跨档量级**（S1 24,542 vs S2 1,484） | 需真机同场景对比（旧版量级差已按 E2 归因于重绘频次，但缺 A/B 实证） | 本版固定两档各跑同场景 ≥10 秒，比 `建筑剔除/弹道剔除` 绝对量级（应同阶） | **P2** |
| U4 | `s_shroudBlackDraws` 的**帧内倍数**语义（每格每帧 1 次 ⇒ 值 = 格·帧 累计，非「独立黑幕区域数」） | 设计属性（追求零成本），非缺陷 | 判据只看「>0 且随帧增长」；若需区域数可改用 token 去重（会加每格开销） | **P2** |
| U5 | `s_shroudBlackDraws` 为 `uint32`，每帧 ~600–2000 次 ⇒ 长局理论回绕（4.29e9 ≈ 数十小时） | 与既有 `s_fogLayerDraws` 同口径 | 如需绝对计数改 64 位 | **P2** |
| U6 | 联机（MpActive）侧总闸纪律未实测 | 单机环境不便构造联机会话（任务卡许可跳过） | 既有约束未变（`EnableMinimapFog` 在 MpActive 下强制 0；本特性联机不放开）；若未来放开需双端对拍 | **P1（仅当放开联机）** |

---

## [5] 写作用域合规声明

**改动文件清单**

| 文件 | 性质 | 字节数 / 行数 | 时间 | 哈希 |
|---|---|---|---|---|
| `ra2render/blitter_hooks.cpp` | 编辑：F1 三态判定 + F2 解耦 + F3 遥测 + 0x47EFE0 只读计数桩 + L4 桩解耦 | 132,852 B / 1,996 行 | 15:58–16:03 | MD5 `CB4D5E72888B08B2494C99787906EC22` |
| `ra2render/ra2render.h` | 编辑：新地址宏（`0x47EFE0` + 恢复点）、CellClass 三态字段宏、`g_enableUnitFog` 声明、旧宏勘误注释 | 19,737 B / 288 行 | 15:57–16:00 | MD5 `CF78CED41114938ACF7040130F45E0B3` |
| `ra2render/ra2render.ini` ≡ `ra2youli/ra2render.ini` | 编辑（**仅注释** + 新增 `EnableUnitFog=1`） | 9,459 B / 100 行 | 16:04 | SHA-256 `8D289390EEFF93BF115863461D43E8BD00FE5F6FA39E93C4BE2377384BB6C902` |
| `ra2render/ra2render.dll` ≡ `ra2youli/ra2render.dll` | 构建产物并部署 | 138,752 B | 16:03 | MD5 `59671E8BC333A999820C788D76A5B375` |
| `docs/re/fog_split_report.md` | 新建（本文件） | 见 §[8] | 16:1x | — |
| `docs/re/fog_switch_report.md` | 编辑（**仅 F8 两处勘误 + E5/E6 表格行 + 一条指向新版的追加说明**；原文一律以【原记】保留） | 49,019 B | 16:08 | MD5 `299F27FC0A54CE0CA72EAEF71B615942` |
| `out/re_work/fog_split/**` | 新建（证据/脚本/claims/备份/清单） | 见 §[8] | 15:56–16:1x | — |

**ini 键值逐键比对（证明默认值未改）**

| 键 | 现值 | 说明 |
|---|---|---|
| `EnableSIMD` / `TargetScanInterval` / `TargetScanKey` / `UnlockGameSpeed` / `EnableLFH` / `HighPrecisionTimer` | 1 / 8 / position / 0 / 1 / 1 | 未动 |
| `EnableStarCraftFog` | **1** | 总闸（未动） |
| `EnableSpySatRadarSweep` / `RadarSweepCooldownFrames` / `RadarSweepRadiusCells` | 1 / 600 / 16 | 未动 |
| `EnableBuildingFog` / `EnableBulletFog` | 1 / 1 | 未动 |
| **`EnableUnitFog`** | **1（新增键，API 默认值同为 1）** | 本版新增，逻辑可见性键，不受总闸影响 |
| `FadeFogTransition` | 1 | 未动 |
| `EnableMinimapFog` / `RadarFogGuardMode` | 0 / 3 | 未动 |

**未触碰清单（逐项声明）**

* `ra2youli/gamemd.exe` —— **只读**：MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367` / 4,825,360 B（开工=收工一致）
* 任何 `.mix` / `.map` / `.sav`；工作区根部 `temp*.mix`、`scratch_*.shp`
* `ra2forge/**`、`mcp/**`、`ra2opt/**`
* 台账 `REVERSE_ENGINEERING_AND_PATCHES.md`、`docs/RE_COORDINATION.md`、`docs/re/radar_fix2_report.md`、其它 `docs/**`（**唯一例外**：F8 明令的 `docs/re/fog_switch_report.md` 两处勘误）
* `docs/re/anchor_claims.txt`（仅运行 `verify_anchors.py` 复核）
* `ra2render/build.bat`（未修改；loader 部署保持可选，本次构建同样 skip）

---

## [6] 门禁实跑输出（原文粘贴，不许概述）

> 注：本节粘贴的原始输出中，Windows 路径分隔符在本文档内统一写作 `/`（内容其余逐字保留）；完整存档文件中的分隔符为原始 `\`。

### 6.1 构建（F5）

```text
> cmd /c ra2render/build.bat
**********************************************************************
** Visual Studio 2022 Developer Command Prompt v17.14.33
**********************************************************************
[vcvarsall.bat] Environment initialized for: 'x86'
Building ra2render.dll...
dllmain.cpp
blitter_hooks.cpp
正在生成代码...
Building ra2loader.exe...
ra2loader.cpp
        1 file(s) copied.
[build.bat] skip ra2loader.exe deploy (default). Set RA2RENDER_DEPLOY_LOADER=1 to deploy it.
ALL BUILDS FINISHED SUCCESSFULLY
```

### 6.2 全库锚点回归（须 323/323 PASS）

```text
> python tools/verify_anchors.py
目标文件 : D:/Project/ra2-campaign-forge/ra2youli/gamemd.exe (大小: 4,825,360 字节, ImageBase: 0x400000)
断言文件 : D:/Project/ra2-campaign-forge/docs/re/anchor_claims.txt
反汇编器 : Capstone x86-32 引擎已就绪
-------------------------------------------------------------------------------------------------------------------
[基线完整性审计]
  [PASS] .text 原始段哈希: c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738 (口径: raw(SizeOfRawData=0x3E0000))
  [INFO] PE头特征判定 : RA2OPT_PERF_APPLIED (0xAE=0x20, Stack=4MB, .text未变) (DllChar: 0x20, StackReserve: 0x400000)
  [PASS] .detour 原生签名: 40 00 00 00 44 74 72 00 (@ VA 0xb93000) -> 严禁写入/注入原则确立
-------------------------------------------------------------------------------------------------------------------
回归汇总 : 断言总数 323 条 | PASS: 323 (100.00%) | FAIL: 0 | NOREAD: 0
★ 最终裁决 : [100% ALL PASS] 全库决定性锚点与二进制基线完全一致，生产环境可安全放行！
===================================================================================================================
```

### 6.3 引擎侧 claims（27 条）

```text
> python tools/audit_bytes.py out/re_work/fog_split/claims_exe.txt        （尾部原文）
0x81ce10   46 4f 47 2e 53 48 50 00      46 4f 47 2e 53 48 50 00 OK    FOG.SHP 字符串 | inc esi
0x81ce18   53 48 52 4f 55 44 2e 53 48 50 00  53 48 52 4f 55 44 2e 53 48 50 00 OK   SHROUD.SHP 字符串 | push ebx
--------------------------------------------------------------------------------------------------------------
合计 27 条：OK=27  MISMATCH/NOREAD=0
（全文存档：out/re_work/fog_split/gate_audit_exe.txt）
```

### 6.4 产物侧 claims（35 条，两个独立口径）

```text
> python tools/audit_bytes.py out/re_work/fog_split/claims_dll.txt --exe ra2youli/ra2render.dll      （尾部原文）
0x402ba5   c6 05 9a 71 65 00 e8      c6 05 9a 71 65 00 e8   OK   补丁写入：0x65719A <- 0xE8（未变） | mov byte ptr [0x65719a], 0xe8
0x402c72   c6 05 87 5d 65 00 e9      c6 05 87 5d 65 00 e9   OK   补丁写入：0x655D87 <- 0xE9（未变） | mov byte ptr [0x655d87], 0xe9
--------------------------------------------------------------------------------------------------------------
合计 35 条：OK=35  MISMATCH/NOREAD=0
（全文存档：out/re_work/fog_split/gate_audit_dll.txt）

> python out/re_work/fog_split/verify_dll_bytes.py       （按 PE 头真实 ImageBase=0x10000000 独立复算）
DLL D:/Project/ra2-campaign-forge/ra2youli/ra2render.dll  size=138752  md5=59671E8BC333A999820C788D76A5B375  真实 ImageBase=0x10000000
  0x401FCB   RVA 001FCB 真VA 10001FCB OK   exp=A1 E0 19 02 10 85 C0 74 0C FF 74 24 0C 8B CE FF 74 24 0C FF got=(同)  Hook_CellClass_Draw 头部：原版调用（g_pOrigCellClassDraw）恒定执行
汇总：35 OK / 0 FAIL
（全文存档：out/re_work/fog_split/gate_verify_dll_truebase.txt）
```

### 6.5 obj 符号表（F6③ 新符号齐备）

```text
> dumpbin /symbols ra2render/blitter_hooks.obj        （节选原文，全文 out/re_work/fog_split/F6_obj_symbols.txt）
014 0000000B SECT4  notype       External     | ?g_enableStarCraftFog@@3_NA (bool g_enableStarCraftFog)
01A 0000000F SECT4  notype       External     | ?g_enableUnitFog@@3_NA (bool g_enableUnitFog)
045 002C00E8 SECT3  notype       External     | _s_fogLayerDraws
04A 002C00FC SECT3  notype       External     | _s_shroudBlackDraws
04B 002C0100 SECT3  notype       External     | _s_shroudEdgeDraws
04C 002C0104 SECT3  notype       External     | _s_fogUnexploredPassed
04D 002C0108 SECT3  notype       External     | _s_fogVisiblePassed
04E 002C010C SECT3  notype       External     | _s_exploredFogDarken
04F 002C0110 SECT3  notype       External     | _s_gate0DarkenSkipped
050 002C0114 SECT3  notype       External     | _s_radarUnexploredPassed
051 002C0118 SECT3  notype       External     | _s_pDrawShroudFogTrampoline
197 00000000 SECT42 notype ()    External     | ?Hook_DrawShroudFog_Stub@@YAXXZ (void __cdecl Hook_DrawShroudFog_Stub(void))
19A 00000000 SECT47 notype ()    External     | ?Hook_L4FullRedraw_Stub@@YAXXZ (void __cdecl Hook_L4FullRedraw_Stub(void))
```

---

## [7] 风险与红线提示

* ① **同步语义 / 命令序**：**未新增任何引擎状态写**。相较旧版总闸=0 档，本版**恢复了 1 处引擎状态写的常规执行**（`UpdateVisionGrid` 内的 `*Scenario &= ~0x1000`，与总闸=1 档行为**相同**，属既有 S2 面）。新增的 0x47EFE0 钩子**只读**（`mov al,[ecx+0x120]`）并自增 DLL 私有计数，不改任何引擎内存。
* ② **随机数消费序**：**未触及**（无 RNG 调用点或节拍变化）。
* ③ **存档结构**：**未触及**（无序列化字段；全部 `s_*` 为 DLL 私有静态）。
* ④ **渲染像素等价性**：**触及**。总闸=1 档的「已探索非直视」绘制路径与原版逐位一致（仅总闸判定位置前移，比较结果相同、绘制指令同序同值）；但**未探索/直视两档的判定判据已换**（`CopyFlags&0x08` → 引擎 `Shroudedness==-2`）⇒ 我方在未探索格上**不再可能**叠加绘制（此前可能叠加；因该处已是黑幕，观感差异预期极小）。**像素级等价需真机对拍**（U1/U2/D4）。
* ⑤ **玩法可见性**：机动单位剔除改由新键 `EnableUnitFog`（默认 1）门控 ⇒ **出厂行为不变**；建筑/弹道门控未动。
* **需要 MP 门控矩阵 / 真机对拍验收**：**是**。联机既有约束未变（`EnableMinimapFog` 在 `MpActive` 下强制 0；`TargetScanKey` 强制 position）。本改动**不宣称「零风险 / 零 Desync」**。
* **禁止事项遵守**：**未启动游戏、未注入、未改 exe、未伪造实测** —— 所有真机项一律标 [待实测] / [纸面规格]；`gamemd.exe` 只读（MD5 未变）。

---

## [8] 交付物清单

| 类型 | 路径 | 规模 |
|---|---|---|
| 代码 | `ra2render/blitter_hooks.cpp`、`ra2render/ra2render.h` | 132,852 B / 19,737 B |
| 产物 | `ra2render/ra2render.dll` ≡ `ra2youli/ra2render.dll` | 138,752 B / MD5 `59671E8B…` |
| 配置 | `ra2render/ra2render.ini` ≡ `ra2youli/ra2render.ini` | 9,459 B / SHA-256 `8D289390…` |
| 报告 | `docs/re/fog_split_report.md`（本文件）+ `out/re_work/fog_split/ZCODE_ACCEPTANCE_FOG_SPLIT.md` | 2 份 |
| 勘误（就地） | `docs/re/fog_switch_report.md`（F8 两处 + E5/E6 行 + 一条追加说明） | 49,019 B |
| 断言 | `claims_exe.txt`（27）、`claims_dll.txt`（35） | 62 条，全 OK |
| 校验脚本 | `gen_claims.py`、`verify_dll_bytes.py`、`prod_scan.py`、`prod_scan2.py`、`prod_scan3.py`、`prod_scan4.py`、`prod_scan5.py`、`prod_dump.py`、`mk_evidence.py`、`rva_probe.py`、`zc4_counters.py`、`ini_diff.py`、`shp.py`、`imgstat.py`、`ratio.py`、`dump1.py`–`dump6.py`、`sym.bat` | 21 支（可复跑） |
| 证据 dump | `out/re_work/fog_split/evidence/`：`F6_prod_cellclass_hook.txt`、`F6_prod_shroud_stub.txt`、`F6_prod_l4_stub.txt`、`F6_prod_unit_hooks.txt`、`F6_prod_radar_decide.txt`、`F6_prod_install_patches.txt`、`F6_prod_install_shroud.txt` | 7 份 |
| 门禁原文 | `gate_audit_exe.txt`、`gate_audit_dll.txt`、`gate_verify_dll_truebase.txt`、`F6_obj_symbols.txt`、`gen_claims_out.txt` | 5 份 |
| 备份 | `ra2render.dll.bak-491C25F9`（135,680 B）、`ra2render.ini.bak-26E7297E`（7,047 B，= 开工时部署态）；另存 ZC-4 快照 `ra2render.ini.zc4-0DAD9A41`（7,001 B） | 3 件 |
| 引擎侧取证 | `claims_exe.txt` 覆盖：黑幕层入口 / 图像选择 / 唯一调用者 / 两道位门 / L4 / 三挂钩点 / 字符串 | 27 条 |

---

## [9] 待裁决项（需人/Lead 决定的分叉，附建议）

| # | 分叉 | 建议 | 理由 |
|---|---|---|---|
| D1 | L4 全量重绘（`0x006D3D99`）是否重新对总闸门控？ | **维持本版「与总闸无关、恒强制全量重绘」**；待 U2 真机定谳后再议 | 该耦合是「总闸=0 连未探索黑幕一起消失」的两条候选之一；在真机确证根因前，与总闸解耦是**保证裁决①**的最稳做法。代价：总闸=0 档仍付全量重绘开销（画面表现类，逻辑无关） |
| D2 | 是否给「机动单位剔除」独立成键（`EnableUnitFog`）？ | **本版已新增**（默认 1 = 旧行为）；若 Lead 要求「零新增键」，可回退为「恒开启」——但不推荐（失去可控性与 A/B 能力） | 旧版该能力被总闸裹挟（违反裁决②）；独立成键后可单变量验证 F2 与 F7③ |
| D3 | `s_shroudBlackDraws` 判据门槛（>0 还是「随帧线性增长」） | 建议真机读**两行**遥测：要求**严格递增且第二轮 ≥ 第一轮** | 单看 >0 无法排除「只画了一帧」 |
| D4 | 总闸=1 档与旧件（`491C25F9`）的**逐像素**等价性 | 建议 U1 插一组回归：旧件 vs 新件（总闸=1 同场景）逐像素 diff | 本版换了「未探索/直视」判据（E3/E4）⇒ 总闸=1 档理论上仍可能有极细微差异（仅涉及原本已被黑幕覆盖的格），需对拍确认 |
| D5 | 「未探索黑幕绘制次数」是否升级为 64 位 | 暂不（与既有计数同口径） | 判据只看趋势；64 位改法在每格热路径加 1 条指令 |

---

# 附录 A. 未探索黑幕路径说明（F1 必答：走哪条路径、为何不受影响）

## A.1 路径（一条链，无分叉）

```text
战术格绘制循环（0x6D3693 循环体 / 另一处 0x6D751A）
   └─ call 0x4801F0                CellClass::Draw
        ├─ 0x6D8700(cell, which=0) 引擎逐格遮蔽查询：读 CellClass::Flags(+0x140)，(Flags&3)==0 ⇒ -2
        ├─ 0x480207  写 CellClass::Shroudedness(+0x120) = -2 | -1 | 0..48
        ├─ 0x48022E/0x480230  mov ecx,esi / call 0x47EFE0   ★恒定执行（在 0x480251 位门之前）
        │     └─ 0x47EFE0：懒加载 SHROUD.SHP([0x89E794])、FOG.SHP([0x89E790])
        │          ├─ 0x47F01F test ch,0x10（Scenario FogOfWar 位）
        │          ├─ 位=1 ⇒ 用 FOG.SHP（0x47F024）
        │          └─ 位=0 ⇒ 用 SHROUD.SHP（0x47F02F）★我方恒清该位 ⇒ 走这条
        └─ 0x480251 test dh,0x10 / je 尾声（位=1 时才再调 0x47F250 两次）—— 我方恒清位 ⇒ 不可达
```

## A.2 为何不受总闸影响（三重保证，逐条可验）

1. **补丁面**：我方在 `0x47EFE0` 安装的是**只读计数桩**（产物 RVA `0x21C0`–`0x21E4`）：`cmp ecx,0x10000` → `mov al,[ecx+0x120]` → `cmp al,0xFE` →（命中即）`inc [s_shroudBlackDraws]` →（否则 `cmp al,0xFF` / `inc [s_shroudEdgeDraws]`）→ `jmp dword ptr [s_pDrawShroudFogTrampoline]`。桩内**没有**任何总闸引用、没有写引擎内存、破坏面仅 `AL`+flags，而被回放的前 6 字节（`push ebp / mov ebp,esp / sub esp,0x34`）不读二者。
2. **耦合面**：旧版在总闸=0 时切断的两条**非绘制**耦合（§2.2 的 (a)(b)）已解除 —— `UpdateVisionGrid` 恒调用（`RVA 0x2048`，位于未探索判定之前）、L4 桩无总闸分支（`RVA 0x2390`）。
3. **作用域面**：主视图绘制路径上 `g_enableStarCraftFog` 只剩 `RVA 0x2105` **一处**判定，且位于 `0x2072`（未探索）与 `0x211E`（直视）**之后**（§2.3）⇒ **=0 的差值集合 = {已探索非直视档的 `0x47F250` 调用}**，未探索档与直视档的绘制**逐位不受总闸影响**。

## A.3 我方对未探索格的零介入不变量（可被真机反证）

* 主视图：`Shroudedness == -2` ⇒ 自增 `s_fogUnexploredPassed` 后 `jmp` 函数尾声（**不调用** `0x47F250`、**不写** `s_cellFogDrawnToken`、除 `UpdateVisionGrid` 外不调任何函数）
* 小地图：`!explored` ⇒ 自增 `s_radarUnexploredPassed` 后返回（**不写** `[esp+0x13]`，保持引擎自身判定）
* ⇒ 真机若观察到「未探索区仍全黑 + 上述两计数 >0 + `s_shroudBlackDraws` >0」，即三条独立证据同时成立。

---

# 附录 B. 产物级证据（反汇编原文节选）

> 对象：`ra2youli/ra2render.dll`（138,752 B / MD5 `59671E8BC333A999820C788D76A5B375`，真实 ImageBase `0x10000000`）。完整清单见 `out/re_work/fog_split/evidence/F6_prod_*.txt`。

## B.1 Hook_CellClass_Draw：三态判定 + 总闸作用域

```text
RVA 001FCB  A1 E0 19 02 10        mov eax,[0x100219E0]       ; g_pOrigCellClassDraw
RVA 001FD2  74 0C                 je 0x10001FE0
RVA 002035  8B CE                 mov ecx,esi
RVA 002037  FF D0                 call eax                   ; ★原版 CellClass::Draw 恒定执行（黑幕在此绘制）
RVA 002039  85 F6                 test esi,esi               ; pCell == 0 ?
RVA 002048  E8 D3 2B 00 00        call 0x10004C20            ; ★UpdateVisionGrid（(a) 已解耦：恒调用）
RVA 002072  80 BE 20 01 00 00 FE  cmp byte ptr [esi+0x120],0xFE   ; ★引擎口径未探索（Shroudedness == -2）
RVA 002079  75 0B                 jne 0x10002086
RVA 00207B  FF 05 54 1A 2E 10     inc dword ptr [0x102E1A54]     ; s_fogUnexploredPassed++（未探索格放行）
RVA 002081  E9 FB 00 00 00        jmp 0x10002181                 ; → 函数尾声（零引擎介入）
   ...  cellIdx / inVision / strength（含 4 帧渐变）计算 ...
RVA 002105  80 3D 0B 10 02 10 00  cmp byte ptr [0x1002100B],0     ; ★总闸（唯一绘制路径判定；位于三态分流之后）
RVA 00210C  75 0C                 jne 0x1000211A
RVA 00210E  85 D2                 test edx,edx
RVA 002110  7E 6F                 jle 0x10002181
RVA 002112  FF 05 60 1A 2E 10     inc dword ptr [0x102E1A60]     ; s_gate0DarkenSkipped++（强度被归零）
RVA 002118  EB 67                 jmp 0x10002181                 ; ★总闸=0 直接返回，不调 0x47F250
RVA 00211E  FF 05 58 1A 2E 10     inc dword ptr [0x102E1A58]     ; s_fogVisiblePassed++（直视档放行）
RVA 00213C  FF 05 38 1A 2E 10     inc dword ptr [0x102E1A38]     ; s_fogLayerDraws++（既有计数①）
RVA 002145  01 05 5C 1A 2E 10     add dword ptr [0x102E1A5C],eax ; ★s_exploredFogDarken += !inVision
RVA 002156  B8 50 F2 47 00        mov eax,0x47F250               ; 引擎 FOG.SHP 层
RVA 00215B  FF D0                 call eax
```

## B.2 Hook_DrawShroudFog_Stub：未探索黑幕绘制次数（引擎侧实测）

```text
RVA 0021C0  81 F9 00 00 01 00     cmp ecx,0x10000                 ; ecx = CellClass*（唯一调用者恒定传入）
RVA 0021C6  72 1C                 jb 0x100021E4
RVA 0021C8  8A 81 20 01 00 00     mov al,byte ptr [ecx+0x120]     ; ★只读 Shroudedness
RVA 0021CE  3C FE                 cmp al,0xFE
RVA 0021D0  75 08                 jne 0x100021DA
RVA 0021D2  FF 05 4C 1A 2E 10     inc dword ptr [0x102E1A4C]      ; ★s_shroudBlackDraws++（未探索黑幕）
RVA 0021D8  EB 0A                 jmp 0x100021E4
RVA 0021DA  3C FF                 cmp al,0xFF
RVA 0021DC  74 06                 je 0x100021E4
RVA 0021DE  FF 05 50 1A 2E 10     inc dword ptr [0x102E1A50]      ; s_shroudEdgeDraws++（边缘帧）
RVA 0021E4  FF 25 68 1A 2E 10     jmp dword ptr [0x102E1A68]      ; → 跳板（回放 6B 原指令后 jmp 0x47EFE6）
```

## B.3 Hook_L4FullRedraw_Stub：已与总闸解耦（(b)）

```text
RVA 002390  B9 37 3E 6D 00        mov ecx,0x6D3E37         ; 恒强制全量重绘
RVA 002395  FF E1                 jmp ecx
（对比旧版：RVA 0x22C1 起曾有 cmp [s_fogMasterGate],0 / je 原版 jge 分支 —— 本版已删除）
```

## B.4 玩法钩子门控（F2）

```text
RVA 001950  80 3D 0F 10 02 10 00  cmp byte ptr [0x1002100F],0   ; Hook_Unit_Draw：g_enableUnitFog（旧版为总闸）
RVA 00195D  E8 CE 2B 00 00        call 0x10004530               ; ShouldDrawMobileObject
RVA 001969  83 05 80 19 02 10 01  add dword ptr [0x10021980],1  ; unitsCulledByFog++
RVA 002330  80 3D 0F 10 02 10 00  cmp byte ptr [0x1002100F],0   ; Hook_Infantry_Draw
RVA 002608  80 3D 0F 10 02 10 00  cmp byte ptr [0x1002100F],0   ; Hook_Aircraft_Draw
RVA 001F50  80 3D 0D 10 02 10 00  cmp byte ptr [0x1002100D],0   ; Hook_Building_Draw（未变）
RVA 001FA0  80 3D 0E 10 02 10 00  cmp byte ptr [0x1002100E],0   ; Hook_Bullet_Draw（未变）
```

## B.5 小地图：未探索放行（不写引擎判定位）

```text
RVA 004904  8A 44 24 10          mov al,byte ptr [esp+0x10]    ; explored
RVA 004908  FF 05 24 1A 2E 10   inc dword ptr [0x102E1A24]    ; s_radarProbeOk++
RVA 004918  8A 4C 24 0B          mov cl,byte ptr [esp+0x0B]    ; inVision
RVA 004926  84 C0                test al,al                    ; explored == 0 ?
RVA 004928  75 08                jne 0x10004932
RVA 00492A  FF 05 64 1A 2E 10   inc dword ptr [0x102E1A64]    ; ★s_radarUnexploredPassed++
RVA 004930  EB 9B                jmp 0x100048CD                ; → 返回（**不经过** mov [eax],bh）
RVA 004934  0F 94 C7             sete bh                       ; ours = (!inVision)（此处 explored != 0）
RVA 004967  FF 05 40 1A 2E 10   inc dword ptr [0x102E1A40]    ; s_radarDarkenDriven++
RVA 004970  88 38                mov byte ptr [eax],bh         ; *[esp+0x13] = ours（仅已探索档）
```

## B.6 挂钩点补丁写入点（未变项逐条）

```text
RVA 002798  C6 05 F0 01 48 00 E9  mov byte ptr [0x4801F0],0xE9   ; CellClass::Draw 5B（未变）
RVA 002A33  C6 05 E0 EF 47 00 E9  mov byte ptr [0x47EFE0],0xE9   ; ★新增：黑幕层只读计数桩（6B）
RVA 002A4E  C6 05 E5 EF 47 00 90  mov byte ptr [0x47EFE5],0x90   ; ★新增：6B 补丁尾部 NOP
RVA 002B38  C6 05 38 5D 65 00 E9  mov byte ptr [0x655D38],0xE9   ; H1（未变）
RVA 002BA5  C6 05 9A 71 65 00 E8  mov byte ptr [0x65719A],0xE8   ; H2（未变）
RVA 002C72  C6 05 87 5D 65 00 E9  mov byte ptr [0x655D87],0xE9   ; H3（未变）
RVA 002ED1  C6 05 F0 8D 6F 00 E9  mov byte ptr [0x6F8DF0],0xE9   ; Greatest_Threat（未变）
```

---

# 附录 C. 真机复验清单（F7，交 ZCode）

> 前提：`ra2youli/gamemd.exe` 为基线；DLL = 138,752 B / MD5 `59671E8BC333A999820C788D76A5B375`；ini = 9,459 B / SHA-256 `8D289390…`。
> 单变量纪律：**全程只改 `[FogOfWar] EnableStarCraftFog`（A 组 =0 / B 组 =1）**，其余键固定：
> `EnableMinimapFog=1`、`RadarFogGuardMode=3`、`EnableBuildingFog=1`、`EnableBulletFog=1`、**`EnableUnitFog=1`**、`FadeFogTransition=1`。
> 独立清单文件：`out/re_work/fog_split/ZCODE_ACCEPTANCE_FOG_SPLIT.md`。

## C.1 场景（关键：必须让「未探索区」在视野内）

1. 载入**战役局内**存档（或新开战役），**镜头不动**；确保屏幕内同时存在三类区域：① **未探索区**（纯黑，对应 S1 的「近黑」带）② **已探索非直视区**（B 组应有灰雾）③ 己方/盟友**直视区**。
2. 标记三类区域的**固定采样矩形**（像素坐标），A/B 两组**完全一致**。
3. 速度默认；不要按 `+`/`-`；不要滚动镜头（避免 (b) 类耦合干扰复现）。

## C.2 步骤

| 步 | 动作 | 记录 |
|---|---|---|
| C0 | 启动进入局内，等待 ≥10 秒 | `ra2render.log` 首屏 `[ra2render-fog] 灰雾总闸: …` 行（应含 `EnableUnitFog=…` 与「[FOG-SPLIT] 总闸语义」段） |
| C1 | **A 组**（总闸=0）→ 重启 → 同一场景，等 ≥8 秒 | ① 主视图截图 ② 小地图截图 ③ 抓 **2 行** `[ra2render-telemetry-fogsplit]`（间隔 ≥4 秒）④ 同步抓 `[ra2render-telemetry]` 行（玩法三计数） |
| C2 | **B 组**（总闸=1）→ 重启 → 同一场景 | 同上四项 |
| C3 | 像素统计 | 对 A/B 两组的三类采样矩形做亮度直方图（口径见 §C.3） |
| C4 | 还原 | ini 还原为部署态并贴 sha256；确认无 `except.txt` 更新（无崩溃） |

## C.3 判据（A 组 = 总闸=0，逐条缺一不可）

| # | 判据 | 机器口径（可脚本化） |
|---|---|---|
| ① | **未探索区仍全黑** | 采样矩形「未探索」区亮度中位数 ≤ B 组同区 + 3/255；且 A 组该区**远暗于**「直视」区（比值 ≤0.15） |
| ② | 已探索非直视区与直视区**亮度一致**（无压暗） | A 组两区同种地表像素亮度中位数差 ≤ 3/255；B 组同两区应有系统性差（压暗比 ≈0.29–0.31，ZC-4 口径） |
| ③ | 玩法三计数 **两档都 >0 且同阶** | A 组 `机动单位剔除`/`建筑剔除`/`弹道剔除` 均 >0，且与 B 组同场景同机位**同数量级**（比值 0.3–3） |
| ④ | 「已探索非直视压暗次数」与「小地图已探索非直视减暗驱动次数」**≡0** | A 组 `s_exploredFogDarken=0`、`s_radarDarkenDriven=0`（连同既有三计数 `半透明层绘制次数=0`/`混色桩介入次数=0`） |
| ⑤ | 「未探索黑幕绘制次数」**>0** | A 组 `未探索黑幕绘制次数 > 0` 且**严格递增**（第 2 行 ≥ 第 1 行）；辅证：`未探索格放行次数 > 0` |
| ⑥ | B 组与 ZC-4 S1 同构 | `半透明层绘制次数`/`混色桩介入次数`/`小地图减暗驱动次数` 三计数增长；观感有灰雾 |
| ⑦ | 无崩溃 + ini 还原 | `except.txt` 未更新；两份 ini 还原后 sha256 = `8D289390…`（或 A/B 编辑态各自哈希） |

## C.4 注意事项

* **A 组若仍见未探索区透出地形**：先看 `未探索黑幕绘制次数` 是否 >0 ——
  * `>0` 但画面仍亮 ⇒ 黑幕层被调用但被覆盖/未落屏，回报「(b) 类（重绘路径）」并附 `s_shroudBlackDraws` 曲线；
  * `≡0` ⇒ 引擎黑幕层根本没被调用，回报「(a) 类（Scenario FogOfWar 位 / 调用循环）」并附 `[Scenario]&0x1000` 探针值。
* **A 组若仍见灰雾压暗**：读既有三计数区分：`半透明层绘制次数`>0（我方层未归零）/ `混色桩介入次数`>0（混色桩路径）/ `小地图减暗驱动次数`>0（小地图未关）。
* 机器判定优先，观感只作辅证；每局至少两行遥测（`fogsplit` + 常规行）并附截图与采样矩形坐标。

---

# 附录 D. 遥测字段与地址表（本版）

**既有行（字段与顺序零变化）**

`[ra2render-telemetry-fogswitch] 灰雾总闸: EnableStarCraftFog=%d | 半透明层绘制次数: %u | 混色桩介入次数: %u | 小地图减暗驱动次数: %u | (工具.asm 镜像=%u)，总闸=0 时三计数应恒 0`（产物 RVA `0x18F70`）

**新增行（全部字段追加在后）**

`[ra2render-telemetry-fogsplit] 总闸按格三态: EnableStarCraftFog=%d | 未探索黑幕绘制次数: %u | 未探索格放行次数: %u | 已探索非直视压暗次数: %u | 小地图已探索非直视减暗驱动次数: %u | 总闸=0 跳过压暗次数: %u | 黑幕边缘帧绘制次数: %u | 已探索直视格放行次数: %u | 小地图未探索格放行次数: %u | 玩法层(与总闸无关): 机动单位剔除 %llu, 建筑剔除 %llu, 弹道剔除 %llu, 渲染单位 %llu | 判据: …`（产物 RVA `0x19050`）

| 符号 | 产物 VA | 自增点（产物 RVA） | 语义 |
|---|---|---|---|
| `s_fogLayerDraws` | `0x102E1A38` | `0x213C` | 半透明层绘制次数（既有，口径不变） |
| `s_fogBlendStubHits` | `0x102E1A3C` | `0x21FD`（B1）/ `0x229D`（B2） | 混色桩介入（既有） |
| `s_radarDarkenDriven` | `0x102E1A40` | `0x4967`（原生档）/ `0x4B76`（自绘档） | 小地图减暗驱动（既有） |
| **`s_shroudBlackDraws`** | `0x102E1A4C` | `0x21D2` | **未探索黑幕绘制次数**（引擎 `0x47EFE0` 只读计数） |
| `s_shroudEdgeDraws` | `0x102E1A50` | `0x21DE` | 黑幕边缘渐变帧绘制次数 |
| `s_fogUnexploredPassed` | `0x102E1A54` | `0x207B` | 未探索格放行次数（主视图） |
| `s_fogVisiblePassed` | `0x102E1A58` | `0x211E` | 已探索直视格放行次数 |
| **`s_exploredFogDarken`** | `0x102E1A5C` | `0x2145` | **已探索非直视压暗次数** |
| `s_gate0DarkenSkipped` | `0x102E1A60` | `0x2112` | 总闸=0 跳过压暗次数 |
| `s_radarUnexploredPassed` | `0x102E1A64` | `0x492A` | 小地图未探索格放行次数 |
| `s_pDrawShroudFogTrampoline` | `0x102E1A68` | —（`jmp dword ptr [imm]` @ `0x21E4`） | 黑幕层计数桩跳板 |
| `g_enableUnitFog` | `0x1002100F` | — | 机动单位剔除门控（三处 cmp：`0x1950`/`0x2330`/`0x2608`） |
| `g_enableStarCraftFog` | `0x1002100B` | — | 总闸（绘制路径唯一判定 @ `0x2105`） |
| `s_fogMasterGate` | `0x1002101A` | — | 汇编侧镜像（B1/B2/H2/H3 桩） |
| `g_fadeFogTransition` | `0x10021018` | — | 4 帧渐变 |
| `g_enableBuildingFog` / `g_enableBulletFog` | `0x1002100D` / `0x1002100E` | — | 逻辑可见性键 |
| `s_fogBlendStrength` | `0x10021024` | — | 混色强度 |

---

（报告完）




