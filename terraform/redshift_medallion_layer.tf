resource "aws_redshift_schema" "bronze" {
  name     = "bronze"
  database = aws_redshift_cluster.final_project.database_name
  owner    = var.redshift_master_username
}

resource "aws_redshift_schema" "silver" {
  name     = "silver"
  database = aws_redshift_cluster.final_project.database_name
  owner    = var.redshift_master_username
}

resource "aws_redshift_schema" "gold" {
  name     = "gold"
  database = aws_redshift_cluster.final_project.database_name
  owner    = var.redshift_master_username
}