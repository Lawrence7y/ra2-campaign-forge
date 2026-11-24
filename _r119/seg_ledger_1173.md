## §1173 R119 · `.data` IID 拷贝的代码证据推翻 R118 邻接判据；C16 把「整节清空」从 16/16 不可见变成 0/16

### §1173.1 业务结论（可机械核验）

`.data` 里 5 个 COM 形态 GUID 常量**全部**被 `.text` 以指令对齐的立即数引用，按「push 后第一条 call 的落点」分类：

| `.data` 常量 | 值（d1） | 站点 | 分类 |
|---|---|---|---|
| 0x817bc0 | 0x0（IID_IUnknown） | 9 | CoCreateInstance 8 + `call [ecx]` 1 |
| 0x818858 | 0x10c（IID_IPersist） | 16 | `call [ecx]` 15 + `call [edx]` 1 |
| 0x81fc50 | 0xc（IID_IStream） | 2 | `call [ecx]` 2 |
| 0x820270 | 0x109（IID_IPersistStream） | 8 | `call [ecx]` 8 |
| 0x87da00 | 0x20400（IID_IDispatch） | 1 | `call [ecx + 0xc]` 1 |

另有 2 个同值拷贝（0x817bb0 ILocomotion 4 站点、0x819088 IPiggyback 8 站点）同样有真实引用。

⇒ R118 §EK4 把其中 3 处判为「同值巧合字节」并据此回退按值数字，**该回退撤销**：IUnknown 65、ILocomotion 11、IPiggyback 8（恢复 r118a 原值）。R118 的邻接判据另有配对歧义：0x818858 在 gap 0x10 与 0x30 处分别紧邻 `.?AV?$VectorClass@G@@` 与 `.?AV?$DynamicVectorClass@G@@`；0x820270 在 gap 0x10 与 0x28 处分别紧邻 `.?AVEditClass@@` 与 `.?AVDropListClass@@`。故「GUID+type_info+类名」不能唯一配对。

**判据口径的另一处纠错**：R112..R118 的「push 站点数」混合了 `QueryInterface(riid, ppv)` 与 `CoCreateInstance(rclsid,…, riid, ppv)` 两种语义（IUnknown 的 9 个站点 8 个属后者）。数字算对、口径把两件事并成一件。

### §1173.2 门禁 C16 家族（四处，均已装盘并回归）

| 子项 | 判据 | 反控 |
|---|---|---|
| C16 | 116 节逐节字节 >= 建表值的 25%（下限 300 B） | 清空 2.107..2.122 ⇒ 0/16 漏检（原 16/16） |
| C16b | 表外新节张数 <= 2 | 追加 3 个表外节 ⇒ FAIL |
| C16c | 表外新节必须 >= 1 行正文 | title-only 空壳 ⇒ FAIL；带 1 行正文 ⇒ PASS |
| C16d | 下界表 sha256 钉 | 只改 1 个 floor 不同步改 sha ⇒ FAIL |

`GATE_VER` 由 `R103` 升为 `R119`，`DISC_RECHECK.tsv` 第 20 行同步登记（C10 独立性）。成对回归 `_r119/r119e_gate.py` **14/14 PASS**；旧 gate 与旧表配套后作干净对照（S-63）。

### §1173.3 数值台账（本轮新增/更正）

| 项 | 值 | 依据 |
|---|---|---|
| `.data` COM 形态 16 字节常量 | 5 | r119b B1 |
| type_info vftable 0x7f9594 出现的 dword | 988（全在 .data） | r119d D1 |
| 其中 `.?AU` 接口 | 26 | r119d D1 |
| GUID 常量紧邻 type_info 的配对（gap 4..0x40） | 5 对，2 个常量各有 2 个候选类 | r119f G1 |
| `shl` 移位量 4 的站点 | 616 = 599(C1 32 位) + 13(C0 8 位) + 4(66 C1 16 位) | r119d D4 |
| 反控：移位量 8 的 C1 形态 | 897 | r119d D4 |
| C15_SECS 覆盖 | 100 / 116 节（漏 16 节，168,835 B，占 2.x 正文 21.7%） | r119a H2 |
| 覆盖集内连续清空多少节才跌破 byte floor | 8 | r119a H3c |
| R14_COMMON 节和 vs 文件字节 | 778,085 vs 1,008,448，差 230,363 = preamble 230,247 + 116 个边界 LF | r119g A4 |
| 116 节内部 CR 数 | 0（1081 个 CR 全在 preamble） | r119g A4b |

### §1173.4 范畴边界

① 未给出 0x7f7c70 的接口名（本机仍无 IID→名映射表）。② 「push 后第一条 call」判据的三种失败模式（夹入 helper call、第一条 call 是虚调用但确消费 IID、跨基本块尾跳转）由审计员列出、复算确认对本样本 8/1 计数无影响，**不向其他 IID 推广**。③ C16 家族只抬成本，不防「同改表 + 同步改 sha + 同步改 GATE_VER」的协同伪造。④ 25% 下界对未来的合法大幅删减仍会误伤，届时须显式重钉。⑤ 门禁 C11 的 5 条 FAIL 与 5 处「永远通过」子项本轮未动。
