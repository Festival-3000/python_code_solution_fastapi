# python_code_solution
# Weather API

This API provides historic weather data based on user input.

## Table of Contents

- Framework Selection
- User Registration
- User Authentication and Token-based Authorization
- API Endpoints

## Framework Selection

We chose FastAPI as the web framework for building this API. FastAPI is a modern, fast, web framework for building APIs with Python 3.7+ based on standard Python type hints. It provides automatic interactive documentation (Swagger UI) and validation.

## User Registration

Register a new user by providing a unique username, email, and password. Passwords are hashed for security.


### User Authentication and Token-based Authorization

Authenticate a user by providing their username and password. Upon successful authentication, a JWT token will be provided, which should be used for accessing secured endpoints.

### API Endpoints
`POST /users/register`
`POST /users/login`
`GET /users/get_user_details`
`GET /historic_weather`