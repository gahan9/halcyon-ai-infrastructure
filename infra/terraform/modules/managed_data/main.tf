# SPDX-License-Identifier: MIT

resource "digitalocean_database_cluster" "postgres" {
  name                 = "${var.name_prefix}-postgres"
  engine               = "pg"
  version              = var.postgres_version
  size                 = var.postgres_size
  region               = var.region
  node_count           = 1 + var.postgres_standby_count
  private_network_uuid = var.vpc_id
  storage_size_mib     = var.postgres_storage_size_mib

  lifecycle {
    precondition {
      condition     = var.environment == "staging" ? var.postgres_standby_count == 0 : var.postgres_standby_count >= 1
      error_message = "Staging PostgreSQL must be single-node; production requires at least one standby."
    }
  }
}

resource "digitalocean_database_cluster" "valkey" {
  name                 = "${var.name_prefix}-valkey"
  engine               = "valkey"
  version              = var.valkey_version
  size                 = var.valkey_size
  region               = var.region
  node_count           = 1 + var.valkey_standby_count
  private_network_uuid = var.vpc_id

  lifecycle {
    precondition {
      condition     = var.environment == "staging" ? var.valkey_standby_count == 0 : var.valkey_standby_count >= 1
      error_message = "Staging Valkey must be single-node; production requires at least one standby."
    }
  }
}
