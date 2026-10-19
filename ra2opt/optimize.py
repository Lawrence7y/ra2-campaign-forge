"""优化配置档与执行。

两个档位，区别只在"是否动 exe 头部"：

**safe**（默认）—— 不碰引擎二进制，只改它外围的东西，任何一步出问题都不影响
"游戏本身还是原来那个游戏"：

1. 升级/安装 cnc-ddraw，并按 RA2/YR 调优 `ddraw.ini`
2. `ra2md.ini` / `ra2.ini` 的 `[Video]` 修正
3. 主线程栈 1MB → 4MB（只改 PE 头字段，不影响代码与指针运算）
4. 清理有害兼容性标记、补上两个有益的
5. 生成高优先级启动器 `ra2opt_play.bat`

**perf** —— 在 safe 之上再开引擎侧开关：

6. `gamemd.exe` 等 exe 置 COFF Characteristics 的 LAA 位（IMAGE_FILE_LARGE_ADDRESS_AWARE，
   4GB 寻址；出厂件该位本已置起，重复 apply 会如实报 already_set 而非假装变更）
7. `DetailLevel` 从 2 降到 1（少画动画/装饰层，换取帧率）

每一步都在 `backup.BackupSet` 里留下原始快照，`restore` 可完全还原。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from . import appcompat, backup, cddraw, game as gamemod, inifile, launcher, pe
from . import safewrite

# 参照 esident 的健壮性：栈提到 4MB 是社区常用值（地址空间按需提交，不会真的占 4MB）
STACK_RESERVE_MB = 4

# [Video] 段的标准修正（RA2 社区多年共识）
VIDEO_FIXES = {
    "VideoBackBuffer": "no",
    "AllowHiResModes": "yes",
    "AllowVRAMSidebar": "no",
    "StretchMovies": "no",
}

PROFILES = {
    "safe": {
        "label": "稳妥",
        "description": "不动 exe 二进制；升级渲染代理、修配置、调栈、清兼容性标记",
        "laa": False,
        "detail": None,
    },
    "perf": {
        "label": "性能",
        "description": "在 safe 基础上置 COFF 头 LAA 位（4GB 寻址）并把渲染细节降到 1 档",
        "laa": True,
        "detail": 1,
    },
}


@dataclass
class ApplyReport:
    profile: str
    game_dir: str
    dry_run: bool = False
    steps: list = field(default_factory=list)
    changed_files: list = field(default_factory=list)
    ini_changes: list = field(default_factory=list)
    registry_changes: list = field(default_factory=list)
    pe_changes: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    skipped: list = field(default_factory=list)
    backup_run: str | None = None

    def step(self, text: str) -> None:
        self.steps.append(text)

    def as_dict(self) -> dict:
        return {
            "profile": self.profile,
            "game_dir": self.game_dir,
            "dry_run": self.dry_run,
            "steps": self.steps,
            "changed_files": self.changed_files,
            "ini_changes": self.ini_changes,
            "registry_changes": self.registry_changes,
            "pe_changes": self.pe_changes,
            "warnings": self.warnings,
            "skipped": self.skipped,
            "backup_run": self.backup_run,
        }


def resolve_zip(*, zip_path=None, online=True, report: ApplyReport | None = None):
    """决定用哪个 cnc-ddraw 包：显式路径 > 本地缓存 > 联网下载。"""
    if zip_path:
        p = Path(zip_path)
        if not p.is_file():
            raise FileNotFoundError(f"指定的 cnc-ddraw 包不存在：{p}")
        return p, "显式指定"
    cached = cddraw.cached_zip()
    if cached is not None:
        return cached, f"本地缓存 {cached.name}"
    if not online:
        raise FileNotFoundError(
            "没有本地缓存的 cnc-ddraw 包，且指定了 --offline。"
            "请先联网跑一次，或用 --ddraw-zip 指定已下载的包。"
        )
    rel = cddraw.latest_release()
    if report is not None:
        report.step(f"联网查到 cnc-ddraw 最新版 {rel.version}（{rel.published}）")
    return cddraw.download(rel), f"联网下载 {rel.version}"


def apply(game_path, *, profile: str = "safe", online: bool = True,
          ddraw_zip=None, detail=None, laa=None, exes=None,
          dry_run: bool = False, multi_cpu: bool = False,
          skip_cddraw: bool = False, skip_registry: bool = False,
          keep_display: bool = False) -> ApplyReport:
    """执行优化。返回结构化报告。"""
    if profile not in PROFILES:
        raise ValueError(f"未知配置档：{profile}（可选 {', '.join(PROFILES)}）")
    spec = PROFILES[profile]
    g = gamemod.GameDir(game_path)
    if not g.valid:
        raise ValueError(f"{g.path} 里没有 {gamemod.GAMEMD_EXE}，不是有效的游戏目录")

    use_laa = spec["laa"] if laa is None else bool(laa)
    use_detail = spec["detail"] if detail is None else detail
    targets = list(exes) if exes else list(g.present_exes())

    report = ApplyReport(profile=profile, game_dir=str(g.path), dry_run=dry_run)
    if dry_run:
        report.step("dry-run：只报告将要做的改动，不写任何文件")

    bk = backup.BackupSet(g.path, note=f"apply {profile}", profile=profile)
    if not dry_run:
        bk.ensure_area()

    # --- 1. cnc-ddraw -----------------------------------------------------
    if skip_cddraw:
        report.skipped.append("按 --no-cddraw 跳过 cnc-ddraw 升级")
    else:
        try:
            zip_path, source = resolve_zip(zip_path=ddraw_zip, online=online, report=report)
            report.step(f"cnc-ddraw 包：{source}")
            if dry_run:
                payload = cddraw.read_zip(zip_path)
                tuned = cddraw.tune_ini(
                    safewrite.read_bytes(g.path, "ddraw.ini").decode("latin-1")
                    if g.has("ddraw.ini") else (payload["ini"] or ""),
                    baseline_text=payload["ini"], keep_display=keep_display)
                report.ini_changes += [f"ddraw.ini: {c}" for c in tuned.changes]
                report.changed_files += ["ddraw.dll", "ddraw.ini"]
                report.step(f"将替换 ddraw.dll（{len(payload['dll']) // 1024} KB）"
                            f"，并调整 ddraw.ini 的 {len(tuned.changes)} 个键")
            else:
                res = cddraw.install(g, zip_path, backup=bk, keep_display=keep_display)
                if res["dll_unchanged"]:
                    report.step("ddraw.dll 与新版逐字节相同，跳过写入")
                else:
                    report.changed_files.append("ddraw.dll")
                if res["ini_unchanged"]:
                    report.step("ddraw.ini 无需改动")
                elif res["ini_written"]:
                    report.changed_files.append("ddraw.ini")
                report.ini_changes += [f"ddraw.ini: {c}" for c in res["ini_changes"]]
                report.step(f"已升级 ddraw.dll，调整 ddraw.ini 的 {len(res['ini_changes'])} 个键")
                for change, why in cddraw.describe_changes(res["ini_changes"]):
                    report.step(f"  {change}" + (f" —— {why}" if why else ""))
                for section, keys in (res.get("new_keys_available") or {}).items():
                    report.step(f"新版 [{section}] 还提供了这些未配置的键（用的是官方默认值）："
                                + ", ".join(keys))
                if res["unknown_keys"]:
                    report.warnings.append(
                        "新版 ddraw.ini 里不存在这些键，已跳过（说明本工具需要更新）："
                        + ", ".join(res["unknown_keys"]))
        except (OSError, ValueError) as exc:
            report.warnings.append(f"cnc-ddraw 步骤失败：{exc}")

    # multi_cpu：把 cnc-ddraw 的单核绑定关掉（换吞吐，稳定性风险自担）
    if multi_cpu and g.has("ddraw.ini"):
        try:
            doc = inifile.IniFile.load(g.path, "ddraw.ini")
            if doc.set("ddraw", "singlecpu", "false"):
                if dry_run:
                    report.ini_changes.append("ddraw.ini: ddraw.singlecpu=false")
                else:
                    bk.snapshot("ddraw.ini")
                    doc.save()
                    bk.record_file("ddraw.ini")
                    report.ini_changes.append("ddraw.ini: ddraw.singlecpu=false")
                    report.changed_files.append("ddraw.ini")
                report.step("已关闭 cnc-ddraw 的单核绑定（multi-cpu）")
        except (OSError, ValueError) as exc:
            report.warnings.append(f"调整 ddraw.ini singlecpu 失败：{exc}")

    # --- 2. ra2md.ini / ra2.ini ------------------------------------------
    for name in ("ra2md.ini", "ra2.ini"):
        if not g.has(name):
            report.skipped.append(f"{name} 不存在")
            continue
        try:
            doc = inifile.IniFile.load(g.path, name)
            changes = doc.set_many("Video", VIDEO_FIXES)
            if use_detail is not None:
                if doc.set("Options", "DetailLevel", use_detail):
                    changes.append(f"Options.DetailLevel={use_detail}")
            if not changes:
                report.step(f"{name} 无需改动")
                continue
            report.ini_changes += [f"{name}: {c}" for c in changes]
            report.changed_files.append(name)
            if dry_run:
                report.step(f"{name} 将改动 {len(changes)} 个键")
            else:
                bk.snapshot(name)
                doc.save()
                bk.record_file(name)
                report.step(f"{name} 已改动 {len(changes)} 个键")
        except (OSError, ValueError) as exc:
            report.warnings.append(f"处理 {name} 失败：{exc}")

    # --- 3. PE 头（栈 / LAA）---------------------------------------------
    for name in targets:
        # 文件名可能来自 --exe，必须过沙箱解析，不能直接拼路径
        try:
            path = g.resolve_exe(name)
        except (ValueError, safewrite.UnsafePathError) as exc:
            report.warnings.append(f"跳过 {name}：{exc}")
            continue
        try:
            info = pe.read(path)
        except pe.PEError as exc:
            report.warnings.append(f"{name}: {exc}")
            continue
        todo = []
        if info.stack_reserve < STACK_RESERVE_MB * pe.MB:
            todo.append(("stack", f"栈 {info.stack_reserve // pe.MB}MB → {STACK_RESERVE_MB}MB"))
        laa_already = bool(use_laa) and info.laa
        if laa_already:
            # 出厂件的 COFF Characteristics 本来就带 LAA 位（0x032F）：如实报告，
            # 不假装变更、也不为此写盘。
            report.step(f"{name} 的 COFF Characteristics 已置 LAA 位（already_set），无需改动")
        elif use_laa:
            todo.append(("laa", "置 COFF Characteristics 的 LAA 位 0x0020（4GB 寻址）"))
        if not todo:
            if not laa_already:
                report.step(f"{name} 的 PE 头已符合目标，跳过")
            continue
        for what, text in todo:
            report.pe_changes.append(f"{name}: {text}")
        if dry_run:
            report.changed_files.append(name)
            report.step(f"{name} 将修改 PE 头：{'；'.join(t for _, t in todo)}")
            continue
        bk.snapshot(name)
        if info.stack_reserve < STACK_RESERVE_MB * pe.MB:
            pe.set_stack_reserve(path, STACK_RESERVE_MB)
        if use_laa:
            pe.set_laa(path, True)
        bk.record_file(name)
        report.changed_files.append(name)
        report.step(f"{name} 已修改 PE 头：{'；'.join(t for _, t in todo)}")

    if use_laa and not pe.is_64bit_host():
        report.warnings.append(
            "当前是 32 位 Windows：LAA 不会带来额外地址空间（32 位系统本身就只有 2GB 用户态），"
            "也不会造成损害。")

    # --- 4. 兼容性标记 ---------------------------------------------------
    if skip_registry:
        report.skipped.append("按 --no-registry 跳过兼容性标记处理")
    else:
        for name in targets:
            try:
                path = g.resolve_exe(name)
            except (ValueError, safewrite.UnsafePathError) as exc:
                report.warnings.append(f"跳过 {name}：{exc}")
                continue
            try:
                info = appcompat.analyze(path, name)
            except OSError as exc:
                report.warnings.append(f"读取 {name} 的兼容性标记失败：{exc}")
                continue
            before = info.get("raw")
            after = appcompat.merge_flags(before, add=appcompat.HELPFUL_FLAGS,
                                          remove=appcompat.HARMFUL_FLAGS)
            if after == before:
                report.step(f"{name} 的兼容性标记已符合目标，跳过")
                continue
            report.registry_changes.append(
                f"{name}: {before or '<无>'} → {after or '<删除>'}")
            if dry_run:
                continue
            try:
                appcompat.set_layer(path, after)
                bk.record_registry(name, before, after)
                report.step(f"{name} 兼容性标记已更新")
            except OSError as exc:
                report.warnings.append(f"写入 {name} 的兼容性标记失败：{exc}")

    # --- 5. 启动器 -------------------------------------------------------
    exe = gamemod.GAMEMD_EXE if g.has(gamemod.GAMEMD_EXE) else targets[0]
    if dry_run:
        report.step(f"将生成高优先级启动器 {launcher.LAUNCHER_NAME}（目标是 {exe}）")
    else:
        try:
            written = launcher.write_launcher(g, exe=exe, priority="high")
            if written:
                report.changed_files.append(written)
                report.step(f"已生成高优先级启动器 {written}")
            else:
                report.step(f"{launcher.LAUNCHER_NAME} 内容未变，跳过")
            # 只要没有它的原始快照，这个文件就是本工具放的，回滚时要负责删掉
            # （覆盖"上一轮 apply 生成、这一轮内容未变"的情况）
            if g.has(launcher.LAUNCHER_NAME) and not (bk.orig / launcher.LAUNCHER_NAME).exists():
                bk.record_file(launcher.LAUNCHER_NAME)
        except (OSError, ValueError) as exc:
            report.warnings.append(f"生成启动器失败：{exc}")

    # --- 收尾 ------------------------------------------------------------
    if not dry_run:
        bk.run.notes.append(f"steps={len(report.steps)} changed={len(report.changed_files)}")
        bk.commit()
        report.backup_run = bk.run.run_id
    report.changed_files = sorted(set(report.changed_files))
    return report


def verify(game_path, *, exe: str = "gamemd.exe", seconds: float = 8.0) -> dict:
    """启动冒烟测试：确认改动之后游戏至少能起来（不做功能验证）。"""
    g = gamemod.GameDir(game_path)
    return launcher.smoke_test(g, exe=exe, seconds=seconds)


def restore(game_path, *, run_id=None, dry_run: bool = False) -> list:
    return backup.BackupSet.restore(game_path, run_id=run_id, dry_run=dry_run)


def status(game_path) -> dict:
    """当前状态：已应用了什么、能回滚什么。"""
    g = gamemod.GameDir(game_path)
    manifest = backup.BackupSet.manifest(g.path)
    exes = {}
    for name in g.present_exes():
        ident = g.identity(name)
        if ident:
            exes[name] = {"laa": ident.laa, "high_entropy_va": ident.high_entropy_va,
                          "stack_reserve_mb": ident.stack_mb}
    return {
        "game_dir": str(g.path),
        "valid": g.valid,
        "exes": exes,
        "ddraw_version": g.ddraw_version(),
        "launcher_present": g.has(launcher.LAUNCHER_NAME),
        "backup_runs": manifest.get("runs", []),
        "pristine_files": backup.BackupSet.pristine_files(g.path),
    }
