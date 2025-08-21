from abc import ABC, abstractmethod

class DBProvider(ABC):
    """
    Abstract base class for database providers.
    All database providers should inherit from this class.
    """
    
    def __init__(self, db_config, tokenizer=None):
        self.db_config = db_config
        self.tokenizer = tokenizer

    @abstractmethod
    def connect(self):
        """
        Connect to the database.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement this method.")
    
    @abstractmethod
    def disconnect(self):
        """
        Disconnect from the database.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement this method.")
    
    @abstractmethod
    def add_document(self, document):
        """
        Add a document to the database.
        
        Args:
            document (dict): The document to add.
        
        Returns:
            bool: True if the document was added successfully, False otherwise.
        """
        raise NotImplementedError("Subclasses must implement this method.")
    
    def retrieve_similar(self, query, k=1):
        """
        Retrieve top-k similar documents based on a query.
        
        Args:
            query (str): The query string to search for.
            k (int): The number of similar documents to retrieve.
        
        Returns:
            list: A list of similar documents.
        """
        raise NotImplementedError("Subclasses must implement this method.")