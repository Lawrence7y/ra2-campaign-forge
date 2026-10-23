# §402　H-6 定谳：`wait_returncode` 的 1 vs 0 是「活着被杀」vs「自己退了」

**性质**：离线（本机实验 + 只读趟产物）。零真机、零游戏启动。

---

## 结论先行

| 登记问题 | 结论 | 依据 |
|:--|:--|:--|
| `terminate()` 打在「还活着」与「已退出」的进程上分别返回什么 | **活着 → 1**；**已退出 → 进程自己的退出码** | 本机实验 P1/P2/P3 |
| A/B 的 `wait_returncode = 1` 是什么 | 进程在 `terminate()` 时**还活着**，被这趟终止 | 实验 + 产物 |
| C/L3 的 `wait_returncode = 0` 是什么 | 进程**已自行退出，且退出码为 0** | 实验 + 产物 |

**一句话**：1 和 0 **不是两种"退出路径"，是两种"进程状态"**——
1 表示"我杀它时它还活着"，0 表示"等我杀它时它已经自己以 0 退出了"。

---

## 一、登记原文与它缺的东西

台账 §397 §八 H-6：

> `wait_returncode` 来自 `proc.terminate()` 后 `proc.wait()` 的返回值。
> 1 vs 0 说明两类趟的退出路径不同，但**本轮未查明** `terminate()` 打在
> 「还活着」与「已退出」的进程上分别返回什么，故只登记现象。

**「未查明」的这件事，本机 3 秒就能测。**

---

## 二、判据从哪来：CPython 源码

`Subprocess.Popen.terminate()`（Python 3.12.10 / MSC v.1943）：

```python
def terminate(self):
    """Terminates the process."""
    # Don't terminate a process that we know has already died.
    if self.returncode is not None:
        return                                  # ★ 已知死 ⇒ 静默返回
    try:
        _winapi.TerminateProcess(self._handle, 1)   # ★ 注意这个 1
    except PermissionError:
        rc = _winapi.GetExitCodeProcess(self._handle)
        if rc == _winapi.STILL_ACTIVE:
            raise
        self.returncode = rc                    # ★ 回填的是**进程自己的码**
```

两个关键点：

1. `TerminateProcess(handle, 1)` 的第二个参数是 **exit code 1**
   ⇒ 被杀死的进程，`wait()` 返回 **1**。
2. 进程若已死，`self.returncode` 已在 `poll()`/`wait()` 里被填成**进程自己的退出码**
   ⇒ 走 `return` 分支静默退出，`wait()` 返回**那个码**，不是 1。

**注**：`terminate()` 里那句 `if self.returncode is not None: return` 只在
调用方**先 poll 过**时才生效。harness 的 `terminate_owned_process`
**全文件零 `.poll()` 调用**（`grep -c "\.poll()"` = 0），所以 `self.returncode`
仍是 `None`，实际走的是 `TerminateProcess` 分支并抛 `PermissionError`，
再被 `except PermissionError` 捕获、回填真实退出码。

**这条路径已实测**（复刻 harness 场景：不先 poll，直接 terminate 已死进程）：

```
returncode 属性（未 poll 时）= None
terminate() 未抛异常                       ← PermissionError 被内部吃掉
之后 returncode = 0                        ← 回填的是进程自己的码
```

⇒ **两条路径的最终结果相同**（都得到进程自己的退出码），但走的是不同分支。

---

## 三、实验（本机实测，非推断）

| 实验 | 进程状态 | `terminate()` 抛异常 | `wait_returncode` |
|:--|:--|:--|--:|
| P1 | **活着**（`poll()=None`） | 无 | **1** |
| P2 | 已自行退出，code 0 | **无**（静默） | **0** |
| P3 | 已自行退出，code **7** | **无**（静默） | **7** |

P3 是关键：如果返回值恒为 1，P3 就该是 1；实测 **7** ⇒ 证明返回值是
**进程自己的退出码**，不是 `TerminateProcess` 的常量。

---

## 四、四趟真实产物

| 趟 | `wait_returncode` | `terminate_sent` | `termination_verdict` |
|:--|--:|:--|:--|
| A `l1_20261023` | **1** | True | PASS |
| B `l1_20261023b` | **1** | True | PASS |
| C `l1_20261023c` | **0** | True | PASS |
| L3 `l3_20261023` | **0** | True | PASS |

对照 H-5（§401）已证的：C 在 measure 阶段（161.75 s）就已死（`ws_kb=20`、RPM 全失败）。
⇒ **C/L3 的 0 = 进程自己以 0 退出**，与 H-5 的"在 terminate 之前已消失"完全一致。

---

## 五、★ 附带发现（超出登记范围，比登记问题更重要）

### 5.1 `terminate_sent=True` 不能证明「终止动作生效」

`terminate_owned_process`（harness `:1369`）：

```python
try:
    proc.terminate()
    rec.add("TERM", "terminate_sent", True, ...)   # ★ 只要不抛就算 True
except Exception:
    rec.add("TERM", "terminate_sent", False, ...)
    return False
```

实验 P2/P3 已证：**对已死进程 `terminate()` 同样不抛异常**。
⇒ 四趟的 `terminate_sent` 全是 `True`，但 C/L3 的进程**根本没被杀**（早就死了）。

**这是一个「否定式不可用」的实例**：不能拿 `terminate_sent=True` 去论证
"进程是被终止的"；反过来也不能拿它去论证"进程被正常关闭"。

### 5.2 `termination_verdict=PASS` 只证明「进程已退出」

`terminate_owned_process` 的返回值语义是「进程退出是否已由本趟句柄确认」，
返回 `True` 的条件是 `proc.wait(timeout=10)` **没超时**。
对已死进程，`wait()` 立即返回 ⇒ `True`。

⇒ 四趟全 PASS，但**只有 A/B 是被杀的**。这个字段回答的是
"进程现在确实不在了吗"，不是"是我送走的吗"。

### 5.3 对 H-5 死因的意义

H-5 说死因"未定谳"。本节把范围**收窄**了一格：

- C/L3 的进程是**以退出码 0 自行退出**的，**不是被 `TerminateProcess` 打死的**
  （后者会留下 exit code 1）。
- 退出码 0 通常意味着 `ExitProcess(0)` / `main` 正常返回。
  ⇒ **"被 TerminateProcess 时序搞死"这个假说被排除**（§397 列的三种可能之一）。

**仍未定谳**：退出码 0 既可能是**正常退出**，也可能是**崩溃处理器自己调了
`ExitProcess(0)`**。Windows 上未处理异常通常给 `0xC0000005` 之类的 NTSTATUS，
但游戏若装了 SEH 兜底并主动退出，也会是 0。
★ 要真正区分，需要 WER 的 `AppCrash` 记录或进程退出时刻的 dump——本轮未做。

---

## 六、验证

`_adjudicate_h6.py`：

- **主检 20/20 PASS**（P 实验 4 项 / T 产物 8 项 / C 推论 4 项 / D 发现 2 项）
- **变异自检 11 条，全覆盖**（`--self-mutation`）
  —— 14 个基线断言**每一个都至少被一条变异杀死**，无恒真式。

| 变异 | 改坏什么 | 击杀 |
|:--|:--|:--|
| MP1 | 伪造「活着时也抛异常」 | P1a |
| MP2 | 伪造「活着时返回 0」 | P1b / P4 |
| MP3 | 伪造「已死时抛异常」 | P2a / D1 |
| MP4 | 伪造「已死时返回 1」 | P2b / P4 / C3 |
| MP5 | 伪造「退出码 7 读成 1」 | P3 / P4 / C3 |
| MP6 | 把 C 趟 rc 改成 1 | T_C / C2 |
| MT2 | 把 A 趟 rc 改成 0 | T_A / C1 / D2 |
| MT3 | 把 C 趟 terminate_sent 改成 False | D1 |
| MT4 | 把 C 的 ws_kb 改成活进程量级 | C4 |
| MT5 | 把 B 趟 rc 改成 0 | T_B |
| MT6 | 把 L3 趟 rc 改成 1 | T_L3 / C2 |

**两处自我推翻**：

1. **C4 初版写成 `rec(..., True, ...)`** —— 判据位置放字面 `True`，
   与前两轮（Q7d）同一个毛病。改为从 `measure_w0.json` **独立判**：
   `units is None and ws_kb < 1024`（不引用 §401 的结论，自己算）。
2. **MP2 的变异目标列了 C1，但 C1 读的是产物**（A/B 的 TERM 记录），
   伪造实验值不会动它 ⇒ 报「未变」。这不是恒真式，是目标列错。
   补 MT5/MT6 专门覆盖 T_B / T_L3 后，覆盖检查才全绿。

---

## 七、诚实边界

1. **实验在本机 Python 3.12.10 上做**，不是游戏进程。但 `subprocess` 的
   `terminate/wait` 语义与进程类型无关，且源码已列（§二）——两者互证。
2. **"退出码 0 = 正常退出"是倾向，不是定论**：SEH 兜底主动 `ExitProcess(0)`
   同样给 0。区分它需要 WER `AppCrash` 或退出时刻 dump，本轮未做。
3. **只覆盖四趟**：本机历史趟里 `_launch_result.json` 记 `wait_returncode`
   的样本就这四趟（10-21 那批发射器不记该字段）。
4. **"被 TerminateProcess 打死"这个假说被排除**，依据是"打死会留 exit code 1"。
   若将来发现某条路径杀进程时传了别的码，此结论需重审。
   （当前 harness 与 libc 均传 1，已核。）
5. **未改动任何 harness 代码**：本件只判定语义，不建议改。
   `terminate_sent` 的命名虽易误读，但它是既有字段，改语义会破坏历史可比性。
