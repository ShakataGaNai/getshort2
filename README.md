# GetShort URL Shortener

GetShort is a simple, powerful URL shortener service that allows you to create shortened URLs that are easy to share and track visitor analytics.

## Features

- **Simple URL Shortening**: Create short URLs with just a few clicks
- **Custom URLs**: Create memorable URLs for your brand or campaign
- **Comprehensive Analytics**: Track visitor data including browser, device type, and location
- **User Authentication**: Secure GitHub OAuth integration
- **API Support**: REST API for URL management and analytics
- **Containerized Deployment**: Docker and Kubernetes support

## Tech Stack

- **Backend**: Python 3.12, Flask
- **Database**: SQLite (development), MySQL/MariaDB (production)
- **Authentication**: GitHub OAuth
- **Analytics**: GeoIP2 for location tracking
- **Deployment**: Docker, Kubernetes

## Installation

### Local Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/ShakataGaNai/getshort2.git
   cd getshort2
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the project root and add:
   ```
   SECRET_KEY=your-secret-key
   GITHUB_CLIENT_ID=your-github-client-id
   GITHUB_CLIENT_SECRET=your-github-client-secret
   # Optional: GEOIP_DB_PATH=path/to/your/GeoLite2-City.mmdb
   ```

5. Run the application:
   ```bash
   python run.py
   ```

The app will be available at http://localhost:5000

## Docker Setup and Testing

### Using Pre-built Images from GitHub Packages

We provide pre-built Docker images via GitHub Packages:

```bash
# Pull the latest image
docker pull ghcr.io/shakatagaNai/getshort2:latest

# Run the container
docker run -p 8000:8000 \
  -e SECRET_KEY=your-secret-key \
  -e GITHUB_CLIENT_ID=your-github-client-id \
  -e GITHUB_CLIENT_SECRET=your-github-client-secret \
  -e PORT=8000 \
  ghcr.io/shakatagaNai/getshort2:latest
```

Available tags:
- `latest`: Latest version from the main branch
- `vX.Y.Z`: Specific version (e.g., `v1.0.0`)
- `vX.Y`: Latest patch version of minor release (e.g., `v1.0`)
- `vX`: Latest minor version of major release (e.g., `v1`)
- `sha-XXXXXXX`: Specific Git commit SHA

### Building and Running with Docker

1. Build the Docker image:
   ```bash
   docker build -t getshort:latest .
   ```

2. Run the container with SQLite (development mode):
   ```bash
   docker run -p 8000:8000 \
     -e SECRET_KEY=your-secret-key \
     -e GITHUB_CLIENT_ID=your-github-client-id \
     -e GITHUB_CLIENT_SECRET=your-github-client-secret \
     -e PORT=8000 \
     getshort:latest
   ```

3. Run with MariaDB (production-like setup):
   ```bash
   # First start a MariaDB container
   docker run --name getshort-db \
     -e MYSQL_ROOT_PASSWORD=rootpassword \
     -e MYSQL_DATABASE=getshort \
     -e MYSQL_USER=getshort \
     -e MYSQL_PASSWORD=getshortpass \
     -d mariadb:10.5

   # Then start the application container linked to the database
   docker run -p 8000:8000 \
     --link getshort-db:db \
     -e SECRET_KEY=your-secret-key \
     -e GITHUB_CLIENT_ID=your-github-client-id \
     -e GITHUB_CLIENT_SECRET=your-github-client-secret \
     -e DB_TYPE=mysql \
     -e DB_USER=getshort \
     -e DB_PASSWORD=getshortpass \
     -e DB_HOST=db \
     -e DB_NAME=getshort \
     -e PORT=8000 \
     getshort:latest
   ```

4. Check that the application is running:
   ```bash
   curl http://localhost:8000
   ```

### Docker Compose (Alternative Setup)

Create a `docker-compose.yml` file:

```yaml
version: '3'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SECRET_KEY=your-secret-key
      - GITHUB_CLIENT_ID=your-github-client-id
      - GITHUB_CLIENT_SECRET=your-github-client-secret
      - DB_TYPE=mysql
      - DB_USER=getshort
      - DB_PASSWORD=getshortpass
      - DB_HOST=db
      - DB_NAME=getshort
      - PORT=8000
    depends_on:
      - db
    restart: always

  db:
    image: mariadb:10.5
    environment:
      - MYSQL_ROOT_PASSWORD=rootpassword
      - MYSQL_DATABASE=getshort
      - MYSQL_USER=getshort
      - MYSQL_PASSWORD=getshortpass
    volumes:
      - db_data:/var/lib/mysql
    restart: always

volumes:
  db_data:
```

Then run:
```bash
docker-compose up -d
```

### Running Tests in Docker

1. Create a Docker container for testing:
   ```bash
   docker build -t getshort-test -f Dockerfile.test .
   ```

   Where `Dockerfile.test` is:
   ```
   FROM python:3.12-slim

   WORKDIR /app

   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   RUN pip install pytest pytest-cov

   COPY . .

   CMD ["pytest", "-v", "--cov=app"]
   ```

2. Run the tests:
   ```bash
   docker run --rm getshort-test
   ```

## Kubernetes Setup and Testing

### Prerequisites

- A Kubernetes cluster (Minikube, Docker Desktop Kubernetes, GKE, EKS, etc.)
- `kubectl` installed and configured to connect to your cluster
- Optionally: Helm for easier deployments

### Testing with Minikube

1. Start Minikube:
   ```bash
   minikube start
   ```

2. Build the Docker image in Minikube's Docker daemon:
   ```bash
   eval $(minikube docker-env)
   docker build -t getshort:latest .
   ```

3. Create a Kubernetes namespace:
   ```bash
   kubectl create namespace getshort
   ```

4. Create Secret:
   ```bash
   # Base64 encode your secrets
   echo -n "your-secret-key" | base64
   echo -n "your-github-client-id" | base64
   echo -n "your-github-client-secret" | base64
   
   # Create a local secrets file with the base64 values
   cat > kubernetes/secrets-local.yaml << EOF
   apiVersion: v1
   kind: Secret
   metadata:
     name: getshort-secrets
     namespace: getshort
   type: Opaque
   data:
     secret-key: $(echo -n "your-secret-key" | base64)
     db-user: $(echo -n "getshort" | base64)
     db-password: $(echo -n "getshortpass" | base64)
     github-client-id: $(echo -n "your-github-client-id" | base64)
     github-client-secret: $(echo -n "your-github-client-secret" | base64)
   EOF
   
   # Apply the secrets
   kubectl apply -f kubernetes/secrets-local.yaml
   ```

5. Apply the Kubernetes manifests:
   ```bash
   kubectl apply -f kubernetes/mariadb.yaml -n getshort
   kubectl apply -f kubernetes/deployment.yaml -n getshort
   kubectl apply -f kubernetes/service.yaml -n getshort
   ```

6. For local access, create a port-forward:
   ```bash
   kubectl port-forward -n getshort svc/getshort-service 8000:80
   ```

7. Visit `http://localhost:8000` in your browser

### Testing with kubectl

Check your deployment status:
```bash
# Check if pods are running
kubectl get pods -n getshort

# Check logs from the application
kubectl logs -n getshort deployment/getshort

# Describe services
kubectl describe svc getshort-service -n getshort

# Get detailed information about pods
kubectl describe pods -n getshort
```

### LoadBalancer Service (Cloud Environments)

For cloud environments, you can modify the service to use a LoadBalancer:

```yaml
# kubernetes/service-cloud.yaml
apiVersion: v1
kind: Service
metadata:
  name: getshort-service
spec:
  selector:
    app: getshort
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

Apply it with:
```bash
kubectl apply -f kubernetes/service-cloud.yaml -n getshort
```

### Cleaning Up

To remove all resources:
```bash
kubectl delete namespace getshort
```

## CI/CD Pipeline

GetShort uses GitHub Actions for continuous integration and delivery:

### Automated Docker Builds

The repository includes a GitHub Actions workflow (`.github/workflows/docker-build-publish.yml`) that:

1. Builds the Docker image on every push to main, version branches (v*), version tags, and pull requests
2. Runs tests in a containerized environment
3. Publishes images to GitHub Container Registry (ghcr.io) with appropriate tags

### Docker Image Tags

The workflow automatically tags the Docker images with:

- Branch name (e.g., `main`, `v1`)
- Semantic version tags for releases (e.g., `v1.0.0`, `v1.0`, `v1`)
- Git commit SHA (e.g., `sha-1a2b3c4`)
- `latest` tag for the main branch

### How to Use the CI/CD Pipeline

1. For feature development:
   - Create a feature branch and open a pull request
   - The workflow will build and test your changes

2. For releases:
   - Tag your release with a semantic version (e.g., `v1.0.0`)
   - Push the tag to trigger a build and publish workflow
   - The image will be published with semantic versioning tags

3. To use the published images:
   ```bash
   docker pull ghcr.io/shakatagaNai/getshort2:latest
   ```

## Configuration

All configuration is managed through environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| SECRET_KEY | Flask secret key | dev-key-please-change-in-production |
| DB_TYPE | Database type (sqlite or mysql) | sqlite |
| DB_USER | Database username (MySQL only) | - |
| DB_PASSWORD | Database password (MySQL only) | - |
| DB_HOST | Database host (MySQL only) | - |
| DB_NAME | Database name (MySQL only) | getshort |
| DATABASE_URL | Full database URL (alternative to individual settings) | - |
| GITHUB_CLIENT_ID | GitHub OAuth client ID | - |
| GITHUB_CLIENT_SECRET | GitHub OAuth client secret | - |
| GEOIP_DB_PATH | Path to GeoIP database | GeoLite2-City.mmdb |
| LOG_TO_STDOUT | Whether to log to stdout (good for containers) | false |

## API Usage

### Get all URLs for the current user

```
GET /api/urls
```

### Create a new short URL

```
POST /api/urls
Content-Type: application/json

{
  "target_url": "https://example.com",
  "custom_code": "optional-custom-code"
}
```

### Get analytics for a specific URL

```
GET /api/urls/{url_id}/analytics
```

### Delete a URL

```
DELETE /api/urls/{url_id}
```

## Development

### Database Migrations

To create and apply migrations:

```bash
flask db init  # Only once
flask db migrate -m "Initial migration"
flask db upgrade
```

### Running Tests

```bash
pytest
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.