"""最后一轮：标题数、影响面具体下游、重跑片段口径冲突、⑦ 指纹末态。"""
import os, re, hashlib

ROOT="D:/Project/ra2-campaign-forge"
def RD(p): return open(os.path.join(ROOT,p),"rb").read().decode("utf-8","replace")
def L(p): return RD(p).split("\n")

print("=== ④ 报告称 RULING_D30.md「7 个二级标题」——核门禁源码与实际标题 ===")
for k in ["d27","d28","d29","d30"]:
    src=L(f"lead/{k}_ruling_20261106/check_{k}.py")
    print(f"-- check_{k}.py REQUIRED_HEADINGS --")
    for i,s in enumerate(src):
        if "REQUIRED_HEADINGS" in s or "HEADINGS" in s and "=" in s:
            print(f"   L{i+1}: {s.strip()[:220]}")
    rul=L(f"lead/{k}_ruling_20261106/RULING_{k.upper()}.md")
    h=[(i+1,s.strip()) for i,s in enumerate(rul) if s.startswith("## ")]
    print(f"   RULING_{k.upper()}.md 实际 '## ' 标题数 = {len(h)}")
    for n,s in h[:12]: print(f"      L{n}: {s[:90]}")

print()
print("=== ④ 影响面具体下游：REFSYNC_SCOPE_FIX.md §5.4 的件数结论 ===")
F=L("lead/refsync_scope_20261109/REFSYNC_SCOPE_FIX.md")
for n in range(266,288):
    print(f"   FIX:{n}: {F[n-1].strip()[:300]}")

print()
print("=== ④ PENDING:109 勘误行（依赖 RULING_D28.md 正文，与 gate 无关） ===")
P=L("lead/PENDING_DECISIONS.md")
for n in [109,110,111]:
    print(f"   PENDING:{n}: {P[n-1].strip()[:300]}")

print()
print("=== ⑤ 三处命令口径逐字对照（登记 / 审计可粘贴片段 / 本会话单跑） ===")
print("   FIX:251 登记:", F[250].split("`")[1][:300] if "`" in F[250] else F[250][:300])
M=L("lead/masking_effect_20261109/MASKING_EFFECT_AUDIT.md")
print("   MEA:231 片段:", M[230].strip())
print("   MEA:385-386 口径差说明:")
for n in [385,386]: print(f"      MEA:{n}: {M[n-1].strip()[:330]}")
A=L("lead/stale_pass_20261109/_sp_agg_f0b7c1.txt")
B=L("lead/stale_pass_20261109/_sp_agg_87196b.txt")
C=L("lead/stale_pass_20261109/_sp_rs_broken_out.txt")
print("   agg1 needles:", A[7].strip(), "|", A[1].strip(), "|", A[9].strip())
print("   agg2 needles:", B[7].strip(), "|", B[1].strip(), "|", B[9].strip())
print("   broken needles:", C[7].strip(), "|", C[9].strip())

print()
print("=== ⑦ 末态：九件指纹 + 被核报告 + 两账 git 状态 ===")
BASE={
 "lead/PENDING_DECISIONS.md":("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7",52419),
 "lead/GOAL_THREE_TARGETS_20261018.md":("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede",759518),
 "lead/check_masking_20261109/CHECK_MASKING_INJECT.md":("99131e8aa03717c555a56b7cee75cf747b4127287e2cc1ec9b6bef5656da3c6c",56575),
 "lead/masking_effect_20261109/MASKING_EFFECT_AUDIT.md":("2f55283ef3380c6cb5915b2e8654a5506061ccb667a986d397b45a10a2f9119f",45536),
 "lead/d27_ruling_20261106/check_d27.py":("3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c",3764),
 "lead/d29_ruling_20261106/check_d29.py":("2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14",3906),
 "lead/d30_ruling_20261106/check_d30.py":("6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd",3926),
 "lead/refsync_scope_20261109/_rs_carrier_scan.py":("9ccca808d52f44aaee895e30f9a84f6f3b6ae5ee292ea71281e2b46e627a1c57",16053),
 "lead/refsync_scope_20261109/REFSYNC_SCOPE_FIX.md":("83b215ccbbf2c3e221c247e7bd9c7c221fddcf9472977d2df8902bf1b94ec65e",49958),
}
ok=True
for rel,(h0,n0) in BASE.items():
    b=open(os.path.join(ROOT,rel),"rb").read()
    h=hashlib.sha256(b).hexdigest(); n=len(b)
    good=(h==h0 and n==n0); ok &= good
    print(f"   {'OK' if good else 'MISMATCH'} {rel} {h[:16]}… {n}")
print("   NINE_ALL_MATCH_END =",ok)
b=open(os.path.join(ROOT,"lead/stale_pass_20261109/_sp_STALE_PASS_CENSUS.md"),"rb").read()
print("   REPORT sha256 =",hashlib.sha256(b).hexdigest(),"bytes =",len(b))
print("   被核对象 SHA256 =",hashlib.sha256(b).hexdigest(),"，字节数 =",len(b))
