#!/bin/bash
#
# Test report creation and analysis pipeline
#

cd /home/aiguru/repo/clean_neighborhood

API_URL="http://localhost:8000/api/v1"
IMAGE_PATH="/home/aiguru/Pictures/Screenshots/Screenshot From 2026-04-14 00-32-11.png"

echo "Creating test report..."

# Create report
REPORT_RESPONSE=$(curl -s -X POST "${API_URL}/reports" \
  -H "Content-Type: application/json" \
  -d '{
    "office_id": 1,
    "text_description": "this is a test",
    "media_summary": {
      "image_count": 1,
      "video_count": 0,
      "has_audio": false
    }
  }')

REPORT_ID=$(echo $REPORT_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['report_id'])")
echo "Created report ID: $REPORT_ID"

# Upload image
echo "Uploading image..."
curl -s -X POST "${API_URL}/reports/${REPORT_ID}/upload?type=image&index=0" \
  -F "file=@${IMAGE_PATH}"

echo ""
echo "Submitting report..."
curl -s -X POST "${API_URL}/reports/${REPORT_ID}/submit"

echo ""
echo ""
echo "Report submitted. Waiting for analysis..."
echo "Check status at: ${API_URL}/reports/${REPORT_ID}/status"
echo ""

# Poll for status
for i in {1..30}; do
    STATUS=$(curl -s "${API_URL}/reports/${REPORT_ID}/status" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"{d['status']} ({d['progress_percent']}%)\")")
    echo "Status: $STATUS"

    if [[ "$STATUS" == *"completed"* ]] || [[ "$STATUS" == *"failed"* ]] || [[ "$STATUS" == *"review_required"* ]]; then
        break
    fi

    sleep 2
done

echo ""
echo "Final report state:"
curl -s "${API_URL}/reports/${REPORT_ID}" | python3 -m json.tool
