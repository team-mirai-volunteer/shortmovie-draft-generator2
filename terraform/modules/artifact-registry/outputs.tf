output "repository_id" {
  description = "The ID of the repository"
  value       = google_artifact_registry_repository.repository.repository_id
}

output "repository_name" {
  description = "The full repository name"
  value       = google_artifact_registry_repository.repository.name
}

output "repository_url" {
  description = "The URL of the repository"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.repository.repository_id}"
}