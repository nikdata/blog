---
title: "Fresh Setup of my MacBook Pro"
date: 2026-07-18
description: "A clean install instead of a migration. It takes longer, but you only keep what you actually use."
draft: false
---

My MacBook Pro was starting to become a bit stale with software bloat. Over the months, I installed quite some number of applications in order to try them out. In some cases, I was using a particular piece of software for some time, found something better, switched, and the unused application just lingered.

I had some free time so I decided to just start over. And this time, I was going to only install the software that I know I really enjoy using and actually use on a regular basis.

I code for a living and for fun - so this post will only cover applications that are either quality-of-life (QoL) improvements for me and/or coding related applications.

## The Essential Starting Points

### Homebrew

First things first: [Homebrew](https://brew.sh).

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Homebrew is very similar to an app store (i.e., Mac App Store). It has thousands of applications that you can easily install through the command line. In fact, through Homebrew, you can install regular Mac apps without having to go to the application homepage or through the Mac App Store.

### Ghostty

macOS does ship with the Terminal app. It's nice. But have you tried Ghostty?

Ghostty is a terminal emulator for macOS and it's blazing fast. Switch and you won't regret it.

I don't use iTerm2 anymore.

## The Bag of Trusty Marbles

Some of the software listed below comes with macOS. However, they are not always up to date with the latest/greatest version. That's why I install the newest versions from Homebrew and let Homebrew manage it. The "risky" one here is Python. I've found that it is a bad idea to mess with the default Python version in macOS. That's why it's a good idea to install Python separately through Homebrew and it will put Python on a different path than the default one. 

In no particular order:

- [git](https://git-scm.com)
- [zsh](https://www.zsh.org)
- [zsh-syntax-highlighting](https://github.com/zsh-users/zsh-syntax-highlighting)
- [uv](https://docs.astral.sh/uv/)
- [python](https://www.python.org) (at the time of writing: 3.14)
- [pipx](https://pipx.pypa.io/latest/index.html)
- [mole](https://github.com/tw93/Mole)

I don't use Oh My ZSH since for me it's overkill. I have a very lean .zshrc file

### git

git is the foundation for source control/version control. It works well with text-based files. I use GitHub as my cloud git provider.

### zsh

macOS comes with the zsh. However, it may not necessarily be the most up to date.

### zsh syntax highlighting

This nifty app (or extension?) adds color to your commands in the terminal. Green means valid, Red means invalid. This is a huge QoL upgrade.

### uv

This is by-far the best virtual environment manager for Python. Anything else is just garbage.

### python

It's better to install Python from Homebrew and not touch the default install of Python. Trust me.

### pipx

Pipx is something I discovered recently. To put it lightly, if you install a package with pipx, it'll basically be available everywhere.

### mole

I discovered this handy app recently as well. Mole is a nifty utility app that can identify extraneous files that are no longer needed and free up disk space. It's like Daisy Disk and the countless Mac cleaning apps, but better and for the command line.

## The Box of Goodies

There are several applications (GUI) that I use daily.

- [Zed](https://zed.dev)
- [Maccy](https://maccy.app)
- [CotEditor](https://coteditor.com)
- [Alt-Tab](https://github.com/lwouis/alt-tab-macos)
- [Bartender](https://www.macbartender.com)
- [Little Snitch](https://obdev.at/products/littlesnitch/index.html)
- [Claude (and Claude Code)](https://claude.ai)
- [Orbstack](https://orbstack.dev)
- [itsycal](https://www.mowglii.com/itsycal/)

### Zed

Zed is an IDE that I discovered recently. It's absolutely phenomenal and blazing fast. Written in Rust. Unspoken rule on the web is that if an application is written in Rust, it'll be blazing fast.

I gave up on VSCode. I don't like Electron based applications. I tried Cursor; same concerns as VSCode.

### Maccy

I copy/paste things all the time. This is a clipboard history app.

### CotEditor

Quite a few times, I need to edit a text-based document, but I don't need a full IDE. CotEditor satisfies that itch. It's lightweight and fast.

### Alt-Tab

This is an absolute QoL improvement and totally optional. macOS has a terrible implementation of app switching when using the command key and tab combo. If you have multiple windows for an app, it's not very intuitive. Alt-Tab mimics the feature Windows has where you can see each open window for all open applications with a small preview.

### Bartender

Another QoL application. Newer MacBooks have a notch and Bartender can "hide" app icons in the menubar so they don't overflow.

### Little Snitch

This little application lets me block silly telemetry and nefarious ad calls made by applications. Install it and see where each application calls home. Microsoft tracks you like crazy with their applications. I block almost everything related to tracking how I use any application.

### Claude & Claude Code

Claude is my favorite AI/LLM model.

### Orbstack

Docker Desktop is garbage. Just use Orbstack.

### itsycal

Another QoL application that puts the current day on the menubar. Click it, and you get a monthly calendar. Super convenient.

## What I've Learned Over Time

Over the past few years, I've discovered that not every application lets me work the way I want to. However, the applications that do, I find it harder to use other machines (e.g., my work machine) that don't have those same applications. Perhaps the most important thing I appreciate is speed. I really dislike it when applications are laggy, not updated/maintained, and resource hogs. In this day and age of AI, it seems that many applications are just not as refined as they used to be. So my takeaway: I'm going to stay on the lookout for applications that adhere to speed, efficient memory management, and well maintained.
