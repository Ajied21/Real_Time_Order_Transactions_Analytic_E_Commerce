terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ======================
# AWS Provider
# ======================
provider "aws" {
  region                   = var.aws_region
  shared_credentials_files = [var.aws_credentials]
  profile                  = var.aws_profile
}

# ======================
# S3 Bucket
# ======================
resource "aws_s3_bucket" "real_time_ecommerce_analytics" {
  bucket        = var.s3_bucket_name
  force_destroy = true
}

resource "aws_s3_bucket_lifecycle_configuration" "bucket_lifecycle" {
  bucket = aws_s3_bucket.real_time_ecommerce_analytics.id

  rule {
    id     = "abort-multipart-upload"
    status = "Enabled"

    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = 1
    }
  }
}

# ======================
# Redshift Cluster
# ======================
resource "aws_redshift_cluster" "real_time_ecommerce_analytics" {
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