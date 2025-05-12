import chromadb
from chromadb.utils import embedding_functions
import pandas as pd
from pathlib import Path

def test_database():
    # Initialize ChromaDB
    client = chromadb.Client()
    
    # Use sentence-transformers for embeddings
    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    
    # Create or get the collection
    collection = client.get_or_create_collection(
        name="lonca_faqs",
        embedding_function=embedding_function
    )
    
    # Load data from Excel
    faq_file = Path("prompts/LoncaFAQs.xlsx")
    df = pd.read_excel(faq_file)
    
    # Get region columns (excluding 'Question' and unnamed columns)
    region_cols = [col for col in df.columns if col not in ['Question'] and not col.startswith('Unnamed')]
    print(f"Found region columns: {region_cols}")
    
    # Process each row and region
    for idx, row in df.iterrows():
        question = str(row['Question']).strip()
        
        # Process each region's answer
        for region in region_cols:
            answer = str(row[region]).strip()
            
            if pd.notna(question) and pd.notna(answer) and question and answer and answer.lower() != 'nan':
                # Create a unique ID for each FAQ
                doc_id = f"q{idx}_r{region}"
                
                # Add to vector database
                collection.add(
                    documents=[f"Q: {question}\nA: {answer}"],
                    metadatas=[{
                        "question": question,
                        "answer": answer,
                        "region": region
                    }],
                    ids=[doc_id]
                )
    
    # Get all documents
    results = collection.get()
    
    # Print all questions
    print("\nAll questions in database:")
    for i, metadata in enumerate(results['metadatas']):
        print(f"\n{i+1}. Question: {metadata['question']}")
        print(f"   Answer: {metadata['answer']}")
        print(f"   Region: {metadata['region']}")
    
    # Search specifically for sample-related questions
    print("\nSearching for 'sample' related questions:")
    sample_results = collection.query(
        query_texts=["Do you offer samples?"],
        n_results=5
    )
    
    print("\nSample search results:")
    for i, (metadata, distance) in enumerate(zip(
        sample_results['metadatas'][0],
        sample_results['distances'][0]
    )):
        print(f"\n{i+1}. Question: {metadata['question']}")
        print(f"   Answer: {metadata['answer']}")
        print(f"   Region: {metadata['region']}")
        print(f"   Distance: {distance:.4f}")

if __name__ == "__main__":
    test_database() 