"""Plain-text export formatting for plan_history entries."""

from __future__ import annotations

import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo

MAX_EXPORT_CHARS = 8000
JST = ZoneInfo("Asia/Tokyo")


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _plan_fields(item) -> tuple[str, str]:
    if isinstance(item, dict):
        plan = str(item.get("plan") or item.get("案") or "").strip() or "（なし）"
        reason = str(item.get("reason") or item.get("理由") or "").strip() or "（なし）"
    else:
        plan = str(item).strip() or "（なし）"
        reason = "（なし）"
    return plan, reason


def truncate_export_text(text: str, max_len: int = MAX_EXPORT_CHARS) -> str:
    if len(text) <= max_len:
        return text
    suffix = "…（長いので省略）"
    keep = max_len - len(suffix)
    if keep < 1:
        return suffix[:max_len]
    trimmed = text[:keep].rstrip()
    if not trimmed.endswith("\n"):
        trimmed += "\n"
    return trimmed + suffix + "\n"


def format_plan_history_entry(entry: dict) -> str:
    eid = entry.get("id", "?")
    created_at = float(entry.get("created_at") or 0)
    dt = datetime.fromtimestamp(created_at, tz=JST).strftime("%Y/%m/%d %H:%M")
    summary = str(entry.get("slots_summary") or "").strip() or "（なし）"

    lines = [
        f"【デートBot 候補セット #{eid}】",
        dt,
        "",
        "■ 条件",
        summary,
        "",
    ]

    plans = entry.get("plans") or []
    if not plans:
        lines.extend(["■ 案1", "（なし）", "理由: （なし）", ""])
    else:
        for i, item in enumerate(plans, 1):
            plan, reason = _plan_fields(item)
            lines.extend([f"■ 案{i}", plan, f"理由: {reason}", ""])

    text = "\n".join(lines).rstrip() + "\n"
    return truncate_export_text(text)
