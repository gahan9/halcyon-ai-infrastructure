# SPDX-License-Identifier: MIT

resource "digitalocean_project" "this" {
  name        = var.project_name
  description = "Halcyon Part 1 ${var.environment} infrastructure"
  purpose     = "Web Application"
  environment = title(var.environment)
}

resource "digitalocean_vpc" "this" {
  name        = "${var.project_name}-vpc"
  region      = var.region
  ip_range    = var.vpc_ip_range
  description = "Private network for ${var.environment} services"
}
