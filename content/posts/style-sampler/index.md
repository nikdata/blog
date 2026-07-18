---
title: "Style Sampler"
date: 2026-06-24
description: "A reference page showing every text element and component this blog supports."
draft: true
---

This post exists as a visual reference for every typographic and layout element the blog can render. It is not meant to be published. Keep it as `draft: true` and view it locally with `hugo server --buildDrafts`.

# Heading Level 1

H1 is normally reserved for the post title (rendered by the template above). Using it in the body creates a second H1, which is not ideal for document structure, but this is what it looks like.

## Heading Level 2

The primary section heading inside a post. Body text is set in Lato at 18px with a line-height of 1.7. The max content width is 680px. Here is a [hyperlink to the homepage](/) for reference, and here is some **bold text** alongside *italic text* to show emphasis styles.

### Heading Level 3

Use H3 for subsections within a larger topic. Slightly smaller and with less vertical margin than H2.

#### Heading Level 4

A fourth-level heading. Useful for deeply nested structure, though most posts should not need to go this deep.

##### Heading Level 5

Fifth-level heading. Rarely used in practice.

###### Heading Level 6

Sixth-level heading. The smallest available.

## Inline Formatting

Regular text. **Bold text.** *Italic text.* ***Bold and italic.*** ~~Strikethrough text.~~ Inline `code` looks like this, rendered in a monospace font with a subtle background.

## Blockquote

> This is a blockquote. It gets a left border in the accent color and renders in italic with secondary text color. Useful for quoting someone or calling out a key idea.

> Multi-paragraph blockquotes work too.
>
> This is the second paragraph inside the same blockquote.

## Unordered List

- First item in the list
- Second item, which is a bit longer to show how wrapping behaves when the text extends beyond a single line in the container
- Third item
  - Nested item under the third
  - Another nested item

## Ordered List

1. First step
2. Second step
3. Third step, again with some extra length so you can see how numbered items wrap at the content width
   1. A nested numbered item
   2. Another nested numbered item

## Code Blocks

Inline code was shown above. Here is a fenced code block with syntax highlighting:

```python
import pandas as pd

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Remove rows with missing timestamps."""
    before = len(df)
    df = df.dropna(subset=["timestamp"])
    print(f"Dropped {before - len(df)} rows")
    return df
```

And one without a language specified:

```
This is a plain code block.
No syntax highlighting, just monospace text
with preserved whitespace.
```

## Prompt Block

The custom prompt component wraps a code block in a labeled container with an accent-colored "PROMPT" badge and vertical scroll for long content.

<div class="prompt">

```
You are a data analyst. Given the following CSV schema, write a Python script
that reads the file, cleans missing values, and produces a summary table
grouped by region. Use pandas. Output the result to stdout as a markdown table.

Schema:
- region (string)
- date (ISO 8601)
- revenue (float, nullable)
- units_sold (int, nullable)
```

</div>

## Images

Images render at full content width with a small border radius. Since this is a draft-only sampler, here is the markup you would use:

```markdown
![Alt text describing the image](image-filename.jpg)
```

If you place an image file in this folder (`content/posts/style-sampler/`), Hugo will serve it as part of the page bundle.

## Horizontal Rule

Three dashes produce a horizontal rule:

---

The rule above separates this paragraph from the previous section.

## Table

Hugo supports GitHub-flavored markdown tables:

| Element       | Tag / Class         | Custom Styling? |
|:--------------|:-------------------:|----------------:|
| Heading 2     | `h2`                | Yes             |
| Heading 3     | `h3`                | Yes             |
| Blockquote    | `blockquote`        | Yes             |
| Code block    | `pre > code`        | Yes             |
| Prompt block  | `.prompt`           | Yes             |
| Table         | `table`             | Yes             |

Column alignment is controlled in the separator row: `:---` for left, `:---:` for center, `---:` for right. The table above uses left, center, and right respectively.

## Footnotes

Hugo supports footnotes via the Goldmark renderer. Here is a sentence with a footnote[^1].

[^1]: This is the footnote content. It will render at the bottom of the post.

## Line Breaks and Spacing

Sometimes you need a hard line break within a paragraph.
This line was separated with a trailing double space (or a backslash in some renderers), not a new paragraph.

This is a separate paragraph, with the standard 1.25rem bottom margin between it and the text above.

## Combined Example

To close out, here is a realistic passage mixing several elements to show how they flow together in practice.

### Analyzing the results

After running the pipeline, I noticed something odd in the output. The counts were off by exactly one in every group:

> Off-by-one errors account for roughly 50% of all software bugs.
> -- Someone, probably

The fix was a single character. Changing `range(1, n)` to `range(0, n)` resolved it:

```python
for i in range(0, n):
    process(items[i])
```

The key takeaway: when counts are wrong by a consistent offset, check your loop bounds before anything else.
