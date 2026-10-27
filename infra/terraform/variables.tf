variable "project" {
  type    = string
  default = "example-azure-depot-pdf"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "location" {
  type    = string
  default = "switzerlandnorth"
}

variable "container_image" {
  description = "Container image for Example Azure Depot PDF"
  type        = string
}

variable "postgres_admin" {
  type    = string
  default = "pgadminuser"
}

variable "postgres_sku" {
  type    = string
  default = "B_Standard_B1ms"
}

variable "tags" {
  type = map(string)
  default = {
    workload = "example-azure-depot-pdf"
    owner    = "interview-demo"
  }
}

variable "subscription_id" {
  description = "Azure subscription used for deployment; null uses the Azure CLI context."
  type        = string
  default     = null
}
