variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "asia-northeast1"
}

variable "repository_id" {
  description = "The repository ID"
  type        = string
}

variable "description" {
  description = "Repository description"
  type        = string
  default     = ""
}

variable "format" {
  description = "Repository format (DOCKER, MAVEN, NPM, etc.)"
  type        = string
  default     = "DOCKER"
}