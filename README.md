# NutriTrack
**Intelligent Malnutrition Analysis and Early Risk Identification System**

NutriTrack is a full-stack educational prototype for recording nutrition-related measurements, exploring descriptive indicators, reviewing assessment history and viewing general food guidance. It is not a medical device and does not diagnose malnutrition or nutrient deficiencies.

## Features
- Registration, login, logout and PBKDF2 password hashing
- Signed, expiring bearer tokens
- User-owned assessment records and persistent SQLite database
- BMI calculation for descriptive adult screening only
- Under-20 records explicitly require age- and sex-specific growth references; this prototype does not calculate percentiles
- Transparent screening observations, not a trained malnutrition classifier
- Unsupervised Isolation Forest anomaly exploration after at least five records; this is not a health-risk prediction
- General Indian food suggestions, PDF assessment reports and interactive Chart.js trend view
- Admin statistics and user listing with role-based authorization
- FastAPI Swagger documentation, automated tests, Docker and GitHub Actions CI

## Technology
Python 3.12, FastAPI, SQLAlchemy, SQLite, scikit-learn, NumPy, HTML, CSS, JavaScript, Chart.js, ReportLab, Docker and GitHub Actions.

## Run locally in VS Code
1. Install Python 3.12.
2. Extract the ZIP and open the `NutriTrack_Complete_Project` folder in VS Code.
3. Open the terminal in the project root.
4. Create and activate a virtual environment:
   - Windows: `py -3.12 -m venv venv`
   - Windows PowerShell: `.\venv\Scripts\Activate.ps1`
   - Windows CMD: `venv\Scripts\activate`
   - macOS/Linux: `python3.12 -m venv venv` then `source venv/bin/activate`
5. Install: `python -m pip install -r requirements.txt`
6. Start: `python -m uvicorn backend.main:app --reload`
7. Open `http://127.0.0.1:8000` and API docs at `http://127.0.0.1:8000/docs`.

The database is created automatically in `data/nutritrack.db`.

## Demo administrator
The local demo administrator is created on first startup:
- Email: `admin@nutritrack.local`
- Password: `ChangeThisAdminPassword123!`

Change these values using environment variables before any shared or deployed use. This default is for local demonstration only.

## Docker
Build and start: `docker compose up --build`
Stop: `docker compose down`
Stop and remove database volume: `docker compose down -v` (this permanently deletes stored demo records)
View containers: `docker compose ps`
View logs: `docker compose logs -f`
The named `nutritrack_data` volume persists SQLite data.

## GitHub Actions
The workflow at `.github/workflows/ci-cd.yml` runs on pushes and pull requests. It installs dependencies, runs pytest and builds the Docker image. It is a CI validation pipeline; it does not deploy to a cloud host. Add a deployment job only after selecting a host and configuring its secrets.

## Tests
Run: `python -m pytest -q`

## API overview
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `GET /api/summary`
- `GET/POST /api/assessments`
- `GET/DELETE /api/assessments/{id}`
- `GET /api/assessments/{id}/report`
- `GET /api/recommendations`
- `GET /api/ml/status`
- `GET /api/admin/stats` and `/api/admin/users`

Swagger UI: `/docs`.

## ML and clinical limitations
No validated, appropriately licensed labelled malnutrition dataset was supplied for this project. In accordance with the project specification, no synthetic labels or invented classifier accuracy are presented. The assessment result uses transparent, limited prototype rules and clearly labels its limitations. Isolation Forest is used only for unsupervised exploration of unusual combinations in the user's saved measurements; it is not a malnutrition predictor. No model accuracy, precision, recall, F1 score or confusion matrix is claimed because there is no valid ground-truth labelled evaluation dataset.

Adult BMI reference values are screening references only. For anyone under 20, age- and sex-specific growth references are required; this prototype deliberately does not apply adult BMI categories to children. Dietary suggestions are general education and do not diagnose nutrient deficiencies.

## Privacy and safety
Use fictional demonstration data. Do not enter real patient-identifying information. This is a student prototype, not a substitute for qualified healthcare advice. The default local secret and administrator credentials must be changed before deployment. For production, configure HTTPS, a strong secret, restrictive CORS, rate limiting, secure session storage and a reviewed security model.

## Screenshots
Add project screenshots here after capturing your own running application.

## License
MIT License. See `LICENSE`.
