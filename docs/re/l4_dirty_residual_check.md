# L4DirtyMode 残留复核（R-L4-RESID）

[META]
task=R-L4-RESID  scope=ra2render/**(只读)  baseline=blitter_hooks.cpp (2026-09-30 15:04)
可写域=out/re_work/re_sprint/R_l4_resid/**, docs/re/l4_dirty_residual_check.md

---

## [1] 现状复核（三问）

| 项 | 结论 | 证据锚点 |
|---|---|---|
| 门控是否已解耦 | **已解耦（扫描侧）** | `blitter_hooks.cpp:1638-1667` 逐格迁移/ramp 扫描**无条件**运行；仅小地图强制刷新副作用仍按原门控 `1676`（`g_fadeFogTransition \|\| GetEffectiveMinimapFog()`），注释明示为保 force-full 默认档与现网件逐位等价 |
| 联检 transition/ramp | **已联检** | `blitter_hooks.cpp:2447-2450` 先 `s_fogViewportTransitionCount==0` 再 `s_fogViewportRampActive==0`，任一非零 ⇒ `l4_force_full`。符合 L4-DIRTY-SAFETY §0.3「防渐变中途误切原生分支」 |
| 遥测三键是否齐 | **齐（格式/字段全）** | `blitter_hooks.cpp:847-850` 输出 `l4RedrawSkippedStatic` / `l4DirtyTransitions` / `l4DirtyRampActive` + 本帧 `视口迁移` / `视口渐变活跃`；三档机判注释 `843-845`；ra2bench 日志 `ra2render-telemetry-l4dirty` 实跑可见 |

L4DirtyMode 三档（ZC-10B 落地确认）：解析 `718-732`，ini 键 `ra2render.ini:202-212`，默认 `force-full`，非法值收敛为 `force-full`。运行期判定在 `Hook_L4FullRedraw_Stub`（`2438-2470`）。

**门控解耦本身无残留问题**；真正挡住 vision-dirty 开档的是下面 [2] 的 flags 纪律缺陷。

---

## [2] vision-dirty 最小侵入残留清单（还缺什么才能开）

### P0-1 ★阻断★ stub 未保护 0x6D3D97 的原始 flags
- **现状**：`Hook_L4FullRedraw_Stub`（`2438-2470`）**无 `pushfd`/`popfd`**（全文件仅有注释 `2425/2428` 提到该纪律）。桩入口本应承接 `0x006D3D97 cmp` 的 flags，却被 `cmp [g_l4DirtyMode]`、`cmp [s_fogViewport*]`、`inc [s_l4RedrawSkippedStatic]` 层层覆盖。
- **后果 A（vanilla 恒全刷）**：`2460-2463` `cmp [g_l4DirtyMode],2` 相等时 SF=OF=0，随后 `jge l4_take_full` **恒真** ⇒ vanilla 实际≡force-full，与 `54` 行「等价于不打本补丁」定义相反；`2464` 落点 `0x006D3D9F` 是死代码。
- **后果 B（vision-dirty 静态时也恒全刷）**：`2452 inc` 后 `2453 jge` 测的是 inc 的 SF/OF（正数恒真）⇒ 静态视口仍走 `l4_take_full`；同时 `s_l4RedrawSkippedStatic` **虚增**（计了却没跳过）。E5 机判「`l4RedrawSkippedStatic>0` 且同帧像素差≡0」永远无法同时成立。
- **修法**（见补丁清单 ZC-P1）：桩入口 `pushfd`，判定原版 jge 前 `popfd`，把原版 `jge` 语义建立在被还原的 flags 上。

### P0-2 ★红线未跑★ E5 静态镜头同帧像素对拍
- L4-DIRTY-SAFETY §7 红线：P0-2 上线前必做。当前只有纸面判据（E5 行，`[推演]`），无实跑证据。
- 判据：`L4DirtyMode=0` 与 `=1` 静态镜头同帧像素差 D≡0，且 `l4RedrawSkippedStatic>0`，且对象运动无旧位残影。

### P1-1 机判与实现不一致
- `845` 称「vanilla ⇒ l4RedrawSkippedStatic 恒 >0」，但 vanilla 分支（`2459-2465`）**不 inc** 该计数。要么实现补 inc，要么机判改为「vanilla 不计此键 / 另立键」。开档前必须二选一统一。

### P2-1 视口窗口 1 帧滞后（可接受，需书面锁定）
- `60` 行注释 + `1672-1674`：`s_viewCell*` 在扫描末复位，下一帧才收齐本逻辑帧后续格子的绘制窗口。边界格可能被误判「视口外」⇒ `vpTransition` 漏计。方向是**多刷/保守**（漏计⇒更易 force-full），不致漏画；但若误计为 0 而实际有迁移，会误放行 jge。建议：窗口并入**上一帧 ∪ 本帧**或整体外扩 1 格（补丁清单 ZC-P3）。

### P2-2 最小侵入范围外（勿在本卡做）
- 最终 spec 的「视野翻转格 3×3 外扩 + >350 格全屏保底」局部打脏（`l4_vision_dirty_final_spec.md`）**未实现**；当前 ZC-10B 只做 jge 全量/交还二分。最小侵入开档**不需要**它，但 TC-L4-01 若走 vanilla 会缺保护（见 [3]）。

---

## [3] vanilla 档与 v1.5.0 即时性相容性 / 漏画风险（对照 E1–E5）

| # | 结论 | 依据 |
|---|---|---|
| E1 | dirty 打标链路完备（`0x6DA7D0` 开雾 25 调用；帧末清零 `0x6D4571`/`0x6D4B37`） | 静态实证，继承 L4-DIRTY-SAFETY |
| E2 | 单位机动**必然**打脏（`0x4DF639→0x5F4EC0→0x5F5146→0x6D2790`） | 静态无迁移时 jge 路径不漏画运动残影 |
| E3 | 动画/粒子/炮弹/建筑/桥梁均自打脏 | 同上 |
| E4 | v1.5.0 无条件全刷**仅**为掩盖「迷雾/黑幕退回是逐格底层状态、无对象标脏」 | 这是 vanilla 档唯一真实漏画洞 |
| E5 | 未实跑 | 开档红线 |

**vision-dirty 相容性**：**相容**。它用 `视口迁移==0 && 渐变活跃==0` 把 E4 的洞挡在门内——有迷雾退回（迁移>0）时仍强制全量，无迁移时 E2/E3 覆盖动态要素。故静止视角雾退回 0 帧延迟（TC-L4-01）在 vision-dirty 下由「迁移触发全刷」保证。

**vanilla 档相容性**：**不相容于 v1.5.0 即时性**。vanilla 恒还原原版 jge ⇒ 静止镜头 + 迷雾退回时，退回格不进脏表（E4）也不进全刷 ⇒ **漏画 / 灰雾滞后**，直接违反 TC-L4-01（0 帧延迟）与 L4 视觉铁律。vanilla 仅适用于「接受灰雾即时性下降」或另有退回打脏机制的场景；**不得作为 v1.5.0 等价档放行**。

**漏画风险排序**（开档视角）：
1. flags 未修 ⇒ 三档判定全部失真（最高，表现为「切了档但行为不变/全变」）。
2. vanilla 档在静态镜头 + 迷雾退回 ⇒ 真实漏画（若误把 vanilla 当 safe 默认）。
3. 视口窗口滞后 ⇒ 误放行 jge 的低概率边界漏画（P2-1）。
4. E5 未跑 ⇒ 上述 2/3 无像素级兜底证据。

---

## [4] 给 ZCode 的补丁清单（非本任务实施）

见 `out/re_work/re_sprint/R_l4_resid/zcode_patch_list.md`。摘要：

| ID | 位置 | 动作 | 开档门槛 |
|---|---|---|---|
| ZC-P1 | `blitter_hooks.cpp:2438-2470` | 补 `pushfd`/`popfd`，原版 jge 必须在**还原后 flags** 上判定 | **必须** |
| ZC-P2 | `2451-2455` / `2459-2465` + `845` | 统一 `s_l4RedrawSkippedStatic` 语义与机判 | **必须** |
| ZC-P3 | `1645-1674` | 视口窗外扩 1 格或双帧并集 | 建议 |
| ZC-P4 | 验收 | 跑 E5 像素对拍 + TC-L4-01 | **必须（红线）** |
| ZC-P5 | 文档/机判 | 明示 vanilla 不满足 v1.5.0 即时性，禁止作 safe 默认 | **必须** |

---

## [5] 写作域合规
- 触碰：`docs/re/l4_dirty_residual_check.md`（本文件）、`out/re_work/re_sprint/R_l4_resid/**`
- 未触碰：`ra2render/**`、`gamemd.exe`、`ra2youli/**`、`tools/**`、台账、看板、ATLAS
