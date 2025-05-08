import asyncio
from services.faq_service import FAQService

async def test_chat():
    # Initialize FAQ service
    print("Initializing FAQ service...")
    faq_service = FAQService()
    
    # Example conversation with different regions
    conversations = [
        {
            "region": "Europe",
            "messages": [
                "Can I get samples?",
                "How long does shipping take?",
                "What is the minimum order quantity?"
            ]
        },
        {
            "region": "Turkey",
            "messages": [
                "Can I get samples?",
                "How long does shipping take?",
                "What is the minimum order quantity?"
            ]
        }
    ]
    
    # Process each conversation
    for conv in conversations:
        print(f"\n{'='*80}")
        print(f"Testing conversation for region: {conv['region']}")
        print(f"{'='*80}\n")
        
        for message in conv['messages']:
            print(f"\nUser ({conv['region']}): {message}")
            
            # Get relevant FAQs for the region
            faqs = faq_service.get_relevant_faqs(message, region=conv['region'])
            
            if faqs:
                # Get the most relevant FAQ
                top_faq = faqs[0]
                print(f"\nAssistant: {top_faq['answer']}")
                print(f"(Relevance: {top_faq['relevance']:.1%})")
            else:
                print("\nAssistant: I'm sorry, I don't have a specific answer for that question.")
            
            print("\n" + "-"*40)
            
        print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(test_chat()) 