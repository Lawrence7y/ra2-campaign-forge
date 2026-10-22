# R-032 · H-015 核验：字典节到底把什么当数据

**二进制**：`ra2youli/gamemd.exe`，sha256 `73201cc0…f67476`（门禁 P1 每次复验）
**门禁**：`tools/verify_r032_claims.py` → **13/13 PASS，EXIT=0**（`evidence/r032_verify.txt`，两次复跑逐字相同）
**工具 sha16**：`b274dc994271fd01`（P3 改写后；改写前的 `7f95079967962413` 结论是错的，见 §五）
**对象**：H-015 的三条判断（`kb/30_ini_subsystem.md` §14，R-022 交付）
**异族盲验**：`evidence/r032_crosscheck_blind.md`

---

## 一、判定表

| # | H-015 原判断 | 判定 | 依据 |
|:--|:--|:--|:--|
| 1 | `ShortGame` 由 `Read_MultiplayerDialogSettings`（`0x671EA0`）读取，同节 27 键 | ✅ **HOLDS** | 已由 R-023 门禁 P5/P6 独立覆盖（27 键逐名相等），本轮不重做 |
| 2 | **`[VehicleTypes]` 等节的「键名就是数据」**；20 个 loader 走 `GetKeyCount`→`GetKeyName` | ❌ **半条推翻** | 「20 个 loader 走 `GetKeyCount`→`GetKeyName`」**HOLDS**（P4 逐名相等）；但**「键名即数据」对其中 17 个（族 A）不成立** —— 注册的是**值**，键名只是查表的键（P3） |
| 3 | 「只有 5 个 loader 读固定键（27/19/14/12/11 个）」 | ❌ **FALSIFIED** | P5/P10：**15 个** loader / 660 站点 / **651 键** |

**这是本轮最重要的结论**：H-015 的核心判断**方向对了、对象错了**。
字典节确实"不用配字段"，但原因不是"键名是数据"，而是
**键名是查表的键、值是数据**。这个区别决定编译器该把类型名写在哪一侧。

---

## 二、族 A 的真实机制（P3，16 站点全对）

### 2.1 指令形状

以 `Read_VehicleTypes`（`0x672360`）为例：

```text
0x672372  call 0x526960          ; n = CountKeys("VehicleTypes")      <- 上界来自 INI
0x672379  xor  esi,esi           ; i = 0
0x67237D  jle  ...               ; n <= 0 直接返回 false
  ; --- 循环体 ---
0x672389  push 0x20              ; (5) size
0x67238B  push ecx               ; (4) &buf   [esp+0xc]，32 字节栈缓冲
0x67238C  push 0x889F64          ; (3) default（BSS 空串 ""）
0x672391  push esi              ; (2) i
0x672392  push edx              ; (1) section = "VehicleTypes"
0x672395  call 0x526CC0          ; key = GetKeyName(section, i)   -> eax
0x67239A  push eax               ; 键槽 ← 键名（运行期从 INI 读到的键）
0x6723A0  push [0x7f0cb0]        ; section
0x6723A3  call 0x528A10          ; ReadString(section, key, "", &buf, 0x20)
0x6723A8  test eax,eax
0x6723AA  je   0x6723B5          ; 值取不到 => 跳到 inc esi，**不注册**
0x6723AC  lea ecx,[esp+0xc]      ; ← this = buf（ReadString 写进去的**值**）
0x6723B0  call 0x7480D0          ; Registrar(buf)  —— 注册的是值
0x6723B5  inc esi / cmp esi,ebx / jl 0x67237F
```

### 2.2 判据

**键名进的是 `ReadString` 的键槽**（`0x67239A push eax`），
**注册进对象系统的是 `ReadString` 写出来的缓冲**（`0x6723AC lea ecx,[esp+0xc]`）。

16 个族 A loader 全部满足 "注册 callee 的 `this` 来自 `[esp+..]`"（门禁 P3 断言）。
⇒ **键名是查表的键，值是数据。**

### 2.3 这意味着什么

`.ini` 里应该写成：

```ini
[VehicleTypes]
0=HTNK        ← 键（0/1/2…，名字任意），值 = HTNK（类型名）
1=SMCV
```

**不是**：

```ini
[VehicleTypes]
HTNK=1        ← 这样 HTNK 会被当成"键"去查值，查到的 "1" 被当成类型名注册
```

后一种写法在引擎看来是"注册了一个叫 `1` 的类型"，会**静默产生垃圾条目**（或撞 `<none>` 挡板）。
**这是编译器最容易写反的一处，也是本轮最有实用价值的结论。**

---

## 三、族 B 才是「键名即数据」（3 个）

| loader | 键名的去向 | 判据 |
|:--|:--|:--|
| `Read_Sides` `0x672440` | `0x672489 call 0x526CC0` → `0x672492 call 0x6A46D0`（按名字在 Side 表里线性查找，`cmp [obj+0x24]`）；未命中则 `0x6724A1 new 0xB4` + `0x6724B0 call 0x6A4550` 构造并追加 | **键名 = 类型名**，且**不存在则新建** |
| `Read_Colors` `0x66D3A0` | `0x66D3E9 call 0x526CC0` → `esi` → `0x66D42D call 0x626AB0`（以键名为索引写颜色表）| **键名 = 条目名** |
| `Read_ColorAdd` `0x66D480` | `0x66D4CD call 0x526CC0` → `0x66D4F2 call 0x474B50`（按 section+key 读三元组）| 键名 = 查表键，值另读 |

⇒ **「键名即数据」只对族 B（3/20）成立**；对族 A（17/20）不成立。
H-015 原文把它推广到全部 20 个，是本轮推翻的部分。

---

## 四、验证通过的部分

### 4.1 20 个枚举 loader（P4/P6）

P4：`GetKeyCount` 或 `GetKeyName` 出现过的 loader **恰好 20 个**，与交付表**逐名相等**
（`only_mine=[] only_delivered=[]`）。

P6 把它们分成两族：

| 族 | 数量 | 形状 |
|:--|--:|:--|
| **A** | 17 | `GetKeyName` → `ReadString` → 有值才注册（**值=数据**）|
| **B** | 3 | `GetKeyName` 的名字直接进查找/构造（**键名=数据**）|

### 4.2 值取不到就不注册（P7，17/17）

族 A 全部在 `ReadString` 后 `test eax,eax / je 跳过注册`。
⇒ **`Key=`（空值）与「不写这个键」行为完全相同**：都整条不生效。
`ReadString` 失败时会在 `0x528BBB` 把 `buffer[0]` 置 0 并返回 0，所以
「值不存在」与「值为空」走同一条路。

### 4.3 `<none>` / `none` 挡板（P8，方向已断言）

注册 callee `0x7480D0`：

```text
0x7480D4  push edi / push 0x817474   ; "<none>"
0x7480DA  call 0x7C8D20              ; 大小写不敏感比较
0x7480E4  je   0x74814E              ; 命中 => 跳过
0x7480E6  push edi / push 0x817694   ; "none"
0x7480EC  call 0x7C8D20
0x7480F6  je   0x74814E              ; 命中 => 跳过
0x7480F8  ... 线性查 obj+0x24 ... 命中返回既有对象（0x748142）
0x748126  push 0xE78 / call 0x7C8E17 ; new 3704 字节
0x74813A  call 0x7470D0              ; 构造 + 自动追加全局表
0x74814E  pop edi; xor eax,eax; pop esi; ret   ; 两个 none 分支都汇到这里，返回 0
```

**方向已断言**（不只是"比对了这两个串"）：两个 `je` 都指向 `0x74814E`，
而 `0x74814E` 是 `xor eax,eax` 的零返回 ⇒ 命中即**不建条目**。

### 4.4 未知名字会新建，不报错

按盲验追到的结论（我方独立复核一致）：
名字不在已知集合 → `0x748126 push 0xE78` → `new` → `0x7470D0` 构造并写入
`[0xA83CE4+ecx*4]`、`inc [0xA83CF0]`（自动注册进全局 Unit 类型表）。
全程**无任何报错/日志调用**。
⇒ 往 `[VehicleTypes]` 的**值**里写引擎不认识的名字，会**成功新建一个类型**，
既不报错也不静默丢弃 —— 除非撞上 `<none>` / `none` 两个保留字。

---

## 五、参数个数：`ret imm16` 才是权威（P2）

| 函数 | `ret imm16` | 栈参数 | 角色 |
|:--|--:|--:|:--|
| `0x00526810` | `ret 4` | 1 | `GetSection(name)` |
| `0x00526960` | `ret 4` | 1 | `GetKeyCount(section)` |
| `0x00526CC0` | `ret 8` | 2 | `GetKeyName(section, index)` |
| `0x00528A10` | `ret 0x14` | **5** | `ReadString(section, key, default, buf, size)` |
| `0x005283D0` | `ret 0x10` | 4 | `ReadDouble` |
| `0x005276D0` | `ret 0xC` | 3 | `ReadInteger` |
| `0x005295F0` | `ret 0xC` | 3 | `ReadBool` |
| `0x00529160` | `ret 0x10` | 4 | 第 4 个读族（`0x414` 帧）|

**这纠正了 R-024 门禁里的一张表**（`verify_r024_claims.py:73` / `dump_rules_keys.py:48` 同一份）：

| 函数 | R-024 表 | `ret imm16` | 实测 | 判定 |
|:--|--:|--:|--:|:--|
| `0x00528A10` ReadString | 4 | `ret 0x14` | **5** | ❌ 差 1 |
| `0x00528F00` ReadUnicodeString | 4 | `ret 0x14` | **5** | ❌ 差 1 |
| `0x00529160` | 3 | `ret 0x10` | **4** | ❌ 差 1 |
| `0x005283D0` / `0x005276D0` / `0x005295F0` | 4 / 3 / 3 | — | 4 / 3 / 3 | ✅ |

**但这三个错不影响键清单**，理由可证：`want` 在那两个工具里只用作"向后走几步的上限"
（`len(got) < want + 2`），键永远是 `got[1]`（倒数第二个 push），与 `want` 的绝对值无关。
本轮 P10 用独立路径重算，**逐 loader 与交付表逐项相等**（660 站点 / 651 键）。

---

## 六、`660 → 651` 的对账（P10）

| loader | 站点 | 去重 | 差 | 双读的键 |
|:--|--:|--:|--:|:--|
| `Read_General` | 280 | 279 | 1 | `EngineerCaptureLevel`（`+0x17F8`/`+0x17FC`）|
| `Read_AudioVisual` | 153 | 152 | 1 | `Smoke`（`+0x0BAC`/`+0x0BB0`）|
| `Read_LandCharacteristics` | 15 | 8 | 7 | 7 个移动类别各读两次 + `Buildable` 一次 |
| **合计** | **660** | **651** | **9** | |

`Read_LandCharacteristics` 逐址核对：`Hover`@`0x674039`/`0x67405C`、`Foot`@`0x67407D`/`0x6740A0`、
`Track`@`0x6740C1`/`0x6740E4`、`Wheel`@`0x674104`/`0x674127`、`Float`@`0x67414F`/`0x674172`、
`Amphibious`@`0x674193`/`0x6741B6`、`FloatBeach`@`0x6741D7`/`0x6741FA`、`Buildable`@`0x674216`。

三个数各有量纲：

| 数 | 数的是什么 |
|--:|:--|
| 660 | 读取**站点**（同键读两次算两个）|
| 651 | **loader 内**去重（§14.2 交付口径）|
| 650 | **全引擎跨 loader** 去重（`ContentScan` 在 Difficulty/IQ 各读一次）|

---

## 七、异族盲验对账

盲验（`evidence/r032_crosscheck_blind.md`）独立推导，**Q1/Q3 与我方一致，Q2 推翻我方**。

| 盲验结论 | 我方 | 处理 |
|:--|:--|:--|
| `0x528A10` = `ret 0x14` = 5 个栈参数 | ✅ 一致 | — |
| 7 个函数的 arity 8/8 逐个一致 | ✅ 一致 | — |
| 「5 条 push 只吃 2 个参数」= 预置实参，多出的 3 个成为 `ReadString` 的 default/buf/size | ✅ 一致 | — |
| `0x889F64` 是 BSS 空串（不是字符串） | ✅ 一致 | — |
| **`0x672360` 注册的是「值」不是「键名」** | ❌ **我方原判错** | **采纳盲验**，见 §五（原 P3）|
| 读到空/失败就不注册 | ✅ 一致 | — |
| `0x7480D0` 两个保留字 `<none>`/`none` 返回 NULL | ✅ 一致 | 我方另加了"方向"断言 |
| 未知名字会新建 UnitTypeClass，不报错 | ✅ 一致 | 我方独立复核一致 |
| `0x66D3A0` / `0x672440` 与 `0x672360` 的结构差异 | ✅ 一致 | 我方归为族 B |

### 盲验抓到的我方错误（本节的核心）

**我原来的 P3 断言是「`ReadString` 的键槽里是 `eax`（`GetKeyName` 的返回值）」，
并据此写下「这就是『键名即数据』的机器判据」。**

**错在哪**：这条只证明**键名从哪来**（`GetKeyName` 的返回值），
完全没有证明**键名被当成数据用**。要证后者，必须看**谁被注册**。
实测：注册 callee 的 `this` 是 `[esp+0xc]`（`ReadString` 的落盘缓冲 = 值），
不是 `eax`。**键名只是查表的键。**

**这条错误比数字错更严重**，因为它会把编译器引到**相反**的写法（§2.3）。
盲验是"用另一套方法撞同一堵墙"的价值实证（G-51 的又一次应验）。

**新 G-53**（已写入 `CONFLICTS.md`）：
**"X 被用作 Y 的输入" 不等于 "X 是 Y"**。断言必须落在**语义终点**（谁被注册/谁被存下），
不能落在中间传递（谁提供了这个值）。

---

## 八、我自己踩的坑（本轮五处，全部被门禁或盲验抓出）

1. **把编译器的"预置实参"当规则**（错两次）：先推"`ReadString` 吃 2 个参数"，
   再断言 `esp@GetKeyName == esp@ReadString`。判死它的是 `Read_Teams_obsolete`
   （`0x67276F` esp=−148 vs `0x67278C` esp=−160，差 12 字节，全 5 个参数现推）。
2. **向后走 push 时撞上 `mov ecx,<this>` 就停**：22 个 `GetKeyName` 站点全报 0 条 push。
3. **用 push 条数当参数个数**：会吞掉夹在中间的 callee-saved `push esi`（`Read_Movies` `0x67458E`）。
4. **P8 只断言"比对了两个串"**，没断言方向（`je` 到底跳去创建还是跳过）—— G-42 的老毛病，
   已改为断言 `je → 0x74814E` 且该处是 `xor eax,eax`。
5. **P3 把"键名从哪来"当成"键名是数据"**（§七）。这是本轮最严重的一处，
   由异族盲验抓出，已改写断言并推翻 H-015 的半条判断。

---

## 九、诚实边界

- **族 A 的 17 个 loader 静态无法列出它们认哪些键**，因为键名运行期由 INI 提供。
  能静态回答的只有「读哪个节」和「遍历该节全部键」。这是原理限制，不是工具缺陷。
- `GetKeyCount`/`GetKeyName` 的"第 i 个键名"语义是推断（盲验追到
  `[node+0x18]→[+4]` 链走 i 步取 `[+0xC]`），**未跑游戏确认**。
- `0x529160` 只测 arity（4 参 / `ret 0x10`），**未定**它是哪个读族。
- 「未知名字会新建」追到 `0x7470D0` 写 `[0xA83CE4+ecx*4]` / `inc [0xA83CF0]`，
  但**未验证运行期这些全局初值确实为 0**（BSS 未初始化是盘上推断，非观测）。
- 全部断言绑定 sha256 `73201cc0…f67476`；换二进制需重跑。
