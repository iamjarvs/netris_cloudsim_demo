###################################################################################################
# Global Unique Naming Overrides for Multi-DC Deployments
# In Netris, all Hardware (switches, softgates, servers) and Profiles must have
# globally unique names across the entire controller, even in different Sites.
###################################################################################################

locals {
  dc_prefix = lower(var.site-name)
}
