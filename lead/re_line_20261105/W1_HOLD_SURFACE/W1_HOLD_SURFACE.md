# W1_HOLD_SURFACE · 挂起计数器 `[Scenario+0x62C]` 来源完备性普查（汇总报告）

> 汇总员：把四份节文件与四份复核意见合成对外报告。零真机、纯离线静态；全程不 commit / 不 push。
> 材料：`sections/Q1_B45B68.md`（524 行 / 34,649 B）、`sections/Q2_6579E0.md`（210 / 23,856）、
> `sections/Q3_SOURCES.md`（657 / 43,283）、`sections/Q3B_MAPS.md`（524 / 38,994）、
> `sections/_q3b_probe.py`（10,123）、`sections/_q3b_probe_out.txt`（316 / 20,513）——
> 行数与字节数为本次实跑 `wc -l -c sections/*.md TASK.md` 所得。
> 复核意见由本次 ask 正文以 JSON 给出；凡标「复核实跑」的证据均来自该材料，未由本人重跑者一律标明。

## 本报告的复核状态

| 节 | 复核状态 | 本报告处置 |
|---|---|---|
| **Q1 · `0xB45B68` 定谳** | **PARTIAL** | 主身份/字段/静态初值/5 个写点/±20 条反汇编/每帧泵均 CONFIRMED；**核心肯定结论 Q1(c)「没有任何地图脚本动作时它仍会非 0」被反证，已按复核意见降级为「静态证据不支持、无已知路径，未验」，原结论不保留**。另修正 §6.2 的 14/6 → 15/5 笔误。 |
| **Q2 · `0x6579E0` 子系统归属** | **CONFIRMED** | 主项照收；按复核修正 3 处瑕疵（`0x6579B1` 归属、`+0x14BD` 字段语义、`GameMode==0` 门限定），补入 2 项补强（Bink 直调、CRT init 归属），剔除 2 项不支撑论断的 IAT 通用检查。 |
| **Q3 · 来源完备清单** | **PARTIAL** | 闭合结论保留；补 2 项漏项（`0x53A747` 分类、`0x5BF2F9` pause 旗标），改正 4 处错误（「256 等距 0x22B」、`0x68361E` VA、dump 条数、交付元数据），移除已过时 unverified（Q1/Q3 冲突已由领队裁决），登记 §8 可复算性与交付物偏离。 |
| **Q3b · 地图全量普查** | **CONFIRMED** | 265 张全量计数照收；补写「按扩展名」口径边界（范围外 32 个文件含 `[Actions]`，`mapsmd03.mix` 内确有 2 条 kind=127）、裸 token 的段内限定、18 份 measure_w 已由复核枚举完、行号精度与结论措辞。 |

四项复核**无 REFUTED 标签**；但 Q1 被判 PARTIAL 的那一条是「肯定结论被推翻」，按铁律不保留原文。
本报告不新增任何反汇编结论：所有降级、改写、补项均以复核意见或本人本次实跑为依据，出处逐条给出。

---

## 1. 一句话结论

在 `[Scenario+0x62C]` 唯一能变非 0 的指令 `0x684174 inc [eax+0x62C]`（唯一入口 `0x684060`，全镜像**恰 4 个直接 call 点**）上，单机局 `GameMode∈{0,5}` 的静态可见来源已收敛为 **3 类脚本可达来源（动作 110 PauseGame、127 StartChronoScreenEffect、117 PlayIngameMovieAndPause，各含从属体）+ 1 个静态零 xref 的未验残余 `0x5BF2B0`**；`0x684240`/`0x684290`、主循环 `+0x35A2` 镜像链、`0x55D377` 失焦等待环都不读写该计数器；`ra2youli/` 下按扩展名纳入的 **265 张图中含 110 或 127 的图为 0 张**（动作 117 亦为 0），测量趟的 10 个 `map_sha` 前缀全部反查到物理文件且这些文件同样 0 张含 110/127，故测量语料里三条脚本入口均不存在——**但「无任何脚本动作时计数器自发非零」在本次静态证据下没有已证实来源，只能定谳为「静态无已知路径 / 未验」**；零真机、间接 CFG 与整对象拷贝边界未闭合。

依据：`sections/Q3_SOURCES.md:14-34,73-91`、`sections/Q3B_MAPS.md:13-16,129-131`、领队裁决 `lead/GOAL_THREE_TARGETS_20261018.md:5880`（§559「Q3 对、Q1 错」）与 `lead/re_line_20261105/GOAL_RE_CONTINUOUS.md:65-66`（A13/A14）。

---

## 2. Q1 · `0xB45B68` 定谳

### 2.1 已定谳（复核 CONFIRMED，本人本次亦复算）

`0xB45B68` 是全局对象 `0xB45B58`——一个 `DynamicVectorClass<影片播放器*>`——的 **`Count`（元素个数，dword @ +0x10）**，不是「布尔沿计数器」。`0x6579FD setg bl` 把 `Count>0` 折成布尔沿，领队 §2.2 看到的「沿」是**派生量**（`sections/Q1_B45B68.md:13-17`；复核意见 Q1「确认无误的部分」）。

- **字段布局**：`0x759180` CRT 静态初始化器在 `0x75919D` 写 vptr `0x7F6984`、`0x7591A7` 写 `CapacityIncrement=0xA`、`0x7591B1` 写 `Count=0`；字段与 `YRpp/ArrayClasses.h:183-186,338-339` 逐项落位（`Q1_B45B68.md:46-80`）。本人本次读缓存流复核 `u32(0x815728)=0x759180`。
- **静态初值 0 双证**：`.data` VA `0x812000..0xB79BE4`、rawsz `0x6C000`，`0xB45B68−0x812000=0x333B68 ≥ 0x6C000` ⇒ 属 PE 零填充 BSS（无文件字节）；CRT init 再显式写 0（`Q1_B45B68.md:140-151`；复核 Q1「静态初值 0 双证成立」）。
- **引用全集**：`disp_hits(0xB45B68)` = **23 处 / 5 W / 18 R**，`.text` 原始 `disp32 = 68 5B B4 00` 亦恰 23 处，一一对应（复核 Q1 实跑；本人本次用 `P01/stream_cache.pkl` 独立筛出 23 处、W 恰 `0x5BF341 / 0x5BF43B / 0x5BF487 / 0x657B67 / 0x7591B1`）。
  ⇒ **对领队 `TASK.md:41`「写点 3 个」的更正成立**：局内非 CRT 写点是 3 个，全镜像写点是 5 个；多出的 `0x657B67`（`dec` 后写回 = 影片播完 Count--）与 `0x7591B1`（CRT 初始化写 0）。
- **每帧泵**：`0x48D091 mov eax,[0xB45B68]` → `test/jle` → `Items[0]` → `0x48D0A7 call [edx+8]`；`0x55D835`（冻结体）与 `0x55DE4A`（正常体）都调 `0x48D080`，故冻结帧也泵影片（`Q1_B45B68.md:299-400`）。本人本次复核 `0x48D080` 的入边总数 **170 = 169×E8 call + 1×E9 jmp**，与 `docs/re/audio_input_hotspots.md:72/:404` 及复核 Q1 一致。
- **±20 条反汇编**：重同步解码 `0x48D000..0x48D200` 得 `insns=185, fails=0`，`index(0x48D091)=52`（复核 Q1 实跑）。**按复核意见修正 `Q1_B45B68.md:323-325` 的计数笔误**：前 20 条里属上一函数尾（6 条：`0x48D06A call` / `06F test` / `071 jg` / `073 mov` / `075 pop` / `076 ret`）加 9 条 `0x90` NOP 共 **15 条**，属 `0x48D080` 序言的是 **5 条**（`push ebp / mov ebp,esp / and esp,0xfffffff8 / sub esp,0x100 / call 0x406f70`）；原文「14 条 / 6 条」应为 **15 / 5**。本人本次逐条打印该 20 条，得 `after_ret_start_idx=5, nops=9, prologue=5`，与复核一致。不影响语义判断：`0x48D091` 是每帧影片心跳门，不是挂起计数器本身的门。

### 2.2 ★ Q1(c) 已降级（复核 PARTIAL，原肯定结论不保留）

**原节文件结论**（`Q1_B45B68.md:19-23,250-260`）称「**会**：引擎片头 INTRO / 简报 / VQA / 胜败影片直接调 `0x5BF260` 或 `0x5BF390` 令 `Count++`，无需任何 `[Actions]` 段。**本报告不保留该结论**，改为：

> **静态证据下无已知路径，未验。** 既有静态证据不能证明「不经任何地图脚本动作 `0xB45B68` 会非 0」；同样也不能证明「运行时绝对不可能非 0」。

反证与边界（复核 Q1 实跑 ①②③ + 本人本次缓存流复核）：

1. `0x5BF260` 确实有 12 个直接 call 点，其中 10 个是引擎内部影片路径（含 `0x53933E` 的 `ecx=0x8263A8` = `"INTRO"`，以及 Intro/Basic/Brief/LOADING/`%s.VQA`/`D:\ra2mdpost\Scenario.CPP` 串邻域），**但函数体 `0x5BF260..0x5BF2A2` 只调 `0x5BED40`**（`0x5BF296 call 0x5bed40`），`ret 0xC`。本人本次打印该函数全部 19 条指令，除 `call 0x5BED40` 外无任何 `0xB45B68` 写。
2. `0x5BED40` 链不写 Count：复核实跑 `resync(0x5BED40,0x5BF2A2)` → `insns=374 fails=0`，全链 `disp32(0xB45B68)=0`、对 `0x5BF2B0/0x5BF390` 无 E8/E9 目标；从 `0x5BF260` 按「解码到第一个 ret」的传递闭包深度 ≤12 得 **251 节点**，`contains 0x5BF2B0 / 0x5BF390 / 0x5BF341 / 0x5BF43B = False`，闭包内向量字段引用数 = 0。本人本次独立扫 `[0x5BED40,0x5BF260)` **354 条缓存指令**：`0xB45B68` 引用 0、`0x62C` 引用 0、对 `0x5BF2B0/0x5BF390/0x684060/0x684180` 的调用 0；该窗口内确实含 `0x5BEDEC call 0x432690` 与 `0x5BEE58 call 0x432C70`（全屏 Bink 链）。
3. **全镜像仅两处 `inc→写回` 能把 Count 从 0 变正**：`0x5BF341`（`0x5BF2B0` 内）与 `0x5BF43B`（`0x5BF390` 内）。`Q1_B45B68.md:206` 的 J1 本身正确，与 §0/§5.2 的「`0x5BF260` 令 Count++」自相矛盾；`Q1_B45B68.md:134` 亦已自认「`0x5BF260` 走的是另一条链」。
   - `0x5BF390` 的 4 个直接 call 点全是脚本动作或 ACTION_FUNC slave：`0x6DF54E`(100) / `0x6DF916`(117) / `0x6E1728` / `0x6E1748`（本人本次复算一致）。
   - `0x5BF2B0` **静态零 xref**：本人本次 `callers(0x5BF2B0)=0`、全文件原始 LE dword `0x5BF2B0/0x5BF390/0x5BF341/0x5BF43B/0x539320/0x6579E0` 计数均为 **0**；复核另查动作跳表 `0x6DFDEC` 与向量 vtable `0x7F6984`（8 槽）均不含这些地址。`Q1_B45B68.md:132-136` 自己已写「`0x5BF341` 静态证据下无法证明会被执行」。
4. ⇒ 原 (c) 依赖的正是这个不可达写点或未经求解的间接调用，而复核已把「全文件 dword 指针 / 动作跳表 / vtable / 59 条向量字段引用位置」全部扫过、未发现间接入口。**结论降为「静态未验 / 无已知路径」**；受限于零真机与未做间接 CFG/虚表间接调用求解，不得改写成「运行时绝无可能」。
5. 领队已亲自裁决这处冲突：`lead/GOAL_THREE_TARGETS_20261018.md:5880` §559「`0x5BF260` 不写 `0xB45B68`，**Q3 对、Q1 错**」；`lead/re_line_20261105/GOAL_RE_CONTINUOUS.md:66` A14 同。Q3 原「unverified：冲突未由 Q1 作者确认」已过时，见 §6。

### 2.3 未改动的部分

`0x5BF260..0x5BF5BF` 九个函数边界与身份、`0x5BF450 ClearAll` 的 6 个清场调用点、`0x5BF500 PumpHead` 的 5 个调用点、`0x48D0AA` 起的 GameMode 3/4 联机保活段，均按 `Q1_B45B68.md:108-137` 照收（复核 Q1「确认无误的部分」逐字节复现）。元素确切 C++ 类名、`0x7F6984` 各虚槽定名、`0x653446` 宿主归属（Q2 已定 RadarClass）属推导/未验，进 §6。

---

## 3. Q2 · `0x6579E0` 子系统归属

### 3.1 定谳（复核 CONFIRMED）

`0x6579E0..0x657CDB`（`0x657CDB ret`）是 **HUD/侧边栏—雷达小地图渲染子系统（`RadarClass` 一族）的每帧影片队列显示状态机**，不是输入/网络/AI 层；它消费全局 `0xB45B58` 影片队列，把「队列非空 ∧ 当前项 `pause=1`」的沿翻译成 `0x684060(0)` 挂起 / `0x684180()` 释放，因此是**玩家可见的侧边栏影片显示接管**（`sections/Q2_6579E0.md:6-8,131,150-152`）。

- **唯一调用者链**（复核 Q2 实跑；本人本次复算 `callers(0x6579E0)=1 ['0x653446']`、`u32(0x7F0384)=0x653100`）：
  `0x6D0E38 → 0x6A6C30 → 0x6A6FFC → 0x63FB20 → 0x63FDAC → 0x653100 (RadarClass::v[16]) → 0x653446 → 0x6579E0`（`Q2_6579E0.md:89-114`；`docs/re/radar_minimap_dots.md:23-40`）。
- **关键字节链**（本人本次逐址复核）：`0x6579E3 mov edx,[0xB45B68]` → `0x6579FB test edx,edx` → `0x6579FD setg bl`；`0x657B24 call [edx+0x14]` → `0x657B2D mov [esp+0x12],al`（still_playing）；`0x657B31 mov dl,[ecx+4]` → `0x657B34 mov [esp+0x13],dl`（**pause 旗标**）；`0x657B64 dec ecx` → `0x657B67 mov [0xB45B68],ecx`（Count--/移位）；沿块 `0x657C8B test dl,dl` / `0x657C8D sete dl` / `0x657C90 cmp cl,al` / `0x657C92 mov [esi+0x14bd],dl` / `0x657C98 je 0x657CD4` / `0x657C9A test al,al` / `0x657C9C je 0x657CC8` / `0x657CA0 call 0x684060` / `0x657CC8 call 0x684180`。
  全镜像 `call 0x684060 = 4 {0x53B612, 0x657CA0, 0x6DF703, 0x6E4086}`、`call 0x684180 = 3 {0x53B6E6, 0x55D81C, 0x657CC8}`（本人本次复算一致，与 `P01/VERIFY.md:58` 对齐）。
- **不是凭字符串猜**：`"Radar: Movie done.\n"` / `"Radar: Next movie.\n"` / `"Radar: Movie full redrawn\n"` 三串及唯一 push 点 `0x657C05/0x657BA4/0x657AA6`（复核 Q2 实跑）。
- **与动作族的关系**：动作 **117** `0x6DF916 mov dl,1; call 0x5BF390` 与从属 `0x6E1748` 入队 `pause=1`，**直接同链**；动作 **100** `0x6DF54E xor dl,dl; call 0x5BF390` 同队列但不暂停；动作 **10** `0x6DE755 call 0x5BF260` 是并行的全屏 Bink 族，不写 `0xB45B68`；动作 **110/127** 直调 `0x684060` / 渐变启动器，不经本对象（`Q2_6579E0.md:137-153,175-195`）。
- **对领队表述的证据修正**（复核 Q2 确认成立）：`LEADER_PRECHECK_20261105.md:53`「不经 TActionClass 派发」只对 `0x6579E0` **本身**成立（唯一 call 点在雷达绘制函数里）；对整条链不成立——`0x6DF916 → 0x5BF390 → 0xB45B68 → 0x6579E0` 字节链使 117 脚本可达。`TASK.md:29`/领队 `:73` 的「无脚本入口」推论据此作废。
- **六个提示库函数分层**（`Q2_6579E0.md:158-171`，复核 Q2 全部复跑）：`0x752370 / 0x752480 / 0x753570 / 0x7529E0` = EVA/Vox **音频层**；`0x70F120` = **渲染/UI**（TalkBubble/Reveal）；`0x6F1F70` = **队伍对象查询**（AI 数据侧）；无网络层、无输入层。`0x6579E0` 本体内直接调用的只有 `0x7529E0`。

### 3.2 按复核意见修正的瑕疵与补强

1. **`0x6579B1` 归属**（复核 Q2「内部不一致」）：`Q2_6579E0.md:36` 把 `0x6579B1 mov ecx,[esi+0x14D4]` 列进「本函数用法」并归到 `+0x14D4`。本人本次实读 `0x6579AC call 0x752370`、`0x6579B1 mov ecx,[esi+0x14d4]`、`0x6579BB call 0x752480`、`0x6579C0 call 0x753570` 全部 `< 0x6579E0`，属紧邻函数 `0x6578F0`；`Q2_6579E0.md:160` 亦自认 0x752480 在 `0x6578F0` 内被调。⇒ 本报告把 `+0x14D4 / 0x752480` 记为**邻函数用法**，不列为本函数用法。
2. **`+0x14BD` 字段语义**（复核 Q2「字段标注错」）：`Q2_6579E0.md:48` 注释「上帧 pause 状态」、`:71`「保存新 pause 状态」**不成立**。按字节：`dl` 来自 `0x657B2D mov [esp+0x12],al`（vtable+0x14 的 still_playing），`0x657C8B test dl,dl` → `0x657C8D sete dl` ⇒ **写入 `+0x14BD` 的是 `!still_playing`（影片播完标志）**；pause 旗标在 `al=[esp+0x13]`（来自 `0x657B31 mov dl,[ecx+4]`），挂起沿由 `0x657C90 cmp cl,al`（`+0x14BC` latch vs pause flag）决定。沿判定结论不受影响。
3. **`GameMode==0` 门限定**（复核 Q2「条件省略」）：本人本次复核 `0x5BF3B0 mov eax,[0xa8b238]` / `0x5BF3B5 test eax,eax` / `0x5BF3B7 jne 0x5bf44a`。⇒ 动作 100/117 的入队**仅在 Campaign(0) 生效**；`Q2_6579E0.md:146`「117 的 pause=1 会在下一绘制帧触发 `0x684060(0)`」须加此限定，Skirmish(5) 局该来源不成立（`Q3_SOURCES.md:234-236` 同）。
4. **跳表索引**（复核 Q2「口径」）：`0x65338B dec eax` 在 `0x653395 jmp [eax*4+0x653734]` 之前，实为 `(state−1)` 索引；表值 `{0x6534EA, 0x65339C, 0x653444, 0x6534EA}` 数值正确，结论不受影响（本人本次逐址复核）。
5. **`+0x11E4` 头文件锚**：复核指出 `YRpp/RadarClass.h:42` 是 `unknown_11E8`，头文件无 `+0x11E4` 字段；`Q2_6579E0.md:31` 的精确对应不成立，本报告只保留「雷达显示坐标/矩形族」的近似字段族表述。
6. **Bink 链补强**（复核 Q2「实质补强」，本人本次复核）：`0x5BED40` 的直接 callee 中 `0x5BEE58 call 0x432C70` 正落在 `docs/NEXT_RE_AND_MODERNIZATION.md:51,72` 定名的 `BinkMovieClass::Play (0x432C70–0x432E39)`；`CALLERS 0x432C70 = {0x5BEE58, 0x5C0559}`；另有 `0x5BEDEC call 0x432690`。⇒「动作 10 是另一条全屏 Bink 影片链」比原 §4.1 点 5 更稳固，非缺陷。
7. **`0x7591B1` 归属**：复核 Q2 确认它是 `0x759180` CRT 构造块（同块设 `0x7F6984` vtable 与容量 `0xA`）中的 `Count=0` 初始化写，不是「未追到运行期触发者的队列清理/初始化邻域」；`Q2_6579E0.md:154` 该表述已按 §2.1 更正。
8. **IAT 项剔除**：复核实跑 `IAT_USER32_REFS_IN_0x6579E0 []`、`IAT_USER32_REFS_IN_0x653100 []`，`SendMessageA/GetDlgItem`（slot `0x7E14A4/0x7E14A8`）只是探针通用检查，**不支撑任何 Q2 论断**，本报告不作为证据项。

---

## 4. Q3 · 来源完备清单

**写点完备性**（`Q3_SOURCES.md:88-91`；本人本次缓存流独立得内存 `[reg+0x62C]` 访存 **18 处 / W 7**）：挂到 `[0xA8B230]` Scenario 的写点恰 3 处——`0x6836D2`（复位 0）、`0x684174 inc`、`0x684195 dec 后写回`。**除 `0x684174` 外，静态可见指令没有一条能把 `+0x62C` 从 0 变非 0**，故「完备」= 把 `0x684060` 的 4 个 call 点全部展开。冻结门 `0x55D826 mov ecx,[eax+0x62c]` / `0x55D82E je 0x55d878` 只读该 dword（本人本次逐址复核）。

| # | 来源 | 触发条件 | 脚本可达? | 证据 |
|---|---|---|---|---|
| S1 | **动作 110 PauseGame** 内联 `0x6DF703 → 0x684060` | 地图 `[Actions]` 含 kind 110、`Value`=时长秒；**时长≠0 且 `[Scenario+0x630]` 已武装时 `0x6840A9 jne 0x68417A` 早退、不 inc**；时长=0 必 inc | **✔** | `call 0x684060 = 4 {0x53B612,0x657CA0,0x6DF703,0x6E4086}`（本人复算）；`0x684066 test esi,esi` / `0x6840A1 mov cl,[eax+0x630]` / `0x6840A9 jne` / `0x684174 inc`（本人逐址）；`action_dispatch_table.tsv` kind `0x6E` span `006DF6FD..006DF717`（`Q3_SOURCES.md:75,110-143`） |
| S2 | 110 从属体 `PauseScenarioFor 0x6E4080/0x6E4086` | 同 S1，按 YRpp/manifest 从属体口径 | **✔（采信，运行时调用者未验）** | `YRpp/TActionClass.h:238`；`.data:0x872E78 → 0x6E4080`；全镜像 E8 直接调用者 0（`Q3_SOURCES.md:76,281-297`） |
| S3 | **动作 127 StartChronoScreenEffect** `0x6DFAC5 → 0x53B460 → 0x53B560(state2) → 0x53B612 → 0x684060(0)` | 含 kind 127、`Value`=渐变刻数 >0；`[0xA9FAB0]=1` 由 `0x53B4F7` 写入，state2→3 由 `0x55D83A`（冻结体）每帧推进 | **✔**（执行时机引擎内部不可控） | `call 0x53B460 = 2 {0x6DFAC5,0x6E2F96}`、`call 0x53B560 = 2 {0x53A747,0x55D83A}`、`call 0x53B612` → `0x684060`、`0x53B6E6` → `0x684180`（本人复算）；`Q3_SOURCES.md:77,145-154` |
| S4 | 127 从属体 `SetChronoScreenEffectState 0x6E2F90/0x6E2F96` | 同 S3；调用者 `0x6DFDC4` | **✔（采信，运行时调用者未验）** | `YRpp/TActionClass.h:198`；`Q3_SOURCES.md:78` |
| S5 ★ | **动作 117 PlayIngameMovieAndPause** `0x6DF916 → 0x5BF390(dl=1) → 0x5BF43B Count++ → 0x6579E0 → 0x657CA0 → 0x684060(0)`（基线漏项） | 含 kind 117、影片 id 合法、**`GameMode==0`（战役）**；队列项 `pause=1`；沿在雷达每帧绘制里判定 | **✔（间接）** | `call 0x5BF390 = 4 {0x6DF54E,0x6DF916,0x6E1728,0x6E1748}`（本人复算）；`0x5BF3B0..B7` GameMode 门、`0x5BF3F4 mov [esi+4],bl`、`0x5BF43A/43B`（本人逐址）；`0x657CA0 call 0x684060`（`Q3_SOURCES.md:79,194-236`） |
| S6 | 117 从属体 `PlayMovieInSidebarPauseGame 0x6E1740/0x6E1748` | 同 S5 | **✔（采信，运行时调用者未验）** | `YRpp/TActionClass.h:126`；`Q3_SOURCES.md:80` |
| S7 | **引擎内部非脚本入队残余 `0x5BF2B0`** | `0x5BF340 inc ecx → 0x5BF341 mov [0xB45B68],ecx`；`0x5BF2F9 mov [esi+4],bl` 同时写播放项 pause 旗标（`bl` 来自入口 `dl`）；`0x5BF2B0..BB` 亦要求 `GameMode==0` | **✘（未证：静态零 xref）** | 本人：`callers(0x5BF2B0)=0`、全文件原始 LE dword 计数 0、该窗口 `[0x5BF2B0,0x5BF352)` 内 0 个外来分支目标；复核 Q3「漏项·残余入口」另加固 `[0x5BF2B0,0x5BF353)` 外来分支 0、原始 dword 0；复核 Q1：不在 `0x6DFDEC` 动作表、不在 `0x7F6984` vtable。**若可达且 `dl=1`，它是一条完整的非脚本入队链（Count++ 且带 pause 旗标）**，不只是「Count 写点之一」；可达性未做间接 CFG 求解 ⇒ 进 §6 |
| S8 | 引擎内部影片路径：`0x5BF260` 的 10 个非动作调用者（`0x53933E "INTRO"`、`0x683CBD/DB6` Intro/Brief、`0x6859xx` 胜败影片、`0x686073`、`0x6E992A/DED3`） | 片头/简报/VQA/胜败结算等；`0x5BF260` 只 `call 0x5BED40`，全屏 Bink 链 `0x432690/0x432C70` | **✘（反证：不是来源）** | 本人：`0x5BF260` 全 19 条指令唯一 `call 0x5BED40`；`[0x5BED40,0x5BF260)` 354 条内 `0xB45B68`/`0x62C` 引用 0、对 `0x5BF2B0/0x5BF390/0x684060/0x684180` 调用 0；复核 Q1 374 条 `fails=0` + 251 节点闭包；领队 `GOAL_THREE_TARGETS_20261018.md:5887-5899` 裁决「Q3 对、Q1 错」；`Q3_SOURCES.md:267-279` |
| S9 | 渐变机每帧推进 `0x53A747`（在 `0x53A6C0` 内，唯一调用者 `0x55B5C8`）**（复核补漏项）** | 与脚本无关、主循环侧每帧推进渐变状态机；但 `[0xA9FAB0]` 全镜像唯一写 `state=1` 的 `0x53B4F7` 位于 `0x53B460` 内，而 `0x53B460` 调用者恰 `{0x6DFAC5, 0x6E2F96}`；跳表 4 case 中 state2 分支才含 `0x53B612 call 0x684060` | **✘（不是独立新来源；仍须 127/slave 武装）** | 本人：`0x53A747 call 0x53b560`、`0x55B5C8 call 0x53a6c0`、`0x53B4F7 mov [0xa9fab0],1`、`0x53B612 call 0x684060`；复核 Q3 probe7/probe2 给出 `[0xA9FAB0]` 全镜像 W 恰 6 点。原 `Q3_SOURCES.md:77` 主表只写 `0x55D83A`，漏标此点，本报告补入，闭合结论不变 |
| S10 | 动作 **100 PlayIngameMovie** / **10 PlayMovie** | 100：`dl=0` → `0x657C9C je 0x657CC8` 走释放侧，`0x68418E je 0x684239` 在 counter==0 直退；10：`0x6DE755 → 0x5BF260` 全屏链，不写 Count | ✔（动作本身）/ **✘（不产生 +1）** | `Q3_SOURCES.md:156-192,230-232,450-451`；复核 Q3 对 146 行 `action_dispatch_table.tsv` 全表扫描无第 5 个动作块漏项 |
| S11 | `0x684240`（7 call 点）/ `0x684290`（4 call 点） | 只改 `[+0x35A2]` / `[0xA8ED9C]` / `[0xB07784]`，**不加不减不读 `+0x62C`**；对 `0x55D877` 冻结出口无间接影响 | 部分 ✔（46/47/1/2/67/68/43/127 等） | 本人：`call 0x684240 = 7`、`call 0x684290 = 4`；`Q3_SOURCES.md:301-352` 全函数 dump 与 `+0x62C` 扫描 0 命中；复核 Q3 `probe4_out:5-18`「any +0x62C access inside any action block = 空」 |
| S12 | 释放侧 / 复位 / 三链分离（**非来源**，列出以闭合写点全集） | `0x684180` 3 call 点 → `0x684195 dec`；`0x6836D2` 写 0；链 B `0x48CE67 mov cl,[eax+0x35a2]` → `0x48CE73 mov [0xa8ed9c],cl`；链 C `0x55D377 mov al,[0xa8ed80]` | —（非来源） | 本人逐址复核 `0x48CE62..8A`、`0x55D7C2..82E`、`0x6836D2`、`0x684195`；复核 Q3「三链分离：确认无误」；`Q3_SOURCES.md:356-445` |
| S13 | 其它「看似来源但不是」 | 4 个非 Scenario 的 `[reg+0x62C]` W（`0x665EDE/0x671836/0x71106E/0x71463F`）、动作 46/47/1/2/67/68/43、MLF PauseTimer、`[0xA8ED9C]`/`[+0x35A2]` 为 1、读档反序列化、`rep movsd`/指针副本间接写 | — | `P01/VERIFY.md:49`；本人缓存流得 18 处 `0x62C` 访存、W 7；`Q3_SOURCES.md:448-463,498-515`（**后两项仍未闭合，见 §6**） |

### 4.1 按复核意见改正的 Q3 数字 / VA / 范围 / 元数据

| 项 | 原节文件 | 本报告更正 | 依据 |
|---|---|---|---|
| `0x872A7C` 表间距 | `Q3_SOURCES.md:285,504,610`「256 个**等距** `0x22B`」 | **256 项、distinct 256、zero=0、间距 550–555**；`0x22B=555` 仅 **33/255** 个间距恰为它，222 个不等（min `0x226`=550，max `0x22B`=555）。不影响「消费方 count 0」结论 | 本人本次实算 `u32` 表：`min 550 / max 555 / Counter{555:33,554:50,553:51,552:51,551:51,550:19} / n_exact_0x22B 33`；复核 Q3 `probe6_out:136-142` |
| `+0x35A2` 场景复位写者 | `Q3_SOURCES.md:396` 列为 `0x68361E` | **`0x6839CE mov byte [ebp+0x35a2], bl`**；`0x68361E` 实为 `lea ecx,[esp+0x18]`，相差 `0x3B0` | 本人本次逐址复核两条指令；复核 Q3 `probe6_out:162,173` |
| `0x5BED40` dump 条数 | `Q3_SOURCES.md:178-181`「`0x5BED40..0x5BF178` 完整 dump，约 130 条」 | 该区间 **291 条**；`[0x5BED40,0x5BF260)` **354 条**；且漏掉 `0x5BF189 call 0x5C07D0` 等 ⇒「完整 dump」不成立。但复核另扫更宽窗口得 `artifact hits 0`，本人对 354 条亦得 0 命中 ⇒「动作 10 不进 `0x684060`」在 Q3 自述的「直接调用图 + 已 dump 函数体」口径下仍成立 | 本人本次缓存流计数 291 / 354 / 374；复核 Q3 `probe2_out:670-671,674`、`probe7_out:205` |
| 交付元数据 | 结论 evidence「657 行 / ~31.7 KB」 | 657 行正确；真实 **43,283 B ≈ 42.27 KiB**，31,750 是 **字符数**被误标成 KB（低估约 25%） | 本次 `wc -l -c`；复核 Q3 `probe3_out:236-239` |
| Q1/Q3 冲突状态 | `Q3_SOURCES.md` 结论 `unverified[1]`「未由 Q1 作者确认」 | **已裁决：Q3 对、Q1 错**，非开放项 | `lead/GOAL_THREE_TARGETS_20261018.md:5880,5887`、`lead/re_line_20261105/GOAL_RE_CONTINUOUS.md:66`；本人本次实读 |
| 表命名 | 把 `0x872A7C` 称作「ACTION_FUNC 指针表」 | 与真实 `Execute` 跳表 `0x6DFDEC` 区分：本人实读 `0x6DFDEC` 头四项 `0x6DEA37/0x6DEA67/0x6DEA97/0x6DEB57`，`0x872A7C` 头四项 `0x6C1A07/0x6C1C32/0x6C1E5D/0x6C2088`，**是两张不同的表**；「0 条引用指令」判断成立但标签易混淆 | `docs/re/trigger_system_manifest.md:284`；复核 Q3 `probe5_out:247-248`；本人实读 |
| 可复算性 / 交付物 | `Q3_SOURCES.md:595-599,634-637` 为只有注释的 `<<'PY'` 占位块；§8-B/§8-D 为散文摘要 | 5 个「实跑命令」小节中 **4 个不可直接复跑**，与 `TASK.md:111`「每个数字都要能追到实跑命令 + 输出」有落差；`TASK.md:87-91` 要求的 `W1_HOLD_SURFACE.md` + `_w1_probe.py` + `_w1_probe_out.txt` 在节文件写作时均不存在（本人本次实查 `sections/` 只有 4 份 md + `_q3b_probe.py/_q3b_probe_out.txt`）。属工作流分片造成的范围偏离，登记不补造 | 复核 Q3；本人本次 `git status --short` 与目录列举 |

### 4.2 三链分离（任务书 `TASK.md:68-70` 特别要求，复核确认「无混为一谈」）

- **链 A（冻结出口）** `0x55D7C2..0x55D877`：门 = `GameMode∈{0,5}` ∧ `[Scenario+0x62C]≠0`，`0x55D826 mov ecx,[eax+0x62c]` / `0x55D82E je 0x55d878`（本人逐址复核）。
- **链 B（主循环镜像）** `0x48CE62..0x48CE8A`：`0x48CE67 mov cl,[eax+0x35a2]` → `0x48CE73 mov [0xa8ed9c],cl` → `0x48CE8A call 0x55d360`（本人逐址复核）。是单向刷新，`[0xA8ED9C]==1` ≠ `+0x62C≠0`。
- **链 C（失焦等待环）** `0x55D360..0x55D3BB`：读 `[0xA8ED80]`，写 `[0xABCD58]` 闩锁，Sleep(500)+泵，不碰 `+0x62C`。
- `0x684240/0x684290` 只影响链 B 的表现变量；`0x55DE8F`（正常体尾部）在 `0x55D878` 之后，冻结体整体跳过 ⇒ 不可能回喂链 A。复核 Q3 `probe5_out:254-261` 得 `+0x35A2` 在冻结段内访问 0、`[0xA8ED9C]` 在 MLF/主循环判定段内 R 为 `[]`、`[0xA8ED80]` 唯一 W `0x7778CE`。

---

## 5. Q3b · 地图全量普查表

### 5.1 口径与汇总（复核 CONFIRMED，本人本次独立复算）

- **分母 265 = 按 `TASK.md:74` 授权的扩展名全量**：`.yrm` 224 / `.map`（含 `.MAP`）3 / `.mmx` 38。本人本次 `os.walk('ra2youli')` 得 in-scope 文件 **265**，与 TSV 的 265 个 relpath 集合一致；复核 Q3b 以独立脚本枚举亦得 265 且 `set equal True`。
- `[Actions]` 布局：行首 `COUNT`、`1 + COUNT*8` token（`ra2forge/triggers.py:19-20`、`ra2forge/maplib.py:463-472`；实读 `ra2youli/[2]0LoadBench_U0400.yrm:401-404`）。**154 张有段 / 111 张无；1,261 条记录 / 5,309 条动作 / 34 种 kind / 0 畸形记录；`[Actions]` 段值内裸 `110`/`127` token = 0**（`sections/_q3b_probe_out.txt:4-17`）。
- 本人本次对 `sections/Q3B_MAPS.md` §5 表逐行校验：**265 行、265 个互异文件名、`sum n_rec=1261`、`sum n_actions=5309`、有段 154 行、`110!=否` 的行 0、`127!=否` 的行 0**；对 `_q3b_probe_out.txt:15` 的全局直方图求值得 `sum=5309 / distinct=34`，且 `110`、`127`、`117` 三个键均不存在。
- **本人本次实跑复算命令**：`cd /d/Project/ra2-campaign-forge && python -I -X utf8 D:/Project/ra2-campaign-forge/lead/re_line_20261105/W1_HOLD_SURFACE/sections/_q3b_probe.py > D:/Project/ra2-campaign-forge/.tmp/w1_final_verify/q3b_rerun.txt 2>&1` → `EXIT=0`，与 `sections/_q3b_probe_out.txt` `diff -q` 无差异（`DIFF=identical`），`316 行 / 20,513 B`。

### 5.2 必须随表一起读的边界（复核 Q3b 补强，本人本次核实）

1. **「0 张」只对这 265 张按扩展名的图成立，不是「整个 `ra2youli/` 目录任何文件都没有 127」。** 本人本次枚举范围外文件：含 `[Actions]` 的共 **32 个**（`.mpr` 20 / `.mix` 7 / `.bak` 4 / `.old-pre-migrate` 1，与复核一致）；其中 **`mapsmd03.mix` 内确有 2 条货真价实的 kind=127 动作**（8-token 组首 token，本人本次解析得 2 条，样例 `0A8E0E9C=6,47,…,127,0,40,…` 与 `0951A8BC=3,54,…,127,0,40,…`），另有参数位 110 出现在 `mapsmd03.mix` / `maps02.mix`。`Q3B_MAPS.md:207-210,523` 只声明 `.bak/.mix/.sav` 不在范围、未点名 `.mpr`、也未点明被排除的 `.mix` 中确实有 127 ⇒ 本报告补写此边界。
2. **「裸 110·127 token = 0」必须按 `[Actions]` 段值读**（`Q3B_MAPS.md:46-47` 已限定）。复核 Q3b 全文件扫描发现 265 张图其它段（`[Structures]/[Units]/[Terrain]` 坐标等）共 611 个裸 110/127 token；本人本次以不同切段/正则口径亦在 263 个文件内见到非 `[Actions]` 段的裸 token（计数 1835，与复核的 611 **口径不同、不可直接比较**）。这些是坐标不是动作，不改变结论，但两个数字都不作为本报告结论值。
3. **领队抽查 8 张对齐**（`Q3B_MAPS.md:53-93`）：`U0400={2,4,9}`、`ECH={(1,11)}` 等是 **`COUNT` 直方图不是 kind**；真实 kind 为 `U0400={99:15}`，ECH01/02/03 分别 7/8/8 种。口径错误不改变「无 110/127」实质结论（`LEADER_PRECHECK_20261105.md:65` 仍成立）。
4. **测量趟 10 个 `map_sha` 前缀全部 FOUND**（`_q3b_probe_out.txt:302-311`；复核 Q3b 独立重写 sha 反查得 FOUND=10/MISSING=0，并对 10 个 sha 的全部 75 份同哈希副本逐份跑 `[Actions]`，含 110/127 的副本 0）。`MEASUREMENT SHAS PRESENT UNDER ra2youli/? matches = 0`（`:313-314`）。措辞精修：10 个前缀均指向 `XMP29U2.MAP` spawnfix 族**同哈希物理实例**；`e3acc130` 首选 `_maps_fixed\XMP29U2.MAP.u0050_2013a100`，`93c2974b` 的 27 份副本含 `[2]0LoadBench_U0400.yrm`，不宜概括成「全部是 `XMP29U2.MAP`」（`Q3B_MAPS.md:152-164` 表格本身准确）。
5. **120 份 `XVERIFY_H8` 的 `map_sha256` 是占位串** ⇒ 写「找不到对应物理文件」；原 `Q3B_MAPS.md:201,520` 的「另 18 份未逐一枚举：未验」已由复核 Q3b 枚举完（12 份 `lead/qc161_u0400_trip/{l1c,l1d,l1e,l3}_20261021`、3 份 `lead/t55k_20261020`、3 份 `XVERIFY_V3_20261101/mock_trip_*`），**不引入新 sha、不产生新的「找不到」**，`10/10 FOUND` 不受影响。
6. `map_sha256` 只是 argv 回显、**不证明实载**（`GOAL_THREE_TARGETS_20261018.md:260` 的 F-4 记载回显曾与实载不符）；本表证明的是「该哈希对应磁盘上哪个文件」。
7. 行号精度：探针 TSV **表头在 `_q3b_probe_out.txt:20`、数据行 21–285**；`Q3B_MAPS.md` **§5 标题在 :220、数据行 229–493**（本人本次数得 265 个编号行）。原引用把表头/标题含进范围，属引用不精确而非数字错误。

### 5.3 逐图全量表（265 行）

列：`文件名`（`ra2youli/` 下相对路径）/ `n_actions`（展开后的动作条数）/ `kind 直方图`（真实动作 kind）/ `含110?` / `含127?`。
265 行中后两列**全部为「否」**；可机读原始版本见 `sections/_q3b_probe_out.txt:20-285`（另含 `count_hist` 列可复核领队口径）。

| 文件名 | n_actions | kind 直方图 | 含110? | 含127? |
|---|---:|---|---|---|
| Arena.mmx | 12 | `{99:10, 108:2}` | 否 | 否 |
| BayOPigs.mmx | 0 | `{}` | 否 | 否 |
| Bermuda.mmx | 45 | `{53:4, 54:8, 99:30, 102:3}` | 否 | 否 |
| Break.mmx | 22 | `{99:22}` | 否 | 否 |
| Carville.mmx | 5 | `{99:5}` | 否 | 否 |
| Deadman.mmx | 28 | `{99:28}` | 否 | 否 |
| Death.mmx | 8 | `{99:8}` | 否 | 否 |
| Disaster.mmx | 55 | `{99:55}` | 否 | 否 |
| Dustbowl.mmx | 25 | `{99:25}` | 否 | 否 |
| EB1.mmx | 11 | `{99:11}` | 否 | 否 |
| EB2.mmx | 20 | `{42:8, 99:12}` | 否 | 否 |
| EB3.mmx | 67 | `{99:67}` | 否 | 否 |
| EB4.mmx | 33 | `{99:33}` | 否 | 否 |
| EB5.mmx | 11 | `{99:11}` | 否 | 否 |
| ECH01.MAP | 11 | `{1:1, 2:1, 6:2, 11:3, 17:1, 21:2, 80:1}` | 否 | 否 |
| ECH02.MAP | 13 | `{1:1, 2:1, 6:4, 11:3, 21:1, 23:1, 27:1, 80:1}` | 否 | 否 |
| ECH03.MAP | 12 | `{1:1, 2:1, 6:2, 11:4, 17:1, 21:1, 53:1, 80:1}` | 否 | 否 |
| GoldSt.mmx | 53 | `{99:53}` | 否 | 否 |
| Grinder.mmx | 63 | `{99:63}` | 否 | 否 |
| HailMary.mmx | 1 | `{113:1}` | 否 | 否 |
| Hills.mmx | 18 | `{99:18}` | 否 | 否 |
| Kaliforn.mmx | 47 | `{99:47}` | 否 | 否 |
| Killer.mmx | 39 | `{99:39}` | 否 | 否 |
| Lostlake.mmx | 42 | `{99:42}` | 否 | 否 |
| NewHghts.mmx | 18 | `{99:18}` | 否 | 否 |
| Oceansid.mmx | 0 | `{}` | 否 | 否 |
| Pacific.mmx | 53 | `{99:53}` | 否 | 否 |
| Potomac.mmx | 30 | `{99:30}` | 否 | 否 |
| PowdrKeg.mmx | 84 | `{99:84}` | 否 | 否 |
| Rockets.mmx | 45 | `{99:45}` | 否 | 否 |
| Roulette.mmx | 68 | `{99:68}` | 否 | 否 |
| Round.mmx | 33 | `{99:33}` | 否 | 否 |
| Shrapnel.mmx | 11 | `{99:11}` | 否 | 否 |
| Tanyas.mmx | 25 | `{99:25}` | 否 | 否 |
| Tower.mmx | 35 | `{99:35}` | 否 | 否 |
| Tsunami.mmx | 82 | `{99:82}` | 否 | 否 |
| Valley.mmx | 69 | `{99:69}` | 否 | 否 |
| YuriPlot.mmx | 43 | `{99:43}` | 否 | 否 |
| [2]0LoadBench_U0050.yrm | 15 | `{99:15}` | 否 | 否 |
| [2]0LoadBench_U0100.yrm | 0 | `{}` | 否 | 否 |
| [2]0LoadBench_U0200.yrm | 15 | `{99:15}` | 否 | 否 |
| [2]0LoadBench_U0400.yrm | 15 | `{99:15}` | 否 | 否 |
| [2]0LoadBench_U0800.yrm | 0 | `{}` | 否 | 否 |
| [2]世仇Ⅱ_Pro_BloodFeudⅡ.yrm | 11 | `{0:1, 99:10}` | 否 | 否 |
| [2]丛林盆地_JungleBasin.yrm | 0 | `{}` | 否 | 否 |
| [2]九霄云外_Pro_CloudNine.yrm | 0 | `{}` | 否 | 否 |
| [2]亚马逊三角洲_AmazonaDelta_.yrm | 0 | `{}` | 否 | 否 |
| [2]内华达山谷_NevadaValley.yrm | 17 | `{99:17}` | 否 | 否 |
| [2]再顾城海_Urban_Marine_revisited.yrm | 38 | `{99:38}` | 否 | 否 |
| [2]冰洁鸿沟_FrozenDivide_.yrm | 0 | `{}` | 否 | 否 |
| [2]冷彻之日_Another_Cold_Day.yrm | 0 | `{}` | 否 | 否 |
| [2]冷战LE.yrm | 20 | `{99:20}` | 否 | 否 |
| [2]南太平洋_左上v右下.yrm | 28 | `{99:28}` | 否 | 否 |
| [2]双峰_Pro_TwinPlateaus_.yrm | 76 | `{99:76}` | 否 | 否 |
| [2]双重恶意LE.yrm | 0 | `{}` | 否 | 否 |
| [2]发光的水.yrm | 0 | `{}` | 否 | 否 |
| [2]可爱的雪_Pro_LovelySnow.yrm | 0 | `{}` | 否 | 否 |
| [2]地峡_LandSlide.yrm | 0 | `{}` | 否 | 否 |
| [2]地标_Landmarks.yrm | 0 | `{}` | 否 | 否 |
| [2]城市突击战_Pro_UrbanRush.yrm | 15 | `{99:15}` | 否 | 否 |
| [2]声之国度_LoudKingdom.yrm | 0 | `{}` | 否 | 否 |
| [2]多有人走的路_ThePathMoreTraveledBy.yrm | 0 | `{}` | 否 | 否 |
| [2]大河奔流多路口版.yrm | 6 | `{99:6}` | 否 | 否 |
| [2]嫌疑犯_suspect.yrm | 23 | `{98:2, 99:21}` | 否 | 否 |
| [2]小湾_LittleBigBay.yrm | 36 | `{99:36}` | 否 | 否 |
| [2]怒火燎原LE_AllTheFury.yrm | 1 | `{19:1}` | 否 | 否 |
| [2]战争园地LE.yrm | 10 | `{99:10}` | 否 | 否 |
| [2]捏点_Pro_PinchPoints.yrm | 0 | `{}` | 否 | 否 |
| [2]无限岛SE_infinityisle.yrm | 0 | `{}` | 否 | 否 |
| [2]星球改造_TerraforMation.yrm | 30 | `{99:30}` | 否 | 否 |
| [2]星际黄昏_Pro_StarDusk.yrm | 0 | `{}` | 否 | 否 |
| [2]月夜下的虎湾_Tiger_Bay_Night.yrm | 18 | `{99:18}` | 否 | 否 |
| [2]极夜_PolarNights.yrm | 12 | `{99:12}` | 否 | 否 |
| [2]梅萨_Mesa.yrm | 13 | `{63:5, 99:8}` | 否 | 否 |
| [2]正式锦标赛地图P.yrm | 0 | `{}` | 否 | 否 |
| [2]正式锦标赛地图Q.yrm | 0 | `{}` | 否 | 否 |
| [2]沙丘巡礼Ⅱ_Pro_DunePatrolⅡ_.yrm | 7 | `{99:7}` | 否 | 否 |
| [2]海啸Ⅱ.yrm | 82 | `{99:82}` | 否 | 否 |
| [2]海市蜃楼LE.yrm | 56 | `{99:56}` | 否 | 否 |
| [2]海湾战争_BayWar.yrm | 115 | `{14:8, 19:9, 21:9, 32:8, 53:24, 54:32, 55:8, 119:16, 131:1}` | 否 | 否 |
| [2]海盗湾_PirateBay.yrm | 2 | `{99:2}` | 否 | 否 |
| [2]特区暴动_左下v右上.yrm | 49 | `{99:49}` | 否 | 否 |
| [2]特攻要塞LE(火线冲突改).yrm | 18 | `{99:18}` | 否 | 否 |
| [2]猎手本能_PredatorInstinct.yrm | 52 | `{0:2, 99:50}` | 否 | 否 |
| [2]秘密山谷LE.yrm | 4 | `{99:4}` | 否 | 否 |
| [2]笛卡尔_Tikar.yrm | 0 | `{}` | 否 | 否 |
| [2]管道问题_PipelineProblem.yrm | 8 | `{99:8}` | 否 | 否 |
| [2]绞肉机_Pro_MeatGrinder_.yrm | 63 | `{99:63}` | 否 | 否 |
| [2]缆桩脊se.yrm | 28 | `{99:28}` | 否 | 否 |
| [2]薄冰_ThinIce.yrm | 6 | `{99:6}` | 否 | 否 |
| [2]蜿蜒SE_serpentine.yrm | 23 | `{54:1, 63:2, 99:20}` | 否 | 否 |
| [2]调和(停火线)Reconcile.yrm | 0 | `{}` | 否 | 否 |
| [2]酷热干旱LE_DryHeatLE.yrm | 8 | `{99:8}` | 否 | 否 |
| [2]重返巴黎_左v右.yrm | 30 | `{99:30}` | 否 | 否 |
| [2]针锋相对_Standoff.yrm | 111 | `{99:111}` | 否 | 否 |
| [2]锦标赛地图P_Pro_TournamentMapP.yrm | 0 | `{}` | 否 | 否 |
| [2]长征Ⅱ_左下v右上.yrm | 59 | `{99:59}` | 否 | 否 |
| [2]阿拉斯加油矿作战版.yrm | 16 | `{99:16}` | 否 | 否 |
| [2]隔山有眼_The_Hills_Have_Eyes.yrm | 11 | `{99:11}` | 否 | 否 |
| [2]雅顿河_ArdenRiver.yrm | 0 | `{}` | 否 | 否 |
| [2]雪谷_左上v右下.yrm | 26 | `{99:26}` | 否 | 否 |
| [2]频闪_Strobe.yrm | 4 | `{99:4}` | 否 | 否 |
| [2]马里布悬崖_左上v右下.yrm | 65 | `{99:65}` | 否 | 否 |
| [2]黄尘地带_Pro_Dustbowl.yrm | 25 | `{99:25}` | 否 | 否 |
| [2]黄金国SE.yrm | 33 | `{99:33}` | 否 | 否 |
| [2]黑曜石之山_ObsidianKnoll.yrm | 0 | `{}` | 否 | 否 |
| [3]冰冷三角_FrigidTriangle.yrm | 0 | `{}` | 否 | 否 |
| [4]不列孜然湖se.yrm | 32 | `{99:32}` | 否 | 否 |
| [4]中暑_Sunstroke_sunstroke.yrm | 181 | `{7:4, 11:1, 14:16, 19:10, 21:10, 32:8, 42:4, 53:40, 54:40, 55:8, 56:4, 99:15, 104:4, 119:16, 131:1}` | 否 | 否 |
| [4]乡村乐LE.yrm | 33 | `{99:33}` | 否 | 否 |
| [4]低洼地带_LowLands.yrm | 0 | `{}` | 否 | 否 |
| [4]公平公正_FairAndSquare.yrm | 0 | `{}` | 否 | 否 |
| [4]公牛狂奔_BullRun.yrm | 0 | `{}` | 否 | 否 |
| [4]冰冻高地_FrozenBadLands.yrm | 0 | `{}` | 否 | 否 |
| [4]冰天LE.yrm | 16 | `{99:16}` | 否 | 否 |
| [4]冰天LE_SEⅡ.yrm | 16 | `{99:16}` | 否 | 否 |
| [4]冰天富矿.yrm | 16 | `{99:16}` | 否 | 否 |
| [4]冰天封神赛.yrm | 16 | `{99:16}` | 否 | 否 |
| [4]冰天贫矿.yrm | 16 | `{99:16}` | 否 | 否 |
| [4]冰天雪地LE 6号版.yrm | 16 | `{99:16}` | 否 | 否 |
| [4]冰天雪地富矿 6号版.yrm | 16 | `{99:16}` | 否 | 否 |
| [4]冰天雪地封神 6号版.yrm | 16 | `{99:16}` | 否 | 否 |
| [4]冰天雪地贫矿 6号版.yrm | 16 | `{99:16}` | 否 | 否 |
| [4]冷锋(极寒之冠).yrm | 0 | `{}` | 否 | 否 |
| [4]分割雪地.yrm | 13 | `{99:13}` | 否 | 否 |
| [4]分而治之.yrm | 11 | `{99:11}` | 否 | 否 |
| [4]划分_DivisionDelta.yrm | 0 | `{}` | 否 | 否 |
| [4]加州谷_GoldenStateValley_goldvall.yrm | 12 | `{99:12}` | 否 | 否 |
| [4]加州高速公路LE_GoldenStateFwy.yrm | 26 | `{99:26}` | 否 | 否 |
| [4]北浪_NorthWaves_northwav.yrm | 0 | `{}` | 否 | 否 |
| [4]双重巡礼_DoublePatrol.yrm | 13 | `{99:13}` | 否 | 否 |
| [4]双重恶意_DoubleMalice.yrm | 0 | `{}` | 否 | 否 |
| [4]可爱的雪_LovelySnow_lovelysnow.yrm | 0 | `{}` | 否 | 否 |
| [4]士兵游戏_SoldierGame.yrm | 12 | `{99:12}` | 否 | 否 |
| [4]天寒地冻_Pro_Frostbite.yrm | 68 | `{99:68}` | 否 | 否 |
| [4]天秤的舞台Libra'sPlayground.yrm | 23 | `{99:23}` | 否 | 否 |
| [4]天蝎迷踪_Scorpion'sTrail_scorpionstrail.yrm | 0 | `{}` | 否 | 否 |
| [4]小片岛屿_LittlePieceOfIsland_lpofisle.yrm | 0 | `{}` | 否 | 否 |
| [4]峡湾_FiordLand.yrm | 0 | `{}` | 否 | 否 |
| [4]工业意志_IndustrialFortitude.yrm | 40 | `{99:40}` | 否 | 否 |
| [4]巨猪湾_GiantHogBay.yrm | 115 | `{14:8, 19:9, 21:9, 32:8, 53:24, 54:32, 55:8, 119:16, 131:1}` | 否 | 否 |
| [4]惊天逆转_Inversion.yrm | 143 | `{14:8, 19:9, 21:9, 32:8, 53:24, 54:32, 55:8, 99:28, 119:16, 131:1}` | 否 | 否 |
| [4]成事在人se.yrm | 18 | `{21:3, 23:3, 27:3, 40:3, 53:4, 99:2}` | 否 | 否 |
| [4]择路而战.yrm | 68 | `{99:68}` | 否 | 否 |
| [4]据点.yrm | 0 | `{}` | 否 | 否 |
| [4]无穷大_Infinity.yrm | 68 | `{99:68}` | 否 | 否 |
| [4]晨光_Morningtide_morntide.yrm | 0 | `{}` | 否 | 否 |
| [4]松果岛_PineconeIsland.yrm | 21 | `{99:21}` | 否 | 否 |
| [4]正式锦标赛地图se.yrm | 0 | `{}` | 否 | 否 |
| [4]死冰_DeadIce.yrm | 0 | `{}` | 否 | 否 |
| [4]沙漠黄昏_DesertTwilight.yrm | 10 | `{99:10}` | 否 | 否 |
| [4]流氓国家SE_roguestate.yrm | 0 | `{}` | 否 | 否 |
| [4]海嘯se.yrm | 82 | `{99:82}` | 否 | 否 |
| [4]清凉派对.yrm | 37 | `{99:37}` | 否 | 否 |
| [4]湖畔分界线_Lakeside_lakeside.yrm | 9 | `{99:9}` | 否 | 否 |
| [4]特攻要塞SE_FortKickAss.yrm | 18 | `{99:18}` | 否 | 否 |
| [4]草地战争1080P_turfwarse.yrm | 8 | `{99:8}` | 否 | 否 |
| [4]荒岛_DesertIsland.yrm | 0 | `{}` | 否 | 否 |
| [4]菲因_V_阿莉兹：终结黎明_Finalized.yrm | 20 | `{99:20}` | 否 | 否 |
| [4]蒙大拿非军事区Ⅱ.yrm | 0 | `{}` | 否 | 否 |
| [4]西伯利亚洞穴_CavernsOfSiberia_caverns.yrm | 12 | `{99:12}` | 否 | 否 |
| [4]财富之井_WellofWealth.yrm | 0 | `{}` | 否 | 否 |
| [4]越南丛林_JungleOfVietnam_jungleof.yrm | 8 | `{99:8}` | 否 | 否 |
| [4]酷热干旱Ⅱ_Pro_DryHeatⅡN.yrm | 8 | `{99:8}` | 否 | 否 |
| [4]野蛮冬季_SavageWinter.yrm | 0 | `{}` | 否 | 否 |
| [4]锦标赛：山岭_TournamentTridge.yrm | 0 | `{}` | 否 | 否 |
| [4]锦标赛：岛屿_TournamentIsland.yrm | 0 | `{}` | 否 | 否 |
| [4]锦标赛：沙丘_II_TournamentDuneTwo.yrm | 0 | `{}` | 否 | 否 |
| [4]锦标赛：沼泽_TournamentSwamp.yrm | 20 | `{99:20}` | 否 | 否 |
| [4]阴-阳se.yrm | 7 | `{0:1, 99:6}` | 否 | 否 |
| [4]阿拉斯加内陆_Pro_AlaskanOutback.yrm | 114 | `{99:114}` | 否 | 否 |
| [4]隐秘山谷Ⅱ_HiddenValleyⅡ.yrm | 0 | `{}` | 否 | 否 |
| [4]雪地交战.yrm | 0 | `{}` | 否 | 否 |
| [4]雪地巡礼_Pro_SnowPatrol.yrm | 0 | `{}` | 否 | 否 |
| [4]雪地巡礼_SnowPatrol.yrm | 0 | `{}` | 否 | 否 |
| [4]雪硝基_Pro_SnowNitro.yrm | 0 | `{}` | 否 | 否 |
| [4]雪羽_SnowFeathers.yrm | 62 | `{41:49, 99:13}` | 否 | 否 |
| [4]风暴.yrm | 91 | `{99:91}` | 否 | 否 |
| [4]鬼驱人.yrm | 0 | `{}` | 否 | 否 |
| [4]魔法一号之魂se.yrm | 29 | `{99:29}` | 否 | 否 |
| [4]鳄鱼湾_Don'tMockTheCrocs_mockcrocs.yrm | 0 | `{}` | 否 | 否 |
| [4]黄尘峡谷_dustycanyon.yrm | 0 | `{}` | 否 | 否 |
| [4]黄昏_Eventide_eventide.yrm | 0 | `{}` | 否 | 否 |
| [4]黄昏峡谷LE_DuskRavinele2.yrm | 0 | `{}` | 否 | 否 |
| [4]黄石国家公园.yrm | 21 | `{99:21}` | 否 | 否 |
| [4]黄金试炼_PracticeYellow.yrm | 0 | `{}` | 否 | 否 |
| [6]一丘之隔.yrm | 0 | `{}` | 否 | 否 |
| [6]乡村乐Ⅱ.yrm | 33 | `{99:33}` | 否 | 否 |
| [6]关原之战_Sekigahara.yrm | 0 | `{}` | 否 | 否 |
| [6]冰天雪地.yrm | 16 | `{99:16}` | 否 | 否 |
| [6]冰天雪地黄金矿版.yrm | 16 | `{99:16}` | 否 | 否 |
| [6]冰山冷水.yrm | 0 | `{}` | 否 | 否 |
| [6]南极洲_Pro_AntArctic.yrm | 0 | `{}` | 否 | 否 |
| [6]坏天气_Badweather.yrm | 1 | `{102:1}` | 否 | 否 |
| [6]失而复得(MO).yrm | 0 | `{}` | 否 | 否 |
| [6]失而复得.yrm | 0 | `{}` | 否 | 否 |
| [6]孤立之海6人se.yrm | 27 | `{99:27}` | 否 | 否 |
| [6]帮派战争_GangWar.yrm | 27 | `{99:27}` | 否 | 否 |
| [6]平原和溪流_FieldAndStream_.yrm | 0 | `{}` | 否 | 否 |
| [6]幻影山SE_mountmirage.yrm | 0 | `{}` | 否 | 否 |
| [6]强取豪夺_Ravenous.yrm | 0 | `{}` | 否 | 否 |
| [6]当东方遇到最差.yrm | 17 | `{19:3, 98:7, 99:7}` | 否 | 否 |
| [6]怒火燎原se(有船厂)_allthefury.yrm | 1 | `{19:1}` | 否 | 否 |
| [6]抹茶月饼.yrm | 0 | `{}` | 否 | 否 |
| [6]攻击与防御6人无高地.yrm | 0 | `{}` | 否 | 否 |
| [6]攻击与防御6人有高地.yrm | 0 | `{}` | 否 | 否 |
| [6]机械岛_MechanicalIsland.yrm | 0 | `{}` | 否 | 否 |
| [6]林地和平原.yrm | 13 | `{11:2, 99:11}` | 否 | 否 |
| [6]正面交锋.yrm | 0 | `{}` | 否 | 否 |
| [6]死亡六人组_DeadSix.yrm | 0 | `{}` | 否 | 否 |
| [6]死亡谷之女6人se.yrm | 0 | `{}` | 否 | 否 |
| [6]流氓竞技场_Rogues'Arena.yrm | 13 | `{0:1, 7:11, 14:1}` | 否 | 否 |
| [6]海啸6人se.yrm | 82 | `{99:82}` | 否 | 否 |
| [6]猪猡湾Ⅱ_BayOfPigs.yrm | 130 | `{14:8, 19:9, 21:9, 32:8, 53:24, 54:32, 55:8, 99:15, 119:16, 131:1}` | 否 | 否 |
| [6]联合作战.yrm | 0 | `{}` | 否 | 否 |
| [6]苦痛恶意_MiseryMalice.yrm | 0 | `{}` | 否 | 否 |
| [6]草地之旅.yrm | 0 | `{}` | 否 | 否 |
| [6]荒岛6人版.yrm | 0 | `{}` | 否 | 否 |
| [6]蒙大拿非军事区Ⅲ.yrm | 0 | `{}` | 否 | 否 |
| [6]资源争端_ResourcesTrain.yrm | 0 | `{}` | 否 | 否 |
| [6]越南丛林Ⅱ.yrm | 8 | `{99:8}` | 否 | 否 |
| [6]进攻策略.yrm | 6 | `{14:6}` | 否 | 否 |
| [6]连贯se_connectioncut.yrm | 0 | `{}` | 否 | 否 |
| [6]阿拉斯加宝石热_AlaskanGemRush.yrm | 114 | `{99:114}` | 否 | 否 |
| [6]雪地巡礼Ⅱ.yrm | 0 | `{}` | 否 | 否 |
| [6]马尔翁的沙盒_MalversSandbox.yrm | 36 | `{99:36}` | 否 | 否 |
| [6]马里布悬崖3v3版.yrm | 65 | `{99:65}` | 否 | 否 |
| [6]麦格马_Magma.yrm | 0 | `{}` | 否 | 否 |
| [8]三岔路口Ⅱ.yrm | 6 | `{99:6}` | 否 | 否 |
| [8]东风谷_EastwindValley.yrm | 12 | `{19:2, 98:10}` | 否 | 否 |
| [8]冰霜峡谷_CanyonFrost..yrm | 0 | `{}` | 否 | 否 |
| [8]冷场新高_ColdHardTruth.yrm | 0 | `{}` | 否 | 否 |
| [8]别踩鳄鱼_DontStepOnTheCrocodile.yrm | 0 | `{}` | 否 | 否 |
| [8]北极.yrm | 0 | `{}` | 否 | 否 |
| [8]四叶草对决_Clover.yrm | 0 | `{}` | 否 | 否 |
| [8]幻象绿洲_mirageoasis.yrm | 10 | `{99:10}` | 否 | 否 |
| [8]悬崖滑行_CliffsideSlide.yrm | 0 | `{}` | 否 | 否 |
| [8]摊牌.yrm | 0 | `{}` | 否 | 否 |
| [8]攻击与防御8人无高地.yrm | 0 | `{}` | 否 | 否 |
| [8]攻击与防御8人有高地.yrm | 0 | `{}` | 否 | 否 |
| [8]新山岭杀戮_RidgeCarnageRedux.yrm | 0 | `{}` | 否 | 否 |
| [8]星尘斗士_StardustCrusader.yrm | 50 | `{99:50}` | 否 | 否 |
| [8]楚河汉界_CowFields.yrm | 0 | `{}` | 否 | 否 |
| [8]正式锦标赛：X.yrm | 0 | `{}` | 否 | 否 |
| [8]死亡谷之女8人.yrm | 4 | `{99:4}` | 否 | 否 |
| [8]沙漠风暴.yrm | 0 | `{}` | 否 | 否 |
| [8]海啸8人.yrm | 0 | `{}` | 否 | 否 |
| [8]灰色风暴_Greywind.yrm | 0 | `{}` | 否 | 否 |
| [8]猪猡湾Ⅲ_BayOfPigsⅢ.yrm | 0 | `{}` | 否 | 否 |
| [8]环太平洋_Pacificrim.yrm | 0 | `{}` | 否 | 否 |
| [8]矢志不渝_Dedication.yrm | 0 | `{}` | 否 | 否 |
| [8]科威克森林_CorwickForest.yrm | 0 | `{}` | 否 | 否 |
| [8]绿岛蓝洞_BlueHole.yrm | 0 | `{}` | 否 | 否 |
| [8]绿洲生机_LifeInTheOasis.yrm | 0 | `{}` | 否 | 否 |
| [8]联合作战8人.yrm | 0 | `{}` | 否 | 否 |
| [8]试验地_Pro_ProvingGrounds.yrm | 67 | `{99:67}` | 否 | 否 |
| [8]边城决战_BorderTown.yrm | 0 | `{}` | 否 | 否 |
| [8]雪 雪 雪_SnowSnowSnow.yrm | 28 | `{99:28}` | 否 | 否 |
| [8]音速公路_SonicHighways.yrm | 118 | `{41:1, 80:4, 88:2, 99:111}` | 否 | 否 |
| [8]风暴Ⅱ.yrm | 91 | `{99:91}` | 否 | 否 |
| [8]黑心湾_HexBay.yrm | 0 | `{}` | 否 | 否 |
| amazon.mmx | 62 | `{19:1, 99:61}` | 否 | 否 |
| invasion.mmx | 37 | `{99:37}` | 否 | 否 |
| prm.yrm | 56 | `{14:7, 56:1, 68:1, 107:39, 109:7, 119:1}` | 否 | 否 |
| xmas.mmx | 29 | `{99:18, 108:11}` | 否 | 否 |

---

## 6. 诚实账

### 6.1 本人本次实跑（命令 + 输出）

| # | 命令（均在 `/d/Project/ra2-campaign-forge` 下，`python -I -X utf8`） | 输出要点 |
|---|---|---|
| 1 | `wc -l -c sections/*.md TASK.md` | Q1 524/34,649、Q2 210/23,856、Q3 657/43,283、Q3B 524/38,994、TASK 113/7,954 |
| 2 | 表校验脚本（解析 `Q3B_MAPS.md` §5） | 265 行 / 265 互异文件名 / `sum n_rec=1261` / `sum n_actions=5309` / 有段 154 / `110!=否` 0 行 / `127!=否` 0 行 |
| 3 | `python -I -X utf8 <sections/_q3b_probe.py> > .tmp/w1_final_verify/q3b_rerun.txt 2>&1` 后 `diff -q` | `EXIT=0`、`DIFF=identical`、316 行 / 20,513 B；`GLOBAL_HIST` 无 110/117/127 键、`sum=5309`、`distinct=34` |
| 4 | `pickle.load(lead/goal3t_nightwatch_20261102/swarm_20261104/P01/stream_cache.pkl)`（1,394,120 条，记录格式 `(VA,size,hex,mnemonic,operands)`）+ 多个只读查询脚本，输出落在 `.tmp/w1_final_verify/{stream_check,closure_check,final_checks}.txt` | `callers`：`0x684060`=4、`0x684180`=3、`0x53B460`=2、`0x53B560`=2、`0x684240`=7、`0x684290`=4、`0x6579E0`=1、`0x5BF390`=4、`0x5BF260`=12、`0x5BF2B0`=0、`0x5BF450`=6、`0x5BF500`=5、`0x5C07D0`=5、`0x432C70`=2、`0x53A6C0`=1(`0x55B5C8`)；`TO_48D080=170 (169 E8 + 1 E9)`；`DISP_HITS_B45B68=23 / W 5 / R 18`；`MEM_DISP_62C=18 / W 7`；`RAW_DWORD 0x5BF2B0/0x5BF390/0x5BF341/0x5BF43B/0x539320/0x6579E0` 全为 0；`u32(0x815728)=0x759180`、`u32(0x7F0384)=0x653100`；`TABLE_872A7C` n=256/distinct=256/zero=0/间距 min 550 max 555/`n_exact_0x22B=33`；`0x6DFDEC` 与 `0x872A7C` 头四项不同；`0x5BED40..0x5BF178`=291 条、`..0x5BF260`=354 条、`..0x5BF2A2`=374 条；354 条窗口内 `0xB45B68` 引用 0、`0x62C` 引用 0、对 4 个目标的调用 0；`0x6579AC/B1/BB/C0` 全 `<0x6579E0`；`0x68361E lea` vs `0x6839CE mov [ebp+0x35a2],bl`；`0x5BF2F9`/`0x5BF3F4 mov [esi+4],bl`；`0x53B4F7 mov [0xa9fab0],1` 为唯一 state=1 写者；Q1 §6.2 前 20 条 = 6 尾 + 9 NOP + 5 序言 |
| 5 | `os.walk('ra2youli')` 扩展名/段检测脚本 | 磁盘 in-scope 文件 265；范围外含 `[Actions]` 32 个（`.mpr` 20/`.mix` 7/`.bak` 4/`.old-pre-migrate` 1）；`mapsmd03.mix` 内 `[Actions]` 中 kind=127 组首 2 条；`mapsmd03.mix`/`maps02.mix` 存在参数位 110 |
| 6 | 实读 `lead/GOAL_THREE_TARGETS_20261018.md:5880-5899`、`lead/re_line_20261105/GOAL_RE_CONTINUOUS.md:62-69` | §559「裁决 Q3 对、Q1 错」、A13「265 张 0 张含 110/127/117」、A14「Q1 vs Q3 冲突已裁；残余唯一未证入口 `0x5BF2B0`」 |
| 7 | `git status --short -- lead/re_line_20261105/W1_HOLD_SURFACE/` | `?? lead/re_line_20261105/W1_HOLD_SURFACE/`（未跟踪、未 commit、未 push） |
| 8 | 交付物存在性检查 | 写作前 `W1_HOLD_SURFACE.md` / `_w1_probe.py` / `_w1_probe_out.txt` 三者均不存在；`sections/` 仅有 Q1/Q2/Q3/Q3B 四份 md 与 `_q3b_probe.py`/`_q3b_probe_out.txt`。本次**只写出 `W1_HOLD_SURFACE.md`**，另两个文件仍未生成（不属本次 ask 范围） |

**本人未运行**：`Engine()` 构造（SHA256 断言）与 `Engine.stream` 全量重同步解码本身——本人用的是 `P01/stream_cache.pkl` 的既有解码缓存（`P01/v1_mega.py:25-28` 记载由 `eng.stream` 序列化）。因此 `SHA 73201cc0…f67476` 与 `coverage (99.99837567729335, 1394120, 66)` 是**采信**复核意见与四份节文件的记载，不是本人本次实跑产生的输出；本人只复核了缓存长度 1,394,120 与节文件/复核所列指令逐址一致。

### 6.2 采信（复核意见 / 节文件提供，本人本次未重跑）

- 复核 Q1 的 `resync(0x5BF280,0x5BF5A0)` 293 条 `fails=0`、`resync(0x5BED40,0x5BF2A2)` 374 条 `fails=0`、**251 节点精确边界传递闭包**、全流 59 条向量字段引用定位、动作跳表 145/146 行区间普查、字符串解析、`0x7F6984` 8 槽 vtable。
- 复核 Q2 的 4 个探针（`q2_review_probe{,2,3,4}.py`）与 `BinkMovieClass::Play` 定位、`+0x14BC/+0x14BD` 全镜像仅 3 处访问、IAT slot、`pickle.load` 与「另一次独立解码计时 344.7s」——复核自陈**未逐字运行**该两条命令，改用等价 `Engine()` 全量重同步解码，本人亦未运行。
- 复核 Q3 的 8 个探针（`probe1..8`）：146 行动作表全表扫描、4889 条 `rep*` 指令计数、`[0xA9FAB0]` 6 个 W、`0x5BF2B0..0x5BF353` 外来分支 0、Win/Lose 路径调用者、`+0x35A2`/`[0xA8ED9C]`/`[0xA8ED80]` 链隔离、`0x872A7C` 表消费方 count 0、三链分离逐字节。
- 复核 Q3b 的独立重写解析器 `verify_lean.py`、265 relpath 集合比对、`crosscheck_md.py` 265/265 键命中、`verify_sha.py`（FOUND=10/MISSING=0、5 处引用字节数）、`all_copies.py`（75 份同哈希副本全 0）、`grep -a -rl -i '\[Actions\]'` 154 段独立互证、18 份 measure_w 枚举、三个交付物 sha256sum。
- 未由本人重新打开核对的仓内锚点：`YRpp/*.h`、`docs/re/*.md`、`P01/REPORT.md`、`P01/VERIFY.md`、`Q02/REPORT.md`、`out/re_work/triggers/action_dispatch_table.tsv`、`LEADER_PRECHECK_20261105.md`、`ra2forge/triggers.py:19-20`、`ra2forge/maplib.py:463-472` —— 本报告中对这些文件的行号引用**继承自四份节文件与复核意见**，不是本人本次实读。

### 6.3 未验 / 缺口（不补造，一律登记）

1. **零真机**：`TASK.md:103-104` 铁律；四份复核亦均未启动游戏、未读活进程、未写采样代码。所有「运行时是否真的非 0 / 何时翻沿」只给静态判据。
2. **间接 CFG / 虚表间接调用求解未做** ⇒ Q1(c) 只能判「静态证据不支持、无已知路径」，**不能判「运行时绝对不可能非 0」**；`0x5BF2B0` 运行时可达性、`0x5BF520 IsNonEmpty()` 零 xref、ACTION_FUNC slave（`0x6E16D0/0x6E1720/0x6E1740/0x6E4080/0x6E2F90`）运行时调用者、`0x872A7C` 表运行时消费方，均未验。
3. **Q3 §7 #4 边界仍未闭合**：复核自陈未实跑 `disp_hits(0xA8EDA0)=32`、`disp_hits(0xB07784)=8(7W)`、`disp_hits(0xB054CC)=2`、`disp_hits(0xA8B230)` 的 3 个 W，本人亦未实跑；复核虽数出全镜像 4889 条 `rep*` 指令，但**未穷尽证明**其中无一条能整对象覆盖 `Scenario+0x62C`，故 `rep movsd / memset` 整对象拷贝、经 `[0xA8B234]` 等指针副本的间接写仍未排除。读档/存档反序列化是否把 `+0x62C` 恢复成非 0、ACTION_FUNC 从属体运行时消费方、`0x5BED40` 内虚调与 `0x5BFAA0` 下游的全间接闭包，均按 Q3 诚实账保留「未验」。
4. **Q3 可复算性 / 交付物偏离**：§8-C/§8-E 为占位块、§8-B/§8-D 为散文摘要，5 个实跑小节中 4 个不可直接复跑（`TASK.md:111`）；`TASK.md:87-91` 的三交付物中 `_w1_probe.py` 与 `_w1_probe_out.txt` 至今未生成（本人本次只写 `W1_HOLD_SURFACE.md`）。
5. **Q3b 未复核项**：动作 110/127 编号名称、`TASK.md:26-27` 的 `0x6DF703/0x6DFAC5` 归属、其余 33 种 kind 名称——复核与节文件均标「采信」，本人未做反汇编/跳表复核；`map_sha` 只是 argv 回显不证明实载；`.bak/.mix/.mpr/.old-pre-migrate` 未纳入 265 张（已核实其中确有 `[Actions]`，且 `mapsmd03.mix` 内有 2 条 kind=127）；本人对非 `[Actions]` 段裸 110/127 token 的计数与复核的 611 口径不同，不可直接比较，两者都只用于说明「0 必须按段内读」。
6. **命名精度未到符号级**：向量元素确切 C++ 类名、`0x7F6984` 各虚槽定名、`0x653446` 宿主对象的虚方法名、六个库函数的精确业务名、`0x5D3BA0` 的参数语义（`0x4046`/`0xA8BC60`）、`0x6842F0` 业务名，均未解到函数名级。
7. **已按复核改正、不再作为缺口**：Q1 §6.2 的 15/5、`0x48D080` 的 169+1；Q2 的 `0x6579B1` 归属 / `+0x14BD` 语义 / GameMode 门 / `(state−1)` 跳表索引 / `+0x11E4` 头文件锚 / IAT 项剔除；Q3 的 256 项间距、`0x6839CE` VA、291/354 条 dump、43,283 B 元数据、Q1/Q3 冲突已裁、`0x872A7C` 与 `0x6DFDEC` 区分、`0x53A747` 分类、`0x5BF2F9` pause 旗标；Q3b 的扩展名边界与 18 份 measure_w 枚举。

---

*本报告为四节与四份复核意见的汇总，不新增反汇编结论；凡复核判 PARTIAL 的原肯定结论均已改写或降级。零真机、未修改任何只读母本、未 commit / 未 push。*
