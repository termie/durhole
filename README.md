# Event Horizon

`blackhole.dur` is a seamless procedural ASCII animation in Ly-compatible Durdraw v7 format
(gzip-compressed JSON): 400 columns × 120 rows, 96 frames, 16 fps, 6 seconds.
Uses the terminal's 256-color palette on black; no Unicode art characters.

Features a dark shadow, photon ring, lensed upper disk, near-side accretion
flow, Doppler-inspired brightness asymmetry, orbiting spiral turbulence,
and a seeded starfield. The camera is zoomed 2.1x, tilted -25 degrees, and
positioned toward the right, cropping roughly a third of the structure beyond
the canvas for a close-up composition. This is a stylized visualization, not a ray-traced
relativistic simulation.

Open in Durdraw:

```sh
durdraw blackhole.dur
```

Regenerate with Python 3 (standard library only):

```sh
python3 generate.py
python3 generate.py --tilt -35 --zoom 2.3 --center-x 0.8 --center-y 0.62 -o closeup.dur
# Restore the original centered, uncropped composition:
python3 generate.py --tilt 0 --zoom 1 --center-x 0.5 --center-y 0.5 -o centered.dur
```

Use a terminal at least as large as the canvas, plus room for Durdraw's UI.

Ly compatibility: the file uses v7's column-major color map and explicitly
floating-point framerate (`16.0`). Ly's loader only accepts v7 and accesses
the framerate as a JSON float; an integer can panic in that loader.
