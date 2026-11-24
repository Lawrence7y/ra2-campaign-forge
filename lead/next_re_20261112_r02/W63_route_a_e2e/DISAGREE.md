# W63 · DISAGREE.md

> 执行者 Hy4（W63）｜记录本卡与卡面/前卡口径的**分歧、偏离与自我设限**；不隐藏、不粉饰。
> 主结论见 `E2E_RESULT.md`；未定谳项见 `UNKNOWNS.md`。

## D1 · 对「MAPSELMD 数字子项从 1 连续」的实现口径 —— 采用单变量 `1=`，并把 `2=` 留作未跑的回退

- **卡面**：「阶段段 `Scenario=` 与数字子项也从 1 连续（W34 当年用 `2=` 起始是已知疑点，本卡改用从 1 连续，若失败请记录并回退对比）」。
- **前卡事实**（`[转引]`）：v15 `mapselmd.py` 用 `CHILD_COLOUR_INDEX = 2`，W44 的实测可用包就是 `2=RA2F_ECH02_…`；W59 `LEAD_VERIFY_W59.md` §3 明确「`2=` 无 `1=` 的疑点**未定谳**」，W39 用 `SkipMapSelect=no` + 同一份 `2=` 文件成功推进过。
- **本卡做法**：把 v15 原生输出逐字节另存为变体 B（`out\MAPSELMD.INI.variant_from2`，`2=`）；把**追加阶段**里的 `2=<下一阶段名>` 改为 `1=<下一阶段名>` 作为主用变体 A，其余字节（含官方全文、`[Nod]` 键 1..10、各阶段 `Scenario=`）不变。单变量 = 追加阶段子项键 `1=` vs `2=`。
- **分歧点**：卡面把「从 1 连续」当作要改的项，而 v15/W44 的**已证可用**实现是 `2=`。本卡没有把 `2=` 判成「错」，也没有把 `1=` 判成「必需」——只按卡面把 `1=` 作为**主用**，并诚实登记「因主用未失败，按卡面无需回退，变体 B 未运行」。
- **结论口径**：`[本次实测]` 只能写「变体 A（from1）在 `SkipMapSelect=no` 上够用」；**不能**写「`2=` 起始已否证」或「从 1 连续是必修项」。因果仍归 `UNKNOWNS.md` U1（`[待运行验证]`）。
- **理由**：W27/W34/W59 三次教训都是「把未定谳当已定谳 / 把进图当链贯通」。宁可交付一个带明确边界的成功，也不编造一个 A/B 结论。

## D2 · 运行器基底：复制 W44 的 `w44_lib.py` 而非 W55b 的 `w55b_dual_track.py`

- **卡面**：「可参考的运行器：`W55b_equivalence_rerun\tools\w55b_dual_track.py`（… 复制到本卡后改输出路径；⚠ 不要直接 import 别卡脚本，它们把输出路径硬编码）」。
- **本卡做法**：主体用 `W44_c_line_e2e\tools\w44_lib.py` 的**本卡副本**（`work\tools\w63_lib.py`，路径常量全部重指到 W63；新增 `Scen+0x34AC`/`+0x34AE`、`+0x125C` 读 260 B），并对照了 W55b 的函数表（同为 W27 `live_lib.py` 一族：`list_gamemd`/`launch_game`/`desktop_precheck`/`close_game`/`controls`/`read_counters`/`screenshot`/`robocopy`/`tree_manifest` 等）。
- **理由**：W44 是**本环境里唯一已真机走过「战役菜单 → 苏联徽章 → 通关 → `GUI:Continue` → 下一关」的卡**（`LEAD_VERDICT_C_line_E2E.md` S3/S4 签发），其 `phase_run.py` 的点击坐标、控件文本、胜利/推进判据与本卡任务逐字对应；W55b 是双轨等价性采样卡，其 `collect_one_arm` 是长时间帧采样，不含三关推进状态机。两者同族、可互换，但复用 W44 的**已证流程**风险最低。
- **纪律遵守**：卡面禁的是「直接 import 别卡脚本」（输出路径硬编码）；本卡是**复制文件后重指常量**，未 import 任何他卡模块（`w63_common.py` 亦为本卡新写）。所有写入落 `W63_route_a_e2e\`。

## D3 · 对「不 `taskkill` 用户进程；只关自己启动的 `gamemd.exe`」的解释

- **实测**：`close_game` 顺序为 `WM_CLOSE(hwnd=331606)` →（未关）`taskkill /PID 34668` →（仍未关）`taskkill /F /PID 34668`；`residual_own_pid=0`。34668 是本卡 WMI `Win32_Process.Create` 启动的沙箱 `gamemd.exe`，`wait_for_pid` 由 launcher ppid 归因得到。
- **口径**：卡面「不 `taskkill` 用户进程」= 不碰用户/他卡已存在的进程；「只关自己启动的 `gamemd.exe`」= 允许对本卡自己启动的实例做关闭。W44（`LEAD_VERDICT_C_line_E2E.md` §3 已抽核）与 W55b 的 `close_game` 都是同一实现。本卡**未按名字批量 `taskkill /IM gamemd.exe`**，只对单个自己拿到的 pid。
- **自我设限**：如实登记用了 `taskkill /F`，不隐藏；若 Lead 认为该口径应更严（例如禁 `/F`、只允许 `WM_CLOSE` + 等超时），本卡结论不受影响（游戏已在 23:39:36 完成全部观测后才关闭）。

## D4 · 沙箱里存在「无清单认领的 241 B 孤儿 `.bak`」—— 本卡在**沙箱副本**里移除，真目录未动

- **事实**：`ra2youli\BATTLEMD.INI.ra2forge.bak` 是 241 B 的 W27 时代诊断备份，v0.3 清单**不拥有** `BATTLEMD.INI`。v15 `inplace_preflight()` 在 `.bak` 存在且清单不认领目标时 **exit 34 `INPLACE_BACKUP_ORPHAN`**（W60 INPLACE4 实测）。
- **本卡做法**：`save_pristine` 先存其字节副本（SHA `9f804531…`），**仅从沙箱副本删除**，使 inplace install 能过预检；收尾 `restore_one` 从 pristine 逐字节还原（`byte_identical=True`），沙箱 `identical_tree=True`。
- **分歧点**：这算一次对「沙箱基线」的写，但它是**沙箱副本**、可逐字节还原、且与 W44「处理旧包 v0.3」同型。真目录 `BATTLEMD.INI.ra2forge.bak` PRE==POST 未变（`REAL_DIR_PROOF.txt`）。
- **未做**：没有改 v15 的预检、没有 `--force` 绕过、没有把孤儿 `.bak` 直接覆盖成官方 2733 B。

## D5 · `ra2forge_install.json` 是否进「配置还原集合」

- **前卡规则**（`LEAD_VERDICT_C_line_E2E.md` §7，Lead 从 W44 缺陷提炼）：安装记录是安装事务的**结果**，不是配置；把 PRE 阶段的旧清单还原回去会抹掉本次安装事实 ⇒ 启动前配置字节基线还原集合**不得**包含 `ra2forge_install.json`。
- **本卡做法**：在**离线 PRE**（任何安装之前）`save_pristine` 把 v0.3 清单存为基线；安装/真机期间**不碰**它；收尾 uninstall 删除本次清单后，才从 pristine 还原回 v0.3 原始清单，并跑 `verify_post` exit 0 自证。
- **不冲突**：Lead 的规则针对「启动前/运行中的 self-heal 别用旧清单覆盖新安装记录」；本卡是**收尾**（uninstall 已删除新记录）回到 PRE 状态，方向相反，不抹掉任何本次安装事实（本次安装事实已固化在 `INPLACE_INSTALL.json` / `offline.ndjson` / `cmd_install_inplace_plain.log`）。

## D6 · 结算屏 M2/M3 截图哈希相同 —— 如实登记，不夸大

- `screen_victory_M2.png` 与 `screen_victory_M3.png` 均 246,905 B、SHA `99d3135c…` 逐字节相同（静态结算模板）。
- 本卡**不**把它当「两次独立胜利」的视觉证据；两次胜利各自另有 `level_victory` 事件的 `w59`（`0x125C` 分别 `RA2F_M2.MAP` / `RA2F_M3.MAP`）、`GUI:Continue` 控件枚举、`frame` 停滞读数支撑。W44 §8 的「图不够完整就说不够完整」口径照用。

## D7 · 一次成功 ≠ 泛化

- 本卡只有**一趟**真机、`SkipMapSelect=no`、3 关、单一分辨率/语言、单一 MAPSELMD 变体 A。未做重复臂、未做负对照（故意破坏 MAPSELMD 看是否弹 `MSG:UnableMapSelect`）。
- 因此不写「(a) 在所有配置下稳定工作」；只写「本环境本包本变体下，三关链真机贯通一次，逐关有独立读数与截图」。重复性与负对照归 `[待运行验证]`。

## D8 · 与 W27 口径的自我核对（防止重蹈覆辙）

- W27 栽在「把进图成功当链贯通」。本卡 `E2E_RESULT.md` §1 逐关列出**进关 / 通关 / 推进 / 终止**、`§2` 给出 `0x125C` 三关轨迹 + `+0x35A0` + `+0x34AC`，`§3` 给出 10 张截图哈希，`out\run.ndjson` 198 行逐帧 RPM —— 满足 `LEAD_RULING` §3「不是能进图就算过」的逐关判据，故「多关链贯通」的措辞是**有落盘证据**的，不是自述。
