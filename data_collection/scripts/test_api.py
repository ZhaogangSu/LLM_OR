# test_api.py
# from openai import OpenAI

# # Test first API key
# with open("API_keys.txt", 'r') as f:
#     api_key = f.readline().strip()

# print(f"Testing API key: {api_key[:10]}...")

# client = OpenAI(
#     api_key=api_key,
#     base_url="https://api.deepseek.com"  # Change if needed
# )

# try:
#     response = client.chat.completions.create(
#         model="deepseek-chat",
#         messages=[{"role": "user", "content": "Say 'API works!'"}],
#         max_tokens=10
#     )
#     print("✓ API connection successful!")
#     print(f"Response: {response.choices[0].message.content}")
# except Exception as e:
#     print(f"❌ API connection failed: {e}")

# test_all_qwen_keys.py
from openai import OpenAI
import time

# Load all keys
with open("API_keys.txt", 'r') as f:
    api_keys = [line.strip() for line in f if line.strip()]

print(f"Testing {len(api_keys)} Qwen API keys...")
print("="*60)

valid_keys = []
invalid_keys = []

for i, key in enumerate(api_keys, 1):
    print(f"\n[{i}/{len(api_keys)}] Testing key: {key[:15]}...{key[-4:]}")
    
    try:
        client = OpenAI(
            api_key=key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        response = client.chat.completions.create(
            model="qwen-max",
            messages=[{"role": "user", "content": "Reply with just: OK"}],
            max_tokens=5
        )
        
        print(f"  ✓ VALID - Response: {response.choices[0].message.content}")
        valid_keys.append(key)
        
    except Exception as e:
        error_msg = str(e)
        print(f"  ❌ ERROR - {error_msg[:150]}")
        invalid_keys.append(key)
    
    time.sleep(0.5)  # Rate limiting

# # Summary
# print("\n" + "="*60)
# print("SUMMARY")
# print("="*60)
# print(f"✓ Valid keys: {len(valid_keys)}")
# print(f"❌ Invalid keys: {len(invalid_keys)}")

# if valid_keys:
#     print(f"\n✓ Found {len(valid_keys)} working Qwen API key(s)!")
#     # Save valid keys
#     with open("valid_qwen_keys.txt", 'w') as f:
#         for key in valid_keys:
#             f.write(key + '\n')
#     print(f"Valid keys saved to: valid_qwen_keys.txt")
    
#     # Update configuration recommendation
#     print(f"\n📝 Recommended configuration:")
#     print(f"  NUM_WORKERS={min(len(valid_keys), 9)}")
#     print(f"  Update API_keys.txt to only include valid keys")
# else:
#     print("\n❌ No valid API keys found!")