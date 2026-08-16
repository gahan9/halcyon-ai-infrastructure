# SPDX-License-Identifier: MIT

output "bucket_name" {
  description = "Private Spaces bucket name."
  value       = digitalocean_spaces_bucket.this.name
}

output "bucket_urn" {
  description = "Private Spaces bucket resource URN."
  value       = digitalocean_spaces_bucket.this.urn
}

output "bucket_domain_name" {
  description = "Spaces bucket domain; no access credentials are included."
  value       = digitalocean_spaces_bucket.this.bucket_domain_name
}
