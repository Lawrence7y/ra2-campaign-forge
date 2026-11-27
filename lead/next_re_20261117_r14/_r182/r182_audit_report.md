# R182 审计报告 · C20 判据的独立性与边界（只读）

- 角色：跨家族审计员（audit / deepseek 家族）
- 待审对象：`lead/next_re_20261117_r14/check_disc.py:1177-1247`（`# ---- C20` 至 `# ---- C5 CR` 之前）
- 被审文件指纹：`check_disc.py` 1271 行，sha256 `365f000394917593cea988c97d7b2ec973f67b8a9c29df57b4f7bbc5fc38c461`
- 取证方式：**全部只读**。未运行 `check_disc.py`、未运行 `gate_runner.py`、未创建任何 /tmp 镜像、未删除任何文件。破坏性判别矩阵（B1/B6）全部在**内存字符串**上跑正则/AST，未落盘。
- 生产态基线（本次审计全程未变，可事后复算）：
  - `_r160/facts_floors.py` 26147 B，sha256 `ed717d13f700dd8855f90cca04637afc76103c022748068918281ce4d503108e`，mtime 1795766783，islink=False
  - `_r161/gate_runner.py` 20268 B，sha256 `5fe108f54a2532670d34320588f102ee679b8a96ac820439c95fd7f8c358e56f`，mtime 1795764534，islink=False

---

## B1 · (d) 的正则能抓住什么、抓不住什么

**正则原文**（`check_disc.py:1223-1224`）：

```python
_c20_occ = len(re.findall(r'^\s*LEDGER\s*=\s*os\.path\.join\([^)]*FACTINDEX_V\d+',
                          _c20_txt, re.M))
```

判据在 `_c20_occ != 1` 时 FAIL（`1225-1227`）。

**实测判别矩阵**（内存字符串，非落盘）：

| 工况 | (a) `_c20_join_of` 可解析 | (d) 计数 | 结果 |
|---|---|---|---|
| 生产现况（GR:51 单行单引号） | True | 1 | 绿（正确） |
| 第二份同名再赋值 `LEDGER = ...V562` | True | **2** | 红（正确） |
| 第二份换名 `LEDGER2 = ...V562` | False | **0** | **绿（漏抓）** |
| 第二份换名 `LEDGER_ALT = ...V562` | False | 0 | 绿（漏抓） |
| 第二份无变量名裸字面量 `X = os.path.join(TIER,'…V562',…)` | False | 0 | 绿（漏抓） |
| 拼接写法 `'R17_R131_FACTINDEX_' + 'V562'` | False | 0 | 绿（漏抓） |
| 缩进在函数内的自测夹具 `    LEDGER = …V562` | False | **1** | 红（可能是假 FAIL） |

**结论**

1. **抓得住**「第二份同名再赋值」（`LEDGER = LEDGER2` 式覆写）——因为 `re.M` 下 `^` 逐行锚，同名会出现 2 次。
2. **抓不住**「第二份换了变量名」：`LEDGER2` / `LEDGER_ALT` / 任何其它名字的计数都是 0，判据读到 `_c20_occ == 0`，直接报
   `declares 0 LEDGER version literals (expected exactly 1)` → 这**会**红。
   ⚠️ 但要注意它红的是**错误的理由**：它不是因为"发现第二份"而红，而是因为**第一份都认不出来了**。也就是说这条判据的语义是
   "名为 LEDGER 的那一行必须恰好出现一次"，而不是"文件里只能有**一个**台账版本字面量"。两者的区别正好覆盖本卡要防的场景。
3. **正确判据形态**（我建议改成 AST，去正则化）：

```python
# 收集全文件所有 os.path.join(...) 实参里指向台账目录的字符串常量
_t = ast.parse(_c20_txt)
_consts = set()
for n in ast.walk(_t):
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'join':
        for a in n.args:
            if isinstance(a, ast.Constant) and isinstance(a.value, str) \
               and re.fullmatch(r'R17_R\d+_FACTINDEX_V\d+', a.value):
                _consts.add(a.value)
if len(_consts) != 1:
    fails.append('C20 gate_runner.py carries %d distinct ledger version literals: %r'
                 ' (a second copy drifts silently)' % (len(_consts), sorted(_consts)))
```

   实测该 AST 判据在生产文件上：`count=1, [(51, ['R17_R131_FACTINDEX_V563','FACT_INDEX.tsv'])]` —— 基线干净。
   它在上述矩阵上：`LEDGER2=V562` → 集合大小 2 → **红（抓到）**；`LEDGER2=V563`（同值改名，合法）→ 1 → 绿；
   `from facts_floors import EXPECT_CUR as LEDGER`（合法重构）→ 1 → 绿；`VDIR` 间接 → 需回退查顶层常量表（C19 的 `_c19_consts` 已可直接复用）。

   **代价**：约 10 行，替换现有 4 行；`ast.parse` 一次（文件 20 KB，可忽略）。**关键收益**：AST 只收 `Constant` 节点，天然忽略注释与 docstring —— 这一点在本文件上**必须**，因为 `gate_runner.py:18,19` 的 docstring 和 `187,192` 的 ck 名称里都残留着过时的 `V553` 字样；任何"全文正则数版本号"的写法都会在这份文件上假 FAIL。
4. **(d) 的第二处缺陷**：`^\s*` 锚允许缩进，而 (a) 的 `_c20_join_of`（`1201-1202`）只用 `^LEDGER` 顶格锚。同一条语句，两个判据的锚不一致 ⇒ 将来 `gate_runner.py --self-test` 里若出现一个函数内的 `LEDGER = os.path.join(...)` 夹具，(d) 会计成 2 → **假 FAIL**，(a) 却仍是 1。建议 (d) 与 (a) 统一到顶格 `^LEDGER`，或直接并入上面的 AST 判据（AST 能按 `ast.Module.body` 区分顶层与函数内）。

---

## B2 · 对 C19 内部符号的执行顺序依赖是否安全

**现状安全。** 依赖面三处，全部在 C19 块内先定义：

| C20 引用 | 定义位置 | 性质 |
|---|---|---|
| `C19_FACTS` | `1060` | 模块级赋值 |
| `C19_PTR` | `1061` | 模块级赋值 |
| `_c19_eval_expect_cur` | `1073` | 模块级 `def` |
| `_c19_abs` | `1120` | 模块级赋值（**条件分支内**） |

C19 块 1041-1174，C20 块 1177-1247，Python 自上而下执行 ⇒ 当前顺序成立。

**若把 C20 移到 C19 之前**：

- `1216` 的 `_c19_eval_expect_cur(...)` → `NameError`，`1196` 的 `C19_FACTS` → `NameError`。`check_disc.py` 全文**没有**包裹 C19/C20 的 `try/except` ⇒ 直接 traceback、非 0 退出。这是**响亮的**失败，不会静默通过。
- 唯一的静默通道是 `1218` 的 `locals().get('_c19_abs')`：`.get()` 在 C19 从未运行时返回 `None`，而 `None` 随后落到 `1234-1236` 的 FAIL 分支 ⇒ 仍是红。所以顺序倒置**不会**变成静默通过。

**但 C20 块内有没有显式断言防顺序依赖？** 实测：块内 `assert` 计数 **0**、`try/except` 计数 **0**、`locals()/globals()` 计数 1（就是 1218 那一处）。也就是说：

- 唯一的"保护"是 `NameError` 这种**偶然**的副作用，而不是设计出来的判据；
- 一旦有人把 `1216` 改成 `C19_FACTS if 'C19_FACTS' in globals() else None` 这种"更防御"的写法（很自然的改动），或把 C20 包进 `try/except`，顺序依赖就**变成静默通过**：`_c20_ptr`/`_c20_ff` 双双 `None` 会连报两条 FAIL（还不算静默），但若同时把 C20 的 FAIL 降级为 skip，就真的静默了。

**建议（代价小、收益明确）**：C19 成功分支（`1169` 处）加一行布尔，C20 头部加一条显式门：

```python
# C19 成功分支内
_c19_ptr_ok = True
# C20 头部（1208 之前）
if not globals().get('_c19_ptr_ok'):
    fails.append('C20 requires C19 to have run and certified the pointer in this process '
                 '(_c19_ptr_ok unset); refusing to certify a three-way link against an '
                 'unverified pointer [order dependency guard]')
```

代价：2 处各 1 行，不动任何既有判定逻辑；把"靠 NameError 兜"换成"靠判据兜"。

**另一条独立的、更严重的发现（顺带报出）**：`_c19_abs` 在 `1120` 就被绑定，而 C19 的 sha/bytes/版本目录三条判据在其后的 `1128/1131/1135` 才会红。因此**当 C19 因为台账内容漂移而 FAIL 时，C20 依然会拿这个 `_c19_abs` 做三方比对并打印绿 NOTE**（`1241` 的判据只筛 `C20` 前缀的 fail）。实测日志形态会是：`C19 fact-layer link: FAIL` + `C20 three-way ledger path: ok(...)` + `NOTE C20 ... all three resolve to ...`。exit 码仍为 1（不会假绿到门级），但那行 NOTE 在红日志里是误导性的。这属于 B5 讨论的"边界"问题的一个具体表现，建议 C20 的 `ok` 分支额外要求 `_c19 == 'ok(...)'`。

---

## B3 · `locals().get('_c19_abs')` 在各分支下的取值，及 FAIL 消息的可辨识度

`1218` 的取法在各分支的实际结果：

| 走向 | 触发行 | `_c20_ptr` | C20 输出 |
|---|---|---|---|
| 正常 | 1120 执行 | 绝对路径 | 参与 `1237` 比对 |
| `FACT_INDEX_CURRENT.md` 不存在 | `1103` | `None`（从未绑定） | `C20 pointer relative path unavailable`（`1234-1236`） |
| `facts_floors.py` 不存在 | `1107` | `None` | 同上 |
| 指针四个字段有任一解析不出 | `1115` | `None` | 同上 |
| 字段解析出但路径不存在 | `1121`（`_c19_abs` 已在 `1120` 绑定） | **非 None 的不存在路径** | **不报 C20 失败**，照常参与 normpath 字符串比对 |

所以 `.get()` 在"没跑 / 解析不出"的两类情况下都返回 `None`，**无法区分**。

**C20 的 FAIL 消息能不能让人区分「指针坏了」与「指针解析没跑」？**

- 单看 C20 自己这一条：**不能**。`1235-1236` 的文本把两种情况合写成 `pointer relative path unavailable (cannot complete the three-way comparison; see the C19 entry for the reason)`，取值都是 `None`，措辞完全相同。
- 看整份日志：**能**，但要靠人去上文找 `C19 ...` 那一行，属于"靠交叉引用而非判据本身"。审计口径上这算「不充分」：FAIL 文本应当自证。
- 第 5 行的行为更值得注意：C20 对它**根本不报**，只在 `1237` 做字符串 `normpath` 相等比较，**从不 `os.path.exists` / 不 stat `_c20_gr` 指向的文件**（实测：块内对 `_c20_gr` 只有 `io.open(C20_GR).read()` 一处，没有任何 `getsize/exists(_c20_gr)/sha256`）。这本身与卡面声明的边界一致（C20 不证内容），但会让"指针指向一个已不存在的 V564"在 C20 侧看起来完全正常。

**建议改法（代价 2 行 + 1 行）**：

```python
# C19 块头（1102 附近）显式初始化，消灭 locals() 取法
_c19_abs = None
_c19_ptr_state = 'not-run'        # 'ok' / 'ptr-missing' / 'fields-unparseable' / 'path-missing'
# 各分支内赋值；C20 的 FAIL 文本带上状态：
fails.append('C20 pointer not usable (state=%s); see the C19 entry above '
             '(distinguishes "pointer broken" from "pointer parse never ran")' % _c19_ptr_state)
```

代价：C19 四条分支各加一次状态赋值（4 行），C20 的 `.get()` 换成直接引用（1 行）。收益：B2/B3 两条问题**一起**消失，块内不再有 `locals()` 反模式。

---

## B4 · 「本块内不存任何版本号常量」的实测

**实测结论：作为"代码常量"这句话成立；作为"文本里没有任何版本号"不成立。**

可复算的最小命令（纯 shell，已在本机验证输出）：

```bash
cd /home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14
awk 'NR>=1177&&NR<=1246' check_disc.py | grep -n 'V[0-9]'
echo "total=$(awk 'NR>=1177&&NR<=1246' check_disc.py | grep -c 'V[0-9]') \
noncomment=$(awk 'NR>=1177&&NR<=1246' check_disc.py | grep -v '^[[:space:]]*#' | grep -c 'V[0-9]')"
```

实测输出：

```
blk+ 3:#   LEDGER = os.path.join(TIER, 'R17_R131_FACTINDEX_V563', 'FACT_INDEX.tsv')
blk+ 7:# 实测分辨率（_r182/r182b T3）：沙箱把 gate_runner.LEDGER 改成 V562，本脚本基线仍 exit 0
blk+ 18:# facts_floors.D0 与 C19 的 (a)(b)(c) 负责。三处**同时**改成 V562 时本块仍绿 ——
total=3  noncomment=0
```

即：块内 `V<digits>` 共 **3 处，全部在注释里**（对应源码绝对行 1179 / 1183 / 1194）；**非注释行 0 处**。另测 `re.findall(r'FACTINDEX_V\d+', blk)` 得 **1**（仅 1179 行；`1223` 的正则字面量 `FACTINDEX_V\d+` 里 `\d` 不是数字，不计）。`py_compile` 通过，块内无语法问题。

**判断**

- 注释不是常量 ⇒ 「不存任何版本号**常量**」这句话**字面成立**，卡的措辞是精确的，不构成虚报。
- 但 **1179 行把 `V563` 写死进了散文**，这与 C19 块 `1047-1051` 自己批判的"钉住一个永不变化的僵尸快照"是**同型病**，只是从代码搬到了注释。下一次升版到 V564 时，这行注释会静默变成错的版本号；而它长得**恰好是一行可复制的合法代码**，是最容易被顺手粘进代码的位置。这才是实际风险。
- **建议**：把 1179 改写成占位式，例如
  `#   LEDGER = os.path.join(TIER, '<CURRENT_VERSION_DIR>', 'FACT_INDEX.tsv')`。
  代价：1 行注释、零行为影响。收益：注释永不陈旧，且不再提供可直接粘贴的版本字面量。

---

## B5 · 「C20 只证三处同一路径，不证那份是当前版」这个边界是否诚实

**卡面对 C20 自身的边界描述诚实；但卡面对"谁来补这个缺口"的归属交代**不诚实**——它把缺口推给了两个并不覆盖该缺口的判据。这是本卡最实质的问题。**

### 三家各自的覆盖面（逐条对源码）

| 判据 | 位置 | 证明了什么 | 明显**不**证明什么 |
|---|---|---|---|
| C19 (a)(b)(c) | `1121-1138` | 指针所**指名**的那份文件存在、现盘 sha/bytes 与指针字段一致、指针的"版本目录"字段与路径目录名一致 | 不问那份是不是当前版；纯自洽 |
| C19 (e)(f) | `1150-1167` | `facts_floors.EXPECT_CUR` 与指针同一路径；`CUR_SHA256`/`TOTAL_BYTES` 与那份文件的实测值一致 | 同上，纯自洽 |
| C20 (b)(c) | `1230-1240` | `gate_runner.LEDGER` 与另两者同一路径 | 同上，纯字符串相等 |
| facts_floors D0 | `339-343` | `sha(CUR) == CUR_SHA256` | 钉的是 CUR 所指那份 |
| facts_floors D10 | `434-470` | 指针 sha/bytes == `CUR_SHA256`/`TOTAL_BYTES` == CUR 实测 | 同上 |

**共同的不动点**：这五处**全部**以"指针/常量已经声明的那一份"为输入，没有任何一处反向去看"盘上最新的是哪一份"。也就是说，整条链条是**自洽性**链条，不是**时序性**链条。

### 实测空隙（可复算）

```bash
python3 - <<'EOF'
import os,re
R='/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
v=[int(m.group(1)) for d in os.listdir(R)
   if (m:=re.match(r'R17_R\d+_FACTINDEX_V(\d+)$',d)) and os.path.exists(os.path.join(R,d,'FACT_INDEX.tsv'))]
print('dirs-with-tsv n=%d max=V%d pointer=V563' % (len(v),max(v)))
EOF
```

实测：`n=34, max=V563, pointer=V563` ⇒ **今天恰好相等，是巧合，不是判据**。全套三个门禁里对版本目录族的枚举次数：`check_disc.py` 的 `os.listdir` = **0**、`facts_floors.py` = **0**、`gate_runner.py` = 5 次（全部用于 /tmp 沙箱镜像，与版本排序无关）。因此：

> **空隙：建立 `R17_R131_FACTINDEX_V564/` 并写好台账，但三处指针一个都忘了改 ⇒ 三门全绿、exit 0、零告警。**

这正是卡面说要交出去的那件事，而**没有任何一家接住了它**。卡面 `1193-1195` 写「后者由 facts_floors.D0 与 C19 的 (a)(b)(c) 负责」，按上文表格：D0 与 C19(a)(b)(c) 只证"指名那份是真货且自洽"，**证不了"指名那份是当前版"**。所以这句话需要改。

### 建议的诚实表述（写进 C19/C20 的边界注释，替代 `1193-1195`）

```
**边界**：C20 只证三处指向同一绝对路径。至于「那份是否当前版」，本系统**无人覆盖**：
C19 的 (a)(b)(c)、facts_floors 的 D0/D10 都以"指针已声明的那份"为输入做自洽校验，
若要它们回答"是不是最新"，必须反向枚举 R17_R*_FACTINDEX_V* 家族——三份源码里
os.listdir 对版本目录的调用次数均为 0（R182 实测）。故「建了 V564 却忘记改指针」
是本体系的已知盲区，登记为未取得项，不以 C20 的绿色代表已覆盖。
```

若决定**真正关掉**该空隙（可选，非本卡必做）：新增一条 `C21` 版本单调判据——解析三处路径的目录名取 `V(\d+)` 最大值，要求"存在更高的带 `FACT_INDEX.tsv` 的版本目录 ⇒ FAIL"。代价：约 12 行 + 一次 `os.listdir(R14)`；**风险**：会与"先写新版本目录、后改指针"的升版顺序天然冲突（指针文件 `## 升版必备步骤` 第 3 条明确要求先建目录、后改本文档），窗口期内必然红。因此若要加，必须同时把升版步骤改成"在同一原子步骤内完成三步"，否则就是从"覆盖不到"换成"每次升版都假红"。**我不建议本卡追加**，建议只把边界文字改诚实。

### 另两处次级空隙（一并登记）

1. C20 只比字符串（`os.path.normpath`），不比 `realpath`/inode。若 `R17_R131_FACTINDEX_V563` 被换成指向另一目录的软链，C20 仍绿（此时 C19 的 sha 比对会兜住内容变化，但"同一路径、不同实体"这件事本身没人看）。
2. C20 对 `_c20_gr` 指向的文件**不做存在性检查**（见 B3），所以"指针已指向被删掉的 V564"在 C20 侧无感。

---

## B6 · C20 是否引入了新的假 FAIL 面

**是，且其中最刺眼的一条是：它惩罚的恰恰是它应该奖励的重构。**

### (d) 线的假 FAIL

| 工况 | 是否合法 | (d) | (a) | 总结果 |
|---|---|---|---|---|
| 生产现况 | 合法 | 1 | 解析 | 绿 |
| `gate_runner` 内新增函数级自测夹具含 `    LEDGER = os.path.join(...)` | **合法**（自测） | **2** | False | **红（假 FAIL）** |

原因见 B1 第 4 点：`^\s*` vs `^LEDGER` 锚不一致。

### ★ 升版流程与「改成 import」这两种合法操作的误判（卡面 B6 点名问的两条）

**(1) 升版流程：先写新版本目录、再改指针。**
C20 在"新目录已建、三处指针尚未全改"的窗口期内会红。这是**设计意图**（要抓的正是漏改），不是假 FAIL——但有三点必须写进升版步骤，否则会变成操作性假红：

- 指针文件 `## 升版必备步骤` 现有 3 步，只要求"先写目录、后改本文件"，**未提 `gate_runner.py:51`**。窗口期内任何人跑 `gate_runner.py --self-test` 的 S0.1（`GR:215` 断言"生产 check_disc exit 0"）都会红，看起来像门坏了。
- **建议**：在 `FACT_INDEX_CURRENT.md` 的升版步骤追加第 4 步「同步改 `_r161/gate_runner.py` 的 `LEDGER` 常量」。代价：文档 1 行。这不改代码、不动判据，纯操作纪律。

**(2) `gate_runner` 改成 `from facts_floors import EXPECT_CUR as LEDGER`（消除第二份字面量）。**
实测：`(a) _c20_join_of` → **False**，`(d)` 计数 → **0**。
⇒ **会红，但红在 (a) 不是 (d)**：`1219-1221` 报 `C20 cannot resolve LEDGER in gate_runner.py (the runner must declare which ledger it feeds to both gates)`。
从判据设计意图看，这个重构**正是 C20 想要的终局**（把"第三份常量"消灭成"零份常量"，从根上消除漂移面），却被 (a) 的词法形状判成"未能声明"。这是**明确的假 FAIL**，且是 C20 最该支持的方向。

**建议改法（代价约 4 行，加在 `_c20_gr = _c20_join_of(...)` 之后）**：

```python
if _c20_gr is None:
    # 合法形态：从 facts_floors 导入 ⇒ LEDGER 与 EXPECT_CUR 同源，(b)(c) 恒等成立
    _imp = re.search(r'^from\s+facts_floors\s+import\s+[^\n]*\bEXPECT_CUR\b[^\n]*\bas\s+LEDGER\b',
                     _c20_txt, re.M)
    if _imp and _c20_ff is not None:
        _c20_gr = _c20_ff
        notes.append('C20 gate_runner LEDGER is imported from facts_floors (single source of '
                     'truth; the (d) copy-count criterion is deliberately not applied)')
```

### 其余可预见的假 FAIL（同一根因：一切靠"单行单引号 `os.path.join(TIER, ...)`"）

| 合法写法 | (a) | 结论 |
|---|---|---|
| `os.path.join(TIER, "R17_R131_FACTINDEX_V563", 'FACT_INDEX.tsv')`（双引号） | False | 假 FAIL |
| `LEDGER: str = os.path.join(...)`（类型注解） | False | 假 FAIL |
| `LEDGER = TIER / 'R17_...' / 'FACT_INDEX.tsv'`（pathlib） | False | 假 FAIL |
| `VDIR = 'R17_...'; LEDGER = os.path.join(TIER, VDIR, 'FACT_INDEX.tsv')`（变量间接） | False | 假 FAIL |
| 折行 `os.path.join(\n  TIER, '…', '…')` | True | 绿（`\s*` 兜住，OK） |
| 行尾加注释 `… )  # v563` | True | 绿（OK） |

根因与 B1 相同：C19 已经走过了"词法解析太脆 ⇒ 改 AST"的弯路（见 `1145-1149` 的 S-677 记录），C20 又踩了一次。**建议把 (a) 也改为 AST**：

```python
def _c20_ast_ledger(src):
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.Assign) and len(n.targets) == 1 \
           and isinstance(n.targets[0], ast.Name) and n.targets[0].id == 'LEDGER' \
           and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Attribute) \
           and n.value.func.attr == 'join':
            return n.lineno, [a.value for a in n.value.args if isinstance(a, ast.Constant)]
    return None
```

代价：约 10 行，替换 `1198-1206` 的 9 行（净增约 1 行）+ 一次 `ast.parse`。收益：双引号/注解/pathlib/折行/缩进全部一次性解决，并且天然不进注释与 docstring。

### 有没有新的假 **绿**（比假红更危险）？

逐条查过，**未发现**门级的假绿：

- (a) 解析不出 ⇒ `1219` 必报 FAIL，不会跳过；
- (d) 在 `_c20_gr is None` 时被 `1222` 的 else 跳过 ⇒ 只是不检查 (d)，但 (a) 已红，整体仍红；
- `_c20_ptr`/`_c20_ff` 为 `None` 时均有 FAIL 分支（`1228-1229`、`1234-1236`）；
- (e) "缺文件/解析不出不跳过"这条纪律（`1191`）在 `1209-1212`、`1216`、`1228`、`1234` 四处都落实了。

唯一"看起来绿"的是 B2/B3 里说的那个 **NOTE 行**（`1243-1244` 打印 `all three resolve to ...` 而 C19 同时 FAIL），它不影响 exit 码，但会污染日志。建议 `1241` 的条件加上 `and _c19 == 'ok'` 之类的前置。

### 改动清单与代价汇总（供主会话决策）

| 优先级 | 改动 | 位置 | 行数代价 | 风险 |
|---|---|---|---|---|
| P1 | (a) 改 AST 解析（顺带解决双引号/注解/pathlib/缩进） | 替 `1198-1206` | ≈ +1（10 换 9） | 低；`ast.parse` 已有 `ast` 导入（`check_disc.py:22`） |
| P1 | 支持 `from facts_floors import EXPECT_CUR as LEDGER` | `1219` 前插 4 行 | +4 | 低；纯增分支 |
| P2 | (d) 改"全文件台账目录字面量集合大小 == 1"（AST），并统一锚 | 替 `1223-1224` | +6 | 低；需排除 docstring（AST 天然排除） |
| P2 | `_c19_abs = None` / `_c19_ptr_state` 显式初始化，替掉 `locals().get` | `1102`、`1218` + 4 分支 | +5 | 极低 |
| P2 | C20 头部加 `_c19_ptr_ok` 顺序依赖显式门 | 2 处 | +2 | 极低 |
| P3 | 1179 注释去版本字面量 | 1 行注释 | 0 | 无 |
| P3 | 卡面 `1193-1195` 边界文字改诚实（见 B5 给出的整段） | 注释 | 0 | 无 |
| P3 | `FACT_INDEX_CURRENT.md` 升版步骤追加"同步改 gate_runner LEDGER" | 文档 1 行 | 0 | 无；**不属我权限，须主会话/授权角色改** |
| 不建议 | 新增 C21"版本单调/最新版"判据 | 新块 | +12 | 中；与既有升版顺序冲突，需同时改升版步骤，否则每次升版假红 |

---

## B7 · 我会怎么构造 /tmp 镜像（以及我实际做了什么）

**先如实交代实际行为**：本次审计**没有**建任何 /tmp 镜像，**没有**运行 `check_disc.py` 或 `gate_runner.py`，**没有**删除任何文件。B1/B6 的判别矩阵是在**内存字符串**上跑正则/AST 得到的。之所以能不做破坏性验证，是因为 C20 的四条判据全是"读文件 + 比字符串"，静态可判定；破坏性验证在这里买不到新信息，却要冒本卡点名的风险。生产文件 sha256 在审计全程保持不变（见文首基线，可事后复算）。

**如果必须做，我会这样构造**（R182 事故的机制是：镜像里的路径是指向生产的**软链**，而对软链做 `open(...,'w'/'wb')` 会**穿透写入生产文件**、对软链做 `unlink` 或在软链目录上做 `rmtree` 也有连带风险）：

```python
import os, shutil, tempfile, hashlib
ROOT = '/home/t628/projects/ra2-campaign-forge'
PROD = [ROOT + '/_r160/facts_floors.py', ROOT + '/_r161/gate_runner.py']

def dig(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()
BEFORE = {p: dig(p) for p in PROD}                     # ① 进场基线（tripwire）

mir = tempfile.mkdtemp(prefix='/tmp/r182_mirror_')      # ② 根目录只能是 /tmp/…
assert os.path.realpath(mir).startswith('/tmp/r182_mirror_')

# ③ check_disc 的 ROOT 由自身位置反推三层 ⇒ 镜像必须同深度三截
tier = os.path.join(mir, 'lead', 'next_re_20261117_r14')
for d in ('_r160', '_r161', os.path.join('lead', 'next_re_20261117_r14')):
    os.makedirs(os.path.join(mir, d), exist_ok=True)    # ④ 实体目录，绝不用 os.symlink

# ⑤ 要读/要写的文件一律 shutil.copy2 成实体副本，绝不软链
for p in PROD:
    dst = os.path.join(mir, os.path.relpath(p, ROOT))
    assert not os.path.islink(dst)
    shutil.copy2(p, dst)
    assert os.path.islink(dst) is False and os.path.getsize(dst) == len(open(p, 'rb').read())

# ⑥ 每次写镜像文件前强制断言：既不是软链，且 realpath 落在镜像内
def w(p, data):
    rp = os.path.realpath(p)
    assert rp.startswith(mir + '/'), rp              # 绝不写到镜像外
    assert not os.path.islink(p), p                  # 绝不穿透软链
    open(p, 'wb').write(data)

# ⑦ 删除只允许：镜像根 + rmtree（因为全是实体副本，rmtree 不会波及生产）
shutil.rmtree(mir)

# ⑧ 出场基线（事故的硬闸）：任一不符即中止并告警
for p in PROD:
    assert dig(p) == BEFORE[p], 'PRODUCTION FILE CHANGED: ' + p
```

要点逐条对应事故教训：

1. **`_r160`、`_r161` 一律 `os.makedirs` 建实体目录**，再 `shutil.copy2` 成实体文件，**任何情况下不用 `os.symlink`**。这样对镜像里任何路径做 `open(...,'wb')` / `os.unlink` / `rmtree`，作用域都被物理封在 `/tmp` 内——这是唯一从根本上与"软链穿透"绝缘的做法，比事后加判断更可靠。
2. **污染面只有一类**：`check_disc.py` 的 C7 会逐个 grep 大量产物文件，只拷几件会得到几十个假 FAIL（`gate_runner.py:258-267` 已踩过并记录）。所以镜像若要"保真"，正确做法是像 `GR:268-285` 那样**逐项软链只读区、仅对要改的少数文件用实体副本**——但那就把软链引回来了。**我的取舍**：要么接受假 FAIL 只用镜像验证"我要改的那一条"，要么把 `OVERRIDE` 之外的条目也用 `copy2` 硬拷（磁盘代价：几百 MB，t628 只有 16 GB 系统盘，需先估尺寸）——**我不会为了省事重新引入指向生产的软链**。
3. **进场/出场双基线 sha256 是硬闸**，尤其出场那条：它把"我这次失败会不会已经伤了生产"从"靠流程自律"变成"机器断言"。R182 那次如果有这一条，事故会在 5 秒内被抓住而不是靠事后发现。
4. **子进程一律 `PYTHONDONTWRITEBYTECODE=1`**（`gate_runner.py:28` 已有此纪律），避免往镜像里落 `__pycache__`；本审计我只用了 `compile()` 做语法检查，未 import 任何待审文件，也未产生 `.pyc`。
5. **禁止 `pkill -f` / `kill $(pgrep -f ...)`**（会误匹配自身命令行，SIGTERM 自杀 / code 143）。若镜像里有长跑命令需终止，只记录其精确 PID（`$!` 或 `pgrep -P` 得到的数字）再 `kill <PID>`。

---

## 附：本文所有结论的最小复算命令（合并，一次跑完）

```bash
P=/home/t628/projects/ra2-campaign-forge; R=$P/lead/next_re_20261117_r14
# B4：C20 块内版本字面量（应为 3 处全注释、非注释 0）
awk 'NR>=1177&&NR<=1246' $R/check_disc.py | grep -c 'V[0-9]'
awk 'NR>=1177&&NR<=1246' $R/check_disc.py | grep -v '^[[:space:]]*#' | grep -c 'V[0-9]'
# B1/B6：(a) 与 (d) 的实测计数 + 全文件台账字面量集合 + 版本目录族
python3 - <<'EOF'
import re, io, os, hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'; R14=ROOT+'/lead/next_re_20261117_r14'
t=io.open(ROOT+'/_r161/gate_runner.py',encoding='utf-8',newline='').read()
pa="^LEDGER(\\s*)=\\s*os\\.path\\.join\\(\\s*TIER\\s*,\\s*'([^']+)'\\s*,\\s*'([^']+)'\\s*\\)"
print('(a) resolve =', bool(re.search(pa,t,re.M)),
      '| (d) count =', len(re.findall(r'^\\s*LEDGER\\s*=\\s*os\\.path\\.join\\([^)]*FACTINDEX_V\\d+',t,re.M)),
      '| file distinct =', sorted(set(re.findall(r'R17_R\\d+_FACTINDEX_V\\d+',t))))
v=[int(m.group(1)) for d in os.listdir(R14)
   if (m:=re.match(r'R17_R\\d+_FACTINDEX_V(\\d+)$',d)) and os.path.exists(os.path.join(R14,d,'FACT_INDEX.tsv'))]
print('B5 dirs-with-tsv n=%d max=V%d (pointer declares V563)' % (len(v),max(v)))
for p in ('_r160/facts_floors.py','_r161/gate_runner.py'):
    b=open(ROOT+'/'+p,'rb').read(); print('B7', p, len(b), hashlib.sha256(b).hexdigest()[:16])
EOF
# B5 空隙：三门对版本目录族的枚举次数（应全是 0）
for f in $R/check_disc.py $P/_r160/facts_floors.py; do echo -n "$(basename $f) listdir+glob="; grep -c -E 'os\.listdir|glob\.' $f; done
```

（以上命令在本机已逐条执行并核对输出，与本报告所引数值一致。）
