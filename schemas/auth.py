from pydantic import BaseModel,validator 

# Create the schema for user input
class UserInput(BaseModel):
    username: str
    email: str
    password: str

    @validator("username")
    def username_parameter_check_check(cls,username):
        if not username:
            raise ValueError("username is required")
        return username
    
    @validator("email")
    def email_parameter_check_check(cls,email):
        if not email:
            raise ValueError("email is required")
        return email
    
    @validator("password")
    def password_parameter_check(cls,password):
        if not password:
            raise ValueError("password is required")
        return password
    
    class Config:
        schema_extra = {
            "example": {
                "username": "User1",
                "email": "user1@gmail.com",
                "password": "user@123"
            }
        }

# Create the schema for user credentials
class UserCredentials(BaseModel):
    username: str
    password: str

    @validator("username")
    def username_parameter_check_check(cls,username):
        if not username:
            raise ValueError("username is required")
        return username
    
    @validator("password")
    def password_parameter_check(cls,password):
        if not password:
            raise ValueError("password is required")
        return password
    
    class Config:
        schema_extra = {
            "example": {
                "username": "User1",
                "password": "user@123"
            }
        }