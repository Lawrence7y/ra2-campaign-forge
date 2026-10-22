# 待办 9 · One_Time 调用时机普查（含对 §347 的推翻）

**轮次**：GOAL-3T 2026-10-22 11:0x–12:5x　**性质**：只读离线，零真机
**二进制**：`ra2youli/gamemd.exe` sha256 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`

---

## 0. 一句话结论

**`0x87F7E8` 不是 RadarClass 单例，是 MouseClass 单例。**

表 A `0x7E1964` 的 RTTI = `.?AVMouseClass@@`，表 B `0x7F0344` = `.?AVRadarClass@@`。
`0x87F7E8` 在启动期构造（`0x5BDA40`）时装的是**表 A**，其 slot5 = `0x5BDF30`（不是 One_Time）。
把表 B 装到 `0x87F7E8` 上的那两行代码（`0x40D1B2` 写表A、`0x40D1F7` 调 `0x652C00` 写表B）
位于 `0x40D1B0`，而 `0x40D1B0` **只在 atexit 回调表里**——是**退出期**析构函数。

⇒ **§347「运行时是表 B ⇒ slot5 = One_Time」的推论前提不成立。**
⇒ RC-4 崩溃时 `ecx = [0x887368] = 0`，那个全局与 `0x87F7E8` 是**两个不同的东西**。
⇒ 待办 9 的分岔 A / B / A' **不能**由"One_Time 经 slot5 被调"来回答；需换路径（见 §5）。

---

## 1. 证据链（每一步都可复跑）

| 步 | 断言 | 脚本 | 结果 |
|:--|:--|:--|:--|
| 1 | 表 A RTTI = `.?AVMouseClass@@` | `_singleton_identity_rejudge.py` STEP A | PASS |
| 2 | 表 B RTTI = `.?AVRadarClass@@` | 同上 | PASS |
| 3 | 表 A slot5 = `0x5BDF30`，表 B slot5 = `0x652CF0` | 同上 | PASS |
| 4 | `0x87F7E8` 构造（`0x5BDA40`）装表 A，不装表 B | `_exit_vs_init.py` STEP 3 | PASS |
| 5 | `0x40D1B0` 不在任何 `.data` 指针表内 | `_atexit_verdict.py` STEP 2 | PASS |
| 6 | `0x40D1B0` 从不被 `call`/`jmp`，唯一引用是 `0x40D19A` 的 `push` | 同上 STEP 3 | PASS |
| 7 | `0x7C978A` 是 0/-1 语义的注册包装（`neg/sbb/neg/dec`） | 同上 STEP 1 | PASS |
| 8 | `0x7C970C` 把函数指针存进 `[0xB78BBC]` 表 | 同上 STEP 1 | PASS |
| 9 | `0x40D190` **在** `.data` 表 `0x81216C` 内（启动期静态构造） | 同上 STEP 2 | PASS |
| 10 | `0x652CF0` 在 `.rdata` 只出现 1 次（`0x7F0358` = 表 B slot5） | 同上 STEP 4 | PASS |
| 11 | `0x652CF0` 全 `.text` **0 处** E8 直接调用 | 同上 STEP 4 | PASS |
| 12 | `0x887368` 由 `0x777803`（WM_DESTROY）清零 | `_singleton_identity_rejudge.py` STEP B | PASS |

**负控**（`_atexit_negctl.py`，8/8 全过）：
- N-1 `0x40D190`→`0x40D191`：`"在 .data 表内"` 变红 ✅
- N-3 把 `EXIT_CB` 换成表内成员 `0x40D190`：`"不在表内"` 变红 ✅
- N-4 `0x652CF0`→`0x652CF1`：`".rdata 唯一 dword"` 变红 ✅
- N-5 表全局地址改 1 位：集合相等断言变红 ✅
- N-2 **如实记录为无判别力**：把 `EXIT_CB` 改一位后仍不在表内 ⇒ 这种改法检验不了该断言，故补 N-3。

---

## 2. atexit 判定细节（这是推翻 §347 的关键）

```asm
0x007C978A  push dword ptr [esp+4]      ; 取参数（待注册函数）
0x007C978E  call 0x007C970C             ; 真正注册
0x007C9793  neg eax                     ; CF = (ret != 0)
0x007C9795  sbb eax, eax                ; eax = -(CF)
0x007C9797  pop ecx
0x007C9798  neg eax                     ; eax = (ret != 0 ? 1 : 0)
0x007C979A  dec eax                     ; eax = (ret != 0 ? 0 : -1)
0x007C979B  ret                         ; 0 = 成功，-1 = 失败
```

这正是 MSVC `_onexit` / `atexit` 的返回约定。`0x7C970C` 体内：
`push [0xB78BC0]` → `call 0x7D107D` → `mov edx,[0xB78BC0]` / `mov ecx,[0xB78BBC]`
→ `mov [ecx], eax`（存函数指针）→ `add dword [0xB78BBC], 4`（表尾推进）。

⇒ `[0xB78BBC]` = 表尾指针，`[0xB78BC0]` = 表基指针，构成 CRT 的 atexit 表。

**为什么 §347 会错**：它看到 `0x40D1B2` 与 `0x40D1F7` 在同一条线性指令流里，
就假定二者都在启动期执行。实际 `0x40D1B0` 是**独立函数**（前面有 `nop` 填充和 `ret`），
它只被 `0x40D19A` 的 `push 0x40D1B0; call 0x7C978A` 注册进 atexit 表。

---

## 3. 表 B 的真实用途：装到**别的对象**上

`0x652C00`（唯一装表 B 的函数）有 6 个调用者：

| 调用点 | `ecx` 来源 | 时机 | 宿主特征 |
|:--|:--|:--|:--|
| `0x40D1F7` | `mov ecx,0x87F7E8` | **退出期**（atexit 回调 `0x40D1B0`） | — |
| `0x40D2D4` | `ebx`（参数） | 运行期 | 与 `0x40D1B0` 同构的循环体（`0x40D260` 为参数） |
| `0x5BEA0A` | `ebx`（`mov ebx,ecx`） | 运行期 | `lea esi,[ebx+0x53ec]`，4 次循环调 `0x40AFD0` |
| `0x6404B3` | `ecx`（`mov esi,ecx`） | 运行期 | 函数头 `0x6404A3`，紧跟 `test [esp+8],1` |
| `0x69391A` | `ebx`（`mov ebx,ecx`） | 运行期 | 同 `0x5BEA0A` 形态 |
| `0x6AC81A` | `ebx`（`mov ebx,ecx`） | 运行期 | 同形态，宿主串含 `RandMap.img` |

⇒ RadarClass（表 B）实例由这 5 个运行期站点构造。**One_Time 的调用者必在这 5 个对象之一**。

---

## 4. 分岔 A / B / A' 的当前状态

| 分岔 | 含义 | 本轮判定 |
|:--|:--|:--|
| A | 启动期执行（只一次） | **不能排除** |
| B | 换图/读盘时重跑 | **不能排除** |
| A' | 加载未完成时收到 WM_CLOSE（单例先清零、One_Time 后跑） | **不能排除** |

**为什么三个都"不能排除"**：One_Time 只经表 B slot5 可达（`.rdata` 唯一 dword + 0 处 E8），
而表 B 装在 5 个运行期构造的 RadarClass 实例上。**这 5 个实例的生命周期**才是分岔的答案，
本轮只定位了构造点，没有定位"谁在什么时机调 slot5"。

**纯离线仍可继续**（下一轮）：
1. 对 `0x40D2D4` / `0x5BEA0A` / `0x6404B3` / `0x69391A` / `0x6AC81A` 五个宿主，
   各自向上求 E8 闭包到「场景加载 / 地图切换 / 每帧」入口。
2. 关键判据：宿主是否在 `LoadDlg.CPP` / `Scenario` / `Map` 相关路径上。
   已在 §3 见到 `0x6AC81A` 宿主带 `RandMap.img`（随机地图），这是**换图路径**的强信号。

---

## 5. 对 ② 的影响（重要）

### 5.1 需要更正的台账结论

| 台账位置 | 原记 | 本轮更正 |
|:--|:--|:--|
| §347 | "0x40D1B2 先设表A 后 0x40D1F7 call 0x652C00 改写成表B ⇒ **运行时是表B**" | 那两行在 **atexit 回调**内，是**退出期**行为；运行期是表 A |
| §349 | "One_Time 是单例 0x87F7E8 的 vtable slot5" | 表 B slot5 确是 One_Time，但 `0x87F7E8` 装的是表 A ⇒ 该单例上 slot5 = `0x5BDF30` |
| §351 | "0x5610EC/0x67E7F9 紧邻 `mov ecx,0x87F7E8` ⇒ this 钉死雷达" | **这条不受影响**：`0x4A8960` 在两个表的 slot42 都是同一地址，且这两处直接 `call 0x4A8960`，不依赖 this 的类身份 |

### 5.2 仍然成立的部分

- RC-4 崩溃链 `0x652CF0 → 0x4A8850 → v[42] 0x4A8960 → …` 的**函数级**拓扑不变。
- 崩溃时 `ecx = [0x887368] = 0`（74 处引用，其中 `0x6403A8`/`0x654405` 就在链上）。
- `0x777803` 在 WM_DESTROY 清零 `0x887368`。
- 修复方向（在 `0x724730` 入口或 28 个无守卫站点加 null 守卫）**不受影响**——
  因为修复针对的是"把 0 当 this 传下去"，与单例身份无关。

### 5.3 新增的可疑点

`0x887368` 有 **74 处引用**，绝大多数是 `mov ecx,[0x887368]` 后紧跟虚调用。
若 `0x887368` 也是某个对象指针，那它被清零后这 74 处**全部**可能解引用 0。
⇒ 这是比"单例身份"更值得普查的一条线（下一轮可做）。

---

## 6. 交付件

| 文件 | 作用 | EXIT | 断言 |
|:--|:--|:--:|:--:|
| `_onetime_census.py`（子代理） | One_Time 基础普查 | 0 | 32/32 |
| `_probe.txt` | 上述输出 | — | — |
| `_vtable_verify.py` | 两张表 slot5/slot42 与写入方式 | 0 | 13/13 |
| `VTABLE_VERIFY.txt` | 上述输出 | — | — |
| `_slot5_callers.py` | 273 处 `call [reg+0x14]` 来源分类 | 0 | 3/3 |
| `SLOT5_CALLERS.txt` | 上述输出 | — | — |
| `_singleton_slot5_trace.py` | 多级回溯查单例直调 | 1 | 4/5（1 条为假设错误，见下） |
| `SINGLETON_SLOT5_TRACE.txt` | 上述输出 | — | — |
| `_exit_vs_init.py` | 构造 vs 退出期初判 | 1 | 4/6（2 条为假设错误，见下） |
| `EXIT_VS_INIT.txt` | 上述输出 | — | — |
| `_reinit_callers.py` | 6 个 `0x652C00` 调用者上下文 | 1 | 见下 |
| `REINIT_CALLERS.txt` | 上述输出 | — | — |
| `_singleton_identity_rejudge.py` | **RTTI 定身份 + 0x887368 普查** | **0** | **6/6** |
| `SINGLETON_IDENTITY_REJUDGE.txt` | 上述输出 | — | — |
| `_atexit_verdict.py` | **atexit 定谳** | **0** | **9/9** |
| `ATEXIT_VERDICT.txt` | 上述输出 | — | — |
| `_atexit_negctl.py` | 负控 | **0** | **8/8** |
| `ATEXIT_NEGCTL.txt` | 上述输出 | — | — |

**三份 EXIT=1 的脚本**都是因为**我的假设写错**而非证据不足，已如实保留：
- `_singleton_slot5_trace.py`：假设"`0x5BDF30` 函数体 > 6 条"；实测它就是 6 条（真函数头，
  前面是 `ret 8` + nop 填充）⇒ 假设错，证据本身成立。
- `_exit_vs_init.py`：假设"`0x652C00` 只有 1 个调用者"；实测 6 个 ⇒ 假设错，
  但"构造装表A"这条关键证据成立。
- `_reinit_callers.py`：`ecx <- unknown` 的回溯实现有缺陷（未处理 `mov ecx,ebx` 形态），
  但 STEP D 的上下文 dump 已直接给出答案，故结论不受影响。

---

## 7. 本轮踩的四个坑（供后续复用）

1. **RTTI 的 `pTypeDescriptor` 在本件是 VA，不是 RVA**。按 RVA 处理会加两次 imagebase 得越界值。
   另：TypeDescriptor 的 name 在 **+0x08**，不是 +0x10。
2. **`mov [abs], imm32` 的 disp 已是绝对 VA**，不要再加 imagebase（我在 `_vtable_verify.py` 踩过）。
3. **`ImageBase` 偏移**：`e_lfanew + 0x18 + 0x1C`；直接读文件偏移 `0x34` 只在 `e_lfanew==0x80` 时巧合成立。
4. **负控改位落在真指令边界上不算错位**：`push esi` 只有 1 字节，+1 仍是合法边界。
   且 capstone 从错位起解**会重新同步**，所以"错位必丢证据"这个假设不成立。
   ⇒ 负控要么换**被比较的具体值**，要么换**完全无关的函数**。

---

## 8. 结论的可信度分级

| 结论 | 等级 | 依据 |
|:--|:--|:--|
| 表 A = MouseClass，表 B = RadarClass | **[已证]** | RTTI 字符串直接读出 |
| `0x87F7E8` 运行期装表 A | **[已证]** | 构造体 `0x5BDA40` 装表A；表B 唯一写入点在 atexit 回调内 |
| `0x40D1B0` 是 atexit 回调 | **[已证]** | 注册例程形态 + 不在 .data 表 + 从不被 call/jmp |
| §347 的"运行时是表B"不成立 | **[已证]** | 上述三条 |
| One_Time 只经表 B slot5 可达 | **[已证]** | `.rdata` 唯一 dword + 0 处 E8 |
| One_Time 的实际调用时机 | **[未定]** | 需追 5 个 RadarClass 构造宿主的入口 |
| 分岔 A / B / A' | **[未定]** | 同上 |
