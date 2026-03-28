import google.generativeai as genai

# Configure your API key
genai.configure(api_key="AIzaSyByoMbtInl4tD1ygI-7ywCl2sa3B2RNkpY")

# Try gemini-2.5-flash
model = genai.GenerativeModel("models/gemini-2.5-flash")
response = model.generate_content("Say 'Hello, I am StudyPal and I am ready to help!'")

print(response.text)