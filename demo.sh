#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEMO_DIR="/private/tmp/offline-project-launch-assistant-demo"

echo "Ares Demo"
echo "Generated workspace path: ${DEMO_DIR}"
echo

rm -rf "${DEMO_DIR}"

python3 -B "${ROOT_DIR}/main.py" init "${DEMO_DIR}" "Build a customer support dashboard for support managers"

python3 -B "${ROOT_DIR}/main.py" add-decision "${DEMO_DIR}" "Version 1 will target support managers"
python3 -B "${ROOT_DIR}/main.py" add-risk "${DEMO_DIR}" "Zendesk API access may be delayed"
python3 -B "${ROOT_DIR}/main.py" add-task "${DEMO_DIR}" "Interview 3 support managers"
python3 -B "${ROOT_DIR}/main.py" answer-question "${DEMO_DIR}" 1 "The primary user is the support operations manager"

mkdir -p "${DEMO_DIR}/research" "${DEMO_DIR}/docs" "${DEMO_DIR}/reports" "${DEMO_DIR}/data"
cp "${ROOT_DIR}/examples/support-dashboard/research/customer-interviews.md" "${DEMO_DIR}/research/customer-interviews.md"
cp "${ROOT_DIR}/examples/support-dashboard/docs/support-process.md" "${DEMO_DIR}/docs/support-process.md"
cp "${ROOT_DIR}/examples/support-dashboard/reports/weekly-summary.md" "${DEMO_DIR}/reports/weekly-summary.md"
cp "${ROOT_DIR}/examples/support-dashboard/data/support_tickets.csv" "${DEMO_DIR}/data/support_tickets.csv"
printf "Support managers need a single daily view of high-priority open tickets.\n" > "${DEMO_DIR}/docs/local-note.txt"

echo
echo "== Project control plane =="
python3 -B "${ROOT_DIR}/main.py" state "${DEMO_DIR}"
python3 -B "${ROOT_DIR}/main.py" validate "${DEMO_DIR}"
python3 -B "${ROOT_DIR}/main.py" drift "${DEMO_DIR}"

echo
echo "== Ask root project docs =="
python3 -B "${ROOT_DIR}/main.py" ask "${DEMO_DIR}" "What is missing before kickoff?"

echo
echo "== Ask deep project knowledge =="
python3 -B "${ROOT_DIR}/main.py" ask-deep "${DEMO_DIR}" "What are customers complaining about?"

echo
echo "== Health check =="
python3 -B "${ROOT_DIR}/main.py" health "${DEMO_DIR}"

echo
echo "== Graph kickoff workflow =="
python3 -B "${ROOT_DIR}/main.py" kickoff-graph "${DEMO_DIR}"

echo
echo "== Data inspection =="
if python3 -c "import pandas, numpy" >/dev/null 2>&1; then
  python3 -B "${ROOT_DIR}/main.py" inspect-data "${DEMO_DIR}"
else
  python3 -B "${ROOT_DIR}/main.py" inspect-data "${DEMO_DIR}" || true
fi

echo
echo "== Local model status =="
python3 -B "${ROOT_DIR}/main.py" model-status

echo
echo "== Local chat fallback or response =="
python3 -B "${ROOT_DIR}/main.py" chat "${DEMO_DIR}" "What should we do before kickoff?"

echo
echo "== Multiagent PM review =="
python3 -B "${ROOT_DIR}/main.py" pm-review "${DEMO_DIR}" --fast

echo
echo "== Superagent request =="
python3 -B "${ROOT_DIR}/main.py" super "${DEMO_DIR}" "Prepare this project for kickoff" --fast

echo
echo "== Multimodal/text ingestion =="
python3 -B "${ROOT_DIR}/main.py" ingest "${DEMO_DIR}" "${DEMO_DIR}/docs/local-note.txt"

echo
echo "== Quality gate =="
python3 -B "${ROOT_DIR}/main.py" quality-gate "${DEMO_DIR}"

echo
echo "== Job ledger =="
python3 -B "${ROOT_DIR}/main.py" jobs "${DEMO_DIR}"
