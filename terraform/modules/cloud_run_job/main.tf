# Google Driveサービスアカウントキーを保存するシークレット
resource "google_secret_manager_secret" "service_account_key" {
  project   = var.project_id
  secret_id = "${var.service_name}-service-account-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.secretmanager_api]
}

# シークレットのバージョン（実際のキーデータ）
resource "google_secret_manager_secret_version" "service_account_key" {
  secret      = google_secret_manager_secret.service_account_key.id
  secret_data = var.service_account_key_base64
}

resource "google_cloud_run_v2_job" "shortmovie_generator" {
  name     = var.service_name
  location = var.region
  project  = var.project_id

  template {
    template {
      containers {
        image = var.container_image
        args  = ["python", "-m", "src.main", "--drive-batch"]

        resources {
          limits = {
            cpu    = var.cpu_limit
            memory = var.memory_limit
          }
        }

        env {
          name  = "OPENAI_API_KEY"
          value = var.openai_api_key
        }

        env {
          name = "GOOGLE_SERVICE_ACCOUNT_KEY_BASE64"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.service_account_key.secret_id
              version = "latest"
            }
          }
        }

        env {
          name  = "GOOGLE_DRIVE_SOURCE_FOLDER_URL"
          value = var.google_drive_source_folder_url
        }

        env {
          name  = "GOOGLE_DRIVE_DESTINATION_FOLDER_URL"
          value = var.google_drive_destination_folder_url
        }

        env {
          name  = "SLACK_WEBHOOK_URL"
          value = var.slack_webhook_url
        }

      }

      timeout         = "${var.timeout_seconds}s"
      service_account = google_service_account.cloud_run_sa.email
      max_retries     = 1
    }
  }

  depends_on = [
    google_project_service.cloud_run_api,
    google_secret_manager_secret_version.service_account_key
  ]
}

resource "google_service_account" "cloud_run_sa" {
  account_id   = "${var.service_name}-sa"
  display_name = "Service Account for ${var.service_name}"
  project      = var.project_id
}

resource "google_secret_manager_secret_iam_member" "cloud_run_secret_accessor" {
  secret_id = google_secret_manager_secret.service_account_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

resource "google_project_service" "cloud_run_api" {
  project = var.project_id
  service = "run.googleapis.com"

  disable_on_destroy = false
}

resource "google_project_service" "secretmanager_api" {
  project = var.project_id
  service = "secretmanager.googleapis.com"

  disable_on_destroy = false
}
