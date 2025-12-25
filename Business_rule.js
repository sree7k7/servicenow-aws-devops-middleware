(function executeRule(current, previous /*null when async*/) {

    // --- RELIABLE TRIGGER ---
    // We send EVERYTHING to Lambda. 
    // The Lambda will decide what is important enough to forward to AWS.
    
    gs.info('=== AWS Middleware Triggered: ' + current.number + ' ===');

    try {
        var lambdaUrl = 'https://9vyeo42xxx.execute-api.us-east-1.amazonaws.com/default/servicenow-devops-middleman';
        
        // Determine simplistic event type
        var evtType = "incident_updated";
        if (current.isNewRecord()) {
            evtType = "incident_created";
        }
        
        var payload = {
            "event_type": evtType,
            "incident": {
                "number": current.number.toString(),
                "sys_id": current.sys_id.toString(),
                "short_description": current.short_description.toString(),
                "description": (current.description || "").toString(),
                "priority": current.priority.toString(),
                "state": current.getValue('state'), // Send raw state value (e.g. "1", "7")
                "state_display": current.getDisplayValue('state') // Send readable name (e.g. "Resolved")
            }
        };
        
        var request = new sn_ws.RESTMessageV2();
        request.setEndpoint(lambdaUrl);
        request.setHttpMethod('POST');
        request.setRequestHeader('Content-Type', 'application/json');
        request.setRequestBody(JSON.stringify(payload));
        
        var response = request.execute();
        gs.info("AWS Sync Status: " + response.getStatusCode());

    } catch (ex) {
        gs.error("AWS Sync Error: " + ex.message);
    }

})(current, previous);