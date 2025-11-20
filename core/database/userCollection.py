"""
Filename:       userCollection.py
Version:        1.0
Authors:        Jason Huang, ECE4574_F25_Team8
Description:    This module deals with database operations with the user's information

"""

from bson import ObjectId
from core.database.mongdb_client import database
from pymongo.errors import WriteError
from datetime import datetime


class UserCol:
    """
    User information should follow this structure in the dict:
    username:               str
    email:                  str
    password_hash:          str
    first_name:             str
    last_name:              str
    phone:                  str
    created_at:             datetime
    last_login:             datetime
    monthly_spending_limit: double
    monthly_savings_goal:   double
    goal_streak_count:      int
    """
    COLLECTION = "users"

    def __init__(self):
        """Initialize a connection to the user collection"""
        if self.COLLECTION not in database.get_db().list_collection_names():
            self.create_user_collection()
        self._collection = database.get_db()[self.COLLECTION]


    def create_user_collection(self):
        """Creates a new user collection if it does not already exist in the database with a json schema"""
        property_list = ["username", "email", "password_hash", "first_name", "last_name",
                         "phone", "created_at", "last_login", "monthly_spending_limit",
                         "monthly_savings_goal", "goal_streak_count"]
        database.get_db().create_collection(self.COLLECTION, validator = {
            "$jsonSchema": {
                "bsonType": "object",
                "additionalProperties": False,
                "required": property_list,
                "properties": {
                    "_id": {
                        "bsonType": "objectId"
                    },
                    "username": {
                        "bsonType": "string"
                    },
                    "email": {
                        "bsonType": "string"
                    },
                    "password_hash": {
                        "bsonType": "string"
                    },
                    "first_name": {
                        "bsonType": "string"
                    },
                    "last_name": {
                        "bsonType": "string"
                    },
                    "phone": {
                        "bsonType": "string"
                    },
                    "created_at": {
                        "bsonType": "date"
                    },
                    "last_login": {
                        "bsonType": "date"
                    },
                    "monthly_spending_limit": {
                        "bsonType": "double"
                    },
                    "monthly_savings_goal": {
                        "bsonType": "double"
                    },
                    "goal_streak_count": {
                        "bsonType": "int"
                    }
                }
            }
        },  validationLevel = "strict", validationAction = "error")


    def create_user(self, user: dict) -> str | None:
        """
        Creates a user with the given dict.
        
        Params:
            user: A dictionary with a valid format
        Returns:
            The object ID of the new document
        Raises:
            Raises exception if a user with a same username exists
        """
        if (self._collection.find_one({"username": user["username"]}) != None):
            raise Exception("User already exists in db")
        try:
            inserted = self._collection.insert_one(user)
            return str(inserted.inserted_id)
        except WriteError as e:
            print(e)
            
    
    def get_user(self, username: str) -> dict | None:
        """
        Get the document with the specified username

        Params:
            username: The username of the user
        Returns:
            The user information as a dict if it exists (or None if it doesn't exist)
        """
        return self._collection.find_one({"username": username})
    

    def get_userid(self, username: str) -> ObjectId | None:
        """
        Get the document unique object id

        Params:
            username: The username of the user
        Returns:
            The unique object id of the document
        """
        if self.get_user(username) is not None:
            return self._collection.find_one({"username": username}, {"_id": 1})
        else:
            print(f"No document with username {username} exists.")
    

    def update_user(self, username: str, updates: dict) -> int | None:
        """
        Updates the user information

        Params:
            username: The username of the user
        Returns:
            The amount of fields successfully modified
        """
        try:
            update_result = self._collection.update_one({"username": username}, {"$set": updates})
            return update_result.modified_count
        except WriteError as e:
            print(e)


def main():
    """Demo usage for the user class"""
    userCollection = UserCollection()
    user_input = input("Enter 1 to create a new account, 2 to view an account information, or 3 to update an existing user's email: ")
    if user_input == "1":
        user_dict = dict()
        user_dict["username"]       = input("Enter a username: ")
        user_dict["email"]          = input("Enter an email: ")
        user_dict["password_hash"]  = input("Enter a password: ")
        user_dict["first_name"]     = input("Enter your first name: ")
        user_dict["last_name"]      = input("Enter your last name: ")
        user_dict["phone"]          = input("Enter your phone number: ")
        user_dict["created_at"]     = datetime.now()
        user_dict["last_login"]     = datetime.now()
        user_dict["monthly_spending_limit"] = 0.0
        user_dict["monthly_savings_goal"]   = 0.0
        user_dict["goal_streak_count"]      = 0
        userCollection.create_user(user_dict)
    elif user_input == "2":
        username = input("Enter username: ")
        if (userCollection.get_user(username) != None):
            update_dict = dict()
            update_dict["last_login"] = datetime.now()
            userCollection.update_user(username, update_dict)
            user_info = userCollection.get_user(username)
            print(user_info)
        else:
            print(f"No document with username {username} exists.")
    elif user_input == "3":
        username = input("Enter username: ")
        update_dict = dict()
        update_dict["last_login"] = datetime.now()
        update_dict["email"] = input("Enter new email: ")
        userCollection.update_user(username, update_dict)
    else:
        print("Invalid input")


if __name__ == "__main__":
    main()



    