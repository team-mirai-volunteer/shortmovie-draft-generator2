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

output "cloud_run_job_name" {
  description = "Name of the Cloud Run job"
  value       = module.cloud_run_job.job_name
}

output "service_account_email" {
  description = "Email of the Google Drive service account"
  value       = module.service_account.service_account_email
}

output "scheduler_job_name" {
  description = "Name of the Cloud Scheduler job"
  value       = module.cloud_scheduler_job.scheduler_job_name
}