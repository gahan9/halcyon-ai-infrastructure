# SPDX-License-Identifier: MIT

output "postgres_id" {
  description = "Managed PostgreSQL cluster identifier."
  value       = digitalocean_database_cluster.postgres.id
}

output "postgres_urn" {
  description = "Managed PostgreSQL resource URN."
  value       = digitalocean_database_cluster.postgres.urn
}

output "postgres_private_host" {
  description = "Private PostgreSQL hostname; credentials are intentionally excluded."
  value       = digitalocean_database_cluster.postgres.private_host
}

output "postgres_port" {
  description = "PostgreSQL connection port."
  value       = digitalocean_database_cluster.postgres.port
}

output "valkey_id" {
  description = "Managed Valkey cluster identifier."
  value       = digitalocean_database_cluster.valkey.id
}

output "valkey_urn" {
  description = "Managed Valkey resource URN."
  value       = digitalocean_database_cluster.valkey.urn
}

output "valkey_private_host" {
  description = "Private Valkey hostname; credentials are intentionally excluded."
  value       = digitalocean_database_cluster.valkey.private_host
}

output "valkey_port" {
  description = "Valkey connection port."
  value       = digitalocean_database_cluster.valkey.port
}
