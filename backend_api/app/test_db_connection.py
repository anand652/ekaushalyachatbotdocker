from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:anandpm19@localhost/chatbot_db"

engine = create_engine(DATABASE_URL, echo=True)

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM companies;"))
        for row in result:
            print(row)
    print("Connection successful!")
except Exception as e:
    print("Connection failed:", e)
