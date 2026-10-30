terraform {
  required_version = ">= 1.5.0"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

resource "docker_network" "grades" {
  name = "${var.container_name}-net"
}

resource "docker_volume" "grades_data" {
  name = "${var.container_name}-data"
}

resource "docker_image" "grades" {
  name         = "${var.image_name}:${var.image_tag}"
  keep_locally = true
}

resource "docker_container" "grades" {
  name  = var.container_name
  image = docker_image.grades.image_id

  ports {
    internal = 8000
    external = var.host_port
  }

  env = [
    "APP_VERSION=${var.app_version}",
    "LOG_LEVEL=INFO"
  ]

  networks_advanced {
    name = docker_network.grades.name
  }

  volumes {
    volume_name    = docker_volume.grades_data.name
    container_path = "/data"
  }

  restart = "unless-stopped"
}
