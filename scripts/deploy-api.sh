#!/usr/bin/env bash
# Deploy ChainLens API image to AWS App Runner via ECR.
# Prerequisites: aws CLI logged in (`aws login`), docker or podman, TiDB DATABASE_URL.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REGION="${AWS_REGION:-$(aws configure get region 2>/dev/null || echo ap-southeast-3)}"
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
REPO="chainlens-api"
IMAGE_TAG="${IMAGE_TAG:-latest}"
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO}"
SERVICE_NAME="${SERVICE_NAME:-chainlens-api}"
CONTAINER_RUNTIME="${CONTAINER_RUNTIME:-}"

if command -v docker >/dev/null 2>&1; then
  CONTAINER_RUNTIME="${CONTAINER_RUNTIME:-docker}"
elif command -v podman >/dev/null 2>&1; then
  CONTAINER_RUNTIME="${CONTAINER_RUNTIME:-podman}"
else
  echo "Need docker or podman" >&2
  exit 1
fi

: "${DATABASE_URL:?Set DATABASE_URL to TiDB Cloud SQLAlchemy URL}"
: "${CORS_ORIGINS:?Set CORS_ORIGINS to your Pages URL}"

MOCK_ANALYZE="${MOCK_ANALYZE:-true}"
SOLANA_RPC_URL="${SOLANA_RPC_URL:-https://api.mainnet-beta.solana.com}"
OPENAI_API_KEY="${OPENAI_API_KEY:-}"

echo "==> Ensuring ECR repository ${REPO}"
aws ecr describe-repositories --repository-names "${REPO}" --region "${REGION}" >/dev/null 2>&1 \
  || aws ecr create-repository --repository-name "${REPO}" --region "${REGION}" >/dev/null

echo "==> Logging into ECR"
aws ecr get-login-password --region "${REGION}" \
  | "${CONTAINER_RUNTIME}" login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

echo "==> Building image"
"${CONTAINER_RUNTIME}" build -t "${REPO}:${IMAGE_TAG}" "${ROOT}/backend"
"${CONTAINER_RUNTIME}" tag "${REPO}:${IMAGE_TAG}" "${ECR_URI}:${IMAGE_TAG}"

echo "==> Pushing ${ECR_URI}:${IMAGE_TAG}"
"${CONTAINER_RUNTIME}" push "${ECR_URI}:${IMAGE_TAG}"

ENV_JSON=$(cat <<EOF
[
  {"name":"DATABASE_URL","value":"${DATABASE_URL}"},
  {"name":"SOLANA_RPC_URL","value":"${SOLANA_RPC_URL}"},
  {"name":"OPENAI_API_KEY","value":"${OPENAI_API_KEY}"},
  {"name":"MOCK_ANALYZE","value":"${MOCK_ANALYZE}"},
  {"name":"CORS_ORIGINS","value":"${CORS_ORIGINS}"}
]
EOF
)

ACCESS_ROLE="arn:aws:iam::${ACCOUNT_ID}:role/AppRunnerECRAccessRole"

if aws apprunner list-services --region "${REGION}" --query "ServiceSummaryList[?ServiceName=='${SERVICE_NAME}'].ServiceArn" --output text | grep -q .; then
  SERVICE_ARN="$(aws apprunner list-services --region "${REGION}" --query "ServiceSummaryList[?ServiceName=='${SERVICE_NAME}'].ServiceArn" --output text | awk '{print $1}')"
  echo "==> Updating App Runner service ${SERVICE_NAME}"
  aws apprunner start-deployment --service-arn "${SERVICE_ARN}" --region "${REGION}" >/dev/null
else
  echo "==> Creating App Runner service ${SERVICE_NAME}"
  # App Runner ECR access role must exist: AppRunnerECRAccessRole (AWS managed wizard creates this)
  aws apprunner create-service \
    --region "${REGION}" \
    --service-name "${SERVICE_NAME}" \
    --source-configuration "{
      \"AuthenticationConfiguration\": {\"AccessRoleArn\": \"${ACCESS_ROLE}\"},
      \"AutoDeploymentsEnabled\": false,
      \"ImageRepository\": {
        \"ImageIdentifier\": \"${ECR_URI}:${IMAGE_TAG}\",
        \"ImageRepositoryType\": \"ECR\",
        \"ImageConfiguration\": {
          \"Port\": \"8000\",
          \"RuntimeEnvironmentVariables\": {
            \"DATABASE_URL\": \"${DATABASE_URL}\",
            \"SOLANA_RPC_URL\": \"${SOLANA_RPC_URL}\",
            \"OPENAI_API_KEY\": \"${OPENAI_API_KEY}\",
            \"MOCK_ANALYZE\": \"${MOCK_ANALYZE}\",
            \"CORS_ORIGINS\": \"${CORS_ORIGINS}\"
          }
        }
      }
    }" \
    --instance-configuration '{"Cpu":"1024","Memory":"2048"}' \
    --health-check-configuration '{"Protocol":"HTTP","Path":"/health","Interval":10,"Timeout":5,"HealthyThreshold":1,"UnhealthyThreshold":5}' \
    >/tmp/chainlens-apprunner-create.json
fi

echo "==> Waiting for RUNNING"
for i in $(seq 1 60); do
  STATUS="$(aws apprunner list-services --region "${REGION}" --query "ServiceSummaryList[?ServiceName=='${SERVICE_NAME}'].Status" --output text)"
  URL="$(aws apprunner list-services --region "${REGION}" --query "ServiceSummaryList[?ServiceName=='${SERVICE_NAME}'].ServiceUrl" --output text)"
  echo "  status=${STATUS} url=${URL}"
  if [[ "${STATUS}" == "RUNNING" ]]; then
    echo "API_URL=https://${URL}"
    exit 0
  fi
  sleep 10
done

echo "Timed out waiting for App Runner" >&2
exit 1
