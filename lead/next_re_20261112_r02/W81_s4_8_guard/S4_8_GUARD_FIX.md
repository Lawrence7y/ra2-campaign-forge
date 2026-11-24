# W81 · S4_8 守护恢复：全包 delta 扫描 + `docs/` 显式白名单

> 记录人：W81（GLM-5.3-Flash）｜2026-11-14｜纯离线（I launched 0 / attached 0）
> 基座：`W77_exit33_message_v16\` 的 v16 回归套件与夹具（只读复制，W77 本体零改动）

## 1 · 改了什么（文件:行）

本卡只改**回归脚本**，不改任何产品代码（`ra2forge_patched_v16b\` 是 W77 `ra2forge_patched_v16\` 的逐字节副本，robocopy 排除 `__pycache__`/`*.pyc`，26 文件：ra2forge 25 + docs 1；v14ref 夹具 23 文件，SHA 与 W77 侧一致 `[本次实测·复制后清点]`）。

| 位置 | 改动 |
|---|---|
| `s4_cases.py:846-847` | v14ref 侧收集器恢复**全包**：`(v14ref / "ra2forge").rglob("*")` → `v14ref.rglob("*")`（撤销 W77 收窄） |
| `s4_cases.py:849-850` | V14_ROOT 侧收集器同样恢复全包：`(G.V14_ROOT / "ra2forge").rglob("*")` → `G.V14_ROOT.rglob("*")` |
| `s4_cases.py:863-868` | `expected_added` **显式加** `"docs/ONE_PACKAGE_AT_A_TIME.md"`（白名单按 `sorted()` 字典序排列：docs 在前），并加注释说明顺序敏感 |
| `s4_cases.py:832-844` | 注释块改写：说明 W81 恢复全包的理由与守护语义（W77 的收窄注释移除） |
| `regress_dlc_v16.py:63` | `W43_ROOT_NAME = "W81_s4_8_guard"` |
| `regress_dlc_v16.py:73` | `V12_ROOT = W43_ROOT / "ra2forge_patched_v16b"` |
| `regress_dlc_v16.py:25-36`（头部） | 加 W81 re-point 说明段 |

**逐字未动**（任务红线）：S4_8 三条 check（`S4_8e` 869-872 / `S4_8f` 874-878 / `S4_8g` 880-884）的断言文本与判定逻辑，`expected_changed`，`untouched` 列表，以及其余 96 个用例全部照抄 W77。`[本次读码·diff 自查]`

## 2 · 为什么"恢复全包 + 显式白名单"比"收窄"正确

- W77 收窄后，S4_8 不再守护**包根下不得出现任意新文件**——LEAD_VERIFY_W77.md §3 明记此缺口。守护的范围应该由**期望集合**决定，而不是由**扫描范围**决定：收窄是把眼睛蒙上，白名单是把例外写明。
- 恢复全包后，`added == expected_added`（顺序敏感、精确相等）成为对**整个包根**的封闭性断言：任何多出来的文件（ wherever it lands ）都会进 `added` 并打红 S4_8e。`docs/ONE_PACKAGE_AT_A_TIME.md` 作为 Lead 签发的合法包内容被**承认**进白名单，而不是被排除在视野外。
- 三条 check 的守护意图（source delta CLOSED / 无其他守卫被削弱 / 无 `__pycache__`）在全包扫描下只会**更严**，不会更松。

## 3 · 回归结果 `[本次实测]`

命令行：
```
cd D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W81_s4_8_guard
python -B -X utf8 regress_dlc_v16.py        *> out\regress_full_stdout.txt
```
`out\SUMMARY.txt` 关键行：
```
cases: 97  passed: 97  failed: 0
assertions: 844 passed / 0 failed
exit: 0
inherited v13 cases: 89
S4 cases: 8
W60 S5 cases: 6
W77 EXIT-33 message cases: 1
```
- 退出码 **0**；`regress_full_stdout.txt` 中 **Traceback 计数 = 0**。
- 用例数/通过数/断言数与 W77 基线（97/97/844）**完全一致**——本卡未加新 check，未改产品代码，断言面零变化。
- S4_8 单例：`PASS  S4_8  checks: 7 passed / 0 failed`（a-g 全绿）。

## 4 · 反向验证 `[本次实测]`（守护有效的实证）

在**本卡沙箱副本** `ra2forge_patched_v16b\` 包根投放假文件 `STRAY.txt`：

```
python -B -X utf8 regress_dlc_v16.py S4_8     → EXIT=1（FAIL）
```
`out\REVERSE_STRAY_S4_8_FAIL.log` 关键行：
```
[assert] S4_8e (W60): v14->v15 source delta is CLOSED (3 changed + 2 added) ... FAIL
          changed=[...3 项...] added=['STRAY.txt', 'docs/ONE_PACKAGE_AT_A_TIME.md',
          'ra2forge/battlemd_inplace.py', 'ra2forge/data/BATTLEMD.OFFICIAL.INI'] removed=[]
```
守护**精确点名** stray 文件并 FAIL。移走后重跑：
```
python -B -X utf8 regress_dlc_v16.py S4_8     → EXIT=0（PASS，7/7）
```
日志：`out\REVERSE_STRAY_S4_8_FAIL.log`、`out\REVERSE_STRAY_stdout.txt`、`out\REVERSE_STRAY_REMOVED_S4_8_PASS.log`、`out\REVERSE_STRAY_REMOVED_stdout.txt`。

## 5 · 有没有连带打红别的用例

**没有。** 全量 97/97 一次通过，无任何用例因恢复全包扫描而变红。`[静态推断·已实测证实]` 原因：v14ref 包根只含 `ra2forge/`（23 文件），v16b 包根 = `ra2forge/`（25）+ `docs/`（1），全包 delta 恰为 `expected_changed`(3) + `expected_added`(3) + removed(空)，没有其他非源码文件需要额外白名单。

## 6 · 结论口径

`[可以写]` S4_8 已恢复全包扫描且 `docs/ONE_PACKAGE_AT_A_TIME.md` 显式列入 `expected_added`；97/97 全绿（844 断言、退出码 0）；反向验证（投 stray 文件 → S4_8 FAIL，移走 → PASS）成立。
`[可以写]` v16 产品代码零改动（`ra2forge_patched_v16b` 为 W77 v16 逐字节副本）。
`[不得写]` "v16 产品代码有改动"。
