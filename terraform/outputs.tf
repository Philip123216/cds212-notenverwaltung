output "container_name" {
  description = "Name des laufenden Containers"
  value       = docker_container.grades.name
}

output "app_url" {
  description = "Lokale URL der Notenverwaltung"
  value       = "http://localhost:${var.host_port}"
}
