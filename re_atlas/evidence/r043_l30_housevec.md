# R-043 · 门后注册表身份定谳 + L-30 进展（arg2 类仍未闭）：`+0x54` 写门查询 `DynamicVectorClass<HouseClass*>` @ `0xA80228`

镜像：`gamemd.exe` sha256 `73201cc0…f67476`（只读）。全部字节窗口本轮重 dump；
跳表/`ret`/函数头锚点对齐解码，**未**采用 resync 助手输出作事实源（R-042 幻影教训）。
门禁 `tools/r043_l30_housevec.py`：**6/6 字节断言 PASS**（G0 指纹、Y2b 结构性具名不入分母）；
变异 `tools/mutate_r043_gate.py`：**12/12 killed（精确集合）**。原始输出 `r043_l30_housevec.txt`。

## 1. 结论（只到字节能支撑处）

R-042 把 `event+0x54` 的存活写入钉到 handler `0x71E940`@`0x71F209`，并登记该写入受
一道注册表门约束但未追归属（新债 L-30）。本轮**闭合「门查询的是哪张注册表」这一子问题**：

- 门调用查找器 `0x502D30`，它遍历 `[0xA8022C]`（向量）× `[0xA80238]`（计数），按
  `[[item+0x34]+0xB8] == 事件参数` 匹配，命中返回 item、未命中 `xor eax,eax`（返 0）。
- 这一对全局属于一个对象，`this = 0xA80228`：init 装 vptr `0x7E9EE4`、teardown 换 `0x7E9F04`。
  两张 vtable 的 RTTI COL→TD 名 = `?$DynamicVectorClass@PAVHouseClass@@` /
  `?$VectorClass@PAVHouseClass@@` ⇒ **门查询的注册表 = `DynamicVectorClass<HouseClass*>`**。
- 写入前还要求 **arg2 的 slot14(+0x38) 返回值 == 命中 House item 的 `+0x30` 字段**。
- HouseClass 自证：vtable slot11 `0x50E360` = `mov eax,0xd; ret`，AbstractType 名字表
  `0x816EE0` 第 `0x0D` 对（实测 word0=nameptr、word1=id）= `'House'`/`0x0D` ⇒
  WhatAmI `0x0D` ↔ 注册表 TD 名 **交叉闭合**。

> **收紧（G-57 自我纠偏）**：以上**不**等于「`event+0x54` 是 House*」。存进 `+0x54` 的是
> **arg2 的 slot15(+0x3c) 返回值**（R-042 Y 链），门只是把 arg2.slot14() 与 House item 比对。
> 反证就在手：HouseClass 裸 vtable 的 slot15 = 桩 `0x4104A0`（`xor eax,eax`）⇒ 若 arg2 是
> 裸 HouseClass，则 `+0x54` 恒 NULL，与「非空缓存」矛盾。**⇒ arg2 不是 HouseClass**，
> 其精确类**仍未定谳**（L-30 核心半边保持开放）。本轮只把「门涉及 House 向量」钉成事实。

## 2. 证据链（字节）

| 断言 | 地址 | 钉住的字节事实 |
|---|---|---|
| Y1 | 0x502D30..0x502D5F | 查找器整函数 0x30 字节（head→`ret`）：`mov edi,[0xA80238]`、`mov esi,[0xA8022C]`、`cmp [ebx+0xB8],ecx` 命中返 item、未命中 `xor eax,eax` |
| Y2a | 0x4E6CFD/0x4E6D28/0x4E6CE7/0x4E6D11 | `this=0xA80228`：init 装 vptr `0x7E9EE4`、teardown 换 `0x7E9F04`；`[0xA8022C]/[0xA80238]` 清零站点字节 |
| Y2b | RTTI + 镜像串 | 两 vtable 的 TD 名 = `?…@PAVHouseClass@@`；两条修饰名原始串在镜像存在（结构性） |
| Y3 | 全 .text 存储普查 | `[0xA8022C]←` 恰 `{0x4E6CE7,0x4E6D47}`、`[0xA80238]←` 恰 `{0x4E6D11,0x4F61E0}`；元素写入 `0x4F61EC mov [ecx+eax*4],ebp`（rm==4 此站合法 SIB）；编码枚举含 `a3/89+r/m/c705/88/a2` |
| Y4 | 0x71F1DA..0x71F1F9 | handler 门 33 字节（含 rel32 复算 `call 0x502D30`）：`[this+0x34]==-1` 跳存、`call [arg2_vt+0x38]→ebx`、`cmp ebx,[eax+0x30]` |
| Y5 | 0x72651F..0x726532 | 消费方 arg2 取法：`[esi+0x24]→+0xA4→+0xB4`（链登记，不臆断类名） |
| Y6 | 0x50E360 / 名字表 0x816F48 | HouseClass slot11=`mov eax,0xd;ret`；名字表第 0x0D 对 `word0='House'/word1=0x0D` 交叉闭合 |

## 3. 本轮抓到并修复的判据缺陷（诚实账）

1. **Y6 首版把名字表当 word0=id**：raw dump 实测每对是 **word0=nameptr、word1=id**
   （`+0x00→'<none>'/0`、`+0x08→'Unit'/1`），首版 `+0x0D*8` 读成 id 判据 ⇒ FAIL，
   改正 word1=id 后 PASS。G-61「API/结构语义首次使用先打印实测」第三次同型。
2. **Y2b 首版从磁盘重读原始串**（`open(EXE).read()`）⇒ 内存突变对其不生效、变异永不被捕。
   改读 `bytes(blob)`（内存态）后 C3 可杀。**结构性断言也必须可被变异证伪**，
   否则「不计数但红则退出」形同虚设。
3. **诚实账自身的对账**：本 §3 初稿曾写「C12 目标字节位错、改 `0x50E362`→`0x50E361`」，
   **该修改从未发生**——C12 用 `0x50E362`（Y6 六字节窗 `b8 0d 00 00 00 c3` 的第 3 字节）
   改 `0x0C` 即可让 Y6 FAIL，实测 `killed=['Y6']`。那条"修复"是写总结时凭记忆虚构
   （G-55/G-60 同族，且发生在最该自证的「诚实账」里）。删除虚构，改登记此条为教训：
   **erratum/诚实账与结论同级，落笔前对产物逐条核**。

## 4. 边界与债务（L-30 未闭的半边）

- **未闭**：门后 `+0x30`（命中 House 的字段）与 arg2 slot14 返回值究竟是什么语义，
  本轮只钉「相等」这一**关系**，未定谳该字段/方法名 ⇒ L-30 保持开放（半闭）。
- **查找器 miss 路径疑点**：未命中返 0，handler 紧接 `cmp ebx,[eax+0x30]` 将对 `[0+0x30]`
  解引用——除非 `[this+0x34]==-1` 早跳或调用方保证命中。**未追到底**，登记不臆断。
- arg2 slot14 对**裸 HouseClass** = 桩 `0x410490`（`or eax,0xffffffff`→-1）；非 -1 路径来自
  派生/覆写，宿主链（Y5 的 +0xA4/+0xB4）未定谳。
- 消费方 `0x7264C0` 宿主类、容器 `[esi+0x2C]` 元素类型未定谳（resync 漂移再次出现于
  `0x6e5448` 上下文，未纳入任何断言）。
  【勘误·R-048】宿主类已定谳 = **TriggerClass**；「容器」为措辞误导，实测为标量对端字段
  （setter/getter/detach 三件套）。见 `evidence/r048_triggerclass_host.md`，站点与值不变。
- 未做异族盲验（本线 R-035…R-043 全部待 C 会话队列）。
- 本结论是注册表身份定谳，**不宣称任何地址可改写**。
