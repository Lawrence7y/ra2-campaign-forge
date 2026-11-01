# R-053 · L-30 残余①定谳：TagClass ctor `0x6E4DE0` 的 arg1 = **TagTypeClass\***（或 NULL）

门禁 `tools/r053_tag_arg1.py`：**10/10 字节断言 PASS**（S1 结构性不入分母）；
变异 `tools/mutate_r053_gate.py`：**16/16 killed（精确集合；G-67 现值前置）**。
证据 `evidence/r053_tag_arg1.txt` / `evidence/r053_mutate.txt`。

## 1. 结论链（全字节级，gamemd.exe `73201cc0…f67476` 只读）

**收口对象**：R-052 登记的 L-30 残余①——TagClass ctor 的唯一栈参数 `arg1` 到底是什么。

**构造点精确集合**：全镜像 `.text` 内 `E8 → 0x6E4DE0` 恰 **3** 处，`E9` 尾跳 **0** 处
（Z1，可杀「有第四个构造点」）。三点 arg1 来源各不相同：

| 站点 | 宿主 | arg1 来源 | 类别 |
|:--|:--|:--|:--|
| `0x6C20CE` | `TClassFactory<TagClass>` 虚表 `0x7F3A80` 的 slot3 = `0x6C2090` | `push 0`（`6a00` @0x6C20CA） | **NULL** |
| `0x6E52D6` | find-or-create `0x6E52A0`（按 `cmp [eax+0x24],edi` 去重） | 调用者 `ecx`（来自 TagType 查找器） | **TagTypeClass\*** |
| `0x6E8D90` | TeamClass ctor `0x6E8A90`（`ret 0xc`，三参） | `[[esi+0x24]+0xD0]` | **TagTypeClass\*** |

**arg1 的落位与消费**（Z5/Z6）：Tag ctor 首句即 `mov [esi+0x24],edi`（`8b7c2410` 取
`[esp+0x10]` = arg1）；随后 `cmp edi,ebx; je`（arg1 为 NULL 则整段跳过）→
`mov edi,[edi+0xA0]` → `cmp edi,ebx; je` → 循环体 `push 0x48; call 0x7C8E17;
push edi; call 0x725FA0`（rel32 复算 = TriggerClass ctor）→ 头插
`8b5628 / 895028 / 894628`（`[esi+0x28]` 链头）→ 回边 `mov edi,[edi+0xA8]`。
⇒ **arg1+0xA0 是 TriggerType 链头，+0xA8 是 next**；TagClass 实例按 TriggerType
逐个建 TriggerClass 实例。

**arg1 的类归属三路互锁**：

1. **站点 B 的调用链**：`0x6E5E70` 显示从 `[0xB0E784]`（= `DynamicVector<TagTypeClass*>`
   的 data 指针，vptr `0x7F4558`，安装站恰 `0x6E5AFD`/降级 `0x6E5B28`）取元素、
   比 `[elem+0x24]` 名串，命中则返回该元素（Z8/Z9）。该返回值直接作 `ecx` 传给
   `0x6E52A0` 再转 arg1。
2. **站点 C 的两跳**：TeamClass ctor 三参，`+0x24` = TeamTypeClass\*（`0x6E8AA7`）；
   `TeamTypeClass+0xD0` 的写入者精确集合 = `{0x6F0799, 0x6F1041, 0x6F135D}`（恰 3，
   Z10 可杀「有第四个写入者」）。其中 `0x6F135D` 的值来自 `0x6E6310`：该函数扫
   `[0xB0E780]` 逐元素比名串，未命中则 `push 0xA4`（= **TagTypeClass 的 GetSize**，Z7
   实测 `b8a4000000c3`）分配、`call 0x6E5B60`（= **TagTypeClass ctor**，体内装 vptr
   `0x7F45C4`）。
3. **链头字段的类归属**：`+0xA0` 的所有者经其 ctor/dtor 判定——TagTypeClass ctor
   `0x6E5B60` 内 `mov [ebp+0xa0],ebx`（清零，S1），dtor `0x6E5CA0` 沿
   `[+0xA0]→[+0xA8]` 逐节点 `call [vptr+0x20]` 释放并回写 `[+0xA8]=0`（S1）；
   `0x6E5E50` 提供按值摘链（`[ecx+0xA0]` 命中则改成 `[eax+0xA8]`）。

**类身份六类铁证**（Z7，RTTI 名 + WhatAmI 即时数 + GetSize 即时数三者同钉）：

| 类 | 主虚表 | WhatAmI | GetSize |
|:--|:--|:--|:--|
| TagClass | `0x7F44E0` | `0x2C` | `0x38` |
| **TagTypeClass** | **`0x7F45C4`** | **`0x2D`** | **`0xA4`** |
| TriggerClass | `0x7F5858` | `0x26` | `0x48` |
| TriggerTypeClass | `0x7F5904` | `0x27` | `0xB4` |
| TeamClass | `0x7F4730` | `0x22` | `0xA0` |
| TeamTypeClass | `0x7F47D0` | `0x23` | `0xF8` |

**排除法**：arg1 在 Tag ctor 内**从不被 WhatAmI 检查、从不经其 vptr 调用**，唯一用途是
取 `+0xA0` 链头 ⇒ 与「TagType 是类型描述符（非运行实例状态）」一致；反证 TagClass
arg1 ≠ TriggerClass：R-052 已确立二者 `+0x34` 宽度矛盾（字节 vs dword），本轮 Z5 再钉
Tag ctor `885e34/885e35` 字节写。

## 2. 语义（登记，不下「可改写」结论）

`arg1` = **TagTypeClass\***（或 NULL）。语义务：一个 TagClass 实例是「某个 TriggerType 的
一组触发条件」的运行期载体——ctor 拿 TagType 描述符，沿其 TriggerType 链为**每个**
TriggerType 派生一个 TriggerClass 实例，头插进 `Tag+0x28` 链。站点 A（工厂，arg1=NULL）
造出的是**无主 Tag**：链为空，`+0x24` 为 0。这与 `0x6E53A0`（R-052 的收割驱动）的三重
门卫完全自洽：门卫含「owner `[+0x24]` 非空」，NULL Tag 会被自然跳过。

## 3. 对 R-052 残量表的更新

| 项 | R-052 状态 | R-053 后 |
|:--|:--|:--|
| L-30 残余②（`0x6E53A0` 宿主类） | 已定谳 = TagClass 非虚成员 | 不变 |
| **L-30 残余①（Tag ctor arg1 类归属）** | 开放（3 个构造点待追） | **已定谳 = TagTypeClass\* / NULL** |
| 新登记（不裁） | — | TagClass 是「TagType 描述符的一次实例化」；三构造点分别对应 工厂/按名/按 Team 三条建 Tag 路径 |

**L-20 不变更**（仍待「载入后必跑」动态序证据）。

## 4. 诚实账

1. **变异偏移两次心算错，被 G-67 现值前置当场拒**（M3 的 `24` 写在 `6E52B9`，实际 disp
   在 `6E52BA`；M13 的 `84` 写在 `6E5E88`，实际在 `6E5E85`）——G-67 第四、五役。
2. **变异暴露门禁两处真空**（不是偏移错，是断言缺口）：
   - M8 首次「存活」⇒ Z6 只钉了链头 `+0xA0` 与 rel32，**没钉回边 `+0xA8` 本身**；
     补 `8bbfa8000000` 与头插三连 `8b5628/895028/894628` 后必杀。
   - M16 首次「存活」⇒ S1 的 stderr 行格式写成 `S1 OK (...)` 而非 `S1 PASS: ...`，
     判别器按 `parts[1] == "FAIL:"` 解析不到；改 `PASS:/FAIL:` 统一格式后必杀。
   —— **这两条是「门禁抓不住变异就改门禁、不改结论」的正面执行**（G-70 同族）。
3. **M4 首稿预期错在预期侧而非门禁侧**：我预言 `Z4+Z10` 双杀，实测只杀 `Z4`
   （`0x6E8D89` 在 Z10 的 census 窗 `0x6F06E0..0x6F2000` 之外）。按实测改正预期并在
   变异脚本头注记原因，未改门禁去迁就。
4. **Y3/Z6 窗口长度两处首稿错**（0x42/0x40、9 vs 10 字节）由机器 dump 当场暴露并纠正。
5. **Z8 的四个 RTTI 字面量首稿多写一个 `@`**（模板名以 `@@@@` 收尾，不是 `@@@@@`）——
   门禁变红暴露，按 dump 值改；并补四个 name 长度钉死（40/33/44/37）作二次钉。
6. **未做动态验证**：本结论是纯静态推导；未在真机观察 Tag/Trigger 实例的构造时序。

## 5. 异族盲验（**通过**）

两路 `new-provider-2/glm-5.3-flash$max` 独立盲验（工作流 `dwfrun-a0031d9f-05e5-4c2d-a52c-d1fa6d62a395`），
各按逐字固定规格独立复算，**七标签逐值一致 + 自检 3/3 + 判据七项全命中**：

| 标签 | 两路一致值 |
|:--|:--|
| `SITES` | 恰 3 站 `0x6C20CE, 0x6E52D6, 0x6E8D90` |
| `ARG1_PUSHES` | `0x6C20CE:push 0` / `0x6E52D6:push edi` / `0x6E8D90:push ecx` |
| `ARG1_STORE_DISP` | `0x24` |
| `CHAIN_HEAD_DISP` / `CHAIN_NEXT_DISP` | `0xA0` / `0xA8` |
| `CLASS_TABLE` | 六类 WhatAmI/GetSize 全等于本文 Z7 |
| `VECTOR_NAMES` | `0xB0E780` 安装 `0x6E5AFD`→vptr `0x7F4558`→`DynamicVectorClass@PAVTagTypeClass`；降级 `0x6E5B28`→`0x7F4578` |
| `SELFTEST` | 两路皆 `PASS/PASS/PASS` |

站点 B/C 的 arg1 是寄存器（`edi`/`ecx`）这条被两路独立复现——正是「arg1 由外层传入而非就地常量」
的直接旁证，与站点 A 的 `push 0` 形成对照。

**打分器假红（G-72）**：汇总判据首报 `unconfirmed`，因用**原始字符串相等**比较两路输出；
两路仅格式不同（大写/小写十六进制、`;`/`,` 分隔）。归一化后 7/7 `semantic_equal=True`。
**未重跑子代理**（零 token），仅在返回数据上重打分。据此判**通过**，同时把打分器缺陷记为 G-72。

## 6. 复跑入口

```
python re_atlas/tools/r053_tag_arg1.py            # 期望 10/10 PASS, exit 0
python re_atlas/tools/mutate_r053_gate.py         # 期望 16/16 killed, exit 0
R053_MUTATE="0x6E4DF2=0x28" python re_atlas/tools/r053_tag_arg1.py   # 单点变异
```
