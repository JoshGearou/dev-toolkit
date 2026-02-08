# Git Submodule Manager

A simple, user-friendly script for managing git submodules with ease.

## Features

- **List** all submodules with detailed information
- **Add** new submodules with optional branch specification
- **Remove** submodules safely (preserves working directory as backup)
- **Update** submodules to latest commits
- **Status** view of all submodules
- **Initialize** submodules after cloning
- **Sync** submodule URLs from .gitmodules

## Installation

Make the script executable:

```bash
chmod +x ./git_submodules.sh
```

Optionally, create a symlink to use it from anywhere:

```bash
ln -s "$(pwd)/git_submodules.sh" ~/bin/git-submodules
```

## Usage

### List all submodules

```bash
./git_submodules.sh list
```

Shows all submodules with their paths, URLs, branches, and initialization status.

### Add a new submodule

```bash
# Add submodule tracking default branch
./git_submodules.sh add https://github.com/user/repo.git libs/mylib

# Add submodule tracking a specific branch
./git_submodules.sh add https://github.com/user/repo.git libs/mylib main
```

After adding, don't forget to commit:
```bash
git commit -m "Add submodule libs/mylib"
```

### Remove a submodule

```bash
./git_submodules.sh remove libs/mylib
```

This will:
1. Backup the working directory to `libs/mylib.backup`
2. Deinitialize the submodule
3. Remove it from git tracking
4. Clean up .git/modules directory

After removing, commit the changes:
```bash
git commit -m "Remove submodule libs/mylib"
```

### Update submodules

```bash
# Update all submodules
./git_submodules.sh update

# Update all submodules recursively
./git_submodules.sh update --recursive

# Update a specific submodule
./git_submodules.sh update libs/mylib
```

### Show submodule status

```bash
./git_submodules.sh status
```

Displays the commit hash and status of all submodules.

### Initialize submodules

```bash
# Initialize all submodules (after cloning a repository)
./git_submodules.sh init

# Initialize a specific submodule
./git_submodules.sh init libs/mylib
```

After initialization, run update to checkout the code:
```bash
git submodule update
```

### Sync submodule URLs

```bash
./git_submodules.sh sync
```

Synchronizes submodule URLs from .gitmodules to .git/config. Useful when submodule URLs have changed.

## Command Aliases

The script supports short aliases for convenience:

- `list` → `ls`
- `add` → `create`
- `remove` → `rm`, `delete`
- `update` → `up`
- `status` → `st`

## Examples

### Complete workflow for adding a submodule

```bash
# Add a submodule
./git_submodules.sh add https://github.com/org/shared-lib.git vendor/shared-lib main

# Verify it was added
./git_submodules.sh list

# Commit the change
git commit -m "feat: add shared-lib submodule"
git push
```

### Working with submodules after cloning

```bash
# Clone a repository with submodules
git clone https://github.com/user/myproject.git
cd myproject

# Initialize and update all submodules
./git_submodules.sh init
git submodule update --recursive
```

### Removing a submodule cleanly

```bash
# Remove the submodule
./git_submodules.sh remove vendor/old-lib

# Check the backup was created
ls vendor/old-lib.backup

# Commit the removal
git commit -m "refactor: remove old-lib submodule"
git push

# Optionally delete the backup
rm -rf vendor/old-lib.backup
```

## Safety Features

- **Confirmation prompts** for destructive operations
- **Backup creation** when removing submodules
- **Git repository validation** before operations
- **Existence checks** to prevent duplicate submodules
- **Color-coded output** for better readability

## Error Handling

The script uses `set -euo pipefail` for strict error handling:
- Exits on undefined variables
- Exits on command failures
- Properly propagates errors in pipelines

## Integration with Git

This script is a wrapper around standard git submodule commands, making them more user-friendly while maintaining full compatibility with git's submodule system.

## Troubleshooting

### Submodule not showing up after init

Run update to checkout the actual code:
```bash
git submodule update
```

### Submodule URL changed

Use sync to update the URLs:
```bash
./git_submodules.sh sync
git submodule update --remote
```

### Submodule is in detached HEAD state

This is normal for submodules. To work on a branch:
```bash
cd path/to/submodule
git checkout main
# Make changes, commit, push
cd ../..
git add path/to/submodule
git commit -m "Update submodule"
```

## Related Documentation

- [Git Submodules Official Documentation](https://git-scm.com/book/en/v2/Git-Tools-Submodules)
- [Pro Git Book - Submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules)

## License

This script follows the repository's license.
