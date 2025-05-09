from typing import Dict, Tuple
from .ai_service import AIService

class QueryValidator:
    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service
        self.standard_response = (
            "I am Lonca's B2B fashion supplier assistant. I can only assist with questions "
            "about Lonca's products, services, and business operations. How can I help you "
            "with your Lonca-related needs?"
        )
        
        # Define the business context
        self.context = {
            "business_type": "B2B fashion supply",
            "company": "Lonca",
            "valid_topics": [
                "product catalog and specifications",
                "ordering process and requirements",
                "shipping and delivery",
                "business terms and conditions",
                "customer service",
                "business policies",
                "minimum order quantities",
                "customization options",
                "sample requests",
                "payment terms",
                "lead times",
                "quality standards",
                "sustainability practices",
                "business partnerships"
            ],
            "invalid_topics": [
                "general fashion trends",
                "retail shopping",
                "personal styling",
                "general business advice",
                "unrelated services",
                "competitor information"
            ]
        }
        
    async def validate_query(self, user_input: str) -> Tuple[bool, str]:
        """
        Validate if the query is Lonca-related using context-based classification.
        
        Args:
            user_input (str): The user's message
            
        Returns:
            Tuple[bool, str]: (is_valid, response)
            - is_valid: True if query is Lonca-related, False otherwise
            - response: Standard response if not valid, empty string if valid
        """
        classification_prompt = f"""
        You are a context-aware query classifier for {self.context['company']}'s {self.context['business_type']} business.
        
        Your task is to determine if the following query is related to {self.context['company']}'s business operations.
        
        Business Context:
        - Company: {self.context['company']}
        - Business Type: {self.context['business_type']}
        
        Valid Topics:
        {', '.join(self.context['valid_topics'])}
        
        Invalid Topics:
        {', '.join(self.context['invalid_topics'])}
        
        Query: {user_input}
        
        Consider:
        1. Is this a business-related query?
        2. Is it about fashion supply or related operations?
        3. Could this be a valid question for a B2B fashion supplier?
        4. Does it fall within our valid topics?
        5. Is it clearly about an invalid topic?
        
        Respond with ONLY 'yes' if the query is related to {self.context['company']}'s business, or 'no' if it's not.
        """
        
        try:
            classification = await self.ai_service.get_classification(classification_prompt)
            is_valid = classification.strip().lower() == 'yes'
            
            if not is_valid:
                return False, self.standard_response
                
            return True, ""
            
        except Exception as e:
            print(f"Error in query validation: {e}")
            # In case of error, default to standard response
            return False, self.standard_response 