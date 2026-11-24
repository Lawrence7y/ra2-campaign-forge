# W177 UNKNOWNS（未证项与待确认）

| # | 未证项 | 引用节号 | 现状/下一步 |
|---|---|---|---|
| U1 | 「重叠 10 格」现象本身 | PROBE_TABLE §使用顺序步4；R14 §2.3 | 未能构造可归因的"放到已占用格"点击；33 次定点 click 的 YAPOWR 差分恒 0。需在可稳定连续放置的场景（无限资金+固定镜头）重试。 |
| U2 | C1/C2 `cell+0xE4/E8` 格链头与展开链长 | PROBE_TABLE C1/C2/R2；R14 §2.2 | 未定位独立 CellClass 对象地址；BuildingClass `+0x30` 全 0，无法区分"链尾"与"偏移非 next"。需先由 `obj` 坐标反查 CellClass*。 |
| U3 | O7(`*[obj+0x520]+0xE58`) / O8(`+0x1571`) 短路门控 | PROBE_TABLE O7/O8 | 因 `+0x520` 实为 BuildingTypeClass（非 MapClass，见 DISAGREE D1），这两个表达式的基址假设不成立，未采样。 |
| U4 | F1–F8（SetOwner / can-place / slot73 失败出口的 EIP 上下文门控） | PROBE_TABLE F1–F8 | 未做 EIP 命中采样（本卡以放置前后只读差分为主）；EIP 分桶框架在 `work\w177_core.py` 已备（Wow64GetThreadContext）。 |
| U5 | ≥10 次连续放置 | 卡正文 §4 | 只达成净增 5 座；资金 UI 恒显 10000（未扣款），但自动化点击未逐次生效，原因未定（建造模式在进入/取消间翻转？坐标无效？）。 |
| U6 | R1/R2 成因判据（标志与链状态失配 / 摘挂链对称性） | PROBE_TABLE R1/R2 | 因 U2 链不可读，R1/R2 未判定。已有 R1 的部分：世界中建筑均 `+0x81=0/+0x74=1`，无失配样本。 |

## 说明
- 以上均为 [未证]，未以静态推断冒充实测。
- 核心可证结论（G0/G1/G2、BuildingClass 定位、O1/O2 语义、O6 否证）见 PROGRESS.md 结论表 1–5。
