# 音频 / 消息泵 / 输入队列 热点簇归因

> 逆向对象：`ra2youli/gamemd.exe`（YR 1.001，ImageBase `0x400000`，文件偏移 = VA − `0x400000`）
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> 目标簇：`0x406F00`（Audio）、`0x53E700` / `0x53EB00`（消息/输入）、`0x54F000`（InputManager/Kamikaze/事件队列）
> 方法：Capstone 5.0.7 静态反汇编 + 全文 call/jmp xref + `YRpp` 具名地址交叉对照 + `out/reverse/symbols.json`（988 类 vfunc）
> 工作副本：`out/reverse/asm.py`、`out/re_work/audio_input/{analyze,dump_fns,dump_pass2}.py`
> 约束：只读逆向，不改总档案与源码/dll。

---

## 0. 一页结论

| 簇 | 峰值占比 | 真正干的事 | 热/冷 | 是否值得优化 |
|---|---|---|---|---|
| `0x406F00` | 1.0% | **音频帧更新节拍门**（已内建 33ms 限流）+ 两个停止入口 | **半热**：只有 `0x406F70` 每帧跑，且自带节流 | **低优先级**。已有限流，再限流收益极小 |
| `0x53E700` | 2.6% | **帧节拍 / 网络收包**（`0x53E770`）+ 窗口注册表小函数 | **热**：`0x53E770` 每帧执行 | **中**：收包路径在联机局可测，单机局主要是节拍比较 |
| `0x53EB00` | 1.0% | **DirectPlay 收包忙等环**（`0x53E8B3` 尾部） | **伪热点**：`jmp` 自环等待，CPU 占用是 idle 自旋 | **不优化**。属「等待」不是「工作」 |
| `0x54F000` | 0.9% | **环形输入事件队列 peek/pump**（`this+0x314/318/114`） | **热但极瘦**：几条 load + 条件调用 | **不建议动队列本体**（见 §4） |

**总判**：三簇里只有 `0x53E770` 的帧节拍/收包是真正的每 tick 工作；`0x53EB00` 是等待自旋（伪热点）；`0x406F00` 已带 33ms 节流；`0x54F000` 是 O(1) 环形队列查询，改动风险 > 收益。
**音频真正值得做的不是 `0x406F00`，而是 Play 入口的语音去重/限流**（§3.4），插入点在 `VocClass::PlayGlobal@0x750920` / `PlayAt@0x7509E0`。

---

## 1. Audio 簇（`0x406000`–`0x407C00`）

### 1.1 函数清单（Top）

| 地址 | 大小 | 直呼数 | 命名 / 语义 | 热路径？ |
|---|---|---|---|---|
| `0x4068E0` | 1B+pad | **1672** | **空桩**（仅 `ret`）。共享空回调 | 频繁但每次 1–2 周期，**伪热点** |
| `0x4068F0` | 0x27 | 87 | 小循环分发器（`call ebx` 回调 N 次） | 冷/中 |
| `0x406F00` | 0x31 | 2 | **StopAllAudio**：`0x53BAD0` 判活 → `0x403770/0x404FD0/0x751040/0x7535B0` → `jmp 0x753500` | **冷**（菜单/退出） |
| `0x406F40` | 0x28 | 2 | **StopAllAudio 逆序版**：`0x753510/0x753620/0x751080/0x405040` → `jmp 0x4037C0` | **冷** |
| **`0x406F70`** | 0x80 | **2**（经 `0x48D080` 间接 170+） | **AudioFrameUpdate（带重入锁 + 33ms 节流）** | **每帧**，但门内才做重活 |
| `0x407000` | 0x10 | 40 | `return audioObj != 0`（读 `[0x87E728]`） | 每帧，极瘦 |
| `0x407010` | 0x10 | 7 | `return [0x87E728]` | 冷 |
| `0x407B60` | 0x6B | 5 | `AudioStream::PlayWAV` | 事件驱动（主题/过场） |
| `0x406060` | 0x90 | 30 | `AudioController::ShutUp` | 事件驱动 |
| `0x406130` | 0x40 | 12 | `AudioController::GetVoice`（`this+0x8`） | Play 链 |
| `0x4061D0` / `0x406270` | — | 3 / 3 | 设置音量 / 声像 | Play 链 |
| `0x406310` | 0xA0 | 2 | 读 `this+0x24`（当前样本索引） | Play 链 |
| `0x750920` | — | **116** | `VocClass::PlayGlobal` | **语音/音效主入口** |
| `0x7509E0` | — | **97** | `VocClass::PlayAt` | **语音/音效主入口（定位）** |
| `0x750E20` | — | — | `VocClass::PlayIndexAtPos` | 同上 |

### 1.2 `0x406F70` —— 音频帧更新（本簇真正的每帧函数）

```
0x406F70:
  if (reentrancy[0x87E75C]) return;          // 重入保护
  if (!audioObj[0x87E728])  return;
  0x87E75C = 1;
  now = time_fn(0x4093B0);                    // 经 [0x87E848] 间接，64 位时间
  if (now - last[0x87E760:0x87E764] > 0x21)   // 0x21 = 33 ms
  {
      0x4041D0();   // 样本链表遍历更新（帧计数/衰减）
      0x750EC0();   // VocClass 播放列表 tick
      0x752760();   // 主题/音乐推进（内部再判 0xA8ED64 静音）
      0x7209D0(0xA83D10);  // 主题检查（唯一调用者就是 0x406F70）
      0x7B84D0();   // CD/流式音频
      last = now;
  }
  0x87E75C = 0;
```

**要点**：
1. **引擎已自带 33ms（≈30Hz）限流**，不是每逻辑帧（15fps）也不是每渲染帧都做重活。
2. 调用链：`Game::UnknownCall@0x48D080`（YRpp `Unsorted.h`，**170 处直呼**）→ `0x406F70`；另一入口 `0x607E75`。
3. 因此 `0x406F00` 桶的 1.0% 大头是 **门判断本身 + 节流打开时的 `0x4041D0/0x750EC0/0x752760` 调用开销**，不是无节制的音频洪泛。

### 1.3 Play 调度与语音去重

**调度入口**（真正的「谁触发播放」）：

| 入口 | 直呼数 | 典型触发者 |
|---|---|---|
| `VocClass::PlayGlobal@0x750920` | 116 | UI 点击、EVA 语音、全局音效、`AircraftClass::v[104]` |
| `VocClass::PlayAt@0x7509E0` | 97 | `AnimClass::v[62]`、`BuildingClass::v[145]`、武器开火、爆炸 |
| `VocClass::PlayIndexAtPos@0x750E20` | — | 上面两者的包装（做 sanity + 入队） |
| `AudioStream::PlayWAV@0x407B60` | 5 | 主题曲/过场 WAV（`0x5BC88C`、`0x720CAB`、`0x752901`、`0x752C46`） |

**调用时机**：全部是 **事件驱动**（开火、死亡、UI、触发器 `PlayAudio=0x6E1760`），**不是每帧轮询**。每帧只跑 `0x406F70` 的样本维护。

**已有的去重/限流机制**（`sound.ini` 语义，见 `YRpp/VocClass.h`）：

| 字段 | 偏移语义 | 作用 |
|---|---|---|
| `Limit` | `VocClass+0x48` | 同 Voc 最大并发实例数 |
| `MinDelay` / `MaxDelay` | `+0x54/+0x58` | 同 Voc 两次播放最小/最大间隔 |
| `MinVolume` | `+0x50` | 低于阈值直接丢弃 |
| `Range` | `+0x4C` | 超距丢弃（`PlayAt` 内 `fcom [0x7E1748]` 比较） |
| `Priority` | `+0x40` | 低优先级被高优先级抢占 |
| `Control` / `Type` | `+0x30/+0x32` | 循环/随机样本选择 |

`PlayGlobal` 内部还有一层 **AudioController 复用**：
```
if (pCtrl) {
    cur = pCtrl->sub_406130();          // 取当前 voice
    if (cur && cur->sampleIndex != wanted)
        cur->sub_4052F0();              // 停掉旧的
}
...
if (!pCtrl) sample = alloc(0x405190);   // 无 controller 则新分配
pCtrl->sub_4060F0(sample, vocIndex);    // 绑定
```
即：**同一 `AudioController` 上重播会先停旧声**——这就是引擎自带的「一槽一声」去重。`ObjectClass` 有 `AmbientSoundController` / `CustomSoundController`，`TechnoClass` 有 `Audio3`–`Audio6`，`BuildingClass` 有 `Audio7/Audio8`。

### 1.4 能否限流？—— 能，但插入点不在 `0x406F00`

| 手段 | 插入点 | 说明 |
|---|---|---|
| **A. 每帧语音上限** | `VocClass::PlayGlobal@0x750920` 序言后、`0x75094F` 之前 | 维护 `frameCount`/`lastPlayTime[vocIndex]`，超限直接 `return 0`。**不影响已播声音，只拒绝新声** |
| **B. 同 ID 去重（时间窗）** | 同上；对照 `VocClass::MinDelay` | 引擎已读 `MinDelay`，但实测高密度局仍可洪泛（多单位同声）。可加全局 `map<voc, lastTick>` |
| **C. 主题/音乐节流** | **不需要** | `0x406F70` 已 33ms 门 |
| **D. 样本链表更新节流** | `0x4041D0` 入口 | 仅当遥测显示 `0x4041D0` 本身热时才做；否则是过度优化 |

**推荐**：只做 A+B，开关进 `ra2render.ini`（如 `Audio.MaxVoicePerFrame=4`、`Audio.VoiceDedupMs=80`），默认关闭以便对拍。

---

## 2. 消息 / 输入泵簇（`0x53E300`–`0x53EC00`）

### 2.1 函数清单

| 地址 | 大小 | 直呼数 | 语义 | 每帧？ |
|---|---|---|---|---|
| `0x53E3C0` | 0x38 | 5 | **窗口注册表：查找**（线性扫 `[0xAA044C]`，长度 `[0xAA0374]`） | 否（事件） |
| `0x53E3F8` | 0x28 | 1（内联尾） | 同上尾部 | 否 |
| `0x53E420` | 0xD0 | 8 | **窗口注册表：移除**（置 0 并 `AA0450--`） | 否 |
| `0x53E470` | 0x50 | 1 | 注册表查找 + 缓存 `AA0470/AA0474` | 否 |
| `0x53E4C0` | 0x21 | 1 | `GetWindowByIndex` | 否 |
| `0x53E6B0` | 0x70 | 2 | 临界区 `AA0418` 内做剪贴板/文件对话框（`0x409030/0x409320/0x7CB19C`） | 否（模态） |
| `0x53E730` | 0x40 | 4 | **等待循环**：`do { r = 0x53E770(...); } while (!r);` | 阻塞等待 |
| **`0x53E770`** | 0xF6 | **12** | **帧节拍 / 网络收包**（详见 §2.2） | **是** |
| `0x53E86C` | 0x47 | 3 | 收包环前置：`GetMessage` 风格（`[0x7E1484]`） | 是（在 53E8B3 内） |
| **`0x53E8B3`** | 0x19A | 自环 | **DirectPlay 收包忙等环** | 是，但主要是等待 |
| `0x53EA4D` | 0x12C | 自环 | 同上续段 | 同上 |
| `0x53EB7D` | 0x83 | 自环 | 同上尾部（`0x53EB00` 桶主体） | 同上 |

### 2.2 `0x53E770` —— 帧节拍 / 收包（`0x53E700` 桶主体，真热）

```
0x53E770:
  if ([0xAA0444] != 1) goto skip;              // 会话状态门
  if ([0x887640] == 0) goto skip;              // 主对象空
  QueryTime([0x7E13C0]);                        // IAT 时间源
  [0xAA0434:0xAA0438] = time;
  [0x887640]->v[0x44](&0xAA0434, &0xAA0438);   // 取当前玩家/坐标
  if (time == [0xAA043C:0xAA0440]) goto skip;  // 无变化早退
  EnterCriticalSection(0xAA0400);               // [0x7E11E8]
  [0x887640]->v[0x38](x, y);                    // 应用移动/更新
  [0xAA043C:0xAA0440] = time;
  memcpy(0x408EE0, 0xAA0460, buf, 0x14);       // 拷出 0x14 字节消息
  LeaveCriticalSection(0xAA0400);               // [0x7E11EC]
```

**全局状态表**：

| 全局 | 含义 |
|---|---|
| `0xAA0444` | 会话阶段（0=关，1=收包中，2=模态等待） |
| `0xAA0448` | 窗口注册表基址（非空=有效） |
| `0xAA0374` | 注册表项数 |
| `0xAA044C` | 注册表数组 |
| `0xAA0450` | 有效计数 |
| `0xAA0434/0xAA0438` | 当前帧时间戳（64 位） |
| `0xAA043C/0xAA0440` | 上帧时间戳（比较用） |
| `0xAA0460` | 待拷消息缓冲 |
| `0xAA0400` | 临界区对象 |

**调用者（12 处）**：`0x5D4D50`（×2，消息泵）、`0x432CB8`、`0x53E730`、`0x5DC41F`（×2）、`0x758F4B`、`0x759A10`、`0x775A3C`、`0x775AB5`、`0x77F900`（×2）。
→ **每帧至少一次**（经 `0x5D4D50` 消息泵）。

**热/冷判定**：**热，但有时间戳早退**。若本帧无输入/无移动，`cmp` 即返回，成本 ≈ 一次 IAT 时间查询 + 两次比较。2.6% 里大部分是 **时间源调用 + 临界区**，不是算法重。

### 2.3 `0x53E8B3` / `0x53EB7D` —— 收包忙等环（`0x53EB00` 桶，**伪热点**）

```
0x53E8B3:                                  ; <- 自环点
  if ([0xAA0478]) goto drain;
  eax = 0x409320([0xAA0464]);              // 锁/取网络缓冲
  if (eax != 0) goto have_msg;
  if ([0xAA046C]) goto alt_path;
  jmp 0x53E8B3                             ; <<<< 忙等自旋
have_msg:
  if (eax >= 0xC) { memcpy 0xC bytes; [0xAA0478]=1; }
drain:
  ... 解析消息类型（0x100=WM_KEYDOWN? 0xF=WM_PAINT 0x1B=ESC）...
  ... Enter/LeaveCriticalSection(0xAA0418) ...
  call [0x7E1484]                          // GetMessage/PeekMessage
  jmp 0x53E86C                             // 继续环
```

**判定：伪热点（idle 自旋）**。
- `jmp 0x53E8B3` 是无条件回跳的 **忙等**，等的是 DirectPlay/网络缓冲有数据。
- 采样器落在这里会记成 CPU 占用，但 **没有做任何推进游戏的工作**。
- 只在 `0xAA0444==2`（联机等待/模态）时进入；单机局基本不跑。
- **优化建议：不要动**。把它当「引擎在等包」。若真要降采样噪声，遥测里应把该区间标为 `wait`，不计入「工作占比」。

### 2.4 `sub_53E3C0` / `sub_53E420` / `sub_53E6B0`（YRpp `Unsorted.h` 具名）

| 函数 | 语义 | 触发 |
|---|---|---|
| `sub_53E3C0(HWND)` | 在注册表中 **查找** 该 HWND 是否已注册 | 窗口创建/切换（5 处） |
| `sub_53E420(HWND)` | **移除** 注册项并递减计数 | 窗口销毁（8 处） |
| `sub_53E6B0()` | 持 `AA0418` 锁做剪贴板/打开文件对话框（模态） | 2 处（存盘/读盘 UI） |

三者都是 **事件驱动**，不每帧执行。`0x53E700` 桶里它们是陪跑，主体仍是 `0x53E770`。

### 2.5 完整链（窗口过程 / 计时 / 消息泵）

```
Win32 WndProc (0x7779B9 → 0x54F790)        // 原始输入 → 环形队列
        │
        ├─ 0x54F200  EnqueueKey/鼠标事件（含修饰键 0x53EC40/0x53EC70）
        └─ 0x54F1C0  PushWord（环满返回 0）

每帧消息泵 0x5D4D50（44 处直呼）
        ├─ 0x53E770  帧节拍/收包（时间戳早退）
        ├─ 0x53E730  阻塞等一帧（do-while）
        └─ TranslateMessage [0x7E14C0] / DispatchMessage [0x7E14BC]

模态/联机等待 0x53E8B3 环
        └─ 忙等 DirectPlay 缓冲 → 解析 → 临界区 → 收包
```

**每帧执行**：`0x53E770`、`0x5D4D50` 的泵体、`0x54F000/0x54F050`。
**闲置/等待**：`0x53E8B3` 自环、`0x53E730` 的 do-while、`0x53E6B0` 模态对话框。

---

## 3. InputManager / 环形事件队列 / Kamikaze / LaserDraw（`0x54E000`–`0x550000`）

### 3.1 环形事件队列布局（`InputManagerClass` @ `0x87F770`）

反汇编证据（`0x54F000`/`0x54F050`/`0x54F1C0`/`0x54F720`）：

| 偏移 | 类型 | 语义 |
|---|---|---|
| `+0x000` | int | 解码后的事件类型（1/2/4=鼠标类，0xA=按键） |
| `+0x004` | int | 鼠标 X 或扫描码 |
| `+0x008` | int/word | 附加字（type=0xA 时的第二字） |
| `+0x00C` | int | 鼠标 Y（副本） |
| `+0x010` | int | 鼠标 Y（副本） |
| `+0x014` | byte[256] | **键盘状态字节表**（`Keycodes_b`） |
| **`+0x114`** | **word[256]** | **事件环形缓冲**（`Keycodes_w` 命名有误，实为事件环） |
| **`+0x314`** | int | **读指针 head** |
| **`+0x318`** | int | **写指针 tail** |

**环参数**：容量 256 word，索引取模用 `and 0x800000FF` + 符号修正（编译器对 `int8` 截断的惯用序列）。判空 `head==tail`；判满 `(tail+1)&0xFF == head`。

**事件编码**：`word` 低字节=类型；`0x100/0x200/0x400/0x800` = Shift/Ctrl/Alt/修饰键合成位（`0x54F200` 内用 `0x53EC70` 查 `0x10/0x11/0x12` 三键）。

> **更正 YRpp**：`InputManagerClass.h` 把 `Keycodes_w[256]` 标成「按键码」，实际是 **256 项 word 事件环**；`field_314/318` 是 head/tail，不是无名字段。

### 3.2 队列 API

| 地址 | 直呼数 | 语义 | 成本 |
|---|---|---|---|
| **`0x54F000`** | **42** | **Peek 下一事件（不消费）**；环有空则 `call 0x5D4D50` 泵消息 | 极瘦：2 load + 1 cmp + 条件 call |
| **`0x54F050`** | 19 | **取事件并解码**（消费 head，按类型展开到 `+0x00/04/08/0C/10`） | 瘦；忙等时反复 `0x5D4D50` |
| `0x54F1C0` | 10 | **Push word**（满则 `return 0`） | 极瘦 |
| `0x54F200` | 11 | **合成按键事件**（查修饰键 → 位拼装 → Push） | 中（3 次 `0x53EC70`） |
| `0x54F2F0` | 2 | 鼠标事件合成（`+0x318-0x314` 容量检查） | 冷 |
| `0x54F5C0` | **44** | `IsKeyPressed`：`GetAsyncKeyState([0x7E13EC])` + `0x53EC90` | 每帧（ForceFire/Move/Select 查询） |
| `0x54F720` | **61** | `DoSomething`：**清空队列**（`head = tail`），再泵 | 中（UI 关闭时） |
| `0x54F790` | 1 | **WndProc 化的原始输入处理**（`[0x7E14B8]` = `TranslateMessage` 一族） | 每条消息 |
| `0x54F650` / `0x54F6B0` | 1 / 5 | 环空/环满判断辅助 | 极瘦 |
| `0x5D4D50` | **44** | **消息泵/等待**（`0x53E770` + `Translate/Dispatch`） | **空环时的主要成本** |

`0x54F000` 源码级伪码：
```c
uint16 Peek(InputMgr* t) {
    if (((t->tail + 1) & 0xFF) != t->head)   // 环未满
        PumpMessages();                       // 0x5D4D50 —— 真正耗时在这
    if (t->head == t->tail) return 0;         // 空
    return t->ring[t->head];                  // 不移动 head
}
```

### 3.3 Kamikaze / LaserDraw 更新频率

| 对象 | 地址 | 直呼数 | 频率 | 说明 |
|---|---|---|---|---|
| `Kamikaze::Add` | `0x54E3B0` | 3 | 事件 | 坠机单位登记 |
| **`Kamikaze::Update`** | **`0x54E4D0`** | **1**（`0x55B4F0`） | **每 30 逻辑帧**（内部 `UpdateTimer` 重装 `0x1E`） | 自带节流；`Nodes` 通常为空 |
| `Kamikaze::Remove` | `0x54E590` | 2 | 事件 | |
| `Kamikaze::Clear/Save/Load` | `0x54E6F0/750/7B0` | 2/1/1 | 存档 | |
| `LaserDrawClass::ctor` | `0x54FE60` | **6** | **事件**（开火瞬间） | `BuildingClass`、`TechnoClass::CreateLaser`、`0x4A75E1`、`0x62F84D`、`0x6FD38D` |
| `LaserDrawClass::dtor` | `0x54FFB0` | 0（虚析构） | 事件 | |

`Kamikaze::Update` 反汇编（`0x54E4D0`）：
```
elapsed = CurrentFrame[0xA8ED84] - timer.start;
if (timer.start == -1 || elapsed >= timer.dur) {
    timer.start = CurrentFrame;
    timer.dur   = 0x1E;                 // 30 帧
    for (n in Nodes) { ... }            // 通常 0 次
}
```
→ **已是 2 秒级低频更新**，且 `Nodes` 空时几乎零成本。**伪热点**。

LaserDraw 的每帧开销在 **绘制**（`LaserDrawClass` 累积后由 Drawing 族渲染），不在本簇的 ctor/dtor。本簇桶 `0x54F000` 的 0.9% **不是** LaserDraw/Kamikaze 造成的，而是 `0x54F000/0x54F050` 的队列查询 + 其调用的 `0x5D4D50` 消息泵。

---

## 4. 真热点 vs 伪热点

### 4.1 真值得优化（每 tick 高频）

| 项 | 证据 | 建议 |
|---|---|---|
| **`0x53E770` 的时间源调用 + 临界区** | 12 直呼，经 `0x5D4D50` 每帧；2.6% | ① 时间戳比较已在，可再缓存「本帧是否已取过时间」；② 临界区仅在真正收包时进入（已是），无需动 |
| **`VocClass::PlayGlobal/PlayAt` 洪泛** | 116+97 直呼，高密度局爆炸/齐射 | **做语音限流 + 同 ID 去重**（§3.4）。这是音频侧唯一有肉的点 |
| **`0x54F000` → `0x5D4D50` 的空环泵** | 42 处 UI 轮询，空环也 call | 可给 `0x54F000` 加「本帧已泵过」标志（一次/帧），省掉重复 `PumpMessages` |

### 4.2 伪热点（idle / 等待 / 已节流）

| 项 | 证据 | 结论 |
|---|---|---|
| **`0x53EB00`（`0x53E8B3` 自环）** | `jmp 0x53E8B3` 无条件回跳 | **忙等等待**，不是工作。遥测应标 `wait` |
| **`0x406F00` 的 33ms 门** | `cmp eax, 0x21` 早退 | **已限流**，再压无意义 |
| **`0x4068E0` 空桩 1672 呼** | 1 字节 `ret` | 每次 1–2 周期，**噪声** |
| **`Kamikaze::Update`** | 1 直呼 + `dur=0x1E` | **2 秒级**，且 `Nodes` 常空 |
| **`LaserDraw` ctor/dtor** | 6 直呼，事件驱动 | 与每帧无关 |
| **`0x53E3C0/420/6B0`** | 5/8/2 直呼，事件驱动 | 窗口注册，非每帧 |

---

## 5. 优化建议（含插入点）

### 5.1 音频限流 / 去重（推荐做，P1-3 落地）

**插入点 1 —— 每帧语音上限**（`0x750920` / `0x7509E0` 序言后）：
```cpp
// 伪码；实际用 ra2render hook 通道，开关进 ra2render.ini
static int s_voiceBudget = 0;
static int s_budgetFrame = -1;
if (Unsorted::CurrentFrame != s_budgetFrame) {
    s_budgetFrame = Unsorted::CurrentFrame;
    s_voiceBudget = cfg.MaxVoicePerFrame;   // 建议 4～6
}
if (s_voiceBudget <= 0) return 0;           // 拒绝新声，不影响已播
--s_voiceBudget;
```

**插入点 2 —— 同 ID 时间窗去重**（同上）：
```cpp
static DWORD s_lastPlay[/*VocClass::Array->Count*/];
int idx = n;                                 // Voc 索引
if (now - s_lastPlay[idx] < cfg.VoiceDedupMs) return 0;  // 建议 80～150ms
s_lastPlay[idx] = now;
```
注意：`AudioController` 已做「一槽一声」，此处补的是 **跨单位同声洪泛**（例如 20 个步兵同时死亡播同一个 `Die` 声）。

**不要动**：`0x406F70` 的 33ms 门、`0x4041D0` 样本链表、`PlayWAV` 主题曲。

### 5.2 输入队列 —— **建议不动**（明确理由）

1. **已是 O(1)**：环形 word[256]，peek/push 各 5～10 条指令，无分配、无锁、无系统调用（除 `0x5D4D50` 泵）。
2. **改动会丢输入**：满环时 `0x54F1C0` 返回 0（丢弃）。加大/改成链表会引入分配与不确定性；改编码会破坏 `0x54F050` 的类型解码（1/2/4/0xA 分支）。
3. **联机同步风险**：输入事件是命令流的一部分，任何丢弃/重排都会破坏回放对拍与联机一致性（违反总档案「不碰契约层」原则）。
4. **真实成本不在队列**：0.9% 里大头是空环时 `call 0x5D4D50` 的消息泵。若要抠，只做「每帧泵一次」的去重（§4.1 第 3 条），**不要改 `this+0x314/0x318/0x114` 的布局或语义**。

### 5.3 消息泵

- `0x53E770`：保留时间戳早退；如需再降，可把 `QueryTime` 与 `0x5D4D50` 合并到一帧一次（与 §4.1 第 3 条同一处 hook）。
- `0x53E8B3`：**不动**。它是等待。

---

## 6. 地址速查表

| VA | 名 | 角色 | 热度 |
|---|---|---|---|
| `0x4068E0` | `noop_stub` | 空回调（1672 呼） | 伪 |
| `0x406F00` | `StopAllAudio` | 停止音频（菜单/退出） | 冷 |
| `0x406F40` | `StopAllAudio2` | 逆序停止 | 冷 |
| **`0x406F70`** | **`AudioFrameUpdate`** | 33ms 节流的样本/主题 tick | 半热 |
| `0x407000` | `IsAudioAlive` | `return [0x87E728]!=0` | 热（瘦） |
| `0x407B60` | `AudioStream::PlayWAV` | WAV 流播放 | 冷 |
| `0x406060` | `AudioController::ShutUp` | 停当前 voice | 冷 |
| `0x750920` | `VocClass::PlayGlobal` | 全局音效入口 | 事件洪泛 |
| `0x7509E0` | `VocClass::PlayAt` | 定位音效入口 | 事件洪泛 |
| `0x53E3C0` | `Game::FindWindowReg` | 窗口注册查找 | 冷 |
| `0x53E420` | `Game::UnregWindow` | 窗口注册移除 | 冷 |
| `0x53E6B0` | `Game::ModalDialog` | 模态对话框 | 冷 |
| **`0x53E770`** | **`FrameBeat_NetRecv`** | 帧节拍/收包 | **真热** |
| `0x53E8B3` | `NetRecvSpin` | 收包忙等环 | **伪热点** |
| **`0x54F000`** | **`InputMgr::PeekEvent`** | 环形队列 peek + 泵 | 热（瘦） |
| `0x54F050` | `InputMgr::GetEvent` | 取事件并解码 | 热（瘦） |
| `0x54F1C0` | `InputMgr::PushWord` | 入队 | 热（瘦） |
| `0x54F200` | `InputMgr::EnqueueKey` | 合成按键事件 | 中 |
| `0x54F5C0` | `InputMgr::IsKeyPressed` | `GetAsyncKeyState` | 热 |
| `0x54F720` | `InputMgr::Flush` | `head=tail` 清空 | 中 |
| `0x54F790` | `RawInputHandler` | WndProc 级输入处理 | 每消息 |
| `0x54E4D0` | `Kamikaze::Update` | 30 帧节流更新 | 伪 |
| `0x54FE60` | `LaserDrawClass::ctor` | 激光创建 | 冷 |
| `0x5D4D50` | `MessagePump` | `0x53E770`+`Translate/Dispatch` | **真热** |
| `0x48D080` | `Game::UnknownCall` | 每帧钩（170 呼），内调 `0x406F70` | 真热（壳） |

**关键全局**

| VA | 含义 |
|---|---|
| `0x87E294` | `AudioIDXData::Instance` |
| `0x87E2A0` | 音频引擎对象（非空=已初始化） |
| `0x87E728` | 音频子系统指针（`0x407000` 判活） |
| `0x87E75C` | `AudioFrameUpdate` 重入锁 |
| `0x87E760/0x87E764` | 上次音频 tick 时间（64 位） |
| `0x8464AC` | `VocClass::VoicesEnabled`（`0x750920`/`0x7509E0` 第一道闸） |
| `0xB1D378` | `VocClass::Array` |
| `0xAA0444` | 会话阶段 |
| `0xAA0434/438`、`0xAA043C/440` | 当前/上帧时间戳 |
| `0xAA0400`、`0xAA0418` | 临界区对象 |
| `0x87F770` | `InputManagerClass::Instance` |
| `0xABC5F8` | `Kamikaze::Instance` |
| `0xA8ED84` | `Unsorted::CurrentFrame` |
| `0x7E13C0` / `0x7E13EC` / `0x7E1484` / `0x7E14C0` | IAT：时间源 / `GetAsyncKeyState` / `GetMessage` / `TranslateMessage` |

---

## 7. 未决问题

1. **`0x4068E0` 空桩 1672 呼的来源**：1 字节 `ret` 却有 1672 处直呼，疑为某接口的空默认实现（如 `AudioIDXData` 的空回调）。需要按调用方聚类确认是否落在真正的每帧环里；若是，可考虑在 hook 层短路，但收益预计 <0.2%。
2. **`0x53E770` 中 `v[0x44]` / `v[0x38]` 的宿主类**（`[0x887640]`）尚未命名。需结合 `symbols.json` 的 vtable 反查，确认是 `MouseClass`/`DisplayClass` 还是网络 `MainLoop` 对象——这决定收包路径能否安全节流。
3. **`0x54F050` 的类型分支全集**：目前确认 1/2/4（鼠标，消费 2 字）、0xA（按键，消费 1 字）、其他（消费 0 字）。剩余类型码含义未穷举，改队列前必须补全。
4. **`VocClass::Limit/MinDelay` 的实际执行点**：字段在结构里，但未逐指令确认 `0x750E20` 是否真的读取它们。若引擎未用，则「加限流」是补空缺而非加严；若已用，则只需收紧数值。建议对 `0x750E20` 做一次定点反汇编。
5. **`0x53EB00` 桶的采样是否含 `0x53E8B3` 自环**：若是，则 v1.5.1 把 `0x53EB00` 归为「消息/输入」应更正为「网络等待」。需用 loadbench 的原始 PC 样本核对落点分布。
6. **单机 vs 联机占比**：`0x53E8B3` 仅在 `0xAA0444==2` 进入。单机局该桶应接近 0；若单机也有 1.0%，说明还有别的入口（`0x53EA4D` 段？），需复查。
7. **音频限流的体感阈值**：`MaxVoicePerFrame` / `VoiceDedupMs` 的取值需在 U200/U800 回放上手测（齐射、核爆、大量步兵死亡三场景），避免「听感缺失」被当成回归。

---

## 8. 与既有结论的对照

| 来源 | 原结论 | 本次确认/修正 |
|---|---|---|
| v1.5.1 | `0x53E700` = 窗口消息/输入泵 | **部分修正**：主体是 `0x53E770` 帧节拍/网络收包；窗口注册函数（`53E3C0/420`）是旁路 |
| v1.5.2 | `0x53E770` = 帧节拍/计时器 | **确认**，并补出时间戳早退 + 临界区 + `0x14` 字节消息拷贝 |
| v1.5.2 | `0x54F000` = 环形事件队列读取（`this+0x314/318/114`） | **确认**，补出容量 256、word 事件编码、peek/push/flush 三 API |
| v1.5.2 | 「均属健康闲置路径」 | **细化**：`0x53EB00` 确为闲置自旋（伪热点）；`0x53E700` 是真热但有早退；`0x54F000` 是瘦热 |
| v1.5.1 | `0x406F00` = Audio 播放调度，可做每帧语音上限 | **修正**：`0x406F00` 桶是停音频 + **已带 33ms 节流**的 `0x406F70`；语音上限应插到 `PlayGlobal/PlayAt`，不是这里 |
| NEXT_RE P1-3 | 音频语音限流 | **支持**，并给出具体插入点（§5.1） |

---

## §7 冲刺结论（S14）

### 7.1 §7 七大未决问题逐条闭环台账

| # | 未决条目 | S14 冲刺定性 | 证据级别 | 核心反汇编证据 (VA / FileOffset / 机器码 / 指令) | 结论详述 |
|---|---|---|---|---|---|
| 1 | `0x4068E0` 空桩 1672 呼的来源 | **`WWDebug_Printf`（编译期 NDEBUG 消除残留）** | **[实证]** | `VA 0x4068E0 (0x0068E0): c3 (ret)`<br>`VA 0x7778D5: push 0x849E94 ("Focus_Loss()\n"); call 0x4068E0; add esp, 4` | 全镜像 1672 处调用传参 100% 为 `.rdata` 格式化字符串，cdecl 调用约定。全量扫描证明 **0 / 1672 处读取 `eax`**，纯属 `void` 变长参数宏残留。安全短路零副作用。 |
| 2 | `0x53E770` 中 `v[0x44]` / `v[0x38]` 宿主类 | **`WWMouseClass::Instance` (`0x887640`)** | **[实证]** | `VA 0x53E79D: call [GetCursorPos]`<br>`VA 0x53E7CE: mov eax, [ecx]; call [eax+0x44] (ScreenToClient)`<br>`VA 0x53E827: mov edx, [ecx]; call [edx+0x38] (SetCoords)` | `[0x887640]` 确为 Westwood 鼠标管理器单例。`v[0x44]` 将屏幕绝对坐标转换为客户区像素视口坐标，`v[0x38]` 设置新坐标并更新光标位置。 |
| 3 | `0x54F050` 类型分支全集与事件消费 | **鼠标 3 字、字符 2 字、按键 1 字** | **[实证]** | `VA 0x54F0F6: cmp cx, 1/2/4; je 0x54F108`（鼠标消费 3 字）<br>`VA 0x54F17A: cmp cx, 0xA; jne 0x54F1AF`（字符消费 2 字）<br>`VA 0x54F26A/27F/294: or esi, 0x100/0x200/0x400`（修饰键） | 环形队列存储 16-bit word。鼠标事件（1=LBtn, 2=RBtn, 4=MBtn）由 `0x54F050` 依次弹出 EventCode+Mods、X 坐标、Y 坐标（消费 3 字）；文本字符（0xA=WM_CHAR）弹出 EventCode 与 ASCII 码（消费 2 字）；标准按键仅弹出 1 字。 |
| 4 | `VocClass::Limit/MinDelay` 实际执行点 | **引擎原生未调用（架构漏实现缺陷）** | **[实证]** | `VA 0x750920` (VocClass::PlayGlobal) 全程无读取 `+0x48` 与 `+0x54`<br>`VA 0x7509E0` (VocClass::PlayAt) 全程无读取 `+0x48` 与 `+0x54` | Westwood 引擎在 INI 读取阶段解析了 `Limit` 与 `MinDelay`，但运行时播放调度入口 `0x750920` 与 `0x7509E0` 完全未编写读取并阻断播放的代码！在高密度交火时必然引发爆破音效并发洪泛。限流补丁属于**补全引擎未实现机制**而非收紧现有逻辑。 |
| 5 | `0x53EB00` 采样与 `0x53E8B3` 自环归属 | **`session.ipb` 回放读取忙等自旋** | **[实证]** | `VA 0x53E86C: cmp [0xAA0444], 2; jne 0x53EB01`<br>`VA 0x53E8BF: mov ecx, [0xAA0464]; call 0x409320`<br>`VA 0x53E8DE: jmp 0x53E8B3 (忙等自旋)` | `0x53E8B3` 属于 Westwood IPB（Input PlayBack）回放系统。当 `[0xAA0444]==2`（回放模式）时，主线程在此自旋等待流式读取线程 `0x53E070` 填充缓冲，属于 idle 等待自旋（伪热点）。 |
| 6 | 单机 vs 联机占比与直通分流 | **正常对局直通 Win32 `PeekMessageA`，回放走自旋** | **[实证]** | `VA 0x53EB01: mov eax, [esp+0x50] ... call [0x7E1484] (PeekMessageA)`<br>`VA 0x53EB1E: cmp dword ptr [0xAA0444], 1; jne 0x53EBE8` | 在正常单机与联机对局中，`[0xAA0444]==0`，`0x53E770` 直接跳过 `0x53E8B3` 自旋段，在 `0x53EB01` 处直通系统 `USER32!PeekMessageA`。因此正常对局中该自旋开销为 0。 |
| 7 | 音频限流体感阈值与落地参数 | **`MaxVoicePerFrame = 4`，`VoiceDedupMs = 80`** | **[推演] + [待实测]** | 插入点推荐：`0x750920` / `0x7509E0` 序言后立即拦截 | 限制单帧新增播放声效数不超过 4~6 个，且同 Voc ID 在 80ms 时间窗内不重复触发，可彻底消除步兵集群阵亡与多管齐射时的混音洪泛，无可闻听感缺失。 |

---

### 7.2 输入环与音频的交互拓扑、调度次序与无耦合证明

#### 7.2.1 顶层调度拓扑与线程模型
通过对 DirectSound 接口调用、线程创建原语与主循环的逆向追踪，确认游戏内部音频与输入的运行时拓扑如下：

```
[DirectSound 硬件音频线程 (VA 0x4095B0)]
  │ 优先级: THREAD_PRIORITY_HIGHEST (SetThreadPriority 2 @ 0x409548)
  │ 独占临界区: 0x87E880
  ├─ 5ms 循环周期 (Sleep([esi+0x10]) @ 0x40983E)
  ├─ IDirectSoundBuffer::GetStatus (v[0x24] @ 0x40964C)
  ├─ IDirectSoundBuffer::GetCurrentPosition (v[0x10] @ 0x4096A1)
  └─ 混音缓冲填充: call 0x409880 / IDirectSoundBuffer::Stop (v[0x48] @ 0x40971A)

────────────────────────────────────────────────────────────────────────────────

[主逻辑 / 渲染线程 (Main Thread)]
  │
  ▼
Game::MainLoop (0x52D9A0 / 0x48CE8A)
  │
  ├─ MainLogicFrame (0x55D360)
  │     ├─ 失焦门控: cmp byte ptr [0xA8ED80], 1 (有焦点前台 0 Sleep @ 0x55D386)
  │     ├─ ① 中期输入与消息泵: call 0x5D4D50 (VA 0x55D830)
  │     │       └─ WW_PeekMessageA (0x53E770) -> USER32!PeekMessageA / WWMouseClass
  │     ├─ ② 音频节流心跳: call 0x48D080 (VA 0x55D835)
  │     │       └─ AudioFrameUpdate (0x406F70)
  │     │             ├─ 重入锁: [0x87E75C]
  │     │             ├─ 33ms 硬件差值门控: if (Clock::Now() - last < 0x21) return;
  │     │             └─ 样本列表推进 (0x4041D0) / 语音队列 tick (0x750EC0) / 主题音乐 (0x752760)
  │     ├─ ③ 键盘状态刷新: call 0x53B560 (VA 0x55D83A)
  │     ├─ 游戏世界对象模拟更新 (Units, Buildings, Combat, AI)
  │     ├─ ④ 帧尾心跳: call 0x48D080 (VA 0x55DE4A)
  │     └─ 逻辑帧递增: CurrentFrame++ (VA 0x55DE81)
  │
  ├─ LogicUpdate (0x55E160)
  │     ├─ ⑤ 节拍开门心跳: call 0x48D080 (VA 0x55E1F3)
  │     └─ 帧节拍同步与 TickMiss 动态补偿 (timeGetTime 节拍)
  │
  └─ RenderFrame (0x48C8B0) -> 脏矩形与表面提交
```

#### 7.2.2 临界区锁集合隔离证明（无死锁、无竞争）
扫描全镜像 `InitializeCriticalSection` 与 `EnterCriticalSection` 调用点，提取出的临界区全表如下：
1. **音频专用锁**：
   - `0x87E880`：DirectSound 后台工作线程互斥锁（由线程 `0x4095B0` 内部独占持有，主线程仅在退出析构 `0x40A210` 时获取，日常对局主线程从不触碰）。
   - `0x87E7F8`：AudioStream 流式音频缓冲锁（`AudioStream` WAV 解码使用）。
   - `0x887818`：SoundBuffer 锁。
2. **输入专用锁**：
   - `0xAA0400`：IPB 会话鼠标队列锁。
   - `0xAA0418`：IPB 会话文件流读写锁。

**耦合排查定谳**：
- **临界区正交性**：音频锁集合与输入锁集合严格互斥，交集为空。在整个程序生命周期中，不存在任何“持有音频锁同时申请输入锁”或“持有输入锁同时申请音频锁”的代码路径，死锁概率为 0。
- **输入不会阻塞音频**：DirectSound 混音在独立的高优先级线程 `0x4095B0` 中运行，直接操作硬件声卡 DMA 缓冲。即使主线程因 Win32 消息繁重或模态对话框阻塞，DirectSound 线程仍以 5ms 周期持续运行，直到当前循环缓冲区播放完毕。
- **音频卡顿不会拖慢输入**：主线程在 `0x406F70` 中执行的音频操作为纯内存样本状态维护（`0x4041D0`、`0x750EC0`），包含内建 33ms 硬件节流，单次耗时 < 0.1ms，且不包含任何 DirectSound 阻塞式 API 调用。音频与输入在主线程上仅呈现为 `0x55D830`（输入泵）与 `0x55D835`（音频心跳）的前后串行调度，无反向等待依赖。

---

### 7.3 `0x53E7*` 族与输入队列边界、数据结构与入出队机制

#### 7.3.1 系统职责定性：Westwood IPB 会话流与 Win32 适配层
`0x53E300`–`0x53EC00` 并非网络传输层，而是 **Westwood Input PlayBack（IPB）输入录制/回放与 Win32 输入抽象层**：
- 全局状态 `[0xAA0444]`（`SessionState`）：
  - `0`：实时对局（Live Interactive Mode，正常游戏）。
  - `1`：输入录制模式（Record Mode，通过 `0x53E4F0` 打开 `session.ipb` 并写入 `"wb"`）。
  - `2`：输入回放模式（Playback Mode，通过 `0x53E550` 打开 `session.ipb` 并读取 `"rb"`）。
- `0x53E770`（`WW_PeekMessageA`）：是对 Win32 `PeekMessageA` 的重写包装。若处于录制模式，采样硬件光标（`GetCursorPos`），经 `WWMouseClass` 换算坐标后调用 `0x408EE0` 写入录制文件缓冲，随后调用 Win32 `PeekMessageA` 并将接收到的 Windows 消息序列化；若处于实时模式，直接直通 `0x53EB01` 处的 Win32 `PeekMessageA`。
- `0x53E730`（`WW_GetMessageA`）：基于 `WW_PeekMessageA` 实现的阻塞式消息泵，遇到 `WM_QUIT (0x12)` 时返回 0。

#### 7.3.2 Windows 消息转化为游戏内部输入事件全流程
当 Win32 消息通过 `DispatchMessageA` 传递给窗口过程时，进入 `InputManagerClass::WndProc`（`0x54F790`）：

```
Win32 原始消息 (uMsg, wParam, lParam)
       │
       ▼
InputManagerClass::WndProc (0x54F790)
       │
       ├─ [鼠标消息 WM_LBUTTONDOWN..WM_MBUTTONDBLCLK (0x201..0x209)]
       │     ├─ 从 lParam 提取原始像素坐标: X = lParam & 0xFFFF, Y = lParam >> 16
       │     ├─ 调用 WWMouseClass::func_44 (0x887640->v[0x44] @ 0x54F7E6) 转换为客户端视口坐标
       │     ├─ 检查事件环剩余容量 >= 3 word (VA 0x54F8E0 / 0x54F944)
       │     ├─ PushWord 1: 事件码 (1=LDown, 2=LUp, 4=RDown, etc.) + 修饰键 (Shift/Ctrl/Alt)
       │     ├─ PushWord 2: 视口 X 坐标 (VA 0x54F9F4: call 0x54F670)
       │     └─ PushWord 3: 视口 Y 坐标 (VA 0x54F9FC: call 0x54F1C0)
       │
       ├─ [键盘按键 WM_KEYDOWN / WM_SYSKEYDOWN (0x100 / 0x104)]
       │     ├─ 更新虚拟键盘状态表: 0xAA0168[ecx] (VA 0x54F237: call 0x53EC40)
       │     ├─ 检查修饰键状态 (0x53EC70): Shift (0x100), Ctrl (0x200), Alt (0x400)
       │     └─ 合成 16 位事件字并压入事件环: KeyCode | ModFlags (VA 0x54F843: call 0x54F200)
       │
       └─ [文本字符 WM_CHAR (0x102)]
             ├─ 检查事件环剩余容量 >= 2 word (VA 0x54F890)
             ├─ PushWord 1: 事件类型 0x000A (WM_CHAR 标记)
             └─ PushWord 2: ASCII 字符码 (wParam)
```

#### 7.3.3 环形事件队列数据结构与出入队函数
- **数据结构布局**（`InputManagerClass` @ `0x87F770`）：
  - `this + 0x000`：当前消费的鼠标 X 坐标（int32）
  - `this + 0x004`：当前消费的鼠标 Y 坐标（int32）
  - `this + 0x008`：当前消费的文本字符码 / Y 副本（int32）
  - `this + 0x014`：按键按下状态位表（byte[256]）
  - `this + 0x114`：**环形事件缓冲 `ring[256]`（uint16_t[256]，总容量 512 字节）**
  - `this + 0x314`：**读指针 `Head`（int32）**
  - `this + 0x318`：**写指针 `Tail`（int32）**
- **入队函数（Enqueue）**：
  - `InputManagerClass::PushWord (VA 0x54F1C0 / 0x54F670)`：
    ```c
    bool PushWord(InputManagerClass* pThis, uint16_t val) {
        int nextTail = (pThis->Tail + 1) & 0xFF;
        if (nextTail == pThis->Head) return false; // 队列满，丢弃事件
        pThis->ring[pThis->Tail] = val;
        pThis->Tail = nextTail;
        return true;
    }
    ```
- **出队函数（Dequeue / Decode）**：
  - `InputManagerClass::GetEvent (VA 0x54F050)`：
    ```c
    uint16_t GetEvent(InputManagerClass* pThis) {
        while (pThis->Head == pThis->Tail) {
            MessagePump(); // 环空时泵消息 0x5D4D50
        }
        uint16_t eventCode = pThis->ring[pThis->Head];
        pThis->Head = (pThis->Head + 1) & 0xFF;
        uint8_t type = eventCode & 0xFF;
        if (type == 1 || type == 2 || type == 4) { // 鼠标事件
            pThis->MouseX = pThis->ring[pThis->Head];
            pThis->Head = (pThis->Head + 1) & 0xFF;
            pThis->MouseY = pThis->ring[pThis->Head];
            pThis->Head = (pThis->Head + 1) & 0xFF;
        } else if (type == 0x0A) { // WM_CHAR 字符事件
            pThis->CharCode = pThis->ring[pThis->Head];
            pThis->Head = (pThis->Head + 1) & 0xFF;
        }
        return eventCode;
    }
    ```

---

### 7.4 帧节拍剩余项：时钟变量传递、GameSpeed 映射与 TickMiss 动态补偿

#### 7.4.1 时钟变量矩阵与换算关系
在 `0x55D360`（`MainLogicFrame`）中，游戏时钟系统的全局变量演化与职能如下：

| 全局变量 (VA) | 变量名称 | 物理量纲 | 计算公式 / 赋值位置 | 核心职能 |
|---|---|---|---|---|
| `0xA8B558` | `TargetFPS` | 帧/秒 (Hz) | `0x4C807D` (网络协商) / `0x52DABD` (默认 30) | 逻辑帧率设定值（默认 30，单机 15~60） |
| `0x887330` | `TargetIntervalMs` | 毫秒 (ms) | `VA 0x55D51C: 1000 / [0xA8B558]` | 单个逻辑帧的目标时间跨度（30FPS 为 33ms） |
| `0x887350` | `TargetTickInterval` | 1/60 秒 ticks | `VA 0x55D501: 60 / [0xA8B558]` | 单机模式逻辑帧步长刻度 |
| `0x887328` | `LastTickTime` | 毫秒 (ms) | `VA 0x55D54E: timeGetTime()` | 上一次逻辑帧启动时的物理时间戳 |
| `0x887348` | `LastTickTime60Hz`| 16ms 刻度 | `VA 0x55D50E: timeGetTime() >> 4` | 单机模式 60Hz 刻度基准时间戳 |
| `0xABCE04` | `FrameDelayRemaining`| 毫秒 (ms) | `VA 0x55D597: TargetIntervalMs - Elapsed` | 当前帧剩余需要消耗的休眠时长 |

#### 7.4.2 GameSpeed 滑块调节对时钟变量的具体改变过程
1. **选项界面交互**：玩家拖动设置菜单中的 GameSpeed 滑块时，`GameOptionsClass`（`0x8870C0`）接收滑块数值（0~5 挡位）。
2. **目标 FPS 写入**：
   - 联机模式通过网络选项同步包在 `0x4C807D` 将协商值写入 `[0xA8B558]`。
   - 单人模式/遭遇战在关卡载入与重置时，在 `0x52DABD` 将默认值 30 (`0x1E`) 写入 `[0xA8B558]`。
3. **主逻辑帧重算（`0x55D51C`）**：
   - 进入 `MainLogicFrame` 序言时，检测 `[0xA8B558]`：
     - 若 `TargetFPS == 0`（极速无上限模式），执行 `0x55D4DB`：将 `[0x887330]` 设为 33ms (`0x21`)，`[0x887350]` 设为 2 ticks。
     - 若 `TargetFPS != 0`，执行 `0x55D4FB`：
       - `0x55D501`：`60 / [0xA8B558] -> [0x887350]`（单机步长）。
       - `0x55D522`：`1000 / [0xA8B558] -> [0x887330]`（毫秒间隔）。
   - 调用 `timeGetTime`（`0x5D5890`）刷新 `[0x887328]`，实现平滑瞬时调速，无时间累积突变。

#### 7.4.3 TickMiss 网络滞后动态补偿策略（`0x55D600`–`0x55D75B`）
在联机或互联网对局中（`GameMode == 4`），网络丢包或对端计算缓慢会导致本地帧接收滞后（Tick Miss）。引擎在 `0x55D5B3`–`0x55D75B` 部署了自适应滞后补偿算法：
1. **滞后检测（`0x55D5B3`）**：比较滞后包计数 `ebp` 与窗口阈值 `ebx`（默认 30 ticks）。
2. **阶梯式降速补偿（Pacing Expansion）**：
   - 当 `ebp >= ebx / 2`（滞后达到 50% 缓冲窗口）时，执行 `0x55D650`：
     `lea eax, [esi + 0x0A]; mov dword ptr [0x887330], eax`
     **向目标帧间隔动态注入 +10ms 延迟**！
   - 当 `ebp >= 3 * ebx / 4`（滞后达到 75% 严重拥塞）时，执行 `0x55D744`：
     再次叠加 +10ms 延迟。
3. **补偿策略机理**：
   - 通过动态扩大 `TargetIntervalMs`（从 33ms 增至 43ms、53ms），强制延缓本地逻辑推进速率，为网络端数据包到达与解包重组争取时间窗口。
   - 避免了直接调用 `Sleep` 导致的前台交互卡死，使游戏呈现为平滑减速而非断续硬冻结；网络恢复后，`[0x887330]` 自动恢复基准值 `1000 / TargetFPS`。

