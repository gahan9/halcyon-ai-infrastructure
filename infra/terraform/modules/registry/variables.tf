# SPDX-License-Identifier: MIT

variable "registry_name" {
  description = "Globally unique DigitalOcean container registry name."
  type        = string
}

variable "region" {
  description = "DigitalOcean registry region slug."
  type        = string
}

variable "subscription_tier_slug" {
  description = "Container registry subscription tier."
  type        = string
  default     = "starter"
}
