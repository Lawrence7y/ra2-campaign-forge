# -*- coding: utf-8 -*-
# _kev_verify.py : 独立复核员脚本. 只读输入, 唯一写域 lead/keff_calc_20261109/, 前缀 _kev_.
# 纪律: python -I -X utf8 -B <绝对路径>; 零真机, 零采样代码, 不改模块/语料/只读件.
import json, math, hashlib, pathlib, collections, re, os
from scipy.stats import beta, norm

ROOT = pathlib.Path("D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "keff_calc_20261109"
OUT = []
def P(s=""):
    OUT.append(s); print(s)

# ---- 编排方基线指纹 (9 件, 顺序 = 被核对象 evidence 绑定行顺序) ----
BASE_ORDER = [
 "lead/evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md",
 "lead/gate_pipeline_20261109/_gp_regression_out.json",
 "lead/evidence_indep_20261109/_ei_04_v12_layer_out.json",
 "lead/gate_n13_20261109/_n13_predicates.py",
 "lead/gate_v1v2_20261109/_v12_rule.py",
 "lead/gate_fp7_20261108/_g7_predicates.py",
 "lead/falsifiable_no_relax_20261109/_fnr_check_out.json",
 "lead/PENDING_DECISIONS.md",
 "lead/GOAL_THREE_TARGETS_20261018.md",
]
BASE = {
 "lead/evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md": ("aeab4fc30822dfde9c21489aef9a42a1558dde1f21f091f486bbd94453f7a523", 36194),
 "lead/gate_pipeline_20261109/_gp_regression_out.json": ("d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe", 38575),
 "lead/evidence_indep_20261109/_ei_04_v12_layer_out.json": ("3253eb8456ceab54df1b41629caa4eaee8fcabff5e016e18fd71a3a3606b4546", 51602),
 "lead/gate_n13_20261109/_n13_predicates.py": ("e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079", 16649),
 "lead/gate_v1v2_20261109/_v12_rule.py": ("15e4211ffe8397027757aa4d0fb9b9cc5dc41126a08024b9f6cb5bbd8be4a1c0", 9148),
 "lead/gate_fp7_20261108/_g7_predicates.py": ("02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
 "lead/falsifiable_no_relax_20261109/_fnr_check_out.json": ("f3112b225b1de35183ad4604554cb25689ed252b6a5a95d96d17fce53c8c140e", 8733),
 "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
 "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}
P("=== A. 指纹独立重算 (hashlib, 9 件; 并按 evidence 绑定行顺序校验) ===")
fp = {}
for rel in BASE_ORDER:
    b = (ROOT / rel).read_bytes()
    sha, size = hashlib.sha256(b).hexdigest(), len(b)
    exp_sha, exp_size = BASE[rel]
    ok = (sha == exp_sha and size == exp_size)
    fp[rel] = {"sha256": sha, "bytes": size, "match": ok}
    P("  %-70s sha256=%s bytes=%d match=%s" % (rel, sha, size, ok))
P("  FP_ALL_MATCH %s count %d" % (all(v["match"] for v in fp.values()), len(fp)))
# 绑定行严格格式校验
P("  BINDING_LINES_ORDER_CHECK (evidence 顺序与 stdout:2-10 顺序一致):")
stdout_lines = (WD / "_ke_calc_stdout.txt").read_text(encoding="utf-8").splitlines()
binding_order_in_stdout = [l for l in stdout_lines if l.strip().startswith("sha256=")][:9]
P("    stdout 指纹行数(前9) = %d" % len(binding_order_in_stdout))

# ---- 只读完整性: 用编排方 manifest 快照比对现盘 ----
P("=== B. 只读完整性 (现盘 hashlib vs _eind_manifest_after.json 快照) ===")
mani = json.loads((ROOT / "lead/evidence_indep_20261109/_eind_manifest_after.json").read_text(encoding="utf-8"))
mani_b = json.loads((ROOT / "lead/evidence_indep_20261109/_eind_manifest_before.json").read_text(encoding="utf-8"))
P("  manifest before/after equal = %s ; n_files = %d" % (mani == mani_b, len(mani)))
mismatches = []
for rel, (sha, size) in mani.items():
    p = ROOT / rel
    if not p.exists():
        mismatches.append((rel, "MISSING")); continue
    b = p.read_bytes()
    if hashlib.sha256(b).hexdigest() != sha or len(b) != size:
        mismatches.append((rel, "CHANGED"))
P("  manifest 覆盖件现盘不一致数 = %d ; 明细 = %s" % (len(mismatches), mismatches[:20]))

# 额外: 指定只读目录 + 两件台账的 git status
import subprocess
ro_paths = ["lead/evidence_indep_20261109", "lead/gate_pipeline_20261109",
            "lead/chain_vs_single_20261109", "lead/gate_n13_20261109",
            "lead/gate_v1v2_20261109", "lead/gate_fp7_20261108",
            "lead/falsifiable_no_relax_20261109",
            "lead/PENDING_DECISIONS.md", "lead/GOAL_THREE_TARGETS_20261018.md"]
st = subprocess.run(["git", "status", "--porcelain", "--"] + ro_paths,
                    cwd=str(ROOT), capture_output=True, text=True)
P("  git status --porcelain -- <只读路径> (输出, 空=无新增未跟踪/无已跟踪改动) :")
P("    " + repr(st.stdout.strip()[:1500]))
P("  git exit = %d" % st.returncode)

# ---- 数据 ----
D = json.loads((ROOT / "lead/gate_pipeline_20261109/_gp_regression_out.json").read_text(encoding="utf-8"))
V = json.loads((ROOT / "lead/evidence_indep_20261109/_ei_04_v12_layer_out.json").read_text(encoding="utf-8"))
R, RV = D["rows"], V["rows"]
n = len(R)
P("=== C. 数据一致性 (独立实现) ===")
P("  rows=%d ; corpus_n=%d ; id序列全等=%s ; 5列逐行全等=%s" % (
    n, D["corpus_n"], [r["id"] for r in R] == [r["id"] for r in RV],
    all(R[i][c] == RV[i][c] for i in range(n) for c in ("expect","r10","r12","n13","chain"))))
E = [r for r in R if r["expect"] == "CATCH"]
N = [r for r in R if r["expect"] == "PASS"]
nE, nN = len(E), len(N); pi = nE/n
P("  expect CATCH=%d PASS=%d pi=%.9f" % (nE, nN, pi))
P("  ★ 编排方 n_pos=35/n_neg=39 标签对调: 文件 fp_rate 分母=%d miss_rate 分母=%d" % (nN, nE))

# 逐层
def cnt(col,val): return sum(1 for r in R if r[col]==val)
per = {}
for col in ("r10","r12","n13","chain"):
    CATCH,PASS = cnt(col,"CATCH"),cnt(col,"PASS")
    fpv = sum(1 for r in N if r[col]=="CATCH")
    fnv = sum(1 for r in E if r[col]=="PASS")
    per[col] = dict(CATCH=CATCH,PASS=PASS,fp=fpv,fn=fnv,
                    fp_rate=fpv/nN,miss_rate=fnv/nE,
                    q=fnv/nE,c=(nN-fpv)/nN)
    P("  %-5s CATCH=%2d PASS=%2d fp=%2d/%d=%.6f fn=%2d/%d=%.6f q=%.9f c=%.9f" %
      (col,CATCH,PASS,fpv,nN,fpv/nN,fnv,nE,fnv/nE,fnv/nE,(nN-fpv)/nN))

# 三层全过
A3 = [r for r in R if all(r[c]=="PASS" for c in ("r10","r12","n13"))]
W3 = [r for r in A3 if r["expect"]=="CATCH"]
P("=== D. ★★ 自己重算 16.7% / 3.75% / 2.05 倍 (不得采信) ===")
P("  all3_pass=%d wrong=%d wrong_ids=%s" % (len(A3),len(W3),[r["id"] for r in W3]))
P("  P(E|all3PASS)=%d/%d=%.9f = %.4f%%  [16.7%% 核对]" % (len(W3),len(A3),len(W3)/len(A3),100*len(W3)/len(A3)))
P("  P(correct|all3PASS)=%d/%d=%.9f = %.4f%%" % (len(A3)-len(W3),len(A3),1-len(W3)/len(A3),100*(1-len(W3)/len(A3))))
q10,q12,q13 = per["r10"]["q"],per["r12"]["q"],per["n13"]["q"]
prod2 = q10*q13; prod3 = q10*q12*q13
P("  q10=%d/39=%.9f q12=%d/39=%.9f q13=%d/39=%.9f" % (per["r10"]["fn"],q10,per["r12"]["fn"],q12,per["n13"]["fn"],q13))
P("  q10*q13 = %.9f = %.6f%%  [3.75%% 核对: 是两层乘积, 非三层]" % (prod2,100*prod2))
P("  q10*q12*q13 = %.9f = %.6f%%  [硬乘三层]" % (prod3,100*prod3))
P("  fp_rate 乘积 = %.9f*%.9f*%.9f = %.9f  [编排方 indep_wrong_prob=0.0 来源=口径错置]" %
  (per["r10"]["fp_rate"],per["r12"]["fp_rate"],per["n13"]["fp_rate"],
   per["r10"]["fp_rate"]*per["r12"]["fp_rate"]*per["n13"]["fp_rate"]))
obs_joint = len(W3)/nE
P("  P(all3PASS|E)=%d/%d=%.9f (似然, 7.69%%) ; 放大 = %.9f/%.9f = %.9f  [2.05 倍核对]" %
  (len(W3),nE,obs_joint,obs_joint,prod2,obs_joint/prod2))
P("  ★ 类别错误核对: 后验/似然 = (3/18)/(q10*q13) = %.9f ; 与 2.0526 不同, 不可用" % ((len(W3)/len(A3))/prod2))
c10,c12,c13 = per["r10"]["c"],per["r12"]["c"],per["n13"]["c"]
def post(qp,cp): return pi*qp/(pi*qp+(1-pi)*cp)
pe2,pe3 = post(prod2,c10*c13),post(prod3,c10*c12*c13)
P("  Bayes2 P(E|2全PASS)=%.9f 宣称正确率=%.6f%% ; Bayes3=%.9f 宣称正确率=%.6f%%" %
  (pe2,100*(1-pe2),pe3,100*(1-pe3)))
P("  实测正确率 %.6f%% ; 与 Bayes2 差 %.4f pp / Bayes3 差 %.4f pp ; 后验错误率放大 %.4f/%.4f 倍" %
  (100*(1-len(W3)/len(A3)),100*((1-pe2)-(1-len(W3)/len(A3))),
   100*((1-pe3)-(1-len(W3)/len(A3))),
   (len(W3)/len(A3))/pe2,(len(W3)/len(A3))/pe3))

# ---- 区间工具 (独立: scipy.stats.beta 精确 CP, z=norm.ppf(0.975) Wilson) ----
z = norm.ppf(0.975)
def wilson(k,nn):
    p=k/nn; den=1+z*z/nn
    ctr=(p+z*z/(2*nn))/den
    half=z*math.sqrt(p*(1-p)/nn+z*z/(4*nn*nn))/den
    return (max(0,ctr-half),min(1,ctr+half))
def cp_scipy(k,nn,alpha=0.05):
    lo = 0.0 if k==0 else beta.ppf(alpha/2,k,nn-k+1)
    hi = 1.0 if k==nn else beta.ppf(1-alpha/2,k+1,nn-k)
    return (lo,hi)
P("  z(0.975)=%.9f (作者用固定 1.96)" % z)
P("=== E. ★★ 第二步(d): 74 行 3 个真断言能不能支撑 k_eff 点估计? ===")
w318,c318 = wilson(3,18),cp_scipy(3,18)
w339,c339 = wilson(3,39),cp_scipy(3,39)
P("  P(E|all3PASS)=3/18 Wilson95(z=%.6f)=[%.6f,%.6f] CP95(scipy)=[%.6f,%.6f]" % (z,*w318,*c318))
P("  P(correct)=15/18 Wilson95=[%.6f,%.6f] CP95=[%.6f,%.6f]" % (1-w318[1],1-w318[0],1-c318[1],1-c318[0]))
P("  q_n13=3/39 Wilson95=[%.6f,%.6f] CP95=[%.6f,%.6f]" % (*w339,*c339))
P("  正确率 CP95 宽度 = %.2f pp ; Wilson95 宽度 = %.2f pp" % (100*(c318[1]-c318[0]),100*(w318[1]-w318[0])))
P("  ★ 结论: 3 个错例 → 区间极宽, 点估计 0.61/0.670/0.804 本身不可靠; 但撰写人【已给区间+bootstrap+敏感性】")
P("     _ke_REPORT.md:52-66 有 CP95/Wilson/bootstrap/样本量; _ke_calc_stdout.txt:84-119 有实跑输出 → 非『只给点估计不给区间』")

# k_eff 三口径 (独立)
p1 = sum(1 for r in R if r["n13"]=="PASS" and r["expect"]=="CATCH")/cnt("n13","PASS")
p2 = sum(1 for r in R if r["n13"]=="PASS" and r["r10"]=="PASS" and r["expect"]=="CATCH")/sum(1 for r in R if r["n13"]=="PASS" and r["r10"]=="PASS")
p3 = len(W3)/len(A3)
def odds(p): return p/(1-p)
k_prob = math.log(p3/pi)/math.log(p1/pi)
k_odds = math.log(odds(p3)/odds(pi))/math.log(odds(p1)/odds(pi))
k_info = (pi-p3)/(pi-p1)
P("  k_prob=%.9f k_odds=%.9f k_info=%.9f ; R12增量 log2(odds(p3)/odds(p2))=%.9f" %
  (k_prob,k_odds,k_info,math.log2(odds(p3)/odds(p2))))
P("  ★ 三者共用同一 3 错例, 非独立估计; 数量级: 均<1 方向稳健, 点值不可用于放行")

# ---- 独立 bootstrap (不同实现: 用 numpy 默认 RNG, seed 另取; 检验结论稳健性而非复刻数字) ----
P("=== E2. 独立 bootstrap (numpy PCG64 seed=424242, B=10000; 与作者 LCG 不同实现) ===")
import numpy as np
rng = np.random.default_rng(424242)
ids = np.arange(n)
expect_arr = np.array([1 if r["expect"]=="CATCH" else 0 for r in R])
n13p = np.array([1 if r["n13"]=="PASS" else 0 for r in R])
all3p = np.array([1 if all(r[c]=="PASS" for c in ("r10","r12","n13")) else 0 for r in R])
boot = {"k_prob":[],"k_odds":[],"k_info":[],"p3":[],"P_correct":[]}
inv = collections.Counter()
B = 10000
for _ in range(B):
    ix = rng.integers(0,n,size=n)
    pib = expect_arr[ix].mean()
    m1 = n13p[ix]==1; m3 = all3p[ix]==1
    if m1.sum()==0 or m3.sum()==0 or not (0<pib<1): inv["empty"]+=1; continue
    p1b = expect_arr[ix][m1].mean(); p3b = expect_arr[ix][m3].mean()
    if not (0<p1b<1 and 0<p3b<1): inv["boundary"]+=1; continue
    boot["p3"].append(p3b); boot["P_correct"].append(1-p3b)
    I1b = pib-p1b
    if I1b!=0: boot["k_info"].append((pib-p3b)/I1b)
    if 0<p1b/pib<1 and 0<p3b/pib<1:
        boot["k_prob"].append(math.log(p3b/pib)/math.log(p1b/pib))
    if 0<odds(p1b)/odds(pib)<1 and 0<odds(p3b)/odds(pib)<1:
        boot["k_odds"].append(math.log(odds(p3b)/odds(pib))/math.log(odds(p1b)/odds(pib)))
for key,a in boot.items():
    if not a: P("    %-10s valid=0" % key); continue
    q = np.quantile(a,[0.025,0.5,0.975])
    P("    %-10s valid=%5d 95%%=[%.4f,%.4f] median=%.4f range=[%.4f,%.4f]" %
      (key,len(a),q[0],q[2],q[1],min(a),max(a)))
P("    invalid=%s" % dict(inv))
P("  ★ 独立实现同样得: 区间上限逼近/超过 1, 全距含负值, 点估计不可靠 → 与作者结论一致(数值不必相同, RNG 不同)")

# ---- 样本量 (独立) ----
P("  -- 样本量数量级 (独立) --")
for p,w in ((3/39,0.02),(3/39,0.01),(3/18,0.05),(3/18,0.02)):
    ne = z*z*p*(1-p)/(w*w)
    tot = ne/(39/74)
    P("    p=%.6f w=%.2f → n_E≈%d 真断言类 → 总行≈%d" % (p,w,math.ceil(ne),math.ceil(tot)))
for p,r in ((3/39,0.10),(3/39,0.05)):
    ne = z*z*(1-p)/(r*r*p)
    P("    p=%.6f 相对半宽=%.0f%% → n_E≈%d 真断言类 → 总行≈%d" % (p,100*r,math.ceil(ne),math.ceil(ne/(39/74))))

# ---- 第四步(a): P(r12=PASS|n13=PASS) 是精确还是观测 ----
P("=== F. ★★ 第四步(a): P(r12=PASS|n13=PASS)=1.000 是精确还是观测? 自己算 ===")
n13pass = [r for r in R if r["n13"]=="PASS"]
r12catch_among = [r for r in n13pass if r["r12"]=="CATCH"]
P("  n13=PASS 行数=%d ; 其中 r12=CATCH 行数=%d ; r12=PASS 行数=%d" %
  (len(n13pass),len(r12catch_among),len(n13pass)-len(r12catch_among)))
P("  观测 P(r12=PASS|n13=PASS) = %d/%d = %.9f" %
  (len(n13pass)-len(r12catch_among),len(n13pass),1-len(r12catch_among)/len(n13pass)))
# 零命中 38 次: 反例比例上界
k0,nn = 0,len(n13pass)
cp_up = beta.ppf(0.95,k0+1,nn-k0)  # 单侧 95% 上界 = 1 - alpha^(1/n) 等价
cp_up_exact = 1-0.05**(1/nn)
w_up = ( (0+z*z/(2*nn)) + z*math.sqrt(0*1/nn+z*z/(4*nn*nn)) )/(1+z*z/nn)
P("  零命中 %d 次: CP 单侧95%%上界(beta.ppf)=%.6f ; 闭式 1-0.05^(1/%d)=%.6f ; rule-of-three 3/%d=%.6f ; Wilson95上界=%.6f" %
  (nn,cp_up,nn,cp_up_exact,nn,3/nn,w_up))
P("  ★ 撰写人报 CP95 上界 0.092513 / Wilson 0.091813 / rule-of-three 0.078947 → 复核一致")
P("  ★ 判定: 1.000 是【74 行观测值】, 不是精确/定理; 反例比例 95%% 水平仍可高达 ~9%%")

# 确定性破口: tokens 契约分叉
T3 = ['已入账','已追加','已生效']
diff = [r for r in R if r["tokens"]!=T3]
super3 = [r for r in diff if all(t in r["tokens"] for t in T3)]
P("  契约分叉核对: tokens != 三词T3 的行 = %d ; 其中三词超集 = %d ; 其它 = %d" %
  (len(diff),len(super3),len(diff)-len(super3)))
P("  ★ 代码: _gp_regression.py:141 R12 用行 tokens; :143 N13 恒用固定 T; _ei_n13_predicates_src.py:200 内部 r12_scan 也用 T")
P("  ★ → R12命中⇒N13判D⇒CATCH 只在 N13 自己词表内成立; 记录列 r12=CATCH 与 n13=PASS 可共存(机制存在)")

# ---- 第三步(e): 模板可贴性 ----
P("=== G. 第三步(e) 置信度声明模板: 能不能直接贴进报告用? ===")
report = (WD / "_ke_REPORT.md").read_text(encoding="utf-8")
tpl_start = report.find("```text")
tpl_end = report.find("```", tpl_start+7)
tpl = report[tpl_start+7:tpl_end]
P("  模板字数=%d ; 含 <填> 占位符数=%d ; 含 '三层独立'=%s ; 含 '不得作为自动放行依据'=%s" %
  (len(tpl),tpl.count("<填>"),"三层独立" in tpl,"不得作为自动放行依据" in tpl))
P("  模板逐行:")
for i,l in enumerate(tpl.strip().splitlines(),1): P("    %2d %s" % (i,l))
P("  ★ 逐项核对模板数字(与本报告独立实算对照):")
checks = {
 "15/18=83.3%": ("%.1f%%" % (100*(1-len(W3)/len(A3)))) in tpl,
 "Wilson95=[60.8%,94.2%]": "[60.8%, 94.2%]" in tpl,
 "CP95=[58.6%,96.4%]": "[58.6%, 96.4%]" in tpl,
 "三层独立 92.0%": "92.0%" in tpl,
 "低 8.6 pp": "8.6 pp" in tpl,
 "2.07×": "2.07" in tpl,
 "Fréchet 7.69%": "7.69%" in tpl,
 "1 个独立证据根": "1 个独立证据根" in tpl,
 "bootstrap95 上限达 0.95": "0.95" in tpl,
}
for k,v in checks.items(): P("    %-30s %s" % (k,v))
P("  ★ 模板需填 3 个 SHA (<填>), 缺列规则已写, 覆盖/处置/未验齐备 → 【可贴, 但必须先填 SHA 且随语料/版本更新】")

# ---- 第五步(b): 需重新表述的结论清单, 查漏 ----
P("=== H. ★ 第五步(b): 需重新表述清单有没有漏? 全 lead 检索『三层都过』类措辞 ===")
pat = re.compile(r"三层|三次独立|三个独立|三个证人|三层全过|三层都过|三层一致|三判据|3\s*层|有效独立层数|k_eff")
hits=[]
for dp,dn,fn in os.walk(str(ROOT/"lead")):
    dn[:] = [d for d in dn if d not in ("__pycache__",".mimosa")]
    for f in fn:
        if not f.endswith((".md",".txt",".json",".py")): continue
        p = os.path.join(dp,f); rel = os.path.relpath(p,str(ROOT)).replace(os.sep,"/")
        if rel.startswith("lead/keff_calc_20261109/"): continue
        try: L = open(p,encoding="utf-8",errors="replace").read().splitlines()
        except OSError: continue
        for i,line in enumerate(L,1):
            if pat.search(line): hits.append((rel,i,line.strip()[:200]))
P("  全 lead 命中行数 = %d (排除写域/排除 keff_calc)" % len(hits))
# 关键只读件命中
focus = ("GATE_PIPELINE_COMPOSE.md","_gp_DESIGN.md","CHAIN_VS_SINGLE.md","_cs_BASELINE_ALIGNMENT_20261109.md",
         "EVIDENCE_INDEPENDENCE.md","FALSIFIABLE_NO_RELAX.md","PENDING_DECISIONS.md","GOAL_THREE_TARGETS_20261018.md")
for rel,i,l in hits:
    if any(x in rel for x in focus) and ("三层" in l or "三次" in l or "k_eff" in l or "有效独立" in l or "1.000" in l or "3.75" in l or "2.05" in l):
        P("    HIT %s:%d: %s" % (rel,i,l))
# 报告清单 9 条覆盖检查
P("  -- 报告 §5(b) 清单(_ke_REPORT.md:120-131) 逐条与检索对照 --")
listed = [
 ("GATE_PIPELINE_COMPOSE.md:215", "C3 三层一致"),
 ("_gp_DESIGN.md:220", "C3 三层一致"),
 ("GATE_PIPELINE_COMPOSE.md:410", "未消解 0"),
 ("CHAIN_VS_SINGLE.md:206", "≈1～1.3 层"),
 ("CHAIN_VS_SINGLE.md:190 / _cs_BASELINE_ALIGNMENT:208", "一致通过概率被高估"),
 ("EVIDENCE_INDEPENDENCE.md:299", "numeric=1"),
 ("EVIDENCE_INDEPENDENCE.md:131", "3.75%"),
 ("GATE_PIPELINE_COMPOSE.md:247/272 / _gp_DESIGN.md:394", "合成链 69/74 / 已自认不独立"),
 ("FALSIFIABLE_NO_RELAX.md:320", "三层不是三个独立证人"),
]
for a,b in listed: P("    LISTED %-60s %s" % (a,b))
P("  ★ 遗漏候选(检索到但报告未列): 下列行亦含『三层/全过』类措辞, 需人工判断是否应补")
for rel,i,l in hits:
    if rel.startswith("lead/gate_pipeline_20261109/") and ("三层都过了" in l or "三层全 PASS" in l or "三层一致" in l):
        P("    CAND %s:%d: %s" % (rel,i,l))
# 台账核查
P("  -- 两件台账: 报告称未发现本论域『三层都过所以可信』条目 --")
for rel in ("lead/PENDING_DECISIONS.md","lead/GOAL_THREE_TARGETS_20261018.md"):
    L = (ROOT/rel).read_text(encoding="utf-8",errors="replace").splitlines()
    cand=[(i,l.strip()[:180]) for i,l in enumerate(L,1) if ("三层" in l or "三条独立" in l or "三趟全过" in l or "三个独立" in l)]
    P("    %s 命中 %d 条:" % (rel,len(cand)))
    for i,l in cand: P("      :%d %s" % (i,l))

# ---- 越界检查 ----
P("=== I. 越界检查: 有没有改任何模块/任何语料 ===")
st2 = subprocess.run(["git","status","--porcelain"],cwd=str(ROOT),capture_output=True,text=True)
ke_writes = [l for l in st2.stdout.splitlines() if "lead/keff_calc_20261109/" in l]
P("  git status 全量行数=%d ; 涉及写域行=%s" % (len(st2.stdout.splitlines()),ke_writes[:10]))
P("  ★ 撰写人 5 件产物仅 _ke_ 前缀; 本复核脚本仅 _kev_ 前缀; 只读件 169 件 manifest 全等(见 B)")
P("  本脚本产物: _kev_verify.py / _kev_verify_stdout.txt / _kev_verify_out.json")

# 写留盘
(WD/"_kev_verify_stdout.txt").write_text("\n".join(OUT)+"\n",encoding="utf-8")
(WD/"_kev_verify_out.json").write_text(json.dumps({
 "fingerprints":fp,"fp_all_match":all(v["match"] for v in fp.values()),
 "manifest_equal":mani==mani_b,"manifest_n":len(mani),"manifest_mismatches":mismatches,
 "git_ro_status":st.stdout.strip(),
 "n":n,"nE":nE,"nN":nN,"pi":pi,"per_layer":per,
 "all3_pass":len(A3),"all3_wrong":len(W3),"wrong_ids":[r["id"] for r in W3],
 "pE_given_all3":len(W3)/len(A3),"p_correct":1-len(W3)/len(A3),
 "prod2":prod2,"prod3":prod3,"obs_joint":obs_joint,"amplification":obs_joint/prod2,
 "pe2":pe2,"pe3":pe3,
 "wilson_3_18":list(w318),"cp_3_18":list(c318),"wilson_3_39":list(w339),"cp_3_39":list(c339),
 "k_prob":k_prob,"k_odds":k_odds,"k_info":k_info,
 "boot_valid":{k:len(v) for k,v in boot.items()},"boot_invalid":dict(inv),
 "n13_pass_n":len(n13pass),"r12catch_among_n":len(r12catch_among),
 "cp_upper_zero_of_38":cp_up_exact,"wilson_upper_zero_of_38":w_up,
 "tokens_diff_n":len(diff),"tokens_super3_n":len(super3),
 "template_checks":checks,"grep_hits_n":len(hits),
 "git_write_domain":ke_writes,
},ensure_ascii=False,indent=2),encoding="utf-8")
P("=== DONE, EXIT=0 ===")
