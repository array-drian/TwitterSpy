# TwitterSpy
This bot is used to track certained users followings/unfollowings.

## Getting started

### Get the software
git clone https://github.com/array-drian/TwitterSpy.git

pip install -r requirements.txt

### Creating your Discord bot

Go to https://discord.com/developers/ and create your application. Make sure to copy your Bot-Token and save it for later usage.

### Create the Database

Now you need to Create a Database named 'Discordbot' and three Tabled called: tracked_users, followed_users and tracked_followings.

#### tracked_users

- tracked_user_id (VARCHAR(45)) Primary key
- tracked_user_name (VARCHAR(45))
- tracked_user_url (VARCHAR(45))

#### followed_users

- followed_user_id (VARCHAR(45)) Primary key
- followed_user_name (VARCHAR(45))
- followed_user_url (VARCHAR(45))

#### tracked_followings

- tracked_followings_id (INT) Primary key, AI
- tracked_user_id (VARCHAR(45)) Foreign Key
- followed_user_id (VARCHAR(45)) Foreign Key

### Insert your Data into .env

Now you need to insert your: DB_NAME, DB_HOST, DB_USER, DB_PASSWORD, DB_PORT, BOT_TOKEN into the .env-configuration file.

### Setting up TWSCRAPE

This bot uses TWSCRAPE to scrape twitter. Check out https://github.com/vladkens/twscrape to get started.
