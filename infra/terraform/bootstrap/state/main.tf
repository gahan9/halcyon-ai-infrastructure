# SPDX-License-Identifier: MIT

variable "bucket_name" {
  description = "DigitalOcean Spaces bucket used for Terraform remote state."
  type        = string
}

variable "region" {
  description = "DigitalOcean Spaces region slug."
  type        = string
}

variable "spaces_access_id" {
  description = "Spaces access key id supplied by the WSL doctl bootstrap."
  type        = string
  sensitive   = true
}

variable "spaces_secret_key" {
  description = "Spaces secret key supplied by the WSL doctl bootstrap."
  type        = string
  sensitive   = true
}

provider "digitalocean" {
  # DIGITALOCEAN_TOKEN is read from the environment.
  spaces_access_id  = var.spaces_access_id
  spaces_secret_key = var.spaces_secret_key
}

resource "digitalocean_spaces_bucket" "terraform_state" {
  name          = var.bucket_name
  region        = var.region
  acl           = "private"
  force_destroy = false

  versioning {
    enabled = true
  }

  lifecycle {
    prevent_destroy = true
  }
}

output "bucket_name" {
  description = "Remote-state Spaces bucket name."
  value       = digitalocean_spaces_bucket.terraform_state.name
}
