
provider "vsphere" {
  user           = "${var.vsphere_user}"
  password       = "${var.vsphere_password}"
  vsphere_server = "${var.vsphere_server}"
  # if you have a self-signed cert
  allow_unverified_ssl = true
}

# Create a virtual machine within the folder
resource "vsphere_virtual_machine" "web" {
  name   = "terraform-web"
  vcpu   = 2
  memory = 4096
  linked_clone = true

  network_interface {
    label = "VM Network"
  }

  disk {
    template = "Templates/CentOS7-Server"
  }
}