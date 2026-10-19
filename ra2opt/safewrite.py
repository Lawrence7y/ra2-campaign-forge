"""受控写盘：全项目唯一的"落盘出口"。

规则（每次写盘都强制校验，不做例外）：

1. `base_dir` 必须是真实存在的目录；目标文件必须落在它的**直属**层级。
2. 路径先 `realpath()` 规范化（消解符号链接与 `..`），再用 `commonpath` 与基准
   比对，必须完全等于基准——既挡住 `../` 上跳，也挡住软链接外逃。
3. 默认只允许改写**已存在**的文件（本工具不新建文件）；需要新建时显式传
   `allow_create=True`，且仍然限制在基准目录直属层级。
4. 先写同目录临时文件再原子替换，避免中途失败留下半截文件。

调用方负责在写入前做备份（见 `backup.BackupSet`）。
"""

from __future__ import annotations

import os
from pathlib import Path


class UnsafePathError(ValueError):
    """目标路径不在允许范围内，拒绝读写。"""


class MissingTargetError(UnsafePathError):
    """目标文件不存在，且调用方不允许新建。"""


def resolve_within(base_dir, target, *, allow_create: bool = False) -> Path:
    """把 target 规范化并校验它确实位于 base_dir 的直属层级，返回真实路径。

    这个函数只做校验与规范化，不做任何写入。
    """
    base = Path(os.path.realpath(os.fspath(base_dir)))
    if not base.is_dir():
        raise UnsafePathError(f"基准目录不存在：{base}")

    candidate = Path(os.fspath(target))
    if ".." in candidate.parts:
        raise UnsafePathError(f"拒绝含 .. 的路径：{candidate}")

    real = Path(os.path.realpath(str(base / candidate.name)))
    if os.path.commonpath([str(base), str(real)]) != str(base):
        raise UnsafePathError(f"拒绝越界访问：{real}（基准 {base}）")
    if real.parent != base:
        raise UnsafePathError(f"只允许访问基准目录的直属文件：{real}")

    if real.exists():
        if not real.is_file():
            raise UnsafePathError(f"目标已存在且不是普通文件：{real}")
    elif not allow_create:
        raise MissingTargetError(f"拒绝操作不存在的文件（本工具不新建文件）：{real}")
    return real


def write_bytes(base_dir, target, data: bytes, *, allow_create: bool = False) -> Path:
    """校验后原子写入字节，返回实际写入的真实路径。"""
    real = resolve_within(base_dir, target, allow_create=allow_create)
    staging = real.with_name(real.name + ".ra2opt.tmp")
    staging.write_bytes(data)
    staging.replace(real)
    return real


def read_bytes(base_dir, target) -> bytes:
    """校验后读取字节（同样限制在基准目录内，避免被诱导读任意文件）。"""
    real = resolve_within(base_dir, target)
    with open(real, "rb") as fh:
        return fh.read()
