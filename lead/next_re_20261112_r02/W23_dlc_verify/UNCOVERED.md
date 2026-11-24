# UNCOVERED · W23（SEAL-CHAIN01）未覆盖与不确定项

日期：2026-11-13。按影响排序；每项给「是什么 / 为什么没做 / 建议归哪张卡」。

## 1. seal 的对抗性上限（本卡边界，重申）
seal 绑定的是「清单自 install 以来未被改过」这一件事，且**无密钥**：能改清单的攻击者能
重算 seal（`manifest_sha256` 的算法在 `--help`/文档里是公开的）。因此 W21 §3 的完整威胁
（蓄意伪造清单骗过 uninstall）**只在**「攻击者不重算 seal」的前提下被缓解。任何把本卡
表述成「防篡改/安全可信」的引用都是错的。若要真正的抗恶意，需要签名体系（外部密钥或
TPM），属独立卡。

## 2. install 不做 seal 门禁（范围决策，非遗漏）
任务书把 seal 校验点定为 uninstall/verify。install 会**替换**信任锚（重写清单 + 新
seal），因此对既有记录的 seal 异常只做 notice 披露、不做门禁。残余面：seal 异常的记录
在升级时被静默（但可见地）消费，孤儿清理靠 per-file sha 判据兜底。若要把 install 也
纳入门禁，需要定义「合法覆盖既有记录」的显式旗标，属独立决策——未做。

## 3. 清单整体伪造 + digest 一致伪造 = verify 全绿
若攻击者/误操作者把清单**连同 `package_digest`、seal 一起重算**（即完整伪造一遍本工具
的输出），`verify` 的 1/2/5 项全绿，只有第 3 项（磁盘对账）可能暴露——而且如果磁盘上
的文件也与其记录一致（例如把别人的文件记录成自己的、sha 填对了），verify 无法区分
「谁装的」。这与 W21 §3 的原始结论一致：文件层没有出处证明，只有内容对账。文档已写明
「digest 检查 ≠ 磁盘证明」（VERIFY.md §6.2），无行动项，除非上签名体系。

## 4. seal 世代判定基于 `version` 字段（字符串自报）
`_manifest_is_seal_era` 信任清单里自报的 tool version。手写清单把 version 填成 0.3 可
以**绕开 seal 门禁**（走降级路径）——这再次落在「防误操作 ≠ 抗恶意」边界内：伪造者
本来就能重算 seal，改个 version 字段是同一工作量。**副作用**：seal 世代清单若把
version 改小，将失去门禁但 verify 会按旧清单警告（不会静默全绿）。归同一张「签名体系」
卡。

## 5. seal 写失败回滚的极窄窗口未做真机故障注入
install 的 seal 写失败回滚（清单恢复到上一版字节）有代码路径与注释，但 W22 的
v5_fail_driver 只注入 `_copy_verified` 与 `_stage_text_and_replace` 两类故障——
`@record` 注入在**清单写**处 raise，天然到不了 seal 写；「清单写成功、seal 写失败」
的形态没有执行证据（只有代码审读）。可通过给 driver 加 `@seal` 注入点补测，属测试
基建增强。

## 6. `verify` 在巨型目录/深展开 MIX 上的性能
孤儿扫描是 `game.iterdir()` 一次遍历 + 每个被记录文件一次 sha256 读盘，与 W21 的结论
相同（对真实包成本可忽略）；但未做数千文件目录的基准。非本卡目标。

## 7. 非 Windows 平台未复核
全部实验在 Windows（NTFS）。seal 的规范化哈希（CRLF→LF）在 Linux 上行为一致（代码对
`\r`/`\n` 显式处理），但 `os.linesep` 相关的 staged 写、别名/链接类判据未在 Linux 复测。
沿 W21 UNCOVERED §7 的提醒，仍然成立。

## 8. `*.ra2forge-stage*` 孤儿的告警粒度
staging 残留（带随机后缀的 `.ra2forge-stage.<hex>`）被列入孤儿（informational）。正常
流程不会留下它们（install 失败时 staging 文件被清理）；若真出现，多半是旧版本工具的
遗留。未为它做专门的「清理」命令——孤儿只列出、不动手，与「verify 只读」的定位一致。
