---
description: how to push the project to a github repo
---

Follow these steps to push your project to a new GitHub repository:

1. **Create a new repository on GitHub**:
   - Go to [GitHub](https://github.com/new).
   - Give it a name (e.g., `ai-resume-screener`).
   - Do **NOT** initialize it with a README, license, or .gitignore (we already have them).
   - Click "Create repository".

2. **Add the remote origin**:
   Copy the SSH or HTTPS URL of your new repository and run:
   ```powershell
   git remote add origin YOUR_REPOSITORY_URL
   ```

3. **Stage and commit your changes**:
   ```powershell
   git add .
   git commit -m "Initial commit: Llama-3 Powered Resume Screener"
   ```

4. **Push to GitHub**:
   ```powershell
   git branch -M main
   git push -u origin main
   ```

> [!IMPORTANT]
> Your `.gitignore` is already configured to exclude `.streamlit/secrets.toml` and `.env` files. This ensures your API keys stay safe and are not pushed to GitHub.
