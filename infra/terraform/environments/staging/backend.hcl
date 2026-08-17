# SPDX-License-Identifier: MIT
# Staging remote state (same Spaces bucket as production, separate key).
# First staging exercise used local state; migrate after bootstrap:
#   terraform init -migrate-state -backend-config=backend.hcl

bucket                      = "halcyon-part1-tfstate"
key                         = "halcyon/part1/staging/terraform.tfstate"
region                      = "us-east-1"
encrypt                     = true
use_lockfile                = true
skip_credentials_validation = true
skip_region_validation      = true
skip_metadata_api_check     = true
skip_requesting_account_id  = true
skip_s3_checksum            = true

endpoints = {
  s3 = "https://nyc3.digitaloceanspaces.com"
}
