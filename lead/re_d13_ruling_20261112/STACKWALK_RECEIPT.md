# E3 甲案 · StackWalk64 真栈回溯实现与验证（2026-11-12 续二）

> 执行方：调度方（Lead）。用户当轮指令：**「持续推进」**。
> 前置：真机已授权；Wow64 路径与端到端触发链已在前一轮打通。

---

## 1 · 本轮目标与结果

**目标**：把「单帧（只报栈顶 IP）」升级为**真栈回溯**，因为「冻结瞬间栈在哪」这个问题单帧答不了。

**结果**：双架构真机全通。

| 架构 | 帧数 | 实测调用栈 |
|:--|--:|:--|
| **32 位**（charmap.exe） | **6** | `win32u.dll+0x11dc` ← `charmap.exe+0x1155e` ← `charmap.exe+0x1b930` ← `KERNEL32.DLL+0x15d49` ← `ntdll.dll+0x6c75b` ← `ntdll.dll+0x6c6e1` |
| **64 位**（python.exe） | **24** | `ntdll.dll+0x1628a4` ← `KERNELBASE.dll+0x22773` ← `KERNELBASE.dll+0x22641` ← `python312.dll+0x18f38f` ← … |

**注意 32 位那张栈的意义**：`#0 win32u.dll` = 消息循环等待；`#1 #2 charmap.exe+...` = **目标进程自己的代码**；`#3 KERNEL32.DLL` = `BaseThreadInitThunk`；`#4 #5 ntdll.dll` = 线程入口。
⇒ 能定位「目标在哪个模块的哪个偏移处等待」，这正是 E3 要的答案形态。

---

## 2 · 踩到的三个坑（全部是「静默失败」，返回值看不出来）

| # | 坑 | 现象 | 根因 |
|:--|:--|:--|:--|
| **K1** | `STACKFRAME64` 多写了 8 字节 | 永远只回 **1 帧**，且 `StackWalk64` 不报错 | `KDHELP64` 里多一个 `DWORD Reserved0` 字段，使结构变 **272** 而非 **264** ⇒ 后续字段错位 |
| **K2** | `ReadProcessMemory` 回调**少一个参数** | 永远只回 **1 帧** | `PREAD_PROCESS_MEMORY_ROUTINE64` 是 **5 参数**（`hProcess, qwBaseAddress, lpBuffer, nSize, lpNumberOfBytesRead`），我写成 4 个 ⇒ 每次回调抛 `TypeError`，被 ctypes 吞掉，`StackWalk64` 只返回 FALSE |
| **K3** | `SymInitialize(hProc, NULL, FALSE)` | 同样只回 1 帧 | `fInvadeProcess=FALSE` 时 dbghelp 不知道目标加载了哪些模块，拿不到 `.pdata`/FPO 表 ⇒ 无法展开父帧 |

**K1/K2 的教训**：`StackWalk64` 失败时不设 last-error、不抛异常，只是 `return FALSE`。
「只回 1 帧」这个现象对上述三个原因**完全同形**，只能靠逐项排查。
**K2 尤其隐蔽**：ctypes 回调里的异常默认被吞（"Exception ignored on calling ctypes callback function"），
必须主动打开 stderr 才能看见。

---

## 3 · 交付件

| 件 | 规模 | 说明 |
|:--|:--|:--|
| `e3_stackwalker.py` | 新模块 | StackWalker64 封装：结构定义 + 5 参数回调 + `StackWalker` 类 + 模块枚举/命名 + 自证 `selftest()` |
| `e3_stack_sampler_candidate.py` | 51 KB → 更大 | 集成 `attach_stackwalker()`；`_get_context` 返回 `_raw` 原始结构；`_walk` 三级优先级（dbghelp walker / stub / 单帧回退，后者标 `frames_is_single`） |
| `_live_verify_stackwalk.py` | 新 | 双架构 StackWalk64 独立验证（20 项） |

### 3.1 结构尺寸自证（写死在模块里，防回退）

```python
assert ctypes.sizeof(STACKFRAME64) == 264   # K1
assert ctypes.sizeof(KDHELP64) == 112
```

`e3_stackwalker.py --selftest` → 7 项全通过。

---

## 4 · 端到端复验（触发链 + 真栈）

`_live_verify_chain.py` 重跑，**10 项 0 失败**：

```
[OK] B-1 冻结阶段触发恰好 1 次            fired=1
[OK] B-2 触发时真的采到了栈              samples=1
[OK] B-3 采样结果含有效 frames          n=19
[OK] B-4 采样无错误                    []
[OK] B-5 目标位宽判为 32 位             32
      首个栈: tid=3280 bits=32 ip=0x766911dc
[OK] D-1 再次冻结再次触发（共 2 次）        fired=2
[OK] D-2 第二次采样同样无错误             []
结果：10 项检查，0 项失败
```

⇒ **停滞检测 → 采样 → 真栈回溯 → 精确恢复**，全链闭环。

---

## 5 · 顺带修掉的两处

| Bug | 现象 | 修法 |
|:--|:--|:--|
| CLI 里 `attach_stackwalker` 用 `bool(s._target_is32)`，但那一刻它还是 `None` | 用 AMD64 机器类型去回溯 32 位目标 ⇒ `unexpected:OSError` | attach 前用进程句柄先判位宽，再传正确的 is32 |
| `write_e3_output` 序列化 `ctx["_raw"]`（ctypes 结构）失败 | `write_fail:TypeError` | 加 `default=` 处理 ctypes 结构/数组/bytes，只留类型名不丢数据 |

---

## 6 · 边界与未验（如实）

1. **未对 `gamemd.exe` 本体采样**：技术前置（Wow64 + StackWalk64）已全部通过，
   但游戏本体采样涉及启动、状态、存档，应单独批次。
2. **触发链里的「帧号」仍是脚本模拟的**：真接游戏时来源应为 `ReadProcessMemory(G_FRAME=0xA8ED84)`，
   这一步**尚未在真机跑过**。
3. **无符号解析（函数名）**：当前只到「模块名+偏移」，没解析 `SymFromAddr` 拿函数名
   （那需要 PDB/符号服务器，gamemd.exe 无公开符号）。
4. **死锁风险**：已对 charmap/python 等良性目标验证多轮无残留挂起，
   但**未在复杂目标（如游戏）上验证**。
5. **栈的语义解读未做**：拿到 `charmap.exe+0x1155e` 这样的偏移，但没有把它映射回源码/函数语义
   —— 那需要 RE 侧的函数边界知识（re_atlas 的 kb 卷可能有，但本案未接）。
