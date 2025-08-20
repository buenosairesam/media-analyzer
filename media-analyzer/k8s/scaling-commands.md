# Celery Worker Scaling Commands

## Current Analysis Workers

### Logo Detection (ENABLED)
```bash
# Scale up for high load
kubectl scale deployment celery-logo-worker --replicas=4

# Scale down for low load  
kubectl scale deployment celery-logo-worker --replicas=1

# Check status
kubectl get pods -l queue=logo-detection
```

### Visual Analysis (DISABLED for demo)
```bash
# Enable visual analysis
kubectl scale deployment celery-visual-worker --replicas=2

# Disable visual analysis
kubectl scale deployment celery-visual-worker --replicas=0

# Check status
kubectl get pods -l queue=visual-analysis
```

## Adding New Analysis Types

1. Copy `celery-worker-template.yaml`
2. Replace placeholders (WORKER_NAME, QUEUE_NAME)
3. Apply: `kubectl apply -f celery-new-worker.yaml`
4. Scale: `kubectl scale deployment celery-new-worker --replicas=2`

## Monitor All Workers
```bash
# View all analysis workers
kubectl get deployments -l component=backend

# View worker pods by queue
kubectl get pods -l component=backend --show-labels

# Check Celery queues in Redis
kubectl exec -it redis-pod -- redis-cli llen logo_detection
kubectl exec -it redis-pod -- redis-cli llen visual_analysis
```

## Auto-scaling (Future)
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: celery-logo-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: celery-logo-worker
  minReplicas: 1
  maxReplicas: 10
  metrics:
  - type: External
    external:
      metric:
        name: redis_queue_length
      target:
        type: Value
        value: "5"  # Scale up when queue > 5 tasks
```