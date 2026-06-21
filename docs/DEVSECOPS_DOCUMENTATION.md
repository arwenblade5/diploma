# Дипломная документация: безопасный CI/CD пайплайн для open-source проекта

## 1. Название и цель работы

**Тема:** проектирование и внедрение безопасного DevSecOps пайплайна для open-source веб-приложения.

**Цель:** построить CI/CD процесс, в котором безопасность встроена в жизненный цикл поставки ПО: код проверяется статическими анализаторами, зависимости и контейнерные образы анализируются на уязвимости, staging окружение проверяется динамическим анализатором, результаты выгружаются в GitHub Security и DefectDojo, а релиз блокируется Security Gateway при превышении заданных порогов риска.

## 2. Выбор проекта

В качестве целевого open-source проекта выбран **OWASP Juice Shop**.

Причины выбора:

1. Это веб-приложение с реальным фронтендом и backend API.
2. Стек проекта соответствует требованиям диплома: Node.js, Express, Angular, JavaScript/TypeScript, npm dependencies, Docker container.
3. Проект хорошо подходит для демонстрации SAST, SCA, container scanning и DAST.
4. Приложение намеренно содержит уязвимости, поэтому можно наглядно показать работу Security Gateway: релиз блокируется при наличии критичных или высоких рисков.
5. Проект можно быстро развернуть на VPS как контейнеризированный сервис.

Ограничение выбора: Juice Shop является учебно-уязвимым приложением, поэтому строгий security gate в норме будет блокировать production release. В рамках диплома это является преимуществом, потому что демонстрирует fail-closed модель релизного контроля. Для демонстрации успешного релиза используется staging deployment, а production gate остаётся блокирующим до исправления или формального waiver.

## 3. Выбор CI/CD платформы

Выбрана платформа **GitHub Actions**.

Обоснование:

- GitHub Actions нативно интегрируется с GitHub repository, pull request, environments и GitHub Security.
- Можно публиковать контейнерные образы в GitHub Container Registry.
- Поддерживается загрузка SARIF-отчётов в GitHub Code Scanning.
- Можно реализовать deployment на VPS через SSH.
- Инструменты CodeQL, Semgrep, Trivy, Gitleaks, CycloneDX, npm audit и ZAP хорошо автоматизируются в workflow.

## 4. Целевая архитектура

```text
Developer commit / Pull Request
        |
        v
GitHub Actions pipeline
        |
        +--> Build + unit tests
        +--> SAST: CodeQL + Semgrep
        +--> SCA/SBOM: npm audit + CycloneDX
        +--> Secret scanning: Gitleaks
        +--> Container/IaC scan: Trivy
        |
        v
Build container image
        |
        v
Push to GHCR
        |
        v
Deploy to staging VPS
        |
        v
DAST: OWASP ZAP baseline scan
        |
        v
Security Gateway
        |
        +--> GitHub PR comment
        +--> GitHub Actions artifacts
        +--> GitHub Code Scanning / Security tab
        +--> DefectDojo import
        |
        v
Release allowed or blocked
```

## 5. Этап 1 - CI/CD

### 5.1. Цель этапа

Настроить автоматическую сборку, проверку и доставку приложения на staging VPS.

### 5.2. Реализация

CI/CD pipeline расположен в файле:

```text
.github/workflows/devsecops.yml
```

Основные job:

- `build-test` - установка зависимостей, запуск тестов и lint.
- `container-build-scan` - сборка Docker image, публикация в GHCR, сканирование image и filesystem.
- `deploy-staging` - deployment на VPS через SSH и Docker Compose.
- `dast-zap` - динамическое тестирование staging URL.
- `security-gateway` - итоговая агрегация security findings и решение allow/block.
- `defectdojo-upload` - загрузка отчётов в DefectDojo.

### 5.3. Cloud/hosting контур

В качестве облачного сервиса используется связка:

- GitHub Actions как CI/CD runner;
- GitHub Container Registry как registry артефактов;
- VPS как staging окружение;
- DefectDojo как система менеджмента уязвимостей.

### 5.4. Требования к VPS

Минимальные требования:

- Ubuntu 22.04/24.04 LTS;
- Docker Engine;
- Docker Compose plugin;
- открытый порт `3000/tcp` или reverse proxy Nginx/Caddy;
- SSH доступ по ключу;
- отдельный пользователь без root login, добавленный в группу docker.

Базовая подготовка VPS:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
mkdir -p /opt/juice-shop
```

### 5.5. GitHub Secrets и Variables

Secrets:

| Secret | Назначение |
|---|---|
| `VPS_HOST` | IP или DNS VPS |
| `VPS_USER` | SSH пользователь |
| `VPS_SSH_KEY` | приватный SSH ключ для деплоя |
| `GHCR_PULL_TOKEN` | token для pull из GHCR, если image приватный |
| `DEFECTDOJO_URL` | URL DefectDojo |
| `DEFECTDOJO_TOKEN` | API token DefectDojo |

Variables:

| Variable | Назначение |
|---|---|
| `STAGING_URL` | URL приложения на staging |
| `DEFECTDOJO_ENABLED` | включение загрузки в DefectDojo |
| `DEFECTDOJO_PRODUCT_NAME` | имя продукта в DefectDojo |

## 6. Этап 2 - SAST

### 6.1. Цель этапа

Покрыть исходный код проверками на уязвимости, не пропуская языки и фреймворки проекта.

### 6.2. Матрица покрытия

| Компонент проекта | Технология | Инструменты |
|---|---|---|
| Backend | Node.js, Express, JavaScript/TypeScript | CodeQL, Semgrep |
| Frontend | Angular, TypeScript | CodeQL, Semgrep |
| Dependencies | npm package-lock | npm audit, CycloneDX SBOM, Trivy fs |
| Docker/container | Dockerfile/image | Trivy image, Trivy misconfig |
| Repository history | Git commits | Gitleaks |
| Runtime HTTP surface | staging URL | OWASP ZAP |

### 6.3. CodeQL

CodeQL используется как основной семантический SAST анализатор для JavaScript/TypeScript. Он выполняется отдельным job `sast-codeql` и загружает результаты в GitHub Code Scanning.

Параметры:

```yaml
languages: javascript-typescript
queries: security-and-quality
```

### 6.4. Semgrep

Semgrep дополняет CodeQL быстрыми правилами:

- OWASP Top 10;
- JavaScript/TypeScript rules;
- локальные дипломные правила из `config/semgrep/semgrep.yml`.

Результаты сохраняются в двух форматах:

- SARIF для GitHub Code Scanning;
- JSON для Security Gateway и DefectDojo.

### 6.5. Почему используются два SAST инструмента

CodeQL хорошо подходит для data-flow анализа, а Semgrep удобен для быстрых паттернов, custom rules и policy-as-code. Совместное использование снижает риск пропуска класса уязвимостей и показывает зрелый подход к DevSecOps.

## 7. Этап 3 - DAST

### 7.1. Цель этапа

Проверить работающее приложение на staging по HTTP-интерфейсу.

### 7.2. Инструмент

Используется **OWASP ZAP baseline scan**.

Выбран baseline режим, потому что он безопаснее для staging, чем aggressive active scan, и хорошо подходит для CI/CD. Он проверяет распространённые ошибки безопасности веб-приложений: security headers, cookie flags, потенциальные XSS/инъекции в пассивном режиме, disclosure и другие web findings.

### 7.3. Реализация

Job `dast-zap` запускает ZAP Docker image против `STAGING_URL` и сохраняет отчёты:

- `zap.json` - машинный формат для Security Gateway;
- `zap.html` - человекочитаемый отчёт;
- `zap.md` - Markdown summary;
- `zap-exit-code.txt` - код завершения сканера.

### 7.4. Политика правил ZAP

Файл:

```text
config/zap/zap-rules.tsv
```

В нём часть hardening findings переводится в WARN, а high-risk findings остаются blocking через Security Gateway.

## 8. Этап 4 - Security Checks

### 8.1. Secret scanning

Используется Gitleaks. Проверяется не только текущий код, но и история repository за счёт `fetch-depth: 0`.

Политика:

- любой реальный секрет считается `CRITICAL`;
- при обнаружении секрета требуется немедленная ротация;
- секреты должны храниться только в GitHub Secrets, Vault или аналогичном хранилище.

### 8.2. SCA и SBOM

Используются:

- `npm audit` - анализ зависимостей npm;
- CycloneDX - генерация SBOM `bom.cdx.json`;
- Trivy filesystem scan - дополнительная проверка зависимостей, секретов и misconfig.

SBOM нужен для прозрачности supply chain: по нему можно понять, какие компоненты включены в поставку, и использовать его в дальнейшем для Dependency-Track или DefectDojo.

### 8.3. Container scanning

Trivy image scan проверяет:

- OS packages в контейнере;
- library vulnerabilities;
- severity `CRITICAL`, `HIGH`, `MEDIUM`;
- только findings, для которых есть смысл принимать решение на gate.

### 8.4. IaC/config checks

Trivy filesystem scan дополнительно анализирует Dockerfile, compose/config files и потенциальные misconfiguration.

## 9. Этап 5 - Security Gateway

### 9.1. Цель

Security Gateway - это контрольная точка перед релизом. Он агрегирует результаты всех security tools и принимает решение:

- `allow` - релиз можно продолжать;
- `block` - релиз остановлен из-за превышения порогов риска.

### 9.2. Реализация

Реализация находится в:

```text
scripts/security_gate.py
```

Gateway читает отчёты из artifacts:

- `semgrep.sarif` / `semgrep.json`;
- `trivy-image.json`;
- `trivy-fs.json`;
- `npm-audit.json`;
- `gitleaks.json`;
- `zap.json`.

### 9.3. Пороговая политика

Базовая строгая политика:

| Severity | Порог |
|---|---:|
| Critical | 0 |
| High | 0 |
| Medium | 20 |
| Low | не блокирует |
| Info | не блокирует |

Это означает:

- один critical finding блокирует релиз;
- один high finding блокирует релиз;
- medium findings допускаются только в пределах технического долга;
- low/info findings фиксируются, но не блокируют релиз.

### 9.4. Дополнительные триггеры

Security Gateway реализует дополнительные требования диплома:

1. Оставляет Markdown comment в Pull Request.
2. Формирует summary с количеством findings по severity.
3. Даёт рекомендации по исправлению для каждого инструмента.
4. Сохраняет JSON result как artifact.
5. Может выгружать отчёты в DefectDojo.

### 9.5. Fail-closed модель

Если Security Gateway обнаруживает превышение порогов, job завершается с non-zero exit code. Это останавливает релиз и делает проблему видимой в CI/CD.

Для учебно-уязвимого OWASP Juice Shop ожидаемо, что release будет заблокирован. Это демонстрирует корректность модели: уязвимое приложение не должно автоматически попадать в production.

## 10. DefectDojo как система менеджмента уязвимостей

### 10.1. Роль DefectDojo

DefectDojo используется как централизованная система для:

- хранения findings;
- дедупликации;
- ведения жизненного цикла уязвимостей;
- назначения ответственных;
- отслеживания SLA;
- аналитики безопасности по продукту и engagement.

### 10.2. Загрузка результатов

Скрипт:

```text
scripts/defectdojo_upload.sh
```

Загружает результаты через API endpoint `/api/v2/reimport-scan/`.

Поддерживаемые типы отчётов:

| Файл | Scan type |
|---|---|
| `semgrep.json` | Semgrep JSON Report |
| `trivy-image.json` | Trivy Scan |
| `trivy-fs.json` | Trivy Scan |
| `npm-audit.json` | NPM Audit Scan |
| `gitleaks.json` | Gitleaks Scan |
| `zap.json` | ZAP Scan |

## 11. Процесс работы команды

### 11.1. Pull Request flow

1. Разработчик создаёт ветку.
2. Делает commit и открывает Pull Request.
3. Запускаются build, tests, SAST, SCA, secret scanning и container/config checks.
4. Security Gateway публикует comment в PR.
5. Если есть blocking findings, PR не должен быть merge до исправления или waiver.

### 11.2. Main branch flow

1. Merge в `main` запускает полный pipeline.
2. Собирается Docker image.
3. Image публикуется в GHCR.
4. Приложение разворачивается на staging VPS.
5. OWASP ZAP сканирует staging URL.
6. Security Gateway принимает итоговое решение.
7. Результаты выгружаются в DefectDojo.

### 11.3. Waiver policy

Waiver допустим только при выполнении условий:

- finding подтверждён как false positive или accepted risk;
- есть владелец риска;
- есть срок пересмотра;
- waiver оформлен документально;
- critical secrets не могут быть waiver без ротации.

## 12. SLA по уязвимостям

| Severity | SLA исправления | Действие |
|---|---:|---|
| Critical | 24-48 часов | немедленно блокировать release |
| High | 7 дней | блокировать release |
| Medium | 30 дней | допускать в пределах лимита |
| Low | 90 дней | плановое исправление |
| Info | best effort | hardening backlog |

## 13. Критерии приемки дипломного проекта

### Этап 1. CI/CD

- Pipeline запускается при Pull Request, push в `main` и вручную.
- Сборка и тесты выполняются автоматически.
- Docker image публикуется в GHCR.
- Staging deployment выполняется на VPS.
- Процесс документирован.

### Этап 2. SAST

- JavaScript/TypeScript покрыты CodeQL и Semgrep.
- Результаты Semgrep выгружаются как SARIF.
- CodeQL публикует findings в GitHub Code Scanning.
- Custom Semgrep rules подключены.

### Этап 3. DAST

- Staging URL проверяется OWASP ZAP.
- ZAP генерирует JSON, HTML и Markdown отчёты.
- Результаты учитываются Security Gateway.

### Этап 4. Security Checks

- Gitleaks проверяет секреты в истории repository.
- npm audit проверяет зависимости.
- CycloneDX формирует SBOM.
- Trivy проверяет image, filesystem и misconfig.

### Этап 5. Security Gateway

- Есть триггер на остановку release.
- Есть PR comment с summary.
- Есть рекомендации по исправлению.
- Есть JSON artifact с итоговым решением.
- Есть выгрузка в DefectDojo.

## 14. Аналитика выбора инструментов

| Зона | Инструмент | Причина выбора | Альтернативы |
|---|---|---|---|
| CI/CD | GitHub Actions | нативная интеграция с repository и security tab | GitLab CI/CD, CircleCI |
| SAST | CodeQL | data-flow анализ для JS/TS, GitHub integration | SonarQube, Snyk Code |
| SAST | Semgrep | быстрые правила и custom policy-as-code | ESLint security plugins |
| DAST | OWASP ZAP | open-source web scanner, удобен для CI | Burp Suite Enterprise, Arachni |
| Secrets | Gitleaks | проверяет историю git и PR | TruffleHog |
| SCA | npm audit | нативный анализ npm ecosystem | Snyk, OWASP Dependency-Check |
| SBOM | CycloneDX | распространённый формат SBOM | SPDX |
| Container | Trivy | image, fs, secret, misconfig checks | Grype, Docker Scout |
| Vulnerability management | DefectDojo | open-source менеджмент findings | Dependency-Track, Jira + custom |
| Gateway | custom Python | прозрачные правила и демонстрация policy-as-code | OPA/Conftest, GitHub branch protection |

## 15. Зоны роста

1. Перейти от ZAP baseline к authenticated scan.
2. Добавить active scan в отдельном nightly pipeline.
3. Подключить OPA/Conftest для policy-as-code.
4. Настроить Dependency-Track для постоянного мониторинга SBOM.
5. Подписывать контейнерные образы через cosign/keyless signing.
6. Добавить SLSA provenance для build artifacts.
7. Включить branch protection: required checks, required reviews, no direct push to main.
8. Настроить секреты через Vault вместо хранения всех параметров в GitHub Secrets.
9. Добавить WAF/reverse proxy hardening на VPS.
10. Ввести threat modeling и security champions process.

## 16. Риски и ограничения

| Риск | Влияние | Митигирующая мера |
|---|---|---|
| Juice Shop содержит намеренные уязвимости | Gateway блокирует release | использовать как демонстрацию block, для allow - patched fork или waiver |
| False positive SAST/DAST | лишняя нагрузка на разработчиков | triage, waiver, tuning rules |
| ZAP baseline без авторизации | неполное DAST покрытие | добавить authenticated scan |
| VPS без reverse proxy/TLS | hardening findings | добавить Nginx/Caddy и TLS |
| Зависимость от внешних registry | supply chain risk | pin actions, SBOM, image signing |

## 17. Итог

В результате спроектирован полный DevSecOps pipeline, который покрывает требования дипломной задачи:

- есть автоматизированный CI/CD;
- есть SAST по всему стеку проекта;
- есть DAST работающего staging сервиса;
- есть secret scanning, SCA, SBOM, container/config scan;
- есть Security Gateway с release block, PR comments и рекомендациями;
- есть интеграция с системой менеджмента уязвимостей;
- процесс документирован и масштабируем.

## 18. Источники

- OWASP Juice Shop: https://owasp.org/www-project-juice-shop/
- OWASP Juice Shop architecture: https://pwning.owasp-juice.shop/companion-guide/latest/introduction/architecture.html
- GitHub Actions documentation: https://docs.github.com/en/actions
- GitHub Actions environments: https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/deploy-to-environment
- GitHub SARIF upload: https://docs.github.com/en/code-security/how-tos/find-and-fix-code-vulnerabilities/integrate-with-existing-tools/uploading-a-sarif-file-to-github
- CodeQL Action: https://github.com/github/codeql-action
- Semgrep documentation: https://semgrep.dev/docs/
- Trivy Action: https://github.com/aquasecurity/trivy-action
- Gitleaks Action: https://github.com/gitleaks/gitleaks-action
- OWASP ZAP baseline action: https://github.com/zaproxy/action-baseline
- DefectDojo API import: https://docs.defectdojo.com/import_data/import_scan_files/api_pipeline_modelling/
- npm audit: https://docs.npmjs.com/cli/v10/commands/npm-audit/
- CycloneDX Node npm: https://github.com/CycloneDX/cyclonedx-node-npm
