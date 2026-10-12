#!/usr/bin/env bash
# Foundation's gates differ from the separate Resilient compiler repository.
set -euo pipefail
if [[ $# != 2 || $1 != --pr || ! $2 =~ ^[1-9][0-9]*$ ]]; then
  echo 'Usage: agent-scripts/ready-or-bail.sh --pr N' >&2
  exit 2
fi
PR="$2"
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
REPO="$(gh repo view --json nameWithOwner --jq .nameWithOwner)"
[[ "$REPO" == EricSpencer00/Resilient-Foundation ]]
[[ -z "$(git status --porcelain)" ]] || { echo 'Commit all changes before readiness.' >&2; exit 1; }
git fetch origin main
HEAD_SHA="$(git rev-parse HEAD)"
git merge-base --is-ancestor origin/main HEAD
read -r REMOTE_HEAD BASE STATE <<< "$(gh pr view "$PR" --json headRefOid,baseRefName,state --jq '[.headRefOid,.baseRefName,.state] | @tsv')"
[[ "$REMOTE_HEAD" == "$HEAD_SHA" && "$BASE" == main && "$STATE" == OPEN ]]
CHANGES="$(git diff --name-status origin/main...HEAD)"
[[ -n "$CHANGES" ]]
# Existing tests, dependency declarations and CI are protected in this run.
while IFS=$'\t' read -r STATUS FILE OTHER; do
  case "$FILE" in
    .github/workflows/*|Cargo.toml|Cargo.lock|*/Cargo.toml|requirements-dev.txt|examples/nonnegative/oracle.json|benchmarks/negative-manifests.json)
      echo "Protected file changed: $FILE" >&2; exit 1 ;;
    tests/*|scripts/test_*|*/tests/*)
      [[ "$STATUS" == A ]] || { echo "Existing test changed: $FILE" >&2; exit 1; } ;;
  esac
  [[ "$STATUS" != R* && "$STATUS" != D ]] || { echo 'Deletions/renames require separate review.' >&2; exit 1; }
done <<< "$CHANGES"
printf '%s\n' "$CHANGES" | grep -q $'^A\ttests/'
printf '%s\n' "$CHANGES" | grep -q $'\tfoundation/'
if git diff --unified=0 origin/main...HEAD -- '*.rs' | grep -E '^\+[^+].*\bunsafe\b'; then
  echo 'Unsafe changes require approval.' >&2; exit 1
fi
export CARGO_BUILD_JOBS=2
mkdir -p artifacts
GATE_DIR="$(mktemp -d "$ROOT/artifacts/readiness.XXXXXX")"
trap 'rm -rf -- "$GATE_DIR"' EXIT
make check
cargo build --workspace --locked
python3 scripts/run_e2e.py --report "$GATE_DIR/report.json" --evidence-dir "$GATE_DIR/evidence"
python3 scripts/replay_resilient.py
python3 scripts/validate_spec.py
[[ -z "$(git status --porcelain)" && "$(git rev-parse HEAD)" == "$HEAD_SHA" ]]
read -r REMOTE_HEAD BASE STATE <<< "$(gh pr view "$PR" --json headRefOid,baseRefName,state --jq '[.headRefOid,.baseRefName,.state] | @tsv')"
[[ "$REMOTE_HEAD" == "$HEAD_SHA" && "$BASE" == main && "$STATE" == OPEN ]]
git fetch origin main
git merge-base --is-ancestor origin/main HEAD
gh label create agent-vetted --color 0E8A16 --description 'Required local Foundation gates passed' --force
gh pr ready "$PR"
gh pr edit "$PR" --add-label agent-vetted
