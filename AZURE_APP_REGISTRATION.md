# Azure App Registration Guide

This guide walks you through registering the application in Azure Portal to enable Microsoft Graph API integration for creating Outlook draft emails.

## Prerequisites

- Azure account with access to Azure Active Directory
- Admin permissions to register applications (or request from IT admin)

## Step-by-Step Instructions

### 1. Navigate to Azure Portal

1. Go to [https://portal.azure.com](https://portal.azure.com)
2. Sign in with your Azure/Microsoft 365 account
3. Search for "Azure Active Directory" in the top search bar
4. Click on "Azure Active Directory" from the results

### 2. Register New Application

1. In the left sidebar, click on **"App registrations"**
2. Click **"+ New registration"** at the top
3. Fill in the registration form:
   - **Name**: `Handwritten Notes Outlook Integration`
   - **Supported account types**: Select **"Accounts in any organizational directory and personal Microsoft accounts (Multitenant + Personal accounts)"**
   - **Redirect URI**: 
     - Platform: **Web**
     - URI: `http://localhost:8000/api/auth/callback`
4. Click **"Register"**

### 3. Note Application Credentials

After registration, you'll see the application overview page. **Copy and save these values**:

1. **Application (client) ID**: Copy this value (looks like: `12345678-1234-1234-1234-123456789012`)
2. **Directory (tenant) ID**: Copy this value (looks like: `87654321-4321-4321-4321-210987654321`)

### 4. Create Client Secret

1. In the left sidebar, click on **"Certificates & secrets"**
2. Click on the **"Client secrets"** tab
3. Click **"+ New client secret"**
4. Add a description: `Handwritten Notes App Secret`
5. Select expiration: **24 months** (or as per your organization's policy)
6. Click **"Add"**
7. **IMPORTANT**: Immediately copy the **Value** (not the Secret ID). This is your **Client Secret**
   - ⚠️ **You can only see this value once!** If you lose it, you'll need to create a new secret.

### 5. Configure API Permissions

1. In the left sidebar, click on **"API permissions"**
2. Click **"+ Add a permission"**
3. Select **"Microsoft Graph"**
4. Select **"Delegated permissions"**
5. Search for and select:
   - **Mail.ReadWrite** - Allows the app to create, read, update, and delete email in user mailboxes
6. Click **"Add permissions"**
7. (Optional but recommended) Click **"Grant admin consent for [Your Organization]"** if you have admin rights
   - This pre-approves the permission for all users
   - If you don't have admin rights, users will need to consent individually on first use

### 6. Update Environment Variables

Now update your `.env` file with the credentials you collected:

```bash
# Microsoft Graph API Configuration
MICROSOFT_CLIENT_ID=<your-application-client-id>
MICROSOFT_CLIENT_SECRET=<your-client-secret-value>
MICROSOFT_TENANT_ID=common
MICROSOFT_REDIRECT_URI=http://localhost:8000/api/auth/callback
```

**Note**: Use `common` for MICROSOFT_TENANT_ID to support both organizational and personal Microsoft accounts. If you want to restrict to your organization only, use your actual Directory (tenant) ID.

### 7. For Production Deployment

When deploying to production (e.g., Azure Container Apps), you'll need to:

1. Add the production redirect URI to your app registration:
   - Go back to **"Authentication"** in your app registration
   - Click **"+ Add a platform"** → **"Web"**
   - Add your production URL: `https://your-production-domain.azurecontainerapps.io/api/auth/callback`
   - Click **"Configure"**

2. Update your production environment variables with the production redirect URI

## Verification

To verify your setup:

1. Start your application: `python main.py`
2. Open http://localhost:8000
3. Upload and process a note
4. Click "Create Outlook Email"
5. You should be prompted to enter your email
6. If not authenticated, a popup will open for Microsoft login
7. After login, consent to the permissions
8. Try creating the draft again - it should work!

## Troubleshooting

### "AADSTS7000215: Invalid client secret"
- Your client secret may have expired or was copied incorrectly
- Create a new client secret and update your `.env` file

### "AADSTS50011: The reply URL does not match"
- Your redirect URI in the code doesn't match what's registered in Azure
- Verify `MICROSOFT_REDIRECT_URI` in `.env` matches exactly what's in Azure Portal

### "Need admin approval"
- The Mail.ReadWrite permission requires admin consent in some organizations
- Contact your IT admin to grant consent, or use a personal Microsoft account for testing

### "Application not found"
- Verify your `MICROSOFT_CLIENT_ID` is correct
- Ensure you're using the Application (client) ID, not the Object ID

## Security Notes

- **Never commit your `.env` file** to version control
- Client secrets should be rotated regularly (every 6-12 months)
- For production, consider using Azure Key Vault to store secrets
- The `Mail.ReadWrite` permission only allows access to the authenticated user's mailbox
- Users must explicitly consent to permissions on first use

## Additional Resources

- [Microsoft Graph API Documentation](https://docs.microsoft.com/en-us/graph/overview)
- [Azure App Registration Guide](https://docs.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app)
- [Microsoft Graph Permissions Reference](https://docs.microsoft.com/en-us/graph/permissions-reference)

