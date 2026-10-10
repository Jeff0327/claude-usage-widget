import ctypes, json, os, subprocess, sys, time, tkinter as tk, urllib.error, urllib.request
from datetime import datetime

CREDS = os.path.expanduser("~/.claude/.credentials.json")
SETTINGS = os.path.expanduser("~/.claude-usage-widget.json")
TEXT = {
    "en": dict(limited="Rate limited", code="EN", five_hour="5-hour session", seven_day="Weekly", resets="Resets", offline="Offline", signin="Sign in required", login="Log in", logout="Log out"),
    "ru": dict(limited="Лимит запросов", code="RU", five_hour="Сессия 5 ч", seven_day="Неделя", resets="Сброс", offline="Нет сети", signin="Нужен вход", login="Войти", logout="Выйти"),
    "ko": dict(limited="요청 제한", code="KO", five_hour="5시간 세션", seven_day="주간", resets="리셋", offline="오프라인", signin="로그인 필요", login="로그인", logout="로그아웃"),
    "zh": dict(limited="请求受限", code="ZH", five_hour="5小时会话", seven_day="每周", resets="重置", offline="离线", signin="需要登录", login="登录", logout="退出登录"),
}
# Measured: calls 180s apart never hit 429 (5/5); 30s apart hit it on the 3rd call.
REFRESH_MS = 300_000
MIN_GAP = 60
BG, RING_BG, ACCENT = "#1f1f1e", "#3a3a38", "#d97757"
SIZE, W = 96, 12
lang = json.load(open(SETTINGS))["lang"] if os.path.exists(SETTINGS) else "en"


def fetch_usage():
    """Returns None when logged out or the token has expired."""
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
root.title("Claude Usage")
root.iconbitmap(os.path.join(getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__))), "icon.ico"))


def show_in_taskbar():
    # overrideredirect windows get no taskbar button; WS_EX_APPWINDOW forces one
    hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
    style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
    ctypes.windll.user32.SetWindowLongW(hwnd, -20, (style & ~0x80) | 0x40000)
    root.withdraw()
    root.after(10, root.deiconify)


def minimize():
    # iconify() is ignored while overrideredirect is on
    root.overrideredirect(False)
    root.iconify()


def restore_frameless():
    # overrideredirect(False) itself triggers a Map, so only act once the window is really back to normal
    if not root.overrideredirect() and root.state() == "normal":
        root.overrideredirect(True)
        root.after(10, show_in_taskbar)


def on_map(e):
    if e.widget is root:
        root.after(100, restore_frameless)


root.bind("<Map>", on_map)
root.after(100, show_in_taskbar)

header = tk.Frame(root, bg=BG)
header.grid(row=0, column=0, columnspan=2, sticky="ew")
donuts = {}
titles = {}
for col, key in enumerate(["five_hour", "seven_day"]):
    c = tk.Canvas(root, width=SIZE + 16, height=SIZE + 58, bg=BG, highlightthickness=0)
    c.grid(row=1, column=col, padx=4, pady=(0, 8))
    box = (8 + W / 2, 8 + W / 2, 8 + SIZE - W / 2, 8 + SIZE - W / 2)
    c.create_oval(*box, outline=RING_BG, width=W)
    arc = c.create_arc(*box, start=90, extent=0, style="arc", outline=ACCENT, width=W)
    center = c.create_text(8 + SIZE / 2, 8 + SIZE / 2 - 6, fill="#f0eee6", font=("Consolas", 16, "bold"))
    sub = c.create_text(8 + SIZE / 2, 8 + SIZE / 2 + 14, fill="#9a9a95", font=("Malgun Gothic", 8))
    titles[key] = (c, c.create_text(8 + SIZE / 2, SIZE + 22, fill="#f0eee6", font=("Malgun Gothic", 9, "bold")))
    when = c.create_text(8 + SIZE / 2, SIZE + 40, fill="#9a9a95", font=("Malgun Gothic", 8))
    donuts[key] = (c, arc, center, sub, when)


logged_in = False


def toggle_auth():
    if logged_in:
        global next_ok
        subprocess.run(["claude", "auth", "logout"], creationflags=subprocess.CREATE_NO_WINDOW)
        next_ok = 0
        refresh()
    else:
        subprocess.Popen(["claude", "auth", "login"], creationflags=subprocess.CREATE_NEW_CONSOLE)


auth_btn = tk.Button(header, command=toggle_auth, fg="white", relief="flat", bd=0, padx=8, font=("Segoe UI", 8, "bold"))
auth_btn.pack(side="left", padx=6, pady=4)


job = None
state = dict(usage=None, error=False)


def next_lang():
    global lang
    codes = list(TEXT)
    lang = codes[(codes.index(lang) + 1) % len(codes)]
    json.dump({"lang": lang}, open(SETTINGS, "w"))
    render()


next_ok = 0


def refresh():
    global job, next_ok
    if time.monotonic() < next_ok:
        return
    root.after_cancel(job) if job else None
    wait = MIN_GAP
    delay = REFRESH_MS
    try:
        state.update(usage=fetch_usage(), error=False)
    except urllib.error.URLError as e:
        state.update(error="limited" if isinstance(e, urllib.error.HTTPError) and e.code == 429 else True)
        if state["error"] == "limited":
            wait = max(int(e.headers["Retry-After"]), REFRESH_MS // 1000)
            delay = wait * 1000
    next_ok = time.monotonic() + wait
    job = root.after(delay, refresh)
    render()


def tick():
    left = int(next_ok - time.monotonic())
    sync_btn.config(text=f"⟳ {left}" if left > 0 else "⟳", state="disabled" if left > 0 else "normal")
    root.after(1000, tick)


def render():
    global logged_in
    usage = state["usage"]
    logged_in = usage is not None or (state["error"] and os.path.exists(CREDS))
    T = TEXT[lang]
    lang_btn.config(text=T["code"])
    auth_btn.config(text=T["logout" if logged_in else "login"], bg="#3a3a38" if logged_in else ACCENT)
    for key, (c, arc, center, sub, when) in donuts.items():
        titles[key][0].itemconfig(titles[key][1], text=T[key])
        if usage is None:
            c.itemconfig(arc, extent=0)
            c.itemconfig(center, text="--")
            c.itemconfig(sub, text="")
            c.itemconfig(when, text=(T["limited"] if state["error"] == "limited" else T["offline"]) if state["error"] else T["signin"])
            continue
        pct = usage[key]["utilization"]
        left, at = reset_text(usage[key]["resets_at"])
        c.itemconfig(arc, extent=-min(pct / 100, 0.9999) * 360, outline="#c0392b" if pct >= 90 else ACCENT)
        c.itemconfig(center, text=f"{pct:.0f}%")
        c.itemconfig(sub, text=left)
        c.itemconfig(when, text=(T["limited"] if state["error"] == "limited" else T["offline"]) if state["error"] else f"{T['resets']} {at}")


tk.Button(header, text="✕", command=root.destroy, bg=BG, fg="#9a9a95", activebackground="#c0392b", activeforeground="white", relief="flat", bd=0, font=("Segoe UI", 9)).pack(side="right", padx=4)
tk.Button(header, text="—", command=minimize, bg=BG, fg="#9a9a95", activebackground=ACCENT, activeforeground="white", relief="flat", bd=0, font=("Segoe UI", 9)).pack(side="right")
sync_btn = tk.Button(header, text="⟳", command=refresh, bg=BG, fg="#9a9a95", activebackground=ACCENT, activeforeground="white", relief="flat", bd=0, font=("Segoe UI", 10))
sync_btn.pack(side="right", padx=(0, 4))

lang_btn = tk.Button(header, command=next_lang, bg=BG, fg="#9a9a95", activebackground=ACCENT, activeforeground="white", relief="flat", bd=0, font=("Segoe UI", 8, "bold"))
lang_btn.pack(side="right")

drag = {}
root.bind("<ButtonPress-1>", lambda e: drag.update(x=e.x, y=e.y))
root.bind("<B1-Motion>", lambda e: root.geometry(f"+{root.winfo_x()+e.x-drag['x']}+{root.winfo_y()+e.y-drag['y']}"))

tick()
refresh()
root.mainloop()
