"""Application entry point"""
from dotenv import load_dotenv
from app import create_app
from app.config import Config

load_dotenv()

app = create_app()

if __name__ == '__main__':
    print(f"Starting app on {Config.HOST}:{Config.PORT} with debug={Config.DEBUG}")
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )
