## 🟢 R17 第 119 轮（2026-11-24 19:0x–20:0x）· `.data` 里的 IID 拷贝**确实被代码当 riid 用**（推翻 R118 的「同值巧合」判定）；门禁 C16 把「整节清空」从 **16/16 不可见**变成 **0/16**

**主攻**：R118 遗留的「`.data` 拷贝算不算数」+ 门禁 C15 的两处结构性缺口。两项都收口，各带一次自我降级。

### 一 · R118 §EK4 的邻接判据被推翻

R118 用「GUID 后 0x10 处是 type_info 0x7f9594 + 合法装饰类名」判真/假记录，据此把 IUnknown / ILocomotion / IPiggyback 从 65/11/8 **回退**到 56/7/0。本轮查出两个缺陷：

**① 配对歧义**：`.data` 的 type_info 是**成对相邻**存放（派生紧跟基类），同一 GUID 因此紧邻两个不同类 — 0x818858：gap 0x10 → `VectorClass@G`、gap 0x30 → `DynamicVectorClass@G`；0x820270：gap 0x10 → `EditClass`、gap 0x28 → `DropListClass`。⇒ 不能唯一配对。

**②（决定性）被判「同值巧合」的 3 处都真有代码引用**（PE 导入表自解析 + push 后第一条 call 的落点）：

| `.data` 常量 | 站点 | 分类 |
|---|---|---|
| 0x817bc0 IID_IUnknown | 9 | **CoCreateInstance 8** + `call [ecx]` 1 |
| 0x818858 IID_IPersist | 16 | `call [ecx]` 15+1 |
| 0x81fc50 IID_IStream | 2 | `call [ecx]` 2 |
| 0x820270 IID_IPersistStream | 8 | `call [ecx]` 8 |
| 0x817bb0 ILocomotion | 4 | `call [ecx]` 3 + CoCreateInstance 1 |
| 0x819088 IPiggyback | 8 | `call [ecx]` 5 + `call [edx]` 3 |
| 0x87da00 IID_IDispatch | 1 | `call [ecx + 0xc]` 1 |

巧合字节不会进 riid 槽位 ⇒ **回退撤销**，恢复 **65 / 11 / 8**。QI 三参数形态在 `.data` 侧 26/26 全满足（形态判据非恒真：171 个 push 里只 75 个满足）。

**第二处口径纠错**：R112..R118 的「push 站点数」混合了 `QueryInterface` 请求与 `CoCreateInstance` 创建两种语义（IUnknown 的 9 个站点 8 个是后者）。数字对、口径把两件事并成一件。

### 二 · 门禁 C16 家族（四处，已装盘，成对回归 14/14）

| 子项 | 判据 | 反控实测 |
|---|---|---|
| C16 | 116 节逐节字节 >= 建表值的 25%（下限 300 B） | 清空 2.107..2.122 ⇒ **0/16 漏检**（原 16/16） |
| C16b | 表外新节张数 <= 2 | 追加 3 个 ⇒ FAIL |
| C16c | 表外新节 >= 1 行正文 | title-only 空壳 ⇒ FAIL；带 1 行 ⇒ PASS |
| C16d | 下界表 sha256 钉 | 只改 1 个 floor ⇒ FAIL 点名 C16d |

`GATE_VER` R103→**R119**，`DISC_RECHECK.tsv` 第 20 行同步登记。缺口量化：C15 覆盖 100/116 节，漏的 16 节 = 168,835 B = 2.x 正文 **21.7%**；覆盖集内要连续清空 **8 节**才跌破 byte floor。

### 三 · 跨家族

**exec deepseek task 219**：`failed` / `error_max_turns`（61 回合）/ **[OVERTIME] 12.4 分钟 vs 预算 8.0**，产物仍落盘但不采信，`r119d` 亲自复算 **6/6 PASS**（988 / 988 / 26 / 5 / 3 / 616 / 897 / 16 / 8）。**执行员一条真异议成立**：我卡面把 COM 判据写成「第 3 个 dword 低 16 位 == 0xC000」，实测是 `0x00C0` ⇒ 我表述错（S-59）。

**audit hy4 task 220**（`x119audit_gate.md` 9,428 B）：7 条判定 **6 成立 / 1 不成立**，`r119g` 复算 **11/11 PASS**。三条真缺陷已真修（①②③ → C16c/C16d/下界降至 25%）；④ 不成立——CRLF 不是节和与文件字节差 230,363 B 的原因，它给的正解（preamble 230,247 + 116 个边界 LF）我逐字节复算吻合，且 116 节内部 CR 数为 **0**；⑤⑥⑦ 三处字节数字全部对上。

### 四 · 自错 S-55..S-67（13 条，全部当场抓出）
S-55 CRLF 归一假 FAIL；S-56 skipdata=False 静默停在 0x46f59d（只解 11.1%）；S-57 KeyError；S-58 强反控打在不该打的位置；S-59 卡面判据写错；S-60 616 vs 599 是口径非分歧；S-61 新节设下限误伤合法短节；S-62/S-63 旧 gate 配新表造成假 FAIL；S-64 切片起点错 1 字节；S-65 type_info 对象地址误当值地址；S-66 QI 形态方向读反；S-67 floor 表正则假定行首。

### 五 · 未取得
① `0x7f7c70` 接口名（本机无映射表）；② `IPersistStream` 方法数（RTTI 路已证伪）；③ 0x7f7c80 的 L3「通用包装器」替代解释未排除；④ 35 个静态容器除 field0 外运行期值；⑤ 门禁 C11 的 5 条 FAIL 与 5 处「永远通过」子项本轮未动；⑥ 「push 后第一条 call」判据的三种失败模式仅在本样本证无影响，未跨 IID 推广。
