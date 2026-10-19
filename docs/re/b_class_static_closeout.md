# R-B-STATIC · B 类 STATIC 24 条离线关账

> **任务号**：R-B-STATIC · **产物标注**：「离线闭环·真机可选烟雾」
> **源（只读）**：`docs/re/b_class_live_test_index.md` §2 STATIC 桶 · `docs/re/offline_verification_alternatives.md` §6 矩阵 · S18 工具链规格
> **禁写**：open_items / 台账 / 看板 / ra2render / gamemd
> **复算脚本**：`out/re_work/re_sprint/R_b_static/{verify_static_24.py, check_trampoline_rel32.py, binary_rollback_oracle.py}`
> **可写域**：`out/re_work/re_sprint/R_b_static/**` · 本文件

---

## 0. 总裁定

| 指标 | 值 |
|---|---:|
| STATIC 桶总数 | 24 |
| **离线闭环（可关账）** | **24 / 24** |
| 须真机 | 0（全部 24 条判据均为 ABI/数学/机器码/控制流，可离线复算） |
| 真机可选烟雾 | 24（每条均附烟雾建议，非强制） |
| 复算脚本退出码 | 3/3 = 0 |

**关闭语义**：S18 三脚本（`verify_all_24.py` / `check_trampoline_rel32.py` / `binary_rollback_oracle.py`）复算通过 → `[待实测]` 降为 **「离线闭环·真机可选烟雾」**。**不得**写「已实测」。

---

## 1. 复算脚本与结果

| 脚本 | 覆盖 | 断言数 | 退出码 | 结果文件 |
|---|---|---:|---:|---|
| `verify_static_24.py` | 24 条主断言（机器码/ABI/数学/锚点） | 24 | **0** | `results_verify_static_24.txt` |
| `check_trampoline_rel32.py` | Rel32 复算 + 4GB 溢出 + ΔESP 平衡 + H-D5 movzx 规格 | 4 | **0** | `results_trampoline_rel32.txt` |
| `binary_rollback_oracle.py` | 补丁 Install→Uninstall 回滚 MD5 纯净度 | 6 | **0** | `results_rollback_oracle.txt` |

**二进制身份**：`ra2youli/gamemd.exe` · size=4,825,360 · MD5=`4f37486e5b0dbe2ae5f45aeee0f98367` · ImageBase=`0x00400000`

---

## 2. 逐条结论（24 条）

### 2.1 渲染与微内核 B-R（10 条）

| ID | 测什么 | 结论 | 证据等级 | 脚本复算结果 | 烟雾建议 |
|---|---|---|---|---|---|
| **B-R04** | 3x3 菱形外扩几何包络 | **离线闭环·真机可选烟雾** | [实证·数学] | 3x3 邻域 9/9 格 100% 覆盖；高程 Z∈[0,2080] lepton 邻域并集=外扩矩形 | 高地斜坡边缘单位移动无切割 |
| **B-R05** | RLE 虚表 30 变体分发 | **离线闭环·真机可选烟雾** | [实证·机器码] | 4 关键虚表条目均定义且指向代码段：Particle→0x62CEC0 / PSys→0x62E280 / Building→0x43D290 / Bullet→0x468090 | 全图素调用无非法指令 |
| **B-R07** | Blitter 工厂 this 布局 | **离线闭环·真机可选烟雾** | [实证·机器码] | 0x48EBF0: `push 8` + `call 0x7C8E17` → this=8B（1 vptr + 4B flags）；尺寸表 4/8/12/16 自洽 | 所有材质零泄漏 |
| **B-R09** | Pitch stride 跨行安全 | **离线闭环·真机可选烟雾** | [实证+推演] | Blitter 经虚函数走 Surface Pitch 步进；尺寸表 8B 自洽（参 `blitter_microkernel_deep_dive.md`） | 2560x1440 无撕裂 |
| **B-R12** | VXL 切片深度单调性 | **离线闭环·真机可选烟雾** | [实证·数学] | θ∈[-80°,80°] cos(θ)>0 ⇒ 深度序列单调；后→前绘制无反向遮挡 | 360° 旋转无穿模 |
| **B-R14** | VXL 法线定点精度 | **离线闭环·真机可选烟雾** | [实证·数学] | \|n\|,\|l\|≤127 ⇒ \|prod\|≤16129，32bit 零溢出；量化误差≤0.5 ulp | 环境光渐变平滑无黑斑 |
| **B-R19** | 粒子槽 69 ABI ret 8 | **离线闭环·真机可选烟雾** | [实证·机器码] | v[69]@0x007EFA68 → 0x0062CEC0 (ParticleClass::Draw)；入口 `83 EC 24 53 55 56 57` | 大面积烟雾 ESP 零偏移 |
| **B-R20** | 微粒槽 69 ABI ret 8 | **离线闭环·真机可选烟雾** | [实证·机器码] | v[69]@0x007EFCB0 → 0x0062E280 (PSysClass::Draw)；入口 `83 EC 08 56 57` | V3 尾烟黑雾不渲染栈平衡 |
| **B-R22** | 565 环境光饱和钳位 | **离线闭环·真机可选烟雾** | [实证·数学] | RGB565 钳位 R/B∈[0,31] G∈[0,63] 全值域 [-100,200] 合法；无高位回绕 | 核爆白光无紫绿噪点 |
| **B-R28** | 坐标边界钳位 | **离线闭环·真机可选烟雾** | [实证·机器码] | TryGetCellAt@0x5657A0 越界→InvalidCell@0x00ABDC50；.text 457 处钳位引用 | 边缘疯狂点击无崩溃 |

### 2.2 音频 B-A（2 条）

| ID | 测什么 | 结论 | 证据等级 | 脚本复算结果 | 烟雾建议 |
|---|---|---|---|---|---|
| **B-A06** | PlayGlobal ABI ret 8 | **离线闭环·真机可选烟雾** | [实证·机器码] | 0x750920 早退路径 `xor eax,eax; pop ecx; ret 8` @ 0x750931；raw=`51 A0 AC 64 84 00 89 54 24 00 84 C0 75 06 33 C0 59 C2 08 00` | 高频调用 ESP 水平 |
| **B-A07** | PlayAt ABI ret 4 | **离线闭环·真机可选烟雾** | [实证·机器码] | 0x7509E0 早退路径 `xor eax,eax; pop ebx; ret 4` @ 0x7509EF；raw=`A0 AC 64 84 00 53 84 C0 8B DA 75 06 33 C0 5B C2 04 00` | 远处爆炸栈深度恒定 |

### 2.3 联机网络 B-N（6 条）

| ID | 测什么 | 结论 | 证据等级 | 脚本复算结果 | 烟雾建议 |
|---|---|---|---|---|---|
| **B-N02** | GameSpeed 映射公式 | **离线闭环·真机可选烟雾** | [实证·机器码] | 0x55D51C `mov eax,0x3E8` / 0x55D522 `idiv [0xA8B558]` / 0x55D55E `mov [0x887330],esi`；60fps→16ms / 30fps→33ms | 速度 6=60fps 3=30fps |
| **B-N04** | CRC 环 &0xFF 取模 | **离线闭环·真机可选烟雾** | [实证·机器码] | 0x64DE60 `and ecx,0x800000FF` (signed-mod 256)；&0xFF∈[0,255] 环内安全；LatestFramesCRC[256]@0xB04474 | 长跑帧号溢出无崩 |
| **B-N05** | H-D1 EFLAGS/ZF 保持 | **离线闭环·真机可选烟雾** | [实证·机器码] | 0x64C6F2 `jne 0x64CC61` (rel32=+0x569)；ZF=1 顺序 / ZF=0 跳转 | CRC 相等 100% 顺序执行 |
| **B-N08** | H-D5 0F B6 C0 修正 | **离线闭环·真机可选烟雾** | [实证·机器码] | 原版尾声 `5F 5E 5D 5B 83 C4 14 C3` 匹配；邻域无 `83 E0 FF`；生产跳板 +0x10=`0F B6 C0` movzx eax,al | 长跑 1000 帧写指针回绕 |
| **B-N09** | H-D6 call 0x4C6CB0 重放 | **离线闭环·真机可选烟雾** | [实证·机器码] | 0x64C911 call 0x4C6CB0 / 0x64CC0A call 0x4C6CB0；双站点 rel32 精确 | 命令 100% 消费镜像无丢 |
| **B-N16** | PRNG 零污染 | **离线闭环·真机可选烟雾** | [实证·机器码] | CRT 体(0x7C8B00..0x7D1000)→Random=0/RandomRanged=0；Draw 族→Random=0 | 双端 500 帧 PRNG 消费相等 |

### 2.4 游戏逻辑 B-L（2 条）

| ID | 测什么 | 结论 | 证据等级 | 脚本复算结果 | 烟雾建议 |
|---|---|---|---|---|---|
| **B-L03** | 寻路无 PRNG 副作用 | **离线闭环·真机可选烟雾** | [实证·机器码] | PathFinder::FindPath@0x42C900(体 0x42C900..0x42D200)→Random=0/Ranged=0；UpdatePathfinding@0x4D3920→0/0。注：实际算法为 Dijkstra/均匀代价搜索，非 A* | 相同起终点拐点序列一致 |
| **B-L16** | InvalidCell 单例边界退避 | **离线闭环·真机可选烟雾** | [实证·机器码] | 0x00ABDC50 .text 立即数引用 457 处；+0x24 (0x00ABDC74) 配对 443 处；TryGetCellAt 越界返回单例 | 点黑边外原地不动 |

### 2.5 内存/CRT B-M（4 条）

| ID | 测什么 | 结论 | 证据等级 | 脚本复算结果 | 烟雾建议 |
|---|---|---|---|---|---|
| **B-M04** | P-M1 8 字节对齐 | **离线闭环·真机可选烟雾** | [实证·数学] | SBH 块公式 `(req+0x17)&~0xF` 对 req∈[1,511] 全 16B 对齐 ⇒ 8B 模数恒 0 | 数千炮弹齐射零异常 |
| **B-M05** | P-M2 Double Free 投毒 | **离线闭环·真机可选烟雾** | [实证·数学] | 投毒魔数 0xDEADBEEF 二次 free 检出自愈；图论切断 freelist 环形死循环 | 重复释放池自愈不卡死 |
| **B-M06** | P-M3 地址范围双守卫 | **离线闭环·真机可选烟雾** | [实证·数学] | 双边界 [lo,hi) 分类 100% 正确；池外指针穿透原生堆 | Bink/DirectPlay 释放零误 |
| **B-M08** | P-M5 启动期单次锁定 | **离线闭环·真机可选烟雾** | [实证+推演] | EnableMemoryPool 启动期读取→常量；运行期无写路径；热改 INI 不切池开关 | 对局中改配置池仍稳定 |

---

## 3. 跳板 Rel32 与回滚纯净度

### 3.1 check_trampoline_rel32.py

| 断言 | 结果 | 详情 |
|---|---|---|
| Rel32 公式复算 | **PASS** | Rel32 = TargetVA - (InsnVA + InsnLen) 全部一致 |
| 4GB 符号溢出 | **PASS** | 最大 \|rel32\|=0x163946D (23.3M) < 2^31 |
| ΔESP == 0 | **PASS** | pushfd(+4)+pushad(+32) ↔ popad(-32)+popfd(-4) 对称 |
| H-D5 0F B6 C0 规格 | **PASS** | 生产跳板含 movzx eax,al，无 83 E0 FF |

> **历史注记**：S15 `verify_trampolines.py` 中的 TRAMP_HD5 草案字节串仍含 `83 E0 FF`（符号扩展漏洞）。生产规格已修正为 `0F B6 C0`（见 `landing_pack_preflight_audit.md` §一 P-1.3）。本脚本采用生产版字节。

### 3.2 binary_rollback_oracle.py

| 断言 | 结果 | 详情 |
|---|---|---|
| 4 补丁点原字节匹配 | **PASS** | H-D5 尾声 / PlayGlobal / Particle v[69] / PSys v[69] |
| Install→Uninstall 回滚 | **PASS** | 全镜像 MD5 = `4f37486e5b0dbe2ae5f45aeee0f98367` |
| Install 检测器 | **PASS** | 补丁后 MD5 ≠ 原始，确认补丁生效 |

---

## 4. 须真机项

**0 条**。全部 24 条 STATIC 判据均为 ABI/数学/机器码/控制流，已离线闭环。

---

## 5. 真机可选烟雾（非强制）

每条可在解冻后追加轻量烟雾验证（约 5–10 min/条），但**不作为关账前提**：

| 组 | 烟雾动作 | 覆盖 |
|---|---|---|
| 渲染 | 高地斜坡移动 + 核爆白光 + 360° VXL 旋转 + 边缘点击 | B-R04/12/14/22/28 |
| ABI | 大面积烟雾 / 高频音效，断点查 ESP | B-R19/20, B-A06/07 |
| 联机 | 速度 6/3 各 30 秒 + 长跑帧 CRC | B-N02/04/05/08/09/16 |
| 逻辑 | 点黑边 + 相同起终点寻路 | B-L03/16 |
| 内存 | 千弹齐射 + 视频过场释放 | B-M04/05/06/08 |

---

## 6. 合规声明

- **未写「已实测」**：全部标注「离线闭环·真机可选烟雾」
- **未改**：`open_items_sweep.md`、`offline_verification_alternatives.md`、台账、看板、`ra2render/**`、`gamemd*`
- **证据分级**：[实证·机器码] = 字节可复算 · [实证·数学] = 公式/算法闭合 · [实证+推演] = 机器码 + 逻辑推断

---

*R-B-STATIC 离线关账完成 · 24/24 闭环 · 复算脚本 3/3 退出码 0 · 须真机 0 条*
