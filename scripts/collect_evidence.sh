#!/usr/bin/env bash
# Run on the LinuxONE VM from repo root: ./scripts/collect_evidence.sh
#
# Collects platform, model and API evidence for the IBM Z Datathon 2026 (SSF2026)
# into evidence/*.txt. It installs nothing, kills nothing and changes no config.
# IPv4 addresses, the hostname and the username are redacted from every file.
#
# If the app is running on port 8000, the script sends two sample payments to
# POST /assess. That adds two rows to the audit log, with payee names starting
# "Evidence check". Pass --no-requests to skip them.

set -euo pipefail

SEND_REQUESTS=1
if [ "${1:-}" = "--no-requests" ]; then
    SEND_REQUESTS=0
fi

if [ ! -f app.py ] || [ ! -d .git ]; then
    echo "Run this from the repo root: ./scripts/collect_evidence.sh" >&2
    exit 1
fi

OUT_DIR="evidence"
mkdir -p "$OUT_DIR"
STAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
HOST_NAME="$(hostname 2>/dev/null || echo unknown-host)"
USER_NAME="$(id -un 2>/dev/null || echo unknown-user)"
BASE_URL="http://127.0.0.1:8000"

PYTHON="python3"
if [ -x .venv/bin/python ]; then
    PYTHON=".venv/bin/python"
fi

redact() {
    sed -E \
        -e 's/([0-9]{1,3}\.){3}[0-9]{1,3}/[IP REDACTED]/g' \
        -e "s/${HOST_NAME}/[HOST REDACTED]/g" \
        -e "s/${USER_NAME}/[USER REDACTED]/g"
}

# run "label" command...  Prints the command and its output; never fails.
run() {
    local label="$1"
    shift
    echo "\$ $label"
    if "$@" 2>&1; then
        :
    else
        echo "not available"
    fi
    echo
}

# write NAME: reads a block of output on stdin, redacts it, saves it.
write() {
    local file="$OUT_DIR/$1"
    {
        echo "# Collected $STAMP (UTC) by scripts/collect_evidence.sh · SSF2026"
        echo
        cat
    } | redact > "$file"
}

# 01 Platform
{
    run "date -u" date -u
    run "uname -a" uname -a
    run "uname -m" uname -m
    run "cat /etc/os-release" cat /etc/os-release
    run "nproc" nproc
    run "lscpu" lscpu
    run "free -h" free -h
    run "df -h /" df -h /
} | write 01_platform.txt

# 02 IBM machine type: only these lines, never serial or sequence codes
{
    run "grep machine type lines from /proc/sysinfo" \
        grep -E "^(Type|Model|Manufacturer|Model Capacity)" /proc/sysinfo
} | write 02_sysinfo.txt

# 03 Python and libraries
{
    run "$PYTHON --version" "$PYTHON" --version
    echo "\$ pip list (filtered)"
    "$PYTHON" -m pip list 2>/dev/null \
        | grep -iE "^(scikit-learn|pandas|numpy|fastapi|uvicorn|joblib|jinja2|httpx) " \
        || echo "not available"
    echo
} | write 03_python.txt

# 04 Model results
{
    found=""
    for candidate in results.json models/results.json data/results.json artifacts/results.json; do
        if [ -f "$candidate" ]; then
            found="$candidate"
            break
        fi
    done
    if [ -n "$found" ]; then
        run "cat $found" cat "$found"
    else
        echo "results.json not found (run: python3 generate_and_train.py)"
    fi
} | write 04_results.txt

# 05 API: field names match the form in templates/index.html and app.py
{
    run "ss -tlnp | grep 8000" sh -c "ss -tlnp 2>/dev/null | grep ':8000'"
    if command -v curl >/dev/null 2>&1 \
        && curl -s -o /dev/null --max-time 5 "$BASE_URL/health"; then
        run "GET /health" curl -s --max-time 10 \
            -w "\nhttp_code=%{http_code} time_total=%{time_total}s\n" "$BASE_URL/health"

        if [ "$SEND_REQUESTS" = "1" ]; then
            echo "\$ POST /assess (legit sample)"
            curl -s --max-time 10 -o /tmp/evidence_legit.$$ \
                -w "http_code=%{http_code} time_total=%{time_total}s\n" \
                -X POST "$BASE_URL/assess" \
                -d payee="Evidence check (legit)" -d amount=75 -d usual_amount=80 \
                -d payee_age_hours=720 -d hour=14 -d typing_time_seconds=7 \
                || echo "not available"
            grep -oE "PAYMENT (APPROVED|PAUSED)" /tmp/evidence_legit.$$ | head -1 \
                || echo "outcome text not found"
            rm -f /tmp/evidence_legit.$$
            echo

            echo "\$ POST /assess (scam-like sample)"
            curl -s --max-time 10 -o /tmp/evidence_scam.$$ \
                -w "http_code=%{http_code} time_total=%{time_total}s\n" \
                -X POST "$BASE_URL/assess" \
                -d payee="Evidence check (scam-like)" -d amount=2400 -d usual_amount=650 \
                -d new_payee=on -d payee_age_hours=1 -d hour=1 -d device_change=on \
                -d typing_time_seconds=60 -d pasted_payee=on -d on_call=on \
                || echo "not available"
            grep -oE "PAYMENT (APPROVED|PAUSED)" /tmp/evidence_scam.$$ | head -1 \
                || echo "outcome text not found"
            rm -f /tmp/evidence_scam.$$
            echo
        else
            echo "POST /assess samples skipped (--no-requests)"
            echo
        fi

        echo "\$ GET /audit"
        curl -s --max-time 10 -o /tmp/evidence_audit.$$ \
            -w "http_code=%{http_code} time_total=%{time_total}s\n" "$BASE_URL/audit" \
            || echo "not available"
        echo "status words on page:"
        grep -oE "\b(approved|paused|confirmed|cancelled)\b" /tmp/evidence_audit.$$ \
            | sort | uniq -c || echo "none found"
        rm -f /tmp/evidence_audit.$$
        echo
    else
        echo "App not reachable on port 8000 (start it as in the README, then re-run)"
    fi
} | write 05_api.txt

# 06 Containers
{
    if command -v podman >/dev/null 2>&1; then
        run "podman ps" podman ps
    elif command -v docker >/dev/null 2>&1; then
        run "docker ps" docker ps
    else
        echo "No podman or docker found: no containers used."
    fi
} | write 06_containers.txt

# Each block above runs in a pipeline subshell, so build the summary from the files.
echo "Evidence collected at $STAMP (UTC). Files written:"
for f in 01_platform 02_sysinfo 03_python 04_results 05_api 06_containers; do
    [ -f "$OUT_DIR/$f.txt" ] && echo "  - $OUT_DIR/$f.txt"
done
echo
echo "Checks not available:"
if grep -lE "not available|not found|not reachable" "$OUT_DIR"/0[1-6]_*.txt 2>/dev/null; then
    echo "(see 'not available' lines in the files above)"
else
    echo "  none"
fi
echo
echo "Check each file before committing: make sure nothing private slipped through."
