# Архитектура DevSecOps пайплайна

## Целевая схема

```text
GitHub Repository
  -> Pull Request / push
  -> GitHub Actions
  -> Build + tests
  -> SAST / SCA / Secrets / Container scan
  -> GHCR image
  -> VPS staging
  -> OWASP ZAP DAST
  -> Security Gateway
  -> GitHub Security + PR comment + DefectDojo
```

## Потоки данных

1. Исходный код хранится в fork OWASP Juice Shop.
2. GitHub Actions получает событие и запускает workflow.
3. SAST и checks формируют отчёты в SARIF/JSON.
4. Docker image публикуется в GHCR.
5. VPS получает image и запускает compose stack.
6. ZAP сканирует staging URL.
7. Security Gateway агрегирует findings и принимает решение.
8. Отчёты сохраняются в artifacts, GitHub Code Scanning и DefectDojo.

## Security boundaries

- GitHub Secrets не выводятся в logs.
- SSH ключ имеет доступ только к staging VPS.
- GHCR token используется только для pull image.
- Production release не выполняется при fail Security Gateway.
- DAST запускается только после staging deploy.

## Рекомендуемые branch protection rules

- запрет прямого push в `main`;
- required pull request review;
- required status checks: build-test, sast-codeql, sast-semgrep, secrets, sca-sbom, container-build-scan, security-gateway;
- require branches to be up to date before merge;
- dismiss stale approvals after new commits.
