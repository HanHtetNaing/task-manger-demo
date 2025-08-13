terraform {
  required_version = ">= 1.4.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
#   backend "s3" {
#     bucket = "your-tf-state-bucket" # Change to your S3 bucket for state
#     key    = "eks-demo/terraform.tfstate"
#     region = "us-west-2"
#   }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
