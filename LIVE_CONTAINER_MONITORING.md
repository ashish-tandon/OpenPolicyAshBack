# 🔍 Live Container Monitoring Quick Reference

## 🚀 Real-Time Monitoring Commands

### 1. Live Logs (Most Important)
```bash
# Real-time logs (follow mode)
az containerapp logs show --resource-group openpolicy-rg --name openpolicy-api --follow

# Last 50 log lines
az containerapp logs show --resource-group openpolicy-rg --name openpolicy-api --tail 50

# Logs from specific revision
az containerapp logs show --resource-group openpolicy-rg --name openpolicy-api --revision openpolicy-api--REVISION_NAME
```

### 2. Container Status
```bash
# Check if container is running
az containerapp show --resource-group openpolicy-rg --name openpolicy-api --query "properties.runningStatus"

# Get container details
az containerapp show --resource-group openpolicy-rg --name openpolicy-api

# List all revisions
az containerapp revision list --resource-group openpolicy-rg --name openpolicy-api
```

### 3. Health Checks
```bash
# Test health endpoint
curl -f https://openpolicy-api.kindgrass-4bb31d5d.eastus.azurecontainerapps.io/health

# Continuous health monitoring
watch -n 5 'curl -s -o /dev/null -w "%{http_code}" https://openpolicy-api.kindgrass-4bb31d5d.eastus.azurecontainerapps.io/health'

# Test all endpoints
./deployment-verification.sh
```

## 🛠️ Quick Debugging Commands

### Container Issues
```bash
# Restart container
az containerapp restart --name openpolicy-api --resource-group openpolicy-rg

# Force new revision (if container not updating)
az containerapp delete --name openpolicy-api --resource-group openpolicy-rg --yes
# Then redeploy

# Check resource usage
az containerapp show --resource-group openpolicy-rg --name openpolicy-api --query "properties.template.containers[0].resources"
```

### Registry Issues
```bash
# Check ACR credentials
az acr credential show --name openpolicyacr

# List images in registry
az acr repository list --name openpolicyacr

# Delete old images
az acr repository delete --name openpolicyacr --image openpolicy-api:old-tag
```

## 📊 Monitoring Dashboard Commands

### Performance Monitoring
```bash
# Get CPU metrics
az monitor metrics list --resource "/subscriptions/YOUR_SUB_ID/resourceGroups/openpolicy-rg/providers/Microsoft.App/containerApps/openpolicy-api" --metric "cpu" --interval PT1M

# Get memory metrics
az monitor metrics list --resource "/subscriptions/YOUR_SUB_ID/resourceGroups/openpolicy-rg/providers/Microsoft.App/containerApps/openpolicy-api" --metric "memory" --interval PT1M
```

### Network Monitoring
```bash
# Check outbound IP addresses
az containerapp show --resource-group openpolicy-rg --name openpolicy-api --query "properties.outboundIpAddresses"

# Test external connectivity from container
curl -f https://httpbin.org/status/200
```

## 🚨 Emergency Commands

### Container Not Starting
```bash
# 1. Check logs immediately
az containerapp logs show --resource-group openpolicy-rg --name openpolicy-api --tail 50

# 2. Check status
az containerapp show --resource-group openpolicy-rg --name openpolicy-api --query "properties.runningStatus"

# 3. Restart
az containerapp restart --name openpolicy-api --resource-group openpolicy-rg

# 4. If still failing, redeploy
az containerapp delete --name openpolicy-api --resource-group openpolicy-rg --yes
```

### Performance Issues
```bash
# Scale up resources
az containerapp update --name openpolicy-api --resource-group openpolicy-rg --cpu 2 --memory 4Gi

# Increase replicas
az containerapp update --name openpolicy-api --resource-group openpolicy-rg --min-replicas 2 --max-replicas 5
```

## 📱 One-Liner Monitoring

### Quick Status Check
```bash
echo "Status: $(az containerapp show --resource-group openpolicy-rg --name openpolicy-api --query 'properties.runningStatus' -o tsv) | Health: $(curl -s -o /dev/null -w '%{http_code}' https://openpolicy-api.kindgrass-4bb31d5d.eastus.azurecontainerapps.io/health)"
```

### Continuous Monitoring
```bash
# Monitor status and health every 10 seconds
watch -n 10 'echo "=== $(date) ===" && echo "Status: $(az containerapp show --resource-group openpolicy-rg --name openpolicy-api --query "properties.runningStatus" -o tsv)" && echo "Health: $(curl -s -o /dev/null -w "%{http_code}" https://openpolicy-api.kindgrass-4bb31d5d.eastus.azurecontainerapps.io/health)"'
```

## 🔄 Update Monitoring

### During Deployment
```bash
# 1. Start monitoring logs
az containerapp logs show --resource-group openpolicy-rg --name openpolicy-api --follow

# 2. In another terminal, update the container
az containerapp update --name openpolicy-api --resource-group openpolicy-rg --image openpolicyacr.azurecr.io/openpolicy-api:latest

# 3. Watch for new revision
az containerapp revision list --resource-group openpolicy-rg --name openpolicy-api --query "[0].name" -o tsv
```

### Post-Deployment Verification
```bash
# Run comprehensive verification
./deployment-verification.sh

# Quick endpoint test
for endpoint in health docs stats jurisdictions; do
    echo "Testing $endpoint: $(curl -s -o /dev/null -w '%{http_code}' https://openpolicy-api.kindgrass-4bb31d5d.eastus.azurecontainerapps.io/$endpoint)"
done
```

## 📋 Monitoring Checklist

### Daily Monitoring
- [ ] Container status: Running
- [ ] Health endpoint: 200 OK
- [ ] Recent logs: No errors
- [ ] Resource usage: Within limits
- [ ] Response times: Acceptable

### Weekly Monitoring
- [ ] Review error logs
- [ ] Check resource utilization trends
- [ ] Verify all endpoints working
- [ ] Update dependencies if needed
- [ ] Backup configuration

### Monthly Monitoring
- [ ] Review performance metrics
- [ ] Check security settings
- [ ] Update monitoring scripts
- [ ] Review cost optimization
- [ ] Plan capacity upgrades

---

**💡 Pro Tip:** Always keep the `--follow` logs running in a separate terminal during deployments to catch issues immediately! 