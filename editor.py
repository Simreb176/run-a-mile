#!/usr/bin/env python3
"""Run A Mile — the "edit it yourself" page.

A small web app that lets the site's owner change the words on runamile.co.uk
from a browser, with no YAML, no commands and no git:

    .venv/bin/python editor.py
    # then open http://simon-dev.rebecchi.uk:8091

There are only two buttons that matter:

    Save      writes the words back to data/*.yml and rebuilds the preview
    Publish   Save, then commits and pushes — the live site follows in a minute

Saving is deliberately gentle: values that haven't changed are left exactly as
they are in the file (comments, quoting and all), and the two list files are
rewritten in the same shape the hand-written versions use, so a save that
changes nothing produces no diff at all. Every version is in git regardless,
so nothing here can lose work.

Dependencies are listed in `requirements-editor.txt` (Flask + ruamel.yaml).
Only this script needs them — the website build itself uses `requirements.txt`.
"""
from __future__ import annotations

import os
import re
import secrets
import socket
import subprocess
import sys
import time
from datetime import date
from io import StringIO
from pathlib import Path

import textwrap

from flask import (
    Flask,
    flash,
    get_flashed_messages,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import LiteralScalarString

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
TEMPLATES = ROOT / "editor_templates"

# The dev preview (serve.py) and this editor. Both bind to 0.0.0.0 so they are
# reachable over the tailnet, not just on the LAN.
PREVIEW_PORT = 8080
HOST = "0.0.0.0"
PORT = int(os.environ.get("EDITOR_PORT", "8091"))

# Kept out of git (see .gitignore): the password, the session key, preview log.
PASS_FILE = ROOT / ".editor-pass"
SECRET_FILE = ROOT / ".editor-secret"
PREVIEW_LOG = ROOT / ".preview.log"

COMMIT_MESSAGE = "Content update from the editing page"
PROSE_WIDTH = 78  # how wide the long paragraphs are wrapped in the YAML files

# Values YAML would otherwise reinterpret if they were left bare.
TIME_RE = re.compile(r"^\d{1,3}:\d{2}(:\d{2})?$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
NUMBER_RE = re.compile(r"[-+]?(\d[\d_]*(\.\d*)?|\.\d+)([eE][-+]?\d+)?")
YAML_WORDS = {"true", "false", "yes", "no", "on", "off", "null", "~", "none"}


class EditorError(Exception):
    """Something we can explain to the person typing, rather than a traceback."""


# --------------------------------------------------------------------------
# Reading and writing YAML
# --------------------------------------------------------------------------
def yaml_io(indent_sequences=False):
    """A round-trip YAML parser: comments, order and quoting all survive.

    The two mapping files (site.yml, profile.yml) keep their lists indented
    under their key — hence the different sequence indent for those.
    """
    y = YAML()
    y.preserve_quotes = True
    y.width = 4096  # never re-wrap long sentences behind our back
    if indent_sequences:
        y.indent(mapping=2, sequence=4, offset=2)
    else:
        y.indent(mapping=2, sequence=2, offset=0)
    return y


def load(path):
    with open(path, encoding="utf-8") as f:
        data = yaml_io(indent_sequences=path.name in {"site.yml", "profile.yml"}).load(f)
    return {} if data is None else data


def dump(path, data):
    y = yaml_io(indent_sequences=path.name in {"site.yml", "profile.yml"})
    buf = StringIO()
    y.dump(data, buf)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(buf.getvalue(), encoding="utf-8")
    os.replace(tmp, path)  # atomic: a crash can't leave a half-written file


def normalise(text):
    """Textarea newlines arrive as CRLF; the files use LF."""
    return str(text).replace("\r\n", "\n").replace("\r", "\n")


def same(current, value):
    if current is None or value is None:
        return current is None and value is None
    return normalise(current).strip() == normalise(value).strip()


def set_value(mapping, key, value):
    """Set a key, but leave the existing one completely alone if it's unchanged.

    That's what keeps comments, quoting (`"32:15"`) and the folded style of
    long paragraphs intact when someone saves without editing them.
    """
    if key in mapping and same(mapping[key], value):
        return
    mapping[key] = value


def slugify(raw):
    return re.sub(r"[^a-z0-9]+", "-", normalise(raw).strip().lower()).strip("-")


# --------------------------------------------------------------------------
# Formatting values for the hand-written files
# --------------------------------------------------------------------------
def needs_quotes(text):
    if not text or text != text.strip():
        return True
    if TIME_RE.match(text) or DATE_RE.match(text):
        return True
    if text[0] in "-?:,[]{}#&*!|>'\"%@`":
        return True
    if ": " in text or text.endswith(":") or " #" in text:
        return True
    return text.lower() in YAML_WORDS or bool(NUMBER_RE.fullmatch(text))


def fmt_scalar(text):
    return f'"{text}"' if needs_quotes(text) else text


def fmt_block(text, indent, wrap=True):
    """A `|` block: prose is wrapped, and the lines are otherwise kept as typed."""
    lines = normalise(text).rstrip("\n").split("\n")
    if wrap:
        wrapped = []
        for para in "\n".join(lines).split("\n\n"):
            joined = " ".join(para.split())
            if joined:
                wrapped.extend(textwrap.wrap(joined, PROSE_WIDTH - indent) or [""])
            wrapped.append("")
        wrapped.pop()
        lines = wrapped
    return "\n".join((" " * indent) + line.rstrip() if line.strip() else "" for line in lines)


def leading_comments(path):
    """Whatever sits at the top of the file — its explanatory comment block."""
    lines = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.lstrip().startswith("#"):
            break
        lines.append(line)
    return "\n".join(lines).rstrip()


def write_rows_file(path, rows, block_keys=()):
    """Write a `- date: ...` style list file, keeping the file's own header."""
    blocks = []
    for row in rows:
        lines = []
        first = True
        for key, value in row.items():
            if value is None or value == "":
                continue
            prefix = "- " if first else "  "
            if key in block_keys:
                lines.append(f"{prefix}{key}: |")
                # Post text is kept exactly as typed: markdown lists and quotes
                # would not survive being re-wrapped.
                lines.append(fmt_block(value, 4, wrap=False))
            elif key == "date":
                lines.append(f"{prefix}{key}: {value}")  # bare, so it reads as a date
            else:
                lines.append(f"{prefix}{key}: {fmt_scalar(normalise(value).strip())}")
            first = False
        blocks.append("\n".join(lines))

    parts = [leading_comments(path)] + blocks if blocks else [leading_comments(path)]
    text = "\n\n".join(part for part in parts if part) + "\n"
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


# --------------------------------------------------------------------------
# The form -> the files
# --------------------------------------------------------------------------
def form_rows(form, fields, essential):
    """Collect a repeatable block of rows, in the order they appear on screen."""
    columns = [form.getlist(name) for name in fields]
    out = []
    for values in zip(*columns):
        row = {name: normalise(value).strip() for name, value in zip(fields, values)}
        if not row.get(essential):
            continue  # the blank "add a new one" row, or a row that's been emptied
        out.append(row)
    return out


def clean_date(raw, label, problems):
    text = normalise(raw).strip()
    if not DATE_RE.match(text):
        problems.append(f"{label}: “{text}” isn't a date I recognise — they look like 2026-10-20")
    return text


def save_site(form):
    site = load(DATA / "site.yml")
    set_value(site, "title", normalise(form.get("site_title")).strip())
    set_value(site, "description", normalise(form.get("site_description")).strip())
    set_value(site, "url", normalise(form.get("site_url")).strip())

    author = site.get("author") or {}
    set_value(author, "name", normalise(form.get("author_name")).strip())
    set_value(author, "tagline", normalise(form.get("author_tagline")).strip())
    set_value(author, "location", normalise(form.get("author_location")).strip())
    set_value(author, "email", normalise(form.get("author_email")).strip())

    social = site.get("social") or {}
    for network in ("github", "strava", "twitter"):
        value = normalise(form.get(f"social_{network}")).strip()
        set_value(social, network, value or None)

    seo = site.get("seo") or {}
    set_value(seo, "description", normalise(form.get("seo_description")).strip())

    dump(DATA / "site.yml", site)


def number_or_text(text):
    """Stats read better as numbers when they are numbers."""
    return int(text) if re.fullmatch(r"-?\d+", text) else text


def save_profile(form, progress):
    profile = load(DATA / "profile.yml")
    set_value(profile, "name", normalise(form.get("profile_name")).strip())
    set_value(profile, "eyebrow", normalise(form.get("profile_eyebrow")).strip())
    set_value(profile, "tagline", normalise(form.get("profile_tagline")).strip())
    set_value(profile, "location", normalise(form.get("profile_location")).strip())

    intro = normalise(form.get("profile_intro")).strip("\n")
    if not same(profile.get("intro"), intro):
        # A literal block, so the paragraphs stay readable in the file.
        profile["intro"] = LiteralScalarString(fmt_block(intro, 2) + "\n")

    goal = profile.get("goal") or {}
    set_value(goal, "label", normalise(form.get("goal_label")).strip())
    set_value(goal, "target", normalise(form.get("goal_target")).strip())
    set_value(goal, "progress", min(100, int(progress)) if progress else 0)

    # Reuse the existing rows where we can, so their formatting stays untouched.
    pool = {}
    for row in profile.get("stats") or []:
        pool.setdefault(str(row.get("label", "")), []).append(row)
    stats = []
    for row in form_rows(form, ["stat_label", "stat_value"], essential="stat_label"):
        waiting = pool.get(row["stat_label"]) or []
        old = waiting.pop(0) if waiting else {}
        set_value(old, "label", row["stat_label"])
        set_value(old, "value", number_or_text(row["stat_value"]))
        stats.append(old)
    profile["stats"] = stats

    dump(DATA / "profile.yml", profile)


def save_posts(rows, problems):
    posts = []
    for row in rows:
        date_text = clean_date(row["post_date"], f"The post “{row['post_title']}”", problems)
        posts.append(
            {
                "date": date_text,
                "title": row["post_title"],
                "slug": slugify(row["post_slug"]) or slugify(row["post_title"]),
                "body": row["post_body"],
            }
        )
    posts.sort(key=lambda post: post["date"], reverse=True)
    return posts


def save_training(rows, problems):
    runs = []
    for row in rows:
        date_text = clean_date(row["run_date"], f"The run on {row['run_date']}", problems)
        runs.append(
            {
                "date": date_text,
                "distance": row["run_distance"],
                "duration": row["run_duration"],
                "pace": row["run_pace"],
                "notes": row["run_notes"],
            }
        )
    runs.sort(key=lambda run: run["date"], reverse=True)
    return runs


def save_from_form(form):
    """Check everything first, then write — so a mistake changes nothing."""
    problems = []

    progress = normalise(form.get("goal_progress")).strip()
    if progress and not re.fullmatch(r"\d{1,3}", progress):
        problems.append(f"The goal percentage needs to be a whole number, not “{progress}”")

    posts = save_posts(
        form_rows(form, ["post_title", "post_date", "post_slug", "post_body"], essential="post_title"),
        problems,
    )
    runs = save_training(
        form_rows(form, ["run_date", "run_distance", "run_duration", "run_pace", "run_notes"],
                  essential="run_distance"),
        problems,
    )
    if problems:
        raise EditorError("Nothing was saved, because of this:\n\n" + "\n".join(f"• {p}" for p in problems))

    write_rows_file(DATA / "posts.yml", posts, block_keys=("body",))
    write_rows_file(DATA / "training.yml", runs)
    save_site(form)
    save_profile(form, progress)
    return len(posts), len(runs)


# --------------------------------------------------------------------------
# Building, previewing, publishing
# --------------------------------------------------------------------------
def python():
    """Prefer the project's virtualenv, so the build always has its packages."""
    venv = ROOT / ".venv" / "bin" / "python"
    return str(venv) if venv.exists() else sys.executable


def run(*args):
    return subprocess.run(
        args, cwd=ROOT, capture_output=True, text=True, timeout=120,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )


def rebuild():
    done = run(python(), "generate.py")
    return done.returncode == 0, (done.stdout + done.stderr).strip()


def unpushed_commits():
    done = run("git", "rev-list", "--count", "@{upstream}..HEAD")
    return int(done.stdout.strip() or 0) if done.returncode == 0 else 0


def publish():
    ok, output = rebuild()
    if not ok:
        return False, f"The site didn't build, so nothing was published.\n\n{output}"

    changes = bool(run("git", "status", "--porcelain").stdout.strip())
    if not changes and not unpushed_commits():
        return True, "There was nothing new to publish — the site is already up to date."

    if changes:
        run("git", "add", "-A")
        commit = run("git", "commit", "-m", COMMIT_MESSAGE)
        if commit.returncode != 0:
            return False, f"Couldn't save a version of your changes.\n\n{commit.stdout}{commit.stderr}"

    push = run("git", "push", "origin", "main")
    if push.returncode != 0:
        return False, (
            "Your changes are safe on this computer, but couldn't be sent to the live "
            f"site.\n\n{push.stdout}{push.stderr}"
        )
    return True, "Published. runamile.co.uk updates itself in about a minute."


def port_is_open(port):
    with socket.socket() as sock:
        sock.settimeout(0.4)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def ensure_preview():
    """Make sure the dev preview (serve.py) is running, then return its URL."""
    if not port_is_open(PREVIEW_PORT):
        with open(PREVIEW_LOG, "a", encoding="utf-8") as log:
            subprocess.Popen(
                [python(), "serve.py"], cwd=ROOT, stdout=log, stderr=log,
                start_new_session=True,
            )
        for _ in range(20):
            time.sleep(0.25)
            if port_is_open(PREVIEW_PORT):
                break
    return f"http://{request.host.split(':')[0]}:{PREVIEW_PORT}/"


# --------------------------------------------------------------------------
# The password (this page can publish, so it isn't left wide open)
# --------------------------------------------------------------------------
def read_or_create(path, factory):
    if not path.exists():
        path.write_text(factory(), encoding="utf-8")
        path.chmod(0o600)
    return path.read_text(encoding="utf-8").strip()


WORDS_A = ["steady", "early", "uphill", "tailwind", "sunrise", "long", "gentle", "brisk"]
WORDS_B = ["miles", "strides", "shoelaces", "kilometre", "lap", "finish", "splits", "trail"]


def new_password():
    return f"{secrets.choice(WORDS_A)}-{secrets.choice(WORDS_B)}-{secrets.randbelow(90) + 10}"


app = Flask(__name__, template_folder=str(TEMPLATES))
app.secret_key = read_or_create(SECRET_FILE, lambda: secrets.token_hex(32))
PASSWORD = read_or_create(PASS_FILE, new_password)


@app.before_request
def require_login():
    if request.endpoint in {"login", "do_login", "static"}:
        return None
    if not session.get("in"):
        return redirect(url_for("login", next=request.path))
    return None


@app.get("/login")
def login():
    return render_template("login.html", messages=get_flashed_messages(with_categories=True))


@app.post("/login")
def do_login():
    if secrets.compare_digest(request.form.get("password", ""), PASSWORD):
        session.permanent = True
        session["in"] = True
        return redirect(request.args.get("next") or url_for("home"))
    flash("That password didn't match. Try again.", "warn")
    return redirect(url_for("login"))


@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# --------------------------------------------------------------------------
# The editing screens
# --------------------------------------------------------------------------
def model():
    def newest(items):
        return sorted(items, key=lambda item: str(item.get("date", "")), reverse=True)

    return {
        "site": load(DATA / "site.yml"),
        "profile": load(DATA / "profile.yml"),
        "posts": newest(load(DATA / "posts.yml")),
        "training": newest(load(DATA / "training.yml")),
    }


@app.get("/")
def home():
    data = model()
    return render_template(
        "editor.html",
        view=data,
        today=date.today().isoformat(),
        live_url=data["site"].get("url") or "https://runamile.co.uk",
        messages=get_flashed_messages(with_categories=True),
    )


@app.post("/save")
def do_save():
    try:
        posts, runs = save_from_form(request.form)
    except EditorError as error:
        flash(str(error), "bad")
        return redirect(url_for("home"))
    except Exception as error:  # noqa: BLE001 — never show a traceback to him
        flash(f"Something went wrong saving that, and nothing was changed: {error}", "bad")
        return redirect(url_for("home"))

    ok, output = rebuild()
    if ok:
        flash(f"Saved — {posts} posts and {runs} runs. Have a look at the preview.", "good")
    else:
        flash(f"Saved, but the site didn't rebuild:\n\n{output}", "bad")
    return redirect(url_for("home"))


@app.post("/publish")
def do_publish():
    ok, message = publish()
    flash(message, "good" if ok else "bad")
    return redirect(url_for("home"))


@app.get("/preview")
def preview():
    return redirect(ensure_preview())


if __name__ == "__main__":
    print(f"\n  Editing page:  http://simon-dev.rebecchi.uk:{PORT}/")
    print(f"  Also on:       http://{socket.gethostname()}:{PORT}/\n")
    print(f"  Password:      {PASSWORD}")
    print(f"  (kept in {PASS_FILE.name}; change it by editing that file)\n")
    app.run(host=HOST, port=PORT, debug=False)
