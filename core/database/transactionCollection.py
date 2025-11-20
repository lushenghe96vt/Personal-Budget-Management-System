"""
Filename:       transactionCollection.py
Version:        1.0
Authors:        Jason Huang, ECE4574_F25_Team8
Description:    This module deals with database operations with transactions
"""

from bson import ObjectId
from core.database.mongdb_client import database
from pymongo.errors import WriteError
from datetime import datetime


class TransactionCol:
    """
    User information should follow this structure in the dict:
    user_ref:           string
    id:                 string
    date:               datetime
    description:        string
    amount:             double
    posted_date:        datetime
    description_raw:    string
    merchant:           string
    currency:           string
    txn_type:           string
    balance:            double
    category:           string
    notes:              string
    user_override:      bool
    statement_month:    int
    source_name:        string
    source_upload_id:   string
    raw:                dict
    """
    COLLECTION = "transactions"

    def __init__(self):
        """Initialize a connection to the user collection"""
        if self.COLLECTION not in database.get_db().list_collection_names():
            self.create_user_collection()
        self._collection = database.get_db()[self.COLLECTION]


    def create_user_collection(self):
        """Creates a new user collection if it does not already exist in the database with a json schema"""
        property_list = ["id", "date", "description", "amount", "posted_date", "description_raw",
                         "merchant", "currency", "txn_type", "balance", "category", "notes",
                         "user_override", "statement_month", "source_name", "source_upload_id", "raw"]
        database.get_db().create_collection(self.COLLECTION, validator = {
            "$jsonSchema": {
                "bsonType": "object",
                "additionalProperties": False,
                "required": property_list,
                "properties": {
                    "_id": {
                        "bsonType": "objectId"
                    },
                    "user_ref": {
                        "bsonType": "string"
                    },
                    "id": {
                        "bsonType": "string"
                    },
                    "date": {
                        "bsonType": "date"
                    },
                    "description": {
                        "bsonType": "string"
                    },
                    "amount": {
                        "bsonType": "double"
                    },
                    "posted_date": {
                        "bsonType": ["date", "null"]
                    },
                    "description_raw": {
                        "bsonType": "string"
                    },
                    "merchant": {
                        "bsonType": ["string", "null"]
                    },
                    "currency": {
                        "bsonType": "string"
                    },
                    "txn_type": {
                        "bsonType": ["string", "null"]
                    },
                    "balance": {
                        "bsonType": "double"
                    },
                    "category": {
                        "bsonType": "string"
                    },
                    "notes": {
                        "bsonType": ["string", "null"]
                    },
                    "user_override": {
                        "bsonType": "string"
                    },
                    "statement_month": {
                        "bsonType": "int"
                    },
                    "source_name": {
                        "bsonType": "string"
                    },
                    "source_upload_id": {
                        "bsonType": "string"
                    },
                    "raw": {
                        "bsonType": "object"
                    },
                }
            }
        },  validationLevel = "strict", validationAction = "error")


    def create_transaction(self, username: str, info: dict) -> str | None:
        """
        Creates a transaction tied to a user with the given info
        
        Params:
            username: The username of the user owning the transaction
            info:     The information of the transaction
        Returns:
            The object ID of the new document
        Raises:
            Raises exception if a user with a same username exists
        """
        # TODO: implement this function
        ...
            
    
    def get_transactions(self, username: str, filter: dict = None) -> list | None:
        """
        Get the document with the specified username

        Params:
            username: The username of the user
            filter:   A dictionary which contains the specific parameters the transactions returning must have
        Returns:
            The list of transactions that follow the filter
        """
        # TODO: implement this function
        ...

    
    def update_transaction(self, username: str, transaction_id: str, updates: dict) -> int | None:
        """
        Updates a specific transaction

        Params:
            username:       The username of the user owning the transaction
            transaction_id: The ID of the transaction 
        Returns:
            The amount of fields successfully modified
        """
        # TODO: implement this function
        ...


def main():
    """Demo usage for the user class"""
    ...


if __name__ == "__main__":
    main()



    