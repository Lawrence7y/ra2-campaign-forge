# harness 进程死亡 fail-fast 补丁（Notion 裁决1 附加项）

- 日期：2026-10-20 17:2x
- 执行：主会话
- 性质：**补丁副本制**，未改在用脚本 `qc151_trip.py`
- 依据：Notion 裁决1 附加项 —— 「harness 要补一条独立缺陷修复（另开项，不阻塞 E1）：进程死亡后 fail-fast，不要再对死 PID 空转 148 秒、产出错误截图。退出码要记进字段」

## 一句话结论

补丁副本 `qc151_trip.failfast.py` 已生成，`py_compile` 通过，9 项结构自检 + 5 项逻辑真值表全过。
L1 那种场景下（t=5.188s 进程死亡），新脚本会在**第 10 次采样（t≈5.1s）** 就 `SystemExit(29)`，
而不是空转到 148 秒。

## 缺陷根因

`qc151_trip.py:6553` 原本就有 `_pid_alive_check(pid)`，但它的返回值**只被写进诊断数组
`_stab_rect_series`**，从不驱动任何控制流：

```python
_stab_rect_series.append({
    ...
    "pid_alive": _pid_alive_check(pid),   # ← 只采集，不判定
})
```

于是 L1 五趟里：进程 t=5.188s 就死了，脚本继续按 `_stab_deadline` 轮询到 148.063s，
采满 240 个点，并在死 PID 上抓了 140 张截图（实际抓到的是桌面左上角 800×600 区域，
因为 `rect_of(hwnd)` 退化后 `ox/oy` 回落 (0,0)）。

## 交付物

| 文件 | 说明 |
|:--|:--|
| `qc151_trip.failfast.py` | **成品补丁副本**（7,322 行；母本 7,321 行 + 净 +1） |
| `failfast.diff` | 相对在用脚本的 unified diff（CRLF） |
| `failfast_report.json` | 插入点表 + 自检结果 |

## 改动（4 处，最小侵入）

| # | 位置 | 内容 |
|:--|:--|:--|
| 1 | `_pid_alive_check` 定义之后（第 4,372 行） | 新增 `_pid_exit_code(pid)` helper：只读 `GetExitCodeProcess`，进程仍活返回 `None` |
| 2 | `EXIT_PID_IDENTITY_UNVERIFIED = 28` 之后 | 新增 `EXIT_PID_DEAD = 29`（**避开已被 `LAUNCH_FAILED` 占用的 20**） |
| 3 | `_esc_sent = 0` 之后 | 新增 `_pid_dead_streak = 0` 初值 |
| 4 | 稳定性轮询里 `if len(_stab_rect_series) < 240: ... else: _stab_series_truncated = True` **之后** | `_pid_alive_now = _pid_alive_check(pid)` 单次取样；字典改用该变量；FAILFAST 判定块 |

### FAILFAST 判定块（核心）

```python
if _pid_alive_now is False:
    _pid_dead_streak += 1
else:
    _pid_dead_streak = 0
if _pid_dead_streak >= 2:
    _dead_ec = _pid_exit_code(pid)
    rec.add("WIN", "pid_dead_failfast", {
        "t_dead": round(time.monotonic() - _stab_t0, 3),
        "pid": pid,
        "exit_code": _dead_ec,
        "esc_sent_before_death": _esc_sent,
        "polls_before_death": _poll,
        "rect_before_death": list(_sr),
    }, "script:_pid_alive_check", note="★ FAILFAST：...")
    raise SystemExit(EXIT_PID_DEAD)
```

**三条设计纪律**：
1. **只在 `is False` 时计数** —— `None` 表示 `OpenProcess` 失败/权限问题，不等于进程已死，不能当死亡。
2. **连续 2 次才触发** —— 单次抖动不误杀。
3. **先 `rec.add` 再 `raise`** —— 退出码与死亡时刻必须落盘，否则事后无法归因（这正是裁决要求的「退出码要记进字段」）。

## 自检实跑

### 结构自检（9/9）

```
lines: 7322
EXIT_PID_DEAD_defined      : true      (EXIT_PID_DEAD = 29)
failfast_block_present     : true      (FAILFAST-BEGIN 标记在位)
pid_alive_now_used         : true      (_pid_alive_now 单次取样)
pid_dead_streak_init       : true      (_pid_dead_streak = 0)
raise_systemexit           : true      (raise SystemExit(EXIT_PID_DEAD))
rec_add_field              : true      ("pid_dead_failfast" 字段)
old_pid_line_removed       : true      (重复调用已删)
no_stage_timeout_change    : true      (STAGE_TIMEOUT_S = 150 未动)
```

`python -m py_compile qc151_trip.failfast.py` ⇒ **PY_COMPILE_OK**

### 逻辑真值表（5/5）

| 用例 | 触发 | 期望 | 结果 |
|:--|:--|:--|:--|
| L1 实况 `[True×8, False×20]` | True @ 第 10 次 | True | ✅ |
| 单次 False 不连续 | False | False | ✅ |
| `None` 不当死亡 | False | False | ✅ |
| 一开始就死 `[False, False, ...]` | True @ 第 2 次 | True | ✅ |
| 一直活着 `[True×240]` | False | False | ✅ |

## 开发过程中修掉的 2 个自身 bug（如实记录）

1. **重复 `if` 行**：`new_append_start` 里同时含 `if len(...)` 与新增赋值行，而锚点又插在同一个 `if` 前
   ⇒ 产物出现两行相同的 `if`，`IndentationError`。改成只插 1 行。
2. **`else` 被拆开（更危险，语法能过、语义错）**：FAILFAST 块最初插在 `})` 之后，
   导致原来的 `else: _stab_series_truncated = True` 粘到了新 `if _pid_dead_streak >= 2:` 上。
   `py_compile` **不报错**，但语义完全错位。改插到 `_stab_series_truncated = True` 之后。
   **教训：语法检查不足以验证补丁正确性，必须读插入点上下文。**

## 未覆盖

- **未真机**：本轮只做文本层补丁 + 静态/逻辑验证，未跑任何一趟。
- **未与 QC151FS 全屏路径交互测试**：fail-fast 在 `_QC151FS["on"]` 判据之前，两者独立；但真机需确认全屏下
  `_pid_alive_check` 的取样频率不受影响。
- **退出码 29 尚未在任何判读表/文档中登记**：若采用，需同步更新 `QC161` 卡面的退出码表与
  任何按退出码分支的上游脚本。

## 施用步骤（待批准）

```bash
cd D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc151_u0400_trip
copy qc151_trip.py qc151_trip.py.pre_failfast
copy ..\qc151_failfast_20261020\qc151_trip.failfast.py qc151_trip.py
python -m py_compile qc151_trip.py
```

## 复现

```bash
cd D:\Project\ra2forge-audittools\scratch_failfast
python patch_failfast.py --root D:/Project/ra2-campaign-forge
```
