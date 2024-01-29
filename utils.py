import os
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your_secret_key')
FLASK_SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'your_secret_key')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '12345')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_NAME = "postgres"
DB_HOST = "localhost"
DB_PORT = "9000"
REDIS_HOST = "localhost"
REDIS_PORT = 6379