# B 路续探（第 2 轮）：输入注入的完整排查与边界定谳

> 执行方：调度方（Lead）。承接 `PATH_B_VERDICT.md`（第 1 轮已解出渲染面、排除坐标假设）。
> 本轮把「为什么点不动」排查到底，并排除了 5 个备选假设。

---

## 1 · 本轮新增的**可用技巧**（有独立价值）

### 1.1 WMI 分离启动 —— 解决「启动全屏游戏阻塞 shell」

前两轮 `Start-Process gamemd.exe` 会让宿主 PowerShell **卡死**（两次后台任务都被迫终止）。
本轮找到可行方法：

```powershell
Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
  CommandLine = 'cmd.exe /c cd /d "D:\Project\ra2-campaign-forge\ra2youli" && start "" "gamemd.exe"'
}
```

⇒ **ReturnValue=0、游戏正常起来（窗口 `Yuri's Revenge`）、shell 未被阻塞。**
这解决了本环境「无法从脚本启动游戏」的障碍，后续任何真机自动化都可复用。

### 1.2 ctypes 句柄坑（复发记录）

`GetWindowDC` 返回的 HDC 高位可能为 1，用 `wt.HDC`（有符号 int）声明会
`OverflowError: int too long to convert`。**必须声明 `restype = ctypes.c_void_p`**。
（`GetWindowDC`/`CreateCompatibleDC`/`CreateCompatibleBitmap`/`SelectObject` 全都要。）

---

## 2 · 排查矩阵（逐个假设 → 实测 → 排除/成立）

| # | 假设 | 检验方法 | 结果 |
|:--|:--|:--|:--|
| H1 | 坐标算错 | 截图逐按钮标定 y 值；包围盒实测 `(0,0,800,600)`、scale 1.0 | ❌ 排除（坐标精确命中「單人遊戲」y≈222） |
| H2 | 渲染面原点非窗口原点 | `GetWindowDC` 截本窗口求非黑包围盒 | ❌ 排除（原点 = (0,0)） |
| H3 | cnc-ddraw 按「窗口→游戏」缩放鼠标坐标 | 反推屏幕坐标 `(700×1707/800, 222×960/600) = (1493,355)` 后点击 | ❌ 排除（按钮区差异 = 1，仍无变化） |
| H4 | 玩了 DirectInput 独占鼠标，SendInput 不产生设备事件 | **解析 gamemd.exe 导入表** | ❌ **排除**：16 个导入 DLL 里**没有 dinput**，鼠标走 `USER32` 的 `WM_*` |
| H5 | `ClipCursor` 把鼠标限制在别处 | `GetClipCursor` 实读 | ❌ 排除（区域 = `(0,0)-(1707,960)`，即整屏，无限制） |
| H6 | 窗口没拿到焦点/前台 | `GetForegroundWindow==hwnd` → True；`AttachThreadInput` 成功；`SetFocus` 后 `GetFocus()==hwnd` | ❌ 排除（焦点确实在游戏窗口） |
| H7 | 我的判据不可靠（背景动画恒变） | 对照：用「按钮栏区域」判 vs 用「全画面稀疏指纹」判 | ✅ **成立**：全画面指纹每帧都变（雷达背景动画），只有按钮栏区域是可靠判据 |

### 2.1 关键读数（本轮实测）

| 项 | 值 |
|:--|:--|
| 窗口 | `1707×960`，客户区 `1706×960`，客户区屏幕原点 `(0,0)` |
| 渲染面（非黑包围盒） | `(0, 0, 800, 600)` |
| scale | `(1.0000, 1.0000)` |
| ClipCursor | `(0,0)-(1707,960)` |
| `GetForegroundWindow == hwnd` | **True** |
| `AttachThreadInput(cur, game_tid, TRUE)` | **True** |
| `SetFocus(hwnd)` 后 `GetFocus()` | **== hwnd** |
| gamemd.exe 导入 DLL（16 个） | `xyr.dll, KERNEL32, USER32, GDI32, ADVAPI32, SHELL32, ole32, OLEAUT32, WINMM, WSOCK32, DDRAW, DSOUND, VERSION, COMCTL32, IMM32, binkw32` |
| **含 dinput?** | **无** |
| **hover 按钮栏差异** | **0** |
| **点击后按钮栏差异** | **0** |
| 缩放坐标点击后按钮栏差异 | **1**（等于无变化） |

### 2.2 一个诚实的自我纠正

本轮我还测了键盘 `Esc`，用「全画面差异」判得 1345 —— **但那不可信**：
主菜单雷达背景是持续动画，全画面指纹永远在变。截图显示仍是主菜单，**Esc 也没生效**。

⇒ **判据必须限定在「静态区域」**（按钮栏），不能用全画面。
这条我在上一轮已经踩过（误判点击成功），本轮又差点重复。已在 H7 登记。

---

## 3 · 边界定谳

**已排除**：坐标、渲染面原点、缩放映射、DirectInput、ClipCursor、焦点/前台、权限。

**仍然成立的现象**：
- 游戏正常渲染（背景动画在播）⇒ 主循环在跑
- 窗口有前台 + 焦点
- 但 **hover 与 click 对按钮栏区域产生 0 像素变化**

⇒ **合成鼠标输入在本配置下不被游戏消费，而键盘路径未能证实有效（判据不可用）。**
⇒ 这是**环境级输入注入边界**，不是坐标/焦点/架构问题。

最可能的剩余解释（**均未验**）：
1. `xyr.dll`（gamemd.exe 的第一个导入 DLL，333,312 B）作为 wrapper 拦截/重写了鼠标消息；
2. cnc-ddraw 的 `adjmouse=true` 在 `windowed=false` 全屏下把鼠标消息吞掉或改投到别处；
3. 游戏用 `WM_MOUSEMOVE` 但依赖 `MK_*` 键状态或需要真实 `GetMessage` 队列时序（合成事件时序不符）。

---

## 4 · 结论与下一步

**B 路在「不改配置」前提下的自动导航已走到尽头。**

E3 最后一环（真对局 `G_FRAME` 递增验证）现在只剩两条路，都**不需要我再改代码**：

| 路 | 做法 | 状态 |
|:--|:--|:--|
| **人工** | 用户手动点进对战 → 我跑 `verify_battle_frame.py` 只读验证 | 工具已就绪（`HOW_TO_VERIFY_BATTLE.md`） |
| **改配置** | 临时 `ddraw.ini` 的 `windowed=true`（原值已备份在 `deploy/backup_ddraw/`），跑完还原 | 用户此前未选 |

**不建议**继续在这条路上投入：已排除 6 个假设，剩余解释都指向「wrapper/驱动层拦截」，
需要调试器级或驱动级手段，性价比低。

---

## 5 · 零破坏自证（本轮）

| 项 | 值 |
|:--|:--|
| `ddraw.ini` sha256 | `c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52`（**与基线一致，未改**） |
| `ra2md.ini` sha256 | `2ccf13c23b4c958bc6eb6030f1349e891606d3a37d014e3a1115d8e469d2f0c9`（**与基线一致，未改**） |
| 残留 gamemd 进程 | **0** |
| 游戏目录写入 | **无**（只读 + 截图落工作区） |
| 本轮唯一新增运行期动作 | 用 WMI 启动过一次游戏，随后 `Stop-Process` 终止 |
