#!/usr/bin/env bash
set -e

PROJECT_ID="letzryd-dev-test"
REGION="asia-south1"
REPO_NAME="ola-sync-repo"
IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/ola-sync-worker:latest"
JOB_NAME="ola-sync-job"
SCHEDULER_NAME="ola-sync-hourly-trigger"
CRON_SCHEDULE="0 * * * *"  # Every hour
TIMEZONE="Asia/Kolkata"

echo "=== STAGE 1: Config GCP Project ==="
gcloud config set project "${PROJECT_ID}"

echo "=== STAGE 2: Create Artifact Registry Repo if needed ==="
gcloud artifacts repositories describe "${REPO_NAME}" --location="${REGION}" >/dev/null 2>&1 || \
gcloud artifacts repositories create "${REPO_NAME}" \
  --repository-format=docker \
  --location="${REGION}" \
  --description="Docker repository for Ola Sync Worker"

echo "=== STAGE 3: Build & Push Container Image ==="
gcloud builds submit --tag "${IMAGE_NAME}" .

echo "=== STAGE 4: Create or Update Cloud Run Job ==="
gcloud run jobs deploy "${JOB_NAME}" \
  --image="${IMAGE_NAME}" \
  --region="${REGION}" \
  --memory=2Gi \
  --cpu=2 \
  --max-retries=2 \
  --set-env-vars="OLA_PHONE_NUMBER=${OLA_PHONE_NUMBER:-7483731338},DATABASE_URL=${DATABASE_URL},SMTP_HOST=${SMTP_HOST:-smtp.gmail.com},SMTP_PORT=${SMTP_PORT:-587},SMTP_USER=${SMTP_USER},SMTP_PASSWORD=${SMTP_PASSWORD},ALERT_TO_EMAIL=${ALERT_TO_EMAIL},OLA_EMAIL=${OLA_EMAIL},GMAIL_IMAP_USER=${GMAIL_IMAP_USER},GMAIL_IMAP_PASSWORD=${GMAIL_IMAP_PASSWORD}"

echo "=== STAGE 5: Create or Update Cloud Scheduler Trigger ==="
gcloud scheduler jobs create http "${SCHEDULER_NAME}" \
  --location="${REGION}" \
  --schedule="${CRON_SCHEDULE}" \
  --time-zone="${TIMEZONE}" \
  --uri="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${JOB_NAME}:run" \
  --http-method=POST \
  --oauth-service-account-email="925756819101-compute@developer.gserviceaccount.com" || \
gcloud scheduler jobs update http "${SCHEDULER_NAME}" \
  --location="${REGION}" \
  --schedule="${CRON_SCHEDULE}" \
  --time-zone="${TIMEZONE}" \
  --http-method=POST \
  --uri="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${JOB_NAME}:run" \
  --oauth-service-account-email="925756819101-compute@developer.gserviceaccount.com"

echo "✅ GCP Deployment Complete!"
echo "Cloud Run Job: ${JOB_NAME}"
echo "Cloud Scheduler: ${SCHEDULER_NAME} (${CRON_SCHEDULE})"
