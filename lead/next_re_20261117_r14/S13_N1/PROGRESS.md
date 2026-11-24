# S13-N1 PROGRESS（≤50 行）

目标只读，SHA-256 73201CC0…F67476 复算一致；Python 3.12.10 + capstone 5.0.7(skipdata=True) + pefile；无 Ghidra；只写本卡目录。entry 统一大小写后与 atlas 求交；grade 只读第 5 列。
现场复算：S13∩atlas=240；named=214/240=89.17%；proved=74/240=30.83%；门槛 ceil(0.9×240)=216，差 2。残行 sub_=26（卡面“28 左右”以现场为准）。
双通道：A=PE/VA 直读字节 + capstone 入口逐条反汇编；B=YRpp 源契约 / RTTI(COL 在 vt-4, TD+8 内联串) / 调用点字符串 / 按 entry 全库冲突检索。至少一条不依赖 atlas size。

## 可定 2 行（coverage_delta.tsv，9 列，name_kind=symbolic，conflict=0）
0065B1E0 RadSiteClass::RadSiteClass() [已证]：A=ctor 体 call 0x410170 + 写 VT 0x7F0810/子表 + 注册 Array@0xB04BD0 + factory push0x74→new→call；RTTI COL=0x8086D8 TD=0x839600 TD+8=.?AVRadSiteClass@@。B=YRpp/RadSiteClass.h:93-95 JMP_THIS(0x65B1E0) 与 N_FIX 按地址同案。证据 N65_proof.txt。
00773030 WeaponTypeClass::FindIndex [已证]：A=扫 0x88756C/Count 0x887578，strcmp(Items[i]+0x24,ECX) 返 index/-1；调用点 0x46B371/0x6E39C3 传 "NukePayload"/"ChemLauncher" 后索引同数组；WeaponTypeClass ctor 0x771C70 写该数组。B=YRpp/AbstractTypeClass.h:32-38 FindIndex 契约 + WeaponTypeClass.h Array@0x887568。证据 W773030_proof.txt。
按地址全库冲突检索：0065B1E0 只有 RadSiteClass ctor/noinit_t 同案别名，无不同语义冲突；00773030 只有 sub_ 占位，无既有真名。见 name_conflict_search.txt。

## 26 条残行逐条判定（可定/不可定）
0041C230 不可定：3-dword 构造/赋值，无 VT/RTTI、无源名，调用点仅弱信号。
0041C350 不可定：double 乘积后 call 0x4CAC40，无类/源锚点。
0041C380 不可定：int→double 三元乘积后 call 0x4CAC40，无源锚点。
0041C3C0 不可定：三组 double 乘积后 call 0x4CAC40，无源锚点。
0041C430 不可定：double 乘积后 call 0x4CAC40，与 0041C350 仅输入数不同。
0041D7E0 不可定：入口 72B 内即跳转，需跨块闭合；无 RTTI/字符串。
004251F0 不可定：cell→MapClass 调用 + 单人分支 EVA，方法级语义未闭。
00452820 不可定：vector remove/compact 形态，容器模板无 RTTI 类归属。
00477BE0 不可定：写 VT 0x7E4DB8 但该地址无 COL/TD，不可据字段定名。
00487C70 不可定：写 [this+0xF8] 的 setter，类未知；越界 delete 模式不属本函数。
00487C80 不可定：读 [this+0xF8] 的 getter，类未知；越界 delete 模式不属本函数。
0048AB90 不可定：int×double×常量→0x4CAC40 包装，无源锚点。
0048ACE0 不可定：返回常量 0xFFFFFFF1，缺配对基线，不能定语义。
0048ACF0 不可定：Rules+0x16B8 乘全局 double，返回值语义未证。
004CACB0 不可定：double×标量→三角表查表，行为描述不足以定真名。
004CAD00 不可定：同上，偏移/常量不同但无配对基线。
004CAE30 不可定：double clamp + 表查找，无源级契约。
004E1100 不可定：初始化 7 个 dword 字段，无 VT/RTTI/源名。
0062AC30 不可定：长函数仅见 map/alloc 调用，缺方法级行为链。
0065B1E0 可定：RadSiteClass::RadSiteClass()，见上。
006851F0 不可定：Scenario/Rules 初始化序列，方法边界内无独立语义锚点。
006FD460 不可定：new 0x30 + vtcall，无 RTTI TD，缺类归属。
00703590 不可定：vcall + 坐标缩放，无 RTTI TD，缺源名。
0070FEE0 不可定：写 [obj+0x425/0x427/0x428] 并 vcall，字段偏移不能定语义。
0074FF50 不可定：double 加/夹到 Rules+0x698，无源级配对。
00773030 可定：WeaponTypeClass::FindIndex，见上。

优先通道结果：有界标量删除析构扫描 0 真阳性；00487C70/00487C80/00773030 的 test/delete/ret4 均为越界扫到后续函数，已剔除。入口区 INI/EVA 键串 0 条。
结果：delta 2 行使 named 214→216/240=90.00%，达到门槛；proved 74→75/240=31.25%（非本卡目标）。未改 coverage.tsv/游戏文件，未 git commit。
交付：PROGRESS.md / UNKNOWNS.md / DISAGREE.md / coverage_delta.tsv / EVIDENCE\ / work\。