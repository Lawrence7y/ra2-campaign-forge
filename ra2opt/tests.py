"""内置自检：`python -m ra2opt selftest`。

覆盖的是"错了会真的搞坏玩家游戏目录"的那些路径：

- safewrite 拒绝越界/目录穿越/不存在的目标
- PE 头读写往返（COFF LAA 位、栈、堆；DllCharacteristics 与 LAA 互不污染），且代码段字节不变
- INI 行级保留（注释、顺序、键名大小写、GBK 中文）
- 备份 → 回滚的字节级往返
- cnc-ddraw 调优的幂等性与"只写新版存在的键"
- 端到端：在临时目录里造一个假游戏目录，跑完整 apply(--profile perf)，
  然后 restore，核对除了"我们明确要改的"以外一个字节都没动，
  尤其**不能碰**战役文件（expandmd98.mix / BATTLEMD.INI）
- 单位预算分析
"""

from __future__ import annotations

import io
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

from . import appcompat, backup, budget, cddraw
from . import game as gamemod, inifile, launcher, optimize, pe, safewrite
from .cddraw import DDRAW_GLOBAL, DDRAW_PER_EXE

PASSED = []
FAILED = []


def check(name, fn):
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 - 自检要把失败原因完整打出来
        FAILED.append((name, f"{type(exc).__name__}: {exc}"))
        print(f"  FAIL  {name}\n        {type(exc).__name__}: {exc}")
    else:
        PASSED.append(name)
        print(f"  ok    {name}")


def expect_raises(fn, exc_types, needle=""):
    try:
        fn()
    except exc_types as exc:
        if needle and needle not in str(exc):
            raise AssertionError(f"异常信息里没有 {needle!r}：{exc}") from exc
        return
    raise AssertionError(f"预期抛出 {exc_types}，但正常返回了")


# ---------------------------------------------------------------------------
# 1. safewrite
# ---------------------------------------------------------------------------

def test_safewrite(tmp: Path):
    base = tmp / "gamedir"
    base.mkdir(parents=True, exist_ok=True)
    (base / "ok.txt").write_bytes(b"hello")

    def roundtrip():
        safewrite.write_bytes(base, "ok.txt", b"world")
        assert (base / "ok.txt").read_bytes() == b"world"

    def reject_traversal():
        expect_raises(lambda: safewrite.write_bytes(base, "../evil.txt", b"x"),
                      safewrite.UnsafePathError, "..")
        expect_raises(lambda: safewrite.resolve_within(base, "../evil.txt"),
                      safewrite.UnsafePathError, "..")

    def reject_outside():
        outside = tmp / "outside.txt"
        outside.write_bytes(b"keep")
        expect_raises(lambda: safewrite.write_bytes(base, str(outside), b"x"),
                      safewrite.UnsafePathError)

    def reject_subdir():
        sub = base / "sub"
        sub.mkdir()
        (sub / "deep.txt").write_bytes(b"x")
        expect_raises(lambda: safewrite.write_bytes(base, "sub/deep.txt", b"y"),
                      safewrite.UnsafePathError)

    def reject_missing():
        expect_raises(lambda: safewrite.write_bytes(base, "nope.txt", b"x"),
                      safewrite.UnsafePathError, "不存在")

    def allow_create_ok():
        safewrite.write_bytes(base, "new.txt", b"n", allow_create=True)
        assert (base / "new.txt").read_bytes() == b"n"

    check("safewrite: 正常改写", roundtrip)
    check("safewrite: 拒绝 ../ 穿越", reject_traversal)
    check("safewrite: 拒绝目录外路径", reject_outside)
    check("safewrite: 拒绝子目录路径", reject_subdir)
    check("safewrite: 拒绝不存在的目标", reject_missing)
    check("safewrite: allow_create 可新建", allow_create_ok)


# ---------------------------------------------------------------------------
# 2. PE
# ---------------------------------------------------------------------------

def test_pe(game_copy: Path):
    info0 = pe.read(game_copy)
    assert info0.is_pe32, "测试用的 exe 不是 PE32"
    original = game_copy.read_bytes()

    def text_unchanged_after_patch():
        pe.set_laa(game_copy, True)
        pe.set_stack_reserve(game_copy, 4)
        pe.set_heap_reserve(game_copy, 8)
        info = pe.read(game_copy)
        assert info.laa is True
        assert info.stack_reserve == 4 * pe.MB
        assert info.heap_reserve == 8 * pe.MB
        # 代码段必须字节级不变：只动 PE 头字段（COFF LAA 位 + 栈/堆）
        after = game_copy.read_bytes()
        old_text = original[info0.sections[0].raw_offset:][:info0.sections[0].raw_size + 4096]
        new_text = after[info0.sections[0].raw_offset:][:info0.sections[0].raw_size + 4096]
        assert old_text == new_text, "代码段被改动了"
        # 每个字段实际只会差 1 个字节：COFF 0x66、栈 0xB2、堆 0xBA
        diff = [i for i, (a, b) in enumerate(zip(original, after)) if a != b]
        assert len(diff) <= 8, f"改了太多字节：{diff}"

    def idempotent():
        assert pe.set_laa(game_copy, True) is False, "重复设置 LAA 不应再写盘"
        assert pe.set_stack_reserve(game_copy, 4) is False

    def revert():
        assert pe.set_laa(game_copy, False) is True
        assert pe.read(game_copy).laa is False

    def text_fingerprint_stable():
        # 头部改动不应影响 .text 指纹（这是识别引擎版本的依据）
        before = pe.text_section_sha256(game_copy)
        pe.set_laa(game_copy, True)
        assert pe.text_section_sha256(game_copy) == before
        pe.set_laa(game_copy, False)

    check("pe: 打补丁后代码段字节不变", text_unchanged_after_patch)
    check("pe: 重复设置幂等", idempotent)
    check("pe: 可以还原 LAA", revert)
    check("pe: .text 指纹不受头部改动影响", text_fingerprint_stable)


def find_factory_exe() -> Path | None:
    """出厂原版 gamemd.exe（首次 apply 留在 .ra2opt/orig 的原始快照）。"""
    root = Path(__file__).resolve().parent.parent
    cand = root / "ra2youli" / ".ra2opt" / "orig" / "gamemd.exe"
    return cand if cand.is_file() else None


def test_laa_coff_field(tmp: Path):
    """LAA 字段回归（W3-ZC-S2）：LAA 在 COFF Characteristics（e_lfanew+0x16），
    与 DllCharacteristics 完全无关。

    旧版缺陷：把 0x0020 写进 DllCharacteristics——按 PE 规范那是
    HIGH_ENTROPY_VA，且需 DYNAMIC_BASE(0x0040) 配合才生效；而官方件的
    COFF Characteristics 出厂就是 0x032F（LAA 已置），旧码从未真正动过 LAA。
    """

    def factory_baseline():
        src = find_factory_exe()
        if src is None:
            print("        （本机没有 .ra2opt/orig 出厂快照，跳过出厂件断言）")
            return
        copy = tmp / "factory.exe"
        shutil.copy2(src, copy)
        info = pe.read(copy)
        # ① 读出厂件：COFF Characteristics=0x032F，laa=True，DllCharacteristics=0x0000
        assert info.characteristics == 0x032F and info.laa, \
            f"出厂件 COFF Characteristics 应为 0x032F（LAA 已置），实际 {info.characteristics:#06x}"
        assert info.dll_characteristics == 0x0000 and info.high_entropy_va is False
        assert info.stack_reserve == 1 * pe.MB
        # ② laa off：COFF 位真的被清掉（旧码做不到——它只会去写 DllCharacteristics）
        assert pe.set_laa(copy, False) is True
        after = pe.read(copy)
        assert after.laa is False and after.characteristics == 0x030F
        assert after.dll_characteristics == 0x0000, "LAA off 不得触碰 DllCharacteristics"
        # ③ laa on：可复原为出厂字节
        assert pe.set_laa(copy, True) is True
        restored = pe.read(copy)
        assert restored.laa is True and restored.characteristics == 0x032F
        # ④ 解耦：DllCharacteristics 的 0x0020 与 LAA 互不污染
        assert pe.set_high_entropy_va(copy, True) is True
        he = pe.read(copy)
        assert he.high_entropy_va is True and he.dll_characteristics == 0x0020
        assert he.laa is True and he.characteristics == 0x032F, \
            "HIGH_ENTROPY_VA 不得影响 COFF LAA"
        assert pe.set_laa(copy, False) is True
        he2 = pe.read(copy)
        assert he2.laa is False and he2.high_entropy_va is True, \
            "LAA off 不得动 DllCharacteristics"
        assert pe.set_high_entropy_va(copy, False) is True
        he3 = pe.read(copy)
        assert he3.high_entropy_va is False and he3.dll_characteristics == 0x0000
        assert he3.laa is False and he3.characteristics == 0x030F

    def current_exe_decoupled():
        # 当前件带着旧版写下的 DllChar=0x0020：新代码的 laa 判定只看 COFF，
        # 不再被那个惰性位干扰；laa off 清 COFF 位，DllChar 留痕原样保留。
        copy = tmp / "current.exe"
        shutil.copy2(find_real_exe(), copy)
        info = pe.read(copy)
        assert info.laa is True and info.characteristics == 0x032F
        assert info.dll_characteristics == 0x0020 and info.high_entropy_va is True
        assert pe.set_laa(copy, False) is True
        after = pe.read(copy)
        assert after.laa is False and after.characteristics == 0x030F
        assert after.dll_characteristics == 0x0020, \
            "旧版留痕的 DllChar 位不应被 laa off 顺带清掉"
        assert pe.set_laa(copy, True) is True
        assert pe.read(copy).characteristics == 0x032F

    check("pe.laa: 出厂件 COFF 0x032F→laa=True；off 真清 COFF 位；on 复原；与 DllChar 互不污染",
          factory_baseline)
    check("pe.laa: 当前件（DllChar=0x0020 旧留痕）laa 判定与 DllCharacteristics 解耦",
          current_exe_decoupled)


# ---------------------------------------------------------------------------
# 3. INI
# ---------------------------------------------------------------------------

SAMPLE_INI = (
    "; 中文注释：尤复主配置\r\n"
    "[Options]\r\n"
    "GameSpeed=6\r\n"
    "  DetailLevel = 2\r\n"
    "\r\n"
    "[Video]\r\n"
    "VideoBackBuffer=yes\r\n"
    "\r\n"
    "[Audio]\r\n"
    "SoundVolume=0.700000\r\n"
)


def test_ini(tmp: Path):
    base = tmp / "inidir"
    base.mkdir()
    (base / "ra2md.ini").write_bytes(SAMPLE_INI.encode("gbk"))

    def preserve():
        doc = inifile.IniFile.load(base, "ra2md.ini")
        assert doc.encoding == "gbk", doc.encoding
        assert "; 中文注释：尤复主配置" in doc.text()
        assert doc.get("Options", "GameSpeed") == "6"
        assert doc.get("options", "detaillevel") == "2", "键名大小写应不敏感"
        assert doc.sections() == ["Options", "Video", "Audio"], doc.sections()

    def set_in_place_keeps_format():
        doc = inifile.IniFile.load(base, "ra2md.ini")
        assert doc.set("Video", "VideoBackBuffer", "no") is True
        assert "VideoBackBuffer=no" in doc.text()
        # 原来写成 "  DetailLevel = 2" 的缩进/空格风格要保留
        doc.set("Options", "DetailLevel", "1")
        assert "  DetailLevel = 1" in doc.text()

    def add_missing_key_and_section():
        doc = inifile.IniFile.load(base, "ra2md.ini")
        doc.set("Video", "AllowHiResModes", "yes")
        doc.set("BrandNew", "X", "1")
        text = doc.text()
        assert "AllowHiResModes=yes" in text
        assert "[BrandNew]" in text and "X=1" in text
        # [Video] 的新键应插在 Video 段内，而不是跑到别的段后面
        assert text.index("[Video]") < text.index("AllowHiResModes=yes") < text.index("[Audio]")

    def unmodified_detected():
        doc = inifile.IniFile.load(base, "ra2md.ini")
        assert doc.is_modified() is False
        assert doc.save() is False, "无改动时不应写盘"

    def roundtrip_bytes():
        before = (base / "ra2md.ini").read_bytes()
        doc = inifile.IniFile.load(base, "ra2md.ini")
        doc.set("Options", "GameSpeed", "5")
        doc.save()
        after = (base / "ra2md.ini").read_bytes()
        assert after != before
        # 中文注释在 GBK 往返后仍在
        assert "中文注释" in after.decode("gbk")
        assert b"\r\n" in after, "应保留 CRLF"

    def no_bom_introduced():
        """纯 ASCII 的 INI 本来没有 BOM，改一个键之后也不能凭空多出 BOM。

        这是真实踩过的坑：`utf-8-sig` 解码 + 编码会把 BOM 加回去，而 RA2 的 INI
        解析器遇到 `\\xEF\\xBB\\xBF[Intro]` 就认不出这是节头，第一节设置直接失效。
        """
        plain = base / "nobom.ini"
        plain.write_bytes(b"[Intro]\r\nPlay=no\r\n")
        assert not plain.read_bytes().startswith(b"\xef\xbb\xbf")
        doc = inifile.IniFile.load(base, "nobom.ini")
        assert doc.bom is False, "不应把无 BOM 文件判成有 BOM"
        assert doc.sections() == ["Intro"], f"节头没解析出来：{doc.sections()}"
        doc.set("Intro", "Play", "yes")
        doc.save()
        data = plain.read_bytes()
        assert not data.startswith(b"\xef\xbb\xbf"), "凭空加了 BOM"
        assert data == b"[Intro]\r\nPlay=yes\r\n", data
        # 首节仍然可解析
        assert inifile.IniFile.load(base, "nobom.ini").sections() == ["Intro"]

    def bom_preserved():
        """本来有 BOM 的文件（例如被别的编辑器写过的）要保持原样。"""
        withbom = base / "withbom.ini"
        withbom.write_bytes(b"\xef\xbb\xbf[Intro]\r\nPlay=no\r\n")
        doc = inifile.IniFile.load(base, "withbom.ini")
        assert doc.bom is True
        assert doc.sections() == ["Intro"], "带 BOM 时首个节头也要能解析"
        doc.set("Intro", "Play", "yes")
        doc.save()
        data = withbom.read_bytes()
        assert data.startswith(b"\xef\xbb\xbf"), "BOM 应保留"
        assert b"Play=yes" in data

    check("ini: 保留注释/顺序/编码", preserve)
    check("ini: 原地改值保留格式", set_in_place_keeps_format)
    check("ini: 新增键落在正确的段", add_missing_key_and_section)
    check("ini: 无改动不写盘", unmodified_detected)
    check("ini: GBK + CRLF 往返", roundtrip_bytes)
    check("ini: 不给无 BOM 文件加 BOM", no_bom_introduced)
    check("ini: 有 BOM 时保持 BOM", bom_preserved)


# ---------------------------------------------------------------------------
# 4. 备份 / 回滚
# ---------------------------------------------------------------------------

def test_backup(tmp: Path):
    base = tmp / "bkdir"
    base.mkdir()
    (base / "a.ini").write_bytes(b"original-a")
    (base / "b.dll").write_bytes(b"original-b")

    def snapshot_and_commit():
        bk = backup.BackupSet(base, note="test", profile="x")
        bk.snapshot("a.ini")
        (base / "a.ini").write_bytes(b"changed-a")
        bk.record_file("a.ini")
        bk.commit()
        assert (base / ".ra2opt" / "orig" / "a.ini").read_bytes() == b"original-a"
        assert backup.has_backup(base)

    def snapshot_is_first_touch_only():
        bk = backup.BackupSet(base, note="test2")
        bk.snapshot("a.ini")           # 第二次不应覆盖原始快照
        assert (base / ".ra2opt" / "orig" / "a.ini").read_bytes() == b"original-a"

    def restore_roundtrip():
        bk = backup.BackupSet(base, note="test3")
        bk.snapshot("b.dll")            # 先快照，再改动（顺序反了就会把"改后的内容"当原始态）
        (base / "b.dll").write_bytes(b"changed-b")
        bk.record_file("b.dll")
        bk.commit()
        done = dict(backup.restore(base))
        assert done.get("a.ini") is True, f"a.ini 未还原：{done}"
        assert done.get("b.dll") is True, f"b.dll 未还原：{done}"
        assert (base / "a.ini").read_bytes() == b"original-a", (base / "a.ini").read_bytes()
        assert (base / "b.dll").read_bytes() == b"original-b", (base / "b.dll").read_bytes()
        assert not backup.has_backup(base), "回滚后快照应清空"
        assert not (base / ".ra2opt").exists(), ".ra2opt 目录应清理"

    check("backup: 首次快照 + 记录", snapshot_and_commit)
    check("backup: 快照只写一次（原始态）", snapshot_is_first_touch_only)
    check("backup: 字节级回滚 + 清理", restore_roundtrip)


# ---------------------------------------------------------------------------
# 5. 兼容性标记 / ddraw 配置（纯函数部分）
# ---------------------------------------------------------------------------

def test_pure_logic():
    def merge():
        assert appcompat.parse_flags("~ RUNASADMIN 16BITCOLOR WINXPSP2") == \
            ["RUNASADMIN", "16BITCOLOR", "WINXPSP2"]
        out = appcompat.merge_flags("~ RUNASADMIN 16BITCOLOR",
                                   add=appcompat.HELPFUL_FLAGS,
                                   remove=appcompat.HARMFUL_FLAGS)
        assert "RUNASADMIN" not in out and "16BITCOLOR" not in out
        assert "DISABLEDXMAXIMIZEDWINDOWEDMODE" in out and "HIGHDPIAWARE" in out
        assert appcompat.merge_flags("~ 16BITCOLOR", remove=appcompat.HARMFUL_FLAGS) is None

    def tune_is_idempotent():
        base_ini = "[ddraw]\n" + "\n".join(f"{k}={v}" for k, v in DDRAW_GLOBAL.items()) \
            + "\n\n[gamemd]\n" + "\n".join(f"{k}={v}" for k, v in DDRAW_PER_EXE.items()) + "\n"
        first = cddraw.tune_ini("[ddraw]\nwindowed=false\n", baseline_text=base_ini)
        assert first.changes, "第一次调优应有改动"
        assert not first.unknown_keys, first.unknown_keys
        second = cddraw.tune_ini(first.text, baseline_text=base_ini)
        assert not second.changes, f"第二次不应再有改动：{second.changes}"

    def tune_refuses_unknown_keys():
        small = "[ddraw]\nwindowed=false\n"
        res = cddraw.tune_ini("[ddraw]\n", baseline_text=small)
        assert res.unknown_keys, "基线里没有的键应被识别为 unknown"
        assert "ddraw.width" in res.unknown_keys

    def version_compare():
        assert gamemod.compare_versions("4.4.7.0", "7.1.0.0") < 0
        assert gamemod.compare_versions("7.1.0.0", "7.1.0.0") == 0
        assert gamemod.compare_versions("7.2", "7.1.0.0") > 0
        assert gamemod.compare_versions(None, "7.1") == 0

    def budget_thresholds():
        ok = budget.MissionBudget(name="M1", structures=50, units=50, infantry=50)
        warn = budget.MissionBudget(name="M2", structures=150, units=200, infantry=150)
        heavy = budget.MissionBudget(name="M3", structures=400, units=500, infantry=400)
        assert ok.verdict == "ok", f"250 个物件应是 ok，实际 {ok.verdict}"
        assert warn.verdict == "warn", f"500 个物件应是 warn，实际 {warn.verdict}"
        assert heavy.verdict == "heavy", f"1300 个物件应是 heavy，实际 {heavy.verdict}"
        assert "M3" in budget.render([heavy])

    check("appcompat: 标记增删逻辑", merge)
    check("cddraw: 调优幂等", tune_is_idempotent)
    check("cddraw: 拒绝基线里不存在的键", tune_refuses_unknown_keys)
    check("game: 版本比较", version_compare)
    check("budget: 阈值与渲染", budget_thresholds)


# ---------------------------------------------------------------------------
# 6. 端到端
# ---------------------------------------------------------------------------

def make_fake_ddraw_zip(path: Path) -> Path:
    """造一个"官方 release 包"：ddraw.ini 里列出我们所有要写的键（模拟真实新版）。"""
    default_ini = "[ddraw]\n" + "\n".join(
        f"{k}={v}" for k, v in DDRAW_GLOBAL.items()) + "\n[gamemd]\n" + "\n".join(
        f"{k}={v}" for k, v in DDRAW_PER_EXE.items()) + "\n"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("ddraw.dll", b"MZ" + b"\x00" * 4096)
        zf.writestr("ddraw.ini", default_ini)
        zf.writestr("readme.txt", "fake cnc-ddraw for tests")
    return path


def normalize_pe(path: Path) -> None:
    """把 PE 头恢复到"未优化"的基线（COFF LAA 关、栈 1MB、堆 1MB）。

    `ra2youli/gamemd.exe` 可能已经被本工具优化过了（LAA 置位、栈 4MB），
    直接拿它当夹具会让"应该产生改动"的断言全部失效。测试必须从确定的基线出发。
    旧版曾把 DllCharacteristics 的 0x0020（HIGH_ENTROPY_VA）当 LAA 写，那一位
    不归 LAA 管，这里也不清——它由 `set_high_entropy_va` 单独负责。
    """
    pe.set_laa(path, False)
    pe.set_stack_reserve(path, 1)
    pe.set_heap_reserve(path, 1)


def build_fake_game(root: Path, real_exe: Path) -> Path:
    game = root / "fakegame"
    game.mkdir(parents=True, exist_ok=True)
    shutil.copy2(real_exe, game / "gamemd.exe")
    normalize_pe(game / "gamemd.exe")
    (game / "ra2md.ini").write_bytes(
        ("[Options]\r\nGameSpeed=6\r\nDetailLevel=2\r\n\r\n"
         "[Video]\r\nVideoBackBuffer=yes\r\nAllowHiResModes=yes\r\n"
         "ScreenWidth=1366\r\nScreenHeight=768\r\n").encode("gbk"))
    (game / "ra2.ini").write_bytes(
        ("[Options]\r\nGameSpeed=1\r\nDetailLevel=2\r\n\r\n"
         "[Video]\r\nVideoBackBuffer=yes\r\n\r\n").encode("gbk"))
    (game / "ddraw.ini").write_bytes(
        "[ddraw]\r\nwindowed=true\r\nwidth=1280\r\nheight=800\r\n"
        "maintas=false\r\nrenderer=direct3d9\r\n".encode("latin-1"))
    # 战役产物：本工具绝不能碰
    #   BATTLEMD.INI   = 官方战役列表（旧版 ra2forge 会覆写它）
    #   BATTLEMD98.INI = 新版 ra2forge（方案 B）的散装追加注册文件，自有条目
    (game / "expandmd98.mix").write_bytes(b"FAKE-CAMPAIGN-MIX" * 100)
    (game / "BATTLEMD.INI").write_bytes(b"[Battles]\r\n1=SOV1\r\n")
    (game / "BATTLEMD98.INI").write_bytes(
        b"[Battles]\r\n15=RA2F1\r\n\r\n[RA2F1]\r\nCD=2\r\nScenario=ECH01.MAP\r\n"
        b"FinalMovie=\r\nDescription=FAKE-CAMPAIGN\r\n")
    return game


def test_end_to_end(tmp: Path, real_exe: Path):
    game_path = build_fake_game(tmp, real_exe)
    zip_path = make_fake_ddraw_zip(tmp / "cnc-ddraw-test.zip")
    pristine = {
        "expandmd98.mix": (game_path / "expandmd98.mix").read_bytes(),
        "BATTLEMD.INI": (game_path / "BATTLEMD.INI").read_bytes(),
        "BATTLEMD98.INI": (game_path / "BATTLEMD98.INI").read_bytes(),
        "ra2md.ini": (game_path / "ra2md.ini").read_bytes(),
        "ra2.ini": (game_path / "ra2.ini").read_bytes(),
        "ddraw.ini": (game_path / "ddraw.ini").read_bytes(),
        "gamemd.exe": (game_path / "gamemd.exe").read_bytes(),
    }
    state = {}

    def dry_run_changes_nothing():
        rep = optimize.apply(game_path, profile="perf", online=False,
                            ddraw_zip=zip_path, skip_registry=True, dry_run=True)
        assert rep.pe_changes, "dry-run 也应报告 PE 改动"
        for name, before in pristine.items():
            assert (game_path / name).read_bytes() == before, f"dry-run 改动了 {name}"
        assert not (game_path / ".ra2opt").exists(), "dry-run 不应创建快照目录"

    def apply_perf():
        rep = optimize.apply(game_path, profile="perf", online=False,
                            ddraw_zip=zip_path, skip_registry=True)
        state["rep"] = rep
        assert rep.warnings == [], f"apply 有警告：{rep.warnings}"
        info = pe.read(game_path / "gamemd.exe")
        assert info.laa, "perf 档应打开 LAA"
        assert info.stack_reserve == optimize.STACK_RESERVE_MB * pe.MB
        doc = inifile.IniFile.load(game_path, "ra2md.ini")
        assert doc.get("Video", "VideoBackBuffer") == "no"
        assert doc.get("Video", "AllowVRAMSidebar") == "no"
        assert doc.get("Options", "DetailLevel") == "1", "perf 档应把细节降到 1"
        assert doc.keys("Options").get("GameSpeed") == "6", "其它键不能被顺手改掉"
        assert (game_path / launcher.LAUNCHER_NAME).is_file()
        assert (game_path / ".ra2opt" / "orig" / "gamemd.exe").is_file()

    def campaign_files_untouched():
        assert (game_path / "expandmd98.mix").read_bytes() == pristine["expandmd98.mix"], \
            "战役 MIX 被改动了！"
        assert (game_path / "BATTLEMD.INI").read_bytes() == pristine["BATTLEMD.INI"], \
            "BATTLEMD.INI 被改动了！"
        assert (game_path / "BATTLEMD98.INI").read_bytes() == pristine["BATTLEMD98.INI"], \
            "BATTLEMD98.INI 被改动了！"

    def apply_is_idempotent():
        rep = optimize.apply(game_path, profile="perf", online=False,
                            ddraw_zip=zip_path, skip_registry=True)
        assert not rep.pe_changes, f"第二次不该再有 PE 改动：{rep.pe_changes}"
        assert not rep.ini_changes, f"第二次不该再有配置改动：{rep.ini_changes}"
        assert rep.changed_files == [], f"第二次不该再写任何文件：{rep.changed_files}"
        # 内容没变时不应重复生成启动器
        assert launcher.write_launcher(gamemod.GameDir(game_path)) is None
        # 但启动器仍要留在"回滚时负责清理"的名单里
        runs = backup.manifest(game_path).get("runs", [])
        assert any(launcher.LAUNCHER_NAME in r.get("files", []) for r in runs), \
            "启动器应被记入 manifest，否则 restore 会留下它"

    def restore_roundtrip():
        done = dict(optimize.restore(game_path))
        assert done, "应回滚了文件"
        for name, before in pristine.items():
            assert (game_path / name).read_bytes() == before, f"{name} 没有回到原始状态"
        # apply 新建的文件（启动器）应被删除，而不是留在目录里
        assert not (game_path / launcher.LAUNCHER_NAME).exists(), \
            "restore 应删除 apply 新建的启动器"
        assert not backup.has_backup(game_path)

    check("e2e: dry-run 不写任何文件", dry_run_changes_nothing)
    check("e2e: apply --profile perf 生效", apply_perf)
    check("e2e: 不碰战役产物（mix / BATTLEMD / BATTLEMD98）", campaign_files_untouched)
    check("e2e: 重复 apply 幂等", apply_is_idempotent)
    check("e2e: restore 字节级还原", restore_roundtrip)


def test_path_sandbox(tmp: Path, real_exe: Path):
    """文件名来自用户输入时（`--exe`）绝不能跳出游戏目录。

    这里的几个用例都是真实攻击面：
    - `../evil.exe` 相对上跳；
    - `C:/.../x.dll` 绝对路径 —— pathlib 的 `/` 运算符在 Windows 上遇到
      drive-qualified 右操作数会**整段替换**，于是"拼路径"等于"写任意文件"；
    - `sub/x.exe` 借子目录绕开"只操作直属文件"的约定。
    """
    root = tmp / "sandbox"
    game_path = build_fake_game(root, real_exe)
    outside = root / "evil.exe"
    shutil.copy2(real_exe, outside)
    normalize_pe(outside)
    outside_bytes = outside.read_bytes()
    g = gamemod.GameDir(game_path)

    def bare_name_rejected():
        for bad in ("../evil.exe", "sub/x.exe", "C:/Windows/System32/x.dll",
                    "..\\evil.exe", "a/b", ""):
            expect_raises(lambda b=bad: g.exe(b), ValueError)
            assert g.has(bad) is False, f"{bad!r} 不该被当成存在的文件"
        assert g.exe("gamemd.exe").name == "gamemd.exe"

    def resolve_rejects_escape():
        for bad in ("../evil.exe", "sub/x.exe", "C:/Windows/System32/x.dll"):
            expect_raises(lambda b=bad: g.resolve_exe(b), ValueError)
        expect_raises(lambda: g.resolve_exe("nope.exe"), safewrite.UnsafePathError)
        assert g.resolve_exe("gamemd.exe").name == "gamemd.exe"

    def pe_refuses_dotdot():
        expect_raises(lambda: pe.set_laa(game_path / ".." / "evil.exe", True),
                      pe.PEError, "..")
        expect_raises(lambda: pe.set_stack_reserve(game_path / ".." / "evil.exe", 4),
                      pe.PEError, "..")

    def apply_cannot_escape():
        # 绝对路径才是真正会静默写盘的那个变体：`..` 会被 snapshot 的校验挡住并抛错，
        # 而绝对路径经过 pathlib 的路径替换后，snapshot 只会看到 `x.dll` 不存在就放行，
        # 紧接着 pe 就照着绝对路径把 PE 头改掉了。两个都测。
        rep = optimize.apply(game_path, profile="perf", online=False,
                            ddraw_zip=make_fake_ddraw_zip(root / "z.zip"),
                            skip_registry=True, skip_cddraw=True,
                            exes=["../evil.exe", str(outside), "gamemd.exe"])
        assert outside.read_bytes() == outside_bytes, "游戏目录外的文件被改了！"
        assert sum(1 for w in rep.warnings if "evil.exe" in w) == 2, \
            f"两种越界写法都应被拒绝并告警：{rep.warnings}"
        assert rep.pe_changes and rep.pe_changes[0].startswith("gamemd.exe"), rep.pe_changes
        assert pe.read(game_path / "gamemd.exe").laa is True, "合法目标仍应正常生效"

    check("sandbox: exe() 拒绝裸文件名之外的输入", bare_name_rejected)
    check("sandbox: resolve_exe 拒绝越界/不存在", resolve_rejects_escape)
    check("sandbox: pe 写盘拒绝 .. 路径", pe_refuses_dotdot)
    check("sandbox: apply 的 --exe 无法写出目录", apply_cannot_escape)


def test_safe_profile_is_conservative(tmp: Path, real_exe: Path):
    """safe 档绝不能改 exe 二进制（只允许改 PE 头里的栈字段）。"""
    game_path = build_fake_game(tmp / "safe", real_exe)
    zip_path = make_fake_ddraw_zip(tmp / "safe" / "z.zip")
    rep = optimize.apply(game_path, profile="safe", online=False,
                        ddraw_zip=zip_path, skip_registry=True)
    info = pe.read(game_path / "gamemd.exe")
    assert info.laa is False, "safe 档不该打开 LAA"
    assert info.stack_reserve == optimize.STACK_RESERVE_MB * pe.MB
    doc = inifile.IniFile.load(game_path, "ra2md.ini")
    assert doc.get("Options", "DetailLevel") == "2", "safe 档不该改渲染细节"

    def code_untouched():
        # 与原始文件相比只应差 1 个字节：normalize_pe 关掉的 COFF LAA 位（0x66）。
        # safe 档不重新置位，也不会碰栈/堆（normalize 已把栈压到 1MB，safe 再提回
        # 4MB，一来一回与原件相同）。
        orig = real_exe.read_bytes()
        now = (game_path / "gamemd.exe").read_bytes()
        assert len(orig) == len(now)
        diff = [i for i in range(len(orig)) if orig[i] != now[i]]
        assert len(diff) <= 4, f"safe 档改了 {len(diff)} 个字节：{diff}"
        info0 = pe.read(real_exe)
        sec = info0.sections[0]
        assert orig[sec.raw_offset:sec.raw_offset + sec.raw_size] == \
            now[sec.raw_offset:sec.raw_offset + sec.raw_size], "代码段被改了"

    check("safe: 不动 LAA / DetailLevel", lambda: None)
    check("safe: 只改 PE 头栈字段的 4 个字节", code_untouched)
    assert rep.warnings == [], rep.warnings


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

def find_real_exe() -> Path:
    """找一个真实的 gamemd.exe 用于 PE 测试（本仓库里就有）。"""
    root = Path(__file__).resolve().parent.parent
    for cand in (root / "ra2youli" / "gamemd.exe",
                 root.parent / "ra2youli" / "gamemd.exe"):
        if cand.is_file():
            return cand
    raise FileNotFoundError("找不到 ra2youli/gamemd.exe，PE 测试需要一个真实 PE32 文件")


def main() -> int:
    print(f"ra2opt 自检（Python {sys.version.split()[0]}）")
    real_exe = find_real_exe()
    with tempfile.TemporaryDirectory(prefix="ra2opt-selftest-") as td:
        tmp = Path(td)
        print("\n[1] safewrite")
        test_safewrite(tmp)

        print("\n[2] PE 头")
        pe_copy = tmp / "gamemd-copy.exe"
        shutil.copy2(real_exe, pe_copy)
        normalize_pe(pe_copy)
        test_pe(pe_copy)
        test_laa_coff_field(tmp)

        print("\n[3] INI")
        test_ini(tmp)

        print("\n[4] 备份/回滚")
        test_backup(tmp)

        print("\n[5] 纯逻辑")
        test_pure_logic()

        print("\n[6] 端到端")
        test_end_to_end(tmp, real_exe)
        test_path_sandbox(tmp, real_exe)
        test_safe_profile_is_conservative(tmp, real_exe)

    print()
    total = len(PASSED) + len(FAILED)
    if FAILED:
        print(f"失败 {len(FAILED)} / {total}")
        for name, err in FAILED:
            print(f"  - {name}: {err}")
        return 1
    print(f"全部通过：{total} 项")
    return 0
