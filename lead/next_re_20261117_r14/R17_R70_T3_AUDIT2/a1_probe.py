import io, os, re, collections
ROOT = r"D:\Project\ra2-campaign-forge"
R14  = os.path.join(ROOT, "lead", "next_re_20261117_r14")
def load(p):
    raw = io.open(p, encoding="utf-8", newline="").read()
    lines = raw.split("\n")
    h = lines[0].split("\t")
    return [dict(zip(h, l.split("\t"))) for l in lines[1:] if l.strip()]
def key(s):
    return re.sub(r"[\s，。；、「」『』（）()·`*_\"'：:；;,.!?！？\-—]+", "", s)
HEDGE_WORDS = ["推断", "未证", "未经", "存疑", "不能排除", "疑似", "待裁", "待核", "不构成", "不得当", "中等偏强", "中等", "偏弱"]
DOWNGRADE_PATTERNS = [
    r"[「『]([^」』]{2,40})[」』]\s*(?:是|属)[^。；]{0,20}(?:推断措辞|单源归因|行动裁决|推断)",
    r"[「『]([^」』]{2,40})[」』][^。；]{0,40}(?:不随数字一并作已证|不入本条证据|未经字节证实|未经[^。；]{0,4}证实)",
    r"不得写成[「『]?([^，。；」』]{2,30})",
    r"[「『]([^」』]{2,40})[」』][^。；]{0,20}不得当[^。；]{0,10}用",
]
DUTY_CONTEXT = ("本条不支撑","不得据此","不得引申","不得反推","不得再用","只能引其","须同引","必须同引","引用时二者同看","不得只引用","不得单独引用","削弱")
def downgraded_tokens(lim):
    out=[]
    for pat in DOWNGRADE_PATTERNS:
        for m in re.finditer(pat, lim):
            t=m.group(1).strip()
            if len(t)>=2: out.append(t)
    return sorted(set(out))
def is_duty_sentence(lim, token):
    for seg in re.split(r"[；;。]", lim):
        if token in seg:
            return any(d in seg for d in DUTY_CONTEXT)
    return False
def paired_quote_spans(s):
    spans=[];stack=[]
    opens={"「":"」","『":"』","“":"”","\"":"\""}
    for i,ch in enumerate(s):
        if ch in opens: stack.append((ch,i))
        elif stack and ch==opens[stack[-1][0]]:
            _,j=stack.pop();spans.append((j,i))
    return spans
def inside_spans(i,spans): return any(a<=i<=b for a,b in spans)
def stmt_uses_hedged(stmt,token,window=45):
    k=key(token)
    if not k: return (False,None,"")
    ks=key(stmt); idx=ks.find(k)
    if idx<0: return (False,None,"")
    seg=ks[max(0,idx-window):idx+len(k)+window]
    hedged=any(w in seg for w in HEDGE_WORDS)
    raw_i=stmt.find(token)
    if raw_i<0 and len(token)>=4: raw_i=stmt.find(token[:4])
    ctx=stmt[max(0,raw_i-40):raw_i+60] if raw_i>=0 else "(原文未能定位)"
    return (True,hedged,ctx)
def check_C1(row):
    hits=[]
    for t in downgraded_tokens(row["limitations"]):
        if is_duty_sentence(row["limitations"],t): continue
        used,hedged,ctx=stmt_uses_hedged(row["statement"],t)
        if used and not hedged: hits.append((t,ctx))
    return hits
def check_C2(row):
    if row["grade"]!="[已证]": return []
    st=row["statement"];spans=paired_quote_spans(st);bad=[]
    for w in ("推断","推测","疑似"):
        for m in re.finditer(w,st):
            i=m.start()
            if inside_spans(i,spans): continue
            ctx=st[max(0,i-30):i+30]
            if re.search(r"(静态|中等|偏强|偏弱|待裁|推断强度)",ctx): continue
            if re.search(r"(不再是|不是|不再|不得|不能|非|不作|不构成|视为|降级为|改为|升级为)\s*"+w,ctx): continue
            if re.search(w+r"\s*(措辞)?\s*(?:已|经)[^。；]{0,10}证实",ctx): continue
            bad.append((w,ctx));break
    return bad

V510=os.path.join(R14,"R17_R65_FACTINDEX_V510","FACT_INDEX.tsv")
V513=os.path.join(R14,"R17_R69_FACTINDEX_V513","FACT_INDEX.tsv")
v510={r["fact_id"]:r for r in load(V510)}
v513={r["fact_id"]:r for r in load(V513)}
rows=load(V513)
print("=== A. 复算 checkC2.py 自己的控制组（原样复制全部谓词，不跑 C3 文件 IO）===")
p1,p2=check_C1(v510["F24"]),check_C1(v510["F29"])
n1,n2=check_C1(v513["F24"]),check_C1(v513["F29"])
print("  C1 正控 v5.10 F24 =",len(p1),[x[0] for x in p1])
print("  C1 正控 v5.10 F29 =",len(p2),[x[0] for x in p2])
print("  C1 反控 v5.13 F24 =",len(n1),"| v5.13 F29 =",len(n2))
fake={"grade":"[已证]","statement":"该函数是构造器（推断）。","limitations":"—","fact_id":"FAKE","evidence_paths":""}
c2pos=check_C2(fake)
fake_ok1=dict(fake,statement="该函数性质记为「推断」。")
fake_ok2=dict(fake,statement="语义疑似占格 helper（静态推断/中等偏强）。")
print("  C2 正控(裸断言) =",len(c2pos),"| 反控(引号内) =",len(check_C2(fake_ok1)),"| 反控(强度标注) =",len(check_C2(fake_ok2)))
print()
print("=== B. downgraded_tokens 在 54 行上的总产出（C1 的分子分母）===")
tot=0;rows_with=0;duty_skipped=[]
for r in rows:
    ts=downgraded_tokens(r["limitations"])
    if ts: rows_with+=1
    tot+=len(ts)
    for t in ts:
        if is_duty_sentence(r["limitations"],t): duty_skipped.append((r["fact_id"],t))
print("  有降级 token 的行数 =",rows_with,"/ 54 ; token 总数 =",tot)
print("  被 is_duty_sentence 静默跳过的 token 数 =",len(duty_skipped))
for fid,t in duty_skipped: print("    skip:",fid,repr(t))
print()
print("=== C. 逐行 dump limitations / statement 里含 HEDGE_WORDS 的行（供人工核）===")
for r in rows:
    lim=r["limitations"]; st=r["statement"]
    hedge_in_lim=[w for w in HEDGE_WORDS if w in lim]
    quotes=re.findall(r"[「『]([^」』]{1,40})[」』]",lim)
    if quotes or hedge_in_lim:
        print("  %s | grade=%s" % (r["fact_id"], r["grade"]))
        print("     lim=",lim)
        print("     quoted=",quotes," hedge=",hedge_in_lim)
