
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

export const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '2m', target: 50 },   // Ramp up
    { duration: '5m', target: 100 },  // Sustained load
    { duration: '2m', target: 200 },  // Stress
    { duration: '5m', target: 100 },  // Recovery
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    http_req_failed: ['rate<0.01'],
    errors: ['rate<0.01'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

function healthCheck() {
  const res = http.get(`${BASE_URL}/api/v1/health`);
  check(res, { 'health status 200': (r) => r.status === 200 });
  errorRate.add(res.status !== 200);
}

function livenessCheck() {
  const res = http.get(`${BASE_URL}/api/v1/health/live`);
  check(res, { 'liveness status 200': (r) => r.status === 200 });
  errorRate.add(res.status !== 200);
}

function readinessCheck() {
  const res = http.get(`${BASE_URL}/api/v1/health/ready`);
  check(res, { 'readiness status 200': (r) => r.status === 200 });
  errorRate.add(res.status !== 200);
}

function metricsCheck() {
  const res = http.get(`${BASE_URL}/api/v1/metrics`);
  check(res, { 'metrics status 200': (r) => r.status === 200 });
  errorRate.add(res.status !== 200);
}

function authCheck() {
  const res = http.get(`${BASE_URL}/api/v1/auth/me`);
  // 401/403 is expected for unauthenticated
  check(res, { 'auth returns 401/403': (r) => r.status === 401 || r.status === 403 });
  errorRate.add(!(res.status === 401 || res.status === 403));
}

function apiRootCheck() {
  const res = http.get(`${BASE_URL}/api/v1/`);
  check(res, { 'api root status 200': (r) => r.status === 200 });
  errorRate.add(res.status !== 200);
}

export default function () {
  // Health checks (no auth)
  healthCheck();
  sleep(1);
  livenessCheck();
  sleep(1);
  readinessCheck();
  sleep(1);
  
  // Public metrics (no auth)
  metricsCheck();
  sleep(1);
  
  // Auth check (expects 401/403)
  authCheck();
  sleep(1);
  
  // API root
  apiRootCheck();
  sleep(1);
}
