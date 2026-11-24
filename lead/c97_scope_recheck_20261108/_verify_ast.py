# _verify_ast.py — 复核员独立 AST 实证：_dC_recompute.py 的 all_pass 门与 :420 文案
# 只读；自写遍历，不复用被核脚本代码。
import ast

BASE = "D:/Project/ra2-campaign-forge"
with open(BASE + "/lead/dtrigger_round2_20261107/_dC_recompute.py", "rb") as f:
    src = f.read().decode("utf-8", errors="replace")
tree = ast.parse(src)

gate = None
for node in ast.walk(tree):
    if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "all_pass" for t in node.targets):
        gate = node
print("all_pass 赋值行域 = %d-%d" % (gate.lineno, gate.end_lineno))
names = sorted({n.id for n in ast.walk(gate) if isinstance(n, ast.Name)})
print("门内 Compare =", sum(1 for n in ast.walk(gate) if isinstance(n, ast.Compare)))
print("门内 Not    =", sum(1 for n in ast.walk(gate) if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.Not)))
print("门内 Name 集合 =", names)
print("ge100/supp_rows/probe_rows 在门内 =",
      ("ge100" in names), ("supp_rows" in names), ("probe_rows" in names))

# 全模块：任何 Compare 节点子树内出现 ge100（Name / keyword / 字符串常量三种形态都查）
cmp_dump_hits = [n.lineno for n in ast.walk(tree)
                 if isinstance(n, ast.Compare) and "ge100" in ast.dump(n)]
name_hits = [(n.lineno, type(n.ctx).__name__) for n in ast.walk(tree)
             if isinstance(n, ast.Name) and n.id == "ge100"]
kw_hits = [(n.lineno, [k.arg for k in n.keywords if k.arg == "ge100"])
           for n in ast.walk(tree) if isinstance(n, ast.Call) and any(k.arg == "ge100" for k in n.keywords)]
print("含 ge100 的 Compare 节点（dump 法） =", len(cmp_dump_hits), cmp_dump_hits)
print("ast.Name ge100 出现处 =", name_hits if name_hits else "无（:297 为 keyword、:340 为字符串下标，均非 Name）")
print("ge100 keyword 出现处 =", kw_hits)

# :356-369 emit 字面统计
lit = nonlit = 0
for n in ast.walk(tree):
    if (isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
            and isinstance(n.value.func, ast.Name) and n.value.func.id == "emit"
            and 356 <= n.lineno <= 369):
        if all(isinstance(a, ast.Constant) and isinstance(a.value, str) for a in n.value.args):
            lit += 1
        else:
            nonlit += 1
print(":356-369 emit 纯字面 =", lit, "含非字面 =", nonlit)

# :420 总判定
for n in ast.walk(tree):
    if (isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
            and isinstance(n.value.func, ast.Name) and n.value.func.id == "emit"
            and n.lineno == 420):
        consts = [c.value for c in ast.walk(n.value) if isinstance(c, ast.Constant) and isinstance(c.value, str)]
        print(":420 字符串常量 =", consts)
        print(":420 含「9.1–9.7」 =", any("9.1–9.7" in c for c in consts))
        print(":420 调用子树含 all_pass =", any(isinstance(x, ast.Name) and x.id == "all_pass" for x in ast.walk(n.value)))
        for x in ast.walk(n.value):
            if isinstance(x, ast.IfExp):
                t = x.test
                print(":420 IfExp 条件 =", ("Name(all_pass)" if isinstance(t, ast.Name) else ast.dump(t)[:80]))

# :417-419 §9.7 文案（确认高档≥100ms 子句为纯字面、不在任何门内）
for n in ast.walk(tree):
    if (isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
            and isinstance(n.value.func, ast.Name) and n.value.func.id == "emit"
            and 417 <= n.lineno <= 419):
        print(":417-419 emit@%d 纯字面 = %s" % (n.lineno, all(isinstance(a, ast.Constant) and isinstance(a.value, str) for a in n.value.args)))

# 全模块 If/条件中对 supp_rows / probe_rows / ge100 的判定性使用
for target in ("supp_rows", "probe_rows", "ge100"):
    in_test = []
    for n in ast.walk(tree):
        if isinstance(n, ast.If) and target in ast.dump(n.test):
            in_test.append(n.lineno)
    print("if 条件含 %s 的节点行 = %s" % (target, in_test if in_test else "无"))
