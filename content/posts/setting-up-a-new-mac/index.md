---
title: "How I Set Up My New MacBook Air"
date: 2026-06-08
description: "A clean install instead of a migration. It takes longer, but you only keep what you actually use."
draft: true
---

I recently picked up a new MacBook Air and decided to do a clean setup instead of migrating from a backup. It takes a bit longer, but it forces me to only install what I actually use.

## The Essentials

First things first: Homebrew. Everything else flows from there.

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Then the core tools:

```bash
brew install git python node hugo
```

## Editor Setup

I have been using VS Code for years now, but I keep my extensions minimal:

- Python
- Markdown All in One
- GitLens
- A dark theme (naturally)

## The Philosophy

The temptation is always to install everything you *might* need. I have learned to wait until I actually need something before installing it. My machine stays fast and I spend less time managing tools and more time using them.
