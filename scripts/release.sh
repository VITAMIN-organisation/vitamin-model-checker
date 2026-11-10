#!/usr/bin/env bash
# Release steps for vitamin-model-checker. Run them through the make targets.
# Usage: scripts/release.sh check | publish | publish-test | tag | push-tag
set -euo pipefail
cd "$(dirname "$0")/.."

PYTHON=${PYTHON:-python3}
UV=${UV:-uv}
VERSION=$("$PYTHON" -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")
TAG="v$VERSION"
# Written by `check` so that `publish` can tell dist/ was built from the commit it is on.
BUILT_FROM=build/.release-head

die() { echo "FAIL: $*" >&2; exit 1; }

require_clean_tree() {
  [ -z "$(git status --porcelain)" ] || die "git tree is not clean: commit or stash first"
}

require_tag_absent() {
  if git rev-parse -q --verify "refs/tags/$TAG" >/dev/null; then die "tag $TAG already exists"; fi
}

require_changelog() {
  grep -q "^## \[$VERSION\]" CHANGELOG.md || die "CHANGELOG.md has no '## [$VERSION]' section"
}

# dist/ must hold exactly this version, or an old build gets uploaded.
require_dist() {
  local sdist="dist/vitamin_model_checker-$VERSION.tar.gz"
  local wheel="dist/vitamin_model_checker-$VERSION-py3-none-any.whl"
  [ -f "$sdist" ] && [ -f "$wheel" ] || die "dist/ must hold $sdist and $wheel"
  [ "$(find dist -type f | wc -l)" -eq 2 ] || die "dist/ holds other files: $(ls dist | tr '\n' ' ')"
  [ "$(cat "$BUILT_FROM" 2>/dev/null)" = "$(git rev-parse HEAD)" ] \
    || die "dist/ was not built from HEAD $(git rev-parse --short HEAD): run make release-check"
}

confirm() {
  echo
  echo "$1"
  printf 'Type %s to continue: ' "$VERSION"
  read -r answer || die "no input, aborted"
  [ "$answer" = "$VERSION" ] || die "aborted"
}

cmd_check() {
  require_clean_tree
  require_changelog
  require_tag_absent
  make lint typecheck test
  rm -rf dist build
  make build
  mkdir -p build
  git rev-parse HEAD > "$BUILT_FROM"
  require_dist
  # shellcheck disable=SC2086  # UV may hold a command with arguments
  $UV tool run twine check --strict dist/*
  echo "release-check passed for $VERSION: nothing was uploaded or tagged"
}

# Arguments go to uv publish; for publish-test the second one is the upload URL.
cmd_publish() {
  local target=${2:-PyPI}
  require_clean_tree
  require_changelog
  require_dist
  confirm "Upload to $target: $(ls dist | tr '\n' ' ')"
  # shellcheck disable=SC2086
  $UV publish "$@" dist/*
}

cmd_tag() {
  require_clean_tree
  require_changelog
  require_tag_absent
  confirm "Create tag $TAG on branch $(git branch --show-current) at $(git log -1 --format='%h %s' | cut -c1-70)"
  git tag "$TAG"
  echo "created $TAG (local only): run make push-tag to push it"
}

cmd_push_tag() {
  git rev-parse -q --verify "refs/tags/$TAG" >/dev/null || die "tag $TAG does not exist: run make tag"
  confirm "Push $TAG ($(git log -1 --format='%h %s' "$TAG" | cut -c1-70)) to $(git remote get-url origin)"
  git push origin "$TAG"
}

case "${1:-}" in
  check) cmd_check ;;
  publish) cmd_publish ;;
  publish-test) cmd_publish --publish-url https://test.pypi.org/legacy/ ;;
  tag) cmd_tag ;;
  push-tag) cmd_push_tag ;;
  *) die "usage: $0 check | publish | publish-test | tag | push-tag" ;;
esac
