"""Step 3: player finishing, non-penalty. Placement = xGOT - xG; against keepers = goals - xGOT.
Shown for players with at least MIN_SHOTS non-penalty shots; the full table keeps everyone."""
import numpy as np
import pandas as pd

from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW, DATA, OUT = ROOT / "raw" / "fotmob_pl_2026_27", ROOT / "data", ROOT / "out"
DATA.mkdir(exist_ok=True); OUT.mkdir(exist_ok=True)
MIN_SHOTS = 15
S = pd.read_csv(DATA / "shots_xgot.csv")
N = S[~S.penalty].copy()
N["var"] = N.xg * (1 - N.xg)

g = N.groupby(["player_id", "player", "team"])
P = pd.DataFrame({
    "shots": g.size(), "on_target": g.on_target.sum(), "goals": g.goal.sum(),
    "xg": g.xg.sum(), "xgot": g.xgot.sum(), "sd": np.sqrt(g["var"].sum()),
}).reset_index()
P["xg_per_shot"] = P.xg / P.shots
P["on_target_pct"] = P.on_target / P.shots
P["finishing"] = P.goals - P.xg
P["placement"] = P.xgot - P.xg
P["vs_keepers"] = P.goals - P.xgot
P["z"] = P.finishing / P.sd
P = P.round(2)
P.to_csv(DATA / "players_finishing.csv", index=False)

Q = P[P.shots >= MIN_SHOTS].sort_values("finishing", ascending=False)
cols = ["player", "team", "shots", "on_target", "goals", "xg", "xgot", "finishing", "placement", "vs_keepers", "xg_per_shot", "z"]
print(f"{len(Q)} players with {MIN_SHOTS}+ non-penalty shots (of {len(P)} who shot)")
print("TOP 12 by finishing\n", Q[cols].head(12).to_string(index=False))
print("BOTTOM 12 by finishing\n", Q[cols].tail(12).to_string(index=False))
print("TOP 8 by placement\n", Q.sort_values("placement", ascending=False)[cols].head(8).to_string(index=False))
print("BOTTOM 8 by placement\n", Q.sort_values("placement")[cols].head(8).to_string(index=False))
print("check: player goals sum", P.goals.sum(), "= non-penalty goals", N.goal.sum())
