# LEAD_W28_VERIFY · W28「NextScenario 形式」独立复核

> 复核人：Lead（本会话）｜ 日期：2026-11-13
> 复核方式：**不采信 W28 摘要**，用自写脚本对 `W28_nextscenario_form/out/official_maps/` 下 14 份官方图原件 + ra2forge 构建产物 `ECH01.MAP` 直接做字节级提取。

---

## 1. Lead 自己的复算结果（原始字节）

```
file             [Basic]@ NextScenario     AltNextScenario  eol
ALL01UMD.MAP         7544 GDI2A.map        GDI9C.MAP        CRLF
ALL02UMD.MAP         3747 GDI2A.map        GDI9C.MAP        CRLF
ALL03UMD.MAP         8649 GDI2A.map        GDI9C.MAP        CRLF
ALL04DMD.MAP         3482 GDI2A.map        GDI9C.MAP        CRLF
ALL05UMD.MAP         2984 GDI2A.map        GDI9C.MAP        CRLF
ALL06UMD.MAP         3455 GDI2A.map        GDI9C.MAP        CRLF
ALL07SMD.MAP         1675 GDI2A.map        GDI9C.MAP        CRLF
SOV01UMD.MAP         6350 GDI2A.map        GDI9C.MAP        CRLF
SOV02SMD.MAP         3798 GDI2A.map        GDI9C.MAP        CRLF
SOV03UMD.MAP         8134 GDI2A.map        GDI9C.MAP        CRLF
SOV04DMD.MAP         2931 GDI2A.map        GDI9C.MAP        CRLF
SOV05UMD.MAP         1984 GDI2A.map        GDI9C.MAP        CRLF
SOV06LMD.MAP         2910 GDI2A.map        GDI9C.MAP        CRLF
SOV07TMD.MAP         3871 GDI2A.map        GDI9C.MAP        CRLF

distinct NextScenario = ['GDI2A.map']

ra2forge ECH01.MAP: [Basic]@247 NextScenario=b'ECH02.MAP' eol=LF size=4671
```

`[本次实测]` 14 张官方 MD 图的 `NextScenario` **无一例外全部是 `GDI2A.map`**，`AltNextScenario` 全部 `GDI9C.MAP`，行尾 **CRLF**。
`[本次实测]` ra2forge 产物 `NextScenario=ECH02.MAP`，行尾 **LF**。
`[本次实测]` 两者**形式一致**：均为「裸文件名 + 扩展名」，无路径、无前导 `\`、扩展名齐备。**差异只有两处：大小写（`.map` vs `.MAP`）、行尾（CRLF vs LF）。**

⇒ W28 的 T3 = `[形式相同]` **成立**，其「写法不是成因」的结论我签发。

---

## 2. 但 W28 顺带挖出的东西比它自己的结论更重要

### 2.1 `GDI2A.map` 是泰伯利亚之日的占位名，官方链目标根本不存在

`[转引]` W28 称其 CRC `B639B8AC` / `A63E1B0F` 在 17 个容器与游戏目录散装中**均不存在**（未被我独立复算，标转引）。

`[静态推断·强]` 若成立，其含义是：**官方战役自己也没有可用的 `NextScenario` 链** ⇒
- 官方图**不能当「能工作」的正对照**（W28 已自我声明这点，诚实）；
- 更可能的是：**官方战役推进根本不走 `NextScenario`**，而走 `BATTLEMD.INI` 的 `[Battles]` 编号序列（`1..14`，每项一个 `[ALL1]/[SOV1]…` 段，段内 `Scenario=ALL01umd.MAP`）。
- `NextScenario=GDI2A.map` 很可能是 **TS 时代的遗留字段**，引擎在 RA2/YR 战役路径上不读它。

`[待运行验证]` 这条若为真，则 Q2 的排查方向要整体改向：不是「修 `NextScenario` 写法」，而是「**战役推进是否按 Battle 表序号走**」，以及「序号 15 的记录为何推进不到」。

### 2.2 另一条竞争假设：`Scenario=` 走文件系统，Continue 走 MIX/CRC

`[转引]` W28 提出：官方图在 MIX 内（CRC 寻址），ra2forge 的 `ECH02.MAP` 是**散装**；若 `Scenario=` 走文件系统而 Continue 推进走 MIX/CRC 查找，就能同时解释「D2 直接指向成功 / D3 链式推进失败」。

`[静态推断]` 这个假设**能解释观测到的非对称性**，是目前最贴合证据的一条。但注意它和 §2.1 冲突：
- 若 §2.1 成立（NextScenario 是死字段），Continue 就不该去解析 `GDI2A.map`，也就谈不上 MIX/CRC 查找；
- 若 §2.2 成立（Continue 真去解析 `NextScenario`），那官方自身点 Continue 也必然报同样的错——**这一点极易验证，是本轮最该做的下一步**。

**两条假设互相排斥，且都有廉价判决实验**，见 §3。

---

## 3. 下一轮的最小判决实验（暂停中，未执行）

| 编号 | 实验 | 判决什么 | 成本 |
|---|---|---|---|
| **E1** | 真机跑**官方** `[SOV1]` 原样（`Scenario=SOV01umd.MAP`），打到胜利后点 Continue | 若也弹「無法啟始選取地圖！」⇒ §2.1 成立（NextScenario 是死字段，官方自己也不走它）；若正常进下一关 ⇒ §2.2 成立（引擎确实按 `NextScenario` 解析，且能解析 MIX 内的 `GDI2A.map`…但该文件不存在，仍需解释） | 中（要打一关，可用 `survive` 加速） |
| **E2** | 把 `ECH02.MAP` 打进 `expandmd98.mix`（ra2forge 已会生成该 mix）后再 Continue | 若成功 ⇒ MIX/CRC 查找假设成立，修复方案 = 把后续关也打进 MIX | 低（离线改构建 + 一次真机） |
| **E3** | 在 `BATTLEMD*.INI` 里给 A2 单独登记一条 battle（`16=RA2F2`），A1 的 `NextScenario` 指向它或用表序推进 | 判决推进是否按 Battle 表序号 | 低 |

`[静态推断]` E2 性价比最高且能直接产出修复方案；E1 决定性最强。**建议 E1 与 E2 并行（E1 需游戏实例，E2 离线可先备好包）。**

---

## 4. W28 未覆盖项（沿用其自述，我确认合理）

- `theme.mix` / `thememd.mix` 未开（C&C 格式，mixlib 明确不支持，与战役图无关）——合理
- MIX 索引无明文名，故「大小写与容器条目一致」无法字面核验——合理，但 §1 已证明大小写不是变量
- **官方 CRLF vs ra2forge LF 的行尾差异在推进路径上未验证**——这条我标为**真实未决项**，不得因「W10 已否证 CRLF」而跳过（W10 针对的是地图**列表显示** `No Name`，症状不同）
- 未反汇编引擎、未读活进程、未做 T2——合理

---

## 5. 结论

`[签发]` T3 **形式相同**，`NextScenario` **写法不是 Q2 成因**；ra2forge **不需要改写法**（把扩展名改小写预计无效，不建议当修复）。
`[未签发·待运行验证]` Q2 真正成因有两条互斥假设（NextScenario 为死字段 / MIX-CRC 查找），必须用 §3 的 E1/E2 判决。
`[不得外溢]` 不可写「Q2 已定位为 MIX 查找问题」——那只是假设之一。
