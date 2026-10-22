import requests
import ollama

BASE = "https://fantasy.premierleague.com/api/"

print("Loading live FPL data...")
data = requests.get(BASE + "bootstrap-static/").json()
teams = {t["id"]: t["short_name"] for t in data["teams"]}
positions = {p["id"]: p["singular_name_short"] for p in data["element_types"]}
players = {p["id"]: p for p in data["elements"]}
gameweek = next(e["id"] for e in data["events"] if e["is_current"])

# Next 3 fixtures for every team
upcoming = {}
for f in requests.get(BASE + "fixtures/?future=1").json():
    if f["event"] is None:
        continue
    games = [(f["team_h"], f["team_a"], "H", f["team_h_difficulty"]),
             (f["team_a"], f["team_h"], "A", f["team_a_difficulty"])]
    for team, opponent, venue, difficulty in games:
        upcoming.setdefault(team, [])
        if len(upcoming[team]) < 3:
            upcoming[team].append(f"{teams[opponent]} {venue} (diff {difficulty})")

def describe(p):
    fixtures = ", ".join(upcoming.get(p["team"], []))
    return (f"{p['web_name']} ({teams[p['team']]}, {positions[p['element_type']]}) "
            f"£{p['now_cost']/10}m, {p['total_points']} pts, form {p['form']}, next: {fixtures}")

# Your team
team_id = input("Enter your FPL team ID: ")
picks = requests.get(f"{BASE}entry/{team_id}/event/{gameweek}/picks/").json()["picks"]
my_team = "\n".join(describe(players[pick["element"]]) for pick in picks)

# Top 40 scorers as transfer options
top = sorted(players.values(), key=lambda p: p["total_points"], reverse=True)[:40]
options = "\n".join(describe(p) for p in top)

system = ("You are a Fantasy Premier League adviser for the current season, gameweek "
          f"{gameweek}. Only use the data below. If the answer isn't in it, say you don't know. "
          "Fixture difficulty runs from 1 (easy) to 5 (hard).\n\n"
          f"MY TEAM:\n{my_team}\n\nTOP PLAYERS:\n{options}")
messages = [{"role": "system", "content": system}]

print("FPL bot ready! Type quit to exit.")
while True:
    question = input("You: ")
    if question == "quit":
        break
    messages.append({"role": "user", "content": question})
    response = ollama.chat(model="llama3.1:8b", messages=messages, options={"num_ctx": 8192})
    answer = response["message"]["content"]
    messages.append({"role": "assistant", "content": answer})
    print("Bot:", answer)