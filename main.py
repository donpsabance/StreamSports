import os
from bs4 import BeautifulSoup
import discord
from discord.ext import commands
from discord.ext.commands import CommandNotFound
from dotenv import load_dotenv
import requests
import socket

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='/', description='ehh')


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        return


@bot.command()
async def watch(ctx, *args):

    # await ctx.send('@' + ctx.author.id)
    result = find_game(*args)
    link = result[0]
    game = result[1]

    # await ctx.send(link)
    # await ctx.send(game.split('\n')[0])
    # await ctx.send(game.split('\n')[1])

    embedded = discord.Embed(title=game.split('\n')[0], url=link)
    embedded.set_footer(text=game.split('\n')[1])
    await ctx.send(embed=embedded)
    # await ctx.send(find_game(*args))


def find_game(*args):

    if len(args) == 2:

        category = args[0]
        team = args[1]

        url_end = ''
        if category.lower() == 'nba':
            url_end = 'nbastreams/'
        elif category.lower() == 'nfl':
            url_end = 'nfl-streams/'

        url = 'http://crackstreams.com/' + url_end
        page = requests.get(url)

        soup = BeautifulSoup(page.content, 'html.parser')
        links = soup.findAll('a', href=True)

        for link in links:

            media = link.find('div', {'class': 'media'})
            if media is not None:
                if team in media.get_text().strip().lower():

                    return link['href'], link.get_text().strip()

        return "No scheduled games found"

    else:

        return "Invalid command, please use /watch <nba/nfl/mma...> <team name> \n Example: /watch nba warriors"


# find_game('nba', 'hornets')
bot.run(TOKEN)