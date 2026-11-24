# -*- coding: utf-8 -*-
"""W11/T3 · `except_freshness` 四分支（+T2 扩展分支）离线测试。

★ 测试沙箱 = `W11_EXCEPT_FRESHNESS/_t3_sandbox_<pid>_<rand>/`（本文件父目录的
  父目录之下新建的临时目录，用完即删）；**不触碰 `out/re_work/` 下任何真实目录**，
  不启动游戏/loader、不注入、不读活进程内存。

运行：python -I -X utf8 test_except_freshness.py
输出：逐用例结果 …，末两行 `PASS=n FAIL=m` / `EXIT=0|1`。
"""
import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path

_HERE = os.path.dirname(os.path.abspath(__file__))
_W11 = os.path.dirname(_HERE)          # = W11_EXCEPT_FRESHNESS/
if _HERE not in sys.path:              # python -I 不自动加脚本目录 ⇒ 手动补
    sys.path.insert(0, _HERE)
import except_freshness as ef          # noqa: E402

SANDBOX_PARENT = Path(_W11)


class FreshnessTest(unittest.TestCase):
    def setUp(self):
        self.sb = Path(tempfile.mkdtemp(prefix="_t3_sandbox_",
                                        dir=str(SANDBOX_PARENT)))
        self.carrier = self.sb / "carrier"
        self.out = self.sb / "out"
        self.carrier.mkdir()
        self.out.mkdir()

    def tearDown(self):
        shutil.rmtree(self.sb, ignore_errors=True)

    # ------------------------------------------------------------------
    # TASK T3 四个必备分支
    # ------------------------------------------------------------------
    def test_01_branch1_source_missing(self):
        """分支1 · 源件缺失：跑前无、跑后无 ⇒ absent_both / is_new=False。"""
        f = self.carrier / "except.txt"
        pre = ef.make_pre_snapshot(f)
        self.assertFalse(pre["exists"])
        res = ef.classify_except_post(pre, f, run_start_ts=time.time())
        self.assertEqual(res["reason"], "absent_both")
        self.assertIs(res["is_new"], False)
        self.assertEqual(res["confidence"], "low")
        self.assertIn("不能证", "".join(res["evidence"]["notes"]))

    def test_02_branch2_leftover_unchanged(self):
        """分支2 · 原样遗留：跑前有、跑后内容与 mtime 均未变 ⇒ not_new。"""
        f = self.carrier / "except.txt"
        f.write_bytes(b"line1\nException occurred at OLD\n")
        pre = ef.make_pre_snapshot(f)
        self.assertTrue(pre["exists"])
        # 原样：不写不动
        res = ef.classify_except_post(pre, f)
        self.assertEqual(res["reason"], "leftover_unchanged")
        self.assertIs(res["is_new"], False)
        self.assertEqual(res["confidence"], "high")
        self.assertEqual(res["evidence"]["post"]["sha256"], pre["sha256"])
        self.assertEqual(res["evidence"]["post"]["mtime"], pre["mtime"])

    def test_03_branch3_content_changed(self):
        """分支3 · 内容变化：跑前有、跑后内容变了 ⇒ new_write / is_new=True。"""
        f = self.carrier / "except.txt"
        f.write_bytes(b"old baseline\n")
        pre = ef.make_pre_snapshot(f)
        time.sleep(0.05)
        f.write_bytes(b"old baseline\nException occurred at NEW\n")
        res = ef.classify_except_post(pre, f)
        self.assertEqual(res["reason"], "new_write")
        self.assertIs(res["is_new"], True)
        self.assertEqual(res["confidence"], "high")
        self.assertNotEqual(res["evidence"]["post"]["sha256"], pre["sha256"])
        # ★ 口径边界：内容变化只回答 F，不当 crash 归因（:677）
        self.assertIn("集合差", res["f_vs_e_note"])

    def test_04_branch4_copy_failure_write(self):
        """分支4 · 复制失败（write_bytes 抛异常）⇒ error 显式留痕，不是静默。"""
        f = self.carrier / "except.txt"
        f.write_bytes(b"data\n")
        bad_out = self.sb / "no_such_out_dir"        # out_dir 不存在 ⇒ 写必抛
        rec = ef.copy_post_evidence_guarded(f, bad_out)
        self.assertFalse(rec["ok"])
        self.assertEqual(rec["stage"], "write_bytes")
        self.assertIsNotNone(rec["traceback"])
        self.assertIn("FileNotFoundError", rec["error"] or "")
        self.assertFalse(bad_out.exists())           # 无静默半成品

    def test_04b_branch4_copy_failure_read(self):
        """分支4b · 复制失败（read_bytes 抛异常：src 是目录）⇒ 同样显式留痕。"""
        d = self.carrier / "not_a_file"
        d.mkdir()
        rec = ef.copy_post_evidence_guarded(d, self.out)
        self.assertFalse(rec["ok"])
        self.assertEqual(rec["stage"], "read_bytes")
        self.assertIsNotNone(rec["traceback"])

    def test_04c_copy_src_missing(self):
        """复制前置：源件缺失 ⇒ 显式 src_missing（harness :4575-4578 返回 None 的对应位）。"""
        rec = ef.copy_post_evidence_guarded(self.carrier / "except.txt", self.out)
        self.assertFalse(rec["ok"])
        self.assertEqual(rec["stage"], "src_missing")
        self.assertFalse(rec["ok"] is None)          # 非静默 None

    # ------------------------------------------------------------------
    # T2 六分支决策表余下分支 + 判据加固
    # ------------------------------------------------------------------
    def test_05_post_read_error(self):
        """跑后件读失败（classify 路径）⇒ post_read_error 显式留痕。"""
        f = self.carrier / "except.txt"
        f.write_bytes(b"x\n")
        pre = ef.make_pre_snapshot(f)
        f.unlink()
        f.mkdir()                                    # 原位变目录 ⇒ 读必抛 OSError
        res = ef.classify_except_post(pre, f)
        self.assertEqual(res["reason"], "post_read_error")
        self.assertIsNone(res["is_new"])
        self.assertIsNotNone(res["evidence"]["post"]["traceback"])

    def test_06_rewritten_same_content(self):
        """T2 盲区补测 · 同内容重写：sha 同 mtime 变 ⇒ rewritten_same_content。"""
        f = self.carrier / "except.txt"
        f.write_bytes(b"same content\n")
        pre = ef.make_pre_snapshot(f)
        time.sleep(0.05)
        f.write_bytes(b"same content\n")             # 内容逐字节相同，确是本趟新写
        res = ef.classify_except_post(pre, f)
        self.assertEqual(res["reason"], "rewritten_same_content")
        self.assertIs(res["is_new"], True)           # ★ 纯 B 会漏（探针[4]），A 补住
        self.assertEqual(res["confidence"], "medium")

    def test_07_vanished(self):
        """跑前在、跑后失 ⇒ vanished 旗标，is_new=None（F 不可判）。"""
        f = self.carrier / "except.txt"
        f.write_bytes(b"x\n")
        pre = ef.make_pre_snapshot(f)
        f.unlink()
        res = ef.classify_except_post(pre, f)
        self.assertEqual(res["reason"], "vanished")
        self.assertIsNone(res["is_new"])

    def test_08_new_first_appearance_and_c_mode(self):
        """跑前无、跑后有 ⇒ new_first_appearance；C 模式只改置信标注。"""
        f = self.carrier / "except.txt"
        pre = ef.make_pre_snapshot(f)
        self.assertFalse(pre["exists"])
        f.write_bytes(b"Exception occurred at NEW\n")
        res = ef.classify_except_post(pre, f)
        self.assertEqual(res["reason"], "new_first_appearance")
        self.assertIs(res["is_new"], True)
        self.assertEqual(res["confidence"], "high")
        res2 = ef.classify_except_post(pre, f, policy={"hard_evidence_mode": True})
        self.assertEqual(res2["reason"], "new_first_appearance")
        self.assertIn("hard", res2["confidence"])

    def test_09_clock_rollback_flag(self):
        """mtime 被拉回 + sha 同 ⇒ rewritten_same_content + suspect_clock_rollback。"""
        f = self.carrier / "except.txt"
        f.write_bytes(b"stable\n")
        pre = ef.make_pre_snapshot(f)
        time.sleep(0.05)
        f.write_bytes(b"stable\n")
        past = pre["mtime"] - 3600.0
        os.utime(f, (past, past))                    # T2 探针[3]手法：utime 伪造
        res = ef.classify_except_post(pre, f)
        self.assertEqual(res["reason"], "rewritten_same_content")
        self.assertIs(res["is_new"], True)
        self.assertTrue(res["suspect_clock_rollback"])
        self.assertEqual(res["confidence"], "low")

    def test_10_run_start_anchor_is_corroboration_only(self):
        """★ 防回归：run_start 只是旁证——锚点再荒谬也不改变判定（否决 naive A）。"""
        f = self.carrier / "except.txt"
        f.write_bytes(b"old\n")
        pre = ef.make_pre_snapshot(f)
        time.sleep(0.05)
        f.write_bytes(b"new\n")
        absurd_anchor = time.time() + 10_000.0       # 落在未来 ⇒ mtime_ge=False
        res = ef.classify_except_post(pre, f, run_start_ts=absurd_anchor)
        self.assertEqual(res["reason"], "new_write")  # 判定不被锚点否决
        self.assertIs(res["is_new"], True)
        self.assertIs(res["evidence"]["corroboration"]["post_mtime_ge_run_start"], False)

    def test_11_pure_function_writes_nothing(self):
        """纯函数性：classify 全程不产生/修改任何文件（沙箱目录清单不变）。"""
        f = self.carrier / "except.txt"
        f.write_bytes(b"a\n")
        pre = ef.make_pre_snapshot(f)
        before = sorted(os.listdir(self.sb))
        ef.classify_except_post(pre, f)
        after = sorted(os.listdir(self.sb))
        self.assertEqual(before, after)

    def test_12_pre_snapshot_error_is_loud(self):
        """跑前快照失败（src 变目录）⇒ classify 返回 error_pre_snapshot（不静默）。"""
        d = self.carrier / "except.txt"
        d.mkdir()                                    # 快照目标不可读
        pre = ef.make_pre_snapshot(d)
        if pre["error"] is None:                     # 某些 FS 允许 stat 目录 ⇒ 人为构造
            pre = {"exists": True, "sha256": None, "mtime": None,
                   "error": "synthetic", "traceback": "synthetic"}
        res = ef.classify_except_post(pre, self.carrier / "except.txt")
        self.assertEqual(res["reason"], "error_pre_snapshot")
        self.assertIsNone(res["is_new"])


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(FreshnessTest)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    n_bad = len(result.failures) + len(result.errors)
    n_pass = result.testsRun - n_bad
    print(f"PASS={n_pass} FAIL={n_bad}")
    print(f"EXIT={0 if n_bad == 0 else 1}")
    return 0 if n_bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
