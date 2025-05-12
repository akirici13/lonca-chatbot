import asyncio
from services.faq_service import FAQService
import sys

async def test_faq_service():
    try:
        # Initialize FAQ service
        print("Initializing FAQ service...")
        faq_service = FAQService()
        
        # Test queries
        test_queries = [
            "How long does shipping take?",
            "How can I place an order?",
            "What is the minimum order quantity?",
            "Can I get samples?"
        ]
        
        # Test each query
        for query in test_queries:
            print(f"\n{'='*80}")
            print(f"Testing query: {query}")
            print(f"{'='*80}")
            
            # Get relevant FAQs
            faqs = faq_service.get_relevant_faqs(query)
            
            if faqs:
                for i, faq in enumerate(faqs, 1):
                    print(f"\nResult {i}:")
                    print(f"Question: {faq['question']}")
                    print(f"Answer: {faq['answer']}")
                    print(f"Region: {faq['region']}")
                    print(f"Distance: {faq['distance']:.4f} (lower is better)")
                    print(f"Relevance: {faq['relevance']:.1%} match")
            else:
                print("No relevant FAQs found.")
                
            print("\nScore Guide:")
            print("- Distance: 0.0-1.0 (Very good), 1.0-1.5 (Good), 1.5-2.0 (Moderate), >2.0 (Poor)")
            print("- Relevance: Higher percentage = Better match")
                
    except Exception as e:
        print(f"Error during testing: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_faq_service()) 