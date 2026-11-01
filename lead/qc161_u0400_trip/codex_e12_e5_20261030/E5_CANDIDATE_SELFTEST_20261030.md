# E5_CANDIDATE_SELFTEST_20261030.md — E5 关窗时机梯度候选离线自证报告

**日期**：2026-10-30 · **来源**：GOAL-3T X 退出线（E5 参数化轮，候选件离线制作）
**性质**：离线制作+自证。本轮**零真机、零发射、零游戏启动、零扩 Hook、零网络**。
发射永远等 Leader 授权（裁决权=Leader/用户）；本件 `--live` 无 `--approved` **恒 rc=3**（本轮实测在盘，§3）。
**写域纪律**：本轮新建且仅新建 `lead/qc161_u0400_trip/codex_e12_e5_20261030/` 目录
（candidate 四件+本稿+本轮证据 txt）；两冻结母版（v2 / earlyclose）、修复候选原件
（codex_e12_fix_20261029/）、TRIP_INDEX、台账、设计件、游戏目录=**零字节触碰**
（运行前后哈希复验在盘，§1/§6）。

---

## 1. 交付件与哈希（sha256，本轮终值）

| 件 | 绝对路径 | sha256 | 尺寸 |
|---|---|---|---|
| E5 候选驱动 | `D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip\codex_e12_e5_20261030\candidate\_drive_c2_x_e12.py` | `90a1890afe356191231307b80efa2a3b920de2fa480c8f5ffc5185f33a038d03` | 36,637 B |
| 离线自检套件 | `D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip\codex_e12_e5_20261030\candidate\_drive_c2_x_e12_selftest.py` | `fdc4f7e8ae34f415b286bb9486ef3c032e8538ae93fa60ddadfceac9153b94c7` | 58,054 B |
| 依赖副本 v2 | `…\codex_e12_e5_20261030\candidate\_drive_c2_x_probe_v2.py` | `6afe2711136c3b52344cd435f6dbd64508378a1e019c552228ff4f5e653d13b9` | 48,630 B（字节同母版） |
| 依赖副本 earlyclose | `…\codex_e12_e5_20261030\candidate\_drive_c2_x_earlyclose.py` | `2e970eec43fe37ff02cab98e71bce9c764d11d758ab2a7b31b495100d109c2e1` | 9,061 B（字节同母版） |
| 本自证报告 | `…\codex_e12_e5_20261030\E5_CANDIDATE_SELFTEST_20261030.md` | （交付后由 Leader 复算登记） | — |

**基线自验**（派单钉值命中，制作前置条件）：修复候选
`codex_e12_fix_20261029/candidate/_drive_c2_x_e12.py` 实测
`75daf4f7358996aa0af1aa1454b63bed6156826a7c047f784b3e9d997a652901` ✓；其自检件 `95e365aa…` ✓。
**轮末复验**：修复候选原件与其自检件哈希轮末不变（无漂移）；仓库根 `_drive_c2_x_probe_v2.py`/
`_drive_c2_x_earlyclose.py` 冻结母版与本目录副本同哈希（零触碰）。

**import 前置哈希门（不变）**：E5 件沿用模块级 `verify_frozen_masters()`/`_MAESTRO`——任何
import 两母版之前实读 sha256 对钉（`6afe2711…`/`2e970eec…`），不符/不可读⇒`RuntimeError` 拒载；
自检件同样先验再 import（不符⇒rc=4）。副本与母版字节同源，门语义与修复候选逐字相同。

## 2. 验收条件逐项回执

| 验收项 | 结果 | 证据 |
|---|---|---|
| `--selftest` rc=0 全绿（95+新增全过） | **110/110 红=0 ALL-PASS，rc=0**（原 95 项全保留+E5 组 15 项） | 附录 A（驱动委托入口）；直接入口 `python _drive_c2_x_e12_selftest.py` 复跑同 110/0/rc=0（`evidence_selftest_run2_direct_entry.txt`） |
| `--live` rc=3 | **rc=3**，输出「需 --approved（D-11 …）——--live 无授权恒拒」 | `evidence_live_rc.txt`；自检 E-06/E5-14 子进程双测 |
| 母版哈希门生效 | 通过（模块级门+自检件门+自检 E-02/E-03 反证：钉值不符/不可读⇒RuntimeError） | §1；附录 A E-02/E-03 |
| `--hold 6` 与修复候选逐字节等价 | **通过（E5-12）**：修复候选 / E5 缺省 / E5 `--hold 6` 三方，同替身同虚拟时钟同定桩 ⇒ **rec 与 timeline 的 sort_keys JSON 串全等**（rec_equal=True tl_equal=True，三方 verdict 全 OK） | 附录 A E5-12（原理：生效 hold==常量 6.0 时零新键、零数值路径改动） |
| E2 轴全保留 | 通过（hook6/CPU/ws/窗口枚举/闩+30 截图原样；梯度档 hold=15 抽查闩检测+9 慢行+P1 标签+闩+2 s 截图全在） | 附录 A E5-08/E5-10；A/B/C/D/F/BOOT 组全绿 |
| `--trips` 语义保持 | 通过（default=2 不变；`--hold 10 --trips 1` 离线形态 rc=0 实测，附录 B） | E5-15 |
| 非法 hold 拒收 | 通过：CLI `--hold 0/-1/abc/nan/inf` ⇒ **全 rc=2**（argparse 闸前拦截）；`run_trip` 直调 ⇒ 趟 FAIL `hold_invalid`（双保险） | E5-02/E5-03/E5-13；`evidence_hold_invalid.txt` |
| 附加：`--preflight` 真 OS 只读 | **rc=0 全过 10 项**（v2 预检 7+终钉复验+源 ini 钉+BOOT 读数） | 附录 B `evidence_preflight.txt` |

## 3. 与 E12 修复版（75daf4f7…）的差分摘要

**驱动件 diff：10 个 hunk，+60/−5 行**，全部集中于 E5 增量面，逐条：

1. 文件头 docstring：标题注 E5 谱系（基线=75daf4f7…）+ 新增「E5 增量」段（说明 --hold 语义与等价承诺）；
2. 新增 `normalize_hold_s(val)`：E5 seam 纯函数——None⇒常量 6.0；合法数⇒float；非数/非有限/≤0⇒(None, err)，不抛；
3. 新增 `_hold_arg(s)`：argparse 类型闸（ArgumentTypeError ⇒ CLI rc=2，先于一切闸/分支）；
4. `run_trip` 签名增 `hold_after_window_s=None`（**参数传递覆盖生效值，不改两冻结母版、不改常量本身**）；
   rec 构造前归一；生效值≠6.0 时在 `e2_params.hold_after_window_s`+`rec.hold_override` 显式留痕
   （**==6.0 时零新键**——等价承诺的实现点）；try 内 precheck 段二次校验，非法⇒`TripFail(hold_invalid)`（不发射）；
5. 生效值两个使用点：hold 循环 `while now()-th < hold_s`（原 `< HOLD_AFTER_WINDOW`）、protocol 串 `% hold_s`
   （原 `% HOLD_AFTER_WINDOW`；6.0 时输出逐字节同原串）；
6. `main()`：新增 `--hold` 参数（type=_hold_arg, default=None）+ 趟循环传 `hold_after_window_s=a.hold`；
   **gate_decision/offline/live 拒绝/预检/selftest 委托全部零改动**；`--trips` default=2 零改动。

**自检件 diff**：原 95 项（H1/A13/B20/C13/D12/E7/F13/BOOT13/G3）逐项保留、断言原语义；
适配性改动三处（不弱化）：`schema_check` 的 protocol 断言参数化（`window+%.1fs % hold_s`，原调用点默认 6.0 行为不变）；
`trip_once` 增 `hold_after_window_s=None` 透传；终旗横幅改 `E5 SELFTEST (E12-lineage)`（E-07 针词同步，
断言意图=「自检分支优先于 live 闸且零发射」不变）。新增 **E5 组 15 项**（§4）。

## 4. E5 组 --hold 参数化回归（15 项，附录 A 全绿）

| 项 | 断言 | 实测 |
|---|---|---|
| E5-01 | 缺省常量不回归：`HOLD_AFTER_WINDOW==EC.HOLD_AFTER_WINDOW==6.0`（单一来源不变） | OK |
| E5-02 | `normalize_hold_s` 分臂：None→6.0；10→10.0；"15"→15.0；`_hold_arg("20")`==20.0；0/−3/"abc"/nan/inf ⇒ err 不抛 | OK（5 err 臂全中） |
| E5-03 | run_trip 直调 0/−3/nan ⇒ 趟 FAIL `hold_invalid`（不发射、不崩套） | OK |
| E5-04 | **mock 关窗时点 hold=10**：hold_tl_n==10（逐秒哨兵满额，关窗不早于 hold）∧closed_at∈[10.1,11.5] | OK（n=10，closed=10.127） |
| E5-05 | **hold=15**：hold_tl_n==15 ∧closed_at∈[15.1,16.5] | OK（n=15，closed=15.137） |
| E5-06 | **hold=20**：hold_tl_n==20 ∧closed_at∈[20.1,21.5] | OK（n=20，closed=20.147） |
| E5-07 | 关窗时点线性平移：Δclosed(15−10)==Δclosed(20−15)==5.01 s（±0.01；节律 1.002 s/哨兵） | OK（5.0100/5.0100） |
| E5-08 | 梯度档 E2 轴全保留（hold=15 代表档）：闩检测+慢采样≥3 行+P1 标签+闩+2 s 截图+stop=None | OK（slow=9，P1_first_candidate） |
| E5-09 | 梯度档留痕：`hold_override={常量6.0,生效档}`∧`e2_params.hold_after_window_s`==档∧protocol=`window+<档>.0s` | OK |
| E5-10 | hold=20 趟 schema 同形（close_rows/_e2/慢行配对全过——参数化不破坏 schema） | OK（bad=[]） |
| E5-11 | 缺省不传 --hold 不回归：protocol=window+6.0s∧hold_tl_n==6∧**零新键**（无 hold_override/hold_after_window_s） | OK（n=6） |
| E5-12 | ★ 逐字节等价：修复候选/E5 缺省/E5 --hold 6 三方同替身同钟 ⇒ rec+timeline JSON 串全等 | OK（rec_equal=True tl_equal=True） |
| E5-13 | CLI 非法 hold 拒收：`--hold 0/-1/abc/nan/inf` ⇒ 全 rc=2（argparse 闸前拦截） | OK（{0:2, −1:2, abc:2, nan:2, inf:2}） |
| E5-14 | 硬闸不变：`--live --hold 10` 无授权 ⇒ rc=3（梯度档不旁路授权闸） | OK |
| E5-15 | 离线 `--hold 10 --trips 1` ⇒ rc=0 不发射（Leader 梯度调用形态离线确认） | OK |

计数=H 1 + A 13 + B 20 + C 13 + D 12 + E 7 + **E5 15** + F 13 + BOOT 13 + G 3 = **110**。

## 5. 发射前置清单（Leader 批准后逐项核对；--preflight 已内置 1–5 全部）

1. **授权闸值**：Leader 批准文本在手（`--approved` 仅透传闸值，绝不自动跑；`--live --approved` 仍须预检全过才发射）；
2. **两终钉件复验**：sha256 `6afe2711…`（v2）/`2e970eec…`（earlyclose）——本件 import 前内置自验，
   发射时以 `--preflight` 现读再证（本轮 rc=0 命中）；
3. **BOOT 同会话**：`--preflight` 读 GetTickCount64（本轮读数 59,291,328 ms 仅为记录样例，发射以当场值为准）；
   批次内跨趟开机墙钟估计差 >2000 ms ⇒ 停（BOOT 组实测在盘）；
4. **进程零残留**：gamemd.exe/rc4_loader.exe=0（v2.preflight+趟前 precheck 双核；本轮实测=0）；
5. **载体源 ini**：sha16=`27c9a60c55a8a1b4` ∧ 16,496 B（本轮实测命中）；gamemd `73201cc021497c95`/
   loader `ebddf6a61273c874`/c2 DLL `edb9a0cd…`/h7 `d019e8be…`/探针 `b063052c…`/源 88 件=v2 七项预检（本轮全过）；
6. **载体纪律**：批准根内+路径长≤130+建后断言空+身份闸（沿用 v2，零改动）；
7. **时段预算**：每趟 ≈（前段 ~125 s@hold6 + Δhold）+ watch 120 s + 收尾 ⇒ hold=10/15/20 约
   **4.3/4.4/4.6 min/趟**；三趟串行预留 ≥20 min；
8. **命名与登记注意**：趟目录 `…_P3e_E12_T1` **不含 hold 值**，三趟仅时间戳不同——台账/TRIP_INDEX
   登记时档位以 `_rec.json` 的 `protocol`（`window+10.0s`…）与 `hold_override.effective_s` 字段为准。

## 6. 三档发射命令建议（Leader 逐条批准、串行执行、单实例）

```text
python candidate/_drive_c2_x_e12.py --live --approved --hold 10 --trips 1
python candidate/_drive_c2_x_e12.py --live --approved --hold 15 --trips 1
python candidate/_drive_c2_x_e12.py --live --approved --hold 20 --trips 1
```

- 每条=独立批次单趟（`--trips 1`），**每次调用各自 `capture_boot()` 自为 BOOT 参考**——三档之间
  无跨批 BOOT 互相约束，同开机会话前提由 Leader 现场保证（或三档并入一次调用
  `--hold <档> --trips 3` 的形态**不支持**：hold 为批次级参数，一调用一档）；
- 串行、单实例、趟间核对残留=0；任何一档非 OK 或触停 ⇒ 后续档停（承 G-9 纪律，Leader 处置）。

**停止条件**（与修复候选逐字相同，E5 未触碰）：慢采样期新可见窗（交互关键字命中⇒定性）⇒ 只留证据即停；
except.txt 哈希中途变化 ⇒ 停；跨趟 BOOT 变化 ⇒ 停；预检 fail ⇒ 停；趟非 OK ⇒ 批次停。
**回退**：配置回滚零成本（Guard/Bail 只写载体副本 ini，源母本只读，趟毕 finalize 删载体树）；
终钉恢复=哈希复验 6afe2711/2e970eec（本轮零触碰）；异常时本 E5 件直接弃用、回退修复候选 75daf4f7… 即可
（E5 相对其仅差 --hold 参数面，缺省行为逐字节等价已证）。
**判读纪律**：只报盘面并趟计数，禁比率表述；E2 分叉标签是首候选提示，裁决权在 Leader。

## 7. 局限（如实）

1. 三档关窗时点断言在 mock 时钟（1.002 s/哨兵确定性节律）下成立；真机 hold 期节律受真实
   phase_sentinels 耗时影响，closed_at 会高于 mock 值——但「不早于 hold」由 while 条件保证（结构性，非计时性）。
2. hold 期（窗现→PostMessage）只有 phase_sentinels 被动记录、**无停止判定**（与修复候选 hold=6 同语义）：
   hold=20 暴露面更长，若宿主在 hold 期自行弹窗，仍按协议在窗现+hold 时点投递关窗，窗面变化以
   `hold_tl[].visible_windows` 证据在录，判读时留意。
3. `--hold 6` 等价性为替身时钟下的逐字节比对（结构等价）；真机行为等价由「同代码路径+同常量」推得。
4. 自检沙箱=系统 tempdir（自动清除）；本轮 E5 目录内零 `__pycache__`（全程 PYTHONDONTWRITEBYTECODE=1）。

---

## 附录 A：自检全文输出要点（110 项全绿，rc=0；全文见 `evidence_selftest_run1.txt`/`run2`）

```text
== E5 候选驱动件离线自检（E12 修复版 95 项谱系 + E5 组 --hold 梯度回归；零真机·零发射·零游戏启动）==
驱动件 sha256=90a1890afe356191231307b80efa2a3b920de2fa480c8f5ffc5185f33a038d03
[OK] H-00     母版哈希自验通过方可 import（早窗件/v2 实读对钉）          ec=2e970eec43fe… v2=6afe2711136c… hold=6.0 watch=120.0
[OK] A-01..A-13   组件分臂 13 项（闩检测/1Hz 节律/hook6 锚/CPU 增量/闩+30 截图/finalize/schema/枚举/hold_tl/丁臂/schema 同形）
[OK] B-01..B-20   三态与故障注入 20 项（阻塞族/哨兵读败/hook6 读败/CPU None·异常·基线败/ws 读败/枚举异常/OpenProcess=0/残留/投递失败/mkdir/身份/自然退/零样本/BOOT×2/WAIT_FAILED）
[OK] C-01..C-08   通用停止条件 13 项（#32770/只留证据/停即退采/新窗保守停/except 变化/停止趟 finalize/关键字×6/同名句柄）
[OK] D-01..D-12   分叉标签机 12 项（P1/丁/阻塞/中间带/不可读/读败未决/混合/ws 增长/闩后零行/未闩/阈值/禁比率词面）
[OK] E-01..E-07   硬闸 7 项（gate_decision 四组合/哈希门拒不符·不可读/子进程实测 无参0·approved0·live3·live+selftest 自检优先）
[OK] E5-01..E5-15 --hold 梯度回归 15 项（§4 逐项）
[OK] F:×13    变异全部被抓出（闩常量/节律/哨兵吞值/hook6 吞读败/CPU 分母/慢行旁路/停止旁路/finalize 跳过/BOOT 断言旁路/live 闸篡改/E2 段删/交互关键字清空/闩+30 截图旁路）
[OK] BOOT-×13 BOOT 回归 13 项（双趟推进/参考不变/重启拦/±2000/2001 边界/无效参考/RAW·BYPASS 变异）
[OK] G:×3     运行前后 v2/earlyclose/e12 三件哈希不变
== E5 SELFTEST (E12-lineage): 110 项，红=0 ⇒ ALL-PASS ==
件 sha256: e12=90a1890afe356191231307b80efa2a3b920de2fa480c8f5ffc5185f33a038d03
           earlyclose=2e970eec43fe37ff02cab98e71bce9c764d11d758ab2a7b31b495100d109c2e1
           v2=6afe2711136c3b52344cd435f6dbd64508378a1e019c552228ff4f5e653d13b9
```

## 附录 B：命令级实测记录（本轮真跑）

| 命令 | 实测 rc | 输出要点 | 证据文件 |
|---|---|---|---|
| `python _drive_c2_x_e12.py --selftest` | **0** | 委托自检 110 全绿 | `evidence_selftest_run1.txt` |
| `python _drive_c2_x_e12_selftest.py` | **0** | 直接入口同 110 全绿 | `evidence_selftest_run2_direct_entry.txt` |
| `python _drive_c2_x_e12.py --live` | **3** | 需 --approved 恒拒 | `evidence_live_rc.txt` |
| `python _drive_c2_x_e12.py --hold 0` | **2** | `error: argument --hold: hold_invalid(hold_out_of_range:'0')` | `evidence_hold_invalid.txt` |
| `python _drive_c2_x_e12.py --hold 10 --trips 1` | 0 | 离线不发射 | `evidence_hold10_offline.txt` |
| `python _drive_c2_x_e12.py`（无参） | 0 | 离线不发射 | `evidence_noargs_offline.txt` |
| `python _drive_c2_x_e12.py --approved` | 0 | 闸值透传不自动跑 | `evidence_approved_offline.txt` |
| `python _drive_c2_x_e12.py --preflight` | **0** | 10 项全过（终钉复验+源 ini `27c9a60c55a8a1b4`/16,496 B+BOOT 59,291,328 ms+残留=0） | `evidence_preflight.txt` |

## 附录 C：足迹核对

`git status --porcelain`：本轮新增仅 `?? lead/qc161_u0400_trip/codex_e12_e5_20261030/`（整目录未跟踪）；
其余 454 条 M/A 条目均为本轮之前已存在的他线足迹（未触碰）。修复候选原件、冻结母版、TRIP_INDEX、
台账、游戏目录零写入；自检沙箱自动清除；目录内无 pyc。
