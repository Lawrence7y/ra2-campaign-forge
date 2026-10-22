# A8 修复 · 实现者自述（补充件）

> **说明**：本目录的 `A8_VERDICT.md` 现为**独立核验员的判定书**（它覆盖了本卡首版同名文件）。
> 本文件是**实现者侧自述**的存档，供对照。核验员判定为 **CONFIRMED（REFUTED=0）**。
> 实现者自述里有一处**已被核验纠正的错误**，见 §3.3（已在本文件修正）。

**日期**：2026-10-22　**性质**：离线补丁副本，**未部署、未真机**
**依据**：Lead 裁决 3（10-22）
**母本**：`qc151_u8_impl_20261021/qc151_trip.harness3_u8.py`
　　LF sha16 `7db3c11009b7183c`　**零改动**

---

## 0. 结论

A8 已实现为**补丁副本** `qc151_trip.harness4.py`（+160 行，**零删除行**）：

- 收尾按**载体目录**精确清扫 `gamemd.exe` / `ra2loader.exe` 残留（**不按名全杀**）；
- 清扫后**再枚举一次**断言零残留，非 0 ⇒ `note_cleanup_failure(EXIT_TERMINATE_FAILED)`
  ⇒ 退出码非 0 ⇒ **该趟判 V-fail**（满足裁决 3 第 2 条）；
- 仅在 `--allow-loader` 授权趟生效；**非授权趟行为逐字不变**。

---

## 1. 缺陷与修法

### 1.1 缺陷

```python
# 母本 launch_direct()：授权趟 exe = carrier/ra2loader.exe
proc = subprocess.Popen([str(exe)], cwd=str(carrier_dir))
token.register_proc(proc)      # ← 记的是 loader 的 pid

# 母本 finally：
terminate_owned_process(rec, term_proc, term_pid, term_ct)
# ⇒ 只终止 loader；loader 派生的 gamemd.exe 残留
```

母本第 47 行铁律：`taskkill` **非本卡自己 `Popen` 的 pid**（★ 只杀 `self.launch_pid`）。
⇒ A8 不能靠"放宽铁律"实现，必须回答**定义问题**：
「本趟创建的载体里的子进程算不算本趟自己的」。

### 1.2 修法（不动铁律，只补定义）

新增 `a8_sweep_carrier_processes(rec, carrier_dir, own_pid)`：

1. 用既有 `find_pids()` 枚举 `gamemd.exe` + `ra2loader.exe`（**只读枚举**）；
2. 对每个候选用 `QueryFullProcessImageNameW` 取**可执行文件全路径**；
3. 用 `_a8_path_under_carrier` 判定是否落在**本趟载体目录**下（`Path.relative_to`）；
4. 只对"落在本趟载体下、且不是本趟自己的 pid"的进程 `TerminateProcess`；
5. 最多 3 轮（子进程退出可能滞后），每轮 0.8 s；
6. 最后**再枚举一次**，仍落在载体下的记为 `remaining`；非空 ⇒ 记账 ⇒ 退出码非 0。

**为什么不动铁律**：不按名杀、不杀身份不明的 pid，只杀**可执行文件路径落在本趟自建载体目录内**的进程。
与既有先例 `u8_v1v2_probe.py:196-220` 同口径。

---

## 2. 补丁结构（4 个 hunk）

| hunk | 位置 | 内容 |
|--:|:--|:--|
| 1 | `terminate_owned_process` 之后 | 新增三个函数（约 140 行） |
| 2 | 模块级 `LAUNCH_TOKEN` 之后 | 新增 `A8_ALLOW_LOADER = [False]` |
| 3 | `main()` 内 `_u8_authorized` 赋值后 | `A8_ALLOW_LOADER[0] = bool(_u8_authorized)` |
| 4 | `main()` 的 `finally` 终止块之后 | 清扫 + 断言 + 记账 |

### 2.1 ★ hunk 2/3 为什么必须存在（本轮踩的坑）

首版直接写 `if allow_loader_flag:` —— **该名字不存在**（真实名是 try 内的 `_u8_authorized`）。
若照首版部署，`finally` 会 `NameError`，**收尾本身崩掉**，比原缺陷更糟。

更隐蔽：即便写对名字 `_u8_authorized`，它也是 `main()` **try 块内**的局部变量。
若在它赋值**之前**抛异常（母本冻结失败 / 预算超限 / argparse 失败），`finally` 引用它同样 `NameError`。

⇒ 必须用**模块级容器**，与既有 `FINALIZE_CODE` / `TRIP_CARRIER` / `LAUNCH_TOKEN` 同范式。
生成器已加两条自检（自检 5、6）专门防这个回归。

---

## 3. 核验结果

### 3.1 生成器自检（`_gen_harness4.py`，EXIT=0）

| 自检 | 结果 |
|:--|:--|
| 母本 LF sha16 == `7db3c11009b7183c` | PASS |
| 4 个 anchor 各唯一命中 | PASS（4/4） |
| `ast.parse` 通过 | PASS |
| 4 个新增符号存在 | PASS |
| 母本 5 条关键约束仍在 | PASS |
| A8 守卫为模块级（自检 5） | PASS |
| `A8_ALLOW_LOADER` 顺序 decl < assign < guard（自检 6） | PASS |
| **零删除行** | PASS（removed lines: 0） |

### 3.2 负控（`_a8_negctl.py`，EXIT=0，13/13，**6/6 全红**）

| 段 | 做法 | 实测 |
|:--|:--|:--|
| N-1 | 母本哈希改位 | ✅ 红 |
| N-2 | 守卫换成 try 局部名 `allow_loader_flag` | ✅ 红 |
| N-3 | 删掉 `A8_ALLOW_LOADER = [False]` | ✅ 红 |
| N-4 | 删一行母本内容 | ✅ 红 |
| N-5 | 删 A8 清扫函数定义 | ✅ 红 |
| N-6 | A8 块塞回 `if _u8_authorized:` | ✅ 红 |

### 3.3 路径归属边界测试（`_test_path_scope.py`，EXIT=0，13/13）

| 用例 | 期望 | 实测 |
|:--|:--|:--|
| 载体 `C:\t\abc`，进程 `C:\t\abc\gamemd.exe` | True | ✅ |
| 载体 `C:\t\abc`，进程 `C:\t\abcd\x.exe` | **False**（startswith 陷阱） | ✅ |
| 载体 `C:\t\abc`，进程 `C:\Windows\system32\x.exe` | False | ✅ |
| 空 / None 路径 | False | ✅ |
| 正斜杠变体 | True | ✅ |
| 同前缀兄弟目录 `C:\t\abc-x\y.exe` | False | ✅ |
| 实现用 `relative_to` 而非 `startswith`（只看**代码行**） | True | ✅ |
| 清扫先判路径再杀 / 无 `taskkill` 全杀 / 排除自身 pid / 重新枚举断言 | True | ✅ |

#### ★ 本节首版有错，已被核验纠正（如实保留）

首版写「`Path.relative_to` 在 win32 是**大小写敏感**的字符串比较，故 `C:\T\ABC` 会判 True 属"意外"」。
**这是错的。** 实测：

```
Path(r"C:\T\ABC\gamemd.exe").relative_to(Path(r"C:\t\abc"))  ->  gamemd.exe   （成功）
```

win32 上 `Path` 是 `WindowsPath`，其 `relative_to` 用 `_str_normcase`（等价 `os.path.normcase`）
比较 ⇒ **大小写不敏感**，与 NTFS 语义一致。⇒ **不存在"大小写导致漏杀"的局限**，这是正确行为。

**错误来源**：我把 `PurePosixPath` 的行为套到了 `WindowsPath` 上，**未实测就下结论**。
这正是异族核验的价值 —— 核验员实跑后纠正了它。

### 3.4 异族核验（`VERIFY_A8.py`，EXIT=0）

**K1–K10 全 CONFIRMED，REFUTED=0。** 逐项：母本零改动 / 副本双哈希 / 反向重建逐字节 /
AST 零改动面 / 禁止面 / 作用域 / 路径归属 / 负控有效性 / 合成冒烟 / 附加风险审查。

核验员另指出两条**真实缺口**（不构成 REFUTED，但必须记）：

1. **`find_pids` 快照失败 ⇒ 空表 ⇒ false-PASS 通道**。若 `CreateToolhelp32Snapshot` 失败，
   `find_pids` 返回空 list，A8 会把"枚举失败"误判为"零残留"。**建议加正控探针**
   （枚举一个必然存在的进程名，确认枚举器本身工作）。
2. 核验员发现并**纠正了实现者 §3.3 的大小写错误**（见上）。

---

## 4. 交付件与哈希

| 文件 | 字节 | LF sha16 | CRLF sha16 |
|:--|--:|:--|:--|
| `qc151_trip.harness4.py`（补丁副本） | 424,078 | `cd9bbc87e46054af` | `896f45f1dcb474f5` |
| `_gen_harness4.py`（生成器） | 17,271 | `a695de00d9c98f80` | `05b10394beba6973` |
| `a8.diff` | 9,330 | `363cebf89bcda373` | `8e412b5b5a4086be` |
| 母本（**未改**） | 416,425 | `7db3c11009b7183c` | — |

---

## 5. 未做 / 待办

| 项 | 状态 |
|:--|:--|
| 异族核验 | **✅ CONFIRMED（K1–K10）** |
| 真机验证（loader 派生的 gamemd 确实被清扫） | **待用户在场** |
| 部署 | **未部署**（等真机时段，走 ③ 规程） |
| `find_pids` 枚举失败的 false-PASS 缺口 | **待修**（加正控探针） |

---

## 6. 诚实边界

- 本卡只做**静态 + 内存级**验证，**未在真机跑过**。清扫逻辑是否真能杀掉 loader 派生的
  gamemd，只有真机趟能证明。静态能证明的是：判据正确、路径边界正确、失败会记账。
- `remaining` 断言依赖 `find_pids` 枚举完整性 —— 这是**已知残留缺口**（见 §3.4 第 1 条）。
- 未使用 `--no-verify`；未跑 `build.bat`。
