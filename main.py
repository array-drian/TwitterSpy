import asyncio
from db_config import config as db_config
from decouple import config as decouple_config
import discord
from discord.ext import commands
import mysql.connector
import nest_asyncio
from twscrape import API, gather

nest_asyncio.apply()

#------------------------------------Script----------------------------------

#-------------------Database-------------------

try:
    connection = mysql.connector.connect(**db_config)
    connection.autocommit = True
    if connection.is_connected():
        print('Connected to MySQL database')
except mysql.connector.Error as e:
    print(f'Error connecting to MySQL database: {e}')

#-------------------DB-Functions-------------------

def getCurrentFollowingsForUser(user_id):
    cursor = connection.cursor()
    sql = "SELECT u.* FROM tracked_followings AS f INNER JOIN followed_users AS u ON f.followed_user_id = u.followed_user_id WHERE f.tracked_user_id = %s"
    param = (str(user_id),)
    cursor.execute(sql, param)
    rows = cursor.fetchall()
    return rows

def getTrackedUser(user_id):
    cursor = connection.cursor()
    sql = "SELECT * FROM tracked_users WHERE tracked_user_id = %s"
    param = (str(user_id),)
    cursor.execute(sql, param)
    rows = cursor.fetchall()
    return rows

def getFollowedUser(user_id):
    cursor = connection.cursor()
    sql = "SELECT * FROM followed_users WHERE followed_user_id = %s"
    param = (str(user_id),)
    cursor.execute(sql, param)
    rows = cursor.fetchall()
    return rows

def getCurrentFollowedUsers():
    cursor = connection.cursor()
    sql = "SELECT * FROM followed_users"
    cursor.execute(sql)
    rows = cursor.fetchall()
    return rows

def getActivelyTrackedUsers():
    cursor = connection.cursor()
    sql = "SELECT * FROM tracked_users WHERE tracking_active = %s"
    param = (1,)
    cursor.execute(sql, param)
    rows = cursor.fetchall()
    return rows

def addNewFollowing(id, name, url):
    cursor = connection.cursor()
    sql = "INSERT INTO followed_users (followed_user_id, followed_user_name, followed_user_url) VALUES (%s, %s, %s)"
    data = (str(id), name, url)
    cursor.execute(sql, data)
    connection.commit()

def addNewTrackedFollowing(user_id, following_id):
    cursor = connection.cursor()
    sql = "INSERT INTO tracked_followings (tracked_user_id, followed_user_id) VALUES (%s, %s)"
    data = (str(user_id), str(following_id))
    cursor.execute(sql, data)
    connection.commit()

async def addNewTrackedUser(name):
    user = await getUserDetails(name)
    try:
        if len(getTrackedUser(user.id)) == 0:
            cursor = connection.cursor()
            sql = "INSERT INTO tracked_users (tracked_user_id, tracked_user_name, tracked_user_url) VALUES (%s, %s, %s)"
            data = (str(user.id), name, user.url)
            cursor.execute(sql, data)
            connection.commit()
            return True
        else:
            cursor = connection.cursor()
            sql = "UPDATE tracked_users SET tracking_active = %s WHERE tracked_user_id = %s"
            data = (1, str(user.id))
            cursor.execute(sql, data)
            connection.commit()
            return True    
    except Exception as e:
        return False

async def updateTrackedFollowings(currentList, newList, user_id):
    onlyInCurrentList = currentList - newList
    onlyInNewList = newList - currentList

    if(len(onlyInCurrentList) != 0):
        await removedFollowings(getTrackedUser(user_id)[0][1], onlyInCurrentList)
        for i in onlyInCurrentList:
            removeTrackedFollowing(user_id, i[0])
    elif(len(onlyInNewList) != 0):
        await newFollowings(getTrackedUser(user_id)[0][1], onlyInNewList)
        for i in onlyInNewList:
            addNewTrackedFollowing(user_id, i[0])

def updateFollowedUsers(currentList, newList):
    onlyInNewList = newList - currentList

    if(len(onlyInNewList) != 0):
        for i in onlyInNewList:
            if len(getFollowedUser(i[0])) == 0:
                addNewFollowing(i[0], i[1], i[2])
            else:
                updateFollowedUser(i[0], i[1], i[2])

def updateFollowedUser(user_id, name, url):
    cursor = connection.cursor()
    sql = "UPDATE followed_users SET followed_user_name = %s, followed_user_url = %s WHERE followed_user_id = %s"
    data = (name, url, str(user_id))
    cursor.execute(sql, data)
    connection.commit()

async def untrackUser(name):
    user = await getUserDetails(name)
    try:
        cursor = connection.cursor()
        sql = "UPDATE tracked_users SET tracking_active = %s WHERE tracked_user_id = %s"
        data = (0, str(user.id))
        cursor.execute(sql, data)
        connection.commit()
        return True
    except Exception as e:
        return False


def removeTrackedFollowing(user_id, following_id):
    cursor = connection.cursor()
    sql = "DELETE FROM tracked_followings WHERE tracked_user_id = %s AND followed_user_id = %s"
    data = (str(user_id), str(following_id))
    cursor.execute(sql, data)
    connection.commit()

#-------------------Other Functions-------------------

def updateNeeded(currentList, newList):
    if(currentList - newList == newList - currentList):
        return False
    else:
        return True

async def getUserDetails(name):
    api = API()
    user = await api.user_by_login(name)
    return user

#-------------------Process-------------------

async def process_user(api, user_id):
    followings = await gather(api.following(user_id, limit=10000))
    print('tracked Followings for: ' + getTrackedUser(user_id)[0][1])
    friends = []
    for friend in followings:  # NewFollowingList
        friends.append((str(friend.id), friend.username, friend.url))

    currentFollowing = getCurrentFollowingsForUser(user_id)  # CurrentFollowingList
    allFollowedUsers = getCurrentFollowedUsers()  # AllFollowedUsers

    # Add new identified followings to 'followed_users'
    if updateNeeded(set(allFollowedUsers), set(friends)):
        updateFollowedUsers(set(allFollowedUsers), set(friends))

    # Update 'followed_trackings'
    if updateNeeded(set(currentFollowing), set(friends)):
        await updateTrackedFollowings(set(currentFollowing), set(friends), user_id)

#-------------------Main-------------------

async def main():
    api = API()
    
    while True:
        try:
            tracked_users = getActivelyTrackedUsers()
            user_ids = [user[0] for user in tracked_users]
            tasks = [process_user(api, user_id) for user_id in user_ids]
            await asyncio.gather(*tasks)
            print('I am still up and running...')
            await asyncio.sleep(60)
        except Exception as e:
            print('Something went wrong.')

#------------------------------------Discord Bot----------------------------------

#-------------------Intents----------------------

intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent

#-------------------Settings----------------------

bot = commands.Bot(command_prefix='/', intents=intents)

#-------------------On Startup----------------------

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')

#-------------------Commands----------------------

@bot.command(name='add_tracking', help='Track a new User')
async def add_tracking(ctx, *, message):
    success = await addNewTrackedUser(message)
    if success:
        await ctx.send('Now tracking User: ' + message)
    else:
        await ctx.send('Something went wrong.')

@bot.command(name='untrack_user', help='Untrack an existing User')
async def untrack_user(ctx, *, message):
    success = await untrackUser(message)
    if success:
        await ctx.send('Now untracking User: ' + message)
    else:
        await ctx.send('Something went wrong.')

@bot.command(name='list_tracked_users', help='Get a list of all tracked User')
async def list_tracked_users(ctx):
    tracked_users = getActivelyTrackedUsers()
    for i in range(0, len(tracked_users), 20):
        embed = discord.Embed(description="Currently tracking " + str(len(tracked_users)) + " Users:")
        embed.colour = discord.Colour.green()
        for user in tracked_users[i:i+20]:
            embed.add_field(name=user[1], value=f"[{user[2]}]", inline=False)
        await ctx.send(embed=embed)


#-------------------Bot Functions----------------------

async def newFollowings(user, followings):
    channel = bot.get_channel(1241731419361906718)
    if channel is not None:
        followings = list(followings) 
        for i in range(0, len(followings), 20):
            embed = discord.Embed(description=f"{user} is now following:")
            embed.colour = discord.Colour.green()
            for follow in followings[i:i+20]:
                embed.add_field(name=follow[1], value=f"[{follow[2]}]", inline=False)
            await channel.send(embed=embed)

async def removedFollowings(user, followings):
    channel = bot.get_channel(1241731419361906718)
    if channel is not None:
        followings = list(followings) 
        for i in range(0, len(followings), 20):
            embed = discord.Embed(description=f"{user} has unfollowed:")
            embed.colour = discord.Colour.red()
            for follow in followings[i:i+20]:
                embed.add_field(name=follow[1], value=f"[{follow[2]}]", inline=False)
            await channel.send(embed=embed)

#-------------------Start----------------------

async def run_bot():
    while True:
        try:
            await bot.start(decouple_config('BOT_TOKEN'))
        except (discord.errors.HTTPException, discord.errors.GatewayNotFound, discord.errors.ConnectionClosed, asyncio.TimeoutError) as e:
            print(f'Bot encountered an error: {e}. Reconnecting in 5 seconds...')
            await bot.close()  # Ensure the bot is properly closed
            await asyncio.sleep(5)  # Wait before reconnecting

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(run_bot(), main()))