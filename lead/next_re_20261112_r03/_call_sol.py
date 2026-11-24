#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""向 magpie /v1/responses 调 codex/gpt-6.1-sol（reasoning effort=high），把裁决原文落盘。
只用 stdlib（urllib），不依赖 requests。"""
import json
import sys
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:3425/v1/responses"
KEY = "magpie"
CARD = Path(__file__).resolve().parent


def call(prompt: str, effort: str = "high") -> dict:
    body = {
        "model": "codex/gpt-6.1-sol",
        "input": prompt,
        "reasoning": {"effort": effort},
        "max_output_tokens": 32000,
    }
    req = urllib.request.Request(
        BASE,
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=1200) as r:
        return json.loads(r.read().decode("utf-8"))


def extract_text(resp: dict) -> str:
    out = []
    for item in resp.get("output", []) or []:
        if item.get("type") == "reasoning":
            for c in item.get("summary", []) or []:
                if c.get("text"):
                    out.append(c["text"])
            continue
        for c in item.get("content", []) or []:
            if c.get("type") in ("output_text", "text") and c.get("text"):
                out.append(c["text"])
    return "\n\n".join(out).strip()


def main() -> int:
    prompt_file = Path(sys.argv[1]) if len(sys.argv) > 1 else CARD / "RULING_prompt.md"
    out_file = Path(sys.argv[2]) if len(sys.argv) > 2 else CARD / "RULING_GPT61SOL.md"
    effort = sys.argv[3] if len(sys.argv) > 3 else "high"
    prompt = prompt_file.read_text(encoding="utf-8")
    print(f"[sol] prompt chars={len(prompt)} effort={effort}", flush=True)
    resp = call(prompt, effort)
    text = extract_text(resp)
    usage = resp.get("usage", {})
    meta = {
        "model": resp.get("model"),
        "status": resp.get("status"),
        "usage": usage,
        "effort": effort,
        "prompt_chars": len(prompt),
        "response_chars": len(text),
    }
    (CARD / "RULING_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    header = (
        "# 裁决 · Codex `codex/gpt-6.1-sol`（reasoning effort=%s）\n\n"
        "> 通道：magpie 网关 `POST /v1/responses`（实测该模型 id 在本通道可用；"
        "本机 Codex CLI 的自带清单一栏只有 gpt-6.1-terra / gpt-6-luna / gpt-5.6-*，"
        "**不含 sol**，故走网关而非 CLI）。\n"
        "> 元数据：%s\n\n---\n\n" % (effort, json.dumps(meta, ensure_ascii=False))
    )
    out_file.write_text(header + text + "\n", encoding="utf-8")
    print(f"[sol] wrote {out_file} chars={len(text)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
