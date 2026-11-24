# W177-G · HOVER_CELL（T1a 交付：引擎「鼠标所在格」全局 —— 全项目可复用）

> 目标 `ra2youli\gamemd.exe` SHA-256 `73201CC0…F67476`（只读未改）。全程 ReadProcessMemory + 合成 SetCursorPos；未写内存/未注入/未改 `ra2youli\`/未联网。

## 结论（一句话）
**引擎维护的鼠标所在格全局 = `0x0088095C`，读宽度 dword(4B)，编码 = packed CellStruct `{ X:uint16(low), Y:uint16(high) }`（即 `value = (Y<<16)|X`），不是 `(Y<<9)+X`。** 读它即得光标尖端所在格，光标→格成为格空间闭环，无需任何屏幕标定。分级 `[已证]`（动态自洽 26/26 + 静态 xref 到 GetCellAt）。

## 1 动态验证（只读轮询 + 细步进；不靠移动猜格）
方法：
1. 进游戏（Deadman's Ridge SE，Libya，10000 credit，相机 `0x886FA0/4=(0,0)` 全程不变），把光标置于安全区 `P0=(1300,600)` 物理像素（离四边/侧栏 ≥200px，绝不触发边缘滚屏）。
2. 对 `.data` 全段 `0x812000..0xB79BE4`（892,665 个对齐 dword）在 4 个光标位置做只读快照：base / +10X-cell / +10Y-cell / 回 base。筛"回 base 相等"（鼠标驱动、非帧噪声）且增量呈格坐标签名的 dword。
3. 唯一符合者 `0x88095C`（详见 `EVIDENCE/t1a_k10_changes.json`）。
4. 细步进确认（`work/t1a_verify.py`，`EVIDENCE/t1a_v1_verify.json`）：沿下右（X 轴）每 0.5 格步进 12 步、回中、沿下左（Y 轴）12 步；每点读 `dword[0x88095C]` 拆出 X/Y，再用 §951 取格路径 `CellClass*=dword[0x87F924]+((Y<<9)+X)*4` 取格，读其 `MapCoords(+0x24/+0x26)` 回验。

结果（26 个采样点，**26/26 自洽**）：
- base `(1300,600)` → `0x00500025` → X=37,Y=80 → 取格 `0x02C8C580`，其 `+0x24=37 / +0x26=80` ✓
- X 轴步进 6 格：`X=37→43`，Y 恒 80；每格 `X` 在两物理步间按阶梯 +1（如 X+0.5: X=38，X+1.0: X=38，X+1.5: X=39…），每点取格 MapCoords 与 (X,Y) 全等 ✓
- 回中 `(1300,600)` → 精确复位 `0x00500025` ✓
- Y 轴步进 6 格：`Y=80→89`（阶梯），每点取格 MapCoords 全等 ✓

**结论**：`dword[0x88095C]` 的 lo16/hi16 就是引擎光标格的 X/Y；且该格在格数组中真实存在、自报坐标一致。**无需标定**。

## 2 静态确认链（磁盘只读反汇编；`work/t1a_xref.py` / `t1a_xref2.py`）
- **写入点**：`0x004FB3BC mov dword ptr [0x88095C], edx`（源 `0x88096A/6E/74/78/80/7C` 一组格坐标全局）⇒ 引擎每帧维护该全局，非我方写入。
- **喂给 GetCellAt 的直接证据**：`0x006DBEB2 mov ecx,[0x88095C]` → `mov [esp+0x24],ecx` → `lea eax,[esp+0x24]` → `push eax` → `mov ecx,0x87F7E8` → **`call 0x5657A0`**（GetCellAt，入参 `&CellStruct`，this=MapClass 单例）。完全符合任务给的确认链。
- **逐字读点**：`0x004AACDE cmp dx, word [0x88095C]` / `0x004AACEC cmp ax, word [0x88095E]` ⇒ X 在 `+0`，Y 在 `+2`，印证 packed CellStruct 布局。
- **足迹迭代基准**：`0x006D5144 / 0x006D541E / 0x006D546D / 0x006D54CE` 等 6 处以 `0x88095C` 为基址做 `[base+off]` 偏移，正是"以光标格为原点铺建筑足迹"的静态形状。
- 全镜像 `.text` 中 `0x0088095C` 立即数裸字节命中 **12 处**：`4AACE1/4FB3BE/57B4BE/6D5146/6D52B3/6D541F/6D546E/6D54CF/6DBEB4/6DC017/6DC103/6DC1E3`。

## 3 编码细节与旁证
- packed CellStruct：`value=(Y<<16)|X`，X/Y 均为 uint16（有符号 movsx 读时按 short）。W177-F 曾把 `0x88095C` 列为未确认候选（`mouse_scan_changes.json`），本卡坐实。
- `0xABDC74`（S12-Q2 记为 InvalidCell packed 暂存）在鼠标移动时瞬时出现 `0x5D0017`（X=23,Y=93），同布局，佐证引擎用同一 packed 形式传格坐标。
- 附：鼠标**像素**全局（非格、勿混）：`0x00B0CBF8`=X、`0x00B0CBFC`/`0x00B0563C`=Y（逻辑 client 像素 = 物理像素/1.875；本卡 P0 物理(1300,600)→(693,320)）。格全局与像素全局都在 `.data`，一次快照可同时取。

## 4 可独立复算（给审计）
```
# 动态：读格 + 自洽
python work/t1a_verify.py audit            # 需游戏在相同地图/相机；每点打印 X/Y 与取格 MapCoords
# 静态：xref
python work/t1a_xref2.py                    # 打印 12 处命中窗口，含 6DBECB call 0x5657a0
# 差分原始
work/t1a_scan.py / EVIDENCE/t1a_k10_scan.json  → candidates[addr=0x0088095C]
EVIDENCE/t1a_v1_verify.json                 → 26 行 X_lo/Y_hi == mapcx/mapcy
```
核心数字：**26/26**（细步进自洽点数）、**12**（.text 立即数命中）、**1**（`call 0x5657A0` 直接证据 `0x6DBECB`）。

## 5 对 T2 的直接使用（闭环，无需仿射）
目标格 `(Tx,Ty)`：移动光标，读 `dword[0x88095C]`，拆 `curX=lo16, curY=hi16`；按屏幕微分 `ΔX 格→(≈+50.85,+28.08)px`、`ΔY 格→(≈-70.35,+28.34)px`（本卡实测阶梯：+1 X 约需物理步 (+50.8,+28)，+1 Y 约 (-70,+28)，仅用于步进方向，判据始终回读格全局）把光标挪到 `cur==(Tx,Ty)`。每次点击前后回读 `0x88095C` 与 `0x886FA0/4` 验证相机未动、落点未漂。**判据以格全局为准，不用颜色。**
