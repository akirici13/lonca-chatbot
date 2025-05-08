import asyncio
from services.faq_service import FAQService
from services.ai_service import AIService
from services.prompt_builder import PromptBuilder

async def interactive_chat():
    # Initialize services
    print("Initializing services...")
    faq_service = FAQService()
    ai_service = AIService()
    prompt_builder = PromptBuilder()
    
    # Get user's region
    print("\nAvailable regions: Europe, Turkey, Other, Own")
    while True:
        region = input("\nPlease select your region: ").strip()
        if region in ["Europe", "Turkey", "Other", "Own"]:
            break
        print("Invalid region. Please choose from: Europe, Turkey, Other, Own")
    
    print(f"\nWelcome to the Lonca Chatbot! (Region: {region})")
    print("Type 'exit' to end the conversation.")
    print("="*80)
    
    while True:
        # Get user input
        user_message = input("\nYou: ").strip()
        
        # Check for exit command
        if user_message.lower() == 'exit':
            print("\nThank you for chatting with us. Goodbye!")
            break
        
        # Skip empty messages
        if not user_message:
            continue
        
        try:
            # Get relevant FAQs for the region
            faqs = faq_service.get_relevant_faqs(user_message, region=region)
            
            # Build the prompt with relevant FAQs
            system_prompt, user_prompt = prompt_builder.build_prompt(user_message, region)
            
            # Get AI response
            response = await ai_service.get_response(system_prompt, user_prompt)
            
            # Print the response
            print("\nAssistant:", response.get('choices', [{}])[0].get('message', {}).get('content', 'Error'))
            
            # If we have relevant FAQs, show them
            if faqs:
                print("\nRelevant FAQs found:")
                for i, faq in enumerate(faqs[:2], 1):  # Show top 2 FAQs
                    print(f"\n{i}. Q: {faq['question']}")
                    print(f"   A: {faq['answer']}")
                    print(f"   (Relevance: {faq['relevance']:.1%})")
            
        except Exception as e:
            print(f"\nError: {e}")
        
        print("\n" + "-"*40)

if __name__ == "__main__":
    try:
        asyncio.run(interactive_chat())
    except KeyboardInterrupt:
        print("\n\nChat session ended by user. Goodbye!") 