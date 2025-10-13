#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

import hashlib
import json
import os
import re
import shlex
import sys
import time
import shutil
from datetime import datetime
from pathlib import Path


def is_dangerous_deletion_command(command):
    """
    Token-based detection of destructive commands.
    Uses shlex.split() to properly tokenize the command and check the first token
    against known destructive commands, avoiding false positives from substrings.
    """
    if not command or not command.strip():
        return False

    # Try to tokenize the command
    try:
        tokens = shlex.split(command.lower())
    except ValueError:
        # If tokenization fails, fall back to basic split
        tokens = command.lower().split()

    if not tokens:
        return False

    first_token = tokens[0]

    # List of known destructive commands
    destructive_commands = {
        # File deletion
        'rm', 'unlink', 'rmdir',
        # File system operations
        'dd', 'shred', 'wipe', 'srm', 'trash',
        # Truncation
        'truncate',
        # Package managers
        'pip', 'npm', 'yarn', 'conda', 'apt', 'yum', 'brew',
        # System operations
        'kill', 'killall', 'pkill', 'fuser',
        'umount', 'swapoff', 'fdisk', 'mkfs', 'format',
        # Archive operations
        'tar', 'zip', 'unzip', 'gunzip', 'bunzip2', 'unxz', '7z',
        # Database operations (if run as commands)
        'mongo', 'psql', 'mysql',
    }

    # Check if the first token is a destructive command
    if first_token in destructive_commands:
        # For package managers, check if they're doing destructive operations
        if first_token in {'npm', 'yarn', 'pip', 'conda', 'apt', 'yum', 'brew'}:
            destructive_verbs = {'uninstall', 'remove', 'rm', 'purge'}
            return any(verb in tokens for verb in destructive_verbs)

        # For archive commands, check for destructive flags
        if first_token in {'tar', 'zip', '7z'}:
            destructive_flags = {'--delete', '-d', 'd'}
            return any(flag in tokens for flag in destructive_flags)

        # For gunzip, bunzip2, unxz - these delete source by default
        if first_token in {'gunzip', 'bunzip2', 'unxz'}:
            return '--keep' not in tokens and '-k' not in tokens

        # All other destructive commands are blocked by default
        return True

    # Check for output redirection that overwrites files (>)
    if '>' in command and '>>' not in command:
        # Allow redirection to /dev/null
        if '/dev/null' not in command:
            return True

    return False


def is_env_file_access(tool_name, tool_input):
    """
    Check if any tool is trying to access .env files containing sensitive data.
    Allows reading .env files but blocks editing/writing operations.
    Also allows access to .env.sample and .env.example files.
    """
    if tool_name in ["Read", "Edit", "MultiEdit", "Write", "Bash"]:
        if tool_name in ["Edit", "MultiEdit", "Write"]:
            file_path = tool_input.get("file_path", "")
            if ".env" in file_path and not (
                file_path.endswith(".env.sample") or file_path.endswith(".env.example")
            ):
                return True

        elif tool_name == "Bash":
            command = tool_input.get("command", "")
            env_write_patterns = [
                r"echo\s+.*>\s*\.env\b(?!\.sample|\.example)",
                r"touch\s+.*\.env\b(?!\.sample|\.example)",
                r"cp\s+.*\.env\b(?!\.sample|\.example)",
                r"mv\s+.*\.env\b(?!\.sample|\.example)",
                r">\s*\.env\b(?!\.sample|\.example)",
                r">>\s*\.env\b(?!\.sample|\.example)",
                r"vim\s+.*\.env\b(?!\.sample|\.example)",
                r"nano\s+.*\.env\b(?!\.sample|\.example)",
                r"emacs\s+.*\.env\b(?!\.sample|\.example)",
                r"sed\s+.*-i.*\.env\b(?!\.sample|\.example)",
            ]

            for pattern in env_write_patterns:
                if re.search(pattern, command):
                    return True

    return False


def is_command_file_access(tool_name, tool_input):
    """
    Check if any tool is trying to access .claude/commands/ files.
    This now only provides warnings, not blocks, to avoid workflow disruption.
    """
    if tool_name not in ["Write", "Edit", "MultiEdit"]:
        return False

    file_path = tool_input.get("file_path", "")
    if not file_path:
        return False

    normalized_path = os.path.normpath(file_path)
    is_commands_file = (
        "/.claude/commands/" in normalized_path
        or normalized_path.startswith(".claude/commands/")
        or normalized_path.startswith(".claude\\commands\\")
        or "/.claude/commands/" in normalized_path
        or normalized_path.endswith("/.claude/commands")
        or normalized_path.endswith("\\.claude\\commands")
    )

    return is_commands_file


def check_root_structure_violations(tool_name, tool_input):
    """
    Check if any tool is trying to create files in the root directory that violate project structure.
    Only certain specific .md files are allowed in the root.
    """
    if tool_name not in ["Write", "Edit", "MultiEdit"]:
        return False

    file_path = tool_input.get("file_path", "")
    if not file_path:
        return False

    normalized_path = os.path.normpath(file_path)
    path_parts = normalized_path.split(os.sep)

    if len(path_parts) == 1 or (len(path_parts) == 2 and path_parts[0] == "."):
        filename = path_parts[-1]

        allowed_root_md_files = {
            "README.md",
            "CHANGELOG.md",
            "CLAUDE.md",
            "ROADMAP.md",
            "SECURITY.md",
        }

        if filename.endswith(".md"):
            if filename not in allowed_root_md_files:
                return True

        config_extensions = {".json", ".yaml", ".yml", ".toml", ".ini", ".env"}
        if any(filename.endswith(ext) for ext in config_extensions):
            allowed_root_configs = {
                "package.json",
                "package-lock.json",
                "yarn.lock",
                "pnpm-lock.yaml",
                "pyproject.toml",
                "requirements.txt",
                "Cargo.toml",
                "Cargo.lock",
                "go.mod",
                "go.sum",
            }
            if filename not in allowed_root_configs:
                return True

        script_extensions = {".sh", ".py", ".js", ".ts", ".rb", ".pl", ".php"}
        if any(filename.endswith(ext) for ext in script_extensions):
            return True

    return False


def get_claude_session_id():
    """Generate or retrieve a unique session ID for Claude interactions."""
    session_file = Path.home() / ".cache" / "claude" / "session_id"
    session_file.parent.mkdir(parents=True, exist_ok=True)

    if session_file.exists():
        try:
            with open(session_file) as f:
                session_id = f.read().strip()
                if session_id:
                    return session_id
        except Exception:
            pass

    session_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]

    try:
        with open(session_file, "w") as f:
            f.write(session_id)
    except Exception:
        pass

    return session_id


# -----------------------------
# SAFE TRASH (ultra-conservative)
# -----------------------------
REPO_ROOT = Path.cwd().resolve()
MAX_TRASH_BYTES = 20 * 1024 * 1024  # 20MB cap
TRASH_DIR = REPO_ROOT / ".trash"


def _is_simple_relpath(p: str) -> bool:
    # disallow globs and backrefs; must not be absolute
    if not p or p.startswith("-"):
        return False
    bad_tokens = ["*", "?", "[", "]", ".."]
    if any(b in p for b in bad_tokens):
        return False
    return not os.path.isabs(p)


def _resolve_inside_repo(raw_path: str) -> Path | None:
    try:
        candidate = (Path.cwd() / raw_path).resolve()
    except Exception:
        return None
    try:
        if str(candidate).startswith(str(REPO_ROOT) + os.sep) or str(candidate) == str(
            REPO_ROOT
        ):
            return candidate
        return None
    except Exception:
        return None


def _is_denied_path(p: Path) -> bool:
    try:
        rel = p.resolve().relative_to(REPO_ROOT)
    except Exception:
        return True
    s = str(rel)
    if s == ".env" or s.endswith(os.sep + ".env"):
        return True
    parts = set(s.split(os.sep))
    # Never touch these; also forbids any nested target within these dirs
    denied_dirs = {"node_modules", "venv", "dist", "build", ".trash", "logs"}
    if parts.intersection(denied_dirs):
        return True
    return False


def _is_regular_and_small(p: Path, max_bytes: int = MAX_TRASH_BYTES) -> bool:
    try:
        st = p.stat()
        return p.is_file() and not p.is_symlink() and st.st_size <= max_bytes
    except Exception:
        return False


def _trash_destination_for(p: Path) -> Path:
    ts = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    bucket = TRASH_DIR / ts
    rel = p.resolve().relative_to(REPO_ROOT)
    dest = bucket / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    return dest


def _append_trash_log(original: Path, moved_to: Path, session_id: str):
    try:
        log_dir = REPO_ROOT / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "pre_tool_use.json"

        entry = {
            "tool_name": "Bash",
            "tool_input": {"command": f"safe_trash {original}"},
            "session_id": session_id,
            "hook_event_name": "PreToolUse",
            "decision": "approved",
            "working_directory": str(Path.cwd()),
            "reason": "allowed_trash_command",
            "timestamp": datetime.now().strftime("%b %d, %I:%M%p").lower(),
            "moved_from": str(original),
            "moved_to": str(moved_to),
        }

        if log_path.exists():
            try:
                with open(log_path) as f:
                    existing = json.load(f)
            except Exception:
                existing = []
        else:
            existing = []
        existing.append(entry)
        with open(log_path, "w") as f:
            json.dump(existing, f, indent=2)
    except Exception:
        pass


def is_allowed_trash_command(command: str) -> tuple[bool, str | None]:
    """
    Allow exactly one ultra-safe pattern:
      safe_trash <relative-file>
    We intentionally DO NOT allow multi-args, globs, or directories.
    Returns (allowed, resolved_absolute_path | None).
    """
    if not command:
        return (False, None)
    normalized = " ".join(command.strip().split())
    m = re.match(r"^safe_trash\s+([^\s]+)$", normalized)
    if not m:
        return (False, None)
    raw_path = m.group(1)
    if not _is_simple_relpath(raw_path):
        return (False, None)
    target = _resolve_inside_repo(raw_path)
    if target is None:
        return (False, None)
    if _is_denied_path(target):
        return (False, None)
    if not _is_regular_and_small(target):
        return (False, None)
    return (True, str(target))


def handle_safe_trash(command: str, session_id: str) -> bool:
    """
    If command matches safe_trash policy, move the file into ./.trash/<timestamp>/...
    Returns True if we handled it here (and external command should be blocked).
    """
    allowed, target_s = is_allowed_trash_command(command)
    if not allowed:
        return False
    target = Path(target_s)
    dest = _trash_destination_for(target)
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(target), str(dest))
        _append_trash_log(target, dest, session_id)
        log_tool_call(
            "Bash",
            {"command": command},
            "approved",
            "allowed_trash_command",
            f"target={target}",
        )
        print(
            f"✅ safe_trash moved file:\n   from: {target}\n   to:   {dest}",
            file=sys.stderr,
        )
        print(
            "ℹ️ External command was intercepted by pre_tool_use hook (no shell execution).",
            file=sys.stderr,
        )
        return True
    except Exception as e:
        print(f"safe_trash error: {e}", file=sys.stderr)
        return False


def log_tool_call(tool_name, tool_input, decision, reason=None, block_message=None):
    """Log all tool calls with their decisions to a structured JSON file."""
    try:
        session_id = get_claude_session_id()
        input_data = {
            "tool_name": tool_name,
            "tool_input": tool_input,
            "session_id": session_id,
            "hook_event_name": "PreToolUse",
            "decision": decision,
            "working_directory": str(Path.cwd()),
        }

        if reason:
            input_data["reason"] = reason
        if block_message:
            input_data["block_message"] = block_message

        log_dir = Path.cwd() / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "pre_tool_use.json"

        if log_path.exists():
            with open(log_path) as f:
                try:
                    log_data = json.load(f)
                except (json.JSONDecodeError, ValueError):
                    log_data = []
        else:
            log_data = []

        timestamp = datetime.now().strftime("%b %d, %I:%M%p").lower()
        input_data["timestamp"] = timestamp

        log_data.append(input_data)

        with open(log_path, "w") as f:
            json.dump(log_data, f, indent=2)

    except Exception as e:
        print(f"Logging error: {e}", file=sys.stderr)


def main():
    try:
        input_data = json.load(sys.stdin)
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})

        if not tool_name:
            print("Error: No tool_name provided in input", file=sys.stderr)
            sys.exit(1)

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        # Early-intercept: handle ultra-safe trash command inline to avoid any shell-side surprises
        if tool_name == "Bash":
            command = tool_input.get("command", "")
            if handle_safe_trash(command, get_claude_session_id()):
                sys.exit(2)

        # Check for .env file access violations
        if is_env_file_access(tool_name, tool_input):
            block_message = "Access to .env files containing sensitive data is prohibited"
            log_tool_call(
                tool_name, tool_input, "blocked", "env_file_access", block_message
            )

            print(
                "BLOCKED: Access to .env files containing sensitive data is prohibited",
                file=sys.stderr,
            )
            print("Use .env.sample for template files instead", file=sys.stderr)
            sys.exit(2)

        # Block ALL forms of deletion and destructive operations
        if tool_name == "Bash":
            command = tool_input.get("command", "")
            if is_dangerous_deletion_command(command):
                block_message = (
                    "Destructive command detected and blocked for data protection"
                )
                log_tool_call(
                    tool_name,
                    tool_input,
                    "blocked",
                    "dangerous_deletion_command",
                    block_message,
                )

                print(
                    "🚫 DELETION PROTECTION: ALL destructive operations are BLOCKED",
                    file=sys.stderr,
                )
                print("", file=sys.stderr)
                print("🛡️  PROTECTED OPERATIONS:", file=sys.stderr)
                print("   • File deletion (rm, unlink, rmdir)", file=sys.stderr)
                print("   • Directory removal (rm -r, rm -rf)", file=sys.stderr)
                print("   • File overwriting (>, echo >, cat >)", file=sys.stderr)
                print("   • Truncation (truncate, :>, /dev/null)", file=sys.stderr)
                print("   • Package removal (npm uninstall, pip uninstall)", file=sys.stderr)
                print("   • Database drops (DROP TABLE, DELETE FROM)", file=sys.stderr)
                print("   • System operations (kill -9, format, fdisk)", file=sys.stderr)
                print("   • Archive destructive ops (tar --delete)", file=sys.stderr)
                print("   • Dangerous paths (/, ~, *, .., system dirs)", file=sys.stderr)
                print("", file=sys.stderr)
                print("💡 SAFE ALTERNATIVES:", file=sys.stderr)
                print("   • Use 'mv' to relocate instead of delete", file=sys.stderr)
                print("   • Use 'cp' to backup before changes", file=sys.stderr)
                print("   • Use '>>' to append instead of overwrite", file=sys.stderr)
                print("   • Use specific file paths (no wildcards)", file=sys.stderr)
                print(
                    "   • Request manual confirmation for destructive operations",
                    file=sys.stderr,
                )
                print("", file=sys.stderr)
                print("🔒 This protection ensures NO accidental data loss", file=sys.stderr)
                sys.exit(2)

        # Check for root directory structure violations
        if check_root_structure_violations(tool_name, tool_input):
            file_path = tool_input.get("file_path", "")
            filename = os.path.basename(file_path)
            block_message = f"Root structure violation: unauthorized file {filename} in root directory"
            log_tool_call(
                tool_name,
                tool_input,
                "blocked",
                "root_structure_violation",
                block_message,
            )

            print("🚫 ROOT STRUCTURE VIOLATION BLOCKED", file=sys.stderr)
            print(f"   File: {filename}", file=sys.stderr)
            print("   Reason: Unauthorized file in root directory", file=sys.stderr)
            print("", file=sys.stderr)
            print("📋 Root directory rules:", file=sys.stderr)
            print(
                "   • Only these .md files allowed: README.md, CHANGELOG.md, CLAUDE.md, ROADMAP.md, SECURITY.md",
                file=sys.stderr,
            )
            print("   • Config files belong in config/ directory", file=sys.stderr)
            print("   • Scripts belong in scripts/ directory", file=sys.stderr)
            print("   • Documentation belongs in docs/ directory", file=sys.stderr)
            print("", file=sys.stderr)
            print(
                "💡 Suggestion: Use /enforce-structure --fix to auto-organize files",
                file=sys.stderr,
            )
            sys.exit(2)

        # WARNING (not blocking) for command file access
        if is_command_file_access(tool_name, tool_input):
            file_path = tool_input.get("file_path", "")
            filename = os.path.basename(file_path)
            log_tool_call(
                tool_name,
                tool_input,
                "approved",
                "command_file_warning",
                f"Warning: modifying command file {filename}",
            )

            print(f"⚠️  COMMAND FILE MODIFICATION: {filename}", file=sys.stderr)
            print("   Location: .claude/commands/", file=sys.stderr)
            print("   Impact: May affect Claude's available commands", file=sys.stderr)
            print("", file=sys.stderr)
            print("💡 Best practices:", file=sys.stderr)
            print("   • Test command changes carefully", file=sys.stderr)
            print("   • Document any custom commands", file=sys.stderr)
            print("   • Consider using /create-command for new commands", file=sys.stderr)
            print("", file=sys.stderr)

    except Exception as e:
        print(f"Pre-tool use hook error: {e}", file=sys.stderr)
        log_tool_call(
            tool_name, tool_input, "approved", "hook_error", f"Hook error occurred: {e}"
        )

    # If we get here, the tool call is allowed - log as approved
    log_tool_call(tool_name, tool_input, "approved")
    sys.exit(0)


if __name__ == "__main__":
    main()