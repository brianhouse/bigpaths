#!/usr/bin/env python3

import yaml, json, datetime, jinja2, random
from housepy import timeutil, drawing
from colors import colors

with open("master_narrative.yaml") as f:
    try:        
        days = yaml.load(f)
    except yaml.parser.ParserError as e:
        print(e)
        exit()

strips = []
for d, day in enumerate(days):
    strips.append([])
    for entry in day:
        if entry['time'] == "WAKE":
            continue
        strips[d].append(entry['time'])


for strip in strips:
    for t in strip:
        print(t)
    print()

for s, strip in enumerate(strips):
    start_time = strip[len(strip) // 2].replace(hour=9, minute=0)
    # print("start_time", start_time)
    stop_time = (start_time + datetime.timedelta(days=1)).replace(hour=2, minute=30)
    # print("stop_time", start_time)
    start_t = timeutil.timestamp(start_time)
    stop_t = timeutil.timestamp(stop_time)
    strips[s] = [(timeutil.timestamp(dt) - start_t) / (stop_t - start_t) for dt in strip]

for strip in strips:
    for t in strip:
        print(t)
    print()


ctx = drawing.Context(256 * 5, 72 * 5, hsv=False, relative=True, flip=False, background=(1., 1., 1., 1.))

for s, strip in enumerate(strips):

    if s > 0:
        ctx.rect((s / len(strips)) + (5/ctx.width), 0, (1 / len(strips)) - (10/ctx.width), strip[0], fill=color, thickness=0)

    for i in range(len(strip) - 1):
        color = colors[((s * 10) + i) % len(colors)]

        ctx.rect((s / len(strips)) + (5/ctx.width), strip[i], (1 / len(strips)) - (10/ctx.width), strip[i+1]-strip[i], fill=color, thickness=0)

    if s < len(strips) - 1:
        color = colors[((s * 10) + i + 1) % len(colors)]        
        ctx.rect((s / len(strips)) + (5/ctx.width), strip[-1], (1 / len(strips)) - (10/ctx.width), 1.0-strip[-1], fill=color, thickness=0)

HOURS = 10.28
for i in range(int(HOURS)):
    ctx.line(0, i / HOURS, 1, i / HOURS, thickness=1.0, stroke=(0., 0., 0., 1.))


ctx.output("timelines")

