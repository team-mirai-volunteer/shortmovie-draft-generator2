resource "google_cloud_run_v2_job" "shortmovie_generator" {
  name     = var.service_name
  location = var.region
  project  = var.project_id

  template {
    template {
      containers {
        image = var.container_image
        args  = ["python", "-m", "src.main", "--drive"]
        
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
          name  = "GOOGLE_SERVICE_ACCOUNT_KEY_PATH"
          value = "/secrets/service-account-key.json"
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

        volume_mounts {
          name       = "service-account-key"
          mount_path = "/secrets"
        }
      }

      volumes {
        name = "service-account-key"
        secret {
          secret = google_secret_manager_secret.service_account_key.secret_id
          items {
            version = "latest"
            path    = "service-account-key.json"
          }
        }
      }

      timeout           = "${var.timeout_seconds}s"
      service_account   = google_service_account.cloud_run_sa.email
      max_retries       = 1
    }
  }

  depends_on = [
    google_project_service.cloud_run_api,
    google_secret_manager_secret_version.service_account_key_version
  ]
}

resource "google_service_account" "cloud_run_sa" {
  account_id   = "${var.service_name}-sa"
  display_name = "Service Account for ${var.service_name}"
  project      = var.project_id
}

resource "google_secret_manager_secret" "service_account_key" {
  secret_id = "${var.service_name}-service-account-key"
  project   = var.project_id

  replication {
    auto {}
  }

  depends_on = [google_project_service.secretmanager_api]
}

resource "google_secret_manager_secret_version" "service_account_key_version" {
  secret      = google_secret_manager_secret.service_account_key.id
  secret_data = var.service_account_key_json
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
