from explainer import get_gemini_client
import traceback

try:
    client = get_gemini_client()
    print('Client created:', client)
    response = client.models.generate_content(model='gemini-2.5-flash', contents='test')
    print('Response:', response.text)
except Exception as e:
    print('Error:', e)
    traceback.print_exc()
