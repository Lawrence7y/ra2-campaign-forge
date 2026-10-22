## §373　Lead 自查：探针 + harness6 的 41 项机械核验（含 1 处真缺陷修正）

**心跳**：2026-10-22 22:1x–22:4x　**性质**：只读静态核验，**零真机**
**背景**：原计划派异族子代理核验待办 9 / ①-1，子代理被取消 ⇒ 改由 Lead 亲自做**机械可判定**的静态核验。

**★ 结论定位**：本件是 **Lead 自查**，**不是异族 CONFIRMED**。
下轮仍需补一次真异族核验（执行者 ≠ 核验者）。

---

### 一、核验结果：41/41 ALL PASS

| 组 | 项数 | 结果 |
|:--|--:|:--|
| A 组 `_rc4_ab_probe.py`（探针） | 29 | **29/29 PASS** |
| B 组 `qc151_trip.harness6.py` | 12 | **12/12 PASS** |

核验器：`_lead_audit_probe_h6.py`，输出 `LEAD_AUDIT_PROBE_H6.txt`（EXIT=0）。

---

### 二、★★ 自查抓到 1 处**真缺陷**（已修）

**`clean_exit` 在 B 臂存在假绿通道。**

```python
# 修正前
exited = exit_seen or (proc.poll() is not None)
if not exited:
    # loader 派生的情况下 proc 是 loader；直接查 gamemd 是否还在
    exited = not any(p == pid for p in list_procs())
```

问题：**B 臂的 `proc` 是 `rc4_loader.exe`，不是 `gamemd.exe`。**
`proc.poll()` 只能说明 **loader** 退没退。

失败场景：
```
loader 因自身异常先退（CreateRemoteThread 失败 / 被外部杀掉）
  → proc.poll() is not None  → exited = True
  → 但 gamemd 仍在跑
  → clean_exit = True  ⇒ 假绿
```
后果：②-A (c) 的「关窗后 ≤20 s 进程正常退出」判据会被 loader 的状态污染，
**把没退的游戏报成正常退出**。

修正：按臂分流，B 臂**只认 gamemd 的 pid**。

```python
# 修正后
if arm == "A":
    exited = exit_seen or (proc.poll() is not None)
else:
    # ★ 只认 gamemd（pid）已从进程表消失；loader 死活不参与判定
    exited = not any(p == pid for p in list_procs())
rec["exit_judged_by"] = "exit_event|proc.poll" if arm == "A" else "gamemd_pid_only"
rec["loader_alive_at_judge"] = (proc.poll() is None) if arm == "B" else None
```

★ `loader_alive_at_judge` 保留为**诊断字段**（记录 loader 状态有用），
但**不参与** `clean_exit` 的计算。

---

### 三、核验器自身踩到的 4 个坑（全是假红，已修）

| # | 假红原因 | 修法 |
|--:|:--|:--|
| 1 | A2 抓了 `main()` 里的**预检**分支，不是 `one_trip()` 里的真实 pid 解析 | 改为在 `one_trip` 的 AST 节点里找 |
| 2 | A2 又抓了内层 `if not dll_name:` 子分支 | 改为定位 `if arm == "A": ... else: ...` 的 **orelse 体** |
| 3 | A5 搜 `"except"` 子串，命中**注释**「不看 except.txt」 | 剔除注释行 |
| 4 | A5 剔注释后仍命中**紧邻其后的字段名** `rec["except_sha16_after"]`（那是记录 except 变化，不是判据输入） | 只取 `clean_exit` 赋值前 12 行，**不含其后** |
| 5 | A5b 把 `rec["loader_alive_at_judge"] = ... proc.poll() ...` 这条**诊断记录**算进了判据 | 截到第一条 `rec[` 为止 |

**教训**：**核验器的假红与假绿同样有害。** 假红会让人把正确代码改坏；
假绿会放过真缺陷。每一条断言都要问「它到底在断言哪个对象」。

---

### 四、A 组逐项（29 项）

| 项 | 断言内容 | 结果 |
|:--|:--|:--|
| A1 | `--live` 门禁存在；`one_trip` 只在门禁之后被调用（guard@749，call@762） | PASS |
| A2 | B 臂按载体目录匹配 gamemd 取 pid；**无** `pid = proc.pid` 兜底；找不到则 abort | PASS |
| A3 | 无 `startswith` 用于路径归属；`under_carrier` 用 `relative_to` + 捕获 `ValueError` | PASS |
| A4 | 清扫前/收尾前各有枚举器正控；正控失败返回 `ENUM_FAILED` 哨兵（非空 list） | PASS |
| A5 | `clean_exit` 判据窗口不含 `except` 变量；用 `CLOSE_WAIT_S` 时限 | PASS |
| A5b | 按臂分流；B 臂判据语句**不含** `proc.poll()`；只按 gamemd pid | PASS |
| A6 | `safe_name` 拒绝 `..` / `/` / `\`；B 臂强制要求 `--dll` | PASS |
| A7 | 预检与 `one_trip` 两处都查**载体目录**长度；对象是 `str(carrier)` | PASS |
| A8 | `DebugActiveProcessStop`(118) 先于 `a8_sweep`(402) 先于 `rm_carrier`(439)；`own_pid=os.getpid()` | PASS |

---

### 五、B 组逐项（12 项）

| 项 | 断言内容 | 结果 |
|:--|:--|:--|
| B1 | 母本 sha16 `f1e5bc7b0ff30c9c` / 427,456 B | PASS |
| B2 | **零删除行（多重集）**：`removed=0`，母本 7781 行 ⊂ 副本 8451 行 | PASS |
| B3 | WER `Sig[]` 按 `.Name` 读（L1684/L1704）；**不存在** `Sig[0]`/`Sig[1]` 固定索引读 | PASS |
| B4 | 隔离计数函数存在；枚举失败时计数为 `None` 而非 0 | PASS |
| B5 | `near limit 130` WARN 存在；`>=131` 硬停逻辑仍在 | PASS |
| B6 | `close-mode` 默认 `terminate`；记录 `close_fallback_terminate` | PASS |
| B7 | `terminate_owned_process` 函数体与母本**逐字节相同**（各 3494 chars） | PASS |

---

### 六、修正后的探针复跑

```
arm=B 干跑：源 sha16 OK / 源件数 88 OK / 残留进程 0 OK / dump 目录 OK
           rc4_loader.exe OK / ra2rc4guard.dll OK
           载体目录长度 96 ≤ 130 OK / 正控 read=3735928559 OK
```

`py_compile` 通过，零 `.pyc` 残留。

---

### 七、对 §4 待办的影响

| 待办 | 状态变化 |
|:--|:--|
| 9 RC-4 A/B 探针 | ⚠️ **Lead 自查 29/29 过 + 修正 1 处真缺陷**；**异族核验仍欠**（下轮） |
| ①-1 harness6 | ⚠️ **Lead 自查 12/12 过**；**异族核验仍欠**（下轮） |
| ②-A (c) A/B | 前置从「异族核验」缩到「异族核验（1 项）」，其余已就绪 |
