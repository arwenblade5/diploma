#!/usr/bin/env bash
set -euo pipefail

ARTIFACT_DIR="${1:-artifacts}"
: "${DEFECTDOJO_URL:?DEFECTDOJO_URL is required}"
: "${DEFECTDOJO_TOKEN:?DEFECTDOJO_TOKEN is required}"
: "${DEFECTDOJO_PRODUCT_NAME:?DEFECTDOJO_PRODUCT_NAME is required}"
: "${DEFECTDOJO_ENGAGEMENT_NAME:?DEFECTDOJO_ENGAGEMENT_NAME is required}"

upload_scan() {
  local file="$1"
  local scan_type="$2"
  if [[ ! -s "$file" ]]; then
    echo "Skip missing report: $file"
    return 0
  fi
  echo "Uploading $file as $scan_type"
  curl -fsS -X POST "${DEFECTDOJO_URL%/}/api/v2/reimport-scan/" \
    -H "Authorization: Token ${DEFECTDOJO_TOKEN}" \
    -F "scan_type=${scan_type}" \
    -F "file=@${file}" \
    -F "product_name=${DEFECTDOJO_PRODUCT_NAME}" \
    -F "engagement_name=${DEFECTDOJO_ENGAGEMENT_NAME}" \
    -F "auto_create_context=true" \
    -F "active=true" \
    -F "verified=false" \
    -F "close_old_findings=false" \
    -F "push_to_jira=false" >/tmp/dojo-upload-response.json
  cat /tmp/dojo-upload-response.json
  echo
}

upload_scan "${ARTIFACT_DIR}/semgrep.json" "Semgrep JSON Report"
upload_scan "${ARTIFACT_DIR}/trivy-image.json" "Trivy Scan"
upload_scan "${ARTIFACT_DIR}/trivy-fs.json" "Trivy Scan"
upload_scan "${ARTIFACT_DIR}/npm-audit.json" "NPM Audit Scan"
upload_scan "${ARTIFACT_DIR}/gitleaks.json" "Gitleaks Scan"
upload_scan "${ARTIFACT_DIR}/zap.json" "ZAP Scan"
