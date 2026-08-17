# SPDX-License-Identifier: MIT

terraform {
  # use_lockfile on the S3-compatible backend requires Terraform 1.10+.
  required_version = ">= 1.10.0, < 2.0.0"

  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = ">= 2.45.0, < 3.0.0"
    }
  }

  # Local state was used for the first staging exercise. After
  # scripts/bootstrap_tf_state.sh, enable the backend and migrate:
  #   terraform init -migrate-state -backend-config=backend.hcl
  # backend "s3" {}
}
