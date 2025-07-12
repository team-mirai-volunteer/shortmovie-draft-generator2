# Enable Artifact Registry API
resource "google_project_service" "artifact_registry" {
  project            = var.project_id
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

# Create Artifact Registry repository
resource "google_artifact_registry_repository" "repository" {
  location      = var.region
  repository_id = var.repository_id
  description   = var.description
  format        = var.format
  project       = var.project_id

  depends_on = [google_project_service.artifact_registry]
}