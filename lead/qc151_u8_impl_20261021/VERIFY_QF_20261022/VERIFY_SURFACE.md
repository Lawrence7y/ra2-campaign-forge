# U8 补丁面独立核验报告（VERIFY_QF_20261022）

- **核验人**：补丁面核验员（异族复核，只读；未改动任何被核验文件）
- **日期**：2026-10-22
- **基线**：`out/re_work/work_chain/CONTINUE_20261003/lead/qc151_harness_merge_20261021/qc151_trip.harness3.py`
  （408,089 B，sha256 前16 `5c56dac5c17a2ba4`，7,439 行，全 LF，与 RECEIPT §一表格声明一致 ✅）
- **补丁件**：`out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u8_impl_20261021/qc151_trip.harness3_u8.py`
  （416,425 B，sha256 前16 `7db3c11009b7183c`，7,559 行，与 RECEIPT 声明一致 ✅）
- **交付 diff**：`u8.diff`（14,792 B，sha256 前16 `f009c358bd10ab3b`，与 RECEIPT 声明一致 ✅）

## 总体判定：**CONFIRMED（补丁面属实）**，附 2 项交付者自述与磁盘不符的登记性发现（均不影响补丁内容本身）

---

## C1 反向重建 —— **PASS**

**命令 1**（本核验目录 `_verify_c1_diff.py`，`python out/.../VERIFY_QF_20261022/_verify_c1_diff.py`）：
用 `difflib.unified_diff`（上下文 3 行、`lineterm=''`）从两个文件的磁盘字节重建差异，与 `u8.diff` 全文比对：

```
P1 verbatim match (difflib rebuild == u8.diff): True
hunk headers identical (delivered vs rebuilt): True      （来自 _verify_c1b_hunks.py）
```

**命令 2**（`_verify_c1b_hunks.py`，严格 hunk 引擎：逐块解析 `u8.diff` 的 9 个 hunk，先验证每块上侧上下文与基线磁盘字节**逐行相等**，再应用）：

```
num hunks: 9
STRICT APPLY: all 9 hunks applied with context verified
STRICT applied-bytes == patched-bytes: True
```

即：**基线 + u8.diff ⇒ 补丁件，逐字节相等**；且 **u8.diff 与 difflib 重建逐字一致**。
两条方向都闭环：交付 diff 没有漏报任何改动，也没有多报。

> 过程登记：首轮脚本曾报 `HUNK CONTEXT MISMATCH at old line 6579`，经定位是**核验工具自身的解析缺陷**
> （文件以 `\n` 结尾 ⇒ `split('\n')` 末元素多一空行；且 difflib 把空上下文行输出为裸空行而非带前导空格）。
> 修正解析后严格应用全过。与被核验文件无关。

## C2 改动面清单 —— **PASS**（全部可归因于 --allow-loader 通道；含 1 处已登记的缺省路径记录字段变化）

difflib 给出 **16 个改动块**（合并在 9 个 hunk 内），逐块归因（行号 = 基线 → 补丁件）：

| # | 基线 | 补丁件 | 内容 | 归因 |
|---|------|--------|------|------|
| 1 | L341(插入) | L341-384 | 新增 44 行块：`ALLOW_LOADER_EXE` + `allow_loader_authorized()` + U8 依据注释 | 通道本体 |
| 2 | L991 | L1035 | `s4_injection_gate` 签名加 `authorized: bool = False` | 通道 |
| 3 | L1000后 | L1044-1049 | 该函数 docstring 增补 U8 说明（含"授权不放宽枚举失败"声明） | 注释 |
| 4 | L1079后 | L1129-1149 | 命中分支内 `if authorized:` 旁路（落 4 条 rec + `hit_authorized`/EXIT_OK + return True） | 通道 |
| 5 | L1138-1139 | L1209-1210 | `launch_direct` 签名加 `allow_loader: bool = False`；docstring 首行加"缺省路径" | 通道 |
| 6 | L1145 | L1216 | docstring `- 不经批处理、不经 start、不经 loader。` → 删"不经 loader"三字 | 授权后该无条件断言变假，属通道必需修订 |
| 7 | L1147后 | L1218-1226 | docstring 新增 U8 例外说明（含与禁止面 (d) 的区分） | 注释 |
| 8 | L1148-1150 | L1228-1239 | exe 选择：`if allow_loader: exe = carrier_dir / ALLOW_LOADER_EXE` else 原 gamemd.exe；rec 留痕 | 通道核心 |
| 9 | L1152-1153 | L1241-1244 | `via_loader` 由恒 `None` 改为 `bool(allow_loader)`，note 分支 | 记录字段（见下方偏差） |
| 10 | L1180-1181 | L1271-1273 | `resolve_pid` 签名加 `expect_name: str = "gamemd.exe"` | 必要配套（RECEIPT §3.5：授权趟 proc.pid 即 loader，不配则必死 21） |
| 11 | L1191后 | L1283-1293 | 同上 docstring 说明 | 注释 |
| 12 | L1192 | L1295 | `find_pids("gamemd.exe")` → `find_pids(expect_name)`（缺省即原名） | 配套 |
| 13 | L1194 | L1297 | rec note 追加"查询名 = {expect_name!r}" | 记录细节 |
| 14 | L6197后 | L6300-6306 | argparse 注册 `--allow-loader`（`store_true, default=False`） | 通道入口 |
| 15 | L6582 | L6692-6698 | main()：`_u8_authorized = allow_loader_authorized(args, TRIP_ID)` + rec + 传参 | 通道 |
| 16 | L6585-6586 | L6701-6706 | main()：`resolve_pid(..., expect_name=...)`、`s4_injection_gate(..., authorized=_u8_authorized)` | 通道 |

**归因判定**：16 块全部服务于「加 --allow-loader 通道」及其必要配套；无时间常量、无阈值、无顺序调整、无与通道无关的功能改动。`_u8_authorized` 全文件仅 5 处引用（L6693/6694/6698/6703/6706，grep 实证），无扩散。

**登记的偏差（缺省路径并非 100% 逐字相同）**：补丁件 L1047 注释宣称"缺省 False ⇒ 行为与授权前逐字相同"，但第 9 块 `via_loader` 字段在**未授权**时也由 `None` 变为 `False`（记录值变化，无控制流/时序影响；RECEIPT §3.3 已自行披露"由 None 改为 bool"）。属注释措辞与磁盘事实的轻微不符，不构成越权。

**交付者自述 vs 磁盘不符（本项最高优先级发现，两处，均非补丁内容问题）**：
1. RECEIPT L18 称"16 hunk，**+136 / −16**"、RECEIPT L224 又称"u8.diff 的 **12 hunk**"——实测 `u8.diff` 为 **9 hunk，+138 / −18**（计数脚本输出见 C1 运行记录）。两处自述统计互相矛盾且都不等于磁盘值；但 diff **内容**已被 C1 双向闭环证实无漏报。
2. RECEIPT L130 摘录自测输出 `bytes=415282`——磁盘上 `u8_selftest.txt` 及复跑实测均为 `bytes=416425`（陈旧数字，来自改版前的运行）。

## C3 禁止面 —— **PASS**

- 基线禁止面块 L21-35（`QC141:171`，含伪装形态 (a) 批处理 (b) `start` (c) `lpApplicationName` 指 shell (d) 先起 loader 再按名找 gamemd）在补丁件中**零改动**：C2 全部 16 块起点在 L341 之后，`sed -n '15,40p'` 对照两文件同段逐字相同。
- 新增的仅是注释里明说的第 (e) 条：「本通道只新增 (e) 显式授权直启 loader」（补丁件 L354）。
- **缺省启动目标仍是 gamemd.exe**：`launch_direct` 形参 `allow_loader: bool = False`（L1209），else 分支 `exe = carrier_dir / "gamemd.exe"`（L1234）。
- **ra2loader.exe 可达性收口**：全文件 `carrier_dir /` 拼接可执行体的仅两行（L1229/L1234，grep 实证）；L1229 仅在 `if allow_loader:` 内；该形参的唯一调用点 L6697-6698 传 `_u8_authorized`；`_u8_authorized=True` 仅当 `allow_loader_authorized` 双键成立（L6693）。`ALLOW_LOADER_EXE` 的另一处使用 L6703 只是 `resolve_pid` 的**查询名**，不产生启动。
- **无新增进程入口**：全文件 `subprocess.Popen` 唯一实调用点仍是 L1255 `subprocess.Popen([str(exe)], cwd=str(carrier_dir))`（无 `creationflags`、无 shell、参数即 exe 全路径）；复跑 `_u8_selftest.py` 输出 `[2] subprocess.Popen 次数 = 1（要求 1）`。无 `os.system`/`WinExec`/`ShellExecute` 实调用。禁止形态 (a)(b)(c) 无任何代码支撑；(d) 的语义区别（查 loader 自身而非被注入 gamemd）在 L1288-1293 注释中划清，且 `resolve_pid` 确实按 `proc.pid` 绑定。

## C4 fail-closed 结构性 —— **PASS**（12/12 用例实测全过）

读补丁件 L366-384（原文见 C2 清单第 1 块）+ 复跑测试 `VERIFY_QF_20261022/_verify_c4_authorize.py`（对磁盘 L366-384 逐字转写，转写保真度经逐行打印比对确认）：

```
PASS | no flag at all: got=False            ← 不给 --allow-loader ⇒ 拒绝
PASS | allow_loader=True, no trip attr: False
PASS | allow_loader=True, trip_id=None: False  ← 给了 --allow-loader 不给 --trip-id ⇒ 拒绝
PASS | allow_loader=True, trip_id="" : False
PASS | allow_loader=True, trip_id="   " : False
PASS | flag + exact match: True
PASS | flag + match, spaces both sides: True  ← 前后空格归一（L384 两侧 .strip()）
PASS | flag + mismatch: False
PASS | flag + trip_id case differs: False
PASS | args is plain object w/o attrs: False  ← 缺属性不抛异常（getattr 带默认）
PASS | args=None: False                        ← None args 亦安全（getattr(None,…) 返回默认）
ALL CASES PASS: True（共 12 项，含 flag=False+可匹配 ⇒ False）
```

**结构性论断的证明（TRIP_ID 随机性）**：`main()` 内原文（补丁件 L6491-6493）：

```python
    TRIP_ID = (str(args.trip_id).strip()
               if getattr(args, "trip_id", None)
               and str(args.trip_id).strip() else new_trip_id())
```

`new_trip_id()`（L480-483）原文：`"qc151-" + datetime.now().strftime("%Y%m%dT%H%M%S%f") + "-" + str(os.getpid()) + "-" + os.urandom(8).hex()` ⇒ 含 128-bit 随机量，**不可预测**。
故 `--trip-id` 缺省时双重失败：① `allow_loader_authorized` 在 `raw=None` 处直接拒绝（L381-383）；② 即便绕过，随机 `TRIP_ID` 与任何命令行字符串逐字相等的概率可忽略。**fail-closed 论断成立**（且比注释声称的更强：第一道 `raw` 检查已兜住）。调用点唯一：L6693，位于 TRIP_ID 赋值（L6491）之后，无先用后赋问题。

## C5 S-4 闸门语义 —— **PASS**（分支顺序以行号实证）

读补丁件 `s4_injection_gate`（L1035-1168）全文 + 分支扫描脚本输出：

```
gate spans L1035..L1168
names-is-None (enum fail) branch:  L1064: if names is None:
  EXIT_MODULE_ENUM_FAILED:          L1078 / L1085        ← 63 常量定义于 L427
  return False:                     L1101                ← 枚举失败硬停出口
hit branch:                         L1128: if scan["hit_count"] > 0:
authorized check:                   L1132:   if authorized:   ← 授权旁路（L1133-1149，EXIT_OK + return True）
EXIT_INJECTION_SUSPECTED:           L1153 / L1157        ← 62 常量定义于 L426
  return False:                     L1159（未授权命中出口）
```

- **未授权命中 ⇒ 62 硬停**：L1128 命中且 L1132 `authorized=False` 时直落 L1150-1159：`s4_gate="HIT"`、`S4_VERDICT["exit_code"]=62`、`return False`；main() L6706 收 `False` ⇒ 本趟 VOID。✅
- **授权命中 ⇒ 降级放行**：L1132-1149 落 4 条 rec（`u8_authorized_bypass`、`u8_bypass_hits` 含命中明细、`s4_gate="hit_authorized"`、`s4_exit_code=EXIT_OK`）后 `return True`，事后可审计。✅
- **授权不放宽枚举失败**：**顺序 = L1064（枚举失败分支，含 63 收口）→ L1101 return False → L1128（命中判定）→ L1132（authorized）**。`authorized` 在整个 L1064-1101 段内**零出现**（全函数 `authorized` 用法仅 L1035/1045/1046/1132/1133/1142/1146，扫描输出实证）；且该段先于授权检查 return，结构上不可被旁路。✅
- 复跑交付者 `_u8_invariants.py`（exit=0）第 2/4 节同样给出"枚举失败分支在授权之前 ⇒ True / 枚举失败段不含 authorized ⇒ True"，与本行号实证一致。

## C6 时序零改动 —— **PASS**

```
$ grep -n "time\.sleep\|time\.monotonic\|time\.perf_counter\|TIMEOUT\|sleep(" u8.diff
（无输出，exit=1）
```

两文件全量对照：

```
基线   time.sleep=12  time.monotonic=41  time.perf_counter=11
补丁件 time.sleep=12  time.monotonic=41  time.perf_counter=11
diff <(grep 时间相关行 基线) <(grep 同上 补丁件) ⇒ TIMING_LINES_IDENTICAL
（行集含 time.sleep/time.monotonic/time.perf_counter/datetime.now/TIMEOUT，逐行内容零差异）
```

补丁件 `python -m py_compile` 通过。复跑 `_u8_selftest.py` 第 [5] 节：14 个时序函数中仅 `main` 被改，且 `main()` 的时序调用**多重集完全相同**（输出 `[5] main() 时序调用多重集相同 = True`）——与 C2 清单吻合：main 的两处改动（L6692-6706）只插授权判定/传参，不含任何时间操作。✅

## 交付者自带件复跑（一致性）

- `PYTHONDONTWRITEBYTECODE=1 python _u8_selftest.py` ⇒ **exit=0**，输出与 `u8_selftest.txt` 逐行一致（唯 `bytes=416425` 与 RECEIPT 摘录 415282 不符，见 C2）。
- `PYTHONDONTWRITEBYTECODE=1 python _u8_invariants.py` ⇒ **exit=0**，输出与 `u8_invariants.txt` 逐字一致；其中"顺序: hit分支@4277 < authorized@4473 < 62@5526"是**字符偏移**口径，本核验另以行号口径独立复核（C5）。
- 两脚本均为只读（AST + import 调用，补丁件受 `__main__` 守卫，L7558），运行不启动游戏进程。
- 基线纯净性（RECEIPT §二"重建后零 U8 痕迹"）：磁盘基线 `[U8` 计数 = 0、`allow_loader` 计数 = 0 ✅；`build_out2.json` 记录基线 sha `5c56dac5c17a2ba4…`/408089 B 与磁盘一致 ✅。

## 缺项 / 无法核验

- 真机行为（V1–V5、loader 启动 gamemd 的进程树、`find_pids("ra2loader.exe")` 能否命中）：本核验为离线只读，与 RECEIPT §五/§七.5 声明一致，未测即未测。
- "静态自检 #3/#4" 的 AST 校验器本体不在 harness3 内（疑在 `_build.py`/门禁侧，`_build.py` 中仅见 CARRIER_FILES 一处相关行），其完整重放超出本 ask 六项范围；C3 中以"唯一 Popen + 两处 exe 拼接点"的直接 grep 覆盖了同等检查面。

## 结论

补丁面与「仅新增 --allow-loader 双键授权通道」的声称**一致**：diff 双向闭环、改动面 16 块全部归因、禁止面原文未动、fail-closed 12 用例全过、闸门分支顺序结构正确、时序零改动。两处 RECEIPT 自述统计（hunk/+/- 计数、changelog 摘录 bytes=415282）与磁盘不符，均为**描述性/陈旧摘录**问题，不影响补丁本体正确性；`via_loader` 缺省值 None→False 为已披露的轻微记录字段偏差。
