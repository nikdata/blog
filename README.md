# Niks Tavern

Personal blog of Nikhil Agarwal. Built with Hugo and hosted on Netlify.

## Local Development

Install Hugo with Homebrew if you have not already:

```bash
brew install hugo
```

Start the local development server:

```bash
hugo server --buildDrafts
```

The site will be available at `http://localhost:1313`. The `--buildDrafts` flag includes draft posts so you can preview them locally before publishing.

## Creating Content

### New Post

Posts are longer form writing. Each post lives in its own folder under `content/posts/`.

```bash
hugo new posts/my-post-slug/index.md
```

This creates a new post with `draft: true` in the frontmatter. When you are ready to publish, change `draft` to `false` and set the `date` field.

### New Blip

Blips are short form content: quick thoughts, links, photos. Simple text blips are single files. Blips with images get their own folder.

Text-only blip:

```bash
hugo new blips/my-blip-slug.md
```

Blip with an image:

```bash
hugo new blips/my-blip-slug/index.md
```

Then place any images in the same folder alongside `index.md`.

## Content Structure

```
content/
  posts/          # Long form writing (essays, tutorials, etc.)
    my-post/
      index.md
      image.jpg
  blips/          # Short form (links, photos, quick thoughts)
    my-blip.md
    my-photo-blip/
      index.md
      photo.jpg
  about.md        # About page
```

Posts and blips both appear in a single blended feed, sorted by date. Blips render their full content inline with a tinted card background. Posts show a title, summary, and a link to the full article.

## URL Structure

Both posts and blips are served under `/blog/`:

- `https://nik.netlify.app/blog/my-post/`
- `https://nik.netlify.app/blog/my-blip/`

Because they share a URL prefix, slugs must be unique across posts and blips.

## Publishing

Push to the `main` branch. Netlify picks up the change and deploys automatically.

For longer posts where you want to preview first, create a branch and push it. Netlify generates a deploy preview for every branch.

## Dark Mode

The site respects the visitor's system preference and also provides a manual toggle in the header. The preference is stored in the browser's local storage.
