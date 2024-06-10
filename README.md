# CAPTCHA API

## Setup Instructions

### Prerequisites

- Git
- Docker

### Local Development with Docker

1. **Clone the repository**:
    ```sh
    git clone https://github.com/DanieleBelfiore/captcha-api.git
    cd captcha-api
    ```

2. **Create a `.env` file for environment variables**:
    Create a file named `.env` in the project root with the following content:
    ```env
    DATABASE_URL=postgresql://postgres:password@db:5432/captcha_api
    POSTGRES_USER=postgres
    POSTGRES_PASSWORD=password
    POSTGRES_DB=captcha_api
    ```

3. **Build and run the application**:
    ```sh
    docker-compose up --build
    ```

    This command will build the Docker images for the services defined in the `docker-compose.yml` file and start the containers.

4. **Access the application**:
    Open your browser and navigate to `http://localhost:8000`.

### Endpoints

#### Generate CAPTCHA

- **URL**: `/captcha`
- **Method**: `GET`
- **Response**:
  ```json
  {
    "id": 1,
    "image": "<base64_image_data>"
  }
  ```  

#### Validate CAPTCHA
- **URL**: `/captcha/validate`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "id": 1,
    "text": "ABC123"
  }
  ```
- **Response**:
  ```json
  {
    "valid": false
  }
  ```

### Running Tests

#### Run tests
```sh
pytest
```