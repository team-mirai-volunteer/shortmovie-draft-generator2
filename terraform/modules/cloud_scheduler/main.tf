resource "google_cloud_scheduler_job" "shortmovie_generator_job" {
  name        = "${var.service_name}-scheduler"
  description = "Trigger ${var.service_name} every hour"
  schedule    = var.schedule
  time_zone   = var.time_zone
  project     = var.project_id
  region      = var.region

  http_target {
    http_method = "POST"
    uri         = "${var.cloud_run_url}/batch-process"
    
    headers = {
      "Content-Type" = "application/json"
    }

    body = base64encode(jsonencode({
      update = true
    }))

    oidc_token {
      service_account_email = google_service_account.scheduler_sa.email
      audience              = var.cloud_run_url
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
  account_id   = "${var.service_name}-scheduler-sa"
  display_name = "Service Account for Cloud Scheduler"
  project      = var.project_id
}

resource "google_cloud_run_service_iam_member" "scheduler_invoker" {
  service  = var.cloud_run_service_name
  location = var.region
  project  = var.project_id
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler_sa.email}"
}

resource "google_project_service" "cloudscheduler_api" {
  project = var.project_id
  service = "cloudscheduler.googleapis.com"

  disable_on_destroy = false
}