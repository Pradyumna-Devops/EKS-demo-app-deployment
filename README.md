🚀 AWS EKS 3-Tier Application Deployment

A hands-on project demonstrating deployment of a containerized 3-tier application on Amazon EKS using Docker, Kubernetes, AWS Load Balancer Controller, EKS Pod Identity, IAM, Amazon EBS CSI, Persistent Volumes, and an AWS Application Load Balancer.

📌 Project Overview

This project demonstrates a complete application flow:

                    Internet
                       |
                       v
              +----------------+
              | AWS ALB        |
              | Application LB |
              +----------------+
                       |
                       v
              +----------------+
              | Kubernetes     |
              | Ingress        |
              +----------------+
                       |
                       v
              +----------------+
              | Frontend       |
              | Nginx          |
              | 3 replicas     |
              +----------------+
                       |
                       | /api/health
                       v
              +----------------+
              | Backend        |
              | Python Flask   |
              | 3+ replicas    |
              +----------------+
                       |
                       | PostgreSQL
                       v
              +----------------+
              | PostgreSQL     |
              | 1 replica      |
              | Persistent PVC |
              +----------------+
                       |
                       v
              +----------------+
              | AWS EBS gp3    |
              | 5 GiB          |
              +----------------+
Application Components
Layer	Technology
Frontend	Nginx
Backend	Python Flask
Database	PostgreSQL 16
Containers	Docker
Orchestration	Amazon EKS
Ingress	AWS Load Balancer Controller
Load Balancer	AWS Application Load Balancer
Storage	Kubernetes PVC + AWS EBS gp3
CSI	AWS EBS CSI Driver
IAM	EKS Pod Identity
Package Manager	Helm
Container Registry	Docker Hub
📁 Repository Structure
EKS-demo-app-deployment/
│
├── backend/
│   ├── Dockerfile
│   ├── app.py
│   └── requirements.txt
│
├── frontend/
│   ├── Dockerfile
│   ├── index.html
│   └── nginx.conf
│
├── database/
│   └── ...
│
├── k8s/
│   ├── backend.yaml
│   ├── frontend.yaml
│   ├── postgres.yaml
│   └── ingress.yaml
│
└── README.md
☁️ EKS Environment

Cluster:

k8-demo-cluster

Region:

ap-south-1

Node group:

3 x t3.medium

The EKS cluster contains the required Kubernetes system components including:

CoreDNS
kube-proxy
VPC CNI
Metrics Server
EKS Pod Identity Agent
AWS Load Balancer Controller
AWS EBS CSI Driver
1️⃣ Clone the Repository
git clone https://github.com/Pradyumna-Devops/EKS-demo-app-deployment.git

cd EKS-demo-app-deployment

Verify the repository:

ls -la
2️⃣ Validate Kubernetes Manifests

Before applying a manifest, validate it using client-side dry run:

kubectl apply --dry-run=client -f k8s/ingress.yaml

Expected:

ingress.networking.k8s.io/demo-app-ingress created (dry run)

This is useful for catching YAML and Kubernetes manifest problems before changing the cluster.

3️⃣ Docker Image Build
Backend

Build the Python Flask backend:

cd backend

docker build -t eks-demo-backend:1.0 .

Verify:

docker images

Test locally:

docker run -d \
  --name eks-demo-backend \
  -p 5000:5000 \
  eks-demo-backend:1.0

Verify:

docker ps

Test the API:

curl http://localhost:5000/api/

Expected:

{
  "application": "EKS 3-Tier Demo",
  "message": "Hello from Python Flask Backend!"
}
4️⃣ Push Docker Images to Docker Hub

Tag the images:

docker tag eks-demo-backend:1.0 \
  pddevops1998/eks-demo-backend:1.0

docker tag eks-demo-frontend:1.0 \
  pddevops1998/eks-demo-frontend:1.0

Verify:

docker images | grep pddevops1998

Login:

docker login -u pddevops1998

Push backend:

docker push pddevops1998/eks-demo-backend:1.0

Push frontend:

docker push pddevops1998/eks-demo-frontend:1.0

Docker Hub:

https://hub.docker.com/repositories/pddevops1998

5️⃣ AWS Load Balancer Controller

The AWS Load Balancer Controller is responsible for watching Kubernetes resources such as Ingress and creating/managing AWS load balancing resources.

In this project:

Kubernetes Ingress
        |
        v
AWS Load Balancer Controller
        |
        v
AWS Application Load Balancer
        |
        v
Frontend Service

The controller requires AWS IAM permissions because it needs to call AWS APIs to create and manage ALB-related resources.

AWS documents the controller IAM policy as AWSLoadBalancerControllerIAMPolicy.

6️⃣ AWS Load Balancer Controller Service Account

Create the service account:

kubectl create serviceaccount \
  aws-load-balancer-controller \
  -n kube-system

Verify:

kubectl get serviceaccount \
  aws-load-balancer-controller \
  -n kube-system

Expected:

NAME                           SECRETS   AGE
aws-load-balancer-controller   0         ...
7️⃣ IAM Permissions for AWS Load Balancer Controller

The controller needs permission to interact with AWS services required for load balancing.

The IAM policy is responsible for permissions related to resources such as:

Application Load Balancers
Target Groups
Listeners
Security groups
EC2/VPC information
Subnets
Network interfaces
AWS resource tagging

The important concept is:

Kubernetes ServiceAccount
        |
        v
EKS Pod Identity
        |
        v
IAM Role
        |
        v
AWSLoadBalancerControllerIAMPolicy
        |
        v
AWS APIs

AWS's current documentation provides the controller policy and recommends using IAM permissions specifically for the controller rather than giving the worker nodes broad permissions.

8️⃣ EKS Pod Identity

This project uses EKS Pod Identity rather than relying on the worker node's IAM permissions.

The cluster already has the EKS Pod Identity Agent:

kubectl get pods -n kube-system | grep pod-identity

Expected:

eks-pod-identity-agent-...   1/1   Running

The architecture is:

Pod
 |
 | ServiceAccount
 v
EKS Pod Identity Agent
 |
 v
IAM Role
 |
 v
AWS Permissions

This provides a cleaner separation between:

Kubernetes workload
        ↓
Specific IAM role
        ↓
Specific AWS permissions
9️⃣ Verify AWS Load Balancer Controller

After deployment:

kubectl get pods \
  -n kube-system \
  -l app.kubernetes.io/name=aws-load-balancer-controller

Expected:

aws-load-balancer-controller-...   1/1   Running
aws-load-balancer-controller-...   1/1   Running

Verify the deployment:

kubectl get deployment \
  aws-load-balancer-controller \
  -n kube-system

Expected:

READY   UP-TO-DATE   AVAILABLE
2/2     2            2
🔟 EBS CSI Driver

PostgreSQL requires persistent storage.

The EKS cluster initially had:

kubectl get storageclass

Result:

gp2   kubernetes.io/aws-ebs

The AWS EBS CSI driver was then enabled as an EKS add-on.

Check:

aws eks list-addons \
  --cluster-name k8-demo-cluster \
  --region ap-south-1

The EBS CSI driver was added to the cluster.

1️⃣1️⃣ EBS CSI Driver IAM Policy

The EBS CSI driver needs AWS permissions to manage EBS resources.

The policy used during this deployment was:

AmazonEBSCSIDriverPolicy

ARN:

arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy

Verify:

aws iam get-policy \
  --policy-arn \
  arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy

AWS describes this policy as allowing the CSI driver to make EC2/EBS-related API calls on behalf of the Kubernetes workload.

1️⃣2️⃣ EBS CSI Controller Service Account

Check the service account used by the EBS CSI controller:

kubectl get deployment ebs-csi-controller \
  -n kube-system \
  -o jsonpath='{.spec.template.spec.serviceAccountName}{"\n"}'

Result:

ebs-csi-controller-sa

Verify:

kubectl get serviceaccount \
  ebs-csi-controller-sa \
  -n kube-system \
  -o yaml
1️⃣3️⃣ Create EBS CSI Pod Identity Association

The EBS CSI controller was associated with an IAM role using:

eksctl create podidentityassociation \
  --cluster k8-demo-cluster \
  --region ap-south-1 \
  --namespace kube-system \
  --service-account-name ebs-csi-controller-sa \
  --permission-policy-arns \
  arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy

eksctl created the IAM role and Pod Identity association.

Verify:

aws eks list-pod-identity-associations \
  --cluster-name k8-demo-cluster \
  --region ap-south-1

The association should show:

namespace: kube-system
serviceAccount: ebs-csi-controller-sa
1️⃣4️⃣ EBS CSI Controller Troubleshooting

Initially:

kubectl get pods -n kube-system | grep ebs-csi

showed:

ebs-csi-controller-...   1/6   CrashLoopBackOff
ebs-csi-controller-...   1/6   CrashLoopBackOff

At the same time:

ebs-csi-node-...   3/3   Running

The controller was failing because the required AWS permissions were not yet available to the controller service account.

After creating the Pod Identity association, restart the controller:

kubectl rollout restart deployment \
  ebs-csi-controller \
  -n kube-system

Check rollout:

kubectl rollout status deployment \
  ebs-csi-controller \
  -n kube-system

Final result:

deployment "ebs-csi-controller" successfully rolled out

Verify:

kubectl get pods -n kube-system | grep ebs-csi

Final:

ebs-csi-controller-...   6/6   Running
ebs-csi-controller-...   6/6   Running
ebs-csi-node-...         3/3   Running
ebs-csi-node-...         3/3   Running
ebs-csi-node-...         3/3   Running

Finally:

aws eks describe-addon \
  --cluster-name k8-demo-cluster \
  --addon-name aws-ebs-csi-driver \
  --region ap-south-1 \
  --query 'addon.status'

Result:

"ACTIVE"
1️⃣5️⃣ PostgreSQL Deployment

The PostgreSQL manifest contains several Kubernetes resources:

Secret
PersistentVolumeClaim
Deployment
ConfigMap
Service

The PostgreSQL database uses:

postgres:16

and:

replicas: 1

The PVC requests:

5Gi

with:

ReadWriteOnce

and:

storageClassName: gp3

The current manifest also sets:

PGDATA=/var/lib/postgresql/data/pgdata

which was important for solving the PostgreSQL initialization problem.

1️⃣6️⃣ PostgreSQL PVC Issue

Initially:

kubectl get pvc -n demo-app

showed:

postgres-pvc   Pending

Describe:

kubectl describe pvc postgres-pvc \
  -n demo-app

The important event was:

no persistent volumes available for this claim
and no storage class is set

The problem was that the PVC did not specify a StorageClass.

After configuring the gp3 StorageClass:

kubectl get storageclass

result:

gp3   ebs.csi.aws.com

The PVC became:

postgres-pvc   Bound   ...   5Gi   RWO   gp3
1️⃣7️⃣ PostgreSQL CrashLoopBackOff

After the PVC was successfully attached, PostgreSQL entered:

CrashLoopBackOff

Check:

kubectl get pods -n demo-app

Then inspect:

kubectl describe pod \
  -n demo-app \
  <postgres-pod>

Logs:

kubectl logs \
  -n demo-app \
  <postgres-pod>

The important error was:

initdb: error: directory "/var/lib/postgresql/data"
exists but is not empty

It contains a lost+found directory

This happens because the EBS filesystem mount contains the filesystem's lost+found directory.

Fix

Instead of using the mount point directly as PostgreSQL's data directory, the deployment was configured with:

env:
  - name: PGDATA
    value: /var/lib/postgresql/data/pgdata

The volume remains mounted at:

/var/lib/postgresql/data

but PostgreSQL stores its actual database files under:

/var/lib/postgresql/data/pgdata

After applying the corrected configuration:

kubectl apply -f k8s/postgres.yaml

PostgreSQL initialized successfully.

1️⃣8️⃣ PostgreSQL Initialization

The ConfigMap contains the initialization SQL.

The database creates a users table and inserts demo records.

The flow is:

PostgreSQL container starts
        |
        v
PGDATA directory initialized
        |
        v
/docker-entrypoint-initdb.d/init.sql
        |
        v
Database/table initialization
        |
        v
PostgreSQL starts normally

Verify:

kubectl logs -n demo-app <postgres-pod>

The final log included:

PostgreSQL ... database system is ready to accept connections
1️⃣9️⃣ Backend Deployment

The backend deployment uses:

pddevops1998/eks-demo-backend:1.0

and initially runs:

replicas: 3

The backend exposes:

5000

The Kubernetes service is:

backend-service

with:

ClusterIP

The backend connects to PostgreSQL using:

DB_HOST=postgres-service
DB_PORT=5432

The database credentials are loaded from the Kubernetes Secret rather than hard-coded directly into the Deployment.

Apply:

kubectl apply -f k8s/backend.yaml

Verify:

kubectl get pods \
  -n demo-app \
  -l app=backend
2️⃣0️⃣ Backend Service Testing

Check:

kubectl get svc \
  backend-service \
  -n demo-app

Expected:

backend-service   ClusterIP   ...   5000/TCP

Test from inside Kubernetes:

kubectl run test-curl \
  -n demo-app \
  --rm -it \
  --image=curlimages/curl:8.10.1 \
  --restart=Never \
  -- curl -v http://backend-service:5000/api/

Expected response:

{
  "application": "EKS 3-Tier Demo",
  "message": "Hello from Python Flask Backend!"
}

Verify service endpoints:

kubectl get endpoints \
  backend-service \
  -n demo-app

For newer Kubernetes versions, EndpointSlice can also be checked:

kubectl get endpointslice \
  -n demo-app \
  -l kubernetes.io/service-name=backend-service
2️⃣1️⃣ Frontend Deployment

The frontend runs on Nginx.

Image:

pddevops1998/eks-demo-frontend:1.0

The frontend deployment runs multiple replicas and is exposed internally using:

frontend-service

Service type:

ClusterIP

Port:

80

Test:

kubectl get svc frontend-service \
  -n demo-app

Then:

kubectl run test-frontend \
  -n demo-app \
  --rm -it \
  --image=curlimages/curl:8.10.1 \
  --restart=Never \
  -- curl -v http://frontend-service/

The Nginx frontend returned HTTP 200.

2️⃣2️⃣ Frontend → Backend Testing

The frontend exposes:

/api/health

Test:

kubectl run test-api \
  -n demo-app \
  --rm -it \
  --image=curlimages/curl:8.10.1 \
  --restart=Never \
  -- curl -v http://frontend-service/api/health

Expected:

{
  "message": "Backend and database are connected",
  "status": "healthy"
}

This verified the complete internal application path:

Frontend Nginx
      |
      v
Backend Service
      |
      v
Flask Backend
      |
      v
PostgreSQL
2️⃣3️⃣ AWS Load Balancer Controller Ingress

The project uses:

k8s/ingress.yaml

The important configuration is:

apiVersion: networking.k8s.io/v1
kind: Ingress

metadata:
  name: demo-app-ingress
  namespace: demo-app

  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP":80}]'

spec:
  ingressClassName: alb

  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80

This tells the AWS Load Balancer Controller to create an internet-facing ALB and route traffic to the frontend service. The current repository contains these exact annotations and routing settings.

2️⃣4️⃣ Validate Ingress

Dry run:

kubectl apply \
  --dry-run=client \
  -f k8s/ingress.yaml

Apply:

kubectl apply \
  -f k8s/ingress.yaml

Verify:

kubectl get ingress \
  -n demo-app

Expected:

NAME               CLASS   HOSTS   ADDRESS
demo-app-ingress   alb     *       k8s-demoapp-...
2️⃣5️⃣ ALB Verification

Get the ALB:

aws elbv2 describe-load-balancers \
  --region ap-south-1 \
  --query 'LoadBalancers[?Type==`application`].[LoadBalancerName,DNSName,State.Code]' \
  --output table

The ALB showed:

State: active

Verify Kubernetes:

kubectl get ingress \
  demo-app-ingress \
  -n demo-app \
  -o wide
2️⃣6️⃣ ALB DNS Troubleshooting

Initially:

curl -I http://<ALB-DNS>

returned:

Could not resolve host

DNS lookup:

nslookup <ALB-DNS>

returned:

NXDOMAIN

Instead of assuming the ALB was broken, the ALB was independently verified using AWS CLI:

aws elbv2 describe-load-balancers \
  --region ap-south-1

The ALB was confirmed:

active

Then DNS was tested using an external DNS resolver:

nslookup <ALB-DNS> 8.8.8.8

The ALB resolved successfully.

The returned IP addresses were then tested directly:

curl -I http://<ALB-IP>

Result:

HTTP/1.1 200 OK
Server: nginx

Then:

curl http://<ALB-IP>/api/health

Returned:

{
  "message": "Backend and database are connected",
  "status": "healthy"
}

This confirmed that the complete application path through the ALB was working.

2️⃣7️⃣ Final Application Flow

The final traffic flow is:

User / Browser
      |
      | HTTP :80
      v
AWS Application Load Balancer
      |
      | Kubernetes Ingress
      v
AWS Load Balancer Controller
      |
      v
frontend-service
      |
      v
Nginx Frontend Pods
      |
      | /api/health
      v
backend-service
      |
      v
Python Flask Backend Pods
      |
      | PostgreSQL :5432
      v
postgres-service
      |
      v
PostgreSQL
      |
      v
Kubernetes PVC
      |
      v
AWS EBS gp3
2️⃣8️⃣ End-to-End Testing
Frontend
kubectl get pods \
  -n demo-app \
  -l app=frontend

Result:

3/3 Running
Backend
kubectl get pods \
  -n demo-app \
  -l app=backend

Result:

3/3 Running
PostgreSQL
kubectl get pods \
  -n demo-app \
  -l app=postgres

Result:

1/1 Running
PVC
kubectl get pvc \
  -n demo-app

Result:

postgres-pvc   Bound   ...   5Gi   RWO   gp3
Ingress
kubectl get ingress \
  -n demo-app

Result:

demo-app-ingress   alb   *   <ALB-DNS>
2️⃣9️⃣ Kubernetes Self-Healing Test

To verify Kubernetes self-healing, one backend pod was intentionally deleted:

kubectl delete pod \
  backend-dff95d5c8-h826l \
  -n demo-app

Immediately check:

kubectl get pods \
  -n demo-app | grep backend

Kubernetes automatically created a replacement pod.

Example:

backend-...   1/1   Running
backend-...   1/1   Running
backend-...   1/1   Running

This demonstrated Kubernetes ReplicaSet/Deployment self-healing.

3️⃣0️⃣ Backend Scaling Test

The backend was initially configured with 3 replicas.

Scale to 5:

kubectl scale deployment backend \
  -n demo-app \
  --replicas=5

Verify:

kubectl get pods \
  -n demo-app | grep backend

Final result:

5 backend pods
5/5 Running

This demonstrated Kubernetes horizontal replica scaling.

3️⃣1️⃣ Continuous Health Testing

The ALB endpoint was continuously tested:

while true; do
  date
  curl -s http://<ALB-IP>/api/health
  echo
  sleep 2
done

Repeated responses:

{
  "message": "Backend and database are connected",
  "status": "healthy"
}

During this test, a backend pod was deleted intentionally.

The application continued serving successful health responses because Kubernetes replaced the failed pod and the Service continued routing traffic to healthy backend endpoints.

3️⃣2️⃣ Final Kubernetes Status

Final application status:

Frontend:
3/3 Running

Backend:
3/3 Running

PostgreSQL:
1/1 Running

PVC:
Bound

StorageClass:
gp3

Ingress:
ALB

AWS Load Balancer Controller:
Running

EBS CSI Controller:
Running

EBS CSI Add-on:
ACTIVE

System components were also verified:

kubectl get pods -n kube-system

Important components:

aws-load-balancer-controller    Running
ebs-csi-controller               Running
ebs-csi-node                     Running
eks-pod-identity-agent           Running
coredns                          Running
kube-proxy                       Running
aws-node                         Running
metrics-server                   Running
3️⃣3️⃣ Important Kubernetes Commands Used
Cluster
kubectl get nodes
kubectl get pods -A
kubectl get pods -n kube-system
Application
kubectl get all -n demo-app
kubectl get pods -n demo-app
kubectl get svc -n demo-app
Storage
kubectl get storageclass
kubectl get pvc -n demo-app
kubectl describe pvc postgres-pvc -n demo-app
Logs
kubectl logs -n demo-app <pod-name>
Troubleshooting
kubectl describe pod -n demo-app <pod-name>
kubectl describe pvc -n demo-app postgres-pvc
Ingress
kubectl get ingress -n demo-app
kubectl get ingress demo-app-ingress -n demo-app -o wide
Services
kubectl get svc -n demo-app
kubectl get endpoints -n demo-app
kubectl get endpointslice -n demo-app
Deployment
kubectl get deployment -n demo-app
kubectl rollout status deployment backend -n demo-app
Scaling
kubectl scale deployment backend \
  -n demo-app \
  --replicas=5
Self-healing
kubectl delete pod <pod-name> -n demo-app
3️⃣4️⃣ Useful AWS Commands
EKS Add-ons
aws eks list-addons \
  --cluster-name k8-demo-cluster \
  --region ap-south-1
EBS CSI Add-on
aws eks describe-addon \
  --cluster-name k8-demo-cluster \
  --addon-name aws-ebs-csi-driver \
  --region ap-south-1 \
  --query 'addon.status'

Expected:

ACTIVE
IAM Policy
aws iam get-policy \
  --policy-arn \
  arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy
Pod Identity
aws eks list-pod-identity-associations \
  --cluster-name k8-demo-cluster \
  --region ap-south-1
ALB
aws elbv2 describe-load-balancers \
  --region ap-south-1 \
  --query 'LoadBalancers[?Type==`application`].[LoadBalancerName,DNSName,State.Code]' \
  --output table
3️⃣5️⃣ Key Troubleshooting Lessons
Lesson 1 — Always check the PVC

When a pod is Pending, don't immediately troubleshoot the container.

First check:

kubectl describe pod ...
kubectl get pvc
kubectl describe pvc ...
kubectl get storageclass

The PostgreSQL pod was blocked because its PVC had no StorageClass.

Lesson 2 — Check application logs after scheduling succeeds

Once the PVC was fixed, PostgreSQL was scheduled but entered:

CrashLoopBackOff

The actual problem was only visible in:

kubectl logs

The lost+found directory caused PostgreSQL initdb to reject the mount point.

Lesson 3 — IAM is critical for AWS-integrated Kubernetes components

The EBS CSI controller initially failed because its service account did not have the required AWS permissions.

The solution was:

IAM Policy
    ↓
IAM Role
    ↓
EKS Pod Identity Association
    ↓
Kubernetes ServiceAccount
    ↓
EBS CSI Controller

After the association was created and the controller restarted, the pods became healthy and the EBS CSI add-on eventually reached:

ACTIVE
Lesson 4 — Don't assume an ALB is broken because DNS fails

The ALB was:

ACTIVE

but the EC2 environment initially returned:

NXDOMAIN

The troubleshooting process was:

DNS failure
     ↓
Check Kubernetes Ingress
     ↓
Check ALB using AWS CLI
     ↓
Confirm ALB ACTIVE
     ↓
Test external DNS resolver
     ↓
Resolve ALB
     ↓
Test ALB IP
     ↓
HTTP 200
     ↓
/api/health = healthy

This is a good example of troubleshooting each layer independently.

3️⃣6️⃣ Overall Architecture and IAM Flow

The project uses two important AWS-integrated Kubernetes controllers.

AWS Load Balancer Controller
Ingress
   |
   v
AWS Load Balancer Controller
   |
   | EKS Pod Identity
   v
IAM Role
   |
   | AWSLoadBalancerControllerIAMPolicy
   v
AWS ELB / EC2 / VPC APIs
   |
   v
Application Load Balancer
EBS CSI Controller
PersistentVolumeClaim
   |
   v
EBS CSI Controller
   |
   | EKS Pod Identity
   v
IAM Role
   |
   | AmazonEBSCSIDriverPolicy
   v
AWS EC2 / EBS APIs
   |
   v
EBS gp3 Volume

This separation allows each controller to receive the AWS permissions required for its specific function.

3️⃣7️⃣ Final Result

The final application successfully demonstrated:

✅ Docker containerization
✅ Docker Hub image publishing
✅ Amazon EKS deployment
✅ Kubernetes Deployments
✅ Kubernetes Services
✅ Kubernetes Secrets
✅ Kubernetes ConfigMaps
✅ PostgreSQL deployment
✅ PersistentVolumeClaim
✅ AWS EBS gp3 storage
✅ AWS EBS CSI Driver
✅ EKS Pod Identity
✅ IAM roles and policies
✅ AWS Load Balancer Controller
✅ Kubernetes Ingress
✅ AWS Application Load Balancer
✅ Frontend → Backend communication
✅ Backend → PostgreSQL communication
✅ ALB → Frontend routing
✅ Kubernetes self-healing
✅ Deployment scaling
✅ End-to-end health testing
✅ Troubleshooting and recovery
📚 What I Learned

This project helped me understand the complete flow of a Kubernetes application running on AWS:

Docker
  ↓
Docker Hub
  ↓
Amazon EKS
  ↓
Kubernetes Deployment
  ↓
Kubernetes Service
  ↓
Ingress
  ↓
AWS Load Balancer Controller
  ↓
Application Load Balancer
  ↓
Frontend
  ↓
Backend
  ↓
PostgreSQL
  ↓
PVC
  ↓
AWS EBS

More importantly, this project demonstrated that DevOps is not just about getting a deployment to work.

It is about:

Observe
   ↓
Identify the failure
   ↓
Understand the dependency
   ↓
Troubleshoot each layer
   ↓
Apply the fix
   ↓
Validate
   ↓
Test failure scenarios
   ↓
Prove the application works
