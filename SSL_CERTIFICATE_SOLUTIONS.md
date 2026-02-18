# SSL Certificate Solutions for MCP Servers

## Problem
The literature MCP server is encountering SSL certificate verification failures when connecting to NCBI APIs:

```
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate in certificate chain
```

## Solutions Implemented

### Solution 1: Disable SSL Verification (Current - Quick Fix)
The literature MCP server has been updated to disable SSL verification for HTTPS requests.

**File:** `servers/literature/index.js`
```javascript
import https from 'https';

const httpsAgent = new https.Agent({
  rejectUnauthorized: false, // Disable SSL verification
});
```

**Pros:** Quick fix, allows immediate functionality
**Cons:** Less secure, bypasses SSL certificate validation

### Solution 2: Use Your PEM Certificate File (Recommended for Production)

If you have a PEM certificate file, update the literature server:

```javascript
import https from 'https';
import fs from 'fs';

const httpsAgent = new https.Agent({
  ca: fs.readFileSync('/path/to/your/certificate.pem'),
  // Keep SSL verification enabled
  rejectUnauthorized: true
});
```

**Steps to implement:**
1. Place your PEM file in a secure location (e.g., `certs/certificate.pem`)
2. Update the path in the code above
3. Restart the literature MCP server

### Solution 3: Environment-Based Certificate Configuration

Create a more flexible solution:

```javascript
import https from 'https';
import fs from 'fs';
import path from 'path';

// Check for certificate file in environment or default location
const certPath = process.env.SSL_CERT_PATH || path.join(process.cwd(), 'certs', 'certificate.pem');
const disableSSL = process.env.DISABLE_SSL_VERIFICATION === 'true';

let httpsAgent;
if (disableSSL) {
  httpsAgent = new https.Agent({
    rejectUnauthorized: false
  });
} else if (fs.existsSync(certPath)) {
  httpsAgent = new https.Agent({
    ca: fs.readFileSync(certPath),
    rejectUnauthorized: true
  });
} else {
  // Use default system certificates
  httpsAgent = new https.Agent({
    rejectUnauthorized: true
  });
}
```

**Environment variables:**
```bash
# To use custom certificate
SSL_CERT_PATH=/path/to/your/certificate.pem

# To disable SSL verification (development only)
DISABLE_SSL_VERIFICATION=true
```

### Solution 4: System-Wide Certificate Installation

Install your certificate in the system certificate store:

**macOS:**
```bash
# Add to system keychain
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain /path/to/certificate.pem
```

**Linux:**
```bash
# Copy to ca-certificates directory
sudo cp /path/to/certificate.pem /usr/local/share/ca-certificates/your-cert.crt
sudo update-ca-certificates
```

### Solution 5: Node.js Specific Certificate Configuration

Set Node.js environment variables:

```bash
# Use custom CA file
export NODE_EXTRA_CA_CERTS=/path/to/your/certificate.pem

# Or disable SSL verification globally (NOT recommended for production)
export NODE_TLS_REJECT_UNAUTHORIZED=0
```

## Current Status

✅ **Solution 1 is implemented** - SSL verification is disabled for the literature MCP server
⚠️ **Security Note:** This allows the server to connect but bypasses certificate validation

## Recommended Next Steps

1. **For Development:** Current solution is fine
2. **For Production:** Implement Solution 2 or 3 with your PEM certificate
3. **For Enterprise:** Consider Solution 4 (system-wide installation)

## Testing

To test if the SSL issue is resolved:

1. Restart your Streamlit application
2. Try using a literature search query
3. Check if the SSL warnings disappear

## Troubleshooting

### If you still see SSL errors:

1. **Check which MCP server is failing:**
   - Look at the error message to identify the specific server
   - The error might be from `biomcp` or another server

2. **Check if BioMCP has similar issues:**
   ```bash
   cd streamlit-app
   python -c "import biomcp; print('BioMCP available')"
   ```

3. **Disable problematic servers temporarily:**
   In `config.py`, comment out servers that are failing:
   ```python
   MCP_SERVERS = {
       "pubchem": {...},
       # "literature": {...},  # Temporarily disabled
       # "biomcp": {...},      # Temporarily disabled
   }
   ```

### Alternative: Update Specific PEM Path

If you know the exact path to your PEM file, update `servers/literature/index.js`:

```javascript
const httpsAgent = new https.Agent({
  ca: fs.readFileSync('/Users/M251914/path/to/your/certificate.pem'),
  rejectUnauthorized: true
});
```

**Replace `/Users/M251914/path/to/your/certificate.pem` with your actual PEM file path.**

## Security Considerations

- **Never commit PEM files to version control**
- **Use environment variables for certificate paths**
- **Only disable SSL verification in development environments**
- **For production, always use proper certificate validation**