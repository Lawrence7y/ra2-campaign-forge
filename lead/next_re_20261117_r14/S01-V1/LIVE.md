# S01-V1 · 实测值 vs 静态预测对照表

卡号 S01-V1｜目标 `ra2youli\gamemd.exe`（SHA256 73201CC0…F67476，ImageBase 0x400000）｜2026-11-17

## 0. 静态最小定位（步骤 0，全部 `[静态推断]`）

方法：capstone 5.0.7 `skipdata=True` + pefile 节表 VA→file offset；脚本 `work/static_s01.py`，
原始输出 `EVIDENCE/static_entry_disasm.txt` / `static_mainloop_disasm.txt`（250 条指令）/ `static_summary.json`（30 个 call 点）。

| 角色 | 地址 | 取证方式 | 分级 |
|---|---|---|---|
| PE 入口（WinMainCRTStartup） | `0x7CD80F` | `AddressOfEntryPoint=0x3CD80F` + ImageBase | `[静态推断]` |
| 游戏入口（WinMain 等价 / GameMain） | `0x6BB9A0` | CRT 在 `0x7CD8EA` 处 `call 0x6BB9A0`；台账 §881 证其直接调主循环两次（`0x6BE041`/`0x6BE061`） | `[静态推断]` |
| 游戏主循环（Conquer.CPP） | `0x48CCC0`（780 B / 206 指令） | 体内字符串 `D:\ra2mdpost\Conquer.CPP`；内层回边 `0x48CEA8→0x48CE8A` | `[静态推断]` |

### 预期每帧调用点表（步骤 0，每条 `[静态推断]`）

主循环内层体 `0x48CE8A..0x48CEA8`（回边 `0x48CEA8 je 0x48CE8A`），按 call 指令地址排序：

| # | call site | 目标入口 | 名字 / 槽（台账） | 预期相对顺序 | 取证方式 |
|---:|---|---|---|---|---|
| 1 | `0x48CE8A` | `0x55D360` | PerFrameUpdate 每帧更新心跳（帧计数 `0xA8ED84` 在此 +1，台账 §881-1） | 1 | 本卡静态反汇编 + 台账 §881 |
| 2 | `0x48CE93` | `0x55CFD0` | FramePredicate（条件：仅当 #1 返回 al≠0；`0x48CE91 je 0x48CE9C`） | 2 | 本卡静态反汇编 |
| 3 | `0x48CE9C` | `0x48C8B0` | Conquer.CPP 帧绘制/HUD（978 B） | 3 | 本卡静态反汇编 + 台账 §881 |
| 4 | `0x48CEA1` | `0x55CFD0` | FramePredicate（无条件，循环继续判据 `0x48CEA8 je`） | 4 | 本卡静态反汇编 |
| 5 | `0x48CE85` | `0x69BAB0` | 进内层循环前 helper（每外层迭代 1 次，144 B） | 0（循环前） | 本卡静态反汇编 |
| 6 | `0x48CE5D` | `0x7241A0` | 条件前置 helper（②-a 受害例程，87 B；`0x48CE54 je 0x48CE62` 跳过） | 前置（条件） | 本卡静态反汇编 + 台账 §881 |

区分 5 个**不同 callee 目标入口**：`{0x7241A0, 0x69BAB0, 0x55D360, 0x55CFD0, 0x48C8B0}`。
主循环容器 `0x48CCC0` 单列（非 callee）。

## 1. 实测对照

| 预期点（目标入口） | 静态预测 | EIP 分桶（45 s，1,352,400 样本） | 栈返回地址（dense 15 s，94,744 样本） | 判定 |
|---|---|---|---|---|
| `0x55D360` @`0x48CE8A` | 每帧调用、帧计数在此 +1 | region 命中 **4** | `0x48CE8F` **94,739**（几乎每次采样都在其内） | **[已证]** 出现 |
| `0x55CFD0` @`0x48CEA1` | 每帧调用（第 2 处，无条件） | region 命中 **2** | `0x48CEA6` **2** | **[已证]** 出现 |
| `0x55CFD0` @`0x48CE93` | 每帧调用（第 1 处，条件） | 同一 region（无法分site） | `0x48CE98` **0** | **[未证]** 该 call site 本身 |
| `0x48C8B0` @`0x48CE9C` | 每帧调用、帧绘制 | region 命中 **0** | `0x48CEA1` **3** | **[已证]** 出现 |
| `0x69BAB0` @`0x48CE85` | 每外层迭代 1 次 | region 命中 **0** | `0x48CE8A` **0** | **[未证]** |
| `0x7241A0` @`0x48CE5D` | 条件前置 | region 命中 **0** | `0x48CE62` **0** | **[未证]** |
| 容器 `0x48CCC0` | 主循环函数区间 | EIP 命中 0（线程在非 .text） | 返回地址 `0x48CE8F`/`0x48CEA1`/`0x48CEA6` 全落在其区间 `[0x48CCC0,0x48CFCC)` ⇒ 间接证明在执行 | **[已证]** 出现 |

**出现/未出现计数**（5 个不同 callee 目标）：**出现 3**（`0x55D360`/`0x55CFD0`/`0x48C8B0`）；**未出现 2**（`0x69BAB0`/`0x7241A0`）。
容器 `0x48CCC0` 由栈返回地址间接证明在执行。

## 2. 关键数字

| 量 | 实测值 | 复算方法 / 证据 |
|---|---|---|
| 帧率 W1 | **31.2503 fps**（32.000 ms/帧） | `Δframe=375 / Δt=12.000 s`，`t∈[0.002,12.002]` |
| 帧率 W2 | **31.2380 fps**（32.012 ms/帧） | `Δframe=373 / Δt=11.941 s`，`t∈[16.111,28.052]` |
| 帧率 W3 | **31.2268 fps**（32.024 ms/帧） | `Δframe=378 / Δt=12.105 s`，`t∈[31.969,44.074]` |
| 帧率均值 / 整段 | **31.2383 / 31.2472 fps** | 3 窗均值；整段 `Δframe=1404 / Δt=44.932 s`（=32.003 ms/帧） |
| EIP 采样桶总数 | **917** 个不同 EIP 值 / **1,352,400** 样本 | `EVIDENCE/eip_raw_hist.tsv` distinct 行数 / hits 和 |
| top-10 桶占比 | **99.7948%**（其中 ntdll 4 桶 = **99.7152%**） | top-10 `pct_total` 求和；`0x7712890C`=39.1274%、`0x7712837C`=34.7763%、`0x7712869C`=17.1192%、`0x7712A1CC`=8.6923% |
| game .text 内 EIP 占比 | **0.18%**（2,496 / 1,352,400） | `EVIDENCE/live45.log`；`.text=[0x401000,0x7DF38D)` |
| 帧计数自变量 | `0xA8ED84`，`inc` 在 `0x55DE7E` / 写回 `0x55DE81`（在 `0x55D360` 内） | `EVIDENCE/static_framecounter.txt`；台账 §881-1 |

复算脚本：`work/analyze_s01.py`（输出 `EVIDENCE/analysis_summary.txt`）；采样：`work/s01_live_probe.py`（输出 `live45.ndjson`/`eip_raw_hist.tsv`/`stack_sites.tsv`）；密集栈：`work/stack_dense.py`（输出 `stack_dense.ndjson`/`.log`）。

## 3. 顺序验证结论（诚实分级）

- **EIP 分桶单独不能定序**：它是“线程此刻停在哪”的分布，不是时序；且本场景 **99.72% 样本落在 ntdll.dll 的 Sleep/等待路径**（`0x7712890C` 等 4 个地址，模块表 `EVIDENCE/module_list2.txt` 定位在 `ntdll.dll` base `0x770B0000`）。帧限速 `Sleep` 在 `0x55D360` 内 ⇒ 主线程绝大部分时间被钉在 ntdll，per-frame 目标函数在 EIP 样本中几乎不可见。**禁止用 EIP 权重当调用频率**（纪律 10/R14 §5）。
- **栈回溯采样给出调用边（替代观测）**：返回地址出现在栈上，直接证明“该 call site → 该 callee”这段边被执行。实测抓到 3 条边：`0x48CE8F⇒0x55D360`（94,739）、`0x48CEA1⇒0x48C8B0`（3）、`0x48CEA6⇒0x55CFD0`（2）。
- **相对顺序**：静态 call site 地址给出 `0x48CE8A < 0x48CE93 < 0x48CE9C < 0x48CEA1`（+ 回边 `0x48CEA8→0x48CE8A`）；栈样本对其中 3 个 site 提供执行证据。合并判定为 `[静态推断]`，其中 3 个边为 `[已证]`。
- **不能证明的**：单一帧内 4 个调用的**严格时序**（微秒级，只读采样分辨不了；需单步/硬件断点 ⇒ 写线程上下文，卡面禁止）。“每帧每对象调用一次”**无调用计数证据，判 `[未证]`**（纪律 10）。
