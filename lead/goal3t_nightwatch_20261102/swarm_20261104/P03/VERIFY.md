# P03-VERIFY · 独立核验：CurrentFrame 10 写点全归因 + 「唯一 inc」——全部关键事实字节级复现成立，ATLAS §8.4 勘误两条均属实

- 被核验件：`lead/goal3t_nightwatch_20261102/swarm_20261104/P03/REPORT.md`（P03 自报 headline / keyFacts / prediction）
- 核验人：核验员-P03（独立探针复算，未复用 P03 原脚本逻辑；原脚本仅 `_p2_funcs.py` 读了源码以消解 E8 口径差）
- 母本：`ra2youli/gamemd.exe`（SHA-256 前缀 `73201cc021497c95` 自证一致，全程只读，零真机）
- **裁决：CONFIRMED**（9 条 keyFact 全部复现；发现 4 处轻微不完整/表述偏差，均不动摇结论，见 §3/§4）

---

## 0. 现场自证

| 检查 | 命令 | 结果 |
|---|---|---|
| 零真机 | `tasklist \| grep -i -E "gamemd\|ra2loader\|YURI"` | 无输出，grep exit=1 ✓ |
| 母本一致 | `Engine()` 内建 SHA-256 断言（`_v1_site.py`） | `73201cc021497c95` ✓ |
| 引擎覆盖 | `python -I -X utf8 _v1_site.py`（及 `_v2/_v3/_v4/_v5/_v8` 各次独立构建流） | `coverage = 100.00% / 1394120 insns / resync=66` ✓（5 次复建全部一致） |
| disp_hits | 同上 | `total=1007 / W=10 / R=997` ✓ |

## 1. 结论（逐 keyFact）

| # | keyFact | 裁决 | 核心证据 |
|---|---|---|---|
| KF1 | 现场自证（tasklist / coverage / 1007 引用 10W997R / 10 写点字节 / SHA） | **CONFIRMED** | 10 写点 12 字节现场逐一 dump，与 REPORT §0.4 表**逐字节一致**（含 3 处 `c70584eda80000000000`） |
| KF2 | 唯一读-加-写链 0x55DE73→0x55DE7E→0x55DE81 + 四旗标守卫 + reach_without 冻结出口 | **CONFIRMED** | 锚点字节 `8b1584eda800`/`42`/`891584eda800`；10 写点 mnemonic 普查 = 10×`mov`（无 `inc/add [mem]` 直接形式）；四旗标检查链 0x55DE4F/58/61/6A 四连 `mov al,[flag]; test al,al; jne 0x55DEC8`（全 .text 仅此 4 条跳向 0x55DEC8）；0x55DEC8 块 `mov byte [0xABCD58],0; …; mov al,1; ret 0x55DEDB`；`reach_without` 三种实现（eng 原生 + 本人两种 CFG 构建）一致输出 `{0x55D877, 0x55DEDB}`；**inc/write 对窗口 [0x55DE73,0x55DE82) 零跳入边** |
| KF3 | 9/10 写点写 0（含 W4 341 指令反向切片） | **CONFIRMED** | W3/W6/W9 字面 `c705…00000000`；**W4 切片独立复建 = 341 条指令（与自报数字完全一致），切片内 ebp 唯一写点 = 0x5BACBE `xor ebp,ebp`**；W4 写窗 95 条跳入边**全部在宿主内部**（切片 CFG 完备）；W1 切片 865 条、ebx 4 个 def 全为 `xor ebx,ebx`（两处 `jmp 0x52D9C9` 为 init 内部回跳重试环，非外来入口）；W5 `xor esi,esi`@0x5E54E5 支配写点（唯一疑似跳入边 0x5E54C8 为 `call` 指令中字节的假阳性）；W7 写点前 2 字节 `xor esi,esi`@0x684669、零跳入边；W8 `xor ebp,ebp`@0x68675F、零跳入边；W10 `xor eax,eax`@0x797541 → 12 条指令直线到写点，中间零 call 零 eax 定义 |
| KF4 | 宿主定界（E8 头集 6719 + 10 宿主 rets/callers/边界） | **CONFIRMED** | **decoded-call 口径唯一目标 = 6719，与自报完全一致**（68244 条解码 call；raw 字节扫描口径=7279，系两种口径之差，见 §3-①）；10 宿主 rets 数与地址、E8 调用者数与地址**逐项命中**：W2=3 rets/6 callers（0x48CE8A+0x608206/0x60D407/0x62314E/0x623D72/0x624271）、W1=15/2、W3=3/1、W4=5/1、W5=4/3、W6=**0**/5、W7=2/1、W8=3/1、W9=4/1、W10=1/**0**；W6 尾 `jmp 0x6B8B10`@0x5E74D9、下一头 0x5E74E0=`81ecf8010000`(sub esp,0x1F8)；W3 等待环回边 (0x5B72C2→0x5B724D)；0x77F900 调用者=39；W9 调用侧守卫 `[0xB77E28]==2 && [0xB77E27]!=0 && [0xB77E26]==0`@0x7800D1-0x7800EC 逐字节吻合 |
| KF5 | 间接写路径：push 0xA8ED84 ×2 + 字节计数 1009 闭合 | **CONFIRMED** | `push 0xA8ED84` 全 .text 恰 2 处：0x67F819（`call [edx+0x10]`）与 0x67FA19（`call [edx+0xc]`），形态 `push 0; push 4; push <g>; push esi; call [reg+slot]`；错误路径 `jl 0x67F9B8`/`jl 0x67FD11` ✓；hostB 在流读 [0xA8ED78] 后调 `0x6CF240(0xB0C110, buf)` 两次 @0x67F9E8/0x67FA0E ✓；8 全局序列化清单逐个 push-imm 计数：hostA 8×1、hostB 8×1（0xA8ED78/0xA83D4C 各 ×2）✓；调用链 0x67D421@0x67D300←0x67D1AF@0x67CEF0、0x67E8B5@0x67E730←0x67E659@0x67E440 ✓；`.text` 内 `84eda800` = **1009** = 1007 disp + 2 push；`disp_hits_field`=1007（无 [reg+disp] 家族）、`mov reg,0xA8ED84`(B8+r) = 0、**全文件 dword 0xA8ED84 = 1009 处且全部落在 .text（无任何数据段指针表持有该地址）** |
| KF6 | measure 窗：dispatcher 帧循环 + 0x55CFD0 四变体 + 触发链 | **CONFIRMED** | 0x48CCC0 循环体逐字节：`0x48CE8A call 0x55D360` / `test al,al; je 0x48CE9C` / `call 0x55CFD0` / `jne 0x48CEAA` / `call 0x48C8B0` / `call 0x55CFD0` / `0x48CEA8 je 0x48CE8A`（回边）✓；`xor ebx,ebx`@0x48CCD4 且 0x48CDD0-0x48CE8A 间 ebx 只读不写（bl=0 实参成立）✓；`Game loop finished. Average FPS = %d\n`@0x81D514 ✓；0x55CFD0 头 `mov eax,[g]`+`test eax,0x3FF`@0x55CFD8、函数内恰 1 处 R ✓；四写块 0x55D123/0x55D1B1/0x55D219/0x55D25C 各清四旗标（`mov byte [flag],bl` ×4）并 `mov byte [0xABCD58],bl`@0x55D15F/0x55D1ED/0x55D245/0x55D292 ✓；触发接线 0x55D14A→0x685670、0x55D1D8→0x685DC0、0x55D236→0x6863E0、0x55D283→0x686570 ✓；`call 0x683AB0` 全图 6 站点：init×2（0x52E718/0x52E745）+ 0x685670 内×2（0x685C54/0x685C71）+ 0x685DC0 内×1（0x686296）+ 0x6863E0 内×1（0x6864FC）——与「三者各 1-2 处」一致，0x686570 无加载器调用 ✓；'Disconnect_Gracefully'(0x82A044) 在 0x55D299 被推参（状态机内、经 0x4068E0 空桩打印）✓ |
| KF7 | ATLAS §8.4 地址勘误（散文 0x0055DE73 错、0x55DE7E/0x55DE81 对） | **CONFIRMED** | `docs/re/ARCHITECTURE_ATLAS.md:2008` 散文「全镜像唯一定常递增写入点位于 0x0055DE73」；`:2010` 该地址=`8B 15 84 ED A8 00 mov edx,[0xA8ED84]`（**读**）；`:2012` `0x0055DE7E: 42 inc edx ; ★★★ CurrentFrame++`；`:2014` `0x0055DE81: 89 15 … 写回`——散文与自带代码块自相矛盾，P03 判定正确。**补充：同类错址散文还见于 :260、:1927（mermaid 节点）、:2418、:2819，勘误范围宜扩大（见 §3-④）** |
| KF8 | ATLAS §8.4「9 处均为载入地图、读取存档或开局清零」需修正 | **CONFIRMED** | `:2007` 原句在案。10 个 disp 写点内确无一处是读档（唯一存读档写=KF5 序列化路径，不在 10 写点内）；载入地图 ✓（W7 宿主 0x684620 含 '.SED'@0x83DA88、被 0x683AB0 调用、0x683AB0 被 init 与 0x685670/0x685DC0/0x6863E0 调用）；开局清零 ✓（W1=init，INGAME=1@0x52D9D7 同块）；W3/W4/W5/W6/W9 归「任务/会话转换复位」有调用链支撑（W4='ModemHost.StartGame(enter)'@0x82CC04 + 'LoadGame = %s'@0x82CBF4 + 'D:\ra2mdpost\ModemHst.cpp'@0x82C9A4；W6='Pregame setup for %d players.'@0x831A60；W9=会话复位守卫）；W10 死代码 ✓ |
| KF9 | 0x4068E0/0x6B8B10 空桩 + [0xA8B24C]=2 同现 | **CONFIRMED** | 两处均为 `c3` + nop 雪橇（0x4068F0=`8b44240c` 与 ATLAS §8.6 QC4 补证一致）；0x4068E0/0x6B8B10 的 push-fmt+call 现场无副作用 ✓；[0xA8B24C] 字面 imm=2 写点 6 处：0x52E3D2（W1 宿主）、0x52F467、0x5B7333（W3+10B）、0x5BB212（W4+6B）、0x5E5515（W5+6B）、0x5E74C3（W6 宿主）——「6 处同现」成立 ✓ |
| 附加 | 「其余 9 宿主写点前 0 读」 | **CONFIRMED** | 逐宿主审计：W3-W10 共 8 宿主 0 读；W1 唯一 1 读在 0x52DA3C（写点**之后**）——「写点之前 0 处」精确成立；W2=3 读（0x55D3BB/0x55D8C9/0x55DE73），前两者去向字节级核对（`cmp [0xA8E2E4]`（静态 0、全镜像 0W）+ timeGetTime 存 [0xA8B55C]；`and eax,7`+GameMode==4→call 0x542520），均不流向写回 |
| 附加 | prediction（真机采样差 ∈{0,+N}，负值/大跳仅可归因读档序列化） | **静态前提全部成立；动态部分零真机不可测** | 局内稳态唯一周期写=W2(+1)、其余写点均写 0（跳变到 0，非任意 N）、唯一非零覆盖写=序列化路径——三要素字节级闭环；采样预测本身属真机实验，本轮无法执行（铁律禁止），与原报告将其列为 prediction 的定性一致 |

## 2. 证据（关键字节摘录）

1. **三锚点**（`_v1_site.py` 实测）：`0x55DE73=8b1584eda800`、`0x55DE7E=42`、`0x55DE81=891584eda800`。
2. **四旗标守卫链**（`_v6_align.py` 模式扫描 + `_v5_run.log` 流对齐）：
   ```
   0x55de4f  a0493da800  mov al,[0xa83d49]; 84c0; 7570 → jne 0x55dec8
   0x55de58  a0d0eca800  mov al,[0xa8ecd0]; 84c0; 7567 → jne 0x55dec8
   0x55de61  a0c0418b00  mov al,[0x8b41c0]; 84c0; 755e → jne 0x55dec8
   0x55de6a  a0483da800  mov al,[0xa83d48]; 84c0; 7555 → jne 0x55dec8
   0x55de73  8b1584eda800 mov edx,[0xa8ed84]   ← 读，紧贴守卫链尾
   ```
   全 .text 跳向 0x55DEC8 的站点**恰为这 4 条**（`_v5_run.log`）。
3. **W4 切片**（`_v3_rest.py` 独立实现，非 call 边 + 全 jcc/jmp 双边前驱闭包）：`slice_size=341`，EBP def 集合 = `{0x5BACBE: xor ebp,ebp}`；W4 写窗 (0x5BACC0,0x5BB20C] 的 95 条跳入边全部源于宿主内部（`_v7_raw2.py` 全列表核对，OUTSIDE_host=[]）。
4. **字节账闭合**（`_v1_site.py`/`_v0_fast.py`）：`.text` 内 `84eda800` = 1009；全文件 dword 0x00A8ED84 = 1009 处全部位于 .text（Counter 仅 .text 项）→ 无数据段指针别名；`push 0xA8ED84` = 2 处（0x67F819/0x67FA19）。
5. **宿主/调用者全表**（`_v3_out_partAB.txt`）：与 REPORT §2.1 表逐格一致（rets 数、ret 地址、caller 数、caller 地址、下一头字节、W6 尾 jmp、W3 回边、0x77F900=39）。
6. **ATLAS 原文**：`docs/re/ARCHITECTURE_ATLAS.md:2006-2015`（§8.4）、`:2038-2040`（§8.6 `0x004068E0: C3`、`0x004068f0 = 8B 44 24 0C`，实测字节一致）。

## 3. 与本仓既有记载的对账（含发现的轻微出入）

| 项 | 对账 |
|---|---|
| ① E8 头集 6719 | **一致**——REPORT 的口径是「解码后 call 指令的目标」（`_p2_funcs.py:14-19` 遍历流），我按同口径复算 = **6719 精确命中**（68244 条 call）。我最初 raw 字节扫描得 7279，差 560 个「位于其它指令操作数中的 E8 字节」假目标——两种口径都对，REPORT 数字在其声明的方法下正确，无口径偷换 |
| ② 已定谳基线（1007/10、3 rets+冻结出口、IAT Sleep/timeGetTime、MLF 边界） | **全部复算一致**；未复核项（0xA8ED80 唯一写者 0x7778CE、[0xA8B230] 1293/3）REPORT 已如实声明「范围外未动」，本轮亦未动 |
| ③ [0xB07784] 写者 | REPORT 列 0x55DE94(mov edi)+地图族 4 处全存 0 ✓；**另有 2 处 REPORT 未列**：0x69BB0F(`mov [0xB07784],edx`，edx 值未追) 与 0x69BBD2(mov 0)。该事实仅用于 REPORT §4 一条**已明标 [推测]** 的未定谳项，不影响任何定谳结论，但「地图族写者全存 0」的完备性应加此注 |
| ④ ATLAS §8.4 勘误范围 | 散文错址句不只在 §8.4：`:260`、`:1927`（mermaid「CurrentFrame++ 唯一推进点 (0x0055DE73)」）、`:2418`、`:2819` 同样写 0x55DE73——P03 只报了 §8.4 两处，**勘误实际应覆盖 5 处**（P03 结论方向正确、范围略窄） |
| ⑤ 'Disconnect_Gracefully' 与 0x686570 | 串(0x82A044)是由状态机在 `call 0x686570`@0x55D283 **之后** push（0x55D299，经 0x4068E0 空桩实为无输出），不在 0x686570 函数体内；REPORT 的「0x686570（'Disconnect_Gracefully'，不加载）」为松表述，实质（该支线属断线路径、不调加载器）正确 |
| ⑥ hostB 校验调用次数 | REPORT 称 0x6CF240 在读 [0xA8ED78] 后「调两次（0x67F9E8/0x67FA0E）」✓；函数后段还有 3 处（0x67FADE/0x67FBC2/0x67FC84）未提——不影响「读后验→Load 侧」的次序论证 |

## 4. 诚实账（核验侧）

- **没做**：全部真机动态验证（铁律）；prediction 的采样实验无法离线执行；REPORT 自报的 0xA8ED80/[0xA8B230] 基线（其已声明范围外）未复核；W5 祖链 0x7A41A0←0x785410@0x786390、W4 祖链 0x5EF240×2 只核了 REPORT 给出的第一层 call 站点，更上层未追；0x6CF240/0x4790E0 语义未定谳（0x4790E0 行为字节级吻合 REPORT：`cmp eax,-2→al=1`、`cmp byte [0x89E3A0],1→al=1`，[0x89E3A0] 唯一写者 0x52F7AF ✓）。
- **静态方法残留盲区**（REPORT §4 已自认，本轮确认无法用静态手段排除）：rep movs/运行期计算指针别名理论上可绕过 disp 普查；已用「全文件 dword 0xA8ED84=1009 全在 .text、无 mov reg,imm 形态、无 [reg+disp] 家族」把**地址立即数形态**的总体收全，但「某寄存器运行期恰好持有 0xA8ED84」不能静态穷尽——REPORT 的 1009 闭合论证在其声明口径内成立。
- **核验过程自身两次探针崩溃**（`_v4_rest2.py` 缺函数定义、`_v6_align.py` capstone detail 未开），均已修复重跑；相关检查全部有最终通过输出。`_v1_site.py` 中我自己的「extra locs」初版对照逻辑有 bug（拿字节偏移比指令地址），已在 `_v0_fast.py`/`_v7_raw2.py` 用覆盖指令/全列表方式重做——**原报告无此问题**。
- **可能出错处**：我对 `eng.disasm(0x55DE60,…)` 起始的解码一度怀疑共享引擎流错位（`mov al,[0x41c0]` 假象），经原始字节+全 .text jne 目标扫描证伪——那是「从指令中段起解」的假象，**共享引擎流在该区段对齐正确**（`_v5_run.log` 流边界与 `_v6_align.py` 模式扫描互证）。
- **冲突**：无推翻性冲突。§3-③④⑤⑥ 为补充/加注，不改裁决。

## 5. 复算入口

全部核验探针在 `lead/goal3t_nightwatch_20261102/swarm_20261104/P03/`，`python -I -X utf8 <脚本>`（零真机、只读母本）：

| 脚本 | 复算内容 | 输出 |
|---|---|---|
| `_v0_fast.py` | 空桩/IAT/u32/格式串/全文件 dword 普查/push 位点/1009 计数 | stdout |
| `_v1_site.py` | SHA+coverage+1007/10/997+10 写点字节+mnemonic 普查+锚点 | stdout |
| `_v2_all.py` | RMW 链+inc 对零入边+MLF 尾+reach_without×3+两读点上下文 | `_v2_out_part1.txt` |
| `_v3_rest.py` | 6 写点独立切片（含 W4=341）+E8 头集+10 宿主 rets/callers+守卫/回边/39 callers | `_v3_out_partAB.txt` |
| `_v4_rest2.py` | push 路径现场+序列化+调用链+dispatcher+四变体+四旗标写者+0x4790E0 | `_v4_run.log` |
| `_v5_final.py` | 四旗标 MLF 命中+0x55DEC8 跳源+循环体+0x683AB0 六站点+8 全局 push 计数+写窗入边+**decoded-call 6719** | `_v5_run.log` |
| `_v6_align.py` | 守卫链模式扫描（A0/84C0/75→0x55DEC8 四连） | stdout |
| `_v7_raw2.py` | W4 入边全列表（95 全内部）+0x82A044 引用+0x686570/0x52D9A0 反汇编+W1 回跳现场 | stdout |
| `_v8_last.py` | 9 宿主写点前 0 读审计+[0xABCD58] 写者+MLF 头 INGAME 早退 | `_v8_run.log` |

最小三行：
```python
import sys; sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine
eng = Engine(); print(eng.coverage)            # (100.0, 1394120, 66)
print(len(eng.disp_hits(0xA8ED84)))            # 1007
print(eng.rd(0x55DE7E,1).hex(), eng.rd(0x55DE73,6).hex(), eng.rd(0x55DE81,6).hex())
# 42 8b1584eda800 891584eda800
```
