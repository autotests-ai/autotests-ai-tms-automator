#!/usr/bin/env bash
# 3-run TestOps launch: fast → fast retry → diagnostic.
# ADR 004, config/fast-testops.properties.
#
# Requires: warm-pool orchestrator (selenoid-home), allurectl, Gradle daemon on agent.
#
#   export TEST_CLASS='tests.LoginTests.successfulAuthorizationTest'
#   export WARM_POOL_URL=http://127.0.0.1:9090
#   export PREOPEN_URL='https://qa-guru.github.io/one-page-form/login.html'
#   ./scripts/testops-fast-launch.example.sh

set -euo pipefail

TEST_CLASS="${TEST_CLASS:?Set TEST_CLASS, e.g. tests.LoginTests.successfulAuthorizationTest}"
WARM_POOL_URL="${WARM_POOL_URL:-http://127.0.0.1:9090}"
PREOPEN_URL="${PREOPEN_URL:-}"
OWNER="${BUILD_TAG:-local-$(date +%s)}"
GRADLE="${GRADLE:-./gradlew}"

FAST_ARGS=(
  -Denv=fast-testops
  -DskipHealthCheck=true
)

DIAG_ARGS=(
  -Denv=ci
)

upload_allure() {
  if [[ -z "${ALLURE_PROJECT_ID:-}" ]]; then
    echo "ALLURE_PROJECT_ID unset — skip allurectl upload"
    return 0
  fi
  allurectl upload build/allure-results
}

release_slot() {
  if [[ -z "${WARM_SLOT_ID:-}" ]]; then
    return 0
  fi
  curl -sf -X POST "${WARM_POOL_URL}/pool/release" \
    -H 'Content-Type: application/json' \
    -d "{\"slotId\":\"${WARM_SLOT_ID}\"}" || true
  unset WARM_SLOT_ID
}

reserve_and_preopen() {
  release_slot
  if [[ -z "${PREOPEN_URL}" ]]; then
    echo "PREOPEN_URL empty — skip warm pool"
    return 0
  fi
  local reserve_json
  reserve_json="$(curl -sf -X POST "${WARM_POOL_URL}/pool/reserve" \
    -H 'Content-Type: application/json' \
    -d "{\"protocol\":\"webdriver\",\"browser\":\"chrome\",\"owner\":\"${OWNER}\"}")"
  WARM_SLOT_ID="$(printf '%s' "${reserve_json}" | python -c "import sys,json; print(json.load(sys.stdin)['slot']['id'])")"
  local webdriver_url
  webdriver_url="$(printf '%s' "${reserve_json}" | python -c "import sys,json; print(json.load(sys.stdin)['slot'].get('webdriverUrl') or '')")"
  curl -sf -X POST "${WARM_POOL_URL}/pool/preopen" \
    -H 'Content-Type: application/json' \
    -d "{\"slotId\":\"${WARM_SLOT_ID}\",\"url\":\"${PREOPEN_URL}\"}"
  if [[ -n "${webdriver_url}" ]]; then
    FAST_ARGS+=("-DremoteUrl=${webdriver_url}")
  fi
  export WARM_SLOT_ID
}

run_fast() {
  reserve_and_preopen
  "${GRADLE}" test --tests "${TEST_CLASS}" "${FAST_ARGS[@]}"
}

run_diag() {
  release_slot
  "${GRADLE}" test --tests "${TEST_CLASS}" "${DIAG_ARGS[@]}"
}

trap release_slot EXIT

if run_fast; then
  upload_allure
  echo "Run 1 (fast): PASSED"
  exit 0
fi

echo "Run 1 (fast): FAILED — retry with same keys"
if run_fast; then
  upload_allure
  echo "Run 2 (fast retry): PASSED (possible flake)"
  exit 0
fi

echo "Run 2 (fast retry): FAILED — diagnostic run"
run_diag
upload_allure
echo "Run 3 (diagnostic): finished (check Allure for attachments)"
exit 1
