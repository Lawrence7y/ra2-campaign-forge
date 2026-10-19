# ZCode 真机（游戏内）验收任务卡 · ZC-1
# Live Acceptance Task Card for ZCode

> 状态：**待派发**（Lead 已备好，等时机合适交 ZCode）。
> 依据：`docs/re/AGENT_TASK_TEMPLATE.md` 模板 + `docs/re/AGENT_DELIVERY_FORMAT.md` 回报格式 + `docs/re/execution_runbook.md` 执行剧本。
>
> **【勘误 2026-09-29 · MIMO-BENCHPRIS】** 本卡正文不含色彩类硬门槛。若引用 `docs/re/v160_acceptance.md` 的截图判据，注意其原文「唯一颜色数 $\ge 20,000$ 种」**在本渲染路径不可达**（ZC-9B 实测 978–1756 色）；**建议口径为「≥800 色，且与既有已验收证据同量级」**。性能门槛 `valid_pct ≥ 10%` / `帧推进 ≥ 3 fps` / `CRC ≥ 500 帧` 均可达，不受影响。详见 `out/re_work/mimo_benchpris/audit/threshold_census.md`。

---

```text
【任务卡 ZC-1】真机（游戏内）验收：联机门控 + v1.6.0 四项功能 + 稳定性回归

◆ 执行方：ZCode      ◆ 期望耗时：60-90 分钟（含 3 局对局）
◆ 工作区：D:\Project\ra2-campaign-forge（Windows），游戏目录 ra2youli\
◆ 基线二进制：ra2youli\gamemd.exe（MD5 4f37486e5b0dbe2ae5f45aeee0f98367）【只读】
◆ 当前注入模块：ra2youli\ra2render.dll（SHA256 前缀 e7fa669c85b5da53c71898dc，129,536 B，2026-09-27 09:07 构建）
◆ 启动方式：ra2youli\ra2loader.exe（挂起启动 gamemd.exe 并注入 DLL）

◆ 写作用域
  允许写：out/re_work/zcode_live/**（证据包：截图、日志切片、判据表）
  允许改：ra2youli\ra2render.ini（**仅**用于步骤 2 的反例验证，验证后必须还原；改动前后各存一份副本进证据包）
  禁止写：ra2render\**、gamemd.exe、任何 .mix/.map、其他 docs、台账

◆ 绝对禁止：伪造证据（截图必须唯一 MD5、须有真实进程留痕）、把“没崩”当作“功能成立”的证据

◆ 必答项（逐条给判据与证据）

  Q1【SP 门控基线，Lead 已跑过一次，请独立复核】启动单机，读 ra2youli\ra2render.log 尾部的门控行。
     期望：门控: MpActive=false, TargetScanKey=配置(position)->生效(position),
           TargetScanInterval=配置(8)->生效(8), EnableMinimapFog=配置(0)->生效(0)
     ⇒ 单机下生效值必须等于配置值（不得误覆盖）。Lead 实测已通过（PID 36408，见台账 [v1.6.8]）。

  Q2【联机门控，本卡核心】进入**真实网络会话**（LAN/互联网对局）后读门控行。
     ⚠️【前提勘误 2026-09-27 · ZCode 实测】原文写「联机/遭遇战（使 MpActive=true）」**不成立**：遭遇战**不置位** MP 会话位（实测 `[0xA8D5F8]=0x00`、`[0xAA0444]=0`，而局内帧在推进）；构造真实网络会话需 **≥2 名玩家**（引擎明示），本机双开受单实例限制。⇒ 本项**只能在双机 LAN 环境下验证**，无法构造时必须如实标注「未验证」。
     期望：MpActive=true 且 生效(TargetScanInterval)=1、生效(TargetScanKey)=position、生效(EnableMinimapFog)=0。
     反例验证：把 pointer 写进 `ra2render.ini` 的**第一个 `[Logic]` 节**（注意：该 ini 曾有两个同名节，第二节为死配置）后重进联机，
     期望日志出现【警告/红字】并强制纠正为 position；单机下则允许 pointer 生效。验证完还原 ini 并贴 sha256 对照。

  Q3【v1.6.0 四项功能游戏内表现】按 execution_runbook.md 的判据逐项记录（每项：期望现象 / 实际现象 / 截图路径）
     ① 小地图灰化 + 敌点隐匿（静止画面即时刷新）  ② 建筑三态（雾中初始隐形、侦察后常驻）
     ③ 弹道剔除（雾中敌方开火不可见弹道）        ④ 灰雾 4 帧渐变（无闪烁/错位）
     注：`EnableMinimapFog` 现默认 0 ⇒ ③④ 之外的 ① 需在 ini 中显式置 1 才启用（这是 G-01 的既定决策）。

  Q4【路线 A 雷达回归】确认历史崩溃 `EIP 0x5450202F` 不再出现（对局中反复开合小地图/雷达）。

  Q5【稳定性回归】连续 3 局（含至少 1 局高负载：U200/U800 级），要求：
     ① 无新增崩溃（无 0xC0000005 / 0xC0000374）  ② 遥测末行非零  ③ 日志无新异常串
     并记录每局的 平均帧 / CPU0 占用（可用 tools/bench_*.py 或任务管理器采样）。

  Q6【帧 CRC 对拍（若可联机）】双端逐帧 CRC 至少 500 帧（混联场景 ≥300 帧）无 `TXT_OUT_OF_SYNC`；
     若两端构建不一致（对方原版无 DLL），须整局不加载 ra2render.dll 再对拍。

◆ 失败判据（出现任一即判该子项 FAIL，须原样回报，不得掩盖）
  - 单机下生效值 ≠ 配置值；或联机下未强制为 1 / position / 0；或 pointer 反例未告警
  - 四项功能任一项现象与期望不符（含“无变化”“看不到”“反而更差”）
  - 出现任何崩溃、卡死、黑屏、desync
  - 遥测计数为 0（说明钩子没生效，属“装了但没干活”）

◆ 交付物
  1) out/re_work/zcode_live/evidence/**：每项的截图（唯一 MD5）+ 对应日志切片（注明 offset）
  2) out/re_work/zcode_live/RESULT.md：Q1-Q6 判据表（期望/实际/判定/证据路径）
  3) out/re_work/zcode_live/claims.txt（可选）：把关键日志行抽成断言
  4) ini 改前/改后副本（Q2 反例验证用）

◆ 自证门禁（必须实跑并贴原文）
  python tools\verify_anchors.py   → 须 323/323 PASS（证明你未破坏基线资产）

◆ 回报格式：严格按 docs/re/AGENT_DELIVERY_FORMAT.md 的 10 节骨架；缺节=不合格。
  ⚠️ 特别提醒：[5] 作用域合规 必须声明 ini 是否已还原；[7] 风险红线 必须回答是否触发过 desync。
```

---

## Lead 侧备注
1. **本卡不含任何需要写代码的活**；若验收发现需修复，另开任务卡（ra2render 单写者规则）。
2. 若 Q2 无法构造：可用“单机 + 手动置 iní 为 pointer”先验证告警逻辑，再标注联机强制路径**未验证**，不要猜。
3. 验收通过后由 Lead 登记 `[v1.6.9]` 并解除 `[v1.6.0]` 的真机验收闸门；未通过则按 `execution_runbook.md` 第五章三套灾难预案处理。

---

## 附：Q1 harness 已就位（2026-09-27 更新，执行前必读）

> 本卡的对局内性能采数**不再靠手写判断**。基准 harness 已由 Q1H-R3 收口（DSH），口径唯一、且**「没数据不得判达标」已机器化**。

**工具与文件**
- `tools/bench_replay.py` —— 真机采样（探针 10 ms×30 轮、零命中**抛错拒绝采样**；`sample_window(require_match=True)` 采样前帧推进 <3 fps 直接拒绝；A/B 联动 `--ab-simd` 改 ini 后**逐字节 sha256 校验还原**、键不唯一拒绝盲改）
- `tools/bench_metrics.py` —— **唯一合法判定器**（7 项指标：平均帧 / 1% low / 单核 CPU / TickMiss / 有效样本数 / 归因覆盖率 / 采样覆盖率，每项带计算式 + 门禁 + 判定）
- `tools/bench_filter.py` —— 噪声过滤（idle、`AcGenral`/`acspecfc`/`acwinrt`/`apphelp`、`wow64*`、`msctf`、`ntdll`、`USER32`…；`binkw32`→video 单列；`ddraw` 单列且**禁止断言全为等待**）
- `tools/bench_diff.py` —— 像素对拍（阈值参数化、ROI 遮罩按 800×600 定义并随分辨率等比缩放且留痕、**新增对齐前置条件**）
- `out/loadbench/PROTOCOL.md` **v2.1**（§10 离线自检门禁 / §11 离线-真机边界与人工参与清单 / §12 **防误用条款**）
- `out/loadbench/report_20260927_r3.md` **§7.3** —— 实机步骤 **S0–S9**（启动什么、采样 3 局 × 20 s、看哪些字段、U200/U800 阈值表）

**性能是否达标的唯一合法形态（缺一不可）**
1. `valid_pct ≥ 10%`（有效样本占比，排除菜单/加载期）；
2. 通过**对局内校验**（采样窗口内帧推进 ≥3 fps）；
3. 含**帧序列**与 **CPU 首尾差分**；
4. `python tools/bench_metrics.py --run <json>` 判 **`overall = PASS`**。

**明确禁止的引用方式（PROTOCOL §12）**
- 旧 JSON（`perf_U0800.json`/`perf-profile.json`）→ 分别只会判 **PARTIAL / INVALID_SAMPLE**，不得当收益证据；
- 「区间表命中率 **99.69%**」不得单独引用（**锚点支撑占比仅 66.26%**，须并列）；
- 未对齐截图的 diff%（同场景未对齐可达 **18.75% 假回归**）；
- 菜单/中断期采样；
- 合成自检产物（已标【非证据】）。

**当前闸门状态**：Q1 基础设施 ✅ **已就位**；渲染/迷雾补丁仍**锁闭**，解锁所需的最后一项是**本卡的真机数值 + ZCode 执行结论**。
