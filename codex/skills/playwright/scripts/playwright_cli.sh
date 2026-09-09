#!/usr/bin/env bash
set -euo pipefail

if ! command -v npx >/dev/null 2>&1; then
  echo "Error: npx is required but not found on PATH." >&2
  exit 1
fi

has_session_flag="false"
for arg in "$@"; do
  case "$arg" in
    -s|-s=*|--session|--session=*)
      has_session_flag="true"
      break
      ;;
  esac
done

# A separate profile does not separate the macOS Chrome application identity.
# Validate launch overrides before npx can create a persistent CLI daemon.
launch_browser="$(python3 - "$@" <<'PYGUARD'
import argparse
import json
import os
from pathlib import Path
import sys

parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
parser.add_argument("--browser", action="append")
for flag in ("config", "profile", "executable-path", "cdp", "endpoint"):
    parser.add_argument("--" + flag)
parser.add_argument("-s", "--session")
parser.add_argument("--extension", action="store_true")
options, rest = parser.parse_known_args()
command = next((arg for arg in rest if not arg.startswith("-")), None)
if command != "open":
    sys.exit(0)


def reject(message):
    print("Blocked test browser launch: " + message, file=sys.stderr)
    sys.exit(2)


def browser_choice(value, *, cli=False):
    allowed = (None, "", "chromium", "firefox", "webkit") + (() if cli else ("chrome-for-testing",))
    if value not in allowed:
        reject("use managed chromium, firefox or webkit; connect to daily Chrome with an explicitly authorized attach instead")
    return "chromium" if value == "chrome-for-testing" else value


def check_profile(value):
    if value:
        daily = Path.home() / "Library/Application Support/Google/Chrome"
        if Path(value).expanduser().resolve().is_relative_to(daily.resolve()):
            reject("the daily Chrome profile cannot be used for testing")


# The CLI parses repeated --browser flags as an array and falls back to Chrome.
if options.browser is not None:
    if len(options.browser) != 1 or not options.browser[0]:
        reject("--browser must have one nonempty value")
    options.browser = options.browser[0]

if options.extension or options.cdp or options.endpoint:
    reject("use an explicitly authorized attach for an existing browser")

chosen = "chromium"
global_config = Path(os.environ.get("PWTEST_CLI_GLOBAL_CONFIG", str(Path.home()))) / ".playwright/cli.config.json"
default_config = Path.cwd() / ".playwright/cli.config.json"
local_config = options.config or (str(default_config) if default_config.exists() else os.environ.get("PLAYWRIGHT_MCP_CONFIG"))
configs = ([global_config] if global_config.exists() else []) + ([Path(local_config)] if local_config else [])
for path in configs:
    try:
        config = json.loads(path.read_text(encoding="utf-8-sig"))
        browser = config.get("browser") or {}
        launch = browser.get("launchOptions") or {}
        if launch.get("executablePath"):
            reject("remove the executablePath override; the wrapper uses Playwright-managed browsers")
        if config.get("extension") or browser.get("cdpEndpoint") or browser.get("remoteEndpoint"):
            reject("use an explicitly authorized attach for an existing browser")
        chosen = browser_choice(browser.get("browserName")) or chosen
        chosen = browser_choice(launch.get("channel")) or chosen
        check_profile(browser.get("userDataDir"))
    except (OSError, ValueError, AttributeError, TypeError):
        reject("the selected configuration must be a readable JSON object")
if options.executable_path or os.environ.get("PLAYWRIGHT_MCP_EXECUTABLE_PATH"):
    reject("remove the executable path override; the wrapper uses Playwright-managed browsers")
if os.environ.get("PLAYWRIGHT_MCP_CDP_ENDPOINT") or os.environ.get("PLAYWRIGHT_MCP_EXTENSION", "").lower() in ("1", "true"):
    reject("use an explicitly authorized attach for an existing browser")
chosen = browser_choice(os.environ.get("PLAYWRIGHT_MCP_BROWSER")) or chosen
chosen = browser_choice(options.browser, cli=True) or chosen
check_profile(options.profile or os.environ.get("PLAYWRIGHT_MCP_USER_DATA_DIR"))
# An explicit CLI choice already has higher precedence than environment/config.
if not options.browser:
    print(chosen)
PYGUARD
)"

cmd=(npx --yes --package @playwright/cli playwright-cli)
if [[ "${has_session_flag}" != "true" && -n "${PLAYWRIGHT_CLI_SESSION:-}" ]]; then
  cmd+=(--session "${PLAYWRIGHT_CLI_SESSION}")
fi
cmd+=("$@")
if [[ -n "${launch_browser}" ]]; then
  cmd+=(--browser "${launch_browser}")
fi

exec "${cmd[@]}"
