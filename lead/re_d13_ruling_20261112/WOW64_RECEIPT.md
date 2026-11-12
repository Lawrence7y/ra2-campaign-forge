# E3 甲案 · 32 位采集能力补齐 + 端到端真机验证（2026-11-12 续）

> 执行方：调度方（Lead）。用户当轮指令：**「继续推进」**。
> 前置授权：用户 2026-11-12 明示「D 13 选 c」+「统一真机以及一切操作，可以上传GitHub」。

---

## 1 · 本轮补完的核心能力：`Wow64GetThreadContext`

### 1.1 为什么它是硬前置

`gamemd.exe` 是 **32 位（x86）** 进程。上一轮真机验证已确证：64 位进程中
`GetThreadContext` + `CONTEXT_i386`(716 B) 会**返回成功但字段全零**（静默失败）。
所以采 32 位目标必须换 API —— 这就是 `Wow64GetThreadContext` + `WOW64_CONTEXT`。

### 1.2 结构事实（已实测自证）

`WOW64_CONTEXT` 与 `CONTEXT_i386` **字段偏移完全一致**（716 B；`Eip`@184、`Esp`@196、`Ebp`@180、`EFlags`@192）。
差别只在 API 名与 `ContextFlags`（均为 `0x00010001`）。

### 1.3 真机验证（对 32 位目标，脚本 `_live_verify_wow64.py`）

| 项 | 实测读数 |
|:--|:--|
| 目标 | `C:\Windows\SysWOW64\charmap.exe`，`IsWow64Process=True` |
| 枚举线程 | **7 个** |
| `Wow64GetThreadContext` | **成功** |
| **Eip** | **`0x766911dc`**（32 位地址空间，非零） |
| **Esp** | **`0x003ffb44`** |
| EFlags | `0x00000206` |
| **SegCs** | **`0x23`** —— 32 位 ring-3 代码段选择子（64 位为 `0x33`）⇒ **确证 32 位上下文** |
| 恢复 | `resume=1`，精确还原 |
| **结果** | **0 项失败** |

**过程中踩到的坑（如实记）**：最初拿 `SysWOW64\notepad.exe` 当目标，
`IsWow64Process` 却返回 False —— 实测发现 Windows 把它**重定向**到了
`C:\Program Files\WindowsApps\Microsoft.WindowsNotepad_11.2607.14.0_x64...`（64 位 Store 应用）。
换 `charmap.exe` / `dxdiag.exe` 后正常。**PE 架构与运行时实际架构可能不一致，必须运行时判。**

---

## 2 · 端到端真机采集（双架构全通过）

`--live` 入口已从「拒绝执行」改为「真机采集」，护栏不因授权放宽。

### 2.1 32 位目标

```
pid=37724 n_threads=5 paused_ms=0.0 aborted=False errors=[]
  tid=14056  bits=32 ip=0x766911dc
  tid=40172  bits=32 ip=0x77c1a0bc
  tid=33740  bits=32 ip=0x77c1a0bc
  tid=41876  bits=32 ip=0x77c1a0bc
  tid=15140  bits=32 ip=0x77c187fc
```

### 2.2 64 位目标

```
pid=35024 n_threads=3 paused_ms=0.0 aborted=False errors=[]
  tid=38500  bits=64 ip=0x7ffb365628a4
  tid=37776  bits=64 ip=0x7ffb36565a24
  tid=18776  bits=64 ip=0x7ffb36565a24
```

**两例均 `errors=[]`、`paused_ms=0.0`（低于测量精度，远低于 50ms 约束）、无残留挂起。**
`0x77c...` / `0x766...` 落在 32 位系统 DLL 区、`0x7ffb...` 落在 64 位 ntdll 区 ——
与「空闲消息循环线程停在等待点」的预期一致。

---

## 3 · 本轮修掉的四个真 bug（全部是真机/端到端暴露的）

| # | Bug | 现象 | 根因 | 修法 |
|:--|:--|:--|:--|:--|
| B1 | `IsWow64Process` 传**线程句柄** | 19 线程 ⇒ 19 个 `wow64_query_failed` | 该 API 要**进程句柄**；位宽是进程级属性 | 在 `sample()` 里用进程句柄查**一次**，存 `_target_is32` 供各线程复用 |
| B2 | 预算从 `sample()` 开头起算 | 19 线程目标第一次迭代前就 `budget_exceeded`，采到 **0** 个线程 | `enumerate_threads` 的耗时被算进「暂停预算」 | 预算基准移到**枚举之后**（枚举不挂起任何线程，不该计入）；另加 `--budget`（默认 300ms） |
| B3 | `per_thread_ms=15` 硬编码 | 64 位目标采 1 个线程后 `per_thread_budget_exceeded` | 15ms 对真实 SuspendThread+GetContext 太紧，且与总预算语义重叠 | 默认改 **0（禁用）**，只由 `budget_ms` 承担 C3 的「≤50ms」约束 |
| B4 | `OPS["sleep"]` 在 `bind_real_ops()` 之前调用 | `--live --launch` 直接 KeyError | 绑定顺序错误 | 把 `bind_real_ops()` 提到启动目标之前 |

**另有 1 处设计修正**：`_walk` 原在无 walker 时抛 `walker_not_bound`（fail-late，先挂后败）。
改为**退回单帧**（只报 `ip`，并置 `frames_is_single=True`），
使 preflight 的硬前置收敛为「context 通道可用」——这是真正会导致挂起后失败的依赖。

---

## 4 · 新增 CLI

```
--selftest                                      离线单测（47 项，零真机）
--live --pid <PID>  [--budget MS] [--max-threads N] [--dry-run] [--out DIR]
--live --launch <EXE> [--budget MS] [--max-threads N] [--out DIR]
```

护栏（代码级，非文档级）：
- **L1** 必须显式给 `--pid` 或 `--launch`，不猜目标
- **L2** 拒绝采样自身 pid（返回 4，防自死锁）
- **L3** `--dry-run` 只枚举与判位宽，**不挂起任何线程**
- **L4** 结果写独立目录 `lead/re_d13_ruling_20261112/e3_out/`（MF-8，不碰②读数）
- **L5** 任一步失败只记错误码，**不重试、不强杀**
- **L6** `--launch` 启动的进程在 `finally` 里终止，不遗留

---

## 5 · 离线单测：47 项 0 失败

在原有 44 项上新增：
- `MF4-c/d`：无 walker 时退回单帧（frames 长度 1）且仍无残留挂起
- `AUTH-a/b` 改为断言新护栏：无目标拒绝(2)、自 pid 拒绝(4)

---

## 6 · 边界与未验（如实）

1. **真栈回溯仍未实现**：当前是**单帧**（只报栈顶 IP），不是调用栈。
   要拿完整回溯需 `StackWalk64` + dbghelp + 32 位 `FPO`/`ReadProcessMemory` 回调，属后续工作。
2. **尚未对 `gamemd.exe` 本体采样**：已具备技术前置（Wow64 路径通过），
   但游戏本体采样涉及启动/状态/存档，需按批次单独安排。
3. **触发链条未端到端连通**：`StallDetector`（帧号停推）与 `StackSampler` 仍未在真机上串起来跑过
   —— `--live` 目前是「立即采一次」，不是「等停滞再采」。
4. **死锁风险真实程度仍未验证**：只对 charmap/python 等良性目标验证，未在复杂目标上验证。
5. `paused_ms=0.0` 是**低于测量精度**，不等于「零开销」；真实开销需更细粒度计时。

---

## 7 · 入库

见本轮回执末尾的 git 提交记录。

---

## 8 · 端到端触发链验证（本轮补完）

**目标**：验证「等停滞再采」这条链真的能串起来，而不是「立即采一次」。

脚本 _live_verify_chain.py，对受控 32 位目标（charmap.exe），
由脚本自己模拟帧号源分四阶段：

| 阶段 | 条件 | 期望 | 实测 |
|:--|:--|:--|:--|
| A | 帧号持续递增 1.2s | 不触发 | ✅ ired=0 |
| B | 帧号冻结 2.4s | ~1.0s 后触发 **1 次** | ✅ ired=1，**采到 7 个线程的栈**（ip=0x766911dc, bits=32） |
| C | 帧号恢复递增 1.0s | 不再新触发（段重置） | ✅ ired=1（未增） |
| D | 再次冻结 2.0s | 再触发一次（共 2 次） | ✅ ired=2，第二次采样 rrors=[] |
| S | 安全 | 目标进程存活 | ✅ |

**结果：10 项检查，0 项失败。**

⇒ **E3 甲案闭环打通：停滞检测 → 自动采样 → 精确恢复。**

**边界（必须连带）**：本验证中的「帧号」是脚本内**模拟**的；
真接 gamemd.exe 时帧号来源是 ReadProcessMemory(G_FRAME=0xA8ED84)。
本次验证的是**触发逻辑与采样的串联**，不是游戏帧号读取 —— 后者仍需单独真机批次。
