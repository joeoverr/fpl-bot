import requests
import ollama

url = "https://fantasy.premierleague.com/api/bootstrap-static/"
data = requests.get(url).json()

teams = {t["id"]: t["short_name"] for t in data["teams"]}
positions = {p["id"]: p["singular_name_short"] for p in data["element_types"]}

top = sorted(data["elements"], key=lambda p: p["total_points"], reverse=True)[:60]

lines = []
for p in top:
    lines.append(f"{p['web_name']} ({teams[p['team']]}, {positions[p['element_type']]}) £{p['now_cost']/10}m, {p['total_points']} pts, form {p['form']}")
player_info = "\n".join(lines)

messages = [{"role": "system", "content": "You are a Fantasy Premier League adviser for the current season. Only use the player data below. If the answer isn't in it, say you don't know.\n\n" + player_info}]

print("FPL bot ready! Type quit to exit.")
while True:
    question = input("You: ")
    if question == "quit":
        break
    messages.append({"role": "user", "content": question})
    response = ollama.chat(model="llama3.1:8b", messages=messages)
    answer = response["message"]["content"]
    messages.append({"role": "assistant", "content": answer})
    print("Bot:", answer)