variable "project" {
  type    = string
  default = "css-portfolio"
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
  type    = string
  default = "acrcssportfoliodevnttm3u.azurecr.io/portfolio-analyzer:v3"
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
    workload = "portfolio-analyzer"
    owner    = "interview-demo"
  }
}
