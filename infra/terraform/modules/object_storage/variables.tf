# SPDX-License-Identifier: MIT

variable "bucket_name" {
  description = "Globally unique private Spaces bucket name."
  type        = string
}

variable "region" {
  description = "DigitalOcean Spaces region slug."
  type        = string
}

variable "environment" {
  description = "Deployment environment controlling deletion safeguards."
  type        = string

  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "Environment must be staging or production."
  }
}

variable "force_destroy" {
  description = "Allow bucket deletion with objects; keep false for production."
  type        = bool
  default     = false
}
