output "eks_cluster_name" {
  value       = aws_eks_cluster.main.name
  description = "EKS Cluster Name"
}

output "eks_cluster_endpoint" {
  value       = aws_eks_cluster.main.endpoint
  description = "EKS Cluster API Endpoint"
}

output "eks_node_group_name" {
  value       = aws_eks_node_group.default.node_group_name
  description = "Node Group Name"
}
