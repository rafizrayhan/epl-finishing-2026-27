"""Step 5: the five charts as designed 1080x1350 pages (HTML + Playwright), in the xPts carousel's dark style and fonts."""
import asyncio
import re
import pandas as pd
from playwright.async_api import async_playwright

from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW, DATA, OUT = ROOT / "raw" / "fotmob_pl_2026_27", ROOT / "data", ROOT / "out"
DATA.mkdir(exist_ok=True); OUT.mkdir(exist_ok=True)
FONTDIR = ROOT / "fonts"
def _ff(fam, f, w): return f"@font-face{{font-family:{fam};src:url('{(FONTDIR / f).as_uri()}') format('woff2');font-weight:{w}}}"
FONTS = "".join([_ff("BS", "big-shoulders-display-latin-800-normal.woff2", 800), _ff("BSX", "big-shoulders-display-latin-ext-800-normal.woff2", 800)]
                + [_ff("FT", f"figtree-latin-{w}-normal.woff2", w) + _ff("FTX", f"figtree-latin-ext-{w}-normal.woff2", w) for w in (400, 500, 600, 700, 800)])
GOOD, BAD, SHOOT, KEEP, MUT = "#2bb886", "#e5534b", "#5aa9e6", "#f2a541", "#b3c0c5"
SHORT = {"Nottingham Forest": "Nott'm Forest", "Manchester City": "Man City", "Manchester United": "Man Utd",
         "Newcastle United": "Newcastle", "Tottenham Hotspur": "Spurs", "AFC Bournemouth": "Bournemouth",
         "Brighton & Hove Albion": "Brighton", "Leeds United": "Leeds", "Ipswich Town": "Ipswich",
         "Coventry City": "Coventry", "Hull City": "Hull", "Crystal Palace": "Palace"}
sh = lambda t: SHORT.get(t, t)
sgn = lambda v: f"{v:+.1f}".replace("-", "−")
col = lambda v: GOOD if v > 0 else BAD
FOOT = "Premier League 2026/27 · first 10 games · data: FotMob (Opta xG models) · own goals left out"

CSS = f"""<style>{FONTS}
*{{box-sizing:border-box;margin:0;padding:0}} body{{background:#111}}
.s{{width:1080px;height:1350px;position:relative;overflow:hidden;background:#1d2b33;color:#e8eeeb;font-family:FT,FTX,sans-serif;
   padding:70px 72px 0;display:flex;flex-direction:column;page-break-after:always}}
.k{{font-weight:700;font-size:21px;letter-spacing:.18em;text-transform:uppercase;color:{GOOD}}}
.h{{font-family:BS,BSX,sans-serif;font-weight:800;text-transform:uppercase;font-size:86px;line-height:.9;margin-top:16px}}
.sub{{font-size:25px;line-height:1.38;color:#d0dadd;margin-top:20px;max-width:900px}}
.body{{flex:1;display:flex;flex-direction:column;justify-content:center;padding:26px 0 18px}}
.foot{{flex:none;height:92px;border-top:1px solid #364850;display:flex;justify-content:space-between;align-items:center;font-size:17px;color:{MUT}}}
.foot b{{color:#e8eeeb;font-weight:700}}
.num{{font-variant-numeric:tabular-nums;font-weight:800}}
.panel{{background:#26363f;border:1px solid #364850;border-radius:20px}}
.note{{font-size:20px;line-height:1.45;color:#dbe3e6}}
</style>"""


def page(kicker, head, sub, body):
    return f"""<section class="s"><div class="k">{kicker}</div><div class="h">{head}</div><div class="sub">{sub}</div>
<div class="body">{body}</div><div class="foot"><span>{FOOT}</span><b>Rafiz Rayhan</b></div></section>"""


T = pd.read_csv(DATA / "team_finishing.csv", index_col=0)
G = pd.read_csv(DATA / "keepers_prevented.csv")
P = pd.read_csv(DATA / "players_finishing.csv")
pages = []

# 0 explainer ----------------------------------------------------------------------------------------------------
steps = [("1", "The chance", "Expected goals · xG", GOOD,
          "How often an average player scores from that spot, in that situation.",
          "A 12-yard shot after a cut-back", "0.20", "scored about 1 time in 5"),
         ("2", "The shot", "Expected goals on target · xGOT", SHOOT,
          "Re-rates the shot once it is struck, from where it ends up in the goal.",
          "Same chance, into the top corner", "0.70", "straight at the keeper: 0.05"),
         ("3", "The keeper", "Goal or save", KEEP,
          "Did it go in? Keeping out hard-to-save shots is saving goals.",
          "Keeper saves that 0.70 shot", "+0.70", "goals prevented")]
cards = "".join(f"""<div class="panel" style="display:flex;gap:30px;padding:30px 34px;margin-bottom:22px;border-left:8px solid {c}">
 <div style="flex:1"><div style="font-weight:700;font-size:19px;letter-spacing:.16em;text-transform:uppercase;color:{c}">{n} · {a}</div>
  <div style="font-size:31px;font-weight:800;margin-top:10px">{b}</div><div class="note" style="margin-top:10px">{d}</div></div>
 <div style="width:250px;border-left:1px solid #3a4d55;padding-left:28px;display:flex;flex-direction:column;justify-content:center">
  <div style="font-size:13px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:{MUT};margin-bottom:4px">For example</div>
  <div style="font-size:17px;color:{MUT};line-height:1.3">{e}</div><div class="num" style="font-size:52px;color:{c};margin:6px 0 2px">{v}</div>
  <div style="font-size:17px;color:{MUT}">{f}</div></div></div>""" for n, a, b, c, d, e, v, f in steps)
formula = f"""<div style="display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:6px">
 <div class="panel" style="padding:22px 26px"><div style="font-size:19px;font-weight:700;color:{SHOOT}">Their shooting</div>
  <div style="font-size:30px;font-weight:800;margin-top:6px">xGOT − xG</div><div class="note" style="font-size:18px;margin-top:4px">how much the shot beat the chance</div></div>
 <div class="panel" style="padding:22px 26px"><div style="font-size:19px;font-weight:700;color:{KEEP}">The keepers faced</div>
  <div style="font-size:30px;font-weight:800;margin-top:6px">goals − xGOT</div><div class="note" style="font-size:18px;margin-top:4px">how many of those shots went in</div></div></div>"""
pages.append(page("How to read this", "Three numbers<br>behind every goal",
                  "A goal is a chance, then a shot, then a save or not. Splitting them shows whether a team's finishing is about the shooting or the keepers.",
                  cards + formula))

# 1 teams -------------------------------------------------------------------------------------------------------
TT = T.sort_values("finishing", ascending=False)
M = 8.0  # half-width of the scale in goals
rows = ""
for t, r in TT.iterrows():
    v = r.finishing; w = abs(v) / M * 50
    bar = (f'<div style="position:absolute;left:50%;width:{w}%;top:7px;bottom:7px;background:{GOOD};border-radius:0 6px 6px 0"></div>'
           f'<div class="num" style="position:absolute;left:calc(50% + {w}% + 10px);top:0;line-height:38px;font-size:21px">{sgn(v)}</div>') if v >= 0 else \
          (f'<div style="position:absolute;right:50%;width:{w}%;top:7px;bottom:7px;background:{BAD};border-radius:6px 0 0 6px"></div>'
           f'<div class="num" style="position:absolute;right:calc(50% + {w}% + 10px);top:0;line-height:38px;font-size:21px">{sgn(v)}</div>')
    rows += f"""<div style="display:flex;align-items:center;height:41px;border-bottom:1px solid #2c3d45">
 <div style="width:190px;font-size:22px;font-weight:600">{sh(t)}</div>
 <div style="flex:1;position:relative;height:38px">{bar}<div style="position:absolute;left:50%;top:-2px;bottom:-2px;border-left:2px solid #6a7c84"></div></div>
 <div style="width:150px;text-align:right;font-size:19px;color:{MUT}"><b style="color:#e8eeeb">{int(r.goals)}</b> from {r.xg:.1f}</div></div>"""
head1 = f"""<div style="display:flex;font-size:16px;letter-spacing:.12em;text-transform:uppercase;color:{MUT};padding-bottom:10px;border-bottom:1px solid #3a4d55">
 <div style="width:190px">Team</div><div style="flex:1;display:flex;justify-content:space-between;padding:0 30px"><span style="color:{BAD}">◀ fewer than expected</span><span style="color:{GOOD}">more than expected ▶</span></div>
 <div style="width:150px;text-align:right">Goals · xG</div></div>"""
axis = f'<div style="position:relative;height:0"><div style="position:absolute;left:190px;right:150px;top:-{44*20}px;height:{44*20}px"><div style="position:absolute;left:50%;top:0;bottom:0;border-left:2px solid #6a7c84"></div></div></div>'
pages.append(page("Finishing after 10 games", "Who is scoring<br>more than their chances?",
                  "Goals scored minus the goals their chances were worth (xG). Sunderland scored 8 from chances worth 15.6.",
                  head1 + rows))

# 2 why ---------------------------------------------------------------------------------------------------------
pick = [("Chelsea", "Shots going in that keepers usually save"), ("Brighton & Hove Albion", "Well-placed shots, and a bit of luck"),
        ("AFC Bournemouth", "Good shots, but keepers keep saving them"), ("Nottingham Forest", "The shooting itself: wide, or at the keeper"),
        ("Fulham", "The shooting, plus good keepers"), ("Sunderland", "Both: poor shooting and hot keepers")]
SC = 8.5
def mini(v, c):
    w = abs(v) / SC * 50
    if v >= 0:
        return (f'<div style="position:absolute;left:50%;width:{w}%;top:4px;bottom:4px;background:{c};border-radius:0 5px 5px 0"></div>'
                f'<div class="num" style="position:absolute;left:calc(50% + {w}% + 8px);line-height:28px;font-size:19px">{sgn(v)}</div>')
    return (f'<div style="position:absolute;right:50%;width:{w}%;top:4px;bottom:4px;background:{c};border-radius:5px 0 0 5px"></div>'
            f'<div class="num" style="position:absolute;right:calc(50% + {w}% + 8px);line-height:28px;font-size:19px">{sgn(v)}</div>')
cards = ""
for t, verdict in pick:
    r = T.loc[t]
    cards += f"""<div class="panel" style="padding:16px 24px 14px;margin-bottom:12px;display:flex;gap:22px;align-items:center">
 <div style="width:250px"><div style="font-size:27px;font-weight:800">{sh(t)}</div>
  <div style="font-size:16.5px;color:#dbe3e6;line-height:1.3;margin-top:4px;font-style:italic">{verdict}</div></div>
 <div style="flex:1"><div style="display:flex;align-items:center;height:30px"><div style="width:135px;font-size:16px;font-weight:700;color:{SHOOT}">Shooting</div>
   <div style="flex:1;position:relative;height:28px;border-left:0">{mini(r.placement, SHOOT)}<div style="position:absolute;left:50%;top:-4px;bottom:-34px;border-left:2px solid #6a7c84"></div></div></div>
  <div style="display:flex;align-items:center;height:30px;margin-top:4px"><div style="width:135px;font-size:16px;font-weight:700;color:{KEEP}">Keepers faced</div>
   <div style="flex:1;position:relative;height:28px">{mini(r.vs_keepers, KEEP)}</div></div></div>
 <div style="width:96px;text-align:right"><div style="font-size:14px;letter-spacing:.12em;color:{MUT};text-transform:uppercase">Total</div>
  <div class="num" style="font-size:34px;color:{col(r.finishing)}">{sgn(r.finishing)}</div></div></div>"""
key = f"""<div class="panel" style="padding:18px 24px;margin-top:6px;font-size:17px;line-height:1.5">
 <div style="font-weight:700">Numbers are goals. Total = goals − xG = shooting + keepers faced</div>
 <div style="color:{SHOOT}"><b>Shooting = xGOT − xG.</b> + shots harder to save than the chance suggested · − wide or straight at the keeper</div>
 <div style="color:{KEEP}"><b>Keepers faced = goals − xGOT.</b> + more of their shots went in than usual · − opposing keepers saved more than usual</div>
 <div style="color:#dbe3e6">League average shooting this season: −1.3 per team, so compare each team with that, not with zero.</div></div>"""
pages.append(page("Why the gaps?", "Bad shooting,<br>or great goalkeeping?",
                  "Each team's gap split in two: their own shooting, and what the goalkeepers did against them.", cards + key))

# 3 keepers -----------------------------------------------------------------------------------------------------
GG = G[G.faced >= 20].sort_values("prevented", ascending=False)
sel = list(GG.head(5).itertuples()) + [None] + list(GG.tail(5).itertuples())
KM = 7.5
rows = ""
for r in sel:
    if r is None:
        rows += f'<div style="text-align:center;font-size:17px;color:{MUT};padding:10px 0;border-bottom:1px dashed #3a4d55;margin-bottom:6px">· · ·  {len(GG) - 10} keepers in between  · · ·</div>'
        continue
    v = r.prevented; w = abs(v) / KM * 50
    bar = (f'<div style="position:absolute;left:50%;width:{w}%;top:10px;bottom:10px;background:{GOOD};border-radius:0 7px 7px 0"></div>'
           f'<div class="num" style="position:absolute;left:calc(50% + {w}% + 12px);line-height:62px;font-size:25px">{sgn(v)}</div>') if v > 0 else \
          (f'<div style="position:absolute;right:50%;width:{w}%;top:10px;bottom:10px;background:{BAD};border-radius:7px 0 0 7px"></div>'
           f'<div class="num" style="position:absolute;right:calc(50% + {w}% + 12px);line-height:62px;font-size:25px">{sgn(v)}</div>')
    cc = GOOD if v > 0 else BAD
    star = f' <span style="font-size:13px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:{cc};border:1.5px solid {cc};border-radius:20px;padding:2px 9px;vertical-align:4px;margin-left:6px">stands out most</span>' \
        if r.keeper in ("Bart Verbruggen", "Carl Rushworth") else ""
    rows += f"""<div style="display:flex;align-items:center;height:66px">
 <div style="width:330px"><div style="font-size:23px;font-weight:700;white-space:nowrap">{r.keeper}{star}</div><div style="font-size:17px;color:{MUT}">{sh(r.club)} · faced {r.faced} on target</div></div>
 <div style="flex:1;position:relative;height:62px">{bar}<div style="position:absolute;left:50%;top:0;bottom:0;border-left:2px solid #6a7c84"></div></div></div>"""
note = f"""<div class="panel note" style="padding:20px 26px;margin-top:18px;font-size:19px">Goals prevented = xGOT faced − goals conceded. Verbruggen and Rushworth stand out most, but with this many keepers one or two
 would look this extreme by chance alone: it takes more games to be sure. Keepers with 20+ shots on target faced.</div>"""
pages.append(page("Goalkeepers", "Which keepers are<br>saving the most?",
                  "Goals kept out above what an average keeper would have saved from the same shots.", rows + note))

# 4 players -----------------------------------------------------------------------------------------------------
Q = P[P.shots >= 15].sort_values("finishing", ascending=False)
sel = list(Q.head(5).itertuples()) + [None] + list(Q.tail(5).itertuples())
XM = 8.0
rows = ""
for r in sel:
    if r is None:
        rows += f'<div style="border-bottom:1px dashed #3a4d55;margin:6px 0 12px"></div>'
        continue
    c = col(r.finishing); a, b = sorted([r.xg, r.goals])
    rows += f"""<div style="display:flex;align-items:center;height:64px">
 <div style="width:330px"><div style="font-size:23px;font-weight:700">{r.player}</div>
  <div style="font-size:17px;color:{MUT}">{sh(r.team)} · {int(r.goals)} goal{'s' if r.goals != 1 else ''} from {r.xg:.1f} xG</div></div>
 <div style="flex:1;position:relative;height:40px">
  <div style="position:absolute;left:{a / XM * 82}%;width:{(b - a) / XM * 82}%;top:17px;height:6px;background:{c};border-radius:3px"></div>
  <div style="position:absolute;left:calc({r.xg / XM * 82}% - 11px);top:9px;width:22px;height:22px;border-radius:50%;border:3px solid {MUT};background:#1d2b33"></div>
  <div style="position:absolute;left:calc({r.goals / XM * 82}% - 12px);top:8px;width:24px;height:24px;border-radius:50%;background:{c}"></div>
  <div class="num" style="position:absolute;left:calc({b / XM * 82}% + 20px);line-height:40px;font-size:23px;color:{c}">{sgn(r.finishing)}</div></div></div>"""
ticks = "".join(f'<span style="position:absolute;left:calc({v / XM * 82}% - 6px)">{v}</span>' for v in range(0, 9, 2))
legend = f"""<div style="display:flex;gap:30px;align-items:center;font-size:18px;color:{MUT};margin:0 0 14px 330px">
 <span style="display:flex;align-items:center;gap:10px"><i style="width:20px;height:20px;border-radius:50%;border:3px solid {MUT};display:inline-block"></i>chances were worth (xG)</span>
 <span style="display:flex;align-items:center;gap:10px"><i style="width:20px;height:20px;border-radius:50%;background:#e8eeeb;display:inline-block"></i>goals scored</span></div>"""
axis = f'<div style="margin-left:330px;position:relative;height:26px;font-size:16px;color:{MUT};border-top:1px solid #3a4d55;padding-top:4px">{ticks}</div>'
note = f'<div class="panel note" style="padding:18px 26px;margin-top:16px;font-size:19px">Penalties left out. Players with 15+ shots. Cherki stands out most, but with 53 players one or two would look this hot or cold by chance alone.</div>'
pages.append(page("Finishers", "Hottest and coldest<br>finishers",
                  "Goals scored against the goals their chances were worth.", legend + rows + axis + note))

html = f"<html><head><meta charset='utf-8'>{CSS}</head><body>{''.join(pages)}</body></html>"
open(OUT / "pages.html", "w", encoding="utf-8").write(html)
NAMES = ["page_0_explainer", "page_1_teams", "page_2_why", "page_3_keepers", "page_4_players"]


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={"width": 1080, "height": 1350})
        await pg.goto((OUT / "pages.html").as_uri()); await pg.wait_for_timeout(1500); await pg.evaluate("document.fonts.ready"); await pg.wait_for_timeout(300)
        secs = await pg.query_selector_all("section.s")
        for el, n in zip(secs, NAMES):
            await el.screenshot(path=f"{OUT}/{n}.png")
        # overflow check: body content must fit above the footer
        print(await pg.evaluate("""[...document.querySelectorAll('section.s')].map(s=>{const b=s.querySelector('.body');return [b.scrollHeight,b.clientHeight]})"""))
        await b.close()
asyncio.run(main())
