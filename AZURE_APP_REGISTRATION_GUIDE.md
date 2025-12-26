# Azure App Registration Guide

This guide walks you through registering your application in Azure AD to enable Microsoft Graph API integration for Outlook draft creation.

## Prerequisites

- Azure AD account with admin permissions (or ability to register apps)
- Access to Azure Portal: https://portal.azure.com

## Step 1: Create App Registration

1. Navigate to **Azure Portal**: https://portal.azure.com
2. Go to **Azure Active Directory** (in left sidebar or search bar)
3. Click **App registrations** in the left menu
4. Click **+ New registration**

## Step 2: Configure Basic Settings

Fill in the registration form:

- **Name**: `Handwritten Notes Outlook Integration`
- **Supported account types**: Select **"Accounts in any organizational directory and personal Microsoft accounts (e.g. Skype, Xbox)"**
  - This allows both work/school accounts and personal Microsoft accounts
- **Redirect URI**: 
  - Platform: **Web**
  - URI: `http://localhost:8000/api/auth/callback`
  - For production deployment, add: `https://notes-processing-app-test.agreeablebay-60185f5e.westus2.azurecontainerapps.io/api/auth/callback`

Click **Register**

## Step 3: Note Application IDs

After registration, you'll see the app overview page. **Copy these values** to your `.env` file:

1. **Application (client) ID**: 
   - Copy this value
   - Add to `.env` as: `MICROSOFT_CLIENT_ID=<paste-value-here>`

2. **Directory (tenant) ID**:
   - Copy this value
   - Add to `.env` as: `MICROSOFT_TENANT_ID=<paste-value-here>`
   - Or use `common` to allow any tenant

## Step 4: Create Client Secret

1. In the left menu, click **Certificates & secrets**
2. Click **+ New client secret**
3. Description: `Outlook Integration Secret`
4. Expires: Choose **24 months** (or as per your security policy)
5. Click **Add**
6. **IMPORTANT**: Copy the **Value** (not the Secret ID) immediately
   - This value is shown only once!
   - Add to `.env` as: `MICROSOFT_CLIENT_SECRET=<paste-value-here>`

## Step 5: Configure API Permissions

1. In the left menu, click **API permissions**
2. Click **+ Add a permission**
3. Select **Microsoft Graph**
4. Select **Delegated permissions**
5. Search for and add these permissions:
   - `Mail.ReadWrite` - Required for creating draft emails
   - `User.Read` - Required for getting user profile/email
6. Click **Add permissions**

7. **Grant Admin Consent** (if you have admin rights):
   - Click **Grant admin consent for [Your Organization]**
   - Click **Yes** to confirm
   - This allows users to use the app without individual consent

   If you don't have admin rights, users will see a consent screen on first login.

## Step 6: Configure Redirect URI (Additional URLs)

If deploying to production, add additional redirect URIs:

1. Go to **Authentication** in the left menu
2. Under **Platform configurations** → **Web** → Click **Add URI**
3. Add your production URL:
   - `https://notes-processing-app-test.agreeablebay-60185f5e.westus2.azurecontainerapps.io/api/auth/callback`
4. Click **Save**

## Step 7: Update .env File

Your `.env` file should now have these values:

```bash
# Microsoft Graph API Configuration
MICROSOFT_CLIENT_ID=12345678-1234-1234-1234-123456789abc
MICROSOFT_CLIENT_SECRET=your_secret_value_here
MICROSOFT_TENANT_ID=common
MICROSOFT_REDIRECT_URI=http://localhost:8000/api/auth/callback
```

For production, update `MICROSOFT_REDIRECT_URI` to match your deployed URL.

## Step 8: Test Authentication

1. Start your application:
   ```bash
   python main.py
   ```

2. Upload and process a note

3. Click **"Create Outlook Email"**

4. When prompted, enter your email address

5. If not authenticated, a popup will open for Microsoft login

6. Log in with your Microsoft account and grant permissions

7. After authentication, click **"Create Outlook Email"** again

8. Draft should be created in your Outlook mailbox!

## Troubleshooting

### Error: "AADSTS50011: The redirect URI specified in the request does not match"

- **Solution**: Make sure the redirect URI in your `.env` file exactly matches the one registered in Azure Portal
- Check for trailing slashes, http vs https, and port numbers

### Error: "AADSTS65001: The user or administrator has not consented"

- **Solution**: 
  - Have an admin grant consent in Azure Portal (Step 5)
  - Or ensure the consent screen is shown to users on first login

### Error: "Invalid client secret"

- **Solution**: 
  - Create a new client secret in Azure Portal
  - Copy the **Value** (not Secret ID) to your `.env` file
  - Restart your application

### Error: "Mail.ReadWrite permission required"

- **Solution**: 
  - Verify the permission is added in Azure Portal (Step 5)
  - If added recently, wait a few minutes for propagation
  - Try logging out and logging in again

## Security Best Practices

1. **Never commit `.env` file**: Keep credentials out of version control
2. **Rotate secrets regularly**: Create new client secrets every 6-12 months
3. **Use least privilege**: Only request necessary permissions (Mail.ReadWrite, User.Read)
4. **Monitor usage**: Check Azure AD sign-in logs for suspicious activity
5. **Production secrets**: Use Azure Key Vault for production deployments

## Production Deployment

For production deployment to Azure:

1. Register additional redirect URIs for your Azure Container Apps URL
2. Update `.env` or Azure Container Apps environment variables:
   ```
   MICROSOFT_REDIRECT_URI=https://your-app.azurecontainerapps.io/api/auth/callback
   ```
3. Store secrets in Azure Key Vault (recommended)
4. Configure managed identity for secure secret access

## Additional Resources

- [Microsoft Graph API Documentation](https://learn.microsoft.com/en-us/graph/)
- [Azure AD App Registration](https://learn.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app)
- [Microsoft Graph Mail API](https://learn.microsoft.com/en-us/graph/api/resources/mail-api-overview)
- [OAuth 2.0 Authorization Code Flow](https://learn.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-auth-code-flow)

## Summary

You've now:
- ✅ Registered your app in Azure AD
- ✅ Configured OAuth redirect URI
- ✅ Created client secret
- ✅ Added Microsoft Graph API permissions
- ✅ Updated `.env` with credentials
- ✅ Ready to test Outlook integration

The application can now create formatted draft emails directly in users' Outlook mailboxes with formatting preserved!

