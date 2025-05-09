import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
from typing import Dict, List, Tuple, Optional
import os
from pathlib import Path

class FAQService:
    def __init__(self):
        """Initialize the FAQ service with vector database."""
        self.prompts_dir = Path("prompts")
        self.faq_file = self.prompts_dir / "LoncaFAQs.xlsx"
        
        # Initialize ChromaDB
        self.client = chromadb.Client()
        
        # Use sentence-transformers for embeddings
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Create or get the collection
        self.collection = self.client.get_or_create_collection(
            name="lonca_faqs",
            embedding_function=self.embedding_function
        )
        
        # Cache for FAQ results
        self._cache: Dict[str, List[Dict]] = {}
        
        # Load and process FAQs
        self._load_faqs()
        
    def has_relevant_faqs(self, query: str, region: str = None, min_relevance: float = 0.3) -> bool:
        """
        Check if there are any relevant FAQs for the query.
        
        Args:
            query (str): The user's question
            region (str, optional): The region to filter by
            min_relevance (float): Minimum relevance score to consider an FAQ relevant
            
        Returns:
            bool: True if there are relevant FAQs, False otherwise
        """
        faqs = self.get_relevant_faqs(query, region)
        return any(faq['relevance'] >= min_relevance for faq in faqs)
        
    def _load_faqs(self):
        """Load FAQs from Excel and add to vector database."""
        try:
            # Read Excel file
            df = pd.read_excel(self.faq_file)
            
            # Get region columns (excluding 'Question' and unnamed columns)
            region_cols = [col for col in df.columns if col not in ['Question'] and not col.startswith('Unnamed')]
            
            if not region_cols:
                raise ValueError(f"No region columns found. Available columns: {df.columns.tolist()}")
            
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
                        self.collection.add(
                            documents=[f"Q: {question}\nA: {answer}"],
                            metadatas=[{
                                "question": question,
                                "answer": answer,
                                "region": region
                            }],
                            ids=[doc_id]
                        )
                        
        except Exception as e:
            raise Exception(f"Error loading FAQs: {e}")
            
    def _calculate_relevance_score(self, distance: float) -> float:
        """
        Convert distance to a relevance score between 0 and 1.
        Lower distances become higher relevance scores.
        
        Args:
            distance (float): The distance from ChromaDB
            
        Returns:
            float: Relevance score between 0 and 1
        """
        # Based on typical ChromaDB distance ranges
        max_relevant_distance = 2.0
        
        # Convert distance to relevance score (0 to 1)
        relevance = max(0, 1 - (distance / max_relevant_distance))
        return round(relevance, 4)
            
    def get_relevant_faqs(self, query: str, region: str = None, n_results: int = 3) -> List[Dict]:
        """
        Get relevant FAQs based on the query.
        
        Args:
            query (str): The user's question
            region (str, optional): The region to filter by. If provided, only returns answers for that region.
            n_results (int): Number of results to return
            
        Returns:
            List[Dict]: List of relevant FAQs with their answers
        """
        try:
            # Create cache key
            cache_key = f"{query}_{region}_{n_results}"
            
            # Check cache first
            if cache_key in self._cache:
                return self._cache[cache_key]
            
            # Search without region filter first to get all results
            results = self.collection.query(
                query_texts=[query],
                n_results=50
            )
            
            # Format and filter results
            faqs = []
            seen_questions = set()  # Track unique questions
            
            for i in range(len(results['ids'][0])):
                question = results['metadatas'][0][i]['question']
                result_region = results['metadatas'][0][i]['region']
                
                # Skip if we've already seen this question
                if question in seen_questions:
                    continue
                    
                # Skip if region doesn't match (when region filter is applied)
                if region and result_region != region:
                    continue
                    
                seen_questions.add(question)
                distance = results['distances'][0][i]
                relevance = self._calculate_relevance_score(distance)
                
                faqs.append({
                    "question": question,
                    "answer": results['metadatas'][0][i]['answer'],
                    "region": result_region,
                    "distance": distance,
                    "relevance": relevance
                })
            
            # Sort by relevance score (highest first)
            faqs.sort(key=lambda x: x['relevance'], reverse=True)
            
            # Take top n_results
            faqs = faqs[:n_results]
            
            # Cache the results
            self._cache[cache_key] = faqs
            
            return faqs
            
        except Exception as e:
            raise Exception(f"Error getting relevant FAQs: {e}")
            
    def format_faqs_for_prompt(self, faqs: List[Dict]) -> str:
        """
        Format FAQs for inclusion in the prompt.
        
        Args:
            faqs (List[Dict]): List of FAQ dictionaries
            
        Returns:
            str: Formatted FAQ text for the prompt
        """
        if not faqs:
            return ""
            
        formatted_text = "\nRelevant FAQs:\n"
        for faq in faqs:
            formatted_text += f"\nQ: {faq['question']}\nA: {faq['answer']}\n"
            
        return formatted_text 