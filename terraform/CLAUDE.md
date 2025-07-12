# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
Terraform infrastructure code for managing GCP resources for the shortmovie-draft-generator2 application. This infrastructure supports an automated video processing system that transcribes audio and generates drafts using AI APIs.

## Development Commands

### Initial Setup
```bash
# Navigate to the appropriate environment
cd environments/staging  # or production

# Copy and configure terraform variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your configuration

# Initialize Terraform (uses Terraform Cloud backend)
terraform init
```

### Common Terraform Operations
```bash
# Preview changes
terraform plan

# Apply infrastructure changes
terraform apply

# Format Terraform files
terraform fmt -recursive

# Validate configuration
terraform validate

# Destroy infrastructure (use with caution)
terraform destroy
```

## Architecture Structure

### Module Organization
```
modules/
├── artifact-registry/    # Docker image storage
├── cloud-build/         # CI/CD pipeline configuration
├── cloud_run_job/       # Batch processing with Cloud Run Jobs
├── cloud_scheduler_job/ # Scheduled job triggers
└── service_account/     # Google Drive access permissions
```

### Environment Structure
- `environments/staging/`: Staging environment configuration
- `environments/production/`: Production environment configuration

Each environment has its own:
- `main.tf`: Resource definitions and module calls
- `variables.tf`: Variable declarations
- `outputs.tf`: Output values
- `terraform.tfvars`: Environment-specific values (not in git)

## Key Infrastructure Components

### Cloud Run Job
- Executes video processing as batch jobs
- Configurable CPU (default: 2000m) and memory (default: 2Gi)
- Timeout: 1 hour per job execution
- Scheduled via Cloud Scheduler (default: hourly)

### CI/CD Pipeline
- **Staging**: Auto-builds on `develop` branch push
- **Production**: Auto-builds on `main` branch push
- Docker images tagged with commit SHA and `latest`

### Security Configuration
- API keys stored in Google Secret Manager
- Service accounts follow least-privilege principle
- Separate service accounts for Cloud Build and Cloud Run
- OpenAI API Key and Slack Webhook URL are automatically created as secrets

## Important Configuration Variables

Key variables in `terraform.tfvars`:
```hcl
# GCP Configuration
project_id = "your-project-id"
region = "asia-northeast1"

# GitHub Integration
github_app_installation_id = 123456789
github_oauth_token_secret_version = "projects/PROJECT/secrets/github-token/versions/latest"

# Cloud Run Job Resources
cpu_limit = "2000m"
memory_limit = "2Gi"
timeout_seconds = 3600
schedule = "0 * * * *"  # Cron format

# External Services (stored in Secret Manager)
openai_api_key = "sk-..."  # Will be stored in Secret Manager
google_drive_source_folder_url = "https://drive.google.com/..."
google_drive_destination_folder_url = "https://drive.google.com/..."
slack_webhook_url = "https://hooks.slack.com/..."  # Will be stored in Secret Manager
```

## Terraform Cloud Configuration
- Organization: `shortmovie-draft-generator`
- Workspaces: `sm-draft-staging`, `sm-draft-production`
- State management handled by Terraform Cloud

## Naming Conventions
- Resources: `${app_name}-${environment}` (e.g., `sm-draft-staging`)
- Docker images: `${region}-docker.pkg.dev/${project_id}/${app_name}/${app_name}`
- Service accounts: `${app_name}-${service}-${environment}@${project_id}.iam.gserviceaccount.com`