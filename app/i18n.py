"""Complete bilingual (zh_CN / en_US) localization dictionary for OC-Studio."""

from __future__ import annotations

from typing import Dict


STRINGS: Dict[str, Dict[str, str]] = {
    "zh_CN": {
        "app.title": "OC-Studio",
        "nav.home": "首页",
        "nav.report": "1. 硬件报告",
        "nav.macos": "2. 系统版本",
        "nav.customize": "3. 高级定制",
        "nav.build": "4. 生成 EFI",
        "nav.settings": "设置",
        # Home
        "home.welcome": "欢迎使用 OC-Studio",
        "home.subtitle": "基于官方最新版 OpCore-Simplify 的中文现代图形化向导，零侵入接入上游内核，帮你一步步生成干净、可引导的 OpenCore EFI。",
        "home.start_btn": "开始制作 EFI",
        "home.diff_btn": "查看 / 对比 config.plist",
        "home.settings_btn": "镜像加速与内核设置",
        "home.steps_title": "四步完成 EFI 制作",
        "home.step1_title": "① 采集硬件报告",
        "home.step1_desc": "Windows 下一键调用 Hardware Sniffer 采集硬件与 ACPI 表，或直接拖入已有 Report.json，自动给出每块硬件的兼容性评级。",
        "home.step2_title": "② 选择 macOS 版本",
        "home.step2_desc": "自动筛选本机原生支持与 OCLP 支持的系统版本；支持随时重选多显卡组合和 Intel Wi-Fi 驱动方案。",
        "home.step3_title": "③ 高级定制微调",
        "home.step3_desc": "图形化勾选 ACPI 补丁（附中文人话说明）、Kext 驱动、SMBIOS 机型和声卡 Layout ID，不懂可直接保持默认。",
        "home.step4_title": "④ 生成并核对配置",
        "home.step4_desc": "自动下载最新版 OpenCore 与驱动（支持国内镜像加速），构建完成后可用内置树形对比器核对 config.plist 改动。",
        "home.tip_title": "贴心提示",
        "home.tip_body": "• 如果你在国内网络环境下下载 OpenCore 或驱动较慢，建议先点上方「镜像加速与内核设置」开启 GitHub 镜像或填写本地代理。\n• 笔记本用户生成 EFI 后，别忘了按构建完成页的指引定制 USB 端口（USBToolBox）并关闭 BIOS 安全启动（Secure Boot）。",
        "home.core_badge": "OC-Studio v{ver}  |  内置官方内核：{repo} @ {sha}（{date}）",
        # Report
        "report.title": "硬件报告与兼容性检测",
        "report.desc": "直接采集本机硬件信息，或导入由 Hardware Sniffer 生成的 Report.json 报告文件。",
        "report.export_btn": "一键采集本机硬件（推荐）",
        "report.import_btn": "导入 Report.json",
        "report.acpi_btn": "选择 ACPI 表目录",
        "report.drop_hint": "也可直接把 Report.json 文件或 SysReport 文件夹拖放到这里",
        "report.win_only_hint": "一键采集仅支持 Windows；macOS/Linux 请先在 Windows 下用 Hardware Sniffer 导出报告后拖入。",
        "report.summary_title": "硬件兼容性总览",
        "report.next_btn": "下一步：选择 macOS 版本",
        "report.no_data": "请先采集或导入硬件报告，检测结果会显示在这里。",
        "report.no_file": "当前未加载报告",
        "report.file_prefix": "报告文件：",
        "report.acpi_loaded": "✓ ACPI 表已就绪（{path}）",
        "report.acpi_missing": "⚠ 尚未加载 ACPI 表，请点击「选择 ACPI 表目录」",
        "report.notice_title": "内核提示",
        "report.platform_title": "基础平台信息",
        # macOS
        "macos.title": "选择目标 macOS 版本",
        "macos.desc": "系统已根据你的硬件自动筛选出可安装的 macOS 版本范围，推荐使用标记为“官方推荐”的版本。",
        "macos.need_report_first": "请先在「1. 硬件报告」页面加载硬件报告。",
        "macos.list_title": "可选 macOS 版本列表",
        "macos.apply_btn": "应用此版本并重新匹配驱动",
        "macos.reselect_btn": "重选显卡 / Wi-Fi 组合",
        "macos.next_btn": "下一步：高级定制",
        "macos.active_hw_title": "当前版本已启用的关键硬件",
        "macos.disabled_title": "将自动屏蔽的不兼容硬件",
        "macos.no_disabled": "当前版本下没有需要屏蔽的硬件。",
        "macos.recommended_tag": "★ 官方推荐",
        "macos.oclp_tag": "需 OCLP 补丁",
        "macos.native_tag": "原生支持",
        # Customize
        "custom.title": "高级定制（ACPI / Kext / SMBIOS / 声卡）",
        "custom.desc": "内核已按你的硬件自动选好推荐项，不懂可保持默认直接进入「4. 生成 EFI」。",
        "custom.next_btn": "下一步：生成 EFI",
        "custom.tab_acpi": "ACPI 补丁",
        "custom.tab_kext": "Kext 驱动",
        "custom.tab_smbios": "SMBIOS 机型",
        "custom.tab_audio": "声卡 Layout ID",
        "custom.search_placeholder": "搜索名称或说明...",
        "custom.show_all_smbios": "显示全部机型（含不匹配平台的机型）",
        "custom.restore_default": "恢复默认推荐",
        "custom.restore_audio": "恢复推荐 ID",
        "custom.smbios_current": "当前机型：{model}",
        "custom.audio_none": "当前硬件报告中未检测到需要 AppleALC Layout ID 的声卡芯片。",
        "custom.audio_none_tip": "（如果使用的是 USB 声卡或免驱 HDMI 音频，不需要设置 Layout ID）",
        "custom.audio_tip": "提示：不同机型同款声卡芯片的扬声器/耳机/麦克风引脚定义不同；若进系统无声或杂音，可回来换一个 Layout ID 重新生成。",
        "custom.audio_header": "声卡：{name} ({cid})  |  当前 Layout ID：{lid}",
        "custom.rec_badge": "★ 默认推荐",
        "custom.audio_rec_badge": "★ 常用推荐",
        "custom.unsup_badge": "该系统官方不支持",
        # Build
        "build.title": "生成 OpenCore EFI",
        "build.desc": "自动下载最新版 OpenCore 与所需驱动，编译 ACPI 补丁并生成可直接使用的 EFI 文件夹。",
        "build.summary_title": "构建前配置核对",
        "build.no_report": "尚未加载硬件报告，请先完成前面步骤。",
        "build.start_btn": "开始生成 EFI",
        "build.open_result_btn": "打开 EFI 输出目录",
        "build.diff_btn": "查看 config.plist 对比",
        "build.progress_title": "构建进度",
        "build.waiting": "等待开始...",
        "build.no_download": "当前无下载任务",
        "build.bios_title": "使用 EFI 前请检查以下事项",
        "build.log_title": "实时运行日志",
        "build.clear_log_btn": "清空日志",
        "build.oclp_warn_title": "OpenCore Legacy Patcher (OCLP) 风险提示",
        "build.oclp_warn_body": "你当前的硬件或所选系统版本需要配合 OCLP 根补丁才能正常工作：\n\n• 会关闭 SIP 与 AMFI 等部分系统安全校验\n• 系统更新需要完整安装包，稳定性不如纯原生配置\n• 进系统后需按提示运行对应版本的 OCLP 打补丁\n\n确认要继续生成吗？",
        # Settings
        "settings.title": "设置与内核管理",
        "settings.desc": "配置国内下载加速代理、界面主题与语言，以及一键检测同步上游 OpCore-Simplify 内核。",
        "settings.network_group": "下载与网络加速",
        "settings.mirror_title": "GitHub 镜像加速",
        "settings.mirror_desc": "国内网络拉取 OpenCore / Kext 慢或失败时，可切换镜像源（失败时会自动回退直连）",
        "settings.custom_mirror_title": "自定义镜像前缀",
        "settings.custom_mirror_desc": "当镜像模式选择“自定义”时生效，例如 https://ghfast.top/",
        "settings.proxy_title": "HTTP / HTTPS 代理",
        "settings.proxy_desc": "可选，例如 http://127.0.0.1:7890（留空则不使用代理）",
        "settings.appearance_group": "界面与输出",
        "settings.theme_title": "界面主题",
        "settings.theme_desc": "切换浅色、深色或跟随系统主题（选择后立即生效）",
        "settings.lang_title": "界面语言 / Language",
        "settings.lang_desc": "切换简体中文或英文（选择后立即生效）",
        "settings.output_title": "EFI 默认输出目录",
        "settings.output_desc": "留空则默认保存到程序目录下的 Results 文件夹",
        "settings.browse_btn": "浏览",
        "settings.reset_btn": "恢复默认设置",
        "settings.save_btn": "保存网络与路径设置",
        "settings.core_group": "上游内核状态（零修改解耦）",
        "settings.core_check_btn": "检查上游更新",
        "settings.core_sync_btn": "同步最新内核",
        "settings.about_group": "关于 OC-Studio",
        "settings.about_body": "OC-Studio v{ver}\n核心引擎：{repo}（零修改子模块解耦调用）\n原则：不魔改官方核心逻辑，方便长期紧跟上游同步更新。",
        "settings.mirror_direct": "直连 GitHub（默认）",
        "settings.mirror_ghfast": "ghfast.top 镜像加速",
        "settings.mirror_ghproxy_net": "ghproxy.net 镜像加速",
        "settings.mirror_ghproxy_cc": "mirror.ghproxy.com 镜像加速",
        "settings.mirror_custom": "自定义镜像前缀",
        "settings.theme_auto": "跟随系统",
        "settings.theme_light": "浅色主题",
        "settings.theme_dark": "深色主题",
    },
    "en_US": {
        "app.title": "OC-Studio",
        "nav.home": "Home",
        "nav.report": "1. Hardware Report",
        "nav.macos": "2. macOS Version",
        "nav.customize": "3. Customize",
        "nav.build": "4. Build EFI",
        "nav.settings": "Settings",
        # Home
        "home.welcome": "Welcome to OC-Studio",
        "home.subtitle": "A modern Fluent GUI for the latest upstream OpCore-Simplify with zero modifications to the core engine, guiding you step-by-step to build a clean OpenCore EFI.",
        "home.start_btn": "Start Building EFI",
        "home.diff_btn": "Inspect / Diff config.plist",
        "home.settings_btn": "Mirrors & Core Settings",
        "home.steps_title": "Build Your EFI in 4 Steps",
        "home.step1_title": "1. Hardware Report",
        "home.step1_desc": "Export your hardware & ACPI tables on Windows via Hardware Sniffer, or drag & drop Report.json to view per-device compatibility.",
        "home.step2_title": "2. Target macOS Version",
        "home.step2_desc": "Automatically lists native and OCLP-supported macOS versions. Re-pick multi-GPU or Intel Wi-Fi combinations anytime.",
        "home.step3_title": "3. Fine-Tune Options",
        "home.step3_desc": "Visually toggle ACPI patches, Kexts, SMBIOS models, and AppleALC Audio Layout IDs — or keep the recommended defaults.",
        "home.step4_title": "4. Build & Review Config",
        "home.step4_desc": "Downloads the latest OpenCore and kexts (with optional GitHub mirror acceleration) and lets you inspect every config.plist diff.",
        "home.tip_title": "Quick Tips",
        "home.tip_body": "• If GitHub downloads are slow on your network, enable a GitHub mirror or HTTP proxy in Settings first.\n• Remember to map your USB ports with USBToolBox and disable Secure Boot in BIOS before booting the generated EFI.",
        "home.core_badge": "OC-Studio v{ver}  |  Upstream Core: {repo} @ {sha} ({date})",
        # Report
        "report.title": "Hardware Report & Compatibility",
        "report.desc": "Export your hardware report directly on Windows or import an existing Report.json from Hardware Sniffer.",
        "report.export_btn": "Export Hardware Report (Recommended)",
        "report.import_btn": "Import Report.json",
        "report.acpi_btn": "Select ACPI Folder",
        "report.drop_hint": "Or drag & drop a Report.json file or SysReport folder right here",
        "report.win_only_hint": "One-click export is Windows-only. On macOS/Linux, import Report.json exported on Windows.",
        "report.summary_title": "Hardware Compatibility Overview",
        "report.next_btn": "Next: Select macOS Version",
        "report.no_data": "Export or import a hardware report to see compatibility details here.",
        "report.no_file": "No hardware report loaded",
        "report.file_prefix": "Report file: ",
        "report.acpi_loaded": "✓ ACPI tables ready ({path})",
        "report.acpi_missing": "⚠ ACPI tables not loaded yet — click 'Select ACPI Folder'",
        "report.notice_title": "Core Notices",
        "report.platform_title": "Platform Summary",
        # macOS
        "macos.title": "Select Target macOS Version",
        "macos.desc": "Compatible macOS versions are filtered based on your hardware. Choosing the recommended version gives the best stability.",
        "macos.need_report_first": "Please load a hardware report on '1. Hardware Report' first.",
        "macos.list_title": "Available macOS Versions",
        "macos.apply_btn": "Apply Version & Recalculate",
        "macos.reselect_btn": "Re-select GPU / Wi-Fi",
        "macos.next_btn": "Next: Customize",
        "macos.active_hw_title": "Active Hardware for Selected Version",
        "macos.disabled_title": "Incompatible Devices to Be Disabled",
        "macos.no_disabled": "No devices need to be disabled for this version.",
        "macos.recommended_tag": "★ Recommended",
        "macos.oclp_tag": "Requires OCLP",
        "macos.native_tag": "Native",
        # Customize
        "custom.title": "Customize (ACPI / Kexts / SMBIOS / Audio)",
        "custom.desc": "Recommended options are pre-selected automatically. Keep defaults if you are unsure and jump straight to Build EFI.",
        "custom.next_btn": "Next: Build EFI",
        "custom.tab_acpi": "ACPI Patches",
        "custom.tab_kext": "Kexts",
        "custom.tab_smbios": "SMBIOS Model",
        "custom.tab_audio": "Audio Layout ID",
        "custom.search_placeholder": "Search name or description...",
        "custom.show_all_smbios": "Show all models (including mismatched platform)",
        "custom.restore_default": "Restore Default",
        "custom.restore_audio": "Restore Default ID",
        "custom.smbios_current": "Selected Model: {model}",
        "custom.audio_none": "No AppleALC-supported audio codec detected in this hardware report.",
        "custom.audio_none_tip": "(USB audio devices or native HDMI audio do not require an AppleALC Layout ID.)",
        "custom.audio_tip": "Tip: Pinouts differ across laptops with the same codec. If audio or mic doesn't work after boot, try another Layout ID here and rebuild.",
        "custom.audio_header": "Codec: {name} ({cid})  |  Selected Layout ID: {lid}",
        "custom.rec_badge": "★ Recommended",
        "custom.audio_rec_badge": "★ Suggested",
        "custom.unsup_badge": "Unsupported by OS",
        # Build
        "build.title": "Build OpenCore EFI",
        "build.desc": "Download latest OpenCore & required kexts, compile ACPI patches, and generate a ready-to-use EFI folder.",
        "build.summary_title": "Pre-Build Summary",
        "build.no_report": "No hardware report loaded yet. Please finish the previous steps first.",
        "build.start_btn": "Build OpenCore EFI",
        "build.open_result_btn": "Open Output Folder",
        "build.diff_btn": "Inspect config.plist Diff",
        "build.progress_title": "Build Progress",
        "build.waiting": "Waiting to start...",
        "build.no_download": "No active downloads",
        "build.bios_title": "Before Using This EFI",
        "build.log_title": "Live Build Log",
        "build.clear_log_btn": "Clear Log",
        "build.oclp_warn_title": "OpenCore Legacy Patcher Warning",
        "build.oclp_warn_body": "Your selected hardware or macOS version requires OpenCore Legacy Patcher root patches:\n\n• Disables macOS security features including SIP and AMFI\n• macOS updates require full installers and stability may be reduced\n• You must apply matching OCLP root patches after booting macOS\n\nContinue building?",
        # Settings
        "settings.title": "Settings & Core Management",
        "settings.desc": "Configure GitHub download mirrors, proxy, appearance, language, and upstream OpCore-Simplify core sync.",
        "settings.network_group": "Network & Download Acceleration",
        "settings.mirror_title": "GitHub Mirror",
        "settings.mirror_desc": "Accelerate OpenCore/Kext downloads (automatically falls back to direct on failure)",
        "settings.custom_mirror_title": "Custom Mirror Prefix",
        "settings.custom_mirror_desc": "Used when mirror is set to Custom, e.g. https://ghfast.top/",
        "settings.proxy_title": "HTTP / HTTPS Proxy",
        "settings.proxy_desc": "Optional, e.g. http://127.0.0.1:7890 (leave blank to disable)",
        "settings.appearance_group": "Appearance & Output",
        "settings.theme_title": "Theme",
        "settings.theme_desc": "Switch between Light, Dark, or System theme (applies immediately)",
        "settings.lang_title": "Language / 界面语言",
        "settings.lang_desc": "Switch between Chinese and English (applies immediately)",
        "settings.output_title": "Default EFI Output Folder",
        "settings.output_desc": "Leave blank to save into the Results folder inside OC-Studio",
        "settings.browse_btn": "Browse",
        "settings.reset_btn": "Reset Defaults",
        "settings.save_btn": "Save Network & Path",
        "settings.core_group": "Upstream Core (Zero-Modification Submodule)",
        "settings.core_check_btn": "Check Upstream",
        "settings.core_sync_btn": "Sync Latest Core",
        "settings.about_group": "About OC-Studio",
        "settings.about_body": "OC-Studio v{ver}\nCore engine: {repo} (untouched git submodule)\nDesigned to stay in sync with upstream effortlessly.",
        "settings.mirror_direct": "Direct GitHub (Default)",
        "settings.mirror_ghfast": "ghfast.top Mirror",
        "settings.mirror_ghproxy_net": "ghproxy.net Mirror",
        "settings.mirror_ghproxy_cc": "mirror.ghproxy.com Mirror",
        "settings.mirror_custom": "Custom Mirror Prefix",
        "settings.theme_auto": "Follow System",
        "settings.theme_light": "Light",
        "settings.theme_dark": "Dark",
    },
}

ACPI_DESC_ZH: Dict[str, str] = {
    "ALS": "伪造环境光传感器，用于记住屏幕亮度及自动亮度状态",
    "APIC": "修复高端 HEDT 平台的首核编号问题，避免启动内核崩溃",
    "BATP": "开启笔记本电池电量百分比显示（自动联动 ECEnabler）",
    "BUS0": "添加 SMBus 设备，修复 AppleSMBus 相关功能",
    "Disable Devices": "屏蔽不兼容的 PCI 设备（如无法驱动的独显、无线网卡或读卡器）",
    "FakeEC": "伪造 macOS 兼容的嵌入式控制器（EC），几乎所有机器必备",
    "RCSP": "移除导致解析报错的条件 ACPI 作用域声明",
    "CMOS": "修复惠普（HP）主板重启后报 005 实时时钟掉电错误",
    "FixHPET": "修复 IRQ 中断冲突，常用于解决老平台声卡无声或卡顿",
    "GPI0": "启用 GPIO 设备，让笔记本 I2C 触控板能正常干活",
    "IMEI": "伪造 IMEI 设备，确保老代 Intel 核显硬件加速正常",
    "MCHC": "添加内存控制器设备，配合修复 AppleSMBus",
    "PMC": "为 Intel 300 系主板添加 PMCR 设备，修复原生 NVRAM",
    "PM (Legacy)": "屏蔽老平台（3 代及更早）的 CpuPm/Cpu0Ist 表防止崩溃",
    "PLUG": "注入 plugin-type=1 开启 Intel CPU 原生变频与电源管理",
    "PNLF": "添加背光设备，让笔记本能正常调节内屏亮度",
    "RMNE": "创建虚拟有线网卡，解决无有线网卡时无法登录 iCloud/iServices",
    "RTC0": "为 HEDT 平台创建新 RTC 时钟设备，解决 PCI 配置卡住",
    "RTCAWAC": "禁用 AWAC 时钟并启用/修复 RTC，防止 300 系及新主板卡死",
    "PRW": "修复 _PRW 睡眠唤醒状态，防止合盖或休眠后秒醒",
    "Surface Patch": "微软 Surface 系列笔记本专用 ACPI 补丁",
    "UNC": "禁用未使用的 HEDT 桥接设备，防止内核崩溃",
    "USB Reset": "重置 USB Hub，方便后续重新定制 USB 端口",
    "USBX": "注入 USB 供电属性，解决 USB 口供电不足或休眠断电",
    "WMIS": "修复部分笔记本温控表未返回结果的 ACPI 缺陷",
    "XOSI": "向主板伪装成 Windows 系统，解锁被屏蔽的触控板等硬件",
}

CATEGORY_ZH: Dict[str, str] = {
    "Motherboard": "主板",
    "BIOS": "BIOS / 固件",
    "CPU": "处理器 (CPU)",
    "GPU": "显卡 (GPU)",
    "Monitor": "显示器",
    "Sound": "声卡",
    "Network": "网卡",
    "Storage Controllers": "存储控制器 / 硬盘",
    "Bluetooth": "蓝牙",
    "SD Controller": "SD 读卡器",
    "Biometric": "指纹 / 生物识别",
    "USB Controllers": "USB 控制器",
    "Input": "输入设备",
}

BUILD_STEPS_ZH: Dict[str, str] = {
    "Copying EFI base to results folder": "复制 OpenCore 基础框架到输出目录",
    "Applying ACPI patches": "编译并写入 ACPI 补丁",
    "Copying kexts and snapshotting to config.plist": "复制 Kext 驱动并写入 config.plist",
    "Generating config.plist": "生成最终 config.plist 配置与三码",
    "Cleaning up unused drivers, resources, and tools": "清理多余驱动、主题资源和工具",
}

BIOS_REQ_ZH: Dict[str, str] = {
    "Enable UEFI mode (disable Legacy/CSM (Compatibility Support Module))": "开启 UEFI 启动模式（关闭 Legacy / CSM 兼容模式）",
    "Disable Secure Boot": "关闭 Secure Boot（安全启动）",
    "Enable Above 4G Decoding": "开启 Above 4G Decoding（大于 4G 地址空间解码）",
    "Disable Resizable BAR/Smart Access Memory": "关闭 Resizable BAR / SAM",
}


class Translator:
    def __init__(self, language: str = "zh_CN"):
        self.language = language if language in STRINGS else "zh_CN"

    def set_language(self, language: str) -> None:
        if language in STRINGS:
            self.language = language

    @property
    def is_zh(self) -> bool:
        return self.language == "zh_CN"

    def t(self, key: str, default: str | None = None, **kwargs: object) -> str:
        table = STRINGS.get(self.language, STRINGS["zh_CN"])
        text = table.get(key)
        if text is None:
            text = STRINGS["zh_CN"].get(key, default if default is not None else key)
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text

    def acpi_desc(self, patch_name: str, fallback: str) -> str:
        if self.language == "zh_CN" and patch_name in ACPI_DESC_ZH:
            return ACPI_DESC_ZH[patch_name]
        return fallback

    def category(self, name: str) -> str:
        if self.language == "zh_CN":
            return CATEGORY_ZH.get(name, name)
        return name

    def build_step(self, step: str) -> str:
        if self.language == "zh_CN":
            return BUILD_STEPS_ZH.get(step, step)
        return step

    def bios_req(self, req: str) -> str:
        if self.language == "zh_CN":
            return BIOS_REQ_ZH.get(req, req)
        return req
