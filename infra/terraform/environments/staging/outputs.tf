# SPDX-License-Identifier: MIT

output "project_id" {
  value = module.part1_foundation.project_id
}

output "vpc_id" {
  value = module.part1_foundation.vpc_id
}

output "postgres_id" {
  value = module.part1_foundation.postgres_id
}

output "postgres_private_host" {
  value = module.part1_foundation.postgres_private_host
}

output "postgres_port" {
  value = module.part1_foundation.postgres_port
}

output "valkey_id" {
  value = module.part1_foundation.valkey_id
}

output "valkey_private_host" {
  value = module.part1_foundation.valkey_private_host
}

output "valkey_port" {
  value = module.part1_foundation.valkey_port
}

output "spaces_bucket_name" {
  value = module.part1_foundation.spaces_bucket_name
}

output "spaces_bucket_domain_name" {
  value = module.part1_foundation.spaces_bucket_domain_name
}

output "registry_name" {
  value = module.part1_foundation.registry_name
}

output "registry_endpoint" {
  value = module.part1_foundation.registry_endpoint
}
