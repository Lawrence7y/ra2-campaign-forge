# W8·F6 独立复核 · 真实视口坐标 / 当前可见世界矩形（复核员 F6）

```
被复核件 = F6_VIEWPORT.md（2026-11-06 01:34:31）+ 探针 _w8_f6.py / _w8_f6_out.txt（460 行）
复核探针 = reviews/_f6rev_probe.py → _f6rev_probe_out.txt（996 行，exit=0，178.9s）
           reviews/_f6rev_probe2.py → _f6rev_probe_out2.txt（exit=0）
复核口径 = 自带 PE 解析 + 自带重同步线性解码（capstone 5.0.7，detail），不复用 ra2tool 缓存流；
           查询集合独立设计；单趟普查 + 邻域反例狩猎 + 数值模拟 + RTTI 独立走法。
纯静态：零真机、零活进程；唯一写域 = reviews/（本文 + 两个复核探针 + 两个复核输出）。
```

## 0. 复核结论

**CONFIRMED —— F6 = LOCATED 成立。** 19 项 located VA 全部具备「类型 + 生命周期 + 访问证据」，
且我逐条重跑反汇编复核通过；排除清单不是空话，我复跑后逐条复现。同时发现 3 处
文档级缺陷（见 §5/§6），均不动摇 LOCATED 判定。复核还把 F6 自己挂起的 §6.2 几何
疑问部分关闭（矩阵常量 = 256/60、256/30 leptons/px，见 §4.4）。

## 1. SHA256 绑定复核（第一问：回件是否真含自算 SHA256 头部）

- F6_VIEWPORT.md:7 含强制头部 `gamemd.exe SHA256 = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476，字节数 = 4825360`，:8 含 COVERAGE/IMAGEBASE 自证 —— 头部齐全。
- 我独立实算（`python -I -X utf8 -c` 对 `ra2youli\gamemd.exe` hashlib.sha256）：**同值**，SIZE 4825360（_f6rev_probe_out.txt:1-2）。ra2tool.EXE 指向同一文件且自带断言（ra2tool.py:28-29,55），无镜像漂移。
- 我自带 PE 解析：IMAGEBASE 0x400000（out:3）；我自带重同步解码 1,394,120 条 / resync 66 / 99.9984%（out:4）——与 F6 的 COVERAGE 自证（_w8_f6_out.txt:5-6）**逐位一致**（含 insn 数与 resync 数），双方解码器相互印证。

## 2. 逐 VA 复核（第二问：LOCATED 是否真有类型+生命周期+访问证据）

| # | located VA | 类型 | 生命周期 | 访问证据 | 复核结果（我的证据行） |
|---|---|---|---|---|---|
| 1 | `0x887324` 单例槽 | `Tactical*`（RTTI `.?AVTactical@@`，out2:3-6） | ctor 尾 `0x6D1E1E mov [0x887324],esi`（out:109）；dtor `0x6DC48E mov [0x887324],0`（out:758） | 全镜像 461 引用 / 11 W（out:196-207，与 _w8_f6_out.txt:211 逐条同表） | ✅ |
| 2-3 | `[T+0xB0]/[T+0xB4]` 视口像素原点 | dword×2 | ctor 清零 `0x6D1C48/0x6D1C4E`（out:23-24）；每逻辑帧重算 | 唯一运行期写者 `0x6D8B30`（out:391/392/398/411）；读者 IsVisible `0x6D2202/0x6D2208`（out:536-537） | ✅ |
| 4-7 | `[T+0xD64..0xD78]` 当前/目标滚动 | dword×4 | ctor 清零 `0x6D1CAA..0x6D1CC8`（out:39-44） | 写点普查 TacW=7/7/8/8（out:651-658，与 _w8_f6_out.txt:355-358 完全一致）；目标推进 `0x6D861A/0x6D8622` + 方向表 `[ecx*8+0xB0CE38/3C]`（out2:31-45） | ✅ |
| 8-11 | `[T+0xD80/D84]` 可见区左上格、`[T+0xD88/D8C]` 跨度 | dword×4（格空间） | ctor 从 `[0xB0CD60..0xB0CD6C]` 装入 `0x6D1CE1..0x6D1D09`（out:48-56，**F6 文档漏记，见异议2**）；此后由 0x6D8B30 每次刷新 | 写点普查 W=5/2/2/3、TacW=2/1/1/1（out:659-666，**本项是 F6 探针缺失的排除面，我补跑证实**）；读者 `0x6D8AE0`（out:495-507） | ✅ |
| 12 | `0x6D8B30` 计算者 | Tactical 方法（thiscall，`mov esi,ecx` out:386） | 函数体 `0x6D8B30..0x6D8C50`（`ret` @0x6D8C50，out:384-466） | 直接调用者恰 6 处全在 Tactical 族（out:474）；写 +0xB0/B4（out:391-411）、+0xD80/84（out:438-445）、+0xD88/8C（out:455-463） | ✅ |
| 13 | `0x6D2540` = vtable[23] | Tactical::AI | vtable 0x7F4348 槽 23 = 0x6D2540（out:7-8） | 无 E8 直调（纯虚派发，out:644）；帧戳守卫 `[T+0xA8]` vs `[0xA8ED84]`（out:603-607）；两处同步+`call 0x6D8B30` = `0x6D267D`/`0x6D2778`（out:620,632）+ 置脏 `0xD7D`（out:621,633） | ✅ |
| 14 | `0x55D847` 派发点 | `call dword ptr [edx+0x5C]` | 位于 MainLogicFrame 锚 `[0x55D360,0x55DEE0)` 内（out:214） | 字节现场 `0x55D83F mov ecx,[0x887324]; 0x55D845 mov edx,[ecx]; 0x55D847 ff525c`（out:210-212） | ✅ |
| 15 | `0x6D2140` IsVisible | Tactical 方法，this=ebp（`0x6D2153 mov ebp,ecx` out:526） | 读 `[ebp+0xB0]/[ebp+0xB4]`（out:536-537），边界 −360/宽+360/−180/高+180（out:549-568） | 直接调用者 **139**（out:575，与 _w8_f6_out.txt:326 一致）；链头 `0x5F4B63 mov ecx,[0x887324] → 0x5F4B6A call 0x6D2140`（out:589-591） | ✅ |
| 16 | `0x6D8AE0` 格包含判定 | 取 CellStruct\*，`x∈[D80,D80+D88)&&y∈[D84,D84+D8C)` | — | 四条比较/跳转逐字节吻合（out:495-510，`ret 4`） | ✅ |
| 17 | `0x6D1C20` ctor | `.?AVTactical@@`；vtable `0x7F4348`+次级×3（out2:3-6）；sizeof 0xE18 | 5 个创建点逐字核对：`0x687604 push 0xE18; 0x687609 call 0x7C8E17(new); 0x687617 call 0x6D1C20; 0x687627 mov [0x887324],eax; 0x68762C push 0x886FA0; call 0x6D5F60`（out:168-180）；调用者恰 5（out:122） | ✅ |
| 18 | `0x6DC470`/`0x6DC48E` deleting dtor | vtable[8]=0x6DC470（out:8）；体重写 4 vtable 后 `[0x887324]=0`（out:752-758）；无 E8 直调（out:750，纯虚销毁） | ✅ |
| 19 | `0xB0CE28..0xB0CE34` 屏幕 Rect | 16 字节全局 | 每 dword 恰 2 写者：零初始化函数 `0x6D1A40..0x6D1A56`（out:698-703）+ 装载者 `0x6D5F6C..0x6D5F87`（out:936-942）（out:685-688） | 源 Rect `0x886FA0`：142 引用 / 2 W（out:692）；默认值现场 0x886FA8=0x280(640)、0x886FAC=0x190(400)（out:718,721）；`0x4A8987` 拷 16 字节后 `mov ecx,[0x887324]` → `call 0x6D5F60`（out:733-745） | ✅ |
| 20 | `0x886FA0` 源 Rect 全局 | 16 字节 | W 仅 `0x40DA2C`/`0x4A8987`（out:692） | ✅ |
| 21 | `0x432750..0x432A50` Bink 函数 | thiscall，`ret 4`（out:810）；尾后 13×NOP、次函数 0x432A60 起（out:811-825） | — | IAT 判名 11 槽（_w8_f6_out.txt:59-69）、`"Bink Error: %s\n"`@0x818B2C（out2:12）；体内**零** `0x887324` 引用、**零** IsVisible/0x6D8B30 调用（out:766）；调用者 2 处（out:767，但宿主区间表述有误，见异议1） | ✅ |
| 22 | `0x4BA5A0` DSurface ctor | `ret 0x10`（out:886） | `lea ebp,[esi+0x1C]`→NULL 初值（out:836,845）；`call [ecx+0x18]`=IDirectDraw 槽6 CreateSurface（out:857）；`call [ecx+0x58]`=槽22 GetSurfaceDesc（out:871）；`([ddsd+0x54]+7)>>3 → +0x10`（out:873-876）——与 108 字节 DDSURFACEDESC（DDPIXELFORMAT@0x48、dwRGBBitCount@+0x54）自洽 | RTTI `.?AVDSurface@@`（out2:2；复现 _w8_f6_out.txt:96） | ✅ |
| 23 | `DSurface::Primary+0x1C`@0x887308 | LPDIRECTDRAWSURFACE 指针 | 0x887308 恰 5 W、0x88730C 恰 5 W，全在表面生命周期簇（out:693-694） | 消费方 `0x432A35..0x432A3E`：`mov eax,[0x887308]; mov eax,[eax+0x1C]; push; call [0x7E15A8]=binkw32!_BinkDDSurfaceType@4`（out:798-801）——只 push+call，无坐标语义 | ✅ |

**结论：没有一项是「只给地址」。** 每项都有写入点字节、读取点字节或调用者计数，
且生命周期两端（ctor/dtor/装载）齐备。

## 3. 排除清单是否真跑过（第三问）

| 排除项 | F6 交付内的证据 | 我的复跑 |
|---|---|---|
| `0x887308/0x88730C` 非视口坐标 | _w8_f6_out.txt:96-99,156-163 | out:693-694（W 恰 5+5，表面生命周期簇）+ out:798-801（消费形态）——维持 §563，复核通过 |
| `0x432A35` 线索 = Bink | _w8_f6_out.txt:22-33,49-71 | out:765-825 全复现（边界/4-dword/IAT/零交集）；out2:11-13 字符串 |
| `DSurface+0x1C` = LPDDS | _w8_f6_out.txt:98-163 | out:828-886 全复现（CreateSurface 出参 + GetSurfaceDesc + bpp 公式） |
| `[reg+0xB0/0xB4]` 196/165 W 点 | _w8_f6_out.txt:354-360 | **逐位复现**：W=196/165、Tactical 族名单一致（out:647,649） |
| 族内 6 嫌疑点 = 栈槽 | 仅文字（out 无逐条字节） | **6 条全部 `[esp+0xB0/0xB4]`，字节实证**（out:673,675,677,679,680,682）——F6 的排除为真，但其探针输出未含这 6 条现场（见异议3） |
| `0x66/67xxxx` 同偏移异族 | _w8_f6_out.txt:354-360 的 nonTac 项 | out:651-666 的 nonTacW 与「±3000B 内无 0x887324 引用」一致（out:652,654,656,658,660,662,664,666）——维持「不纳入」，双方口径一致 |

**判定：排除清单真实跑过、结论可复现。** 其中「6 嫌疑点=栈槽」与「+0xD80 族唯一写者」
两处，F6 回件内的证据链不完整（见 §5 异议 2/3），我补跑后证实其结论正确。

## 4. 反例狩猎（默认找反例的结果）

1. **字段全域普查**：对 +0xB0/+0xB4/+0xD64/68/74/78/**D80/D84/D88/D8C**/D7D 做单趟 [reg+disp] W 点普查。所有 Tactical 族名单与 F6 一致；**未发现任何**能写该单例同字段的非族写者（非族 W 点 ±3000B 内含 0x887324 引用者逐条目检：均为 `[esp+…]` 栈槽或其他类对象字段，如 0x62xxxx/0x633-0x636/0x74xxxx 簇）。注意 ±3000B 邻域法是启发式而非证明（残余风险登记于 §7）。
2. **Bink 函数体内**：0x887324 引用 = 0；对 0x6D2140/0x6D8B30 的调用 = 0（out:766）——「不是视口来源」的反例不存在。
3. **派发点唯一性方向**：全镜像 `call [reg+0x5C]` 共 170 处（out:215-381），0x55D847 是其中唯一以 `[0x887324]` 取 this 的现场（直接字节证）。（我探针的 16B 邻域列有算术瑕疵全部打成 False——已由直接字节证取代，见 §7 自纠。）
4. **几何反证**：ctor 写入的矩阵常量 0x408888CE/0x410888CE = **4.2667 / 8.5333 = 256/60、256/30 leptons/px**（out2:14-19）——与跨度公式 ÷60/÷15（数值模拟 11/11 OK，out:477-488）同源于等距菱形格 60×30px 的几何。F6 §6.2 挂起的「为何 ÷60/÷15」由本复核部分关闭；也反证 +0xD80/D84 的「格空间」语义自洽。

## 5. 异议（objections，均不动摇 LOCATED）

1. **§1.3 宿主区间写错**（F6_VIEWPORT.md:62-64）：「0x4326B3、0x4326E9 都在 3 指令级 wrapper/构造 0x4326C0..0x4326F1」——实测 `0x4326B3` 的宿主是**另一个**小构造 `0x432690..0x4326BD`（`ret 4`@0x4326BB，out:769-784），不在 0x4326C0..0x4326F1。两个宿主都是相邻电影对象构造，Bink 判定不变，但表述为假。
2. **生命周期表漏记 +0xD80 族的真实初始化**（F6_VIEWPORT.md:212）：「ctor（全部字段清 0）」对 +0xB0/B4、+0xD64..0xD78 成立，但 **+0xD80..+0xD8C 是从全局 `[0xB0CD60..0xB0CD6C]` 四连拷贝**（`0x6D1CE1..0x6D1D09`，out:48-56），不是清零；「唯一业务写者 = 0x6D8B30」只在「运行期业务写」口径成立，ctor 亦是这两组四字段的装载期写者。
3. **证据出户缺口**（F6_VIEWPORT.md:195-196）：「偏移扫描另见消费点 0x54AD9B..0x54ADEF」——`_w8_f6.py` 的 `disp_hits_field` 只扫了 0xD64/68/74/78/B0/B4 六个偏移，**+0xD80/D84/D88/D8C 的偏移扫描在 `_w8_f6_out.txt` 中不存在**；「唯一写者」与「0x54AD9B 消费点」两句在 F6 交付时无实跑出处（TASK §6 要求每个数字追到实跑命令+输出）。我补跑证实两句内容为真（out:659-666；out:890-925 逐条与 F6 登记一致：经 `call [edx+0x84]` 间接读 +0xD7C/D80/D84/D88/D90/byte D8C，且 0x54AD9B..0x54ADA7 有对 `[0xABC5E8]*2` 的 clamp）——**结论对、证据缺**。

## 6. 必须改项（mustFix，文档级）

1. 改 §1.3：`0x4326B3` 宿主 = `0x432690..0x4326BD`（ret 4 @0x4326BB），非「0x4326C0..0x4326F1 之内」。
2. 改 §3.6 创建行 + §3.2/§3.4 口径：ctor 对 +0xD80..+0xD8C 是「从 [0xB0CD60..0xB0CD6C] 装入」（0x6D1CE1..0x6D1D09），非清零；「唯一业务写者 0x6D8B30」注明限「运行期业务写」。
3. 补证据链：把 +0xD80/+0xD84/+0xD88/+0xD8C 的 `disp_hits_field` 扫描与 6 条栈槽嫌疑点的字节现场补进 F6 探针输出（或显式引用复核件 `_f6rev_probe_out.txt:659-682`），使 §3.2/§3.4/§4.4 三处断言在 F6 交付件内有实跑出处。

## 7. 复核员未验 / 自纠（诚实账）

1. `0x5AFB80` 全函数数学未重建（与 F6 §6.1 同深度）：我只核到「(viewX−60, viewY−30) 两 float 入栈、edx=&[T+0xDE4]、call 0x5AFB80、结果经 0x7C5F00(ftol)、cdq/and 0xff/add/sar 8 → +0xD80/+0xD84」的数据流（out:413-445）。
2. `0x54ADxx` 间接消费者与 `0x66/67xxxx` 同偏移异族的**类身份**双方都未证——维持登记不采信。
3. ±3000B 邻域反例狩猎是启发式：不能形式化排除「经别名指针写单例 +0xB0」的假阴性。
4. 自纠两条（我的探针，不影响对 F6 的判定）：[F] 段 16B 邻域检查一处算术错（`ins.address + 16 - 16` 应为 `ins.address - 16`）致该列全 False，已由 out:210-212 直接字节证取代；首次 RTTI 守卫误用 x64 sig 位口径致返回 None，已改 x86 正确走法重跑（out2:1-7）。
5. 工具环境披露：Mimosa 写入钩子拦截「脚本内落盘」，故两个复核探针均为 stdout 输出、由 shell 重定向落盘；零真机、零活进程、未改本目录外任何文件、未 commit。

## 8. 复核判定

**verdict = CONFIRMED；sha256BindingPresent = true；independentlyReproduced = true。**
F6 的 LOCATED 结论、全部 VA/偏移/类型/生命周期/访问证据、排除清单与勘误（TASK「8 dword」→实为 4 dword，out:789-797）全部经独立重跑成立；3 条文档级缺陷已列为 mustFix，不改变判定档。
