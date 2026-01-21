output "redshift_endpoint" {
  value = aws_redshift_cluster.real_time_ecommerce_analytics.endpoint
}

output "s3_bucket_name" {
  value = aws_s3_bucket.real_time_ecommerce_analytics.bucket
}