# SPDX-License-Identifier: MIT

output "project_id" {
  description = "DigitalOcean project identifier."
  value       = digitalocean_project.this.id
}

output "vpc_id" {
  description = "VPC identifier used for private service attachment."
  value       = digitalocean_vpc.this.id
}

output "vpc_urn" {
  description = "VPC resource URN."
  value       = digitalocean_vpc.this.urn
}
