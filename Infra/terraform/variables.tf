variable "aws_region" {
  description = "AWS region to deploy resources."
  type        = string
  default     = "ap-southeast-1"
}

variable "project_name" {
  description = "Project name for tagging."
  type        = string
  default     = "SimpleDevOps"
}

variable "environment" {
  description = "Deployment environment."
  type        = string
  default     = "demo"
}

variable "kubernetes_version" {
  description = "Kubernetes version for EKS."
  type        = string
  default     = "1.27"
}

variable "node_instance_types" {
  description = "EC2 instance types for EKS nodes."
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_desired_size" {
  description = "Desired node count."
  type        = number
  default     = 2
}

variable "node_min_size" {
  description = "Minimum node count."
  type        = number
  default     = 1
}

variable "node_max_size" {
  description = "Maximum node count."
  type        = number
  default     = 2
}
