# Reading Room: how this site looks

Every page uses one visual style, called **Reading Room**. It comes from our old project
(`mostafansh/interface@b6adb6d`). The whole style is one file: `static/css/reading-room.css`.
Do not add a second stylesheet or a second look.

## The idea

- **Dark first.** Radiologists read in dark rooms, so dark is the default.
- **Lightbox.** Warm charcoal ground, bone-white text, like films on a lightbox in a dark room.
- **One accent.** A signal orange, like a marker on a film. The AI is one cobalt blue.
- **Calm.** No gradients, glows or shadows. Motion is small: short colour changes and a
  1 px press on buttons and choices. The images and the data matter most.
- **Phone first.** Workshop attendees use their phones. Every page works at 360 px wide.
- **Nothing external.** No font, script or image from another server. The site also runs offline.

The look was designed in Claude Design and approved by the owner on 2026-09-26. The design
system there is "Reading Room" (the link is in the owner's notes, not in this repo). The code
is the truth: if they differ, this file and the stylesheet win.

## Colours are tokens

A **token** is a named value, such as `--accent`. It is written once, at the top of the
stylesheet. Every other rule uses the name, never the colour code. Change the token and the
whole site follows.

| Token | Used for |
|---|---|
| `--ground` | The page background |
| `--surface` | Header, footer, cards, tables |
| `--raised` | Inputs, notices, answer choices |
| `--ink` / `--soft` | Main text / secondary text |
| `--rule` | Thin decorative lines (table rows, card edges) |
| `--line-strong` | Edges people must see: inputs, buttons, choices |
| `--accent` / `--accent-ink` | Links, the primary button, the focus ring / text on the accent |
| `--ok` / `--warn` / `--stop` | States only: done, needs attention, refused |
| `--you` | The reader's own marks. It is the accent. |
| `--ai` | AI suggestions. One cobalt blue, used for nothing else. Orange (you) and blue (AI) stay apart for colour-blind readers too. |
| `--viewport` | Pure black behind medical images |

Every text colour passes the WCAG AA contrast test (4.5:1) in every theme. Edges people must
see pass 3:1. Check with a contrast tool before you change a value.

## Themes

A **theme** is a set of token values. A theme changes values only, never a component.

- **Dark** is the default. **Light** is used when the phone or computer is set to light mode.
- To force a theme, put `data-theme="dark"`, `"light"` or `"projector"` on `<html>`.
- **Projector** is for the congress hall: light, high contrast, 25% larger text. A projector
  washes out dark greys.
- **The image frame is always dark**, in every theme. A light surround changes how greys look.

## Images and marks

- Every medical image goes in `.frame`. The frame is black, with square corners.
- The whole image shows, scaled to fit. CSS never crops it. Only the reader's zoom does.
- The reader's marks use `--you`, drawn with a solid line.
- AI marks use `--ai`, drawn with a dashed line and an "AI" label (`.badge-ai`).
  Colour is never the only sign.
- A correct and a planted AI suggestion look identical: same colour, line and label.
  Never add a second AI style.
- The AI's confidence stays at text size (`.ai-score`): never a large figure, a meter or a
  bar. A loud score pulls the reader toward the AI and could let a planted one stand out.
- Give every mark a thin black outline (`--viewport`), so it shows on bone and on air.
- The reading screen reads mark colours from the frame, not from the page.
- On the reading screen the image stays in view: on a phone it sticks to the top of the
  screen and the answers scroll under it; on a wide screen the answers scroll beside it.

## Page shell

`base.html` holds the shell. A page fills `{% block content %}` and nothing else.

```html
<body>
  <header class="site-header">
    <a class="brand" href="/"><svg class="brand-mark" width="20" height="20" …>…</svg> Name</a>
    <nav class="site-nav" aria-label="Main">
      <a href="…" aria-current="page">Projects</a> <a href="…">Profile</a>
      <form method="post" action="…">{% csrf_token %}<button type="submit">Sign out</button></form>
    </nav>
  </header>
  <main id="main" class="site-main">{% block content %}{% endblock %}</main>
  <footer class="site-footer"><a href="…">About</a> <a href="…">Image credits</a></footer>
</body>
```

## Type

- **Instrument Serif** for the page title (`h1`) only: one serif line per page.
- **Geist** for everything else. Headings under the title are medium weight.
- **Geist Mono** for figures, pills, badges and the confidence scale.
- The font files are in `static/fonts/`, with their open licences (SIL OFL 1.1). They are
  Latin only; other letters fall back to the system fonts. Never link Google Fonts.

## Components

- `.stack`: puts even space between the blocks inside it. Use it on forms and sections.
- `h1`–`h3`, `.lede` (opening paragraph), `.muted` (secondary text), `.num` (aligned digits).
- `.btn` (bordered), `.btn-primary` (filled), `.btn-quiet` (text only), `.btn-block` (full
  width), `.btn-row` (a row that wraps). **Only one `.btn-primary` per screen.**
- `.notice` plus one of `.notice-info`, `.notice-ok`, `.notice-warn`, `.notice-stop`: a
  quietly tinted box. The words must say the state too. An icon may come first (see Icons).
- `.table` inside `.table-wrap`. The wrapper scrolls sideways; the page never does.
- `.pill` (plus `.pill-ok`, `.pill-warn`, `.pill-stop`): a short state word with a small dot.
- `.stats` holding `.stat` blocks: `.stat-figure`, `.stat-label`, and `.stat-note` for
  "Not measured yet".
- `.card-list` holding `.card` items: the project list.
- Forms: labels, inputs, selects, text areas. `.choice-list` with `.choice` turns radio
  buttons and checkboxes into large tap targets. Add `.choice-row` for a 1–5 scale.
- `.frame` (image viewport), `.badge-ai` (AI label), `.visually-hidden` (for screen readers only).
- Reading screen: `.case-progress` ("Case 7 of 24" and a thin progress line), `.ai-panel`
  holding `.ai-verdict` (the AI's answer and its `.ai-score`).
- Two corner radii: `--radius` (6 px) for controls, `--radius-lg` (10 px) for notices, panels
  and cards.
- A tint (notice, AI panel, chosen answer) uses `color-mix()`. Always write a plain
  `var(--raised)` line before it: phones from before 2023 do not know `color-mix()`.

## Icons

- Controls use words. An icon is rare: a 16 px inline line icon, 1.5 px stroke, drawn in
  `currentColor`, always beside words that say the same thing.
- Icons in use: the padlock in the "Your first read is locked" notice. Add a new icon here
  first. No emoji.
- `.landing-hero`, `.landing-section`, `.landing-facts`, `.landing-steps`: the home page only.
  It is text only: no picture, so nothing on it can look like a scan.

## Persian and right-to-left

- Wrap Persian text in `<div lang="fa" dir="rtl">`. `lang` picks the font; `dir` flips the layout.
- The stylesheet uses **logical properties**: "start" and "end" instead of "left" and "right".
  So a notice's icon moves to the right side in Persian by itself.
- The Persian font is Vazirmatn if the device has it, else Tahoma or Segoe UI. A slot at the
  top of the stylesheet is ready for Vazirmatn as a file on our own server.
- Letter spacing is off in Persian, because it breaks joined letters.

## Phones and access

- Anything you tap is at least 44 px tall. Body text and inputs are at least 16 px.
- The content column is at most 960 px wide, with 16 px side margins on a phone.
- Keyboard focus always shows an orange ring. Reduced-motion settings stop all motion.

## Never

- A colour code inside a component rule, or a colour only one theme defines.
- A second accent, or a state colour used as decoration.
- Colour as the only sign of meaning. Add a word or a shape.
- Rounded corners on an image, or CSS that crops one.
- `left` or `right` where `start` or `end` works.
- A page that scrolls sideways at 360 px, or that fails in one of the three themes.
- A font or file from Google or any CDN.

## What changed from the old standard

- The old site banned images, fonts and scripts. This site shows images and runs a small
  script, so those bans are gone. Still, nothing may come from another server.
- The stylesheet is now a file, not inline. The browser keeps a copy between pages.
- New: the image frame, four tokens (`--you`, `--ai`, `--line-strong`, `--viewport`), the
  projector theme, Persian support and phone sizes. `--stop` is brighter in the dark theme.
- 2026-09-26: the "lightbox" look replaced the teal look: new colours in all three themes,
  three self-hosted fonts, `--radius-lg`, tinted notices, dotted pills, the case progress
  line, the locked-read notice with a padlock, and small motion.
