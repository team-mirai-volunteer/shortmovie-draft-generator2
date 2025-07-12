output "scheduler_job_name" {
  description = "Name of the Cloud Scheduler job"
  value       = google_cloud_scheduler_job.shortmovie_generator_job.name
}

output "scheduler_service_account_email" {
  description = "Email of the scheduler service account"
  value       = google_service_account.scheduler_sa.email
}