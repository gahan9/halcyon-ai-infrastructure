# SPDX-License-Identifier: MIT

locals {
  registry_name = var.create_registry ? digitalocean_container_registry.this[0].name : data.digitalocean_container_registry.existing[0].name
  registry_endpoint = var.create_registry ? digitalocean_container_registry.this[0].endpoint : data.digitalocean_container_registry.existing[0].endpoint
}

output "registry_name" {
  description = "Container registry name."
  value       = local.registry_name
}

output "registry_endpoint" {
  description = "Container registry endpoint; credentials are intentionally excluded."
  value       = local.registry_endpoint
}
