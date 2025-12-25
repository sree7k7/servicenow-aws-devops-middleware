import json
import hmac
import hashlib
import datetime
import urllib3
import base64
import logging

# --- CONFIGURATION ---
WEBHOOK_URL = "https://event-ai.us-east-1.api.aws/webhook/generic/80e72670-995e-4eaa-9eee-787ce5b3dxxx"
SECRET_STRING = "xxxxxxxyyyyyzzzzzz"  # Replace with your actual secret
# ---------------------

logger = logging.getLogger()
logger.setLevel(logging.INFO)
http = urllib3.PoolManager()

def lambda_handler(event, context):
    try:
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event

        inc_data = body.get('incident', body)
        inc_id = inc_data.get('number', 'UNKNOWN')
        
        # --- SMART LOGIC ---
        event_type = body.get('event_type', 'incident_created')
        
        # Default to 'created'
        aws_action = "created" 
        
        # Explicitly handle Resolution
        if "resolve" in event_type or "close" in event_type:
            aws_action = "resolved"
            logger.info(f"Resolving Incident: {inc_id}")
        
        # Priority Mapping
        p_val = str(inc_data.get('priority', '3'))
        if '1' in p_val: priority = 'CRITICAL'
        elif '2' in p_val: priority = 'HIGH'
        else: priority = 'MEDIUM'

        # Payload
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        
        agent_payload = {
            "eventType": "incident",
            "incidentId": str(inc_id),
            "title": f"[{inc_id}] {inc_data.get('short_description', '')}",
            "action": aws_action,  # <--- This will now correctly send "resolved"
            "priority": priority,
            "description": inc_data.get('description', ''),
            "timestamp": timestamp
        }

        # Sign & Send (Your existing working logic)
        payload_str = json.dumps(agent_payload, separators=(',', ':'))
        string_to_sign = f"{timestamp}:{payload_str}"
        
        signature_bytes = hmac.new(SECRET_STRING.encode('utf-8'), string_to_sign.encode('utf-8'), hashlib.sha256).digest()
        signature_b64 = base64.b64encode(signature_bytes).decode('utf-8')

        headers = {
            "Content-Type": "application/json",
            "x-amzn-event-signature": signature_b64,
            "x-amzn-event-timestamp": timestamp
        }

        response = http.request('POST', WEBHOOK_URL, body=payload_str, headers=headers)
        return {'statusCode': 200, 'body': "Success"}

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {'statusCode': 500, 'body': str(e)}