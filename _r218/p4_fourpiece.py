# -*- coding: utf-8 -*-
"""R218 p4：四件套追加（wx 独占备份 -> 断言旧 sha/CR -> 一次性写 -> 回读校验）。
R14_COMMON §2.226 / GOAL §1276 / LEAD_LOCK QL / STATUS_BOARD 第 218 轮。
"""
import os,hashlib,json
ROOT='/home/t628/projects/ra2-campaign-forge'
T=ROOT+'/lead/next_re_20261117_r14'; BASE=ROOT+'/R17_LEAD_BASELINE'
SPEC={
 'R14_COMMON':dict(path=T+'/R14_COMMON.md',cr=1081),
 'GOAL':dict(path=ROOT+'/lead/GOAL_THREE_TARGETS_20261018.md',cr=337),
 'LOCK':dict(path=ROOT+'/lead/LEAD_LOCK',cr=137),
 'BOARD':dict(path=T+'/STATUS_BOARD.md',cr=0),
 'ARCH':dict(path=T+'/BOARD_ARCHIVE.md',cr=2952),
}
def bak(path,tag):
    b=open(path,'rb').read()
    base='%s/%s.before_r218_%s'%(BASE,os.path.basename(path),tag)
    for i in range(10):
        dst=base+(('_%d'%i) if i else '')+'_20261128.bak'
        if os.path.exists(dst):
            if open(dst,'rb').read()==b: return b
            continue
        fd=os.open(dst,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
        with os.fdopen(fd,'wb') as f: f.write(b)
        return b
    raise SystemExit('bak exhausted '+tag)
pre={}
for k,v in SPEC.items():
    b=open(v['path'],'rb').read()
    assert b.count(b'\r')==v['cr'],'%s CR %d != %d'%(k,b.count(b'\r'),v['cr'])
    pre[k]=dict(cr=v['cr'],bytes=len(b),sha=hashlib.sha256(b).hexdigest())
    print('[前置OK] %-10s cr=%-5d bytes=%-8d sha=%s'%(k,v['cr'],len(b),hashlib.sha256(b).hexdigest()[:16]))

R14 = """
## 2.226 R218（2026-11-28）· 虚表口径二分（1214 真表 + 4 幻影）+ BCD 记录 24 B 订正 + 464 高槽归因 + disp 扫描定稿

### 一 · 🔴 「1218 张虚表」不是同质集合：1214 真表 + 4 幻影，真表与 COL 双射
判据 `dw(V-4)==COL` 选出 **1218** 个候选；再加 `dw(V)` 必须落在 `.text` 后只剩 **1214**。
差集 4 个全在 `.data`：`0x877000` / `0x877010` / `0x87b17c` / `0x87b18c`。
- 4 个的 16 B 形态完全相同：`c0000001 00000000 00000000 00800040`（`+0xc` 才是 COL `0x800040`），**槽数 0**。
- `.text` 内以 dword 形式被引用的次数：4 个全 **0**；正控 `0x7e8278`（真表，`DropPodLocomotionClass`）**4** 次、`0x7e1f50` **5** 次。
- `.data` 内 COL `0x800040` 出现 **4** 处，恰为这 4 个候选的 `V-4`，无第五处。

⇒ **1214 张真虚表 ↔ 1214 条 COL 严格双射**（单射与满射同时成立）。R217 的「同一 COL 被 5 张视图共用，本二进制唯一示例」在真表口径下**不存在**；
`mdisp!=0` 视图数 **264（含幻影） vs 260（真表）= 差 4** 正是这 4 个幻影，而非「共用 COL」。
**总槽数 14044 与主视图 9958 不受影响**（幻影 0 槽）：族数 954 / 主视图 954 / 主视图 slot≥3 **9958** / 全表 slot≥3 **10814**，与 R217 逐数一致。

### 二 · 🔴 BCD 记录 24 B，pBCA 是 4 B 指针数组（自错 E6 订正）
`CHD+8` = numBase、`CHD+0xc` = pBCA。**pBCA 元素是 BCD 地址（4 B）**，BCD 记录本体 **24 B**：`+0 pTD / +4 ncb / +8 mdisp / +0xc pdisp / +0x10 vdisp / +0x14 attributes`。
- 正控：6 张超 256 表的 94 个数组元素，`+0` 解出合法 pTD 名 **94/94**。
- 反控：若记录长 `0x1c`，则 `+0x1c` 也应是 pTD ⇒ 实测 **0/94**。
- 邻接证据：`+0x18` 处落点解出合法 pTD **84/94**（= 下一条记录的 `+0`）。
⇒ 此前把 `+0x18` 当 pCHD 字段的写法作废；「pBCA 是内联记录数组」写法作废。

### 三 · 🔴 464 个 slot≥256 槽归因：cov 294 / diff 67 / oob 103
父类判定 = 基类数组中**紧跟在自身项之后（ncb 递减序）**的那一项，**6/6 PASS**：
Unit/Infantry/Aircraft → Foot；Foot/Building → Techno；Techno → Radio。
| 表 | 槽数 | 父类 | 父类槽数 | cov | diff | oob |
|---|---|---|---|---|---|---|
| Unit `0x7f5c70` | 344 | Foot | 341 | 73 | 12 | 3 |
| Infantry `0x7eb058` | 343 | Foot | 341 | 63 | 22 | 2 |
| Aircraft `0x7e22a4` | 341 | Foot | 341 | 80 | 5 | 0 |
| Foot `0x7e8c94` | 341 | Techno | 309 | 37 | 16 | 32 |
| Building `0x7e3ebc` | 322 | Techno | 309 | 41 | 12 | 13 |
| Techno `0x7f4960` | 309 | Radio | 161 | 0 | 0 | 53 |

父类范围内覆盖率 **294/361 = 81.44%**；`oob` 恰等于 `Σ max(0, n − max(par_n,256))`（校验 PASS）⇒ 超出父类槽数的尾部必为本类新增。
464 个目标去重 **170**、全部落 `.text`、在本表低 256 槽内重复仅 **1** 个；
把每张表每个 shift 与全部 1214 张表做最大公共前缀搜索，**≥12 的拼接候选 0 条**（反控：随机 10 对无关表最大公共前缀 0）
⇒ 高槽段**不是**拼接另一张 vftable，也**不是**父类表整体复制。

### 四 · 🔴 disp 扫描定稿口径（全 `.text` 线性 sweep，遇非法字节前进 1 B）
| 项 | 实测 |
|---|---|
| 解码指令数 | **1,394,120**（非法跳字节 66，末指令 `0x7e0ffd`） |
| `call/jmp` 且 `[reg+disp]`（无索引，排除 esp） | **18,930** |
| `disp==0x2c`（slot 11） | **1114** |
| `disp==0` | **819** |
| `disp==0x48`（slot 18） | **930** |
| slot≥256（`disp≥0x400`）位点 | **931**，不同 s **91** 个 |
| 非 4 对齐 disp | **0** |
| 正控 `0x41021a`（`call dword ptr [edx+0x2c]`） | **命中** |

- 931 个位点中 **925** 落在 UnitClass 槽域（s<344，top：s=288 有 309 处、s=289 有 85 处、s=337 有 73 处）；
  **6** 处 s∈{479,480,481,482,2224418} 超出最大槽数 344，须另行定性（本轮不归因）。
- **口径警告**：`slot≥256 位点 931` 与 R215 记载的「**931** 处 +0x48 消费位点」是**数字巧合**，本轮实测 `disp==0x48` 为 **930**，两数不可互引。

### 五 · 🟡 自错登记 3 条（0 条进结论）
E1 `m16` 用固定 64 KB 切块解码，块边界截断指令，只解出 1,150,117 条（少 17.5%）。
E2 `m17` 改为「按最后完整指令推进」，遇非法字节时逐字节前进不足，仅 155,215 条。
E3 二轮均误把「BCD 数组」当内联记录（步长 `0x18`/`0x1c`），第二轮起改指针数组才自洽。
最终口径 = 逐字节 sweep（m19/m21），与 card C（#567，21 回合 / 3.18 分 vs 12，无 OVERTIME）逐数一致：
其报 1,394,300 / 18,935 / 1114 / 931 / 91 / 0，主会话复算 1,394,120 / 18,930 / 1114 / 931 / 91 / 0
⇒ 差异仅在其把 `esp` 基址计入（18,935−18,930=5）与跳过字节计数差 180，**结论层无数值分歧**。

### 六 · 🟡 落盘与门禁
`_r218/m11_final_ctl.py` **34 断言 0 FAIL**；`_r218/m21_freeze.py` 全部终值一条命令复现。
**FACT_INDEX V599 → V600**（仅 F29.limitations 追加，其余 56 行逐字节不变）：277566 → **280689** B，sha `616a86e2` → **`fb513cc8`**；
`facts_floors` CUR_SHA256/TOTAL_BYTES/`MASTER_SHA256` `b058464c` → **`37c8063f`**；`gate_runner.LEDGER` → V600；指针文件同步。
三门实测 **exit 0**（check_disc live 31 / C19 `fb513cc8`/280689/V600 / C20 V600；facts_floors D0–D10；gate_runner G1 G2 G3a–G3f）。
"""
p=SPEC['R14_COMMON']['path']; b0=bak(p,'R14COMMON')
assert b0.endswith(b'\n') and b0.count(b'\r')==1081
new=b0+R14.encode('utf-8')
assert new.count(b'\r')==1081,'R14 CR %d'%new.count(b'\r')
open(p,'wb').write(new); chk=open(p,'rb').read()
assert chk.startswith(b0) and chk.count(b'\r')==1081
print('[写入] R14_COMMON bytes %d -> %d  CR %d  sha %s -> %s'%(len(b0),len(chk),chk.count(b'\r'),
      hashlib.sha256(b0).hexdigest()[:16],hashlib.sha256(chk).hexdigest()[:16]))
json.dump({'pre':{k:{kk:vv for kk,vv in v.items()} for k,v in pre.items()},
           'r14':dict(bytes=len(chk),sha=hashlib.sha256(chk).hexdigest())},open(ROOT+'/_r218/p4.json','w'),indent=1)
