output "openai_api_key_secret_id" {
  description = "The secret ID for OpenAI API key"
  value       = google_secret_manager_secret.openai_api_key.id
}

output "slack_webhook_secret_id" {
  description = "The secret ID for Slack webhook URL"
  value       = google_secret_manager_secret.slack_webhook_url.id
}