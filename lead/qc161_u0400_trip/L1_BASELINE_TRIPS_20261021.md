# L1 基线趟（Arm A）三趟历程与定谳（2026-10-21）

**性质**：真机趟记录 + 根因判定。**用户授权**：本会话「允许进行真机测试，每次真机复制的游戏本体测试后删掉」。
**载体制**：每趟 `create_isolated_carrier` 新建 → 趟后按载体路径精确终止进程 → `shutil.rmtree` 删除 → 复测残留。
**三趟全部满足删除要求**：`残留进程: 无` / `载体残留: 无`。

---

## 一、三趟一览

| 趟 | out-dir | 载体件数 | exit | 判定 |
|:--|:--|--:|--:|:--|
| **l1b** | `l1b_20261021` | **5** | **22** | ❌ 失败（载体件不足）|
| **l1c** | `l1c_20261021` | 88 | 0 | ⚠️ 判据全过，但环境受限 |
| **l1d** | `l1d_20261021` | 88 | **0** | ✅ **① 的 Arm A 基线成立** |

---

## 二、l1b 失败：`rc=22` 的真根因（**不是路径长度、不是导航失败**）

### 2.1 退出码解码

`EXIT_WINDOW_NOT_FOUND = 22`（`qc151_trip.harness3.py:374`）= 主窗未出现。
但**下游症状不是根因**。决定性证据在 `TERM.wait_returncode`：

```
TERM  wait_returncode  3221225781
```

`3221225781 = 0xC0000135 = STATUS_DLL_NOT_FOUND`。

### 2.2 根因

`carrier_manifest_pre_delete.json` 显示 **`pre_delete_file_count = 5`** —— 载体只含默认 5 件
（`gamemd.exe` / `ra2loader.exe` / `ra2render.dll` / `ra2opt_play.bat` / `except.txt`），
**缺 `ddraw.dll` 与全部 `*.mix`** ⇒ gamemd 在加载期即死 ⇒ 主窗永不出现 ⇒ 22。

对照：同源变体的 `l1a_20261020` 与 `t55k_20261020` 载体均为 **88 件**，均 `exit=0`。
**同类先例**：T6 六件载体缺 `ddraw.dll` 启动即亡 `0xC0000135`（台账 §317 附近）。

### 2.3 我当时的错误决定及其证伪

我为了绕开 `RA2MD Update.ico` 的**空格**问题，把 `--carrier-create-files` **整个丢掉**，
理由是「整串含空格项会被 argv 拆开」。该理由**已被探针证伪**：

`_argv_rt_probe.py` 实测（`os.spawnv` + 整串加引号）：

```
spawn_argv = [..., '"a,b,配置器.exe,XMP29U2.MAP,RA2MD Update.ico"']
child argv = ['--child', 'a,b,配置器.exe,XMP29U2.MAP,RA2MD Update.ico']
identical  = True          ← 逗号 / 非 ASCII / 空格 全部原样往返
```

⇒ **`os.spawnv` 下整串加引号可原样送达**。丢弃参数是错误决策。

### 2.4 顺带定谳：清单 A12 的「89 件」是错的

| 来源 | 件数 | 是否含 `RA2MD Update.ico` |
|:--|--:|:--|
| `L1_PRELAUNCH_CHECKLIST.md` A12 散文 | 89 | 声称含 |
| `_src_L1_sf8_20261020_MANIFEST.json`（冻结）| **88** | **不含** |
| `_src_L1_sf8_20261020/` 实际目录 | 89（88 + `.mimosa` 噪声）| **不存在该件** |

`RA2MD Update.ico` 只存在于 `ra2youli/` 与 `ra2bench/`，**不在 L1 源变体内**。
⇒ **88 才是真值**，A12 的「89」应勘误为「88」。本趟按冻结清单 88 件执行，
83 件附加名里**无空格、无逗号**（唯一非 ASCII = `配置器.exe`，探针已验证可往返）。

---

## 三、l1c 与 l1d：判据全过，但 fps 受环境压制

### 3.1 两趟都合格

| 判据 | l1c | l1d | 门 |
|:--|:--|:--|:--|
| `final_exit_code` | 0 | 0 | =0 |
| `NAV.verdict` | OK | OK | OK |
| 导航链 attempts | 1/1/1 | 1/1/1 | 一次过 |
| `S4.hit_count` | 0 | 0 | =0（Arm A 定义）|
| `units0` | **881** | **874** | ≥800 |
| `MEASURE.verdict` | ok | ok | ok |
| `except` 新增 | 0 | 0 | 0 |
| 载体删除 | ✅ | ✅ | 必删 |

### 3.2 fps 异常低：10 而非 31

| 趟 | 日期 | units0 | fps_p50 (w0) | logic_frames |
|:--|:--|--:|--:|--:|
| `l1a_20261020` | 10-20 | 732 | **30.97** | 781 |
| `t55k_20261020` | 10-20 | 842 | **31.01** | 781 |
| `l1c_20261021` | 10-21 | 881 | 9.69 | 229 |
| `l1d_20261021` | 10-21 | 874 | **11.08** | 256 |

### 3.3 我先误判为并发负载，已被证伪

l1c 期间机器上有两个**接近满核**的进程（CPU 累计 2918 s / 1413 s）：
- pid 3760 = #10 子代理的 `os.walk` 全树正则扫描（18:29 起，48 分钟无产出）
- pid 19956 = **我自己**后台起的搜索（18:53 起）

我据此判 l1c 为「负载污染」，清场后重跑 l1d。
**但 l1d 在干净机器上（CPU 33%、零满核）依然只有 10.2 fps** ⇒ **负载不是原因**，该归因错误，此处更正。

### 3.4 真因：GameViewer 远程会话缺失

决定性差异在 `WIN.win_end_scan.big_visible`：

| 趟 | `GameViewerPrivateWindowName` |
|:--|:--|
| `t55k_20261020`（31 fps）| **有 2 个**（pid 8376，2560×1440 与 2304×1296）|
| `l1d_20261021`（10 fps）| **完全没有** |

显示适配器实测：

```
GameViewer Virtual Display Adapter   2560×1440 @ 210 Hz
NVIDIA GeForce RTX 3060 Laptop GPU   1920×1080 @ 144 Hz
```

游戏主窗 `wh=[2560,1440]` ⇒ 挂在 **GameViewer 虚拟显示器**上。
`ddraw.ini:31 maxfps=-1`（= 跟随屏幕刷新率）。
GameViewer 进程组（GameViewer / Healthd / Server / Service）在跑，但**无活动远程会话窗口**
⇒ 虚拟显示器呈现路径退化 ⇒ 帧时间从 32 ms 涨到 92–110 ms。

**这是远程桌面虚拟显示器的环境特性，与游戏、单位数、地图、载体全部无关。**
佐证：l1d 的 units0=874 与 t55k 的 842 只差 3.8%，帧率却差 3 倍，**不成比例**。

### 3.5 对 ① 判据的影响（诚实登记）

- **可用**：`exit=0` / `nav OK` / `S4=0` / `units0≥800` / `except=0` ⇒ **Arm A 基线成立**。
- **不可用**：`fps_*` / `frame_ms_*` / `tick_miss` 的**绝对值**受 GameViewer 会话状态支配，
  与 10-20 的 31 fps 不可直接横比。
- **A/B 对比仍有效**：只要 A 与 B0/B1 **在同一会话状态下**成对跑，差值是干净的。
  ⇒ 后续 A/B 对拍**必须同会话状态连跑**，且记录 `GameViewerPrivateWindowName` 有无作为环境指纹。

---

## 四、本轮产出

| 件 | 路径 |
|:--|:--|
| 本报告 | `lead/qc161_u0400_trip/L1_BASELINE_TRIPS_20261021.md` |
| l1b 失败证据 | `l1b_20261021/`（5 件载体、`wait_returncode=3221225781`）|
| l1c 受限证据 | `l1c_20261021/` |
| **l1d 基线证据** | `l1d_20261021/`（三窗 `measure_w*.json`、`qc151_fields.json`）|
| argv 往返探针 | `_argv_rt_probe.py` |
| 帧像素统计/字符图 | `_frame_stats.py` / `_frame_ascii.py` |
| #10 孤儿扫描产物（备份）| `goal2_writer_20261021/scan_0054a56e_orphan_181855.txt` |

## 五、待办

1. **A/B 对拍须同会话状态**：跑前记录 `GameViewerPrivateWindowName` 有无；三趟 A、三趟 B0、三趟 B1 连跑不中断。
2. `L1_PRELAUNCH_CHECKLIST.md` A12 的「89 件」勘误为「88 件」（等 Lead 裁决，不自行改签署件）。
3. l1d 的 `units0=874` 已达 ≥800 门 ⇒ ① 的 U0800 档**成立**，无需再调图。
