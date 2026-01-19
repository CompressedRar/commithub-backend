#!/bin/bash

# CommiHub API Testing with cURL
# Usage: bash backend/tests/test.sh

BASE_URL="http://localhost:5000"
TOKEN=""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}COMMITHUB API TESTING WITH CURL${NC}"
echo -e "${YELLOW}========================================${NC}"

# Test 1: Public endpoints
echo -e "\n${YELLOW}📌 TEST 1: PUBLIC ENDPOINTS${NC}"

echo -e "\n${GREEN}1. Get all departments:${NC}"
curl -s -X GET "$BASE_URL/api/v1/departments" \
  -H "Content-Type: application/json" | jq .

echo -e "\n${GREEN}2. Get all categories:${NC}"
curl -s -X GET "$BASE_URL/api/v1/categories" \
  -H "Content-Type: application/json" | jq .

echo -e "\n${GREEN}3. Get system settings:${NC}"
curl -s -X GET "$BASE_URL/api/v1/settings" \
  -H "Content-Type: application/json" | jq .

# Test 2: Error handling
echo -e "\n${YELLOW}📌 TEST 2: ERROR HANDLING${NC}"

echo -e "\n${GREEN}1. Test 404 (nonexistent endpoint):${NC}"
curl -s -X GET "$BASE_URL/api/v1/nonexistent" \
  -H "Content-Type: application/json" | jq .

echo -e "\n${GREEN}2. Test 401 (protected without auth):${NC}"
curl -s -w "\nStatus: %{http_code}\n" \
  -X GET "$BASE_URL/api/v1/logs" \
  -H "Content-Type: application/json" | jq .

# Test 3: Authentication
echo -e "\n${YELLOW}📌 TEST 3: AUTHENTICATION${NC}"

echo -e "\n${GREEN}1. Login attempt:${NC}"
RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "password123"
  }')

echo "$RESPONSE" | jq .

# Extract token if login successful
TOKEN=$(echo "$RESPONSE" | jq -r '.token // empty')

if [ -n "$TOKEN" ]; then
    echo -e "\n${GREEN}✅ Token obtained: ${TOKEN:0:20}...${NC}"
    
    echo -e "\n${GREEN}2. Get protected endpoint with token:${NC}"
    curl -s -X GET "$BASE_URL/api/v1/logs" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $TOKEN" | jq .
fi

# Test 4: Create operations
echo -e "\n${YELLOW}📌 TEST 4: CREATE OPERATIONS${NC}"

if [ -n "$TOKEN" ]; then
    echo -e "\n${GREEN}1. Create new category:${NC}"
    curl -s -X POST "$BASE_URL/api/v1/categories" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $TOKEN" \
      -d '{
        "name": "Test Category",
        "priority_order": 5
      }' | jq .
fi

echo -e "\n${YELLOW}========================================${NC}"
echo -e "${YELLOW}✅ TESTING COMPLETE${NC}"
echo -e "${YELLOW}========================================${NC}\n"
