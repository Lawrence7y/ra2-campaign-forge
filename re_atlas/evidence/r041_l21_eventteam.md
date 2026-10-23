# R-041 · L-21 定谳：`TEventClass+0x28` = 前一个 `TEventClass`（回链）；`+0x30` = `TeamTypeClass*`

- 镜像：`ra2youli/gamemd.exe`，sha256 `73201cc0…f67476`（只读，全程未写）
- 方法：线性对齐反汇编（+1 重同步，1,394,120 条）+ 直接字节比对（不复制散文）
- 门禁：`tools/r041_l21_eventteam.py` **10/10 字节断言 PASS**（X0 指纹、X6 结构性具名不计数）
- 变异：`tools/mutate_r041_gate.py` **10/10 killed（精确集合判定）**
- 作用域纪律：本结论是 **L-21 类名定谳**，不宣称任何地址「可改写」。真机核验归 GOAL-3T/C 会话。

## 1. `+0x28` —— 同一 `TEventClass` 的链表字段（事件列表前驱回链）

| 证据 | 字节/位置 | 含义 |
|:--|:--|:--|
| 写入站点 | loader `0x7274FD`: `mov ecx,esi; call 0x71F4E0`（parse fn）→ `mov edx,[ebp+0xAC]` → `mov [esi+0x28],edx` → `mov [ebp+0xAC],esi` | 事件列表解析循环：新事件（esi=`push 0x58→new→ctor@0x71E6A0`）的 `+0x28` ← **前一个事件**；`[ebp+0xAC]` 前移。X9 钉此段 17 字节 |
| 同类链读取 | `0x71F800`（主 vtable 槽10）：`mov eax,[ecx+0x28]; mov edx,[esp+4]; cmp eax,edx;` 命中 → `mov eax,[eax+0x28]; mov [ecx+0x28],eax` | 链摘除：字段值按**同类对象的同一偏移**再读（X1） |
| 同 setter 配对 | `0x71F80B..`: `mov [ecx+0x28],eax; cmp [ecx+0x30],edx; … mov dword [ecx+0x30],0` | +0x28/+0x30 在同一函数成对处理（X7） |
| 清零站点 | ctor `0x71E6B2`（写 ebx=0）；摘除路径 `0x71F816` | 除 0 与同类指针外无第三种值（X10 census） |
| 存档消费 | `0x71F82E`: `mov eax,[esi+0x28]; test; mov ecx,[eax+4]; add eax,4; push eax; call [ecx+0x10]` | Save 走 IPersistStream 子对象（+4 挂 `0x7F555C`）slot4（X2） |

⇒ `+0x28` = **本 trigger 事件列表中的前一个 `TEventClass`**（同类）。

## 2. `+0x30` —— `TeamTypeClass*`（按名经全局类型注册表解析）

| 环节 | 字节/位置 | 含义 |
|:--|:--|:--|
| 簇内唯一取值写入点 | parse fn `0x71F4E0` 内 `0x71F595`: `call 0x6F0FC0; mov [esi+0x30],eax` | `+0x30` = 解析器返回值（X3；census 收口见 X10） |
| 解析器 | `0x6F0FC0`: 全局向量 `[0xA8ECA4]`/计数 `[0xA8ECB0]`，逐项 `add ecx,0x24`（AbstractTypeClass INI Name 槽，kb/16 §16.1）+ `[item+0x64]` 双串比对 | 按名在类型注册表查对象（X4）；未命中走 `0x6F1015` 返回 `vector[count]` 哨兵位（旁注：reader `0x6F1922` 有 `<none>`/`none` 串守卫） |
| 注册表持有物类 | ctor `0x6F06E0` 区写子 vtable `0x7F47AC`/`0x7F47A4`（主表 `0x7F47D0` 前 0x24/0x2C，AbstractClass 多 vptr facet 间距规律）；`TeamTypeClass.vfuncs` 含 `0x6F1030`，主 vtable `0x7F47D0`（X5/X6） | 向量持有 `TeamTypeClass*` |
| 注册表来源 | TeamTypes reader `0x6F1976`: 未命中即 `push 0xF8; call new`（=248=`TeamTypeClass::GetSize`，G-1/H-001 双证尺寸）；`"TeamTypes"`@`0x8430FC` | 从 rules INI `[TeamTypes]` 节构建 |
| 调试转储 | dump fn `0x71F390` @`0x71F3FE`: `mov esi,[ecx+0x30]; add esi,0x24; push esi` 进 `"%d,%d,%s"`@`0x844714` | 第 3 参=**注册表对象的 +0x24 名字缓冲** ⇒ 字段确为 AbstractTypeClass 系（类型类）实例 |

⇒ `+0x30` = **`TeamTypeClass*`**（`Team` 类触发参数的团队名归属）。

## 3. 诚实边界

1. `+0x54` 是第三个 swizzle 字段（L-20 仍开放）；本轮未动。
2. X6 为**结构性**断言（RTTI `symbols.json` 交叉，不随 exe 字节变红），已具名标注；
   真正被字节钉死的是 X1–X5c/X7–X10 共 10 条，变异 10/10 各有专属杀手。
3. **「唯一」的范围是 TEvent 函数簇**：全对齐 dword 存储普查（非栈基址、disp 0x28/0x30）
   在簇 0x71E000–0x720000 + loader 0x7274xx 内得——
   `[reg+0x28]`: ctor `0x71E6B2`(0)、unlink `0x71F80E`、loader `0x72750B`；
   `[reg+0x30]`: ctor `0x71E6B8`(0)、parse `0x71F59A`、`0x71F816`(0)。
   **同函数 `0x72759D` 的 `[edi+0x28]` 已归属排除**：esi 来自 `push 0x94→new→ctor@0x6DD000`、
   主 vtable `0x7F443C`=**TActionClass**（RTTI），是同一 loader 里的兄弟动作链，非本类。
   首版普查把 `endswith('…0x28]')` 作用在**完整双操作数串**上（结尾是源操作数，恒假），664 行清单滤成 0（假阴性）；纠正后才是上表——教训入 G-60。
4. 名字表/全局在 `.data`（可写段）；本结论描述镜像静态形态，不覆盖运行期改写。
5. 未做异族盲验（新欠账，见 LEDGER §5）。

## 4. 工具输出

- `tools/r041_l21_eventteam.py` → stderr `10/10 字节断言 PASS`，EXIT=0
- `tools/mutate_r041_gate.py` → `10/10 killed (exact-set scoring)`，EXIT=0
- 探查中间件输出：`tmp_qwen_grade/_l21_*.txt`（临时目录，不入库；正对照站点表在
  `_l21_writes_census2.txt`，664 行全镜像存储清单）
