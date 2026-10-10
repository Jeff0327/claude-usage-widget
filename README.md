# Claude Usage Widget

Windows 바탕화면에 Claude 사용량(5시간 세션 / 주간)을 도넛 그래프로 띄우는 작은 위젯입니다.
A tiny always-on-top Windows desktop widget showing your Claude plan usage (5-hour session / weekly) as donut charts.

- 계정의 실제 사용률(%)과 리셋 시각을 표시합니다 (Claude Code `/usage`와 같은 값).
- 60초마다 자동 갱신, ⟳ 버튼으로 즉시 동기화, ✕ 버튼으로 종료, 드래그로 이동.
- 위젯 안에서 로그인 / 로그아웃 가능.

## 요구 사항

- Windows
- [Claude Code](https://claude.com/claude-code) CLI (`claude` 명령이 PATH에 있어야 함) — 로그인/로그아웃과 토큰 저장에 사용
- Python 3.10+ (소스로 실행할 때만, 표준 라이브러리만 사용)

## 실행

```
pythonw claude_usage_widget.pyw
```

## exe 빌드

```
pip install pyinstaller
pyinstaller --onefile --windowed --name ClaudeUsageWidget --icon icon.ico claude_usage_widget.pyw
```

`dist/ClaudeUsageWidget.exe`가 생성됩니다.

## 사용법

1. 처음 실행하면 "Claude 로그인" 버튼이 보입니다. 누르면 콘솔 창에서 `claude auth login`이 실행됩니다. 로그인 후 ⟳를 누르세요.
2. 로그인된 상태에서는 같은 버튼이 "로그아웃"으로 바뀝니다.
3. 오래 켜 둬서 값이 안 맞으면 ⟳를 누르세요. 토큰이 만료되면 로그인 버튼이 다시 나타납니다.

## 주의

- **비공식 프로젝트**입니다. Anthropic과 무관하며, 문서화되지 않은 사용량 API(`api.anthropic.com/api/oauth/usage`)를 사용하므로 언제든 동작하지 않을 수 있습니다.
- 위젯은 Claude Code가 저장한 `~/.claude/.credentials.json`의 토큰을 읽어 위 API 호출에만 사용합니다. 토큰을 저장하거나 다른 곳으로 보내지 않습니다.
- **로그아웃은 Claude Code 자체의 로그인도 해제합니다.** 같은 자격 증명을 공유하기 때문입니다.
- 아이콘은 팬이 그린 픽셀 아트이며 Anthropic 공식 이미지가 아닙니다. Claude는 Anthropic의 상표입니다.

## License

[MIT](LICENSE)
