# Приложение: аналитика выбора инструментов

## GitHub Actions

Плюсы: интеграция с GitHub PR, environments, GitHub Security, GHCR и SARIF upload. Минусы: зависимость от GitHub-hosted runners и внешних actions. Митигируется pinning actions и branch protection.

## CodeQL

Плюсы: data-flow анализ, поддержка JavaScript/TypeScript, загрузка в GitHub Security. Минусы: может быть медленнее простых pattern scanners. Используется для deep SAST.

## Semgrep

Плюсы: быстрый анализ, кастомные правила, понятный YAML, удобно для policy-as-code. Минусы: pattern-based анализ может давать false positives. Используется как быстрый SAST и custom policy.

## OWASP ZAP

Плюсы: open-source DAST, удобный baseline scan для CI/CD, отчёты в JSON/HTML/Markdown. Минусы: baseline scan без авторизации не покрывает все бизнес-сценарии. Зона роста - authenticated scan.

## Gitleaks

Плюсы: быстрый secret scanning, проверка истории git, удобная интеграция в CI. Минусы: требует настройки allowlist для документационных placeholder.

## Trivy

Плюсы: единый инструмент для image, filesystem, secret и misconfig checks. Минусы: для некоторых CVE нужны suppressions/ignore policies после triage.

## npm audit

Плюсы: нативный инструмент npm ecosystem. Минусы: часть findings требует ручного анализа совместимости обновлений.

## CycloneDX

Плюсы: SBOM format для dependency transparency и дальнейшей интеграции с Dependency-Track/DefectDojo. Минусы: SBOM сам по себе не исправляет уязвимости, нужен процесс обработки.

## DefectDojo

Плюсы: open-source vulnerability management, API import, дедупликация, lifecycle findings. Минусы: требуется отдельное сопровождение инстанса и настройка product/engagement model.
