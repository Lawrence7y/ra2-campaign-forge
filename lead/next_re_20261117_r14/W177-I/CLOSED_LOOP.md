# W177-I · CLOSED_LOOP（T3 步长与迭代轨迹）

## 1. 步长（cell→screen 正向 J，审计独立拟合值）
- `JX = (55.6, +25.9)` px/格：cellX +1 → screen (+55.6,+25.9)
- `JY = (−55.6, +25.9)` px/格：cellY +1 → screen (−55.6,+25.9)
- 闭环用阻尼 0.75 + Broyden rank-1 自适应；每步重读相机 0x886FA0/4，变了即停。
- hover = `dword[0x88095C]` packed CellStruct（X 低16、Y 高16）。

## 2. 迭代轨迹（首会话 pid 3928，目标 anchor(112,61)）
```
it00 screen=(1400,600) cell=(111,60) err=(+1,+1) cam=(0,0) frame=642
it01 screen=(1400,638) cell=(112,61) err=(0,0)   cam=(0,0) frame=652  → E=0 收敛
```
- 1 步收敛（2 trace 行）；Jfinal 因 dsx≈0 的 rank-1 修正偏离初值，但已收敛无碍。
- 相机全程 (0,0)。

## 3. 第2次尝试（pid 23208，修正 anchor(113,62)）
```
loop ok=True cur=(113,62), iters 同结构；J0=[55.6,25.9]/[-55.6,25.9]
```

## 4. 地基偏移（实测更正 —— 本卡最重要更正）
- 上轮/任务假设：地基占格 = hover + (0..2, +1..+2)。
- **本卡实测**（对照放置成功，hover(106,60)）：NAPOWR 足迹六格 =
  `(105,60) (105,61) (106,60) (106,61) (107,60) (107,61)`
  ⇒ **X ∈ [hover−1, hover+1]，Y ∈ [hover, hover+1]**；building Location = hover−(1,0)；实测 offset=[−1,0]。
- 因此覆盖目标 T 应取 hover≈(T.x, T.y−1) 或 (T.x±1, T.y−1)，使 T 落在 `[hover−1..hover+1, hover..hover+1]` 内。
- 第1次尝试 anchor(112,61) 的足迹 Y 只到 62，未覆盖 T.y=63（偏移假设错）——这是第1次失败的原因之一。
- 第2次用修正 anchor(113,62) 足迹覆盖 T，但**步兵格预览 RED，UI 拒绝放置**（因步兵占位），非偏移问题。
- 证据：`EVIDENCE/control_green.json`（placed + measured_offset）、`EVIDENCE/full_run.json`（closed_loop trace）、`EVIDENCE/t3b_full.json`（修正 anchor loop）。

## 5. 收尾纪律
- 全程只读 RPM + 合成 SetCursorPos/mouse_event，未写内存/未注入。
- 落格判据保持：点击前读 headA/frame，≤2 帧内读目标格 [+0xE4]，nA≥2 且新 head RTTI=BuildingClass（本卡两次均未达）。
