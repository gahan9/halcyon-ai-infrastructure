# SPDX-License-Identifier: MIT

resource "digitalocean_container_registry" "this" {
  count = var.create_registry ? 1 : 0

  name                   = var.registry_name
  region                 = var.region
  subscription_tier_slug = var.subscription_tier_slug
}

data "digitalocean_container_registry" "existing" {
  count = var.create_registry ? 0 : 1

  name = var.registry_name
}
