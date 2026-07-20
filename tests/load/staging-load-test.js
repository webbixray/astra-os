import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const apiLatency = new Trend('api_latency');
const requestsTotal = new Counter('requests_total');

// Test configuration
export const options = {
  scenarios: {
    // Smoke test - verify basic functionality
    smoke: {
      executor: 'constant-vus',
      vus: 5,
      duration: '30s',
      tags: { test_type: 'smoke' },
    },
    // Load test - simulate normal traffic
    load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 50 },   // Ramp up
        { duration: '5m', target: 50 },   // Stay at 50 VUs
        { duration: '2m', target: 100 },  // Ramp to 100 VUs
        { duration: '5m', target: 100 },  // Stay at 100 VUs
        { duration: '2m', target: 0 },    // Ramp down
      ],
      tags: { test_type: 'load' },
    },
    // Stress test - find breaking point
    stress: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 100 },
        { duration: '5m', target: 100 },
        { duration: '2m', target: 200 },
        { duration: '5m', target: 200 },
        { duration: '2m', target: 300 },
        { duration: '5m', target: 300 },
        { duration: '2m', target: 0 },
      ],
      tags: { test_type: 'stress' },
    },
    // Spike test - sudden traffic surge
    spike: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '10s', target: 100 },
        { duration: '1m', target: 100 },
        { duration: '10s', target: 500 },
        { duration: '1m', target: 500 },
        { duration: '10s', target: 100 },
        { duration: '1m', target: 100 },
        { duration: '10s', target: 0 },
      ],
      tags: { test_type: 'spike' },
    },
    // Soak test - long duration
    soak: {
      executor: 'constant-vus',
      vus: 50,
      duration: '1h',
      tags: { test_type: 'soak' },
    },
  },

  thresholds: {
    // Global thresholds
    'http_req_duration': ['p(95)<500', 'p(99)<1000'],
    'http_req_failed': ['rate<0.01'],
    'errors': ['rate<0.01'],

    // Per-scenario thresholds
    'http_req_duration{test_type:smoke}': ['p(95)<300'],
    'http_req_duration{test_type:load}': ['p(95)<500'],
    'http_req_duration{test_type:stress}': ['p(95)<1000'],
    'http_req_duration{test_type:spike}': ['p(95)<2000'],
  },
};

// Base URL - set via environment variable
const BASE_URL = __ENV.BASE_URL || 'https://staging-api.astra-os.io';

// Test data
const testOrgId = '00000000-0000-0000-0000-000000000001';
const authToken = __ENV.AUTH_TOKEN || '';

function getHeaders() {
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`,
    'X-Organization-ID': testOrgId,
  };
}

function checkResponse(res, expectedStatus = 200) {
  const success = check(res, {
    [`status is ${expectedStatus}`]: (r) => r.status === expectedStatus,
    'response time < 1000ms': (r) => r.timings.duration < 1000,
  });

  errorRate.add(!success);
  apiLatency.add(res.timings.duration);
  requestsTotal.add(1);

  return success;
}

export function setup() {
  // Verify API is reachable
  const res = http.get(`${BASE_URL}/health/live`, { timeout: '10s' });
  if (res.status !== 200) {
    throw new Error(`Health check failed: ${res.status}`);
  }
  console.log('Setup: API is healthy');
}

export default function () {
  const headers = getHeaders();

  // 1. Health checks
  let res = http.get(`${BASE_URL}/health/live`, { headers, timeout: '10s' });
  checkResponse(res, 200);

  res = http.get(`${BASE_URL}/health/ready`, { headers, timeout: '10s' });
  checkResponse(res, 200);

  // 2. Authentication (if token not provided, test signup/signin)
  if (!authToken) {
    const email = `test_${Date.now()}@astra-os.io`;
    const password = 'TestPassword123!';

    res = http.post(`${BASE_URL}/api/v1/auth/signup`, JSON.stringify({
      email,
      password,
      name: 'Load Test User',
    }), { headers: { 'Content-Type': 'application/json' }, timeout: '10s' });

    if (checkResponse(res, 201)) {
      const token = res.json('data.access_token');
      // Note: In real test, you'd store this for subsequent requests
    }
  } else {
    // 3. Campaign CRUD
    res = http.get(`${BASE_URL}/api/v1/campaigns?organization_id=${testOrgId}`, { headers, timeout: '10s' });
    checkResponse(res, 200);

    // 4. Content generation
    res = http.post(`${BASE_URL}/api/v1/ai/content/generate`, JSON.stringify({
      organization_id: testOrgId,
      template_id: '00000000-0000-0000-0000-000000000001',
      variables: { topic: 'AI in Marketing' },
      tone: 'professional',
    }), { headers, timeout: '30s' });
    checkResponse(res, 200);

    // 5. Analytics
    res = http.get(`${BASE_URL}/api/v1/analytics/overview?organization_id=${testOrgId}`, { headers, timeout: '10s' });
    checkResponse(res, 200);

    // 6. Brand voices
    res = http.get(`${BASE_URL}/api/v1/brand-voices?organization_id=${testOrgId}`, { headers, timeout: '10s' });
    checkResponse(res, 200);

    // 7. Templates
    res = http.get(`${BASE_URL}/api/v1/content/templates?organization_id=${testOrgId}`, { headers, timeout: '10s' });
    checkResponse(res, 200);

    // 8. Dashboards
    res = http.get(`${BASE_URL}/api/v1/dashboards?organization_id=${testOrgId}`, { headers, timeout: '10s' });
    checkResponse(res, 200);
  }

  sleep(1);
}

export function teardown(data) {
  console.log('Teardown: Load test completed');
}
