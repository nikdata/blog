# Backlog

Ideas and improvements for the blog that are not built yet.

## Instant, app-like page transitions

Make navigating between pages feel instant, with a smooth crossfade instead of a white flash. Inspired by blog.jim-nielsen.com, which is also a static site on Netlify and does this with almost no JavaScript.

### How it works

1. **Cross-document View Transitions.** One CSS rule tells the browser to crossfade between pages on navigation:

    ```css
    @view-transition {
      navigation: auto;
    }
    ```

2. **Shared-element morphing.** Give a post's title the same `view-transition-name` in the blog feed and on the post page. The browser then animates the title from its spot in the feed into the post's heading instead of just fading it.

3. **Speculation Rules (optional, goes beyond what Jim does).** A `<script type="speculationrules">` block prerenders a page when you hover its link, so it shows up with no wait when clicked.

### Implementation notes

- `assets/css/style.css`: add the `@view-transition` rule. Wrap it in `@media (prefers-reduced-motion: no-preference)` so people who turn off motion don't get the animation.
- `layouts/blog/list.html`: add `style="view-transition-name: post-title-{{ .File.ContentBaseName }}"` to the `<h2 class="post-title">`.
- `layouts/posts/single.html`: add the same `view-transition-name` to the `<h1>`.
- `layouts/_default/baseof.html`: optionally add the speculation rules block, using `"eagerness": "moderate"` (prerender on hover).
- Names must be unique on a page. Slugs are already unique across posts and blips, so the slug is a safe key.

### Browser support

Supported in Chrome, Edge, and Safari 18.2+. Firefox does normal page loads, so nothing breaks there.

### Rollout

Do it on a branch and check the Netlify deploy preview, since this is a visual change worth seeing before it goes live.

## GitHub Actions workflow

On push to main, check for duplicate slugs across posts and blips and fail the build if found. Simple shell commands in the workflow YAML, no Python scripts needed.

## Pre-commit hook for image resizing

Investigate using a pre-commit hook (via `git config core.hooksPath`) to automatically resize oversized images before they enter Git. For now, images are resized manually before committing.

## Favicon

Not yet created. Plan is something simple like initials or a single letter in the accent color.

## Analytics

May add GoatCounter (free for personal sites) later. Just a script tag.

## Custom domain

Currently nik.netlify.app. Considering short domains like nik.blog, nik.ink, or similar. Not a blocker.

## iCloud drafts workflow

Writing on iPad/phone in an iCloud-synced folder, with a script to move drafts into the repo. Deferred. For now, writing happens directly in the repo.

## Projects section

A new content type for longer-running creative projects (e.g., a 365-day photo challenge).

- Structure: `content/projects/<project-name>/` with each entry as a page bundle containing an image and optional caption.
- The project landing page (`/projects/<project-name>/`) displays a 4-column CSS Grid of thumbnails (2 columns on mobile), newest first.
- Hover overlay shows the entry count (e.g., "1/365").
- Clicking a thumbnail goes to a detail page with the full image and caption.
- Thumbnails generated at build time via Hugo's built-in image processing. Images use `loading="lazy"` for performance.
- A top-level `/projects/` page lists all projects. Nav integration TBD.

## Live heartbeat widget

A small pulsing heart icon (in the footer or on the homepage) that displays real heart rate data. Inspired by snehankekre.com/posts/hr/.

- Data source: Oura Ring API (most reliable since it's always worn).
- A GitHub Action runs on a schedule to fetch heart rate samples and export them to a static JSON file.
- Client-side JS replays yesterday's heart rate with interpolation.
- The CSS heartbeat animation pulses at the displayed BPM.
- No dedicated server needed.
