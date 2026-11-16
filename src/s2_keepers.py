"""Step 2: goalkeeper table. Goals prevented = xGOT faced - goals conceded, on shots on target that the keeper faced.

Left out: own goals (no xGOT), blocked shots (not on target), and clearances off the line (a defender, not the keeper).
"""
import pandas as pd

from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW, DATA, OUT = ROOT / "raw" / "fotmob_pl_2026_27", ROOT / "data", ROOT / "out"
DATA.mkdir(exist_ok=True); OUT.mkdir(exist_ok=True)
S = pd.read_csv(DATA / "shots_xgot.csv")
K = pd.read_csv(DATA / "keepers.csv")

F = S[S.on_target & ~S.off_line].copy()
F = F.merge(K, on="keeper_id", how="left")
print("on-target shots faced by a keeper:", len(F), "| no keeper id:", F.keeper.isna().sum(),
      "| club check (keeper's club = team that faced the shot):", (F.club == F.opponent).all())

g = F.groupby(["keeper", "club"])
G = pd.DataFrame({
    "matches": g.match_id.nunique(),
    "faced": g.size(),
    "conceded": g.goal.sum(),
    "xgot": g.xgot.sum(),
    "pens_faced": g.penalty.sum(),
    "pen_conceded": g.apply(lambda d: (d.goal & d.penalty).sum()),
    "pen_xgot": g.apply(lambda d: d.loc[d.penalty, "xgot"].sum()),
})
G["saves"] = G.faced - G.conceded
G["save_pct"] = G.saves / G.faced
G["prevented"] = G.xgot - G.conceded
G["np_prevented"] = (G.xgot - G.pen_xgot) - (G.conceded - G.pen_conceded)
G["prevented_per_match"] = G.prevented / G.matches
G = G.sort_values("prevented", ascending=False).round(2)
G.to_csv(DATA / "keepers_prevented.csv")
print(G[["matches", "faced", "saves", "conceded", "xgot", "prevented", "np_prevented", "pens_faced", "pen_conceded", "save_pct"]].to_string())
print("league total prevented:", G.prevented.sum().round(2), "| conceded", G.conceded.sum(), "| xGOT", G.xgot.sum().round(1))
# goals conceded from shots on target that no keeper id was attached to (off-line clearances excluded above)
print("goals in shots_xgot not attributed to a keeper:", S.goal.sum() - G.conceded.sum())
