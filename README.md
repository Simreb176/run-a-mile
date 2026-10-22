# Run A Mile

A personal blog and training log documenting a return to running, live at
**[runamile.co.uk](https://runamile.co.uk)**. The site is generated from YAML
data using Python and Jinja2, then published for free on GitHub Pages.

A custom domain is attached via the `CNAME` file in this repo.

## Documentation

| File | For whom | What it covers |
|------|----------|----------------|
| **[EDITING.md](EDITING.md)** | The site owner (non-technical) | Plain-English guide to editing content, changing the look, previewing and publishing |
| **[AGENTS.md](AGENTS.md)** | AI agents working on the site | Build/preview/deploy workflow, and how to work with the owner |
| **README.md** (this file) | Developers | The technical overview |

If you're the owner: read **EDITING.md**. Everything here can be done for you by
asking the AI assistant — you never need to run a command.

## How it works

```
data/*.yml        ← all the content lives here (edit these)
templates/*.html  ← the layouts (Jinja2 templates, incl. _macros.html)
styles.css        ← the styling (design tokens are in section 1)
generate.py       ← reads the YAML, renders the templates into a static site
docs/             ← the generated site (committed for review/preview)
editor.py         ← the owner's editing page, as a service on port 9001
```

The workflow is: edit the YAML (or templates/styles), run `generate.py`, commit
the result. GitHub Actions rebuilds and publishes on every push to `main`.

## Editing the content

Everything is driven by the files in `data/`:

| File            | What it controls                                              |
|-----------------|---------------------------------------------------------------|
| `site.yml`      | Site title, description, contact email, social links, SEO text |
| `profile.yml`   | Who you are, your goal, and the quick stats on the home page   |
| `posts.yml`     | The blog posts (newest at the top)                            |
| `training.yml`  | The running log (one line per run)                            |

### Adding a blog post

Add a new block at the top of the list in `data/posts.yml`:

```yaml
- date: 2026-10-20
  title: My Next Run
  slug: my-next-run          # becomes the URL: /posts/my-next-run/
  body: |
    The first paragraph goes here.

    Blank lines separate paragraphs. **Bold**, *italic*, headings, lists,
    quotes and [links](https://example.com) all work (Markdown).
```

Then rebuild and commit.

## The design

- **`styles.css`** is a single hand-written stylesheet. Section 1 defines every
  colour, font and sizing token as a CSS custom property; the rest of the file
  consumes them. Changing `--accent` (or any token) restyles the whole site.
- It ships a **dark theme** (via `prefers-color-scheme`), a responsive layout
  (the training table becomes cards on narrow screens), and honours
  `prefers-reduced-motion`.
- Templates share chrome and reusable snippets through `templates/base.html` and
  `templates/_macros.html` (post cards, the run table, the goal card).
- Pages live at the site root except posts, which are written to
  `/posts/<slug>/`. Templates therefore build every link from a `base` prefix
  (`""` for root pages, `"../"` for posts) — keep using `{{ base }}` when adding
  links.

## Building locally

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python generate.py
```

## The editing page

`editor.py` is a small Flask app that lets the (non-technical) owner change the
words on the site from a browser, without touching YAML. It runs as a systemd
service on port **9001**:

```bash
.venv/bin/pip install -r requirements-editor.txt   # Flask + ruamel.yaml
make deploy                                        # install, enable and start it
```

- **Save** writes `data/*.yml` and rebuilds `docs/`; **Publish** also commits and
  pushes, so GitHub Pages picks it up.
- **There is no login.** It binds `0.0.0.0` (required for the tailnet) but is not
  reachable from the public internet — see `deploy/runamile-editor.service`.
- Blog posts are written on their own screen (`/posts`): a list with Edit and
  Delete, and a writing form. Deleting removes the post and its generated page.
  The main screen handles details, goal, runs and site settings.
- Writes are conservative: values that haven't changed are left byte-identical
  (comments, quoting and folded prose included), so a no-op save produces no
  diff. `data/posts.yml` and `data/training.yml` are re-emitted in the same
  shape the hand-written versions use.
- Its screens live in `editor_templates/`, with `editor_static/editor.css` —
  deliberately separate from the website's `templates/` and `styles.css`.
- `make status`, `make logs` and `make undeploy` do what they say; `make preview`
  and `make edit` run the preview and the page in the foreground.

## Previewing the site

```bash
.venv/bin/python serve.py
```

This rebuilds the site and serves it on `0.0.0.0:8080`:

- development version: http://simon-dev.rebecchi.uk:8080
- local network: http://192.168.1.127:8080

## Publishing to GitHub Pages

The site deploys automatically when you push to `main` (via
`.github/workflows/pages.yml`). This is already set up:

1. ✅ The repo exists and `main` is pushed.
2. ✅ **Settings → Pages → Source** is set to **GitHub Actions**.
3. ✅ The `CNAME` file and DNS point `runamile.co.uk` at GitHub Pages.

So publishing is simply:

```bash
git add -A
git commit -m "Describe the change"
git push origin main
```

(or the **Publish** button on the editing page, which runs exactly that). Check
the deploy by watching the Actions tab; the site updates about a minute after a
green run.
