# SPDX-License-Identifier: MIT

module "network" {
  source = "../network"

  project_name = var.project_name
  environment  = var.environment
  region       = var.region
  vpc_ip_range = var.vpc_ip_range
}

module "managed_data" {
  source = "../managed_data"

  name_prefix               = var.project_name
  environment               = var.environment
  region                    = var.region
  vpc_id                    = module.network.vpc_id
  postgres_version          = var.postgres_version
  postgres_size             = var.postgres_size
  postgres_standby_count    = var.postgres_standby_count
  postgres_storage_size_mib = var.postgres_storage_size_mib
  valkey_version            = var.valkey_version
  valkey_size               = var.valkey_size
  valkey_standby_count      = var.valkey_standby_count
}

module "object_storage" {
  source = "../object_storage"

  bucket_name   = var.spaces_bucket_name
  environment   = var.environment
  region        = var.region
  force_destroy = var.spaces_force_destroy
}

module "registry" {
  source = "../registry"

  registry_name          = var.registry_name
  create_registry        = var.create_registry
  region                 = var.region
  subscription_tier_slug = var.registry_subscription_tier_slug
}

resource "digitalocean_project_resources" "foundation" {
  project = module.network.project_id
  # Valkey URNs are rejected by the Projects API resource-type allow-list in
  # some accounts; keep the project assignment to PostgreSQL + Spaces only.
  resources = [
    module.managed_data.postgres_urn,
    module.object_storage.bucket_urn,
  ]
}
