# S13-K10 DISAGREE — 与既有结论的分歧/一致性说明

## 1. 与 S13_K6 的名字相同
K6 PROGRESS.md 已列 0040B640=DynamicVectorClass<BombClass*>::Clear、0040B670=VectorClass<BombClass*>::GetItemIndex 等。K6 被审计 FAIL 的判据是「slot-baseline（全 .text 6,313 处同类虚派发，检出力=0）」，不是名字本身错。本卡：
- 不引用 K6 结论作为证据（只在 ⑱ 冲突扫描时发现其存在）；
- 以 capstone 解码的字节合同 + YRpp 源虚序 + K9 已证的 slot↔语义锚点独立复算；
- 环④用 K8 installs（活 vptr 写全局）而非 slot 存在性，符合 CARD 硬禁令 2。
审计若认为「合同与源虚序同属通道 A、K8 RTTI 也属通道 A」，请注意：K8 的 RTTI/VT 是**盘上字节事实**（类归属），合同是**函数体行为**（语义动词），两者不可互相推出；K9 的 slot2/4/6 锚点来自 exact call 站点（通道 B 的分支）。这是本卡能给出的最强双通道。

## 2. 0040F5E0 剔除
K6 和 K8 都把它列为 DynamicVectorClass<WarheadTypeClass*>::Clear；KICKOFF_R14_SUCCESSOR_3.md 指其 exact 调用点为幽灵绑定。本卡保守剔除，保留 [静态推断]。若审计认为 ④ 误绑不影响 ③ 的字节合同，可在本卡结果上追加 1 行（总计 44）——但不主动升。

## 3. 检出力基线口径
合同单判据 2.02% 误命中率不算「零误命中」；本卡的判据是**合同 + RTTI 类属 + 槽位一致 + vptr 安装**的合取，在 106 行候选集内无歧义（合同/槽号 44/44 一致）。随机 .text 基线 393 个合同命中中，多数是其他容器族的真实同构函数（例如 0x40CAF0/0x40CC80），不是本卡候选；合取判据下这些函数因无 S13 RTTI 归属 + 安装点而不入集。