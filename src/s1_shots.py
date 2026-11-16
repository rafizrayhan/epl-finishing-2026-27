"""Step 1: build one row per shot with xG, xGOT and the keeper, then the team finishing table.

Own goals are left out (no shooter on the scoring team). Clearances off the line count as on target for the
shooter but are not keeper saves. xGOT is FotMob's post-shot model: 0 for shots off target or blocked.
"""
import glob
import json
import pandas as pd

from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW, DATA, OUT = ROOT / "raw" / "fotmob_pl_2026_27", ROOT / "data", ROOT / "out"
DATA.mkdir(exist_ok=True); OUT.mkdir(exist_ok=True)

rows = []
for f in sorted(glob.glob(str(RAW / "match_*.json"))):
    d = json.load(open(f))
    teams = {t["id"]: t["name"] for t in d["header"]["teams"]}
    for s in d["shotmap"]["shots"]:
        opp = [n for i, n in teams.items() if i != s["teamId"]][0]
        rows.append(dict(
            match_id=d["general"]["matchId"], team=teams[s["teamId"]], opponent=opp,
            player=s["playerName"], player_id=s["playerId"], minute=s["min"],
            event=s["eventType"], situation=s["situation"], shot_type=s["shotType"],
            xg=s["expectedGoals"], xgot=s.get("expectedGoalsOnTarget") or 0.0,
            on_target=bool(s["isOnTarget"]) and not s["isBlocked"], blocked=bool(s["isBlocked"]),
            own_goal=bool(s["isOwnGoal"]), off_line=bool(s.get("isSavedOffLine")),
            keeper_id=s.get("keeperId"), goal=s["eventType"] == "Goal"))
S = pd.DataFrame(rows)
S = S[~S.own_goal].copy()
S["penalty"] = S.situation.eq("Penalty")
S.to_csv(DATA / "shots_xgot.csv", index=False)

# checks
on = S[S.on_target]
checks = [
    ("100 matches", S.match_id.nunique() == 100),
    ("every goal is on target", S[S.goal].on_target.all()),
    ("no xGOT on shots off target or blocked", (S[~S.on_target].xgot == 0).all()),
    ("every goal has xGOT > 0", (S[S.goal].xgot > 0).all()),
]
for name, ok in checks:
    print(("PASS " if ok else "FAIL ") + name)
print(f"{len(S)} shots, {len(on)} on target, {S.goal.sum()} goals, xG {S.xg.sum():.1f}, xGOT {S.xgot.sum():.1f}")

T = S.groupby("team").agg(
    shots=("xg", "size"), on_target=("on_target", "sum"), goals=("goal", "sum"),
    xg=("xg", "sum"), xgot=("xgot", "sum"), pens=("penalty", "sum"),
    pen_goals=("goal", lambda g: (g & S.loc[g.index, "penalty"]).sum()),
    pen_xg=("xg", lambda v: v[S.loc[v.index, "penalty"]].sum()))
T["finishing"] = T.goals - T.xg          # goals above expected from the chances
T["placement"] = T.xgot - T.xg           # how much harder the shots were to save than the chances suggested
T["vs_keepers"] = T.goals - T.xgot       # what the keepers (and luck) did after the shot was struck
T["np_finishing"] = (T.goals - T.pen_goals) - (T.xg - T.pen_xg)
T["on_target_pct"] = T.on_target / T.shots
T = T.sort_values("finishing", ascending=False).round(2)
T.to_csv(DATA / "team_finishing.csv")
print(T[["shots", "on_target", "goals", "xg", "xgot", "finishing", "placement", "vs_keepers", "np_finishing", "pens", "pen_goals"]].to_string())
print("league:", T[["goals", "xg", "xgot"]].sum().round(1).to_dict())
