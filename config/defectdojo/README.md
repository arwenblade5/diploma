# DefectDojo setup

## Product model

Recommended objects:

- Product Type: `Diploma DevSecOps`
- Product: `OWASP Juice Shop Secure Pipeline`
- Engagement: `${branch}-${run_number}` or monthly engagement
- Environment: `staging`

## API token

Create API token in DefectDojo user profile and save it as GitHub Secret `DEFECTDOJO_TOKEN`.

## Import mode

The pipeline uses `/api/v2/reimport-scan/` with `auto_create_context=true` to simplify diploma deployment. In a production process, product and engagement should be created explicitly and managed by IaC or an onboarding script.
