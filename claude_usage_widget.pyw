import json, os, subprocess, tkinter as tk, urllib.error, urllib.request
from datetime import datetime

CREDS = os.path.expanduser("~/.claude/.credentials.json")
REFRESH_MS = 60_000
BG, RING_BG, ACCENT = "#1f1f1e", "#3a3a38", "#d97757"
SIZE, W = 96, 12


def fetch_usage():
    """로그인 안 됐거나 토큰이 만료됐으면 None."""
    if not os.path.exists(CREDS):
        return None
    token = json.load(open(CREDS, encoding="utf-8"))["claudeAiOauth"]["accessToken"]
    req = urllib.request.Request(
        "https://api.anthropic.com/api/oauth/usage",
        headers={"Authorization": "Bearer " + token, "anthropic-beta": "oauth-2025-04-20"},
    )
    try:
        return json.load(urllib.request.urlopen(req, timeout=15))
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return None
        raise


def reset_text(iso):
    at = datetime.fromisoformat(iso)
    s = int((at - datetime.now().astimezone()).total_seconds())
    left = f"{s//86400}d {s%86400//3600}h" if s >= 86400 else f"{s//3600}h {s%3600//60:02d}m"
    return left, at.astimezone().strftime("%m/%d %H:%M")


root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)
root.attributes("-alpha", 0.92)
root.configure(bg=BG)
root.geometry("+40+40")

header = tk.Frame(root, bg=BG)
header.grid(row=0, column=0, columnspan=2, sticky="ew")
donuts = {}
for col, (key, title) in enumerate([("five_hour", "5-hour session"), ("seven_day", "Weekly")]):
    c = tk.Canvas(root, width=SIZE + 16, height=SIZE + 58, bg=BG, highlightthickness=0)
    c.grid(row=1, column=col, padx=4, pady=(0, 8))
    box = (8 + W / 2, 8 + W / 2, 8 + SIZE - W / 2, 8 + SIZE - W / 2)
    c.create_oval(*box, outline=RING_BG, width=W)
    arc = c.create_arc(*box, start=90, extent=0, style="arc", outline=ACCENT, width=W)
    center = c.create_text(8 + SIZE / 2, 8 + SIZE / 2 - 6, fill="#f0eee6", font=("Consolas", 16, "bold"))
    sub = c.create_text(8 + SIZE / 2, 8 + SIZE / 2 + 14, fill="#9a9a95", font=("Malgun Gothic", 8))
    c.create_text(8 + SIZE / 2, SIZE + 22, text=title, fill="#f0eee6", font=("Malgun Gothic", 9, "bold"))
    when = c.create_text(8 + SIZE / 2, SIZE + 40, fill="#9a9a95", font=("Malgun Gothic", 8))
    donuts[key] = (c, arc, center, sub, when)


logged_in = False


def toggle_auth():
    if logged_in:
        subprocess.run(["claude", "auth", "logout"], creationflags=subprocess.CREATE_NO_WINDOW)
        refresh()
    else:
        subprocess.Popen(["claude", "auth", "login"], creationflags=subprocess.CREATE_NEW_CONSOLE)


auth_btn = tk.Button(header, command=toggle_auth, fg="white", relief="flat", bd=0, padx=8, font=("Segoe UI", 8, "bold"))
auth_btn.pack(side="left", padx=6, pady=4)


job = None


def refresh():
    global job, logged_in
    root.after_cancel(job) if job else None
    job = root.after(REFRESH_MS, refresh)
    try:
        usage = fetch_usage()
    except urllib.error.URLError:
        for c, arc, center, sub, when in donuts.values():
            c.itemconfig(when, text="Offline")
        return
    logged_in = usage is not None
    auth_btn.config(text="Log out" if logged_in else "Log in", bg="#3a3a38" if logged_in else ACCENT)
    if usage is None:
        for c, arc, center, sub, when in donuts.values():
            c.itemconfig(arc, extent=0)
            c.itemconfig(center, text="--")
            c.itemconfig(sub, text="")
            c.itemconfig(when, text="Sign in required")
    else:
        for key, (c, arc, center, sub, when) in donuts.items():
            pct = usage[key]["utilization"]
            left, at = reset_text(usage[key]["resets_at"])
            c.itemconfig(arc, extent=-min(pct / 100, 0.9999) * 360, outline="#c0392b" if pct >= 90 else ACCENT)
            c.itemconfig(center, text=f"{pct:.0f}%")
            c.itemconfig(sub, text=left)
            c.itemconfig(when, text=f"Resets {at}")


tk.Button(header, text="✕", command=root.destroy, bg=BG, fg="#9a9a95", activebackground="#c0392b", activeforeground="white", relief="flat", bd=0, font=("Segoe UI", 9)).pack(side="right", padx=4)
tk.Button(header, text="⟳", command=refresh, bg=BG, fg="#9a9a95", activebackground=ACCENT, activeforeground="white", relief="flat", bd=0, font=("Segoe UI", 10)).pack(side="right", padx=(0, 4))

drag = {}
root.bind("<ButtonPress-1>", lambda e: drag.update(x=e.x, y=e.y))
root.bind("<B1-Motion>", lambda e: root.geometry(f"+{root.winfo_x()+e.x-drag['x']}+{root.winfo_y()+e.y-drag['y']}"))

refresh()
root.mainloop()
