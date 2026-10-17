# Run A Mile

A personal blog and training log documenting a return to running. The site is
generated from YAML data using Python and Jinja2, then hosted for free on
GitHub Pages. A custom domain (`runamile.co.uk`) is attached via the `CNAME`
file in this repo.

## How it works

```
data/*.yml      ← all the content lives here (edit these)
templates/*.html← the layout (Jinja2 templates)
styles.css      ← the styling
generate.py     ← reads the YAML, renders the templates into a static site
docs/           ← the generated site (this is what gets published)
```

You edit the YAML, run `generate.py`, and commit the result. GitHub Pages
serves whatever is in `docs/`.

## Editing the content

Everything is driven by the files in `data/`:

| File            | What it controls                                              |
|-----------------|---------------------------------------------------------------|
| `site.yml`      | Site title, description, contact email, SEO text              |
| `profile.yml`   | Who you are, your goal, and the quick stats on the home page   |
| `posts.yml`     | The blog posts (newest at the top)                            |
| `training.yml`  | The running log (one line per run)                            |

### Adding a blog post

Add a new block to the top of the list in `data/posts.yml`:

```yaml
- date: 2026-10-20
  title: My Next Run
  slug: my-next-run          # becomes the URL: /posts/my-next-run/
  body: |
    The first paragraph goes here.

    Blank lines separate paragraphs. **Bold**, *italic* and
    [links](https://example.com) work too (Markdown).
```

Then rebuild and commit.

## Building locally

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python generate.py
```

## Previewing the site

```bash
.venv/bin/python serve.py
```

This rebuilds the site and serves it on `0.0.0.0:8083`:

- local network: http://192.168.1.124:8083
- tailnet: http://dev.rebecchi.uk:8083

## Publishing to GitHub Pages

The site deploys automatically when you push to `main` (via
`.github/workflows/pages.yml`). One-time setup:

1. Create the repo on GitHub and push this code to `main`.
2. Go to **Settings → Pages** and set **Source** to **GitHub Actions**.
3. The first build deploys the site at `https://<username>.github.io/<repo>/`.
4. To use `runamile.co.uk`, add the domain in **Settings → Pages → Custom
   domain** (the `CNAME` file is already in the repo) and point the DNS
   records at GitHub once the domain is registered.
