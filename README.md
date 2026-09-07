# NEET-PG QBank — phone-deployable build

This is the FastAPI + vanilla JS NEET-PG QBank app with the Pediatrics source QBank already imported.

## Deploy with Render (recommended for phone)

1. Create a GitHub repository named `neet-pg-qbank`.
2. Upload the contents of this folder to the repository.
3. In Render, create **New → Web Service** and connect the GitHub repository.
4. Runtime: Python.
5. Build command: `pip install -r requirements.txt`
6. Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
7. Deploy. Render will provide an `onrender.com` URL.

`render.yaml` is included for reproducible configuration.

## Deploy with Railway

1. Push this folder to GitHub.
2. In Railway choose **New Project → Deploy from GitHub repo**.
3. Select this repository and deploy.
4. Railway will detect the included Dockerfile.
5. In the service's Settings → Networking, choose **Generate Domain**.

## Included

- 47 Pediatrics lessons
- 870 parsed questions from the supplied PDF
- 1310-page source PDF
- Correct answer/explanation display after submission
- Green correct answer / red selected incorrect answer
- Chapter navigation and search
- Bookmarks and progress saved in browser local storage
- Timed exam mode
- Source-page image display
- PDF upload/parser endpoint

## Important production note

The initial Pediatrics PDF and parsed JSON are bundled with the app. Uploaded replacement PDFs are written to the server filesystem; on free/ephemeral hosting they may not survive a redeploy/restart. For a production multi-user version, use object storage + PostgreSQL and authenticated admin uploads.


## Updated quiz behavior
- Practice mode displays up to 5 questions per screen.
- Every question has its own independent option selection and Submit Answer button.
- After submission, the selected wrong answer is red, the correct answer is green, and the explanation is always shown.
- Source PDF pages are mapped to the page where each question actually starts.
- The full source page is hidden inside “View source PDF page …” so multiple questions on one PDF page are not confused with the interactive question.
