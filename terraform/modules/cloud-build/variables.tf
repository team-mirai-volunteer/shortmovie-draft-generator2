variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "asia-northeast1"
}

variable "environment" {
  description = "Environment name (staging or production)"
  type        = string
  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "Environment must be either 'staging' or 'production'."
  }
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "shortmovie-draft-generator"
}

variable "github_app_installation_id" {
  description = "GitHub App Installation ID"
  type        = number
}

variable "github_oauth_token_secret_version" {
  description = "Secret Manager version ID for GitHub OAuth token"
  type        = string
}

variable "github_repository_remote_uri" {
  description = "GitHub repository remote URI"
  type        = string
  default     = "https://github.com/team-mirai-volunteer/shortmovie-draft-generator2.git"
}

variable "trigger_branch" {
  description = "Branch pattern to trigger builds"
  type        = string
}

variable "artifact_registry_repository" {
  description = "Artifact Registry repository name"
  type        = string
}