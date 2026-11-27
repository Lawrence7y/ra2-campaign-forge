#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R191 四件套追加（R14_COMMON §2.196 / 台账 §1246 / LEAD_LOCK PT / 看板第 191 轮）。

★ 幂等保护（R190 g4 的教训，本轮强制）：
   写任何一份之前，**先断言目标文件的当前 sha256 等于开跑前记录的基线 sha**，
   不相等就整体 fail-closed 不写。这样即使脚本被重跑，也绝不会重复追加。
★ fail-closed：任一断言不过，四份一份都不写。
"""
import hashlib, io, os, sys, time
ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
BL = os.path.join(TIER, 'R17_LEAD_BASELINE')
R14 = os.path.join(TIER, 'R14_COMMON.md')
LED = os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md')
LCK = os.path.join(ROOT, 'lead/LEAD_LOCK')
BRD = os.path.join(TIER, 'STATUS_BOARD.md')
fails = []; n = 0
def ck(nm, c, d=''):
    global n; n += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

base = {}
for tag, p in (('R14', R14), ('LED', LED), ('LCK', LCK), ('BRD', BRD)):
    b = open(p, 'rb').read()
    base[tag] = (len(b), hashlib.sha256(b).hexdigest(), b.count(b'\r\n'), b.count(b'\n'))
print('开跑基线:', {k: (v[0], v[1][:8], v[2], v[3]) for k, v in base.items()})
ck('B1 R14_COMMON 1,669,308 B / CR 1081 / sha 737cd4e3…',
   base['R14'][:2] == (1669308, base['R14'][1]) and base['R14'][2] == 1081
   and base['R14'][1].startswith('737cd4e3'), base['R14'][:3])
ck('B2 台账 5,342,907 B / CR 337 / sha f5fa8b47…',
   base['LED'][0] == 5342907 and base['LED'][2] == 337 and base['LED'][1].startswith('f5fa8b47'),
   base['LED'][:3])
ck('B3 LEAD_LOCK 1,331,683 B / CR 137 / sha 113ab5a5…',
   base['LCK'][0] == 1331683 and base['LCK'][2] == 137 and base['LCK'][1].startswith('113ab5a5'),
   base['LCK'][:3])
ck('B4 看板 53,979 B / CR 0 / sha a1e8d8d7…',
   base['BRD'][0] == 53979 and base['BRD'][2] == 0 and base['BRD'][1].startswith('a1e8d8d7'),
   base['BRD'][:3])

# ---------- 1) R14_COMMON §2.196 ----------
S196 = '''## 2.196 R191：{172,176,240,248} 四档「为何没有副表」的判别量定出（是基类身份，不是偏移/不是无COL/不是attributes）；并订正 R190 的「镜像外 COM 接口」措辞

**一、三条候选解释被自己的反例逐一否掉.** 把 (基类, 偏移) 做成 24 行全表（16 个基类 × 各自偏移），再与「宿主类的表组里到底有没有 `mdisp == 该偏移` 的表」交叉：**（i）偏移不是判别量** —— 偏移 **4** 上 has 696 / no 10、偏移 **36** 上 has 14 / no 4，这两个是仅有的两个「两种情形并存」的偏移，其余偏移全是单边；**（ii）「基类无自身 COL」不是判别量** —— 14 个无 COL 的基类里 **9 个会拿到副表**（`IUnknown` / `IRTTITypeInfo` / `ILocomotion` / `IPiggyback` / `IHouse` / `IPublicHouse` / `IConnectionPointContainer` / `ILinkStream` / `IFlyControl`），只有 5 个从不拿到；**（iii）`BCD.attributes`（bit0 = non-virtual 基类）也不是判别量** —— 非零 BCD 共 **1,498** 条，attributes × 有无副表的 2×2 为 `{0,有:1024}` / `{0,无:72}` / `{2,有:392}` / `{9,有:6}` / `{9,无:4}`，**两个方向都有反例**（bit0=1 却有副表 6 条；attributes=0 却无副表 72 条）。且 attributes 在同一 (基类,偏移) 上**恒定**，说明它是基类属性，与宿主无关。

**二、真正的判别量是基类身份.** 16 个基类在「有无副表」上**完全一致**（跨全部偏移混合 **0 个**）。从不拿到副表、且**只**以「无副表」身份出现的基类恰 **5 个**：`StageClass`（偏移 36/172/248）、`BounceClass`（176）、`FlasherClass`（240），外加 R190 漏掉的 ATL 两个 —— `CComObjectRootBase@ATL`（偏移 4）与 `?$CComObjectRootEx@VCComMultiThreadModel@ATL`（偏移 4）。四档 {172,176,240,248} 涉及的基类恰前三个，全在上述 5 个之内。

**三、R190 的「镜像外」措辞是错的（就地订正）.** R190 写「2,111 条（34 个名）指向**本镜像之外**的 COM 接口基类」。实测：这 34 个 pTD **全部**落在 `.data` 段内（`where()` 无一为 None）、34/34 的 TypeDescriptor 可读、`pVFTable` 全等于 `0x7F9594`。**没有一条在镜像外**。2,111 这个数本身可复现（BCD 引用数恰 2111，其中 `IUnknown` 841 / `IPersistStream` 346 / `IPersist` 346 / `IRTTITypeInfo` 316 / `IClassFactory` 78）。正确说法是「**有 TypeDescriptor 但没有 COL 的基类**」。

**四、1,013 个直接槽的复用结构量化.** 1,013 个非 thunk 直接槽只指向 **278 个不同入口**；其中 **47** 个入口被 2 个以上槽共用、合计吃掉 **782 个槽（77.19%）**；用量前五：`0x410590`(78, `C2 04 00` = ret 4) / `0x410220`(78, `mov eax,[esp+4]; mov eax,[eax+0xC]; ret 4`) / `0x410230`(78) / `0x410210`(76, 取 `[this-4]` 的 vptr 再 `call [vptr+0x2C]` 的转调 thunk) / `0x410580`(75, `32 C0 C2 08 00` = xor al,al; ret 8)。单入口最多被 **78** 个不同修饰名的类共用。

**五、反控与边界.** 反控一：把「无 COL」当判据 ⇒ 报 9 个反例。反控二：把「偏移是层偏移集合里的值」当判据 ⇒ 报 3 行反例（StageClass@36 + ATL 两条@4）—— 该判据本身是循环论证，因为层偏移集合是从**实际存在的表**反推的。反控三：把 11 个「每次都拿到副表」的基类**逐一**翻面（共 11 次）⇒ 每次都使「基类层面混合 = 0」变红；未翻面时同一函数返回空（正对照）。**边界**：「基类身份是判别量」只是「16 个基类 × 24 行实测范围内一致」，**不是因果解释** —— 本轮**没有**取得「为什么这 5 个基类不需要副表」的机制。

**六、三门与落盘.** 台账 **V575 → V576**，只改 F55 一行并就地订正 ⑨(e)：statement 7,937 → **10,455 B**、limitations 5,791 → **7,691 B**、第 4 列 247 → **311 B**，**171,758 B（+4,482）/ 57 行 5 列 / CR 0 / sha `50efc728…`**（**18 断言 0 FAIL**）。重钉 `_r191/r191i_repin_v576.py` **44 断言 0 FAIL**：旧常量复算旧 MASTER `f150e6a1…` 命中旧 pin 作硬闸 → 新 MASTER **`86874cbe…`**；`FLOORS['F55']` (7937,5791)→**(10455,7691)**、`EVID['F55']` **11→14** 条、`EVIDB['F55']` 247→**311**、`ITEMS` 194→**197**、`UNIQ` 86→**89**、`LOST` 保持 **43/16**、gate_runner LEDGER 1 行、指针四字段（「530..575 / 46 份」→「**530..576 / 47 份**」、声明轮次 R190→**R191**）。**三门终态**：`check_disc` exit 0（C19 ok(50efc728/171758/V576) / C20 ok(V576)）、`facts_floors` exit 0（D7 items=197 uniq=89、D8 floor==171,758、D9+D10 双一致）、`gate_runner` G1=G2=G3=ok。

**七、自错（五处，全部当场抓出）.** **h1** `r191a_direct.py` 的 Q2a 把「自项 BCD 的 PMD.mdisp」写成 `== COL.mdisp`（正确是 `== 0`）⇒ 954/1214 FAIL；**h2** 同脚本 Q3 用 COL.mdisp 筛四档，而四档是 **BCD** 的 mdisp ⇒ 四档全 0 条；**h3** `r191b_recheck.py` 的 V1a 断言「自项 BCD+24 == 基类数组地址」，实测只 **944/1214** 成立（数组[0]==自项BCD 才是 1214/1214）—— **「把应然数当实测」第二十一次**；V3d/V3e 同样先写 5228 与 1 再断言；**h4** `r191g_deliver.py` 的 G1c 写死 `by_off[4] == [1345,10]`（实测 696/10）、G4b 写死「4 行」（实测 3 行）—— 同族第二次；**h5** `r191e_why.py` 的 E9 判据写成「基类无 COL 且偏移落在层集合」就断言"有副表"，**没检查宿主是否真有该层** ⇒ 得出的「11 个」把 StageClass@36 算进去了，而 FactoryClass 的层集合是 [0,4,8,12]，根本没有 36 —— 判据与结论不一致，该条结论已撤回。

**八、未取得（不粉饰）.** ① 本轮**无第二家族审计结论**：审计员 #463（deepseek）跑满 **36 回合** `error_max_turns` 失败（**OVERTIME 15.17 分 vs 预算 8 分**），全部主张只有主会话 + 执行员 #462/#464（hy4，两轮独立脚本，`ok=9 fail=0`）复算；② 「为什么这 5 个基类不需要副表」的机制未取得；③ `0x410450`/`0x410580`/`0x410590`/`0x4C9150` 四个实现的**游戏语义名**仍未取得；④ 1,013 个直接槽「无同槽号匹配」仍不等于「语义不同」；⑤ F23/F35 grade 未改；⑥ `coverage.tsv`/`function_atlas.tsv` 仍不可读；⑦ 86.19% 原值仍不可重算；⑧ C7 三死分支仍各 0 行；⑨ C11 十二个永不 FAIL id 未动；⑩ 「哪份是当前版」仍无人覆盖。

'''
# ---------- 2) 台账 §1246 ----------
S1246 = '''## §1246 R191：四档「无副表」的判别量定出（基类身份，三类候选解释全被反例否掉）；订正 R190「镜像外 COM 接口」措辞

**一、判别量.** (基类, 偏移) 全表 **24 行** / 16 个基类。三条候选解释逐一实测否掉：**偏移**（4 与 36 是仅有的两个混合偏移，4: has 696/no 10，36: has 14/no 4）、**无 COL**（14 个无 COL 基类里 9 个会拿到副表）、**attributes bit0**（1,498 条非零 BCD 的 2×2 两向都有反例：bit0=1 有副表 6 条、attributes=0 无副表 72 条）。真正的判别量是**基类身份**：16 个基类在有无副表上完全一致（混合 0）；从不拿到的恰 **5 个** = StageClass / BounceClass / FlasherClass + ATL 两个（R190 只报 3 个）。

**二、订正 R190.** R190 说 34 个名「指向镜像外 COM 接口基类」**是错的**：34/34 全在 `.data` 内、TD 全可读、pVFTable 全 `0x7F9594`。2,111 这个数本身可复现。正确说法：「有 TypeDescriptor 但没有 COL 的基类」。

**三、直接槽复用.** 1,013 直接槽 → **278** 个入口；**47** 个入口被 ≥2 槽共用、吃掉 **782 槽（77.19%）**；前五 `0x410590`(78) / `0x410220`(78) / `0x410230`(78) / `0x410210`(76) / `0x410580`(75)；单入口最多被 78 个类共用。

**四、落盘.** 台账 V575→V576（只改 F55，stmt 10,455 B / lim 7,691 B / 第4列 311 B / 171,758 B / sha `50efc728…` / 18 断言 0 FAIL）；重钉 44 断言 0 FAIL（MASTER `f150e6a1…`→`86874cbe…`、ITEMS 197 / UNIQ 89 / EVID 14 条 / EVIDB 311 / LOST 43-16 / 指针 530..576、47 份、R191）；三门 exit 0。

**五、未取得.** 无第二家族审计（#463 deepseek 36 回合 error_max_turns，OVERTIME 15.17'）；「为什么这 5 个基类不需要副表」的机制；四个实现的游戏语义名。

'''
# ---------- 3) LEAD_LOCK PT ----------
PT = '''## PT · R17 第 191 轮（2026-11-28 7x–8x）· {172,176,240,248} 四档「为何没有副表」的判别量定出为**基类身份**（偏移/无COL/attributes 三条候选解释各自被反例否掉）；并订正 R190 的「镜像外 COM 接口」措辞

**PT1. 🔴 交付一：三条候选解释被自己的反例逐一否掉.** `_r191/r191g_deliver.py`（**23 断言 0 FAIL**）把 (基类, 偏移) 做成 **24 行**全表（16 个基类 × 各自偏移），与「宿主类表组里到底有没有 `mdisp == 该偏移` 的表」交叉：**（i）偏移不是判别量** —— 偏移 **4** 上 has 696 / no 10、偏移 **36** 上 has 14 / no 4，这两个是仅有的「两种情形并存」偏移；**（ii）「基类无自身 COL」不是判别量** —— 14 个无 COL 基类里 **9 个会拿到副表**（IUnknown / IRTTITypeInfo / ILocomotion / IPiggyback / IHouse / IPublicHouse / IConnectionPointContainer / ILinkStream / IFlyControl），只有 5 个从不拿到；**（iii）`BCD.attributes`（bit0 = non-virtual）不是判别量** —— 非零 BCD **1,498** 条，attributes × 有无副表 2×2 = `{0,有:1024}`/`{0,无:72}`/`{2,有:392}`/`{9,有:6}`/`{9,无:4}`，**两向都有反例**。

**PT2. ✅ 交付二：判别量是基类身份，且 R190 的「3 个」漏了 2 个.** 16 个基类在有无副表上**完全一致**（跨全部偏移混合 **0 个**）。从不拿到副表的恰 **5 个**：StageClass（偏移 36/172/248）、BounceClass（176）、FlasherClass（240），外加 R190 漏掉的 ATL 两个 —— `CComObjectRootBase@ATL` 与 `?$CComObjectRootEx@VCComMultiThreadModel@ATL`（各在偏移 4）。四档涉及的基类恰前三个，全在该集合内。

**PT3. 🔴 交付三：R190「2,111 条 / 34 个名指向镜像外 COM 接口基类」是错的，已就地订正.** `_r191/r191d_td.py`（**16 断言**）：这 34 个 pTD **全部**落在 `.data` 段（`where()` 无一为 None）、34/34 的 TypeDescriptor 可读、`pVFTable` 全 == `0x7F9594`。**没有一条在镜像外**。2,111 这个数本身可复现（BCD 引用数恰 2111：IUnknown 841 / IPersistStream 346 / IPersist 346 / IRTTITypeInfo 316 / IClassFactory 78 …）。正确说法是「**有 TypeDescriptor 但没有 COL 的基类**」；台账 F55 ⑨(e) 已就地追加订正句。

**PT4. ✅ 交付四：1,013 个直接槽的复用结构量化.** 只指向 **278** 个不同入口；**47** 个入口被 ≥2 槽共用、吃掉 **782 槽（77.19%）**；前五 `0x410590`(78, `C2 04 00`=ret 4) / `0x410220`(78, `mov eax,[esp+4]; mov eax,[eax+0xC]; ret 4`) / `0x410230`(78) / `0x410210`(76, 取 `[this-4]` 的 vptr 再 `call [vptr+0x2C]`) / `0x410580`(75, `32 C0 C2 08 00`=xor al,al; ret 8)。单入口最多被 **78** 个不同修饰名的类共用。另：同一入口在主表的出现次数是 204 次但只涉及 **1 个槽**（`0x4c9150`，LocomotionClass@4 槽 29）—— 槽级与出现级两个口径不可混用。

**PT5. ✅ 落盘 + 重钉 + 三门（台账 V575 → V576）.** 只改 F55 一行并就地订正 ⑨(e)：statement **7,937 → 10,455 B**、limitations **5,791 → 7,691 B**、第 4 列 **247 → 311 B**，**171,758 B（+4,482）/ 57 行 5 列 / CR 0 / sha `50efc728…`**（**18 断言 0 FAIL**）。重钉 `_r191/r191i_repin_v576.py` **44 断言 0 FAIL**：旧常量复算旧 MASTER **`f150e6a1…`** 命中旧 pin 作硬闸 → **`86874cbe…`**；`FLOORS['F55']` (7937,5791)→**(10455,7691)**、`EVID['F55']` **11→14**、`EVIDB['F55']` 247→**311**、`ITEMS` 194→**197**、`UNIQ` 86→**89**、`LOST`/`LOST_UNIQ` 保持 **43/16**、gate_runner LEDGER 1 行、指针四字段（「530..575 / 46 份」→「**530..576 / 47 份**」、声明轮次 R190→**R191**）。**三门终态**：`check_disc` exit 0（**C19 ok(50efc728/171758/V576)** / **C20 ok(V576)**）、`facts_floors` exit 0（D7 items=197 uniq=89、D8 floor==171,758、D9+D10 双一致）、`gate_runner` **G1=G2=G3=ok**。看板 **249 行 < 260** ⇒ 本轮不归档。

**PT6. 📌 自错 h1..h5（五处，全部当场抓出，无一条进入结论）.** **h1** `r191a_direct.py` Q2a 把「自项 BCD 的 PMD.mdisp」写成 `== COL.mdisp`（正确是 `== 0`）⇒ 954/1214 FAIL；**h2** 同脚本 Q3 用 COL.mdisp 筛四档，而四档是 **BCD** 的 mdisp ⇒ 四档全 0 条；**h3** `r191b_recheck.py` V1a 断言「自项 BCD+24 == 基类数组地址」，实测只 **944/1214**（数组[0]==自项BCD 才是 1214/1214）—— **「把应然数当实测」第二十一次**，V3d/V3e 同样先写 5228 与 1 再断言；**h4** `r191g_deliver.py` G1c 写死 `by_off[4]==[1345,10]`（实测 696/10）、G4b 写死「4 行」（实测 3 行）—— 同族第二次；**h5**（最需记住的一处）`r191e_why.py` E9 判据写成「基类无 COL 且偏移落在层集合」就断言"有副表"，**没检查宿主是否真有该层** ⇒ 得出的「11 个」把 StageClass@36 算进去了，而 FactoryClass 的层集合是 [0,4,8,12]、根本没有 36 —— **判据与结论不一致**，该条结论已撤回。另修 `r191e` 的 `Counter - set` TypeError 一处、`r191h_write_v576.py` 的反引号未闭合 SyntaxError 一处。

**PT7. 📌 未取得（不粉饰）.** ① 审计员 **#463**（deepseek）跑满 **36 回合** `error_max_turns` 失败（**OVERTIME 15.17 分 vs 预算 8 分**），本轮**无第二家族结论**，全部主张只有主会话 + 执行员 **#462/#464**（hy4，各自独立脚本，`ok=9 fail=0`，两轮 Q1-Q6 与本会话同值）复算；② 「**为什么**这 5 个基类不需要副表」的机制未取得 —— 本轮只把三条候选解释否掉，没有给出正面机制；③ `0x410450`/`0x410580`/`0x410590`/`0x4C9150` 四个实现的**游戏语义名**仍未取得；④ 1,013 个直接槽「无同槽号匹配」仍**不等于**「语义不同」；⑤ F23/F35 grade 未改；⑥ `coverage.tsv`/`function_atlas.tsv` 仍不可读；⑦ 86.19% 原值仍不可重算；⑧ C7 三死分支仍各 0 行；⑨ C11 十二个永不 FAIL id 未动；⑩ 「哪份是当前版」仍无人覆盖。

'''
# ---------- 4) 看板第 191 轮 ----------
BRD_SEC = '''## 🟢 R17 第 191 轮（2026-11-28 7x–8x）· 上一段留下的「四档为何没有副表」把三个候选解释全否掉，判别量定出为**基类身份**；同时订正 R190 一处**措辞性错误**（「镜像外 COM 接口」实为镜像内「有 TD 无 COL」）

**交付一·三条候选解释各自被反例否掉.** `_r191/r191g_deliver.py`（**23 断言 0 FAIL**）：(基类,偏移) 全表 **24 行** × 有无副表交叉 —— **偏移**不是（偏移 4: has 696/no 10、36: has 14/no 4，仅有的两个混合偏移）、**无 COL** 不是（14 个无 COL 基类里 **9 个会拿到副表**）、**attributes bit0** 不是（1,498 条非零 BCD 的 2×2 两向都有反例：bit0=1 有副表 6 条、attributes=0 无副表 72 条）。

**交付二·判别量是基类身份.** 16 个基类在有无副表上**完全一致**（混合 **0**）；从不拿到副表的恰 **5 个**：StageClass / BounceClass / FlasherClass + **R190 漏掉的 ATL 两个**。四档 {172,176,240,248} 涉及的基类恰前三个。

**交付三·R190 措辞订正.** 34 个名并非「指向镜像外」：**34/34 全在 `.data` 段内**、TD 全可读、pVFTable 全 `0x7F9594`。2,111 这个数本身可复现。台账 F55 ⑨(e) 已就地追加订正句。

**交付四·直接槽复用量化.** 1,013 直接槽 → **278** 个入口；**47** 个入口被 ≥2 槽共用、吃掉 **782 槽（77.19%）**；单入口最多被 **78** 个类共用（`0x410590` / `0x410220` / `0x410230`）。

**落盘 · 三门.** 台账 **V575 → V576**（只改 F55，stmt 10,455 B / lim 7,691 B / 第4列 311 B / **171,758 B** / sha `50efc728…` / 18 断言 0 FAIL）；重钉 **44 断言 0 FAIL**（MASTER `f150e6a1…`→**`86874cbe…`**、ITEMS **197** / UNIQ **89** / EVID **14** 条 / EVIDB **311** / LOST 43-16 未变 / 指针 **530..576、47 份**、声明轮次 **R191**）；**三门 exit 0**（C19 ok(50efc728/171758/V576)、C20 ok(V576)、D7-D10 双一致、G1=G2=G3=ok）。看板 **249 < 260** ⇒ 本轮不归档。

**自错五处（当场全抓出）：** h1 自项 BCD 的 mdisp 写成 `== COL.mdisp`（应为 `== 0`）；h2 四档用 COL.mdisp 筛而四档是 BCD 的 mdisp；h3/h4 **「把应然数当实测」两次**（944/1214 vs 1214；by_off[4] 实测 696 而我先写 1345）；h5 最需记住 —— 判据写成「基类无 COL 且偏移在层集合」就断言有副表，**没检查宿主是否真有该层**，把 StageClass@36 算了进去而 FactoryClass 层集合根本没有 36，该结论已撤回。

**未取得**：① 审计员 **#463**（deepseek）跑满 **36 回合** `error_max_turns` 失败（**OVERTIME 15.17 分 vs 预算 8 分**），本轮**无第二家族结论**（只有主会话 + 执行员 **#462/#464** hy4，各自独立脚本 `ok=9 fail=0`）；② 「**为什么**这 5 个基类不需要副表」的机制未取得（只否掉了三条候选，没给出正面机制）；③ 四个实现的游戏语义名仍未取得；④ 1,013 直接槽「无同槽号匹配」不等于「语义不同」；⑤ F23/F35 grade 未改；⑥ `coverage.tsv`/`function_atlas.tsv` 仍不可读；⑦ 86.19% 原值不可重算；⑧ C7 三死分支各 0 行；⑨ C11 十二个永不 FAIL id 未动；⑩ 「哪份是当前版」仍无人覆盖。

'''
# ---------- 断言：现盘尚未含本轮标记 ----------
ck('C1 R14_COMMON 尚未含 2.196', '2.196 R191' not in open(R14, encoding='utf-8', errors='replace').read())
ck('C2 台账尚未含 §1246', '§1246 R191' not in open(LED, encoding='utf-8', errors='replace').read())
ck('C3 LEAD_LOCK 尚未含 PT · R17 第 191 轮',
   'PT · R17 第 191 轮' not in open(LCK, encoding='utf-8', errors='replace').read())
ck('C4 看板尚未含第 191 轮',
   'R17 第 191 轮' not in open(BRD, encoding='utf-8', errors='replace').read())
# 交替：新段里不应有反引号不配对
for tag, s in (('2.196', S196), ('§1246', S1246), ('PT', PT), ('board', BRD_SEC)):
    ck('C5 %s 反引号成对' % tag, s.count('`') % 2 == 0, s.count('`'))

def newtext(path, sec, cr_ok):
    """四份文件的 CR 数是**固定不变量**：追加段一律用纯 LF、不含任何 CR，
    因此追加后 CR 计数必须与追加前**逐值相等**（不是加上段内换行数）。"""
    b = open(path, 'rb').read()
    t = b.decode('utf-8')
    assert sec.count('\r') == 0, '追加段含 CR'
    return (t.rstrip('\r\n') + '\n\n' + sec).encode('utf-8')

jobs = []
jobs.append(('R14', R14, S196, True))
jobs.append(('LED', LED, S1246, True))
jobs.append(('LCK', LCK, PT, True))
jobs.append(('BRD', BRD, BRD_SEC, False))
plans = []
for tag, path, sec, cr in jobs:
    nb = newtext(path, sec, cr)
    plans.append((tag, path, sec, cr, nb))
    ck('C6 %s 追加后 CR 数与基线逐值相等（CR 是不变量）' % tag,
       nb.count(b'\r\n') == base[tag][2], (nb.count(b'\r\n'), base[tag][2]))
    ck('C6b %s 追加段本身不含 CR' % tag, sec.count('\r') == 0)
    ck('C7 %s 新标记恰 1 次' % tag, nb.decode('utf-8').count(sec.split('\n')[0]) == 1)
    ck('C7b %s 追加后体量按构造闭合（旧 - 尾换行 + 2 + 新段）' % tag,
       len(nb) == base[tag][0] - (len(open(path, 'rb').read())
                                  - len(open(path, 'rb').read().rstrip(b'\r\n'))) + 2 + len(sec.encode()),
       len(nb))
ck('C8 看板追加后行数 <= 300', plans[3][4].count(b'\n') <= 300, plans[3][4].count(b'\n'))

if fails:
    print('★ fail-closed：%d 条未过，四份都不写' % len(fails)); sys.exit(1)
print('== 写盘 ==')
stamp = time.strftime('%Y%m%d_%H%M%S')
for tag, path, sec, cr, nb in plans:
    cur = open(path, 'rb').read()
    ck('W0 %s 现盘 sha 仍等于开跑基线（幂等保护）' % tag,
       hashlib.sha256(cur).hexdigest() == base[tag][1],
       (hashlib.sha256(cur).hexdigest()[:8], base[tag][1][:8]))
    if fails:
        print('★ 目标已被改动，中止'); sys.exit(1)
    bak = os.path.join(BL, '%s.before_r191_fourpiece_%s.bak' % (tag, stamp))
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f: f.write(cur)
    ck('W1 %s 备份 sha 一致' % tag,
       hashlib.sha256(open(bak, 'rb').read()).hexdigest() == hashlib.sha256(cur).hexdigest())
    assert open(path, 'rb').read() == cur
    open(path, 'wb').write(nb)
    ck('W2 %s 回读一致' % tag,
       hashlib.sha256(open(path, 'rb').read()).hexdigest() == hashlib.sha256(nb).hexdigest())
    ck('W3 %s 新标记恰 1 次（回读）' % tag,
       open(path, encoding='utf-8').read().count(sec.split('\n')[0]) == 1)

print('\n断言 %d 条，FAIL %d 条' % (n, len(fails)))
for tag, path, sec, cr, nb in plans:
    b = open(path, 'rb').read()
    print('  %s %d B / CR %d / LF %d' % (tag, len(b), b.count(b'\r\n'), b.count(b'\n')))
sys.exit(1 if fails else 0)
