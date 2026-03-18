# =============================================================================
# GROQ API SETUP GUIDE
# =============================================================================
# This guide explains how to get your free Groq API key
# and set it up for this application.
# =============================================================================

## Model Being Used

**`llama-3.1-8b-instant`**

### Why Groq?
- **Truly free tier** (no billing required!)
- **Extremely fast** inference
- **No rate limits** on free tier
- **Great at understanding code**

### Available Free Models:
| Model | Speed | Best For |
|-------|-------|----------|
| `llama-3.1-8b-instant` | Fastest | General use (RECOMMENDED) |
| `llama-3.2-1b-preview` | Very Fast | Lightweight tasks |
| `llama-3.2-3b-preview` | Fast | Balanced performance |
| `mixtral-8x7b-32768` | Medium | Higher quality responses |

---

## Step-by-Step: How to Get Your API Key

### Step 1: Create a Groq Account

1. Go to https://console.groq.com/
2. Click **"Sign Up"** or **"Log In"**
3. Sign up with Google or email
4. Verify your email (if needed)

### Step 2: Create an API Key

1. Go to: **https://console.groq.com/keys**
2. Click **"Create API Key"**
3. Give it a name: `my-api-key`
4. Click **"Create"**
5. **Copy the key immediately** (starts with `gsk_`)

### Step 3: Add Your API Key to the App

1. Open the file: `.env` in the project root
2. Find this line:
   ```
   GROQ_API_KEY=PASTE_YOUR_KEY_HERE
   ```
3. Replace `PASTE_YOUR_KEY_HERE` with your actual API key

   Example:
   ```
   GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

### Step 4: Save and Restart

1. Save the `.env` file
2. Restart the backend server

---

## Testing Your Setup

### Test 1: Quick API Test

Run this command to verify your API key works:

```bash
cd backend
python test_groq.py
```

Expected output:
```
Testing Groq API...
Model: llama-3.1-8b-instant
API Key: gsk_xxxx...

Test 1: Checking available models...
  Success! Found X models

Test 2: Generating text...
  Success!
  Response: Python is a high-level programming language...

All tests passed! Groq API is working.
```

### Test 2: Full Integration Test

```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Then ask a question in the frontend.

---

## Troubleshooting

### "Invalid API Token" Error

- Make sure you copied the entire key (starts with `gsk_`)
- Make sure there are no spaces before or after

### "Rate Limit" Error

- Groq free tier has generous limits
- Wait a few seconds and try again
- Very unlikely to hit limits with normal usage

### Still Not Working?

1. Check your API key is correct
2. Make sure you saved the .env file
3. Restart the backend
4. Check the backend console for error messages

---

## Summary

1. Go to: https://console.groq.com/keys
2. Create an account / Log in
3. Create a new API key
4. Copy the key (starts with `gsk_`)
5. Paste it in `.env` as `GROQ_API_KEY=gsk_xxxx`
6. Save the file
7. Test with `python test_groq.py`
8. Run the app!
