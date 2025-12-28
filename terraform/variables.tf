# ===== AWS =====
variable "aws_region" {
  type    = string
  default = "ap-southeast-1"
}

variable "aws_credentials" {
  type    = string
  default = "C:/Users/G2 Academy/.aws/credentials"
}

variable "aws_profile" {
  type    = string
  default = "default"
}

variable "s3_bucket_name" {
  type    = string
  default = "final-project-zoomcamp"
}

variable "redshift_cluster_identifier" {
  type    = string
  default = "final-project-cluster"
}

variable "redshift_database_name" {
  type    = string
  default = "final_project"
}

variable "redshift_master_username" {
  type    = string
  default = "adminuser"
}

variable "redshift_master_password" {
  type      = string
  sensitive = true
  default   = "Admin12345!"
}

variable "redshift_node_type" {
  type    = string
  default = "dc2.large"
}

# ===== GCP =====
variable "gcp_credentials" {
  type    = string
  default = "C:/Users/G2 Academy/OneDrive/Desktop/data-engineering-zoomcamp-2024/Project/Keys_GCP/keys.json"
}

variable "gcp_project" {
  type    = string
  default = "marine-aria-419404"
}

variable "gcp_region" {
  type    = string
  default = "asia-southeast2-b"
}

variable "gcp_location" {
  type    = string
  default = "asia-southeast2"
}

variable "gcs_bucket_name" {
  type    = string
  default = "final-project-zoomcamp"
}