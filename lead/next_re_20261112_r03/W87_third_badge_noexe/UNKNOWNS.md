# W87 · UNKNOWNS（静态阶段未证项与最小验证路径）

> 受本卡硬纪律约束（禁止启动游戏、禁止注入与附加调试器），所有需要运行时状态或美术渲染验证的问题均诚实标为 `[未证]`，不作猜想填补。

## 1. `0x52F191` 对 `0x6EB` 跳过 `0x4D7` 消息的运行时后果 `[未证]`
- **已知实测**：`0x52EC00` 的 `0x497` 初始化分支对 `0x6EA`（1770）和 `0x6EC`（1772）依次发送了 `0x4D5`、`0x4D4` 与 `0x4D7`（`0x52F12B..0x52F1C1`）；但对 `0x6EB`（1771）只发送了 `0x4D5` 和 `0x4D4`，**未发送 `0x4D7`**（`Static_Handler` `0x6153E0` 对 `> 0x4D4` 消息通过 `0x616354` 跳转表分发）。
- **未证点**：`0x4D7` 具体在 `Static` 控件中设置哪一项状态（是否仅影响默认动画/高亮帧，还是影响鼠标交互前状态），以及动态下 `1771` 仅靠 `0x4D5`/`0x4D4` 能否正常高亮与触发 `BootCamp` 动画/点击进入 `tut1`。
- **最小验证方法**：继续静态反汇编 `0x615FBD..0x616038` 与 `0x616383` 索引表核实 `0x4D7` 对应跳转表槽位；并在允许运行的测试卡中于沙盒游戏内实测点击 `1771`。

## 2. 第三徽章美术缺失与 `RT_DIALOG 148` 布局坐标选择 `[未证]`
- **已知实测**：
  - `RT_DIALOG 148` 尺寸为 `533×369`（`r2_r3_final_check_stdout.txt`），已占用区域包括：`1770` `(125,34) 174×87`、`1959` `(4,123) 415×13`、`1295` 滑块 `(137,140) 140×14`、`1822`/`1648` 难度文本 `(137..278,167) h=12`、`1772` `(125,216) 173×86`、`1960` `(3,304) 420×13`、`1685` 底部 `(8,354) 303×12`、右侧列 `421..533`。
  - 第 3 徽章没有任何内置像素美术（`W61` 既有结论：`CAMPAIGN.PCX` 无第三徽章，全 MIX/CSF/`.rsrc` 无相关图像）。
- **未证点**：在不改 `gamemd.exe` 的前提下，若仅靠 R1 在对话框模板追加 `1771` 透明 `STATIC` 热区，用户界面上并**不会自动出现可见图标**；需要确定配套视觉呈现方案（例如：利用 MIX/散装 `CAMPAIGN.PCX` 替换背景图，或在 `ddraw.dll` / Hook 中把 `1771` 设为带文字/自绘的 `STATIC`/`SS_OWNERDRAW`），以及左侧空闲区间（如 `x≈4..120` 或压缩重排三徽章纵坐标）在游戏实际缩放后的可用像素矩形。
- **最小验证方法**：在允许启动游戏的沙盒测试中截取 `640×480` 战役菜单实际画面，与 `RT_DIALOG 148` 对照坐标换算。

## 3. `ddraw.dll` Hook 与 `cnc-ddraw` 自身 Detours / Wine 的兼容性 `[未证]`
- **已知实测**：
  - `gamemd.exe` `.rdata` IAT `0x007E1048` 导入 `DDRAW.dll!DirectDrawCreate`（仅 1 处跳板 `0x007C89D4`），且未在 `VERSION.dll` 检测路径（`0x74FDE8..0x74FE99`，查 `[0xb732f0]` 即 exe 自身）检验 `ddraw.dll` 哈希或版本。
  - `work\ddraw.dll`（`cnc-ddraw`）自带 `.detourc`/`.detourd` 节，且导入 `USER32.dll` / `KERNEL32.dll`。
- **未证点**：
  - 若采用"转发代理版 `ddraw.dll`（shim）+ 加载 `cnc-ddraw_orig.dll`"方案，在目标运行环境（Windows 原生 / Steam / Wine 需要 `WINEDLLOVERRIDES="ddraw=n,b"` 等）下，`DllMain` 中挂钩 `gamemd.exe` IAT 槽 `0x007E1450` (`USER32!CreateDialogIndirectParamA`) 的加载时机、锁安全性（Loader Lock 内写 IAT vs 首次 `DirectDrawCreate` 调用时延时挂钩）、以及是否会触发安全软件/兼容性补丁异常，尚未动态实测。
- **最小验证方法**：在允许运行游戏的测试环境编写最小 IAT hook 原型，验证 `DirectDrawCreate` 时改写 `0x007E1450`（或由 `cnc-ddraw` 源码分支挂钩）能否稳定命中 `0x006226CB` 的 `lpDialogFunc == 0x0052EC00`。

## 4. 仓库发行链路对 `ddraw.dll` 哈希的实际门禁执行点 `[静态仅见配置，发布流程未全测]`
- **已知实测**：
  - `ra2forge\version_guard.py` 的 `L1_FIELDS` 只包含 `gamemd.exe` 相关字段，**不含 `ddraw.dll`**；`S1_REASON_CODES` 预留了 `"DDRAW_IDENTITY_MISMATCH"` 但在当前 `classify()` 中未触发阻断。
  - `TRACK_B_gates.json` 记录了 `C07_ddraw_sha256`（`85e0f7d5...`）与 G5 `official_ddraw`，`BASELINE.json` 也登记了 `ddraw.dll`；`ra2opt\cddraw.py` 会在用户运行优化器时管理并覆盖 `ddraw.dll`。
- **未证点**：除 `version_guard.py` 之外，未来项目构建/打包脚本是否会对 `TRACK_B_gates.json` 的 G5 执行硬失败，以及 `ra2opt` 优化器与自定义 `ddraw.dll` 在产品分发层面的优先级约定，需项目工程决策。
