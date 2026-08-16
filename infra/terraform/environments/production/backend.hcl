# SPDX-License-Identifier: MIT
# Stub only. Production must not use local state; verify locking before use.

bucket                      = "replace-with-production-state-bucket"
key                         = "halcyon/part1/production/terraform.tfstate"
region                      = "us-east-1"
endpoint                    = "https://replace-with-approved-s3-compatible-endpoint"
encrypt                     = true
skip_credentials_validation = true
skip_region_validation      = true
skip_metadata_api_check     = true
skip_requesting_account_id  = true
force_path_style            = false
