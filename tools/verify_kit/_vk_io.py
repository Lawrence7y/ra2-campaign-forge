#!/usr/bin/env python3
"""_vk_io.py -- the single disk-writing helper for verify_kit tools.

Every file written by a verify_kit tool goes through write_bytes() so the
target path is normalized and parent-directory traversal is rejected in
exactly one audited place.
"""
import os


def resolve_writable_path(raw):
    """Normalize raw path and reject any upward ('..') traversal."""
    p = os.path.realpath(os.path.abspath(raw))
    parts = p.replace("\\", "/").split("/")
    if ".." in parts:
        raise ValueError("path must not traverse upward: %r" % raw)
    return p


def write_bytes(path, data):
    """Write bytes to path (normalized). Parent dir must already exist."""
    p = resolve_writable_path(path)
    with open(p, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    return p


def write_text(path, text):
    """Write UTF-8 text to path (normalized). Parent dir must already exist."""
    return write_bytes(path, text.encode("utf-8"))
