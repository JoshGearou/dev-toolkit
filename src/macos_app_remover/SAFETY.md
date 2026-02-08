# Safety Features

This document describes the comprehensive safety features built into the macOS App Remover script.

## 🗑️ FILES MOVED TO TRASH, NOT PERMANENTLY DELETED

**Important**: This script moves files to your Trash (~/.Trash/) instead of permanently deleting them.

### What This Means

✅ **Recoverable**: You can restore files from Trash if you change your mind
✅ **Extra Safety Net**: One more layer of protection against accidental removal
✅ **Review Before Delete**: Check Trash to see exactly what was removed
✅ **Manual Control**: You decide when to permanently delete by emptying Trash

### After Removal

1. Files are in: `~/.Trash/` (with timestamp suffix to avoid conflicts)
2. View in Finder: Click "Trash" in the sidebar
3. Restore if needed: Drag files back from Trash to original location
4. Permanently delete: Empty Trash (Cmd+Shift+Delete in Finder)

### Fallback to Permanent Deletion

Only if moving to Trash fails (rare cases like cross-filesystem moves or permission issues), the script will:
1. Warn you it couldn't move to Trash
2. Attempt permanent deletion as last resort
3. Still prompt before doing so

---

## ☁️ CLOUD STORAGE PROTECTION

**Critical**: The script detects and warns before removing files from cloud-synced directories.

### Protected Locations

The script checks for files in these cloud storage locations:

- **iCloud Drive**: `~/Library/Mobile Documents/com~apple~CloudDocs`, `~/iCloud Drive`
- **Google Drive**: `~/Google Drive`, `~/GoogleDrive`
- **OneDrive**: `~/OneDrive`
- **Dropbox**: `~/Dropbox`
- **Box**: `~/Box`, `~/Box Sync`
- **Other Cloud Storage**: `~/Library/CloudStorage/*`

### What Happens

If a file is detected in cloud storage:

```
⚠️  CLOUD STORAGE WARNING ⚠️
Path: /Users/you/Box/MyFile.txt
This is in cloud storage (iCloud, Google Drive, OneDrive, Dropbox, Box, etc.)
Removing this could DELETE files from your cloud!

[WARNING] Are you ABSOLUTELY SURE you want to remove this cloud storage path?
Move to Trash (CLOUD STORAGE): /Users/you/Box/MyFile.txt? [y/N]:
```

**Recommendation**: Answer 'N' (No) to skip cloud storage files.

### Why This Matters

- Cloud storage folders sync to the cloud
- Moving to Trash may trigger cloud deletion
- Could affect files on other devices
- Could delete shared files

**Be Extremely Careful**: Only confirm if you're certain the file is safe to remove.

---

## Proper Removal Order

The script follows best practices for application removal:

1. **Unload Launch Agents/Daemons First**
   - Disables auto-start services
   - Prevents processes from restarting automatically
   - Uses `launchctl unload` and `launchctl remove`

2. **Terminate Running Processes**
   - Finds ALL related processes using three methods:
     - Name matching (finds "Box", "Box Helper", "Box Finder Extension")
     - Bundle ID matching
     - Recursive child process discovery
   - Now safe to kill - they won't restart
   - Tries graceful termination (SIGTERM) first
   - Prompts for force kill (SIGKILL) if needed

3. **Remove Application Files**
   - Main app bundle
   - Support files, caches, preferences
   - Containers and scripts

4. **Remove Launch Agent Files**
   - Deletes the configuration files
   - Already unloaded, so safe to remove

5. **Remove Package Receipts**
   - Cleans up installer metadata

This order ensures:
- No zombie processes
- No auto-restarts during removal
- Clean, complete removal

---

## Multi-Level Confirmation System

The script uses a "defense in depth" approach with multiple confirmation levels:

### 1. Initial Preview (Before Any Action)

When you run the script without `--dry-run`, you get a **complete preview** showing:

```
The following will be removed:

  [APP] /Applications/Box.app
  [SUPPORT] ~/Library/Application Support/Box
  [PREFS] ~/Library/Preferences/com.box.desktop.plist
  [CACHE] ~/Library/Caches/com.box.desktop
  [CONTAINER] ~/Library/Containers/com.box.desktop.boxfileprovider
  [SCRIPT] ~/Library/Application Scripts/com.box.desktop.findersyncext
  [LOGS] ~/Library/Logs/Box
  [LAUNCH AGENT] ~/Library/LaunchAgents/com.box.desktop.launch.plist
  [SYSTEM DAEMON - requires sudo] /Library/LaunchDaemons/com.box.desktop.autoupdater.plist
  [RECEIPTS] 4 package receipt(s) - will prompt individually

[WARNING] Total items to remove: 15
[WARNING] This action cannot be undone!

Do you want to proceed with removal? [y/N]:
```

**Action:** Say 'N' here to cancel everything before any removal starts.

---

### 2. Process Termination (Individual Prompts)

#### Comprehensive Process Detection

The script finds ALL related processes using three methods:

1. **Name Matching**: Searches for processes containing the app name
   - Example: "Box" finds "Box", "Box Helper", "Box Finder Extension", "BoxSync", etc.
   - Uses case-insensitive substring matching

2. **Bundle ID Matching**: Searches for processes containing the bundle identifier
   - Example: "com.box.desktop" finds all processes with that bundle ID
   - Catches background services and helpers

3. **Child Process Discovery**: Recursively finds all child processes
   - Walks the process tree to find spawned processes
   - Ensures no orphaned helper processes remain
   - Catches processes that might have different names

This comprehensive approach ensures that helper processes, extensions, background services, and any spawned child processes are all detected.

#### Termination Process

If the app is running, you'll see:

```
[WARNING] Found 5 running process(es):
  [PID 1234] Box
  [PID 1235] Box Helper
  [PID 1236] Box Finder Extension
  [PID 1237] com.box.desktop.helper
  [PID 1238] BoxSync

Terminate [PID 1234] Box? [y/N]:
```

**For each process:**
- Prompts individually before terminating
- Tries graceful termination (SIGTERM) first
- Waits up to 3 seconds for process to exit
- If process doesn't exit, prompts again for force kill (SIGKILL)
- You can skip any process you want to keep running

**Actions:**
- 'Y' = Terminate this process
- 'N' = Skip this process, leave it running

---

### 3. File/Directory Removal (Individual Prompts)

For **every single file and directory**, you get a prompt:

```
Move to Trash: /Applications/Box.app? [y/N]:
[SUCCESS] Moved to Trash: /Applications/Box.app

Move to Trash: ~/Library/Application Support/Box? [y/N]:
[SUCCESS] Moved to Trash: ~/Library/Application Support/Box

Move to Trash: ~/Library/Preferences/com.box.desktop.plist? [y/N]:
[SUCCESS] Moved to Trash: ~/Library/Preferences/com.box.desktop.plist
```

**For each file/directory:**
- Individual confirmation before moving to Trash
- Files moved to `~/.Trash/` (with timestamp to avoid conflicts)
- Tries move without sudo first
- If permission denied, **prompts again** to use sudo
- Immediate feedback on success/failure
- Files are **recoverable** from Trash
- Continue or skip any item

**Actions:**
- 'Y' = Move this item to Trash (recoverable)
- 'N' = Skip this item, keep it

---

### 3a. Sudo Elevation (Additional Prompt)

If a file requires elevated privileges (sudo), you get an **additional prompt**:

```
Remove: /Library/Application Support/Box? [y/N]: y
[WARNING] Failed to remove without sudo: /Library/Application Support/Box

[WARNING] This file requires elevated privileges (sudo) to remove.

Use sudo to remove: /Library/Application Support/Box? [y/N]:
```

**Actions:**
- 'Y' = Use sudo to remove (you'll be prompted for your password)
- 'N' = Cancel removal, script exits (fail-fast)

---

### 4. Package Receipts (Individual Prompts)

Package receipts also get individual confirmation:

```
[INFO] Checking package receipts...
  - com.box.desktop.installer.local.appsupport

Remove receipt: com.box.desktop.installer.local.appsupport? [y/N]:
```

---

## Safety Modes

### Dry-Run Mode (Safest)

```bash
./remove_app.sh --dry-run "AppName"
```

**Features:**
- Shows exactly what would be removed
- **No confirmations** (nothing is actually removed)
- No changes to your system
- Perfect for previewing before actual removal

**Use this first!**

---

### Normal Mode (Multiple Confirmations)

```bash
./remove_app.sh "AppName"
```

**Features:**
- Initial preview with total count
- One confirmation before starting
- Individual confirmation for each process
- Individual confirmation for each file/directory
- Individual confirmation for each package receipt

**This is the default mode** - maximum safety with granular control.

---

### Skip Confirmations Mode (Dangerous)

```bash
./remove_app.sh -y "AppName"
```

**Features:**
- Skips the initial preview confirmation
- **Still prompts for each individual item** (processes, files, receipts)
- Use only when you're certain

---

## What Gets Prompted

| Item Type | Confirmation Required? | Can Skip? |
|-----------|----------------------|-----------|
| Initial preview | Yes (unless `-y` flag) | Yes - cancels everything |
| Each process | Yes, individually | Yes - leaves process running |
| Force kill (if needed) | Yes, per process | Yes - leaves process running |
| Each file/directory | Yes, individually | Yes - keeps the file |
| Sudo escalation | Yes, per file needing sudo | No - script exits if declined |
| Each package receipt | Yes, individually | Yes - keeps the receipt |

---

## Example: Full Removal Session

Here's what a typical session looks like:

```bash
$ ./remove_app.sh "Box"

==========================================
  macOS Application Removal Tool
==========================================

Application: Box

[INFO] Attempting to detect bundle ID...
[SUCCESS] Detected bundle ID: com.box.desktop

[INFO] Scanning for files to remove...

The following will be removed:
  [APP] /Applications/Box.app
  [SUPPORT] ~/Library/Application Support/Box
  [PREFS] ~/Library/Preferences/com.box.desktop.plist
  ... (10 more items)

[WARNING] Total items to remove: 13
[WARNING] This action cannot be undone!

Do you want to proceed with removal? [y/N]: y    ← DECISION POINT 1

[INFO] Unloading launch agents to prevent auto-restart...
[INFO] Unloaded: com.box.desktop.launch
[SUCCESS] Unloaded 1 launch agent(s)/daemon(s)

[INFO] Checking for running processes...
[WARNING] Found 2 running process(es):
  [PID 1234] Box
  [PID 1235] Box Helper

Terminate [PID 1234] Box? [y/N]: y               ← DECISION POINT 2
[INFO] Terminating [PID 1234] Box...
[SUCCESS] Terminated [PID 1234] Box

Terminate [PID 1235] Box Helper? [y/N]: y        ← DECISION POINT 3
[INFO] Terminating [PID 1235] Box Helper...
[SUCCESS] Terminated [PID 1235] Box Helper

[INFO] Removing main application (1 location(s))...

Remove: /Applications/Box.app? [y/N]: y          ← DECISION POINT 4
[SUCCESS] Removed: /Applications/Box.app

[INFO] Removing support files (8 items)...

Remove: ~/Library/Application Support/Box? [y/N]: y     ← DECISION POINT 5
[SUCCESS] Removed: ~/Library/Application Support/Box

Remove: ~/Library/Preferences/com.box.desktop.plist? [y/N]: y
[SUCCESS] Removed: ~/Library/Preferences/com.box.desktop.plist

Remove: /Library/Application Support/Box? [y/N]: y      ← DECISION POINT 6
[WARNING] Failed to remove without sudo: /Library/Application Support/Box

[WARNING] This file requires elevated privileges (sudo) to remove.

Use sudo to remove: /Library/Application Support/Box? [y/N]: y  ← DECISION POINT 7
[INFO] Attempting removal with sudo...
Password:                                                 ← Enter sudo password
[SUCCESS] Removed with sudo: /Library/Application Support/Box

... (continues for each support file)

[INFO] Removing launch agent files (1 items)...

Remove: ~/Library/LaunchAgents/com.box.desktop.launch.plist? [y/N]: y
[SUCCESS] Removed: ~/Library/LaunchAgents/com.box.desktop.launch.plist

[SUCCESS] Removed 1 launch agent file(s)

... (continues with package receipts)
```

**Total Decision Points:** 1 initial + 2 processes + 13 files + potential sudo prompts

**Note:** Each file requiring sudo adds an extra confirmation prompt.

---

## Cancellation Points

You can safely cancel at any time by:

1. **Pressing Ctrl+C** - Stops the script immediately
2. **Answering 'N' to the initial prompt** - Nothing is removed
3. **Answering 'N' to any individual item** - That item is skipped, others continue

---

## What Happens on 'N' (Skip)

When you skip an item:

- **Processes:** Left running
- **Files/Directories:** Remain on disk
- **Package Receipts:** Remain in system
- **Other Items:** Script continues with remaining items

---

## Recovery

If you accidentally remove something:

1. **Applications:** Reinstall from original source
2. **Preferences:** Settings will be reset to defaults on reinstall
3. **Containers/Support Files:** Recreated by app on next launch
4. **Launch Agents:** Recreated by app installer

**Important:** Once removed, files cannot be recovered unless you have a backup (Time Machine, etc.)

---

## Best Practice Workflow

1. **First, dry-run:**
   ```bash
   ./remove_app.sh --dry-run "AppName"
   ```

2. **Review the output carefully**

3. **Then, actual removal:**
   ```bash
   ./remove_app.sh "AppName"
   ```

4. **Answer 'Y' to initial prompt** (after reviewing preview)

5. **For each item:**
   - Read the path carefully
   - Answer 'Y' if you want to remove it
   - Answer 'N' if you want to keep it

6. **Empty Trash** after completion

7. **Optionally restart** your Mac

---

## Flags to Control Safety

| Flag | Safety Level | Behavior |
|------|-------------|----------|
| `--dry-run` | **Highest** | Preview only, no changes |
| (none) | **High** | All confirmations enabled |
| `-y` | **Medium** | Skips initial prompt, still confirms each item |
| `-y` with `-n` | **Lowest** | Preview mode (same as `--dry-run`) |

---

## Emergency Stop

**Press Ctrl+C at any time** to immediately stop the script.

The script will exit and no further removals will occur. Items already removed cannot be recovered without a backup.
