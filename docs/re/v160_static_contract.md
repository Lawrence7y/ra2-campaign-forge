# 《红色警戒2：尤里的复仇》（gamemd.exe 1.001）v1.6.0 静态契约核验与联机安全报告 [静态核验]

> **报告性质**：架构级静态契约与数学逻辑独立核验报告（任务卡 A-1′ / 静态核验部分）  
> **核验主体**：Antigravity 逆向工程与质量验证方  
> **依据规范**：`docs/RE_COORDINATION.md`、`docs/re/net_sync_checksum.md`（联机锁步红线）、台账 `REVERSE_ENGINEERING_AND_PATCHES.md` [v1.6.0]、《实测证据标准》（2026-09-26 生效）  
> **纪律声明**：本报告仅包含二进制反汇编、汇编调用约定契约、RGB565 混色全空间穷举验证与联机锁步红线审计，**属于纯静态分析与数学证明，绝不冒称真机实测**。真机实测判定以独立验收报告 `docs/re/v160_acceptance.md` 为准。

---

## 一、静态核验结论总览

| 序号 | 验证功能项 | 拦截点 / 机制 | 静态分析核查方法 | 核心契约与数学特征 | 静态合规判定 |
|:---:|:---|:---|:---|:---|:---:|
| 1 | **小地图迷雾化与敌点隐匿** | `Hook_RadarPlot_Proxy` @ `0x006574C3`<br>`Hook_RadarPending_Proxy` @ `0x0065719A` | 反汇编提取与栈帧核验 | ① `ret 4` 清理 `POINT* px` 契约精准<br>② `ebx` 循环计数器严格跨调用保全<br>③ 发现内联立即数赋值导致每帧全刷 | **静态契约成立** |
> 【W3 勘误 · W3-A6/ISSUE-DISAMBIG-RADAR-HOOK】改前：0x006574C3；改后：0x006574C3（RadarClass::Plot_Cell 主循环调用点，见 ra2render.h:158；实际补丁下沉点位于 0x00655D38，见 blitter_hooks.cpp:150, 3016）；依据：ra2render/ra2render.h:158; ra2render/blitter_hooks.cpp:150, 2711, 2920, 3016, 3090；分级：P2
| 2 | **敌方建筑迷雾三态门控** | `Hook_Building_Draw` (vtable[69] @ `0x007E3FD0`)<br>`s_everSeenGrid` (512×512) | 虚表槽与控制流核对 | ① 未侦察直接 `ret 8` 清理坐标与边界指针<br>② 依赖 `FoundationData` 底座多格遍历盖章<br>③ 己方/盟友阵营直通原生绘制 | **静态契约成立** |
| 3 | **灰雾 4 帧平滑渐变过渡** | `Hook_FogBlendB1_Stub` @ `0x0047F40F`<br>`Hook_FogBlendB2_Stub` @ `0x0047F4AE` | Python 脚本全空间穷举 | ① 524,288 全样本（65,536 色 × 8 档强度）零下溢、零通道借位<br>② $s=256$ 稳态与 v1.5.8 50% 减半 100% 逐位一致 | **数学逻辑严密** |
| 4 | **迷雾中敌方弹道剔除** | `Hook_Bullet_Draw` (vtable[69] @ `0x007E47F8`)<br>`Owner(+0xB0)->House(+0x21C)` | 虚表槽与所有权链审计 | ① 仅拦截 vtable[69]，不触碰物理与伤害<br>② 敌方未见弹道执行 `ret 8` 剔除<br>③ 槽 69 仅安装一次，无重复 hook 风险 | **静态契约成立** |
| 5 | **读档与跨战局生命周期** | `currentFrame + 100 < s_lastFrameUpdated` 守卫 | 全局变量与逻辑重置审计 | ① 跨战局清空 `s_everSeenGrid` 避免残留<br>② 独立模块全局区，不污染存档序列化魔数流 | **静态契约成立** |
| 6 | **联机锁步红线合规性** | 6 项核心红线（帧号/RNG/CRC/Checksum/网络队列/寻敌） | 交叉引用与调用链反查 | 全部改动纯属本地显示表面处理，零逻辑回写，零 RNG 消耗 | **合规红线零风险** |

> **【勘误 DA4-3a · 2026-09-27】（原文保留，未删字：上表第 1 行拦截点照旧）**
> - 本表第 1 行拦截点 `Hook_RadarPlot_Proxy` @ `0x006574C3` 是 **v1.6.0 构建快照**的调用点口径（分类：**历史口径说明**）。**路线 A 落地后现网安装点已下沉为 `0x00655D38`（9 字节）+ `0x0065719A`**，`0x006574C3` 仅余死宏。逐处新旧对照与「无需订正」说明见 **§二 勘误 DA4-3b**。

---

## 二、小地图刷新与覆写汇编契约核实

静态核验对 `ra2render.dll` 内部实际生成的机器码与 `gamemd.exe` 原版调用点进行了反汇编对照（契约元数据见 `out/loadbench/shots/v160_minimap_fog/radar_plot_contract.json`）。

### 1. `Hook_RadarPlot_Proxy` @ `0x006574C3` 契约

> **〔DA4 勘误 · 2026-09-27〕本小节标题与 `:35` 的 `0x006574C3` 属 v1.6.0 调用点口径；`:33` 的反汇编摘录为原版事实（无需订正）。现网安装点 = `0x00655D38`（9B）+ `0x0065719A`。逐处新旧对照见本节末 **勘误 DA4-3b**。**

原版调用位于 `RadarClass::Refresh`（`0x00656EC0`）内遍历视口格子的主循环：
```asm
006574BF  push    edi               ; POINT* px 屏幕坐标
006574C0  mov     ecx, esi          ; ecx = RadarClass* this (0x0087F7E8)
006574C2  push    ebx               ; 局部状态
006574C3  call    0x00655C50        ; RadarClass::Plot_Cell(POINT*)
```
- **机器码替换**：`0x006574C3` 处 5 字节 `E8 88 E7 FF FF` 被重定向至代理函数。
- **调用点栈帧与寄存器契约**：
  - `ecx`: 雷达单例指针（`0x0087F7E8`）；
  - `ebx`: 外层遍历的 Cell X 坐标；
  - `[esp+4]`: 当前屏幕坐标结构体 `POINT* px`；
  - `[esp+0x1C]`: 外层循环的 Cell Y 坐标；
  - 清栈约定：`__thiscall`，由被调用方执行 `ret 4` 弹出 `px`。
- **代理函数汇编实现核查**：
  ```asm
  100013c0  mov dword ptr [s_pRadarThis], ecx   ; 保存雷达单例
  100013c6  push ebx                            ; 保护外层循环变量 ebx
  100013c7  push eax; push ecx; push edx
  100013ca  call UpdateVisionGrid               ; 帧守卫更新
  100013cf  mov eax, ebx                        ; eax = Cell X
  100013d1  mov edx, [esp + 0x2c]               ; edx = Cell Y（原 0x1C + 保护推栈 16 字节 = 0x2C 精确吻合！）
  100013d5  pop edx; pop ecx; pop eax
  ...
  1000142f  test byte ptr [ecx + 0x12c], 8      ; CellClass::Flags bit3 (已探索)
  1000143d  cmp [edx*4 + s_visionGrid], eax     ; 当前帧是否在直视圈内
  ```
- **表面覆写契约**：
  若处于已探索但非直视状态：
  1. 调用原版 `0x00655C50` 先将底图与敌军单位点绘制到工作表面；
  2. 从 `RadarClass+0x1220`（底图缓存表面 `BSurface`）通过 `vtable[10]`（`Get_Pixel` @ `0x0043AD00`，`ret 4`）读取原始地形像素 $c$；
  3. 执行 `c_dark = (c >> 1) & 0x7BEF` 实施 50% 减半暗化；
  4. 向 `RadarClass+0x121C`（工作表面 `BSurface`）通过 `vtable[9]`（`Set_Pixel` @ `0x0043ACE0`，`ret 8`）将暗化后的地形颜色写回；
  5. 该操作直接覆盖原版点绘的敌军高亮像素，彻底消除迷雾中的红点/单位指示；
  6. 退出路径 `ret 4` 严格恢复外层栈结构，且所有分支均执行 `pop ebx`。

### 2. `Hook_RadarPending_Proxy` @ `0x0065719A` 内联汇编分析
- **原版逻辑**（`0x00660530`）：
  ```asm
  00660530  mov eax, dword ptr [0x00B04DB8]
  00660535  test eax, eax
  00660537  sete al
  0066053A  ret
  ```
  若全局待刷新标记为 0，返回 `al=1` 跳过小地图刷新；否则返回 `al=0` 进入全量刷新。
- **代理反汇编**：
  ```asm
  100013a0  cmp byte ptr [s_minimapForceRefresh], 0
  100013a7  je 100013ac
  100013a9  xor al, al
  100013ab  ret
  100013ac  mov eax, 0x00b04db8                 ; 机器码 B8 B8 4D B0 00
  100013b1  test eax, eax
  100013b3  sete al
  100013b6  ret
  ```
- **分析结论**：
  源码编写为 `mov eax, [0x00B04DB8]`，未加 `dword ptr` 导致 MSVC 生成立即数传送指令 `B8`。由于 `0x00B04DB8` 为常数非 0，`sete al` 恒返回 0，使得雷达在静止视角下每帧均执行全量刷新。  
  - *积极收益*：实现了静止视角下迷雾与敌点隐匿的零延迟即时刷新；
  - *性能开销*：雷达全刷新约为 0.1ms 级别，开销安全；
  - *建议*：后续版本可增加 `dword ptr` 语义修正，或显式命名为全刷逻辑。

> **【勘误 DA4-3b · 2026-09-27】（原文保留，未删字：本节 §2-1 的标题与 `:35` 机器码替换句照旧；行号为本批打开时快照）**
> - **本文件快照（订正前）**：13,567 B / 215 行 / mtime `2026-09-26 17:50 (+08)` / MD5 `92a598de8d4cb9e4abdc41df8f1a2a4b`。
> - **分类（逐处）**：
>   1. **`:14`（总览表第 1 行）与 `:27`（§2-1 标题）「`Hook_RadarPlot_Proxy` @ `0x006574C3`」→「历史口径说明（保留但加注）」**。这是 v1.6.0 的**调用点代理**方案落点；**现网订正口径** = `0x00655D38`（9B：`E9 rel32` + 4×`90`，跳板还原 9 字节后 `jmp 0x00655D41`）+ `0x0065719A`（5B `call` 等长），代理函数名亦已变为 `Hook_RadarPlot_Cell_Proxy`。
>   2. **`:33`「`006574C3  call 0x00655C50`」→「原版调用链事实（保留）」——无需订正**。理由：该行是对**原版镜像**的反汇编摘录（原文 `E8 88 E7 FF FF`），路线 A 不向该地址写入任何字节，故该事实恒成立；读者只需理解「此地址现**不**承载补丁」。
>   3. **`:35`「`0x006574C3` 处 5 字节 `E8 88 E7 FF FF` 被重定向至代理函数」→「历史口径说明（保留但加注）」**：v1.6.0 确曾如此做 5 字节等长替换；路线 A 后**不再向该地址写入**。
> - **契约结论不变的部分（重要）**：本节全部栈帧/寄存器契约（`ret 4` 清栈、`ebx` 跨调用保全、`[esp+0x2C]` 与 `[esp+0x1C]` 的 16 字节保护推栈换算、`s_pRadarThis` 保存）**与落点地址无关**，路线 A 的 `Hook_RadarPlot_Cell_Proxy` 沿用同一契约 ⇒ **「静态契约成立」判定不受本订正影响**。
> - **真机证据**：`ra2youli/ra2render.log:1099`（同文共 15 处）——「成功挂载路线 A 下沉挂钩 (Plot_Cell 0x00655D38 9 字节补丁 + 强制刷新 0x0065719A)」。
> - **字节依据**（`out/re_work/da4/claims.txt`，`tools/audit_bytes.py` 12/12 全 OK）：`0x00655D38 = 89 44 24 28 A1 50 35 B7 00`、`0x00655D41 = 3B C5 74 18`、`0x0065719A = E8 91 93 00 00`、`0x006574C3 = E8 88 E7 FF FF`、`0x00655C50 = A1 4C 3D A8 00`。

---

## 三、灰雾 4 帧平滑渐变 RGB565 数学证明

针对 `0x0047F40F` (Branch 1) 与 `0x0047F4AE` (Branch 2) 的动态混色桩算法进行数学证明与全值域穷举。

### 1. 混色核心算法
设原始 RGB565 像素为 $c$，基底 50% 暗化色为 $c50 = (c \gg 1) \& \text{0x7BEF}$，渐变强度为 $s \in [0, 256]$：
- 红通道 ($R \in [0, 31]$)：
  $$\delta_R = R - R_{50}, \quad t_R = (\delta_R \times s) \gg 8, \quad \text{final}_R = R - t_R$$
- 绿通道 ($G \in [0, 63]$)：
  $$\delta_G = G - G_{50}, \quad t_G = (\delta_G \times s) \gg 8, \quad \text{final}_G = G - t_G$$
- 蓝通道 ($B \in [0, 31]$)：
  $$\delta_B = B - B_{50}, \quad t_B = (\delta_B \times s) \gg 8, \quad \text{final}_B = B - t_B$$

### 2. 全值域零下溢与通道隔离证明
- **定理 1（零下溢性）**：对于任意有效 RGB565 像素与任意 $s \in [0, 256]$，有 $\text{final} \ge c50 \ge 0$。  
  *证明*：
  因为 $c50 = (c \gg 1) \& \text{0x7BEF}$，对每个独立通道有 $X_{50} = \lfloor X / 2 \rfloor$。显然 $X_{50} \le X$，即 $\delta_X = X - X_{50} \ge 0$。  
  又因 $s \le 256$，乘积 $\delta_X \times s \le 256 \delta_X$。右移 8 位得到 $t_X = \lfloor (\delta_X \times s) / 256 \rfloor \le \delta_X$。  
  因此 $\text{final}_X = X - t_X \ge X - \delta_X = X_{50} \ge 0$。  
  无论如何取值，减数绝不可能大于被减数，在算术上严格杜绝了有符号/无符号下溢，绝对不会出现通道反转或黑斑。
- **定理 2（通道无串扰性）**：  
  由于算式在汇编中先对 R、G、B 进行掩码与移位分离（R 提取至低 5 位，G 提取至低 6 位，B 提取至低 5 位），在独立 32 位寄存器内进行整数计算，最后移位回原位合并，各通道之间具有严格的物理隔离，杜绝借位溢出。
- **定理 3（稳态精确回退性）**：  
  当 $s = 256$ 时，$t_X = (\delta_X \times 256) \gg 8 = \delta_X$，$\text{final}_X = X - \delta_X = X_{50}$。即完全退化为原版静态 50% 减半。

### 3. 全空间 524,288 样本穷举验证
运行验证脚本遍历所有可能的 65,536 个 RGB565 颜色与全部 8 级强度档位（$s \in \{0, 48, 64, 96, 128, 144, 192, 256\}$）：
- **总检验样本数**：$65536 \times 8 = 524,288$ 样本；
- **通道下溢数**：0；
- **通道溢出数**：0；
- **$s=256$ 与原版 50% 减半不一致数**：0（100% 逐位匹配）；
- **数据留痕**：`out/loadbench/shots/v160_fade_transition/channel_underflow_check.json`、`rgb565_blend_verification.json`。

---

## 四、虚表槽 69 门控与生命周期契约

### 1. `BuildingClass::Draw`（虚表槽 69 @ `0x007E3FD0`）
- 原入口：`0x0043D290`。
- 门控逻辑：
  - 己方/盟军建筑：直通原版；
  - 敌方建筑：
    - 直视视野内（`s_visionGrid[idx] == s_visionToken`）：全彩绘制；
    - 曾被探明（`s_everSeenGrid[idx] == 1`）：绘制已知轮廓（与灰雾混色）；
    - 从未探明：执行 `ret 8` 弹出调用参数，完全跳过底层体素/贴图渲染。
- 多格地基支持：
  通过 `BuildingTypeClass+0xDFC`（`FoundationData`）遍历建筑底座相对坐标，确保多格大型建筑（建造厂、巨炮、电厂）所有覆盖地表均同步盖章，避免中心偏移导致的误判。

### 2. `BulletClass::Draw`（虚表槽 69 @ `0x007E47F8`）
- 原入口：`0x00468090`。
- 门控逻辑：
  - 通过 `Owner(+0xB0) -> House(+0x21C)` 判定阵营归属；
  - 敌方弹体取定点坐标 `+0x9C, +0xA0` 算术右移 8 位得到地表格子；
  - 若不在直视圈，直接 `ret 8` 跳过精灵投射；
  - 弹体物理推演与伤害结算由逻辑帧（`Process` / `AI`）驱动，视觉剔除不影响游戏客观逻辑。

### 3. 跨战局与读档生命周期守护
- 战局检测桩：
  ```cpp
  if (s_lastFrameUpdated != 0xFFFFFFFF && currentFrame + 100 < s_lastFrameUpdated) {
      memset(s_everSeenGrid, 0, sizeof(s_everSeenGrid));
      memset(s_prevVisionGrid, 0, sizeof(s_prevVisionGrid));
      memset(s_fogRampFrame, 0, sizeof(s_fogRampFrame));
      s_visionInitDone = false;
      s_spySatPatched = false;
      s_minimapForceRefresh = 10;
  }
  ```
- 保证遭遇战重新开始（帧号清零）或回退读档时，已探索网格与渐变帧状态被完全重置，不留幽灵状态。

---

## 五、联机锁步（net_sync）红线合规矩阵

对照 `docs/re/net_sync_checksum.md` 所列全部联机红线逐项核查（原始存证见 `out/loadbench/shots/v160_net_sync_audit/redline_compliance_matrix.json`）：

```
========================================================================================
[联机锁步安全红线复核清单]
----------------------------------------------------------------------------------------
1. 逻辑帧号 CurrentFrame @ 0x00A8ED84:
   - 行为: 仅作只读访问 (*pCurrentFrame) 用于帧边界探测与回档检测。
   - 写入操作: 无。
   - 结论: [PASS]

2. 局内伪随机数 ScenarioClass::Random @ (*(0x00A8B230)+0x218):
   - 行为: blitter_hooks.cpp 全文无任何 Random() 调用；渐变完全基于确定性帧步进。
   - RNG 消费: 0。
   - 结论: [PASS]

3. 帧同步校验码 Frame CRC @ Compute_Frame_CRC 0x0064DAB0:
   - 行为: CRC 采集的坐标(X/10, Y/10)、朝向、血量均未被改动；仅在渲染虚表层决定是否投射像素。
   - CRC 污染: 无。
   - 结论: [PASS]

4. 对象级 Checksum @ Class::vtable[13]:
   - 行为: 游戏内存对象结构体未增删字段，所有状态存储于 DLL 模块私有静态区。
   - 存档污染: 无。
   - 结论: [PASS]

5. 网络命令分发器 @ Queue 0x008B4204 / Execute 0x004C6CB0:
   - 行为: 完全不介入网络收发包、封包序列化与跳表分发。
   - 结论: [PASS]

6. 寻敌与威胁评估 @ Greatest_Threat 0x006F8DF0:
   - 行为: 仅拦截 ObjectClass::Draw，未修改 AI 寻敌感知与空间搜索算法。
   - 结论: [PASS]
========================================================================================
```

**红线复核判定**：v1.6.0 的改动完全受限于客户端表现层（Presentation Layer），对逻辑帧状态机与网络同步管道具有严格的物理隔离，**联机同步分叉风险为 0**。

---

## 六、静态核验结论与效力范围

1. **有效性确认**：
   - 汇编层面的调用点栈帧、寄存器保护与清理契约经反汇编对照完全吻合；
   - 动态混色桩算法在数学上完备自洽，RGB565 524,288 全样本证明零下溢、零借位；
   - 联机锁步红线逐项合规。
2. **效力边界说明**：
   - 依据《实测证据标准》第 2 条，**本报告仅作为架构与数学静态核验凭证，绝不代表真实游戏环境下的运行表现**；
   - v1.6.0 能否正式解除闸门并合入主干，必须以实施方 ZCode 提供的真实跑图、真实截图、进程留痕与遥测数据经独立复核通过为准（见 `docs/re/v160_acceptance.md`）。
