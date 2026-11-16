"""Step 4: three charts in the dark style of the xPts carousel."""
import numpy as np
import pandas as pd
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from adjustText import adjust_text

for f in fm.findSystemFonts():
    if "Inter" in f: fm.fontManager.addfont(f)
plt.rcParams["font.family"] = ["Inter", "DejaVu Sans"]
BG, INK, MUT, GRID = "#0f1714", "#e8eeeb", "#9aa8a1", "#24302b"
GOOD, BAD = "#2bb886", "#e5534b"
PLACE, KEEP = "#5aa9e6", "#f2a541"
plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG, "text.color": INK,
                     "axes.labelcolor": INK, "xtick.color": MUT, "ytick.color": MUT, "axes.edgecolor": "#4b5a54"})
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW, DATA, OUT = ROOT / "raw" / "fotmob_pl_2026_27", ROOT / "data", ROOT / "out"
DATA.mkdir(exist_ok=True); OUT.mkdir(exist_ok=True)
SHORT = {"Nottingham Forest": "Nott'm Forest", "Manchester City": "Man City", "Manchester United": "Man Utd",
         "Newcastle United": "Newcastle", "Tottenham Hotspur": "Spurs", "AFC Bournemouth": "Bournemouth",
         "Brighton & Hove Albion": "Brighton", "Leeds United": "Leeds", "Ipswich Town": "Ipswich",
         "Coventry City": "Coventry", "Hull City": "Hull", "Crystal Palace": "Palace", "Aston Villa": "Aston Villa"}
FOOT = "Data: FotMob shot xG and xGOT (Opta models), first 10 games of 2026/27. Own goals left out. Rafiz Rayhan"


def style(ax):
    for s in ["top", "right"]: ax.spines[s].set_visible(False)


# 1 teams: finishing split into placement and against keepers -------------------------------------------
T = pd.read_csv(DATA / "team_finishing.csv", index_col=0).sort_values("finishing")
fig, ax = plt.subplots(figsize=(10, 11))
y = np.arange(len(T)); h = 0.36
ax.barh(y + h / 2, T.placement, height=h, color=PLACE, zorder=3)
ax.barh(y - h / 2, T.vs_keepers, height=h, color=KEEP, zorder=3)
ax.scatter(T.finishing, y, marker="D", s=46, color=INK, edgecolor=BG, lw=1, zorder=4)
for yi, (t, r) in zip(y, T.iterrows()):
    ax.text(8.6, yi, f"{r.finishing:+.1f}".replace("-", "−"), va="center", ha="right", fontsize=10.5, weight="bold",
            color=GOOD if r.finishing > 0 else BAD)
ax.axvline(0, color="#7d8b85", lw=1, zorder=2)
ax.set_yticks(y); ax.set_yticklabels([SHORT.get(t, t) for t in T.index], fontsize=11, color=INK)
ax.set_xlim(-8.2, 8.8); ax.set_ylim(-0.7, len(T) - 0.3)
ax.set_xlabel("Goals above (+) or below (−) expected", fontsize=11)
ax.grid(axis="x", color=GRID, zorder=0); style(ax)
ax.text(8.6, len(T) - 0.35, "Total", ha="right", fontsize=10, color=MUT)
ax.legend(handles=[Patch(color=PLACE, label="Placement: xGOT − xG\n(how hard the shots were to save)"),
                   Patch(color=KEEP, label="Against keepers: goals − xGOT\n(the saves, and luck)"),
                   Line2D([], [], marker="D", ls="", color=INK, label="Total: goals − xG")],
          loc="upper left", bbox_to_anchor=(0.0, 1.0), frameon=False, fontsize=9.5, labelcolor=INK, labelspacing=1.0)
ax.set_title("Why are teams scoring more or fewer than their chances?\nFinishing split into shot placement and what the keepers did",
             fontsize=13, loc="left")
fig.text(0.01, 0.005, FOOT + ". The whole league is −26.8 on placement this season (about −1.3 a team).", fontsize=8, color=MUT)
plt.tight_layout(rect=(0, 0.015, 1, 1)); plt.savefig(f"{OUT}/chart_teams.png", dpi=170); plt.close(fig)

# 2 keepers: goals prevented with ±1 SD ------------------------------------------------------------------
S = pd.read_csv(DATA / "shots_xgot.csv"); K = pd.read_csv(DATA / "keepers.csv")
F = S[S.on_target & ~S.off_line].merge(K, on="keeper_id")
F["var"] = F.xgot * (1 - F.xgot)
G = F.groupby(["keeper", "club"]).agg(faced=("xgot", "size"), xgot=("xgot", "sum"), ga=("goal", "sum"), v=("var", "sum")).reset_index()
G["prev"] = G.xgot - G.ga; G["sd"] = np.sqrt(G.v)
G = G[G.faced >= 20].sort_values("prev").reset_index(drop=True)
fig, ax = plt.subplots(figsize=(10, 10.5))
y = np.arange(len(G))
for yi, r in G.iterrows():
    ax.barh(yi, 2 * r.sd, left=-r.sd, height=0.72, color="#1c2823", zorder=1)
ax.barh(y, G.prev, height=0.5, color=[GOOD if p > 0 else BAD for p in G.prev], zorder=3)
for yi, r in G.iterrows():
    out = abs(r.prev) > 2 * r.sd
    ax.text(r.prev + (0.15 if r.prev > 0 else -0.15), yi, f"{r.prev:+.1f}".replace("-", "−") + (" ●" if out else ""), va="center",
            ha="left" if r.prev > 0 else "right", fontsize=10, color=INK, weight="bold" if out else "normal")
ax.axvline(0, color="#7d8b85", lw=1, zorder=2)
ax.set_yticks(y); ax.set_yticklabels([f"{k}  ·  {SHORT.get(c, c)}" for k, c in zip(G.keeper, G.club)], fontsize=10.5, color=INK)
ax.set_xlim(-7.2, 7.2); ax.set_ylim(-0.7, len(G) - 0.3)
ax.set_xlabel("Goals prevented: expected goals on target faced − goals conceded", fontsize=11)
ax.grid(axis="x", color=GRID, zorder=0); style(ax)
ax.legend(handles=[Patch(color="#1c2823", label="Normal luck\n(±1 SD)"),
                   Line2D([], [], marker="o", ls="", color=INK, label="Beyond 2 SD")],
          loc="upper left", frameon=False, fontsize=9.5, labelcolor=INK)
ax.set_title("Which goalkeepers are saving more than expected?\nKeepers who have faced 20+ shots on target",
             fontsize=13, loc="left")
fig.text(0.01, 0.005, FOOT + ". Clearances off the line not counted as saves.", fontsize=8, color=MUT)
plt.tight_layout(rect=(0, 0.015, 1, 1)); plt.savefig(f"{OUT}/chart_keepers.png", dpi=170); plt.close(fig)

# 3 players: goals v xG -----------------------------------------------------------------------------------
P = pd.read_csv(DATA / "players_finishing.csv")
Q = P[P.shots >= 15].copy()
fig, ax = plt.subplots(figsize=(10, 10))
lo, hi = 0, 9.6
ax.plot([lo, hi], [lo, hi], color="#7d8b85", lw=1.2, ls="--", zorder=1)
col = [GOOD if f > 0.05 else (BAD if f < -0.05 else MUT) for f in Q.finishing]
ax.scatter(Q.xg, Q.goals, s=36 + Q.shots * 3, c=col, alpha=0.9, edgecolor=BG, lw=1, zorder=3)
lab = Q[(Q.finishing.abs() >= 1.5) | (Q.xg >= 4.2)].copy()
def name(r):
    v = f"{r.finishing:+.1f}".replace("-", "−")
    return f"{r.player} ({v})"
lab["txt"] = [name(r) for _, r in lab.iterrows()]
# players on the same spot share one label
lab["key"] = lab.xg.round(1).astype(str) + "_" + lab.goals.astype(str)
merged = lab.groupby("key").agg(xg=("xg", "mean"), goals=("goals", "first"), txt=("txt", lambda t: "\n".join(t))).reset_index()
texts = [ax.text(r.xg, r.goals, r.txt, fontsize=9.5, zorder=4) for _, r in merged.iterrows()]
adjust_text(texts, x=Q.xg.values, y=Q.goals.values, ax=ax, expand=(1.2, 1.5), force_text=(0.5, 0.8),
            arrowprops=dict(arrowstyle="-", color="#5f6e68", lw=0.7), min_arrow_len=6)
ax.text(0.3, 9.2, "Scored more than xG", color=GOOD, fontsize=11, weight="bold", va="top")
ax.text(5.6, 0.3, "Scored fewer than xG", color=BAD, fontsize=11, weight="bold")
ax.set_xlim(lo, hi); ax.set_ylim(-0.4, hi); ax.set_aspect("equal")
ax.set_xlabel("Expected goals (non-penalty xG)", fontsize=12); ax.set_ylabel("Non-penalty goals", fontsize=12)
ax.grid(color=GRID, zorder=0); style(ax)
ax.set_title("Who is finishing above and below their chances?\nPlayers with 15+ non-penalty shots · bigger dot = more shots",
             fontsize=13, loc="left")
fig.text(0.01, 0.005, FOOT + ". Penalties left out.", fontsize=8, color=MUT)
plt.tight_layout(rect=(0, 0.015, 1, 1)); plt.savefig(f"{OUT}/chart_players.png", dpi=170); plt.close(fig)
print("ok")
