# EQUIVALENCE_RESULT.md · W45 / B 线（RE-N09）真机双轨结果

> 卡：`W45_b_line_equivalence`｜run_id `NEXT_RE_20261112_R02`｜2026-11-13 20:35–21:31（Asia/Shanghai）
> 执行：W45 子代理｜**A 半规格**：`EQUIVALENCE_SPEC.md`（先完成、先落盘）｜**B 半**：本文件
> 写域：仅 `lead\next_re_20261112_r02\W45_b_line_equivalence\`；真 `ra2youli\` 全程只读
> 原始证据：`out\w45_dual_track.ndjson`、`out\<tag>_result.json`、`out\analysis.json`、`out\screen_*.png`、`out\save_*.SAV`、`out\cmd_*.log`
> 复跑：`tools\w45_dual_track.py --phase all`（当前 `--arms` 默认 `A1,A2,B1`）＋ `tools\w45_analyze.py`

---

## 0 · 一句话结论

> **总判定：`[本次实测]` 无法判定。**
> 四趟真机（A1/A2 不装包、B1/B2 装 v13 包，各 75 s 稳定局内、6 ms 采样）在
> **局内 Esc 菜单控件集合 / 控件可见性**、**只读 RPM 字段** 上等价；
> `verify` 安装态门禁通过；但**局内定时器**与**存档文件字节**两项因
> **同臂噪声基线本身不成立**而判「不可判」。按规格 §3.7，只要有一项不可判，
> 总判定只能是「无法判定」，不得写成「行为等价」。

**明确不写的三句话**：
- ❌「v13 回归 82/82 全绿 ⇒ 行为等价」
- ❌「游戏没崩 / 四趟都进了官方战役 ⇒ 行为等价」
- ❌「`verify` exit 0 ⇒ 行为等价」

---

## 1 · 执行与纪律自证（[本次实测]）

| 项 | 结果 |
|---|---|
| 桌面预检（独立 + 每趟 WMI 启动后 ≤2 s） | **通过**：`WinSta0` / `Default` / `Default`；独立探针 EnumWindows 377/19、EnumChildWindows 首 8 窗 25、`ImageGrab` OK 2560×1440；四趟逐趟 step0 均 `pass=true`（EnumWindows 390–435 / 可见 19–22）`out\desktop_precheck.json` |
| 单实例锁 | 开工前 `owner=lead`（19:57:51）；每趟取 `owner=w45`；**收尾还原 `owner=lead`**（21:30:36，已复核文件内容） |
| 启动方式 | 四趟均 WMI `Invoke-CimMethod Win32_Process Create`；`pre_launch_guard` 每趟 `gamemd=[]` |
| 禁止项 | 仅 `OpenProcess(PROCESS_VM_READ\|PROCESS_QUERY_INFORMATION)` + `ReadProcessMemory`（只读）、`EnumWindows/EnumChildWindows`、`PostMessageW(BM_CLICK)`、`keybd_event`、`mouse_event`、`ImageGrab`；**未**注入、未 attach 写内存、未改 exe/dll、未下断点/挂线程 |
| `finally` 顺序 | WM_CLOSE → `taskkill` → `taskkill /F` → 残留 0 → 逐字节还原 `RA2MD.INI`/`ddraw.ini`/`RA2MD.INI.benchbak`/`BATTLEMD.INI` → 移除投放物（本趟新建 `.sav`）→ `kind=meta_end` → 还锁；四趟 `restore_all_match=true`、`residual=[]` |
| 还原集合 | **不含** `ra2forge_install.json` / `.seal`（安装事务结果，W44 工具缺陷 A 教训） |
| 真目录零改动 | PRE/POST 全树逐文件：`647 / 1,989,215,270 B / 277`；`added=0 removed=0 changed=0`，`IDENTICAL_TREE=True`；四哈希 PRE=POST=基线（`REAL_DIR_PROOF.txt`） |
| 预算 | 总 ≈56 min ≤100 min；单趟 128–166 s ≤10 min |
| 残留 | `Get-Process gamemd` = **0**；`final_sweep` 残留 `[]` |

### 1.1 两轮作废的驱动缺陷（照实写，原始证据已归档）

| 轮次 | 缺陷 | 处置 |
|---|---|---|
| Round 1 | `install --json` 不存在 ⇒ B1 **exit 2、包根本没装上**（`battle_cnt=14`）；A2 Esc 键丢失 ⇒ 无存档 | 全部证据归档 `out\round1_defective\`（15 文件）；不作为判据 |
| Round 2 | B1 首次装包成功（`battle_cnt=15`）但**卡在官方 SOV01 任务简报屏** 90 s（`frame=0`），截图 `out\screen_B1_on_error.png` 已人工读图为「軍事行動:時空轉移」简报屏，非崩溃/非错误框 | 归档 `out\round2_defective\`；判定为 **输入投递噪声**（`VK_RETURN` 未送达），非改造效应——Round 3 用 `force_foreground` 重断言 + 重试后 B1/B2 均正常进图 |
| Round 3 | **权威跑**：A1/A2/B1/B2 四趟全部 `phase_reached=true`、`errors=[]` | 本文件全部结论只引用 Round 3 |

> 这不是「挑好看的一轮」：Round 1/2 的完整 ndjson + 每趟 result.json + 命令日志都留在 `out\round*_defective\`，可复核。Round 2 的 B1 简报屏现象也在 §5 作为「候选差异被同臂/重复排除」的实例列出。

### 1.2 对照臂与自变量（[本次实测]）

| 臂 | 沙箱起点 | 唯一自变量 | 趟数 |
|---|---|---|---|
| A1 / A2 | 同一份 `sandbox_base`（`ra2youli` 只读副本 → 两臂一致地 `uninstall` 掉既存 v0.3 旧包 → `verify exit 0 / manifest_present=false`）；PRE 清单 647/1,989,215,270/277 | 无 | 2 |
| B1 / B2 | **同一份** `sandbox_base` 的逐字节副本 | 额外 `python -m ra2forge install --package out\pkg_v13\W45 Equivalence Probe --game <sandbox>`（v13 工具链构建，默认开关全关） | 2 |

- v13 包产物（固定 design `designs\w45_two_missions.json`）：`BATTLEMD98.INI`（376 B，`15=RA2F1`）、`W45A1.MAP`(4502 B)、`W45A2.MAP`(4433 B)、`expandmd98.mix`(8969 B)；`install_rc=0`，`verify_pre_rc=0` 且 `manifest_present=true`。
- **k=1 事先声明**：`BATTLEMD98.INI [Battles] 15=RA2F1` ⇒ 包只登记 1 个 battle，`k` 由包字节算出，非事后拟合（规格 §2.5 W2）。
- 两臂**同输入脚本、同采样 cadence、同 RPM 地址集、同截图几何、同环境**；官方入口不劫持 `[SOV1]`：`GUI:SinglePlayer → GUI:NewCampaign → GUI:CampaignMenu →` 苏联徽章 `(210,285)` → `SOV01UMD.MAP`。四趟 `scen_filename` 全为 `SOV01UMD.MAP`、`scen_battle_idx=1`（§1.7 进图门禁 ≥2 硬指标：定时器推进 + RPM 场景名 + Esc 控件 + 截图，四项齐备）。
- B1 局内截图 `out\screen_B1_ingame.png` 已人工读图：旧金山海岸 / 盟军舰船 / 苏军与尤里建筑，**确为官方 SOV01 局内**，非加载屏/错误框。

---

## 2 · 六项可比量逐项判定（[本次实测] + 规格 §3 预设判据）

> 全部数值来自 `out\<tag>_result.json`；机器可读判定在 `out\analysis.json`（由 `tools\w45_analyze.py` 用**开跑前**写死的阈值生成，未事后调整）。

### 2.1 局内定时器 `[0xA8ED84]` → **不可判**

| 量 | A1 | A2 | B1 | B2 |
|---|---:|---:|---:|---:|
| 有效局内段 `wall_s` | 74.984 | 74.985 | 74.984 | 74.985 |
| `n_samples` / `read_fail` | 11515 / 0 | 11508 / 0 | 11542 / 0 | 11533 / 0 |
| 区间速率 `rate_cps` | **31.04662** | 31.24625 | 31.23333 | 31.24625 |
| 相邻递增间隔 中位 / p95 / p99 (ms) | 31 / 47 / 47 | 31 / 47 / 47 | 31 / 47 / 47 | 31 / 47 / 47 |
| `interval_max_ms` | **344** | 63 | 79 | 63 |
| `intervals_ge64ms` | **4** | 0 | **2** | 0 |
| `delta_frame_ge2` | **1** | 0 | 0 | 0 |

- **噪声基线 N**（A1 vs A2）= **0.639%** > 预设 0.5% 阈；`≥64 ms` 计数四臂 `{4,0,2,0}`，`Δframe≥2` `{1,0,0,0}` ⇒ 噪声带本身含非零。
- **D**（B vs mean(A)）：B1 = 0.279%、B2 = 0.321%，**均 < N**，按规格 §2.4 不得进入「改造导致」归因。
- **判定：不可判**（规格 §3.1 的「等价」要求「两臂 `≥64 ms` 间隔数 = 0 ∧ `Δframe≥2` = 0」且 N ≤ 0.5%；此处三条同时不满足）。
- **补充观察（不覆盖主判定）**：A1 的 344 ms 长间隔是 **A 臂内**的一次环境瞬态（主机调度/仪器扰动），A2/B1/B2 三者互相差异 ≤0.04%、中位/p95/p99 完全一致。这支持「未观测到由装包引起的节拍变化」，但**不能**据此把主判定改成「等价」——那等于事后丢弃 A1  outlier，违反任务书 L356「不能靠降低验收阈值收口」。
- ⚠️ 该量是 **32 ms 定拍逻辑计时器，不是 FPS**；单拍抖动 11.6–47.9 ms 是已证正常现象；6 ms 采样下偶发 ≥64 ms 间隔本卡无法与主机/仪器噪声分离。
- ⚠️ **`mode[0xA8B238]` 未用作进图判据**（四趟局内读数均为 0，与 HANDOFF §2「mode 不能区分加载/局内」一致；若误用会误杀数据）。

### 2.2 局内 Esc 菜单控件集合 / 控件可见性 → **等价**

| 量 | A1 | A2 | B1 | B2 |
|---|---|---|---|---|
| `esc_menu_opened` | true | true | true | true |
| 必需 6/6 命中 | ✅ | ✅ | ✅ | ✅ |
| `(text,cls,visible,ctrl_id)` 必需集合相同 | ✅ | ✅ | ✅ | ✅ |
| 3 次轮询稳定 / 控件数 | ✅ 13/13/13 | ✅ 13/13/13 | ✅ 13/13/13 | ✅ 13/13/13 |

- 必需集合 = `GUI:AbortMission, GUI:GameControls, GUI:GameOptions, GUI:LoadGame, GUI:ResumeMission, GUI:SaveGame`（与 W39/W44 6/6 一致 `[转引]`）；四趟 `visible` 全 true，`ctrl_id` 一致（1312/1313/1314 等）。
- **控件文本 ≠ 渲染文本**：`out\screen_A1_esc_menu.png` 已人工读图，画面渲染的是「遊戲控制 / 載入遊戲 / 儲存遊戲 / 刪除遊戲 / 放棄任務 / 回到任務」，而控件文本是 `GUI:*`；本项判「控件存在/可见」用控件文本 + `IsWindowVisible`，**不**据此宣称渲染等价（规格 §4.1）。
- 全控件集合含 `MSCTFIME Composition` / `CiceroUIWndFrame` 等 **OS 瞬态窗口**，跨趟会有差异；本卡以「必需 6 控件 + visible + ctrl_id」为主判据（已在 `analysis.json` 同时记录 `full_control_set_equal`）。

### 2.3 只读 RPM 字段 → **等价**

| 字段 | A1 | A2 | B1 | B2 | 判据 |
|---|---|---|---|---|---|
| `scen_filename` | `SOV01UMD.MAP` | 同 | 同 | 同 | 精确字符串相等 ⇒ 等价 |
| `scen_battle_idx` | 1 | 1 | 1 | 1 | 整数严格相等 ⇒ 等价 |
| `battle_cnt` | 14 | 14 | **15** | **15** | `B−A == k=1`（白名单 W2，事先算出）⇒ 等价 |

- `battle_cnt` 的 +1 是**设计预期的安装态可见差异**：v13 包的 `BATTLEMD98.INI` 登记 `15=RA2F1`，引擎把新 battle 计入 Battles 表。这不是行为不等价；若不做白名单而强求相等会误报（规格 §2.5 / `DISAGREE.md` D3）。
- **作用域**：只证「官方既有场景路径上这三个读数等价」；字段语义来自既有反汇编 `[静态推断]`，未做符号级证明，不解释引擎内部含义。

### 2.4 存档文件字节 → **不可判**

| 量 | A1 | A2 | B1 | B2 |
|---|---|---|---|---|
| 产物 | `SAVE2147.SAV` | `SAVE2EB9.SAV` | `SAVE7DBC.SAV` | `SAVE27BB.SAV` |
| size (B) | 1,405,384 | 1,382,212 | 1,382,156 | 1,366,595 |
| sha256 (前 8) | `01ed2755` | `dea9d7ef` | `bd7138ac` | `a6fefe73` |

- **同臂 A1/A2 存档字节已不同** ⇒ 噪声基线不成立。按规格 §3.4 只能写「无法判定」，**不得**把 B 与 A 的差异归因于改造。
- 差异来源未定位 `[待运行验证]`：存档含时间/RNG/状态等非确定字段，文件名由引擎自动生成、各趟不同；本卡**未事先声明非确定字段白名单**（规格要求开跑前声明，未声明即不得豁免）。
- 存档点未按 `frame` 严格对齐到 ≤1 拍（Esc 菜单打开后 frame 冻结，四趟冻结值不同），也是噪声来源之一。
- 四份存档副本保留在 `out\save_*.SAV`，可另立卡做「同臂两次 diff → 定位非确定字段偏移」。

### 2.5 `verify` 退出码 → **等价（安装态门禁通过，非行为证据）**

| 臂 | `install_rc` | `verify_pre_rc` | `verify_post_rc` | `manifest_present` |
|---|---:|---:|---:|---|
| A1/A2 | —（未装） | 0 | 0 | false |
| B1/B2 | 0 | 0 | 0 | true（4 files ok / 0 changed / 0 missing / seal OK） |

- `verify exit 0` **只证安装态**，按规格 §3.5 **不计入六项行为结论的通过数**；`W23\VERIFY.md:31` 明写 `package_digest` 不能证明磁盘内容 `[转引]`。
- 与 RE-N09 L287「安装态/执行态/行为态分别有证据」一致：本卡安装态由本项给出，执行态由 §1 给出，行为态由 §2.1–2.4/2.6 给出。

### 2.6 控件可见性

与 §2.2 同源、同判据 ⇒ **等价**（四趟必需控件 `visible=true` 且 3 次轮询稳定；全集合的 OS 瞬态窗口差异不影响主判据）。

---

## 3 · 三态证据与总判定

| 态 | 证据 | 结论 |
|---|---|---|
| **安装态** | v13 `install_rc=0`；`verify` pre/post 全 exit 0；A/B 两臂 `manifest_present` 分别为 false/true；包 `package_digest` 固定；真目录零改动 | 门禁通过（`[本次实测]`） |
| **执行态** | WMI 启动四趟成功、pid 绑定、逐趟 step0 预检 pass、四趟 `phase_reached=true`（官方 SOV01 局内，截图 + RPM + 定时器 + Esc 控件四项硬指标） | 成立（`[本次实测]`） |
| **行为态** | 六项可比量：2 项等价（Esc/可见性、RPM）、2 项不可判（定时器、存档字节）、1 项门禁、1 项与 §2.2 同源 | **无法判定** |

> **总判定：`[本次实测]` 无法判定。**
> 依据规格 §3.7：任一可比量「不可判」⇒ 总判定只能是「无法判定」。
> 同时按规格 §2.4：`D < N`，**没有出现超出噪声带的差异**，因此也**没有证据支持「不等价」**——
> 本卡的诚实结论是「在现有仪器与噪声水平下，既不能证明等价，也不能证明不等价」。

**首个分歧点**：本次**无**可归因于改造的分歧点（唯一看似分歧的 `battle_cnt=14→15` 落在白名单 W2；Round 2 的 B1 简报屏滞留经重复排除为输入噪声）。因此不产出 §3.7 要求的 `first_divergent_sample_index`。

---

## 4 · 不可判项（规格 §4 逐条落地，不勉强给阈值）

| # | 项 | 判定 | 理由 |
|---|---|---|---|
| 1 | 渲染侧：GPU / `Present` / vsync / 掉帧 / 逐帧渲染等价 | **不可判** | 需注入或调试器，本会话明令禁止（A-line FINAL §5/§8.4、HANDOFF §4.4）`[转引]`。截图只是单帧；`screen_B1_ingame.png` 仅用于确认「确在官方 SOV01 局内」，**不**作渲染等价证据 |
| 2 | 函数级同输入输出对拍 / 按 tick 对象状态、RNG 序列、事件顺序、目标选择 | **不可判** | RE-N09 L280-281；只读 RPM 只给几个字段，无手段 `[转引]` |
| 3 | 「原版对照 / 干净零售金标准」 | **不可判** | W43 `TRACK_B_gates.json` `UNDETERMINED` / `is_clean_retail_gold=false`；真 `ra2youli` 有既存 v0.3 旧包（本卡两臂已一致卸载，但 A 臂仍不是「官方未修改原版」）`[转引]` |
| 4 | 联机同步 / 跨进程存读档全链 / 全战役链 / 其它分辨率·汉化版本·渲染后端 / 更重战斗 | **不在范围** | 单机、官方 SOV01 首关、本配置；规格 §4.4 |
| 5 | `mode[0xA8B238]` 作进图判据 / `frame` 叫 FPS | **禁用** | HANDOFF §2 / A-line FINAL §8.5 `[转引]` |
| 6 | 臂 C（装包但安装期禁用某特性） | **不可实现** | W43 `U-W43-6`：`resolve()` 未接线，执行层仍是整包事务 `[转引]`；本卡未做，也不假装做了 |
| 7 | 存档非确定字段定位 | **不可判** | 见 §2.4；需另立卡 |
| 8 | 6 ms 仪器下 ≥64 ms 间隔的来源（游戏停拍 vs 主机/仪器扰动） | **不可判** | 未做仪器开/关对照（RE-N04 §4 要求），本卡只记录并归入噪声 |

---

## 5 · 一条重要的方法学结果：候选差异必须被重复排除

Round 2 首次装包后 B1 **90 s 未进局内**（`battle_cnt=15`、`frame=0`、停在 SOV01 简报屏）。若单趟收工会写成「装 v13 包导致官方战役不可达」——**这是错的**。Round 3 用同一包、同一路径重跑 B1/B2，两趟均正常进图并采满 75 s；根因是 `VK_RETURN` 偶发未送达（前台焦点），加 `force_foreground` 重断言后消失。

⇒ 这正好实证了题面硬要求「两臂不等价时要区分『改造导致』还是『环境噪声』」：**没有同臂/重复基线，一次失败就会被误归因**。本卡把 Round 2 完整证据归档而不删除，供复核。

同理，A1 的 344 ms 长间隔是 **A 臂内**噪声，若只看 B1（2 个 ≥64 ms）而忽略 A1（4 个）也会误判成「装包引入节拍抖动」。

---

## 6 · 与 B 线四承诺的关系（防止外溢）

`PAUSE_STATE_20261113.md:29` 记 B 线四承诺「①版本守卫 ②行为验证 ③独立开关 ④完整回滚」中「行为验证」唯一没做 `[转引]`。本卡：

- 交付了**行为验证的规格**（`EQUIVALENCE_SPEC.md`）+ **一次真机双轨尝试与原始证据**；
- 结论是 **「无法判定」**，不是「已验证等价」，因此**不能**把 B 线「行为验证」标为已完成；
- 本卡**不**证①版本守卫（v13 守卫是 opt-in，本卡未启用）、**不**证③独立开关（安装期整包事务）、**不**证④完整回滚（本卡未对真目录做 uninstall 还原，只做沙箱内配置还原）；
- RE-N09 L287 通过条件「安装态/执行态/行为态三项分别有证据」中，**行为态证据仍不充分**（2 项不可判）⇒ B 线仍挂在「行为验证待闭合」。

**给 Lead 的最小下一证据**（按成本排序）：
1. 修「存档非确定字段」：同臂两次存档逐字节 diff，定位并**事先声明**白名单偏移；再用 `frame` 严格对齐存档点。
2. 修「定时器噪声」：做一次**仪器开/关对照**量化 6 ms 采样器自身扰动；或在更安静主机上重跑 A1/A2/B1/B2，使 N ≤ 0.5% 且四臂 `≥64 ms = 0`。
3. 若要回答「画面是否卡 / 渲染是否等价」，必须先立项解决渲染帧通道（注入授权），本会话做不到。

---

## 7 · 交付清单与复跑

```
W45_b_line_equivalence/
├── STARTED.txt                  心跳（20:35:08，先于任何读文件）
├── EQUIVALENCE_SPEC.md          A 半完整规格（可比量/双臂/判据/不可判项）
├── EQUIVALENCE_RESULT.md        ← 本文件（B 半）
├── REAL_DIR_PROOF.txt           真目录 PRE/POST 全树零改动自证
├── UNKNOWNS.md / DISAGREE.md    未覆盖项 / 与题面口径不一致处
├── designs/w45_two_missions.json
├── tools/
│   ├── w45_real_dir_baseline.py   真目录基线与零改动自证（只读）
│   ├── w45_desktop_precheck.py    桌面预检（硬闸门）
│   ├── w45_dual_track.py          双臂驱动（WMI/Win32/只读 RPM/UI/存档/finally）
│   └── w45_analyze.py             离线套用规格 §3 预设判据 → out/analysis.json
└── out/
    ├── real_dir_pre.json / real_dir_post.json / desktop_precheck.json / precheck_desktop.png
    ├── w45_dual_track.ndjson（Round 3 全量逐步记录）/ dual_track_results.json
    ├── A1/A2/B1/B2_result.json / analysis.json / analysis.stdout.txt
    ├── round1_defective/ · round2_defective/（15+15 文件，含 ndjson/结果/命令日志）
    ├── cmd_*.log（构建/安装/卸载/verify 原始命令+exit+stdout）
    ├── screen_*.png（4 趟 × 战役菜单/局内/Esc 菜单/存档对话框 + 预检 + on_error）
    ├── save_A1/A2/B1/B2_*.SAV（4 份存档副本）
    └── pkg_v13/W45 Equivalence Probe/（v13 工具链构建的包，8 文件）
```

复跑（前提：`.game_instance.lock` 为 `owner=lead`、无 `gamemd` 残留、`WinSta0\Default`）：
```powershell
$py = 'C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe'
$card = 'lead\next_re_20261112_r02\W45_b_line_equivalence'
& $py -B "$card\tools\w45_real_dir_baseline.py" --phase pre
& $py -B "$card\tools\w45_desktop_precheck.py"
& $py -B "$card\tools\w45_dual_track.py" --phase all --arms A1,A2,B1,B2 --sample-seconds 75
& $py -B "$card\tools\w45_analyze.py"
& $py -B "$card\tools\w45_real_dir_baseline.py" --phase post
```

---

## 8 · 分级索引

| 结论 | 等级 |
|---|---|
| 桌面预检通过、四趟真机执行、真目录 PRE/POST 零改动、锁还原、逐字节配置还原、残留 0 | `[本次实测]` |
| 六项可比量读数、`analysis.json` 判定、Round 1/2 缺陷与归档 | `[本次实测]` |
| `w44_lib.py` 地址表 / RPM 偏移 / W44 存档 UI 序列、v13 CLI 参数 | `[本次读码]` |
| 「≥64 ms 属仪器/主机噪声」「A1 的 344 ms 是环境瞬态」「Round 2 简报屏滞留是输入投递噪声」 | `[静态推断]`（有重复对照支持，未做仪器开/关对照定谳） |
| 31.25 计数/s 定拍语义、Esc 6/6 参考集、`verify` 退出码表、渲染侧需注入、`mode` 陷阱、W43 `U-W43-6` | `[转引]` |
| 存档非确定字段定位、仪器扰动量化、渲染等价、臂 C、联机/跨进程存读档 | `[待运行验证]` |
