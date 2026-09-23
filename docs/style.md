# Reading Room: how this site looks

Every page uses one visual style, called **Reading Room**. It comes from our old project
(`mostafansh/interface@b6adb6d`). The whole style is one file: `static/css/reading-room.css`.
Do not add a second stylesheet or a second look.

## The idea

- **Dark first.** Radiologists read in dark rooms, so dark is the default.
- **One accent.** A muted teal, like a contour drawn on a grey scan.
- **Calm.** No gradients, glows, shadows or animation. The images and the data matter most.
- **Phone first.** Workshop attendees use their phones. Every page works at 360 px wide.
- **Nothing external.** No font, script or image from another server. The site also runs offline.

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
| `--ai` | AI suggestions. One violet, used for nothing else. |
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
- Give every mark a thin black outline (`--viewport`), so it shows on bone and on air.
- The reading screen reads mark colours from the frame, not from the page.

## Page shell

`base.html` holds the shell. A page fills `{% block content %}` and nothing else.

```html
<body>
  <header class="site-header">
    <a class="brand" href="/"><img class="brand-mark" src="…/img/brand.svg" alt=""> Name</a>
    <nav class="site-nav" aria-label="Main">
      <a href="…" aria-current="page">Projects</a> <a href="…">Profile</a>
      <form method="post" action="…">{% csrf_token %}<button type="submit">Sign out</button></form>
    </nav>
  </header>
  <main id="main" class="site-main">{% block content %}{% endblock %}</main>
  <footer class="site-footer"><a href="…">About</a> <a href="…">Image credits</a></footer>
</body>
```

## Components

- `.stack`: puts even space between the blocks inside it. Use it on forms and sections.
- `h1`–`h3`, `.lede` (opening paragraph), `.muted` (secondary text), `.num` (aligned digits).
- `.btn` (bordered), `.btn-primary` (filled), `.btn-quiet` (text only), `.btn-block` (full
  width), `.btn-row` (a row that wraps). **Only one `.btn-primary` per screen.**
- `.notice` plus one of `.notice-info`, `.notice-ok`, `.notice-warn`, `.notice-stop`.
  The words must say the state too.
- `.table` inside `.table-wrap`. The wrapper scrolls sideways; the page never does.
- `.pill` (plus `.pill-ok`, `.pill-warn`, `.pill-stop`): a short state word.
- `.stats` holding `.stat` blocks: `.stat-figure`, `.stat-label`, and `.stat-note` for
  "Not measured yet".
- `.card-list` holding `.card` items: the project list.
- Forms: labels, inputs, selects, text areas. `.choice-list` with `.choice` turns radio
  buttons and checkboxes into large tap targets. Add `.choice-row` for a 1–5 scale.
- `.frame` (image viewport), `.badge-ai` (AI label), `.visually-hidden` (for screen readers only).

## Persian and right-to-left

- Wrap Persian text in `<div lang="fa" dir="rtl">`. `lang` picks the font; `dir` flips the layout.
- The stylesheet uses **logical properties**: "start" and "end" instead of "left" and "right".
  So a notice's coloured edge moves to the right side in Persian by itself.
- The Persian font is Vazirmatn if the device has it, else Tahoma or Segoe UI. A slot at the
  top of the stylesheet is ready for Vazirmatn as a file on our own server.
- Letter spacing is off in Persian, because it breaks joined letters.

## Phones and access

- Anything you tap is at least 44 px tall. Body text and inputs are at least 16 px.
- The content column is at most 960 px wide, with 16 px side margins on a phone.
- Keyboard focus always shows a teal ring. Reduced-motion settings are respected.

## Never

- A colour code inside a component rule, or a colour only one theme defines.
- A second accent, or a state colour used as decoration.
- Colour as the only sign of meaning. Add a word or a shape.
- Rounded corners on an image, or CSS that crops one.
- `left` or `right` where `start` or `end` works.
- A page that scrolls sideways at 360 px, or that fails in one of the three themes.

## What changed from the old standard

- The old site banned images, fonts and scripts. This site shows images and runs a small
  script, so those bans are gone. Still, nothing may come from another server.
- The stylesheet is now a file, not inline. The browser keeps a copy between pages.
- New: the image frame, four tokens (`--you`, `--ai`, `--line-strong`, `--viewport`), the
  projector theme, Persian support and phone sizes. `--stop` is brighter in the dark theme.
