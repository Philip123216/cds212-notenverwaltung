variable "container_name" {
  type        = string
  description = "Name des Notenverwaltungs-Containers"
  default     = "notenverwaltung-app"
}

variable "image_name" {
  type        = string
  description = "Image-Name"
  default     = "notenverwaltung"
}

variable "image_tag" {
  type        = string
  description = "Tag des Images"
  default     = "local"
}

variable "host_port" {
  type        = number
  description = "Port auf dem Host"
  default     = 8000

  validation {
    condition     = var.host_port > 1024 && var.host_port <= 65535
    error_message = "host_port muss ein unprivilegierter Port zwischen 1025 und 65535 sein."
  }
}

variable "app_version" {
  type        = string
  description = "App-Version"
  default     = "1.0.0-tf"
}
