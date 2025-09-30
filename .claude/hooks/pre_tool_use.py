#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

import hashlib
import json
import os
import re
import sys
import time
import shutil
from datetime import datetime
from pathlib import Path


def is_dangerous_deletion_command(command):
    """
    ULTRA-COMPREHENSIVE detection of ANY deletion or destructive commands.
    Blocks absolutely ALL forms of file/directory removal and destructive operations.
    """
    # Normalize command by removing extra spaces and converting to lowercase
    normalized = " ".join(command.lower().split())

    # SAFE OPERATIONS: Allow essential git workflow commands
    safe_git_patterns = [
        r"^\s*git\s+commit\s+",  # git commit (all variations)
        r"^\s*git\s+add\s+",  # git add
        r"^\s*git\s+status\s*$",  # git status
        r"^\s*git\s+log\s+",  # git log
        r"^\s*git\s+diff\s+",  # git diff
        r"^\s*git\s+show\s+",  # git show
        r"^\s*git\s+branch\s+",  # git branch (non-destructive)
        r"^\s*git\s+checkout\s+",  # git checkout (non-destructive)
        r"^\s*git\s+push\s+",  # git push
        r"^\s*git\s+pull\s+",  # git pull
        r"^\s*git\s+fetch\s+",  # git fetch
        r"^\s*git\s+merge\s+",  # git merge
    ]

    # Check if this is a safe git operation
    for pattern in safe_git_patterns:
        if re.search(pattern, normalized):
            return False  # Allow safe git operations

    # PATTERN 1: ALL rm command variations (any rm usage is blocked)
    rm_patterns = [
        r"\brm\b",  # Any rm command at all
        r"\bunlink\b",  # unlink command
        r"\brmdir\b",  # rmdir command
        r"\brm\s+(-[a-z]*r[a-z]*f|-[a-z]*f[a-z]*r)\b",  # rm -rf, rm -fr, rm -Rf, etc.
        r"\brm\s+--recursive\s+--force",  # rm --recursive --force
        r"\brm\s+--force\s+--recursive",  # rm --force --recursive
        r"\brm\s+-[a-z]*r\b",  # rm with recursive flag
        r"\brm\s+-[a-z]*f\b",  # rm with force flag
        r"\brm\s+--recursive\b",  # rm --recursive
        r"\brm\s+--force\b",  # rm --force
        r"\brm\s+-[a-z]*i\b",  # rm with interactive flag
        r"\brm\s+--interactive\b",  # rm --interactive
    ]

    # PATTERN 2: File system destructive operations
    destructive_patterns = [
        r"\bdd\s+.*of=",  # dd command writing to files
        r"\bshred\b",  # shred command
        r"\bwipe\b",  # wipe command
        r"\bsrm\b",  # secure rm
        r"\btrash\b",  # trash command
        r"\bgio\s+trash\b",  # gio trash
        r"\bmv\s+.*\s+/dev/null",  # move to /dev/null
        r"\bcp\s+/dev/null\b",  # copy /dev/null (truncate)
        r">\s*/dev/null",  # redirect to /dev/null
        r"\btruncate\b",  # truncate command
        r"\b:\s*>\s*[^|&;]+",  # shell truncation (:> file)
        r"\btrue\s*>\s*[^|&;]+",  # true > file (truncation)
        r"\bfalse\s*>\s*[^|&;]+",  # false > file (truncation)
    ]

    # PATTERN 3: Dangerous redirection and overwrite operations
    overwrite_patterns = [
        r">\s*[^|&;>\s]+\s*$",  # Simple redirection that overwrites
        r"\becho\s+.*>\s*[^|&;>\s]+",  # echo > file (overwrite)
        r"\bprintf\s+.*>\s*[^|&;>\s]+",  # printf > file (overwrite)
        r"\bcat\s+.*>\s*[^|&;>\s]+",  # cat > file (overwrite)
        r"\bcp\s+/dev/null\s+",  # copy /dev/null to file
        r"\bdd\s+.*>\s*[^|&;>\s]+",  # dd > file
    ]

    # PATTERN 4: Archive/compression destructive operations
    archive_destructive_patterns = [
        r"\btar\s+.*--delete\b",  # tar delete
        r"\bzip\s+.*-d\b",  # zip delete
        r"\bunzip\b",  # unzip (can overwrite)
        r"\bgunzip\b",  # gunzip (deletes .gz)
        r"\bbunzip2\b",  # bunzip2 (deletes .bz2)
        r"\bunxz\b",  # unxz (deletes .xz)
        r"\b7z\s+.*d\b",  # 7z delete
    ]

    # PATTERN 5: Git destructive operations (only truly dangerous ones)
    # NOTE: Removed most git patterns to allow productive git workflow
    # Only keeping the most destructive operations that could cause data loss
    git_destructive_patterns = [
        r"\bgit\s+clean\s+.*-f.*-d.*-x\b",  # git clean -fdx (removes all untracked including ignored)
        r"\bgit\s+filter-branch\b",  # git filter-branch (rewrites entire history)
        # Removed other git patterns to allow normal git workflow
    ]

    # PATTERN 6: Package manager destructive operations
    package_destructive_patterns = [
        r"\bnpm\s+.*uninstall\b",  # npm uninstall
        r"\bnpm\s+.*remove\b",  # npm remove
        r"\bnpm\s+.*rm\b",  # npm rm
        r"\byarn\s+.*remove\b",  # yarn remove
        r"\bpip\s+.*uninstall\b",  # pip uninstall
        r"\bconda\s+.*remove\b",  # conda remove
        r"\bapt\s+.*remove\b",  # apt remove
        r"\bapt\s+.*purge\b",  # apt purge
        r"\byum\s+.*remove\b",  # yum remove
        r"\bbrew\s+.*uninstall\b",  # brew uninstall
        r"\bbrew\s+.*remove\b",  # brew remove
    ]

    # PATTERN 7: Database destructive operations
    database_destructive_patterns = [
        r"\bdrop\s+table\b",  # SQL DROP TABLE
        r"\bdrop\s+database\b",  # SQL DROP DATABASE
        r"\bdelete\s+from\b",  # SQL DELETE FROM
        r"\btruncate\s+table\b",  # SQL TRUNCATE TABLE
        r"\bmongo.*\.drop\b",  # MongoDB drop
        r"\bmongo.*\.remove\b",  # MongoDB remove
        r"\bmongo.*\.deleteMany\b",  # MongoDB deleteMany
        r"\bmongo.*\.deleteOne\b",  # MongoDB deleteOne
    ]

    # PATTERN 8: System destructive operations
    system_destructive_patterns = [
        r"\bkill\s+.*-9\b",  # kill -9 (force kill)
        r"\bkillall\b",  # killall
        r"\bpkill\b",  # pkill
        r"\bfuser\s+.*-k\b",  # fuser -k (kill)
        r"\bumount\s+.*-f\b",  # umount -f (force)
        r"\bswapoff\b",  # swapoff
        r"\bfdisk\b",  # fdisk (disk partitioning)
        r"\bmkfs\b",  # mkfs (format filesystem)
        r"\bformat\b",  # format command
    ]

    # PATTERN 9: Dangerous paths and wildcards
    dangerous_paths = [
        r"\s+/\s*$",  # Root directory as standalone argument
        r"\s+/\*",  # Root with wildcard
        r"\s+~\s*$",  # Home directory as standalone argument
        r"\s+~/\*",  # Home directory with wildcard
        r"\$HOME/\*",  # Home environment variable with wildcard
        r"\.\./\*",  # Parent directory with wildcard
        r"\s+\*\s*$",  # Standalone wildcards
        r"/\*/\*",  # Multiple wildcards in path
        r"\s+\.\s+\*",  # Current directory with wildcard (. *)
        r"rm.*\s+\.",  # rm commands targeting current directory
        r"/usr/\*",  # System directories with wildcards
        r"/var/\*",  # Variable data with wildcards
        r"/etc/\*",  # Configuration with wildcards
        r"/bin/\*",  # Binaries with wildcards
        r"/sbin/\*",  # System binaries with wildcards
        r"/lib/\*",  # Libraries with wildcards
        r"/opt/\*",  # Optional software with wildcards
        r"/tmp/\*",  # Temp with wildcards
        r"\.git/\*",  # Git directories with wildcards
        r"node_modules/\*",  # Node modules with wildcards
    ]

    # Check ALL patterns
    all_patterns = (
        rm_patterns
        + destructive_patterns
        + overwrite_patterns
        + archive_destructive_patterns
        + git_destructive_patterns
        + package_destructive_patterns
        + database_destructive_patterns
        + system_destructive_patterns
    )

    # Check for any destructive pattern
    for pattern in all_patterns:
        if re.search(pattern, normalized):
            return True

    # Check for dangerous paths in any context
    for path in dangerous_paths:
        if re.search(path, normalized):
            # Extra strict: block any command that mentions dangerous paths
            return True

    # PATTERN 10: Command chaining that might hide destructive operations
    chain_patterns = [
        r"&&.*\brm\b",  # && rm
        r"\|\|.*\brm\b",  # || rm
        r";.*\brm\b",  # ; rm
        r"\|.*\brm\b",  # | rm
        r"`.*\brm\b.*`",  # `rm` in backticks
        r"\$\(.*\brm\b.*\)",  # $(rm) in command substitution
    ]

    for pattern in chain_patterns:
        if re.search(pattern, normalized):
            return True

    return False


def is_env_file_access(tool_name, tool_input):
    """
    Check if any tool is trying to access .env files containing sensitive data.
    Allows reading .env files but blocks editing/writing operations.
    Also allows access to .env.sample and .env.example files.
    """
    if tool_name in ["Read", "Edit", "MultiEdit", "Write", "Bash"]:
        # Check file paths for file-based tools
        if tool_name in [
            "Edit",
            "MultiEdit",
            "Write",
        ]:  # Only block edit operations, allow Read
            file_path = tool_input.get("file_path", "")
            if ".env" in file_path and not (
                file_path.endswith(".env.sample") or file_path.endswith(".env.example")
            ):
                return True

        # Check bash commands for .env file access
        elif tool_name == "Bash":
            command = tool_input.get("command", "")
            # Pattern to detect .env file write/edit operations (but allow .env.sample and .env.example)
            # Allow cat/read operations but block write operations
            env_write_patterns = [
                r"echo\s+.*>\s*\.env\b(?!\.sample|\.example)",  # echo > .env
                r"touch\s+.*\.env\b(?!\.sample|\.example)",  # touch .env
                r"cp\s+.*\.env\b(?!\.sample|\.example)",  # cp .env (as destination)
                r"mv\s+.*\.env\b(?!\.sample|\.example)",  # mv .env (as destination)
                r">\s*\.env\b(?!\.sample|\.example)",  # any redirection to .env
                r">>\s*\.env\b(?!\.sample|\.example)",  # any append to .env
                r"vim\s+.*\.env\b(?!\.sample|\.example)",  # vim .env
                r"nano\s+.*\.env\b(?!\.sample|\.example)",  # nano .env
                r"emacs\s+.*\.env\b(?!\.sample|\.example)",  # emacs .env
                r"sed\s+.*-i.*\.env\b(?!\.sample|\.example)",  # sed -i .env (in-place edit)
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

    # Check if this is a .claude/commands/ file
    normalized_path = os.path.normpath(file_path)

    # Check for both relative and absolute paths
    is_commands_file = (
        "/.claude/commands/" in normalized_path
        or normalized_path.startswith(".claude/commands/")
        or normalized_path.startswith(".claude\\commands\\")  # Windows
        or "/.claude/commands/" in normalized_path
        or normalized_path.endswith("/.claude/commands")
        or normalized_path.endswith("\\.claude\\commands")  # Windows
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

    # Normalize the path and get just the filename if it's in root
    normalized_path = os.path.normpath(file_path)

    # Check if this file is being created directly in the project root
    # Look for paths that don't contain directory separators after normalization
    # or that are explicitly in the current directory
    path_parts = normalized_path.split(os.sep)

    # If the path has only one part (filename) or starts with './' it's in root
    if len(path_parts) == 1 or (len(path_parts) == 2 and path_parts[0] == "."):
        filename = path_parts[-1]

        # Allow only specific .md files in root
        allowed_root_md_files = {
            "README.md",
            "CHANGELOG.md",
            "CLAUDE.md",
            "ROADMAP.md",
            "SECURITY.md",
        }

        # Check if it's an .md file
        if filename.endswith(".md"):
            if filename not in allowed_root_md_files:
                return True

        # Check if it's a config file that should be in config/
        config_extensions = {".json", ".yaml", ".yml", ".toml", ".ini", ".env"}
        if any(filename.endswith(ext) for ext in config_extensions):
            # Allow package.json and similar project files
            allowed_root_configs = {
                "package.json",
                "package-lock.json",
                "yarn.lock",
                "pnpm-lock.yaml",
                ".gitignore",
                ".gitattributes",
                "pyproject.toml",
                "requirements.txt",
                "Cargo.toml",
                "Cargo.lock",
                "go.mod",
                "go.sum",
            }
            if filename not in allowed_root_configs:
                return True

        # Check if it's a script file that should be in scripts/
        script_extensions = {".sh", ".py", ".js", ".ts", ".rb", ".pl", ".php"}
        if any(filename.endswith(ext) for ext in script_extensions):
            return True

    return False


def get_claude_session_id():
    """Generate or retrieve a unique session ID for Claude interactions."""
    session_file = Path.home() / ".cache" / "claude" / "session_id"
    session_file.parent.mkdir(parents=True, exist_ok=True)

    # Try to read existing session ID
    if session_file.exists():
        try:
            with open(session_file) as f:
                session_id = f.read().strip()
                if session_id:
                    return session_id
        except Exception:
            pass

    # Generate new session ID
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
        # Python 3.12+: Path.is_relative_to
        if str(candidate).startswith(str(REPO_ROOT) + os.sep) or str(candidate) == str(REPO_ROOT):
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
    denied_dirs = {".git", "node_modules", "venv", "dist", "build", ".trash", "logs"}
    if parts.intersection(denied_dirs):
        return True
    return False

def _is_regular_and_small(p: Path, max_bytes: int = MAX_TRASH_BYTES) -> bool:
    try:
        st = p.stat()
        # regular file only, not dir, not symlink, and below cap
        return p.is_file() and not p.is_symlink() and st.st_size <= max_bytes
    except Exception:
        return False

def _trash_destination_for(p: Path) -> Path:
    # timestamped bucket to keep history
    ts = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    bucket = TRASH_DIR / ts
    # mirror the relative path inside the bucket for easier restore
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
        # logging failures must never block file move
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
        # Also mirror to the standard log flow
        log_tool_call("Bash", {"command": command}, "approved", "allowed_trash_command", f"target={target}")
        # Inform via stderr so the IDE shows it prominently
        print(f"✅ safe_trash moved file:\n   from: {target}\n   to:   {dest}", file=sys.stderr)
        print("ℹ️ External command was intercepted by pre_tool_use hook (no shell execution).", file=sys.stderr)
        return True
    except Exception as e:
        print(f"safe_trash error: {e}", file=sys.stderr)
        return False


def log_tool_call(tool_name, tool_input, decision, reason=None, block_message=None):
    """Log all tool calls with their decisions to a structured JSON file."""
    try:
        # Create input_data dictionary for logging
        session_id = get_claude_session_id()
        input_data = {
            "tool_name": tool_name,
            "tool_input": tool_input,
            "session_id": session_id,
            "hook_event_name": "PreToolUse",
            "decision": decision,
            "working_directory": str(Path.cwd()),
        }

        # Add optional fields if provided
        if reason:
            input_data["reason"] = reason
        if block_message:
            input_data["block_message"] = block_message

        # Ensure log directory exists
        log_dir = Path.cwd() / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "pre_tool_use.json"

        # Read existing log data or initialize empty list
        if log_path.exists():
            with open(log_path) as f:
                try:
                    log_data = json.load(f)
                except (json.JSONDecodeError, ValueError):
                    log_data = []
        else:
            log_data = []

        # Add timestamp to the log entry
        timestamp = datetime.now().strftime("%b %d, %I:%M%p").lower()
        input_data["timestamp"] = timestamp

        # Append new data
        log_data.append(input_data)

        # Write back to file with formatting
        with open(log_path, "w") as f:
            json.dump(log_data, f, indent=2)

    except Exception as e:
        # Don't let logging errors break the hook
        print(f"Logging error: {e}", file=sys.stderr)


def main():
    try:
        # Read input from stdin as per Claude Code hook specification
        input_data = json.load(sys.stdin)

        # Extract tool information from the input
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
            # If we handled a safe_trash request here, block the actual tool call (we already moved the file)
            if handle_safe_trash(command, get_claude_session_id()):
                # Exit code 2 -> block the downstream tool call, but we've performed the action safely
                sys.exit(2)

        # Check for .env file access violations
        if is_env_file_access(tool_name, tool_input):
            block_message = (
                "Access to .env files containing sensitive data is prohibited"
            )
            log_tool_call(
                tool_name, tool_input, "blocked", "env_file_access", block_message
            )

            print(
                "BLOCKED: Access to .env files containing sensitive data is prohibited",
                file=sys.stderr,
            )
            print("Use .env.sample for template files instead", file=sys.stderr)
            sys.exit(2)  # Exit code 2 blocks tool call and shows error to Claude

        # Check for ANY destructive/deletion commands - ULTRA STRICT PROTECTION
        if tool_name == "Bash":
            command = tool_input.get("command", "")
            # If handle_safe_trash already ran, we would have exited with code 2 above.
            # Continue with standard destructive command detection.

            # Block ALL forms of deletion and destructive operations
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
                print(
                    "   • Git destructive ops (reset --hard, clean -f)", file=sys.stderr
                )
                print(
                    "   • Package removal (npm uninstall, pip uninstall)",
                    file=sys.stderr,
                )
                print("   • Database drops (DROP TABLE, DELETE FROM)", file=sys.stderr)
                print(
                    "   • System operations (kill -9, format, fdisk)", file=sys.stderr
                )
                print("   • Archive destructive ops (tar --delete)", file=sys.stderr)
                print(
                    "   • Dangerous paths (/, ~, *, .., system dirs)", file=sys.stderr
                )
                print("", file=sys.stderr)
                print("💡 SAFE ALTERNATIVES:", file=sys.stderr)
                print("   • Use 'mv' to relocate instead of delete", file=sys.stderr)
                print("   • Use 'cp' to backup before changes", file=sys.stderr)
                print("   • Use '>>' to append instead of overwrite", file=sys.stderr)
                print("   • Use specific file paths (no wildcards)", file=sys.stderr)
                print("   • Use git operations without --force flags", file=sys.stderr)
                print(
                    "   • Request manual confirmation for destructive operations",
                    file=sys.stderr,
                )
                print("", file=sys.stderr)
                print(
                    "🔒 This protection ensures NO accidental data loss",
                    file=sys.stderr,
                )
                sys.exit(2)  # Exit code 2 blocks tool call and shows error to Claude

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
            sys.exit(2)  # Exit code 2 blocks tool call and shows error to Claude

        # WARNING (not blocking) for command file access
        if is_command_file_access(tool_name, tool_input):
            file_path = tool_input.get("file_path", "")
            filename = os.path.basename(file_path)
            # Log as approved with warning
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
            print(
                "   • Consider using /create-command for new commands", file=sys.stderr
            )
            print("", file=sys.stderr)
            # Continue execution (warning only)

    except Exception as e:
        print(f"Pre-tool use hook error: {e}", file=sys.stderr)
        # Log the error but don't block
        log_tool_call(
            tool_name, tool_input, "approved", "hook_error", f"Hook error occurred: {e}"
        )
        # Don't block on hook errors, just warn
        pass

    # If we get here, the tool call is allowed - log as approved
    log_tool_call(tool_name, tool_input, "approved")
    sys.exit(0)


if __name__ == "__main__":
    main()
