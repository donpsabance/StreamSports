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
async def on_ready():
    print('StreamSports bot is ready to go!')


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        return


@bot.command()
async def watch(ctx, *args):

    # await ctx.send('@' + ctx.author.id)
    result = find_game(*args)
    if type(result) == tuple:
        link = result[0]
        game = result[1]

        embedded = discord.Embed(title=game.split('\n')[0], url=link)
        embedded.set_footer(text=game.split('\n')[1])
        await ctx.send(embed=embedded)
        # await ctx.send(find_game(*args))

    elif type(result) == list:

        embedded = discord.Embed(title="Livestreams", url='http://crackstreams.com/nbastreams/')
        for games in result:
            embedded.add_field(name='-', value='[Game](' + games[0] + ')\n' + games[1])
        await ctx.send(embed=embedded)

    else:

        await ctx.send(result)


@bot.command()
async def scores(ctx, *args):

    result = get_score(*args)
    if type(result) == tuple:

        embedded = discord.Embed(title="Scores", description=result[0] + '\n' + result[1])
        await ctx.send(embed=embedded)

    elif type(result) == list:

        embedded = discord.Embed(title="Scores", url='https://sports.yahoo.com/nba/scoreboard/')
        for current_score in result:

            embedded.add_field(name='-', value=current_score[0] + '\n' + current_score[1])
        await ctx.send(embed=embedded)

    else:

        await ctx.send(result)


def find_game(*args):

    if 3 > len(args) > 0:

        category = args[0]

        url_end = ''
        if category.lower() == 'nba':
            url_end = 'nbastreams/'
        elif category.lower() == 'nfl':
            url_end = 'nfl-streams/'

        url = 'http://crackstreams.com/' + url_end
        page = requests.get(url)

        soup = BeautifulSoup(page.content, 'html.parser')
        links = soup.findAll('a', href=True)
        results = []

        for link in links:

            media = link.find('div', {'class': 'media'})
            if media is not None:

                if len(args) == 1:

                    if 'vs' in media.get_text().strip().lower():
                        results.append((link['href'], link.get_text().strip()))

                elif len(args) == 2:

                    team = args[1]
                    if team in media.get_text().strip().lower():
                        return link['href'], link.get_text().strip()

        if len(results) == 0:
            return "No livestreams found"

        else:
            return results

    else:

        return "Invalid command, please use /watch <nba/nfl/mma...> <team name> \nExample: /watch nba warriors"


def get_score(*args):

    if 3 > len(args) > 0:

        team_scores = []

        if args[0].lower() == 'nba':

            url = 'https://sports.yahoo.com/nba/scoreboard/'
            page = requests.get(url)

            soup = BeautifulSoup(page.content, 'html.parser')
            scoreboards = soup.findAll('div', {'class': 'scoreboard-group-1'})

            for scoreboard in scoreboards:

                games = scoreboard.findAll('div', {'class': 'score'})

                for game in games:

                    game_scores = game.findAll('span', {'class': 'YahooSans'})

                    team_a = ''
                    team_b = ''
                    counter = 0
                    for score in game_scores:

                        if counter < 3:
                            team_a += score.get_text().strip() + " "
                        else:
                            team_b += score.get_text().strip() + " "
                        counter += 1

                        if counter == 6:

                            team_a = team_a.strip()
                            team_b = team_b.strip()

                            team_scores.append((team_a, team_b))
                            team_a = ''
                            team_b = ''
                            counter = 0

            if len(team_scores) == 0:
                return "No current games being played"

            if len(args) == 1:
                return team_scores

            elif len(args) == 2:

                team = args[1]
                for (a, b) in team_scores:
                    if team.lower() in a.lower() or team in b.lower():
                        return a, b

    else:
        return "Invalid command, please use /scores <nba/nfl/mma...> <team name> \nExample: /score nba warriors"


bot.run(TOKEN)