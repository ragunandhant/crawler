from langchain_pinecone import Pinecone,PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
load_dotenv()
import os
from langchain_core.documents import Document
index_name = os.environ.get("PINECONE_INDEX","default")
pc = Pinecone()
index = pc.index(index_name)
vectorstore = PineconeVectorStore(index=index,embedding=OpenAIEmbeddings(model="text-embedding-3-small",dimensions=1536))


def upload_data(documents:list[Document],namespace:str="default"):
    vectorstore.add_documents(documents=documents,namespace=namespace)

def similarity_search(query:str,namespace:str="default",k:int=10,filter:dict=None):
    return vectorstore.similarity_search(query=query,namespace=namespace,k=k,filters=filter)