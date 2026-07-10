# Kubernetes Deployment Manifests

```bash
# Create namespace
kubectl create namespace astra

# Apply secrets (create from env files)
kubectl create secret generic astra-secrets \
  --namespace astra \
  --from-literal=secret-key="$(openssl rand -base64 48)" \
  --from-literal=postgres-password="$(openssl rand -base64 24)"

# Apply manifests
kubectl apply -k k8s/
```
