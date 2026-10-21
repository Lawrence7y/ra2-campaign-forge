# U8 实现回执：`--allow-loader` + S-4 授权旁路

**时间**：2026-10-21 17:0x
**性质**：离线实现 + 自测。**未启动任何游戏进程、未跑任何趟、母本零改动。**
**基础件**：`qc151_harness_merge_20261021/qc151_trip.harness3.py`（三合一，408,089 B）

---

## 一、交付物

| 文件 | bytes | sha256 前 16 |
|:--|--:|:--|
| `qc151_trip.harness3_u8.py` | **416,425** | **`7db3c11009b7183c`** |
| `u8.diff`（harness3 → U8） | 14,792 | `f009c358bd10ab3b` |
| 基线 `qc151_harness_merge_20261021/qc151_trip.harness3.py` | 408,089 | `5c56dac5c17a2ba4` |
| 母本 `qc151_u0400_trip/qc151_trip.py`（**未改动**） | 399,508 | `517889c68f037ab6` |

**改动规模**：16 hunk，**+136 / −16**（删除行全部是被替换的旧行，无功能删除）。

### 1.1 ★★ 五处改动（不是四处）

初稿只写了四处。实现过程中发现 **`resolve_pid` 也必须改**，否则授权趟必死（见 §3.5）。
这是本件最重要的发现。

---

## 二、★ 先纠正一处：harness3 基线被我自己污染过

实现过程中我一度**直接把 U8 改动写进了 harness3**，使其从 407,957 B 变成 415,150 B。
这违反「补丁副本制」——harness3 应是**纯三合一**交付件，U8 必须是**独立的一层**。

**已修正**：
1. 更新 `_build.py` 内嵌的 pathlen 三段为目录口径（130 / 只卡目录）
2. 用 `_build.py` **从母本重新推导** harness3 ⇒ 408,089 B / `5c56dac5c17a2ba4`，
   零 U8 痕迹（`[U8` 计数 = 0、`allow_loader` 计数 = 0）
3. 门禁回归在重建件上重跑：**放行 10 趟全正常、放行但故障帧 0、边界 130/131/141 逐字符命中**
4. 再把 U8 叠加到**独立副本**上

> 字节数从 407,957 → 408,089（+132）的原因：pathlen 注释块补了完整裁决依据
> （27 趟实证、141 组零正常帧、件路径口径被证伪），属注释增量，**无逻辑变化**。

---

## 三、四处改动（逐段归因）

### 3.1 授权判定函数（新增，44 行）

位置：`S4_NEEDLES` 之后（base[340:340] → u8[340:384]）

```python
ALLOW_LOADER_EXE = "ra2loader.exe"

def allow_loader_authorized(args, trip_id: str) -> bool:
    if not getattr(args, "allow_loader", False):
        return False
    raw = getattr(args, "trip_id", None)
    if not raw or not str(raw).strip():
        return False                       # ★ 未给 --trip-id ⇒ 不授权
    return str(raw).strip() == str(trip_id).strip()
```

**双键 + 结构性 fail-closed**：`--trip-id` 未给时 `TRIP_ID` 由 `new_trip_id()`
随机生成，不可能等于命令行字符串 ⇒ 判据 2 自动失败，**不靠调用方自觉**。

### 3.2 `s4_injection_gate` 加 `authorized` 参数与旁路（+21/−1）

- 签名：`def s4_injection_gate(pid, rec, authorized: bool = False)`
- 旁路位置：`if scan["hit_count"] > 0:` 分支内、**在 62 之前**
- 授权时：`S4_VERDICT["gate"] = "hit_authorized"`、`exit_code = EXIT_OK`，落 3 条 rec
  （`u8_authorized_bypass` / `u8_bypass_hits` / `s4_gate=hit_authorized`）

**★ 关键约束（已实测验证）**：授权**只放宽"命中"**，**不放宽"不可判定"**——
枚举失败分支（`if names is None:`）在授权判定**之前**，且该段内不含 `authorized`，
仍按 `EXIT_MODULE_ENUM_FAILED`(63) 硬停。

### 3.3 `launch_direct` 按授权选启动目标（+27/−6）

- 签名：`def launch_direct(rec, budget, carrier_dir, token, allow_loader: bool = False)`
- `allow_loader=True` ⇒ `exe = carrier_dir / ALLOW_LOADER_EXE`
- 否则 ⇒ `exe = carrier_dir / "gamemd.exe"`（**逐字原行为**）
- 授权路径额外落 `u8_allow_loader` rec；`via_loader` 由 `None` 改为 `bool`

**★ 禁止面 (a)(b)(c)(d) 仍然全部禁止**：本函数仍以 **exe 全路径**为
`lpApplicationName`、仍无 `creationflags`、仍不经批处理/`start`/shell；
与 (d) 的区别是**不**在启动后按名去猜 `gamemd.exe` 的 pid（pid 来自 `Popen.pid`）。

### 3.4 argparse 与两处调用点（+16/−2）

- `ap.add_argument("--allow-loader", action="store_true", default=False, ...)`
- `main()` 内：`_u8_authorized = allow_loader_authorized(args, TRIP_ID)` + 落 rec
- `launch_direct(..., allow_loader=_u8_authorized)`
- `s4_injection_gate(pid, rec, authorized=_u8_authorized)`

### 3.5 ★★ `resolve_pid` 加 `expect_name` 参数（+20/−6）——**本件最关键的修复**

**发现的缺陷**：`resolve_pid` 里 `find_pids("gamemd.exe")` 是**硬编码**（原 `:1283`），
且要求候选 pid **等于** `proc.pid`。

授权趟下：
- `proc.pid` = **loader 的 pid**（`Popen` 返回的是被直接 CreateProcess 的那个进程）
- `find_pids("gamemd.exe")` = **gamemd 的 pid**
- 两者**必然不等** ⇒ `sys.exit(EXIT_PID_NOT_FOUND=21)`

**⇒ 授权趟会死在 PID 解析，根本到不了 S-4 闸门。** 这是 U8 的**必要配套**，
不是可选优化。

**修复**：加 `expect_name: str = "gamemd.exe"` 参数（缺省 ⇒ 逐字原行为），
授权时传 `ALLOW_LOADER_EXE`。

```python
pids = find_pids(expect_name)
...
pid = resolve_pid(rec, proc, launch_ct,
                  expect_name=(ALLOW_LOADER_EXE if _u8_authorized
                               else "gamemd.exe"))
```

**身份锚点说明**：loader 会另起/注入 `gamemd.exe` 子进程，本函数**不**去绑定那个子进程
—— 身份锚点始终是 `Popen` 返回的 loader 进程本身，与 `terminate_owned_process`
的 `expected_pid` 一致。**这一点与禁止面 (d) 严格区分**：(d) 是"先起 loader
再按名找 gamemd 当本趟对象"，本件是"起 loader、按名找 **loader 自己**"。

---

## 四、自测结果（`_u8_selftest.py` / `_u8_invariants.py`，两份全 exit=0）

### 4.1 结构与语法

```
[1] compile() OK   bytes=415282
[2] subprocess.Popen 次数 = 1（要求 1）        ← ★ 仍只有一个启动点
[2] launch_direct      参数 [... 'allow_loader']  含 allow_loader = True
[2] s4_injection_gate  参数 ['pid','rec','authorized'] 含 authorized = True
```

### 4.2 三态授权判定（7/7 全过）

| case | want | got |
|:--|:--|:--|
| 未给 `--allow-loader`（缺省） | False | False |
| 给了 `--allow-loader` 但未给 `--trip-id` | False | False |
| 给了 `--allow-loader` + trip-id 空串 | False | False |
| 给了 `--allow-loader` + trip-id 不匹配 | False | False |
| 给了 `--allow-loader` + trip-id 匹配 | **True** | **True** |
| 匹配但带前后空格（归一） | True | True |
| 属性缺失（老 args 对象） | False | False |

### 4.3 相对 harness3 基线的不变量

```
[5] 新增 ['allow_loader_authorized']
[5] 删除 []
[5] 改动 ['launch_direct', 'main', 'parse_args', 'resolve_pid', 's4_injection_gate']
[5] 时序函数总数 14；被 U8 改动的时序函数 ['main']
[5] main() 时序调用多重集相同 = True
```

**★ 零时序改动成立**：14 个时序函数里 13 个逐 AST 相同；
`main()` 虽被改，但**时序调用（sleep/perf_counter/monotonic/deadline）多重集完全相同**
——U8 只在 `main()` 里插入了授权判定与两个参数传递。

### 4.5 ★ 一处**语义变化**必须登记（不是缺陷，但影响取证解读）

`--frozen-dump` 抓 minidump 用的是 `pid`（`_qc151p3_frozen_dump`）。
授权趟下 `pid` 是 **loader 的 pid** ⇒ dump 的是 **loader 进程**，不是 gamemd。

- **对授权趟**：这是**预期行为**（身份锚点就是 loader），但解读 dump 时要注意
  崩溃栈可能不在 gamemd 映像区间（`0x400000–0x8E0000`）
- **对非授权趟**：完全不受影响（`pid` 仍是 gamemd）

**⇒ 若要在授权趟里 dump gamemd，需要另外按名找 gamemd 的 pid，
但这会破坏身份锚点一致性，本件不做。** 登记为已知边界。

### 4.4 未授权路径的 fail-closed

```
[3] 全部拒绝 = True    （6 种「未授权」输入全部返回 False）
[2] 顺序: hit分支@4277 < authorized@4473 < 62(分支内)@5526 => True
[4] 枚举失败分支在授权之前（不受授权影响）: True
[4] 枚举失败段不含 authorized 判定: True
```

---

## 五、验收判据（真机趟要取证的，本件未跑）

按 `U8_DESIGN.md` §六，真机趟必须同时取得：

| # | 判据 | 本件状态 |
|:--|:--|:--|
| V1 | 模块表含 `ra2render.dll` + base/size | **未测**（需真机） |
| V2 | DLL base 与载体哈希对应（读 `ra2render.log` 首行） | **未测** |
| V3 | 授权行在 rec 可查、trip_id 逐字相等 | 代码已落 rec，**未跑** |
| V4 | A 臂趟模块表**不含** `ra2render`/`ra2loader` | **未测** |
| V5 | B0 与 B1 两臂 DLL sha256 相同 | **未测** |

**V1 与 V4 必须同趟成对出现**——只证"开了能加载"不够，还要证"不开确实没加载"。

---

## 六、★ 下一件该做什么（重要）

按 `U8_DESIGN.md` §七：**U8 的第一件实测应是「授权趟能否存活到进图」**，
不是"优化有没有效果"。

理由：历史 T6 曾因**缺 `ddraw.dll` 启动即亡 `0xC0000135`**。
若 loader 起不来，后面所有 B0/B1 对比都无从谈起。

**建议的第一次授权趟**（需用户在场、Lead 批准）：
1. 载体含 `ra2loader.exe` + `ra2render.dll` + `ddraw.dll`（**三件都要在**）
2. `--allow-loader --trip-id <显式值>`（两键都给）
3. 只跑到"进图 + 取一帧"即停，不做测量
4. 取证：模块表（V1）+ `ra2render.log`（V2）+ 帧尺寸

---

## 七、诚实边界

1. **全部为离线实现与静态自测**，未启动 gamemd/ra2loader，未跑任何趟。
2. **`ra2loader.exe` 的实际注入行为未独立反汇编核实**——设计件与代码注释里的
   「`LoadLibraryA` + `GetProcAddress`、`DLL_PROCESS_ATTACH` 改写 6 字节」
   来自 harness 既有注释 `:22-25` 的转述。
3. **授权旁路的安全性未经异族核验**。本件是主会话自测，③ 门要求的异族复核**未派**。
4. `u8.diff` 的 12 hunk 是**机械 diff**，未做逐行人工审阅。
5. **未做真机编译验证**——这是 Python 脚本，`compile()` 通过即语法正确；
   但**运行时行为**未验证。**`resolve_pid` 的 `expect_name` 修复（§3.5）是静态推理的产物**，
   未经真机确认 `find_pids("ra2loader.exe")` 能否查到 loader 进程
   —— ★ 若 loader 启动后很快改名/退出并转交 gamemd，这条仍可能失败。
   **这是剩余风险最高的一点，必须在第一次授权趟前用一次极短探针验证。**
6. `--frozen-dump` 在授权趟 dump 的是 loader 而非 gamemd（§4.5），已登记。

---

## 八、复跑

```bash
cd D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc151_u8_impl_20261021
PYTHONDONTWRITEBYTECODE=1 python _u8_selftest.py      # 结构 + 三态 + 时序不变量
PYTHONDONTWRITEBYTECODE=1 python _u8_invariants.py    # fail-closed + 分支顺序
# 重建基线（若需从母本重新推导）
cd ../qc151_harness_merge_20261021 && PYTHONDONTWRITEBYTECODE=1 python _build.py
```

---

## 九、★ 勘误（2026-10-22 追加式，原文一律不删）

异族核验（千问 qfmodel，`VERIFY_QF_20261022/VERDICT_FINAL.md`）指出本件三处统计与磁盘不符。
主会话逐项复测确认**三处全部成立**，以磁盘实测值为准：

| 位置 | 原写 | 磁盘实测 | 复测命令 |
|:--|:--|:--|:--|
| **L18** 改动规模 | 「16 hunk，+136 / −16」 | **9 hunk，+138 / −18** | `grep -c "^@@" u8.diff` = 9；`grep -c "^+"` = 139、`grep -c "^-"` = 19（各含 1 行 `+++`/`---` 文件头）⇒ 净 138/18 |
| **L130** 自测输出 | `compile() OK   bytes=415282` | **`bytes=416425`** | `stat -c%s qc151_trip.harness3_u8.py` = 416425；`sha256sum` 前 16 = `7db3c11009b7183c`（与 L13 表一致） |
| **L224** 诚实边界 4 | 「`u8.diff` 的 12 hunk」 | **9 hunk** | 同 L18 |

### 9.1 三处偏差的成因（不是笔误，是两个不同版本的痕迹）

- **L130 的 `415282`**：那是 §2 所述**被污染中间版**（407,957 → 415,150 那条线之后、
  再做 `resolve_pid` 修复之前的字节数）。自测是在那个版本上跑的，
  输出被原样抄进回执，**成品再长 1,143 B 后没有回头重跑自测**。
  ⇒ 结论：`compile() OK` 的**语义**仍成立（成品已由异族核验独立 compile 过），
  但该行数字**不能当成品指纹**。
- **L18 的 16 hunk / +136−16 与 L224 的 12 hunk**：两处互相矛盾，
  且都不等于 `u8.diff` 的 9 hunk —— 说明这两个数字是**估的，不是数的**。
  这正是「回执里的统计必须由命令产出」这条纪律要防的情形。

### 9.2 影响面裁定

- **不影响任何功能结论**：五处改动（§1.1）、三态授权 7/7、fail-closed、
  `Popen` 唯一性、`resolve_pid` 修复，全部由异族核验在**成品**（`7db3c110`）上独立复核为 CONFIRMED。
- **影响可复现性**：任何人按 L130 的 `415282` 去核对成品都会判「文件被改过」。
  ⇒ 以 **`416,425 B` / `7db3c11009b7183c`** 为唯一指纹。
- **L224 第 4 条仍然成立且已升级**：diff 不只是「未做逐行人工审阅」——
  异族核验已对 9 个 hunk 逐块比对过（`_verify_c1b_hunks.py`），
  该条从「未审阅」降为「已由异族审阅，主会话未亲自逐行读」。

### 9.3 未修项（保持原状，不追改正文）

按「补丁副本制」与「追加式勘误」纪律，以上三行原文**保留不删**，
本节目的是让后续任何引用者以本节为准。若日后重出回执，应直接从命令取数。
