# Security Gateway

## Назначение

Security Gateway - это policy-as-code слой, который принимает решение о возможности релиза на основании результатов всех security checks.

## Входные отчёты

| Инструмент | Файл | Формат |
|---|---|---|
| Semgrep | `semgrep.sarif`, `semgrep.json` | SARIF/JSON |
| npm audit | `npm-audit.json` | JSON |
| Trivy image | `trivy-image.json` | JSON |
| Trivy fs/misconfig | `trivy-fs.json` | JSON |
| Gitleaks | `gitleaks.json` | JSON |
| OWASP ZAP | `zap.json` | JSON |

## Пороговая политика

```text
Critical > 0 -> block
High > 0     -> block
Medium > 20  -> block
Low/Info     -> не блокируют
```

## Выходные артефакты

- `gateway/security-gate-result.json` - machine-readable decision.
- `gateway/security-gate-summary.md` - Markdown summary для PR comment.

## Рекомендации по исправлению

Gateway добавляет рекомендации по источнику finding:

- Semgrep: исправить vulnerable data flow и добавить regression test.
- Trivy image: обновить base image или OS package.
- npm audit: обновить npm package и package-lock.
- Gitleaks: ротировать secret и удалить его из истории при необходимости.
- ZAP: воспроизвести finding на staging и исправить HTTP/application control.

## Waiver процесс

Waiver должен содержать:

1. ID finding.
2. Обоснование false positive или accepted risk.
3. Владелец риска.
4. Дата пересмотра.
5. Ссылка на задачу исправления.

Для утечки секретов waiver невозможен без ротации секрета.
