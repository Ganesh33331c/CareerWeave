# 🕸️ CareerWeave — Multi-Agent Job Orchestrator

> **GEN AI APAC Hackathon** · Track 1: AI Agents with Gemini, ADK & Cloud Run

CareerWeave is a fully autonomous multi-agent pipeline that scrapes live job listings,
scores your resume against ATS keywords, rewrites your resume bullets with JD-matching
language, and generates targeted interview questions — all in a single click.

---

## 🏗️ Architecture

```
User Input (Resume PDF + Target Role)
            │
            ▼
┌─────────────────────────────────────────────────────┐
│                  CareerWeave Pipeline                │
│                                                     │
│  ┌──────────────┐    ┌──────────────────────────┐  │
│  │  Agent 1     │    │  Agents 2 + 3 + 4        │  │
│  │  Scout       │───▶│  Analyst + Architect      │  │
│  │              │    │  + Coach                  │  │
│  │  SerpApi     │    │                           │  │
│  │  Google Jobs │    │  Gemini 1.5 Flash         │  │
│  │  Engine      │    │  LangChain PromptTemplate  │  │
│  └──────────────┘    └──────────────────────────┘  │
│                                                     │
│  Returns JSON: ats_score · tailored_summary ·       │
│  tailored_bullets · skills_gap · interview_qs       │
└─────────────────────────────────────────────────────┘
            │
            ▼
    Streamlit UI Results
    (Job Card · ATS Progress · Resume Diff · Interview Prep)
```

## 🗂️ File Structure

```
careerweave/
├── app.py                    # Main Streamlit application (single-file)
├── requirements.txt          # Python dependencies
├── Dockerfile                # Container definition for Cloud Run
├── .dockerignore             # Exclude files from Docker build context
├── cloudbuild.yaml           # Cloud Build CI/CD pipeline (auto-deploy)
├── deploy.sh                 # One-click manual deploy script
├── .gitignore                # Never commit secrets
├── .streamlit/
│   └── config.toml           # Streamlit server config (headless + dark theme)
└── README.md                 # This file
```

---

## ⚡ Quick Start — Local Development

### 1. Clone & set up environment

```bash
git clone https://github.com/YOUR_USERNAME/careerweave.git
cd careerweave

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Run locally

```bash
streamlit run app.py
# Opens at http://localhost:8501
```

### 3. Configure in the sidebar

- Paste your **Gemini API key** → [Get it here](https://aistudio.google.com)
- Paste your **SerpApi key** → [Get it here](https://serpapi.com) (100 free searches/month)
- Upload your **resume** (PDF or DOCX)
- Type a **target role** (e.g. `Cybersecurity Analyst India`)
- Click **Deploy CareerWeave Agents** 🚀

---

## ☁️ Google Cloud Run Deployment

### Prerequisites (one-time setup)

```bash
# Install gcloud CLI if not already installed
# https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login
gcloud auth application-default login

# Set your project
gcloud config set project YOUR_PROJECT_ID
```

### Option A — One-click deploy script (recommended)

```bash
chmod +x deploy.sh

# Deploy with defaults (region: asia-south1 / Mumbai)
./deploy.sh

# Or override region
REGION=us-central1 ./deploy.sh
```

This script automatically:
1. Enables all required GCP APIs
2. Creates an Artifact Registry Docker repository
3. Builds and pushes the Docker image
4. Deploys to Cloud Run with the right settings

### Option B — Cloud Build CI/CD (auto-deploy on git push)

**Step 1: Create Artifact Registry repo**
```bash
gcloud artifacts repositories create careerweave-repo \
    --repository-format=docker \
    --location=asia-south1 \
    --description="CareerWeave Docker images"
```

**Step 2: Submit a manual build**
```bash
gcloud builds submit \
    --config cloudbuild.yaml \
    --substitutions _REGION=asia-south1,_SERVICE_NAME=careerweave,_REPO_NAME=careerweave-repo \
    .
```

**Step 3: Connect GitHub for auto-deploy**
1. Go to **Cloud Build → Triggers** in the Google Cloud Console
2. Click **Create Trigger**
3. Connect your GitHub repository
4. Set **Configuration file** to `cloudbuild.yaml`
5. Set trigger to `Push to main branch`

Every `git push origin main` will now auto-build and deploy.

### Option C — Manual gcloud run deploy

```bash
# Build and push image first
IMAGE="asia-south1-docker.pkg.dev/YOUR_PROJECT/careerweave-repo/careerweave:latest"

gcloud builds submit --tag $IMAGE .

# Deploy to Cloud Run
gcloud run deploy careerweave \
    --image=$IMAGE \
    --region=asia-south1 \
    --allow-unauthenticated \
    --memory=512Mi \
    --port=8080
```

---

## 🔑 API Keys

| Service | Key | Free Tier | Link |
|---------|-----|-----------|------|
| **Google Gemini** | Gemini API Key | 1500 req/day (Flash) | [aistudio.google.com](https://aistudio.google.com) |
| **SerpApi** | SerpApi Key | 100 searches/month | [serpapi.com](https://serpapi.com) |

> **Security note:** API keys are entered by users in the Streamlit sidebar at runtime.
> They are **never stored** server-side, never logged, and never committed to code.

---

## 🛡️ GCP Services Used

| Service | Purpose |
|---------|---------|
| **Cloud Run** | Serverless container hosting |
| **Artifact Registry** | Docker image storage |
| **Cloud Build** | CI/CD pipeline |
| **Cloud Logging** | Runtime logs |
| **Secret Manager** | *(Optional)* Store keys server-side |

---

## 💰 Cost Estimate (Cloud Run)

Cloud Run charges only for actual request processing time.

| Scenario | Est. Cost |
|----------|-----------|
| Hackathon demo (< 100 requests) | **~$0** (within free tier) |
| 1,000 requests/month | **~$0.10 - $0.50** |
| Scale-to-zero (min-instances=0) | No idle charges |

---

## 🧱 Tech Stack

| Layer | Technology |
|-------|-----------|
| UI Framework | [Streamlit](https://streamlit.io) |
| LLM | [Gemini 1.5 Flash](https://aistudio.google.com) via `google-generativeai` |
| Orchestration | [LangChain](https://langchain.com) `PromptTemplate` |
| Job Scraping | [SerpApi](https://serpapi.com) Google Jobs Engine |
| Document Parsing | `PyPDF2` + `docx2txt` |
| Containerisation | Docker → Google Artifact Registry |
| Deployment | Google Cloud Run (serverless) |
| CI/CD | Google Cloud Build |

---

## 🏆 Hackathon Notes

- **Track:** GEN AI APAC — Track 1: AI Agents with Gemini, ADK & Cloud Run
- **Key differentiators:**
  - True multi-agent pipeline (not a single prompt wrapper)
  - Live job data via SerpApi — not static mock data
  - Structured JSON output enforced via LangChain prompt engineering
  - ATS scoring with visual feedback + skills gap analysis
  - Production-ready Cloud Run deployment with CI/CD

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
