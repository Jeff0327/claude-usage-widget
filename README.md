# Claude Usage Widget

A tiny always-on-top Windows desktop widget that shows your Claude plan usage (5-hour session and weekly) as donut charts.

- Shows your account's real usage percentage and reset time (the same numbers as `/usage` in Claude Code).
- Auto-refreshes every 5 minutes; the ⟳ button syncs immediately (with a 60-second cooldown shown on the button), — minimizes to the taskbar, ✕ closes the widget, drag to move.
- Log in / log out from inside the widget (top-left button).
- Four languages (English, Russian, Korean, Chinese): click the language code (EN/RU/KO/ZH) in the header to cycle. The choice is saved to `~/.claude-usage-widget.json`.

## Requirements

- Windows
- [Claude Code](https://claude.com/claude-code) CLI with `claude` on your `PATH` (used for login/logout and token storage)
- Python 3.10+ (only to run from source; standard library only)

## Run

```
pythonw claude_usage_widget.pyw
```

## Build an exe

```
pip install pyinstaller
pyinstaller --onefile --windowed --name ClaudeUsageWidget --icon icon.ico --add-data "icon.ico;." claude_usage_widget.pyw
```

The result is `dist/ClaudeUsageWidget.exe`.

## Usage

1. On first launch the top-left button reads **Log in**. It opens a console running `claude auth login`. After signing in, press ⟳.
2. While logged in, the same button reads **Log out**.
3. The usage endpoint is rate limited. In testing, calls 3 minutes apart never failed, while calls 30 seconds apart returned HTTP 429. The widget therefore polls every 5 minutes, disables ⟳ for 60 seconds after each request, and on a 429 waits out the cooldown and shows "Rate limited".
4. If the numbers look stale after leaving it running for a long time, press ⟳. If the token has expired, the Log in button comes back.

## Notes

- **Unofficial project.** Not affiliated with Anthropic. It relies on an undocumented usage endpoint (`api.anthropic.com/api/oauth/usage`) that may change or stop working at any time.
- The widget reads the token Claude Code stores in `~/.claude/.credentials.json` and uses it only for that request. It does not store the token or send it anywhere else.
- **Logging out also logs out Claude Code itself**, because they share the same credentials.
- The icon is fan-made pixel art, not an official Anthropic asset. Claude is a trademark of Anthropic.

## License

[MIT](LICENSE)
