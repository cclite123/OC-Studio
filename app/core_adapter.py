"""Zero-modification adapter layer over the upstream lzhoang2801/OpCore-Simplify core."""

from __future__ import annotations

import copy
import hashlib
import io
import os
import re
import shutil
import socket
import ssl
import sys
import threading
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.config import AppSettings, get_app_root, get_core_dir

ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]")


class CoreAbortError(RuntimeError):
    """Raised instead of sys.exit() when upstream core aborts due to incompatible hardware."""


@dataclass
class PromptRequest:
    """Interactive choice requested by upstream core during a workflow step."""

    prompt: str
    context_lines: List[str]
    kind: str  # "yes_no" | "choice" | "text"
    options: List[Tuple[str, str]] = field(default_factory=list)  # (return_value, label)
    default_value: str = ""


class CoreEventBridge:
    """Thread-safe callback hub bridging core stdout/progress/prompts to the Qt UI."""

    def __init__(self) -> None:
        self.on_log: Optional[Callable[[str], None]] = None
        self.on_build_progress: Optional[Callable[[str, List[str], int, bool], None]] = None
        self.on_download_progress: Optional[Callable[[int, str, float, float], None]] = None
        self.on_prompt: Optional[Callable[[PromptRequest], str]] = None
        self._lock = threading.Lock()
        self._recent_lines: List[str] = []
        self.notices: List[str] = []

    def clear_recent(self) -> None:
        with self._lock:
            self._recent_lines.clear()

    def clear_notices(self) -> None:
        with self._lock:
            self.notices.clear()

    def push_log(self, text: str) -> None:
        clean = ANSI_RE.sub("", text)
        for line in clean.splitlines():
            stripped = line.rstrip()
            if not stripped:
                continue
            with self._lock:
                self._recent_lines.append(stripped)
                if len(self._recent_lines) > 80:
                    self._recent_lines = self._recent_lines[-80:]
            if self.on_log:
                self.on_log(stripped)

    def get_recent_lines(self, limit: int = 40) -> List[str]:
        with self._lock:
            return list(self._recent_lines[-limit:])

    def emit_build_progress(self, title: str, steps: List[str], idx: int, done: bool) -> None:
        if self.on_build_progress:
            self.on_build_progress(title, steps, idx, done)

    def emit_download_progress(
        self, percent: int, speed_str: str, downloaded_mb: float, total_mb: float
    ) -> None:
        if self.on_download_progress:
            self.on_download_progress(percent, speed_str, downloaded_mb, total_mb)

    def handle_request_input(self, prompt: str) -> str:
        clean_prompt = ANSI_RE.sub("", prompt or "").strip()
        recent = self.get_recent_lines(35)

        # 1) Pure pause prompt ("Press Enter to continue..." or empty) -> do not block GUI
        lower = clean_prompt.lower()
        if not clean_prompt or "press enter" in lower:
            # Capture important experimental notices (e.g. WhateverXe / NullMoth) for display
            important_block = [
                ln for ln in recent[-12:] if any(k in ln for k in ("Important:", "WhateverXe", "NullMoth", "github.com"))
            ]
            if important_block:
                notice = "\n".join(important_block)
                with self._lock:
                    if notice not in self.notices:
                        self.notices.append(notice)
            return ""

        # 2) Interactive yes/no or numbered selection prompt -> delegate to UI dialog
        req = self._parse_prompt(clean_prompt, recent)
        if self.on_prompt:
            return self.on_prompt(req)
        return req.default_value

    def _parse_prompt(self, prompt: str, recent: List[str]) -> PromptRequest:
        lower = prompt.lower()

        # Yes / No questions (UEFI mode, force load kexts, OCLP, etc.)
        if "(yes/no)" in lower:
            default = "yes" if "(Yes/no)" in prompt else "no"
            return PromptRequest(
                prompt=prompt,
                context_lines=recent[-20:],
                kind="yes_no",
                options=[("yes", "是 (Yes)"), ("no", "否 (No)")],
                default_value=default,
            )

        # Numbered menu options parsed from recent stdout lines like "1. Something"
        options: List[Tuple[str, str]] = []
        num_re = re.compile(r"^\s*(\d+)\.\s+(.+)$")
        # Scan from the last header/section marker downwards to avoid stale menu items
        start_idx = 0
        for i in range(len(recent) - 1, -1, -1):
            if recent[i].startswith("***") or "Please select" in recent[i] or "available kext options" in recent[i]:
                start_idx = i
                break
        for ln in recent[start_idx:]:
            m = num_re.match(ln)
            if m:
                options.append((m.group(1), f"{m.group(1)}. {m.group(2).strip()}"))

        # Detect default value from "(default: ...)"
        default_val = "1"
        m_def = re.search(r"\(default:\s*([^)]+)\)", prompt, re.IGNORECASE)
        if m_def and options:
            def_hint = m_def.group(1).strip().lower()
            for val, label in options:
                if def_hint in label.lower():
                    default_val = val
                    break

        if options:
            return PromptRequest(
                prompt=prompt,
                context_lines=recent[start_idx:],
                kind="choice",
                options=options,
                default_value=default_val,
            )

        return PromptRequest(
            prompt=prompt,
            context_lines=recent[-15:],
            kind="text",
            default_value="",
        )


class _StdoutRedirector(io.TextIOBase):
    """Capture stdout from core scripts and forward lines to CoreEventBridge."""

    def __init__(self, bridge: CoreEventBridge, original: Any) -> None:
        self._bridge = bridge
        self._original = original
        self._buffer = ""

    def write(self, s: str) -> int:
        if not s:
            return 0
        self._buffer += s
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            self._bridge.push_log(line)
        return len(s)

    def flush(self) -> None:
        if self._buffer.strip():
            self._bridge.push_log(self._buffer)
            self._buffer = ""

    def isatty(self) -> bool:
        return False


def _should_use_mirror(url: str) -> bool:
    """Only rewrite downloadable file/raw URLs, never GitHub HTML scraping pages."""
    if url.startswith("https://raw.githubusercontent.com/"):
        return True
    if url.startswith("https://github.com/"):
        return any(
            segment in url
            for segment in ("/releases/download/", "/archive/", "/raw/")
        )
    return False


class CoreAdapter:
    """Non-invasive runtime bridge to upstream OpCore-Simplify."""

    _hooks_installed = False
    _active_bridge: Optional[CoreEventBridge] = None
    _active_settings: Optional[AppSettings] = None

    def __init__(self, settings: AppSettings, bridge: CoreEventBridge) -> None:
        self.settings = settings
        self.bridge = bridge
        self._ensure_core_loaded()

        CoreAdapter._active_bridge = bridge
        CoreAdapter._active_settings = settings

        # Instantiate upstream modules
        from Scripts import (
            acpi_guru,
            compatibility_checker,
            config_prodigy,
            gathering_files,
            hardware_customizer,
            kext_maestro,
            report_validator,
            run,
            smbios,
            utils,
        )
        from Scripts.datasets import chipset_data, codec_layouts, kext_data, mac_model_data, os_data

        self.os_data = os_data
        self.kext_data = kext_data
        self.mac_model_data = mac_model_data
        self.chipset_data = chipset_data
        self.codec_layouts = codec_layouts

        self.u = utils.Utils("OC-Studio")
        self.u.clean_temporary_dir()
        self.ac = acpi_guru.ACPIGuru()
        self.c = compatibility_checker.CompatibilityChecker()
        self.co = config_prodigy.ConfigProdigy()
        self.o = gathering_files.gatheringFiles()
        self.h = hardware_customizer.HardwareCustomizer()
        self.k = kext_maestro.KextMaestro()
        self.s = smbios.SMBIOS()
        self.v = report_validator.ReportValidator()
        self.r = run.Run()

        # Bind non-invasive instance hook so pre-selected audio layout ID is used during build
        self._orig_select_audio_layout = self.co.select_audio_codec_layout
        self.co.select_audio_codec_layout = self._patched_select_audio_codec_layout

        # Keep downloaded caches outside core/ so upstream submodule stays clean
        ock_dir = str(get_app_root() / "OCK_Files")
        self.o.ock_files_dir = ock_dir
        self.o.download_history_file = os.path.join(ock_dir, "history.json")
        self.k.ock_files_dir = ock_dir
        self.s.g.ock_files_dir = ock_dir
        self.s.g.download_history_file = os.path.join(ock_dir, "history.json")

        # Workflow state
        self.report_path: Optional[str] = None
        self.acpi_dir: Optional[str] = None
        self.org_hardware_report: Optional[Dict[str, Any]] = None
        self.hardware_report: Optional[Dict[str, Any]] = None
        self.customized_hardware: Optional[Dict[str, Any]] = None
        self.disabled_devices: Dict[str, Any] = {}
        self.native_macos_version: Optional[Tuple[str, str]] = None
        self.ocl_patched_macos_version: Optional[Tuple[str, str]] = None
        self.suggested_macos_version: Optional[str] = None
        self.macos_version: Optional[str] = None
        self.needs_oclp: bool = False
        self.smbios_model: Optional[str] = None
        self.selected_audio_layout_id: Optional[int] = None
        self.last_original_config: Optional[Dict[str, Any]] = None
        self.last_generated_config: Optional[Dict[str, Any]] = None
        self.last_validation_warnings: List[str] = []

    def update_settings(self, settings: AppSettings) -> None:
        self.settings = settings
        CoreAdapter._active_settings = settings

    @property
    def result_dir(self) -> str:
        return str(self.settings.get_effective_output_dir())

    @classmethod
    def _ensure_core_loaded(cls) -> None:
        core_dir = str(get_core_dir())
        if not os.path.isdir(core_dir):
            raise FileNotFoundError(
                f"未找到官方内核目录：{core_dir}\n请先运行 git submodule update --init --recursive"
            )
        if core_dir not in sys.path:
            sys.path.insert(0, core_dir)

        if not cls._hooks_installed:
            cls._install_runtime_hooks()
            cls._hooks_installed = True

    @classmethod
    def _install_runtime_hooks(cls) -> None:
        from Scripts import resource_fetcher, utils

        # --- Hook Utils ---
        def _hook_head(self_u: Any, text: Any = None, width: int = 68, resize: bool = True) -> None:
            bridge = cls._active_bridge
            if bridge and text:
                bridge.push_log(f"── {text} ──")

        def _hook_adjust_window_size(self_u: Any, content: str = "") -> None:
            return

        def _hook_progress_bar(
            self_u: Any, title: str, steps: List[str], current_step_index: int, done: bool = False
        ) -> None:
            bridge = cls._active_bridge
            if bridge:
                bridge.emit_build_progress(title, steps, current_step_index, done)
                if done:
                    bridge.push_log(f"[完成] {title}")
                elif 0 <= current_step_index < len(steps):
                    bridge.push_log(f"[步骤 {current_step_index + 1}/{len(steps)}] {steps[current_step_index]}...")

        def _hook_request_input(self_u: Any, prompt: str = "Press Enter to continue...") -> str:
            bridge = cls._active_bridge
            if bridge:
                return bridge.handle_request_input(prompt)
            return ""

        def _hook_exit_program(self_u: Any) -> None:
            bridge = cls._active_bridge
            recent = bridge.get_recent_lines(12) if bridge else []
            detail = "\n".join(recent) if recent else "硬件不满足 macOS 安装要求，流程已中止。"
            raise CoreAbortError(detail)

        utils.Utils.head = _hook_head
        utils.Utils.adjust_window_size = _hook_adjust_window_size
        utils.Utils.progress_bar = _hook_progress_bar
        utils.Utils.request_input = _hook_request_input
        utils.Utils.exit_program = _hook_exit_program

        # --- Hook ResourceFetcher (mirror + proxy + live download progress) ---
        def _open_url(
            self_rf: Any, url: str, timeout: int = 15, proxy: str = ""
        ) -> Any:
            headers = dict(self_rf.request_headers)
            headers["Accept-Encoding"] = "gzip, deflate"
            req = urllib.request.Request(url, headers=headers)
            ssl_ctx = resource_fetcher.get_ssl_context()
            handlers: List[Any] = [urllib.request.HTTPSHandler(context=ssl_ctx)]
            if proxy:
                handlers.append(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
            opener = urllib.request.build_opener(*handlers)
            return opener.open(req, timeout=timeout)

        def _hook_make_request(self_rf: Any, resource_url: str, timeout: int = 15) -> Any:
            settings = cls._active_settings
            bridge = cls._active_bridge
            proxy = settings.http_proxy.strip() if settings else ""
            mirror = settings.get_active_mirror_prefix() if settings else ""

            candidates: List[Tuple[str, bool]] = []
            if mirror and _should_use_mirror(resource_url):
                candidates.append((mirror + resource_url, True))
            candidates.append((resource_url, False))

            for url, is_mirror in candidates:
                try:
                    if is_mirror and bridge:
                        bridge.push_log(f"使用加速镜像拉取: {url}")
                    return _open_url(self_rf, url, timeout=timeout, proxy=proxy)
                except (socket.timeout, ssl.SSLError, urllib.error.URLError, socket.gaierror, Exception) as exc:
                    if is_mirror and bridge:
                        bridge.push_log(f"镜像访问失败 ({exc})，自动回退直连...")
                    elif bridge:
                        bridge.push_log(f"请求失败 ({url}): {exc}")
            return None

        def _hook_download_with_progress(self_rf: Any, response: Any, local_file: Any) -> str:
            sha256 = hashlib.sha256()
            bridge = cls._active_bridge
            total_header = response.getheader("Content-Length")
            total_size = int(total_header) if total_header and total_header.isdigit() else 0
            bytes_downloaded = 0
            last_time = time.monotonic()
            last_emit = last_time
            last_bytes = 0
            speeds: List[float] = []
            speed_str = "-- KB/s"

            while True:
                chunk = response.read(self_rf.buffer_size)
                if not chunk:
                    break
                local_file.write(chunk)
                sha256.update(chunk)
                bytes_downloaded += len(chunk)

                now = time.monotonic()
                if now - last_emit < 0.15 and bytes_downloaded != total_size:
                    continue
                last_emit = now

                dt = now - last_time
                if dt > 0.35:
                    speeds.append((bytes_downloaded - last_bytes) / dt)
                    if len(speeds) > 5:
                        speeds.pop(0)
                    avg = sum(speeds) / len(speeds)
                    if avg < 1024 * 1024:
                        speed_str = f"{avg / 1024:.1f} KB/s"
                    else:
                        speed_str = f"{avg / (1024 * 1024):.2f} MB/s"
                    last_time = now
                    last_bytes = bytes_downloaded

                if bridge:
                    percent = int(bytes_downloaded * 100 / total_size) if total_size else -1
                    bridge.emit_download_progress(
                        percent,
                        speed_str,
                        bytes_downloaded / (1024 * 1024),
                        total_size / (1024 * 1024) if total_size else 0.0,
                    )

            if bridge:
                bridge.emit_download_progress(
                    100,
                    speed_str,
                    bytes_downloaded / (1024 * 1024),
                    total_size / (1024 * 1024) if total_size else bytes_downloaded / (1024 * 1024),
                )
            return sha256.hexdigest()

        resource_fetcher.ResourceFetcher._make_request = _hook_make_request
        resource_fetcher.ResourceFetcher._download_with_progress = _hook_download_with_progress

    @contextmanager
    def _capture_stdout(self):
        old_stdout = sys.stdout
        redirector = _StdoutRedirector(self.bridge, old_stdout)
        sys.stdout = redirector
        try:
            yield
        finally:
            redirector.flush()
            sys.stdout = old_stdout

    # ------------------------------------------------------------------
    # Step 1: Hardware Report & ACPI Tables
    # ------------------------------------------------------------------
    def export_hardware_report_windows(self) -> Dict[str, Any]:
        """Run Hardware-Sniffer-CLI.exe on Windows, then validate & check compatibility."""
        if os.name != "nt":
            raise RuntimeError("一键硬件采集仅支持 Windows 系统，请从 Windows 导出 Report.json 后导入。")

        self.bridge.clear_recent()
        self.bridge.clear_notices()
        with self._capture_stdout():
            hardware_sniffer = self.o.gather_hardware_sniffer()
            if not hardware_sniffer:
                raise RuntimeError("无法获取 Hardware-Sniffer-CLI.exe，请检查网络或在设置中开启 GitHub 镜像加速。")

            report_dir = str(get_app_root() / "SysReport")
            self.bridge.push_log(f"正在采集本机硬件与 ACPI 表到：{report_dir}")
            output = self.r.run({"args": [hardware_sniffer, "-e", "-o", report_dir]})
            if output[-1] != 0:
                code_map = {
                    3: "采集硬件信息失败",
                    4: "生成硬件报告失败",
                    5: "导出 ACPI 表失败",
                }
                msg = code_map.get(output[-1], f"未知错误（退出码 {output[-1]}）")
                raise RuntimeError(f"硬件报告导出失败：{msg}。建议以管理员身份运行 OC-Studio 再试。")

            report_path = os.path.join(report_dir, "Report.json")
            acpi_dir = os.path.join(report_dir, "ACPI")
        return self.load_hardware_report(report_path, acpi_dir)

    def load_hardware_report(self, input_path: str, acpi_dir: Optional[str] = None) -> Dict[str, Any]:
        """Validate Report.json (or SysReport folder), auto-load ACPI if present, and run compatibility check."""
        self.bridge.clear_recent()
        self.bridge.clear_notices()

        normalized = self.u.normalize_path(input_path)
        if os.path.isdir(normalized):
            candidate = os.path.join(normalized, "Report.json")
            if os.path.isfile(candidate):
                normalized = candidate
            else:
                raise FileNotFoundError(f"目录中未找到 Report.json：{normalized}")

        with self._capture_stdout():
            is_valid, errors, warnings, data = self.v.validate_report(normalized)
            self.last_validation_warnings = list(warnings or [])
            if not is_valid or errors:
                err_text = "\n".join(f"• {e}" for e in errors)
                raise ValueError(f"硬件报告格式校验未通过：\n{err_text}")

            # Reset ACPI tables and try auto-loading sibling ACPI folder
            self.ac.dsdt = None
            self.ac.acpi.acpi_tables = {}
            self.acpi_dir = None

            auto_acpi = acpi_dir
            if not auto_acpi:
                sibling_acpi = os.path.join(os.path.dirname(normalized), "ACPI")
                if os.path.isdir(sibling_acpi):
                    auto_acpi = sibling_acpi

            if auto_acpi and os.path.exists(auto_acpi):
                self.ac.read_acpi_tables(auto_acpi)
                if self.has_loaded_dsdt():
                    self.acpi_dir = auto_acpi

            # Run compatibility check
            self.org_hardware_report = copy.deepcopy(data)
            (
                checked_report,
                native_range,
                oclp_range,
                suggested_version,
            ) = self.c.check_compatibility(data)

            self.report_path = normalized
            self.hardware_report = checked_report
            self.native_macos_version = native_range
            self.ocl_patched_macos_version = oclp_range
            self.suggested_macos_version = suggested_version

            # Automatically apply the suggested macOS version so all subsequent tabs are ready
            self._apply_version_internal(suggested_version)

        return self.get_state_snapshot()

    def has_loaded_dsdt(self) -> bool:
        """Non-interactive check for whether a valid DSDT table is currently loaded."""
        if not self.ac.acpi.acpi_tables:
            self.ac.dsdt = None
            return False
        self.ac.dsdt = self.ac.acpi.get_dsdt_or_only()
        return bool(self.ac.dsdt)

    def load_acpi_tables(self, path: str) -> bool:
        """Manually load an ACPI folder or DSDT.aml file."""
        self.bridge.clear_recent()
        normalized = self.u.normalize_path(path)
        with self._capture_stdout():
            self.ac.read_acpi_tables(normalized)
            ok = self.has_loaded_dsdt()
            if ok:
                self.acpi_dir = normalized
                if self.customized_hardware is not None:
                    self.ac.select_acpi_patches(self.customized_hardware, self.disabled_devices)
                    self.s.smbios_specific_options(
                        self.customized_hardware,
                        self.smbios_model,
                        self.macos_version,
                        self.ac.patches,
                        self.k,
                    )
            return ok

    # ------------------------------------------------------------------
    # Step 2: Select macOS Version & Recompute Hardware / ACPI / Kexts
    # ------------------------------------------------------------------
    def _apply_version_internal(self, target_darwin: str) -> None:
        self.macos_version = target_darwin
        (
            self.customized_hardware,
            self.disabled_devices,
            self.needs_oclp,
        ) = self.h.hardware_customization(copy.deepcopy(self.hardware_report), target_darwin)
        self.smbios_model = self.s.select_smbios_model(self.customized_hardware, target_darwin)
        self.ac.select_acpi_patches(self.customized_hardware, self.disabled_devices)
        self.needs_oclp = self.k.select_required_kexts(
            self.customized_hardware, target_darwin, self.needs_oclp, self.ac.patches
        )
        self.s.smbios_specific_options(
            self.customized_hardware,
            self.smbios_model,
            target_darwin,
            self.ac.patches,
            self.k,
        )
        self._init_default_audio_layout()

    def _find_audio_codec_and_controller(
        self, hardware_report: Optional[Dict[str, Any]]
    ) -> Tuple[Optional[str], Optional[str], Optional[Dict[str, Any]]]:
        if not hardware_report:
            return None, None, None
        for codec_name, codec_props in hardware_report.get("Sound", {}).items():
            cid = codec_props.get("Device ID")
            if cid in self.codec_layouts.data:
                controller_props = None
                ctrl_id = codec_props.get("Controller Device ID")
                if ctrl_id:
                    for dev_props in (hardware_report.get("System Devices") or {}).values():
                        if dev_props.get("Device ID") == ctrl_id:
                            controller_props = dev_props
                            break
                return codec_name, cid, controller_props
        return None, None, None

    def _init_default_audio_layout(self) -> None:
        info = self.get_audio_codec_info()
        if not info:
            self.selected_audio_layout_id = None
            return
        valid_ids = {item["id"] for item in info["layouts"]}
        if self.selected_audio_layout_id not in valid_ids:
            self.selected_audio_layout_id = info["default_id"]

    def get_audio_codec_info(self) -> Optional[Dict[str, Any]]:
        """Return detected AppleALC codec metadata and available layout IDs."""
        codec_name, codec_id, _ = self._find_audio_codec_and_controller(self.customized_hardware)
        if not codec_id:
            return None
        available = self.codec_layouts.data.get(codec_id) or []
        if not available:
            return None

        recommended_authors = ("Mirone", "InsanelyDeepak", "Toleda", "DalianSky")
        rec_ids = {
            lay.id for lay in available if self.u.contains_any(recommended_authors, lay.comment)
        }
        default_id = next((lay.id for lay in available if lay.id in rec_ids), available[0].id)
        current_id = self.selected_audio_layout_id if self.selected_audio_layout_id is not None else default_id

        return {
            "codec_name": codec_name,
            "codec_id": codec_id,
            "default_id": default_id,
            "selected_id": current_id,
            "layouts": [
                {
                    "id": lay.id,
                    "comment": lay.comment,
                    "recommended": lay.id in rec_ids,
                    "selected": lay.id == current_id,
                }
                for lay in available
            ],
        }

    def set_audio_layout_id(self, layout_id: int) -> None:
        self.selected_audio_layout_id = int(layout_id)

    def _patched_select_audio_codec_layout(
        self, hardware_report: Dict[str, Any], config: Any = None, controller_required: bool = False
    ) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
        """Inject user's pre-selected audio layout ID without blocking during build."""
        try:
            for dev_props in config["DeviceProperties"]["Add"].values():
                if dev_props.get("layout-id"):
                    return None, None
        except Exception:
            pass

        _, codec_id, controller_props = self._find_audio_codec_and_controller(hardware_report)
        if not codec_id:
            return None, None
        if controller_required and not controller_props:
            return None, None

        available = self.codec_layouts.data.get(codec_id) or []
        if self.selected_audio_layout_id is not None:
            for lay in available:
                if lay.id == self.selected_audio_layout_id:
                    self.bridge.push_log(f"使用已选声卡 Layout ID：{lay.id} ({lay.comment})")
                    return lay.id, controller_props

        return self._orig_select_audio_layout(
            hardware_report, config=config, controller_required=controller_required
        )

    def apply_macos_version(self, target_darwin: str) -> Dict[str, Any]:
        if not self.hardware_report:
            raise RuntimeError("请先加载硬件报告。")
        self.bridge.clear_recent()
        self.bridge.clear_notices()
        with self._capture_stdout():
            self._apply_version_internal(target_darwin)
        return self.get_state_snapshot()

    def get_available_macos_versions(self) -> List[Dict[str, Any]]:
        if not self.native_macos_version:
            return []
        oclp = self.ocl_patched_macos_version
        oclp_min = int(oclp[-1][:2]) if oclp else 99
        oclp_max = int(oclp[0][:2]) if oclp else 0
        min_v = min(int(self.native_macos_version[0][:2]), oclp_min)
        max_v = max(int(self.native_macos_version[-1][:2]), oclp_max)
        suggested_major = int(self.suggested_macos_version[:2]) if self.suggested_macos_version else -1

        items: List[Dict[str, Any]] = []
        for darwin_major in range(max_v, min_v - 1, -1):
            name = self.os_data.get_macos_name_by_darwin(str(darwin_major))
            if not name:
                continue
            target_darwin = f"{darwin_major}.99.99"
            is_oclp = oclp_min <= darwin_major <= oclp_max
            items.append(
                {
                    "darwin_major": darwin_major,
                    "darwin_version": target_darwin,
                    "name": name,
                    "requires_oclp": is_oclp,
                    "is_suggested": darwin_major == suggested_major,
                    "is_selected": bool(
                        self.macos_version and int(self.macos_version[:2]) == darwin_major
                    ),
                }
            )
        return items

    # ------------------------------------------------------------------
    # Step 3: Customize ACPI / Kexts / SMBIOS
    # ------------------------------------------------------------------
    def set_acpi_patch_checked(self, index: int, checked: bool) -> None:
        if 0 <= index < len(self.ac.patches):
            patch = self.ac.patches[index]
            patch.checked = checked
            if patch.name == "BATP":
                ec_idx = self.kext_data.kext_index_by_name.get("ECEnabler")
                if ec_idx is not None and self.macos_version:
                    if checked:
                        self.k.check_kext(ec_idx, self.macos_version, force_load=False)
                    else:
                        self.k.uncheck_kext(ec_idx)

    def toggle_kext(self, index: int, enable: bool, force_load: bool = False) -> Tuple[bool, str]:
        if not self.macos_version:
            return False, "请先选择目标 macOS 版本。"
        if not (0 <= index < len(self.k.kexts)):
            return False, "无效的 Kext 索引。"

        kext = self.k.kexts[index]
        if not enable:
            if kext.required:
                return False, f"{kext.name} 为系统必需驱动，无法取消勾选。"
            ok = self.k.uncheck_kext(index)
            return (True, f"已取消勾选 {kext.name}") if ok else (False, f"有必需驱动依赖 {kext.name}，无法取消。")

        status = self.k.get_kext_status(kext, self.macos_version)
        if status == "not_needed":
            return False, f"{kext.name} 在当前 macOS 版本中不需要。"
        if status == "requires_newer":
            return False, f"{kext.name} 需要更高版本的 macOS。"

        if not self.k.is_kext_compatible(kext, self.macos_version) and not force_load:
            return False, "NEED_FORCE_CONFIRM"

        ok = self.k.check_kext(index, self.macos_version, force_load=force_load)
        if ok:
            return True, f"已启用 {kext.name}"
        return False, f"无法启用 {kext.name}，其依赖驱动在当前系统版本不可用。"

    def get_smbios_models(self, show_all: bool = False) -> List[Dict[str, Any]]:
        if not self.customized_hardware or not self.macos_version:
            return []
        default_model = self.s.select_smbios_model(self.customized_hardware, self.macos_version)
        is_laptop = self.customized_hardware.get("Motherboard", {}).get("Platform") == "Laptop"
        cur_v = self.u.parse_darwin_version(self.macos_version)

        models: List[Dict[str, Any]] = []
        for dev in self.mac_model_data.mac_devices:
            supported = (
                self.u.parse_darwin_version(dev.initial_support)
                <= cur_v
                <= self.u.parse_darwin_version(dev.last_supported_version)
            )
            if (
                dev.name not in (default_model, self.smbios_model)
                and not show_all
                and (
                    not supported
                    or (is_laptop and not dev.name.startswith("MacBook"))
                    or (not is_laptop and dev.name.startswith("MacBook"))
                )
            ):
                continue
            models.append(
                {
                    "name": dev.name,
                    "cpu": dev.cpu,
                    "cpu_generation": dev.cpu_generation,
                    "discrete_gpu": dev.discrete_gpu or "",
                    "supported": supported,
                    "is_default": dev.name == default_model,
                    "is_selected": dev.name == self.smbios_model,
                }
            )
        return models

    def set_smbios_model(self, model_name: str) -> None:
        if not self.customized_hardware or not self.macos_version:
            return
        self.smbios_model = model_name
        with self._capture_stdout():
            self.s.smbios_specific_options(
                self.customized_hardware,
                self.smbios_model,
                self.macos_version,
                self.ac.patches,
                self.k,
            )

    def restore_default_smbios(self) -> Optional[str]:
        if not self.customized_hardware or not self.macos_version:
            return None
        default_model = self.s.select_smbios_model(self.customized_hardware, self.macos_version)
        self.set_smbios_model(default_model)
        return default_model

    # ------------------------------------------------------------------
    # Step 4: Download & Build OpenCore EFI
    # ------------------------------------------------------------------
    def check_bios_requirements(self) -> List[str]:
        if not self.org_hardware_report or not self.customized_hardware:
            return []
        reqs: List[str] = []
        org_fw = self.org_hardware_report.get("BIOS", {}).get("Firmware Type", "Unknown")
        fw = self.customized_hardware.get("BIOS", {}).get("Firmware Type", "Unknown")
        if org_fw == "Legacy" and fw == "UEFI":
            reqs.append("Enable UEFI mode (disable Legacy/CSM (Compatibility Support Module))")

        secure_boot = self.customized_hardware.get("BIOS", {}).get("Secure Boot", "Unknown")
        if secure_boot != "Disabled":
            reqs.append("Disable Secure Boot")

        mb = self.customized_hardware.get("Motherboard", {})
        if mb.get("Platform") == "Desktop" and mb.get("Chipset") in self.chipset_data.IntelChipsets[112:]:
            rebar = any(
                gpu.get("Resizable BAR", "Disabled") == "Enabled"
                for gpu in self.customized_hardware.get("GPU", {}).values()
            )
            if not rebar:
                reqs.append("Enable Above 4G Decoding")
                reqs.append("Disable Resizable BAR/Smart Access Memory")
        return reqs

    def build_efi(self) -> Dict[str, Any]:
        if not self.customized_hardware or not self.macos_version or not self.smbios_model:
            raise RuntimeError("请先完成硬件报告加载与系统版本选择。")

        self.bridge.clear_recent()
        with self._capture_stdout():
            # Phase A: Gather OpenCorePkg & Kexts
            self.o.gather_bootloader_kexts(self.k.kexts, self.macos_version)

            # Phase B: Build EFI (exact upstream logic from OpCore-Simplify.py)
            steps = [
                "Copying EFI base to results folder",
                "Applying ACPI patches",
                "Copying kexts and snapshotting to config.plist",
                "Generating config.plist",
                "Cleaning up unused drivers, resources, and tools",
            ]
            title = "Building OpenCore EFI"
            out_dir = self.result_dir

            self.u.progress_bar(title, steps, 0)
            self.u.create_folder(out_dir, remove_content=True)

            if not os.path.exists(self.k.ock_files_dir):
                raise FileNotFoundError(f"缓存目录不存在：{self.k.ock_files_dir}")

            source_efi_dir = os.path.join(self.k.ock_files_dir, "OpenCorePkg")
            shutil.copytree(source_efi_dir, out_dir, dirs_exist_ok=True)

            config_file = os.path.join(out_dir, "EFI", "OC", "config.plist")
            config_data = self.u.read_file(config_file)
            if not config_data:
                raise FileNotFoundError(f"缺少模板配置文件：{config_file}")
            original_config_snapshot = copy.deepcopy(config_data)

            self.u.progress_bar(title, steps, 1)
            config_data["ACPI"]["Add"] = []
            config_data["ACPI"]["Delete"] = []
            config_data["ACPI"]["Patch"] = []
            if self.has_loaded_dsdt():
                self.ac.hardware_report = self.customized_hardware
                self.ac.disabled_devices = self.disabled_devices
                self.ac.acpi_directory = os.path.join(out_dir, "EFI", "OC", "ACPI")
                self.ac.smbios_model = self.smbios_model
                self.ac.lpc_bus_device = self.ac.get_lpc_name()

                for patch in self.ac.patches:
                    if patch.checked:
                        if patch.name == "BATP":
                            patch.checked = getattr(self.ac, patch.function_name)()
                            ec_idx = self.kext_data.kext_index_by_name.get("ECEnabler")
                            if ec_idx is not None:
                                self.k.kexts[ec_idx].checked = patch.checked
                            continue

                        acpi_load = getattr(self.ac, patch.function_name)()
                        if not isinstance(acpi_load, dict):
                            continue

                        config_data["ACPI"]["Add"].extend(acpi_load.get("Add", []))
                        config_data["ACPI"]["Delete"].extend(acpi_load.get("Delete", []))
                        config_data["ACPI"]["Patch"].extend(acpi_load.get("Patch", []))

            config_data["ACPI"]["Patch"].extend(self.ac.dsdt_patches)
            config_data["ACPI"]["Patch"] = self.ac.apply_acpi_patches(config_data["ACPI"]["Patch"])

            self.u.progress_bar(title, steps, 2)
            kexts_directory = os.path.join(out_dir, "EFI", "OC", "Kexts")
            self.k.install_kexts_to_efi(self.macos_version, kexts_directory)
            config_data["Kernel"]["Add"] = self.k.load_kexts(
                self.customized_hardware, self.macos_version, kexts_directory
            )

            self.u.progress_bar(title, steps, 3)
            self.co.genarate(
                self.customized_hardware,
                self.disabled_devices,
                self.smbios_model,
                self.macos_version,
                self.needs_oclp,
                self.k.kexts,
                config_data,
            )
            self.u.write_file(config_file, config_data)
            self.last_original_config = original_config_snapshot
            self.last_generated_config = copy.deepcopy(config_data)

            self.u.progress_bar(title, steps, 4)
            self._cleanup_unused_files(out_dir, config_data)

            self.u.progress_bar(title, steps, len(steps), done=True)
            self.bridge.push_log(f"OpenCore EFI 构建完成：{out_dir}")

        return {
            "result_dir": out_dir,
            "config_file": config_file,
            "bios_requirements": self.check_bios_requirements(),
            "needs_oclp": self.needs_oclp,
            "notices": list(self.bridge.notices),
            "original_config": self.last_original_config,
            "generated_config": self.last_generated_config,
        }

    def _cleanup_unused_files(self, out_dir: str, config_data: Dict[str, Any]) -> None:
        files_to_remove: List[str] = []

        drivers_dir = os.path.join(out_dir, "EFI", "OC", "Drivers")
        if os.path.isdir(drivers_dir):
            driver_list = self.u.find_matching_paths(drivers_dir, extension_filter=".efi")
            driver_loaded = [d.get("Path") for d in config_data.get("UEFI", {}).get("Drivers", [])]
            for driver_path, _ in driver_list:
                if driver_path not in driver_loaded:
                    files_to_remove.append(os.path.join(drivers_dir, driver_path))

        resources_audio = os.path.join(out_dir, "EFI", "OC", "Resources", "Audio")
        if os.path.exists(resources_audio):
            files_to_remove.append(resources_audio)

        picker_variant = config_data.get("Misc", {}).get("Boot", {}).get("PickerVariant")
        if picker_variant in (None, "Auto"):
            picker_variant = "Acidanthera/GoldenGate"
        if os.name == "nt":
            picker_variant = picker_variant.replace("/", "\\")

        resources_img = os.path.join(out_dir, "EFI", "OC", "Resources", "Image")
        if os.path.isdir(resources_img):
            for variant_name, _ in self.u.find_matching_paths(resources_img, type_filter="dir"):
                variant_path = os.path.join(resources_img, variant_name)
                if ".icns" in ", ".join(os.listdir(variant_path)):
                    if picker_variant not in variant_name:
                        files_to_remove.append(variant_path)

        tools_dir = os.path.join(out_dir, "EFI", "OC", "Tools")
        if os.path.isdir(tools_dir):
            tool_list = self.u.find_matching_paths(tools_dir, extension_filter=".efi")
            tool_loaded = [t.get("Path") for t in config_data.get("Misc", {}).get("Tools", [])]
            for tool_path, _ in tool_list:
                if tool_path not in tool_loaded:
                    files_to_remove.append(os.path.join(tools_dir, tool_path))

        manifest = os.path.join(out_dir, "manifest.json")
        if os.path.exists(manifest):
            files_to_remove.append(manifest)

        for fp in files_to_remove:
            try:
                if os.path.isdir(fp):
                    shutil.rmtree(fp)
                else:
                    os.remove(fp)
            except OSError:
                pass

    # ------------------------------------------------------------------
    # Snapshot for UI rendering
    # ------------------------------------------------------------------
    def get_state_snapshot(self) -> Dict[str, Any]:
        return {
            "report_path": self.report_path,
            "acpi_dir": self.acpi_dir,
            "acpi_loaded": self.has_loaded_dsdt(),
            "hardware_report": self.hardware_report,
            "customized_hardware": self.customized_hardware,
            "disabled_devices": self.disabled_devices,
            "macos_version": self.macos_version,
            "macos_name": (
                self.os_data.get_macos_name_by_darwin(self.macos_version)
                if self.macos_version
                else None
            ),
            "suggested_macos_version": self.suggested_macos_version,
            "needs_oclp": self.needs_oclp,
            "smbios_model": self.smbios_model,
            "audio_layout_id": self.selected_audio_layout_id,
            "audio_codec": self.get_audio_codec_info(),
            "warnings": self.last_validation_warnings,
            "notices": list(self.bridge.notices),
            "checked_acpi_count": sum(1 for p in self.ac.patches if p.checked),
            "checked_kext_count": sum(1 for k in self.k.kexts if k.checked),
        }
