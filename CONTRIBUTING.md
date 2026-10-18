# Contributing to Leddro

Thank you for your interest in contributing to **Leddro**! We welcome community contributions that help make Leddro more robust, secure, and developer-friendly.

---

## Code of Conduct

Please treat everyone with respect and empathy. We are committed to providing a welcoming and harassment-free environment for all contributors.

---

## Development Setup

### Prerequisites
- **Python**: 3.11 or higher
- **Node.js**: 20.x or higher
- **Package Managers**: `pip` and `npm`

### Local Setup
1. **Clone the repository**:
   ```bash
   git clone https://github.com/PrajwalTheCoder/Leddro.git
   cd Leddro
   ```

2. **Set up Python Virtual Environment**:
   ```bash
   python -m venv .venv
   # Windows:
   .\.venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   pip install -r backend/requirements.txt
   ```

3. **Set up Frontend Dependencies**:
   ```bash
   npm install
   ```

4. **Configure Environment**:
   ```bash
   cp .env.example .env
   ```
   *Edit `.env` to configure your database (`sqlite:///./leddro.db` or Neon PostgreSQL URL) and optional AI providers.*

5. **Run the Application**:
   - Backend:
     ```bash
     uvicorn backend.app.main:app --port 8000 --reload
     ```
   - Frontend:
     ```bash
     npm run dev
     ```

---

## Testing Guidelines

Before submitting any Pull Request, ensure that all automated tests pass:

1. **Backend Tests**:
   ```bash
   pytest
   ```
2. **Frontend Type Check & Build**:
   ```bash
   npx tsc --noEmit
   npm run build
   ```
3. **Secret Verification**:
   Ensure no API keys, OAuth client secrets, or credentials are added to tracked files.

---

## Coding Standards

- **Backend**:
  - FastAPI with SQLAlchemy ORM.
  - Follow PEP 8 style conventions.
  - Never log raw secrets, access tokens, or sensitive user payload data.
  - Maintain SSRF protections for all outbound HTTP requests.
- **Frontend**:
  - React 18, TypeScript, TailwindCSS.
  - Retain the established design aesthetic: dark charcoal surfaces, restrained lime accents, compact typography.
  - Avoid intrusive animations or unnecessary third-party heavy dependencies.

---

## Submitting Pull Requests

1. Fork the repo and create your branch from `main`: `git checkout -b feature/my-feature`.
2. Commit your changes with clear, descriptive commit messages.
3. Push to your branch and open a Pull Request with a summary of changes and testing proof.
