#!/usr/bin/env bash
set -euo pipefail

if [[ $# != 1 ]]; then
  printf 'Usage: %s PATH_TO_SHIZUKU\n' "$0" >&2
  exit 1
fi

source_dir="$(realpath -- "$1")"
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
patch_root="$(realpath -- "$script_dir/../patches")"
api_dir="$source_dir/api"

# git -C api can resolve the parent repository when the submodule is missing.
api_root="$(git -C "$api_dir" rev-parse --show-toplevel)"
if [[ "$api_root" != "$api_dir" ]]; then
  printf 'api/ is not initialized; run git submodule update --init --recursive.\n' >&2
  exit 1
fi

apply_directory() {
  local target="$1" patch_dir="$2" label="$3" patch
  local -a patch_files
  shopt -s nullglob
  patch_files=("$patch_dir"/*.patch "$patch_dir"/*.diff)
  if (( ${#patch_files[@]} == 0 )); then
    printf 'No patches found in %s\n' "$patch_dir" >&2
    exit 1
  fi

  for patch in "${patch_files[@]}"; do
    if git -C "$target" apply --check "$patch" 2>/dev/null; then
      git -C "$target" apply "$patch"
      printf 'Applied (%s): %s\n' "$label" "${patch##*/}"
    elif git -C "$target" apply --reverse --check "$patch" 2>/dev/null; then
      printf 'Already present (%s): %s\n' "$label" "${patch##*/}"
    else
      git -C "$target" apply --3way "$patch"
      printf 'Applied with three-way merge (%s): %s\n' "$label" "${patch##*/}"
    fi
  done
  git -C "$target" diff --check
  git -C "$target" diff --cached --check
}

apply_directory "$source_dir" "$patch_root/main" "Shizuku"
apply_directory "$api_dir" "$patch_root/api" "api"
