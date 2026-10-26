import requests

url = "https://fantasy.premierleague.com/api/bootstrap-static/"
data = requests.get(url).json()

players = data["elements"]

for player in sorted(players, key=lambda p: p["total_points"], reverse=True)[:10]:
    name = player["web_name"]
    price = player["now_cost"] / 10
    points = player["total_points"]
    print(name, "£" + str(price) + "m", points, "points")
