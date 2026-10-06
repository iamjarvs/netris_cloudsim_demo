###################################################################################################
# Dynamic Allocation Overrides
# Avoids collisions when standard allocations (e.g. 10.0.0.0/8, Public NAT, Public L4LB)
# already exist on the Netris Controller.
###################################################################################################

data "netris_allocation" "private-ip-allocation" {
  name = "Private IP Allocation"
}

# If the private allocation already exists, subnets reference this data source:
# Otherwise, OpenTofu would fail trying to re-create 10.0.0.0/8.
