# UNCOVERED · W24（seal 写失败回滚实测）未覆盖与不确定项

日期：2026-11-13。按影响排序；每项给「是什么 / 为什么没做 / 建议归哪张卡」。
继承 W23 UNCOVERED 的全部未决项（§1-§4、§6-§8 仍然成立），此处只列本卡新增。

## 1. uninstall 的 seal 删除无容错（新发现，建议独立小卡）

F7 实测：只读 seal 下，uninstall 在**清单已 unlink、全部记录文件已还原/删除
之后**才删 seal，撞上 PermissionError 直接逸出（CLI exit 1，actions 报告丢失），
留下「清单已删 + 游离 seal」状态。该状态可自愈披露（二次 uninstall exit 0 并
显式警示 stray seal），但与 install 侧"seal 写失败 ⇒ 回滚 + 报告"的纪律不对等。
修法很小（seal unlink 包 try/except → 转 warning + 报告），但涉及 uninstall
报告语义（部分完成如何表述），归独立卡，未在本卡顺手改（改生产代码超出本卡
写域授权的精神——本卡只加测试基建）。

## 2. 「清单回滚写自身失败」的二次故障未注入

install.py L1959-1966 的回滚兜底（`_stage_text_and_replace(prev_record_text…)`
或 `unlink()`）外层只有 `except OSError: pass`。若回滚写也失败（比如目录被第三方
锁住），代码会带着原始 seal 异常继续抛——终态是"新清单站着、无 seal"，正是
断言要防的状态。未测：需要第二个注入点（对 "install record restore" 这次
`_stage_text_and_replace` 再注入），本卡把注入预算用在了断言直接要求的三形态
上。风险窗口极窄（要求两次独立写失败），建议与 §1 同卡处理。

## 3. 非 Windows 未复核

只读属性（`os.chmod(S_IREAD)` → `os.replace` WinError 5）与目录占槽的拒绝行为
是 NTFS/Windows 语义。Linux 上等价障碍（`chattr +i`、目录占槽、EACCES 目录）
大概率命中同样分支，但未实测。沿用 W23 UNCOVERED §7。

## 4. 真实磁盘满未模拟

形态 (b) 用 `write()` 层 ENOSPC 模拟（171/343 字节真实落盘后抛错）。真实卷
配额/容量耗尽还牵涉 `os.open` 创建 staging 就失败（被 `@seal_open` 模式覆盖了
"staging 建不出来"这一半）——两种子形态都有 driver 级证据，但没有"真满盘"的
OS 级证据。判据等价性是推定的。

## 5. `@seal_half` 的半写字节数随 seal JSON 长度浮动

消息里的 "landed N/M bytes"（本卡记录 171/343）取决于当次 seal JSON 的字节
长度（时间戳位数等），断言只判 "ENOSPC + landed 字样"，不锁具体数字。属证据
复现时的已知浮动，非缺陷。
