# Матрица покрытия тестами безопасности

| Область | Проверка | Инструмент | Pipeline job | Выгрузка результата |
|---|---|---|---|---|
| JS/TS source | Semantic SAST | CodeQL | `sast-codeql` | GitHub Code Scanning |
| JS/TS source | Pattern SAST | Semgrep | `sast-semgrep` | SARIF, JSON, artifacts, DefectDojo |
| npm dependencies | SCA | npm audit | `sca-sbom` | JSON, artifacts, Gateway, DefectDojo |
| npm dependencies | SBOM | CycloneDX | `sca-sbom` | `bom.cdx.json` artifact |
| Git history | Secrets | Gitleaks | `secrets` | JSON, artifacts, Gateway, DefectDojo |
| Docker image | CVE scan | Trivy | `container-build-scan` | JSON, SARIF, Gateway, DefectDojo |
| Dockerfile/config | Misconfig | Trivy fs | `container-build-scan` | JSON, Gateway, DefectDojo |
| Runtime HTTP | DAST | OWASP ZAP | `dast-zap` | JSON, HTML, MD, Gateway, DefectDojo |
| Release decision | Policy | custom Python Gateway | `security-gateway` | JSON, MD, PR comment |
