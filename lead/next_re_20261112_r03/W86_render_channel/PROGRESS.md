# W86 · 渲染呈现观测通道可行性（离线卡）· 进度
# run_id NEXT_RE_20261112_R03 / card W86_render_channel / 执行: subagent w86-render

[2026-11-14T11:53:21+08:00] 卡目录建立；bin/ 只读复制 gamemd.exe / ddraw.dll / ddraw.ini，哈希与 ra2youli 原件逐一核对一致（gamemd 73201cc0…67476、ddraw 85e0f7d5…03a9、ini c983abad…f9d52）。前人脚本 3 份复制进 scripts\prior 并核 sha256 与源一致。未触碰 ra2youli 任何文件。

[2026-11-14T11:53~11:56] 阶段0·前人工作通读：LEAD_VERDICT_Aline_FINAL.md（§5 渲染侧未测、需注入）、LEAD_FINDING_counter_is_32ms_timer.md（§6 两路静态扫描失败判据；§4 已判 D3D9 query 帧统计不可行）、LEAD_FINDING_frame_advance_and_enumchildwindows.md、HANDOFF.md §8.4 与帧计数定位失败行。结论：前人失败的是「绝对地址+线性扫描找 inc 全局」这一方法，不属重复劳动；本卡换路子。

[2026-11-14T12:16:50+08:00] [收口] FINAL:

## 三条候选判决

- **候选1 ETW → ① 可立即真机验**。`Microsoft-Windows-D3D9`（GUID 783ACA0A-790E-4D7F-8451-AA850511C6B9）与 `Microsoft-Windows-DxgKrnl`（802EC45A-…BA9D、keyword Present=0x8000000）均本机实测在机；D3D9 EventID 1/2 = Task"Present" Start/Stop = 提交层原生打点；wpr/logman/tracerpt 在机（xperf/wpa 缺）；管理员会话实测。后端已静态钉死：cnc-ddraw 经 LoadLibraryA 动态加载 d3d9.dll（"d3d9.dll"+"Direct3DCreate9" 字符串在 .rdata、无静态导入），renderer=direct3d9 ⇒ 可恢复目标显示链路存在，不判 ③。最小实验：experiment\exp_etw_short.cmd（含裁决三问判据、丢失零容忍）。
- **候选2 cnc-ddraw 结构通道 → ① 可立即真机验（主成果）**。maxfps 解析链三步打通：`0x1001E171 mov ecx,"maxfps"` → `call 0x1001EF70`（per-exe 段优先+[ddraw] fallback）→ `mov [0x100594E8],eax`；限帧初始化 0x10006880（interval=int(1000/有效fps)→[0x1005F128]）；每帧门闸 0x10006AE0（timeGetTime vs [0x1005F120] 上一帧时刻，不足则 Sleep 补差——阻塞式限帧，与 A 线「CPU 不含阻塞等待」互证）；★ **[0x1005F120] 每帧更新、3 个写入点（0x1001B01A/0x1001CD51/0x1001D2D2）**——进程外 RPM 只读轮询即得逐帧时间戳序列，非注入、与 A 线既有读 [0xA8ED84] 同授权类。**旧结论「渲染侧必须注入」否证**。生效 maxfps=60 定谳（[gamemd] 段覆盖全局 -1，双段 getter 静态证实）。最小实验：experiment\exp_rpm_framebeat.py（自洽校验 + 裁决预注册指标 + 措辞纪律「限帧放行间隔」）。
- **候选3 DWM/D3DKMT/GetPresentStatistics → ③ 不可行（作为该进程帧率仪器）**。DwmGetCompositionTimingInfo 是全局合成节奏无进程归属（全屏独占时 DWM 不参与；窗口化时仅系统节奏）；D3DKMTGetPresentStats/GetPresentStatistics 需进程内 hDevice/swapchain 句柄 = 注入域。残余价值：DWM 节奏可作裁决 T 参照。

## 一句话结论
渲染侧观测通道在非注入前提下**存在两条**（D3D9 ETW 提交层打点 + cnc-ddraw 限帧放行时间戳 RPM 轮询），均 ① 可立即真机验；前人失败源于方法不匹配（扫 inc 漏 mov、线性 sweep 失步），非「无计数」。

## 推荐下一步最小实验（按序）
1. exp_rpm_framebeat.py attach 运行中的 gamemd（60–240s）：验证放行间隔 ≈16–17ms、四全局自洽、菜单/失焦时间隔拉长形态；
2. exp_etw_short.cmd 短试采 2–5 分钟：回答裁决三问（归属/层级/丢失），与 1 同场景各一段互校；
3. ABBA ≥5 区组扰动校准 + 独立画面参照到位后，按裁决把 ETW 纳入 A 线正式仪器；无独立参照则试采只产「开启时的节奏」，不闭合「原本是否卡」。

## 落盘清单
RENDER_CHANNEL.md（主报告，含全部地址/字节/分级）、UNKNOWNS.md（9 项）、DISAGREE.md（5 条）、
evidence\（4 份脚本 stdout 留档）、scripts\（3 份本卡脚本 + prior 3 份已核哈希）、
experiment\（exp_etw_short.cmd + exp_rpm_framebeat.py，py_compile 通过）。
bin\ 哈希已核与 ra2youli 原件一致；全程离线、零注入、零文件改动。
