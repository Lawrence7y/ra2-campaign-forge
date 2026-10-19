"""备份与回滚。

`ra2opt` 对游戏目录的任何改动都先落一份"原始快照"，全部放在
`<游戏目录>/.ra2opt/` 下：

    .ra2opt/
      orig/<文件名>        首次被改动前的原始字节（只写一次，永远保留）
      manifest.json        每次 apply 的记录：时间/配置档/改了哪些键/注册表前后值

`restore` 把 `orig/` 里的内容覆盖回去，并还原 AppCompatFlags 注册表值，
所以任何一次优化都能一键撤销。`clean` 在确认无需回滚后删除快照。
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path

from . import safewrite

AREA_NAME = ".ra2opt"
ORIG_DIR = "orig"
MANIFEST = "manifest.json"


@dataclass
class Run:
    """一次 apply 的记录。"""
    run_id: str
    label: str
    profile: str
    created: str
    files: list = field(default_factory=list)         # 本次真正写过的文件名
    registry: list = field(default_factory=list)      # [{exe, before, after}]
    notes: list = field(default_factory=list)


class BackupSet:
    """管理一个游戏目录的原始快照与变更记录。"""

    def __init__(self, game_dir, *, note: str = "apply", profile: str = ""):
        self.game_dir = Path(os.path.realpath(os.fspath(game_dir)))
        if not self.game_dir.is_dir():
            raise ValueError(f"游戏目录不存在：{self.game_dir}")
        self.area = self.game_dir / AREA_NAME
        self.orig = self.area / ORIG_DIR
        self.run = Run(
            run_id=time.strftime("%Y%m%d-%H%M%S"),
            label=note,
            profile=profile,
            created=time.strftime("%Y-%m-%d %H:%M:%S"),
        )
        self._run_recorded = False

    # -- 目录 -------------------------------------------------------------
    def ensure_area(self) -> None:
        self.orig.mkdir(parents=True, exist_ok=True)

    # -- 快照 -------------------------------------------------------------
    def snapshot(self, name: str) -> bool:
        """首次改动某个文件前，保存它的原始字节。已存在快照则不动。

        返回 True 表示本次真的新建了快照。文件本来就不存在时返回 False
        （没有"原始状态"需要保存，例如首次安装 ddraw.dll）。
        """
        self.ensure_area()
        try:
            pristine = safewrite.resolve_within(self.game_dir, name)
        except safewrite.MissingTargetError:
            return False
        keep = self.orig / pristine.name
        if keep.exists():
            return False
        data = pristine.read_bytes()
        safewrite.write_bytes(self.orig, pristine.name, data, allow_create=True)
        return True

    def snapshot_many(self, names) -> list:
        return [n for n in names if self.snapshot(n)]

    def record_file(self, name: str) -> None:
        if name not in self.run.files:
            self.run.files.append(name)

    def record_registry(self, exe: str, before, after) -> None:
        self.run.registry.append({"exe": exe, "before": before, "after": after})

    def add_note(self, text: str) -> None:
        self.run.notes.append(text)

    # -- 清单 -------------------------------------------------------------
    def _load_manifest(self) -> dict:
        path = self._manifest_path()
        if not path.is_file():
            return {"version": 1, "runs": []}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            return {"version": 1, "runs": []}

    def _manifest_path(self) -> Path:
        return self.area / MANIFEST

    def commit(self) -> Path:
        """把本次记录写进 manifest.json。"""
        if not self.run.files and not self.run.registry:
            return self._manifest_path()
        self.ensure_area()
        data = self._load_manifest()
        data["runs"].append({
            "run_id": self.run.run_id,
            "label": self.run.label,
            "profile": self.run.profile,
            "created": self.run.created,
            "files": self.run.files,
            "registry": self.run.registry,
            "notes": self.run.notes,
        })
        payload = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        safewrite.write_bytes(self.area, MANIFEST, payload, allow_create=True)
        self._run_recorded = True
        return self._manifest_path()

    def __enter__(self) -> "BackupSet":
        return self

    def __exit__(self, *exc) -> None:
        if exc[0] is None and (self.run.files or self.run.registry):
            self.commit()

    # -- 静态查询/回滚 ----------------------------------------------------
    @staticmethod
    def manifest(game_dir) -> dict:
        area = Path(os.path.realpath(os.fspath(game_dir))) / AREA_NAME
        path = area / MANIFEST
        if not path.is_file():
            return {"version": 1, "runs": []}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            return {"version": 1, "runs": []}

    @staticmethod
    def pristine_files(game_dir) -> list:
        area = Path(os.path.realpath(os.fspath(game_dir))) / AREA_NAME / ORIG_DIR
        if not area.is_dir():
            return []
        return sorted(p.name for p in area.iterdir() if p.is_file())

    @staticmethod
    def has_backup(game_dir) -> bool:
        return bool(BackupSet.pristine_files(game_dir))

    @staticmethod
    def restore(game_dir, *, run_id: str | None = None, dry_run: bool = False) -> list:
        """把原始快照覆盖回游戏目录，并从 manifest 中移除对应记录。

        返回 [(文件名, 是否实际写入)] 列表。`run_id` 为空表示全部还原。
        """
        game = Path(os.path.realpath(os.fspath(game_dir)))
        area = game / AREA_NAME
        orig = area / ORIG_DIR
        if not orig.is_dir():
            return []

        manifest = BackupSet.manifest(game)
        runs = manifest.get("runs", [])
        if run_id:
            targets = [r for r in runs if r.get("run_id") == run_id]
            if not targets:
                raise ValueError(f"找不到 run_id={run_id} 的记录")
        else:
            targets = runs

        # 名字取自 manifest 的 files：既有"改过的"，也有"新建的"。
        # 判据很直接——有原始快照的还原，没有快照的就是 apply 新建的，删掉。
        names = sorted({n for r in targets for n in r.get("files", [])})

        done = []
        for name in names:
            keep = orig / name
            if keep.is_file():
                if dry_run:
                    done.append((name, False))
                    continue
                safewrite.write_bytes(game, name, keep.read_bytes())
                done.append((name, True))
                keep.unlink(missing_ok=True)
                continue
            # 没有原始快照 = 该文件是 apply 期间新建的（如 ra2opt_play.bat、首次安装的 ddraw.dll）
            try:
                target = safewrite.resolve_within(game, name)
            except safewrite.UnsafePathError:
                done.append((name, False))
                continue
            if dry_run:
                done.append((name, False))
                continue
            target.unlink(missing_ok=True)
            done.append((name, True))

        # 还原注册表
        if not dry_run:
            from . import appcompat

            for r in targets:
                for entry in r.get("registry", []):
                    appcompat.set_layer(game / entry["exe"], entry.get("before"))

        if not dry_run:
            kept_ids = {r.get("run_id") for r in runs} - {r.get("run_id") for r in targets}
            manifest["runs"] = [r for r in runs if r.get("run_id") in kept_ids]
            if not manifest["runs"] and not BackupSet.pristine_files(game):
                # 全部回滚完毕：连 manifest 一起清掉，不留 .ra2opt
                mpath = area / MANIFEST
                if mpath.is_file():
                    mpath.unlink()
                for leftover in (orig, area):
                    try:
                        leftover.rmdir()
                    except OSError:
                        pass
            else:
                payload = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")
                safewrite.write_bytes(area, MANIFEST, payload, allow_create=True)
        return done

    @staticmethod
    def clean(game_dir) -> list:
        """删除全部快照（放弃回滚能力）。"""
        game = Path(os.path.realpath(os.fspath(game_dir)))
        area = game / AREA_NAME
        removed = []
        orig = area / ORIG_DIR
        if orig.is_dir():
            for p in sorted(orig.iterdir()):
                if p.is_file():
                    p.unlink()
                    removed.append(p.name)
            try:
                orig.rmdir()
            except OSError:
                pass
        manifest = area / MANIFEST
        if manifest.is_file():
            manifest.unlink()
            removed.append(MANIFEST)
        try:
            area.rmdir()
        except OSError:
            pass
        return removed


# ---------------------------------------------------------------------------
# 模块级便捷函数（CLI 与审计用，避免到处写 BackupSet.xxx）
# ---------------------------------------------------------------------------

def manifest(game_dir) -> dict:
    return BackupSet.manifest(game_dir)


def pristine_files(game_dir) -> list:
    return BackupSet.pristine_files(game_dir)


def has_backup(game_dir) -> bool:
    return BackupSet.has_backup(game_dir)


def restore(game_dir, *, run_id=None, dry_run=False) -> list:
    return BackupSet.restore(game_dir, run_id=run_id, dry_run=dry_run)


def clean(game_dir) -> list:
    return BackupSet.clean(game_dir)


# 可以从另一份安装安全补回的文件：引擎、wrapper。这些是"出厂字节"，
# 换个安装目录也一样。
SEED_BINARIES = (
    "gamemd.exe", "ra2md.exe", "ra2.exe",
    "ddraw.dll", "ddraw.ini",
)

# 游戏自己会重写的配置（分辨率、速度、昵称、难度…）。**默认不补**：
# 别份安装的这两个文件通常是出厂默认值，拿它当"原始态"会把玩家的
# GameSpeed / Difficulty / 阵营选择一起抹掉。确实需要时用 --include-ini。
SEED_INIS = ("ra2md.ini", "ra2.ini")

SEEDABLE_FILES = SEED_BINARIES + SEED_INIS


def _dedupe_ci(names) -> list:
    """按大小写不敏感去重（Windows 上 ra2md.ini 与 RA2MD.INI 是同一个文件）。"""
    seen, out = set(), []
    for name in names:
        if name.lower() not in seen:
            seen.add(name.lower())
            out.append(name)
    return out


def seed(game_dir, source_dir, *, expected=None, include_ini=False, dry_run=False) -> list:
    """从另一份**未改动**的同版本安装里补回原始快照。

    用途：快照被 `clean` 误删、或换机后需要重建回滚点时，只要还有一份原始安装
    （例如本机的 `D:\\Red2\\ra2youli`），就能把原始字节重新放进
    `<游戏目录>/.ra2opt/orig/`，让 `restore` 重新可用。

    `expected` 传 {文件名: sha256} 时逐个核对——只有哈希对得上才接受，
    避免把"同样被改过的"安装当成原始态。

    `include_ini=False`（默认）只补引擎与 wrapper，不含游戏会自己重写的
    `ra2md.ini` / `ra2.ini`（见 `SEED_INIS` 的说明）。

    返回 [(文件名, 状态)]，状态为 seeded / missing / hash-mismatch / dry-run。
    """
    import hashlib

    game = Path(os.path.realpath(os.fspath(game_dir)))
    src = Path(os.path.realpath(os.fspath(source_dir)))
    if not (src / "gamemd.exe").is_file():
        raise ValueError(f"来源目录里没有 gamemd.exe，不像游戏目录：{src}")
    if game == src:
        raise ValueError("来源目录与游戏目录相同，没有意义")

    wanted = SEEDABLE_FILES if include_ini else SEED_BINARIES
    bk = BackupSet(game, note=f"seed from {src.name}")
    if not dry_run:
        bk.ensure_area()

    out = []
    written = set()
    for name in _dedupe_ci(wanted):
        source = src / name
        # 大小写不敏感地找到真实文件名（Windows 上 "ra2md.ini" 可能实际叫 RA2MD.INI）
        if not source.is_file():
            for entry in os.scandir(src):
                if entry.is_file() and entry.name.lower() == name.lower():
                    source = Path(entry.path)
                    break
        if not source.is_file():
            out.append((name, "missing"))
            continue
        if source.name.lower() in written:
            continue
        written.add(source.name.lower())
        data = source.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if expected and name in expected and expected[name] != digest:
            out.append((name, "hash-mismatch"))
            continue
        if dry_run:
            out.append((name, "dry-run"))
            continue
        safewrite.write_bytes(bk.orig, source.name, data, allow_create=True)
        bk.record_file(source.name)
        out.append((source.name, "seeded"))

    if not dry_run:
        bk.add_note(f"从 {src} 补回原始快照（{sum(1 for _, s in out if s == 'seeded')} 个文件）")
        bk.commit()
    return out
