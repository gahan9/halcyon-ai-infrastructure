# SPDX-License-Identifier: MIT

module "part1_foundation" {
  source = "../../modules/part1_foundation"

  project_name                    = var.project_name
  environment                     = "production"
  region                          = var.region
  vpc_ip_range                    = var.vpc_ip_range
  postgres_version                = var.postgres_version
  postgres_size                   = var.postgres_size
  postgres_standby_count          = var.postgres_standby_count
  postgres_storage_size_mib       = var.postgres_storage_size_mib
  valkey_version                  = var.valkey_version
  valkey_size                     = var.valkey_size
  valkey_standby_count            = var.valkey_standby_count
  spaces_bucket_name              = var.spaces_bucket_name
  spaces_force_destroy            = false
  registry_name                   = var.registry_name
  registry_subscription_tier_slug = var.registry_subscription_tier_slug
}
