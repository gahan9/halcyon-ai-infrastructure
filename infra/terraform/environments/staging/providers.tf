# SPDX-License-Identifier: MIT

variable "spaces_access_id" {
  description = "Spaces access key id (set via TF_VAR_spaces_access_id; never commit)."
  type        = string
  sensitive   = true
  default     = ""
}

variable "spaces_secret_key" {
  description = "Spaces secret key (set via TF_VAR_spaces_secret_key; never commit)."
  type        = string
  sensitive   = true
  default     = ""
}

provider "digitalocean" {
  # DIGITALOCEAN_TOKEN from environment.
  spaces_access_id  = var.spaces_access_id
  spaces_secret_key = var.spaces_secret_key
}
