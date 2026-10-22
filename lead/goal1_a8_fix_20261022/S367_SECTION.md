
## §367　裁决 15 已办：A8 验证器加固版（无动态执行 + 副本哈希门禁）

**日期**：2026-10-22　**性质**：离线，零真机。
**对象**：`lead/goal1_a8_fix_20261022/VERIFY_A8.py`（§364 的唯一真缺口）

### 一、为什么这是真缺口（复述 §364）

原 `VERIFY_A8.py` 的两个执行点把「从 `harness4` 副本读出的函数源码文本」
当代码执行。命名空间只注入 `Path`，执行对象是本仓库内自己生成的文件 ⇒ **危害低**，
但存在结构性缺陷：

- K2 只**记录**副本哈希（`LF16 = cd9bbc87e46054af`），**没有与常量比对**。
- 生成器 `_gen_harness4.py` assert 了**母本**哈希，但**副本**哈希在执行点上**无门禁**。
- ⇒ 若 harness4 被改动，K7/K9 会**静默执行改后代码**，并把结果当作
  「A8 补丁合格」的证据。

### 二、处置：新建加固版，**不改**已交付件

铁律 4（母本与在用脚本零改动）⇒ 不修改 `VERIFY_A8.py`（其 sha16 `179f3af88fac3804`
被加固版 pin 住），而是新建
**`lead/goal1_a8_fix_20261022/VERIFY_A8_HARDENED.py`**。

两处加固：

1. **副本哈希门禁**：K7 / K9 在调用被验证函数**之前**比对
   `lf16(COPY.read_bytes()) == "cd9bbc87e46054af"`。不符则**不调用**，该 K 项记 REFUTED。
2. **彻底去掉动态执行**：改用 `importlib.util.spec_from_file_location` +
   `exec_module` 按路径加载副本模块，再 `getattr` 取函数调用。

   ★ 可行前提由 **K11** 断言（不是假设）：副本的模块级语句只有
     import / 常量赋值 / 函数定义 / 受 `if __name__` 保护的入口，
     加上**一处已登记**的刻意调用 `SetProcessDPIAware()`。

### 三、结果：11/11 CONFIRMED，EXIT=0

| 项 | 判定 | 说明 |
|:--|:--|:--|
| K1 | CONFIRMED | 母本 `7db3c11009b7183c` 未变 |
| K2 | CONFIRMED | 副本双哈希 + **★pin `cd9bbc87e46054af`** |
| K3 | CONFIRMED | a8.diff 逐行在副本中；生成器复跑 EXIT=0 |
| K4 | CONFIRMED | 改动面 = 三个新函数 + `main`（属预期） |
| K5 | CONFIRMED | 无 `/IM` 全杀、无注入类 API、**无写权限掩码**、无 winreg 写 |
| K6 | CONFIRMED | `A8_ALLOW_LOADER = [False]` 模块级；赋值在 try 内；finally 引用 |
| **K11** | **CONFIRMED** | **★ 新增：模块级副作用登记** |
| K7 | CONFIRMED | relative_to + 三用例实跑 + ★门禁 + **无动态执行** |
| K8 | CONFIRMED | 负控重跑 6/6 RED、13/13 PASS |
| K9 | CONFIRMED | ast.parse + 符号 + 路径三用例 + ★门禁 |
| K10 | CONFIRMED | 母验证器 sha16 未变；**本文件零动态执行原语**；门禁覆盖 2 处 |

`EXEC GATE SUMMARY`：K7 / K9 副本哈希均 `PASS`。

### 四、本轮踩到的三个「假红」（都是我判据过严，不是补丁有问题）

1. **K4 `changed: ['main']`** —— A8 补丁**本来就要改 `main`**（装配 A8 调用）。
   首版把 `main` 排除在预期改动面之外 ⇒ 假红。已改为
   `EXPECTED_CHANGED = A8_FUNCS | {"main"}`。

2. **K5 `injection APIs: ['OpenProcess']`** —— `OpenProcess` **不是**注入 API。
   它是否危险取决于**请求的访问权限**。实测副本只请求
   `PROCESS_QUERY_LIMITED_INFORMATION` / `PROCESS_VM_READ`（只读查询）。
   已改为：注入类 API 名单去掉 `OpenProcess`；另加「写/改类权限掩码」检查
   （`PROCESS_VM_WRITE` / `PROCESS_VM_OPERATION` / `PROCESS_CREATE_THREAD` /
   `PROCESS_SUSPEND_RESUME` / `PROCESS_ALL_ACCESS` 均须为 0）。

3. **K6 `A8_ALLOW_LOADER[0]=True 处数: 0`** —— 实际写法是
   `A8_ALLOW_LOADER[0] = bool(_u8_authorized)`，不是 `= True`。
   正则写死 `True` ⇒ 假红。已改为捕获任意右值并逐条打印。

### 五、★ K11 的设计要点（避免把刻意设计判成缺陷）

首版 K11 要求「模块级零裸调用」，报出 `L182 SetProcessDPIAware()` ⇒ 假红。
源码注释明确：

> 模块导入即生效 ⇒ 此后 find_main_window/rect_of/click_*/capture_frame
> 读到的坐标全部是**物理像素**（★ 自身进程声明，不触碰任何其它进程）

这是 QC197/P1 的**刻意设计**（DPI 感知），不能判为副作用缺陷。
⇒ K11 改为**副作用登记制**：模块级调用必须全部在 `WHITELIST_CALLS` 里，
出现未登记调用才 REFUTED。

### 六、交付件

| 文件 | EXIT | 断言 |
|:--|:--:|:--:|
| `lead/goal1_a8_fix_20261022/VERIFY_A8_HARDENED.py` | — | — |
| `lead/goal1_a8_fix_20261022/VERIFY_A8_HARDENED.txt` | **0** | **11/11 CONFIRMED，REFUTED=0** |

### 七、诚实边界

- 哈希门禁只保证「跑的是 pin 过的副本」，**不保证副本本身安全**
  （副本由生成器产出，生成器已 assert 母本哈希）。
- `importlib` 会执行**整个模块**（含所有函数定义与那一次 `SetProcessDPIAware`）。
  对「验证一个补丁副本」这个目的，这比只执行单个函数体更贴近真实使用方式，
  但代价是副作用面更大——所以才有 K11 的登记制。
- 本文件与 `VERIFY_A8.py` 是**两份独立实现**，长期存在漂移风险；
  漂移检测靠 K10 对母验证器 sha16 的 pin。
- `VERIFY_A8.py` **保持原样**，其 `VERIFY_A8.txt`（K1–K10 CONFIRMED）**仍然有效**，
  但其中 K7/K9 的「无门禁」缺陷由本文件补上，两份应并列引用。

---
