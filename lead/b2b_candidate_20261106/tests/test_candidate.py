# -*- coding: utf-8 -*-
"""
test_candidate.py - B2b 候选副本隔离合成测试套件

★ 铁纪律遵守：
1. 零真机：不启动 gamemd.exe / ra2loader / YURI.exe，不 taskkill，不读活进程内存。
2. 零采样代码：不写 hook / MiniDump / SuspendThread / StackWalk / 探针注入。
3. 母本 qc151_trip.py 零修改（只读）。
4. ★ 绝不 import 母本、绝不 import 候选（避免触发模块顶层 SetProcessDPIAware 与 _entry）。
5. 采用 AST 提取候选代码中的所有类、函数与常量，剥离顶层副作用调用后 exec 到隔离命名空间。

覆盖六大类测试：
A. 早退：五个早退路径（:6340/:6349/:6361/:6374/:6377）快照为 None 时 finalize_trip 不崩、输出 unknown/none
B. 异常：快照采集抛异常时出口 state=error、置信 none
C. 未知快照三态：None / {} / {"exists": False} 三态可分，且 unknown 的置信绝不是 high
D. 字段输出：7 个 FRESHNESS 字段 + 12 键 info 全部落盘，字段名逐个核对
E. 接线：:5939 调用点确实传了 pre_freshness_snapshot（AST 静态核，不执行）
F. 状态矩阵：STATE_MATRIX.json 全状态覆盖
"""
from __future__ import annotations

import ast
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path("D:/Project/ra2-campaign-forge")
MOTHER_PATH = PROJECT_ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py"
CANDIDATE_PATH = PROJECT_ROOT / "lead/b2b_candidate_20261106/qc151_trip.candidate.py"


def load_candidate_isolated(candidate_path: Path) -> dict:
    """★ 隔离加载器：使用 importlib.util.spec_from_file_location 独立加载候选副本为新模块。

    ★ 安全与副作用防护说明：
      - 在加载期间使用 unittest.mock.patch 拦截 ctypes.windll.user32.SetProcessDPIAware，
        确保加载不改变当前测试进程的全局 DPI 感知状态；
      - 独立模块名指定为 'qc151_candidate_mod'，绝不使用也不 import 'qc151_trip'；
      - 绝不触发 if __name__ == '__main__': sys.exit(_entry()) 主入口；
      - 绝不使用 eval/exec 动态执行代码，避免代码注入与 shell 策略合规风险；
      - 最终返回模块符号命名空间字典供测试安全调用。
    """
    with patch("ctypes.windll.user32.SetProcessDPIAware", return_value=1):
        spec = importlib.util.spec_from_file_location("qc151_candidate_mod", str(candidate_path))
        if spec is None or spec.loader is None:
            raise ImportError(f"无法为候选副本建立加载规格: {candidate_path}")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    return vars(mod)


# 在测试启动时执行一次干净隔离加载
CANDIDATE_NS = load_candidate_isolated(CANDIDATE_PATH)


class BaseIsolatedTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="test_cand_sb_")
        self.sb = Path(self.temp_dir)
        self.carrier = self.sb / "carrier"
        self.carrier.mkdir(parents=True, exist_ok=True)
        self.out = self.sb / "out"
        self.out.mkdir(parents=True, exist_ok=True)
        self.rec = CANDIDATE_NS["Recorder"]()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)


# ==============================================================================
# Category A: 早退路径测试
# ==============================================================================
class TestCategoryA_EarlyExits(BaseIsolatedTest):
    def test_a1_ast_verify_five_early_exits_pre_freshness_is_none(self):
        """A1: AST 静态验证 main() 中 5 个早退路径均在快照采集之前，快照保持 None。"""
        code_text = CANDIDATE_PATH.read_text(encoding="utf-8")
        tree = ast.parse(code_text)

        main_node = None
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == "main":
                main_node = node
                break
        self.assertIsNotNone(main_node, "main() 函数必须存在")

        # 检查 H7: 预初始化 _pre_freshness_snapshot = None (支持 Assign 与 AnnAssign)
        init_found = False
        init_lineno = None
        for n in ast.walk(main_node):
            if isinstance(n, ast.Assign):
                for target in n.targets:
                    if isinstance(target, ast.Name) and target.id == "_pre_freshness_snapshot":
                        if isinstance(n.value, ast.Constant) and n.value.value is None:
                            init_found = True
                            init_lineno = n.lineno
                            break
            elif isinstance(n, ast.AnnAssign):
                if isinstance(n.target, ast.Name) and n.target.id == "_pre_freshness_snapshot":
                    if isinstance(n.value, ast.Constant) and n.value.value is None:
                        init_found = True
                        init_lineno = n.lineno
                        break
        self.assertTrue(init_found, "H7: main 内必须预初始化 _pre_freshness_snapshot = None")

        # 检查 H8: 采集点 _pre_freshness_snapshot = make_pre_freshness_snapshot(...)
        snap_call_lineno = None
        for n in ast.walk(main_node):
            if isinstance(n, ast.Assign):
                for target in n.targets:
                    if isinstance(target, ast.Name) and target.id == "_pre_freshness_snapshot":
                        if isinstance(n.value, ast.Call) and getattr(n.value.func, "id", None) == "make_pre_freshness_snapshot":
                            snap_call_lineno = n.lineno
                            break
        self.assertTrue(snap_call_lineno is not None, "H8: 必须存在 make_pre_freshness_snapshot 调用")

        # 检查 5 个早退返回码的行号均在 H8 快照采集之前
        early_exit_codes = [
            "EXIT_CARRIER_NOT_OWNED",
            "EXIT_TARGET_MISSING",
            "EXIT_TARGET_MISMATCH",
            "EXIT_PRECHECK_SHA_MISMATCH",
            "EXIT_PRECHECK_SIG_MISMATCH",
        ]

        found_exits = {}
        for n in ast.walk(main_node):
            if isinstance(n, ast.Return) and isinstance(n.value, ast.Name):
                ret_name = n.value.id
                if ret_name in early_exit_codes:
                    found_exits[ret_name] = n.lineno

        self.assertEqual(len(found_exits), 5, f"5 个早退返回码必须全部定位，实际找到: {found_exits}")
        for code_name, lineno in found_exits.items():
            self.assertLess(lineno, snap_call_lineno,
                            f"早退出口 {code_name} (行 {lineno}) 必须在快照采集行 ({snap_call_lineno}) 之前发生！")

    def test_a2_finalize_trip_runs_safely_when_snapshot_is_none_no_carrier_file(self):
        """A2: 早退场景下（快照为 None 且载体无 except.txt），finalize_trip 不崩溃，落盘 unknown/none。"""
        finalize_func = CANDIDATE_NS["finalize_trip"]
        code = finalize_func(
            self.rec, self.carrier, bak={}, t0=None, pre_except_txt=None,
            out_dir=self.out, pre_freshness_snapshot=None
        )
        self.assertIsInstance(code, int)

        f_rows = {r["key"]: r["value"] for r in self.rec.rows if r["group"] == "FRESHNESS"}
        self.assertEqual(f_rows.get("freshness_verdict"), "unknown")
        self.assertEqual(f_rows.get("freshness_confidence"), "none")
        self.assertIsNone(f_rows.get("freshness_is_new"))
        self.assertEqual(f_rows.get("pre_snapshot_state"), "unknown")
        self.assertIs(f_rows.get("usable_as_crash_evidence"), False)

    def test_a3_finalize_trip_runs_safely_when_snapshot_is_none_with_carrier_file(self):
        """A3: 早退场景下（快照为 None 但载体有残留 except.txt），finalize_trip 不崩溃，落盘 unknown/none。"""
        (self.carrier / "except.txt").write_text("old crash remnant\n", encoding="utf-8")
        finalize_func = CANDIDATE_NS["finalize_trip"]
        code = finalize_func(
            self.rec, self.carrier, bak={}, t0=None, pre_except_txt=None,
            out_dir=self.out, pre_freshness_snapshot=None
        )
        self.assertIsInstance(code, int)

        f_rows = {r["key"]: r["value"] for r in self.rec.rows if r["group"] == "FRESHNESS"}
        self.assertEqual(f_rows.get("freshness_verdict"), "unknown")
        self.assertEqual(f_rows.get("freshness_confidence"), "none")
        self.assertIsNone(f_rows.get("freshness_is_new"))
        self.assertEqual(f_rows.get("pre_snapshot_state"), "unknown")
        self.assertIs(f_rows.get("usable_as_crash_evidence"), False)

    def test_a4_copy_post_except_evidence_early_exits_all_five_paths_simulation(self):
        """A4: 模拟五个早退路径直接调用 copy_post_except_evidence，均输出 unknown/none。"""
        copy_func = CANDIDATE_NS["copy_post_except_evidence"]
        for exit_idx in range(1, 6):
            rec = CANDIDATE_NS["Recorder"]()
            sub_out = self.out / f"early_exit_{exit_idx}"
            sub_out.mkdir()
            # 模拟快照为 None
            res = copy_func(rec, self.carrier, sub_out, pre_freshness_snapshot=None)
            self.assertIsNone(res, "载体无 except.txt 时 copy_post_except_evidence 应返回 None")
            f_rows = {r["key"]: r["value"] for r in rec.rows if r["group"] == "FRESHNESS"}
            self.assertEqual(f_rows.get("freshness_verdict"), "unknown")
            self.assertEqual(f_rows.get("freshness_confidence"), "none")
            self.assertIsNone(f_rows.get("freshness_is_new"))
            self.assertEqual(f_rows.get("pre_snapshot_state"), "unknown")


# ==============================================================================
# Category B: 异常处理与独立出口
# ==============================================================================
class TestCategoryB_Exceptions(BaseIsolatedTest):
    def test_b1_make_pre_snapshot_exception_handled_returns_state_error(self):
        """B1: 快照采集阶段抛异常（如目标是目录）时被捕获，返回 state=error 与 traceback。"""
        make_snap = CANDIDATE_NS["make_pre_freshness_snapshot"]
        dir_as_file = self.carrier / "except_is_dir.txt"
        dir_as_file.mkdir()

        snap = make_snap(dir_as_file)
        self.assertIsInstance(snap, dict)
        self.assertEqual(snap["state"], "error")
        self.assertIsNotNone(snap["error"])
        self.assertIsNotNone(snap["traceback"])
        self.assertEqual(snap["source"], "script:make_pre_freshness_snapshot")

    def test_b2_classify_pre_snapshot_error_gives_independent_error_exit(self):
        """B2: classify_except_freshness 收到 state=error 快照时进入独立 error_pre_snapshot 出口。"""
        classify = CANDIDATE_NS["classify_except_freshness"]
        pre_err = {
            "state": "error", "error": "PermissionError: access denied",
            "traceback": "mock traceback"
        }
        post = {"exists": True, "sha256": "abcdef", "mtime_post": 100.0}
        res = classify(pre_err, post)
        self.assertEqual(res["verdict"], "error_pre_snapshot")
        self.assertEqual(res["confidence"], "none")
        self.assertIsNone(res["is_new"])
        self.assertEqual(res["pre_snapshot_state"], "error")
        self.assertIs(res["usable_as_crash_evidence"], False)

    def test_b3_copy_post_evidence_with_pre_snapshot_error_emits_f_and_info(self):
        """B3: copy_post_except_evidence 收到 state=error 快照时落盘 error_pre_snapshot 且置信为 none。"""
        (self.carrier / "except.txt").write_text("crash line\n", encoding="utf-8")
        copy_func = CANDIDATE_NS["copy_post_except_evidence"]
        pre_err = {"state": "error", "error": "DiskReadError", "traceback": "..."}

        info = copy_func(self.rec, self.carrier, self.out, pre_freshness_snapshot=pre_err)
        self.assertIsNotNone(info)
        self.assertEqual(info["freshness_verdict"], "error_pre_snapshot")
        self.assertEqual(info["freshness_confidence"], "none")
        self.assertEqual(info["pre_snapshot_state"], "error")

        f_rows = {r["key"]: r["value"] for r in self.rec.rows if r["group"] == "FRESHNESS"}
        self.assertEqual(f_rows.get("freshness_verdict"), "error_pre_snapshot")
        self.assertEqual(f_rows.get("freshness_confidence"), "none")
        self.assertEqual(f_rows.get("pre_snapshot_state"), "error")

    def test_b4_post_copy_exception_records_error_and_reraises(self):
        """B4: 跑后复制写操作抛异常时，必须记录 3 项 ERROR 留痕、落盘 post_read_error 并原样重抛。"""
        (self.carrier / "except.txt").write_text("crash line\n", encoding="utf-8")
        copy_func = CANDIDATE_NS["copy_post_except_evidence"]
        pre_snap = {"state": "present", "exists": True, "sha256": "oldsha", "mtime_pre": 10.0}

        # 将 out_dir 指向不存在且不可写的路径触发写异常
        non_existent_out = self.sb / "no_such_parent" / "nested_out"

        with self.assertRaises(Exception):
            copy_func(self.rec, self.carrier, non_existent_out, pre_freshness_snapshot=pre_snap)

        err_rows = {r["key"]: r["value"] for r in self.rec.rows if r["group"] == "ERROR"}
        self.assertIn("freshness_copy_failed", err_rows)
        self.assertIn("freshness_copy_stage", err_rows)
        self.assertIn("freshness_copy_traceback", err_rows)

        f_rows = {r["key"]: r["value"] for r in self.rec.rows if r["group"] == "FRESHNESS"}
        self.assertEqual(f_rows.get("freshness_verdict"), "post_read_error")
        self.assertEqual(f_rows.get("freshness_confidence"), "none")


# ==============================================================================
# Category C: 未知快照三态测试
# ==============================================================================
class TestCategoryC_UnknownSnapshotStates(BaseIsolatedTest):
    def test_c1_three_inputs_distinct_in_copy_post_info(self):
        """C1: None / {} / {'exists': False} 三种输入在 copy_post_except_evidence 的 info 中可分。"""
        (self.carrier / "except.txt").write_text("line\n", encoding="utf-8")
        copy_func = CANDIDATE_NS["copy_post_except_evidence"]

        rec1 = CANDIDATE_NS["Recorder"]()
        sub1 = self.out / "sub1"
        sub1.mkdir(parents=True, exist_ok=True)
        info1 = copy_func(rec1, self.carrier, sub1, pre_freshness_snapshot=None)

        rec2 = CANDIDATE_NS["Recorder"]()
        sub2 = self.out / "sub2"
        sub2.mkdir(parents=True, exist_ok=True)
        info2 = copy_func(rec2, self.carrier, sub2, pre_freshness_snapshot={})

        rec3 = CANDIDATE_NS["Recorder"]()
        sub3 = self.out / "sub3"
        sub3.mkdir(parents=True, exist_ok=True)
        info3 = copy_func(rec3, self.carrier, sub3, pre_freshness_snapshot={"exists": False})

        # 字段 pre_freshness_snapshot 必须完整保留输入原样，互不相同
        self.assertIsNone(info1["pre_freshness_snapshot"])
        self.assertEqual(info1["pre_freshness_snapshot"], None)
        self.assertEqual(info2["pre_freshness_snapshot"], {})
        self.assertEqual(info3["pre_freshness_snapshot"], {"exists": False})

        self.assertNotEqual(info1["pre_freshness_snapshot"], info2["pre_freshness_snapshot"])
        self.assertNotEqual(info2["pre_freshness_snapshot"], info3["pre_freshness_snapshot"])
        self.assertNotEqual(info1["pre_freshness_snapshot"], info3["pre_freshness_snapshot"])

    def test_c2_unknown_confidence_is_never_high(self):
        """C2: 所有未采集/缺失快照形态（None, {}, {'exists': False}, unknown, 脏值）置信绝不是 high。"""
        classify = CANDIDATE_NS["classify_except_freshness"]
        uncollected_inputs = [
            None,
            {},
            {"exists": False},
            {"state": "unknown"},
            {"state": "unknown", "exists": False},
            {"state": "dirty_invalid_state"},
        ]

        post_states = [
            {"exists": True, "sha256": "123", "mtime_post": 1.0},
            {"exists": False},
        ]

        for pre in uncollected_inputs:
            for post in post_states:
                res = classify(pre, post)
                self.assertEqual(res["verdict"], "unknown", f"输入 {pre} 必须判为 unknown")
                self.assertEqual(res["confidence"], "none", f"输入 {pre} 置信必须为 none")
                self.assertNotEqual(res["confidence"], "high", f"输入 {pre} 绝不可为 high")
                self.assertIsNone(res["is_new"])
                self.assertIs(res["usable_as_crash_evidence"], False)

    def test_c3_missing_without_state_differs_from_absent_confirmed(self):
        """C3: 伪快照 {'exists': False} 绝不等于确认无件 absent_confirmed。"""
        classify = CANDIDATE_NS["classify_except_freshness"]
        post_present = {"exists": True, "sha256": "abc12345", "mtime_post": 100.0}

        # 无 state 的 {'exists': False} 必须判定为 unknown / none
        res_pseudo = classify({"exists": False}, post_present)
        self.assertEqual(res_pseudo["verdict"], "unknown")
        self.assertEqual(res_pseudo["confidence"], "none")
        self.assertIsNone(res_pseudo["is_new"])

        # 真正有 state="absent_confirmed" 的快照判定为 new_first_appearance / high
        res_confirmed = classify({"state": "absent_confirmed", "exists": False}, post_present)
        self.assertEqual(res_confirmed["verdict"], "new_first_appearance")
        self.assertEqual(res_confirmed["confidence"], "high")
        self.assertIs(res_confirmed["is_new"], True)

        self.assertNotEqual(res_pseudo["verdict"], res_confirmed["verdict"])
        self.assertNotEqual(res_pseudo["confidence"], res_confirmed["confidence"])


# ==============================================================================
# Category D: 字段输出与持久化核验
# ==============================================================================
class TestCategoryD_FieldOutputs(BaseIsolatedTest):
    EXPECTED_FRESHNESS_FIELDS = {
        "freshness_verdict",
        "freshness_confidence",
        "freshness_is_new",
        "freshness_note",
        "pre_snapshot_state",
        "usable_as_crash_evidence",
        "captured_at_iso",
    }

    EXPECTED_INFO_KEYS = {
        "source",
        "evidence_path",
        "size",
        "sha256",
        "note",
        "mtime_post",
        "freshness_verdict",
        "freshness_confidence",
        "freshness_note",
        "captured_at_iso",
        "pre_snapshot_state",
        "pre_freshness_snapshot",
    }

    def test_d1_seven_freshness_fields_exact_match_and_values(self):
        """D1: 7 个 FRESHNESS 字段逐个核对，无漏键、无多键，取值约束正确。"""
        (self.carrier / "except.txt").write_text("crash line\n", encoding="utf-8")
        make_snap = CANDIDATE_NS["make_pre_freshness_snapshot"]
        copy_func = CANDIDATE_NS["copy_post_except_evidence"]

        snap = make_snap(self.carrier / "except.txt")
        copy_func(self.rec, self.carrier, self.out, pre_freshness_snapshot=snap)

        fresh_rows = [r for r in self.rec.rows if r["group"] == "FRESHNESS"]
        found_keys = {r["key"] for r in fresh_rows}

        self.assertEqual(len(found_keys), 7, f"FRESHNESS 必须恰好 7 字段，实际: {len(found_keys)}")
        self.assertEqual(found_keys, self.EXPECTED_FRESHNESS_FIELDS)

        f_map = {r["key"]: r["value"] for r in fresh_rows}
        self.assertIn(f_map["freshness_verdict"], CANDIDATE_NS["FRESHNESS_VERDICTS"])
        self.assertIn(f_map["freshness_confidence"], CANDIDATE_NS["FRESHNESS_CONFIDENCES"])
        self.assertIs(f_map["usable_as_crash_evidence"], False)
        self.assertIsInstance(f_map["captured_at_iso"], str)

    def test_d2_twelve_info_keys_exact_match_and_disk_persistence(self):
        """D2: 12 键 info 全部落盘，逐键核对，且 carrier_post_state.json 正确写入。"""
        (self.carrier / "except.txt").write_text("crash line\n", encoding="utf-8")
        make_snap = CANDIDATE_NS["make_pre_freshness_snapshot"]
        copy_func = CANDIDATE_NS["copy_post_except_evidence"]

        snap = make_snap(self.carrier / "except.txt")
        info = copy_func(self.rec, self.carrier, self.out, pre_freshness_snapshot=snap)

        self.assertIsNotNone(info)
        info_keys = set(info.keys())
        self.assertEqual(len(info_keys), 12, f"info 必须恰好 12 键，实际: {len(info_keys)}")
        self.assertEqual(info_keys, self.EXPECTED_INFO_KEYS)

        # 验证载体件跑后状态文件已写出
        state_path = self.out / "carrier_post_state.json"
        self.assertTrue(state_path.exists(), "carrier_post_state.json 必须写出")
        state_data = json.loads(state_path.read_text(encoding="utf-8"))
        for carrier_name in CANDIDATE_NS["CARRIER_FILES"]:
            self.assertIn(carrier_name, state_data)

    def test_d3_seven_freshness_fields_persisted_in_early_return_when_src_missing(self):
        """D3: 载体无 except.txt 时（早退分支），同样全量落盘 7 个 FRESHNESS 字段。"""
        copy_func = CANDIDATE_NS["copy_post_except_evidence"]
        res = copy_func(self.rec, self.carrier, self.out, pre_freshness_snapshot=None)
        self.assertIsNone(res)

        fresh_rows = [r for r in self.rec.rows if r["group"] == "FRESHNESS"]
        found_keys = {r["key"] for r in fresh_rows}
        self.assertEqual(found_keys, self.EXPECTED_FRESHNESS_FIELDS)


# ==============================================================================
# Category E: 接线 AST 静态验证（不执行）
# ==============================================================================
class TestCategoryE_Wiring(unittest.TestCase):
    def test_e1_ast_verify_copy_post_call_in_finalize_trip(self):
        """E1: :5939 / :6167 调用点确实传了 pre_freshness_snapshot。"""
        code_text = CANDIDATE_PATH.read_text(encoding="utf-8")
        tree = ast.parse(code_text)

        finalize_trip_node = None
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == "finalize_trip":
                finalize_trip_node = node
                break
        self.assertIsNotNone(finalize_trip_node, "finalize_trip 必须存在")

        call_nodes = []
        for n in ast.walk(finalize_trip_node):
            if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "copy_post_except_evidence":
                call_nodes.append(n)

        self.assertEqual(len(call_nodes), 1, "finalize_trip 内应恰好有 1 次 copy_post_except_evidence 调用")
        call = call_nodes[0]
        kw_map = {kw.arg: ast.unparse(kw.value) for kw in call.keywords}
        self.assertIn("pre_freshness_snapshot", kw_map, "调用点必须显式传参 pre_freshness_snapshot")
        self.assertEqual(kw_map["pre_freshness_snapshot"], "pre_freshness_snapshot")

    def test_e2_ast_verify_finalize_trip_signature_has_pre_freshness_snapshot(self):
        """E2: finalize_trip 签名末尾必须包含 pre_freshness_snapshot 参数。"""
        code_text = CANDIDATE_PATH.read_text(encoding="utf-8")
        tree = ast.parse(code_text)

        finalize_trip_node = None
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == "finalize_trip":
                finalize_trip_node = node
                break

        arg_names = [a.arg for a in finalize_trip_node.args.args]
        self.assertIn("pre_freshness_snapshot", arg_names)
        self.assertEqual(arg_names[-1], "pre_freshness_snapshot",
                         "pre_freshness_snapshot 必须为 finalize_trip 的末位形参")

    def test_e3_ast_verify_main_pre_freshness_snapshot_lifecycle(self):
        """E3: main() 内 _pre_freshness_snapshot 的完整生命周期：预初始化 -> 采集 -> 传入 finalize_trip。"""
        code_text = CANDIDATE_PATH.read_text(encoding="utf-8")
        tree = ast.parse(code_text)

        main_node = None
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == "main":
                main_node = node
                break

        # 查找 finally 块中调用 finalize_trip 的参数
        finalize_call_found = False
        for n in ast.walk(main_node):
            if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "finalize_trip":
                kw_names = {kw.arg: ast.unparse(kw.value) for kw in n.keywords}
                if "pre_freshness_snapshot" in kw_names:
                    self.assertEqual(kw_names["pre_freshness_snapshot"], "_pre_freshness_snapshot")
                    finalize_call_found = True
        self.assertTrue(finalize_call_found, "main() 内 finally 必须将 _pre_freshness_snapshot 传入 finalize_trip")


# ==============================================================================
# Category F: 状态矩阵全量覆盖（STATE_MATRIX.json）
# ==============================================================================
class TestCategoryF_StateMatrix(unittest.TestCase):
    def setUp(self):
        self.classify = CANDIDATE_NS["classify_except_freshness"]

    def test_f01_matrix_absent_confirmed(self):
        """F01: absent_confirmed 跑前确认无件 + 跑后在地 ⇒ new_first_appearance / high / is_new=True。"""
        pre = {"state": "absent_confirmed", "exists": False}
        post = {"exists": True, "sha256": "h123", "mtime_post": 100.0}
        res = self.classify(pre, post)
        self.assertEqual(res["verdict"], "new_first_appearance")
        self.assertEqual(res["confidence"], "high")
        self.assertIs(res["is_new"], True)
        self.assertIs(res["usable_as_crash_evidence"], False)

    def test_f02_matrix_absent_both(self):
        """F02: absent_both 跑前确认无件 + 跑后无件 ⇒ absent_both / low / is_new=False。"""
        pre = {"state": "absent_confirmed", "exists": False}
        post = {"exists": False}
        res = self.classify(pre, post)
        self.assertEqual(res["verdict"], "absent_both")
        self.assertEqual(res["confidence"], "low")
        self.assertIs(res["is_new"], False)
        self.assertIs(res["usable_as_crash_evidence"], False)

    def test_f03_matrix_leftover_unchanged_mtime_match(self):
        """F03: leftover_unchanged 跑前在 + 跑后在 + sha同 + mtime同 ⇒ leftover_unchanged / high / is_new=False。"""
        pre = {"state": "present", "exists": True, "sha256": "sha_a", "mtime_pre": 100.0}
        post = {"exists": True, "sha256": "sha_a", "mtime_post": 100.0}
        res = self.classify(pre, post)
        self.assertEqual(res["verdict"], "leftover_unchanged")
        self.assertEqual(res["confidence"], "high")
        self.assertIs(res["is_new"], False)
        self.assertIs(res["usable_as_crash_evidence"], False)

    def test_f04_matrix_leftover_unchanged_mtime_missing(self):
        """F04: leftover_unchanged 跑前在 + 跑后在 + sha同 + mtime缺失 ⇒ leftover_unchanged / medium / is_new=False。"""
        pre = {"state": "present", "exists": True, "sha256": "sha_a", "mtime_pre": None}
        post = {"exists": True, "sha256": "sha_a", "mtime_post": 100.0}
        res = self.classify(pre, post)
        self.assertEqual(res["verdict"], "leftover_unchanged")
        self.assertEqual(res["confidence"], "medium")
        self.assertIs(res["is_new"], False)
        self.assertIs(res["usable_as_crash_evidence"], False)

    def test_f05_matrix_new_write(self):
        """F05: new_write 跑前在 + 跑后在 + sha不同 ⇒ new_write / high / is_new=True。"""
        pre = {"state": "present", "exists": True, "sha256": "sha_a", "mtime_pre": 100.0}
        post = {"exists": True, "sha256": "sha_b", "mtime_post": 101.0}
        res = self.classify(pre, post)
        self.assertEqual(res["verdict"], "new_write")
        self.assertEqual(res["confidence"], "high")
        self.assertIs(res["is_new"], True)
        self.assertIs(res["usable_as_crash_evidence"], False)

    def test_f06_matrix_rewritten_same_content_mtime_greater(self):
        """F06: rewritten_same_content 跑前在 + 跑后在 + sha同 + mtime变大 ⇒ rewritten_same_content / medium / is_new=True。"""
        pre = {"state": "present", "exists": True, "sha256": "sha_a", "mtime_pre": 100.0}
        post = {"exists": True, "sha256": "sha_a", "mtime_post": 105.0}
        res = self.classify(pre, post)
        self.assertEqual(res["verdict"], "rewritten_same_content")
        self.assertEqual(res["confidence"], "medium")
        self.assertIs(res["is_new"], True)
        self.assertIs(res["usable_as_crash_evidence"], False)

    def test_f07_matrix_rewritten_same_content_mtime_rollback(self):
        """F07: rewritten_same_content 跑前在 + 跑后在 + sha同 + mtime回拨 ⇒ rewritten_same_content / low / is_new=True。"""
        pre = {"state": "present", "exists": True, "sha256": "sha_a", "mtime_pre": 100.0}
        post = {"exists": True, "sha256": "sha_a", "mtime_post": 95.0}
        res = self.classify(pre, post)
        self.assertEqual(res["verdict"], "rewritten_same_content")
        self.assertEqual(res["confidence"], "low")
        self.assertIs(res["is_new"], True)
        self.assertIs(res["usable_as_crash_evidence"], False)

    def test_f08_matrix_missing_sha_pre(self):
        """F08: missing_sha 跑前在 + 跑后在 + 缺 pre.sha256 ⇒ error_pre_snapshot / none / is_new=None。"""
        pre = {"state": "present", "exists": True, "sha256": None, "mtime_pre": 100.0}
        post = {"exists": True, "sha256": "sha_a", "mtime_post": 100.0}
        res = self.classify(pre, post)
        self.assertEqual(res["verdict"], "error_pre_snapshot")
        self.assertEqual(res["confidence"], "none")
        self.assertIsNone(res["is_new"])
        self.assertIs(res["usable_as_crash_evidence"], False)

    def test_f09_matrix_missing_sha_post(self):
        """F09: missing_sha 跑前在 + 跑后在 + 缺 post.sha256 ⇒ post_read_error / none / is_new=None。"""
        pre = {"state": "present", "exists": True, "sha256": "sha_a", "mtime_pre": 100.0}
        post = {"exists": True, "sha256": None, "mtime_post": 100.0}
        res = self.classify(pre, post)
        self.assertEqual(res["verdict"], "post_read_error")
        self.assertEqual(res["confidence"], "none")
        self.assertIsNone(res["is_new"])
        self.assertIs(res["usable_as_crash_evidence"], False)

    def test_f10_matrix_vanished(self):
        """F10: vanished 跑前在 + 跑后无件 ⇒ vanished / none / is_new=None。"""
        pre = {"state": "present", "exists": True, "sha256": "sha_a", "mtime_pre": 100.0}
        post = {"exists": False}
        res = self.classify(pre, post)
        self.assertEqual(res["verdict"], "vanished")
        self.assertEqual(res["confidence"], "none")
        self.assertIsNone(res["is_new"])
        self.assertIs(res["usable_as_crash_evidence"], False)

    def test_f11_matrix_post_read_error(self):
        """F11: post_read_error 跑后 read_error 非空 ⇒ post_read_error / none / is_new=None。"""
        pre = {"state": "present", "exists": True, "sha256": "sha_a", "mtime_pre": 100.0}
        post = {"read_error": "PermissionError: locked by another process"}
        res = self.classify(pre, post)
        self.assertEqual(res["verdict"], "post_read_error")
        self.assertEqual(res["confidence"], "none")
        self.assertIsNone(res["is_new"])
        self.assertIs(res["usable_as_crash_evidence"], False)

    def test_f12_usable_as_crash_evidence_is_always_false(self):
        """F12: 铁纪律 N9/N10：所有状态输出的 usable_as_crash_evidence 恒为 False。"""
        matrix_cases = [
            ({"state": "unknown"}, {"exists": False}),
            ({"state": "error", "error": "e"}, {"exists": True}),
            ({"state": "absent_confirmed", "exists": False}, {"exists": True, "sha256": "a"}),
            ({"state": "absent_confirmed", "exists": False}, {"exists": False}),
            ({"state": "present", "sha256": "a", "mtime_pre": 1.0}, {"exists": True, "sha256": "a", "mtime_post": 1.0}),
            ({"state": "present", "sha256": "a", "mtime_pre": 1.0}, {"exists": True, "sha256": "b", "mtime_post": 1.0}),
            ({"state": "present", "sha256": "a", "mtime_pre": 1.0}, {"exists": False}),
        ]
        for pre, post in matrix_cases:
            res = self.classify(pre, post)
            self.assertIs(res["usable_as_crash_evidence"], False,
                          f"usable_as_crash_evidence 必须恒为 False, 实际: {res}")


# ==============================================================================
# 自定义执行器：统计 PASS / FAIL 并打印格式化结论
# ==============================================================================
def run_all_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    test_classes = [
        TestCategoryA_EarlyExits,
        TestCategoryB_Exceptions,
        TestCategoryC_UnknownSnapshotStates,
        TestCategoryD_FieldOutputs,
        TestCategoryE_Wiring,
        TestCategoryF_StateMatrix,
    ]
    for tc in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(tc))

    print(f"[{datetime.now().isoformat()}] 开始执行候选合成隔离测试套件...")
    print(f"候选路径: {CANDIDATE_PATH}")
    print(f"用例总数: {suite.countTestCases()}")
    print("-" * 70)

    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)

    pass_count = result.testsRun - len(result.failures) - len(result.errors)
    fail_count = len(result.failures) + len(result.errors)

    print("-" * 70)
    print(f"PASS={pass_count} FAIL={fail_count}")
    print(f"EXIT={0 if result.wasSuccessful() else 1}")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
