# ② 观测通道核验：WER AppHang 现场（2026-10-16 18:25）

**时间**：2026-10-22 02:0x
**性质**：纯离线取证。**未启动任何游戏进程、未写母本、未跑趟。**
**触发**：上一轮 `RC4_POWER_ANALYSIS.md` §5-2 把「复现可被可靠观测」列为 A/B 的前置阻塞，
本件去查这个阻塞的现状。

---

## §0 一句话结论

**找到一份此前未被登记的 gamemd 挂起现场**：WER `AppHang_gamemd.exe` 记录，
事件时刻 **2026-10-16 18:25:04**，`IsFatal=1`，载体路径 `qc111_run_ready\carrier\`，
对应 **QC111 那一趟**。

它同时证明三件事：

1. **WER 通道对 gamemd 是工作的**——引擎挂起/崩溃会被 WER 捕获并留下 `Report.wer`，
   不像 `except.txt` 那样可能被 SEH 绕过。这是「复现可观测」的第一个正面证据。
2. **WER LocalDumps 从未为 gamemd 配置过**（14 个子键里没有 gamemd）⇒ 上一轮记的
   「WER LocalDumps 不生效」要改口径：**不是不生效，是根本没配**。配上就有 dmp。
3. **这趟挂了约 6 分钟无人发现**：18:19 trip 结束、18:21:55 watcher 超时、
   18:22 forensics 采集时 `wer.gamemd_dirs` 还是空、18:25:04 才判挂起。
   ⇒ **harness 的观测窗口在挂起判生之前就关了**。

---

## §1 现场全貌

### §1.1 WER 记录本身

| 字段 | 值 |
|:--|:--|
| 目录 | `C:\ProgramData\Microsoft\Windows\WER\ReportArchive\AppHang_gamemd.exe_fe8cb8e8…8997` |
| `EventType` | **`AppHangB1`**（挂起，**不是** `AppCrash`） |
| `EventTime` | `134366199044925775` → **2026-10-16 18:25:04.492**（本地） |
| `NsAppName` | `gamemd.exe` |
| `OriginalFilename` | `Sun.exe`（引擎内部名） |
| `AppPath` | `…\lead\qc111_run_ready\carrier\gamemd.exe` |
| `IsFatal` | **1** |
| `Hang Signature` | `5408` = `0x1520` |
| `Hang Type` | `134217728` = **`0x8000000`** |
| `LoadedModule` | **106 个**（完整清单在案） |
| `Report.wer` 大小 | 53,216 B，UTF-16LE，255 行 |

事件日志同一时刻两条：`Application Hang` **ID 1002**（"程序 gamemd.exe 版本 1.0.1.1
停止与 Windows 交互并已关闭"）+ `Windows Error Reporting` **ID 1001**
（`AppHangB1`，P1–P5 = `gamemd.exe / 1.0.1.1 / 3bdf544e / 5408 / 134217728`）。

### §1.2 与 QC111 那一趟的时间对齐

| 时刻（本地） | 事件 | 来源 |
|:--|:--|:--|
| 18:11:37 | 建载体（410 件） | `QC111_carrier_setup.json` mtime |
| 18:11:48 | 零写基线 T0（634 文件） | `QC111_zero_T0.json` |
| 18:13:55 | watcher 取得句柄 | `QC111_watcher_final.jsonl` |
| 18:19:21 | trip1 结束（91 采样，`first_zero_i=None`，`except_delta=0`） | `QC111_trip1.log` |
| 18:21:55 | **watcher 8 分钟窗口超时，进程仍活**（`exit_code=259` = STILL_ACTIVE 哨兵） | `QC111_watcher_final.jsonl` |
| 18:22:14 | forensics 采集 → **`wer.gamemd_dirs: []`**（此时还没有） | `QC111_forensics.json` |
| **18:25:04** | **WER 判挂起（AppHangB1）** | `Report.wer` EventTime |
| 18:25:10 | WER 上报 | `Report.wer` UploadTime |
| 18:26:52 | 卡面写 `status=DONE` | `QC111_RUN_READY.json` |

**★ 关键时序**：forensics 在 **18:22:14** 采，挂起在 **18:25:04** 才发生——
**forensics 采集早于挂起判定 2 分 50 秒**。所以 `wer_new_gamemd_dirs: []` 当时是**真话**，
但它随后被事件推翻：**这趟最终是挂了**，只是卡面在 18:26 写 DONE 时没回头复查 WER。

### §1.3 卡面的自我描述与实际的偏差

`QC111_RUN_READY.json` 写：

```
"answer": "无法判定（本趟无 0x0 帧、进程全程存活 ⇒ 未复现 burst_09 那一刻）"
"exited_after_watcher_window": true
"still_alive_at_trip_end": true
"except_txt": { "delta_bytes": 0, "matches_qc104_baseline": true }
"wer_new_gamemd_dirs": []
```

`still_alive_at_trip_end=true` 和 `except_txt.delta_bytes=0` **都是真的**，
但卡面据此推的「进程全程存活」**不成立**——它在 18:25 被 WER 判挂起并"已关闭"（ID 1002 原文）。
这正是 **§312「`except.txt` 零新增不得单独作为未崩溃判据」的第二个独立实例**：
上一次是 E1b/E1c（WER 接管后 SEH 无机会写文件），这一次是**挂起走了 AppHang 通道，
根本不进 SEH，也不写 `except.txt`**。

---

## §2 这条现场是不是 RC-4？

**结论：不能认定为 RC-4，也不能排除。归为「未归族」（unclassified）。**

### §2.1 支持它是 RC-4 的迹象

- RC-4 的规格明确写「表现为**挂留而非崩溃**」（`RC4_HARDEN_SPEC.md:39`，
  "上游 6 局同路径**未复现**（1/6 单发），表现为挂留而非崩溃"）。
  这条现场的形态（AppHang、进程不退出、需外部终止）**逐字吻合**。
- 这趟跑在载体里（`qc111_run_ready\carrier\`），且 WER 模块表第 54 项就是
  载体内的 **`ra2render.dll`** —— 是带注入的局，不是 Arm A 基线。

### §2.2 反对直接认定的理由（三条硬缺口）

1. **没有 Eip**。AppHang 记录里**没有任何指令地址**——`Sig[]` 只有
   `Hang Signature=5408` / `Hang Type=0x8000000`，没有 RC-4 的 `00724737`。
   没有 Eip 就无法按 §682 的六项判别器判族。
2. **没有 dump**。WER LocalDumps 从未为 gamemd 配置（§3），
   所以这次**没留下任何内存镜像**，无法事后补读 `[0x887368]`。
3. **挂起与崩溃是两种失效**。`Hang Type=0x8000000` 的语义是"UI 线程 5 秒未处理消息"，
   而 RC-4 是 AV（`0xC0000005`，读 `0x250`）。**挂起可能只是"消息泵停了但没崩"**，
   与"空 this 解引用"未必同源。把它当 RC-4 是**推断，不是证据**。

### §2.3 唯一能把它变成证据的动作（待用户在场）

`[0x887368]` 在挂起进程里是 0 还是非 0，**一次 RPM 读就能定**：
- 若 **0** ⇒ 窗口已销毁、单例已置 0 ⇒ **与 RC-4 的触发前提一致**，强支持。
- 若 **非 0** ⇒ 单例还活着 ⇒ 挂起另有原因（消息泵/音线程/渲染线程），与 RC-4 无关。

**但这需要进程还在**——它 10-16 就已经结束了。⇒ **这次无法补读，只能登记为未归族**。

---

## §3 WER LocalDumps：口径更正 + 可操作性

### §3.1 上一轮的口径要改

`l1-baseline-trip-popup-block` 记忆里写「WER LocalDumps 不生效（非托管路径）需 procdump」。
**本次实测把这个说法拆成两半**：

| 说法 | 实测 | 判定 |
|:--|:--|:--|
| 「WER 对 gamemd 不工作」 | `AppHang_gamemd.exe` 记录**存在**（10-16） | ❌ **不成立**——WER 通道是通的 |
| 「WER LocalDumps 不生效」 | `LocalDumps` 有 **14 个子键**，**没有任何 gamemd 子键**；根键 `ValueCount=0` | ⚠️ **要改成「从未配置」**——不是机制失效，是没人配 |

`LocalDumps` 现有 14 个子键全是华硕/NVIDIA/微信等厂商预置
（`ArmouryCrate.exe`、`nvcontainer.exe`、`Weixin.exe` …）。
**`Test-Path …\LocalDumps\gamemd.exe` = `False`。**

### §3.2 这意味着什么

WER 默认行为是**只上报、不落盘**（`LocalDumps` 无默认值 ⇒ 不产生 dmp）。
所以历史上所有 gamemd 的 WER 记录（含这条 AppHang）**都没有 dmp**。
上一轮说"需要 procdump"方向对，但**不是唯一解**：

| 方案 | 改动 | 优点 | 缺点 |
|:--|:--|:--|:--|
| **A. 配 `LocalDumps\gamemd.exe`** | 加一个注册表子键（`DumpFolder` / `DumpType` / `DumpCount`） | 系统级、不侵入 harness、对 AppCrash **和** AppHang 都生效 | 需管理员；**改变系统状态**（须用户授权）；DumpType=2 全内存 = 每份几百 MB |
| **B. procdump -e -ma -w gamemd.exe** | 需先装 Sysinternals | 不动注册表、可按趟启停 | **当前机器上没装**（全盘搜无结果）；`-w` 常驻监听需随趟管理 |
| **C. 只读 WER 记录（现状）** | 零改动 | 已证明能拿到 AppHang/AppCrash 的**存在性 + 时间 + 模块表** | **拿不到 Eip、拿不到内存** ⇒ 定不了族 |

**★ 推荐 A**，理由：① 这次 AppHang 已证明 WER 能看到 gamemd；② A 只需一个子键就能把
"看得到"升级为"抓得住"；③ 它同时对 AppCrash 生效，而 ② 的 RC-4 和 RC-1 都是 AV，
**未来所有趟都能受益**。但 A 改系统状态，**须用户授权**，且要选 `DumpType`：
`1`=mini（小、够看栈和寄存器）、`2`=full（含堆，能查 `[0x887368]` 指向的对象内容）。

### §3.3 顺带发现：harness3 完全没有 WER 检测

```
grep -c "ReportArchive"  qc151_trip.harness3.py  → 0
grep -c "AppHang"         qc151_trip.harness3.py  → 0
grep -c "wer_new_gamemd_dirs" qc151_trip.harness3.py → 0
```

`wer_new_gamemd_dirs` 只存在于 **QC111 那一代脚本**（`QC111_forensics.json` 有这个字段），
**没有继承到 harness3**。⇒ 现行 harness3 的每趟收尾**不查 WER**，
所以"这趟有没有挂/崩"只能靠 `except.txt`（已知不可靠，§312）和进程退出码。
**这是 A/B 观测链上一个真实的缺口**，比趟数设计更靠前。

---

## §4 ★★ 顺带发现：载体隔离存在注册表旁路（**已定根因**）

WER 的 106 项模块表里，**第 58 项是载体外路径**：

```
LoadedModule[58] = D:\Red2\Mental Omega\Blowfish.dll
```

而 QC111 的载体清单（`QC111_carrier_setup.json`，410 件）里**明明有 `Blowfish.dll`**，
且 `byte_identical_all: True`（复制完全正确）。

### §4.1 根因：注册表 `InstallPath` 指向载体外

```
HKLM\SOFTWARE\WOW6432Node\Westwood\Yuri's Revenge
    InstallPath = D:\Red2\Mental Omega\RA2MD.EXE      ← ★ 指向载体外
HKLM\SOFTWARE\WOW6432Node\Westwood\Red Alert 2
    InstallPath = D:\Red2\Mental Omega\RA2.EXE
```

gamemd 启动时读这个键，**据此拼出绝对路径去加载资源**。载体目录只影响
「按相对名/搜索路径」的加载；**凡走 `InstallPath` 的加载都绕开载体，直取 `D:\Red2\Mental Omega\`**。

### §4.2 关键区分：不是"污染"，是"同一个文件"

三处 `Blowfish.dll` 的 sha256 **完全相同**：

| 位置 | sha256 |
|:--|:--|
| 载体外 `D:\Red2\Mental Omega\Blowfish.dll` | `68e4896b1fc0e5828162fbefe1bfb2cc7a1dd4ac34957b5b0194550e36fe7992` |
| 载体清单记录（`dst_sha`） | `68e4896b1fc0e5828162fbefe1bfb2cc7a1dd4ac34957b5b0194550e36fe7992` |
| `ra2youli\Blowfish.dll` | `68e4896b1fc0e5828162fbef…`（同前缀，225,331 B） |

⇒ **这不是外来代码注入**。载体里那份和载体外那份是同一个二进制。
所以**不构成"跑的不是我复制的那份代码"这种污染**。

### §4.3 但它仍然破坏「载体隔离」这个前提

真正的问题是**隔离的边界在哪**：

| 被隔离住的 | 没被隔离住的 |
|:--|:--|
| 载体目录内的文件（复制正确、哈希自证） | 凡经 `InstallPath` 解析的资源 |
| 相对路径/搜索路径命中的 DLL | **可能包括 .MIX / .CSF / 地图 / 音频**等 |

⇒ 一趟里实际读到的资源，**可能一部分来自载体、一部分来自 `D:\Red2\Mental Omega\`**。
载体哈希自证只证明了「复制正确」，**没有证明「实际加载的是哪一份」**。

### §4.4 对既有结论的影响面（诚实评估）

| 结论 | 是否受影响 |
|:--|:--|
| `gamemd.exe` 本体哈希断言 | ❌ 不受影响（`LoadedModule[0]` 明确是载体路径） |
| `ra2render.dll` 注入目标 | ❌ 不受影响（`LoadedModule[54]` 是载体路径） |
| 载体件数与路径门禁 | ❌ 不受影响 |
| **A/B 对拍的可比性** | ⚠️ **受影响**：两臂都走同一 `InstallPath`，**差异被同样引入**，所以相对比较仍成立；但**绝对数值**混入了载体外资源 |
| **"这趟跑的是我复制的那份游戏"** | ⚠️ **不严格成立** |

**结论方向**：这不推翻任何已有数据，但它是**所有真机结论的共同前提**上的一道裂缝，
必须登记并给出检测手段。

### §4.5 建议的检测与修法

| 方案 | 做法 | 代价 |
|:--|:--|:--|
| **A（检测，推荐先做）** | 趟收尾枚举本进程模块表，**断言全部落在载体目录内**，越界项写进报告 | 纯离线，不改进程行为 |
| **B（隔离）** | 建载体时把 `InstallPath` 临时改指向载体（或建沙箱注册表视图） | **改系统状态**，须授权；且可能与 Mental Omega 的安装冲突 |
| **C（记录）** | 不改，只在每趟报告里记下 `InstallPath` 实际值 | 零成本，但隔离问题留着 |

**★ 建议 A 先行**：它不改任何状态，只把"哪些模块来自载体外"变成可观测事实。
等 A 跑几趟、看清越界面有多大，再决定要不要 B。

### §4.5b 方案 A 已实现并实测（`wer_module_isolation_audit.py`）

只读检测器已落地，直接从 `Report.wer` 的模块表判隔离边界。

```
$ python wer_module_isolation_audit.py --scan-archive --carrier <载体目录>
找到 1 份 gamemd WER 记录
  事件类型   : AppHangB1
  发生时刻   : 2026-10-16 18:25:04
  模块总数   : 106
    载体内   : 6
    系统     : 99
    ★ 越界   : 1
  载体内模块：
    [  0] …\qc111_run_ready\carrier\gamemd.exe
    [ 40] …\carrier\WSOCK32.dll
    [ 42] …\carrier\xyr.dll
    [ 44] …\carrier\DDRAW.dll
    [ 52] …\carrier\binkw32.dll
    [ 54] …\carrier\ra2render.dll      ← 注入目标确实来自载体
  ★ 越界模块：
    [ 58] D:\Red2\Mental Omega\Blowfish.dll  (存在)
```

**★ 判别力验证（防止"恒返回同一结果"的假绿）**：

| 测试 | 构造 | 越界数 | EXIT |
|:--|:--|--:|--:|
| 真样本 | 原始 WER 记录 | **1** | **1** |
| **肯定对照** | 把越界那行改写成载体路径后重跑 | **0** | **0** |

⇒ 检测器对"越界"有真实判别力，不是恒真也不是恒假。
（`EXIT=0` 表示无越界，`EXIT=1` 表示发现越界，`EXIT=2` 表示输入错误。）

**★ 一个已知口径**：载体基准若给成**上级目录**（如仓库根），载体内的 6 个模块仍会被
判"载体内"（它们是仓库的子目录）。这是前缀匹配的应有行为，不是缺陷——
判断隔离要按**趟载体目录**给基准，不能给上级。

### §4.6 诚实边界

- 这条 AppHang 是 **QC111 那一代脚本**跑的，**不是现行 harness3**。两者载体构造方式可能不同。
- 我只看到**一次**样本。不能断言「每次都越界」，只能说「至少这一次越界了」。
- **我只读了注册表的 `InstallPath` 值**，没有读 `D:\Red2\Mental Omega\` 的目录内容
  （除 `Blowfish.dll` 的哈希与 `gamemd.exe` 的存在性）。
- 越界到 `.MIX`/`.CSF` 等资源只是**由机制推断**（`InstallPath` 是通用解析根），
  **本次 WER 记录只直接证实了 `Blowfish.dll` 一项**。

---

## §5 对 ② 的三条直接结论

1. **「复现不可观测」这个前置阻塞，有一半可以解**：WER 通道已被证明能看到 gamemd 的
   挂起与崩溃。配上 `LocalDumps\gamemd.exe`（方案 A）就能拿到 dmp ⇒ 能补读 `[0x887368]` ⇒ 能定族。
   **这需要用户授权改注册表。**
2. **harness3 缺 WER 检测**（§3.3），这是纯代码缺口，**可以离线补**，不依赖用户裁决。
   补法：趟收尾时扫 `WER\ReportArchive` 与 `ReportQueue` 的 `*gamemd*` 目录，
   记录新增项与 `EventTime`，写进 `except_set_diff` 同级字段。
3. **RC-4 的"表现为挂留"这句话，现在有了一个真实例证**（§2.1），
   但也暴露了它的观测盲区：**挂起不留 Eip、不留 dmp，除非提前配置**。
   所以「改 `WM_CLOSE` 就能测 RC-4」这个方向，**还缺"怎么把挂起变成可判族的证据"这一步**。

---

## §6 待裁（新增，接上一轮四项）

| # | 事项 | 为什么现在要裁 |
|:--|:--|:--|
| 5 | **是否配 `LocalDumps\gamemd.exe`** | 这是 ② 能否定族的前提；改系统状态须授权；要选 `DumpType=1/2` |
| 6 | **是否给 harness3 补 WER 检测** | 纯离线可做，但不改则在 A/B 里"挂起"这一整类失效不可见 |
| 7 | **载体隔离旁路（§4）怎么处理** | `InstallPath` 指向 `D:\Red2\Mental Omega\`，是**所有真机结论的共同前提**；建议先做检测（方案 A，零改动） |

### §6.1 本轮不需要裁决就能做的（离线）

- 给 harness3 补 WER 扫描（#6 的**实现**可以离线写，**启用**仍算改动，须走补丁副本制）
- 写「收尾模块表断言」的检测脚本（#7 方案 A 的实现）
- 两者都只在补丁副本上做，母本零改动

---

## §7 复跑

```bash
# WER 记录（只读）
python - <<'PY'
p = r'C:\ProgramData\Microsoft\Windows\WER\ReportArchive\AppHang_gamemd.exe_fe8cb8e85f99eac6a79493a939823651f5d56_72100cd1_8c72158d-ece7-4c14-a391-580b6e5a8997\Report.wer'
t = open(p, 'rb').read().decode('utf-16-le')
for line in t.splitlines():
    s = line.strip()
    if s.startswith(('EventType=', 'EventTime=', 'IsFatal=', 'Sig[', 'LoadedModule[')):
        print(s)
PY

# LocalDumps 现状（只读）
powershell -NoProfile -Command "Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps\gamemd.exe'"
```

---

## §8 ★ 第二轮加固：AppCrash 支持与 Sig 索引陷阱

> 追加于 2026-10-22 04:2x。上一版检测器**只能读 AppHang**，而 ② 关心的 RC-4 是 AV（`c0000005`），
> 走的是 **AppCrash** 记录，签名字段完全不同。本节补上这块并登记一个真实陷阱。

### §8.1 ★★ 陷阱：AppCrash 的 `异常代码/异常偏移` 索引**不固定**

对本机 25 份 AppCrash 记录逐份实测，`Sig[i].Name` 的索引布局有三种：

| 布局 | 份数 | `异常代码` 索引 | `异常偏移` 索引 |
|:--|--:|--:|--:|
| 常见 | **17** | `Sig[7]` | `Sig[6]` |
| 另一变体 | **6** | `Sig[6]` | `Sig[7]` |
| 无此两项 | **2** | — | —（Windows Installer 的 MSI 型记录） |

⇒ **按索引硬编码必然读错**（17:6 的多数派反而不是全部）。
必须**按 `.Name=` 配对取值**，不能按 `Sig[N]` 的数字位置取。

**这条的普适意义**：WER 的 `Sig[]` 是"名称/值"的**有序对列表**，
索引只是排列位置，**语义由名称承载**。任何按索引读 WER 的代码都不可靠——
包括未来要给 harness 写的 WER 检测（#6）。

### §8.2 检测器已按名配对重写

`parse_report()` 改为：先扫一遍建 `名称 → 值` 映射，再按**名称**取
`异常代码 / 异常偏移 / 故障模块名称 / 应用程序版本 / 应用程序时间戳`。
`Hang Signature / Hang Type` 同样按名取，与 AppCrash 字段互不干扰。

**全量回归（36 份记录，4 种 EventType）**：

| EventType | 份数 | 异常代码解析 | 故障模块解析 |
|:--|--:|:--|:--|
| `APPCRASH` | 7 | ✅ 全部 `c0000005` / `c000041d` | ✅ `tipskins.dll` / `System.dll` / `StackHash_*` |
| `BEX64` | 14 | ✅ 全部 `c0000409` / `c0000005` | ✅ `koffi.node` / `bt-battery-bar` / `CrashRpt1500.d` |
| `AppHangB1` | 1 | —（无此字段，正确留空） | —（正确留空） |
| `StoreAgentDetected` | 14 | —（无此字段，正确留空） | —（正确留空） |

⇒ **四种类型全部正确分型，无串味**。AppHang 记录**不会**误读成 AppCrash，
反之亦然。

### §8.3 新增能力：`--app` / `--all`

```
--app <名字>   # 默认 gamemd；按目录名过滤
--all          # 扫全部记录（回归用）
```

### §8.4 一条顺带观察：`StackHash_*` 是"符号不可得"的占位

25 份 AppCrash 里有 4 份故障模块写作 `StackHash_bae8…` / `StackHash_d9df…`。
这是 WER 在**拿不到有效模块名**时的占位符（栈哈希）。
⇒ 对我们的意义：**WER 记录里的"故障模块"不一定是真模块名**，
若未来 gamemd 崩溃落在 `StackHash_*` 上，那这条记录对定模块**零信息量**，
只能靠 dmp。这是"必须有 dmp"的又一个理由（对应待裁 #5）。

---
