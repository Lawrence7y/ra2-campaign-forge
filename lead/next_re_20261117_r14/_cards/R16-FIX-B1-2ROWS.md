> 卡号：R16-FIX-B1-2ROWS
> 角色：执行器（`work/cn:hy4flash-free`）
> 写域：`lead\next_re_20261117_r14\R16_FIX_B1_2ROWS\`（新目录，产物放这里）
> 日期：2026-11-21（R16 第 24 轮）· **2 行**

# 任务：重修 2 行的 ④（装配形态标错 + 装表点取了错的命中）

## 0. 绝对边界

1. **严禁写 `COVERAGE\coverage.tsv`**。只产出 delta。
2. 只写 `R16_FIX_B1_2ROWS\`。不改 `R16_D1_WIDE_B1\`（那是上一版，只读）。
3. 可以跑**只读**反汇编/扫描。
4. 不许编造。取不到写 `未取得`。

## 1. 审计判 FAIL 的原因（照录，这就是你要修的）

`R16_AUDIT_D1_WIDE_B1` 判 **2 行 FAIL**：`004322A0`（`CDFileClass::slot9`）与 `004324B0`（`CDFileClass::slot10`），共用装表点 `004014C4`、宿主 `004011C0`。审计给出的四条事实：

1. 该处指令是 **`mov [esp+0x20], 0x7e1668`** —— 写的是**栈临时对象**，**不是 `this`**；
2. 宿主 `004011C0` 把 `ecx` 当**字符串**用（`repne scasb` / `rep movsd`），`malloc 0x124` 后返回堆结构，**全程未在 `this` 上写 vptr** ⇒ 既非构造器也非工厂；
3. **决定性证据**：该函数尾段与 `004019A0`（`test byte [esp+8],1` + `operator delete 0x7C8B3D` + `ret 4` = **scalar deleting destructor**）**逐指令同构** ⇒ 写 vptr 时对象**正在析构**，是内联析构序列；
4. **`0x7E1668` 全镜像 199 处写入**，其中 **`0047A9E3` / `0047AA10` / `0047AA3C` 才是真构造器**（形态：`call 0x431B20` → `mov [esi],0x7e1668` → `mov eax,esi; ret`）。上一版取了「**最低地址命中**」，因此错。

**根因**：上一版的 `install_form` 判定只看**操作数形态**（`op.startswith("0x")` ⇒ `mov_abs`，否则 `ctor_body`），**从不校验宿主身份**。

## 2. 要做的事

### 2.1 重新定位这两行的正确装表点
- 目标表：这两行共同指向 `vt = 007E1668`（`CDFileClass` 的表；`slot9` / `slot10` 各自的值分别是 `004322A0` / `004324B0`）。
- 在**全镜像**枚举所有「把 `0x7E1668` 写进**非栈**内存」的站点（即 `mov [reg+disp], 0x7E1668` 且基址**不是** `esp`/`ebp`），给出每个站点的：地址、指令字节、目标操作数、所在函数、**该函数是否为构造器**。
- 判「真构造器」的可执行规则（自己实现并在报告里写清）：满足 **`call <alloc>` 后紧跟 `mov [esi], vt`、且函数以 `mov eax, esi; ret` 收尾**，且**不是** scalar deleting destructor（排除 `test byte [esp+X],1` + `call 0x7C8B3D` + `ret 4` 同构形态）。
- 从结果里取**该行名类（`CDFileClass`）自己的构造器**站点作为 ④ 的装表点。

### 2.2 重写这 2 行的 ④
- 骨架照既有先例（`coverage.tsv` 第 4 列搜 `④ 活表槽位见证`）。
- 必备：`vt` / `slot` / `slot 值` / `COL` / `offset` / `RTTI`→`mangled` / **正确装表点** / **宿主函数** / 「entry 体外」/ **装配方式（`ctor_body`，并写出实测指令）**。
- **若找不到该类的真构造器装表点**：如实写「装表点取不到真构造器，仅见 N 处写入（含析构序列与栈临时对象）」，并**不要**编一个。这种情况下该行的 ④ 应改为按你实测能撑住的最弱形态写，或记 `SKIP` 并说明。
- **不允许**再把 `[esp+0x20]` 当 `ctor_body`：写了栈目标就是错的。

### 2.3 顺手做一次全批自查（重要）
用你新写的「宿主身份校验」规则，**重跑 `R16_D1_WIDE_B1\delta.tsv` 全部 18 行**，报出是否还有别的行犯了同类错（装配形态标错 / 装表点选了栈写或析构写）。这是本次教训的直接落地。

## 3. 产物（`R16_FIX_B1_2ROWS\`）

### 3.1 `vt1668_sites.tsv`
全镜像所有 `0x7E1668` 的**非栈**写入点：`site	insn_bytes	operand	func_start	is_ctor(是/否)	ctor_evidence	note`

### 3.2 `delta.tsv` —— TAB 分隔，8 列，与 `coverage.tsv` 同构
- 只放这 2 行（若某行按 §2.2 记 SKIP，则只放另一行）。
- 第 4 列 = 盘上原第 4 列原文 + 新的 ④ 段。**注意**：原第 4 列现在**已经含**上一版追加的 ④（若上一版已并表）——你要先查清盘上现状：
  - 若盘上**尚未**并表（B1 delta 还没并），则从**上一版 delta 之前的原文**取前缀基准（即 `coverage.tsv` 当前的第 4 列）；
  - 若盘上**已并表**，则本行属于「替换旧 ④ 段」，需在 `note` 里写清「替换上一版 ④」并给出最小 diff。
- 第 1/2/3/5/6/7/8 列与盘上逐字节相同。

### 3.3 `fields.tsv`
列：`entry	subsystem	name	old_install_site	old_form	old_host	new_install_site	new_form	new_host	form_evidence	status(OK|SKIP)	note`

### 3.4 `selfcheck18.tsv`
对 `R16_D1_WIDE_B1\delta.tsv` 全 18 行的自查：`entry	declared_form	host_is_ctor(是/否)	install_target_is_stack(是/否)	host_is_dtor(是/否)	verdict(OK|SUSPECT)	note`

### 3.5 `REPORT.md`
含：`0x7E1668` 非栈写入点总数与其中真构造器数；2 行的新旧装表点对照；**18 行自查结果**（是否还有 SUSPECT 行，逐行点名）；`coverage.tsv` 与 `gamemd.exe` 的 sha256（证明未改）；一句明示「只重写这 2 行 ④、未改 grade/判定、未并表」。

## 4. 回复里给什么

只给：`0x7E1668` 非栈写入点数与真构造器数；2 行新旧装表点/形态对照；**18 行自查里还有几行 SUSPECT（点名）**；`coverage.tsv` 之前是否已并表 B1；三份产物路径；样例 ④ 一条。**不要贴全表**。
