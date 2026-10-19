#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Portable project-root resolution shared by M-track tools.

Resolution order (see ``docs/re/tools_root_portable.md``):
  1. environment variable ``RA2FORGE_ROOT`` (non-empty)
  2. script-relative ``Path(anchor_file).resolve().parents[1]``
  3. legacy hardcode ``D:\\Project\\ra2-campaign-forge`` (compat only; stderr warning)

Usage::

    from _ra2_paths import resolve_root
    ROOT = resolve_root(__file__)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ENV_KEY = "RA2FORGE_ROOT"
LEGACY_ROOT = Path(r"D:\Project\ra2-campaign-forge")


def resolve_root(anchor_file: str | os.PathLike[str] | None = None) -> Path:
    """Return project ROOT according to the documented resolution order.

    ``anchor_file`` is normally the caller's ``__file__``; when omitted the
    path of this module is used (same ``tools/`` parent, same result).
    """
    env = os.environ.get(ENV_KEY, "").strip()
    if env:
        return Path(env)

    anchor = Path(anchor_file) if anchor_file is not None else Path(__file__)
    try:
        derived = anchor.resolve().parents[1]
    except (IndexError, OSError, RuntimeError):
        derived = None
    if derived is not None and derived.is_dir():
        return derived

    print(
        f"[warn] {ENV_KEY} unset and script-relative root unavailable; "
        f"falling back to legacy hardcode {LEGACY_ROOT} (compat only)",
        file=sys.stderr,
    )
    return LEGACY_ROOT
