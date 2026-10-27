# Editing this site — the plain-English guide

Welcome. This is your site: **runamile.co.uk**. This guide explains how to
change it. There is no software to learn and nothing to install — you describe
what you want, it gets done, and it appears online.

## The easy way: just ask

You don't have to touch anything yourself. Open your AI assistant in this
folder and tell it what you'd like, in your own words:

> "Add a post about this morning's run."
> "Log today: 4 km in 26 minutes, felt tired."
> "I don't like the orange — try a deep green."
> "Put a photo of the park at the top of the home page."

The assistant edits the files, rebuilds the site, and gives you a link to look
at. When you're happy, it publishes it. **You never have to run a command or
edit a file.** The rest of this guide is for when you're curious about what's
under the bonnet, or want to do a small edit by hand.

Whatever happens, remember the golden rule: **nothing goes live until you
publish it.** You can always look first, and nothing can be broken for real
because every version is saved.

## The other way: the editing page

If you'd rather type it yourself, there's a simple editing page, always ready
at:

**http://simon-dev.rebecchi.uk:9001**

There's nothing to sign in to — it's only reachable from your own devices, never
from the open internet. Everything is in boxes: your details, your goal and
numbers, the blog posts, the run log, and the site settings. Type, then press

- **Save** — rebuilds the preview so you can look at it (nothing public changes);
- **Publish** — sends it up, and runamile.co.uk updates itself within a minute.

You can add and remove posts and runs, and the page puts them in date order for
you. Times like `21:40` are looked after, so type them as normal. Nothing you
can do here loses work: every version is saved, and a save that changes nothing
changes nothing at all.


## How the site is put together

```
data/            ← your words: posts, runs, your profile, site settings
templates/       ← the page layouts (the "skeleton" of each page)
styles.css       ← the look: colours, fonts, spacing
generate.py      ← builds the website from the three things above
editor.py        ← the editing page, if you'd rather type it yourself
docs/            ← the finished website (built automatically — don't edit this)
```

You'll mostly live in `data/`. Everything in those files is written in **YAML**,
which is just lists of `label: value` pairs. Indentation matters — items that
line up belong together. When in doubt, copy the shape of the block above.

### The four content files

| File | What it holds |
|------|---------------|
| `data/posts.yml` | Your blog posts (newest at the top) |
| `data/training.yml` | Your running log — one entry per run |
| `data/profile.yml` | The home page: name, tagline, story, goal and stats |
| `data/about.yml` | The About page: its own title, subtitle, story and location |
| `data/site.yml` | The site title, description, the footer line, contact email and social links |

## Writing, editing and deleting a blog post

Open the editing page and choose **Blog posts** in the strip along the top
(that's **http://simon-dev.rebecchi.uk:9001/posts**).

- **Write a new post** — a title, the date it's first written, and the words.
  Press **Save**: it appears on the blog straight away in the preview. Press
  **Publish** when you're ready for the world to see it.
- **Edit** next to any post — the same form, already filled in. Change what you
  like; the date stays put unless you change it, so the post keeps its place.
- **Delete** next to any post — it asks first, then removes the post *and* the
  page it lived at. Nothing is left behind on the site once you publish.

On the blog, each post shows its **title in bold** with the date it was first
written underneath in smaller type.

If you ever want to do it by hand instead, a post is one block at the top of
`data/posts.yml`:

```yaml
- date: 2026-10-20
  title: A Good Run Today
  slug: a-good-run-today        # this becomes the web address
  body: |
    Write your first paragraph here.

    Leave a blank line to start a new paragraph. You can make text **bold**
    or *italic*, and add [links](https://example.com) like this.
```

You can also add headings (`## A smaller heading`), bullet lists (`- like
this`), and quotes (`> like this`) inside `body`.

A few rules that keep things working:

- **Keep the dashes and indentation.** Every post starts with `- ` and each
  line under it is indented the same amount.
- **`slug`** is the end of the web address people will see. Lowercase, use
  hyphens instead of spaces, and never reuse one.
- **`date`** must be in `YYYY-MM-DD` form.
- **Quote any time value** (like `"32:15"`). Without the quotes, YAML thinks a
  time such as `21:40` is a maths sum and turns it into a number.

## Logging a run

Add one entry at the top of `data/training.yml`:

```yaml
- date: 2026-10-20
  distance: 5.0 km
  duration: "32:15"       # keep the quotes — times like 32:15 need them
  pace: 6:27 /km
  notes: Felt great today.
```

`pace` and `notes` are optional — leave them out if you like.

## Changing your story, goal or stats

Open `data/profile.yml`:

- **`name`**, **`tagline`**, **`location`** and **`intro`** are the words at the
  top of the **home page**. **`eyebrow`** is the small line just above your name.
- The **About page** has its own words in `data/about.yml`, so the two pages can
  say different things.
- **`goal`** drives the progress bar. `progress` is a percentage from 0 to 100 —
  nudge it up as you get closer.
- **`stats`** is the row of numbers on the home page. Edit the values or add
  your own; each one is a `label` and a `value`.

## Changing how the site looks

The design lives in two places, both editable in plain English:

- **`styles.css`** — the colours, fonts and spacing. Section 1 at the top of the
  file holds every colour in one list, so a single edit there restyles the whole
  site. For example, changing the line starting `--accent:` changes every
  button, link and highlight at once.
- **`templates/`** — the layout of each page. `base.html` is the header and
  footer that appear everywhere; `index.html` is the home page; `blog.html` is
  the list of posts; `log.html` is the training log; `post.html` is the page for
  a single post; `about.html` is the About page.

The site also switches to a **dark theme** automatically for visitors whose
phone or computer is set to dark mode, and adapts to phones and tablets on its
own.

You can ask the assistant for things like a photo banner at the top, different
fonts, a new page (a "Races" page, a "Kit" page, a photo gallery), automatic
monthly mileage totals, or a contact form — none of it is a big job.

## Seeing your changes — the development version

Before anything goes live you can look at a **development version**:

**http://simon-dev.rebecchi.uk:8080**

That's your work-in-progress. Nothing here is public and nothing here affects
the real site. Press **Save** on the editing page and this rebuilds itself;
when you've looked and you're happy, press **Publish** (or ask the assistant
and it publishes for you).

(If you ever want to stop the preview, just say so — or press `Ctrl+C` in the
terminal window that's running it.)

## Publishing to the internet

Your **live site is https://runamile.co.uk**. Changes go up either when you
press **Publish** on the editing page, or when you ask the assistant to send
them — and then the live site rebuilds itself, usually within a minute.

To double-check it worked, just visit **https://runamile.co.uk** — or open it on
your phone. If you're not sure, ask the assistant to confirm the upload
succeeded.

## What's possible

You're not limited to what's here today. Some things people ask for:

- **Posts:** headings, quotes, photo galleries, embedded videos, tags.
- **The log:** automatic totals ("72 km this month"), pace trends, a yearly
  summary, filters by distance.
- **Pages:** Races & results, Kit I use, Routes, an FAQ, a newsletter sign-up.
- **Appearance:** a photo across the top, a new colour scheme, different fonts,
  a wider or narrower page, rounded or square corners.
- **Sharing:** a nice preview card when someone pastes your link into WhatsApp
  or Facebook, and better text for Google.

Just describe it. If it can be built, the assistant will build it and show you.

## If something breaks

Don't panic — nothing is lost. The most common mistake is indentation: a line
that's spaced differently from the lines above it. Compare your new block with
the one above and make the spacing match. Then ask the assistant:

> "The site didn't build — can you find and fix the mistake and show me again?"

The build error will usually name the file and line, and the assistant can put
it right in seconds. Every previous version is saved, so anything can be
restored.
