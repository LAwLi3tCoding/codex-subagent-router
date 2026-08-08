#!/bin/sh
set -eu

REPOSITORY_URL="https://github.com/LAwLi3tCoding/codex-subagent-router.git"
SOURCE_ROOT=""
TEMP_ROOT=""

cleanup() {
    if [ -n "$TEMP_ROOT" ] && [ -d "$TEMP_ROOT" ]; then
        find "$TEMP_ROOT" -depth -delete
    fi
}
trap cleanup EXIT HUP INT TERM

case "$0" in
    */*)
        CANDIDATE_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
        if [ -f "$CANDIDATE_ROOT/scripts/install.py" ]; then
            SOURCE_ROOT=$CANDIDATE_ROOT
        fi
        ;;
esac

if [ -z "$SOURCE_ROOT" ]; then
    command -v git >/dev/null 2>&1 || {
        echo "git is required for remote installation" >&2
        exit 1
    }
    TEMP_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/codex-subagent-router.XXXXXX")
    git clone --depth 1 --quiet "$REPOSITORY_URL" "$TEMP_ROOT/repository"
    SOURCE_ROOT="$TEMP_ROOT/repository"
fi

command -v python3 >/dev/null 2>&1 || {
    echo "Python 3.11 or newer is required" >&2
    exit 1
}
python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' || {
    echo "Python 3.11 or newer is required" >&2
    exit 1
}

PYTHONDONTWRITEBYTECODE=1 python3 "$SOURCE_ROOT/scripts/install.py" "$@"
PYTHONDONTWRITEBYTECODE=1 python3 "$SOURCE_ROOT/scripts/verify.py" "$@"
