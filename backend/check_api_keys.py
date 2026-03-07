"""
JAWIR OS - API Key Checker
Check which API keys are valid before running the agent.
"""

import asyncio
import sys
from dotenv import load_dotenv

async def check_keys():
    """Check all API keys and report status."""
    load_dotenv()
    
    from app.config import settings
    
    print("\n" + "=" * 60)
    print("JAWIR OS - API KEY CHECKER")
    print("=" * 60)
    print(f"\n📋 Total keys in .env: {len(settings.all_google_api_keys)}")
    
    if not settings.all_google_api_keys:
        print("\n❌ No API keys found in .env!")
        print("   Please add GOOGLE_API_KEYS to your .env file")
        return 1
    
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import HumanMessage
    
    valid_keys = []
    leaked_keys = []
    rate_limited_keys = []
    
    print("\n🔍 Testing each key...\n")
    
    for i, key in enumerate(settings.all_google_api_keys, 1):
        key_preview = f"{key[:10]}...{key[-4:]}"
        print(f"   Key #{i} ({key_preview}):", end=" ")
        
        try:
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",  # Use stable model for testing
                google_api_key=key,
                temperature=0.1,
            )
            response = await llm.ainvoke([HumanMessage(content="Say 'OK'")])
            print(f"✅ VALID")
            valid_keys.append(key)
            
        except Exception as e:
            error_msg = str(e)
            if "PERMISSION_DENIED" in error_msg or "leaked" in error_msg.lower():
                print(f"❌ LEAKED/REVOKED")
                leaked_keys.append(key)
            elif "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                print(f"⚠️ RATE LIMITED (may still be valid)")
                rate_limited_keys.append(key)
            else:
                print(f"❌ ERROR: {error_msg[:50]}")
                leaked_keys.append(key)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"   ✅ Valid keys:       {len(valid_keys)}")
    print(f"   ⚠️ Rate limited:     {len(rate_limited_keys)}")
    print(f"   ❌ Leaked/Invalid:   {len(leaked_keys)}")
    
    if not valid_keys and not rate_limited_keys:
        print("\n❌ NO VALID API KEYS FOUND!")
        print("\n📝 To fix this:")
        print("   1. Go to: https://aistudio.google.com/apikey")
        print("   2. Delete all leaked keys")
        print("   3. Generate new API keys")
        print("   4. Update your .env file with new keys")
        print("   5. Add .env to .gitignore to prevent future leaks")
        return 1
    
    if valid_keys:
        print("\n✅ Valid keys to use in .env:")
        print(f"   GOOGLE_API_KEYS={','.join(valid_keys)}")
    
    return 0


if __name__ == "__main__":
    result = asyncio.run(check_keys())
    sys.exit(result)
