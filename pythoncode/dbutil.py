'''
DBUtils is a class created for DB connection and running the various queries against the DB.
Most of the code here is commented as only what was needed is enable during the specific query run.
Created on May 30, 2015

@author: Feby Thomas
'''
import pprint

def get_db():
    """
    Function to get DB connection
    """
    from pymongo import MongoClient
    client = MongoClient('localhost:27017')
    # 'examples' here is the database name. It will be created if it does not exist.
    db = client.osm
    return db

# def add_city(db):
#     db.cities.insert({"name" : "Chicago"})
#     
# def get_city(db):
#     return db.cities.find_one()

def queries():
    """
    Function to run the various Queries. This was optionally used, most of the analysis was done using Mongo Shell
    """
    db = get_db()
    #Find total number of nodes
    #result = db.osmdatamke.find().count()
    
    #Find total number of nodes of type = node
    #result = db.osmdatamke.find({"type":"node"}).count()
    
    #Find total number of nodes of type = way
    #result = db.osmdatamke.find({"type":"way"}).count()
    
    #Find the user with the highest number of contributions
#     result = db.osmdatamke.aggregate([
#                                    {"$group":{"_id":"$created.user", 
#                                               "count":{"$sum":1}}},
#                                    {"$sort":{"count":-1}},
#                                    {"$limit" : 1}])
    
    #Find the Number of users appearing only once (having 1 post)
#     result = db.osmdatamke.aggregate([
#                                    {"$group":{"_id":"$created.user", 
#                                               "count":{"$sum":1}}},
#                                    {"$group": {"_id": "$count", "num_users": {"$sum":1}}},
#                                    {"$sort":{"_id":1}},
#                                    {"$limit" : 1}])
    
    #Find the top postal codes occurring by count
    result = db.osmdatamke.aggregate([
                                       {"$match": {"address.postcode":{"$exists":1}}},
                                       {"$group": {"_id":"$address.postcode", 
                                                  "count":{"$sum":1}}}, 
                                       {"$sort":{"count":-1}}])
    
    #Update a single record based on a specific postal code condition, to correct that record.
#     result = db.osmdatamke.update(
#                                   {"address.postcode":"Milwaukee WI, 53222"},
#                                   {"$set": {"address.postcode": "53222" }}
#                                   )
                                  
    pprint.pprint(result)

if __name__ == '__main__':
    queries()
    #add_city(db)
    
    