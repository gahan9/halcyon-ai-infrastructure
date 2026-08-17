# SPDX-License-Identifier: MIT

resource "digitalocean_spaces_bucket" "this" {
  name          = var.bucket_name
  region        = var.region
  acl           = "private"
  force_destroy = var.force_destroy

  lifecycle {
    precondition {
      condition     = var.environment != "production" || !var.force_destroy
      error_message = "Production must not enable force_destroy for object storage."
    }
  }
}
