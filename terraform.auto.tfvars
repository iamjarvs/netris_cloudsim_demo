###################################################################################################
#  NETRIS Terraform Module for 2-tier Nvidia Spectrum-X switch-fabric for GPU cluster use case    #
#  Version: 1.9.1                                                                                 #
###################################################################################################

netris_controller_password        = "913QGAi6oQTSGgZm20eU"

pnap_ipam_public                  = {
  default_route                   = "0.0.0.0/0"
  netris_cloudsim_nat_cidr        = "103.67.203.24/30"
  netris_cloudsim_l4lb_cidr       = "192.240.193.172/30"
}
