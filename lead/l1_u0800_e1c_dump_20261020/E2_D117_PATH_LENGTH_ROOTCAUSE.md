# E2：L1 五趟失败的真正根因 = D-117 载体路径长度（2026-10-20）

## 一句话结论

**L1 五趟（含 E1/E1b/E1c）失败的真因不是崩溃、不是遮挡、不是地图、不是 csf 缺件，
而是载体绝对路径 ≥131 字符 ⇒ gamemd 资源路径拼接损坏 ⇒ 弹 csf 初始化失败框。**
D-117 在 2026-10-17 就已确立这个阈值，但本轮 L1 的 out-dir 命名全部超过它，于是同一颗雷
被重新踩了一遍，且被误判成「随机崩溃」。

## 一、路径长度相关性（全趟实测）

| 趟 | 载体绝对路径长度 | 结局 |
|:--|--:|:--|
| `t55k_20261020` | **130** | **成功**（units0=842，三窗 31.24fps）|
| `l1_u0800_20261020` | 134 | EXIT 19 |
| `l1_u0800_e1_20261020` | 137 | EXIT 19 |
| `l1_u0800_e1b_20261020` | 138 | EXIT 19 |
| `l1_u0800_e1c_dump_20261020` | 143 | EXIT 19 |

唯一成功趟 = 130；全部失败趟 = 134–143。分界点落在 131 上。

## 二、单变量对照实验（同内容、只改路径长度）

载体内容 = `scratch/boot_probe/arm_a`（88 件，与 L1 同源）。
用 NTFS 目录联接（junction）造出不同长度的**同一份**载体路径，
`CreateProcessW` 直启（无 stdio 重定向 —— 已实证 PIPE 会导致 0.1s 假退出）。

| 载体路径长度 | 窗口标题 | 窗口尺寸 | 判读 |
|--:|:--|:--|:--|
| 54 | `Yuri's Revenge` | 正常 | ✅ 正常启动 |
| 125 | `Yuri's Revenge` | 正常 | ✅ |
| 128 | `Yuri's Revenge` | 正常 | ✅ |
| **130** | `Yuri's Revenge` | 正常 | ✅ **边界内** |
| **131** | **`Red Alert 2`** | **464×191** | ❌ **csf 失败框** |
| 133 | `Red Alert 2` | 464×191 | ❌ |
| 143 | `Red Alert 2` | 464×191 | ❌ |

**阈值精确落在 131，与 D-117 完全一致（逐字符）。**

## 三、那个 464×191 框的正文（实测读出）

用 `EnumChildWindows` 读对话框静态控件文本：

```
Unable to initialize 'ra2.csf', please reinstall Red Alert.
Keine Initialisierung von 'ra2.csf' möglich. Bitte installieren Sie Red Alert erneut.
Initialisation de 'ra2.csf' impossible. Veuillez réinstaller Red Alert.
```

标题 `Red Alert 2`，尺寸 464×191，位置 `[623,385,1087,576]` —— 与记忆库
`u0400-carrier-csf-root-cause` 记录的 T14 现场**完全同构**（同尺寸、同标题、同文案）。

## 四、这如何解释了 E1b/E1c 的「崩溃」

关键机制：**csf 失败框是模态 MessageBox，进程会一直停在那里等点击。**
harness 看不到 800×600 窗口，于是走 Esc 纪律路径（`qc151_trip.py:6576-6580`，
`_poll % 8 == 0 and _esc_sent < 2`）向该模态框发 Esc。

实测（`dialog_text_probe.py --send-wm-close-at 3.0`）：
给该框发 `WM_CLOSE` ⇒ **进程在 0.25s 内以 exit code 0 干净退出**。

⇒ E1b/E1c 观测到的「t≈5.2s 进程死亡」= harness 的 Esc 纪律把模态框推掉，
   gamemd 走 csf 失败后的 `ExitProcess` 路径。**这不是崩溃，是设计内的错误退出。**

而 E1b 抓到的 `0x0084F2BA` 写 `.data` 被拒、E1c 的 `0x0054A56E` 写 `[esi+4]`，
**是模态框关闭后 gamemd 继续走已损坏初始化路径的次生现象**，不是主因。

## 五、推翻的既有结论

| 既有结论 | 状态 | 依据 |
|:--|:--|:--|
| 「L1 真因=进程 5 秒自行退出（csf 失败消息框）」§308 | **部分成立**：退出确实发生，但**根因是路径长度，不是 csf 缺件**（88/88 件含两件 csf 仍在）| 本表 §二 |
| 「E1b 崩溃框 = Windows WER 崩溃对话框」 | **推翻**：那是 csf 失败的**引擎模态框**，不是 WER | §三 控件文本 |
| 「两趟崩溃地址不同 ⇒ 随机堆腐化」 | **推翻**：崩溃地址是模态框关闭后的次生现象，与 ② RC-1 无关 | §四 |
| 「前台遮挡 / 地图版本 / 载体件数 / DPI」 | 维持排除 | 此前 E1 系列 |

## 六、对 ② 目标的影响（重要）

**E1b/E1c 的两个崩溃地址不能作为 ② 主崩溃的证据。** 它们是在一个
「初始化已失败」的进程里产生的，与正常游戏路径无关。

⇒ **SBH 守卫 A/B 现在跑没有意义**：它要拦的是正常游戏中的堆腐化，
   而当前 L1 连正常启动都做不到。

⇒ 正确的下一步是：**先用短路径跑通 L1 基线**，拿到真实单位数与帧率，
   再在**健康进程**上观察 ② 的主崩溃是否复现。

## 七、修复方案

不是改代码，是**改 out-dir 命名**：

| 项 | 现值 | 应改为 |
|:--|:--|:--|
| out-dir | `l1_u0800_e1c_dump_20261020`（34 字符）| `l1a_20261020`（13 字符）|
| 预测载体长 | 143 | **129**（< 131 ✅）|

长期修法（建议另开项）：harness 在 `create_isolated_carrier` 里**主动断言载体
绝对路径 < 131**，超限即硬停并给出提示。这样这个坑不会再被踩第三次。

## 八、复现命令

```bash
cd D:\Project\ra2-campaign-forge\scratch\boot_probe

# 单变量路径长度扫描（junction 版）
python dialog_text_probe.py --carrier <长度N的junction> --timeout 4

# E2 短路径 harness 趟
python launch_e2_shortpath.py --dry-run
python launch_e2_shortpath.py
```

探针：
- `path_ab_probe.py` —— 只测存活/窗口，不读对话框
- `dialog_text_probe.py` —— 读对话框正文 + Esc/WM_CLOSE 交互
- `launch_e2_shortpath.py` —— 短 out-dir 发射器
