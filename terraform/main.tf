terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "5.6.0"
    }
  }
}

# ===== AWS Provider =====
provider "aws" {
  region                  = var.aws_region
  shared_credentials_files = [var.aws_credentials]
  profile                 = var.aws_profile
}

# ===== S3 Bucket =====
resource "aws_s3_bucket" "final_project_zoomcamp" {
  bucket        = var.s3_bucket_name
  force_destroy = true
}

resource "aws_s3_bucket_lifecycle_configuration" "bucket_lifecycle" {
  bucket = aws_s3_bucket.final_project_zoomcamp.id

  rule {
    id     = "abort-multipart-upload"
    status = "Enabled"

    abort_incomplete_multipart_upload {
      days_after_initiation = 1
    }
  }
}

# ===== Redshift Cluster =====
resource "aws_redshift_cluster" "final_project" {
  cluster_identifier = var.redshift_cluster_identifier
  database_name      = var.redshift_database_name
  master_username    = var.redshift_master_username
  master_password    = var.redshift_master_password

  node_type       = var.redshift_node_type
  cluster_type    = "single-node"
  number_of_nodes = 1

  publicly_accessible = true
  skip_final_snapshot = true
}

# ===== GCP Provider =====
provider "google" {
  credentials = file(var.gcp_credentials)
  project     = var.gcp_project
  region      = var.gcp_region
}

# ===== GCP Storage Bucket =====
resource "google_storage_bucket" "final_project_zoomcamp" {
  name          = var.gcs_bucket_name
  location      = var.gcp_location
  force_destroy = true

  lifecycle_rule {
    condition {
      age = 1
    }
    action {
      type = "AbortIncompleteMultipartUpload"
    }
  }
}