# W39 · UNKNOWNS（未覆盖 / 不确定项）

> 与 `LIVE_RESULT.md` 同目录。分级口径见 `LIVE_RESULT.md §1`。
> 本卡主结论「散装 `MAPSELMD.INI` 登记后 A1→A2 能推进」**已实测成立且被负对照因果锁定**；以下是不改变该结论的边界与未解项。

---

## U1 · 追加战役 `RA2F1` 自身菜单仍不可选 ⇒ 链路未整体贯通 `[转引]`/`[待运行验证]`

- 本卡入口是 **W27 D2 诊断变体**（劫持官方 `BATTLEMD.INI` 的 `[SOV1] Scenario` → `ECH01.MAP`，从苏联徽章进入）。
- W27 Q1 实测 `GUI:CampaignMenu` 只有盟军/苏联两个固定侧别徽章，追加 battle id 不生成第三 UI 条目（`CAMPAIGN_LIVE.md §3`）；D1 证伪「CSF 文本缺失」为根因。
- ⇒ **「追加式 DLC 包从自己的菜单条目进入 → 打通 A1→A2 → EndOfGame」仍未验证**。本卡未测、未改变该事实。

## U2 · 4 条失败分支未能收窄（卡面期望未达成）`[本次实测]`/`[待运行验证]`

- 两个错误趟（负对照 `control_official`、`skip_yes`）的 `memory_search` 都同时命中
  `Invalid side` / `Unable to initialize choices` / `Invalid stage` / `Unable to create font` 各 `ascii=1`
  ⇒ 这些是 **exe 静态字符串**，非运行时分支标志；**只读 RPM 字符串检索无法判别实际走了哪条分支**。
- 要区分需断点/符号级跟踪（在 `0x005ADD10`/`0x005AE100`/`0x005AE220`/`0x005ADF20`/`0x005CF760`/`0x005CF6B0` 附近），本卡纪律**禁止注入/attach 写内存/改 exe**，故未做。
- `SkipMapSelect=yes` 与 `no` 的**可见结果相同**（同一 `MSG:UnableMapSelect` 对话框，截图 SHA 完全相同），只有内部状态差（`scen_filename=""` vs 冻结 `ECH01.MAP`）。
- ⇒ 卡面「区分实验把 4 条失败分支进一步收窄」**本卡未达成**；如需，须另立静态逆向/调试器授权卡。

## U3 · 成功路径里未抓到「追加阶段名驻留内存」的直接瞬间 `[本次实测]`/`[静态推断]`

- `w39_skip_no` 的 `A1_ingame` 与 `post_continue_A2` 两次 `memory_search` 中，`RA2F_ECH01|ascii=0`、`RA2F_ECH02|ascii=0`。
- 对照：`w39_skip_yes` 的 `post_continue_error` 搜索中 `RA2F_ECH01|ascii=2`、`RA2F_ECH02|ascii=3`（追加阶段名确实在进程内存里）→ 证明**散装 `MAPSELMD.INI` 内容确被引擎读入**。
- 合理解释 `[静态推断]`：成功路径在 `A2_confirmed` 采样时 INI 解析缓冲区已释放/复用；本卡未在「Continue 点击瞬间」做定拍 RPM 快照。
- ⇒ 成功路径中「引擎确实解析了追加段」的**直接内存证据缺失**，因果归因主要靠 §5 的单变量负对照 + `scen_filename=ECH02.MAP` + A2 局内 4 项硬指标。这是证据强度的说明，不是对结论的否定。

## U4 · `scen_stage_idx=8` 的语义未定 `[本次实测]`/`[静态推断]`

- A2 加载后 `[Scen+0x35A0]` 2 字节读数由 `0` 变 `8`；追加行在 `[Nod]` 下用 `8=`/`9=` 连续整数键，数值相容。
- 该偏移的「当前阶段」语义来自既有反汇编 `[转引]`，**非符号级证明**；也可能是 battle 表索引、颜色索引等。本卡不据此宣称「引擎选中了第 8 阶段」。

## U5 · A2 之后未测 `[待运行验证]`

- `ECH02.MAP` 的 `EndOfGame=yes`、`NextScenario=` 空。本卡只验到「进入 A2 局内」，**未**验证 A2 判胜后是否正确结束战役、是否回主菜单、是否写进度。
- A2 的 `survive(1800)` 目标需 30 min 自然判胜，超出本卡 8 min/趟预算 ⇒ 未做。

## U6 · 未覆盖的配置/载体维度 `[待运行验证]`

- 单一分辨率/单一 ddraw 后端（1366×768 全屏、`direct3d9` 配置，窗口 rect `[0,0,1707,960]` 为缩放后桌面），未测其它分辨率、renderer、汉化版本。
- 单一难度（`GUI:Harder` 默认），未测其它难度。
- 单一 2 关包，未测 >2 关、`AltNextScenario`、多包并存、跨包升级后推进。
- 未测 `SkipMapSelect=no` 下的**交互式 MapSelect 屏幕**：本卡成功路径在 Continue 后**直接**进入 A2，没有出现需要点击的选关画面（脚本 `--mapsel-click` 未使用、也无需使用）。因此 `ClickMap=NODCLK01.PCX` + 颜色 `2` 的可点区域视觉表现**仍未验证**（W35 已标为 `[待运行验证]`，本卡未推进）。
- 未测 `Description=791` / `VoiceOver` / `MapVQ` / `Overlays` / `Targets` 等克隆字段是否影响交互屏；成功路径不经过这些资源。

## U7 · 读取地址语义的既有边界 `[转引]`

- `[0xA8ED84]` 是 32 ms 定拍逻辑计时器（≈31.25 计数/s），**不是 FPS**；不能据此说「画面不卡」（渲染侧需注入/调试器，本会话禁止）。
- `mode[0xA8B238]` 只能区分 intro/主菜单(0) 与其余(5)，**不能**区分加载/局内（HANDOFF §2 的已更正结论）。本卡未用 `mode` 做进图判据，用的是 `scen_filename` + frame 递增 + 控件文本 + 截图。

## U8 · 桌面差异的根因未查 `[本次实测]`/`[待运行验证]`

- 已实测：W35 执行环境 = `WinSta0\exebox-ZO5YEXSDBF5D74L4BR7PIY34ZX`（0 窗口、ImageGrab 失败），本卡 = `WinSta0\Default`（377–383 窗口、ImageGrab OK）。
- **未**查两个执行环境为何被分配到不同桌面（沙箱/会话/窗口站策略）；本卡只记录现象并用于定位，不做归因。

## U9 · 工具缺陷复现条件 `[本次实测]`

- 首趟 `w39_skip_no` 因 `Sink.step` 的 console `print` 在 GBK 编码下遇到 latin-1 内存上下文 `\xde` 而中止（已归档 `w39_skip_no.run1_toolcrash.ndjson`）。
- 已修（`ensure_ascii=True` + 防御式 try/except + `PYTHONIOENCODING=utf-8`），三趟正式运行均未复现。若他人在非 UTF-8 控制台复跑且不带该环境变量，仍可能踩到——驱动已做防御，但建议保留环境变量。
