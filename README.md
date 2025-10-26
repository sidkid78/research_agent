# Research Agent

An advanced AI-powered research agent that conducts comprehensive academic research using multiple sources including arXiv, PubMed, and Google Search.

## Features

### Core Capabilities
- 🔬 **Multi-Source Research**: Searches across arXiv, PubMed, and web sources
- 🤖 **AI-Powered Analysis**: Uses Google's Gemini 2.5 Flash for intelligent synthesis
- 📊 **Academic Quality Metrics**: Tracks peer-reviewed sources and authority
- 📝 **Multiple Output Formats**: Bullet points or full research reports
- 🎯 **Smart Source Selection**: Automatically chooses relevant databases
- 📚 **Citation Management**: Properly formatted references with metadata
- ⚡ **Real-time Progress**: Live updates during research process
- 🔒 **Persistent Storage**: SQLite database for job history

### Research Modes
- 📋 **Single Research**: Submit one topic, get comprehensive results
- 📦 **Batch Research**: Process multiple topics simultaneously
- 🔴 **Live Research**: Interactive sessions with real-time AI responses
- 📜 **Research History**: Browse and review all past research jobs

## Quick Start with Docker (Recommended)

### Prerequisites

- Docker and Docker Compose installed
- Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

### Setup

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd research_agent
```

2. **Configure environment**
```bash
cp env.example .env
# Edit .env and add your GEMINI_API_KEY and PUBMED_EMAIL
```

3. **Start with Docker**
```bash
# Linux/Mac
chmod +x docker-start.sh
./docker-start.sh

# Or manually
docker-compose up -d
```

4. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Available Pages

- **Main Research**: http://localhost:3000 - Submit single research requests
- **Batch Research**: http://localhost:3000/batch-research - Submit multiple topics at once
- **Live Research**: http://localhost:3000/live-research - Real-time interactive research sessions
- **Research History**: http://localhost:3000/research/history - View past research jobs

## Development Setup (Without Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install --legacy-peer-deps
npm run dev
```

### Start Both Services

```bash
# Windows PowerShell
.\start-servers.ps1

# Linux/Mac
./start-servers.sh  # Create similar script for your OS
```

## Project Structure

```
research_agent/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── main.py         # API endpoints
│   │   ├── agent.py        # Research agent logic
│   │   ├── gemini_helpers.py  # AI integration
│   │   ├── models.py       # Database models
│   │   ├── schemas.py      # Pydantic schemas
│   │   └── crud.py         # Database operations
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/               # Next.js frontend
│   ├── src/
│   │   ├── app/           # Next.js pages
│   │   ├── components/    # React components
│   │   └── lib/          # Utilities and types
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml     # Docker orchestration
├── env.example           # Environment template
└── README.md
```

## API Usage

### Submit Research Request

```bash
curl -X POST "http://localhost:8000/academic-research" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "latest developments in quantum computing",
    "output_format": "full_report",
    "email": "your@email.com"
  }'
```

### Check Job Status

```bash
curl "http://localhost:8000/research/{job_id}/status"
```

### Get Results

```bash
curl "http://localhost:8000/research/{job_id}/result"
```

## Environment Variables

### Backend

- `GEMINI_API_KEY` - Your Google Gemini API key (required)
- `PUBMED_EMAIL` - Email for PubMed API access (optional but recommended)
- `DATABASE_URL` - SQLite database path (default: `sqlite:///./research_agent.db`)

### Frontend

- `NEXT_PUBLIC_API_URL` - Backend API URL (default: `http://localhost:8000`)

## Configuration

### Research Sources

The agent automatically selects appropriate sources based on your topic:

- **arXiv**: Computer science, physics, mathematics, engineering
- **PubMed**: Medicine, biology, health sciences
- **Google Search**: General topics and current information

### Output Formats

- **Bullets**: Concise bullet-point summary (15-20 points)
- **Full Report**: Comprehensive report (1000-2000 words) with sections

## Docker Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild
docker-compose up --build -d

# Clean everything (including database)
docker-compose down -v
```

See [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for detailed Docker documentation.

## Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Google Gemini 2.5 Flash** - AI model for analysis
- **SQLAlchemy** - ORM for database
- **arXiv API** - Academic papers (CS, Physics, Math)
- **PubMed API** - Medical/biological research
- **Google Grounding** - Web search capabilities

### Frontend
- **Next.js 15** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **shadcn/ui** - Component library
- **React Hook Form** - Form management
- **Sonner** - Toast notifications

## Usage Guide

### Single Research (Main Page)
1. Navigate to http://localhost:3000
2. Enter your research topic
3. Select output format (bullets or full report)
4. Choose preferred sources (arXiv, PubMed, Web)
5. Add email if using PubMed
6. Click "Start Research" and wait for results

### Batch Research
1. Navigate to http://localhost:3000/batch-research
2. Enter multiple topics (one per line or comma-separated)
3. Configure output format and sources
4. Submit batch - all topics will be processed in parallel
5. View individual results or download all at once

### Live Research
1. Navigate to http://localhost:3000/live-research
2. Start a new research session
3. Ask questions in real-time
4. Get immediate AI-powered responses
5. Conversation history maintained throughout session

### Research History
1. Navigate to http://localhost:3000/research/history
2. Browse all past research jobs
3. Filter by status, date, or topic
4. Re-open completed research
5. Delete or archive old jobs

## Features in Detail

### Smart Query Generation

The agent uses AI to generate optimized search queries for each database, ensuring relevant results.

### Source Quality Tracking

- **Peer Review %**: Percentage of peer-reviewed sources (primarily PubMed)
- **Authority %**: Percentage from authoritative academic databases
- **Recent Sources %**: Papers from recent years

### Reference Management

All sources are properly cited with:
- Title and authors
- Publication venue and date
- Abstract/snippet
- Direct links to original papers

## Troubleshooting

### Backend Issues

```bash
# Check backend logs
docker-compose logs backend

# Common fixes:
# - Verify GEMINI_API_KEY is set correctly
# - Check port 8000 is not in use
# - Restart: docker-compose restart backend
```

### Frontend Issues

```bash
# Check frontend logs
docker-compose logs frontend

# Common fixes:
# - Clear Next.js cache: rm -rf frontend/.next
# - Rebuild: docker-compose build --no-cache frontend
```

### Database Issues

```bash
# Reset database
docker-compose down -v
docker-compose up -d
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with Docker: `docker-compose up --build`
5. Submit a pull request

## License

[Your License Here]

## Support

For issues and questions:
- Check [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for deployment help
- Review logs: `docker-compose logs`
- Open an issue on GitHub

## Acknowledgments

- Google Gemini API for AI capabilities
- arXiv for open access to research papers
- PubMed/NCBI for biomedical literature access
- Open source community for amazing tools

## Roadmap

### Implemented ✅
- [x] Multi-source research (arXiv, PubMed, Web)
- [x] Batch research for multiple topics
- [x] Live research sessions
- [x] Research history tracking
- [x] Smart source selection

### Planned 🚀
- [ ] Support for more academic databases (IEEE, Scopus, Web of Science)
- [ ] Export to multiple formats (PDF, LaTeX, BibTeX)
- [ ] Collaborative research sessions (multi-user)
- [ ] Research favorites and bookmarking
- [ ] Custom source prioritization and weights
- [ ] Citation graph visualization
- [ ] Advanced analytics dashboard
- [ ] API rate limiting and quotas
- [ ] User authentication and profiles

---

**Made with ❤️ using AI and open source**

