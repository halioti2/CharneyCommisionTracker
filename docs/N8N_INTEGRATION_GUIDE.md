# n8n Integration Guide for Charney Commission Tracker

## Overview

This guide shows how to integrate n8n with the Charney Commission Tracker for automated email processing. **No code changes required** - use the existing API!

## Architecture with n8n

```
┌─────────────────┐
│  Email Server   │
│  (Gmail/IMAP)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│      n8n        │
│  (Email Trigger)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Extract Email  │
│     Content     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  HTTP Request   │
│  POST /parse    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Commission API  │
│ (Your System)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ SQLite Database │
└─────────────────┘
```

## Setup Instructions

### Step 1: Ensure Your API is Running

```bash
# Start your commission tracker API
python run.py

# Verify it's working
curl http://localhost:5000/api/v1/health
```

### Step 2: Create n8n Workflow

#### Node 1: Email Trigger

**Options:**
- **IMAP Email** node (for any email provider)
- **Gmail** node (for Gmail)
- **Microsoft Outlook** node (for Outlook)

**Configuration:**
```json
{
  "pollTimes": {
    "item": [
      {
        "mode": "everyMinute"
      }
    ]
  },
  "mailbox": "INBOX",
  "options": {
    "allowUnauthorizedCerts": false,
    "forceReconnect": false
  },
  "filters": {
    "subject": "commission"
  }
}
```

#### Node 2: Extract Email Data

**Function Node** to prepare data:

```javascript
// Extract email content and metadata
const emailContent = $input.item.json.text || $input.item.json.textAsHtml;
const emailSubject = $input.item.json.subject;
const emailFrom = $input.item.json.from?.address || $input.item.json.from;

// Prepare payload for API
return {
  json: {
    email_content: emailContent,
    email_subject: emailSubject,
    email_source: emailFrom
  }
};
```

#### Node 3: HTTP Request to Commission API

**HTTP Request Node:**

```json
{
  "method": "POST",
  "url": "http://localhost:5000/api/v1/parse",
  "authentication": "none",
  "requestMethod": "POST",
  "sendBody": true,
  "bodyParameters": {
    "parameters": [
      {
        "name": "email_content",
        "value": "={{ $json.email_content }}"
      },
      {
        "name": "email_subject",
        "value": "={{ $json.email_subject }}"
      },
      {
        "name": "email_source",
        "value": "={{ $json.email_source }}"
      }
    ]
  },
  "options": {
    "response": {
      "response": {
        "fullResponse": false,
        "responseFormat": "json"
      }
    }
  }
}
```

#### Node 4: Check Confidence Score (Optional)

**IF Node** to handle low confidence:

```javascript
// Check if confidence score is acceptable
return $json.validation.confidence_score >= 0.7;
```

#### Node 5a: Success Path - Notify

**Send notification** (Slack, Email, etc.):

```
Commission processed successfully!
Transaction: {{ $json.data.transaction_id }}
Property: {{ $json.data.property_address }}
Amount: ${{ $json.data.total_commission }}
Confidence: {{ $json.validation.confidence_score }}
```

#### Node 5b: Low Confidence Path - Alert

**Send alert** for manual review:

```
⚠️ Low confidence commission detected
Transaction: {{ $json.data.transaction_id }}
Confidence: {{ $json.validation.confidence_score }}
Please review manually.
```

### Step 3: Test the Workflow

1. **Send a test email** to your monitored inbox
2. **Watch n8n** process it
3. **Check your API** for the new commission:
   ```bash
   curl http://localhost:5000/api/v1/commissions
   ```

## Complete n8n Workflow JSON

```json
{
  "name": "Commission Email Parser",
  "nodes": [
    {
      "parameters": {
        "pollTimes": {
          "item": [
            {
              "mode": "everyMinute"
            }
          ]
        },
        "mailbox": "INBOX",
        "options": {
          "allowUnauthorizedCerts": false
        }
      },
      "name": "IMAP Email",
      "type": "n8n-nodes-base.emailReadImap",
      "position": [250, 300],
      "typeVersion": 2
    },
    {
      "parameters": {
        "functionCode": "const emailContent = $input.item.json.text || $input.item.json.textAsHtml;\nconst emailSubject = $input.item.json.subject;\nconst emailFrom = $input.item.json.from?.address || $input.item.json.from;\n\nreturn {\n  json: {\n    email_content: emailContent,\n    email_subject: emailSubject,\n    email_source: emailFrom\n  }\n};"
      },
      "name": "Extract Email Data",
      "type": "n8n-nodes-base.function",
      "position": [450, 300],
      "typeVersion": 1
    },
    {
      "parameters": {
        "method": "POST",
        "url": "http://localhost:5000/api/v1/parse",
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {
              "name": "email_content",
              "value": "={{ $json.email_content }}"
            },
            {
              "name": "email_subject",
              "value": "={{ $json.email_subject }}"
            },
            {
              "name": "email_source",
              "value": "={{ $json.email_source }}"
            }
          ]
        },
        "options": {}
      },
      "name": "Parse Commission",
      "type": "n8n-nodes-base.httpRequest",
      "position": [650, 300],
      "typeVersion": 3
    },
    {
      "parameters": {
        "conditions": {
          "number": [
            {
              "value1": "={{ $json.validation.confidence_score }}",
              "operation": "largerEqual",
              "value2": 0.7
            }
          ]
        }
      },
      "name": "Check Confidence",
      "type": "n8n-nodes-base.if",
      "position": [850, 300],
      "typeVersion": 1
    }
  ],
  "connections": {
    "IMAP Email": {
      "main": [
        [
          {
            "node": "Extract Email Data",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Extract Email Data": {
      "main": [
        [
          {
            "node": "Parse Commission",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Parse Commission": {
      "main": [
        [
          {
            "node": "Check Confidence",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}
```

## Advanced Features

### 1. Error Handling

Add **Error Trigger** node to catch failures:

```javascript
// In Function node after HTTP Request
if ($json.success === false) {
  throw new Error(`Parsing failed: ${$json.message}`);
}
return $json;
```

### 2. Duplicate Detection

Check if transaction already exists:

```javascript
// Before parsing, check existing commissions
const transactionId = extractTransactionId($json.email_content);
const checkUrl = `http://localhost:5000/api/v1/commissions?transaction_id=${transactionId}`;
// Make GET request to check
```

### 3. Multi-Stage Approval

```
[Parse] → [Low Confidence?] → [Send to Slack for Approval]
                           ↓
                    [Approved?] → [Update Status to Verified]
```

### 4. Batch Processing

Process multiple emails at once:

```javascript
// In Function node
const emails = $input.all();
const results = [];

for (const email of emails) {
  // Process each email
  results.push(processEmail(email));
}

return results;
```

## Benefits of Using n8n

### ✅ Advantages

1. **Visual Workflow**: Easy to understand and modify
2. **No Code Changes**: Use existing API as-is
3. **Rich Integrations**: 
   - Gmail, Outlook, IMAP
   - Slack, Teams notifications
   - Google Sheets, Airtable
   - Webhooks, HTTP requests
4. **Error Handling**: Built-in retry and error workflows
5. **Monitoring**: Visual execution history
6. **Flexibility**: Easy to add conditional logic
7. **Testing**: Test individual nodes

### 🎯 Use Cases

- **Automated Processing**: Process emails as they arrive
- **Multi-Source**: Handle emails from multiple accounts
- **Notifications**: Alert team on Slack/Teams
- **Approval Workflows**: Route low-confidence items for review
- **Data Export**: Send to Google Sheets, Airtable, etc.
- **Webhooks**: Trigger other systems on new commissions

## Comparison: n8n vs Built-in Email Processor

| Feature | n8n | Built-in Processor |
|---------|-----|-------------------|
| Visual Workflow | ✅ Yes | ❌ No |
| Email Providers | ✅ Many | ⚠️ IMAP only |
| Notifications | ✅ Built-in | ❌ Custom code |
| Approval Flows | ✅ Easy | ❌ Custom code |
| Testing | ✅ Visual | ⚠️ Code-based |
| Monitoring | ✅ Dashboard | ⚠️ Logs only |
| Learning Curve | ✅ Low | ⚠️ Medium |
| Flexibility | ✅ High | ✅ High |

## Recommendation

**Use n8n for email processing** because:
1. ✅ No code changes needed
2. ✅ Better monitoring and debugging
3. ✅ Easier for non-developers to modify
4. ✅ Rich integration ecosystem
5. ✅ Visual workflow is self-documenting

**Keep the built-in processor** for:
- Programmatic access
- Batch processing scripts
- Testing and development

## Next Steps

1. **Install n8n**: 
   ```bash
   npx n8n
   # or
   docker run -it --rm --name n8n -p 5678:5678 n8nio/n8n
   ```

2. **Import workflow**: Copy the JSON above into n8n

3. **Configure email**: Set up your email credentials

4. **Test**: Send a test commission email

5. **Monitor**: Watch the workflow execute

## Support

- n8n Documentation: https://docs.n8n.io
- Your API Documentation: README.txt
- API Endpoint: `POST /api/v1/parse`

## Troubleshooting

**Issue**: n8n can't reach API
- **Solution**: Ensure API is running on `http://localhost:5000`
- **Alternative**: Use `http://host.docker.internal:5000` if n8n is in Docker

**Issue**: Email not triggering
- **Solution**: Check email filters and credentials

**Issue**: Parsing fails
- **Solution**: Check API logs in `logs/app.log`
- **Solution**: Test endpoint directly with curl

**Issue**: Low confidence scores
- **Solution**: Review email format
- **Solution**: Adjust confidence threshold in workflow

