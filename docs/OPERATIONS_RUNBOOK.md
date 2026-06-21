# Runbook эксплуатации пайплайна

## Ежедневная проверка

1. Открыть GitHub Actions и проверить последние workflow runs.
2. Убедиться, что `main` pipeline не падает на build/test.
3. Проверить Security Gateway artifacts.
4. Проверить GitHub Security / Code scanning alerts.
5. Проверить DefectDojo product dashboard.

## Если pipeline упал на build-test

1. Открыть log job `build-test`.
2. Проверить `npm ci`, tests и lint.
3. Исправить functional regression до анализа security findings.

## Если pipeline упал на Security Gateway

1. Открыть `security-gate-summary.md`.
2. Разделить findings на true positive, false positive, accepted risk.
3. Critical/high findings назначить владельцу.
4. Создать исправляющий Pull Request.
5. Для false positive оформить waiver и обновить policy.

## Если DAST не запускается

1. Проверить `STAGING_URL`.
2. Проверить доступность VPS и порта 3000.
3. Проверить compose stack: `docker compose ps`.
4. Проверить logs приложения: `docker compose logs --tail=100 app`.
5. Повторить workflow.

## Если DefectDojo import не работает

1. Проверить `DEFECTDOJO_ENABLED=true`.
2. Проверить `DEFECTDOJO_URL` и `DEFECTDOJO_TOKEN`.
3. Убедиться, что scan type поддерживается DefectDojo.
4. Открыть response API в job logs.

## Команды на VPS

```bash
cd /opt/juice-shop
docker compose ps
docker compose logs --tail=100 app
docker compose pull
docker compose up -d --remove-orphans
```
