# RA2 / 尤复 稳定性与性能优化（ra2opt）

`ra2forge` 负责**造战役**，`ra2opt` 负责**让游戏本身不闪退、少卡顿**。两者互不干扰：
`ra2opt` 不碰 `.mix` 资源、地图、`BATTLEMD.INI`，改的是引擎/wrapper/配置/系统标记。

```bash
python -m ra2opt audit  --online          # 只读体检，出待办清单 + out/optimize/report.md
python -m ra2opt apply  --profile perf    # 应用优化（自动备份，可一键回滚）
python -m ra2opt verify                   # 启动冒烟测试：确认游戏还能起来
python -m ra2opt status                   # 当前状态与可回滚内容
python -m ra2opt restore                  # 完全还原到 apply 之前
python -m ra2opt budget <设计.json>       # 检查战役关卡的单位预算（防"多单位卡顿"）
python -m ra2opt selftest                 # 32 项内置自检
```

默认游戏目录 = 项目内的 `ra2youli/`，也可用 `--game <目录>` 指定。

---

## 这台机器上实际改了什么

| 层 | 改动 | 依据 | 回滚方式 |
|---|---|---|---|
| 渲染代理 | cnc-ddraw **4.4.7.0 → 7.1.0.0** | 见下节，含多条 RA2 专项崩溃修复 | 覆盖前快照，`restore` 还原 |
| 渲染配置 | `ddraw.ini` 的 `[ddraw]`/`[gamemd]` 键校准 | 与官方 v7 键表逐键核对后才写 | 同上 |
| 引擎 PE 头 | `gamemd.exe` / `Ra2md.exe` / `Ra2.exe`：**开 LAA** + 栈 1MB → 4MB | 32 位进程 2GB 地址空间上限；寻路/AI 递归吃栈 | 只改 Optional Header，`restore` 或 `laa off` |
| 游戏配置 | `ra2md.ini` / `ra2.ini`：`DetailLevel` 2 → 1 | 多单位时渲染是主要瓶颈 | 改回 2 即可 |
| 系统标记 | 去掉 `16BITCOLOR`/`RUNASADMIN`，补 `DISABLEDXMAXIMIZEDWINDOWEDMODE`/`HIGHDPIAWARE` | 见下节 | 记录原值，`restore` 还原 |
| 启动方式 | 生成 `ra2opt_play.bat`（高优先级启动） | 减少被其他进程抢占导致的抖动 | 删掉即可 |

`ra2md.ini` 只动了 `[Options] DetailLevel` 一个键；**注释、键顺序、CRLF、编码原样保留**，
玩家的 `GameSpeed=6` / `Difficulty=1` / `CampDifficulty=0` / 阵营与昵称全部不受影响。

---

## 为什么是这几项

### 1. cnc-ddraw 升级（收益最大、风险最低）

本机装的 `ddraw.dll` 是 **2021 年的 v4.4.7**。官方 2021→2024（v7.1.0）之间发布了多条
**直接针对 RA2/YR 的修复**：

- v6.3　Steam 版红色警戒 2 崩溃 workaround
- v6.4　非活动窗口下的步兵鼠标输入修复
- v7.0　特权指令崩溃修复；窗口尺寸与整型缩放修复
- v7.1　无硬件加速时 OpenGL 崩溃、退出时崩溃、GDI 限速器支持

替换一个 dll 就能拿到这些修复。调优项只用**与 v7 键表核对过**的键；发现 v4 的
`d3d9linear` 在 v7 已改名为 `d3d9_filter`，工具会主动跳过而不是写一个失效键。

`windowed` / `fullscreen` 刻意**不动**——那是玩家的显示偏好，不属于稳定性范畴。

### 2. Large Address Aware（针对"闪退"）

`gamemd.exe` 是 32 位且未声明 LAA，用户态地址空间被卡在 2GB。大地图 + 多单位 + 多 AI 时
内存很容易撞上限，表现就是"玩着玩着突然闪退"。开 LAA 后在 64 位系统上可用 4GB。

- 只改 PE Optional Header 的 `DllCharacteristics` 一个 bit，**代码段零改动**（自检里有
  "打补丁后代码段字节不变"和"`.text` 指纹不受影响"两项断言）。
- 用 `.text` 段 SHA-256 当引擎指纹：打完补丁后仍能认出这是哪个版本的 gamemd。
- 32 位 Windows 上没有额外收益（也不会有损害），工具会提示。

### 3. 主线程栈 1MB → 4MB（针对"毫无征兆的闪退"）

MSVC6 默认 1MB 栈。引擎的寻路/AI 递归在大地图 + 大量单位时会吃栈，栈溢出就是无预警闪退。
改成 4MB 只多占**保留**的地址空间（提交仍按需），不改变任何指针运算。

### 4. 兼容性标记（整合包遗留问题）

本机整合版的 `0ne.bat` 给 `Ra2.exe` / `Ra2md.exe` / `配置器.exe` 打了
`RUNASADMIN 16BITCOLOR WINXPSP2`。在已经装了 cnc-ddraw 的前提下：

- `16BITCOLOR` 强制 16 位色深（会改桌面色深），与现代显卡驱动 + cnc-ddraw 冲突，
  只会引入模式切换失败/黑屏/颜色错乱。
- `RUNASADMIN` 每次启动弹 UAC；更麻烦的是提权进程会破坏 ddraw 代理/hook
  （跨完整性级别的注入失败、文件虚拟化）。
- `WINXPSP2` **保留不动**（它可能被整合包用于绕过版本检查，属于"可能有用"的一类）。
- 补上 `DISABLEDXMAXIMIZEDWINDOWEDMODE`（走独占全屏而不是 Win10+ 的"全屏优化"假全屏，
  后者有额外合成延迟）与 `HIGHDPIAWARE`（避免 DPI 缩放导致模糊）。

> `配置器.exe` 的标记本工具不管（它不是游戏本体，改了反而可能影响整合包自带工具）。
> 想一并清掉：
> `reg add "HKCU\Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers" /v "<配置器.exe 完整路径>" /t REG_SZ /d "~ WINXPSP2" /f`

### 5. 高优先级启动器

引擎是 2001 年的单线程循环，被其他进程抢占时抖动明显。`ra2opt_play.bat` 用
`start /high` 启动；`python -m ra2opt play` 走的是 `CreateProcessW` +
`CREATE_SUSPENDED` → 先设优先级/亲和性 → 再 `ResumeThread`，没有"先跑起来再改"的竞态。

---

## 关于"多单位卡顿"：能做与做不到的

必须说清楚**边界**，否则容易期待落空。

**卡顿的根因是引擎结构性的**：RA2/YR 的模拟是单线程、渲染是 CPU 软件 blit（引擎自己
用 RLE 把 SHP 精灵逐像素画进 16 位表面），没有任何硬件加速路径。单位一多，每帧要跑的
逻辑和要画的像素线性增长，主频就是硬上限。**这不是配置能消除的**，重写渲染器/寻路
需要改引擎代码段，风险与工作量都不是这个工具该承担的。

**配置层真正有效的杠杆（按效果排序）**：

| 杠杆 | 说明 | 怎么做 |
|---|---|---|
| 减少同屏物件数 | 唯一真正"根治"的手段 | 用 `ra2opt budget` 在设计期卡住；把"开局铺满"改成"少量开局 + 定时增援" |
| 降低渲染细节 `DetailLevel` | 少画动画/装饰层 | 已设为 1；想恢复画质：把 `ra2md.ini` 的 `DetailLevel` 改回 `2` |
| 降低分辨率 | 视口小 → 可见精灵少 → blit 少 | 改 `ra2md.ini` 的 `ScreenWidth/ScreenHeight`（配合 `ddraw.ini` 保持 `width=0` 即 1:1 输出） |
| CPU 单核性能 | 引擎吃的是单核 | 硬件问题；若愿意冒险可 `apply --multi-cpu` 关掉 cnc-ddraw 的单核绑定换一点吞吐（稳定性风险自担） |
| 高优先级启动 | 减少抢占抖动 | 用 `ra2opt_play.bat` 启动 |

**本工具故意没做的**（做了大概率更糟）：

- **不覆盖 `rulesmd.ini`**。RA2 的文件系统对 `rulesmd.ini` 是"取第一个命中"，不是逐键合并，
  放一份进去会把原版规则**整份替换**。要改就得基于完整原文件派生，那属于 MOD 范畴，
  且会和战役内容互相干扰。
- **不改游戏代码段**。任何寻路/渲染的"优化"都需要反汇编引擎并逐版本验证，
  没有真机验证就发布等于把玩家当测试机。
- **不动显示模式偏好**（`windowed`/`fullscreen`）和分辨率。

---

## 安全设计

所有写操作都过 `safewrite`，只有一条落盘路径，且强制：

1. 目标必须是**游戏目录的直属既有文件**（`realpath` + `commonpath` + 父目录比对）；
2. 拒绝 `..`、拒绝越界、拒绝软链接外逃；
3. 默认不新建文件；要新建必须显式 `allow_create=True` 且仍限制在直属层级；
4. 先写临时文件再原子替换。

### 关于"文件名 → 路径"的三层防护

`--exe <名字>` 是用户可控输入，这类"拼路径再写盘"的代码有一个很阴的坑：

```python
Path("D:/game") / "C:/Windows/System32/x.dll"   # → C:/Windows/System32/x.dll
```

Windows 上 pathlib 的 `/` 遇到 drive-qualified 的右操作数会**整段替换**左侧，
于是"在游戏目录里拼个路径"直接变成"写系统目录里的文件"。所以：

1. `safewrite.resolve_within()`：`realpath` + `commonpath` + 父目录比对，拒绝 `..` 与越界；
2. `GameDir.exe()`：只接受**裸文件名**（`^[A-Za-z0-9._-]{1,64}$`），带分隔符/盘符/`..`
   一律拒绝；`GameDir.resolve_exe()` 在此之上再做沙箱解析并要求目标存在。
   凡是名字来自用户输入的地方都走 `resolve_exe()`，不用直接拼；
3. `pe._atomic_write()`：拒绝含 `..` 的路径、拒绝非普通文件
   （`pe` 是底层模块，不负责沙箱——这一层只是兜底，真正拦住越界的是第 1、2 层）。

自检里有 4 项专门打这组边界（`sandbox:` 前缀），其中一项就是拿
`--exe "../evil.exe"` 和 `--exe "<绝对路径>"` 去跑一遍 `apply`，
断言游戏目录外的文件**一个字节都没变**、且合法目标仍然生效。

出网只有一处：取 cnc-ddraw release 包。协议必须是 https、主机必须在显式白名单内、
解析出的 IP 不能是环回/私网/链路本地/保留地址，重定向逐跳复检，响应体有大小上限。
本机 DNS 走 TUN 代理会返回 `198.18.0.0/15` 的 fake-IP，这是唯一被放行的例外，
且会记进体检报告的 `net.note` 里，不做静默降级（TLS 证书校验仍验证 `api.github.com` 身份）。

### 备份与回滚

每次 `apply` 前把原始字节存进 `<游戏目录>/.ra2opt/orig/`（**首次触碰时**保存，只写一次），
变更记进 `.ra2opt/manifest.json`。`restore` 会把改过的文件还原、把新建的文件
（如启动器）删除、把注册表标记还原成原值。回滚后与原始安装**逐字节相同**（已验证）。

### 快照误删了怎么办

`clean` 会删掉快照（放弃回滚能力）。若误删，只要还有一份**未改动的同版本安装**
（本机是 `D:\Red2\ra2youli`），可以补回来：

```bash
python -m ra2opt seed --from "D:\Red2\ra2youli" --verify
```

`--verify` 会逐个核对 SHA-256 是否等于已知官方版本，不符就拒绝。
**默认不含 `ra2md.ini` / `ra2.ini`**：那两个文件游戏自己会重写，别份安装里通常是出厂
默认值（`GameSpeed=1`），拿它当"原始态"会把玩家设置一起抹掉。确实需要时用
`--include-ini`。

---

## 两个配置档

| 档 | 内容 | 适合 |
|---|---|---|
| `safe`（默认） | cnc-ddraw + `ddraw.ini` + `[Video]` 校准 + 栈 4MB + 兼容性标记 + 启动器。**不动 exe 代码段，也不开 LAA** | 只想要"更不容易崩"，不想动引擎二进制 |
| `perf` | safe + **开 LAA** + `DetailLevel=1` | 想要压"多单位卡顿"和内存崩溃（本机用这个） |

常用开关：`--dry-run`（先看要改什么）、`--keep-display`（保留分辨率/缩放偏好）、
`--no-cddraw`、`--no-registry`、`--multi-cpu`、`--offline`、`--ddraw-zip <包>`。

---

## 验证到什么程度

- ✅ `python -m ra2opt selftest`：**32 项全过**（越界写盘拒绝、PE 补丁后代码段字节不变、
  INI 注释/顺序/GBK/CRLF/BOM 往返、备份→回滚字节级往返、apply 幂等、战役产物零改动、
  `safe` 档只改 4 个字节……）
- ✅ 本机 `ra2youli` 已应用 `perf`：ddraw 7.1.0.0、三个 exe LAA 开 + 栈 4MB
- ✅ **启动冒烟测试通过**：改动后启动 `gamemd.exe` 存活 8 秒未退出（只证明加载器与
  初始化阶段正常，不等于功能验证）
- ✅ **回滚往返验证**：`restore` 后 `gamemd.exe`/`Ra2md.exe`/`Ra2.exe`/`ddraw.dll`/
  `ddraw.ini`/`ra2md.ini`/`ra2.ini` 与原始安装**逐字节相同**，注册表标记还原，
  新建的启动器被删除
- ⚠️ **未做**：进游戏打一局的实际体验（通关节、大规模交战是否真的更流畅）。
  需要玩家实测；不舒服的地方一律 `python -m ra2opt restore` 一键退回。

---

## 代码结构

| 模块 | 作用 |
|---|---|
| `ra2opt/safewrite.py` | 唯一的落盘出口：路径规范化 + 越界拒绝 + 原子替换 |
| `ra2opt/pe.py` | PE32 头读写：LAA、栈/堆保留空间、`.text` 指纹 |
| `ra2opt/inifile.py` | 行级保留的 INI 读写（注释/顺序/大小写/GBK/CRLF/BOM） |
| `ra2opt/backup.py` | 原始快照、变更清单、回滚、`seed` 补快照 |
| `ra2opt/appcompat.py` | HKCU 兼容性标记读写与体检 |
| `ra2opt/cddraw.py` | cnc-ddraw 获取/安装/`ddraw.ini` 调优（含键表校验） |
| `ra2opt/net.py` | 受限下载：https + 主机白名单 + IP 边界 + 重定向复检 |
| `ra2opt/winproc.py` | `CreateProcessW` 封装（无命令行解析，可先设优先级再恢复） |
| `ra2opt/launcher.py` | 启动器生成、启动、冒烟测试、`ddraw.log`/崩溃转储读取 |
| `ra2opt/audit.py` | 只读体检与报告渲染 |
| `ra2opt/optimize.py` | 配置档定义与 apply 编排 |
| `ra2opt/budget.py` | 战役单位预算检查（与 ra2forge 设计 JSON 对接） |
| `ra2opt/cli.py` | 命令行 |

MCP 备选：可参照 `mcp/ra2forge_mcp.py` 的写法把 `audit`/`apply` 也包成 MCP 工具。
