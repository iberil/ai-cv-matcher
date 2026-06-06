# CV-Matcher - AI-Powered Resume and Job Matching System

A comprehensive web application that uses advanced NLP and machine learning to match job seekers with suitable job postings and analyzes CV compliance with Applicant Tracking Systems (ATS).

## 🎯 Features

### For Job Seekers (Adaylar)
- **CV Upload & Analysis**: Upload PDF resumes for automatic feature extraction
- **ATS Compliance Analysis**: Get detailed insights on how ATS-friendly your CV is
- **AI Career Coach**: Interactive career advice powered by AI
- **Job Matching**: Find jobs that match your skills and experience
- **Application Tracking**: Manage your job applications in one place
- **CV Quality Scoring**: Get recommendations to improve your resume

### For Employers (İşverenler)
- **Job Posting**: Create and manage job listings
- **Candidate Matching**: Find the best candidates for your positions
- **Competitor Analysis**: Compare your job postings with market trends
- **Salary Analysis**: Understand market salary ranges
- **Candidate Pipeline**: Review and evaluate matched candidates

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI 0.104.1
- **Database**: SQLAlchemy ORM with PostgreSQL support
- **Authentication**: JWT + OAuth
- **AI/ML**: 
  - Sentence Transformers for semantic similarity
  - BERT-NER for named entity recognition
  - Hugging Face Inference API (Qwen2.5-72B)
  - NLTK for NLP tasks
- **PDF Processing**: pdfplumber, PyPDF
- **Security**: bcrypt, passlib

### Frontend
- **Framework**: Next.js 14+ with TypeScript
- **Styling**: Tailwind CSS
- **Components**: shadcn/ui
- **HTTP Client**: Axios/Fetch API

### DevOps
- **Containerization**: Docker
- **Orchestration**: Docker Compose

## 📋 Project Structure

```
cv-matcher/
├── backend/                    # Python FastAPI application
│   ├── app/
│   │   ├── api/endpoints/     # API route handlers
│   │   ├── core/              # Database, config, security
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   └── main.py            # FastAPI app
│   ├── requirements.txt        # Python dependencies
│   ├── .env                    # Environment variables
│   └── docker-compose.yml      # Docker configuration
├── frontend/                   # Next.js application
│   └── resume-matcher/
│       ├── app/               # Next.js app directory
│       ├── components/        # React components
│       ├── lib/               # Utilities
│       ├── package.json       # Node dependencies
│       └── README.md          # Frontend docs
├── data/                       # Sample job data by sector
└── docker-compose.yml          # Root Docker Compose

```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.10+ (for local development)
- Node.js 18+ (for local frontend development)

### Using Docker (Recommended)

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/cv-matcher.git
cd cv-matcher
```

2. **Configure environment**
```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

3. **Start services**
```bash
docker-compose up -d
```

4. **Access the application**
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Local Development

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

#### Frontend Setup
```bash
cd frontend/resume-matcher
npm install
npm run dev
```

## 🔐 Environment Variables

### Backend (.env)
```env
DATABASE_URL=postgresql://user:password@localhost:5432/cv_matcher
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
HF_TOKEN=your-huggingface-token
HF_MODEL=Qwen/Qwen2.5-72B-Instruct
HF_API_URL=https://api-inference.huggingface.co/v1/chat/completions
```

## 📚 API Documentation

### Authentication
- **POST** `/api/v1/auth/register` - Register new user
- **POST** `/api/v1/auth/login` - User login
- **POST** `/api/v1/auth/logout` - User logout

### CV Management
- **POST** `/api/v1/cv/upload-and-analyze` - Upload and analyze CV
- **POST** `/api/v1/cv/confirm-and-save` - Save CV to database
- **GET** `/api/v1/cv/my-resumes` - List user's CVs
- **DELETE** `/api/v1/cv/resume/{resume_id}` - Delete CV

### ATS Analysis
- **POST** `/api/v1/cv/{cv_id}/analyze-ats` - Analyze CV for ATS compliance
- **GET** `/api/v1/cv/{cv_id}/career-advice` - Get AI career coaching
- **POST** `/api/v1/cv/{cv_id}/career-chat` - Interactive career chat

### Job Matching
- **POST** `/api/v1/match-jobs` - Find matching jobs
- **GET** `/api/v1/jobs/{job_id}/matches` - Find matching candidates

### Job Management
- **POST** `/api/v1/jobs` - Create job posting
- **GET** `/api/v1/jobs` - List active jobs
- **PUT** `/api/v1/jobs/{job_id}` - Update job
- **DELETE** `/api/v1/jobs/{job_id}` - Delete job

See full API documentation at `/docs` when running the server.

## 🤖 How It Works

### CV Analysis Pipeline
1. **PDF Extraction**: Extract text from uploaded CV using pdfplumber
2. **Feature Extraction**: Use Qwen2.5-72B LLM for intelligent data extraction
3. **Fallback System**: Regex + NER for robustness if LLM fails
4. **ATS Compliance**: Check formatting, keywords, and structure
5. **Profile Creation**: Save extracted data to database

### Job Matching Algorithm
1. **Base Similarity**: Calculate semantic similarity using Sentence Transformers
2. **Skill Matching**: Analyze required vs. available skills
3. **Experience Analysis**: Evaluate years and field relevance
4. **Education Compatibility**: Match education requirements
5. **Final Score**: Weighted combination of all factors

### Career Coaching
- Real-time advice using Qwen2.5-72B
- Personalized recommendations based on CV analysis
- Interactive chat for specific questions

## 📊 Database Schema

Key entities:
- **Users**: Job seekers and employers
- **Resumes**: Uploaded CVs with extracted data
- **Experiences**: Work history
- **Educations**: Educational background
- **Skills**: Technical and soft skills
- **JobPostings**: Job listings
- **JobApplications**: Application records
- **CVJobMatch**: Matching scores between CVs and jobs

## 🔍 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend/resume-matcher
npm test
```

## 📈 Performance Optimization

- Semantic similarity caching
- Database query optimization with indexed fields
- Lazy loading of CV data
- API response pagination
- Frontend code splitting

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Authors

- **Your Name** - Initial work

## 🙏 Acknowledgments

- Hugging Face for API access and models
- OpenAI for inspiration
- Contributors and testers

## 📧 Support

For support, email support@cvmatcher.com or open an issue on GitHub.

## 🐛 Known Issues

- Large PDF files (>50MB) may take longer to process
- Turkish character encoding requires UTF-8 support
- Some old PDF formats may not extract perfectly

## 🗺️ Roadmap

- [ ] Mobile app (React Native)
- [ ] Email notifications
- [ ] Advanced analytics dashboard
- [ ] Multi-language support beyond Turkish/English
- [ ] Video interview integration
- [ ] Skill assessment tests
- [ ] LinkedIn integration
