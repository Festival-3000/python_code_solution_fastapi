from fastapi import APIRouter, Depends, status, HTTPException, Security, Query
import bcrypt
from fastapi import security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import httpx
from db_module.db import get_db
from models.auth import User
from schemas.auth import UserInput,UserCredentials
from pytest import Session
import datetime
import jwt
import logging
from logging.handlers import RotatingFileHandler
import os


router = APIRouter()

security = HTTPBearer()

# Set up logging
log_folder = "logs"
log_file_path = os.path.join(log_folder, "app.log")

# Create logs folder if it doesn't exist
if not os.path.exists(log_folder):
    os.makedirs(log_folder)

# Configure logging to a file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s",
    handlers=[
        RotatingFileHandler(log_file_path, maxBytes=5 * 1024 * 1024, backupCount=2),
        logging.StreamHandler()
    ]
)

# Create the route for user registration
@router.post("/users/register")
def register_user(request: UserInput,db: Session = Depends(get_db)):
    try:
        # Check if the email already exists
        existing_user = db.query(User).filter(User.email == request.email).first()

        if existing_user:
            logging.error("Email Already Exists.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

        # Hash the user password using bcrypt
        password_hash = bcrypt.hashpw(request.password.encode(), bcrypt.gensalt())

        # Create a new user object
        user = User(username=request.username, email=request.email, password_hash=password_hash)

        # Try to add the user to the database
        try:
            db.add(user)
            db.commit()
        except:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
        
        # Log a success message
        logging.info(f"User '{request.username}' registered successfully")

        # Return a success message
        return {"message": "User registered successfully"}

    except HTTPException as he:
        # Re-raise HTTPException with proper error message
        raise he

    except Exception as e:
        db.rollback()
        logging.error(f"Error during user registration: {str(e)}")
        raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"something went wrong"+ str(e))
        

# Create the route for user authentication
@router.post("/users/login")
def login_user(request: UserCredentials,db: Session = Depends(get_db)):

    try: 
        # Get the user from the database by username
        user = db.query(User).filter_by(username=request.username).first()

        # Check if the user exists and the password is correct
        if user and bcrypt.checkpw(request.password.encode(), user.password_hash.encode()):
            # Set expiration time for the token (e.g., 30 minutes)
            expiration_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
            # Create a JWT token with the user information and an expiration time
            token = jwt.encode({"id": user.id, "username": user.username, "email": user.email, "exp": expiration_time},
                "secret", algorithm="HS256"
            )
            
            # Log a success message
            logging.info("User authentication successful", user.username, user.email)
            
            # Return the token
            return {"token": token}
        else:
            # Log an error message
            logging.error("Invalid username or password", request.username)
            
            # Return an error message
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    
    except HTTPException as he:
        # Re-raise HTTPException with proper error message
        raise he
        
    except Exception as e:
        db.rollback()
        # Log an error message
        logging.error("Error during user authentication: %s", str(e))
        raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"something went wrong"+ str(e))


# Create the dependency function for token validation
def get_current_user(db: Session = Depends(get_db), token: str = Depends(security)):
    # Try to decode the token using PyJWT
    try:
        # Try to decode the token using PyJWT
        payload = jwt.decode(token, "secret", algorithms=["HS256"])
        user_id = payload.get("id")

        # Get the user from the database by id
        user = db.query(User).get(user_id)

        # Check if the user exists
        if user:
            logging.info("User authentication successful", user.id, user.username,user.email)
            return user
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    except Exception as e:
        # Log an error message
        logging.error("Error during user authentication", str(e))
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# Create the route that requires authorization
@router.get("/users/get_user_details")
def get_user_profile(db: Session = Depends(get_db),credentials: HTTPAuthorizationCredentials = Security(security)):
    try: 
        current_user = get_current_user(db, credentials.credentials)

        logging.info("User profile retrieved successfully", current_user.id, current_user.username, current_user.email)

        return {"id": current_user.id, "username": current_user.username, "email": current_user.email}
    
    except Exception as e:
        db.rollback()
        logging.error("Error retrieving user profile", str(e))
        raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"something went wrong"+ str(e))
    

@router.get("/historic_weather")
async def get_historic_weather(
    db: Session = Depends(get_db),
    latitude: float = Query(..., title="Latitude", description="Location latitude"),
    longitude: float = Query(..., title="Longitude", description="Location longitude"),
    days: int = Query(..., title="Number of Days", description="Number of days in the past"),
):
    try: 
        OPEN_METEO_API_URL = "https://api.open-meteo.com/v1/forecast"

        # Prepare query parameters for Open Meteo API
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "past_days": days,
            "hourly": "temperature_2m,precipitation,cloudcover",
        }

        # Make a request to Open Meteo API
        async with httpx.AsyncClient() as client:
            response = await client.get(OPEN_METEO_API_URL, params=params)
           
            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                # Extract and return relevant historic weather data
                historic_data = response.json()
                # Extract the "hourly" key
                hourly_data = historic_data.get("hourly", {})

                return hourly_data
            else:
                # Log the error message and raise an HTTPException if the request was not successful
                error_message = f"Failed to fetch historic weather data. Status Code: {response.status_code}, Response: {response.text}"
                logging.error(error_message)
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch historic weather data")
        
    except httpx.RequestError as req_err:
        logging.error(f"Request error during Open Meteo API call: {str(req_err)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to connect to Open Meteo API"
        )
        
    except Exception as e:
        db.rollback()
        logging.error("Error retrieving historic weather data:", str(e))
        raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"something went wrong"+ str(e))