# SPDX-License-Identifier: MIT

variable "name_prefix" {
  description = "Prefix for managed data resource names."
  type        = string
}

variable "environment" {
  description = "Deployment environment controlling availability validation."
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

variable "vpc_id" {
  description = "VPC UUID for private database networking."
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
  description = "PostgreSQL standby nodes in addition to the primary."
  type        = number

  validation {
    condition     = var.postgres_standby_count >= 0 && floor(var.postgres_standby_count) == var.postgres_standby_count
    error_message = "PostgreSQL standby count must be a non-negative integer."
  }
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
  description = "Valkey standby nodes in addition to the primary."
  type        = number

  validation {
    condition     = var.valkey_standby_count >= 0 && floor(var.valkey_standby_count) == var.valkey_standby_count
    error_message = "Valkey standby count must be a non-negative integer."
  }
}
