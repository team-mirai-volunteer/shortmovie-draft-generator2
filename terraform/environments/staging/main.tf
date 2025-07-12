locals {
  environment = "staging"
  app_name    = "sm-draft"
}

# Artifact Registry for Docker images
module "artifact_registry" {
  source = "../../modules/artifact-registry"

  project_id    = var.project_id
  region        = var.region
  repository_id = "${local.app_name}-${local.environment}"
  description   = "Docker repository for ${local.app_name} ${local.environment}"
}

# Cloud Build configuration
module "cloud_build" {
  source = "../../modules/cloud-build"

  project_id                        = var.project_id
  region                            = var.region
  environment                       = local.environment
  app_name                          = local.app_name
  github_app_installation_id        = var.github_app_installation_id
  github_oauth_token_secret_version = var.github_oauth_token_secret_version
  trigger_branch                    = var.trigger_branch
  artifact_registry_repository      = module.artifact_registry.repository_id
}

# Service Account for Google Drive access
module "service_account" {
  source = "../../modules/service_account"

  project_id   = var.project_id
  service_name = "${local.app_name}-${local.environment}"
}

# Secret Manager for API keys
module "secret_manager" {
  source = "../../modules/secret_manager"

  project_id        = var.project_id
  app_name          = local.app_name
  environment       = local.environment
  openai_api_key    = var.openai_api_key
  slack_webhook_url = var.slack_webhook_url
}

# Cloud Run Job
module "cloud_run_job" {
  source = "../../modules/cloud_run_job"

  project_id                          = var.project_id
  region                              = var.region
  service_name                        = "${local.app_name}-${local.environment}"
  container_image                     = "${var.region}-docker.pkg.dev/${var.project_id}/${module.artifact_registry.repository_id}/${local.app_name}:latest"
  cpu_limit                           = var.cpu_limit
  memory_limit                        = var.memory_limit
  timeout_seconds                     = var.timeout_seconds
  openai_api_key_secret_id            = module.secret_manager.openai_api_key_secret_id
  service_account_key_base64          = module.service_account.service_account_key
  google_drive_source_folder_url      = var.google_drive_source_folder_url
  google_drive_destination_folder_url = var.google_drive_destination_folder_url
  slack_webhook_secret_id             = module.secret_manager.slack_webhook_secret_id
  environment                         = local.environment

  depends_on = [module.artifact_registry, module.secret_manager]
}

# Cloud Scheduler for periodic execution
module "cloud_scheduler_job" {
  source = "../../modules/cloud_scheduler_job"

  project_id         = var.project_id
  region             = var.region
  service_name       = "${local.app_name}-${local.environment}"
  cloud_run_job_name = module.cloud_run_job.job_name
  schedule           = "0 * * * *" # 1時間に1回実行
  time_zone          = var.time_zone

  depends_on = [module.cloud_run_job]
}

