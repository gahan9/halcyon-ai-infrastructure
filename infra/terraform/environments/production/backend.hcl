# SPDX-License-Identifier: MIT
# Production remote state on DigitalOcean Spaces (S3-compatible).
# Official shape: https://docs.digitalocean.com/products/spaces/reference/terraform-backend/
# Bootstrap once with: scripts/bootstrap_tf_state.sh
#
# Auth: the s3 backend reads AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY because
# those names belong to the S3 protocol. The values are DigitalOcean Spaces
# keys; no AWS account is involved. Never commit them.

bucket                      = "halcyon-part1-tfstate"
key                         = "halcyon/part1/production/terraform.tfstate"
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
