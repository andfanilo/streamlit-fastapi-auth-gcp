provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_compute_network" "vpc_network" {
  name                    = "sandbox-network"
  auto_create_subnetworks = false
  mtu                     = 1460
}

resource "google_compute_subnetwork" "default" {
  name          = "sandbox-subnet"
  ip_cidr_range = "10.0.1.0/24"
  region        = var.region
  network       = google_compute_network.vpc_network.id
}

resource "google_compute_address" "default" {
  name   = "sandbox-static-ip-address"
  region = var.region
}

resource "google_compute_instance" "default" {
  name         = "sandbox-vm"
  machine_type = var.machine
  zone         = var.zone
  tags         = ["http", "https", "ssh"]
  labels = {
    "environment" : "sandbox"
  }

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
    }
  }

  network_interface {
    subnetwork = google_compute_subnetwork.default.id

    access_config {
      nat_ip = google_compute_address.default.address
    }
  }
}

# SSH Rule
resource "google_compute_firewall" "ssh" {
  name = "sandbox-allow-ssh"

  allow {
    ports    = ["22"]
    protocol = "tcp"
  }

  direction     = "INGRESS"
  network       = google_compute_network.vpc_network.id
  priority      = 1000
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["ssh"]
}

# HTTP Rules
resource "google_compute_firewall" "http-streamlit" {
  name    = "sandbox-allow-http-streamlit"
  network = google_compute_network.vpc_network.id

  allow {
    protocol = "tcp"
    ports    = ["8501"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["http"]
}

resource "google_compute_firewall" "http-fastapi" {
  name    = "sandbox-allow-http-fastapi"
  network = google_compute_network.vpc_network.id

  allow {
    protocol = "tcp"
    ports    = ["8000"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["http"]
}

# HTTPS Rule
resource "google_compute_firewall" "https" {
  name    = "sandbox-allow-https"
  network = google_compute_network.vpc_network.id

  allow {
    protocol = "tcp"
    ports    = ["443"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["https"]
}


output "sandbox-vm-web-url" {
  value = join("", ["https://", google_compute_instance.default.network_interface.0.access_config.0.nat_ip])
}
