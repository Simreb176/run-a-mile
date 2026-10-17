# Editing this site — a plain-English guide

This site is built from simple text files. You almost never need to touch any
code. Here's the short version:

**Your content lives in the `data/` folder.** Each file is a list of
information written in YAML — a very readable format that looks like this:

```yaml
- title: My First Run
  date: 2026-10-20
```

A colon separates a **label** from its **value**. Indentation matters: items
that line up belong together. When in doubt, copy the shape of what's already
there.

## The four content files

| File | What it holds |
|------|---------------|
| `data/posts.yml` | Your blog posts (newest at the top) |
| `data/training.yml` | Your running log — one line per run |
| `data/profile.yml` | Your name, your goal, and the stats on the home page |
| `data/site.yml` | The site title, description and contact email |

## Writing a blog post

Open `data/posts.yml` and add a new block at the **top** of the list:

```yaml
- date: 2026-10-20
  title: A Good Run Today
  slug: a-good-run-today        # this becomes the web address
  body: |
    Write your first paragraph here.

    Leave a blank line to start a new paragraph. You can make text **bold**
    or *italic*, and add [links](https://example.com) like this.
```

A few rules that keep things working:

- **Keep the dashes and indentation.** Every post starts with `- ` and each
  line under it is indented the same amount.
- **`slug`** is the part of the web address people will see. Lowercase, use
  hyphens instead of spaces, and don't reuse a slug you've already used.
- **`date`** must be in `YYYY-MM-DD` form.

## Logging a run

Open `data/training.yml` and add a line at the top:

```yaml
- date: 2026-10-20
  distance: 5.0 km
  duration: 32:15
  pace: 6:27 /km
  notes: Felt great today.
```

The `pace` and `notes` lines are optional — just leave them out if you like.

## Changing your goal or the home-page stats

Open `data/profile.yml`. The `goal` section has a `progress` number
(a percentage from 0 to 100) — update it as you get closer. The `stats` list
is the row of numbers on the home page; edit the values or add your own.

## Seeing your changes

After editing any file, the site needs to be **rebuilt**. From a terminal in
this folder:

```bash
.venv/bin/python serve.py
```

That rebuilds the site and shows it at:

- http://192.168.1.124:8083 — on your home network
- http://dev.rebecchi.uk:8083 — over the tailnet

Press `Ctrl+C` in the terminal to stop it.

## Publishing to the internet

Once this code is on GitHub, every time you **push to `main`** the site
rebuilds and republishes itself automatically. You don't run anything special
— just commit and push after rebuilding.

## If something breaks

The most common mistake is indentation — a line that's indented differently
from its neighbours. Compare your new block against the one above it and make
the spacing match. If a build fails, the error message will usually name the
file and line number.
