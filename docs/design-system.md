# ShieldMate UI foundation — Phase 01

The identity pairs condensed editorial typography with deep burgundy and assertive red.
Warm ivory creates reading space; it is not a pink brand palette. Marketing uses varied
scale, an asymmetric concept diagram and horizontal rules. The workspace retains the
identity with compact headings, a stable sidebar and explicit availability states.
All three supplied brand images informed hierarchy, contrast and block rhythm; their
slide compositions, text, people and graphics are not reproduced or embedded.

## Tokens

CSS source of truth: `frontend/src/styles.css` (`@theme`). Supporting files separate
shared controls, marketing composition and workspace layout. No additional font or
runtime dependency was added. Small artwork in `public/favicon.svg` repeats the brand
colors because a standalone SVG cannot inherit document custom properties.

| Token suffix (`--color-…`) | Value   | Use                                                            |
| -------------------------- | ------- | -------------------------------------------------------------- |
| burgundy-950               | #321015 | Body text, darkest audience section, focus outline             |
| burgundy-900               | #570711 | Hero, navigation selection, preview banner                     |
| red-700                    | #98121F | Primary actions, text accents, closing section                 |
| red-500                    | #CF2431 | Red emphasis block, wordmark accent, diagram output            |
| surface                    | #F7F0EA | Main warm-neutral canvas                                       |
| surface-raised             | #FFF9F5 | Readable panels, light buttons, inverse text                   |
| stroke                     | #D9C7C3 | Decorative dividers and inactive borders; not input boundaries |
| success                    | #23613E | Confirmed operation or real health response, always with text  |
| warning                    | #785000 | Attention/permission pattern, always with text                 |
| error                      | #98121F | Error text/border, prefixed with an explicit error message     |

Never put red body text on burgundy. Inverse text is ivory. Form boundaries use burgundy
rather than the low-contrast decorative stroke. Focus uses a 3px dark outline, 4px offset
and an ivory backing ring so it remains discernible on dark and light surfaces.

## Typography and spacing

- Anton 400: wordmark, public display headings and editorial step indices. Local Latin
  WOFF2, SIL Open Font License preserved under `frontend/public/licenses/`.
- IBM Plex Sans 400/500/600: body, UI and workspace headings. Local WOFF2, same license
  location. `font-display: swap`; only used font files ship. System fallbacks remain.
- Hero: fluid 60–160px; public section headings 40–88px; workspace h1 36px in Plex.
  UI section headings 22–24px. Body normally 16px / 1.65; supporting text 12–15px;
  compact nonessential metadata 10–12px. Do not use display type in future data cells.
- Paragraph measure: usually 44–65ch, explanatory footnotes at most 75ch.
- Spacing: 4/8px rhythm; 12, 16, 20, 24, 32, 40, 48, 64 and 80px. Page gutters fluid
  from 24 to 72px. Sharp corners, 1px rules, no decorative shadows or gradients.
- Overall page stops growing beyond 1920px. Short text can span less than the grid.

## Responsive composition

- 360px: single-column marketing; CTA before the noninteractive concept diagram;
  navigation is an inline disclosure. Workspace destinations wrap and remain visible.
- 768px: two-column editorial sections and 220px workspace sidebar; global navigation
  still uses the disclosure. UI examples stack to retain useful field width.
- 1024px: desktop global navigation. No sticky overlay obscures anchor targets.
- 1100px: workflow annotations gain a separate column; hero actions align right.
- 1200px: 256px workspace sidebar, two-column component reference.
- 1280/1920px: large display scale and controlled reading measures. Tables use semantic
  fixed-width columns and wrap long text rather than create page-level overflow.

Do not copy the marketing scale into operational screens. Keep future tables concise,
use explicit column headers and avoid meaningless zeroes where no data exists.

## Shared components and actual uses

- `Button`: primary, secondary, quiet; real `disabled`, pending with `aria-busy`, and
  `type="button"` by default. Used for unavailable feature controls, health retry and
  the component reference. Navigation uses real links with the matching CSS classes;
  light links are for dark marketing surfaces. Never turn an unavailable action into
  a clickable link or hide the reason it is disabled.
- `Field`: stable generated ID, associated label/help/error, `aria-invalid`, error
  text. The local UI reference demonstrates validation, reset and focus recovery.
  This is not domain onboarding or authentication. A future backend must validate
  all business input independently; this component does not establish trust.
- `Badge`: neutral/success/warning/error with written labels. Used for availability
  and status examples. No security severity is represented as a real finding yet.
- `Alert`: neutral/success/warning/error; explicit title and message. Error uses an
  alert live region; other feedback uses status semantics. Used for preview context
  and local validation. Never say an empty findings list means a domain is secure.
- `EmptyState`: heading, explanation, decorative bracket mark. Used by each workspace
  destination. `PlannedState` preserves the separate auth/demo future-route contract.
- `LoadingState`: static skeleton plus text, demonstrated in the UI reference and
  labeled as an example. The existing `ServiceStatus` reports actual pending health
  requests separately. No perpetual spinner pretends to perform a scan.
- `Table<T>`: typed columns/rows/key, caption, header scopes, long-word wrapping and
  explicit full-width empty row. Used for the empty findings structure and the real
  status-token reference. Do not add sample customer/security rows in this phase.
- `Header`/`Footer`/`Wordmark`: shared chrome. Mobile menu is a nonmodal disclosure,
  so it does not trap focus; Escape restores the toggle, route/anchor navigation
  closes it, and hidden links leave the tab/accessibility order. Anchors and route
  changes move focus to the destination content. Native `details` handles FAQs.

No dialog was introduced: Phase 01 has no action needing a modal. The UI reference at
`/app/ui-kit` is deliberately public, explicitly labeled and holds state only in memory.
Never enter sensitive information in the example field.

## Interaction and accessibility

Enabled controls have a concrete action or destination. Hover transitions last 180ms;
active buttons shift 1px. Disabled and pending buttons cannot receive clicks/tab focus.
There are no ambient animations. Reduced motion removes transitions and transforms;
forced-colors mode retains control borders and uses the system Highlight focus color.
One h1 per route, semantic landmarks, labeled navigation, skip link, section headings,
and keyboard FAQ disclosure are required. Preserve textual whitespace at display line
breaks so the accessible heading name does not concatenate words.

See `phase-01-results.md` and `evidence/phase-01/browser-results.json` for measured
contrast, browser checks, actual screenshots and the limitations of automated QA.

## Metadata and pre-launch indexing

`index.html` supplies a descriptive title, description, Open Graph type/title/description,
original SVG favicon and theme color. The router updates titles for each page. The
pre-launch preview retains `noindex,nofollow`; `robots.txt` disallows crawling.
No canonical domain, sitemap URLs, organization claims or social image were invented.
Before an approved public release, configure a real origin, decide which routes may be
indexed, generate a sitemap, and consider SSR/prerendering for marketing. This Vite SPA
has no SSR, route-specific initial metadata or true HTTP 404 for client-side unknown
routes. The rendered 404 works; the SPA fallback still responds with HTTP 200.

## Phase 06 operational composition

The real overview uses a ruled operating strip, an asymmetric first-priority emphasis and
compact paired work/scan lists. It reuses the same Phase 05 evidence/priorities and Plex UI
hierarchy; Anton remains the display brand. Sharp borders, warm ivory and red actions retain
the established identity. Task pages use plain labeled forms, explicit human/technical state,
readable timestamps and escaped work history. No gauges, invented scores or decorative
activity appear. Narrow screens stack actionable rows and forms; native controls, visible
focus, reduced motion and semantic headings remain the foundation.

## Phase 07 reports, demo and Russian typography

Reports reuse the existing compact editorial workspace hierarchy, sharp dividers and
burgundy/red accents. Coverage and history use stacked mobile layouts, with readable
wrapping for checksums and source identifiers. The public guided sample has an explicit
burgundy/red DEMO banner and repeated endnote. PDFs use white A4 pages, dark burgundy
text, red rules and selective emphasis for print readability, with honest scope and
page numbers rather than decorative charts or invented scores.

The UI remains Anton/IBM Plex Sans. Locally served Plex Cyrillic faces cover Russian;
Russian display headings use Plex because Anton lacks Cyrillic. ReportLab embeds the
licensed Liberation Sans regular/bold TTFs for selectable Cyrillic PDFs. That PDF-only
font is a technical Unicode requirement, not a change to the website's design identity.
