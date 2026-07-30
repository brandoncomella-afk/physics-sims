# Physics Simulations

Interactive, quantitative physics labs for high school and AP / intro-college courses. Each simulation is a **single self-contained HTML file** — no build step, no dependencies, no external requests — so they can be hosted anywhere and embedded in any site.

## Current sims

| File | Topic | Highlights |
|---|---|---|
| `pv-cycle-lab.html` | Thermodynamic cycles | Draggable PV diagram, Carnot/Otto/rectangle presets, per-leg W/Q/ΔU table, piston animation, efficiency vs. Carnot limit, copy-data button |
| `relativity-lab.html` | Special relativity | Light clock, length contraction, muon survival lab (with data export), relativity of simultaneity |
| `dune-buggy-challenge.html` | Projectile motion | Ramp → table → moving target. Predict-then-test with the answer hidden, randomised setups, worked solution on reveal, trial log with data export |
| `index.html` | Landing page | Card grid linking all sims |

### Dune Buggy Challenge — physics notes

Adapted from the Physics Classroom's *Dune Buggy Challenge Lab* (2009), which drops a ball
vertically onto a constant-motion cart. This version rolls the ball off a ramp and over a
table edge, making it a two-dimensional projectile problem.

- Ramp exit speed, rolling without slipping (solid sphere, `I = 2/5 mr²`): `v = √(10gh/7)`.
  The "ideal" toggle uses `v = √(2gh)`, which overshoots the range by 18.3 %.
- Time on the ramp: `t_ramp = 2h / (v · sinθ)`. Ramp angle changes this time but **not** the
  exit speed — a useful thing for students to discover.
- Fall time uses `H − c`, the table height minus the cup rim height, not `H`. The teacher's
  guide flags forgetting `c` as the most common student error; at `H = 1 m, c = 8 cm` it is
  worth 7.2 cm of range against a ±3.5 cm target, so the mistake reliably loses the shot.
- Required start distance: `D = R − v_b · t_travel`, where `t_travel` is the fall time alone
  (buggy released at the table edge) or `t_ramp + t_fall` (both released together).

## Hosting on GitHub Pages

1. Create a new GitHub repository (e.g. `physics-sims`) and upload these files to its root.
2. In the repo: **Settings → Pages → Source: Deploy from a branch → Branch: `main` / root → Save**.
3. After a minute the collection is live at `https://YOURUSER.github.io/physics-sims/` — each sim at `.../pv-cycle-lab.html`, etc.

Updating a sim is just committing a new version of its file; the page redeploys automatically.

## Embedding in WordPress

Add a **Custom HTML** block to any page or post:

```html
<iframe src="https://YOURUSER.github.io/physics-sims/pv-cycle-lab.html"
        width="100%" height="760" style="border:none; border-radius:12px;"
        loading="lazy" title="PV Cycle Lab"></iframe>
```

Suggested heights: 760px for the PV Cycle Lab, 700px for the Relativity Lab, 900px for the Dune Buggy Challenge. All are responsive down to ~360px wide.

**Note for WordPress.com:** plans below the Business tier may strip `<iframe>` tags from the editor. If that happens, options are: upgrade the plan, link out to the sim with a screenshot thumbnail, or self-host WordPress.

## Design conventions (for future sims)

- One HTML file per sim; inline all CSS/JS; no CDNs.
- Real numbers students can record; a "Copy data" button that exports TSV for spreadsheets.
- Light and dark mode via `prefers-color-scheme`.
- Pointer events (mouse + touch) for all dragging.
- Physics core isolated in a clearly-marked script section so it can be unit-tested in Node.

## License

Free for classroom and personal use.
