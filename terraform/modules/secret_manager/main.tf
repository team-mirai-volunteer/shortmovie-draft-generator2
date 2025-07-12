# Enable Secret Manager API
resource "google_project_service" "secretmanager_api" {
  project = var.project_id
  service = "secretmanager.googleapis.com"

  disable_on_destroy = false
}

# OpenAI API Key Secret
resource "google_secret_manager_secret" "openai_api_key" {
  project   = var.project_id
  secret_id = "${var.app_name}-${var.environment}-openai-api-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.secretmanager_api]
}

resource "google_secret_manager_secret_version" "openai_api_key" {
  secret      = google_secret_manager_secret.openai_api_key.id
  secret_data = var.openai_api_key
}

# Slack Webhook URL Secret  
resource "google_secret_manager_secret" "slack_webhook_url" {
  project   = var.project_id
  secret_id = "${var.app_name}-${var.environment}-slack-webhook-url"

  replication {
    auto {}
  }

  depends_on = [google_project_service.secretmanager_api]
}

resource "google_secret_manager_secret_version" "slack_webhook_url" {
  secret      = google_secret_manager_secret.slack_webhook_url.id
  secret_data = var.slack_webhook_url
}