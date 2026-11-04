"""Fetch NHL special teams stats, compute STV, write data.json."""
import json, sys, urllib.request, datetime as dt
from zoneinfo import ZoneInfo

now = dt.datetime.now(ZoneInfo("America/Toronto"))
y = now.year if now.month >= 8 else now.year - 1
season = f"{y}{y+1}"
BASE = "https://api.nhle.com/stats/rest/en/team/"

def get(report):
    url = f"{BASE}{report}?limit=-1&cayenneExp=seasonId={season}%20and%20gameTypeId=2"
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)["data"]

def pick(row, *keys):
    for k in keys:
        if row.get(k) is not None:
            return row[k]
    raise KeyError(f"None of {keys} in row. Available keys: {sorted(row)}")

pp = {r["teamId"]: r for r in get("powerplay")}
pk = {r["teamId"]: r for r in get("penaltykill")}

teams = []
for tid, a in pp.items():
    b = pk.get(tid)
    if not b:
        continue
    ppg = pick(a, "powerPlayGoalsFor", "ppGoals")
    ppo = pick(a, "ppOpportunities", "powerPlayOpportunities")
    shga = pick(a, "shGoalsAgainst")
    pkga = pick(b, "ppGoalsAgainst", "powerPlayGoalsAgainst")
    pko = pick(b, "timesShorthanded", "pkOpportunities")
    shg = pick(b, "shGoalsFor")
    pp_pct = round(100 * ppg / ppo, 1) if ppo else 0.0
    pk_pct = round(100 * (1 - pkga / pko), 1) if pko else 0.0
    stv = round(pp_pct + pk_pct + 2 * shg - 2 * shga, 1)
    teams.append(dict(team=a["teamFullName"], ppg=ppg, ppo=ppo, pp_pct=pp_pct,
                      pkga=pkga, pko=pko, pk_pct=pk_pct, shg=shg, shga=shga, stv=stv))

if not teams:
    sys.exit("No team data returned (season may not have started).")
teams.sort(key=lambda t: t["stv"], reverse=True)
out = dict(season=season, updated=now.isoformat(timespec="minutes"), teams=teams)
json.dump(out, open("data.json", "w"), indent=1)
print(f"Wrote {len(teams)} teams for {season}")
