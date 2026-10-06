###################################################################################################
#  Netris Terraform Module for 2-tier Nvidia Spectrum-X switch-fabric for GPU cluster use case    #
#  Version: 1.9.1                                                                                 #
###################################################################################################


variable "pnap_ipam_public" {
  type                            = object({
    default_route                   = string
    netris_cloudsim_nat_cidr        = string
    netris_cloudsim_l4lb_cidr       = string
  })
}
