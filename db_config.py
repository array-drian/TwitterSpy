from decouple import config as decouple_config

#-------------------Databse-------------------
config = {
    'user': decouple_config('DB_USER'),
    'password': decouple_config('DB_PASSWORD'),
    'host': decouple_config('DB_HOST'),
    'database': decouple_config('DB_NAME'),
    'port': decouple_config('DB_PORT') 
}