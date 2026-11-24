# W55b · frame 对齐策略（**开跑前事先声明**）

> 卡 `W55b_equivalence_rerun`｜run_id `NEXT_RE_20261112_R02`｜模型 `Hy4`
> 写于任何真机启动之前。本文件是 W45 `EQUIVALENCE_SPEC.md` §3.4 / §2.5 与 W54 `SAVE_DETERMINISM.md` §5.3 前置 1 的**事先声明**，不按结果反推调整。
> 分级：`[本次实测]` / `[本次读码]` / `[静态推断]` / `[转引]` / `[待运行验证]`。

---

## 1 · 问题（W45 UNKNOWNS U6 / W54 §5.3-1）

- `[转引]` W45 `EQUIVALENCE_RESULT.md:122` / `UNKNOWNS.md:99`：按 Esc 打开局内存档菜单后 `frame` **冻结**，四趟冻结值 `2404 / 2408 / 2441 / 2412`，规格 §3.4 要求 ≤1 拍。
- `[本次读码]` W45 `tools/w45_dual_track.py:883` 的定时器段是**固定 75 s 墙钟**窗口，结束帧随「进图起点帧」漂移（四趟 `counters_at_ingame.frame` = 52/43/76/46）；`counters_after_timer.frame` = 2396/2400/2433/2404，随后到 `counters_after_save.frame`（冻结值）各 +8。
- ⇒ 单纯「等 `frame==N` 再存」若只挂在**存档动作**上确实可能永远等不到（菜单一开就冻结，帧不再推进，条件永不满足）。

## 2 · 本卡采用的对齐策略（三重）

### 2.1 门限挂在「按 Esc」之前，不挂在「存档」之后

**核心改动**：把 W45 的固定 75 s 定时器段，改成 **frame 门限段**：

```
FRAME_GATE_N = 2400          # 事先声明的绝对帧门限
FRAME_ALIGN_TOL = 1          # 规格 §3.4「≤1 拍」，事先声明，不放宽
MAX_GATE_WALL_S = 150        # 安全上限，防止 frame 永不推进时死等
POLL_CADENCE_S = 0.006       # 6 ms，与 W45 一致（同一观测仪器 / C6）

在「稳定局内段」以 6 ms 采样 read_counters()：
    while frame < FRAME_GATE_N and wall < MAX_GATE_WALL_S:
        samples.append((t, frame, mode)); sleep(0.006)
    一旦 frame >= FRAME_GATE_N  =>  立即 keybd_event(VK_ESCAPE)
```

- 门限触发点**在打开菜单之前**，此时 frame 仍在推进 ⇒ 条件可达，不会「永远等不到」。
- 采样过程同时产出 W45 §3.1 的定时器可比量（速率 / 间隔 / ≥64 ms / Δframe≥2），两臂同 cadence。
- 进门限后**不做任何耗时动作**（不截图、不枚举控件、不重新置前），直接发 Esc，以最小化「检测到 N → 游戏处理 Esc」之间的帧漂移。

### 2.2 以「冻结帧值」为对齐键（题面示例口径）

发 Esc 后：

```
1) 立即读 read_counters() -> frame_before_esc（送键前的最后读数）
2) 轮询 controls() 直到出现 GUI:ResumeMission（最多 3 次，每次间隔 0.5 s；
   只在菜单未出现时补发 Esc，避免 W45 Round-1 的「按两次把菜单关掉」）
3) 菜单确认打开的**同一时刻**立即读 read_counters() -> frame_frozen
4) 之后才做 3 次稳定轮询 / 截图 / 存档对话框（此时帧已冻结，不再变化）
```

**对齐键 = `frame_frozen`**（不是 `FRAME_GATE_N`，也不是 `frame_before_esc`）。
每份存档在 `<tag>_result.json` 与 ndjson 里同时落盘：
`frame_gate_target` / `frame_at_gate` / `frame_before_esc` / `frame_frozen` /
`frame_delta_gate_to_frozen` / `alignment_key`。

### 2.3 对齐精度与「不满足则重开」的判定（事先声明）

- 定义**对齐组**：`|frame_frozen_i − frame_frozen_j| ≤ FRAME_ALIGN_TOL (=1)` 的两份存档互为「已对齐」。
- 对每一趟：若 `|frame_frozen − FRAME_GATE_N| ≤ GATE_ACCEPT_BAND (=16)` 视为「门限命中」；否则该趟标 `gate_miss=true`。
- **重开规则**：题目允许「不满足则重开一次」。本卡时间盒 ≤4 趟真机（A1/A2/B1/B2），若某趟 `gate_miss=true` 或有 `errors`，**在剩余趟数预算内**把该臂补跑一次；补跑仍不满足 ⇒ 该样本标 `aligned=false`，**不得当作对齐样本使用**（题面红线）。
- 报告里**如实给出实际达成的对齐精度**：四份（或更多）`frame_frozen` 的原始值、max−min 跨度、以及哪些样本被排除、排除原因。不把没对齐的样本写进 N/D 计算。

### 2.4 同 frame 同臂补样（W54 §5.3-2）

- 每趟真机**在冻结的同一菜单内尝试两次存档**（slot 0 / slot 1，不同文件名），两次都记录各自的 `frame_frozen`。若两次 `frame_frozen` 相同 ⇒ 该趟直接产出一份**同 frame 同臂**对（in-trip pair），用于测 `CONTENTS` 平面噪声基线 N 的下界。
- 每臂 2 趟（A1/A2、B1/B2）⇒ 若两趟 `frame_frozen` 也相同，则额外得到**跨趟同 frame 同臂**对（cross-trip pair，才是 W45 `A1 vs A2` 意义上的 N）。
- 4 趟 ≥4 份存档（题面要求）；若第二次存档因 UI 行为未成功，如实记 `second_save_succeeded=false`，不伪造。

> **诚实边界**：in-trip 两次存档共享同一游戏状态，只能测「序列化噪声」；cross-trip 两次才包含「独立跑到同一帧」的运行间噪声。本卡**以 cross-trip 为主判据**，in-trip 作为下界与补充，两者都落盘。

## 3 · 坐标系纠正（题面强制）

- `[本次实测]` `.SAV` 头 8 字节 `d0cf11e0a1b11ae1` = MS-CFB / OLE2 复合文档，15 个具名 stream。
- **禁止按 raw file 绝对偏移逐字节比较**。本卡比较器 `tools/w55b_cfb_compare.py`：
  1. `import` W54 `EVIDENCE/step2_cfb.py` 的 `CFB` 类（用 `contextlib.redirect_stdout` 抑制其驱动输出，只取类定义）；
  2. 按具名 stream 取 payload，逐 stream 输出 `len / sha256(raw) / sha256(masked) / 差异字节数`；
  3. 元数据平面按 W54 `SAVE_NONDET_WHITELIST.json`（副本 `out/whitelist_applied.json`，SHA256 `dad972c4…` 与 W54 原件一致）**掩码后比较**；掩码坐标用 CFB-logical（`stream` + `offset` + `length`），与 W54 `step6_whitelist.py:39-48,157-165` 的 `build_view`/`mask_view` 完全同构；
  4. FAT / DIFAT / miniFAT 容器分配表**按构造排除**（W54 §5.3-4 / §2.4-1）。

## 4 · CONTENTS 平面的比较口径（W54 §5.3-3）

事先声明的**两步**：

1. **先试结构解析**：对 `CONTENTS` 整流做 `(u16 未压缩长, u16 压缩长)` LCW/LZO 块遍历、以及 `(u32 长度, payload)` 分块遍历，起点试 `0 / 4 / 8 / 0x3C / 0x40`；若某次遍历能**连续消耗 ≥95% 整流且每块长度自洽** ⇒ 判「解出块结构」，改按块序列比较并输出逐块差异。
2. **失败则退化**：W54 §4.4 已实测这些遍历均在第 2–3 块崩掉、未确认 LZO/LCW。本卡若同样失败，**明说「未解出块结构」**，退化为「**按 frame 对齐后的整流 sha256**」比较：只对 `aligned=true` 且同 `alignment_key` 的样本比较 `CONTENTS` 整流 `sha256` 与差异字节数，输出逐 stream 差异表。
3. 两种口径都不把 `CONTENTS` 整段掩掉（W54 `not_covered_deliberately`）。

## 5 · 判据（三选一，事先写死，不按结果放宽）

记 `N` = **同 frame 同臂**对的 `CONTENTS` 整流差异字节数（噪声基线），`D` = **同 frame 跨臂**对的差异字节数。

| 判定 | 条件 |
|---|---|
| **等价** | 前置 1/2/3/4 全部达成 ∧ 已对齐 ∧ 同 frame 同臂对的 `N == 0`（`CONTENTS` 整流 sha 相等、元数据平面掩码后 0 差异）∧ 同 frame 跨臂对的 `D == 0`。按规格 §3.4 仍须连带作用域限定。 |
| **不等价** | 前置 1/2/3/4 全部达成 ∧ 已对齐 ∧ `N` 稳定（`N==0` 或同臂两对 `N` 一致）∧ `D > N` 且差异可复现（另一同 frame 跨臂对同样 `D > N`）⇒ 给出首个分歧点。 |
| **仍不可判** | 任一前置未达成 / 对齐精度 >1 拍 / 同 frame 同臂样本不足 / `N` 本身不稳（同臂两对 `N` 不一致）/ `D ≤ N` 且 `N>0`（差异在噪声带内）/ 存档对话框未到达 / 真实机阻塞。 |

> 依据 W45 `EQUIVALENCE_SPEC.md` §2.4（`D > N` 才可归因）、§3.4、§3.7（任一不可判 ⇒ 总判定不可判）。**不因「其余量等价」而降级成等价**。

## 6 · 白名单事先声明（规格 §1.4 / §2.5）

- 本卡**开跑前**声明采用的非确定字段白名单 = W54 `SAVE_NONDET_WHITELIST.json` 的 30 个 region / 68 个绝对字节位（3 个 FILETIME 流 + `\x05SummaryInformation` 3 个 VT_FILETIME + Root Entry mtime + DIFAT/#FAT/CONTENTS-size 派生量），副本 `out/whitelist_applied.json`。
- 另有 W45 规格 §2.5 的 **W1/W2/W3** 安装态白名单（`battle_cnt` 的 `k=1` 由 `BATTLEMD98.INI` 的 `15=RA2F1` 事先算出），沿用不扩。
- 白名单外任何字节差异都算候选差异，须由同臂噪声基线裁决。
