# FindIt ML

A Python and Flask lost-and-found prototype for a campus. Reports are stored in SQLite. When a report is submitted, FindIt ML compares its item name, category, description, and location with reports of the opposite type and displays the closest candidates.

## How the matching works

The prototype uses **TF-IDF** to turn report text into weighted word vectors, then **cosine similarity** to rank reports. Matching category and location add small transparent boosts. It does not train a supervised classifier: a labeled dataset of confirmed matches is not available yet. Treat percentages as relative similarity scores, not probabilities that two items are the same.

## Run locally on Windows

1. Install Python 3.10 or newer from python.org and select **Add Python to PATH** during setup.
2. Open PowerShell in this folder.
3. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

4. Install packages and start the app:

   ```powershell
   python -m pip install -r requirements.txt
   python app.py
   ```

5. Visit http://127.0.0.1:5000 in your browser. Reports are saved in `findit.db`.

## Publish a free public demo

GitHub stores the source code; it does not run this Flask application. The included `render.yaml` configures a free Render web service, which provides a public `*.onrender.com` address without a custom domain.

1. Create a **public** repository on GitHub and push this project. Do not commit `.venv`, `.env`, or a local database; `.gitignore` excludes these files and the generated report documents.
2. Sign in to Render and choose **New → Blueprint**. Connect the GitHub repository and deploy the `render.yaml` configuration.
3. After the first deployment succeeds, open the service URL shown in the Render dashboard.

The hosted configuration enables public demo mode: it does not collect contact details and disables report deletion. Use fictional report details only. The free service may sleep when idle, and its SQLite database is temporary; reports can disappear when the service sleeps, restarts, or is redeployed. This is suitable for a classroom demo, not real campus operations.

### Push this folder to GitHub

After creating an empty public GitHub repository, run these commands in PowerShell from this folder (replace the URL with the repository URL shown by GitHub):

```powershell
git init
git add app.py templates static requirements.txt README.md render.yaml .gitignore
git commit -m "Prepare FindIt ML for public demo deployment"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/findit-ml.git
git push -u origin main
```

The first push may open a GitHub sign-in flow. Keep the repository public if you want anyone with the Render URL to access the demo.

## Future academic extensions

- Collect voluntary, consented examples of confirmed and rejected suggestions; use them to evaluate precision and recall and explore a supervised ranking model.
- Add image similarity with a pretrained vision model, keeping text and image scores separately visible.
- Add a campus administrator workflow, report expiry, abuse controls, and contact privacy protections before deploying beyond a demo.
- Compare TF-IDF against sentence embeddings on an anonymized evaluation set.

## Prototype limits

This is a local demonstration, not a production service. It has no authentication or moderation. Contact details appear in the report and match views, so use fictional data in demos. Do not expose it publicly without access controls, privacy review, and safe return procedures.
