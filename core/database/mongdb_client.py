"""
Filename:       mongodb_client.py
Version:        1.0
Authors:        Jason Huang, ECE4574_F25_Team8
Description:    This module establishes a connection with the local mongodb server and database

"""

from pymongo import MongoClient


class database():
    """
    The database class handles connecting to the local database for the project.
    The class is a singleton which prevents multiple instances of the database object.
    """
    LOCAL_HOST = "mongodb://localhost:27017/"
    DATABASE = "PBMS_DB"
    _instance = None

    @classmethod
    def instance(cls):
        """Creates and returns a singleton of the server"""
        if cls._instance is None:
            cls._instance = MongoClient(cls.LOCAL_HOST)
        return cls._instance
    

    @classmethod
    def get_db(cls):
        """Returns the database"""
        return cls.instance()[cls.DATABASE]
    

def main():
    """Demo usage for the database class"""
    db_instance = database.get_db()
    for collection_name in db_instance.list_collection_names():
        print(collection_name)


if __name__ == "__main__":
    main()