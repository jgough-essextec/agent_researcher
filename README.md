# Deep Prospecting Engine

An AI-powered prospect research tool that helps sales teams gather comprehensive intelligence on potential clients. Built with Django (backend) and Next.js (frontend), powered by Google Gemini for AI research capabilities.

## Features

### Core Research Capabilities
- **Deep Client Research** - Automated company analysis including overview, decision makers, pain points, and opportunities
- **Digital Maturity Assessment** - Evaluate prospect's technology adoption and AI readiness
- **Competitor Case Studies** - Find relevant AI/technology implementations from competitors
- **Gap Analysis** - Identify technology, capability, and process gaps with recommendations

### Ideation & Asset Generation
- **Use Case Generation** - AI-generated use cases with feasibility assessments
- **Refined Sales Plays** - Polished sales plays with elevator pitches and objection handlers
- **Buyer Personas** - Detailed persona profiles for targeted selling
- **One-Pagers** - Auto-generated sales documents
- **Account Plans** - Strategic account planning documents

### Project-Based Workflow (New)
- **Projects** - Wrap client engagements in projects for iterative research
- **Iterations** - Run multiple research iterations, building on previous findings
- **Context Accumulation** - Optionally carry forward insights between iterations
- **Work Products** - Star and save important findings as "keepers"
- **Annotations** - Add notes to any research output
- **Iteration Comparison** - Side-by-side diff view between iterations

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│                    Next.js 14 + React 18                     │
│                  Tailwind CSS + TypeScript                   │
└─────────────────────────┬───────────────────────────────────┘
                          │ REST API
┌─────────────────────────┴───────────────────────────────────┐
│                         Backend                              │
│                    Django 5 + DRF                            │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  Research   │  │  Ideation   │  │   Assets    │          │
│  │   Module    │  │   Module    │  │   Module    │          │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘          │
│         │                │                │                  │
│  ┌──────┴────────────────┴────────────────┴──────┐          │
│  │              LangGraph Workflow               │          │
│  │           (Orchestrates AI Research)          │          │
│  └──────────────────────┬────────────────────────┘          │
│                         │                                    │
│  ┌──────────────────────┴────────────────────────┐          │
│  │              Google Gemini API                │          │
│  └───────────────────────────────────────────────┘          │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   SQLite    │  │  ChromaDB   │  │  Projects   │          │
│  │  Database   │  │Vector Store │  │   Module    │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└──────────────────────────────────────────────────────────────┘
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Google Gemini API key

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local if needed (default API URL is http://localhost:8000)

# Start development server
npm run dev
```

### Access the Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/
- Django Admin: http://localhost:8000/admin/

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode | `True` |
| `SECRET_KEY` | Django secret key | Required |
| `GEMINI_API_KEY` | Google Gemini API key | Required |
| `CHROMA_PERSIST_DIR` | ChromaDB storage path | `./chroma_data` |
| `ALLOWED_HOSTS` | Allowed host names | `localhost,127.0.0.1` |
| `CORS_ALLOWED_ORIGINS` | CORS origins | `http://localhost:3000` |

### Frontend (`frontend/.env.local`)

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |

## API Endpoints

### Research

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/research/` | POST | Create new research job |
| `/api/research/{id}/` | GET | Get research job status/results |
| `/api/research/{id}/report/` | GET | Get structured research report |
| `/api/research/{id}/competitors/` | GET | Get competitor case studies |
| `/api/research/{id}/gaps/` | GET | Get gap analysis |

### Projects

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/projects/` | GET, POST | List/create projects |
| `/api/projects/{id}/` | GET, PUT, DELETE | Project detail |
| `/api/projects/{id}/iterations/` | GET, POST | List/create iterations |
| `/api/projects/{id}/iterations/{seq}/` | GET | Iteration detail |
| `/api/projects/{id}/iterations/{seq}/start/` | POST | Start research for iteration |
| `/api/projects/{id}/work-products/` | GET, POST | Manage saved items |
| `/api/projects/{id}/annotations/` | GET, POST | Manage notes |
| `/api/projects/{id}/timeline/` | GET | Get timeline view data |
| `/api/projects/{id}/compare/?a=1&b=2` | GET | Compare two iterations |

### Prompts

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/prompts/default/` | GET, PUT | Get/update default prompt |

## Project Structure

```
.
├── backend/
│   ├── backend/           # Django project settings
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── dev.py
│   │   │   └── prod.py
│   │   └── urls.py
│   ├── research/          # Research job management
│   │   ├── models.py      # ResearchJob, ResearchReport, GapAnalysis
│   │   ├── graph/         # LangGraph workflow
│   │   └── views.py
│   ├── ideation/          # Use case & play generation
│   │   └── models.py      # UseCase, FeasibilityAssessment, RefinedPlay
│   ├── assets/            # Asset generation
│   │   └── models.py      # Persona, OnePager, AccountPlan, Citation
│   ├── projects/          # Project-based workflow
│   │   ├── models.py      # Project, Iteration, WorkProduct, Annotation
│   │   ├── services/
│   │   │   ├── context.py # ContextAccumulator
│   │   │   └── comparison.py
│   │   └── views.py
│   ├── prompts/           # Prompt template management
│   └── memory/            # Vector store / knowledge base
│
├── frontend/
│   ├── app/               # Next.js App Router pages
│   │   ├── page.tsx       # Quick research (home)
│   │   └── projects/      # Project pages
│   │       ├── page.tsx   # Project list
│   │       ├── new/       # Create project
│   │       └── [id]/      # Project dashboard
│   ├── components/
│   │   ├── ResearchForm.tsx
│   │   ├── ResearchResults.tsx
│   │   ├── Navigation.tsx
│   │   └── projects/      # Project components
│   ├── lib/
│   │   └── api.ts         # API client
│   └── types/
│       └── index.ts       # TypeScript interfaces
│
└── README.md
```

## Usage

### Quick Research (Single Job)

1. Go to the home page
2. Enter client name and optional sales history
3. Click "Start Research"
4. View results in tabbed interface (Overview, Report, Competitors, Gaps)

### Project-Based Research (Iterative)

1. Go to **Projects** in the navigation
2. Click **New Project** and enter project details
3. Choose context mode:
   - **Build Context**: Each iteration learns from previous findings
   - **Fresh Start**: Each iteration starts clean
4. Click **Start First Iteration** and enter sales context
5. Review results, star important findings
6. Add new iterations to refine research
7. Use **Compare** to see differences between iterations

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm run test
```

### Building for Production

```bash
# Backend
cd backend
python manage.py collectstatic

# Frontend
cd frontend
npm run build
```

## Tech Stack

### Backend
- **Django 5** - Web framework
- **Django REST Framework** - API layer
- **LangGraph** - AI workflow orchestration
- **Google Gemini** - Large language model
- **ChromaDB** - Vector database for knowledge storage
- **SQLite** - Primary database (dev)

### Frontend
- **Next.js 14** - React framework with App Router
- **React 18** - UI library
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **React Hook Form** - Form handling

## License

Proprietary - All rights reserved.

## Contributing

Internal project - contact the development team for contribution guidelines.
