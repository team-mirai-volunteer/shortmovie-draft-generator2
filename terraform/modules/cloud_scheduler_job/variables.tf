variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The region for Cloud Scheduler"
  type        = string
}

variable "service_name" {
  description = "Name of the service"
  type        = string
}

variable "cloud_run_job_name" {
  description = "Name of the Cloud Run job to invoke"
  type        = string
}

variable "schedule" {
  description = "Cron schedule expression"
  type        = string
  default     = "0 * * * *"
}

variable "time_zone" {
  description = "Time zone for the scheduler"
  type        = string
  default     = "Asia/Tokyo"
}