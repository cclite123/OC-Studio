<div align="center">

# 🍎 OC-Studio

**给最新官方 `OpCore-Simplify` 套了个好看又省心的中文图形壳 ✨**

[![Release](https://img.shields.io/github/v/release/cclite123/OC-Studio?style=flat-square&color=0078d4&label=%E6%9C%80%E6%96%B0%E7%89%88%E6%9C%AC)](https://github.com/cclite123/OC-Studio/releases)
[![Build](https://img.shields.io/github/actions/workflow/status/cclite123/OC-Studio/build.yml?style=flat-square&label=%E8%87%AA%E5%8A%A8%E6%9E%84%E5%BB%BA)](https://github.com/cclite123/OC-Studio/actions)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS-16a34a?style=flat-square)](#%E5%BF%AB%E9%80%9F%E4%B8%8A%E6%89%8B%E5%B0%8F%E7%99%BD%E7%9B%B4%E6%8E%A5%E7%9C%8B%E8%BF%99%E9%87%8C)
[![Stars](https://img.shields.io/github/stars/cclite123/OC-Studio?style=flat-square&color=f59e0b)](https://github.com/cclite123/OC-Studio/stargazers)

*不想对着英文黑框输 `1、2、3`，又嫌以前的中文 GUI 停更太久？那来试试这个吧 (｡･ω･｡)ﾉ*

</div>

---

## 💡 为什么要做这个？

折腾黑苹果的朋友应该都用过超好用的 [OpCore-Simplify](https://github.com/lzhoang2801/OpCore-Simplify)，但有两个小小的痛点：

1. 官方原版一直在高频更新（连 12 代核显 `WhateverXe`、20~50 系 N 卡 `NullMoth`、macOS Tahoe 26 都跟上了），但它是**英文命令行黑框**，新手看着容易发懵；
2. 社区里以前有几个中文图形版，可惜都**把原版代码改碎了揉进界面里**，原版一更新就同步不动，停更很久了……

所以就有了 **OC-Studio** ٩(ˊᗜˋ*)و

核心思路特别简单粗暴：**原版 `OpCore-Simplify` 一行不改，直接当成独立内核（`core/` 子模块）塞进来，外面套一层 Win11 Fluent 风格的现代中文界面！**  
以后官方只要更新了新系统或新硬件支持，仓库每周自动同步一次内核，点几下鼠标就能永远用上最新版，再也不用等弃坑的魔改版啦～

---

## ✨ 它能帮你干啥？

- 🖥️ **一键体检你的电脑**  
  Windows 下点一个大按钮自动调用 Hardware Sniffer 扫硬件和 ACPI（也能直接把 `Report.json` 拖进来），哪块硬件原生支持、哪块要 OCLP、哪块没救，红黄绿标签一眼看明白。
- 🎛️ **告别盲选，看得懂再勾**  
  ACPI 补丁全配了**中文人话解释**（终于知道 `FakeEC`、`RTCAWAC`、`XOSI` 都是干嘛的了！），Kext 驱动自动管依赖和冲突，还能直接按声卡芯片挑 **Layout ID（`alcid`）**，显卡 / Wi-Fi 选错了也能随时点一下重选。
- 🔍 **改了什么一目了然**  
  内置 `config.plist` **树形对比查看器**，把模板和生成的最终配置放一块儿，绿（新增）/ 橙（修改）/ 红（删除）高亮标得清清楚楚，强迫症看了极度舒适。
- 🚀 **专治国内网络卡壳**  
  设置页内置 **GitHub 镜像加速** 和本地代理开关，下 OpenCore 和驱动不再转圈圈（镜像抽风还会自动回退直连，很稳）。
- 🌗 **颜值在线，秒切不卡顿**  
  深色 / 浅色 / 跟随系统、简体中文 / English，下拉框一选当场生效，连软件都不用重启！

---

## 📦 快速上手（小白直接看这里）

**不需要装 Python！不需要敲命令！**

1. 点右边或这里进入 👉 **[Releases 发布页](https://github.com/cclite123/OC-Studio/releases)**
2. 按你的电脑下载对应的压缩包：
   - **Windows**：下载 `OC-Studio-Windows-x64.zip`，解压后双击 **`OC-Studio.exe`** 就能用。
   - **macOS**：下载 `OC-Studio-macOS.zip`，解压后打开 **`OC-Studio.app`** 就能用。
3. 打开软件后跟着左侧 **1 → 2 → 3 → 4** 顺着点完就行，最后会帮你直接打开生成好的 `EFI` 文件夹～

> 💬 **温馨小提醒**
> - 国内如果点「一键采集」或「生成 EFI」下载慢，先去左下角 **设置** 里开一下 GitHub 镜像加速，立马起飞。
> - 生成好 EFI 别忘了按完成页的小清单，在 BIOS 里关掉 `Secure Boot`，并抽空用 `USBToolBox` 定制一下本机 USB 端口。

---

## 🛠️ 爱折腾 / 想从源码运行？

```bash
# 记得带上 --recursive，这样才会把官方 core/ 内核一起拉下来
git clone --recursive https://github.com/cclite123/OC-Studio.git
cd OC-Studio

# 建个虚拟环境装依赖
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
# source .venv/bin/activate

pip install -r requirements.txt
python main.py
```

想手动把内核拉到官方最新提交？一行命令搞定（或者直接在软件「设置」页点一下「同步最新内核」）：

```bash
git submodule update --remote core
```

---

## 💛 致谢 & 声明

- 核心黑苹果构建逻辑完全归功于开源项目 **[lzhoang2801/OpCore-Simplify](https://github.com/lzhoang2801/OpCore-Simplify)**，本仓库仅做零侵入图形化封装与中文体验优化。
- 感谢 **[Acidanthera](https://github.com/acidanthera)**、**[CorpNewt](https://github.com/corpnewt)**、**[Dortania](https://dortania.github.io/)** 以及整个黑苹果开源社区。
- 界面组件基于超好看的 **[PySide6-Fluent-Widgets](https://github.com/zhiyiYo/PySide6-Fluent-Widgets)**。

---

<div align="center">

如果这个小工具刚好帮到你省下几个小时折腾时间，欢迎右上角点个免费的 **⭐ Star** 鼓励一下呀～  
遇到 Bug 或有想要的新功能，随时来提 **[Issue](https://github.com/cclite123/OC-Studio/issues)**，看到了就会改！

</div>
