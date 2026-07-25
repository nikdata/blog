---
title: "{{ replace .File.ContentBaseName `-` ` ` | title }}"
slug: "{{ .File.ContentBaseName }}"
date: {{ .Date.Format "2006-01-02" }}
description: "" # Byline: 1-2 sentences shown as preview on the homepage. Write something enticing, not just the opening line.
cover: "" # Optional cover image filename (e.g., "cover.jpg"). Place image in the same folder.
draft: true
---
