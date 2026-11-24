# 字段规格卡 · `0x00B0CE88`（脏矩形向量当前 Count）

> 本卡只覆盖**一个** VA。依据 `W4_FIELD_SPEC/TASK.md:20-35` 已定谳前提与 `TASK.md:40-55` 的 Q1 卡结构。
> 本次为**独立二进制复验**（未采信底稿结论作为亲验），零真机、零活进程内存、零采样实现。
> 目标镜像 `ra2youli/gamemd.exe`，本次 `Engine()` 断言通过：**SHA256 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`**，ImageBase `0x400000`。

---

## 0. 一句话结论

`0x00B0CE88` 是**全局静态** `DynamicVectorClass<DirtyAreaStruct>` 对象（`0x00B0CE78`）的 `+0x10` **Count** 槽，即「待重绘脏矩形队列的**瞬时条目数**」；它**不是 `TacticalClass` 的成员**，**不是屏内可见单位数**，与可见单位数之间**没有已校准的定量映射**。W3 的 `Q3_SAMPLE_PLAN.md:100-102`、`W3_COSTBOUND.md:284` 抄录的判脏字节有误，其 `Q3_SAMPLE_PLAN.md:107-112` 的「Count≤3 ⇒ C2 排除 / ≥50 ⇒ C2 主凶」判据**不成立**。

---

## 1. VA / 符号名

| 项 | 值 | 依据 |
|---|---|---|
| VA | `0x00B0CE88` | `TASK.md:25`（本 ask 给定）；`FACTBASE_D19.md:37` |
| 所属对象基址 | **`0x00B0CE78`**（全局静态对象，非堆/非成员） | 见 §2 |
| 字段偏移 | `+0x10`（`Count`） | `docs/re/dirty_rect_l4.md:184-191`；本次反汇编核实 |
| **符号名** | **未定名** | 变量名/全局符号在本次可读材料中拿不到，按纪律不编造 |
| RTTI 类型名（可作补充说明，**不是变量名**） | `?$DynamicVectorClass@UDirtyAreaStruct@@`（析构切换后为 `?$VectorClass@UDirtyAreaStruct@@`） | 本次实跑：vtable `0x7F429C` 的 `[v-4]=0x80B830` → `col+12` → type_descriptor `0x842988`，`rd(0x842990,80)` = `b'.?AV?$DynamicVectorClass@UDirtyAreaStruct@@@@'`；`0x7F42BC` → `0x842960` → `b'.?AV?$VectorClass@UDirtyAreaStruct@@@@'` |
| W3 使用的名称 | `TacticalClass::DirtyAreas.Count` / `DirtyAreas.Count` | `Q3_SAMPLE_PLAN.md:88-90`、`W3_COSTBOUND.md:284` — **归属错误，本次不采用** |

### 为什么「不是 TacticalClass 的成员」（重点核实项）

按纪律进入 **B 的函数体**核实，而不是凭调用点的 `ecx` 推断：

- `RegisterDirtyArea`（`0x6D2790`）序言 `0x6D2790=83ec58`，紧接着 `0x6D2793=8b0d88ceb000 mov ecx,[0xb0ce88]` —— **传入的 `ecx` 立刻被覆盖，函数体全程用绝对地址** `0xB0CE7C/80/88/8C` 访问向量。
- 扩容路径 `0x6D2A84=b978ceb000 mov ecx,0xb0ce78` 才把**对象基址**装进 `ecx` 再 `0x6D2A89=ff5208 call [edx+8]`。
- 构造 `0x6D1A60` 直接 `0x6D1A7D=c70578ceb0009c427f00 mov [0xb0ce78],0x7f429c` 写**绝对地址**的 vptr。
- 本次全 `.text` 原始字节 `78 CE B0 00`（对象基址 LE）仅 **4 处**：`0x6D1A7F`、`0x6D1AB0`、`0x6D2A7B`、`0x6D2A85`，全部是上述绝对寻址/构造，无 `[TacticalClass+off]` 形式。
- `TacticalClass::Instance` 是 `0x00887324`（`docs/re/dirty_rect_l4.md:32`、`:504`）；**调用点**确实传 `ecx=[0x887324]`（如 `0x5F4E89`、`0x486FC5`），但这是引擎 `thiscall` 调用约定的残留，不改变被调函数的访存对象。

⇒ 结论：这是 `.data` 中的**文件作用域/全局单例向量**；W3 把它写成 `TacticalClass::` 成员不成立。

---

## 2. 类型与宽度

| 项 | 值 | 依据 |
|---|---|---|
| 宽度 | **4 字节 dword** | 全部 6 个绝对写点均为 `mov dword ptr`（如 `0x6D2AA1=890d88ceb000`） |
| 符号性 | **有符号 32 位 `int32_t`** | 循环/边界用 `jle/jge/jl` 有符号比较：`0x6D27B5=0f8e6d020000 jle`（Count≤0 跳过遍历）、`0x6D2A57=7c3b jl`（Count<Capacity）、`0x6D298E=7d30 jge`、`0x6DA988=7e3b jle`；构造 `0x6D1A60=33c0 xor eax,eax` 置 0；增量 `0x6D2AA0=41 inc ecx` / `0x6D2990=48 dec eax` |
| 静态初值 | **0**（PE 零填充 BSS + CRT 显式写 0 双证） | 本次实跑：`.data` VA `0x812000`，VirtualSize `0x367BE4`，RawSize `0x6C000`；`0xB0CE88-0x812000=0x2FAE88 ≥ 0x6C000` ⇒ `fo()` 返回 `None`、`in_raw False`，**无文件字节**；CRT 构造 `0x6D1A91=a388ceb000 mov [0xb0ce88],eax`（`eax=0`） |
| 容器布局 | `+0x00` vptr=`0x7F429C`；`+0x04` Items=`0xB0CE7C`；`+0x08` Capacity=`0xB0CE80`；`+0x0C` flags=`0xB0CE84/85`；**`+0x10` Count=`0xB0CE88`**；`+0x14` CapIncrement=`0xB0CE8C`=`0xA` | `docs/re/dirty_rect_l4.md:181-191`；本次实读构造体 `0x6D1A60..0x6D1A9C` 逐槽吻合 |
| 条目宽度 | **0x14 = 20 字节** | `0x6D29AE=b905000000 mov ecx,5` + `0x6D29B6=f3a5 rep movsd`（5 dword）；`0x6D2AAD=8d0480 lea eax,[eax+eax*4]` + `0x6D2AB0=8d3c81 lea edi,[ecx+eax*4]`（×20）；`docs/re/dirty_rect_l4.md:193-203` |

---

## 3. 写点全集（VA + 字节；**注明是否穷尽**）

普查方法：`ra2tool.Engine.disp_hits(0xB0CE88)`，重同步线性解码 `.text`，本次实跑 **coverage = `(99.99837567729335, 1394120, 66)`**（覆盖率%、指令数、恢复失败字节数）。原始 `88 CE B0 00` 全镜像出现 **27 处**，全部落在 `.text`，与 `disp_hits` 的 **27 处（6 W / 21 R）** 一一对应。

### 3.1 绝对地址写点（6 个，在此解码口径下**穷尽**）

| # | VA | 字节 | 指令 | 语义 | 前置运算 |
|---|---|---|---|---|---|
| W1 | `0x6D1A91` | `a388ceb000` | `mov [0xb0ce88], eax` | CRT 静态构造，Count **置 0** | `0x6D1A60=33c0 xor eax,eax` |
| W2 | `0x6D2995` | `a388ceb000` | `mov [0xb0ce88], eax` | `RegisterDirtyArea` 合并去重时**删除被吞并的条目**，Count−1 | `0x6D2983=a188ceb000` 读，`0x6D2990=48 dec eax`；随后 `0x6D29B6=f3a5 rep movsd` 紧凑搬移 |
| W3 | `0x6D2AA1` | `890d88ceb000` | `mov [0xb0ce88], ecx` | `RegisterDirtyArea` **追加新条目**，Count+1 | `0x6D2A94=8b0d88ceb000` 读，`0x6D2AA0=41 inc ecx`；`0x6D2AB8=f3a5 rep movsd` 写 20B 条目 |
| W4 | `0x6D2CA1` | `a388ceb000` | `mov [0xb0ce88], eax` | `0x6D2B60`（按视口位移平移/裁剪脏区，布尔参数 `0x6D2B60=8a442404` 门控）内**移除无效条目**，Count−1 | `0x6D2C93=a188ceb000` 读，`0x6D2C9C=48 dec eax`；`0x6D2CC0=f3a5 rep movsd` 搬移 |
| W5 | `0x6D451C` | `890d88ceb000` | `mov [0xb0ce88], ecx` | `TacticalClass::Render` 尾部 `0x6D44FC` 起**逐条弹空队列**，Count−1 | `0x6D4517=49 dec ecx`；`0x6D453A=f3a5 rep movsd`；`0x6D453C` 读回作循环界限、`0x6D4554=7dbd jge` 回边 |
| W6 | `0x6DA993` | `890d88ceb000` | `mov [0xb0ce88], ecx` | 独立 Clear 例程 `0x6DA980` **归零/递减** | `0x6DA980=8b0d88ceb000` 读，`0x6DA986=85c9 test`、`0x6DA988=7e3b jle` 保护，`0x6DA98E=49 dec ecx`；`0x6DA9C1=7fcb jg` 循环到 0 |

`0x6DA980` 的直接 rel32 调用者本次实跑恰 **2 处**：`0x599D90`、`0x6853C4`；两者上下文均在 `0x6d1c20` 之后写 `mov [0x887324],eax`（`TacticalClass::Instance`）邻域（本次实读 `0x599D80..0x599DA2`、`0x6853B4..0x6853D6`），疑为战局初始化/退出清场；**其触发条件与「是否每局必走」未验**。

### 3.2 已定位的**间接**写点（2 个，经 `this=0xB0CE78` 的 `[reg+0x10]`）

| # | VA | 字节 | 指令 | 路径 |
|---|---|---|---|---|
| W7 | `0x6DC957` | `894510` | `mov [ebp+0x10], eax` | vtable `0x7F429C+8 = 0x6DC850`（扩容）尾部：`0x6DC950=8b4d10` 读 Count，`0x6DC953=3bc1 cmp eax,ecx`，`0x6DC955=7d03 jge`，否则把 Count **裁剪到新 Capacity**。`ebp=ecx=this`，由 `0x6D2A84=b978ceb000 mov ecx,0xb0ce78` + `0x6D2A89=ff5208` 传入 |
| W8 | `0x6DC4E9` | `895e10` | `mov [esi+0x10], ebx`（`ebx=0`） | vtable `0x7F429C+0xC = 0x6DC4E0`（清空/析构）把 Count **置 0**：`0x6DC4E2=8bf1 mov esi,ecx`、`0x6DC4E4=33db xor ebx,ebx`。经 `0x6DC94A=ff520c call [edx+0xc]` 从扩容例程的「请求容量=0」分支（`0x6DC85D=0f84e2000000 je 0x6dc945`）调用 |

### 3.3 **不宣称写点全集穷尽**

- 上述「穷尽」仅对**绝对 `disp32` 访存**且仅在 coverage 99.998%（**66 个未解码字节**）的重同步线性解码口径下成立。
- **未闭合**：经其它寄存器/指针别名传入 `0xB0CE78` 的间接写、`rep movsd`/`memset` 整对象拷贝、读档反序列化、CRT 初始化/退出全闭包、进程重启时的 BSS 归零。
- 本次仅核实到全 `.text` 原始 `78 CE B0 00` 4 处、`b9 78 ce b0 00`（`mov ecx,0xB0CE78`）**1 处**（`0x6D2A84`），但这**不等于**证明不存在其它别名路径。
- 对照 D-19 的诚实账：`RULING_D19.md:102` 亦登记「未验证每条业务间接写点、重置与全生命周期单调性」；本卡不销该项。

---

## 4. 读点与消费方

### 4.1 引擎内部读点（21 个，按所属函数/用途分组）

| 消费方 | 读点 VA | 读来干什么 |
|---|---|---|
| `RegisterDirtyArea` `0x6D2790` | `0x6D2793`、`0x6D2983`、`0x6D29B8`、`0x6D2A01`、`0x6D2A94` | 遍历现有条目做矩形求交/包围盒合并（`0x6D27F6=e865f3d4ff call 0x421b60` Intersect；`0x6D2B01=e83a54dbff call 0x487f40` Union）；作追加/删除/搬移的循环界限 |
| `0x6D2B60`（视口位移平移/裁剪脏区，未定名） | `0x6D2B75`、`0x6D2C93`、`0x6D2CC2` | 倒序取末条 `Items[Count-1]`（`0x6D2B90=8d2cb6 lea ebp,[esi+esi*4]` / `0x6D2B93=c1e502 shl ebp,2` = ×20），加 `ViewBounds`（`0x886FA0/A4/A8/AC`）后重登记或删除 |
| 倒序绘制族 `0x6D2DE0` / `0x6D3290` / `0x6D3470` | `0x6D2F84`、`0x6D31DD`、`0x6D33C1`、`0x6D35AD` | 每个函数都 `mov eax,[count]; test eax,eax; je 跳过; dec eax; lea edi,[eax+eax*4]; shl edi,2; mov edx,[0xb0ce7c]` ⇒ 取末条与 `ViewBounds` 求交后重绘 |
| `0x6D3660` | `0x6D378E`、`0x6D3850` | `0x6D3797=3bc6 cmp eax,esi` / `0x6D385A=3bc2 cmp eax,edx`，**正序**遍历条目做 `Intersect` + 区域重绘 |
| `0x6D3870`（Render 内 `0x6D44F7=e874f3ffff call 0x6d3870` 的「VisibleCells + 脏矩形消费」） | `0x6D3988`、`0x6D3BD8` | 倒序遍历脏区，逐条 `Drawing::Intersect` 后 `fn_6D9920` 重绘 |
| **`TacticalClass::Render` `0x6D3D10` 判脏段** | `0x6D3DF0=a188ceb000` | **见 §6 门控**：Count 只是「是否需要绘制」的**多个或条件之一** |
| `Render` 尾部清空 | `0x6D44FC`、`0x6D453C` | 逐条弹空（配合写点 W5） |
| 独立 Clear `0x6DA980` | `0x6DA980`、`0x6DA9B5` | 归零循环边界（配合写点 W6） |

`Render` 每帧被调用 **3 次**（`drawMode=0/1/2`），本次实读 `0x4F44DF=e82cf81d00`、`0x4F44F4=e817f81d00`、`0x4F4515=e8f6f71d00` 三个 `call 0x6d3d10`，与 `docs/re/dirty_rect_l4.md:33` 一致。`drawMode==2` 在 `0x6D3DD0=83ff02 cmp edi,2` / `0x6D3DD3=0f847f090000 je 0x6d4758` **跳过主视口绘制**。

### 4.2 项目内（非游戏进程）消费方

| 文件 | 用途与状态 |
|---|---|
| `lead/re_line_20261105/A1_SAMPLER_CANDIDATE/frame_edge_sampler.py:61-67` | 把本 VA 列为第 3 个字段 `dirty_rect_count`；同处已写「能说/不能说」边界。文件头 `:2-24` 明示：内建 `MARKER_ALPHA_UNCALIBRATED` / `MARKER_SUFFICIENCY_UNPROVEN`、**候选、未定谳、未校准、不是已验收观测卡、真机使用须走隔离载体与清场复验**；`:10-17` 披露四 VA 不连续、非原子快照、`df>1`/冻结/读失败 `None` 的处理 |
| `lead/re_line_20261105/A1_SAMPLER_CANDIDATE/test_frame_edge_sampler.py:78,106,202` | 离线单测，用哨兵值 `33`/`None` 验证 schema 行为，**不是字段真值采集** |
| `docs/re/ARCHITECTURE_ATLAS.md:852,947-948` | 静态台账，记录 `0x6D451C`、`0x6D2790`、`0x6D2AA1` 的字节与释义 |

**没有已授权的在线采集器**：`RULING_D19.md:58`（执行步骤 4）、`FACTBASE_D19.md:71` 明确「现有沿表事后提取 ≠ 在线四字段触发采集器」，四 VA 不连续、不能称一次连续 16 字节读取。本卡未运行任何采样代码。

---

## 5. 生命周期

| 阶段 | 依据 |
|---|---|
| **进程加载 / 静态初值** | PE 零填充 BSS（见 §2，`fo()`=`None`）；`.data` 中 `0x814E94` 存 `0x6D1A60`（本次实读 `u32(0x814E94)=0x6d1a60`，邻项 `0x814E84..0x814EA4` 为一串连续函数指针 `0x6D19E0/1A00/1A20/1A40/1A60/1B00/1B10/1BB0/1BF0`）。**该指针表由哪段 CRT 代码遍历消费，本次未验** |
| **构造 / 初始化** | `0x6D1A60..0x6D1A9C`：`0x6D1A67` Items=0、`0x6D1A6C` Capacity=0、`0x6D1A71` flag=1、`0x6D1A7D` vptr=`0x7F429C`、`0x6D1A87` CapIncrement=`0xA`、**`0x6D1A91` Count=0**；`0x6D1A96=e8ef7c0f00 call 0x7c978a` 后 `ret` |
| **析构注册** | `0x6D1A62=68a01a6d00 push 0x6d1aa0` —— 把 `0x6D1AA0` 注册为 atexit 析构。`0x6D1AA0..0x6D1AF7`：`0x6D1AAE` 把 vptr 切到 `0x7F42BC`、`0x6D1AD4` 释放 Items、`0x6D1ADC` Items=0、`0x6D1AE6` flag=0、`0x6D1AED` Capacity=0。**该析构体不写 `0xB0CE88`**（本次逐址核实），即进程退出时 Count 不保证归零；进程重启后由 BSS+构造重新置 0 |
| **运行期增减** | 由 `RegisterDirtyArea`（58 个直接 `call 0x6D2790`，本次实跑枚举）、`0x6D2B60` 平移/裁剪、渲染消费、`Render` 尾部清空、`0x6DA980` Clear、扩容裁剪共同决定（§3） |
| **每帧清空** | `Render` 绘制完成后 `0x6D44FC` 起逐条弹空（W5）；`docs/re/dirty_rect_l4.md:168-169,291` 同述。⇒ **读到的值强依赖采样时刻落在渲染前/后** |
| **每局重置** | 场景开局 `0x68466B=893584eda800 mov [0xa8ed84],esi`（`CurrentFrame=0`）、`0x684675` 置 `Scenario+0x3598=1`（`docs/re/dirty_rect_l4.md:447`；本次实读 `0x684660..0x6846B0`）—— **这一段不写 `0xB0CE88`**。独立 Clear 的两个调用点 `0x599D90`、`0x6853C4` 位于 `TacticalClass::Instance` 赋值邻域，但**是否为每局必走路径未验** |
| **L4 补丁状态** | `docs/re/dirty_rect_l4.md:477` 记「现状 L4」把 `0x6D3D99` 改成 `E9 99 00 00 00 90`（jmp）；但**本次实读当前母本 `0x6D3D99=0f8d98000000 jge 0x6d3e37`（原版字节）**。文档描述的是补丁方案，**不是该文件现状**；本卡全部判脏字节按当前母本原版给出 |

---

## 6. 门控条件（**具体标志与字节**）

本字段**本身没有类似 Bullet `+0x98` 那样的活跃标志门控**；它是无条件的队列长度。但 **`Count` 能否影响渲染**被以下多重条件旁路，这正是「Count=0 或很小 ≠ 不渲染」的字节依据：

`TacticalClass::Render` `0x6D3D10` 判脏段（本次逐址实读 `0x6D3D10..0x6D3E9B`）：

| VA | 字节 | 指令 | 门控含义 |
|---|---|---|---|
| `0x6D3D84` | `0f85c1000000` | `jne 0x6d3e4b` | `drawMode != 0` ⇒ 跳过滚动阈值判定，走 `0x6D3E4B` 读 `0xB0E63C` sticky 全量标志 |
| `0x6D3D99` | `0f8d98000000` | `jge 0x6d3e37` | 当前母本**原版** `jge`：`|scrollDX| >= ViewBounds.Width` ⇒ 全量重绘 |
| `0x6D3DB4` | `c6053ce6b00000` | `mov byte ptr [0xb0e63c],0` | sticky 全量重绘字节标志清零 |
| `0x6D3DC2` | `84c0` / `0x6D3DE2=0f85b3000000` | `test al,al` / `jne 0x6d3e9b` | **`arg2`（强制重绘）非 0 ⇒ 直接进绘制，完全绕过 Count 判脏** |
| `0x6D3DD0` | `83ff02` / `0x6D3DD3=0f847f090000` | `cmp edi,2` / `je 0x6d4758` | `drawMode==2` ⇒ 跳主视口绘制 |
| `0x6D3DE8` | `8a857c0d0000` / `0x6D3DEE=84c0` / `0x6D3DF5=756e` | `mov al,[ebp+0xd7c]` / `test al,al` / **`jne 0x6d3e65`** | **`this+0xD7C`（需重绘标志）⇒ 进绘制/判脏2** |
| `0x6D3DF0` | `a188ceb000` | `mov eax,[0xb0ce88]` | 读 Count |
| `0x6D3DF7` | `84c9` / `0x6D3DF9=0f859c000000` | `test cl,cl` / `jne 0x6d3e9b` | **`cl` = `0x6D3D50 call 0x6d9b50`（建筑需绘制）返回值 ⇒ 进绘制** |
| `0x6D3DFF` | **`85c0`** | **`test eax,eax`** | **真正的 Count 判零在这里** |
| `0x6D3E01` | `7566` | `jne 0x6d3e69` | Count≠0 ⇒ 判脏2 |
| `0x6D3E03` | `8a8d7d0d0000` / `0x6D3E0B=0f858a000000` | `mov cl,[ebp+0xd7d]` / `jne 0x6d3e9b` | `this+0xD7D`（Redrawing）⇒ 进绘制 |
| `0x6D3E11..1F` | `8b8d640d0000` / `3bca` / `7548` | `cmp this+0xD64, this+0xD6C` / `jne 0x6d3e69` | 状态量变化 ⇒ 判脏2 |
| `0x6D3E21..2F` | `3bd1` / `0f8423090000` | `cmp this+0xD68, this+0xD70` / `je 0x6d4758` | 状态量未变 ⇒ 收尾跳过绘制 |
| `0x6D3E37` | `c684240c01000001` / `c6053ce6b00001` | 全量路径：置 `arg2=1`、`0xB0E63C=1` | 全视口重绘 |
| `0x6D3E69` | `8a8d7d0d0000` / `85c0` / `7524` | 判脏2：`this+0xD7D`、`test eax,eax` | 再次检查 Count |
| `0x6D4758` | `8b9c2408010000` / `e91efeffff` | 跳板 → `0x6D4582` 共享收尾 | 同步 `D64→D6C`、`D68→D70`、`B0→B8`、`B4→BC`；`drawMode` 分支做表面 blit |

**勘误（本次独立复核，与 `FACTBASE_D19.md:37`、`RULING_D19.md:23` F7 一致）**：`Q3_SAMPLE_PLAN.md:100-102` 把 `0x6D3DF5` 抄成 `85 C0 test eax,eax`、`0x6D3DF7` 抄成 `75 70 jne`；**真实字节**是 `0x6D3DF5=756e jne 0x6d3e65`、`0x6D3DF7=84c9 test cl,cl`、`0x6D3DFF=85c0 test eax,eax`、`0x6D3E01=7566 jne 0x6d3e69`。抄录错误不改变「Count 是判脏条件之一」的结论，但把 `test` 的位置标错会掩盖 `0x6D3DF5` 其实是 `this+0xD7C` 的旁路分支。

⇒ **可审查判据**：`Count==0` 且 `arg2==0` 且 `this+0xD7C==0` 且 `cl==0` 且 `this+0xD7D==0` 且 `D64==D6C` 且 `D68==D70` 且 `0xB0E63C==0` 且无滚动位移，才走 `0x6D3E2F je 0x6d4758` 收尾。`Q3_SAMPLE_PLAN.md:107-109` 仅凭 `Count≤3` 就断言「C2 静态绝对排除 / `<0.05ms`」**没有静态依据**；`:111-112` 的「Count≥50 ⇒ C2 主凶」同样不成立。

---

## 7. 回绕 / 溢出处理

| 项 | 结论 | 依据 |
|---|---|---|
| 是否累加计数器 | **否**，是**队列长度**，不是 `GenerationStamp` 那种单调积分器。`inc`/`dec` 双向、可增可减、每帧可归零 | §3 写点 W2/W4/W5/W6 均有 `dec`；`0x6D44FC` 逐条弹空 |
| 有无 32 位回绕跳 0 | **已见路径无**；与 `0x0087E8E0` 的回绕机制不同 | 所有 `dec` 前均有 `test`/`jle`/`jl`/`jge` 保护：`0x6DA986=85c9` + `0x6DA988=7e3b`；`0x6D4507=85db test ebx,ebx` + `jl`；`0x6D298E=7d30 jge`。`0x6D279E=3bc8 cmp ecx,eax` + `0x6D27B5=0f8e... jle` 用有符号 `jle` 把 ≤0 视为空 |
| 下溢为负 | 已见路径有界保护；**间接路径/整块拷贝未验** | §3.3 |
| 上界 / 扩容 | `0x6D2A44=a180ceb000 mov eax,[0xb0ce80]` (Capacity) → `0x6D2A51=3bc8 cmp ecx,eax` → `0x6D2A57=7c3b jl 0x6d2a94`（Count<Capacity 直接追加）；否则 `0x6D2A6B=8b0d8cceb000` (CapIncrement=`0xA`) → `0x6D2A79=8b1578ceb000 mov edx,[0xb0ce78]` (vptr) → `0x6D2A84=b978ceb000 mov ecx,0xb0ce78` → `0x6D2A89=ff5208 call [edx+8]`；**扩容失败** `0x6D2A8C=84c0 test al,al` / `0x6D2A8E=0f84a4000000 je 0x6d2b38` ⇒ **静默丢弃该脏区、不递增 Count** |
| 扩容对 Count 的裁剪 | 间接写 W7 `0x6DC957=894510 mov [ebp+0x10],eax` 把 Count 夹到 `min(Count, 新Capacity)` | §3.2 |
| `0x7FFFFFFF` 溢出/饱和 | **未验**：未见饱和检查 | 本次反汇编范围内未找到，不宣称不存在 |
| **合并/去重使 Count 与「登记次数」脱钩** | `0x6D28F8..0x6D291E` 逐字段比较完全相同条目（4 个 dword）+ `0x6D2920=8a44247c mov al,[esp+0x7c]` (bFlag) + `0x6D292C..3C` 比较已有条目的 `+0x10` → `0x6D2926=0f840c020000 je 0x6d2b38` **完全命中则去重跳过、不递增**；否则 `0x6D29D2..0x6D29F5` 计算最小面积增量 → `0x6D2B01 call 0x487f40`（并集）→ `0x6D2B36=f3a5 rep movsd` **原地替换已有条目、也不递增** | 本次实读 `0x6D2790..0x6D2B40`；`docs/re/dirty_rect_l4.md:209-218` 同述 |

---

## 8. 语义边界 —— **能说什么 / 不能说什么**（本卡最重要栏）

### 8.1 与「屏内可见单位数」的关系（本 ask 重点）

**结论：两者是不同的量，中间没有已校准的映射，且机制上不存在 1:1 对应。**

| 维度 | 脏矩形 Count `0x00B0CE88` | 屏内可见单位数 |
|---|---|---|
| 容器 | 全局 `0x00B0CE78`，条目 20B，元素是 `{X,Y,W,H,bFlag}` **矩形** | `MapClass::ObjectsInLayers`（`0x008A0360` 起，5 层，步长 `0x18`，元素是 `ObjectClass*`），地面层 Count=`0x008A03A0` — `Q1_C2_RENDER.md:180-187` |
| 判定 | `RegisterDirtyArea 0x6D2790` 登记矩形 | `DrawIfVisible 0x5F4B10` → `TacticalClass::IsVisible 0x6D2140` 逐单位视口包围盒判定 — `Q1_C2_RENDER.md:26-107,151-187` |
| 数量关系 | **合并/去重**（§7）、**删除/平移**（W2/W4）、**每帧清空**（W5）、**扩容失败丢弃**、**原地并集替换** | 按存活单位线性遍历，每单位一次 |

**逐条字节依据（均进 B 的函数体核实，不凭「A 调用 B」推断）**：

1. `RegisterDirtyArea 0x6D2790` 的**直接 rel32 调用者共 58 处**（本次实跑枚举，VA 清单见 §9 未验栏口径）：分布 `0x42428F`、`0x442184`、…、`0x486FD1`（`CellClass::MarkForRedraw 0x486E70` 尾部，本次实读 `0x486FC5=8b0d24738800 mov ecx,[0x887324]` + `0x486FD1=e8bab72400 call 0x6d2790`）、`0x5F4E8F`、`0x5F5146`、`0x6D9B15`、`0x74CBE5` 等，覆盖地形破坏、建筑、动画、overlay、迷雾等**多种来源，不限于视口内单位**。`docs/re/dirty_rect_l4.md:218` 同记 58 处。
2. 迷雾链：`0x4A9973=e8580e2300 call 0x6da7d0`（`RegisterCellAsVisible`，本次实读）；该函数 25 个直接调用者（本次实跑），且**其函数体内不直接 `call 0x6D2790`**（本次实读 `0x6DA7D0..0x6DA9D0` 只有 `call 0x480a30` / `call 0x6d20e0`）。⇒ 可见性/迷雾变化是独立来源，与单位数无关。`docs/re/dirty_rect_l4.md:235-279` 同述。
3. **`DrawIfVisible 0x5F4B10..0x5F4D0C`（`ret 0xC` 在 `0x5F4D0C`）内没有任何 `call 0x6D2790`**：本次实跑 `RDA callers in [0x5F4B10,0x5F4D30): []`；该函数体只有 `0x5F4B5D call [edx+0xac]`、`0x5F4B6A call 0x6d2140`、`0x5F4B77 call [edx+0x2c]`、`0x5F4CFD call [eax+0x114]`、`0x5F4D28 call 0x4f42f0`。⇒ 「每画一个可见单位就登记一个脏区」的直觉**不成立**。相邻 `0x5F4E8F`/`0x5F5146` 属于 `0x5F4B10` 之后的**其它函数**，不是 `DrawIfVisible` 本体。
4. `0x6D2B60`（视口位移平移/裁剪脏区）会因**摄像机/视口位移**增删改 Count（W4、`0x6D2C93`、加 `ViewBounds` 的 `0x6D2BCB/2BD4/2BE2/2BE7/2BEF`），与单位数无关。
5. `Render` 一帧被调用 3 次且尾部逐条弹空（W5）⇒ 同一帧内 Count 可经历「登记→消费→归零」，外部采样读数**只反映采样瞬间**。

⇒ **可以说的**：`Count` 是「当前待重绘脏矩形队列的条目数」，受登记/合并/去重/删除/清空共同影响；`Count==0` 表示该瞬间队列为空。
⇒ **不能说的**：屏内可见单位数、视口内单位活跃度、每帧 `DrawIfVisible` 调用数、每帧绘制调用数、光栅化像素量、渲染耗时、C2 是否为主犯 / 是否被排除。

### 8.2 完整「能 / 不能」清单

**能说什么**（仅限静态语义，且须带目标哈希与「候选、未授权」限定）

1. 「在 SHA256 `73201cc0…f67476` 的这份 `gamemd.exe` 里，`0x00B0CE88` 是全局 `DynamicVectorClass<DirtyAreaStruct>`（`0x00B0CE78`）的 4 字节有符号 `Count` 槽」—— 有构造器 `0x6D1A60..0x6D1A9C`、RTTI、条目 20B `rep movsd` 三重字节依据。
2. 「该值的每一次绝对写都发生在 §3.1 的 6 个 VA 之一，另已定位 2 个间接写」—— `disp_hits` 27 处、coverage 99.998%。
3. 「该值在 `TacticalClass::Render` 的 `0x6D3DF0` 被读取，并在 `0x6D3DFF test eax,eax` 参与判脏，但只是多重或条件之一」—— §6 逐址字节。
4. 「它是一个**双向变化的瞬时队列量**，每帧可归零；不是单调累加器」—— §3、§7。
5. 「它可被用作**语义受限的渲染侧候选代理**，用于观察『脏区队列是否有积压/波动』这类关联」—— `TASK.md:25` 已定谳前提 1；`PENDING_DECISIONS.md:195`。

**不能说什么**

1. **不能**换算为**屏内可见单位数**（`TASK.md:25,27`；`RULING_D19.md:9,31,103`；`PENDING_DECISIONS.md:160`；`GOAL_THREE_TARGETS_20261018.md:6643`；`D20_B_VISIBILITY_GAP.md:114`；本卡 §8.1 机制证据）。
2. **不能**换算为**实际工作量、绘制调用数、耗时或成本时间占比**（`TASK.md:27`；`RULING_D19.md:99` F4；`Q3_SAMPLE_PLAN.md:177` 的 `y_i=alpha_i*T_i` alpha **未校准**，`TASK.md:59`；`RULING_D19.md:39,60`）。
3. **不能**用 `Count≤3` / `Count≥50` 之类阈值判「C2 彻底排除 / 定谳主凶」（`Q3_SAMPLE_PLAN.md:107-112`、`W3_COSTBOUND.md:284`）；**少量/零 Count 不能自动排除全部渲染**（`RULING_D19.md:23` F7、`FACTBASE_D19.md:37`；本卡 §6 门控字节）。
4. **不能**据 `Q3_SAMPLE_PLAN.md:203`「300–1500 次/秒」或 `:275`「闲置 ≤10 次/秒」做任何引用或推导 —— `TASK.md:30` 已判为非实测、不得引用。
5. **不能**称「1 Hz 已完全充分」「满秩完全解耦」「至少 10 Hz 必要」「帧内计数器完全冻结」「83 次重复信息熵增益为 0」—— `TASK.md:28-34` 已定谳降为未证/已破坏；`FACTBASE_D19.md:31-33`。
6. **不能**称这四 VA 是「一次连续/原子 16 字节读取」或「零新增扰动」—— `RULING_D19.md:58,71,101`；`TASK.md:73`；`frame_edge_sampler.py:10-11` 自述四 VA 不连续。
7. **不能**称「字段运行期有效性已通过」「C2 根因已闭合」「观测卡可直接执行」—— `RULING_D19.md:37,70,104`；`TASK.md:34`。
8. **不能**把本卡当作实现许可 —— `RULING_D19.md:7,61,75-76`、`TASK.md:101-109`；见 §10。
9. **不能**把 W3 的 `TacticalClass::DirtyAreas.Count` 名称或 `0x6D3DF5 test eax,eax` 抄录当作已核实事实 —— 本卡 §1、§6 已纠偏。

---

## 9. 可采性判定：**需补证**

| 判定维度 | 状态 | 依据 |
|---|---|---|
| 字段是否**已定位** | ✔ 是（本次独立二进制复验：RTTI 类型、BSS、构造、6 绝对写 + 2 间接写、21 读、Render 门控字节） | §1–§6 |
| 是否满足 D-17「未定位字段不得进入可采清单」 | ✔ 满足（故**不判「不可采」**） | `RULING_D17_D18.md:61`；`RULING_D19.md:28` F12 |
| 是否**已获准、可直接落地** | ✘ 否。`RULING_D19.md:37`：四字段进入「静态依据明确、口径受限的**候选清单**，不认定其为已获准、可直接落地的观测卡」 | `RULING_D19.md:9,37,55,70` |
| 权限闸 | ✘ D-13/D-16 暂停、D-17 双闸、E3 另裁**全部继续有效**；候选代码与真机/活进程采集**均须用户明示授权** | `TASK.md:33-34,101-109`；`RULING_D19.md:7,61,74-76`；`RULING_D17_D18.md:57-63,77-79` |
| 观测卡细则 | ✘ 读序/每字段起止时间戳/帧号前后读/`df>1` 漏沿/冻结/重置回绕/`null`（不补 0）/附加读取/非原子性/停止与清理条件 —— 均为**未来规格要求，本次未实现、未验收** | `RULING_D19.md:59-60,68`；`TASK.md:73` |
| 运行期有效性 / 扰动 / 数值判据 | ✘ 未验；无真机数据，只能验收文书与静态补证 | `RULING_D19.md:70,102-103,143` |
| alpha 映射 | ✘ 未校准（F4）；代理量→成本时间不可辨识 | `RULING_D19.md:20,39,99`；`TASK.md:59` |
| 与可见单位数的定量关系 | ✘ **未验/未校准** | `D20_B_VISIBILITY_GAP.md:114`；`GOAL_THREE_TARGETS_20261018.md:6832`；`RULING_D19.md:103` |
| 语义证伪后的撤回规则 | ✘ 待建立；若 F7 被证伪须撤回/修订四 VA 采纳及对应读取规格 | `RULING_D19.md:31,90` |

⇒ **需补证**：静态语义已定位且受限，可作为候选字段进入清单；但「可采」需补齐①用户分项明示授权，②运行期字段有效性与扰动验收，③观测卡读序/时间戳/跨帧/null 细则，④alpha 校准或明确报告「不可解」，⑤语义证伪撤回规则。在补齐前不得写入可直接执行的观测卡，也不得据其读数作根因/成本分解/优化排序结论。

---

## 10. 合规与诚实账

**本次实跑**（全部 `python -I -X utf8`，`sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104")` 后 `from ra2tool import Engine`，符合 `TASK.md:111`）：

| # | 命令用途 | 关键输出 |
|---|---|---|
| 1 | `Engine()` + SHA/IB/coverage + 节表 + 六字段初始字节 | `SHA256 73201cc0…f67476`、`IB 0x400000`、`COVERAGE (99.99837567729335, 1394120, 66)`；`.data VirtualSize 0x367be4 / RawSize 0x6c000` |
| 2 | `disp_hits(0xB0CE88)` 全量普查 + 邻槽普查 | `total 27 W 6 R 21`（写集/读集逐条见 §3/§4）；`0xB0CE78` 3、`0xB0CE7C` 25、`0xB0CE80` 3、`0xB0CE8C` 2 |
| 3 | 逐区间 `disasm`（构造 `0x6D1A60`、`0x6D1AA0`、RDA `0x6D2790..0x6D2B50`、`0x6D2AC4`、`0x6D2B50`、`0x6D2C80`、`0x6D3D10..0x6D3E69`、`0x6D44E0`、Clear `0x6DA980`、`0x6DC850`/`0x6DC660`/`0x6DC4E0`、`0x6D2DE0` 族、`0x4F44D0`、`0x5F4B10`、`0x486FC0`、`0x4A9960`、`0x684660`） | 全部字节见各栏引用 |
| 4 | 原始 LE 字节全镜像计数 | `88 CE B0 00` **27** 处全在 `.text`；`78 CE B0 00` **4** 处；`b9 78 ce b0 00` **1** 处（`0x6D2A84`）；`0x006D1A60` 指针 **1** 处 → `.data VA 0x814E94` |
| 5 | rel32 调用者枚举 | `call 0x6D2790` = **58**；`call 0x6DA7D0` = **25**；`call 0x6DA980` = **2**（`0x599D90`,`0x6853C4`）；`call 0x6D1A60` = **0**（CRT 表间接）；`RDA callers in [0x5F4B10,0x5F4D30)` = **[]** |
| 6 | RTTI 链 + vtable 槽 | `0x7F429C` → `.?AV?$DynamicVectorClass@UDirtyAreaStruct@@@@`；`0x7F42BC` → `.?AV?$VectorClass@UDirtyAreaStruct@@@@`；`0x7F429C+8 = 0x6DC850`；`+0xC = 0x6DC4E0` |
| 7 | BSS 判定 | `delta_from_section_start 0x2fae88`，`in_raw False`，`fo() None` |
| 8 | 函数边界重同步解码 `0x6D2B40..0x6D4620` | `insns 2096`；候选起点 `0x6D2B60/2DE0/3290/3470/3660/3AC0/3D10`，用于 §4 读点分组 |

**本次亲读**（含紧邻注释）：`W4_FIELD_SPEC/TASK.md:1-112`、`D19_RULING/RULING_D19.md:1-150`、`D19_RULING/FACTBASE_D19.md:1-183`、`W3_COSTBOUND/sections/Q1_C2_RENDER.md:1-298`、`W3_COSTBOUND/sections/Q3_SAMPLE_PLAN.md:1-276`、`W3_COSTBOUND/W3_COSTBOUND.md:270-314`、`docs/re/dirty_rect_l4.md:1-559`（含 `:550-558` 逆向方法备忘与 `:554-556` 勘误）、`W1_HOLD_SURFACE/W1_HOLD_SURFACE.md:1-468`、`D17D18_RULING/RULING_D17_D18.md:55-79`、`A1_SAMPLER_CANDIDATE/frame_edge_sampler.py:1-85`、`goal3t_nightwatch_20261102/swarm_20261104/ra2tool.py:1-253`（口径纪律 `:4-9`）。另以 `rg` 全仓检索 `B0CE88|B0CE78` 定位 `PENDING_DECISIONS.md:160,195`、`D20_B_VISIBILITY_GAP.md:103,114`、`ARCHITECTURE_ATLAS.md:852,947-948`、`GOAL_THREE_TARGETS_20261018.md:6643,6832`。

**本次未验 / 未做**（一律不补造）：

1. 未启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，未 `taskkill`，**未读活进程内存**，未写任何 RPM/hook/注入/dump/挂线程实现；未运行任何采样代码。
2. **写点全集未穷尽**：66 个未解码字节、指针别名间接写、`rep movsd`/`memset` 整对象拷贝、读档反序列化、CRT 初始化/退出全闭包、进程重启归零路径（§3.3）。
3. `0x814E94` 函数指针表由哪段 CRT 代码遍历消费，未追；`0x6D1A96 call 0x7c978a` 的 CRT 语义（本次只反汇编了 `0x7C978A..0x7C97B8`），未闭合。
4. 58 个 `RegisterDirtyArea` 调用者中，除 `0x486FD1`、`0x5F4E8F`、`0x5F5146` 外**未逐个进函数体核实各自业务性质**；本节只宣称「58 个直接 call 点存在」，不宣称它们各自产生什么。
5. `0x6D2B60`、`0x6D2DE0/3290/3470`、`0x6D3660`、`0x6D3AC0`、`0x6DA980` 的**精确业务名/符号名未定名**；本卡按用途描述，不编造函数名。
6. 每局开局是否必走两个 Clear 调用点、`0x7FFFFFFF` 上溢饱和、运行期真值/分布/扰动/跨帧归属/读失败率、与可见单位数的定量关系、alpha 校准 —— 全部**未验**。
7. 本 ask **只要求写 `sections/card_00B0CE88.md`**；`TASK.md:93-98` 的 `W4_FIELD_SPEC.md` 正文、`_w4_probe.py` + `_w4_probe_out.txt` 以及 Q2/Q3/Q4 **不在本次范围内，未产出**；本卡的实跑输出散见上方各表，未另落盘 `_w4_probe_out.txt`。
8. 唯一写域 = `lead/re_line_20261105/W4_FIELD_SPEC/`（本次建 `sections/` 并写本卡）；未修改任何只读母本，未 commit、未 push。

**本卡是静态规格卡，不是实现，也不是观测卡；任何候选代码或真机/活进程采集须用户分项明示授权（D-13/D-16 暂停、D-17 双闸、E3 另裁继续有效）。**
