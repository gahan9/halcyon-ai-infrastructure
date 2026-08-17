# SPDX-License-Identifier: MIT

variable "project_name" {
  description = "DigitalOcean project and resource name prefix."
  type        = string
}

variable "environment" {
  description = "Deployment environment."
  type        = string

  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "Environment must be staging or production."
  }
}

variable "region" {
  description = "DigitalOcean region slug."
  type        = string
}

variable "vpc_ip_range" {
  description = "Private RFC1918 CIDR assigned to the VPC."
  type        = string
}

variable "postgres_version" {
  description = "Managed PostgreSQL major version."
  type        = string
  default     = "16"
}

variable "postgres_size" {
  description = "Managed PostgreSQL size slug."
  type        = string
}

variable "postgres_standby_count" {
  description = "PostgreSQL standby count; production requires at least one."
  type        = number
}

variable "postgres_storage_size_mib" {
  description = "PostgreSQL storage allocation in MiB."
  type        = number
}

variable "valkey_version" {
  description = "Managed Valkey major version."
  type        = string
  default     = "8"
}

variable "valkey_size" {
  description = "Managed Valkey size slug."
  type        = string
}

variable "valkey_standby_count" {
  description = "Valkey standby count; production requires at least one."
  type        = number
}

variable "spaces_bucket_name" {
  description = "Globally unique private Spaces bucket name."
  type        = string
}

variable "spaces_force_destroy" {
  description = "Allow deletion of a non-empty Spaces bucket."
  type        = bool
  default     = false
}

variable "registry_name" {
  description = "Globally unique container registry name."
  type        = string
}

variable "registry_subscription_tier_slug" {
  description = "Container registry subscription tier."
  type        = string
  default     = "starter"
}
