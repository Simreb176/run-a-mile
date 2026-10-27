#!/usr/bin/env python3
"""Run A Mile — static site generator.

Reads YAML from `data/`, renders Jinja templates from `templates/`,
and writes the finished site to `docs/`.

    .venv/bin/python generate.py        # or: python3 generate.py

`docs/` is the built site. It is committed so the result is easy to preview
and review, but the live copy at runamile.co.uk is built fresh in GitHub
Actions on every push to `main` (see `.github/workflows/pages.yml`).
Run this script after editing data or templates, then commit the changes.
"""
from datetime import datetime
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup

try:
    import markdown
except ImportError:  # markdown is optional — see requirements.txt
    markdown = None

ROOT = Path(__file__).parent
DATA = ROOT / "data"
TEMPLATES = ROOT / "templates"
# Static files that ship with the site, copied verbatim into the output.
# `styles.css` is linked from base.html, so it lives in the site root.
ASSETS = ["styles.css", "favicon.svg"]
OUTPUT = ROOT / "docs"

# Files that must survive a rebuild.
PRESERVE = {"CNAME", ".nojekyll"}

# Where each top-level page lives in the generated site.
# template -> (output file, page id used to highlight the active nav link)
PAGES = {
    "index.html": ("index.html", "home"),
    "blog.html": ("blog.html", "blog"),
    "log.html": ("log.html", "log"),
    "about.html": ("about.html", "about"),
}

# The social links shown in the footer and on the About page, in this order.
# Add or remove networks here; the labels are what visitors see.
SOCIAL_LINKS = [
    ("instagram", "Instagram"),
    ("facebook", "Facebook"),
    ("strava", "Strava"),
]


def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f) or []


def render_markdown(text):
    """Render post bodies. Uses the markdown package if available, otherwise
    falls back to simple paragraph wrapping."""
    if not text:
        return ""
    if markdown is not None:
        return Markup(markdown.markdown(text.strip()))
    parts = [p.strip() for p in text.strip().split("\n\n") if p.strip()]
    return Markup("\n".join(f"<p>{p}</p>" for p in parts))


def parse_date(value):
    if isinstance(value, datetime):
        return value
    return datetime.strptime(str(value), "%Y-%m-%d")


def load_posts():
    posts = []
    for raw in load_yaml(DATA / "posts.yml"):
        post = dict(raw)
        post["date"] = parse_date(raw.get("date"))
        post["slug"] = post.get("slug") or post["title"].lower().replace(" ", "-")
        post["excerpt"] = (post.get("body") or "").strip().split("\n")[0]
        words = len((post.get("body") or "").split())
        post["reading_time"] = max(1, round(words / 200))
        posts.append(post)
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main():
    site = load_yaml(DATA / "site.yml")
    profile = load_yaml(DATA / "profile.yml")
    about = load_yaml(DATA / "about.yml")
    posts = load_posts()
    training = sorted(
        load_yaml(DATA / "training.yml"),
        key=lambda r: str(r.get("date", "")),
        reverse=True,
    )

    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=True)
    env.filters["markdown"] = render_markdown

    context = {
        "site": site,
        "profile": profile,
        "about": about,
        "posts": posts,
        "training": training,
        "social_links": [
            {"name": label, "url": (site.get("social") or {}).get(key)}
            for key, label in SOCIAL_LINKS
            if (site.get("social") or {}).get(key)
        ],
        "year": datetime.now().year,
    }

    # Start each build from a clean slate, keeping only the files we must keep.
    if OUTPUT.exists():
        for child in OUTPUT.iterdir():
            if child.name in PRESERVE:
                continue
            if child.is_dir():
                import shutil

                shutil.rmtree(child)
            else:
                child.unlink()
    OUTPUT.mkdir(parents=True, exist_ok=True)

    for template_name, (out_name, page_id) in PAGES.items():
        template = env.get_template(template_name)
        write(OUTPUT / out_name, template.render(base="", page=page_id, **context))
        print(f"  {out_name}")

    # Individual post pages: docs/posts/<slug>/index.html
    for i, post in enumerate(posts):
        newer = posts[i - 1] if i > 0 else None
        older = posts[i + 1] if i < len(posts) - 1 else None
        template = env.get_template("post.html")
        html = template.render(
            post=post, newer=newer, older=older, base="../../", page="post", **context
        )
        write(OUTPUT / "posts" / post["slug"] / "index.html", html)
        print(f"  posts/{post['slug']}/index.html")

    # A blank file telling GitHub Pages to serve the site as-is
    # (no Jekyll processing).
    write(OUTPUT / ".nojekyll", "")

    # Copy static assets.
    for asset in ASSETS:
        src = ROOT / asset
        if src.exists():
            write(OUTPUT / asset, src.read_text(encoding="utf-8"))
            print(f"  {asset}")

    # Copy the custom domain file so GitHub Pages serves runamile.co.uk.
    cname = ROOT / "CNAME"
    if cname.exists():
        write(OUTPUT / "CNAME", cname.read_text(encoding="utf-8"))
        print("  CNAME")

    print(f"\nDone — {len(PAGES)} pages + {len(posts)} posts written to {OUTPUT}/")


if __name__ == "__main__":
    main()
