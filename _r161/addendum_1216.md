
### 八 · 门禁升级 R160 → R161（五处联动）
2.166 实测 **6,152 B** ⇒ C16 下界 **3,076**；重钉五处：`GATE_VER`→R161、`C16_FLOORS_SHA256` `125d3913…`→`016e1f7e…`、`FREEZE_SHA256` `62d3ddc3…`→`c9973d32…`、`C7_TEXT_SHA256` `33efbd52…`→`bf53e687…`、`C7_ROW_SHA['20']` `8872186b…`→`6d26f783…`。反控 **`C14_TEXT_SHA256` 一字未动**。
沙箱预演 exit 0 / FAIL 0 / C16 unpinned 0；负控改 DR 版本为 R999 ⇒ 报 `C10 registered R999 != actual R161`。生产写入后 `gate_runner` 复验 **G1/G2/G3 全 ok**，G3a 三处版本均 R161，主门禁自报 `160 sections (pinned 160), hollow 0, missing 0, unpinned 0, min margin 20`。⇒ R159、R160 各踩过一次的「改版本锚漏改镜像」自此成为**会 FAIL 的断言**（G3a/G3b）。
