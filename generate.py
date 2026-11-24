#!/usr/bin/env python3
"""Generate a seamless, ASCII-only, 256-color Durdraw black hole animation."""
import argparse
import gzip
import json
import math
import random
from pathlib import Path

TAU = math.tau
RAMP = " .,:;irsXA253hMHGS#9B&@"
PALETTE = [233, 235, 52, 88, 124, 160, 166, 172, 208, 214, 220, 221, 223, 229, 230, 231]


def emission(radius, angle, phase):
    # Integer temporal frequencies make the first/last transition seamless.
    spiral = math.sin(34 * radius - 3 * angle + 2 * phase)
    eddies = math.sin(57 * radius + 7 * angle - 3 * phase)
    fine = math.sin(91 * radius - 13 * angle + 5 * phase)
    return 0.70 + 0.16 * spiral + 0.10 * eddies + 0.04 * fine


def render(width, height, phase, stars, tilt=-25.0, zoom=2.1,
           center_x=0.80, center_y=0.62):
    contents, colors = [], []
    scale = min(width / 100, height / 38) * zoom
    # Rotate in aspect-corrected coordinates, not raw terminal cells.
    radians = math.radians(tilt)
    cosine, sine = math.cos(radians), math.sin(radians)
    for row in range(height):
        chars, inks = [], []
        for col in range(width):
            screen_x = (col - (width - 1) * center_x) / scale
            screen_y = (row - (height - 1) * center_y) * 2 / scale
            x = cosine * screen_x + sine * screen_y
            y = -sine * screen_x + cosine * screen_y
            radius = math.hypot(x, y)
            value = 0.0
            # Thin, inclined annulus. The left side is Doppler-brightened.
            disk_r = math.hypot(x / 41, y / 7.0)
            angle = math.atan2(y / 7, x / 41)
            if 0.31 < disk_r < 1.05:
                edge = min(1.0, (disk_r - 0.31) * 15, (1.05 - disk_r) * 12)
                value = edge * (0.95 - 0.42 * disk_r) * emission(disk_r, angle, phase)
                value *= 1.0 - 0.28 * math.cos(angle)
            # The back of the disk is gravitationally lensed above the shadow.
            lens_r = math.hypot(x / 21.0, (y + 0.4) / 20.0)
            if y < 0:
                band = math.exp(-((lens_r - 1) / 0.115) ** 2)
                value = max(value, band * (0.72 - 0.20 * x / 23) *
                            emission(lens_r * 0.6, math.atan2(y, x), phase))
            # A faint secondary image wraps below the shadow.
            if y > 0:
                secondary = math.exp(-((math.hypot(x / 17, y / 15) - 1) / 0.055) ** 2)
                value = max(value, secondary * 0.30)
            # Photon ring and opaque event horizon.
            ring = math.exp(-((radius - 12.6) / 0.65) ** 2)
            value = max(value, ring * (0.82 - 0.15 * x / 13))
            if radius < 11.8:
                value = 0.0
            # Near-side disk crosses in front of the lower part of the shadow.
            if y > 1.3 and 0.31 < disk_r < 1.05:
                edge = min(1.0, (disk_r - 0.31) * 18, (1.05 - disk_r) * 12)
                front = edge * (1.06 - 0.42 * disk_r) * emission(disk_r, angle, phase)
                front *= 1.0 - 0.30 * math.cos(angle)
                value = max(value, front)
            if value > 0.035:
                value = min(1.0, value)
                chars.append(RAMP[max(1, int(value * (len(RAMP) - 1)))])
                inks.append([PALETTE[min(len(PALETTE) - 1, int(value * len(PALETTE)))], 0])
            elif (col, row) in stars and radius > 24:
                char, color = stars[col, row]
                chars.append(char)
                inks.append([color, 0])
            else:
                chars.append(' ')
                inks.append([0, 0])
        contents.append(''.join(chars))
        colors.append(inks)
    return contents, colors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-o', '--output', type=Path, default=Path('blackhole.dur'))
    parser.add_argument('--width', type=int, default=400)
    parser.add_argument('--height', type=int, default=120)
    parser.add_argument('--frames', type=int, default=96)
    parser.add_argument('--fps', type=int, default=16)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--tilt', type=float, default=-25.0, help='disk angle in degrees')
    parser.add_argument('--zoom', type=float, default=2.1)
    parser.add_argument('--center-x', type=float, default=0.80, help='horizontal canvas fraction')
    parser.add_argument('--center-y', type=float, default=0.62, help='vertical canvas fraction')
    args = parser.parse_args()
    if min(args.width, args.height, args.frames, args.fps) <= 0:
        parser.error('dimensions, frame count and fps must be positive')
    if not all(math.isfinite(v) for v in (args.tilt, args.zoom, args.center_x, args.center_y)) or args.zoom <= 0:
        parser.error('camera values must be finite and zoom must be positive')
    rng = random.Random(args.seed)
    stars = {(rng.randrange(args.width), rng.randrange(args.height)):
             (rng.choice(['.', '.', '.', '+', '*']), rng.choice([237, 240, 244, 250]))
             for _ in range(args.width * args.height // 65)}
    frames = []
    for index in range(args.frames):
        contents, colors = render(args.width, args.height, TAU * index / args.frames, stars,
                                  args.tilt, args.zoom, args.center_x, args.center_y)
        # Ly supports v7 only: colorMap is column-major, unlike contents.
        column_colors = [list(column) for column in zip(*colors)]
        frames.append(dict(frameNumber=index + 1, delay=0.0, contents=contents,
                           colorMap=column_colors))
    movie = {'DurMovie': dict(formatVersion=7, colorFormat='256', preferredFont='fixed',
                             encoding='utf-8', name='Event Horizon', artist='Procedural',
                             # Ly accesses the JSON float variant directly, so 16
                             # must be serialized as 16.0 rather than an integer.
                             framerate=float(args.fps), sizeX=args.width, sizeY=args.height,
                             extra=None, frames=frames)}
    # .dur files are gzip-compressed JSON, as written by Durdraw itself.
    with args.output.open('wb') as raw:
        with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as stream:
            stream.write(json.dumps(movie, separators=(',', ':')).encode('utf-8'))
    print(f'Wrote {args.output}: {args.width}x{args.height}, {args.frames} frames, '
          f'{args.fps} fps ({args.frames / args.fps:g}s loop)')


if __name__ == '__main__':
    main()
