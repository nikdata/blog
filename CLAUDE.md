# Blog Project

Personal blog for Nikhil Agarwal. Built with Hugo, hosted on Netlify at nik.netlify.app.

## What This Blog Is

A personal blog called "Niks Tavern." The primary goal is to build a writing habit as a way to process thoughts. The blog is public as a quality forcing function, but the audience is Nikhil himself. If a post happens to go viral or get posted on Hacker News, the quality bar should hold up, but the blog is not optimized for reach, SEO, or monetization.

There are no comments, no analytics (may be added later via GoatCounter), and no monetization.

## Content Types

There are two content types that blend into a single chronological stream on the `/blog/` page:

- **Posts** (`content/posts/`): Long-form essays. Each post lives in its own folder as a Hugo page bundle (`content/posts/my-slug/index.md`). Posts show as a title + summary + "Read more" link in the blog feed. Posts can optionally have a cover image that appears as a thumbnail in the feed.
- **Blips** (`content/blips/`): Short-form content such as quick thoughts, link commentary, photos. Named after SRAM Blips (small versatile buttons on bike handlebars). Text-only blips are single files (`content/blips/my-slug.md`). Blips with images get their own folder (`content/blips/my-slug/index.md`). Blips render their full content inline in the blog feed with a tinted card background to visually distinguish them from posts.

Both types share the same URL prefix: `/blog/slug/`. Slugs must be unique across posts and blips since they share a namespace.

## Site Structure

- **Homepage (`/`)**: Centered landing page with profile photo, tagline, description, and social icons (GitHub, LinkedIn, Bluesky). Inspired by foosel.net.
- **Blog (`/blog/`)**: Blended chronological feed of posts and blips with pagination.
- **About (`/about/`)**: Standalone page for a longer bio.
- **Individual post/blip pages (`/blog/slug/`)**: Full content view.

## Design Decisions

- Clean, warm, minimal aesthetic. Not brutalist, not magazine-style.
- Dark/light mode respects system preference with a manual toggle (small amount of JS, preference stored in localStorage). In dark mode, the sun icon shows (click to switch to light). In light mode, the moon icon shows.
- Warm accent color in light mode, muted warm tone in dark mode.
- Max reading width of ~680px, good typography, comfortable spacing.
- Font: Lato (loaded from Google Fonts CDN).
- Font Awesome via CDN for social icons (chosen over inline SVGs for easy extensibility when adding new social links).
- Navigation links and social icons are data-driven from `hugo.toml` (not hardcoded in templates). To add a nav link, add a `[[menus.main]]` entry. To add a social icon, add a `[[params.social]]` entry with name, icon (Font Awesome brand icon name), url, and weight.
- Navigation: Home, Blog, About, dark mode toggle, RSS feed icon. Social icons on the landing page only.
- RSS: single combined feed for both posts and blips.
- No taxonomies (tags/categories) for now.
- Code syntax highlighting is enabled (Dracula theme) for occasional code-related posts.
- Post cover images are optional. Only use them when you have a real, relevant image. Do not use stock photos or force an image on every post.

## Folder Structure

```
content/
  posts/          # Long-form (page bundles with index.md)
    my-post/
      index.md
      cover.jpg   # Optional cover image
  blips/          # Short-form (single .md or page bundle for image blips)
    my-blip.md
    my-photo-blip/
      index.md
      photo.jpg
  blog/
    _index.md     # Routing file for /blog/ page. Do not put content here.
  about.md
layouts/
  _default/       # baseof.html, index.html (landing page), list.html, single.html
  blog/           # list.html for the /blog/ feed page
  posts/          # single.html for post pages
  blips/          # single.html for blip permalinks
  partials/       # header.html, footer.html
assets/
  css/style.css
  js/theme-toggle.js
static/
  images/         # Site-wide images (profile photo, favicon, etc.)
archetypes/
  posts.md        # Template for `hugo new posts/my-slug/index.md`
  blips.md        # Template for `hugo new blips/my-slug.md`
```

## Drafts and Publishing Workflow

- New content starts with `draft: true` in frontmatter. Change to `draft: false` and set the `date` field when ready to publish.
- No dates in folder names. The date lives only in frontmatter to avoid the "started on one day, finished on another" mismatch.
- **Fast path** (blips, simple posts): Write on main, push directly. Netlify deploys automatically.
- **Careful path** (longer posts): Create a branch, write, push. Netlify generates a deploy preview for the branch. Merge to main when satisfied.
- Not every post needs a PR. Reserve the branch/preview workflow for posts where visual review matters.

## Planned but Not Yet Built

These items were discussed and agreed upon but are not implemented yet:

- **GitHub Actions workflow**: On push to main, check for duplicate slugs across posts and blips and fail the build if found. Simple shell commands in the workflow YAML, no Python scripts needed.
- **Pre-commit hook for image resizing**: Investigate using a pre-commit hook (via `git config core.hooksPath`) to automatically resize oversized images before they enter Git. For now, images are resized manually before committing.
- **Favicon**: Not yet created. Plan is something simple like initials or a single letter in the accent color.
- **Analytics**: May add GoatCounter (free for personal sites) later. Just a script tag.
- **Custom domain**: Currently nik.netlify.app. Considering short domains like nik.blog, nik.ink, or similar. Not a blocker.
- **iCloud drafts workflow**: Writing on iPad/phone in an iCloud-synced folder, with a script to move drafts into the repo. Deferred. For now, writing happens directly in the repo.
- **Projects section**: A new content type for longer-running creative projects (e.g., a 365-day photo challenge). Structure: `content/projects/<project-name>/` with each entry as a page bundle containing an image and optional caption. The project landing page (`/projects/<project-name>/`) displays a 4-column CSS Grid of thumbnails (2 columns on mobile), newest first. Hover overlay shows the entry count (e.g., "1/365"). Clicking a thumbnail goes to a detail page with the full image and caption. Thumbnails generated at build time via Hugo's built-in image processing. Images use `loading="lazy"` for performance. A top-level `/projects/` page lists all projects. Nav integration TBD.
- **Live heartbeat widget**: A small pulsing heart icon (in the footer or on the homepage) that displays real heart rate data. Inspired by snehankekre.com/posts/hr/. Data source: Oura Ring API (most reliable since it's always worn). A GitHub Action runs on a schedule to fetch heart rate samples and export them to a static JSON file. Client-side JS replays yesterday's heart rate with interpolation. The CSS heartbeat animation pulses at the displayed BPM. No dedicated server needed.

## Local Development

```bash
hugo server --buildDrafts
```

Site available at http://localhost:1313. The `--buildDrafts` flag shows draft content locally.

## Creating Content

```bash
# New post
hugo new posts/my-post-slug/index.md

# New text blip
hugo new blips/my-blip-slug.md

# New blip with image
hugo new blips/my-blip-slug/index.md
# Then place images in the same folder
```

## Quick Reference: What File To Edit

| I want to change...                        | Edit this file                          |
|--------------------------------------------|-----------------------------------------|
| Colors, fonts, spacing, layout             | `assets/css/style.css`                  |
| The nav bar (links, logo, toggle)          | `layouts/partials/header.html`          |
| The footer (copyright)                     | `layouts/partials/footer.html`          |
| The landing page (photo, bio, social)      | `layouts/_default/index.html`           |
| The blog feed (stream of posts/blips)      | `layouts/blog/list.html`               |
| How a single post page looks               | `layouts/posts/single.html`            |
| How a single blip permalink looks          | `layouts/blips/single.html`            |
| The About page or other standalone pages   | `layouts/_default/single.html`          |
| The outer HTML shell (head, meta, scripts) | `layouts/_default/baseof.html`          |
| Dark/light toggle behavior                 | `assets/js/theme-toggle.js`            |
| Site title, URLs, social links, settings   | `hugo.toml`                             |
| Default frontmatter for new posts          | `archetypes/posts.md`                   |
| Default frontmatter for new blips          | `archetypes/blips.md`                   |

There is no themes folder. All templates and styles live directly in the project.

## Custom Components

### Prompt Block

For displaying AI prompts with a labeled container. Wrap a code block in a `<div class="prompt">`:

    <div class="prompt">
    
    ```
    Your prompt text here
    ```
    
    </div>

This renders with an accent-colored "PROMPT" label, a left border, and vertical scrolling for long prompts. Works in both dark and light mode.

## Style Guidelines

- Do not use em-dashes, emojis, or emoticons in any generated content (README, blog posts, etc.).
- Writing should sound natural and human, not like it was generated by an LLM.
- The blog's voice is personal and opinionated. Posts do not need deep research or citations. It is fine to just share opinions.
