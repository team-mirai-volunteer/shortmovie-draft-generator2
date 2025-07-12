output "service_account_email" {
  description = "The email of the Cloud Build service account"
  value       = google_service_account.cloud_build.email
}

output "service_account_id" {
  description = "The ID of the Cloud Build service account"
  value       = google_service_account.cloud_build.id
}

output "trigger_id" {
  description = "The ID of the Cloud Build trigger"
  value       = google_cloudbuild_trigger.build_and_push.id
}

output "trigger_name" {
  description = "The name of the Cloud Build trigger"
  value       = google_cloudbuild_trigger.build_and_push.name
}

output "github_repository_id" {
  description = "The ID of the GitHub repository resource"
  value       = google_cloudbuildv2_repository.github_repository.id
}