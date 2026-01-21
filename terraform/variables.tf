# ======================
# AWS
# ======================
variable "aws_region" {
  type    = string
  default = "ap-southeast-1"
}

variable "aws_credentials" {
  type    = string
  default = "C:/Users/OMEN/Downloads/PROJECT_PORTO/terraform/keys/.aws/credentials"
}

variable "aws_profile" {
  type    = string
  default = "default"
}

# ======================
# Network
# ======================
variable "public_subnet_ids" {
  type = list(string)
}

variable "existing_security_group_id" {
  type        = string
  description = "Existing Security Group ID that allows inbound Redshift (5439) from laptop IP"
}

# ======================
# S3
# ======================
variable "s3_bucket_name" {
  type    = string
  default = "real-time-ecommerce-analytics"
}

# ======================
# Redshift
# ======================
variable "redshift_cluster_identifier" {
  type    = string
  default = "real-time-ecommerce-analytics-cluster"
}

variable "redshift_database_name" {
  type    = string
  default = "real_time_ecommerce_analytics"
}

variable "redshift_master_username" {
  type    = string
  default = "adminuser"
}

variable "redshift_master_password" {
  type      = string
  sensitive = true
}

variable "redshift_node_type" {
  type    = string
  default = "ra3.xlplus"
}