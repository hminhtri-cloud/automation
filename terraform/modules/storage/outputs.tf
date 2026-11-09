output "bucket_name" {
  description = "Name of the private lab S3 bucket"
  value       = aws_s3_bucket.this.bucket
}

output "bucket_arn" {
  description = "ARN of the private lab S3 bucket"
  value       = aws_s3_bucket.this.arn
}
