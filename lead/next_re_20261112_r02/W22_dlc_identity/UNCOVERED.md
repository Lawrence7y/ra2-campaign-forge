# UNCOVERED · W22（PKG-IDENT01）未覆盖与不确定项

日期：2026-11-13。按影响排序；每项给「是什么 / 为什么没做 / 建议归哪张卡」。

## 1. 身份声明无信任链（伪造面仍在，只是收紧）
`ra2forge_package.json` 与清单里的 `package_id` 都是**本地明文声明**，无签名/哈希链。
伪造者完全可以给自己的包贴上受害包的 id（或给清单贴上任意 id）——本卡把"身份不可判"
升级为"身份可判但可谎报"，防的是**误操作**（同路径先后装两个包分不清、升级误覆盖），
不是**主动伪造**。W21 UNCOVERED §3 的"清单本身的可信工件化"（签名/信任链）仍然全量未做。
**建议**：独立卡"清单信任链"；设计时把 `package_digest` 当作现成的锚点（签名对象都现成了）。

## 2. battle ID 的跨包唯一性没有构建/安装期检查
T4 演示依赖身份门把"异 id 同 battle ID"挡在安装层。但**手工拷贝**（不经 install）仍能让
两个包的 `[RA2F1]` 节同目录共存，引擎按 battle id 合并、后枚举者覆盖前者——文件层无法
阻止。`design.validate` 目前只拒绝官方 id（ALL1/SOV1…），不拒绝"与另一个 ra2forge 包
撞车"。**建议**：归"内容隔离"后续卡（并存放开前必须做）：install 侧已经有
`_scan_environment`，可加"目录里已有他包 BATTLEMD98.INI 且 battle id 相同"的 risk 项；
build 侧可加注册表式检查。

## 3. 安装后无"verify"命令，package_digest 只在装/升那一刻有意义
清单记录了 `package_digest` 与每条 `source_package_digest`，但没有一个子命令拿它对照
**当前**游戏目录做漂移检测（哪些文件被用户改了、整体指纹还是不是记录值）。uninstall 的
逐条 sha 校验覆盖了一部分，但那只在卸载时、且告警就完事。**建议**：下一张卡加
`inspect --game <dir>`（或 `verify`）：清单 × 磁盘逐条比对 + 汇总指纹，把"多代升级判定"
从升级时点扩展到任意时点。

## 4. `build --install` 与新 exit 4 的 UX 缝隙
`build --install <dir>` 仍不带 `--adopt-legacy`：往一个"身份未声明清单"的目录构建直装会
exit 4（这是**正确**的守门），但用户必须退出来手动跑 `install --adopt-legacy`。
**建议**：给 build 子命令补 `--adopt-legacy` 透传（一行改动），或文档明示。

## 5. 非 strict 模式 × 采纳路径的孤儿 `changed` 行为未单测
继承 W21 UNCOVERED §2：`strict=False`（仅程序化可达）下"旧文件 sha 不匹配"保留文件+bak
并告警的分支，叠加 `--adopt-legacy` 的组合没有执行证据。本卡所有用例都在默认 strict 下跑。
**建议**：接入正式测试集时补（临时目录 + 手改字节 + strict=False + adopt）。

## 6. 回滚对既有 `keep` 槽的语义限制（继承 W21 §4，未动）
升级失败回滚把既有 bak（真原版）写回后，旧记录的 sha 不再匹配 → 后续 uninstall 告警保留。
状态可解释、非静默损坏；本卡的 `supersedes`/`source_package_digest` 已为"多代 sha"记账
铺了数据，但回滚算法本身没改。**建议**：随"安装事务"深化一并处理。

## 7. 引擎侧行为仍未验证（边界，非本卡职责）
文件层事实（sha/快照）之外，升级/并存拒绝对游戏内战役菜单的实际表现未在真机趟——
归 RE-N10 第 7 项。

## 8. 平台面：仅 Windows/NTFS 实测
`os.replace` 语义、尾点尾空格目录项归一、链接类拒绝等 W21 已测的 Windows 事实仍只在
Windows 上成立；身份判定本身是纯文本比较（跨平台风险低），但整包未在 Linux 复跑。

## 9. 环境观察（与本卡无关但需备案）
会话期间观察到 `ra2youli/` 有 4 个文件 mtime 为 2026-11-13 06:29:19（`ddraw.ini`、
`except.txt`、`RA2MD.INI`、`RA2MD.INI.benchbak`——cnc-ddraw/基准类工具产物），**早于**
本卡首次工具调用（07:05+），非本卡所为；`ra2forge_install.json` mtime 仍为 2026-10-22
（sha256 `fe3bdf62…`），本卡对 `ra2youli/` 的唯一操作是**只读复制该清单**。

## 10. 性能
身份判定是 O(1) 次小文件读 + O(n) 字符串比较；`package_digest` 从计划步骤的 sha 复用，
无额外读盘。真实规模（数十图、几 MB/图）不构成瓶颈，未做基准。
