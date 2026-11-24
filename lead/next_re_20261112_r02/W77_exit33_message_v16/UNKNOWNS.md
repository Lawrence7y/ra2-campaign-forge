# UNKNOWNS — W77_exit33_message_v16

分级：`[本次实测]` / `[本次读码]` / `[静态推断]` / `[转引]`

## U1. ABSENT 分支的文案未产品化（范围外，留待后续小卡）
`resolve_integration.py` 的 `inplace_preflight()` 里与 EXIT 33 共用 reason code 的另一条消息——"the official loose BATTLEMD.INI is ABSENT"（v15/v16 均为 ~:956-962）——**保持 v15 原文**。W74 的场景是"文件被上一个包改写"（modified 分支），任务书只签发了这一条。`[静态推断]` 若后续要做，ABSENT 分支同样值得产品语言化（"游戏目录缺少官方 BATTLEMD.INI"），且同样只改字符串。

## U2. `<package_id>`/`<version>` 的降级分支未被本套件覆盖
v16 消息对"安装记录存在但身份不可读（`package_id` 缺失/`unknown`）"与"无安装记录但文件被改"走诚实降级文案（不点名包）。`[本次实测]` W77_1 只覆盖了主路径（有可读身份）；降级分支没有专门用例（任务书只要求 +1 条）。`[本次读码]` 该分支由 `install.py:_manifest_package_id` 的同款宽容规则驱动，行为上只影响文案措辞，不影响退出码/判定。

## U3. 归因表述的边界
主路径文案断言"它的安装改写过官方 BATTLEMD.INI"。`[静态推断]` 在"有安装记录 + 文件非官方"的观测组合下，这一归因理论上还存在第三种可能：装完包 A 后用户手工/第三方又改过文件（此时 A 的记录仍存在）。文案在 sha 对比里保留了证据（on-disk vs expected），且行为（拒绝 + uninstall 救济）在所有归因下都正确；只有"责任方"一词在极少数组合下可能失准。任务书已签发该措辞，本卡照签发执行，不做二次论证。

## U4. 套件对卡内夹具的依赖是路径耦合，不是用例耦合
S3_19/S3_20/S3_22/S4_8 读**卡根**的 `s1_revision\`、`TRACK_B_gates.json`、`baseline_v14\...\ra2forge_patched_v14\`。`[本次实测]` 这些夹具从 W60 卡只读复制后套件即通过；夹具内容本卡零修改。`[静态推断]` 若未来有卡再迁移该套件，这些夹具需要一并复制（或把路径提为显式 REF_ROOT 常量）。

## U5. v16 包内 docs/ 对 S4_8 的影响已按最小范围处理
`[本次实测]` 整包遍历会让 `docs/ONE_PACKAGE_AT_A_TIME.md` 进入 S4_8e 的 `added` 精确列表断言。处理方式（ra2forge/ 子树 scope 收窄，断言文本未动）与理由见 `DISAGREE.md` §D1 与 `V16_CHANGELOG.md` 改动 4。这是本卡唯一对用例文件的编辑。

## U6. 套件运行的机器口径
`[本次实测]` 本次回归在本机（Windows, Python 3.12）以 `python -B -X utf8 regress_dlc_v16.py` 运行；与 v15 卡当时运行环境可能不同（未考证 v15 卡的运行记录），但 96 个继承用例逐字未动、结果全绿，差异仅体现在本卡新增的 W77_1 与日志/摘要文本上。
