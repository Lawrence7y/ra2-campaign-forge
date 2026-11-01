# R-050 · L-30 残量再收口：TriggerClass 注册表容器定谳 = `DynamicVectorClass<AbstractClass*>` @`0xB0F670`（**不是** `<TriggerClass*>`！）

门禁 `tools/r050_trigger_registry.py`：**7/7 字节断言 PASS**（S1 结构性不入分母，红仍非零退出）；
变异 `tools/mutate_r050_gate.py`：**12/12 killed（精确集合；含内嵌现值断言前置）**。

## 1. 结论链（全部字节级，gamemd.exe sha256 73201cc0…f67476 只读）

**收口对象**：R-048 登记的「owner 类 `[T+0x24]` 与调用方 `0x6E53A0` 宿主」残量中，
先闭掉「TriggerClass 实例被哪个容器持有」这个子问题（它同时给出 GOAL-3T 想要的
「遍历全部 trigger」入口）。

- **W1** 全局 ctor `0x725350` 整窗 0x3D：`[0xB0F674]=0`（数据）、`[0xB0F678]=0`、
  grow 旗标 `[0xB0F67C]=1`、`[0xB0F67D]=0`、**vptr `[0xB0F670]=0x7E91EC`**、
  cap `[0xB0F684]=0xA`、计数 `[0xB0F680]=0`，`push 0x725390` + `call` atexit 助手
  （rel32 复算 = `0x7C978A`）。
- **W2** 安装 pattern `c70570f6b000ec917e00` 与降级 pattern `c70570f6b0000c927e00`
  在全 `.text` **各唯一**（raw-find==1 站：0x72536D / 0x725398）⇒ `0xB0F670` 的
  容器类型只有这两个写主（ctor 安装 / dtor 降级），无第三方改写。
- **W3 RTTI 名定谳**（`vt → COL(vt−4) → TD(COL+12) → name(TD+8)`）：
  `0x7E91EC = '.?AV?$DynamicVectorClass@PAVAbstractClass@@@@'`、
  `0x7E920C = '.?AV?$VectorClass@PAVAbstractClass@@@@'`（降级态）。
  **阳性对照**=同一方法解 House 对 `0x7E9EE4/0x7E9F04` 得 `PAVHouseClass`（R-043 在册）；
  **反证对照**=名串 `.?AV?$DynamicVectorClass@PAVTriggerClass@@@@` 在镜像**存在**、
  但 `0xB0F670` 装的**不是**它 ⇒ 持有 TriggerClass 的静态容器类型参数是
  **`AbstractClass*`**（G-62「关系≠等号」同族：持有≠类型参数）。
- **W4** 全局 dtor `0x725390` 窗（读 `[0xB0F674]` 判非零→`call 0x7C8B3D` 释放数据→
  vptr 降级 `0x7E920C`）与 House 降级站 `0x4E6D28` 同形态（`c7 05 …` + demote-imm）。
- **W5** TriggerClass ctor `0x725FA0` 内注册块 `0x725FE9..0x726037` 整窗逐字节钉：
  `mov eax,[0xB0F678]` vs `cmp [0xB0F680]`（容量查）、`cmp byte [0xB0F67D]`（grow 旗标查）、
  `mov ecx,[0xB0F684]; cmp ecx,ebx`、`mov edx,[0xB0F670]; and eax,edx`（vptr 掩码）、
  **`mov ecx,0xB0F670` + `call dword [edx+8]`**（容器虚槽 2=Add，与 R-043 House 向量
  调用形态同）、计数自增回写、尾 **`mov ecx,[0xB0F674]; mov [ecx+eax*4],esi`**
  （SIB 原始指针入册）。
- **W6 esi 保全**：ctor 头..存点间写 esi 的指令集 == {0x725FA2 `mov esi,ecx`}
  （capstone 寄存器目的谓词）⇒ 入册的 `esi` = **TriggerClass 的 this** 本身。
- **W7** `mov ecx,0xB0F670` 全 `.text` census == **58 站**（内嵌定位对照：含注册站
  0x726016）⇒ 这是**引擎级共享 AbstractClass 注册表**（非 trigger 专属；House/Radar/
  各 AbstractClass 后代都入它）。
- **S1**（结构性·不计数）slot11 WhatAmI `0x726940` = `mov eax,0x26; ret` 且
  = vtable `0x7F5858+0x2C`（R-047 T1 复证）⇒ **遍历 `0xB0F670` 筛 WhatAmI==0x26
  即得全部 TriggerClass 实例**（kb/20 契约用法）。

## 2. 残量更新

- **L-30 再收口（本轮）**：TriggerClass 实例容器类**定谳**。注册表 =
  `DynamicVectorClass<AbstractClass*>` @`0xB0F670`（三字段 `[+4]=data,[+10h]=count,
  [+14h]=cap`，另有 grow 旗标 `[+0xC]/[+0xD]`——注意这是**全局单例的 .data 布局**，
  字段距与 VectorClass 成员距 4/8/0x10 的对应关系登记不定谳）。
  「谁持有 TriggerClass」的答复=**全体 AbstractClass 共享的引擎级注册表**，
  不是专用 trigger 向量；专用 trigger 链另有其头（`[owner+0xAC]`，R-043 Y5 域）。
  【**勘误·R-051（本轮推翻）**】本句**不成立**：TriggerClass ctor 实际向**三个**容器注册
  this，除 `0xB0F670`/`0xB0F708`（皆 `DynamicVector<AbstractClass*>`）外，还有**专用表
  `DynamicVector<TriggerClass*>` @`0xA8EAE8`**（vptr `0x7E9BE4`）。R-050 只看到一条腿
  就外推到总体。见 `evidence/r051_trigger_three_registries.md`（8/8 + 12/12）。
  **R-050 其余结论不受影响**（`0xB0F670` 的容器类型、入册值=this、58 站量级 等全部成立）。
- **未闭残量缩小为两问**：① owner 类 `[T+0x24]`（ctor arg1；attach 工厂 `0x6E4EC0..`
  以 `[[ebp+0x20]+0xA0]→+0xA8` 列表驱动构造，arg1 即该表元素——其宿主 `0xB0F708`
  系全局向量待解）；② 调用方 `0x6E53A0` 宿主类（72 E8 入口）。新线索登记进 L-30 行。
  【**勘误·R-052（G-69）**】②已定谳=**TagClass 非虚成员**（`evidence/r052_tagclass_host.md`，
  10/10+13/13）；①的「attach 工厂 `0x6E4EC0..`」措辞**不成立**——该地址落在 TagClass ctor
  本体跨度 `0x6E4DE0..0x6E4F59` 内（第 2 注册腿中段），节点链循环就在 ctor 体 0x6E4F19 起；
  Trigger`+0x24` 实存**挂接节点**（0x6E4F35 `push edi`）而非 arg1 原值。残量①重述为
  「Tag ctor arg1 类归属（构造点 `0x6C20CE`/`0x6E52D6`/`0x6E8D90` 待追）」。
- **L-20 不变更**：重算趟遍历对象来源现在有了静态入口（注册表+WhatAmI 筛），
  「载入后必跑」仍待动态序证据。

## 3. 诚实账（本轮三处自纠 + G-60 第三次复发的现场）

1. **普查尺子错致假零命中**：首版 `_probe_r050_registry.py` 把节元组存成
   `(va,vs,rp,rs)` 却按 `(vs,va,rp,rs)` 解包 ⇒ `fileoff` 用 VA 比 RVA，窗口整体错位，
   全部全局引用报 **0**（与同轮 capstone 解码直读的 `0x72600E/0x726017` 当场矛盾才暴露）。
   **⇒ G-60 切片/基址家族第三次复发**。修：单一 canonical 元组 + 头行
   `assert SEC[0]==(0x1000,0x3DF38D,0x1000,0x3E0000)` 把顺序钉成可杀断言；
   普查配**控制项**（House 全局 `0xA80228` 同扫得 7 站——若机制坏连控制项都是 0）。
2. **谓词错方向致虚零**：esi 保全普查首版把「写 esi」写成「内存操作数基址=esi」
   ⇒ 报 0 条写入（假绿向）。修谓词（寄存器目的 + REGWR 助记符集）后真值=唯一
   `0x725FA2`——W6 断言自此**有内容**。
3. **变异偏移两处心算错被现值前置拦下**：M3（cap imm 窗口索引）与 M4（TD 名串 VA：
   首稿用文件偏移+IB 近似成 0x822EB0，真值=TD+8=0x8225F0）+ M10（尾存点址算错）；
   G-67 机械前置（现值==预期）全数当场拒入。⇒ 工序再验证一次。

## 4. 复跑入口

```text
python re_atlas/tools/r050_trigger_registry.py     # 期望 7/7 + S1, exit 0
python re_atlas/tools/mutate_r050_gate.py          # 期望 pre-run OK + 12/12, exit 0
```
