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
  trigger_branch                    = "^develop$"
  artifact_registry_repository      = module.artifact_registry.repository_id
}

