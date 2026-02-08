# macOS Application Remover

Comprehensive tool for thoroughly removing macOS applications and all associated files.

## Features

- **Complete Removal**: Removes app bundles, support files, caches, preferences, logs, and more
- **Safe Operation**: Dry-run mode to preview changes before removal
- **Interactive**: Confirmation prompts for critical operations
- **Bundle ID Detection**: Automatically detects app bundle IDs for thorough cleanup
- **Smart Launch Agent Handling**: Unloads launch agents BEFORE killing processes to prevent auto-restart
- **Package Receipt Removal**: Cleans up installer receipts
- **Remaining File Search**: Scans for any leftover files after removal
- **Proper Removal Order**: Follows best practices to prevent zombie processes and auto-restarts

## Usage

```bash
cd src/macos_app_remover
./remove_app.sh [OPTIONS] APP_NAME
```

### Options

- `-n, --dry-run`: Show what would be removed without actually removing files
- `-v, --verbose`: Show detailed output during removal
- `-y, --yes`: Skip confirmation prompts (use with caution)
- `-b, --bundle-id ID`: Specify bundle ID manually (e.g., `com.company.app`)
- `-h, --help`: Show help message

## Examples

### Preview removal (recommended first step)

```bash
./remove_app.sh --dry-run "Slack"
```

### Remove application with confirmation prompts

```bash
./remove_app.sh "Docker"
```

### Remove with specific bundle ID

```bash
./remove_app.sh -b com.docker.docker "Docker"
```

### Remove without prompts (automated)

```bash
./remove_app.sh -y "Zoom"
```

### Verbose removal with detailed output

```bash
./remove_app.sh -v "Visual Studio Code"
```

## Removal Process Order

The script follows a specific order to ensure clean removal and prevent auto-restarts:

1. **Unload Launch Agents/Daemons** - Disables auto-start services first
2. **Terminate Running Processes** - Kills all related processes (they won't restart)
   - Finds processes by app name (e.g., "Box", "Box Helper", "Box Finder Extension")
   - Finds processes by bundle ID
   - Recursively finds all child processes
   - Ensures complete process tree is terminated
3. **Remove Main Application** - Deletes the .app bundle
4. **Remove Support Files** - Cleans up caches, preferences, containers, logs
5. **Remove Launch Agent Files** - Deletes the launch agent/daemon configuration files
6. **Remove Package Receipts** - Cleans up installer metadata
7. **Search for Remaining Files** - Reports any leftover files

### Process Detection

The script uses three methods to find ALL related processes:

1. **Name matching**: Finds processes with the app name (e.g., "Box" finds "Box", "Box Helper", "Box Finder Extension")
2. **Bundle ID matching**: Finds processes using the bundle identifier
3. **Child process discovery**: Recursively finds all child processes spawned by the main app

This ensures helper processes, extensions, and background services are all found and terminated.

### Why This Order Matters

This order prevents:
- Processes from auto-restarting after being killed
- Launch agents from re-launching the app
- Zombie processes or orphaned helper processes
- Partial or incomplete removals

## What Gets Removed

The script searches for and removes files in the following locations:

### 1. Main Application
- `/Applications/AppName.app`
- `~/Applications/AppName.app`

### 2. Support Files
- `~/Library/Application Support/AppName`
- `/Library/Application Support/AppName`
- `~/Library/Preferences/com.company.appname.*`
- `~/Library/Caches/com.company.appname`
- `~/Library/Saved Application State/com.company.appname.savedState`

### 3. Containers (Sandboxed Apps)
- `~/Library/Containers/com.company.appname`
- `~/Library/Group Containers/com.company.appname.*`

### 4. Logs
- `~/Library/Logs/AppName`
- `/Library/Logs/AppName`

### 5. Launch Agents/Daemons
- `~/Library/LaunchAgents/com.company.appname.*`
- `/Library/LaunchAgents/com.company.appname.*` (requires sudo)
- `/Library/LaunchDaemons/com.company.appname.*` (requires sudo)

### 6. Package Receipts
- Package installer receipts via `pkgutil`

## Workflow

### Recommended Safe Workflow

1. **Preview the removal** (dry-run):
   ```bash
   ./remove_app.sh --dry-run "AppName"
   ```

2. **Review the output** to see what will be removed

3. **Perform the actual removal**:
   ```bash
   ./remove_app.sh "AppName"
   ```

4. **Review remaining files** and manually remove if necessary

5. **Empty Trash** and optionally restart your Mac

### Finding Bundle IDs

If the script can't auto-detect the bundle ID, you can find it manually:

```bash
# For installed app
defaults read /Applications/AppName.app/Contents/Info.plist CFBundleIdentifier

# Or search for bundle IDs
find /Applications -name "*.app" -exec defaults read {}/Contents/Info.plist CFBundleIdentifier \; 2>/dev/null
```

## Safety Features

### Multi-Level Confirmations

1. **Initial Preview**: Shows complete list of items to remove before starting
2. **Process Termination**: Individual prompts for each running process
3. **File Removal**: Individual prompts for each file/directory before removal
4. **Package Receipts**: Individual prompts for each package receipt

### Automatic Safety Checks

- **Dry-run mode**: Preview all changes without making any
- **Trash Instead of Delete**: Files are moved to Trash (~/.Trash/), not permanently deleted
- **Recoverable**: You can restore files from Trash if needed
- **Verified Removal**: Checks that each move/removal succeeded before continuing
- **Auto-Escalation**: Tries without sudo first, automatically retries with sudo if needed
- **Fail-Fast**: Exits immediately if any removal fails (prevents partial removal)
- **Graceful Process Termination**: Tries SIGTERM first, prompts for SIGKILL if needed
- **Skippable Items**: Say 'N' to any item to skip it and continue with others
- **Permanent Delete Fallback**: Only if Trash move fails (e.g., cross-filesystem)
- **Cloud Storage Protection**: Detects and warns before removing files from iCloud, Google Drive, OneDrive, Dropbox, Box, etc.

See [SAFETY.md](SAFETY.md) for detailed safety documentation.

## Common Applications

### Examples with detected bundle IDs

| Application | Bundle ID |
|------------|-----------|
| Docker | `com.docker.docker` |
| Slack | `com.tinyspeck.slackmacgap` |
| Visual Studio Code | `com.microsoft.VSCode` |
| Chrome | `com.google.Chrome` |
| Firefox | `org.mozilla.firefox` |
| Zoom | `us.zoom.xos` |

## Troubleshooting

### "Permission denied" errors

Some system-level files require sudo:
```bash
sudo ./remove_app.sh "AppName"
```

### App won't quit

Force quit manually:
```bash
pkill -9 -x "AppName"
```

### Bundle ID not detected

Specify manually:
```bash
./remove_app.sh -b com.company.app "AppName"
```

### Files remain after removal

The script will list remaining files. Review and remove manually if safe:
```bash
# Search for remaining files
find ~/Library -iname "*appname*" 2>/dev/null
```

## Advanced Usage

### Batch removal script

```bash
#!/bin/bash
APPS=("Slack" "Zoom" "Docker")

for app in "${APPS[@]}"; do
    ./remove_app.sh -y "$app"
done
```

### Find all installed apps

```bash
# List all applications
ls -1 /Applications/*.app | sed 's|/Applications/||;s|.app||'

# With bundle IDs
for app in /Applications/*.app; do
    name=$(basename "$app" .app)
    bundle=$(defaults read "$app/Contents/Info.plist" CFBundleIdentifier 2>/dev/null)
    echo "$name - $bundle"
done
```

## Notes

- Always use dry-run mode first to preview changes
- Some system applications are protected and cannot be removed
- Backup important data before removing applications
- Some apps may have additional files in non-standard locations
- System daemons may require sudo to remove
- Empty Trash after removal to free up disk space

## Integration with Repository

This tool follows the repository's bash scripting patterns:
- Sources `bash/common/repo_lib.sh` for shared utilities
- Uses `set -u` for undefined variable checking
- Includes comprehensive error handling
- Provides detailed logging and output

## Related Tools

- `pkgutil`: macOS package utility for receipts
- `launchctl`: Launch agent/daemon management
- `defaults`: Preference file management
- `find`: File system search
