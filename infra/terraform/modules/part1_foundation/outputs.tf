# SPDX-License-Identifier: MIT

output "project_id" {
  description = "DigitalOcean project identifier."
  value       = module.network.project_id
}

output "vpc_id" {
  description = "Private VPC identifier."
  value       = module.network.vpc_id
}

output "postgres_id" {
  description = "Managed PostgreSQL cluster identifier."
  value       = module.managed_data.postgres_id
}

output "postgres_private_host" {
  description = "Private PostgreSQL hostname; no credentials are included."
  value       = module.managed_data.postgres_private_host
}

output "postgres_port" {
  description = "PostgreSQL connection port."
  value       = module.managed_data.postgres_port
}

output "valkey_id" {
  description = "Managed Valkey cluster identifier."
  value       = module.managed_data.valkey_id
}

output "valkey_private_host" {
  description = "Private Valkey hostname; no credentials are included."
  value       = module.managed_data.valkey_private_host
}

output "valkey_port" {
  description = "Valkey connection port."
  value       = module.managed_data.valkey_port
}

output "spaces_bucket_name" {
  description = "Private Spaces bucket name."
  value       = module.object_storage.bucket_name
}

output "spaces_bucket_domain_name" {
  description = "Private Spaces bucket domain."
  value       = module.object_storage.bucket_domain_name
}

output "registry_name" {
  description = "Container registry name."
  value       = module.registry.registry_name
}

output "registry_endpoint" {
  description = "Container registry endpoint."
  value       = module.registry.registry_endpoint
}
