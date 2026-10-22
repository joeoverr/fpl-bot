import threading
import requests
import ollama
import customtkinter as ctk

BASE = "https://fantasy.premierleague.com/api/"
BG, PANEL, BORDER, TEXT, MUTED = "#1C1C1E", "#2C2C2E", "#3A3A3C", "#EDEDED", "#9A9A9F"
messages = []

def build_system(team_id):
    data = requests.get(BASE + "bootstrap-static/").json()
    teams = {t["id"]: t["short_name"] for t in data["teams"]}
    positions = {p["id"]: p["singular_name_short"] for p in data["element_types"]}
    players = {p["id"]: p for p in data["elements"]}
    gameweek = next(e["id"] for e in data["events"] if e["is_current"])

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

    picks = requests.get(f"{BASE}entry/{team_id}/event/{gameweek}/picks/").json()["picks"]
    my_team = "\n".join(describe(players[pick["element"]]) for pick in picks)
    top = sorted(players.values(), key=lambda p: p["total_points"], reverse=True)[:40]
    options = "\n".join(describe(p) for p in top)

    return ("You are a Fantasy Premier League adviser for the current season, gameweek "
            f"{gameweek}. Only use the data below. If the answer isn't in it, say you don't know. "
            "Fixture difficulty runs from 1 (easy) to 5 (hard).\n\n"
            f"MY TEAM:\n{my_team}\n\nTOP PLAYERS:\n{options}")

def add_message(sender, text):
    chat.configure(state="normal")
    chat.insert("end", f"{sender}\n{text}\n\n")
    chat.configure(state="disabled")
    chat.see("end")

def load_team():
    team_id = team_entry.get().strip()
    if not team_id:
        return
    add_message("FPL Bot", "Loading live FPL data...")
    def work():
        try:
            system = build_system(team_id)
            messages.clear()
            messages.append({"role": "system", "content": system})
            app.after(0, add_message, "FPL Bot", "Team loaded! Ask me anything.")
        except Exception:
            app.after(0, add_message, "FPL Bot", "Couldn't load that team. Check the ID and your internet.")
    threading.Thread(target=work, daemon=True).start()

def finish(answer):
    add_message("FPL Bot", answer)
    send_button.configure(state="normal", text="Send")

def send(event=None):
    question = input_box.get().strip()
    if not question:
        return
    if not messages:
        add_message("FPL Bot", "Load your team first, using the box at the top.")
        return
    input_box.delete(0, "end")
    add_message("You", question)
    send_button.configure(state="disabled", text="Thinking...")
    messages.append({"role": "user", "content": question})
    def work():
        try:
            response = ollama.chat(model="llama3.1:8b", messages=messages, options={"num_ctx": 8192})
            answer = response["message"]["content"]
            messages.append({"role": "assistant", "content": answer})
        except Exception:
            answer = "Couldn't reach the AI. Is Ollama running?"
        app.after(0, finish, answer)
    threading.Thread(target=work, daemon=True).start()

# ----- The window -----
ctk.set_appearance_mode("dark")
app = ctk.CTk(fg_color=BG)
app.title("FPL Bot")
app.geometry("720x780")

top_bar = ctk.CTkFrame(app, fg_color=PANEL, corner_radius=12)
top_bar.pack(fill="x", padx=16, pady=(16, 8))
ctk.CTkLabel(top_bar, text="FPL Bot", font=("Segoe UI", 20, "bold"), text_color=TEXT).pack(side="left", padx=14, pady=12)
load_button = ctk.CTkButton(top_bar, text="Load team", width=100, fg_color=BORDER, hover_color="#48484A",
                            text_color=TEXT, command=load_team)
load_button.pack(side="right", padx=(6, 14))
team_entry = ctk.CTkEntry(top_bar, placeholder_text="Team ID", width=140, fg_color=BG,
                          border_color=BORDER, text_color=TEXT)
team_entry.pack(side="right")

chat = ctk.CTkTextbox(app, fg_color=PANEL, text_color=TEXT, corner_radius=12, wrap="word",
                      font=("Segoe UI", 14), border_width=0)
chat.pack(fill="both", expand=True, padx=16, pady=8)
chat.configure(state="disabled")

bottom = ctk.CTkFrame(app, fg_color="transparent")
bottom.pack(fill="x", padx=16, pady=(8, 16))
input_box = ctk.CTkEntry(bottom, placeholder_text="Ask about your team...", height=42, fg_color=PANEL,
                         border_color=BORDER, text_color=TEXT, font=("Segoe UI", 14))
input_box.pack(side="left", fill="x", expand=True, padx=(0, 8))
input_box.bind("<Return>", send)
send_button = ctk.CTkButton(bottom, text="Send", width=100, height=42, fg_color=BORDER,
                            hover_color="#48484A", text_color=TEXT, command=send)
send_button.pack(side="right")

add_message("FPL Bot", "Enter your team ID at the top and click Load team.")
app.mainloop()