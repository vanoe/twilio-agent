from app.core.providers.db_provider import DBProvider
from pymongo import MongoClient

class MongoDBProvider(DBProvider):
    def __init__(self, db_config, tokenizer=None):
        self.db_config = db_config
        self.tokenizer = tokenizer
        self.connect()

    def connect(self):
        """Connect to the MongoDB database."""
        self.client = MongoClient(self.db_config['uri'])
        self.db = self.client[self.db_config['database']]
        # self.collections = []
        # for collection_name, collection in self.db_config['collection'].items():
        #     self.collections['collection_name'] = self.db[collection]

    def disconnect(self):   
        """Disconnect from the MongoDB database."""
        self.client.close()

    def add_document(self, document, collection) -> bool:
        """
        Add a document to the MongoDB collection.
        
        Args:
            document (dict | pydantic.BaseModel): The document to add.
        
        Returns:
            bool: True if the document was added successfully, False otherwise.
        """
        try:
            # Allow passing in a Pydantic model or a plain dict
            if hasattr(document, "model_dump"):
                document = document.model_dump()
            elif hasattr(document, "dict"):
                document = document.dict()

            if not isinstance(document, dict):
                raise TypeError("Document must be a dict or a Pydantic model")
            name = document.get("name")
            if not name:
                raise ValueError("Document is missing required 'name' field")

            text_to_embed = f'Name: {document["name"]} \n Description: {document["description"]} \n Price: {document["price"]}'
            if collection == 'services':
                del document["type"]
            else:
                text_to_embed += f'\n Type: {document["type"]}'
                
            if self.tokenizer is not None:
                embedding = self.tokenizer(text_to_embed)
                document["embedding"] = embedding

            print(f"Adding document with embedding: {document}")
            self.db[collection].insert_one(document)
            return True
        except Exception as e:
            print(f"Error adding document: {e}")
            return False
        
    def retrieve_similar(self, query, resource, k=2):
        """
        Retrieve top-k similar documents based on a query.
        
        Args:
            query (str): The query string to search for.
            k (int): The number of similar documents to retrieve.
        
        Returns:
            list: A list of similar documents.
        """
        try:
            query_embedding = self.tokenizer(query)
            # results = self.collection.aggregate([
            #     {
            #         "$vectorSearch": {
            #             "queryVector": query_embedding,
            #             "path": "embedding",
            #             "numCandidates": k,
            #             "limit": k,
            #             "index": "vector_index"  
            #         }
            #     }
            # ])
            
            results = self.db[resource].aggregate([
                {
                    "$vectorSearch": {
                        "queryVector": query_embedding,
                        "path": "embedding",
                        "numCandidates": k,
                        "limit": k,
                        "index": "vector_index"  
                    }
                },
                {
                    "$project": {
                        "name": 1,
                        "description": 1,
                        "price": 1,
                        "_id": 0
                    }
                }
            ])

            documents = ""
            for result in results:
                documents += f"Name: {result.get('name')}, Description: {result.get('description')}, Price: {result.get('price')}\n"
            return documents.strip()
        except Exception as e:
            print(f"Error retrieving similar documents: {e}")
            return []