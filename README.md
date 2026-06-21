# Дипломный проект DevSecOps: безопасный CI/CD пайплайн для OWASP Juice Shop

Пакет содержит готовую документацию и набор файлов для внедрения безопасного пайплайна в fork open-source проекта OWASP Juice Shop.

## Что входит

- `.github/workflows/devsecops.yml` - основной CI/CD pipeline: build, tests, SAST, SCA, secret scanning, image/config scan, staging deploy, DAST, Security Gateway, DefectDojo upload.
- `scripts/security_gate.py` - Security Gateway: агрегирует отчёты, формирует решение allow/block, пишет Markdown summary для Pull Request.
- `scripts/defectdojo_upload.sh` - загрузка результатов сканирования в DefectDojo через API.
- `config/` - политики Semgrep, Trivy, ZAP и Gitleaks.
- `deploy/docker-compose.vps.yml` - пример развёртывания приложения на VPS.
- `docs/` - пояснительная документация для диплома.

## Целевая архитектура

GitHub repository -> GitHub Actions -> GHCR -> VPS staging -> OWASP ZAP DAST -> Security Gateway -> release decision -> DefectDojo/GitHub Security.

## Необходимые GitHub Secrets

- `VPS_HOST` - IP или DNS staging VPS.
- `VPS_USER` - пользователь SSH на VPS.
- `VPS_SSH_KEY` - приватный SSH key для деплоя.
- `GHCR_PULL_TOKEN` - token для docker login на VPS, если GHCR image приватный.
- `DEFECTDOJO_URL` - URL DefectDojo, например `https://dojo.example.ru`.
- `DEFECTDOJO_TOKEN` - API token DefectDojo.

## Необходимые GitHub Variables

- `STAGING_URL` - публичный URL staging, например `http://<VPS_IP>:3000`.
- `DEFECTDOJO_ENABLED` - `true` или `false`.
- `DEFECTDOJO_PRODUCT_NAME` - название продукта в DefectDojo.

## Как использовать

1. Сделать fork OWASP Juice Shop.
2. Скопировать файлы из этого пакета в корень fork.
3. Настроить Secrets и Variables в GitHub.
4. Подготовить VPS: Docker Engine + Docker Compose plugin, входящий порт 3000 или reverse proxy.
5. Выполнить push в `main` или запустить workflow вручную.
6. Проверить GitHub Actions artifacts, GitHub Security / Code scanning, PR comment от Security Gateway и импорт в DefectDojo.

## Важное замечание для демонстрации

OWASP Juice Shop является намеренно уязвимым приложением. Поэтому строгий Security Gateway с порогами `CRITICAL=0` и `HIGH=0` с высокой вероятностью остановит релиз. Это не ошибка, а демонстрация правильной работы защитного шлюза. Для демонстрации успешного production-release можно использовать patched fork, временный waiver policy или отдельную ветку с исправленными findings.
