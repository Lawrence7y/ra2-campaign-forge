#!/usr/bin/env python3
"""R145 N：向 lead/GOAL_THREE_TARGETS_20261018.md 追加 ## §1200（CR 保持 337）。"""
import hashlib, io, json, os, re, time
BASE = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
LED = '/home/t628/projects/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md'
BL = os.path.join(BASE, 'R17_LEAD_BASELINE')
cc = []
def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c: cc.append(n)

SEC = """## §1200 R145 · R144 残余 5 张的第 5 张根因是解析器整类丢弃负位移写入；修好后并集 1,214、真分母 1,214、覆盖 1,214/1,214 = 100%（原始口径 1,214/1,218 = 99.67% 必须并列），并新增「持久/瞬态装表」区分

- **口径**：现盘 `ra2bench/gamemd.exe`（4,825,360 B、sha256 `73201cc021…`）。本轮 14 个脚本全部带正反控自测：`r145a` 11 / `r145b` 10 / `r145c` 11 / `r145d` 9 / `r145e` 10 / `r145f` 6 / `r145g` 6 / `r145h` 7 / `r145i` 7 / `r145j` 10 / `r145k` 13 / `r145l` 20 / `r145m` 10 / `r145t`（终态）。全程 `disasm_lite` 64 KB 分块流式，未对整段 `.text` 开 `detail=True`。
- **① 根因（最小反例）**：`0x4A8660` 的 `mov dword ptr [eax - 8],0x7e6060`（`c740f860607e00`）被 R144 的 `RE_STORE` **判为不匹配**；把位移写成 `[eax-0x8]` 则匹配。三层叠加：`norm()` 空白压缩字符类 `[+,*]` 不含 `-`；十进制→十六进制归一要求符号紧跟数字；`RE_STORE` 要求 `]` 前紧邻。净效果 = **所有负位移 `mov dword ptr [reg - N], imm` 整类丢弃**。受影响站点 **437**，其中 `imm ∈ VTS` **5 站点 / 4 张表**。
- **② 全量重算**：完整内存操作数解析器（base / index*scale / ±disp 全拆）流式扫 1,394,120 条指令 ⇒ `mov dword ptr <mem>, imm∈VTS` 站点 **5,729**（严格口径 5,724，+5）、distinct **1,212**（严格 1,211，+1）。六形态换宽容解析后 F1 **2,741/838**、F3 **1,310/348**（负位移 5 站点）、F4 **341/243**、F5 **142/42**、F6 **990/3**、F7 **1,337/223** —— 除 F3 外**五项与 R144 逐项相同**（方法一致性正控）。并集 **1,213 → 1,214**，残余 **5 → 4**，新增覆盖**恰为 `0x7E6060`**。
- **③ 语义（RTTI 独立证）**：`0x4A8660` 属一个 5 轮循环（`mov eax,0x8a0368` / `mov edx,5` / `add eax,0x18` / `dec edx` / `jne 0x4a863c`），对**同一** `[eax-8]` 连写三张虚表 `0x7E192C → 0x7E4F64 → 0x7E6060`。三张的 CHD 基类数 **1 / 2 / 3**，`LayerClass` 基类数组依次 `LayerClass`、`DynamicVectorClass<ObjectClass*>`、`VectorClass<ObjectClass*>`，**mdisp 全 0、pdisp 全 -1** ⇒ 单继承链三个子对象都落偏移 0 ⇒ 同一个槽、base→derived 覆写，**last-store-wins = 0x7E6060**。反推基址偏置 **B = 8**（位移下界 -8、上界 0x10，跨度 0x18），对象布局 `{+0 vptr, +4, +8, +0xC, +0xD, +0x10, +0x14}` 无重叠无空洞。
- **④ F6 为何抓不到**：5 个元素在 `0x8A0368 + 0x18k`，而 `.data` `RawSize` 只到 **0x87E000**、`VirtualSize` 到 0xB79BE4 ⇒ 属**未初始化尾（BSS）**，文件里**根本没有字节**（`va2off` 全 None）。
- **⑤ 新区分（持久/瞬态）**：按 `j*`/`call`/`ret` 断块维护 `(base,disp)` 块内最后写，实测 `.text` 里 `mov dword ptr <mem>,…` **18,051** 站点（`imm∈VTS` 5,729）、块 **255,505** ⇒ **持久 5,688 / 瞬态 41**；按虚表 **持久覆盖 1,211 / 瞬态覆盖 20**，**只被瞬态覆盖的恰 1 张** = `0x7E1FB4`（`TD .?AVINoticeSource@@`，三站点 0x41017B / 0x4101C9 / 0x6E800F 均被同块后续写覆盖）⇒ 该表「活」性无静态证据。
- **⑥ 双判据交叉与分母**：判据 A（前 8 槽落 `.text` 数为 0，只看表体字节）与判据 B（六形态零站点，只看代码写点）**互相独立**，给出**完全相同的 4 张**（`0x877000/0x877010/0x87B17C/0x87B18C`，两差集为空），且这 4 张同时有「槽值不落任何节」。分母：VTS 原始 **1,218**；并集 1,214 已不含这 4 张 ⇒ 接受剔除则 **1,214/1,214 = 100%**；保留原始分母则 **1,214/1,218 = 99.67%**。**两数并列、原始分母在前**（采纳审计 #323 的措辞建议）。
- **⑦ 自错四条（全由可失败断言抓出）**：**S-316** `r145c` 双重扣减（并集 1,214 本已不含 4 张误收，再减 4 得 1,210 是错的；真分母 1,214）；**S-317** 把差异 2 张（`0x7F7A1C`/`0x7F7AEC`）归因 F6，实测是 **F5 寄存器搬运**；**S-318** `r145e` 同一槽连写被当布局重叠 + 从未归一化 `op_str`（逗号带空格）解析数组基址得 0；**S-319** `r145i` 元组下标写成字符串键。**另 S-320（门禁真 FAIL）**：`r145l` 替换常量时只换了引号后前 8 个 hex，旧常量剩余 56 hex 留在原地 ⇒ 常量变 120 hex、门禁报「值 == 值 却不相等」；`r145m` 改用整常量正则替换并加「长度必须恰 64」可失败断言修复。
- **⑧ 规则 D 如实**：执行员 **#321（hy4，exec）succeeded** / 3 回合 / 2.5′ / 无 OVERTIME，**10/10 PASS**，5,729 / 1,212 / 5,724 / 1,211 / 残余 6 张与我**逐项相同**；审计员 **#322（deepseek，audit）failed `error_max_turns`**，36 回合 / **23.2′**、回收记录打 **`[OVERTIME]` 实测 23.2′ vs 预算 2.0′**，**零可用输出**（我派发写的是 `--budget-min 8`，回收回填 2.0，差异原因**未查证**，按记录原文登记）；改派窄卡后 **#323（deepseek，audit）succeeded** / 16 回合 / 3.37′ / 无 OVERTIME，两条事实断言我逐条复算（`r145i` **7/7 PASS**）。它另提「`call 0x7C978A` 是 `__EH_prolog` 形态」——**未复算，不引用**。
- **⑨ 门禁回归**：`C16_FLOORS` 加 `150: 8600`（§2.150 实测 8,621 B − 21），表项 **143 → 144**，`C16_FLOORS_SHA256` `05b54f35…` → `183a5d82…`（重钉前先用现表复现旧钉）；`GATE_VER` **R144 → R145**；`DISC_RECHECK.tsv` 第 21 行（主键 20）同步 → C7d `636db13b…` → `13ea4fd3…`、`C7_ROW_SHA['20']` 同步；`DISC_UNVERIFIABLE.tsv` 第 11 行（主键 20）同步 → `FREEZE_SHA256` `c49e2582…` → `d22fd43c…`。**两处主键同为 20 而行号不同（21 与 11）**，脚本先打印目标行再断言。
- **⑩ 未取得（不粉饰）**：4 张误收项**是否剔出 VTS**仍属口径变更（不改 1,218 原始常量）；「持久装表」只证块内无更晚同类写，**不证运行时可读回、也不证构造函数被调用过**（`0x7E6060` 在 `.text` 只有 1 次出现，若循环不执行则静态侧无从得知）；`0x7E1FB4` 到底是谁的活 vptr 未定；大位移组（278 站点）结构未定位；动态项留 win-main；已判死线继续禁投。
"""
b = SEC.encode('utf-8')
ck('追加段不含 CR', b'\r' not in b)
old = open(LED, 'rb').read()
ck('LED 旧 CR == 337', old.count(b'\r') == 337, old.count(b'\r'))
ck('LED 尾部是换行', old.endswith(b'\n'))
ck('LED 旧末节 = §1199', re.findall(rb'(?m)^## \xc2\xa7(\d+)', old)[-1] == b'1199', re.findall(rb'(?m)^## \xc2\xa7(\d+)', old)[-1])
dst = os.path.join(BL, 'GOAL_THREE_TARGETS.before_r145_sec1200_%s.bak' % time.strftime('%Y%m%d_%H%M%S'))
with io.open(dst, 'xb') as f: f.write(old)
ck('备份 wx 独占且逐字节相同', open(dst, 'rb').read() == old, os.path.basename(dst))
open(LED, 'wb').write(old + b"\n" + b)
new = open(LED, 'rb').read()
ck('LED 写后 CR 仍 337', new.count(b'\r') == 337, new.count(b'\r'))
ck('LED 写后以原文件为前缀', new[:len(old)] == old)
ck('LED 写后末节 = §1200', re.findall(rb'(?m)^## \xc2\xa7(\d+)', new)[-1] == b'1200', re.findall(rb'(?m)^## \xc2\xa7(\d+)', new)[-1])
json.dump({'fails': cc, 'bytes_before': len(old), 'bytes_after': len(new)}, io.open('/home/t628/projects/ra2-campaign-forge/_r145/r145n_ledger1200.json', 'w'), indent=1)
print('\n=== §1200 追加：FAIL %d  %d → %d B ===' % (len(cc), len(old), len(new)))
