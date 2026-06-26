# CrysText – AI-Powered Materials Informatics Platform

> Search, visualize, and understand crystal structures with AI-generated scientific insights.

## Project Structure

```
crystext/
├── backend/                  # FastAPI backend
│   ├── app/
│   │   ├── main.py           # App entry point
│   │   ├── config.py         # Settings
│   │   ├── database.py       # MongoDB connection
│   │   ├── models.py         # Pydantic schemas
│   │   ├── cif_parser.py     # pymatgen CIF parser
│   │   ├── ai_service.py     # Ollama AI integration
│   │   └── routes/
│   │       ├── materials.py  # Material CRUD + search
│   │       └── favorites.py  # Favorites (session-based)
│   ├── ingest.py             # CIF ingestion script
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                 # React + Vite frontend
│   ├── src/
│   │   ├── pages/            # HomePage, MaterialPage, etc.
│   │   ├── components/       # SearchBar, CrystalViewer, etc.
│   │   └── lib/              # API client, Zustand store
│   ├── package.json
│   └── Dockerfile
├── dataset/
│   ├── cif_files/            # Place CIF files here
│   └── scripts/
│       └── download_mp.py    # Download from Materials Project
└── docker-compose.yml
```

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- MongoDB (local or Atlas)
- Ollama (optional, for AI summaries)

### 1. Add CIF files
```bash
# Option A: copy from existing data folder
copy data\cifs\*.cif dataset\cif_files\

# Option B: download 1000+ from Materials Project
cd dataset/scripts
python download_mp.py --api-key YOUR_KEY --count 1000
```

### 2. Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env        # edit if needed

# Ingest CIF files into MongoDB
python ingest.py

# Start API server
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev    # runs on http://localhost:3000
```

## Docker (full stack)
```bash
docker-compose up --build
```
Frontend → http://localhost:3000  
Backend API → http://localhost:8000  
API docs → http://localhost:8000/docs

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/materials` | List all materials (paginated) |
| GET | `/api/material/{formula}` | Get material detail |
| POST | `/api/search` | Full-text + filter search |
| GET | `/api/suggestions?q=` | Autocomplete |
| GET | `/api/similar/{formula}` | Similar materials |
| POST | `/api/compare` | Compare materials |
| GET | `/api/download/cif/{formula}` | Download CIF file |
| GET | `/api/export/pdf/{formula}` | Export PDF report |
| GET | `/api/stats` | Database statistics |
| GET/POST/DELETE | `/api/favorites` | Manage favorites |

## AI Features
CrysText uses **Ollama** with Mistral or Llama 3 to generate scientific summaries.

Install Ollama: https://ollama.ai  
Pull a model:
```bash
ollama pull mistral
# or
ollama pull llama3
```
If Ollama is not running, the app falls back to template-based summaries automatically.

## AWS Deployment
See `docs/aws-deployment.md` for EC2 + DocumentDB deployment guide.
