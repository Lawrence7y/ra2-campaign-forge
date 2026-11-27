
**⑦ 门禁升级 R160 → R161（五处联动，一次事务；沙箱预演 + 反控）。** 新节 2.166 实测 **6,152 B**，纳入 C16 逐节下界（下界 = 实测一半 = **3,076**）。四处连带常量全部重钉：
| 常量 | 旧 | 新 |
|---|---|---|
| `GATE_VER` | R160 | **R161** |
| `C16_FLOORS_SHA256` | `125d3913…` | **`016e1f7e…`** |
| `FREEZE_SHA256` | `62d3ddc3…` | **`c9973d32…`** |
| `C7_TEXT_SHA256` | `33efbd52…` | **`bf53e687…`** |
| `C7_ROW_SHA['20']` | `8872186b…` | **`6d26f783…`** |

关键反控：**`C14_TEXT_SHA256` 一字未动**（`a740bcc9…`）。先沙箱预演（三层镜像）得 exit 0 / FAIL 0 / C10 自报 R161 / C16 unpinned 0 / C16d pin OK；再做**负控**：把沙箱 DR 的版本改成 `R999` ⇒ 必须报 `C10 self GATE_VER registered R999 != actual R161`。生产写入后 `gate_runner.py` 实名复验 **G1=ok / G2=ok / G3=ok**，G3a 三处版本全部 `R161`，G3e 由 160 节重算得 `016e1f7e…` 与钉一致；主门禁自报 `160 sections measured (pinned 160), hollow 0, missing 0, unpinned 0, min margin 20`。⇒ **本轮的串联器在它自己的第一次版本升级上就被用上了**：G3a/G3b 两条正好把 R159、R160 各踩过一次的「改版本锚漏改镜像」钉成会 FAIL 的断言。
