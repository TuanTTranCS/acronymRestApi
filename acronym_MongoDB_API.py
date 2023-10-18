# Author: Tuan Tran
# Source reference: https://github.com/ishmeet1995/PublicProjects/blob/4a2aa8861d9b8f813fa7d0a84823f32472097b35/Python/MongoDB%20API/MongoDB%20API.py

from flask import Flask, request, json, Response
from bson import ObjectId
from pymongo import MongoClient
import logging as log
import sys
import getpass

app = Flask(__name__)
acronymAdminPwd = None
adminModeEnabled = False


class MongoAPI:

    mongoDbAccounts = {'acronymReader':'acronymReader2023',
                      'acronymAdmin': None}
    
    def __init__(self, data=None, admin=False):
        log.basicConfig(level=log.DEBUG, format='%(asctime)s %(levelname)s:\n%(message)s\n')
        pwd = None
        if admin:
            username = 'acronymAdmin'
            pwd = acronymAdminPwd
        else:
            username = 'acronymReader'
            pwd = self.mongoDbAccounts[username]

        # Use your own local mongoDb if needed:
        # uri = 'mongodb://localhost:27017/'
        
        # Use my own sandbox mongoDb:
        uri = f'mongodb+srv://{username}:{pwd}@sandbox.pokvrbl.mongodb.net/?retryWrites=true&w=majority'
        
        self.client = MongoClient(uri)
                                                                    
        if data is not None and data != {}:
            database = data['database'] if 'database' in data else 'acronymAPI'
            collection = data['collection'] if 'collection' in data else 'acronyms'
        else:
            database = 'acronymAPI'
            collection = 'acronyms'
        cursor = self.client[database]
        self.collection = cursor[collection]
        self.data = data

    def read(self):
        log.info('Reading all acronyms')
        documents = self.collection.find()
        output = [{item: str(data[item]) for item in data} for data in documents]
        return output

    def write(self, data):
        log.info('Inserting new acronym')
        new_document = data
        if 'acronym' not in new_document or 'definition' not in new_document:
            output = {'Status': 'Error',
                      'Message': "Please provide both fields 'acronym' and 'definition'"}
            return output
        response = self.collection.insert_one(new_document)
        output = {'Status': 'Successfully Inserted',
                  'Document_ID': str(response.inserted_id)}
        return output

    def update(self, filter):
        log.info('Updating acronym')
        
        updated_data = {"$set": self.data}
        response = self.collection.update_one(filter, updated_data)
        output = {'Status': 'Successfully Updated' if response.modified_count > 0 else "Nothing was updated."}
        return output

    def delete(self, filter):
        log.info('Deleting Data')
        # filt = data['Filter']
        response = self.collection.delete_one(filter)
        output = {'Status': 'Successfully Deleted' if response.deleted_count > 0 else "Document not found."}
        return output


@app.route('/')
def base():
    return Response(response=json.dumps({"Status": "UP"}),
                    status=200,
                    mimetype='application/json')


@app.route('/acronym', methods=['GET'])
def mongo_read():
    data = request.json
    # data = None

    obj1 = MongoAPI(data, admin=adminModeEnabled)
    response = obj1.read()
    return Response(response=json.dumps(response),
                    status=200,
                    mimetype='application/json')


@app.route('/acronym', methods=['POST'])
def mongo_write():
    data = request.json
    print(data)
    
    if data is None or data=={}:
            return Response(response=json.dumps({"Error": "Please provide correct acronym and definition to be inserted in JSON format"}),
                        status=400,
                        mimetype='application/json')
    obj1 = MongoAPI(data, admin=adminModeEnabled)
    response = obj1.write(data)
    return Response(response=json.dumps(response),
                    status=200,
                    mimetype='application/json')

@app.route('/acronym/<acronymID>', methods=['PATCH'])
def mongo_update(acronymID):
    data = request.json
    
    if data is None or data=={}:
        return Response(response=json.dumps({"Error": "Please provide correct acronym and definition to be updated in JSON format"}),
                status=400,
                mimetype='application/json')
    filter = {'_id': ObjectId(acronymID)}
    obj1 = MongoAPI(data, admin=adminModeEnabled)
    response = obj1.update(filter)
    return Response(response=json.dumps(response),
                    status=200,
                    mimetype='application/json')


@app.route('/acronym/<acronymID>', methods=['DELETE'])
def mongo_delete(acronymID):
    data = request.json
    filter = {'_id': ObjectId(acronymID)}
    obj1 = MongoAPI(data, admin=adminModeEnabled)
    response = obj1.delete(filter=filter)
    return Response(response=json.dumps(response),
                    status=200,
                    mimetype='application/json')


def main():
    
    global adminModeEnabled, acronymAdminPwd
    args = sys.argv[1:]
    if '-a' in args: # Admin mode is enabled for PUT / PATCH / DELETE methods:
        adminModeEnabled = True
        print('Admin mode is enabled. Admin pasword for mongoDB is required.')

        if '-p' in args:
            adminModeEnabled = True
            print('Admin pasword for mongoDB parsed from command arguments')
            acronymAdminPwd = args[args.index('-p') + 1]
        else:
            print('Admin password is required to be entered manually.')
            acronymAdminPwd = getpass.getpass("Enter MongoDb's Admin Password for acronymAPI database: ")
    else:
        adminModeEnabled = False
        print('Admin mode is disabled. Using read only acount to access mongoDB.')

    app.run(debug=True, port=5001, host='0.0.0.0')



if __name__ == '__main__':
    
    main()
    # mongo_obj = MongoAPI()
    # data = mongo_obj.read()
    # # print(data)
    # print(json.dumps(data, indent=4))

