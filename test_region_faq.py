import asyncio
from services.faq_service import FAQService
import sys

async def test_region_faq():
    try:
        # Initialize FAQ service
        print("Initializing FAQ service...")
        faq_service = FAQService()
        
        # Test queries with different regions
        test_cases = [
            ("Can I get samples?", "Europe"),
            ("Can I get samples?", "Turkey"),
            ("How long does shipping take?", "Europe"),
            ("How long does shipping take?", "Turkey")
        ]
        
        # Test each query and region combination
        for query, region in test_cases:
            print(f"\n{'='*80}")
            print(f"Testing query: {query}")
            print(f"Region: {region}")
            print(f"{'='*80}")
            
            # Get relevant FAQs for the specific region
            faqs = faq_service.get_relevant_faqs(query, region=region)
            
            if faqs:
                for i, faq in enumerate(faqs, 1):
                    print(f"\nResult {i}:")
                    print(f"Question: {faq['question']}")
                    print(f"Answer: {faq['answer']}")
                    print(f"Region: {faq['region']}")
                    print(f"Distance: {faq['distance']:.4f}")
                    print(f"Relevance: {faq['relevance']:.1%}")
            else:
                print("No relevant FAQs found.")
                
    except Exception as e:
        print(f"Error during testing: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_region_faq()) 