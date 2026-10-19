# B 类 92 条真机待测 · 可执行索引（R-B-INDEX）

> 任务号：R-B-INDEX · 产出：本文件 + `out/re_work/re_sprint/R_b_index/**`
> **源（只读，本任务未改）**：`docs/re/open_items_sweep.md` §3（样本 B-01~B-12）· `docs/re/offline_verification_alternatives.md` §6（全量 92 行矩阵，权威 ID）
> **纪律**：不伪造「实测」；真机挂起期本索引只提供**解冻后即插即用**步骤。可写域：`out/re_work/re_sprint/R_b_index/**`、本文件。禁写台账/看板/ra2render/gamemd。
> 机器可读全表：`out/re_work/re_sprint/R_b_index/b92_catalog.tsv` · 分桶摘要：`buckets_top10.md`

---

## 0. 怎么用本索引

1. **ID 以 §6 矩阵为准**（`B-R/A/N/L/M` 五族 92 条）；`open_items_sweep` 的 `B-01~B-12` 是样本别名，对照见 §1。
2. 每条给出：**测什么 / 最小步骤 / 判据 / 预计窗口 / 依赖**。执行时先看「桶」：
   - **STATIC** → 跑 S18 离线脚本即可关账（真机仅可选烟雾，不得标实测）；
   - **MERGE** → 并入既有真机卡/套件，不新开卡；
   - **SOLO** → 必须新开独立卡（环境专属）。
3. **依赖标记**：`ZC-1` / `ZC-RE1` / `ZC-11` / `ZC-GAP-P21|P223` / `EXCEPT-AB` / `DUAL-LAN` / `DEBUGGER` / `WASAPI` / `4K` / `LONGHAUL` / `NETCOND` / `RELOAD5` / `ALTTAB` / `S18 scripts`。

---

## 1. ID 对照（sweep 样本 ↔ §6 全量）

| open_items B- | 补丁/规格 | 矩阵 ID | 备注 |
|---|---|---|---|
| B-01 | M-8 Net Fix | **B-N03**, B-N10 | 帧 CRC 锁步对拍 |
| B-02 | M-8 Net Fix | **B-N11** | 混联 L0 |
| B-03 | M-8 Net Fix | **B-N06** | H-D2 EAX 快照 |
| B-04 | M-10 Gap/SpySat | **B-L10** | 裂缝恢复黑雾 |
| B-05 | M-10 Gap/SpySat | **B-L09** | SpySat 不全图开 |
| B-06 | M-10 Gap/SpySat | **B-L11** | TYPE 跨战局还原 |
| B-07 | M-9 Particle | **B-L13**（兼 B-R20/B-R21） | 敌方尾烟剔除/己方零误杀 |
| B-08 | M-9 Particle | **B-L12**（兼 B-R16） | 微粒无永生 |
| B-09 | CRT 池化 | **B-M01**, B-M07, B-M10 | 堆竞争/长跑 |
| B-10 | 音频限频 | **B-A05**（兼 B-A04） | 听感/爆音 |
| B-11 | L4 视口 | **B-R03** | 350 格保底 |
| B-12 | 联机自动降级 | **B-N12**, **B-N13** | W1–W6 |

---

## 2. 三桶总览

| 桶 | 条数 | ID 清单 |
|---|---:|---|
| **STATIC 可静态关闭** | 24 | B-R04/05/07/09/12/14/19/20/22/28 · B-A06/07 · B-N02/04/05/08/09/16 · B-L03/16 · B-M04/05/06/08 |
| **MERGE 可并入现有卡** | 50 | 渲染 16 + 音频 9 + 联机 6 + 逻辑 12 + 内存 7（见 `buckets_top10.md` §2.2） |
| **SOLO 需独立卡** | 18 | B-R10/13/17/18/31/32 · B-A03/04/11 · B-N01/06/07/14/15/18 · B-L04/11 · B-M11 |

**STATIC 关闭语义**：S18 三脚本（`verify_all_92_sites.py` / `check_trampoline_rel32.py` / `binary_rollback_oracle.py`）复算通过后，将 `[待实测]` 降为「离线闭环·真机可选烟雾」。**不得**写「已实测」。

---

## 3. 优先级 Top10（发布/闸门）

| # | ID | 测什么 | 最小步骤 | 判据 | 窗口 | 依赖 |
|---|---|---|---|---|---|---|
| 1 | **B-N11** | 混联 L0 强判据 | A 开诊断镜像、B 原版；对局≥300 帧 | 零 `SYNC*.TXT`、不弹 OOS | 70m | 套件一 · DUAL-LAN · B-02 |
| 2 | **B-N03** | 逐帧 CRC 锁步 | 双端同种子≥500 帧 + compare_sync_mirrors | MATCH 100% (500/500) | 60m | 套件一 · ZC-1 Q6 · B-01 |
| 3 | **B-N12** | 降级状态机 | 进联机房读门控行 | ONLINE→W1–W6 自动降级 | 40m | ZC-1 Q2 · DUAL-LAN · B-12 |
| 4 | **B-N13** | W1–W6 旁路 | 联机局观察索敌频率 | 回归原版逐帧，不分叉 | 40m | 套件一 · ZC-1 Q2 · B-12 |
| 5 | **B-L09** | SpySat 不全图开 | 建造间谍卫星并通电 | 小地图不整亮；`House+0x577A` 不置 1 | 20m | ZC-1 Q3 · 套件五 · B-05 |
| 6 | **B-L10** | 裂缝黑雾恢复 | 裂缝区 PsychicReveal 后观察 | 扫描退去 100% 全黑；`Cell+0x134≥1` | 25m | 套件五 · ZC-GAP-P21 · B-04 |
| 7 | **B-L13** | 己方/盟友零误杀 | 黑雾边缘己方开火 | 尾烟 100% 可见（兼 B-L12 无永生） | 25m | ZC-1 Q3③ · 套件五 · B-07 |
| 8 | **B-M07** | CRT CAS 并发 | 多线程高压挂机 30–60 min | 零互锁挂死；`except.txt` 0 字节 | 70m | 套件四 · ZC-11/EXCEPT-AB |
| 9 | **B-R03** | L4 350 格保底 | SpySat/心灵探测/快速卷屏 | `fullRedrawTriggered==1`；零残影黑块 | 20m | 套件二 · L4 落地包 · B-11 |
| 10 | **B-L11** | TYPE 跨战局还原 | 同进程进出战局×5 | 备份表=首次原值，无 600/16.0 污染 | 35m | RELOAD5 独立卡 · B-06 |

---

## 4. 可执行索引（92 条）

> 列说明：**步骤**=最小可执行动作；**判据**=通过线；**窗**=预计分钟；**桶**=STATIC/MERGE/SOLO。
> 表格压缩书写；完整五字段机器表见 `b92_catalog.tsv`。

### 4.1 渲染与微内核 B-R01 ~ B-R32

| ID | 测什么 | 最小步骤 | 判据 | 窗 | 依赖 | 桶 |
|---|---|---|---|---|---|---|
| B-R01 | DDraw Lock 争用 | 套件二遥测采样 | `ddrawLockCountPerFrame≤2`，无撕裂 | 15 | 套件二 · ZC-1 | MERGE |
| B-R02 | 脏矩形阈值回退 | 大范围翻转+卷屏 | `tacticalFullRedrawFrames` 超阈值递增 | 15 | 套件二 | MERGE |
| B-R03 | L4 350 格保底 | 剧烈迷雾翻转 | `fullRedrawTriggered==1`，零黑块残影 | 20 | 套件二 · L4 · **B-11** | MERGE |
| B-R04 | 3x3 菱形外扩 | 外扩包络复算 | 几何包络 100%，边缘无切割 | 0 | S18 math | **STATIC** |
| B-R05 | RLE 虚表分发 | 虚表槽复算 | 无未定义槽；无非法指令 | 0 | S18 scripts | **STATIC** |
| B-R06 | zmap 越界读 | 右边界压测 | 0 崩溃，无越界读 | 20 | 套件二 | MERGE |
| B-R07 | Blitter 工厂布局 | 尺寸表复算 | 4/8/12/16 自洽，零泄漏 | 0 | S18 scripts | **STATIC** |
| B-R08 | SSE2 565 等价 | `--ab-simd` A/B | 画面一致；Blit 降≥50% | 30 | ZC-1 harness | MERGE |
| B-R09 | Pitch stride | Pitch 使用点复算 | 2560x1440 无撕裂越界 | 0 | S18 scripts | **STATIC** |
| B-R10 | SURFACELOST | Alt-Tab×20 | 20 次不崩，画面即恢复 | 25 | ALTTABx20 | **SOLO** |
| B-R11 | VSync 帧时抖动 | bench_metrics | 抖动 std<1.5ms，无撕裂 | 20 | ZC-1 harness | MERGE |
| B-R12 | VXL 切片排序 | 深度单调性证明 | 无反向遮挡/穿模 | 0 | S18 math | **STATIC** |
| B-R13 | VXL 缓存命中率 | 大部队调头遥测 | 命中率>88% | 25 | VXL 遥测 | **SOLO** |
| B-R14 | VXL 法线定点 | 误差复算 | 无黑斑，渐变平滑 | 0 | S18 math | **STATIC** |
| B-R15 | Anim 跳过绘制 | 隐形单位移动 | 无像素泄露，倒计时正常 | 15 | ZC-1 · 套件五 | MERGE |
| B-R16 | 特效/生命周期解耦 | 屏外爆炸销毁 | 100% 正常销毁 | 15 | 套件二 | MERGE |
| B-R17 | 激光裁剪 | 10 光棱集火 | 无截断错位，帧率稳 | 25 | 专用场景 | **SOLO** |
| B-R18 | 电弧寿命 | 击中后逐帧计数 | 12 帧内消散 | 25 | 帧计数 | **SOLO** |
| B-R19 | 粒子槽 69 ABI | ret 8 契约复算 | ESP 零偏移 | 0 | S18 scripts | **STATIC** |
| B-R20 | 微粒槽 69 ABI | ret 8 + V3 尾烟 | 黑雾不渲染，栈平衡 | 0 | S18 scripts | **STATIC** |
| B-R21 | 微粒黑雾裁剪 | 穿雾分界观察 | 边界平滑无闪烁 | 15 | ZC-1 Q3③ · 套件五 | MERGE |
| B-R22 | 565 环境光饱和 | 钳位证明 | 核爆无紫绿噪点 | 0 | S18 math | **STATIC** |
| B-R23 | 雷达点绘吞吐 | 单位>1500 | 雷达绘制<0.1ms | 20 | bench · 雷达 | MERGE |
| B-R24 | Cameo 脏门控 | 建造进度观察 | 进度平滑，无多余全刷 | 15 | ZC-1 任意局 | MERGE |
| B-R25 | 地基 22 槽重置 | 进出战局×5 | 向量尺寸稳定 | 25 | RELOAD5 · 套件五 | MERGE |
| B-R26 | 雷达标志过滤 | 平民 1000+ | 无关点零上屏 | 15 | 套件二 | MERGE |
| B-R27 | CanBuild 频次 | 断电/恢复 | 实时变黑/点亮 | 10 | ZC-1 任意局 | MERGE |
| B-R28 | 坐标边界钳位 | 边缘疯狂点击 | 无崩溃，框选不反向 | 10 | ZC-1 烟雾 | **STATIC** |
| B-R29 | 光标残影 | 日常移动 | 无拖尾黑框 | 10 | 日常操作 | MERGE |
| B-R30 | 建筑迷雾残影 | 打爆再探雾 | 残影瞬时消失 | 15 | 套件五 | MERGE |
| B-R31 | 4K 带宽/过度绘制 | 4K 激烈交火 | 稳定 60fps | 40 | 4K 显示器 | **SOLO** |
| B-R32 | 离屏表面重分配 | 拖拽缩放多轮 | 无泄漏无崩溃 | 25 | 窗口缩放协议 | **SOLO** |

### 4.2 音频 B-A01 ~ B-A14

| ID | 测什么 | 最小步骤 | 判据 | 窗 | 依赖 | 桶 |
|---|---|---|---|---|---|---|
| B-A01 | 300 槽通道池 | 套件三采样 | 活跃 10~50，极端≤280 | 20 | 套件三 | MERGE |
| B-A02 | 满载静音降级 | 压满 300 槽 | 零卡顿，无闪退 | 20 | 套件三 | MERGE |
| B-A03 | DS 环形缓冲 | BGM 2 小时 | 无喀哒/断流 | 130 | LONGHAUL-AUDIO | **SOLO** |
| B-A04 | DAC 阶跃爆音 | WASAPI 示波 | 一阶导<15% 满幅 | 35 | WASAPI/SCOPE | **SOLO** |
| B-A05 | 限频听感 | 齐射核爆盲测 | 无噼啪，警报无吞音 | 25 | 套件三 · **B-10** | MERGE |
| B-A06 | PlayGlobal ABI | ret 8 复算 | ESP 水平 | 0 | S18 scripts | **STATIC** |
| B-A07 | PlayAt ABI | ret 4 复算 | 栈深度恒定 | 0 | S18 scripts | **STATIC** |
| B-A08 | EVA 流隔离 | 满载播 EVA | EVA 100% 播报 | 20 | 套件三 | MERGE |
| B-A09 | EVA 优先级 | 警报打断 | 平滑插队无杂音 | 20 | 套件三 | MERGE |
| B-A10 | BGM mB 混音 | 拖音量滑块 | 平滑线性 | 10 | ZC-1 任意局 | MERGE |
| B-A11 | 多声卡重采样 | 48k/192k 试听 | 音调准确 | 30 | MULTI-DEVICE | **SOLO** |
| B-A12 | 3D 衰减/距离 | 左右侧爆炸 | 左爆左响 | 15 | 套件三 | MERGE |
| B-A13 | 警报防吞音 | 100 坦克+铁幕就绪 | 警笛 100% 播报 | 25 | 套件三 | MERGE |
| B-A14 | 失焦静音 | Alt-Tab 切换 | 切出即停，切回无缝 | 10 | ZC-1 · ALTTAB | MERGE |

### 4.3 联机网络 B-N01 ~ B-N18

| ID | 测什么 | 最小步骤 | 判据 | 窗 | 依赖 | 桶 |
|---|---|---|---|---|---|---|
| B-N01 | 锁步平滑累加器 | 延迟抖动观察 | 平稳微调，无暴走 | 30 | 套件一 · NETCOND | **SOLO** |
| B-N02 | GameSpeed 映射 | 公式复算 | 速度 6=60fps，3=30fps | 0 | S18 math | **STATIC** |
| B-N03 | 逐帧 CRC 500 | 双端对拍+比对 | MATCH 100% (500/500) | 60 | 套件一 · ZC-1 Q6 · **B-01** | MERGE |
| B-N04 | CRC 环取模 | `&0xFF` 复算 | 长跑无越界 | 0 | S18 scripts | **STATIC** |
| B-N05 | H-D1 EFLAGS | pushfd/test 复算 | ZF 不误判 | 0 | S18 scripts | **STATIC** |
| B-N06 | H-D2 EAX 快照 | 断点 0x64CC61 | 低字节==slot*37 | 45 | DEBUGGER · **B-03** | **SOLO** |
| B-N07 | 落盘防卡顿 | 只读目录触发 | 平稳弹 OOS，不卡死 | 30 | 只读介质 | **SOLO** |
| B-N08 | H-D5 0F B6 C0 | 机器码比对 | 写指针环内回绕 | 0 | S18 · rollback | **STATIC** |
| B-N09 | H-D6 call 重放 | 等效复算 | 命令 100% 消费 | 0 | S18 scripts | **STATIC** |
| B-N10 | 双端镜像一致 | 导出比对 SHA256 | 两文件哈希相同 | 60 | 套件一 · DUAL-LAN | MERGE |
| B-N11 | 混联 L0 | A 开 B 原版≥300 帧 | 零 SYNC*.TXT | 70 | 套件一 · DUAL-LAN · **B-02** | MERGE |
| B-N12 | 降级状态机 | 进房读门控 | W1–W6 自动降级 | 40 | ZC-1 Q2 · **B-12** | MERGE |
| B-N13 | W1–W6 旁路 | 索敌频率观察 | 回归原版逐帧 | 40 | 套件一 · **B-12** | MERGE |
| B-N14 | 弱网丢包溢出 | 20% 丢包 | 提示等待，不崩 | 40 | NETCOND | **SOLO** |
| B-N15 | 乱序包重排 | 乱序注入对拍 | 回放与主机一致 | 40 | NETCOND | **SOLO** |
| B-N16 | PRNG 零污染 | 调用点扫描 | 双端消费次数相等 | 0 | S18 scripts | **STATIC** |
| B-N17 | 存档 Checksum | 打/不打补丁存读 | 核心块哈希一致 | 25 | ZC-1 可加 | MERGE |
| B-N18 | 断线重连/录像 | 完整重放 | 终局结果 100% 吻合 | 60 | RECONNECT | **SOLO** |

### 4.4 游戏逻辑 / AI B-L01 ~ B-L16

| ID | 测什么 | 最小步骤 | 判据 | 窗 | 依赖 | 桶 |
|---|---|---|---|---|---|---|
| B-L01 | Cell+0x100 链表 | 狭路穿插 | 双向对称，0 野指针 | 20 | 套件五 | MERGE |
| B-L02 | v[73] 多格占用 | 基地车展开 | 3x3 全阻挡 | 15 | 套件五 | MERGE |
| B-L03 | A* 无 PRNG | 寻路扫描 | 跨机拐点序列一致 | 0 | S18 scripts | **STATIC** |
| B-L04 | 隘口绕行死锁 | 桥梁对进 | 一方避让，无假死 | 25 | 专用场景 | **SOLO** |
| B-L05 | 寻敌威胁等价 | 塔+天启 | 稳定打高威胁 | 15 | 套件五 · ZC-1 | MERGE |
| B-L06 | 空间哈希边界 | 基洛夫贴边 | 检索正常不崩 | 15 | 烟雾 | MERGE |
| B-L07 | AITrigger 调权 | 拍核弹井 | 双机同时触发 | 30 | 套件一 · DUAL-LAN | MERGE |
| B-L08 | SuperArray 确定性 | 双超武并行 | 秒数严格同步 | 25 | 套件一 | MERGE |
| B-L09 | SpySat 门控 | 建造通电 | 不整图全亮 | 20 | ZC-1 Q3 · 套件五 · **B-05** | MERGE |
| B-L10 | 裂缝黑雾恢复 | Reveal 后观察 | 100% 全黑恢复 | 25 | 套件五 · ZC-GAP · **B-04** | MERGE |
| B-L11 | TYPE 跨战局还原 | 进出×5 | 无 600/16.0 污染 | 35 | RELOAD5 · **B-06** | **SOLO** |
| B-L12 | 微粒无永生 | 交火采粒子数 | 稳定 50~200 无堆积 | 25 | 套件五 · **B-08** | MERGE |
| B-L13 | 己方零误杀 | 黑雾边缘开火 | 尾烟 100% 可见 | 20 | ZC-1 Q3③ · **B-07** | MERGE |
| B-L14 | 超武 Timer 落盘 | 剩 10s 存读档 | 精准续倒计时 | 20 | ZC-1 可加 | MERGE |
| B-L15 | 变卖地基释放 | 变卖建筑 | 可立刻驶入 | 15 | 套件五 | MERGE |
| B-L16 | InvalidCell 单例 | 点黑边外 | 原地不动，不越界 | 10 | 烟雾 | **STATIC** |

### 4.5 内存 / CRT B-M01 ~ B-M12

| ID | 测什么 | 最小步骤 | 判据 | 窗 | 依赖 | 桶 |
|---|---|---|---|---|---|---|
| B-M01 | 堆争用 | 长跑帧率方差 | 方差降 40% | 70 | 套件四 · LONGHAUL | MERGE |
| B-M02 | new 池化 | 命中率遥测 | ≥95% 入池 | 70 | 套件四 | MERGE |
| B-M03 | delete 分流 | 频繁析构 | 两域各自平衡 | 70 | 套件四 | MERGE |
| B-M04 | 8 字节对齐 | 对齐模数证明 | 零非对齐异常 | 0 | S18 math | **STATIC** |
| B-M05 | Double Free 投毒 | 投毒算法证明 | 自愈不卡死 | 0 | S18 scripts | **STATIC** |
| B-M06 | 地址范围双守卫 | 边界守卫复算 | 跨域零误释放 | 0 | S18 scripts | **STATIC** |
| B-M07 | CAS 并发 | 高压挂机 30–60m | 零互锁，except=0 | 70 | 套件四 · EXCEPT-AB | MERGE |
| B-M08 | 启动期单次锁定 | 静态切断证明 | 热改配置不堆损坏 | 0 | S18 scripts | **STATIC** |
| B-M09 | 池耗尽回退 | 极端微粒海 | 自动穿堆不闪退 | 70 | 套件四 | MERGE |
| B-M10 | 长跑工作集斜率 | 1h Private Bytes | 220~280MB 无线性泄漏 | 70 | 套件四 · LONGHAUL | MERGE |
| B-M11 | 碎片率 | 连续 10 局 | 地址空间无断裂 | 90 | 10 局协议 | **SOLO** |
| B-M12 | DLL 卸载释放 | 点退出 | 干净退出零残留 | 10 | ZC-1 Q5 | MERGE |

---

## 5. 依赖与既有卡挂载点

| 依赖 | 覆盖条目（主） | 挂载方式 |
|---|---|---|
| **ZC-1** | B-N03/N12/N13/N17, B-L09/L13/L14, B-R11/27/28/29, B-M12, B-A05/A10/A14 | 在 Q2/Q3/Q5/Q6 加步骤，不改卡骨架 |
| **ZC-RE1** | （本批 B 类不直接挂钩；ABI 断点习惯可复用至 B-N06） | 调试器段 A 模式 |
| **ZC-11 / harness** | B-M07/M10, 全部长跑 | `bench_replay` + `except_gate`（0 字节红线） |
| **ZC-GAP-P21 / P223** | B-L09, B-L10, B-L11 | 套件五判定指标 |
| **EXCEPT-AB** | B-M07, 崩溃类 | 收尾主动检 `except.txt` |
| **套件一 NetSync** | B-N01/03/10/11/13/15, B-L07/08 | §7.2 双端镜像协议 |
| **套件二 Render** | B-R01/02/03/06/11/16/23/26 | 遥测三指标 |
| **套件三 Audio** | B-A01/02/05/08/09/12/13 | WASAPI+盲测 |
| **套件四 Long-haul** | B-M01/02/03/07/09/10 | 60 min / 8 AI |
| **套件五 Logic/Fog** | B-L01/02/05/09/10/12/13/15 | 裂缝+Reveal 场景 |
| **S18 scripts** | 全部 STATIC 24 条 | 退出码 0 即关账 |
| **DUAL-LAN** | B-N10/11/12/13, B-L07（硬前提，单实例不可代） | 双机同网段 |
| **DEBUGGER** | B-N06 | 硬件断点 0x64CC61 |
| **SOLO 专属** | ALTTABx20 / 4K / WASAPI / NETCOND / RELOAD5 / MULTI-DEVICE | 独立卡 |

---

## 6. 窗口预算与执行顺序建议

1. **先关 STATIC 24 条**（离线脚本，~30 min）——零真机成本。
2. **再跑 MERGE 50 条**（挂套件一~五 + ZC-1，约 12–16 h）——优先 Top10 中的 B-N03/N12/N13/L09/L10/L13/R03。
3. **最后 SOLO 18 条**（约 12–14 h）——其中 B-N06、B-L11 可与长跑并行准备环境。

| 桶 | 条数 | 真机窗口合计 |
|---|---:|---|
| STATIC | 24 | 0 |
| MERGE | 50 | ~12–16 h |
| SOLO | 18 | ~12–14 h |
| **合计** | **92** | **~24–30 h**（不含排障） |

---

## 7. 交付物与合规

| 路径 | 内容 |
|---|---|
| `docs/re/b_class_live_test_index.md` | 本可执行索引（92 条 + Top10 + 三桶） |
| `out/re_work/re_sprint/R_b_index/b92_catalog.tsv` | 92 行机读全表 |
| `out/re_work/re_sprint/R_b_index/buckets_top10.md` | 分桶清单 + Top10 + sweep 对照 |
| `out/re_work/re_sprint/R_b_index/README.md` | 目录说明 |

**未改**：`open_items_sweep.md`、`offline_verification_alternatives.md`、台账、看板、`ra2render/**`、`gamemd*`。

---

*R-B-INDEX 编制完成 · 源口径：open_items §3 样本 12 + offline_verification §6 全量 92 · 可静态关闭 24 / 可并入 50 / 需独立卡 18*
