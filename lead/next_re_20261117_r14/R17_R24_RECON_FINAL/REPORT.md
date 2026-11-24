D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe  sha256 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476

# R17-R24-RECON-FINAL · RTTI × coverage 对账第三版（权威数）

- 校验：第一行路径与 sha256 实测；前缀 73201CC0、尾部 F67476，有效。
- 镜像 4825360 B；只读 .rdata 200704 B + .data 442368 B = 643072 B；未建进程、未调试、未启动 gamemd。
- coverage.tsv 4147334 B，sha256 C2EE063FD4F61F784585EF2ABCC4FF563FA09EC1B1F7F5079643076E359C744A，只读且写后未变。

## Q1 · 复合名口径

- 988 个 TD 中含 @ 复合名 660 条（模板态 634、非模板 26：A@B 24、A@B@C 2）；全量见 compound_names.tsv。
- 形态计数：plain_A@B 24、plain_A@B@C 2、template_at1 132、template_at10 7、template_at16 3、template_at2 1、template_at3 420、template_at4 50、template_at5 4、template_at6 4、template_at7 6、template_at8 7。
- 规则（写进 work.py）：X_Y / X_Y_Z 全体下划线替换为 @，与非模板复合 TD 的 X@Y / X@Y@Z 做大小写不敏感精确相等；禁止丢段取基名。模板态 @ 不适用本规则。
- 26 条非模板复合 TD：Anim@Voices@WorldDominationTour @0x849218、CComObjectRootBase@ATL @0x84a838、Campaign@WorldDominationTour @0x8480f0、CampaignProperties@WorldDominationTour @0x848d08、Conflict@WorldDominationTour @0x848290、DialogControl@OwnerDraw @0x836408、FactionSelectDialogControl@WorldDominationTour @0x84d798、FlagGameOption@WorldDominationTour @0x8486d0、GameOption@WorldDominationTour @0x8485a0、History@WorldDominationTour @0x848768、IChatEvent@WOL @0x84a818、IDownloadEvent@WOL @0x84d6a8、INIEntry@INIClass @0x825af0、INISection@INIClass @0x825b40、INetUtilEvent@WOL @0x84a7a0、InitializerBase@MultiplayerGameMode @0x8309c0、Map@WorldDominationTour @0x8488b8、MapSizeGameOption@WorldDominationTour @0x848730、RTacticalClass@RadarClass @0x839298、SBGadgetClass@SidebarClass @0x83f8c8、SelectClass@StripClass@SidebarClass @0x83f8f8、Selection@WorldDominationTour @0x848da0、SimpleDialogControl@OwnerDraw @0x836430、State@WorldDominationTour @0x849108、TacticalClass@DisplayClass @0x820048、Territory@WorldDominationTour @0x849130。
- 审计 A2 的 SelectClass_StripClass_SidebarClass 两-TD 写法与本轮实测不同；实测是 SelectClass@StripClass@SidebarClass @0x83f8f8（三段），不影响 6 条计数。

## Q2 · 权威三桶（双口径并列）

S=严格基名：大小写不敏感裸名精确相等，保留已审过的 P/A/V 前缀与模板基名键，不接受下划线取段。C=复合名：S 之上加 X_Y↔X@Y 完整匹配。BOTH/COVERAGE_ONLY 分母 429 token；RTTI_ONLY 分母 988 TD 条目。

| 口径 | BOTH | COVERAGE_ONLY | RTTI_ONLY | 机制 |
|---|---:|---:|---:|---|
| S | 397 | 32 | 383 | exact 209 + prefix 186 + template_base 2 |
| C | 403 | 26 | 377 | exact 209 + prefix 186 + compound 6 + template_base 2 |

| 历史/纠正 | BOTH | COVERAGE_ONLY | RTTI_ONLY | 变化原因 |
|---|---:|---:|---:|---|
| R19 | 209 | 220 | 779 | →S：+186 前缀、+2 模板基名；后者覆盖 396 个实例，故 RTTI_ONLY -396 |
| R20 | 403 | 26 | 383 | →S：-6/+6，撤销 6 条下划线取段；这些原为悬挂匹配，RTTI_ONLY 不变 |
| 审计纠正 | 397 | 32 | 383（隐含） | 与 S 独立复算一致；32 未抄写 |
| 本次 C | 403 | 26 | 377 | 6 条改为复合 TD 匹配；6 个 TD 新增覆盖，RTTI_ONLY 383→377 |

C 新增覆盖：INIEntry@INIClass、INISection@INIClass、RTacticalClass@RadarClass、SBGadgetClass@SidebarClass、SelectClass@StripClass@SidebarClass、TacticalClass@DisplayClass。

## Q3 · 剩余未解析项归因复核

C 口径 COVERAGE_ONLY 26 条；逐条见 unresolved_final.tsv。分布：(g) 已由 coverage 内已验证 IID 解决 4；(i) 共同基类重复计数/无独立 RTTI 1；(f) 名字在镜像 ASCII 中零出现 6；(h) 仅以容器模板实参/表行名出现（非模板类） 9；(b) 复合名前缀片段 3；(e) 其它/保守未判定 3。

1. 模板类 9 条：审计批评成立；本轮 9/9 无独立 TD、仅 2 条模板实参 TD 命中，其中 7+ 条 coverage 上下文有 XxxClass::，2 条仅容器行名。改归 (h)，不称模板类。
2. 无独立 vtable 6 条：审计批评成立；6/6 全镜像 ASCII 0 次，coverage 自标 YRpp/kb 地址名；不能从无 TD 反推无 vtable，改归 (f)，不是名字错。
3. 疑似命名差异 5 条：审计批评成立；4 条 MP* IID 解码 4/4 对上 TD，归 (g)；MPGameModeClass coverage 明写无 RTTI 且为共同基类重复计数，归 (i)。

## Q4 · 修正后的正面表述

以 coverage 第 4 列按 Class 后缀正则抽出的 429 个不同 token 为分母：S 口径 397（92.54%）、C 口径 403（93.94%）在 in-binary RTTI 中有对应键；这不是按 3777 次出现的覆盖率，不表示独立验证；186 条前缀 token 命中已被其他 token 覆盖的同类，不新增定位。in-binary 只覆盖有 RTTI 的类；ASCII 零出现项无法用该方法定位。未解析仅表示本口径下未找到对应物，不表示 coverage 名字错。

未取得项：0。
