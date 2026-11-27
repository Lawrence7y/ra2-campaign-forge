# R150-A 执行报告（exec 子代理，家族 hy4）：FACT_INDEX 证据存活普查 + 外部 triage 口径对账

## 第 1 节 命令原文与原始输出摘录

三条 python3 命令跑完 12 项（1 条主普查 + 1 条控制补算 + 1 条 F35/换行符补取）。

命令 A（主普查，只读）：

    python3 - <<'PY'
    import io,os,hashlib,collections,re
    ROOT='/home/t628/projects/ra2-campaign-forge'
    V540=os.path.join(ROOT,'lead/next_re_20261117_r14/R17_R112_FACTINDEX_V540/FACT_INDEX.tsv')
    V532=os.path.join(ROOT,'lead/next_re_20261117_r14/R17_R104_FACTINDEX_V532/FACT_INDEX.tsv')
    TRI=os.path.join(ROOT,'_ext/f_partial_triage/TRIAGE.tsv')
    PYINS=os.path.join(ROOT,'_ext/f_partial_triage/triage.py')
    def sha(p):
     h=hashlib.sha256()
     with open(p,'rb') as f:
      for c in iter(lambda:f.read(65536),b''):h.update(c)
     return h.hexdigest()
    def rows(p):return [l.rstrip('\n').split('\t') for l in io.open(p,encoding='utf-8') if l.strip('\n')]
    def cut(e):
     e=e.strip(); i=e.find('(')
     return (e[:i] if i>=0 else e).replace('\\','/').strip()
    def alive(rel):
     return os.path.exists(os.path.join(ROOT,rel)) or os.path.exists(os.path.join(ROOT,'lead',rel))
    def dump(fix):
     rr=rows(fix); hdr=rr[0]; body=[r for r in rr[1:]]
     ids=[r[0] for r in body]
     print('ROWS',len(body),'COLS',set(map(len,rr)),'IDSEQ',ids==['F%02d'%i for i in range(1,55)])
     print('SHA',sha(fix),'BYTES',os.path.getsize(fix))
     ents=[]; seen=set(); lost=[]
     for r in body:
      es=[x for x in r[3].split(';') if x.strip()]
      ents.append(es)
      for e in es:
       rel=cut(e)
       if not alive(rel):
        lost.append(rel);seen.add(rel)
     ap=sum(map(len,ents))
     print('ENTRIES',ap,'LOST_ENTRIES',len(lost),'UNIQ_LOST',len(seen))
     for x in sorted(seen):print('LOSTPATH',x)
     zero=[];part=[];gd=collections.Counter()
     for r,es in zip(body,ents):
      gd[r[2]]+=1
      dead=sum(1 for e in es if not alive(cut(e)))
      if len(es)-dead==0:zero.append((r[0],r[2]))
      elif dead>0:part.append(r[0])
     print('ZERO_ALIVE',len(zero),zero)
     print('GRADE',dict(gd))
     print('PART',len(part),' '.join(part))
     return seen,set(part)
    s54,p54=dump(V540)
    s32,p32=dump(V532)
    for fid in ('F23','F35'):
     for tag,fix in (('V532',V532),('V540',V540)):
      rr=rows(fix);r=[x for x in rr if x and x[0]==fid][0]
      print(fid,tag,'N',len([e for e in r[3].split(';') if e.strip()]))
    txt=io.open(PYINS,encoding='utf-8').read()
    m=[l for l in txt.splitlines() if l.startswith('FIX =')][0]
    lit=m.split("'")[1] if "'" in m else m.split('"')[1]
    fp=os.path.join(ROOT,lit)
    print('FIXLIT',lit,'SHA',sha(fp),'SAME',sha(fp)==sha(V540))
    tr=rows(TRI)
    print('TRIAGE_ROWS',len(tr)-1,'FIDS',sorted(r[0] for r in tr[1:]))
    vc=collections.Counter(r[4] for r in tr[1:])
    print('VERDICTS',dict(vc))
    for k in ('仍可核验','需重建','不可核验'):print('VFIDS',k,' '.join(r[0] for r in tr[1:] if r[4]==k))
    tset=set(r[0] for r in tr[1:])
    print('DIFF_P_NOT_T',len(p54-tset),sorted(p54-tset))
    print('DIFF_T_NOT_P',len(tset-p54),sorted(tset-p54))
    cnt=0;bad=[]
    for r in tr[1:]:
     for e in r[3].split(';'):
      if not e.strip():continue
      cnt+=1;rel=cut(e)
      if not alive(rel):bad.append(rel)
    print('T_ALIVE_NAMED',cnt,'T_BAD',len(bad))
    for x in bad:print('TBAD',x)
    for label,rel in [('POS','lead/next_re_20261117_r14/R14_COMMON.md'),('NEG1','ZZZ_NOT_ON_DISK_QQQ.md'),('NEG2','lead/next_re_20261117_r14/COVERAGE/PANEL.md'),('POSWIN','lead\\next_re_20261117_r14\\R14_COMMON.md')]:
     print('CTRL',label,'RAW',rel,'NORM',cut(rel),'ALIVE',alive(rel))
    PY

命令 A 输出摘录（完整，VERDICTS 行为实测值）：

    ROWS 54 COLS {5} IDSEQ True
    SHA fabd1e5702814b5c6f89737d905e40a01da241981c8d84361869b2243821d07a BYTES 88786
    ENTRIES 178 LOST_ENTRIES 43 UNIQ_LOST 16
    LOSTPATH lead/next_re_20261117_r14/COVERAGE/PANEL.md
    LOSTPATH lead/next_re_20261117_r14/GATE_BEHAV/PROGRESS.md
    LOSTPATH lead/next_re_20261117_r14/HANDOFF_R14_R3.md
    LOSTPATH lead/next_re_20261117_r14/HANDOFF_R16.md
    LOSTPATH lead/next_re_20261117_r14/NAMED_PUSH_AUDIT10/VERDICT.md
    LOSTPATH lead/next_re_20261117_r14/R17_AUDIT_FI_V5/VERDICT.md
    LOSTPATH lead/next_re_20261117_r14/R17_AUDIT_R9/VERDICT.md
    LOSTPATH lead/next_re_20261117_r14/R17_DELIVERY/DELIVERY_SUMMARY.md
    LOSTPATH lead/next_re_20261117_r14/R17_LEDGER_1062/SECTION.md
    LOSTPATH lead/next_re_20261117_r14/R17_LEDGER_1063/SECTION.md
    LOSTPATH lead/next_re_20261117_r14/R17_LEDGER_1063R/SECTION.md
    LOSTPATH lead/next_re_20261117_r14/R17_LEDGER_1064/SECTION.md
    LOSTPATH lead/next_re_20261117_r14/R17_LEDGER_1065/SECTION.md
    LOSTPATH lead/next_re_20261117_r14/S10_KPROVED/_audit/VERDICT.md
    LOSTPATH lead/next_re_20261117_r14/S13_K10/_audit/VERDICT.md
    LOSTPATH lead/next_re_20261117_r14/S13_K12/_audit/VERDICT.md
    ZERO_ALIVE 1 [('F23', '[已证]')]
    GRADE {'[已证]': 27, '[静态推断]': 1, '未取得': 2, '[流程]': 24}
    PART 33 F04 F06 F07 F08 F09 F10 F11 F12 F13 F14 F15 F16 F18 F19 F22 F24 F25 F27 F28 F29 F34 F35 F36 F39 F43 F44 F45 F46 F47 F48 F49 F51 F52
    ROWS 54 COLS {5} IDSEQ True
    SHA 84863896227062179adc6e437eff3cf89e437fc6a131620a1f50e831b52cf92f BYTES 61822
    ENTRIES 171 LOST_ENTRIES 43 UNIQ_LOST 16
    （16 条 LOSTPATH 字面与 V540 相同，此处省略重复输出）
    ZERO_ALIVE 2 [('F23', '[已证]'), ('F35', '[流程]')]
    GRADE {'[已证]': 27, '[静态推断]': 1, '未取得': 2, '[流程]': 24}
    PART 32 F04 F06 F07 F08 F09 F10 F11 F12 F13 F14 F15 F16 F18 F19 F22 F24 F25 F27 F28 F29 F34 F36 F39 F43 F44 F45 F46 F47 F48 F49 F51 F52
    F23 V532 N 2
    F23 V540 N 2
    F35 V532 N 1
    F35 V540 N 5
    FIXLIT lead/next_re_20261117_r14/R17_R104_FACTINDEX_V532/FACT_INDEX.tsv SHA 84863896227062179adc6e437eff3cf89e437fc6a131620a1f50e831b52cf92f SAME False
    TRIAGE_ROWS 32 FIDS ['F04', 'F06', 'F07', 'F08', 'F09', 'F10', 'F11', 'F12', 'F13', 'F14', 'F15', 'F16', 'F18', 'F19', 'F22', 'F24', 'F25', 'F27', 'F28', 'F29', 'F34', 'F36', 'F39', 'F43', 'F44', 'F45', 'F46', 'F47', 'F48', 'F49', 'F51', 'F52']
    VERDICTS {'仍可核验': 5, '需重建': 18, '不可核验': 9}
    VFIDS 仍可核验 F04 F11 F14 F15 F49
    VFIDS 需重建 F06 F07 F08 F12 F13 F16 F18 F24 F27 F29 F34 F36 F39 F43 F44 F45 F47 F48
    VFIDS 不可核验 F09 F10 F19 F22 F25 F28 F46 F51 F52
    DIFF_P_NOT_T 1 ['F35']
    DIFF_T_NOT_P 0 []
    T_ALIVE_NAMED 91 T_BAD 0
    TBAD （无）
    CTRL POS RAW lead/next_re_20261117_r14/R14_COMMON.md NORM lead/next_re_20261117_r14/R14_COMMON.md ALIVE True
    CTRL NEG1 RAW ZZZ_NOT_ON_DISK_QQQ.md NORM ZZZ_NOT_ON_DISK_QQQ.md ALIVE False
    CTRL NEG2 RAW lead/next_re_20261117_r14/COVERAGE/PANEL.md NORM lead/next_re_20261117_r14/COVERAGE/PANEL.md ALIVE False
    CTRL POSWIN RAW lead\next_re_20261117_r14\R14_COMMON.md NORM lead/next_re_20261117_r14/R14_COMMON.md ALIVE False

其中命令 A 的最后一行 POSWIN 为 False 是控制调用本身的瑕疵：该处直接把含反斜杠的原串传入 alive()，未走 cut() 归一化。命令 B 按真实普查管线（先 cut() 再 alive()）复算，四控全部正确。

命令 B（控制补算，经归一化）：

    python3 - <<'PY'
    import os
    ROOT='/home/t628/projects/ra2-campaign-forge'
    def cut(e):
     e=e.strip();i=e.find('(')
     return (e[:i] if i>=0 else e).replace('\\','/').strip()
    def alive(rel):
     return os.path.exists(os.path.join(ROOT,rel)) or os.path.exists(os.path.join(ROOT,'lead',rel))
    for label,raw in [('POS','lead/next_re_20261117_r14/R14_COMMON.md'),('NEG1','ZZZ_NOT_ON_DISK_QQQ.md'),('NEG2','lead/next_re_20261117_r14/COVERAGE/PANEL.md'),('POSWIN','lead\\next_re_20261117_r14\\R14_COMMON.md')]:
     n=cut(raw)
     print('CTRL',label,'RAW',raw,'NORM',n,'ALIVE',alive(n))
    PY

命令 B 输出：

    CTRL POS RAW lead/next_re_20261117_r14/R14_COMMON.md NORM lead/next_re_20261117_r14/R14_COMMON.md ALIVE True
    CTRL NEG1 RAW ZZZ_NOT_ON_DISK_QQQ.md NORM ZZZ_NOT_ON_DISK_QQQ.md ALIVE False
    CTRL NEG2 RAW lead/next_re_20261117_r14/COVERAGE/PANEL.md NORM lead/next_re_20261117_r14/COVERAGE/PANEL.md ALIVE False
    CTRL POSWIN RAW lead\next_re_20261117_r14\R14_COMMON.md NORM lead/next_re_20261117_r14/R14_COMMON.md ALIVE True

命令 C（F35 原始项、换行符补取）：

    python3 - <<'PY'
    import io,os
    ROOT='/home/t628/projects/ra2-campaign-forge'
    V540=os.path.join(ROOT,'lead/next_re_20261117_r14/R17_R112_FACTINDEX_V540/FACT_INDEX.tsv')
    V532=os.path.join(ROOT,'lead/next_re_20261117_r14/R17_R104_FACTINDEX_V532/FACT_INDEX.tsv')
    for tag,p in (('V540',V540),('V532',V532)):
     b=open(p,'rb').read()
     print(tag,'CR_COUNT',b.count(b'\r'),'LF_COUNT',b.count(b'\n'),'ENDS_NL',b.endswith(b'\n'))
     r=[l.rstrip('\n').split('\t') for l in io.open(p,encoding='utf-8') if l.strip('\n')]
     f35=[x for x in r if x and x[0]=='F35'][0]
     print(tag,'F35_GRADE',f35[2])
     for i,e in enumerate([e for e in f35[3].split(';') if e.strip()],1):
      print(tag,'F35_E',i,repr(e))
    PY

命令 C 输出：

    V540 CR_COUNT 0 LF_COUNT 55 ENDS_NL True
    V540 F35_GRADE [流程]
    V540 F35_E 1 'lead\\next_re_20261117_r14\\COVERAGE\\PANEL.md(M47 / M52 / 严格口径双列表)'
    V540 F35_E 2 'lead\\next_re_20261117_r14\\RULING_R15_20261119\\work\\strict_panel.py(78 行判据 + 14 行散文措辞)'
    V540 F35_E 3 'lead\\next_re_20261117_r14\\_cards\\M59-MERGE\\precheck.py(60)'
    V540 F35_E 4 'lead\\next_re_20261117_r14\\_cards\\M59-MERGE\\simulate.py(72)'
    V540 F35_E 5 'lead\\next_re_20261117_r14\\_cards\\M59-MERGE\\verify.py(83)'
    V532 CR_COUNT 0 LF_COUNT 55 ENDS_NL True
    V532 F35_GRADE [流程]
    V532 F35_E 1 'lead\\next_re_20261117_r14\\COVERAGE\\PANEL.md(M47 / M52 / 严格口径双列表)'

## 第 2 节 基础台账与证据普查（对应第 1、2、3、4、5、6 项）

结论：v5.40 FACT_INDEX 与卡面预期完全一致（54 行、5 列、F01..F54 连续、sha256 fabd1e57 开头、88,786 B、全 LF）；共 178 个 evidence_paths 项，43 项失联，归并 16 个唯一失联路径；存活项为 0 的行恰好 1 行（F23，grade 原文 已证）；部分失联行 33 条（含 F35）；grade 分布为 已证 27、静态推断 1、未取得 2、流程 24。

支撑数字（v5.40）：

    ROWS 54 COLS {5} IDSEQ True
    SHA fabd1e5702814b5c6f89737d905e40a01da241981c8d84361869b2243821d07a BYTES 88786
    CR_COUNT 0 LF_COUNT 55 ENDS_NL True
    ENTRIES 178 LOST_ENTRIES 43 UNIQ_LOST 16
    ZERO_ALIVE 1 [('F23', '[已证]')]
    GRADE {'[已证]': 27, '[静态推断]': 1, '未取得': 2, '[流程]': 24}
    PART 33 F04 F06 F07 F08 F09 F10 F11 F12 F13 F14 F15 F16 F18 F19 F22 F24 F25 F27 F28 F29 F34 F35 F36 F39 F43 F44 F45 F46 F47 F48 F49 F51 F52

16 个唯一失联路径字面（逐条，按字典序）：

    lead/next_re_20261117_r14/COVERAGE/PANEL.md
    lead/next_re_20261117_r14/GATE_BEHAV/PROGRESS.md
    lead/next_re_20261117_r14/HANDOFF_R14_R3.md
    lead/next_re_20261117_r14/HANDOFF_R16.md
    lead/next_re_20261117_r14/NAMED_PUSH_AUDIT10/VERDICT.md
    lead/next_re_20261117_r14/R17_AUDIT_FI_V5/VERDICT.md
    lead/next_re_20261117_r14/R17_AUDIT_R9/VERDICT.md
    lead/next_re_20261117_r14/R17_DELIVERY/DELIVERY_SUMMARY.md
    lead/next_re_20261117_r14/R17_LEDGER_1062/SECTION.md
    lead/next_re_20261117_r14/R17_LEDGER_1063/SECTION.md
    lead/next_re_20261117_r14/R17_LEDGER_1063R/SECTION.md
    lead/next_re_20261117_r14/R17_LEDGER_1064/SECTION.md
    lead/next_re_20261117_r14/R17_LEDGER_1065/SECTION.md
    lead/next_re_20261117_r14/S10_KPROVED/_audit/VERDICT.md
    lead/next_re_20261117_r14/S13_K10/_audit/VERDICT.md
    lead/next_re_20261117_r14/S13_K12/_audit/VERDICT.md

## 第 3 节 triage 输入版本与 F35 增项（对应第 7、8 项）

结论：triage.py 的 FIX 常量指向 v5.32，不是现盘 v5.40（sha256 不同，不是同一文件）；F35 的 evidence_paths 项数从 v5.32 的 1 项变为 v5.40 的 5 项，四新增项均指向 _cards/M59-MERGE 与 RULING_R15_20261119 下的在盘脚本，故 F35 在 v5.40 从「存活项为 0」变为「部分失联」。

支撑数字：

    FIXLIT lead/next_re_20261117_r14/R17_R104_FACTINDEX_V532/FACT_INDEX.tsv
    SHA 84863896227062179adc6e437eff3cf89e437fc6a131620a1f50e831b52cf92f
    SAME False
    V540 SHA fabd1e5702814b5c6f89737d905e40a01da241981c8d84361869b2243821d07a
    F35 V532 N 1
    F35 V540 N 5
    V540 F35_E 1 'lead\\next_re_20261117_r14\\COVERAGE\\PANEL.md(M47 / M52 / 严格口径双列表)'
    V540 F35_E 2 'lead\\next_re_20261117_r14\\RULING_R15_20261119\\work\\strict_panel.py(78 行判据 + 14 行散文措辞)'
    V540 F35_E 3 'lead\\next_re_20261117_r14\\_cards\\M59-MERGE\\precheck.py(60)'
    V540 F35_E 4 'lead\\next_re_20261117_r14\\_cards\\M59-MERGE\\simulate.py(72)'
    V540 F35_E 5 'lead\\next_re_20261117_r14\\_cards\\M59-MERGE\\verify.py(83)'
    V532 F35_E 1 'lead\\next_re_20261117_r14\\COVERAGE\\PANEL.md(M47 / M52 / 严格口径双列表)'

## 第 4 节 TRIAGE.tsv 三档统计（对应第 9 项）

结论：TRIAGE.tsv 有 32 个数据行、6 列，三档计数为 仍可核验 5、需重建 18、不可核验 9（合计 32）；fid 集合恰好是 v5.32 的 32 条部分失联行，不含 F23、F35。

支撑数字：

    TRIAGE_ROWS 32
    VERDICTS {'仍可核验': 5, '需重建': 18, '不可核验': 9}
    VFIDS 仍可核验 F04 F11 F14 F15 F49
    VFIDS 需重建 F06 F07 F08 F12 F13 F16 F18 F24 F27 F29 F34 F36 F39 F43 F44 F45 F47 F48
    VFIDS 不可核验 F09 F10 F19 F22 F25 F28 F46 F51 F52
    TRIAGE_FIDS F04 F06 F07 F08 F09 F10 F11 F12 F13 F14 F15 F16 F18 F19 F22 F24 F25 F27 F28 F29 F34 F36 F39 F43 F44 F45 F46 F47 F48 F49 F51 F52

## 第 5 节 现盘部分失联集合与 triage 覆盖差集（对应第 10 项）

结论：现盘 v5.40 部分失联集合相对 triage 覆盖集合多出 F35 这一条（1 条），triage 覆盖集合相对现盘无多出项（0 条）；根因见第 3 节：v5.40 给 F35 补了 4 条在盘脚本证据，而 triage 基于 v5.32（F35 全链失联）因而未覆盖。

支撑数字：

    DIFF_P_NOT_T 1 ['F35']
    DIFF_T_NOT_P 0 []

## 第 6 节 TRIAGE alive_paths 逐路径存活核验（对应第 11 项）

结论：TRIAGE.tsv 第 4 列 alive_paths 按「第一个左圆括号处切」解析共点名 91 件路径（含分号重复项，含嵌套括号锚点如 R14_COMMON.md(§2.10 / 一 / (a′)) 按首括号切出路径本体），按仓库根与仓库根加 lead/ 两种拼法判活，不存在件数 0。

支撑数字：

    T_ALIVE_NAMED 91 T_BAD 0
    TBAD （无）

## 第 7 节 正反控制（对应第 12 项）

结论：四条控制全部按预期通过——两条正控判活，两条负控判死；win 风格串必须先经反斜杠转正斜杠再判活。命令 A 中 POSWIN 的 False 是该控制调用未走归一化管线的瑕疵，命令 B 按普查真实管线复算为 True，应以命令 B 为准。

支撑数字（命令 B 原始输出）：

    CTRL POS RAW lead/next_re_20261117_r14/R14_COMMON.md NORM lead/next_re_20261117_r14/R14_COMMON.md ALIVE True
    CTRL NEG1 RAW ZZZ_NOT_ON_DISK_QQQ.md NORM ZZZ_NOT_ON_DISK_QQQ.md ALIVE False
    CTRL NEG2 RAW lead/next_re_20261117_r14/COVERAGE/PANEL.md NORM lead/next_re_20261117_r14/COVERAGE/PANEL.md ALIVE False
    CTRL POSWIN RAW lead\next_re_20261117_r14\R14_COMMON.md NORM lead/next_re_20261117_r14/R14_COMMON.md ALIVE True
