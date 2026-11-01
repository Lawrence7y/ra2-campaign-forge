# R-052 · L-30 残余问题②定谳：收割驱动 `0x6E53A0` 宿主类 = **TagClass**（非虚成员），连带 TagClass 三注册表 + 第四共享表 `0xB0F698`

门禁 `tools/r052_tagclass_host.py`：**10/10 字节断言 PASS**（S1 结构性不入分母，红仍非零退出）；
变异 `tools/mutate_r052_gate.py`：**13/13 killed（精确集合；含内嵌现值前置 G-67）**。
证据 stdout：`evidence/r052_tagclass_host.txt`。窗口来源：`out/_probe_r052dump.py`（机器 dump，G-65）。

## 1. 结论链（全部字节级，gamemd.exe sha256 73201cc0…f67476 只读）

**收口对象**：R-050 登记的 L-30 残余两问之②——调用方 `0x6E53A0`（72/73 个 E8 入口）宿主类。

- **Y1** `0x6E53A0` 体内 `[ebp+disp]` 集合**恰** = `{0x24,0x28,0x2C,0x34,0x35}`，且
  `+0x34/+0x35` 为**字节**访问（`8a4534`/`8a4535` 读；`c6453501`/`c6453500` 写=重入旗标）。
- **Y2** 边界逐字节钉：头 `push ecx; mov al,[0xA8ED6B]; push ebx; xor bl,bl; push ebp; …
  mov ebp,ecx`；两退出口皆 `ret 0x14`（0x6E554E/0x6E5556）；0x6E5559 起 90 填充。
- **Y3** **TagClass** ctor `0x6E4DE0` 整窗 0x42 逐字节：`[esi+0x24]=arg`、+0x28/+0x2C 清
  dword、**+0x34/+0x35 清字节**（`885e34 885e35` @0x6E4E01）、`+0x30=[0xB0E700]`、装主 vptr
  `0x7F44E0` 与三 facet vptr——与 Y1 五字段签名逐项吻合。
- **Y4** **排除法反证宿主≠TriggerClass**：TriggerClass ctor 对 +0x34 是 **dword** 写
  （`894e34` @0x725FC4），字节写止于 +0x30；ctor 跨度内 `c6463400`/`c6463500` census=**0/0**
  ⇒ 0x6E53A0 的字节 +0x34/+0x35 与 TriggerClass 布局矛盾。**阳性对照内嵌**：同 pattern 在镜像
  他处有命中（机制看得见，零命中非尺子坏，G-13）。
- **Y5** Tag ctor `0x6E4F27` 起循环：`push 0x48; call 0x7C8E17`（new，尺寸 0x48=TriggerClass，
  R-047 在册）、`push arg; mov ecx,eax; call 0x725FA0`（**rel32 机械复算 = 0x725FA0**）、
  头插 **`[esi+0x28]`**（`8b5628 895028 894628` @0x6E4F41）⇒ **TagClass+0x28 = trigger 链头**。
- **Y6** `0x6E53A0` 起步 `mov esi,[ebp+0x28]`、回边 `mov esi,[esi+0x28]`、循环体
  `mov ecx,esi; call`（**rel32 复算 = 0x7264C0** = R-048 收割趟，其全镜像唯一 E8 入口在册）
  ⇒ 宿主对象持有 trigger 链且逐成员调收割趟——链路同一性闭合（R-048「链成员即宿主对象」的
  宿主侧现在取证）。
- **Y7** `0x6E53A0` 在 .rdata/.data 对齐 dword census=**0**（非任何 vtable 槽）⇒ **非虚成员**；
  **阳性对照**=同扫描法命中 TagClass vtable `0x7F44E0` slot10 函数 `0x6E5610` 恰 1 处 @0x7F4508。
- **Y8** TagClass ctor 向**三**个向量注册 this（R-051 同型三腿）：
  `0x6E4E45→0xB0E720`（**专用 `DynamicVectorClass<TagClass*>`**，vptr `0x7EA5A4`，
  安装/降级 pattern 全段唯一站 `0x6E4D7D`/`0x6E4DA8`）、`0x6E4E98→0xB0F670`、
  `0x6E4EEB→0xB0F708`；ctor 跨度内尾存 `893481` **恰 3 处** = `{0x6E4E70,0x6E4EC3,0x6E4F16}`
  （可数控制，R-051 教训的制度化复用）。
- **Y9** 两代表调用点 this 皆取自 `[0x8B40CC]`（数据指针）按索引：`0x6E92F3 mov eax,[0x8B40CC]` +
  `0x6E92FC mov ecx,[eax+edi*4]`；`0x6EA4B1 mov edx,[0x8B40CC]` + `0x6EA4BE mov ecx,[edx+edi*4]`。
  `0x8B40C8` 的 vptr 安装唯一站 `0x4E7FCD` → imm `0x7EA5A4` = **同一个 `DynamicVector<TagClass*>`
  类型**（引擎级 tag 表，与 `0xB0E720` 同型）⇒ 迭代元素 = TagClass*、this = TagClass*。
- **Y10** RTTI 链解 `0x7F44E0 = .?AVTagClass@@`；槽11 WhatAmI：TagClass=`0x2C`(44)、
  TriggerClass=`0x26`(38)（kb/20 契约）⇒ 类同一性双证（字段签名 + RTTI/WhatAmI）。
- **S1（结构性·不计数）** `0xB0F698` = **第四共享 Abstract 表**（vptr 与 `0xB0F670` 同 `0x7E91EC`；
  安装/降级唯一站 `0x72586D`/`0x725898`；引用量纲 36）；`0x6E53A0` 尾段把**本对象**（ebp）经
  Add 槽后 `892c81` 存入它（体内该 pattern 恰 1 处=0x6E5546）⇒ 登记不定谳：收割驱动收尾
  自报进入延迟处理表。

## 2. 语义（登记不定谳）

`0x6E53A0` = **TagClass 的「逐 trigger 使能收割驱动」**：三重门卫（全局 `[0xA8ED6B]`、
本对象字节旗标 +0x34/+0x35、owner `[+0x24]` 非空）后置 +0x35=1 防重入；遍历 +0x28 trigger 链
逐成员调 `0x7264C0`（收割），命中路径调 `0x7265C0`/`0x726720`（TriggerClass 簇在册），收尾经
`0x7258D0`（WhatAmI==0x18 分派助手）并把本对象登记进 `0xB0F698`。**对 L-20 的意义**：驱动方
宿主已定谳，但「载入后必跑」的动态序证据仍未闭——调用点分布 73 站（`0x4D8xxx`/`0x51xxxx`/
`0x55Bxxx`/`0x6E9xxx`/`0x702Dxx` 等），静态无法定序（维持 L-20 开放）。

## 3. 残量更新

- **L-30 残余②已闭**（本轮）：宿主类=TagClass。
- **L-30 残余①被重述**：旧「attach 工厂 `0x6E4EC0..`」的地址**落在 TagClass ctor 本体跨度内**
  （`0x6E4DE0..0x6E4F59`，非独立工厂）；所谓「arg1 列表驱动构造」实为 Tag ctor 的
  `[[tag-arg1+0xA0]→+0xA8]` 节点链循环（0x6E4F19 起，Y5 窗在册）。新残量=① Tag ctor arg1
  （+0xA0/+0xA8 节点链宿主）的类归属——Tag ctor 的 3 个调用点 `0x6C20CE`（new 0x38 工厂形态）/
  `0x6E52D6`/`0x6E8D90` 在册待追；② Trigger+0x24 存的是**链节点**而非 Tag ctor arg1 原值
  （0x6E4F35 `push edi`，edi=Walked 节点 ⇒ R-048「owner=[T+0x24]」措辞应精确为「挂接节点」）。
- **L-20 不变更**（动态序证据仍未闭；驱动方宿主已定谳 TagClass）。

## 4. 诚实账

1. **变异偏移两处首稿错被 G-67 pre-run 拦下**：M4 首稿把 rel32 低字节写成 `0x6E4F39 want 0x36`
   （心算 rel32 高位）、M8 把尾存 SIB base 写成 `0x6E4F16 want 0x81`（真值：SIB 在 0x6E4F16..18，
   base 字节=0x6E4F18）；现值==预期机械断言当场拒入后修正。G-67 第四役。
2. **一处编辑时自纠**：M6 的 disp 字节位写错（0x6E53D9→0x6E53C9），pre-run 前自查窗 dump 修正。
3. **Y3 窗口拼接首稿 0x42/0x40 长度错配**（ValueError 当场暴露）：机器 dump 重对齐后逐字节
   与镜像全等。
4. **排除法断言配阳性对照**（G-13 纪律）：Y4/Y7 的「0 命中」都有内嵌的机制可见性对照。
5. **73 vs 72 口径**：R-048 当时登记「72 个 E8 入口」（raw 扫描），本轮 canonical 线性扫描
   aligned/raw 皆 **73**——差一站未追因（不影响宿主判定，登记不定谳）。

## 5. 复跑入口

```text
python re_atlas/tools/r052_tagclass_host.py     # 期望 10/10 + S1, exit 0
python re_atlas/tools/mutate_r052_gate.py       # 期望 pre-run OK + 13/13, exit 0
```
