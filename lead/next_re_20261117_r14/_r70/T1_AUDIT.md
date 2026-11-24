# R70-T1-AUDIT 复核报告

角色：审计员（work/cn:hy4flash，家族 hy4）
日期：2026-11-22（R17 第 70 轮）
仓库根：/home/t628/projects/ra2-campaign-forge
被审文件：lead/next_re_20261117_r14/R17_R102_FACTINDEX_V530/FACT_INDEX.tsv
约束遵守：全程只读；未运行反汇编、未读 gamemd.exe 字节、未判函数入口、未调用网络；未复用 _r70 下任何脚本（独立脚本写在 /tmp/r70_t1_audit_parser.py 与 /tmp/r70_t1_m4m6.py）；唯一写入文件为本报告。

## 自测（解析脚本自带，先于数据执行）

命令原文：

```bash
cat > /tmp/r70_t1_audit_parser.py <<'PYEOF'
#!/usr/bin/env python3
# R70-T1-AUDIT 独立复核脚本（只读），不复用 _r70 下任何主会话脚本。
import os, sys

ROOT = "/home/t628/projects/ra2-campaign-forge"
TSV  = os.path.join(ROOT, "lead/next_re_20261117_r14/R17_R102_FACTINDEX_V530/FACT_INDEX.tsv")

# 括号：半角( ) 与全角（ ）都算；分隔符半角分号，仅深度 0 时切分。
OPEN  = {'(', '（'}
CLOSE = {')', '）'}

def strip_backticks(s):
    s = s.strip()
    if len(s) >= 2 and s[0] == '`' and s[-1] == '`':
        return s[1:-1]
    return s

def split_items(field):
    """按括号深度为 0 的半角分号切分。"""
    out, buf, depth = [], [], 0
    for ch in field:
        if ch in OPEN:
            depth += 1
            buf.append(ch)
        elif ch in CLOSE:
            if depth > 0:
                depth -= 1
            buf.append(ch)
        elif ch == ';' and depth == 0:
            out.append(''.join(buf))
            buf = []
        else:
            buf.append(ch)
    out.append(''.join(buf))
    return [x for x in out if x.strip() != '']

def parse_item(item):
    """返回 (path, anchor, raw)。若以右括号结尾，则最后配对括号内为锚点。"""
    raw = item
    s = item.strip()
    if s and s[-1] in CLOSE:
        # 从尾部反向找与之配对的开括号（支持嵌套）
        depth = 0
        open_idx = -1
        for i in range(len(s) - 1, -1, -1):
            ch = s[i]
            if ch in CLOSE:
                depth += 1
            elif ch in OPEN:
                depth -= 1
                if depth == 0:
                    open_idx = i
                    break
        if open_idx >= 0:
            anchor = s[open_idx + 1 : len(s) - 1]
            path_part = s[:open_idx]
            return strip_backticks(path_part), anchor, raw
    return strip_backticks(s), None, raw

def path_exists(path):
    # 反斜杠转正斜杠，相对仓库根，Linux 区分大小写
    p = path.replace('\\', '/')
    return os.path.exists(os.path.join(ROOT, p))

def selftest():
    # 正控 1：用 ls 确认真实存在的路径 -> 判存在
    real = "lead/next_re_20261117_r14/R17_R102_FACTINDEX_V530/FACT_INDEX.tsv"
    assert os.path.exists(os.path.join(ROOT, real)), "selftest prerequisite: real path missing"
    assert path_exists(real) is True, "selftest FAIL: real path judged missing"
    print("SELFTEST-1 PASS: real path -> exists=True  (%s)" % real)

    # 反控：必然不存在的路径 -> 判不存在
    fake = "__R70_T1_NO_SUCH_FILE__/definitely/not/here.xyz"
    assert not os.path.exists(os.path.join(ROOT, fake)), "selftest prerequisite: fake path exists?!"
    assert path_exists(fake) is False, "selftest FAIL: fake path judged exists"
    print("SELFTEST-2 PASS: fake path -> exists=False (%s)" % fake)

    # 正控：带括号锚点条目 -> 锚点剥离、路径正确取出
    sample = "`lead/next_re_20261117_r14/R17_R102_FACTINDEX_V530/FACT_INDEX.tsv`(0x1234-0x5678)"
    p, a, _ = parse_item(sample)
    assert p == real, "selftest FAIL: path parse=%r expected=%r" % (p, real)
    assert a == "0x1234-0x5678", "selftest FAIL: anchor parse=%r" % a
    print("SELFTEST-3 PASS: anchor item -> path=%s | anchor=%s" % (p, a))

    # 附加：分号在括号内不应切分
    sample2 = "`a/b（x;y).c`(anchor)"
    assert split_items(sample2) == [sample2], "selftest FAIL: split inside parens"
    print("SELFTEST-4 PASS: semicolon inside bracket not split")

def main():
    selftest()
    print("=== BEGIN DATA ===")
    with open(TSV, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()
    # 去表头与空行
    data = [ln for ln in lines if ln.strip() != ''][1:]
    print("DATA_ROWS=%d" % len(data))

    total_items = 0
    anchored_items = 0
    exist_items = 0
    missing_items = []
    fact_all_missing = []   # (fact_id, grade)
    fact_rows = []          # (fact_id, grade, n_items, n_exist)

    for ln in data:
        cols = ln.split('\t')
        assert len(cols) == 5, "unexpected col count %d in line: %r" % (len(cols), ln)
        fact_id = cols[0]
        ev = cols[3]
        items = split_items(ev)
        n_exist = 0
        row_items = []
        for it in items:
            p, a, raw = parse_item(it)
            e = path_exists(p)
            total_items += 1
            if a is not None:
                anchored_items += 1
            if e:
                exist_items += 1
                n_exist += 1
            else:
                missing_items.append((fact_id, p, a, raw))
            row_items.append((p, a, e))
        fact_rows.append((fact_id, None, len(items), n_exist, row_items, cols))

    print("M1_TOTAL_ITEMS=%d" % total_items)
    print("M1_ANCHORED_ITEMS=%d" % anchored_items)
    print("M2_EXIST_ITEMS=%d" % exist_items)
    print("M2_MISSING_ITEMS=%d" % len(missing_items))
    print("M2_SUM=%d" % (exist_items + len(missing_items)))

    # 去重缺失路径 & 涉及 fact_id
    uniq_missing_paths = sorted(set(p for (_, p, _, _) in missing_items))
    uniq_missing_facts = sorted(set(fid for (fid, _, _, _) in missing_items))
    print("M3_UNIQ_MISSING_PATHS=%d" % len(uniq_missing_paths))
    print("M3_UNIQ_MISSING_FACTS=%d" % len(uniq_missing_facts))
    print("M3_UNIQ_PATH_LIST:")
    for p in uniq_missing_paths:
        print("  " + p)
    print("M3_UNIQ_FACT_LIST=" + ",".join(uniq_missing_facts))

    # 父目录不存在 vs 文件不存在
    parent_missing = 0
    file_missing_parent_exists = 0
    for (fid, p, a, raw) in missing_items:
        norm = p.replace('\\', '/')
        parent = os.path.dirname(os.path.join(ROOT, norm))
        if not os.path.isdir(parent):
            parent_missing += 1
        else:
            file_missing_parent_exists += 1
    print("M4_PARENT_DIR_MISSING=%d" % parent_missing)
    print("M4_FILE_MISSING_PARENT_EXISTS=%d" % file_missing_parent_exists)

    # 所有 evidence 都不存在的 fact
    for (fid, _, n_items, n_exist, row_items, cols) in fact_rows:
        if n_items > 0 and n_exist == 0:
            fact_all_missing.append((fid, cols))
    print("M5_ALL_MISSING_FACTS=%d" % len(fact_all_missing))
    print("M5_HEADER=" + repr(lines[0]))
    for (fid, cols) in fact_all_missing:
        print("M5_FACT %s cols=%r" % (fid, cols))

if __name__ == '__main__':
    main()
PYEOF
python3 /tmp/r70_t1_audit_parser.py
```

输出原文：

```text
SELFTEST-1 PASS: real path -> exists=True  (lead/next_re_20261117_r14/R17_R102_FACTINDEX_V530/FACT_INDEX.tsv)
SELFTEST-2 PASS: fake path -> exists=False (__R70_T1_NO_SUCH_FILE__/definitely/not/here.xyz)
SELFTEST-3 PASS: anchor item -> path=lead/next_re_20261117_r14/R17_R102_FACTINDEX_V530/FACT_INDEX.tsv | anchor=0x1234-0x5678
SELFTEST-4 PASS: semicolon inside bracket not split
=== BEGIN DATA ===
DATA_ROWS=54
M1_TOTAL_ITEMS=171
M1_ANCHORED_ITEMS=117
M2_EXIST_ITEMS=128
M2_MISSING_ITEMS=43
M2_SUM=171
M3_UNIQ_MISSING_PATHS=16
M3_UNIQ_MISSING_FACTS=34
M3_UNIQ_PATH_LIST:
  lead\next_re_20261117_r14\COVERAGE\PANEL.md
  lead\next_re_20261117_r14\GATE_BEHAV\PROGRESS.md
  lead\next_re_20261117_r14\HANDOFF_R14_R3.md
  lead\next_re_20261117_r14\HANDOFF_R16.md
  lead\next_re_20261117_r14\NAMED_PUSH_AUDIT10\VERDICT.md
  lead\next_re_20261117_r14\R17_AUDIT_FI_V5\VERDICT.md
  lead\next_re_20261117_r14\R17_AUDIT_R9\VERDICT.md
  lead\next_re_20261117_r14\R17_DELIVERY\DELIVERY_SUMMARY.md
  lead\next_re_20261117_r14\R17_LEDGER_1062\SECTION.md
  lead\next_re_20261117_r14\R17_LEDGER_1063R\SECTION.md
  lead\next_re_20261117_r14\R17_LEDGER_1063\SECTION.md
  lead\next_re_20261117_r14\R17_LEDGER_1064\SECTION.md
  lead\next_re_20261117_r14\R17_LEDGER_1065\SECTION.md
  lead\next_re_20261117_r14\S10_KPROVED\_audit\VERDICT.md
  lead\next_re_20261117_r14\S13_K10\_audit\VERDICT.md
  lead\next_re_20261117_r14\S13_K12\_audit\VERDICT.md
M3_UNIQ_FACT_LIST=F04,F06,F07,F08,F09,F10,F11,F12,F13,F14,F15,F16,F18,F19,F22,F23,F24,F25,F27,F28,F29,F34,F35,F36,F39,F43,F44,F45,F46,F47,F48,F49,F51,F52
M4_PARENT_DIR_MISSING=36
M4_FILE_MISSING_PARENT_EXISTS=7
M5_ALL_MISSING_FACTS=2
M5_HEADER='fact_id\tstatement\tgrade\tevidence_paths\tlimitations'
M5_FACT F23 cols=['F23', '④（第 4 列语义）三口径并列：口径 A（含字符 ④）458 行 / 27.69%；口径 B（含「④ 活表槽位见证」）291 行 / 17.59%；宽口径（B ∪ 「④ direct call」2 行，交集 0）293 行 / 17.71%；完全无 ④ 1,196 行。A − B = 167 行形态混杂（含仅 ③b④ 环标签、仅「④ 不同源」否定句等）⇒ 引用 ④ 必须注明口径，不得把口径 A 当作「四环齐全」。', '[已证]', 'lead\\next_re_20261117_r14\\R17_DELIVERY\\DELIVERY_SUMMARY.md(§2);lead\\next_re_20261117_r14\\COVERAGE\\PANEL.md(M86 / M93)', '口径必须写明。另：宽松子串 direct call 命中 12 行，按「减去含全串 ④ direct call 的 2 行」的减法读法为多计 10；按「相对宽口径 W=293 的集合差」为 9（因其中 3 行本已在 W 内）。两读法并列，引用时须注明是哪一种，不得单独写 10 或 9。该 12 行中 6 行为否定式（无 direct caller 等）、2 行为 callers 计数，真正非否定的多计仅 3 行且全为 direct caller。判 ④ 形态须用全串「④ direct call」。']
M5_FACT F35 cols=['F35', '硬规则（DoD 判据口径）：子系统达标须同时满足 named_S(R14) >= ceil(0.9n) 且 proved >= ceil(0.5n)；n 为该子系统 atlas 内分母；严格列另设 proved_strict（atlas 内 [已证] 且语义栏不含 [未证]），对外声明按严格列、名义列并列报告。', '[流程]', 'lead\\next_re_20261117_r14\\COVERAGE\\PANEL.md(M47 / M52 / 严格口径双列表)', 'ceil(0.9n)/ceil(0.5n)/proved_strict 均为卡面口径；PANEL M47 给判定式原文，M52 给达标复算，「严格口径双列表」给 proved_strict 定义（= atlas 内 [已证] 且语义栏不含 [未证]）；M44 是并表说明、正文无 proved_strict 定义。F25/F26 只记结果与裁定、未记判据式，故不重复。']
```

辅助扫描（TSV 中含反引号的条目数；反引号只出现在锚点内部，路径部分无反引号，故剥壳规则对总数无影响）：

```bash
python3 - <<'PYEOF'
import os
ROOT="/home/t628/projects/ra2-campaign-forge"
TSV=os.path.join(ROOT,"lead/next_re_20261117_r14/R17_R102_FACTINDEX_V530/FACT_INDEX.tsv")
OPEN={'(','（'};CLOSE={')','）'}
def split_items(f):
    out=[];buf=[];d=0
    for ch in f:
        if ch in OPEN:d+=1;buf.append(ch)
        elif ch in CLOSE:
            if d>0:d-=1
            buf.append(ch)
        elif ch==';' and d==0:out.append(''.join(buf));buf=[]
        else:buf.append(ch)
    out.append(''.join(buf));return [x for x in out if x.strip()]
with open(TSV,encoding='utf-8') as f:lines=f.read().splitlines()
data=[l for l in lines if l.strip()][1:]
allitems=[it.strip() for ln in data for it in split_items(ln.split('\t')[3])]
bt=[i for i in allitems if '`' in i]
print("TOTAL_ITEMS=%d ITEMS_WITH_BACKTICK=%d"%(len(allitems),len(bt)))
for i in bt[:20]:print("BT:"+repr(i))
PYEOF
```

输出原文：

```text
TOTAL_ITEMS=171 ITEMS_WITH_BACKTICK=2
BT:'lead\\next_re_20261117_r14\\R17_LEDGER_1065\\SECTION.md(86 个 `[reg+0x1AC]` 派发点重审 / 三重负面结果合并判断)'
BT:'lead\\next_re_20261117_r14\\R17_LEDGER_1065\\SECTION.md(`0x5657A0` 定性为公共工具 / `0x5A5020` 的三条静态到达路径)'
```

---

## M1 条目总数 = 171，其中带锚点 = 117

判定：成立

实测数字：条目总数 171（来自 54 条数据行的第 4 列），带锚点 117。

命令原文：见上「自测」节 `python3 /tmp/r70_t1_audit_parser.py`（输出中 `M1_TOTAL_ITEMS=171 / M1_ANCHORED_ITEMS=117`）。

输出原文：

```text
DATA_ROWS=54
M1_TOTAL_ITEMS=171
M1_ANCHORED_ITEMS=117
```

## M2 路径存在 = 128 条，不存在 = 43 条（合计 171）

判定：成立

实测数字：存在 128，不存在 43，合计 171。

命令原文：同上脚本（输出中 `M2_EXIST_ITEMS / M2_MISSING_ITEMS / M2_SUM`）。

输出原文：

```text
M2_EXIST_ITEMS=128
M2_MISSING_ITEMS=43
M2_SUM=171
```

## M3 不存在的 43 条去重后是 16 条不同路径，涉及 34 个 fact_id

判定：成立

实测数字：去重缺失路径 16 条，涉及 fact_id 34 个。清单见自测输出 `M3_UNIQ_PATH_LIST` 与 `M3_UNIQ_FACT_LIST`。

命令原文：同上脚本。

输出原文：

```text
M3_UNIQ_MISSING_PATHS=16
M3_UNIQ_MISSING_FACTS=34
```

## M4 存在 43 条缺失中，有 12 条其「父目录整体不存在」，另 4 条父目录存在但目标文件不存在

判定：不成立（按卡面字面「43 条缺失中」口径）

实测数字（43 条原始条目口径）：父目录不存在 = 36，父目录存在但文件不存在 = 7，合计 43。
实测数字（按去重 16 条路径口径）：父目录不存在 = 12，父目录存在但文件不存在 = 4，合计 16 —— 这与主张的 12/4 数值一致，但分母是 16 而非卡面所写的 43。

主张的数字：12 条父目录缺失 + 4 条父目录存在但文件缺失，表述为「43 条缺失中」。

命令原文（43 条口径）：见自测脚本输出 `M4_PARENT_DIR_MISSING / M4_FILE_MISSING_PARENT_EXISTS`。

输出原文（43 条口径）：

```text
M4_PARENT_DIR_MISSING=36
M4_FILE_MISSING_PARENT_EXISTS=7
```

命令原文（去重 16 条口径）：

```bash
cat > /tmp/r70_t1_m4m6.py <<'PYEOF'
#!/usr/bin/env python3
import os
ROOT="/home/t628/projects/ra2-campaign-forge"
TSV=os.path.join(ROOT,"lead/next_re_20261117_r14/R17_R102_FACTINDEX_V530/FACT_INDEX.tsv")
OPEN={'(','（'}; CLOSE={')','）'}
def strip_bt(s):
    s=s.strip()
    return s[1:-1] if len(s)>=2 and s[0]=='`' and s[-1]=='`' else s
def split_items(f):
    out=[];buf=[];d=0
    for ch in f:
        if ch in OPEN: d+=1;buf.append(ch)
        elif ch in CLOSE:
            if d>0:d-=1
            buf.append(ch)
        elif ch==';' and d==0:
            out.append(''.join(buf));buf=[]
        else: buf.append(ch)
    out.append(''.join(buf))
    return [x for x in out if x.strip()]
def parse(it):
    s=it.strip()
    if s and s[-1] in CLOSE:
        d=0;oi=-1
        for i in range(len(s)-1,-1,-1):
            c=s[i]
            if c in CLOSE:d+=1
            elif c in OPEN:
                d-=1
                if d==0:oi=i;break
        if oi>=0:return strip_bt(s[:oi]),s[oi+1:-1]
    return strip_bt(s),None
with open(TSV,encoding='utf-8') as f: lines=f.read().splitlines()
data=[l for l in lines if l.strip()][1:]
missing=[]
for ln in data:
    c=ln.split('\t')
    for it in split_items(c[3]):
        p,a=parse(it)
        if not os.path.exists(os.path.join(ROOT,p.replace('\\','/'))):
            missing.append(p)
uniq=sorted(set(missing))
pm=0;fe=0
print("=== M4 按去重 16 条路径统计父目录 ===")
for p in uniq:
    norm=p.replace('\\','/')
    parent=os.path.dirname(os.path.join(ROOT,norm))
    ispm=not os.path.isdir(parent)
    if ispm:pm+=1
    else:fe+=1
    print("PARENT_MISSING=%s | %s | parent=%s" % (ispm,p,os.path.relpath(parent,ROOT)))
print("UNIQ_TOTAL=%d PARENT_MISSING=%d FILE_MISSING_PARENT_EXISTS=%d"%(len(uniq),pm,fe))
PYEOF
python3 /tmp/r70_t1_m4m6.py
```

输出原文（去重 16 条口径）：

```text
=== M4 按去重 16 条路径统计父目录 ===
PARENT_MISSING=True | lead\next_re_20261117_r14\COVERAGE\PANEL.md | parent=lead/next_re_20261117_r14/COVERAGE
PARENT_MISSING=False | lead\next_re_20261117_r14\GATE_BEHAV\PROGRESS.md | parent=lead/next_re_20261117_r14/GATE_BEHAV
PARENT_MISSING=False | lead\next_re_20261117_r14\HANDOFF_R14_R3.md | parent=lead/next_re_20261117_r14
PARENT_MISSING=False | lead\next_re_20261117_r14\HANDOFF_R16.md | parent=lead/next_re_20261117_r14
PARENT_MISSING=True | lead\next_re_20261117_r14\NAMED_PUSH_AUDIT10\VERDICT.md | parent=lead/next_re_20261117_r14/NAMED_PUSH_AUDIT10
PARENT_MISSING=True | lead\next_re_20261117_r14\R17_AUDIT_FI_V5\VERDICT.md | parent=lead/next_re_20261117_r14/R17_AUDIT_FI_V5
PARENT_MISSING=True | lead\next_re_20261117_r14\R17_AUDIT_R9\VERDICT.md | parent=lead/next_re_20261117_r14/R17_AUDIT_R9
PARENT_MISSING=True | lead\next_re_20261117_r14\R17_DELIVERY\DELIVERY_SUMMARY.md | parent=lead/next_re_20261117_r14/R17_DELIVERY
PARENT_MISSING=True | lead\next_re_20261117_r14\R17_LEDGER_1062\SECTION.md | parent=lead/next_re_20261117_r14/R17_LEDGER_1062
PARENT_MISSING=True | lead\next_re_20261117_r14\R17_LEDGER_1063R\SECTION.md | parent=lead/next_re_20261117_r14/R17_LEDGER_1063R
PARENT_MISSING=False | lead\next_re_20261117_r14\R17_LEDGER_1063\SECTION.md | parent=lead/next_re_20261117_r14/R17_LEDGER_1063
PARENT_MISSING=True | lead\next_re_20261117_r14\R17_LEDGER_1064\SECTION.md | parent=lead/next_re_20261117_r14/R17_LEDGER_1064
PARENT_MISSING=True | lead\next_re_20261117_r14\R17_LEDGER_1065\SECTION.md | parent=lead/next_re_20261117_r14/R17_LEDGER_1065
PARENT_MISSING=True | lead\next_re_20261117_r14\S10_KPROVED\_audit\VERDICT.md | parent=lead/next_re_20261117_r14/S10_KPROVED/_audit
PARENT_MISSING=True | lead\next_re_20261117_r14\S13_K10\_audit\VERDICT.md | parent=lead/next_re_20261117_r14/S13_K10/_audit
PARENT_MISSING=True | lead\next_re_20261117_r14\S13_K12\_audit\VERDICT.md | parent=lead/next_re_20261117_r14/S13_K12/_audit
UNIQ_TOTAL=16 PARENT_MISSING=12 FILE_MISSING_PARENT_EXISTS=4
```

## M5 全部 54 个 fact 中，有 2 个 fact 的所有 evidence_paths 都不存在，它们是 F23 与 F35；且 F23 的 grade 是[已证]、F35 的 grade 是[流程]

判定：成立

实测数字：全缺失 fact 数 = 2，为 F23（grade `[已证]`）与 F35（grade `[流程]`）；表头为 `fact_id/statement/grade/evidence_paths/limitations`，grade 取第 3 列。

命令原文：见自测脚本输出 `M5_ALL_MISSING_FACTS / M5_HEADER / M5_FACT ...`（完整输出已在「自测」节贴出，此处摘录 grade 与路径列）。

输出原文：

```text
M5_ALL_MISSING_FACTS=2
M5_HEADER='fact_id\tstatement\tgrade\tevidence_paths\tlimitations'
M5_FACT F23 ... '[已证]', 'lead\\next_re_20261117_r14\\R17_DELIVERY\\DELIVERY_SUMMARY.md(§2);lead\\next_re_20261117_r14\\COVERAGE\\PANEL.md(M86 / M93)', ...
M5_FACT F35 ... '[流程]', 'lead\\next_re_20261117_r14\\COVERAGE\\PANEL.md(M47 / M52 / 严格口径双列表)', ...
```

## M6 存在一个名为 anchor_check.txt 的文件，它声称「路径项 171 / 文件存在 171 / 171 / MISS 0」，与本机实测不符

判定：成立

实测数字：文件存在（ls 显示 `-rw-rw-r-- 1 t628 t628 921 Nov 22 18:41 ...`）；原文含「路径项 171 / 文件存在 171 / 171 / MISS 0」；本机实测存在 128 / 不存在 43，与该文件声称的 171/171、MISS 0 不符。

命令原文（文件存在性）：

```bash
ls -la lead/next_re_20261117_r14/R17_R102_FACTINDEX_V530/anchor_check.txt 2>&1
```

输出原文：

```text
-rw-rw-r-- 1 t628 t628 921 Nov 22 18:41 lead/next_re_20261117_r14/R17_R102_FACTINDEX_V530/anchor_check.txt
```

命令原文（原文读取，接在 `/tmp/r70_t1_m4m6.py` 末尾）：

```python
ap=os.path.join(ROOT,"lead/next_re_20261117_r14/R17_R102_FACTINDEX_V530/anchor_check.txt")
print(open(ap,encoding='utf-8').read())
```

输出原文（结果段）：

```text
--- 结果 ---
  路径项                171
  文件存在              171 / 171
  带锚点                117
    机械核验通过        104
    节号体例通过        13
    池未加载(未核验)    0
    人工核验类(无节号)  0
    目录即卡(可接受)    0
    目录+锚(NG)         0
    MISS                0
```

---

## 与主张不一致处

M4：主张称「43 条缺失中，12 条父目录整体不存在，另 4 条父目录存在但文件不存在」。我在 43 条原始条目口径下实测为 36 条父目录不存在 + 7 条父目录存在但文件不存在（合计 43）；主张的 12 + 4 合计仅 16，等于去重后的不同路径数，而非 43。两种口径的实测数字均已在 M4 节列出。M1/M2/M3/M5/M6 与主张一致。
