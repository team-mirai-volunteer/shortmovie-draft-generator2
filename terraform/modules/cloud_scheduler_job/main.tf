resource "google_cloud_scheduler_job" "shortmovie_generator_job" {
  name        = "${var.service_name}-scheduler"
  description = "Trigger ${var.service_name} every hour"
  schedule    = var.schedule
  time_zone   = var.time_zone
  project     = var.project_id
  region      = var.region

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/${var.cloud_run_job_name}:run"

    oauth_token {
      service_account_email = google_service_account.scheduler_sa.email
      scope                 = "https://www.googleapis.com/auth/cloud-platform"
    }
  }

  retry_config {
    retry_count          = 1
    max_retry_duration   = "60s"
    min_backoff_duration = "5s"
    max_backoff_duration = "60s"
  }

  depends_on = [
    google_project_service.cloudscheduler_api
  ]
}

resource "google_service_account" "scheduler_sa" {
  account_id   = "${var.service_name}-sched-sa"
  display_name = "Service Account for Cloud Scheduler"
  project      = var.project_id
}

resource "google_project_iam_member" "scheduler_job_runner" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.scheduler_sa.email}"
}

resource "google_project_service" "cloudscheduler_api" {
  project = var.project_id
  service = "cloudscheduler.googleapis.com"

  disable_on_destroy = false
}