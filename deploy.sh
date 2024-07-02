#!/bin/bash

set -e

handle_error() {
    echo "Error occurred in script at line: ${1}."
    echo "Line exited with status: ${2}"
}

trap 'handle_error ${LINENO} $?' ERR

# Check for required tools
command -v doctl >/dev/null 2>&1 || { echo "doctl is required but it's not installed. Aborting." >&2; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "docker is required but it's not installed. Aborting." >&2; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "kubectl is required but it's not installed. Aborting." >&2; exit 1; }

# Variables - replace these with your actual values
DO_CONTAINER_REGISTRY="registry.digitalocean.com/indiecloud"
K8S_CLUSTER_NAME="indiecloud"
NAMESPACE="default"
QUIPUBASE_IMAGE="quipubase"
QUIPUBASE_TAG="latest"
QUIPUBASE_STORAGE_CLASS="quipu-storage"
DOMAIN="db.indiecloud.co"

# Log in to the container registry
echo "Logging into DigitalOcean Container Registry..."
doctl registry login

# Build, tag, and push quipubase image
echo "Building, tagging, and pushing $QUIPUBASE_IMAGE image..."
docker build -t $DO_CONTAINER_REGISTRY/$QUIPUBASE_IMAGE:$QUIPUBASE_TAG .
docker push $DO_CONTAINER_REGISTRY/$QUIPUBASE_IMAGE:$QUIPUBASE_TAG

# Get Kubernetes cluster credentials
echo "Fetching Kubernetes cluster credentials..."
doctl kubernetes cluster kubeconfig save $K8S_CLUSTER_NAME

# Verify connection to the cluster
echo "Verifying connection to Kubernetes cluster..."
kubectl cluster-info

# Create namespace
kubectl create namespace $NAMESPACE || echo "Namespace $NAMESPACE already exists."

# Create a temporary Kubernetes manifest file
TEMP_K8S_MANIFEST=$(mktemp)

# Write the provided Kubernetes manifest to the temporary file
cat <<EOF > $TEMP_K8S_MANIFEST
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: $QUIPUBASE_STORAGE_CLASS
provisioner: dobs.csi.digitalocean.com
parameters:
  csi.storage.k8s.io/fstype: ext4
reclaimPolicy: Delete
volumeBindingMode: Immediate

---

apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: $NAMESPACE
  namespace: default
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: $QUIPUBASE_STORAGE_CLASS

---

apiVersion: apps/v1
kind: Deployment
metadata:
  name: quipubase
  namespace: $NAMESPACE
spec:
  replicas: 1
  selector:
    matchLabels:
      app: quipubase
  template:
    metadata:
      labels:
        app: quipubase
    spec:
      containers:
      - name: quipubase
        image: $DO_CONTAINER_REGISTRY/$QUIPUBASE_IMAGE:$QUIPUBASE_TAG
        ports:
        - containerPort: 80
        volumeMounts:
        - mountPath: /app/db
          name: quipu-storage
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
      volumes:
      - name: quipu-storage
        persistentVolumeClaim:
          claimName: quipubase-pvc

---

apiVersion: v1
kind: Service
metadata:
  name: quipubase-service
  namespace: $NAMESPACE
spec:
  selector:
    app: quipubase
  ports:
    - protocol: TCP
      port: 80
  type: LoadBalancer

EOF

# Apply Kubernetes manifest
echo "Applying Kubernetes manifest..."
kubectl apply -f $TEMP_K8S_MANIFEST

# Remove the temporary Kubernetes manifest file
rm $TEMP_K8S_MANIFEST

# Wait for deployment to be ready
echo "Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=600s deployment/quipubase -n $NAMESPACE

echo "Script execution completed successfully."
