# SPDX-License-Identifier: MIT

variable "project_name" {
  description = "DigitalOcean project name."
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
