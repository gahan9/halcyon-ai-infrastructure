# SPDX-License-Identifier: MIT

terraform {
  required_version = ">= 1.5.0, < 2.0.0"

  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = ">= 2.45.0, < 3.0.0"
    }
  }

  # First staging exercise uses local state. Re-enable the S3-compatible
  # backend (see backend.hcl) once an encrypted remote backend is approved.
  # backend "s3" {}
}
