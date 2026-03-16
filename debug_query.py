import asyncio
import os
import sys

# Add root to path
sys.path.append(os.getcwd())

from api.schemas import QueryRequest
from api.main import run_query

async def test():
    req = QueryRequest(disease="Alzheimer")
    try:
        response = await run_query(req)
        print("Response successful")
        print(response)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
