output "job_name" {
  description = "Name of the Cloud Run job"
  value       = google_cloud_run_v2_job.shortmovie_generator.name
}

output "job_id" {
  description = "ID of the Cloud Run job"
  value       = google_cloud_run_v2_job.shortmovie_generator.id
}

output "service_account_email" {
  description = "Email of the service account"
  value       = google_service_account.cloud_run_sa.email
}