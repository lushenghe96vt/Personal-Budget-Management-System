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
            self.create_transaction_collection()
        self._collection = database.get_db()[self.COLLECTION]


    def create_transaction_collection(self):
        """Creates a new user collection if it does not already exist in the database with a json schema"""
        property_list = ["id", "date", "description", "amount", "description_raw", 
                         "currency", "category", "notes", "user_override", "statement_month", 
                         "source_name", "source_upload_id", "raw", "is_subscription", "next_due_date",
                         "renewal_interval_type", "custom_interval_days", "alert_sent"]
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
                        "bsonType": "string"
                    },
                    "description_raw": {
                        "bsonType": "string"
                    },
                    "currency": {
                        "bsonType": "string"
                    },
                    "category": {
                        "bsonType": "string"
                    },
                    "notes": {
                        "bsonType": ["string", "null"]
                    },
                    "user_override": {
                        "bsonType": "bool"
                    },
                    "statement_month": {
                        "bsonType": "string"
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
                    "is_subscription": {
                        "bsonType": "bool"
                    },
                    "next_due_date": {
                        "bsonType": ["date", "null"]
                    },
                    "renewal_interval_type": {
                        "bsonType": "string"
                    },
                    "custom_interval_days": {
                        "bsonType": "int"
                    },
                    "alert_sent": {
                        "bsonType": "bool"
                    }
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
        NOTES:
            Currently DOES NOT check if a user with the username exists
        """
        try:
            info["user_ref"] = username 
            inserted = self._collection.insert_one(info)
        except WriteError as e:
            print(e)
            
    
    def get_transactions(self, username: str, filter: dict = {}) -> list:
        """
        Get the document with the specified username

        Params:
            username: The username of the user
            filter:   A dictionary which contains the specific parameters the transactions returning must have
        Returns:
            The list of transactions that follow the filter. An empty list is returned if no transactions match.
        """
        filter["user_ref"] = username
        return list(self._collection.find(filter))

    
    def update_transaction(self, username: str, transaction_id: str, updates: dict) -> int | None:
        """
        Updates a specific transaction

        Params:
            username:       The username of the user owning the transaction
            transaction_id: The ID of the transaction 
        Returns:
            The amount of fields successfully modified
        """
        try:
            transaction_doc = {"user_ref": username, "id": transaction_id}
            update_result = self._collection.update_one(transaction_doc, {"$set": updates})
            return update_result.modified_count
        except WriteError as e:
            print(e)


def main():
    """Demo usage for the user class"""
    test_transaction_doc = {"id": "row:1",
                            "date": datetime.now(),
                            "amount": "-100.00",
                            "description_raw": "This is a test raw description",
                            "currency": "USD",
                            "category": "Utilities",
                            "notes": "Test is a test notes",
                            "user_override": False,
                            "statement_month": "Month_1",
                            "source_name": "Transaction collection python test",
                            "source_upload_id": "some date",
                            "raw": {},
                            "is_subscription": False,
                            "next_due_date": None,
                            "renewal_interval_type": "monthly",
                            "custom_interval_days": 30,
                            "alert_sent": False}
    
    transactionCol = TransactionCol()
    user_input = input("Enter 1 to add a new transaction, or 2 to view a user's transactions: ") 
    username = input("Enter the owner's username: ")
    if user_input == "1":
        description = input("Enter a description for the new transaction: ")
        test_transaction_doc["description"] = description
        transactionCol.create_transaction(username, test_transaction_doc)
    if user_input == "2":
        transactions = transactionCol.get_transactions(username)
        for transaction in transactions:
            print(transaction)


if __name__ == "__main__":
    main()



    