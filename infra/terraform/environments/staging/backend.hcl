# SPDX-License-Identifier: MIT
# Stub only. Verify locking, versioning, encryption, and audit controls before use.

bucket                      = "replace-with-staging-state-bucket"
key                         = "halcyon/part1/staging/terraform.tfstate"
region                      = "us-east-1"
endpoint                    = "https://replace-with-approved-s3-compatible-endpoint"
encrypt                     = true
skip_credentials_validation = true
skip_region_validation      = true
skip_metadata_api_check     = true
skip_requesting_account_id  = true
force_path_style            = false
