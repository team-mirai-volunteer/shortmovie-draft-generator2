variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The region to deploy the Cloud Run service"
  type        = string
}

variable "service_name" {
  description = "Name of the Cloud Run service"
  type        = string
}

variable "container_image" {
  description = "Container image URL"
  type        = string
}

variable "cpu_limit" {
  description = "CPU limit for the container"
  type        = string
  default     = "1000m"
}

variable "memory_limit" {
  description = "Memory limit for the container"
  type        = string
  default     = "512Mi"
}

variable "timeout_seconds" {
  description = "Timeout for the Cloud Run service in seconds"
  type        = number
  default     = 3600
}

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
}

variable "service_account_key_json" {
  description = "Service account key JSON content"
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