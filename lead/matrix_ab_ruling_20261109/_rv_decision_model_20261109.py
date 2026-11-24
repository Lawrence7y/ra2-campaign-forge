# -*- coding: utf-8 -*-
"""Read-only A/B review with a bounded, allowlisted AST expression interpreter.
No module import, dynamic Python execution, process access, or output file writes.
Unsupported syntax is rejected. All prescriptions remain in memory.
"""
import sys
sys.dont_write_bytecode = True
import ast
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
RULING = ROOT / "lead/matrix_ab_ruling_20261109/_ab_RULING_MATRIX_AB_20261109.md"
MATRIX = ROOT / "lead/b2b_design_20261106/STATE_MATRIX.json"
DESIGN = ROOT / "lead/b2b_design_20261106/B2B_DESIGN.md"
CANDIDATE = ROOT / "lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py"
V2 = ROOT / "lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md"
RESIGN = ROOT / "lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md"
R3 = ROOT / "lead/b2b_candidate_review3_20261107/_review_probe_r3.py"
AB = ROOT / "lead/matrix_ab_ruling_20261109/_ab_probe.py"
BASELINES = {
    "lead/matrix_row5_20261109/MATRIX_ROW5_COUPLING.md": ("6f2b3009b0de33bbe6a3f61e7a0e1c9b6e7e20215ea9c94a45f4c52479811ae8", 29818),
    "lead/matrix_row5_20261109/_r5_row5_linkage_assessment.md": ("625436050020104bb6e40bd7b1ec0543b22e3e31cb5bb56a12b0480cff64e26f", 14616),
    "lead/v2_precision_fix_20261108/V2_PRECISION_FIX_PROPOSAL.md": ("b1231ccb8b80c5200e2ff33b15e09ae52b0452a1481dfc7989730f7da16eda5b", 22048),
    "lead/b2b_design_20261106/STATE_MATRIX.json": ("1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016", 3558),
    "lead/b2b_design_20261106/B2B_DESIGN.md": ("565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf", 66735),
    "lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py": ("ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2", 412759),
    "lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md": ("c7bcf035920234bdc66ec410564b296d4c18b62008dd5653ba76a26a38f10801", 28897),
    "lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md": ("1950d3f31048b9a0503f3e026392ca9e15326c39a76104c5cc3fbbdd0455925b", 23129),
    "out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py": ("517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636", 399508),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}


def fingerprint(blob):
    return hashlib.sha256(blob).hexdigest(), len(blob)


def baseline_check(phase):
    for name, expected in BASELINES.items():
        observed = fingerprint((ROOT / name).read_bytes())
        assert observed == expected, (name, observed, expected)
    print(f"BASELINE_{phase}=11/11_MATCH")


class FunctionData:
    def __init__(self, node, closure):
        self.node = node
        self.closure = closure


class DictionaryMethod:
    def __init__(self, receiver, name):
        self.receiver = receiver
        self.name = name


class Returned(Exception):
    def __init__(self, value):
        self.value = value


class BoundedAst:
    """Only literal data, dictionary access, arithmetic and freshness branches.
    Never resolves arbitrary attributes, imports, external callables, or file I/O.
    """
    def __init__(self):
        self.steps = 0
        self.builtins = {"dict": dict, "isinstance": isinstance,
                         "bool": bool, "float": float, "abs": abs}

    def tick(self):
        self.steps += 1
        if self.steps > 10000:
            raise ValueError("AST operation bound exceeded")

    def expr(self, n, env):
        self.tick()
        if isinstance(n, ast.Constant):
            return n.value
        if isinstance(n, ast.Name):
            if n.id in env:
                return env[n.id]
            if n.id in self.builtins:
                return self.builtins[n.id]
            raise ValueError("Unknown data name: " + n.id)
        if isinstance(n, ast.Dict):
            assert all(k is not None for k in n.keys)
            return {self.expr(k, env): self.expr(v, env) for k, v in zip(n.keys, n.values)}
        if isinstance(n, (ast.Tuple, ast.List)):
            values = [self.expr(x, env) for x in n.elts]
            return tuple(values) if isinstance(n, ast.Tuple) else values
        if isinstance(n, ast.Subscript):
            receiver = self.expr(n.value, env)
            assert type(receiver) in (dict, tuple, list, str)
            return receiver[self.expr(n.slice, env)]
        if isinstance(n, ast.Attribute):
            receiver = self.expr(n.value, env)
            if type(receiver) is dict and n.attr in ("get", "update"):
                return DictionaryMethod(receiver, n.attr)
            raise ValueError("Attribute rejected: " + n.attr)
        if isinstance(n, ast.IfExp):
            return self.expr(n.body if self.expr(n.test, env) else n.orelse, env)
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.Not):
            return not self.expr(n.operand, env)
        if isinstance(n, ast.BoolOp):
            value = self.expr(n.values[0], env)
            for child in n.values[1:]:
                if isinstance(n.op, ast.And) and not value:
                    return value
                if isinstance(n.op, ast.Or) and value:
                    return value
                value = self.expr(child, env)
            return value
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Sub):
            a, b = self.expr(n.left, env), self.expr(n.right, env)
            assert type(a) in (int, float) and type(b) in (int, float)
            return a - b
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Mult):
            a, b = self.expr(n.left, env), self.expr(n.right, env)
            assert type(a) is str and type(b) is int and 0 <= b <= 1024
            return a * b
        if isinstance(n, ast.Compare):
            a = self.expr(n.left, env)
            for op, right in zip(n.ops, n.comparators):
                b = self.expr(right, env)
                if isinstance(op, ast.Eq):
                    ok = a == b
                elif isinstance(op, ast.NotEq):
                    ok = a != b
                elif isinstance(op, ast.Is):
                    ok = a is b
                elif isinstance(op, ast.IsNot):
                    ok = a is not b
                elif isinstance(op, ast.In):
                    ok = a in b
                elif isinstance(op, ast.NotIn):
                    ok = a not in b
                elif isinstance(op, ast.Lt):
                    ok = a < b
                elif isinstance(op, ast.LtE):
                    ok = a <= b
                elif isinstance(op, ast.Gt):
                    ok = a > b
                elif isinstance(op, ast.GtE):
                    ok = a >= b
                else:
                    raise ValueError("Comparison rejected")
                if not ok:
                    return False
                a = b
            return True
        if isinstance(n, ast.JoinedStr):
            return "".join(self.expr(v, env) for v in n.values)
        if isinstance(n, ast.FormattedValue):
            value = self.expr(n.value, env)
            assert n.format_spec is None
            return repr(value) if n.conversion == 114 else str(value)
        if isinstance(n, ast.Call):
            fn = self.expr(n.func, env)
            args = [self.expr(x, env) for x in n.args]
            assert all(k.arg is not None for k in n.keywords)
            kwargs = {k.arg: self.expr(k.value, env) for k in n.keywords}
            if isinstance(fn, FunctionData):
                assert not kwargs
                return self.invoke(fn, args)
            if isinstance(fn, DictionaryMethod):
                if fn.name == "get":
                    return fn.receiver.get(*args, **kwargs)
                fn.receiver.update(*args, **kwargs)
                return None
            if fn is dict:
                return dict(*args, **kwargs)
            if fn is isinstance:
                assert len(args) == 2 and args[1] is dict and not kwargs
                return isinstance(args[0], dict)
            if fn is bool:
                return bool(*args)
            if fn is float:
                return float(*args)
            if fn is abs:
                return abs(*args)
            raise ValueError("Callable rejected")
        raise ValueError("Expression rejected: " + type(n).__name__)

    def block(self, nodes, env):
        for n in nodes:
            self.tick()
            if isinstance(n, ast.FunctionDef):
                env[n.name] = FunctionData(n, env)
            elif isinstance(n, ast.Assign):
                value = self.expr(n.value, env)
                for target in n.targets:
                    if isinstance(target, ast.Name):
                        env[target.id] = value
                    elif isinstance(target, (ast.Tuple, ast.List)):
                        assert len(target.elts) == len(value)
                        for name, item in zip(target.elts, value):
                            assert isinstance(name, ast.Name)
                            env[name.id] = item
                    elif isinstance(target, ast.Subscript):
                        receiver = self.expr(target.value, env)
                        assert type(receiver) is dict
                        receiver[self.expr(target.slice, env)] = value
                    else:
                        raise ValueError("Assignment rejected")
            elif isinstance(n, ast.If):
                self.block(n.body if self.expr(n.test, env) else n.orelse, env)
            elif isinstance(n, ast.Expr):
                self.expr(n.value, env)
            elif isinstance(n, ast.Return):
                raise Returned(self.expr(n.value, env))
            else:
                raise ValueError("Statement rejected: " + type(n).__name__)

    def invoke(self, fn, args):
        names = [x.arg for x in fn.node.args.args]
        assert len(names) == len(args)
        env = dict(fn.closure)
        env.update(zip(names, args))
        try:
            self.block(fn.node.body, env)
        except Returned as returned:
            return returned.value
        return None


def fixture_data(path, names):
    env = {}
    interpreter = BoundedAst()
    for n in ast.parse(path.read_bytes().decode("utf-8")).body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            name = n.targets[0].id
            if name in names:
                env[name] = interpreter.expr(n.value, env)
    assert names <= set(env), (names, set(env))
    return env


baseline_check("BEFORE")
ruling_bytes = RULING.read_bytes()
ruling = ruling_bytes.decode("utf-8")
ruling_fp = fingerprint(ruling_bytes)
print("BOUND_RULING=" + str(RULING))
print(f"被核对象 SHA256 = {ruling_fp[0]}，字节数 = {ruling_fp[1]}")
replacements = []
targets = [(MATRIX, 2), (MATRIX, 5), (MATRIX, 4), (DESIGN, 148), (DESIGN, 151), (DESIGN, 150)]
for number, (path, line_number) in enumerate(targets, 1):
    begin = ruling.index(f"### 改动 {number}｜")
    end = ruling.find("\n### ", begin + 1)
    section = ruling[begin:end if end >= 0 else len(ruling)]
    blocks = re.findall(r"^```[^\n]*\n(.*?)\n```", section, flags=re.M | re.S)
    assert len(blocks) == 2, number
    original, prescribed = blocks
    source = path.read_bytes().decode("utf-8")
    assert original == source.splitlines()[line_number - 1], (number, original)
    assert source.count(original) == 1, number
    replacements.append((path, line_number, original, prescribed))
    print(f"ORIGINAL_EXACT_{number}=MATCH {path.relative_to(ROOT).as_posix()}:{line_number}")
print("ORIGINAL_EXACT_TOTAL=6/6_MATCH")
simulated = {p: p.read_bytes().decode("utf-8") for p in (MATRIX, DESIGN)}
for path, _, original, prescribed in replacements:
    simulated[path] = simulated[path].replace(original, prescribed, 1)
rows = json.loads(MATRIX.read_bytes())
rows_b = json.loads(simulated[MATRIX])
assert len(rows) == len(rows_b) == 14
assert all({k: v for k, v in x.items() if k != "condition"} ==
           {k: v for k, v in y.items() if k != "condition"} for x, y in zip(rows, rows_b))
print("B_IN_MEMORY=14_rows_condition_only_noncondition_fields_unchanged")
v2_lines = V2.read_bytes().decode("utf-8").splitlines()
print("V2_115_HEADER=" + v2_lines[114])
print("V2_120_ROW=" + v2_lines[119])
assert "condition" not in v2_lines[114]
assert v2_lines[119] == "| :5 | present | post_read_error | none | false |"
print("V2_CONDITION_COLUMN=ABSENT; V2_120_LITERAL=UNCHANGED_BY_B")

candidate_tree = ast.parse(CANDIDATE.read_bytes().decode("utf-8"))
classifier_node = next(n for n in candidate_tree.body if isinstance(n, ast.FunctionDef) and n.name == "classify_except_freshness")
snapshot_states = next(ast.literal_eval(n.value) for n in candidate_tree.body if isinstance(n, ast.Assign)
                       and any(isinstance(t, ast.Name) and t.id == "FRESHNESS_SNAPSHOT_STATES" for t in n.targets))
function_data = FunctionData(classifier_node, {"FRESHNESS_SNAPSHOT_STATES": snapshot_states})


def classify(pre, post):
    return BoundedAst().invoke(function_data, [pre, post])


print("CHECK_METHOD=BOUNDED_AST_INTERPRETER; ORIGINAL_AB_R3_T5_PYTHON_EXECUTION=NOT_RUN")
ab_data = fixture_data(AB, {"PRE", "POST"})
cells = {(pn, qn): classify(pv, qv) for pn, pv in ab_data["PRE"].items() for qn, qv in ab_data["POST"].items()}
assert len(cells) == 81
read_error_cells = [r for (pn, qn), r in cells.items() if qn.startswith("re(")]
assert len(read_error_cells) == 18
assert all((r["verdict"], r["confidence"], r["is_new"], r["usable_as_crash_evidence"]) ==
           ("post_read_error", "none", None, False) for r in read_error_cells)
print("AB_GRID_AST=81/81_INTERPRETED; READ_ERROR_CELLS=18/18_post_read_error_none_None_False")
r3_data = fixture_data(R3, {"POST_PRESENT", "POST_PRESENT_NO_SHA", "POST_GONE", "FIX", "IS_NEW_EXPECT"})
for label, compared_rows in (("BASELINE", rows), ("IN_MEMORY_B", rows_b)):
    matches = 0
    for idx, row in enumerate(compared_rows, 1):
        pre, post = r3_data["FIX"][idx]
        out = classify(pre, post)
        actual = (out["verdict"], out["confidence"], out["is_new"], out["usable_as_crash_evidence"])
        expected = (row["verdict"], row["confidence"], r3_data["IS_NEW_EXPECT"][idx], row["usableAsCrashEvidence"])
        assert actual == expected, (label, idx, actual, expected)
        matches += 1
    print(f"R3_14_FIXTURES_AST_{label}={matches}/14_MATCH_ALL_FOUR_VALUES")

for state in snapshot_states:
    print(f"B_ROW5_STRICT_KEY pre={state} eligible={rows_b[3]['preState'] == state}")
post_write_failure = ab_data["POST"]["re(exists=True)"]
absent_pre = ab_data["PRE"]["absent_conf"]
assert absent_pre["state"] != rows_b[3]["preState"]
assert absent_pre["state"] == rows_b[4]["preState"] and post_write_failure["exists"] is True
out = classify(absent_pre, post_write_failure)
print("B_STRICT_COUNTEREXAMPLE=absent_confirmed_x_read_error_exists_true; row5_key=False; row6_antecedent=True; matrix_row6="
      + "/".join((rows_b[4]["verdict"], rows_b[4]["confidence"], "True"))
      + f"; actual_AST={out['verdict']}/{out['confidence']}/{out['is_new']}")
assert (rows_b[4]["verdict"], rows_b[4]["confidence"]) != (out["verdict"], out["confidence"])
print("B_MATCH_RULE_CHANGE=REQUIRED_TO_OVERRIDE_preState_AND_APPLY_read_error_PRIORITY")
print("AB_AFTER_B_EVIDENCE=AB.py:219-230_hardcodes_routed_post_read_error_no_matrix_matcher")
pre_error = {"state": "error", "error": "pre capture failed"}
pre_only = classify(pre_error, {"exists": True, "sha256": "x", "read_error": None})
pre_post_error = classify(pre_error, {"exists": True, "read_error": "post copy failed"})
assert pre_only["verdict"] == "error_pre_snapshot"
assert pre_post_error["verdict"] == "post_read_error"
print(f"W2_DISTINCT_EXITS_AST pre_error_only={pre_only['verdict']} both_errors={pre_post_error['verdict']}; pre.error_and_post.read_error_are_distinct")

# Verify exact AST landmarks used in the static O1 reachability proof.
pre_fn = next(n for n in candidate_tree.body if isinstance(n, ast.FunctionDef) and n.name == "make_pre_freshness_snapshot")
copy_fn = next(n for n in candidate_tree.body if isinstance(n, ast.FunctionDef) and n.name == "copy_post_except_evidence")
pre_absent = next(n for n in ast.walk(pre_fn) if isinstance(n, ast.If) and n.lineno == 4598)
assert ast.unparse(pre_absent.test) == "not p.exists()"
assert any(isinstance(n, ast.Return) for n in pre_absent.body)
assert any(isinstance(n, ast.Assign) and ast.unparse(n.targets[0]) == "snap['state']"
           and ast.literal_eval(n.value) == "absent_confirmed" for n in pre_absent.body)
copy_try = next(n for n in copy_fn.body if isinstance(n, ast.Try))
write_call = next(n for n in ast.walk(copy_try) if isinstance(n, ast.Call) and n.lineno == 4772)
assert ast.unparse(write_call.func) == "dst.write_bytes"
update_call = next(n for n in ast.walk(copy_try) if isinstance(n, ast.Call) and n.lineno == 4769)
assert ast.unparse(update_call.func) == "post_observed.update"
assert ast.literal_eval(update_call.args[0].values[0]) is True
error_assign = next(n for n in ast.walk(copy_try.handlers[0]) if isinstance(n, ast.Assign) and n.lineno == 4786)
assert ast.unparse(error_assign.targets[0]) == "post_observed['read_error']"
assert 4769 < 4772 < 4786
print("O1_STATIC_PATH=main:6623_snapshot -> make_pre:4598-4601_absent_return -> main:6636-6649_passive_baseline_no_absent_refusal -> finalize:6167-6168_forward_pre -> copy:4769_exists_True -> :4772_write_can_raise -> :4786_read_error -> :4788_classify -> :4790_reraise")
print("O1_REACHABILITY=STATICALLY_SUPPORTED; REAL_FILESYSTEM_OR_GAME_REPRODUCTION=NOT_RUN")

# Simulate exactly register 7's specified V2 fingerprint changes, without writing.
v2_original = V2.read_bytes().decode("utf-8")
v2_simulated = v2_original
for line_number, target in ((45, DESIGN), (46, MATRIX)):
    old_line = v2_original.splitlines()[line_number - 1]
    old_hash, old_bytes = fingerprint(target.read_bytes())
    new_hash, new_bytes = fingerprint(simulated[target].encode("utf-8"))
    assert old_hash in old_line and f"{old_bytes:,}" in old_line
    new_line = old_line.replace(old_hash, new_hash).replace(f"{old_bytes:,}", f"{new_bytes:,}")
    v2_simulated = v2_simulated.replace(old_line, new_line, 1)
    print(f"SIMULATED_ONLY_{target.name}_SHA256={new_hash} bytes={new_bytes}")
sim_v2_fp = fingerprint(v2_simulated.encode("utf-8"))
resign_lines = RESIGN.read_bytes().decode("utf-8").splitlines()
assert BASELINES["lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md"][0] in resign_lines[34]
assert sim_v2_fp[0] not in resign_lines[34]
print(f"REGISTER7_V2_SIMULATED_SHA256={sim_v2_fp[0]} bytes={sim_v2_fp[1]}")
print("REGISTER7_MISSING_BINDING=RESIGN:35_still_binds_original_V2_and_fails_RESIGN:153")
assert v2_simulated.splitlines()[109] == v2_original.splitlines()[109]
print("REGISTER7_STALE_INLINE_BINDING=V2:110=" + v2_simulated.splitlines()[109])

pattern = re.compile(r"连带供裁量|matrix_row5|欠宽|:5 行|post_read_error")
for ledger in (ROOT / "lead/PENDING_DECISIONS.md", ROOT / "lead/GOAL_THREE_TARGETS_20261018.md"):
    hits = [(idx, line) for idx, line in enumerate(ledger.read_bytes().decode("utf-8").splitlines(), 1) if pattern.search(line)]
    print(f"LEDGER_SEARCH={ledger.name} HITS={len(hits)}")
    for idx, line in hits:
        print(f"LEDGER_HIT={ledger.relative_to(ROOT).as_posix()}:{idx}:{line}")

for idx, line in enumerate(ruling.splitlines(), 1):
    if any(word in line for word in ("已改", "已收紧", "已施行", "已实施")):
        print(f"ACTION_ASSERTION_TEXT_REVIEW={idx}:{line}")
print("ACTION_ASSERTION_REVIEW=no_affirmative_claim_of_implementation_found; hypothetical_B_closures_are_not_executed_changes")
baseline_check("AFTER")
assert fingerprint(RULING.read_bytes()) == ruling_fp
print("REVIEW_EVIDENCE_COMPLETE; RULING_AND_PROTECTED_BASELINES_UNCHANGED; FILE_OUTPUT_WRITES=0")
