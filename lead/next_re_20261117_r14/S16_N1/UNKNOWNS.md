# S16-N1 UNKNOWNS

| # | 项 | 状态 | 说明 / 已试通道 |
|---|---|---|---|
| U1 | 剩余 12 条 sub_ 残行的真实语义名 | [未证] | `0053A6C0`(effect tick,无 YRpp 地址)、`0053D8E0`(螺旋坐标,无绑定)、`0053DDA0`/`006CE320`(RemoveItem 同码 18 命中,不特异)、`0065E660`(docs 称 SpawnAircraftEdge 但 YRpp 无地址绑定)、`00430BA0`(Beacon.CPP 无 RTTI)、`0071AB60`(TemporalClass 未列名) 等；已试：YRpp h/doc 全地址扫描(1,576 地址)、RTTI/vtable、Msg:/EVA 串、源码 __FILE__、调用者名、basename 全库 grep。 |
| U2 | N5 `TimerStruct::Pause` 的显式 YRpp 地址绑定 | [静态推断] | 本机唯一字节签名(1/4.06M)+同簇 StartIfEmpty=0x6CE2C0 地址绑定+源码语义逐字吻合；YRpp 快照未给 Pause 的 JMP_THIS 地址，故不升 [已证]。 |
| U3 | 3 条 reused 的审计名 vs YRpp 名差异 | [已证] | YRpp 称 `PrintMessage`，审计认证名为 `AnnounceActive`；按 CARD 指示保留审计名，不自行改名。 |
| U4 | grade 改动 | [已证] | 本卡 8 行 grade 全部与盘上一致，未动 proved(46/90)。 |
| U5 | 真机 DoD #5 / KB S16 | 缺 | 本卡只补名字，按令不碰。 |
