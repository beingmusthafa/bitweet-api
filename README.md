# Twitter Clone API

This is a backend API for a Twitter clone application. It provides functionalities for user authentication, tweeting, following users, real-time notifications, and audio chat rooms.

## Features

*   **User Authentication:** User registration, login, logout, and profile management.
*   **Tweeting:** Create, update, delete, and view tweets.
*   **User Connections:** Follow and unfollow users.
*   **Timeline:** View a timeline of tweets from followed users.
*   **Real-time Notifications:** Receive real-time notifications for events like new followers.
*   **Audio Chat Rooms:** Create and join real-time audio chat rooms.
*   **Password Management:** Securely reset passwords using OTP.

## Tech Stack

*   **Backend:**
    *   [FastAPI](https://fastapi.tiangolo.com/): A modern, fast (high-performance), web framework for building APIs with Python 3.7+ based on standard Python type hints.
    *   [Uvicorn](https://www.uvicorn.org/): A lightning-fast ASGI server implementation, using uvloop and httptools.
    *   [SQLAlchemy](https://www.sqlalchemy.org/): The Python SQL Toolkit and Object Relational Mapper.
    *   [Alembic](https://alembic.sqlalchemy.org/en/latest/): A lightweight database migration tool for usage with the SQLAlchemy Database Toolkit for Python.
    *   [Pydantic](https://pydantic-docs.helpmanual.io/): Data validation and settings management using Python type annotations.
    *   [Celery](https://docs.celeryq.dev/en/stable/): An asynchronous task queue/job queue based on distributed message passing.
    *   [Redis](https://redis.io/): An in-memory data structure store, used as a message broker for Celery and for managing WebSocket connections.
*   **Database:**
    *   [PostgreSQL](https://www.postgresql.org/): A powerful, open source object-relational database system.
*   **Real-time Communication:**
    *   [WebSockets](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API): For real-time notifications and chat rooms.
*   **Containerization:**
    *   [Docker](https://www.docker.com/): To containerize the application and its services for consistent development and deployment environments.

## Project Structure

```
/
├── app/
│   ├── controllers/      # API endpoint controllers
│   ├── database/         # Database connection and models
│   ├── models/           # Pydantic models for request/response validation
│   ├── prisma/           # Prisma schema for database modeling
│   ├── schemas/          # Pydantic schemas for data validation
│   ├── services/         # Business logic for the application
│   ├── utils/            # Utility functions and middleware
│   ├── __init__.py
│   ├── init_db.py        # Database initialization script
│   ├── main.py           # Main application entry point
│   └── worker.py         # Celery worker definition
├── .dockerignore
├── .env.sample
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── pyrightconfig.json
├── requirements.txt
└── start.sh
```

### Controllers

*   `auth_controller.py`: Handles user registration, login, logout, and profile retrieval.
*   `connections_controller.py`: Manages user following and unfollowing.
*   `notification_controller.py`: Manages real-time notifications via WebSockets.
*   `room_controller.py`: Handles the creation and management of audio chat rooms.
*   `tweet_controller.py`: Manages tweet creation, updating, deletion, and retrieval.
*   `user_controller.py`: Manages user-related actions like password reset.

### Utils and Other Files

*   `main.py`: The entry point of the FastAPI application. It initializes the app, includes the routers, and configures middleware.
*   `database/connection.py`: Manages the database connection pool.
*   `database/models.py`: Contains the SQLAlchemy database models.
*   `prisma/schema.prisma`: Defines the database schema using Prisma, which is then used to generate the SQLAlchemy models.
*   `services/`: This directory contains the business logic of the application, separated by domain (e.g., `auth_service.py`, `tweet_service.py`).
*   `utils/auth_middleware.py`: A middleware to protect routes by verifying JWT tokens.
*   `utils/token_utils.py`: Utility functions for generating and verifying JWT tokens.
*   `init_db.py`: A script to initialize the database with necessary tables.
*   `worker.py`: The entry point for the Celery worker, which handles asynchronous tasks.
*   `docker-compose.yml`: Defines the services, networks, and volumes for the Dockerized application.
*   `Dockerfile`: Defines the Docker image for the FastAPI application.

## Getting Started

### Prerequisites

*   [Docker](https://www.docker.com/get-started)
*   [Docker Compose](https://docs.docker.com/compose/install/)

### Development

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/twitter-clone-api.git
    cd twitter-clone-api
    ```

2.  **Create a `.env` file:**

    Copy the contents of `.env.sample` to a new file named `.env` and fill in the required environment variables.

    ```bash
    cp .env.sample .env
    ```

3.  **Run the development server:**

    ```bash
    ./dev.sh
    ```

    This will start the FastAPI application in development mode with hot-reloading, along with the PostgreSQL and Redis services. The API will be available at `http://localhost:8000`.

### Production

1.  **Create a `.env` file:**

    Copy the contents of `.env.sample` to a new file named `.env` and fill in the required environment variables for your production environment.

2.  **Run the production server:**

    ```bash
    ./start.sh
    ```

    This will start the FastAPI application in production mode, along with the PostgreSQL and Redis services. The API will be available at `http://localhost:8000`.
