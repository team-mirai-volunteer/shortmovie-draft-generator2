# Google Driveサービスアカウントキーを保存するシークレット
resource "google_secret_manager_secret" "service_account_key" {
  project   = var.project_id
  secret_id = "${var.service_name}-service-account-key"

  replication {
    auto {}
  }

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
  
  deletion_protection = false

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
          name = "OPENAI_API_KEY"
          value_source {
            secret_key_ref {
              secret  = var.openai_api_key_secret_id
              version = "latest"
            }
          }
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
          name = "SLACK_WEBHOOK_URL"
          value_source {
            secret_key_ref {
              secret  = var.slack_webhook_secret_id
              version = "latest"
            }
          }
        }

        env {
          name  = "ENVIRONMENT"
          value = var.environment
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

resource "google_secret_manager_secret_iam_member" "cloud_run_openai_secret_accessor" {
  secret_id = var.openai_api_key_secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "cloud_run_slack_secret_accessor" {
  secret_id = var.slack_webhook_secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

resource "google_project_service" "cloud_run_api" {
  project = var.project_id
  service = "run.googleapis.com"

  disable_on_destroy = false
}

