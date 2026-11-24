# D-18 移交包 · `docs/re/pathfinding_deep_dive.md` 勘误请求（移交 RE-ATLAS）

> **本文件是移交包，不是勘误本身。**
> 依 **D-18 定谳**（`magpie/codex/gpt-6.1-sol$medium`，run `dwfrun-9b224a40-55f7-44f6-8dd6-81a0b4664ce6`，
> 审校 APPROVED）：**由 RE-ATLAS 线在 `docs/re/` 自身写域办理追加勘误**；
> 来源线（RE 逆向线）**不写该目录**，只准备本移交包并在自身写域登记传播纠偏。
> **本移交尚未送达 RE-ATLAS**，也未取得回执 —— 按定谳，**不得记「落实完成」**。

## 一、移交对象

| 项 | 值 |
|---|---|
| 目标文档 | `docs/re/pathfinding_deep_dive.md` |
| 需撤回的断言 A | `:48` ——「最大展开深度被硬编码为 `0x7D0`（2000 个节点）」 |
| 需撤回的断言 B | `:74` ——「`+0x3C` \| `int` \| `MaxNodeBudget` \| 最大节点搜索预算，由外层传入（`0x7D0` = 2000）」 |
| 办理方 | **RE-ATLAS 线**（写域归属，依 D-07「按写域路由」） |
| 来源线 | RE 逆向线（`lead/re_line_20261105/`） |

## 二、核证目标（可复算）

```
镜像：D:/Project/ra2-campaign-forge/ra2youli/gamemd.exe
SHA256：73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476
读取器：lead/goal3t_nightwatch_20261102/swarm_20261104/ra2tool.py 的 Engine
       （内部断言上述 SHA；重同步线性解码，coverage 99.9984%）
```

## 三、指定调用链与三处关键字节

```
调用方 0x4D3E3B   68 D0 07 00 00          push 0x7D0          → 第三参数 = 2000
包装层 0x4CBC1B   50                      push eax
       0x4CBC1C   6A FF                   push -1             ← 未转发 2000
       0x4CBC1E   6A FF                   push -1             ← 第五参数位置
       0x4CBC31   E8 CA 0C F6 FF          call 0x42C900       (FindPath)
FindPath 0x42CBEA  8B 54 24 44            mov edx,[esp+0x44]  → 取第五参数
         0x42CBFB  52                      push edx            → 透传给 SearchCore
         0x42CC02  E8 89 CE FF FF         call 0x429A90
SearchCore 0x429D51 8B 44 24 70           mov eax,[esp+0x70]  → = -1
           0x429D55 85 C0                 test eax,eax
           0x429D57 7D 08                 jge 0x429D61        → 非负保留
           0x429D59 C7 44 24 70 F7 FF 00 00  mov dword [esp+0x70],0xFFF7   → 65527
```

**预算计数器的完整闭环**（核证员进 `SearchCore 0x00429A90..0x0042A45D`，
重同步解码 **2509/2509 字节、100%、失败 0**）：

```
0x429AB6  C7 44 24 28 00 00 00 00   mov [esp+0x28],0      ; 轮数计数器归零
0x429D6D  8B 4C 24 70               取预算
0x429D71  8B 44 24 28               取轮数
0x429D77  3B C1                     cmp
0x429D79  0F 8D 5F 06 00 00         jge → 失败收口 0x42A3DE
...
0x42A1A1..0x42A1AD                  独立 [esp+0x18] 邻居方向计数器（1..8）
0x42A3C9  8B 4C 24 28               取轮数
0x42A3D1  41                        inc
0x42A3D4  89 4C 24 28               轮数 += 1
0x42A3D8  0F 85 8F F9 FF FF         jne → 回预算比较
```

## 四、建议的勘误正文（供 RE-ATLAS 参考，**最终措辞由其自定**）

> **勘误（2026-11-05）**：本节原称「最大展开深度被硬编码为 `0x7D0`（2000 个节点）」（`:48`）
> 及「`+0x3C` = `MaxNodeBudget`，由外层传入 2000」（`:74`），**均不成立**。
>
> 对 `FootClass::UpdatePathfinding (0x4D3920) → FootClass::CallFindPath (0x4CBBA0) →
> PathFinder::FindPath (0x42C900) → PathFinder::SearchCore (0x429A90)` 这条**已核路径**：
> 调用方压入的 2000 是**第三参数**，**未被 `CallFindPath` 转发**；
> `CallFindPath` 在 `0x4CBC1C/0x4CBC1E` 改压两个 `-1`，其中位于**第五参数**位置的那一个
> 被 `FindPath` 透传给 `SearchCore`，`SearchCore` 在 `0x429D59` 把**负值**替换为 `0xFFF7` = 65527，
> **非负传入值原样保留**。
>
> ⇒ 正确表述：**`SearchCore` 单次的「节点处理 / 展开轮数」上限，在负预算缺省时为 65527**。
>
> **不可由此推出**：所有路径统一 65527；每次都会用满；65527 = 不同格子数；
> 65527 = 整次 `FindPath` 总工作量或耗时。搜索可**提前终止**（到目标 / 开放集耗尽 / 其他早退）。
>
> 另：`+0x3C` 存的是 `FindPath` 的**第七参数**（`0x42C92F mov [ebp+0x3C],ecx`），
> **不是预算槽**；其完整语义**待补**，不宜继续沿用 `MaxNodeBudget` 这一命名。

## 五、传播位置（来源线已在自身写域处理）

| 位置 | 内容 | 处置 |
|---|---|---|
| `W2_FRAMETIME_ATTRIB.md:37` | 一句话结论采用 2000 | 已在 `ERRATA_D18_20261105.md` 撤回 |
| `W2_FRAMETIME_ATTRIB.md:217` | 候选 C1 行采用 2000 | 同上 |
| `W2_FRAMETIME_ATTRIB.md:232-237` | 机制依据 + 0.5~1.5ms / 100~200ms 推演 | 同上，**推演整体撤回为未实测** |
| `W2_FRAMETIME_ATTRIB.md:305` | `0x887308/0x88730C` 称作视口 X/Y | 同上，已更正为 `DSurface` 指针 |
| `W2_FRAMETIME_ATTRIB.md:316` | `GenerationStamp` 当作实际展开次数 | 同上，已降级为「尝试计数」 |
| `lead/GOAL_THREE_TARGETS_20261018.md` §562 | 「32 倍」表述过简 | 已在 §563 限定为「上限之比」 |

## 六、验收判据（依 D-18 定谳逐条）

1. `docs/re/pathfinding_deep_dive.md` 有 **RE-ATLAS 办理的、可定位的**追加勘误节；
2. 该勘误**同时撤回**「硬编码 2000」与「`+0x3C` 预算槽」**两项**；
3. 保留历史正文，读者能定位到现行解释；
4. 来源线台账含**双方可定位回执**（RE-ATLAS 勘误文件 + 节标题/行号 + 办理方 + 状态）。

**在取得上述回执前**：本移交记为「**路线已裁、落实未闭合**」，
**不得记 D-18 执行验收通过**。

## 七、诚实账

1. 本包内全部字节与 VA **来自两份核证件**（`FACTBASE_D17.md` / `FACTBASE_D18.md`），
   由 `dwfrun-9b224a40` 的独立核证员亲跑；**我未重新反汇编**。
2. **本移交尚未送达** —— 我无 RE-ATLAS 线的会话通道，只能把移交包置于其可见的仓内路径。
   若归属线长期不办理，依 D-18 第 6 步**回退用户**决定跨域例外，**不自行改走 A**。
3. **零真机**、**未修改 `docs/re/` 一字**、**未 commit**。
