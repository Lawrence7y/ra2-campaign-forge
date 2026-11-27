#!/usr/bin/env python3
"""R145 O：向 lead/LEAD_LOCK 追加下一字母段 ## OD（CR 保持 137）。"""
import hashlib, io, json, os, re, time
BASE = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
LK = '/home/t628/projects/ra2-campaign-forge/lead/LEAD_LOCK'
BL = os.path.join(BASE, 'R17_LEAD_BASELINE')
cc = []
def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c: cc.append(n)

SEC = """## OD · R17 第 145 轮（2026-11-27 02:0x–03:0x）· R144 残余 5 张的第 5 张根因是**解析器整类丢弃负位移写入**（单条指令即可复现）；修好后并集 1,214 / 残余 4（全是 VTS 误收）/ 真分母 1,214 覆盖 100%，并新增「持久 vs 瞬态装表」区分（1 张虚表只有瞬态站点）

OD1. ✅ **开局以磁盘为准**：R144 已完整收口（五项 CR 1081/337/137/0/2952 全绿、`check_disc.py` exit 0、C7d `636db13b`、C16 `05b54f35`、看板 216 行）。提示词标的 R137 六项已在 R137..R142 落盘，故按 COMPACT_STATE R144 下轮待办第 1 条（`0x7E6060` 的装表位置）定向。`MAX_SUBAGENTS=4`（1,804 MB），实派 2 支（exec + audit），峰值 2，未超上限。

OD2. 🔴 **根因一句话：`r143lib.norm()` 的空白压缩字符类 `[+,*]` 不含 `-`。** 于是 capstone 打印的 `dword ptr [eax - 8],0x7e6060` 里 minus 两侧空格留着 ⇒ 十进制→十六进制归一 `([+-])(\\d+)` 因 `- 8` 失配 ⇒ `RE_STORE`（要求 `]` 前紧邻基址/位移）整条拒收。**最小反例**：`RE_STORE.match('dword ptr [eax - 8],0x7e6060')` → `None`；同一操作写成 `[eax-0x8]` → 匹配。影响面 **437** 个负位移立即数写站点，其中 `imm ∈ VTS` **5 站点 / 4 张表**。**这是同一族第 4 次（R143 S-295 是形态判断顺序、R144 S-303 是 RE_STORE 吞 call 操作数、S-308 是先宽后窄，本轮是符号空白）—— 共同病根是「用一个窄正则去认一个宽语法」。**

OD3. ✅ **`0x7E6060` 的装表站点就是 `0x4A8660`，而且它是「基类构造函数逐层覆写同一个 vptr 槽」的最后一笔。** 5 轮循环（`mov eax,0x8a0368` / `mov edx,5` / `add eax,0x18` / `dec edx` / `jne 0x4a863c`），循环体对**同一** `[eax-8]` 连写三张：`0x7E192C` → `0x7E4F64` → `0x7E6060`。RTTI 独立证：三张 CHD 基类数 **1 / 2 / 3**，`LayerClass` 基类数组依次 `LayerClass` / `DynamicVectorClass<ObjectClass*>` / `VectorClass<ObjectClass*>`，**mdisp 全 0、pdisp 全 -1** ⇒ 单继承链三个子对象都落偏移 0 ⇒ 同一槽覆写，**last-store-wins = 0x7E6060**。反推基址偏置 **B=8**、对象布局 `{+0 vptr,+4,+8,+0xC,+0xD,+0x10,+0x14}` 无重叠无空洞。

OD4. ✅ **全量重算**：完整操作数解析器（base/index*scale/±disp）流式 1,394,120 条指令 ⇒ `mov dword ptr <mem>, imm∈VTS` **5,729** 站点 / **1,212** 表（严格口径 5,724 / 1,211）。六形态换宽容解析：F1 **2,741/838**、F3 **1,310/348**、F4 **341/243**、F5 **142/42**、F6 **990/3**、F7 **1,337/223** —— **五项与 R144 逐项相同**（不受负位移影响 ⇒ 方法一致性正控），只有 F3 涨。并集 **1,213 → 1,214**，残余 **5 → 4**，新增覆盖**恰一张**。

OD5. 🔴 **F6 抓不到它的原因（新事实）**：5 个元素在 `0x8A0368 + 0x18k`，而 `.data` 的 `RawSize` 只到 **0x87E000**（`VirtualSize` 到 0xB79BE4）⇒ 属**未初始化尾（BSS）**，**文件里根本没有字节**。所以「文件里搜不到该虚表地址」≠「没被装过」。凡以后用「原始字节搜索」判存在性，必须先判目标是否落在 RawSize 之外。

OD6. ✅ **新增区分：持久装表 vs 瞬态装表。** 按 `j*`/`call`/`ret` 断块维护 `(base,disp)` 块内最后写：`mov dword ptr <mem>,…` 共 **18,051** 站点（`imm∈VTS` 5,729）、块 **255,505** ⇒ **持久 5,688 / 瞬态 41**；按表 **持久 1,211 / 瞬态 20**，**只被瞬态覆盖的恰 1 张** = `0x7E1FB4`（`TD .?AVINoticeSource@@`，站点 0x41017B / 0x4101C9 / 0x6E800F 全被同块后续写覆盖）。⇒ 「出现过装表指令」与「运行时持有该 vptr」是**两个命题**，报告必须写「存在静态 vptr 写入点」而不是「持有」。

OD7. ✅ **双判据交叉 + 分母措辞。** 判据 A（前 8 槽落 `.text` 数为 0，只看表体字节）与判据 B（六形态零站点，只看代码写点）**互相独立**，给出**完全相同的 4 张**（`0x877000/0x877010/0x87B17C/0x87B18C`，两差集为空）。分母：VTS 原始 **1,218**；并集 1,214 已不含这 4 张 ⇒ 接受剔除 = **1,214/1,214 = 100%**；保留原分母 = **1,214/1,218 = 99.67%**。**两数并列、原始分母在前**（采纳审计 #323 建议：100% 是派生量、最易被单独摘走）。**仍不改 VTS 常量 1,218**（剔除属口径变更）。

OD8. 📌 **规则 D 如实，含一次失败与一条未复算项。** 执行员 **#321（hy4, exec）succeeded** / 3 回合 / 2.5′ / 无 OVERTIME / **10-10 PASS**，5,729 / 1,212 / 5,724 / 1,211 / 残余 6 张与我**逐项相同**，并自主提出「我 1,212 比 R144 的 1,213 少 1 说明 R144 还含我没纳入的形态」—— 方向对，答案在 `r145c`（那是 F5 寄存器搬运，不是 F6）。审计员 **#322（deepseek, audit）failed `error_max_turns`**：36 回合 / **23.2′**，回收记录打 **`[OVERTIME]` 实测 23.2′ vs 预算 2.0′**，零可用输出。**我派发时写的是 `--budget-min 8`，回收回填 2.0，差异原因未查证**（按记录原文登记，不替工具解释）。处置：改派窄卡（3 问 + `--max-turns 14`）后 **#323（deepseek, audit）succeeded** / 16 回合 / 3.37′ / 无 OVERTIME；两条事实断言我逐条复算（`r145i` **7/7 PASS**：`.text` 原始 4 字节出现数 **18/10/1**、`0x7E6060` 唯一出现 **0x4A8663** = 指令起点 +3、CHD `numBase=3` 与基类顺序、mdisp 全 0 / pdisp 全 -1）。它另提「`call 0x7C978A` 是 `__EH_prolog` 形态」——**未复算，不引用**。

OD9. 🔴 **自错五条（S-316..S-320），其中 S-320 是门禁真 FAIL。** **S-316**：`r145c` 双重扣减 —— 并集 1,214 **本已不含**那 4 张误收，再减 4 得 1,210 是错的（真分母 1,214）；由 `r145h` 的可失败断言抓出。**S-317**：把与 R144 口径差出的 2 张归因 F6，实测 F6 对它们**站点为空**，实际是 **F5**。**S-318**：`r145e` 两处 —— 把「同一槽连写三次」当布局重叠（应先按槽去重）；从未归一化的 `op_str`（`'eax, 0x8a0368'`）里 split 取基址得 0。**S-319**：`r145i` 元组下标写成 `ch['1']`。**S-320（真 FAIL）**：`r145l` 替换常量时只换引号后**前 8 个 hex**，旧常量剩余 56 hex 留在原地 ⇒ 常量变 **120 hex**，门禁报「`sha256 13ea4fd3… != pinned 13ea4fd3…`（**值相同却判不等**）」。`r145m` 改用整常量正则 `= '[0-9a-f]+'` 替换，并加「长度必须恰 64」与「错法必须产生 != 64」两条可失败断言。**教训**：截断式替换（`'%s` 前缀拼接）在「常量本身很长」时会静默造出**值相等但长度不等**的畸形常量 —— 断言不能只比值，还要比**长度与形状**。

OD10. ✅ **门禁回归（四处改动，均为容纳新节 + 同步 + 重钉，未改判据语义）。** ① `C16_FLOORS` 加 `150: 8600`（§2.150 实测 **8,621 B** − 21），表项 **143 → 144**，`C16_FLOORS_SHA256` `05b54f35…` → **`183a5d82…`**（**重钉前先用现表重算复现旧钉**，`r145k` 13 正控 0 FAIL）；② `GATE_VER` **R144 → R145**；③ `DISC_RECHECK.tsv` **第 21 行（主键 20）** 同步 → C7d `636db13b…` → **`13ea4fd3…`**（照抄门禁口径：**丢表头 31 行**，并加「含表头重算得另一个值」的反控）、`C7_ROW_SHA['20']` 同步；④ `DISC_UNVERIFIABLE.tsv` **第 11 行（主键 20）** 同步 → `FREEZE_SHA256` `c49e2582…` → **`d22fd43c…`**。两处主键同为 20 而行号不同（**21 与 11**），脚本先打印目标行再断言（S-299 教训）。

OD11. 📌 **未取得（不粉饰）**：① 4 张误收项**是否剔出 VTS** 属口径变更，本轮只做双判据交叉，不改 1,218 常量；② 「持久装表」只证「块内无更晚的同类立即数写」，**不证运行时可读回、也不证该构造函数被调用过** —— `0x7E6060` 在 `.text` 里只有 **1** 次出现，若那个循环从不执行，静态侧无从得知（动态项）；③ 只被瞬态覆盖的 `0x7E1FB4`（`INoticeSource`）**它到底是哪个对象的活 vptr 未定**；④ 大位移组（278 站点 / 一致率 0.1259 / lift 15.87）是什么结构仍未定位；⑤ 动态项（虚表运行期读取、3,805 处寄存器 `call/jmp` 落点、35 个静态容器运行期值、窗口表 r66 后快照）仍留 win-main；⑥ 已判死线继续禁投：具名池、无名池、direct-only(D2)、D4结构性无、静态④、动态④、证据指针791行、D-48攻②-b。
"""
b = SEC.encode('utf-8')
ck('追加段不含 CR', b'\r' not in b)
old = open(LK, 'rb').read()
ck('LK 旧 CR == 137', old.count(b'\r') == 137, old.count(b'\r'))
ck('LK 尾部是换行', old.endswith(b'\n'))
ck('LK 里尚无 OD 段', b'\n## OD \xc2\xb7' not in old)
ck('LK 末段是 OC', re.findall(rb'(?m)^## ([A-Z]{2}) \xc2\xb7', old)[-1] == b'OC', re.findall(rb'(?m)^## ([A-Z]{2}) \xc2\xb7', old)[-1])
dst = os.path.join(BL, 'LEAD_LOCK.before_r145_lock_od_%s.bak' % time.strftime('%Y%m%d_%H%M%S'))
with io.open(dst, 'xb') as f: f.write(old)
ck('备份 wx 独占且逐字节相同', open(dst, 'rb').read() == old, os.path.basename(dst))
open(LK, 'wb').write(old + b"\n" + b)
new = open(LK, 'rb').read()
ck('LK 写后 CR 仍 137', new.count(b'\r') == 137, new.count(b'\r'))
ck('LK 写后以原文件为前缀', new[:len(old)] == old)
ck('LK 写后末段 == OD', re.findall(rb'(?m)^## ([A-Z]{2}) \xc2\xb7', new)[-1] == b'OD', re.findall(rb'(?m)^## ([A-Z]{2}) \xc2\xb7', new)[-1])
ck('LK 写后 OD1..OD11 齐', all(('OD%d.' % i).encode() in new for i in range(1, 12)))
json.dump({'fails': cc, 'bytes_before': len(old), 'bytes_after': len(new)}, io.open('/home/t628/projects/ra2-campaign-forge/_r145/r145o_lock_od.json', 'w'), indent=1)
print('\n=== LEAD_LOCK OD：FAIL %d  %d → %d B ===' % (len(cc), len(old), len(new)))
