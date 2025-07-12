variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "asia-northeast1"
}

variable "github_app_installation_id" {
  description = "GitHub App Installation ID"
  type        = number
}

variable "github_oauth_token_secret_version" {
  description = "Secret Manager version ID for GitHub OAuth token"
  type        = string
}

variable "trigger_branch" {
  description = "Branch pattern to trigger Cloud Build"
  type        = string
}

variable "cpu_limit" {
  description = "CPU limit for the container"
  type        = string
  default     = "2000m"
}

variable "memory_limit" {
  description = "Memory limit for the container"
  type        = string
  default     = "2Gi"
}

variable "timeout_seconds" {
  description = "Timeout for the Cloud Run service in seconds"
  type        = number
  default     = 3600
}

variable "time_zone" {
  description = "Time zone for the scheduler"
  type        = string
  default     = "Asia/Tokyo"
}

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
}

variable "google_drive_source_folder_url" {
  description = "Google Drive source folder URL (where videos are stored)"
  type        = string
}

variable "google_drive_destination_folder_url" {
  description = "Google Drive destination folder URL (where results are saved)"
  type        = string
}

variable "slack_webhook_url" {
  description = "Slack webhook URL"
  type        = string
  sensitive   = true
}

variable "slack_notifications_enabled" {
  description = "Whether to enable Slack notifications"
  type        = bool
  default     = true
}