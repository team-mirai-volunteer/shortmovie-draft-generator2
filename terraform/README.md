# Terraform Configuration for shortmovie-draft-generator2

This directory contains Terraform configurations for deploying the shortmovie-draft-generator2 application infrastructure on Google Cloud Platform.

## Structure

```
terraform/
├── modules/              # Reusable Terraform modules
│   ├── artifact-registry/   # Artifact Registry for Docker images
│   └── cloud-build/         # Cloud Build configuration
└── environments/         # Environment-specific configurations
    ├── staging/            # Staging environment
    └── production/         # Production environment
```

## Prerequisites

1. Google Cloud SDK installed and authenticated
2. Terraform >= 1.5.0
3. GCP Project with billing enabled
4. GitHub App configured for Cloud Build integration
5. Required APIs enabled (will be enabled by Terraform if not already):
   - Cloud Build API
   - Artifact Registry API
   - Container Registry API

## Setup

### 1. Create GitHub OAuth Token Secret

First, create a GitHub OAuth token and store it in Secret Manager:

```bash
echo -n "YOUR_GITHUB_TOKEN" | gcloud secrets create github-token \
  --data-file=- \
  --project=YOUR_PROJECT_ID
```

### 2. Configure Environment Variables

For each environment (staging/production), copy the example variables file:

```bash
cd environments/staging
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

### 3. Initialize Terraform

```bash
# For staging
cd environments/staging
terraform init \
  -backend-config="bucket=YOUR_TERRAFORM_STATE_BUCKET" \
  -backend-config="prefix=shortmovie-draft-generator/staging"

# For production
cd environments/production
terraform init \
  -backend-config="bucket=YOUR_TERRAFORM_STATE_BUCKET" \
  -backend-config="prefix=shortmovie-draft-generator/production"
```

### 4. Deploy Infrastructure

```bash
# Plan changes
terraform plan

# Apply changes
terraform apply
```

## Cloud Build Triggers

The configuration creates Cloud Build triggers that:

- **Staging**: Triggered on pushes to `develop` branch
- **Production**: Triggered on pushes to `main` branch

Each trigger will:
1. Build a Docker image from the repository
2. Push the image to Artifact Registry with tags:
   - Git commit SHA
   - Environment name (staging/production)
   - latest

## Outputs

After deployment, you can get the following information:

```bash
# Get Artifact Registry URL
terraform output artifact_registry_url

# Get Cloud Build service account
terraform output cloud_build_service_account

# Get Cloud Build trigger name
terraform output cloud_build_trigger_name
```

## Updating Infrastructure

To update the infrastructure:

1. Make changes to the Terraform files
2. Run `terraform plan` to review changes
3. Run `terraform apply` to apply changes

## Destroying Infrastructure

To destroy the infrastructure (use with caution):

```bash
terraform destroy
```

## Security Notes

- Never commit `terraform.tfvars` files containing sensitive information
- Use Secret Manager for all sensitive data
- Cloud Build service accounts have minimal required permissions
- Enable audit logging for production environments