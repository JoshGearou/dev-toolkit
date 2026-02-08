#!/bin/bash
#
# Unified Claude Code deployment script
#
# Deploys to ~/.claude/:
#   - Config: config/settings.json to ~/.claude/settings.json
#   - Rules: rules/*.md to ~/.claude/rules/ (local only, not push/pull)
#   - Agents: agents/**/*.md to ~/.claude/agents/ (flat structure)
#   - Scripts: agents/*/scripts/* to ~/.claude/scripts/
#   - Guides: agents/*/guides/* to ~/.claude/guides/ (PDFs and reference materials)
#   - Statusline: scripts/statusline-command.sh to ~/.claude/
#
# Import with --import:
#   - Copies ~/.claude/settings.json to config/settings.json
#   - Scrubs ~/.claude.json to config/claude.json (secrets removed)
#   - NOTE: config/claude.json is NEVER deployed back (backup only)
#
# Usage:
#   ./deploy.sh                              # Deploy all
#   ./deploy.sh --profile general            # Deploy only general profile
#   ./deploy.sh --dry-run                    # Preview changes
#   ./deploy.sh --import                     # Import from ~/.claude to repo
#   ./deploy.sh --push --target user@host    # Push to remote (excludes rules/)
#   ./deploy.sh --pull --target user@host    # Pull from remote (excludes rules/)

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENTS_DIR="${SCRIPT_DIR}/agents"
SCRIPTS_SRC_DIR="${SCRIPT_DIR}/scripts"
CLAUDE_DEST="${HOME}/.claude"
AGENTS_DEST="${HOME}/.claude/agents"
SCRIPTS_DEST="${HOME}/.claude/scripts"
RULES_DEST="${HOME}/.claude/rules"
GUIDES_DEST="${HOME}/.claude/guides"

# Options
DRY_RUN=false
USE_PREFIX=true
CLEAN=false
BACKUP=true
PROFILE=""
PROFILE_SET=false
CATEGORY=""
PULL=false
PUSH=false
IMPORT=false
TARGET_HOST=""
SYNC=false
SKIP_SELF_UPDATE=false

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

parse_profile_path() {
  local path="$1"
  if [[ "$path" == *"/"* ]]; then
    PROFILE="${path%%/*}"
    CATEGORY="${path#*/}"
  else
    PROFILE="$path"
    CATEGORY=""
  fi
}

get_profile_dirs() {
  find "${AGENTS_DIR}" -maxdepth 1 -type d ! -name ".*" ! -name "$(basename "${AGENTS_DIR}")" -exec basename {} \; 2>/dev/null | sort
}

is_valid_profile() {
  [[ -d "${AGENTS_DIR}/$1" ]]
}

# Extract references from YAML frontmatter for inlining
extract_frontmatter_references() {
  local agent_file="$1"
  if ! head -1 "$agent_file" | grep -q '^---$'; then
    return
  fi
  local frontmatter
  frontmatter=$(awk '/^---$/{p++; next} p==1{print} p==2{exit}' "$agent_file")
  echo "$frontmatter" | awk '
    /^references:/ {
      in_refs = 1
      if (match($0, /\[.*\]/)) {
        content = substr($0, RSTART+1, RLENGTH-2)
        gsub(/,/, "\n", content)
        gsub(/[[:space:]]*/, "", content)
        gsub(/"/, "", content)
        gsub(/'"'"'/, "", content)
        print content
        in_refs = 0
      }
      next
    }
    in_refs && /^[[:space:]]*-[[:space:]]*/ {
      sub(/^[[:space:]]*-[[:space:]]*/, "")
      gsub(/"/, "")
      gsub(/'"'"'/, "")
      gsub(/[[:space:]]*$/, "")
      print
      next
    }
    in_refs && /^[a-z]/ { in_refs = 0 }
  '
}

count_references() {
  local refs
  refs=$(extract_frontmatter_references "$1")
  if [[ -n "$refs" ]]; then
    echo "$refs" | grep -c .
  else
    echo 0
  fi
}

inline_references() {
  local agent_file="$1"
  local base_dir="$2"
  local refs
  refs=$(extract_frontmatter_references "$agent_file")

  if [[ -z "$refs" ]]; then
    cat "$agent_file"
    return
  fi

  local inline_content=""
  local has_inlined=false

  while IFS= read -r ref_path; do
    [[ -z "$ref_path" ]] && continue
    local relative_path="${ref_path#agents/}"
    local full_path="${base_dir}/${relative_path}"
    if [[ -f "$full_path" ]]; then
      has_inlined=true
      local filename
      filename=$(basename "$ref_path")
      inline_content+="
---

## Reference: ${filename}

$(cat "$full_path")
"
    else
      echo -e "${YELLOW}       [WARN]${NC} Referenced file not found: ${ref_path}" >&2
    fi
  done <<< "$refs"

  if [[ "$has_inlined" == "false" ]]; then
    cat "$agent_file"
    return
  fi

  # Output file without references field, then append inlined content
  local in_frontmatter=false
  local frontmatter_count=0
  local in_refs=false

  while IFS= read -r line || [[ -n "$line" ]]; do
    if [[ "$line" == "---" ]]; then
      ((frontmatter_count++))
      [[ $frontmatter_count -eq 1 ]] && in_frontmatter=true
      [[ $frontmatter_count -eq 2 ]] && in_frontmatter=false
      echo "$line"
      continue
    fi
    if [[ "$in_frontmatter" == true ]]; then
      if [[ "$line" =~ ^references: ]]; then
        in_refs=true
        continue
      fi
      if [[ "$in_refs" == true ]]; then
        if [[ "$line" =~ ^[[:space:]]*-[[:space:]] ]]; then
          continue
        fi
        if [[ "$line" =~ ^[a-z] ]]; then
          in_refs=false
        else
          continue
        fi
      fi
    fi
    echo "$line"
  done < "$agent_file"

  echo ""
  echo "---"
  echo ""
  echo "# Inlined Reference Materials"
  echo "$inline_content"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run) DRY_RUN=true; shift ;;
    --clean) CLEAN=true; shift ;;
    --no-backup) BACKUP=false; shift ;;
    --no-prefix) USE_PREFIX=false; shift ;;
    --profile)
      PROFILE_SET=true
      parse_profile_path "$2"
      if [[ "$PROFILE" != "all" ]] && ! is_valid_profile "$PROFILE"; then
        echo -e "${RED}Error: Profile '${PROFILE}' not found${NC}"
        exit 1
      fi
      shift 2
      ;;
    --pull) PULL=true; shift ;;
    --push) PUSH=true; shift ;;
    --import) IMPORT=true; shift ;;
    --sync) SYNC=true; shift ;;
    --skip-self-update) SKIP_SELF_UPDATE=true; shift ;;
    --target) TARGET_HOST="$2"; shift 2 ;;
    --help|-h)
      cat << 'EOF'
Usage: ./deploy.sh [OPTIONS]

Unified Claude Code deployment script.

Local deploy (default) - deploys ALL to ~/.claude/:
  - config/settings.json  -> ~/.claude/settings.json
  - agents/**/*.md        -> ~/.claude/agents/ (flattened)
  - agents/*/guides/*     -> ~/.claude/guides/ (PDFs, reference materials)
  - scripts/*             -> ~/.claude/ (statusline)
  - rules/*.md            -> ~/.claude/rules/

  NOTE: config/claude.json is NEVER deployed (scrubbed backup only)

Push/pull (--push, --pull) - syncs ONLY shareable files:
  - agents/general/       (shared agents)
  - scripts/              (statusline scripts)
  - deploy.sh             (this script)
  NOT synced: agents/work/, config/, rules/ (machine/user specific)

Options:
  --dry-run          Preview changes without copying
  --clean            Remove existing agents before deploying
  --no-backup        Skip creating backup
  --no-prefix        Don't add category prefix to agent names
  --profile PATH     Deploy specific profile (default: all for local)
  --import           Import configs from ~/.claude back to repo
  --push             Push shareable files to remote server
  --pull             Pull shareable files from remote server
  --target HOST      Remote host for push/pull (user@host)
  --sync             Remove extra files on destination
  --help, -h         Show this help

Examples:
  ./deploy.sh                              # Deploy all locally
  ./deploy.sh --dry-run                    # Preview deployment
  ./deploy.sh --import                     # Import from ~/.claude to repo
  ./deploy.sh --push --target user@host    # Push to remote
  ./deploy.sh --pull --target user@host    # Pull from remote
EOF
      exit 0
      ;;
    *) echo -e "${RED}Unknown option: $1${NC}"; exit 1 ;;
  esac
done

# Default profile
if [[ "${PROFILE_SET}" == "false" ]]; then
  if [[ "${PUSH}" == "true" ]] || [[ "${PULL}" == "true" ]]; then
    PROFILE="general"
  else
    PROFILE="all"
  fi
fi

# === IMPORT: Copy from ~/.claude to repo ===
if [[ "${IMPORT}" == "true" ]]; then
  echo -e "${BLUE}=== Import from ~/.claude to repo ===${NC}"
  echo ""
  IMPORTED=0

  # Import settings.json to config/
  if [[ -f "${CLAUDE_DEST}/settings.json" ]]; then
    mkdir -p "${SCRIPT_DIR}/config"
    if [[ "${DRY_RUN}" == "true" ]]; then
      echo -e "${YELLOW}[DRY RUN]${NC} Would import settings.json -> config/settings.json"
    else
      echo -e "${GREEN}[IMPORT]${NC} settings.json -> config/settings.json"
      cp "${CLAUDE_DEST}/settings.json" "${SCRIPT_DIR}/config/settings.json"
      ((IMPORTED++))
    fi
  fi

  if [[ -d "${RULES_DEST}" ]]; then
    mkdir -p "${SCRIPT_DIR}/rules"
    while IFS= read -r -d '' rule_file; do
      rule_name="$(basename "${rule_file}")"
      if [[ "${DRY_RUN}" == "true" ]]; then
        echo -e "${YELLOW}[DRY RUN]${NC} Would import rules/${rule_name}"
      else
        echo -e "${GREEN}[IMPORT]${NC} rules/${rule_name}"
        cp "${rule_file}" "${SCRIPT_DIR}/rules/${rule_name}"
        ((IMPORTED++))
      fi
    done < <(find "${RULES_DEST}" -name "*.md" -type f -print0)
  fi

  if [[ -f "${CLAUDE_DEST}/statusline-command.sh" ]]; then
    if [[ "${DRY_RUN}" == "true" ]]; then
      echo -e "${YELLOW}[DRY RUN]${NC} Would import statusline-command.sh"
    else
      echo -e "${GREEN}[IMPORT]${NC} statusline-command.sh"
      cp "${CLAUDE_DEST}/statusline-command.sh" "${SCRIPTS_SRC_DIR}/statusline-command.sh"
      ((IMPORTED++))
    fi
  fi

  # Import .claude.json (scrubbed) to config/
  if [[ -f "${HOME}/.claude.json" ]]; then
    if [[ "${DRY_RUN}" == "true" ]]; then
      echo -e "${YELLOW}[DRY RUN]${NC} Would import .claude.json -> config/claude.json (scrubbed)"
    else
      echo -e "${GREEN}[IMPORT]${NC} .claude.json -> config/claude.json (scrubbed)"
      if python3 "${SCRIPT_DIR}/scripts/scrub_claude_config.py" "${HOME}/.claude.json" "${SCRIPT_DIR}/config/claude.json" 2>/dev/null; then
        ((IMPORTED++))
      else
        echo -e "${YELLOW}       [WARN]${NC} Failed to scrub .claude.json, skipping"
      fi
    fi
  fi

  echo ""
  echo -e "${GREEN}Imported ${IMPORTED} file(s)${NC}"
  exit 0
fi

# === PULL: From remote to local repo ===
# Syncs ONLY: agents/general/, scripts/, deploy.sh
# NOT synced: agents/work/, config/, rules/ (machine/user specific)
if [[ "${PULL}" == "true" ]]; then
  echo -e "${BLUE}=== Pull from Remote ===${NC}"
  [[ -z "${TARGET_HOST}" ]] && read -p "Enter target host (user@host): " TARGET_HOST
  [[ -z "${TARGET_HOST}" ]] && { echo -e "${RED}Error: No target specified${NC}"; exit 1; }

  REMOTE_PATH="~/src/personal/claude-dotfiles/"
  echo "Remote: ${TARGET_HOST}:${REMOTE_PATH}"
  echo "Local:  ${SCRIPT_DIR}/"
  echo -e "${GREEN}Syncs: agents/general/, scripts/, deploy.sh${NC}"
  echo ""

  if [[ "${DRY_RUN}" == "false" ]]; then
    echo -e "${GREEN}Pulling...${NC}"
    scp -r "${TARGET_HOST}:${REMOTE_PATH}agents/general" "${SCRIPT_DIR}/agents/" 2>/dev/null || true
    scp -r "${TARGET_HOST}:${REMOTE_PATH}scripts/" "${SCRIPT_DIR}/" 2>/dev/null || true
    scp "${TARGET_HOST}:${REMOTE_PATH}deploy.sh" "${SCRIPT_DIR}/" 2>/dev/null || true
    echo -e "${GREEN}Done${NC}"
  else
    echo -e "${YELLOW}[DRY RUN] Would pull agents/general/, scripts/, deploy.sh${NC}"
  fi
  exit 0
fi

# === PUSH: From local repo to remote ===
# Syncs ONLY: agents/general/, scripts/, deploy.sh
# NOT synced: agents/work/, config/, rules/ (machine/user specific)
if [[ "${PUSH}" == "true" ]]; then
  echo -e "${BLUE}=== Push to Remote ===${NC}"
  [[ -z "${TARGET_HOST}" ]] && read -p "Enter target host (user@host): " TARGET_HOST
  [[ -z "${TARGET_HOST}" ]] && { echo -e "${RED}Error: No target specified${NC}"; exit 1; }

  REMOTE_PATH="~/src/personal/claude-dotfiles/"
  echo "Local:  ${SCRIPT_DIR}/"
  echo "Remote: ${TARGET_HOST}:${REMOTE_PATH}"
  echo -e "${GREEN}Syncs: agents/general/, scripts/, deploy.sh${NC}"
  echo ""

  if [[ "${DRY_RUN}" == "false" ]]; then
    echo -e "${GREEN}Pushing...${NC}"
    ssh "${TARGET_HOST}" "mkdir -p ${REMOTE_PATH}agents/general ${REMOTE_PATH}scripts" 2>/dev/null || {
      echo -e "${RED}Error: Could not create remote directory${NC}"; exit 1
    }
    scp -r "${SCRIPT_DIR}/agents/general" "${TARGET_HOST}:${REMOTE_PATH}agents/" 2>/dev/null || true
    scp -r "${SCRIPT_DIR}/scripts" "${TARGET_HOST}:${REMOTE_PATH}" 2>/dev/null || true
    scp "${SCRIPT_DIR}/deploy.sh" "${TARGET_HOST}:${REMOTE_PATH}" 2>/dev/null || true
    echo -e "${GREEN}Done${NC}"
  else
    echo -e "${YELLOW}[DRY RUN] Would push agents/general/, scripts/, deploy.sh${NC}"
  fi
  exit 0
fi

# === LOCAL DEPLOY ===
PROFILE_DISPLAY="${PROFILE}"
[[ -n "${CATEGORY}" ]] && PROFILE_DISPLAY="${PROFILE}/${CATEGORY}"

echo -e "${BLUE}=== Claude Code Deployment ===${NC}"
echo ""
echo "Source:      ${SCRIPT_DIR}"
echo "Dest:        ${CLAUDE_DEST}"
echo "Profile:     ${PROFILE_DISPLAY}"
echo ""

# Create directories
if [[ "${DRY_RUN}" == "false" ]]; then
  mkdir -p "${AGENTS_DEST}" "${SCRIPTS_DEST}" "${RULES_DEST}" "${GUIDES_DEST}"
fi

# Backup existing agents
BACKUP_DIR=""
if [[ "${BACKUP}" == "true" ]] && [[ -d "${AGENTS_DEST}" ]] && [[ "${DRY_RUN}" == "false" ]]; then
  if compgen -G "${AGENTS_DEST}/*.md" > /dev/null; then
    BACKUP_DIR="${HOME}/.claude/agents.backup.$(date +%Y%m%d_%H%M%S)"
    mkdir -p "${BACKUP_DIR}"
    cp "${AGENTS_DEST}"/*.md "${BACKUP_DIR}/" 2>/dev/null || true
    echo -e "${GREEN}Backup: ${BACKUP_DIR}${NC}"
    echo ""
  fi
fi

# Clean if requested
if [[ "${CLEAN}" == "true" ]]; then
  echo -e "${BLUE}=== Cleaning ===${NC}"
  if [[ "${DRY_RUN}" == "false" ]]; then
    rm -f "${AGENTS_DEST}"/*.md 2>/dev/null
    echo -e "${GREEN}Cleaned existing agents${NC}"
  else
    echo -e "${YELLOW}[DRY RUN] Would clean existing agents${NC}"
  fi
  echo ""
fi

# Deploy agents
echo -e "${BLUE}=== Deploying Agents ===${NC}"

FIND_PATHS=()
if [[ "$PROFILE" == "all" ]]; then
  while IFS= read -r profile_dir; do
    [[ -n "${CATEGORY}" ]] && [[ -d "${AGENTS_DIR}/${profile_dir}/${CATEGORY}" ]] && FIND_PATHS+=("${AGENTS_DIR}/${profile_dir}/${CATEGORY}")
    [[ -z "${CATEGORY}" ]] && FIND_PATHS+=("${AGENTS_DIR}/${profile_dir}")
  done < <(get_profile_dirs)
else
  [[ -n "${CATEGORY}" ]] && FIND_PATHS=("${AGENTS_DIR}/${PROFILE}/${CATEGORY}")
  [[ -z "${CATEGORY}" ]] && FIND_PATHS=("${AGENTS_DIR}/${PROFILE}")
fi

COPIED=0
SKIPPED=0

for FIND_PATH in "${FIND_PATHS[@]}"; do
  [[ ! -d "$FIND_PATH" ]] && continue
  while IFS= read -r -d '' agent_file; do
    rel_path="${agent_file#${AGENTS_DIR}/}"
    filename="$(basename "${agent_file}")"

    # Skip docs and guides
    [[ "${filename}" == "README.md" ]] && { ((SKIPPED++)); continue; }
    [[ "${rel_path}" == *"/guides/"* ]] && { ((SKIPPED++)); continue; }

    # Determine dest filename
    category_path="$(dirname "${rel_path}")"
    if [[ "${USE_PREFIX}" == "true" ]] && [[ "${category_path}" != "." ]]; then
      dest_filename="${category_path//\//-}-${filename}"
    else
      dest_filename="${filename}"
    fi
    dest_path="${AGENTS_DEST}/${dest_filename}"

    # Check if update needed
    has_refs=$(count_references "${agent_file}")
    if [[ -f "${dest_path}" ]] && [[ "${has_refs}" -eq 0 ]]; then
      if diff -q "${agent_file}" "${dest_path}" > /dev/null 2>&1; then
        echo -e "${GREEN}[OK]${NC}   ${rel_path}"
        ((SKIPPED++))
        continue
      fi
    fi

    echo -e "${YELLOW}[COPY]${NC} ${rel_path} -> ${dest_filename}"
    if [[ "${DRY_RUN}" == "false" ]]; then
      if [[ "${has_refs}" -gt 0 ]]; then
        inline_references "${agent_file}" "${AGENTS_DIR}" > "${dest_path}"
      else
        cp "${agent_file}" "${dest_path}"
      fi
      ((COPIED++))
    fi
  done < <(find "${FIND_PATH}" -not -path "*/.venv/*" -not -path "*/__pycache__/*" -name "*.md" -type f -print0)
done

# Sync external dependencies from src/scm-checker/ to claude-dotfiles scripts dir
echo ""
echo -e "${BLUE}=== Syncing External Dependencies ===${NC}"

SCM_CHECKER_SRC="${SCRIPT_DIR}/../src/scm-checker"
SCM_CHECKER_DST="${SCRIPT_DIR}/agents/general/code/scripts"

if [[ -d "${SCM_CHECKER_SRC}" ]]; then
    SYNC_COUNT=0
    for src_file in "${SCM_CHECKER_SRC}"/*.py "${SCM_CHECKER_SRC}"/*.sh; do
        [[ ! -f "${src_file}" ]] && continue
        filename="$(basename "${src_file}")"
        [[ "${filename}" == "copy_reports.sh" ]] && continue
        dst_file="${SCM_CHECKER_DST}/${filename}"
        if [[ -f "${dst_file}" ]] && diff -q "${src_file}" "${dst_file}" > /dev/null 2>&1; then
            echo -e "${GREEN}[OK]${NC}   ${filename}"
        else
            echo -e "${YELLOW}[SYNC]${NC} ${filename}"
            if [[ "${DRY_RUN}" == "false" ]]; then
                cp "${src_file}" "${dst_file}"
            fi
            ((SYNC_COUNT++))
        fi
    done
    [[ ${SYNC_COUNT} -eq 0 ]] || echo -e "${GREEN}Synced ${SYNC_COUNT} file(s) from src/scm-checker/${NC}"
else
    echo -e "${YELLOW}[WARN]${NC} src/scm-checker/ not found at ${SCM_CHECKER_SRC}, skipping"
fi

# Deploy agent scripts
echo ""
echo -e "${BLUE}=== Deploying Agent Scripts ===${NC}"
SCRIPTS_COPIED=0
for FIND_PATH in "${FIND_PATHS[@]}"; do
  [[ ! -d "$FIND_PATH" ]] && continue
  while IFS= read -r -d '' script_file; do
    filename="$(basename "${script_file}")"
    dest_path="${SCRIPTS_DEST}/${filename}"
    if [[ -f "${dest_path}" ]] && diff -q "${script_file}" "${dest_path}" > /dev/null 2>&1; then
      echo -e "${GREEN}[OK]${NC}   ${filename}"
    else
      echo -e "${YELLOW}[COPY]${NC} ${filename}"
      if [[ "${DRY_RUN}" == "false" ]]; then
        cp "${script_file}" "${dest_path}"
        chmod +x "${dest_path}"
        ((SCRIPTS_COPIED++))
      fi
    fi
  done < <(find "${FIND_PATH}" -not -path "*/.venv/*" -not -path "*/__pycache__/*" -not -name "test_*" -path "*/scripts/*" -type f \( -name "*.py" -o -name "*.sh" \) -print0 2>/dev/null)
done

# Deploy statusline
echo ""
echo -e "${BLUE}=== Deploying Statusline ===${NC}"
STATUSLINE_SRC="${SCRIPTS_SRC_DIR}/statusline-command.sh"
STATUSLINE_DST="${CLAUDE_DEST}/statusline-command.sh"
if [[ -f "${STATUSLINE_SRC}" ]]; then
  if [[ -f "${STATUSLINE_DST}" ]] && diff -q "${STATUSLINE_SRC}" "${STATUSLINE_DST}" > /dev/null 2>&1; then
    echo -e "${GREEN}[OK]${NC}   statusline-command.sh"
  else
    echo -e "${YELLOW}[COPY]${NC} statusline-command.sh"
    [[ "${DRY_RUN}" == "false" ]] && cp "${STATUSLINE_SRC}" "${STATUSLINE_DST}" && chmod +x "${STATUSLINE_DST}"
  fi
fi

# Deploy config
# IMPORTANT: Only deploys settings.json, NEVER claude.json
# config/claude.json is a scrubbed backup for version control only
echo ""
echo -e "${BLUE}=== Deploying Config ===${NC}"
CONFIG_SRC="${SCRIPT_DIR}/config/settings.json"
CONFIG_DST="${CLAUDE_DEST}/settings.json"
if [[ -f "${CONFIG_SRC}" ]]; then
  if [[ -f "${CONFIG_DST}" ]] && diff -q "${CONFIG_SRC}" "${CONFIG_DST}" > /dev/null 2>&1; then
    echo -e "${GREEN}[OK]${NC}   config/settings.json"
  else
    echo -e "${YELLOW}[COPY]${NC} config/settings.json -> settings.json"
    [[ "${DRY_RUN}" == "false" ]] && cp "${CONFIG_SRC}" "${CONFIG_DST}"
  fi
fi

# Safety check: Warn if config/claude.json would be deployed (it shouldn't)
if [[ -f "${SCRIPT_DIR}/config/claude.json" ]]; then
  echo -e "${GREEN}[SKIP]${NC} config/claude.json (scrubbed backup only, not deployed)"
fi

# Deploy rules (local only)
echo ""
echo -e "${BLUE}=== Deploying Rules ===${NC}"
if [[ -d "${SCRIPT_DIR}/rules" ]]; then
  while IFS= read -r -d '' rule_file; do
    rule_name="$(basename "${rule_file}")"
    dst="${RULES_DEST}/${rule_name}"
    if [[ -f "${dst}" ]] && diff -q "${rule_file}" "${dst}" > /dev/null 2>&1; then
      echo -e "${GREEN}[OK]${NC}   rules/${rule_name}"
    else
      echo -e "${YELLOW}[COPY]${NC} rules/${rule_name}"
      [[ "${DRY_RUN}" == "false" ]] && cp "${rule_file}" "${dst}"
    fi
  done < <(find "${SCRIPT_DIR}/rules" -not -path "*/.venv/*" -not -path "*/__pycache__/*" -name "*.md" -type f -print0)
fi

# Deploy guides (PDFs and other reference materials)
echo ""
echo -e "${BLUE}=== Deploying Guides ===${NC}"
GUIDES_COPIED=0
for FIND_PATH in "${FIND_PATHS[@]}"; do
  [[ ! -d "$FIND_PATH" ]] && continue
  guides_dir="${FIND_PATH}/guides"
  [[ ! -d "$guides_dir" ]] && continue

  # Extract profile and category from path
  rel_path="${FIND_PATH#${AGENTS_DIR}/}"
  profile_name="${rel_path%%/*}"
  category_name="${rel_path#*/}"
  [[ "$category_name" == "$profile_name" ]] && category_name=""

  # Destination directory
  if [[ -n "$category_name" ]]; then
    guides_dest_dir="${GUIDES_DEST}/${profile_name}/${category_name}"
  else
    guides_dest_dir="${GUIDES_DEST}/${profile_name}"
  fi

  # Copy guide files
  while IFS= read -r -d '' guide_file; do
    filename="$(basename "${guide_file}")"
    [[ "$filename" == "README.md" ]] && continue

    dest_file="${guides_dest_dir}/${filename}"
    if [[ "${DRY_RUN}" == "false" ]]; then
      mkdir -p "${guides_dest_dir}"
    fi

    if [[ -f "${dest_file}" ]] && diff -q "${guide_file}" "${dest_file}" > /dev/null 2>&1; then
      echo -e "${GREEN}[OK]${NC}   ${rel_path}/guides/${filename}"
    else
      echo -e "${YELLOW}[COPY]${NC} ${rel_path}/guides/${filename} -> guides/${profile_name}${category_name:+/}${category_name}/${filename}"
      if [[ "${DRY_RUN}" == "false" ]]; then
        cp "${guide_file}" "${dest_file}"
        ((GUIDES_COPIED++))
      fi
    fi
  done < <(find "${guides_dir}" -not -path "*/.venv/*" -not -path "*/__pycache__/*" -type f \( -name "*.pdf" -o -name "*.md" \) -print0 2>/dev/null)
done

# Summary
echo ""
echo -e "${BLUE}=== Summary ===${NC}"
[[ "${DRY_RUN}" == "true" ]] && echo -e "${YELLOW}DRY RUN - no files copied${NC}"
echo "Agents: ${COPIED} copied, ${SKIPPED} skipped"
[[ -n "${BACKUP_DIR}" ]] && echo "Backup: ${BACKUP_DIR}"
