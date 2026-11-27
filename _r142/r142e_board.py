#!/usr/bin/env python3
# R142 E: 看板追加第 142 轮（精简版）
#   r142c 的版本 83 行 => 225 + 83 = 308 > 300，被回退；本版压到 50 行内。
#   同时把「超限被回退 + 重钉 C16」这次事故本身写进看板（不粉饰）。
import hashlib
import io
import json
import os
import time

ROOT = '/home/t628/projects/ra2-campaign-forge'
BASE = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BL = os.path.join(BASE, 'R17_LEAD_BASELINE')
BRD = os.path.join(BASE, 'STATUS_BOARD.md')
OUT = os.path.join(ROOT, '_r142', 'r142e_board.json')

cc, cc_n = [], 0


def ck(name, cond, detail=''):
    global cc_n
    cc_n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond:
        cc.append(name)


BRD_TXT = """
## 🟢 R17 第 142 轮（2026-11-27 00:0x–00:5x）· 三分档不可机械复现定案：纯路径量 T1 一致 18/32 **恰等于**确定性随机基线 18.0（p=1.0000）；读 basis 的 T2 到 24/32（p<0.0001）但余 8 条纯人工判读

> 看板 §十 第 1、2 项都收口，两项都是负面结论。第 1 项给出**判别力上限**（不是又报一次 6/33）；第 2 项把 R141 的推断变成逐版本实测，并**修正了 R141 的机制描述**。

### 一 · 路径层反而被证明是准的（别把结论读歪）

| 声明 | 条数 | 与磁盘不符 |
|---|---|---|
| `alive_paths` | 91 | **0** |
| `lost_primary` | 36 | **0** |
| `lost_side` | 4 | **0** |

⇒ R141「两套分档不可当机械结论引用」易被读成「外部数据不可信」。实测**不是**：**真值表准确，坏的只是「真值→档位」映射**。下游可用路径列，不可用 `verdict` 列。

### 二 · 决定性反例：档位不是路径状态的函数

`lost_primary` 为空的行恰 **4** 条，却跨两档：F18/F27/F39 判**需重建**，**F49 判仍可核验**。
最紧的一对 **F39/F49**：存活数同为 **2**、`basis` 都点名同一个已失件 `HANDOFF_R14_R3`（全库 **0** 个文件），档位仍不同 —— 差别只在散文措辞（F49「为旁证，不影响主体链」vs F39「该条来源需重建」）。

### 三 · 判别力上限：T1 与随机不可分，T2 卡在 24/32

| 定义 | 一致率 | 确定性随机基线 | 置换 p（4000 次） | 判定 |
|---|---|---|---|---|
| T1（只用路径状态） | **18/32 = 56.2%** | **18.0** | **1.0000**（sd 0.00） | **无判据** |
| T2（+ `basis` 关键词） | **24/32 = 75.0%** | 15.69 | **< 0.0001**（μ15.68 / sd1.76） | 有信号、不完整 |

T1 置换分布 **sd 恰为 0**：预测类别计数与真实标签计数都固定，期望一致率是确定数 —— 不是「弱」，是**零**。
T2 残余 **8 条**：F09、F10、F19、F22、F25、F28、F46、F52。推到 32/32 只能继续加关键词（拟合人工结论）⇒ T2 只作**可复算下界**，**不称其为定义**。
过拟合对照：「存活路径全名集合」只分 **15 组**（未饱和成 32 组）且仍有 **3 个冲突组**。

### 四 · 版本漂移：10 版全算（修正 R141）

| 版本 | partial | 全失联 | 全活 | 与外部 32 差 |
|---|---|---|---|---|
| v530 / v531 / v532 / v533 | **32** | **[F23, F35]** | 20 | 空 |
| v534 … v539 | **33** | **[F23]** | 20 | **{F35}** |

- 序列 **32,32,32,32,33,33,33,33,33,33**：**只有 1 个跳变点**（v533→v534，+1），集合差**进入 {F35}、退出 0**
- **修正 R141**：F35 在 v530..v533 **不是不存在，而是在全失联桶里**（1 条路径且不在盘）；v534 补成 5 条（4 在盘）后才**从全失联跳进部分失联** ⇒ 漂移的是**分界**（全失联 2→1、部分 32→33 同步移动）

### 五 · 引用纪律（可执行）

真不变量只有两条：**全活恒 20**、**三桶合计恒 54**（无 no-paths 行）。
**「部分失联 33」与「全失联只有 F23」都只在 ≥v5.34 成立** —— 盘上 10 版有 **4 版（40%）** 给 32，且那 4 版全失联是 **[F23, F35]**。

### 六 · 顺手抓到外部数据缺陷

`lost_primary` 为空的 4 行**正好等于** `basis` 点名「已失」却不进该列的全部 4 行（**同一集合**）。例：F18 的 `basis` 写 `GATE_BEHAV/PROGRESS.md 第二/三步已失` 而该列空；实测该文件确实不在盘（同目录 `CASES.tsv` 在盘，反证非误判）。⇒ **只读该列的下游会把这 4 行误当「无失联」**，这也是 T2 必须读 `basis` 才到 75% 的原因。

### 七 · 规则 D：执行员 #313（hy4）盲测复算，八项逐项一致

禁读 `_r142/r142*.py`，自写 `_r142/sub/sub_independent.py`；**succeeded / 4 回合 / 41 秒 / 无 OVERTIME**。八项：54 行 / partial 33 / dead [F23] / alive 91 条 0 缺失 / lost 36 条 0 仍在盘（另报原始分号段 40、4 段空字段跳过，与法一致）/ F18+F27+F39 需重建 与 F49 仍可核验 / 序列 32×4+33×6 / 非空差集仅 v534..v539 的 {F35} —— **逐项相同**。它另独立指出 F49 值得单独复核，与第二节同向。

### 八 · 事故与自错（不粉饰）

**事故 1：看板超限被回退。** 首版条目 83 行，225 + 83 = **308 > 300**，写入后回读断言当场 FAIL，文件保持 225 行（sha `8124bdcb` 未变）—— 未留半截状态。本版压到 50 行内重写。**教训：我先写内容再数行数，顺序反了；应先知余量（300 − 当前行数）再定篇幅。**

**事故 2：新节 unpinned + 重钉。** 加 §2.146 后 C16 报 `unpinned 1`（表外新节默认 `C16_NEW_MIN=0` ⇒ 永久免检票）。补 `146: 8400`（实测 8,421 B）后 C16d 报 **TAMPERED**（设计如此）⇒ 按设计重钉 `C16_FLOORS_SHA256` 为 `546dbdf7…`。**重钉前先验证方法可复现旧值**：把 146 去掉重算得 `4e1c4e32a323af20`，与旧常量逐字符相同 ⇒ 方法无误，不是我在改判据。

**自错 7 条（S-285..S-291，全由断言抓出）**：**S-285** 断言路径层 127，实测 **131**（漏 `lost_side`）。**S-286** 断言不一致行 3 条，实测 **4 条**（含 F39），补断言才发现它恰等于 `lost_primary` 为空的全部 4 行。**S-287** 正则扫 `basis` 把 **F15 的 `SUPERSEDED.md`** 误报已失 —— 它在「在盘」侧，**正则找得到名字但没有方向感**。**S-288** 断言「全失联恒 [F23]」，实测 v530..533 是 **[F23, F35]** —— 这条错**恰恰藏住了第四节的修正**。**S-289** 断言三桶合计 53，实测 **54**（凭印象假设有 no-paths 行）。**S-290** 断言「T1 ≥60% 说明非随机」，实测 **56.2% 且恰等于基线、p=1.0000** —— 把**无判据**说成**弱判据**，这条改写了第三节的结论强度。**S-291** 断言存活集合 ≥25/32 唯一，实测 **15**。

### 九 · 落盘

FACT_INDEX **未改一字**（档位三元组不在任何 54 行出现，第 0 项已验）。四件套：R14_COMMON **§2.146**（CR **1081**、末节 146、1,217,052 B）、LEDGER **§1196**（CR **337**）、LEAD_LOCK **OA** 段（CR **137**）、看板本轮（CR **0**）。断言 r142a 34 + r142b 22 = **56 正控 0 FAIL**，反控 **5 项 0 FAIL**；终态 `check_disc.py` **exit 0**、C16 pinned 140 / unpinned 0 / min margin 21、C16d `546dbdf7…`。三个 `.bak` 均 `wx` 独占创建并回读校验。

### 十 · 下轮优先（禁写元审计待办）

1. **三分档的「定义」仍未取得** —— 残余 8 条须读 `VERDICT.md` 正文做语义判定，纯路径量做不到；引用「需重建 18 条」前须先立这份可失败定义。
2. **T2 的 75% 含循环风险** —— 关键词抄自 writer 写的 `basis`，置换只证**非随机**、不证**非自证**（按 F44/F47 只当推断）。
3. **`lost_primary` 列不完整** —— 4 行把失联件只写在 `basis` 散文里；改 `_ext/` 外部产物要单独一卡。
4. **F01 的 1201 判据** —— R140 已排除「事后阈值」方向，仍不可复现。
5. **F35 的 `n` 数值** —— 只能重建 `coverage.tsv` 与 `function_atlas.tsv`。
6. 已判死线继续不投。
"""


def main():
    old = open(BRD, 'rb').read()
    before = dict(cr=old.count(b'\r'), lf=old.count(b'\n'), bytes=len(old),
                  sha=hashlib.sha256(old).hexdigest())
    add_lines = BRD_TXT.count('\n')
    print('  当前看板 %d 行，本次新增 %d 行 => 预计 %d 行（上限 300）'
          % (before['lf'], add_lines, before['lf'] + add_lines))
    ck('E0 写前余量足够（预计 <= 300）', before['lf'] + add_lines <= 300,
       before['lf'] + add_lines)
    ck('E1 新增文本全 LF（无 CR）', '\r' not in BRD_TXT, BRD_TXT.count('\r'))

    # wx 备份
    dst = os.path.join(BL, 'STATUS_BOARD.md.before_r142E_%s.bak'
                       % time.strftime('%Y%m%d_%H%M%S'))
    with io.open(dst, 'xb') as f:
        f.write(old)
    ck('E2 备份 wx 独占且逐字节相同', open(dst, 'rb').read() == old, os.path.basename(dst))
    ck('E3 备份旧 sha 一致', hashlib.sha256(open(dst, 'rb').read()).hexdigest() == before['sha'],
       before['sha'][:8])

    data = old + BRD_TXT.encode('utf-8')
    with io.open(BRD, 'wb') as f:
        f.write(data)
    back = open(BRD, 'rb').read()
    after = dict(cr=back.count(b'\r'), lf=back.count(b'\n'), bytes=len(back),
                 sha=hashlib.sha256(back).hexdigest())
    ck('E4 回读 == 期望内容', back == data)
    ck('E5 纯追加（旧内容为前缀）', back.startswith(old))
    ck('E6 CR 保持 0', after['cr'] == 0, after['cr'])
    ck('E7 总行数 <= 300', after['lf'] <= 300, after['lf'])
    ck('E8 含第 142 轮标题', 'R17 第 142 轮'.encode() in back)
    ck('E9 含事故段（不粉饰）', '看板超限被回退'.encode() in back)
    ck('E10 含 8 条残余 fid 列表', 'F46、F52'.encode() in back)

    json.dump(dict(before=before, after=after, cc_checks=cc_n, cc_fails=cc),
              io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('\n=== 收口：正控 %d 项 / FAIL %d ===' % (cc_n, len(cc)))
    print('看板 %d -> %d 行' % (before['lf'], after['lf']))


main()
