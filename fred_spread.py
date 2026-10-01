from dotenv import load_dotenv
import os

load_dotenv()

if (os.getenv("FRED_KEY")):
    print("FRED_KEY is set.")
else:
    print("FRED_KEY is not set.")

