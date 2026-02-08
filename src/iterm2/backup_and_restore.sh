#!/usr/bin/env bash
set -euo pipefail

echo "Starting iTerm2 backup and restore script..."

ts="$(date +%Y%m%d-%H%M%S)"
backup_dir="${HOME}/Desktop/iterm2-backup-${ts}"

die() { echo "ERROR: $*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

echo "Backing up to: ${backup_dir}"
mkdir -p "${backup_dir}"

plist="${HOME}/Library/Preferences/com.googlecode.iterm2.plist"
app_support="${HOME}/Library/Application Support/iTerm2"
saved_state="${HOME}/Library/Saved Application State/com.googlecode.iterm2.savedState"

if [ -f "${plist}" ]; then
  echo "  - Backing up preferences plist"
  cp -p "${plist}" "${backup_dir}/"
fi
if [ -d "${app_support}" ]; then
  echo "  - Backing up Application Support"
  ditto "${app_support}" "${backup_dir}/iTerm2-AppSupport"
fi
if [ -d "${saved_state}" ]; then
  echo "  - Backing up Saved State"
  ditto "${saved_state}" "${backup_dir}/iTerm2-SavedState"
fi

echo "Closing iTerm2 if running..."
osascript -e 'tell application "iTerm2" to quit' >/dev/null 2>&1 || true
sleep 1

echo "Disabling custom prefs folder (prevents crash loop)..."
defaults delete com.googlecode.iterm2 PrefsCustomFolder >/dev/null 2>&1 || true
defaults write com.googlecode.iterm2 LoadPrefsFromCustomFolder -bool false >/dev/null 2>&1 || true

echo "Removing iTerm2 prefs + support state..."
rm -f "${plist}" || true
rm -rf "${app_support}" || true
rm -rf "${saved_state}" || true

if have brew; then
  echo "Reinstalling iTerm2 via Homebrew..."
  brew uninstall --cask --force iterm2 2>/dev/null || true
  brew install --cask iterm2 || echo "Warning: brew install failed, continuing..."
else
  echo "Homebrew not found; skipping reinstall."
fi

if [ -d "/Applications/iTerm.app" ]; then
  echo "Clearing quarantine flag (if present)..."
  xattr -dr com.apple.quarantine "/Applications/iTerm.app" >/dev/null 2>&1 || true
fi

if have brew; then
  echo "Installing a Nerd Font (MesloLGS NF) for agnoster/powerline..."
  brew install --cask font-meslo-lg-nerd-font 2>/dev/null || echo "  (Font already installed or skipped)"
fi

echo
echo "Done."
echo "Backup: ${backup_dir}"
echo
echo "Next:"
echo "  1) Launch iTerm2 once (fresh)."
echo "  2) Re-import only safe items (Profiles/Colors/Keys), avoid full plist auto-load."
