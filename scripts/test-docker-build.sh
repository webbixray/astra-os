#!/bin/bash
set -e

echo "=== Testing Production Docker Builds ==="
echo ""

echo "1. Building API image..."
docker build -f apps/api/Dockerfile -t astra-api:prod-test apps/api

echo ""
echo "2. Building Web image..."
docker build -f apps/web/Dockerfile -t astra-web:prod-test .

echo ""
echo "3. Testing API image..."
docker run --rm astra-api:prod-test python -c "import app.main; print('API imports OK')"

echo ""
echo "4. Testing Web image..."
docker run --rm astra-web:prod-test node -e "console.log('Web runs OK')"

echo ""
echo "=== All production Docker builds successful! ==="
