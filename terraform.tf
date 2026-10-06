###################################################################################################
#  NETRIS Terraform Module for 2-tier Nvidia Spectrum-X switch-fabric for GPU cluster use case    #
#  Version: 1.9.1                                                                                 #
###################################################################################################


terraform {
  required_providers {
    netris                        = {
      source                        = "netrisai/netris"
      version                       = ">=1.0.0"
    }
  }
}

provider "netris" {
  address                         = var.controller_url
  login                           = "netris"               # overwrite env: NETRIS_LOGIN
  password                        = var.netris_controller_password
}

variable "controller_url" {
  type                            = string
}

variable "netris_controller_password" {
  type                            = string
  sensitive                       = true
}

variable "site-name" {
  type                            = string
}

variable "site" {
  type                            = object({
    publicasn                       = number
    rohroutingprofile               = string
    sitemesh                        = string
    acldefaultpolicy                = string
    vlanrangeautoassign             = string
  })
  default                         = {
    publicasn                       = 655001
    acldefaultpolicy                = "permit"
    rohroutingprofile               = "default_agg"
    sitemesh                        = "disabled"
    vlanrangeautoassign             = "2-3999"
  }
}

data "netris_tenant" "admin" {
  name                            = "Admin"
}

resource "netris_site" "site1" {
  name                            = var.site-name
  publicasn                       = var.site.publicasn
  rohasn                          = 65500
  vmasn                           = 65501
  rohroutingprofile               = var.site.rohroutingprofile
  sitemesh                        = var.site.sitemesh
  acldefaultpolicy                = var.site.acldefaultpolicy
  vlanrangeautoassign             = var.site.vlanrangeautoassign
}
