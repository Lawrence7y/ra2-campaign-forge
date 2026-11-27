# R182 · C20 执行复算报告（exec / hy4）

> 角色：exec，家族 hy4。全程只读生产；唯一写入为本文。Q5 的实验全部在 `/tmp/r182c20.QvMfU0` 的**拷贝**上完成，未建任何软链、未运行整份门禁、未触碰 `_r160` / `_r161` 生产实体。

## Q1 — 生产主门禁 exit 0 且同时含 C19/C20 两个 ok 行

**命令**
```bash
cd /home/t628/projects/ra2-campaign-forge && python3 lead/next_re_20261117_r14/check_disc.py
```

**原始输出关键行**
```
  NOTE  C19 fact-layer link (pointer-driven): 'lead/next_re_20261117_r14/R17_R131_FACTINDEX_V563/FACT_INDEX.tsv' sha 28423e79 bytes 133310 ; facts_floors EXPECT_CUR/CUR_SHA256/TOTAL_BYTES all agree
  NOTE  C20 three-way ledger path (runner/facts/pointer): all three resolve to '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/R17_R131_FACTINDEX_V563/FACT_INDEX.tsv'
C19 fact-layer link: ok(28423e79/133310/R17_R131_FACTINDEX_V563)
C20 three-way ledger path: ok(R17_R131_FACTINDEX_V563)
  PASS  structure/paths/sections/self all ok ; live checks 31
[exit 0]
```
裸退出码回显 `Q1_EXIT=0`。

**结论**：确认。同一轮输出里 C19 与 C20 各有独立 `ok` 行，进程 exit 0。

## Q2 — C20 块内版本号字面量计数

**命令（一次跑完；用 tokenize 区分注释/代码）**
```bash
python3 - <<'PYEOF'
import re,io,tokenize
p='/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/check_disc.py'
cd=open(p,encoding='utf-8').read(); L=cd.split('\n')
s=next(i for i,l in enumerate(L) if l.startswith('# ---- C20 [R182 新增]'))
e=next(i for i,l in enumerate(L) if l.startswith('# ---- C5 CR 抽查 ----'))
blk='\n'.join(L[s:e])
hits=re.findall(r'R17_R13\d+_FACTINDEX_V\d+',blk)
comments={t.start[0] for t in tokenize.generate_tokens(io.StringIO(blk).readline) if t.type==tokenize.COMMENT}
print(e-s,len(hits))
PYEOF
```

**原始输出关键行**
```
block lines= 71
raw_version_literals= 1
code_version_literals= 0
C20 line(1based in block)= 4  in_comment=True  #   LEDGER = os.path.join(TIER, 'R17_R131_FACTINDEX_V563', 'FACT_INDEX.tsv')
```

**结论**：以「形如 `R17_R13x_FACTINDEX_Vnnn` 的字面量」计，块内出现 **1 处**（第 4 行）；但它在**注释**里，**可执行代码中的字面量为 0**，符合期望的 0 处（代码侧硬编码为零）。如实登记差别：卡面期望「0 处」只有在排除注释时成立。

## Q3 — 三处版本目录字面量各自独立？

**命令**：同 Q2 的脚本，对三个文件逐一 `re.findall(r"'R17_R13\d+_FACTINDEX_V\d+'", src)`，并用 `tokenize` 标注每个命中是否在注释内。

**原始输出关键行**
```
Q3 check_disc  raw=2  in_comments=2  code=0
   cd line 1146  in_comment=True   # os.path.join(TIER, 'R17_R131_FACTINDEX_V563', 'FACT_INDEX.tsv') —— 是 Call
   cd line 1179  in_comment=True   #   LEDGER = os.path.join(TIER, 'R17_R131_FACTINDEX_V563', 'FACT_INDEX.tsv')
Q3 facts_floors  raw=1  in_comments=0  code=1     # 第 46 行 EXPECT_CUR
Q3 gate_runner   raw=1  in_comments=0  code=1     # 第 51 行 LEDGER
```

**结论**：三份文件各持自己的字面量：`facts_floors.py` 与 `gate_runner.py` 各有 1 处**代码**字面量（同形 `os.path.join(TIER, 'R17_R131_FACTINDEX_V563', 'FACT_INDEX.tsv')`，分别在 46/51 行）；`check_disc.py` 自身 2 处命中**全部在注释里**，代码侧 0 处。即 C20 的实现没有在门禁里再抄第三份版本常量，而是词法解析另外两份 + 读指针。

## Q4 — C20 核心等式复算

**命令**
```bash
python3 - <<'PYEOF'
import os,re
B='/home/t628/projects/ra2-campaign-forge'; T=os.path.join(B,'lead','next_re_20261117_r14')
def join_of(p,var):
    t=open(p,encoding='utf-8').read()
    m=re.search(r'^\s*'+var+r'\s*=\s*os\.path\.join\(\s*TIER\s*,\s*\'([^\']+)\'\s*,\s*\'([^\']+)\'\s*\)',t,re.M)
    return os.path.join(T,*m.groups())
g=join_of(B+'/_r161/gate_runner.py','LEDGER'); f=join_of(B+'/_r160/facts_floors.py','EXPECT_CUR')
rel=re.search(r'\|\s*相对路径\s*\|\s*(\S+)\s*\|',open(T+'/FACT_INDEX_CURRENT.md',encoding='utf-8').read()).group(1)
p=os.path.normpath(os.path.join(B,rel))
print(g,f,p,g==f,f==p,g==p)
PYEOF
```

**原始输出关键行**
```
gate_runner.LEDGER       = /home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/R17_R131_FACTINDEX_V563/FACT_INDEX.tsv
facts_floors.EXPECT_CUR  = /home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/R17_R131_FACTINDEX_V563/FACT_INDEX.tsv
pointer-rel = lead/next_re_20261117_r14/R17_R131_FACTINDEX_V563/FACT_INDEX.tsv -> /home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/R17_R131_FACTINDEX_V563/FACT_INDEX.tsv
g==f: True  f==p: True  g==p: True
三者 exists=True, realpath 均等于同一路径（无软链差异）
```

**解析方式**：runner/facts 两处用正则取 `os.path.join(TIER, DIR, FILE)` 的实参，TIER 取各自文件里的 `TIER = os.path.join(ROOT,'lead','next_re_20261117_r14')`（runner 的 ROOT 为绝对路径 `/home/t628/projects/ra2-campaign-forge`；facts 的 ROOT 为 `dirname(dirname(abspath(__file__)))`，同值）；指针取表格「相对路径」字段，相对仓库根 `os.path.normpath` 展开。三者字符串逐字相同。

**结论**：等式成立。

## Q5 — C20 分辨力的 /tmp 隔离实验

**命令要点**（沙箱 `D=$(mktemp -d /tmp/r182c20.XXXXXX)`；仅 `cp` 四个文件到 `$D`，未建目录软链、未跑整份 `check_disc.py`）：
```bash
cp lead/next_re_20261117_r14/check_disc.py _r161/gate_runner.py _r160/facts_floors.py \
   lead/next_re_20261117_r14/FACT_INDEX_CURRENT.md "$D/"
# 5 行小程序：解析 runner LEDGER、facts EXPECT_CUR、指针相对路径，打印两条相等关系
python3 "$D/mini.py" "$D/gate_runner.py" "$D/facts_floors.py" "$D/FACT_INDEX_CURRENT.md"
# 只在 $D/gate_runner.py 里把 V563 -> V562，再跑；随后把 $D 中 facts 与指针也改成 V562，再跑
```

**原始输出关键行**
```
SANDBOX=/tmp/r182c20.QvMfU0
--- BEFORE ---
runner==facts: True  runner==pointer: True
--- AFTER runner-only V562 ---
runner==facts: False  runner==pointer: False
runner .../V562/FACT_INDEX.tsv | facts .../V563/FACT_INDEX.tsv | pointer .../V563/FACT_INDEX.tsv
--- AFTER all-three V562 ---
runner==facts: True  runner==pointer: True
三者均 .../V562/FACT_INDEX.tsv
LEDGER-version-literal-count: baseline=1  sandbox=1
sanity: 生产 _r161/gate_runner.py:51、_r160/facts_floors.py:46、指针第 10 行仍为 V563
```

**结论**：C20 的两条比较有真实分辨力——只漂移 runner 一份即双红；三份同步漂移则双绿（见 Q7）。拷贝中的 LEDGER 版本字面量仍恰为 1，不会触发「多份漂移常量」的附加判据。生产文件在实验后仍为 V563，未被触碰。

## Q6 — 两个 sha256 常量与 facts_floors.py 自跑

**命令**
```bash
python3 - <<'PYEOF'   # 提取两个 64 位常量
import re
s=open('/home/t628/projects/ra2-campaign-forge/_r160/facts_floors.py',encoding='utf-8').read()
for n in ('MASTER_SHA256','CUR_SHA256'):
    v=re.search(r'^'+n+r'\s*=\s*\'([^\']+)\'',s,re.M).group(1); print(n,len(v),v)
PYEOF
python3 /home/t628/projects/ra2-campaign-forge/_r160/facts_floors.py
```

**原始输出关键行**
```
MASTER_SHA256 len=64 eab670346cd14b6ee5b311e6d20cd36eec04dafc3e3aa1c12211f3be945df1cf
CUR_SHA256    len=64 28423e7928d8414216b6a09f8ea56ef60d484dbd121cf9e5d673ffc3bc45db46
  D0 sha=28423e7928d84142 pinned=28423e7928d84142
  D9 master pin: eab670346cd14b6ee5b311e6d20cd36eec04dafc3e3aa1c12211f3be945df1cf (pinned eab670...1cf)
  D10 pointer sha=28423e7928d84142... bytes=133310 vs CUR 28423e7928d84142.../133310 (on-disk 28423e7928d84142...)
  PASS  structure/scale/ownership/evidence-chain all ok
[exit 0]   (Q6_facts_EXIT=0)
```

**结论**：两个常量均为完整 64 位十六进制；`facts_floors.py` 自跑 exit 0。

## Q7 — C20 能证什么、不能证什么（仅据本次实测）

**能证**：
1. 在 Q1 的生产状态下，三处解析出的**绝对路径字符串逐字相同**（Q4 三个 `True`、`realpath` 同一、文件存在）。
2. 它确实能抓「单点漂移」：Q5 沙箱只改 runner 为 V562 时，runner-vs-facts 与 runner-vs-pointer 两条同时变 `False`。C20 不是哑判据。
3. `check_disc.py` 代码侧无第四份版本硬编码（Q3 code=0），所以判据值来自解析而非抄写。

**不能证**：
1. **不能证「所指版本是当前版／正确版」**。Q5 最后一步把沙箱三份同步改成 V562 后，两条比较都回到 `True`；按 C20 的比较逻辑，这种全绿状态不会因 C20 自身变红。答案：三处同时改成同一份旧版本时，**C20 是绿**。
2. 不能证所指台账内容为真，也不能证该台账的 sha/字节数正确（那是 C19/D0/D10 的职责；本次未把 C20 与它们混同）。
3. 不能排除两处代码字面量同一时刻被同一个编辑动作改写（Q3 显示它们本来就是各自独立的源码字面量，C20 只比对解析结果）。

以上均由 Q1/Q4/Q5/Q6 的实测直接支撑，未引用卡面结论。
