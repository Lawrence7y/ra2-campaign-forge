
---

### §317（2026-10-21 12:1x）① HouseClass 四计数器定谳 + `units0` 归因推翻

**§316 遗留的最高优先项已闭环**：`c5574`/`c5588`/`c559C`/`c5560` 语义**定谳**，并**推翻 §316 的「步兵实例化率 37.8%」归因**。

**定谳**：四字段是 `CounterClass::Total`（`VectorClass` 0x10 + `int Total` @+0x10 ⇒ sizeof 0x14）。
`YRpp/HouseClass.h:879-903` 的 12 个 `CounterClass` 块起点 = `0x55F0−12×0x14` = **0x5500**；四个探针偏移步长**恰 0x14**，全落组 2（「currently owned and on the map」）的 `Total` 槽：
`c5560`=建筑、`c5574`=**车辆**、`c5588`=**步兵**、`c559C`=飞行器（均为「当前在图」）。

**四方对账 8/8 全过**（时钟基准 `frame_edges[0][1]+t_rel`）：四屋 `Σc5574≈units`、`Σc5588≈infantry`、`Σc5560≈b`，残差全 |Δ|≤2；`Σc559C=0`=`aircraft=0` ✓。**四路互证，非命名猜测。**

**★★ 推翻**：`units0` 在 `qc151_trip.py` 取自 **settle 阶段 `s_counters` 第一条**，此时帧号已是 **3849**（约 128 秒）——**不是 t=0 预置数**。最早的快照帧 **3724** 与 3900 几乎无差 ⇒ 损失在帧 0–3724 内已发生完毕。逐槽位：h0 `<human player>` 175 车/**8 兵（5.0%）**、h1 `Computer` 91/23（37.9%/14.4%）、h2 `Neutral` 225/104（93.8%/65.0%）、h3 `Special` 240/107（**100.0%**/66.9%）。**分布极不均匀**，且 **h2 的 c5588 从 3724 到 6000 恒 104、h3 恒 107（零变化）** ⇒ 缺失是**帧 0–3724 的一次性事件**，非持续战损。

**已排除五条**：预置不对称（四槽位完全对称，各 240 车 MTNK/HTNK/TTNK 80 各 + 160 兵 E1/GI/FLAKT）、格子冲突（5600 实体占 5600 不同格，零碰撞）、地形（`[IsoMapPack5]` 仅 18 B、`[OverlayPack]` 44 B ⇒ 纯平坦空图）、建筑击杀（地图无 `[Structures]`，`b` 仅 6→8）、持续战损（h2/h3 零变化）。

**地图结构**：14 owner 沿对角线 14 条带，每带 400 实体，**彼此紧邻**（`<human player>` x[91..139] 与 `Alliance` x[139..188] 在 x=139 相接）；`MaxPlayer=2` 但实际 4 个 HouseClass（h0/h1/h2/h3 = `<human player>`/`Computer`/`Neutral`/`Special`）；**其余 10 owner 的 4000 实体无对应 HouseClass，去向未定谳**。

**★ 新增仪器缺陷**：`latch_frames` 被配成 `[3900..6000]` 而 `anchor_default` 是 `[300,600,1800]` ⇒ 早期快照全靠 QC213P2 `early`（帧 3724）兜底，**仍太晚**。下一趟必须拉回 300/600/1800。

**下一档修正**：①修 latch 取帧 0–3724 损失曲线（真正原因）；②若损失不可免则提高 `<human player>` 预置（`_src_variant_800x600_csf` 即 360 车+240 兵版本）；③拉开槽位/改 Mission（**需 Lead 裁决**）；④仍不足跳 L3。**⇒ 不是改图，是修 latch。**

取证件 `goal1_h1decay_20261021/HOUSE_COUNTERS_DECODED.md`（11,515 B / sha16 `352f23b14d89ccbb`）；台账 §317。独立核验 GLM 5.3 `dwfrun-9fb1ccc3` 在飞。**三目标勾选无变化。**
