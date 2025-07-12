# Cloud Build Service Account
resource "google_service_account" "cloud_build" {
  account_id   = "${var.app_name}-${var.environment}-build-sa"
  display_name = "Cloud Build Service Account for ${var.app_name} ${var.environment}"
  project      = var.project_id
}

# Grant Cloud Build roles
resource "google_project_iam_member" "cloud_build_permissions" {
  for_each = toset([
    "roles/cloudbuild.builds.builder",
    "roles/artifactregistry.writer",
    "roles/storage.objectAdmin",
    "roles/logging.logWriter",
    "roles/secretmanager.secretAccessor",
    "roles/run.admin",
    "roles/iam.serviceAccountUser"
  ])
  
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.cloud_build.email}"
}

# GitHub Connection
resource "google_cloudbuildv2_connection" "github_connection" {
  location = var.region
  name     = "github-connection-${var.app_name}"
  project  = var.project_id

  github_config {
    app_installation_id = var.github_app_installation_id
    authorizer_credential {
      oauth_token_secret_version = var.github_oauth_token_secret_version
    }
  }
}

# GitHub Repository
resource "google_cloudbuildv2_repository" "github_repository" {
  name              = "${var.app_name}-${var.environment}-repo"
  location          = var.region
  project           = var.project_id
  parent_connection = google_cloudbuildv2_connection.github_connection.id
  remote_uri        = var.github_repository_remote_uri
}

# Cloud Build Trigger
resource "google_cloudbuild_trigger" "build_and_push" {
  name            = "build-${var.app_name}-${var.environment}"
  description     = "Build and push ${var.app_name} Docker image for ${var.environment}"
  location        = var.region
  project         = var.project_id
  service_account = google_service_account.cloud_build.id

  repository_event_config {
    repository = google_cloudbuildv2_repository.github_repository.id
    push {
      branch = var.trigger_branch
    }
  }

  # Python project specific files
  included_files = [
    "cloudbuild.yaml",
    "Dockerfile",
    "pyproject.toml",
    "uv.lock",
    "src/**",
    "tests/**"
  ]

  ignored_files = [
    "README.md",
    "LICENSE",
    ".gitignore",
    ".git/**",
    ".github/**",
    "terraform/**",
    "*.md",
    ".env*"
  ]

  filename = "cloudbuild.yaml"

  substitutions = {
    _REGION          = var.region
    _REPOSITORY_NAME = var.artifact_registry_repository
    _IMAGE_NAME      = var.app_name
    _ENVIRONMENT     = var.environment
  }
}

# Enable required APIs
resource "google_project_service" "cloud_build" {
  project            = var.project_id
  service            = "cloudbuild.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "container_registry" {
  project            = var.project_id
  service            = "containerregistry.googleapis.com"
  disable_on_destroy = false
}