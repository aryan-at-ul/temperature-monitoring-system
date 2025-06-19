#!/bin/bash
# Temperature Monitoring API Test Script using curl

# Base URL for the API
BASE_URL="http://localhost:8000/api/v1"

# Token selection
CUSTOMER="${1:-B}"
TOKEN_TYPE="${2:-read}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Token dictionary based on actual values
declare -A TOKENS
TOKENS["A_read"]="read_A_65_token_2025"
TOKENS["A_write"]="write_A_65_token_2025"
TOKENS["B_read"]="read_B_66_token_2025"
TOKENS["B_write"]="write_B_66_token_2025"
TOKENS["C_read"]="read_C_67_token_2025"
TOKENS["C_write"]="write_C_67_token_2025"
TOKENS["D_read"]="read_D_68_token_2025"
TOKENS["D_write"]="write_D_68_token_2025"
TOKENS["E_read"]="read_E_69_token_2025"
TOKENS["E_write"]="write_E_69_token_2025"
TOKENS["admin"]="admin_A_65_admin_token_2025"

# Use selected token
if [ "$TOKEN_TYPE" = "admin" ]; then
    TOKEN=${TOKENS["admin"]}
else
    TOKEN=${TOKENS["${CUSTOMER}_${TOKEN_TYPE}"]}
fi

# Mapping of some facility and storage unit IDs
FACILITY_ID_B="7f84f137-7d21-404c-a46e-5e19a4b61b58"
STORAGE_UNIT_ID_B="adb0a994-1378-4cf2-b022-2c5ec31e8daf"

# Function to test an endpoint
test_endpoint() {
    endpoint=$1
    method=${2:-GET}
    data=$3
    
    echo -e "\n${YELLOW}===== Testing $method $endpoint =====${NC}"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -X GET \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            "${BASE_URL}${endpoint}")
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -X POST \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "${BASE_URL}${endpoint}")
    elif [ "$method" = "PUT" ]; then
        response=$(curl -s -X PUT \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "${BASE_URL}${endpoint}")
    elif [ "$method" = "DELETE" ]; then
        response=$(curl -s -X DELETE \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            "${BASE_URL}${endpoint}")
    fi
    
    # Check if response is valid JSON
    if echo "$response" | jq . > /dev/null 2>&1; then
        echo -e "${GREEN}Response:${NC}"
        echo "$response" | jq .
    else
        echo -e "${RED}Raw response:${NC} $response"
    fi
    
    echo -e "\n${YELLOW}=============================================${NC}"
}

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}Temperature Monitoring API Test - Curl Script${NC}"
echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}Customer: ${CUSTOMER}, Token Type: ${TOKEN_TYPE}${NC}"
echo -e "${BLUE}Token: ${TOKEN}${NC}"
echo -e "${BLUE}==================================================${NC}"

# Test health endpoint (no auth required)
echo -e "\n${YELLOW}===== Testing Health Endpoint =====${NC}"
curl -s http://localhost:8000/health | jq .

# Select tests based on token type
if [ "$TOKEN_TYPE" = "admin" ]; then
    # Admin endpoints
    echo -e "\n\n${YELLOW}====== TESTING ADMIN ENDPOINTS ======${NC}"
    test_endpoint "/admin/customers"
    test_endpoint "/admin/config"
    test_endpoint "/admin/ingestion/logs"
    test_endpoint "/admin/facilities"
    test_endpoint "/admin/storage-units"
    test_endpoint "/admin/analytics/temperature/summary"
else
    # Customer endpoints
    echo -e "\n\n${YELLOW}====== TESTING TEMPERATURE ENDPOINTS ======${NC}"
    test_endpoint "/temperature"
    test_endpoint "/temperature/latest"
    
    # Use facility ID for customer B if testing customer B
    if [ "$CUSTOMER" = "B" ]; then
        test_endpoint "/temperature/facility/$FACILITY_ID_B"
        test_endpoint "/temperature/unit/$STORAGE_UNIT_ID_B"
    fi
    
    # Test with date parameters
    START_DATE=$(date -d "yesterday" +"%Y-%m-%dT00:00:00")
    END_DATE=$(date +"%Y-%m-%dT23:59:59")
    test_endpoint "/temperature/history?start_date=${START_DATE}&end_date=${END_DATE}"
    
    # Test Facilities Endpoints
    echo -e "\n\n${YELLOW}====== TESTING FACILITIES ENDPOINTS ======${NC}"
    test_endpoint "/facilities"
    
    if [ "$CUSTOMER" = "B" ]; then
        test_endpoint "/facilities/$FACILITY_ID_B"
        test_endpoint "/facilities/$FACILITY_ID_B/units"
    fi
    
    # Test Customer Endpoints
    echo -e "\n\n${YELLOW}====== TESTING CUSTOMER ENDPOINTS ======${NC}"
    test_endpoint "/customers/profile"
    
    # Test Analytics Endpoints
    echo -e "\n\n${YELLOW}====== TESTING ANALYTICS ENDPOINTS ======${NC}"
    test_endpoint "/analytics/temperature/summary"
    
    START_DATE=$(date -d "7 days ago" +"%Y-%m-%dT00:00:00")
    END_DATE=$(date +"%Y-%m-%dT23:59:59")
    test_endpoint "/analytics/temperature/trends?start_date=${START_DATE}&end_date=${END_DATE}&interval=day"
    test_endpoint "/analytics/alarms/history"
    test_endpoint "/analytics/performance"
    
    # Test creating a new temperature reading (only with write token)
    if [ "$TOKEN_TYPE" = "write" ] && [ "$CUSTOMER" = "B" ]; then
        echo -e "\n\n${YELLOW}====== TESTING POST OPERATIONS ======${NC}"
        TEMP_DATA='{
          "storage_unit_id": "'$STORAGE_UNIT_ID_B'",
          "temperature": -18.5,
          "temperature_unit": "C",
          "recorded_at": "'$(date -Iseconds)'",
          "sensor_id": "test_sensor_1",
          "quality_score": 1,
          "equipment_status": "normal"
        }'
        test_endpoint "/temperature" "POST" "$TEMP_DATA"
    fi
fi

echo -e "\n${GREEN}All tests completed!${NC}"