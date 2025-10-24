# Production-Ready Architecture Guide

**Scaling to Millions of Users: Complete DevOps & CI/CD Pipeline**

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current Architecture Analysis](#current-architecture-analysis)
3. [Missing Components for Production](#missing-components-for-production)
4. [Complete CI/CD Pipeline Options](#complete-cicd-pipeline-options)
5. [Production Infrastructure Architecture](#production-infrastructure-architecture)
6. [Kubernetes Configuration](#kubernetes-configuration)
7. [Real-World Best Practices](#real-world-best-practices)
8. [Implementation Roadmap](#implementation-roadmap)

---

## Executive Summary

This document outlines how to transform the current **Feedback App** (a Docker Compose-based Flask application with monitoring) into a **production-grade, high-traffic system** capable of handling **millions of users** with:

- ✅ High availability (99.99% uptime)
- ✅ Horizontal scalability (auto-scaling)
- ✅ Complete CI/CD automation
- ✅ Enterprise-grade security
- ✅ Comprehensive observability

### Current State

Your application currently includes:

- ✅ Flask application with RESTful API
- ✅ Docker Compose deployment
- ✅ Prometheus + Loki + Grafana monitoring
- ✅ Structured JSON logging
- ✅ Health checks
- ❌ SQLite database (not production-ready for high traffic)
- ❌ No CI/CD pipeline
- ❌ No authentication/authorization
- ❌ No horizontal scaling
- ❌ No automated testing

---

## Current Architecture Analysis

### Application Stack

```
┌─────────────────────────────────────────┐
│            USER INTERFACE                │
│        Frontend (HTML/CSS/JS)            │
│         Vanilla JS, No Frameworks        │
└──────────────────┬──────────────────────┘
                   │
           ┌───────▼────────┐
           │  REST API      │
           │  (Port 8090)   │
           └────────┬───────┘
                    │
           ┌────────▼────────────────┐
           │  FLASK APPLICATION      │
           │  - Routes Handler       │
           │  - Request Validation   │
           │  - Error Handling       │
           │  - Logging/Metrics      │
           └────────┬────────────────┘
                    │
           ┌────────▼────────────────┐
           │  SQLite Database        │
           │  (Persistent Storage)   │
           └─────────────────────────┘
```

### Current Services (Docker Compose)

| Service | Port | Purpose | Status |
|---------|------|---------|--------|
| **feedback-app** | 8090 | Flask application | ✅ Production-ready |
| **prometheus** | 9090 | Metrics collection | ✅ Production-ready |
| **loki** | 3100 | Log aggregation | ✅ Production-ready |
| **promtail** | 9080 | Log shipping | ✅ Production-ready |
| **grafana** | 3000 | Visualization | ✅ Production-ready |
| **cadvisor** | 8081 | Container metrics | ✅ Production-ready |
| **node-exporter** | 9100 | Host metrics | ✅ Production-ready |

### What Works Well

1. ✅ Complete CRUD API
2. ✅ Professional monitoring stack
3. ✅ Structured JSON logging
4. ✅ Health checks
5. ✅ Responsive frontend UI
6. ✅ Docker-based deployment
7. ✅ Configuration management via .env
8. ✅ ACID database compliance
9. ✅ No external dependencies (everything self-contained)

### Critical Gaps for Production

1. ❌ **SQLite** → Cannot handle concurrent writes at scale
2. ❌ **No load balancing** → Single point of failure
3. ❌ **No horizontal scaling** → Cannot add more instances
4. ❌ **No caching layer** → Every request hits database
5. ❌ **No authentication** → Public API without security
6. ❌ **No rate limiting** → Vulnerable to abuse
7. ❌ **No CI/CD** → Manual deployment process
8. ❌ **No automated testing** → High risk of bugs
9. ❌ **No message queue** → All operations are synchronous
10. ❌ **No CDN** → Static assets served from application

---

## Missing Components for Production

### 1. Application Layer Improvements

#### A. Database Migration

**Current: SQLite (Single file, no replication)**

**Required: PostgreSQL with High Availability**

```
PostgreSQL Primary-Replica Setup
├── Primary Instance (us-east-1a) → Read/Write
├── Replica Instance (us-east-1b) → Read-only
├── Replica Instance (us-east-1c) → Read-only
├── Connection Pooling (pgBouncer)
├── Automated Backups (point-in-time recovery)
└── Monitoring (pg_stat_monitor)
```

**Benefits:**

- Horizontal read scaling (multiple replicas)
- Automatic failover
- ACID compliance at scale
- 1000+ concurrent connections
- Replication lag < 1 second

**AWS Implementation:**

```yaml
# RDS PostgreSQL Configuration
Engine: PostgreSQL 16
Instance: db.r6g.xlarge (4 vCPU, 32 GB RAM)
Storage: 500 GB SSD (auto-scaling to 1 TB)
Multi-AZ: Enabled
Read Replicas: 2
Automated Backups: 7-day retention
```

#### B. Caching Layer

**Redis Cluster for High Performance**

```
Redis Cluster Setup
├── Session Storage (user sessions)
├── API Response Caching (GET requests)
├── Rate Limiting Counters (per user/IP)
├── Real-time Metrics Aggregation
└── Message Queue (Pub/Sub)
```

**Implementation:**

```python
import redis
from functools import wraps

redis_client = redis.Redis(
    host='redis-cluster.cache.amazonaws.com',
    port=6379,
    decode_responses=True
)

def cache_response(ttl=300):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            cache_key = f"cache:{f.__name__}:{str(args)}"
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            result = f(*args, **kwargs)
            redis_client.setex(cache_key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator

@app.route('/feedback')
@cache_response(ttl=60)  # Cache for 60 seconds
def get_all_feedback():
    return database_manager.get_all_feedback()
```

**Benefits:**

- 10-100x faster response times
- Reduced database load
- Sub-millisecond latency
- 1M+ ops/second throughput

#### C. Message Queue

**RabbitMQ / AWS SQS for Async Operations**

```
Message Queue Architecture
├── Background Jobs (email notifications)
├── Event-Driven Processing (webhooks)
├── Celery Workers (async tasks)
├── Dead Letter Queue (failed jobs)
└── Retry Logic (exponential backoff)
```

**Example: Async Email Notification**

```python
# tasks.py (Celery tasks)
from celery import Celery

celery = Celery('tasks', broker='redis://localhost:6379/0')

@celery.task
def send_email_notification(feedback_id):
    feedback = database_manager.get_feedback_by_id(feedback_id)
    # Send email asynchronously
    email_service.send(
        to='admin@example.com',
        subject='New Feedback',
        body=feedback.message
    )

# routes.py (modified)
@api.route('/feedback', methods=['POST'])
def create_feedback():
    # ... validation ...
    feedback = database_manager.create_feedback(feedback)

    # Queue async task instead of blocking
    send_email_notification.delay(feedback.id)

    return jsonify(feedback), 201
```

#### D. API Gateway

**Kong / AWS API Gateway**

```
API Gateway Features
├── Authentication (JWT, OAuth2, API Keys)
├── Rate Limiting (1000 req/min per user)
├── Request Throttling (circuit breaker)
├── API Versioning (/v1/feedback, /v2/feedback)
├── Request/Response Transformation
├── CORS Management
└── Analytics & Monitoring
```

**Rate Limiting Example (Kong):**

```yaml
plugins:
  - name: rate-limiting
    config:
      minute: 1000
      hour: 50000
      policy: local
      fault_tolerant: true

  - name: jwt
    config:
      key_claim_name: kid
      secret_is_base64: false
```

#### E. CDN for Static Assets

**CloudFlare / AWS CloudFront**

```
CDN Configuration
├── Static Assets (CSS, JS, images)
│   → Cached at 200+ edge locations
│   → 99% cache hit rate
│   → Reduced origin load by 90%
├── HTTPS Enforcement
├── DDoS Protection (Layer 3/4/7)
├── Bot Detection & Mitigation
└── Geographic Distribution
```

**Benefits:**

- 50-200ms faster load times globally
- 90% reduction in bandwidth costs
- Automatic HTTPS certificate management
- Built-in DDoS protection

---

### 2. Infrastructure Components

#### A. Load Balancer

**AWS Application Load Balancer (ALB)**

```
Load Balancer Architecture
├── Multiple Availability Zones (3+)
├── Health Checks (active/passive)
├── SSL/TLS Termination
├── Session Affinity (sticky sessions)
├── Path-Based Routing
│   → /api/* → Backend service
│   → /static/* → S3/CDN
│   → /* → Frontend service
└── Auto-Scaling Triggers
```

**Configuration:**

```yaml
# ALB Target Group
TargetGroup:
  Protocol: HTTP
  Port: 8090
  HealthCheck:
    Path: /health
    Interval: 30
    Timeout: 5
    HealthyThreshold: 2
    UnhealthyThreshold: 3
  Stickiness:
    Enabled: true
    Duration: 3600
```

#### B. Container Orchestration (Kubernetes)

**Amazon EKS / Azure AKS / Google GKE**

```
Kubernetes Cluster
├── Control Plane (Managed by cloud provider)
├── Node Groups (3+ AZs)
│   ├── Application Nodes (t3.xlarge)
│   ├── Monitoring Nodes (t3.large)
│   └── Worker Nodes (t3.medium)
├── Auto-Scaling
│   ├── Horizontal Pod Autoscaler (HPA)
│   └── Cluster Autoscaler (CA)
├── Service Mesh (Istio/Linkerd)
├── Ingress Controllers (Nginx/Traefik)
└── Secrets Management (External Secrets Operator)
```

**Benefits:**

- Self-healing (automatic pod restarts)
- Rolling updates (zero-downtime deployments)
- Auto-scaling (based on CPU/memory/custom metrics)
- Multi-region support
- Resource management (CPU/memory limits)

#### C. Service Mesh (Optional)

**Istio / Linkerd**

```
Service Mesh Features
├── Mutual TLS (mTLS) between services
├── Traffic Splitting (A/B testing, canary)
├── Circuit Breaker (fault tolerance)
├── Retry Logic (automatic retries)
├── Timeout Management
├── Distributed Tracing (Jaeger integration)
└── Observability (enhanced metrics)
```

**Canary Deployment Example:**

```yaml
# Istio VirtualService
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: feedback-app
spec:
  hosts:
    - feedback-app.com
  http:
    - match:
        - headers:
            canary:
              exact: "true"
      route:
        - destination:
            host: feedback-app
            subset: v2
    - route:
        - destination:
            host: feedback-app
            subset: v1
          weight: 90
        - destination:
            host: feedback-app
            subset: v2
          weight: 10
```

#### D. Monitoring & Observability Enhancements

**Current:** Prometheus + Loki + Grafana ✅

**Add:**

```
Enhanced Observability Stack
├── Distributed Tracing
│   ├── Jaeger / Zipkin / AWS X-Ray
│   └── OpenTelemetry instrumentation
├── Application Performance Monitoring (APM)
│   ├── New Relic / Datadog / Dynatrace
│   └── Real user monitoring (RUM)
├── Error Tracking
│   ├── Sentry / Rollbar
│   └── Error aggregation & alerting
├── Uptime Monitoring
│   ├── Pingdom / UptimeRobot
│   └── Multi-region checks
└── Alerting & Incident Management
    ├── PagerDuty / OpsGenie
    └── On-call rotations
```

**Distributed Tracing Example:**

```python
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor

# Initialize tracing
tracer = trace.get_tracer(__name__)

# Instrument Flask automatically
FlaskInstrumentor().instrument_app(app)

# Manual span creation
@api.route('/feedback', methods=['POST'])
def create_feedback():
    with tracer.start_as_current_span("create_feedback") as span:
        span.set_attribute("feedback.message_length", len(message))

        with tracer.start_as_current_span("database.insert"):
            feedback = database_manager.create_feedback(feedback)

        span.set_attribute("feedback.id", feedback.id)
        return jsonify(feedback), 201
```

---

### 3. Security Components

#### A. Identity & Access Management

**Auth0 / AWS Cognito / Keycloak**

```
Authentication Flow
├── OAuth2 / OpenID Connect (OIDC)
├── JWT Token Validation
├── Role-Based Access Control (RBAC)
│   ├── Admin (full access)
│   ├── User (read/write own feedback)
│   └── Guest (read-only)
├── Multi-Factor Authentication (MFA)
└── API Key Management
```

**Implementation:**

```python
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity

jwt = JWTManager(app)

@api.route('/feedback', methods=['POST'])
@jwt_required()
def create_feedback():
    current_user = get_jwt_identity()

    # Validate user has permission
    if not has_permission(current_user, 'feedback:create'):
        return jsonify({'error': 'Forbidden'}), 403

    # ... create feedback ...
```

#### B. Secrets Management

**AWS Secrets Manager / HashiCorp Vault / Azure Key Vault**

```
Secrets Management
├── Database Credentials (auto-rotation)
├── API Keys (third-party services)
├── Encryption Keys (AES-256)
├── SSL Certificates
├── Service Account Tokens
└── Audit Logging (who accessed what, when)
```

**Example (AWS Secrets Manager):**

```python
import boto3
import json

def get_secret(secret_name):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Usage
db_credentials = get_secret('prod/database/credentials')
DATABASE_URL = f"postgresql://{db_credentials['username']}:{db_credentials['password']}@{db_credentials['host']}/feedback"
```

#### C. Web Application Firewall (WAF)

**AWS WAF / Cloudflare WAF / ModSecurity**

```
WAF Rules
├── SQL Injection Protection
├── Cross-Site Scripting (XSS) Prevention
├── DDoS Mitigation (rate-based rules)
├── Bot Detection & Challenge
├── Geo-Blocking (block specific countries)
├── IP Reputation Filtering
└── Custom Rules (block specific patterns)
```

**Example Rules:**

```yaml
# AWS WAF Rule
- Name: RateLimitRule
  Priority: 1
  Statement:
    RateBasedStatement:
      Limit: 2000  # requests per 5 minutes
      AggregateKeyType: IP
  Action:
    Block: {}

- Name: SQLiProtection
  Priority: 2
  Statement:
    ManagedRuleGroupStatement:
      VendorName: AWS
      Name: AWSManagedRulesSQLiRuleSet
  Action:
    Block: {}
```

#### D. SSL/TLS Management

**Let's Encrypt / AWS Certificate Manager (ACM)**

```
Certificate Management
├── Automatic Certificate Issuance
├── Auto-Renewal (90-day Let's Encrypt certs)
├── TLS 1.3 Enforcement
├── HSTS Headers (Strict-Transport-Security)
├── Certificate Monitoring (expiry alerts)
└── Wildcard Certificates (*.feedback-app.com)
```

#### E. Container Security

**Trivy / Snyk / Aqua Security**

```
Container Security Pipeline
├── Vulnerability Scanning (daily scans)
├── Image Signing (Notary / Cosign)
├── Runtime Security (Falco)
├── Policy Enforcement (Open Policy Agent)
├── Non-Root Containers (UID 1000)
├── Read-Only Root Filesystem
└── Security Context Constraints
```

**GitHub Actions Integration:**

```yaml
- name: Run Trivy vulnerability scanner
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: 'ghcr.io/your-org/feedback-app:latest'
    format: 'sarif'
    severity: 'CRITICAL,HIGH'
    exit-code: '1'  # Fail build on vulnerabilities
```

---

### 4. Testing Infrastructure

#### A. Unit Tests

**pytest + pytest-cov + pytest-mock**

```python
# app/tests/test_routes.py
import pytest
from app import create_app
from app.database import DatabaseManager

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_db(mocker):
    return mocker.patch('app.routes.database_manager')

def test_create_feedback_success(client, mock_db):
    mock_db.create_feedback.return_value = {
        'id': 1,
        'message': 'Test feedback',
        'created_at': '2024-10-23T12:00:00'
    }

    response = client.post('/feedback', json={'message': 'Test feedback'})

    assert response.status_code == 201
    assert response.json['id'] == 1
    assert response.json['message'] == 'Test feedback'

def test_create_feedback_validation_error(client):
    response = client.post('/feedback', json={'message': ''})

    assert response.status_code == 400
    assert 'error' in response.json

def test_get_all_feedback(client, mock_db):
    mock_db.get_all_feedback.return_value = [
        {'id': 1, 'message': 'Feedback 1'},
        {'id': 2, 'message': 'Feedback 2'}
    ]

    response = client.get('/feedback')

    assert response.status_code == 200
    assert len(response.json) == 2
```

**Run tests:**

```bash
pytest app/tests/ \
  --cov=app \
  --cov-report=html \
  --cov-report=term-missing \
  -v
```

#### B. Integration Tests

```python
# tests/integration/test_api_integration.py
import pytest
import requests

@pytest.fixture
def api_url():
    return "http://localhost:8090"

def test_full_crud_workflow(api_url):
    # Create
    response = requests.post(
        f"{api_url}/feedback",
        json={'message': 'Integration test feedback'}
    )
    assert response.status_code == 201
    feedback_id = response.json()['id']

    # Read
    response = requests.get(f"{api_url}/feedback/{feedback_id}")
    assert response.status_code == 200
    assert response.json()['message'] == 'Integration test feedback'

    # Update
    response = requests.put(
        f"{api_url}/feedback/{feedback_id}",
        json={'message': 'Updated feedback'}
    )
    assert response.status_code == 200
    assert response.json()['message'] == 'Updated feedback'

    # Delete
    response = requests.delete(f"{api_url}/feedback/{feedback_id}")
    assert response.status_code == 200

    # Verify deletion
    response = requests.get(f"{api_url}/feedback/{feedback_id}")
    assert response.status_code == 404
```

#### C. End-to-End Tests

**Playwright / Cypress**

```javascript
// e2e_tests/test_feedback_ui.spec.js
const { test, expect } = require('@playwright/test');

test('Complete feedback workflow', async ({ page }) => {
  // Navigate to app
  await page.goto('http://localhost:8090');

  // Check page loaded
  await expect(page.locator('h1')).toContainText('Feedback App');

  // Add new feedback
  await page.click('button:has-text("Add Feedback")');
  await page.fill('textarea[name="message"]', 'E2E test feedback');
  await page.click('button:has-text("Submit")');

  // Verify feedback appears
  await expect(page.locator('.feedback-card')).toContainText('E2E test feedback');

  // Edit feedback
  await page.click('.feedback-card:has-text("E2E test") button:has-text("Edit")');
  await page.fill('textarea[name="message"]', 'Updated E2E feedback');
  await page.click('button:has-text("Save")');

  // Verify update
  await expect(page.locator('.feedback-card')).toContainText('Updated E2E feedback');

  // Delete feedback
  await page.click('.feedback-card:has-text("Updated E2E") button:has-text("Delete")');
  await page.click('button:has-text("Confirm")');

  // Verify deletion
  await expect(page.locator('.feedback-card:has-text("Updated E2E")')).toHaveCount(0);
});
```

#### D. Load Testing

**k6 / Locust**

```javascript
// loadtests/script.js (k6)
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 100 },   // Ramp up to 100 users
    { duration: '5m', target: 100 },   // Stay at 100 users
    { duration: '2m', target: 200 },   // Ramp up to 200 users
    { duration: '5m', target: 200 },   // Stay at 200 users
    { duration: '2m', target: 0 },     // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95% of requests < 500ms
    http_req_failed: ['rate<0.01'],    // Error rate < 1%
  },
};

export default function () {
  // GET all feedback
  let res = http.get('http://localhost:8090/feedback');
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });

  sleep(1);

  // POST new feedback
  let payload = JSON.stringify({ message: 'Load test feedback' });
  let params = { headers: { 'Content-Type': 'application/json' } };

  res = http.post('http://localhost:8090/feedback', payload, params);
  check(res, {
    'status is 201': (r) => r.status === 201,
    'response has id': (r) => r.json('id') !== undefined,
  });

  sleep(1);
}
```

**Run load test:**

```bash
k6 run loadtests/script.js
```

---

## Complete CI/CD Pipeline Options

### Option 1: Jenkins (Self-Hosted)

**Jenkinsfile (Declarative Pipeline)**

```groovy
pipeline {
    agent {
        kubernetes {
            yaml """
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: docker
    image: docker:24-dind
    securityContext:
      privileged: true
  - name: kubectl
    image: bitnami/kubectl:latest
  - name: python
    image: python:3.12-slim
"""
        }
    }

    environment {
        DOCKER_REGISTRY = 'ghcr.io'
        APP_NAME = 'feedback-app'
        IMAGE_TAG = "${env.BUILD_NUMBER}-${env.GIT_COMMIT.take(7)}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Code Quality') {
            parallel {
                stage('Linting') {
                    steps {
                        container('python') {
                            sh '''
                                pip install flake8 black pylint
                                flake8 app/ --max-line-length=120
                                black --check app/
                                pylint app/ --fail-under=8.0
                            '''
                        }
                    }
                }

                stage('Security Scan') {
                    steps {
                        container('python') {
                            sh '''
                                pip install bandit safety
                                bandit -r app/ -f json -o bandit-report.json
                                safety check --json
                            '''
                        }
                    }
                }
            }
        }

        stage('Unit Tests') {
            steps {
                container('python') {
                    sh '''
                        pip install -r requirements.txt -r requirements-dev.txt
                        pytest app/tests/ \
                          --cov=app \
                          --cov-report=xml \
                          --cov-report=html \
                          --junitxml=junit.xml \
                          -v
                    '''
                }
            }
            post {
                always {
                    junit 'junit.xml'
                    publishHTML([
                        reportDir: 'htmlcov',
                        reportFiles: 'index.html',
                        reportName: 'Coverage Report'
                    ])
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                container('docker') {
                    script {
                        docker.build(
                            "${DOCKER_REGISTRY}/${APP_NAME}:${IMAGE_TAG}",
                            "--build-arg BUILD_DATE=\$(date -u +'%Y-%m-%dT%H:%M:%SZ') " +
                            "--build-arg VCS_REF=${env.GIT_COMMIT} " +
                            "."
                        )
                    }
                }
            }
        }

        stage('Container Security Scan') {
            steps {
                container('docker') {
                    sh '''
                        trivy image \
                          --severity HIGH,CRITICAL \
                          --exit-code 1 \
                          ${DOCKER_REGISTRY}/${APP_NAME}:${IMAGE_TAG}
                    '''
                }
            }
        }

        stage('Push to Registry') {
            steps {
                container('docker') {
                    script {
                        docker.withRegistry("https://${DOCKER_REGISTRY}", 'registry-creds') {
                            docker.image("${DOCKER_REGISTRY}/${APP_NAME}:${IMAGE_TAG}").push()
                            docker.image("${DOCKER_REGISTRY}/${APP_NAME}:${IMAGE_TAG}").push('latest')
                        }
                    }
                }
            }
        }

        stage('Deploy to Staging') {
            when {
                branch 'develop'
            }
            steps {
                container('kubectl') {
                    withKubeConfig([credentialsId: 'k8s-staging-config']) {
                        sh '''
                            kubectl set image deployment/feedback-app \
                              feedback-app=${DOCKER_REGISTRY}/${APP_NAME}:${IMAGE_TAG} \
                              -n staging

                            kubectl rollout status deployment/feedback-app -n staging --timeout=5m
                        '''
                    }
                }
            }
        }

        stage('E2E Tests') {
            when {
                branch 'develop'
            }
            steps {
                container('python') {
                    sh '''
                        export TEST_URL=https://staging.feedback-app.com
                        pytest e2e_tests/ --html=e2e-report.html
                    '''
                }
            }
        }

        stage('Production Approval') {
            when {
                branch 'main'
            }
            steps {
                input message: 'Deploy to Production?', ok: 'Deploy'
            }
        }

        stage('Deploy to Production') {
            when {
                branch 'main'
            }
            steps {
                container('kubectl') {
                    withKubeConfig([credentialsId: 'k8s-prod-config']) {
                        sh '''
                            # Blue-Green Deployment
                            kubectl apply -f k8s/production/deployment-green.yaml
                            kubectl set image deployment/feedback-app-green \
                              feedback-app=${DOCKER_REGISTRY}/${APP_NAME}:${IMAGE_TAG} \
                              -n production

                            kubectl rollout status deployment/feedback-app-green -n production

                            # Switch traffic
                            kubectl patch service feedback-app \
                              -n production \
                              -p '{"spec":{"selector":{"version":"green"}}}'

                            # Scale down blue after 5 minutes
                            sleep 300
                            kubectl scale deployment/feedback-app-blue --replicas=0 -n production
                        '''
                    }
                }
            }
        }
    }

    post {
        success {
            slackSend(
                color: 'good',
                message: "✅ Build #${env.BUILD_NUMBER} succeeded"
            )
        }
        failure {
            slackSend(
                color: 'danger',
                message: "❌ Build #${env.BUILD_NUMBER} failed"
            )
        }
    }
}
```

---

### Option 2: GitHub Actions (Cloud-Native)

**.github/workflows/ci-cd.yml**

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  code-quality:
    name: Code Quality Checks
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install flake8 black pylint bandit safety
          pip install -r requirements.txt

      - name: Linting
        run: |
          flake8 app/ --max-line-length=120
          black --check app/
          pylint app/ --fail-under=8.0

      - name: Security scan
        run: |
          bandit -r app/ -f json -o bandit-report.json
          safety check --json

  test:
    name: Unit & Integration Tests
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s

      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run unit tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379
        run: |
          pytest app/tests/ \
            --cov=app \
            --cov-report=xml \
            --junitxml=junit.xml \
            -v

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          files: ./coverage.xml

  build:
    name: Build & Push Container
    runs-on: ubuntu-latest
    needs: [code-quality, test]
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'

  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/develop'
    environment:
      name: staging
      url: https://staging.feedback-app.com

    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Update kubeconfig
        run: |
          aws eks update-kubeconfig --name feedback-app-staging --region us-east-1

      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/feedback-app \
            feedback-app=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }} \
            -n staging

          kubectl rollout status deployment/feedback-app -n staging --timeout=5m

  e2e-tests:
    name: E2E Tests
    runs-on: ubuntu-latest
    needs: deploy-staging
    if: github.ref == 'refs/heads/develop'

    steps:
      - uses: actions/checkout@v4

      - name: Install Playwright
        run: |
          pip install playwright pytest-playwright
          playwright install --with-deps chromium

      - name: Run E2E tests
        env:
          TEST_URL: https://staging.feedback-app.com
        run: |
          pytest e2e_tests/ --browser=chromium

  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: [build, e2e-tests]
    if: github.ref == 'refs/heads/main'
    environment:
      name: production
      url: https://feedback-app.com

    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Update kubeconfig
        run: |
          aws eks update-kubeconfig --name feedback-app-production --region us-east-1

      - name: Canary Deployment (10%)
        run: |
          kubectl apply -f k8s/production/canary.yaml
          kubectl set image deployment/feedback-app-canary \
            feedback-app=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }} \
            -n production

          kubectl rollout status deployment/feedback-app-canary -n production

      - name: Monitor Canary
        run: |
          sleep 300
          # Check error rates from Prometheus
          ERROR_RATE=$(curl -s \
            'http://prometheus:9090/api/v1/query?query=rate(http_requests_total{status=~"5.."}[5m])' \
            | jq '.data.result[0].value[1]')

          if (( $(echo "$ERROR_RATE > 0.01" | bc -l) )); then
            echo "Error rate too high: $ERROR_RATE"
            kubectl delete deployment feedback-app-canary -n production
            exit 1
          fi

      - name: Full Rollout
        run: |
          kubectl set image deployment/feedback-app \
            feedback-app=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }} \
            -n production

          kubectl rollout status deployment/feedback-app -n production --timeout=10m

          kubectl delete deployment feedback-app-canary -n production

      - name: Notify Slack
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "✅ Production deployment successful",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Production Deployment Complete*\n\nCommit: `${{ github.sha }}`\nURL: https://feedback-app.com"
                  }
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

---

### Option 3: GitLab CI/CD

**.gitlab-ci.yml**

```yaml
stages:
  - lint
  - test
  - build
  - security
  - deploy-staging
  - test-staging
  - deploy-production

variables:
  DOCKER_DRIVER: overlay2
  IMAGE_TAG: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA

.python_template: &python_template
  image: python:3.12
  before_script:
    - pip install --cache-dir .pip -r requirements.txt

lint:
  <<: *python_template
  stage: lint
  script:
    - pip install flake8 black pylint
    - flake8 app/ --max-line-length=120
    - black --check app/
    - pylint app/ --fail-under=8.0

test:unit:
  <<: *python_template
  stage: test
  services:
    - postgres:16
    - redis:7
  variables:
    POSTGRES_DB: test_db
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: postgres
  script:
    - pip install -r requirements-dev.txt
    - pytest app/tests/ --cov=app --cov-report=xml --junitxml=report.xml
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    reports:
      junit: report.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

build:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker build -t $IMAGE_TAG .
    - docker push $IMAGE_TAG
  only:
    - main
    - develop

container_scanning:
  stage: security
  image: aquasec/trivy:latest
  script:
    - trivy image --exit-code 1 --severity HIGH,CRITICAL $IMAGE_TAG
  dependencies:
    - build

deploy:staging:
  stage: deploy-staging
  image: bitnami/kubectl:latest
  script:
    - kubectl set image deployment/feedback-app feedback-app=$IMAGE_TAG -n staging
    - kubectl rollout status deployment/feedback-app -n staging
  environment:
    name: staging
    url: https://staging.feedback-app.com
  only:
    - develop

deploy:production:
  stage: deploy-production
  image: bitnami/kubectl:latest
  script:
    - kubectl set image deployment/feedback-app feedback-app=$IMAGE_TAG -n production
    - kubectl rollout status deployment/feedback-app -n production
  environment:
    name: production
    url: https://feedback-app.com
  when: manual
  only:
    - main
```

---

## Production Infrastructure Architecture

### Multi-Region, High-Availability Setup

```
┌─────────────────────────────────────────────────┐
│                CloudFlare CDN                   │
│         (Global Edge Network - 200+ PoPs)       │
│    - Static asset caching                       │
│    - DDoS protection (Layer 3/4/7)              │
│    - Web Application Firewall (WAF)             │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│              AWS Route 53 (DNS)                 │
│    - Health checks (multi-region)               │
│    - Latency-based routing                      │
│    - Failover routing                           │
└────────────────────┬────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
┌────────▼─────────┐    ┌────────▼─────────┐
│   us-east-1      │    │   us-west-2      │
│   (Primary)      │    │   (Secondary)    │
└────────┬─────────┘    └────────┬─────────┘
         │                       │
┌────────▼─────────┐    ┌────────▼─────────┐
│ Application LB   │    │ Application LB   │
│ (Multi-AZ)       │    │ (Multi-AZ)       │
└────────┬─────────┘    └────────┬─────────┘
         │                       │
   ┌─────┼─────┐          ┌─────┼─────┐
   │     │     │          │     │     │
┌──▼─┐┌──▼─┐┌──▼─┐     ┌──▼─┐┌──▼─┐┌──▼─┐
│AZ-a││AZ-b││AZ-c│     │AZ-a││AZ-b││AZ-c│
└────┘└────┘└────┘     └────┘└────┘└────┘

Each Availability Zone (AZ):
┌─────────────────────────────────────────────┐
│      Kubernetes Node Group (EKS)            │
│                                             │
│  ┌────────────────────────────────────┐    │
│  │  Application Pods (3-10 replicas)  │    │
│  │  - Flask App (Gunicorn)            │    │
│  │  - Envoy Sidecar (Service Mesh)    │    │
│  │  - Metrics Exporter                │    │
│  │                                     │    │
│  │  Resources:                         │    │
│  │  - CPU: 500m-2000m                  │    │
│  │  - Memory: 512Mi-2Gi                │    │
│  │  - Auto-scaling: CPU > 70%          │    │
│  └────────────────────────────────────┘    │
│                                             │
│  ┌────────────────────────────────────┐    │
│  │  Worker Pods (Celery)              │    │
│  │  - Background job processing       │    │
│  │  - Email notifications             │    │
│  │  - Data exports                    │    │
│  └────────────────────────────────────┘    │
│                                             │
│  ┌────────────────────────────────────┐    │
│  │  Monitoring Stack                  │    │
│  │  - Prometheus                      │    │
│  │  - Grafana                         │    │
│  │  - Loki                            │    │
│  │  - Jaeger (distributed tracing)    │    │
│  └────────────────────────────────────┘    │
└─────────────────────────────────────────────┘

Data Layer (Managed AWS Services):
┌─────────────────────────────────────────────┐
│  RDS PostgreSQL 16 (Multi-AZ)               │
│  ─────────────────────────────              │
│  Primary: db.r6g.xlarge (us-east-1a)        │
│    - 4 vCPU, 32 GB RAM                      │
│    - 500 GB SSD (auto-scaling)              │
│                                             │
│  Read Replicas:                             │
│    - Replica 1 (us-east-1b)                 │
│    - Replica 2 (us-east-1c)                 │
│                                             │
│  Features:                                  │
│    - Automated backups (7-day retention)    │
│    - Point-in-time recovery                 │
│    - Encryption at rest (AES-256)           │
│    - Connection pooling (pgBouncer)         │
│    - Max connections: 5000                  │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  ElastiCache Redis (Cluster Mode)           │
│  ─────────────────────────────────          │
│  Configuration:                             │
│    - Node type: cache.r6g.large             │
│    - 3 shards × 2 replicas each             │
│    - Total: 6 nodes                         │
│                                             │
│  Features:                                  │
│    - Automatic failover                     │
│    - Multi-AZ deployment                    │
│    - Encryption in-transit & at-rest        │
│    - 1M+ ops/second throughput              │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  Amazon SQS (Message Queue)                 │
│  ─────────────────────────────────          │
│  Standard Queues:                           │
│    - feedback-tasks                         │
│    - notification-queue                     │
│                                             │
│  Dead Letter Queues:                        │
│    - feedback-tasks-dlq                     │
│    - notification-queue-dlq                 │
│                                             │
│  Features:                                  │
│    - Unlimited throughput                   │
│    - At-least-once delivery                 │
│    - 14-day retention                       │
│    - Server-side encryption                 │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  S3 Buckets                                 │
│  ─────────────────────────────────          │
│  feedback-app-static (Static assets)        │
│    - CSS, JS, images                        │
│    - CloudFront distribution                │
│    - Versioning enabled                     │
│                                             │
│  feedback-app-logs (Application logs)       │
│    - Lifecycle: Move to Glacier after 90d   │
│    - Delete after 1 year                    │
│                                             │
│  feedback-app-backups (Database backups)    │
│    - Cross-region replication               │
│    - Encryption: AES-256                    │
└─────────────────────────────────────────────┘
```

### Cost Estimation (Monthly - AWS)

| Service | Configuration | Cost (USD) |
|---------|--------------|------------|
| **EKS Cluster** | 2 clusters (staging + prod) | $146 |
| **EC2 (Nodes)** | 10× t3.xlarge (prod) | $1,520 |
| **RDS PostgreSQL** | db.r6g.xlarge + replicas | $1,200 |
| **ElastiCache Redis** | 6× cache.r6g.large | $1,440 |
| **ALB** | 2× Application Load Balancers | $40 |
| **S3** | 500 GB storage + requests | $15 |
| **CloudFront** | 1 TB data transfer | $85 |
| **Route 53** | Hosted zone + queries | $1 |
| **CloudWatch** | Logs + metrics | $50 |
| **Data Transfer** | Inter-AZ + outbound | $200 |
| **Total** | | **~$4,700/month** |

*Note: Costs vary based on actual usage, region, and reserved instance discounts.*

---

## Kubernetes Configuration

### Production Deployment

**k8s/production/deployment.yaml**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: feedback-app
  namespace: production
  labels:
    app: feedback-app
    version: v1
spec:
  replicas: 10
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%        # Max 2-3 extra pods during update
      maxUnavailable: 25%  # Max 2-3 pods down during update

  selector:
    matchLabels:
      app: feedback-app

  template:
    metadata:
      labels:
        app: feedback-app
        version: v1
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8090"
        prometheus.io/path: "/metrics"

    spec:
      # Pod anti-affinity (spread across nodes)
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                labelSelector:
                  matchExpressions:
                    - key: app
                      operator: In
                      values:
                        - feedback-app
                topologyKey: kubernetes.io/hostname

      # Security context
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000

      containers:
        - name: feedback-app
          image: ghcr.io/your-org/feedback-app:latest
          imagePullPolicy: Always

          ports:
            - name: http
              containerPort: 8090
              protocol: TCP

          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: database-credentials
                  key: url

            - name: REDIS_URL
              valueFrom:
                secretKeyRef:
                  name: redis-credentials
                  key: url

            - name: SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: app-secrets
                  key: secret-key

            - name: LOG_LEVEL
              value: "INFO"

            - name: ENVIRONMENT
              value: "production"

          # Resource limits & requests
          resources:
            requests:
              cpu: 500m      # 0.5 CPU core
              memory: 512Mi  # 512 MB RAM
            limits:
              cpu: 2000m     # 2 CPU cores
              memory: 2Gi    # 2 GB RAM

          # Health checks
          livenessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 30
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3

          readinessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 10
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 3

          # Security context (container-level)
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop:
                - ALL

          # Volume mounts (read-only root fs requires temp dirs)
          volumeMounts:
            - name: tmp
              mountPath: /tmp
            - name: logs
              mountPath: /app/logs

      volumes:
        - name: tmp
          emptyDir: {}
        - name: logs
          emptyDir: {}

---
apiVersion: v1
kind: Service
metadata:
  name: feedback-app-service
  namespace: production
  labels:
    app: feedback-app
spec:
  type: ClusterIP
  selector:
    app: feedback-app
  ports:
    - name: http
      port: 80
      targetPort: 8090
      protocol: TCP
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 3600

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: feedback-app-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: feedback-app

  minReplicas: 10
  maxReplicas: 100

  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70

    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80

    - type: Pods
      pods:
        metric:
          name: http_requests_per_second
        target:
          type: AverageValue
          averageValue: "1000"

  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300  # Wait 5 min before scaling down
      policies:
        - type: Percent
          value: 50
          periodSeconds: 60

    scaleUp:
      stabilizationWindowSeconds: 0    # Scale up immediately
      policies:
        - type: Percent
          value: 100                   # Double pods if needed
          periodSeconds: 15
        - type: Pods
          value: 4                     # Or add 4 pods at a time
          periodSeconds: 15
      selectPolicy: Max                # Choose most aggressive policy

---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: feedback-app-pdb
  namespace: production
spec:
  minAvailable: 75%
  selector:
    matchLabels:
      app: feedback-app

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: feedback-app-ingress
  namespace: production
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
    - hosts:
        - feedback-app.com
      secretName: feedback-app-tls
  rules:
    - host: feedback-app.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: feedback-app-service
                port:
                  number: 80
```

---

## Real-World Best Practices

### Companies Handling High Traffic

#### 1. **Netflix**

- **Scale:** 230+ million subscribers, 1 billion+ hours streamed/month
- **Architecture:**
  - 700+ microservices
  - AWS-based infrastructure
  - Open Connect CDN (edge caching)
  - Chaos engineering (Chaos Monkey)
  - A/B testing framework
  - Automated canary deployments
  - Regional failover in < 10 minutes

**Key Practices:**

```
- Microservices architecture (loosely coupled)
- Automated chaos testing (kill random services)
- Edge caching (95% of traffic served from edge)
- Real-time data pipelines (Apache Kafka)
- 3-region active-active (US, EU, Asia)
```

#### 2. **Uber**

- **Scale:** 131 million users, 6.3 billion trips/year
- **Architecture:**
  - Multi-region active-active
  - Circuit breakers (Hystrix)
  - Dynamic scaling (10,000+ instances)
  - Real-time data pipelines
  - 99.99% uptime SLA

**Key Practices:**

```
- Microservices (100+ services)
- Ring deployments (gradually increase traffic)
- Observability-first (distributed tracing)
- Automated rollbacks (error rate > threshold)
- Feature flags (gradual rollouts)
```

#### 3. **Airbnb**

- **Scale:** 150 million users, 7+ million listings
- **Architecture:**
  - Progressive rollouts
  - Feature flags (LaunchDarkly)
  - Observability (Datadog)
  - Infrastructure as Code (Terraform)
  - Blue-green deployments

**Key Practices:**

```
- Monorepo (easier code sharing)
- GraphQL API (efficient data fetching)
- Service mesh (Envoy-based)
- Automated testing (90%+ coverage)
- Incident response runbooks
```

---

### Deployment Strategies Comparison

| Strategy | Downtime | Risk | Rollback Speed | Complexity |
|----------|----------|------|----------------|------------|
| **Recreate** | Yes (high) | High | Fast | Low |
| **Rolling Update** | No | Medium | Slow | Low |
| **Blue-Green** | No | Low | Instant | Medium |
| **Canary** | No | Very Low | Fast | High |
| **A/B Testing** | No | Very Low | Fast | High |

#### 1. **Blue-Green Deployment**

```
┌─────────────┐
│ Load Balancer│
└──────┬───────┘
       │ 100% traffic
┌──────▼───────┐      ┌─────────────┐
│ Blue (v1.0)  │      │ Green (v1.1)│
│ 10 instances │      │ 10 instances│ ← Deploy & test
└──────────────┘      └─────────────┘

Switch traffic:
┌─────────────┐
│ Load Balancer│
└──────┬───────┘
       │ 100% traffic
┌─────────────┐      ┌──────▼──────┐
│ Blue (v1.0) │      │ Green (v1.1)│
│ (standby)   │      │ 10 instances│
└─────────────┘      └─────────────┘
```

**Benefits:**

- Instant rollback (switch back to blue)
- Zero downtime
- Full testing before switch

**Drawbacks:**

- 2× infrastructure cost during switch
- Database migrations tricky

#### 2. **Canary Deployment**

```
Phase 1: 10% traffic to new version
┌─────────────┐
│ Load Balancer│
└──────┬───────┘
       ├─ 90% traffic ──► v1.0 (9 instances)
       └─ 10% traffic ──► v1.1 (1 instance)

Monitor metrics → If OK, continue

Phase 2: 50% traffic
       ├─ 50% traffic ──► v1.0 (5 instances)
       └─ 50% traffic ──► v1.1 (5 instances)

Phase 3: 100% traffic
       └─ 100% traffic ──► v1.1 (10 instances)
```

**Benefits:**

- Gradual rollout (reduce blast radius)
- Real-user testing
- Automated rollback on errors

**Drawbacks:**

- Complex traffic management
- Longer deployment time

#### 3. **Feature Flags**

```python
from launchdarkly import get_client

ldclient = get_client()

@app.route('/feedback', methods=['POST'])
def create_feedback():
    user = get_current_user()

    # Check feature flag
    if ldclient.variation('new-feedback-algorithm', user, False):
        # New algorithm (10% of users)
        return create_feedback_v2()
    else:
        # Old algorithm (90% of users)
        return create_feedback_v1()
```

**Benefits:**

- Instant enable/disable (no deployment)
- User targeting (specific users/groups)
- A/B testing support

---

### Incident Response Best Practices

#### 1. **Alerting Hierarchy**

```
Level 1: Warning (Slack notification)
  - CPU > 70% for 5 minutes
  - Error rate > 0.5%
  - Response time P95 > 500ms

Level 2: Critical (PagerDuty alert)
  - CPU > 90% for 2 minutes
  - Error rate > 2%
  - Response time P95 > 1000ms
  - Service down (health check failing)

Level 3: Disaster (Call leadership)
  - Multi-region outage
  - Data loss detected
  - Security breach
```

#### 2. **Incident Response Runbook**

```
STEP 1: Acknowledge (< 2 minutes)
  - Acknowledge PagerDuty alert
  - Post in #incidents Slack channel
  - Assign incident commander

STEP 2: Assess (< 5 minutes)
  - Check Grafana dashboards
  - Review error logs in Loki
  - Identify affected services

STEP 3: Mitigate (< 15 minutes)
  - Rollback to previous version (if deployment issue)
  - Scale up resources (if capacity issue)
  - Failover to backup region (if region issue)

STEP 4: Resolve (< 30 minutes)
  - Verify metrics return to normal
  - Monitor for 15 minutes
  - Post resolution in Slack

STEP 5: Post-Mortem (< 48 hours)
  - Write incident report
  - Identify root cause
  - Create action items
  - Share learnings with team
```

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-4)

**Goals:**

- ✅ Set up CI/CD pipeline
- ✅ Add automated testing
- ✅ Migrate to PostgreSQL

**Tasks:**

1. **Week 1: Testing Infrastructure**
   - [ ] Add pytest with unit tests (80% coverage)
   - [ ] Add integration tests
   - [ ] Add E2E tests (Playwright)
   - [ ] Set up coverage reporting

2. **Week 2: CI/CD Pipeline**
   - [ ] Set up GitHub Actions / Jenkins
   - [ ] Add code quality checks (flake8, black)
   - [ ] Add security scanning (bandit, Trivy)
   - [ ] Configure Docker registry (GHCR / ECR)

3. **Week 3: Database Migration**
   - [ ] Set up PostgreSQL (local + AWS RDS)
   - [ ] Migrate schema from SQLite
   - [ ] Update database.py for PostgreSQL
   - [ ] Test data migration

4. **Week 4: Initial Deployment**
   - [ ] Deploy to staging environment
   - [ ] Run full test suite
   - [ ] Load test (1000 concurrent users)
   - [ ] Fix performance bottlenecks

---

### Phase 2: Scalability (Weeks 5-8)

**Goals:**

- ✅ Add caching layer
- ✅ Add message queue
- ✅ Set up Kubernetes

**Tasks:**

1. **Week 5: Caching Layer**
   - [ ] Set up Redis cluster
   - [ ] Add response caching
   - [ ] Add session storage
   - [ ] Benchmark improvements

2. **Week 6: Message Queue**
   - [ ] Set up RabbitMQ / SQS
   - [ ] Add Celery workers
   - [ ] Implement async tasks
   - [ ] Add retry logic

3. **Week 7: Kubernetes Setup**
   - [ ] Create EKS/AKS cluster
   - [ ] Write Kubernetes manifests
   - [ ] Configure auto-scaling (HPA)
   - [ ] Set up ingress controller

4. **Week 8: Load Testing**
   - [ ] Run k6 load tests (10,000 users)
   - [ ] Optimize bottlenecks
   - [ ] Test auto-scaling
   - [ ] Document results

---

### Phase 3: Security & Observability (Weeks 9-12)

**Goals:**

- ✅ Add authentication/authorization
- ✅ Implement security best practices
- ✅ Enhanced monitoring

**Tasks:**

1. **Week 9: Authentication**
   - [ ] Integrate Auth0 / Cognito
   - [ ] Add JWT validation
   - [ ] Implement RBAC
   - [ ] Add rate limiting

2. **Week 10: Security Hardening**
   - [ ] Set up WAF (AWS WAF / Cloudflare)
   - [ ] Configure secrets management (Vault)
   - [ ] Add SSL/TLS (Let's Encrypt)
   - [ ] Run penetration tests

3. **Week 11: Enhanced Monitoring**
   - [ ] Add distributed tracing (Jaeger)
   - [ ] Set up APM (Datadog / New Relic)
   - [ ] Configure error tracking (Sentry)
   - [ ] Add uptime monitoring

4. **Week 12: Incident Response**
   - [ ] Configure PagerDuty / OpsGenie
   - [ ] Write runbooks
   - [ ] Set up on-call rotation
   - [ ] Conduct chaos engineering test

---

### Phase 4: Production Launch (Weeks 13-16)

**Goals:**

- ✅ Multi-region deployment
- ✅ CDN integration
- ✅ Production launch

**Tasks:**

1. **Week 13: Multi-Region Setup**
   - [ ] Deploy to us-west-2
   - [ ] Configure Route 53 failover
   - [ ] Test regional failover
   - [ ] Benchmark latency

2. **Week 14: CDN & Performance**
   - [ ] Set up CloudFront / CloudFlare
   - [ ] Migrate static assets to S3
   - [ ] Configure edge caching
   - [ ] Optimize bundle size

3. **Week 15: Production Prep**
   - [ ] Run final load tests (1M users)
   - [ ] Security audit
   - [ ] Disaster recovery drill
   - [ ] Update documentation

4. **Week 16: Launch**
   - [ ] Blue-green deployment to production
   - [ ] Monitor for 72 hours
   - [ ] Gradual traffic ramp (10% → 100%)
   - [ ] Post-launch retrospective

---

## Conclusion

Transforming your current **Feedback App** from a Docker Compose deployment to a **production-grade, high-traffic system** requires:

### Critical Components to Add

1. ✅ **CI/CD Pipeline** (Jenkins / GitHub Actions)
2. ✅ **Automated Testing** (Unit, Integration, E2E, Load)
3. ✅ **PostgreSQL** (with replication)
4. ✅ **Redis Caching** (session + API caching)
5. ✅ **Message Queue** (RabbitMQ / SQS)
6. ✅ **Kubernetes** (auto-scaling, self-healing)
7. ✅ **API Gateway** (authentication, rate limiting)
8. ✅ **CDN** (CloudFlare / CloudFront)
9. ✅ **Security** (WAF, secrets management, mTLS)
10. ✅ **Enhanced Monitoring** (tracing, APM, alerting)

### Key Metrics to Achieve

- **Availability:** 99.99% (< 1 hour downtime/year)
- **Scalability:** 1M+ concurrent users
- **Performance:** P95 < 200ms response time
- **Security:** Zero critical vulnerabilities
- **Deployment:** < 10 minutes with zero downtime

### Estimated Timeline

- **16 weeks** (4 months) to production-ready
- **2-4 engineers** (full-time)
- **Monthly cost:** $4,000-$8,000 (AWS infrastructure)

Your current architecture is **excellent for learning** and demonstrates strong DevOps fundamentals. The next steps outlined in this document will transform it into a system that can reliably serve millions of users with enterprise-grade quality.

---

**Document Version:** 1.0
**Last Updated:** 2024-10-23
**Author:** DevOps Architecture Team
