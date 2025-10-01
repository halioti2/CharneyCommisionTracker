# n8n Workflows for Charney Commission Tracker

This folder contains ready-to-use n8n workflows for automated commission email processing.

## 📁 Available Workflows

### 1. `commission-email-parser.json`

**Purpose**: Complete email-to-database pipeline with AI parsing

**Features**:
- ✅ Email trigger (IMAP/Gmail/Outlook)
- ✅ Automatic email content extraction
- ✅ AI parsing via Commission Tracker API
- ✅ Confidence score checking
- ✅ Success/failure notifications
- ✅ Error handling

**Flow**:
```
Email → Extract → Parse → Check Confidence → Notify
```

## 🚀 Quick Start

### Step 1: Install n8n

```bash
# Option A: Using npx (easiest)
npx n8n

# Option B: Using Docker
docker run -it --rm --name n8n -p 5678:5678 n8nio/n8n

# Option C: Global install
npm install n8n -g
n8n
```

n8n will be available at: http://localhost:5678

### Step 2: Import Workflow

1. Open n8n: http://localhost:5678
2. Click **"Workflows"** in the left menu
3. Click **"Import from File"**
4. Select `commission-email-parser.json`
5. Click **"Import"**

### Step 3: Configure Email Credentials

1. Click on the **"Email Trigger"** node
2. Click **"Create New Credentials"**
3. Enter your email settings:
   - **Host**: `imap.gmail.com` (or your provider)
   - **Port**: `993`
   - **User**: Your email address
   - **Password**: Your email password or app password
   - **SSL**: Enable

4. Click **"Save"**

### Step 4: Configure API URL

1. Click on the **"Parse Commission"** node
2. Update the URL if your API is not on localhost:5000
   - Default: `http://localhost:5000/api/v1/parse`
   - Docker: `http://host.docker.internal:5000/api/v1/parse`
   - Remote: `http://your-server:5000/api/v1/parse`

### Step 5: Test the Workflow

1. Click **"Execute Workflow"** button
2. Send a test commission email to your monitored inbox
3. Watch the workflow execute in real-time
4. Check the results in each node

### Step 6: Activate for Production

1. Click the **"Active"** toggle in the top right
2. The workflow will now run automatically
3. Monitor executions in the **"Executions"** tab

## 🔧 Customization

### Change Email Polling Frequency

In the **"Email Trigger"** node:
```json
"pollTimes": {
  "item": [
    {
      "mode": "everyMinute"  // Change to: everyHour, everyDay, custom
    }
  ]
}
```

### Adjust Confidence Threshold

In the **"High Confidence?"** node:
```javascript
// Change 0.7 to your desired threshold (0.0 - 1.0)
value2: 0.7  // 70% confidence
```

### Add Notifications

Replace the **"Log Success"**, **"Log Low Confidence"**, and **"Log Error"** nodes with:

#### Slack Notification
1. Delete the "Log" node
2. Add **"Slack"** node
3. Configure with your Slack credentials
4. Use `{{ $json.message }}` as the message

#### Email Notification
1. Delete the "Log" node
2. Add **"Send Email"** node
3. Configure SMTP settings
4. Use `{{ $json.message }}` as the body

#### Microsoft Teams
1. Delete the "Log" node
2. Add **"Microsoft Teams"** node
3. Configure with webhook URL
4. Use `{{ $json.message }}` as the message

### Filter Emails

In the **"Email Trigger"** node, add filters:
```json
"options": {
  "customEmailConfig": "subject:commission"
}
```

Or use the **"IF"** node after email trigger to filter by:
- Subject contains specific text
- Sender email address
- Email body contains keywords

## 📊 Monitoring

### View Execution History

1. Click **"Executions"** in the left menu
2. See all workflow runs
3. Click any execution to see details
4. View data at each step

### Check for Errors

1. Failed executions are marked in red
2. Click to see error details
3. Retry failed executions manually

### Performance Metrics

- Execution time per workflow
- Success/failure rate
- Average confidence scores

## 🔍 Troubleshooting

### Workflow Not Triggering

**Problem**: Emails arrive but workflow doesn't run

**Solutions**:
1. Check workflow is **Active** (toggle in top right)
2. Verify email credentials are correct
3. Check email filters aren't too restrictive
4. Look at **"Executions"** tab for errors

### API Connection Failed

**Problem**: "Parse Commission" node fails

**Solutions**:
1. Verify Commission Tracker API is running:
   ```bash
   curl http://localhost:5000/api/v1/health
   ```
2. Check API URL in node configuration
3. If using Docker, use `http://host.docker.internal:5000`
4. Check firewall settings

### Low Confidence Scores

**Problem**: All emails getting low confidence alerts

**Solutions**:
1. Check email format is clear
2. Review sample emails with team
3. Lower confidence threshold temporarily
4. Check API logs: `logs/app.log`

### Email Credentials Not Working

**Problem**: Can't connect to email server

**Solutions**:
1. **Gmail**: Enable "Less secure app access" or use App Password
2. **Outlook**: Use App Password
3. **IMAP**: Verify IMAP is enabled in email settings
4. Check host and port are correct

## 🎯 Advanced Workflows

### Multi-Source Email Processing

Create separate workflows for different email sources:
1. Duplicate the workflow
2. Configure different email credentials
3. All workflows use the same API endpoint

### Approval Workflow

Add approval step for low confidence:
1. After "Low Confidence Alert", add **"Wait for Webhook"** node
2. Send approval link to manager
3. On approval, update commission status:
   ```
   PATCH /api/v1/commissions/{id}/status
   {"status": "verified"}
   ```

### Batch Processing

Process multiple emails at once:
1. Change email trigger to fetch multiple emails
2. Add **"Split In Batches"** node
3. Process each email individually

### Data Export

Export to Google Sheets/Airtable:
1. After successful parsing
2. Add **"Google Sheets"** or **"Airtable"** node
3. Map commission data to spreadsheet columns

## 📝 Workflow Nodes Explained

| Node | Purpose | Customizable |
|------|---------|--------------|
| Email Trigger | Monitors inbox for new emails | ✅ Credentials, filters, frequency |
| Extract Email Data | Parses email structure | ⚠️ Advanced users only |
| Parse Commission | Calls your API | ✅ URL, timeout |
| Parsing Successful? | Checks API response | ⚠️ Usually no changes needed |
| High Confidence? | Checks AI confidence | ✅ Threshold value |
| Format Messages | Creates notifications | ✅ Message format |
| Log/Notify | Outputs results | ✅ Replace with Slack/Email/Teams |

## 🔐 Security Best Practices

1. **Email Credentials**:
   - Use app-specific passwords
   - Don't share credentials
   - Rotate passwords regularly

2. **API Access**:
   - Use HTTPS in production
   - Consider API authentication
   - Restrict network access

3. **n8n Access**:
   - Set up authentication
   - Use environment variables for secrets
   - Regular backups of workflows

## 📚 Additional Resources

- **n8n Documentation**: https://docs.n8n.io
- **n8n Community**: https://community.n8n.io
- **Commission Tracker API**: See `README.txt` in project root
- **Integration Guide**: See `docs/N8N_INTEGRATION_GUIDE.md`

## 🆘 Getting Help

1. **n8n Issues**: Check n8n community forum
2. **API Issues**: Check `logs/app.log`
3. **Workflow Issues**: Review execution details in n8n
4. **Integration Questions**: See `docs/N8N_DECISION_GUIDE.md`

## 🎉 Success Checklist

- [ ] n8n installed and running
- [ ] Workflow imported
- [ ] Email credentials configured
- [ ] API URL configured
- [ ] Test email processed successfully
- [ ] Notifications configured (Slack/Email/Teams)
- [ ] Workflow activated
- [ ] Team trained on monitoring

## 📞 Support

For questions about:
- **n8n**: https://community.n8n.io
- **Commission Tracker**: See project documentation
- **Integration**: See `docs/` folder

---

**Ready to automate your commission tracking!** 🚀

