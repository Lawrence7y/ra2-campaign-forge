# W78 · UNKNOWNS（未解决 / 未覆盖 / 待运行验证）

执行者 **Hy4**（W78，非 Lead）。分级：`[待运行验证]` / `[静态推断]` / `[本次实测边界]`。

## U1 · 歼灭类胜利（destroy_all_forces）在真机上到底能不能判胜？ — `[待运行验证]`，**P1**

`[本次读码]` 已确认 ra2forge 的 design schema / builder 会 emit
`event 11 AllDestroyed(P2=4 British) → action 1 WinnerIs(P2=8 Russians)`，且 `[Houses]`
顺序与 HOUSE_INDEX 一致 ⇒ 参数接线正确（见 COMBAT_LOAD_RESULT.md §1）。

`[本次实测]` 但真机 2 次尝试**都没有观察到它产生胜利结算**：
- trip1（v1 远端敌人，annih）：150 s 内敌方未被全歼（远程对射僵持），无结算屏；
- trip2（v2 近距敌人，annih）：玩家先被全歼，出现 RA2「重新執行此場任務嗎」战败对话框。

⇒ 不能写「歼灭胜利已在真机验证可用」。**能力缺口登记在运行时层，不是 schema 层**：
本卡只证明了「触发器会被写进 .MAP」以及「AllDestroyed/LoserIs 的失败侧会触发」，
没有证明「AllDestroyed→WinnerIs 在真实战斗负载下能通关」。

判别实验（未运行）：造一张玩家绝对优势的近距图（如 16 辆 Hunt 苏军坦克 vs 2 辆英军坦克、
无英军建筑），使敌方一定能被全歼，再看 `GUI:Continue` 胜利计分屏是否出现。
若仍不出现，则是 ra2forge 的 `ev_all_destroyed` 事件在引擎上不生效（产品级缺口）；
若出现，则是本卡兵力配比/AI 行为问题。

## U2 · `survive(55)` 的胜利屏为什么在 wall t≈29.6 s 出现？ — `[待运行验证]`，**P1**

trip3 / trip4 的 `survive(55)` 变体都在 wall t≈29.6 s、frame=915 停滞时出现
`任務完成` + 苏军胜利计分屏（两趟一致）。设计值是 55，观测值不是 55。

两种解释本卡**无法区分**：
1. `ElapsedTime(55)` 的引擎时间单位与本卡的 wall 秒不是 1:1（游戏速度/计时器缩放），
   55 个引擎时间单位 ≈ 29.6 wall 秒 ⇒ 确实是 `survive` 时间触发判胜；
2. 引擎内建「敌方全灭即胜」在 ~29 s 先触发（trip3 t=25 截图里仍可见蓝色英军坦克，
   但可能已是残骸/即将清空），而 `ElapsedTime(55)` 根本还没到。

`[静态推断]` W76 的 `survive(8)` 结算屏「所花時間 00:00:07」、frame 停滞于 210，
看起来是 1:1；但本卡 55→29.6 又不像 1:1，二者口径不一致，不能强行统一。

判别实验（未运行）：跑一张**没有任何敌方单位**的 `survive(55)` 图（无战斗），
看胜利屏出现的 wall 时间；若仍是 ~29.6 s ⇒ 解释 1；若 ~55 s 或干脆不出现 ⇒
解释 2（trip3/trip4 的胜利来自引擎内建全灭判定，时间触发未验证）。
在此之前，本卡**不宣称**「survive(55) 的时间触发已在本卡判胜」。

## U3 · 单位计数变化（内存直读）未取到 — `[本次实测边界]`

任务允许「若你知道单位表地址就用；不知道就用截图 + 帧率变化做间接证据，并注明是间接的」。
本卡**没有**在本机 gamemd.exe 上验证过任何「活单位表」地址：
`re_atlas` 中可查到的 `0x00A8B270` 是 RulesClass+0x1494 的 `UnitCount` 全局镜像（多人设置项，
不是局内活单位数），`0xA8EAE8` 是 `DynamicVector<TriggerClass*>` 专用表（触发器，不是单位）。
按红线「不臆造未给定的地址/字段」，本卡**没有**把这些地址当成单位表来读，也没有
伪造单位计数。改用：截图（直接视觉）+ 帧率轨迹（间接）+ 游戏自生成 `.sav` /
计分屏 / frame 停滞（直接状态证据）。强度分级见 COMBAT_LOAD_RESULT.md §6。

## U4 · 计分屏击杀/损失数字未读出 — `[本次实测边界]`

trip3/trip4 的计分屏控件枚举到 `GUI:StandaloneScore` / `GUI:YourTime` / `GUI:ParTime` /
`GUI:HeadsTaken` / `GUI:Blank`，但截图 `screen_trip3_settlement.png` 中计分面板左侧被
对话框裁切，数值仅部分可见（「平 0 / 所 0 / 獲 3」），**未能可靠读出「殲敵數/損失數」**。
因此本卡不把计分屏数字当作「战斗确实发生」的量化证据。若需该量化证据，需重跑并
用全屏（2560×1440）抓取或放大计分面板。

## U5 · v1 远端布局为什么会僵持 — `[静态推断]`

敌方 6 坦克 + 6 步兵置于 rows 8–14（距我方 ~35 格），`hunt_wave`(AllToHunt, t=3) +
`mission="Hunt"` 都写了，但 t=20 起在我方基地右侧出现弹坑、t=40 有炮口焰、t=60 有单位冒烟，
t=176 双方均未被全歼。推测是「Hunt 单位在最大射程边缘与我方 Guard 单位对射、
双方都不推进」；未做逐单位轨迹/寻敌读点，不能写成机制结论。

## U6 · 战斗结果在相同布局下不确定 — `[本次实测]`

v2 近距同一布局：trip2（annih 变体）玩家 ~69 s 战败；trip3 / trip4（time 变体）
玩家 ~29.6 s 胜利。两者唯一设计差异是胜利触发器类型（AllDestroyed vs ElapsedTime）；
本卡无法排除这是战斗 RNG（散布/伤害/寻敌）造成的胜负摆动。
⇒ 不要据此推断「换胜利条件会改变胜负」。要定性需固定随机种子做 A/B 多趟重复。

## U7 · 覆盖范围（不外溢） — `[本次实测边界]`

只测了：1 台机、1 个 ra2youli 镜像、1 个 v15 工具链、4 趟真机、
**本卡自己造的 4 个包**（v1 annih / v1 time / v2 annih / v2 time / 2 关链，共 5 个包中
v1 time 只离线编译未真机）。
未覆盖：其它地图/兵力/阵营/分辨率/语言版本、其它关数（>2）、`SkipMapSelect=yes`、
变体 B（MAPSELMD 子项 `2=`）真机对照、官方全战役通关、破坏特定建筑/摧毁全部建筑/
reinforce/占领等其它 objective 的真机行为、`destroy_all_forces` 的胜利侧（U1）。

## U8 · MAPSELMD 2 关链只跑了主用变体 A（from1） — `[本次实测边界]`

2 关链 package 的 MAPSELMD 用 W76 主用变体 A（追加阶段子项键 `1=<下一阶段>`，
`[Nod]` 键 1..9 连续）。v15 原生对照变体 B（`2=`，SHA `8fee7aa6…`）已离线生成
（`out\MAPSELMD.INI.chain_from2`）但**未**真机跑 A/B 单变量对照。
因此本卡不主张「from1 是必需项」，只主张「本卡这个 2 关包用 from1 在
SkipMapSelect=no 上推进成立」。

## U9 · trip2 的脚本级分类是误报，不是引擎错误 — `[本次实测]`

trip2 在 08:08 运行时，run 脚本的 `ERR_TOKENS` 含通用 `GUI:OK`，把 RA2 战败/
「重新執行此場任務嗎」对话框（`GUI:Blank/GUI:Cancel/GUI:OK`）误判为 error dialog
并 `trip_blocked`。截图 `screen_trip2_error_dialog_t71.png` 目视确认是战败重启确认框。
08:11 已把 ERR_TOKENS 收窄为仅 W59/W76 的地图装载错误串，并给 `is_settlement` 增加
该对话框识别；trip3/trip4 用修正后的脚本，无 `trip_blocked` / `FATAL` / 真 error_dialog。
trip2 的原始 ndjson/截图保持原样未改，本卡如实标注它是脚本误报。
