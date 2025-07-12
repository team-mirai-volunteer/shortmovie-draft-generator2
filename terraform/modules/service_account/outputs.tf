output "service_account_email" {
  description = "Email of the service account"
  value       = google_service_account.drive_access_sa.email
}

output "service_account_key" {
  description = "Service account key"
  value       = google_service_account_key.drive_access_key.private_key
  sensitive   = true
}