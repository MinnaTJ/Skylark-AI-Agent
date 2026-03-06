from langchain.vectorstores import Chroma
from langchain.embeddings import GoogleGenerativeAIEmbeddings

def create_vector_store(texts):

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001"
    )

    vectordb = Chroma.from_texts(texts, embeddings)

    return vectordb