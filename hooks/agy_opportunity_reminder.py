#!/usr/bin/env python3
"""Non-blocking Claude Code and Codex reminder for Agy opportunities.

The hook watches every Claude tool, classifies meaningful Agy opportunities,
and emits at most one compact reminder per category for each user turn.
"""

import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile


AGY_COMMAND = re.compile(
    r"(?<![\w-])agy(?:-(?:scout|delegate|review|job|bridge|doctor|trace))?(?![\w-])",
    re.IGNORECASE,
)

MEDIA_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg",
    ".mp3", ".wav", ".m4a", ".flac", ".mp4", ".mov", ".avi", ".webm",
}

POLICY_FILES = {"claude.md", "agents.md"}

CLAUDE_ONLY_TOOLS = {
    "askuserquestion", "enterplanmode", "exitplanmode", "skill", "toolsearch",
    "todowrite", "taskcreate", "taskget", "tasklist", "taskoutput", "taskstop",
    "taskupdate", "schedulewakeup",
}

REMINDERS = {
    "discovery": (
        "depo/kaynak keşfi veya kod-doküman okuması yapıyorsun",
        "`agy-scout --dir <repo> \"net soru ve kompakt file:line digest isteği\"`",
    ),
    "implementation": (
        "dosya veya kod değişikliği yapıyorsun",
        "işin karmaşıklığına göre `--tier flash-medium` veya `--tier flash` seçilmiş, sınırları ve kabul ölçütleri belirlenmiş `agy-delegate` worker'ı",
    ),
    "review": (
        "diff, değişiklik veya kod incelemesi yapıyorsun",
        "taze bir `agy-review` (gerekirse küçük mantıksal path grupları halinde)",
    ),
    "verification": (
        "test/build/lint çalıştırıyor ya da uzun log ve hata çıktısı inceliyorsun",
        "kanıtı dosyada tutan bir Flash `agy-delegate` doğrulayıcısı ve yalnızca kompakt verdict",
    ),
    "git": (
        "Git durumlandırma, commit veya push işi yapıyorsun",
        "ilgili dosyalarla sınırlandırılmış tek bir Flash `agy-delegate` Git worker'ı",
    ),
    "research": (
        "web veya harici kaynak araştırması yapıyorsun",
        "kaynak/alıntı koşulları verilmiş bir Flash `agy-delegate` araştırmacısı",
    ),
    "media": (
        "görsel, ses veya video içeriği inceliyorsun",
        "dosya yolları ve sorular verilmiş multimodal Flash `agy-delegate` worker'ı",
    ),
    "native_agent": (
        "native Claude subagent oluşturuyorsun",
        "iş read-only ise `agy-scout`, yazma işi ise `agy-delegate`, inceleme ise `agy-review`",
    ),
    "terminal": (
        "Claude üzerinden genel bir terminal/otomasyon işi yürütüyorsun",
        "kesin kapsamlı bir Flash `agy-delegate` worker'ı",
    ),
    "external": (
        "harici/MCP aracıyla AGY'ye devredilebilecek bir işlem yürütüyorsun",
        "aynı erişim AGY ortamında varsa Flash `agy-delegate` worker'ı",
    ),
}


def _load_input():
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}


def _state_path(session_id):
    safe_id = hashlib.sha256(session_id.encode("utf-8", "replace")).hexdigest()[:24]
    root = Path(tempfile.gettempdir()) / "claude-agy-opportunity"
    root.mkdir(parents=True, exist_ok=True)
    return root / f"{safe_id}.json"


def _read_state(path):
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(state, dict) and isinstance(state.get("warned"), list):
            return state
    except Exception:
        pass
    return {"warned": []}


def _write_state(path, state):
    try:
        temporary = path.with_suffix(f".{os.getpid()}.tmp")
        temporary.write_text(json.dumps(state), encoding="utf-8")
        os.replace(temporary, path)
    except Exception:
        pass


def _text(tool_input):
    values = []
    for key in (
        "command", "cmd", "code", "description", "prompt", "query", "pattern", "path",
        "file_path", "url", "goal", "task", "instructions",
    ):
        value = tool_input.get(key)
        if isinstance(value, str):
            values.append(value)
    return "\n".join(values)


def _path_from(tool_input):
    for key in ("file_path", "path", "notebook_path"):
        value = tool_input.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def _is_policy_or_agy_plumbing(path):
    normalized = path.replace("/", "\\").lower()
    name = Path(path).name.lower()
    if name in POLICY_FILES:
        return True
    if name.startswith(("agy_task_", "agy_prompt_")):
        return True
    if name.endswith(".output") and "\\tasks\\" in normalized:
        return True
    return any(part in normalized for part in (
        "\\.claude\\hooks\\",
        "\\.claude\\settings.json",
        "\\agy_task_",
        "\\agy_prompt_",
        "\\claude-agy-opportunity\\",
    ))


def _classify_shell(command):
    lowered = command.lower()
    if AGY_COMMAND.search(command):
        return None
    if re.search(r"\bgit\s+(?:diff|show|range-diff|blame)\b", lowered):
        return "review"
    if re.search(r"\bgit\s+(?:add|commit|push|pull|fetch|merge|rebase|tag|checkout|switch|restore|stash)\b", lowered):
        return "git"
    if re.search(r"\b(?:dotnet\s+(?:build|test)|npm\s+(?:test|run)|pnpm\s+(?:test|run)|yarn\s+(?:test|run)|pytest|cargo\s+(?:test|check|build)|go\s+test|mvn\s+test|gradle\s+test|eslint|tsc|ruff|mypy|unity)\b", lowered):
        return "verification"
    if re.search(r"\b(?:rg|grep|findstr|select-string|glob|fd|find|get-content|type|more|less|sed|awk)\b", lowered):
        return "discovery"
    if re.search(r"\b(?:curl|wget|invoke-webrequest|invoke-restmethod)\b|https?://", lowered):
        return "research"
    return "terminal"


def _classify_mcp(tool_name, payload):
    lowered = f"{tool_name} {payload}".lower()
    if any(word in lowered for word in ("write", "edit", "patch", "create", "delete", "move", "rename")):
        return "implementation"
    if any(word in lowered for word in ("review", "diff", "pull_request", "commit", "push")):
        return "review" if any(word in lowered for word in ("review", "diff")) else "git"
    if any(word in lowered for word in ("test", "build", "lint", "compile", "log")):
        return "verification"
    if any(word in lowered for word in ("browser", "web", "search", "fetch", "github")):
        return "research"
    if any(word in lowered for word in ("read", "file", "repo", "code", "filesystem")):
        return "discovery"
    return "external"


def _classify(tool_name, tool_input):
    payload = _text(tool_input)
    if AGY_COMMAND.search(payload):
        return None

    lowered_name = tool_name.lower()
    path = _path_from(tool_input)

    if lowered_name in {"bash", "powershell", "exec_command"}:
        return _classify_shell(tool_input.get("command") or tool_input.get("cmd") or "")
    if lowered_name in {"grep", "glob"}:
        return "discovery"
    if lowered_name == "read":
        if _is_policy_or_agy_plumbing(path):
            return None
        suffix = Path(path).suffix.lower()
        if suffix in MEDIA_EXTENSIONS:
            return "media"
        if suffix in {".log", ".out", ".trace"}:
            return "verification"
        if suffix in {".diff", ".patch"}:
            return "review"
        return "discovery"
    if lowered_name in {"edit", "write", "notebookedit", "notebook_edit", "apply_patch"}:
        if _is_policy_or_agy_plumbing(path):
            return None
        return "implementation"
    if lowered_name in {"agent", "task", "spawn_agent"}:
        return "native_agent"
    if lowered_name in {"webfetch", "websearch", "web_fetch", "web_search", "web__run"}:
        return "research"
    if lowered_name in {"view_image", "imagegen", "image_gen__imagegen"}:
        return "media"
    if lowered_name in {"read_mcp_resource", "list_mcp_resources", "list_mcp_resource_templates"}:
        return "discovery"
    if lowered_name in {"functions.exec", "exec"}:
        return _classify_shell(payload)
    if lowered_name.startswith("mcp__"):
        return _classify_mcp(tool_name, payload)
    if lowered_name in CLAUDE_ONLY_TOOLS:
        return None
    # Future or installation-specific tools remain visible. The reminder is
    # conditional because Agy may not have the same connector or UI access.
    return "external"


def main():
    data = _load_input()
    event = data.get("hook_event_name") or ""
    session_id = str(data.get("session_id") or data.get("thread_id") or "unknown-session")
    turn_id = str(data.get("turn_id") or data.get("prompt_id") or "")
    state_path = _state_path(f"{session_id}:{turn_id}" if turn_id else session_id)

    if event == "UserPromptSubmit":
        _write_state(state_path, {"warned": []})
        return
    if event != "PreToolUse":
        return

    tool_name = str(data.get("tool_name") or "")
    tool_input = data.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return

    category = _classify(tool_name, tool_input)
    if category not in REMINDERS:
        return

    state = _read_state(state_path)
    warned = set(state.get("warned") or [])
    if category in warned:
        return
    warned.add(category)
    state["warned"] = sorted(warned)
    _write_state(state_path, state)

    activity, route = REMINDERS[category]
    context = (
        f"AGY fırsat uyarısı: Şu an {activity}. Bunu doğrudan Claude context'inde "
        f"sürdürmek yerine {route} kullanmak genellikle daha az Claude tokenı harcar. "
        "Bu araç çağrısı engellenmedi. Yalnızca küçük bir conductor kontrolüyse, kullanıcı "
        "etkileşimi gerekiyorsa, AGY aynı erişime sahip değilse veya AGY kanıtında somut bir "
        "sorun varsa doğrudan devam et."
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": context,
        }
    }))


if __name__ == "__main__":
    main()
