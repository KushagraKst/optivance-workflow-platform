# Optivance Workflow Platform

A Flask based web application that provides task management, analytics, and team collaboration features.

## Features
- User authentication and session management
- Task CRUD operations with SQLite persistence
- Team creation and invitation workflow
- Analytics dashboards for tasks and decisions
- Modular architecture with blueprints and services

## Project Structure
```
optivance-workflow-platform/
├─ app.py                 # Flask app entry point
├─ create_db.py          # Database schema creation script
├─ insert_data.py        # Sample data insertion script
├─ backend/              # Backend related code (if any)
├─ frontend/              # Frontend assets (static, templates)
├─ models/                # SQLAlchemy models
├─ routes/                # Blueprint route definitions
├─ services/              # Business logic services
├─ static/                # CSS, JS, images
├─ templates/             # Jinja2 HTML templates
├─ Dockerfile            # Container build file
├─ requirements.txt       # Python dependencies
├─ README.md             # This file
└─ tests/                # Pytest test suite
```

## Setup (Local Development)
1. **Clone the repository**
   ```bash
   git clone https://github.com/KushagraKst/optivance-workflow-platform.git
   cd optivance-workflow-platform
   ```
2. **Create a virtual environment and install dependencies**
   ```bash
   python -m venv venv
   venv\Scripts\activate   # on Windows
   pip install -r requirements.txt
   ```
3. **Initialize the SQLite database**
   ```bash
   python create_db.py
   ```
4. **Run the development server**
   ```bash
   flask run
   ```
   The app will be available at `http://127.0.0.1:5000/`.

## Docker Deployment
A `Dockerfile` is provided for containerised deployment.
```bash
# Build the image
docker build -t optivance:latest .

# Run the container (exposes port 5000)
docker run -d -p 5000:5000 \
  -e FLASK_SECRET_KEY=your_secret_key \
  -v $(pwd)/database:/app/database \
  optivance:latest
```
The volume mount ensures the SQLite database persists across container restarts.

## Render.com Deployment
1. **Create a new Web Service** on Render and connect it to this GitHub repository.
2. **Set the build command** (Render auto-detects Docker) – no additional configuration needed.
3. **Add an environment variable** `FLASK_SECRET_KEY` with a secure random value.
4. **Configure a Persistent Disk**:
   - Mount point: `/app/database`
   - Size: 1 GB (or larger as needed)
5. Render will automatically build the Docker image and deploy the service.

## Testing
Run the test suite with:
```bash
pytest
```

## Contributing
Contributions are welcome! Please fork the repository, create a feature branch, and submit a pull request. Follow the existing code style and ensure all tests pass.

## License
This project is licensed under the MIT License.
