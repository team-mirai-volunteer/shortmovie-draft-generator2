output "artifact_registry_url" {
  description = "URL of the Artifact Registry repository"
  value       = module.artifact_registry.repository_url
}

output "cloud_build_service_account" {
  description = "Email of the Cloud Build service account"
  value       = module.cloud_build.service_account_email
}

output "cloud_build_trigger_name" {
  description = "Name of the Cloud Build trigger"
  value       = module.cloud_build.trigger_name
}