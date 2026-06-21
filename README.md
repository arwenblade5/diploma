# Дипломный проект DevSecOps: безопасный CI/CD пайплайн для OWASP Juice Shop

Пакет содержит готовую документацию и набор файлов для внедрения безопасного пайплайна в fork open-source проекта OWASP Juice Shop.

## Что входит

- `.github/workflows/devsecops.yml` - основной CI/CD pipeline: build, tests, SAST, SCA, secret scanning, image/config scan, staging deploy, DAST, Security Gateway, DefectDojo upload.
- `scripts/security_gate.py` - Security Gateway: агрегирует отчёты, формирует решение allow/block, пишет Markdown summary для Pull Request.
- `scripts/defectdojo_upload.sh` - загрузка результатов сканирования в DefectDojo через API.
- `config/` - политики Semgrep, Trivy, ZAP и Gitleaks.
- `deploy/docker-compose.vps.yml` - пример развёртывания приложения на VPS.

## Целевая архитектура

GitHub repository -> GitHub Actions -> GHCR -> VPS staging -> OWASP ZAP DAST -> Security Gateway -> release decision -> DefectDojo/GitHub Security.
