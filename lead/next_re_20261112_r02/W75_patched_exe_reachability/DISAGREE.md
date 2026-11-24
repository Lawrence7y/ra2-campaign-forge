# W75 · DISAGREE.md（口径分歧 / 收窄 / 自曝问题）

> 执行者 Hy4｜2026-11-14
> 本文件登记：与已签发表述的**口径差异**（不是推翻）、本卡必须收窄的强表述、
> 以及执行过程中的自曝问题。**不含任何对路线 (c) 冻结裁决的异议。**

---

## D-W75-1 · 对「静默传 `-1` 给 `[Scen+0x34CC]`」的运行期口径收窄 ⚠ 最重要

`[转引]` 任务卡背景 / `LEAD_CHECK_menu_3slot.md` / W58：
> 「`WM_LBUTTONUP` … `call 0x46CC90` 按名查表；`tut1` 在 `BATTLEMD.INI`
> 里不存在 ⇒ 查表返回 `-1`（`0x46CCC2 or eax,-1`）**静默**传给
> `[Scen+0x34CC]`，无错误框。」

`[本次实测]` 本卡读到：`Scen+0x34CC` 在**进入战役菜单的基线**就已经是
`-1 / 0xffffffff`；hover / 点击后 4 个采样点**仍为 -1，零变化**。

⇒ **口径分歧**：不能照抄成「点击把 `Scen+0x34CC` 改成了 -1」。
本卡能写的只有：
> 「点击后 `Scen+0x34CC` 为 -1、`Scen+0x125C` 为空；由于基线已是 -1，
> 本卡**未观测到该字段被改写**，也**未观测到它被改成异常值**；
> 运行期表现为**无错误框 + 退回上一級菜单**。」

这不是否认 W58 的静态结论（`-1` 返回值、无错误串、无 MessageBox 那条链
与本卡观测完全相容），而是**拒绝把「值为 -1」冒充「写动作被实测」**。
写动作需断点 / ms 级采样 → `[待运行验证]`（U-W75-1）。

## D-W75-2 · 「可达」≠「可用」：本卡主动禁止的表述

任务卡红线 7 明确要求「不得写『第三徽章可用』」。本卡额外主动禁用：

| ❌ 禁用 | ✅ 本卡实际写 |
|---|---|
| 第三徽章可用 / 第三个战役能玩 | 补出的是**透明点击热区**，无独立美术，点击不进图 |
| 路线 (c) 解冻 / 产品可做 | 维持 `LEAD_RULING_C_line_route_a_first.md` 冻结裁决，见 §0 |
| 补丁 exe 完全无副作用 | 只说「本镜像/本配置/两趟内未观测到崩溃与资源加载错误」 |
| 「静默失败 = 完全没反应」 | `[本次实测]` 点击**有响应**：画面过渡并退回「單人遊戲」主菜单 |
| 官方战役不受影响 / B 线等价性 | 与本卡无关，一字不写 |

## D-W75-3 · 「`#32770` 窗口」不是错误框（自纠一次判读）

`[本次实测]` `error_windows()` 启发式在两趟 hover / click 后都报了一个
`cls=#32770, text="", rect=[0,0,533,400], visible=True` 的窗口。
第一眼容易被当成「弹出了系统对话框」。核对后：
- 它**两趟都存在**（A/B 各一个，hwnd 不同），是 RA2 自绘对话框的容器；
- `text=""`，无 `GUI:OK` / `Unable…` / 任何错误串；
- 全屏 `*_desktop.png` 与游戏画面截图均**没有 MessageBox 视觉**；
- `except.txt` / `ra2render.log` SHA 零变化。

⇒ 判为**引擎自带空标题对话框容器**，非错误框。本卡在报告里把它显式列出来
并说明判读依据，避免下游误引 `error_windows` 的启发式输出当崩溃证据。

## D-W75-4 · `n_controls` 在点击后 19→13 的解释是推断，不是实测

`[本次实测]` A 点击后 `n_controls=13`、画面退回「單人遊戲」主菜单；
B 保持 18、画面不动。
`[静态推断]` 差值来自「`GUI:CampaignMenu` 对话框被销毁、回到 SinglePlayer
子菜单」，**本卡没有抓栈 / 没有逐帧跟踪窗口销毁序列**。
报告里只把 19→13 当作「点击被响应」的**现象**，不写内部机制。

## D-W75-5 · 与 W61 的几何口径：模板坐标 ≠ 逐像素相等

`[转引]` W61 补丁写入 `(310,34) 110×87`。
`[本次实测]` 运行期 `GetWindowRect(1771) = [310,37,421,132]`（111×95）。
差 y+3 / h+8，来自 DLGTEMPLATEEX 对话框单位→像素换算（同一换算下
1770 模板 `(125,34)174×87` → 实测 `[94,39,326,130]`）。
⇒ 本卡**不**写「几何逐字节精确一致」，只写「一致到几个像素、中心 (365,84)
在 1770 右边界之外、命中由 `[0xA8F7A8]=0x6EB` 独立确证」。
`[静态推断]` 1770/1771 在 x=310..326 约 16 px 重叠，中心不重叠。

## D-W75-6 · 自曝：一次控制台显示伪影（已查清，非数据缺陷）

`[本次实测]` 执行 `python w75_trip.py --trip B 2>&1 | Tee-Object` 时，
`scen_ptr` 在 pwsh 控制台被渲染成 `64011-128`（插入连字符），
初看像非法 JSON / 损坏读数。
`[本次实测]` hexdump 原始文件字节 `3634303131313238` = `64011-128`
（纯 8 位数字），`json.loads` 返回 `int`，所有 `Scen+off` 偏移读取成功。
⇒ **显示层伪影，产物本身合法**；已改用纯文件输出复核
（`AB_COMPARISON.json` / `.tsv`）。登记备查，见 U-W75-9。

## D-W75-7 · 自曝：离线 prep 的一次 benign `UnicodeDecodeError`

`[本次实测]` `w75_prep.py` 调 `robocopy` 时，
`subprocess.run(..., capture_output=True, text=True)` 的后台读取线程
因 robocopy 输出为 GBK、默认解码器报
`UnicodeDecodeError: 'gbk' codec can't decode byte 0xb4`。
该异常**只在读取线程**，`r.returncode=1`（robocopy 成功码）正常取得，
后续 `diff_trees` 全树比对 `identical_tree=True` 证明复制完整。
`[处置]` 已把 `w75_lib.py` / `w75_prep.py` 的 `subprocess.run` 全部改为
`errors="replace"`，TRIP A/B 的日志干净、无此异常。
`[影响]` 无：`out/cmd_robocopy_sandbox.log` 与 `PREP.json` 结论不受影响，
不重跑 prep。

## D-W75-8 · 自曝：`w75_csf_verify.py` 首版 print 触发 GBK 编码异常

`[本次实测]` 首版用 `print(json.dumps(res, ensure_ascii=False))`，
因含 `\ua808` 等字符，pwsh 控制台 GBK 编码抛 `UnicodeEncodeError`。
**JSON 产物 `out/CSF_TOOLTIP_MATCH.json` 在 print 之前已正确写入**。
`[处置]` 改为 `ensure_ascii=True` 打印并重跑，产物一致
（`observed_matches_STT_CampaignAnimTutorial=True`）。
`[影响]` 无。

## D-W75-9 · 本卡不挑战任何已签发裁决

本卡对以下签发件**无异议**，仅补齐「运行期可达性」这一格：
`LEAD_RULING_C_line_route_a_first.md`（(c) 冻结）、
`LEAD_CHECK_menu_3slot.md`（3 槽 / `tut1` 查表 -1）、
`LEAD_VERIFY_W58.md`、`LEAD_VERIFY_W59.md`、`W61 THIRD_BADGE_ROUTE.md`、
`W64b`（`[TUT1]` / `trn01t.MAP`）。
本卡结论**不改变**路线 (c) 的冻结裁决，见 `REACHABILITY_RESULT.md` §0。
