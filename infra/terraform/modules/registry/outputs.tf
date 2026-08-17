# SPDX-License-Identifier: MIT

output "registry_name" {
  description = "Container registry name."
  value       = digitalocean_container_registry.this.name
}

output "registry_endpoint" {
  description = "Container registry endpoint; credentials are intentionally excluded."
  value       = digitalocean_container_registry.this.endpoint
}
