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