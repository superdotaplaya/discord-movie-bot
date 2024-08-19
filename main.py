import discord
from discord.ext import commands, tasks
from discord.commands import Option
import requests
import mysql.connector
from mysql.connector import Error
import os, sys, discord, platform, random, aiohttp, json
import config
import random


mydb = mysql.connector.connect(
          host=config.db_host,
          user="root",
          password=config.db_pass,
          database="user_requests"
          )
mycursor = mydb.cursor()


def add_table():
  
  add_table = """CREATE TABLE movies (
                  server VARCHAR(1000),
                  movie_title VARCHAR(1000),
                  genre VARCHAR(1000)
                )"""
  mycursor.execute(add_table)
  mydb.commit()
  print("done")


def drop_table():
    drop_table = """DROP TABLE movies"""
    mycursor.execute(drop_table)
    mydb.commit()


bot = discord.Bot()


if not os.path.isfile("config.py"):
    sys.exit("'config.py' not found! Please add it and try again.")
else:
    import config


@bot.slash_command(description = "Add a movie to your servers movie list!")
async def addmovie(ctx, movie_title: Option(str, "What movie are you going to add?"), genre: Option(str, "What genre is this movie?")):
    data = (movie_title.lower(), ctx.guild.id)
    query = "SELECT * FROM movies WHERE movie_title = %s AND server = %s"
    mycursor.execute(query, data)
    result = mycursor.fetchall()
    if len(result) >= 1:
        await ctx.respond("This movie is already on your list!")
    else:
        insert_stmt = (
        "INSERT INTO movies(server,movie_title,genre)"
        "VALUES (%s, %s, %s)"
        )
        data = (ctx.guild.id, movie_title.lower(), genre.lower())
        mycursor.execute(insert_stmt,data)
        mydb.commit()
        await ctx.respond(f"{movie_title.title()} has been added to the list!")



@bot.event
async def on_raw_reaction_add(ctx):
    message = bot.get_message(int(ctx.message_id))
    message_text = message.content
    message_author = message.author.id
    print(message_text.split(": "))
    movie_title = message_text.split(": ")[1].lower().replace("```","")
    data = (movie_title,str(ctx.guild_id))
    query = "SELECT * FROM movies WHERE movie_title = %s AND server = %s"
    mycursor.execute(query,data)
    result = mycursor.fetchall()
    if len(result) >= 1:
        if message_author == 1274929108903788665 and movie_title in result[0][1] and ctx.user_id != 1274929108903788665:
            delete_statement = "DELETE FROM movies WHERE movie_title = %s AND server = %s"
            data = (movie_title,ctx.guild_id)                    
            mycursor.execute(delete_statement, data)
            mydb.commit()
            await bot.get_message(int(ctx.message_id)).reply(f"This movie has been removed from your list!")



@bot.slash_command(description = "Add a movie to your servers movie list!")
async def pickmovie(ctx, genre: Option(str, "What genre movie are you wanting to watch? (type 'all' if you want fully random!)")):
    if genre.lower() == "all":
        query = "SELECT * FROM movies WHERE server = %s"
        data = (ctx.guild.id,)
    else:
        query = "SELECT * FROM movies WHERE genre = %s AND server = %s"
        data = (genre,ctx.guild.id)
    
    mycursor.execute(query,data)
    result = mycursor.fetchall()
    if len(result) >= 1:
        movie_number = random.randint(0,len(result)-1)
        await ctx.respond(f"The chosen movie is: {result[movie_number][1]}")
        message = await bot.get_channel(int(ctx.channel_id)).send(content = f"```Reacting below will remove the movie from your list: {result[movie_number][1]}```")
        await message.add_reaction("✅")
    else:
        await ctx.respond("No movies found for this genre! Try adding some with /addmovie")

@bot.slash_command(description = "Use in a thread text channel to add movies as a batch (1 movie per message)")
async def addmovie_batch(ctx, genre: Option(str, "What genre are these movies?")):
    channel = ctx.channel_id
    movies_added = 0
    await ctx.respond("Adding movies/shows now!")
    messages = await ctx.channel.history(limit=200).flatten()
    for message in messages[:-1]:
        insert_stmt = (
        "INSERT INTO movies(server,movie_title,genre)"
        "VALUES (%s, %s, %s)"
        )
        data = (ctx.guild.id, message.content.lower(), genre.lower())
        mycursor.execute(insert_stmt,data)
        mydb.commit()
        movies_added += 1
    await bot.get_channel(int(ctx.channel_id)).send(f"Successfully added {movies_added} to the {genre.title()} list!")

bot.run(config.discord_token)