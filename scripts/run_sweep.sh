#!/usr/bin/env bash
# Run the Curie-temperature sweep for one or more input folders.
# Usage: bash scripts/run_sweep.sh inputs/Fe_bcc [inputs/Co_fcc ...]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VAMPIRE="${VAMPIRE:-$(command -v vampire-serial || echo "$HOME/vampire/vampire-serial")}"
[ -x "$VAMPIRE" ] || { echo "vampire-serial not found; run scripts/build_vampire.sh first"; exit 1; }

for case_dir in "$@"; do
    name="$(basename "$case_dir")"
    out="$ROOT/results/$name"
    mkdir -p "$out"
    cp "$ROOT/$case_dir"/* "$out"/
    echo "[$(date +%T)] running $name in $out"
    start=$SECONDS
    ( cd "$out" && "$VAMPIRE" > vampire.log 2>&1 )
    echo "[$(date +%T)] finished $name ($(grep -vc '^#' "$out/output") temperatures, $((SECONDS - start)) s)"
done
