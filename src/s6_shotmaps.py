"""Step 6: shot maps. Where each team shoots from (pitch) and where its on-target shots end up (goal mouth).

FotMob coordinates: pitch x 0-105 (attacking goal at 105), y 0-68; goal mouth onGoalShot x 0-2 (post to post),
y 0-0.667 (ground to bar). Penalties and own goals left out.
"""
import asyncio
import glob
import json
import sys
import pandas as pd
from playwright.async_api import async_playwright

from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW, DATA, OUT = ROOT / "raw" / "fotmob_pl_2026_27", ROOT / "data", ROOT / "out"
src = open(ROOT / "src" / "s5_pages.py").read()
ns = {"__file__": str(ROOT / "src" / "s5_pages.py")}
exec(src[:src.index("T = pd.read_csv")], ns)
CSS, page, GOOD, BAD, SHOOT, KEEP, MUT, sgn, sh = (ns[k] for k in ["CSS", "page", "GOOD", "BAD", "SHOOT", "KEEP", "MUT", "sgn", "sh"])
T = pd.read_csv(DATA / "team_finishing.csv", index_col=0)

rows = []
for f in sorted(glob.glob(str(RAW / "match_*.json"))):
    d = json.load(open(f))
    teams = {t["id"]: t["name"] for t in d["header"]["teams"]}
    for s in d["shotmap"]["shots"]:
        if s["isOwnGoal"] or s["situation"] == "Penalty":
            continue
        o = s.get("onGoalShot") or {}
        rows.append(dict(team=teams[s["teamId"]], x=s["x"], y=s["y"], xg=s["expectedGoals"],
                         xgot=s.get("expectedGoalsOnTarget") or 0.0, goal=s["eventType"] == "Goal",
                         on=bool(s["isOnTarget"]) and not s["isBlocked"] and not s.get("isSavedOffLine"),
                         gx=o.get("x"), gy=o.get("y")))
S = pd.DataFrame(rows)

# ---- drawing --------------------------------------------------------------------------------------------------
LINE = "#6a7c84"
X0 = 74.0            # show the pitch from here to the goal line (metres)
PS = 6.2             # px per metre
PW, PH = 68 * PS, (105 - X0) * PS


def pitch(d):
    L = f'stroke="{LINE}" stroke-width="2" fill="none"'
    m = lambda v: v * PS
    g = [f'<rect x="0" y="0" width="{PW}" height="{PH}" rx="6" fill="#22323a" {L}/>',
         f'<rect x="{m(34 - 20.16)}" y="0" width="{m(40.32)}" height="{m(16.5)}" {L}/>',
         f'<rect x="{m(34 - 9.16)}" y="0" width="{m(18.32)}" height="{m(5.5)}" {L}/>',
         f'<line x1="{m(34 - 3.66)}" y1="-6" x2="{m(34 + 3.66)}" y2="-6" stroke="#e8eeeb" stroke-width="5"/>',
         f'<circle cx="{m(34)}" cy="{m(11)}" r="3" fill="{LINE}"/>',
         f'<path d="M {m(34 - 7.3)} {m(16.5)} A {m(9.15)} {m(9.15)} 0 0 0 {m(34 + 7.3)} {m(16.5)}" {L}/>']
    d = d.sort_values("goal")
    for r in d.itertuples():
        far = r.x < X0                     # longer shots sit on the bottom edge of the drawing
        cx, cy, rad = m(68 - r.y), m(105 - max(r.x, X0)), 2.5 + 11 * r.xg ** 0.5
        if far and r.goal:
            dist = ((105 - r.x) ** 2 + (34 - r.y) ** 2) ** 0.5
            rad = max(rad, 6)
            g.append(f'<line x1="{cx:.1f}" y1="{cy - rad:.1f}" x2="{cx:.1f}" y2="{cy - 30:.1f}" stroke="{GOOD}" stroke-width="2"/>'
                     f'<text x="{cx:.1f}" y="{cy - 36:.1f}" text-anchor="middle" fill="#e8eeeb" stroke="#22323a" stroke-width="5" paint-order="stroke" '
                     f'font-size="15" font-weight="700" font-family="FT,FTX,sans-serif">goal from {dist:.0f} m</text>')
        if r.goal:
            g.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rad:.1f}" fill="{GOOD}" stroke="#1d2b33" stroke-width="2"/>')
        else:
            g.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rad:.1f}" fill="#e8eeeb" fill-opacity=".10" stroke="#c9d4cf" stroke-opacity=".75" stroke-width="2"/>')
    return f'<svg width="{PW}" height="{PH + 10}" viewBox="0 -10 {PW} {PH + 10}" style="overflow:visible">{"".join(g)}</svg>'


GW = 380
GS = GW / 2
GH = 0.6667 * GS


def mouth(d):
    d = d[d.on & d.gx.notna()].sort_values("goal")
    g = [f'<rect x="0" y="0" width="{GW}" height="{GH:.1f}" fill="#22323a"/>']
    for i in range(1, 8):
        g.append(f'<line x1="{GW * i / 8}" y1="0" x2="{GW * i / 8}" y2="{GH:.1f}" stroke="#2f424b" stroke-width="1"/>')
    for i in range(1, 4):
        g.append(f'<line x1="0" y1="{GH * i / 4:.1f}" x2="{GW}" y2="{GH * i / 4:.1f}" stroke="#2f424b" stroke-width="1"/>')
    for r in d.itertuples():
        cx, cy, rad = r.gx * GS, GH - r.gy * GS, 3 + 11.5 * r.xgot ** 0.5
        if r.goal:
            g.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rad:.1f}" fill="{GOOD}" stroke="#1d2b33" stroke-width="2"/>')
        else:
            g.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rad:.1f}" fill="{KEEP}" fill-opacity=".85" stroke="#1d2b33" stroke-width="2"/>')
    g.append(f'<path d="M -6 {GH + 3:.1f} L -6 -6 L {GW + 6} -6 L {GW + 6} {GH + 3:.1f}" stroke="#e8eeeb" stroke-width="7" fill="none" stroke-linejoin="round"/>')
    g.append(f'<line x1="-40" y1="{GH + 3:.1f}" x2="{GW + 40}" y2="{GH + 3:.1f}" stroke="{LINE}" stroke-width="2"/>')
    return f'<svg width="{GW + 80}" height="{GH + 30:.0f}" viewBox="-40 -20 {GW + 80} {GH + 30:.0f}" style="overflow:visible">{"".join(g)}</svg>'


def stat(label, val, c="#e8eeeb", sub=""):
    return (f'<div><div style="font-size:13.5px;letter-spacing:.1em;text-transform:uppercase;color:{MUT}">{label}</div>'
            f'<div class="num" style="font-size:30px;color:{c};line-height:1.15">{val}</div>'
            f'<div style="font-size:13.5px;color:{MUT}">{sub}</div></div>')


ON = S[S.on]
LG = dict(on=S.on.mean(), should=ON.xgot.mean(), went=ON.goal.mean())


def block(team, line):
    d = S[S.team == team]
    on = d[d.on]
    should, went = on.xgot.mean(), on.goal.mean()
    return f"""<div class="panel" style="padding:18px 26px 16px;margin-bottom:14px">
 <div style="display:flex;justify-content:space-between;align-items:baseline">
  <div style="font-size:32px;font-weight:800">{sh(team)}</div><div style="font-size:19px;color:#dbe3e6;font-style:italic">{line}</div></div>
 <div style="display:flex;gap:34px;align-items:flex-end;margin-top:12px">
  <div><div style="font-size:15px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:{MUT};margin-bottom:12px">Where they shoot from</div>{pitch(d)}</div>
  <div style="flex:1;display:flex;flex-direction:column;gap:16px">
   <div><div style="font-size:15px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:{MUT};margin-bottom:6px">Where the shots on target went</div>{mouth(d)}</div>
   <div style="display:flex;gap:30px;justify-content:center;text-align:center;width:{GW + 80}px">{stat("On target", f"{len(on) / len(d):.0%}", sub=f"{len(on)} of {len(d)}")}{stat("Should go in", f"{should:.0%}", KEEP, "of shots on target")}{stat("Went in", f"{went:.0%}", (GOOD if went > should else BAD) if abs(went - should) > .02 else "#e8eeeb", f"{int(d.goal.sum())} goals, no pens")}</div>
  </div></div></div>"""


legend = f"""<div class="panel note" style="padding:14px 24px;font-size:16.5px;line-height:1.55">
 <span style="display:inline-flex;align-items:center;gap:8px;margin-right:20px"><i style="width:15px;height:15px;border-radius:50%;background:{GOOD};display:inline-block"></i>goal</span>
 <span style="display:inline-flex;align-items:center;gap:8px;margin-right:20px"><i style="width:15px;height:15px;border-radius:50%;border:2px solid #c9d4cf;display:inline-block"></i>no goal</span>
 <span style="display:inline-flex;align-items:center;gap:8px;margin-right:20px"><i style="width:15px;height:15px;border-radius:50%;background:{KEEP};display:inline-block"></i>saved</span>
 Bigger circle = better chance (pitch) or harder to save (goal).<br>
 <b>Should go in</b> = how often an average keeper concedes shots like these (xGOT). League average: {LG["on"]:.0%} on target, {LG["should"]:.0%} should go in, {LG["went"]:.0%} went in. Penalties left out; longer shots sit on the pitch's bottom edge.</div>"""

STORY = [
    ("Shot maps · running hot", "Two ways<br>to run hot",
     "Both teams have scored more than their chances were worth, in different ways.",
     ("Chelsea", "Lots on target, and saveable shots going in"),
     ("Brighton & Hove Albion", "Well-placed shots, finished at a high rate")),
    ("Shot maps · running cold", "Same problem,<br>different reason",
     "Both have scored fewer than their chances deserved. Only one of them is shooting badly.",
     ("Nottingham Forest", "Only 1 shot in 5 hits the target"),
     ("AFC Bournemouth", "The best-placed shots in the league, kept out")),
    ("Shot maps · running cold", "Wrong in<br>both places",
     "Poor shooting and keepers in form against them: the two biggest gaps in the league.",
     ("Fulham", "On target, but easy for the keeper"),
     ("Sunderland", "Rarely on target, and saved when they are")),
]


def build():
    return [page(k, h, sub, block(*a) + block(*b) + legend) for k, h, sub, a, b in STORY]


async def main():
    html = f"<html><head><meta charset='utf-8'>{CSS}</head><body>{''.join(build())}</body></html>"
    open(OUT / "shotmaps.html", "w", encoding="utf-8").write(html)
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={"width": 1080, "height": 1350})
        await pg.goto((OUT / "shotmaps.html").as_uri()); await pg.evaluate("document.fonts.ready"); await pg.wait_for_timeout(300)
        print("fits:", await pg.evaluate("[...document.querySelectorAll('.body')].map(b=>[b.scrollHeight,b.clientHeight])"))
        for i, el in enumerate(await pg.query_selector_all("section.s")):
            await el.screenshot(path=str(OUT / f"page_5_shotmap_{i + 1}.png"))
        await b.close()


if __name__ == "__main__":
    asyncio.run(main())
