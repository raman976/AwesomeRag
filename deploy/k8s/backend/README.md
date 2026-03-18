NST backend deployment steps

1. Build backend image from repo root

docker build -t awesomerag:v1 .

2. Tag for NST local registry

docker tag awesomerag:v1 localhost:30500/awesomerag:v1

3. Push image

docker push localhost:30500/awesomerag:v1

4. SSH into cluster node and go to repo

cd /path/to/AwesomeRag

5. Create namespace and base resources

kubectl apply -f deploy/k8s/backend/namespace.yaml
kubectl apply -f deploy/k8s/backend/configmap.yaml

6. Create secret from env values

kubectl -n awesomerag create secret generic awesomerag-secrets \
 --from-literal=rag_api='YOUR_GROQ_KEY' \
 --from-literal=qd_api_key='YOUR_QDRANT_API_KEY' \
 --from-literal=qd_url='https://1efe5184-73a3-4b29-b8ae-bd3e7e40a020.us-east-1-1.aws.cloud.qdrant.io:6333' \
 --dry-run=client -o yaml | kubectl apply -f -

7. Deploy backend

kubectl apply -f deploy/k8s/backend/deployment.yaml
kubectl apply -f deploy/k8s/backend/service.yaml
kubectl apply -f deploy/k8s/backend/ingress.yaml

8. Verify deployment

kubectl -n awesomerag get pods
kubectl -n awesomerag get svc
kubectl -n awesomerag get ingress
kubectl -n awesomerag logs deploy/awesomerag --tail=100

9. Test from node

curl -i -H "Host: awesomerag.nstsdc.org" http://127.0.0.1/health

10. Point Vercel frontend to backend URL

Set NEXT_PUBLIC_API_BASE_URL to https://awesomerag.nstsdc.org

11. You do not need frontend hosted first

Deploy backend first with localhost origins already in configmap.

12. After frontend is on Vercel, update backend CORS allowlist

Run this command with your Vercel domain:

kubectl -n awesomerag create configmap awesomerag-config \
 --from-literal=ALLOWED_ORIGINS='https://YOUR-PROJECT.vercel.app,http://127.0.0.1:3000,http://localhost:3000' \
 --dry-run=client -o yaml | kubectl apply -f -

kubectl -n awesomerag rollout restart deploy/awesomerag
