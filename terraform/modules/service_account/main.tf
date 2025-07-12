resource "google_service_account" "drive_access_sa" {
  account_id   = "${var.service_name}-drive-sa"
  display_name = "Service Account for Google Drive Access"
  project      = var.project_id
}

resource "google_service_account_key" "drive_access_key" {
  service_account_id = google_service_account.drive_access_sa.name
}

resource "google_project_iam_member" "drive_api_user" {
  project = var.project_id
  role    = "roles/serviceusage.serviceUsageConsumer"
  member  = "serviceAccount:${google_service_account.drive_access_sa.email}"
}

resource "google_project_service" "drive_api" {
  project = var.project_id
  service = "drive.googleapis.com"

  disable_on_destroy = false
}

resource "google_project_service" "sheets_api" {
  project = var.project_id
  service = "sheets.googleapis.com"

  disable_on_destroy = false
}