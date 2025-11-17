"""
Filename:       user.py
Version:        1.0
Authors:        Jason Huang, ECE4574_F25_Team8
Description:    This module deals with database operations with the user's information

"""

from bson import ObjectId
from core.database.mongdb_client import database
from datetime import datetime


class UserCollection:
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
    monthly_spending_limit: float
    monthly_savings_goal:   float
    goal_streak_count:      int
    """
    COLLECTION = "users"

    def __init__(self):
        """Initialize a connection to the user collection"""
        self._collection = database.get_db()[self.COLLECTION]


    def create_user(self, user: dict) -> str:
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
        
        inserted = self._collection.insert_one(user)
        return str(inserted.inserted_id)
            
    
    def get_user(self, username: str) -> dict | None:
        """
        Get the document with the specified username

        Params:
            username: The username of the user
        Returns:
            The user information as a dict if it exists
        """
        return self._collection.find_one({"username": username})
    

    def get_userid(self, username: str) -> ObjectId:
        """
        Get the document unique object id

        Params:
            username: The username of the user
        Returns:
            The unique object id of the document
        """
        return self._collection.find_one({"username": username}, {"_id": 1})
    

    def update_user(self, username: str, updates: dict) -> int:
        """
        Updates the user information

        Params:
            username: The username of the user
        Returns:
            The amount of fields successfully modified
        """
        update_result = self._collection.update_one({"username": username}, {"$set": updates})
        return update_result.modified_count


def main():
    """Demo usage for the user class"""
    userCollection = UserCollection()
    user_input = input("Enter 1 to create a new account or 2 to view an account information: ")
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
        update_dict = dict()
        update_dict["last_login"] = datetime.now()
        userCollection.update_user(username, update_dict)
        user_info = userCollection.get_user(username)
        print(user_info)


if __name__ == "__main__":
    main()



    