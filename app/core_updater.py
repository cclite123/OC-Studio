"""Inspect and sync the upstream OpCore-Simplify core submodule."""

from __future__ import annotations

import json
import re
import subprocess
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app import UPSTREAM_REPO
from app.config import AppSettings, get_core_dir


@dataclass
class CoreVersionInfo:
    local_sha: str
    local_date: str
    local_subject: str
    is_git_repo: bool
    remote_sha: Optional[str] = None
    remote_date: Optional[str] = None
    has_update: Optional[bool] = None
    error: Optional[str] = None

    @property
    def short_local_sha(self) -> str:
        return self.local_sha[:7] if self.local_sha else "未知"

    @property
    def short_remote_sha(self) -> str:
        return self.remote_sha[:7] if self.remote_sha else "未知"


def _run_git(args: list[str], cwd: Path, timeout: int = 20) -> tuple[int, str, str]:
    try:
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        proc = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            creationflags=creationflags,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except FileNotFoundError:
        return 127, "", "未检测到 Git，请先安装 Git 或从 Releases 下载最新打包版。"
    except subprocess.TimeoutExpired:
        return 124, "", "Git 命令执行超时。"
    except Exception as exc:
        return 1, "", str(exc)


def get_local_core_info() -> CoreVersionInfo:
    core_dir = get_core_dir()
    if not core_dir.exists():
        return CoreVersionInfo("", "", "", False, error="未找到 core 内核目录")

    code, out, _ = _run_git(["log", "-1", "--format=%H|%ci|%s"], core_dir)
    if code != 0 or "|" not in out:
        return CoreVersionInfo(
            local_sha="bundled",
            local_date="内置快照",
            local_subject="打包版内置内核",
            is_git_repo=False,
        )

    parts = out.split("|", 2)
    return CoreVersionInfo(
        local_sha=parts[0].strip(),
        local_date=parts[1].strip()[:19],
        local_subject=parts[2].strip(),
        is_git_repo=True,
    )


def _build_opener(settings: AppSettings) -> urllib.request.OpenerDirector:
    handlers = []
    proxy = settings.http_proxy.strip()
    if proxy:
        handlers.append(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
    return urllib.request.build_opener(*handlers)


def check_upstream_core_update(settings: AppSettings) -> CoreVersionInfo:
    info = get_local_core_info()
    api_url = f"https://api.github.com/repos/{UPSTREAM_REPO}/commits/main"
    opener = _build_opener(settings)
    req = urllib.request.Request(
        api_url,
        headers={"User-Agent": "OC-Studio/0.1", "Accept": "application/vnd.github+json"},
    )
    try:
        with opener.open(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        remote_sha = str(data.get("sha", "")).lower()
        commit_date = (
            data.get("commit", {})
            .get("committer", {})
            .get("date", "")
            .replace("T", " ")
            .replace("Z", "")
        )
        if re.fullmatch(r"[0-9a-f]{40}", remote_sha):
            info.remote_sha = remote_sha
            info.remote_date = commit_date
            if info.local_sha and info.local_sha != "bundled":
                info.has_update = info.local_sha.lower() != remote_sha
            else:
                info.has_update = None
            return info
        info.error = "无法解析上游提交记录"
    except Exception as exc:
        info.error = f"检查上游更新失败：{exc}"
    return info


def sync_upstream_core() -> tuple[bool, str]:
    core_dir = get_core_dir()
    info = get_local_core_info()
    if not info.is_git_repo:
        return False, "当前为免 Git 打包版本，无法直接 git 同步；请下载新版 OC-Studio 或通过源码版运行。"

    code, out, err = _run_git(["pull", "--ff-only", "origin", "main"], core_dir, timeout=60)
    if code != 0:
        # Fallback: fetch + reset --hard origin/main (since core/ is untouched)
        f_code, _, f_err = _run_git(["fetch", "origin", "main"], core_dir, timeout=60)
        if f_code != 0:
            return False, f"拉取上游失败：{f_err or err}"
        r_code, r_out, r_err = _run_git(["reset", "--hard", "origin/main"], core_dir, timeout=30)
        if r_code != 0:
            return False, f"更新内核失败：{r_err}"
        out = r_out

    new_info = get_local_core_info()
    return True, f"内核已同步至最新提交 {new_info.short_local_sha}（{new_info.local_date}）。重启应用后生效。\n{out}"
