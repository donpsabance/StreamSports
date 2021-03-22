import os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import discord
from discord.ext import commands
from discord.ext.commands import CommandNotFound
from dotenv import load_dotenv
import requests

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix='/', description='ehh')


@bot.event
async def on_ready():
    print('StreamSports bot is ready to go!')

    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening,
                                                        name='/ss'))


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        return


@bot.command(name='ss')
async def help_me(ctx, *args):

    embedded = discord.Embed(title='StreamSports')
    embedded.add_field(name='/watch <nba/nfl> <team>',
                       value='The first field is required, the second is optional. '
                             'If only one field is passed onto the command, '
                             'a whole list of games steams will be displayed')
    embedded.add_field(name='/scores <nba/nfl> <team>',
                       value='The first field is required, the second is optional. '
                             'If only one field is passed onto the command, '
                             'a whole list of game scores will be displayed')
    await ctx.send(embed=embedded)


@bot.command()
async def watch(ctx, *args):

    # await ctx.send('@' + ctx.author.id)
    result = find_game(*args)
    result_alternative = find_game_alternative(*args)

    if result is not None:
        if type(result) == tuple:
            link = result[0]
            game = result[1]

            embedded = discord.Embed(title=game.split('\n')[0], url=link)
            embedded.set_footer(text=game.split('\n')[1])
            await ctx.send(embed=embedded)

        elif type(result) == list:

            embedded = discord.Embed(title="Livestreams", url='http://crackstreams.is/nba-streams/')
            for games in result:
                embedded.add_field(name='-', value='[Game](' + games[0] + ')\n' + games[1])
            await ctx.send(embed=embedded)

        else:

            embedded = discord.Embed(title="ERROR", description=result)
            await ctx.send(embed=embedded)

    else:

        embedded = discord.Embed(title="ERROR", description="No livestreams found")
        await ctx.send(embed=embedded)

    if result_alternative is not None:
        # all games
        if type(result_alternative) == list:

            embedded = discord.Embed(title='Alternate links', url='https://nbabite.com/')
            for result in result_alternative:
                embedded.add_field(name='-', value=result)
            await ctx.send(embed=embedded)

        # certain team
        elif type(result_alternative) == str:

            embedded = discord.Embed(title='Alternate link', url=result_alternative)
            await ctx.send(embed=embedded)

        else:

            embedded = discord.Embed(title="ERROR", description=result)
            await ctx.send(embed=embedded)


@bot.command()
async def scores(ctx, *args):

    result = get_score(*args)
    date = datetime.now() - timedelta(hours=8)

    if type(result) == tuple:

        embedded = discord.Embed(title="Scores", description=result[0] + '\n' + result[1])
        await ctx.send(embed=embedded)

    elif type(result) == list:

        embedded = discord.Embed(title="Scores", url='https://sports.yahoo.com/nba/scoreboard/')
        for current_score in result:

            embedded.add_field(name='-', value=current_score[0] + '\n' + current_score[1])
        await ctx.send(embed=embedded)

    else:

        embedded = discord.Embed(description='No current games being played')
        await ctx.send(embed=embedded)


def find_game(*args):

    if 3 > len(args) > 0:

        category = args[0]

        url_end = ''
        if category.lower() == 'nba':
            url_end = 'nbastreams/'
        elif category.lower() == 'nfl':
            url_end = 'nfl-streams/'

        try:

            url = 'http://crackstreams.is/' + url_end
            page = requests.get(url)

            soup = BeautifulSoup(page.content, 'html.parser')
            links = soup.findAll('a', href=True)

        except requests.exceptions.RequestException:
            return "Could not reach main server. Try again in a few minutes"

        results = []
        for link in links:

            media = link.find('div', {'class': 'media'})
            if media is not None:

                if len(args) == 1:

                    if 'vs' in media.get_text().strip().lower() or '@' in media.get_text().strip().lower():
                        results.append((link['href'], link.get_text().strip()))

                elif len(args) == 2:

                    team = args[1]
                    if team in media.get_text().strip().lower():
                        return link['href'], link.get_text().strip()

        if len(results) == 0:
            return "No livestreams found"

        elif len(results) == 1:
            return results[0]

        else:
            return results

    else:

        return "Invalid command, please use /watch <nba/nfl/mma...> <team name> \nExample: /watch nba warriors"


def find_game_alternative(*args):

    if 3 > len(args) > 0:

        category = args[0]

        url = ''
        if category.lower() == 'nba':
            url = 'https://nbabite.com/'
        elif category.lower() == 'nfl':
            url = 'https://nflbite.com/'
        else:
            return "Invalid league. NBA and NFL are the only ones currently supported"

        try:
            page = requests.get(url)
            soup = BeautifulSoup(page.content, 'html.parser')
            games = soup.findAll('div', {'class': 'competition'})
            found_games = None

        except requests.exceptions.RequestException:
            return "Could not reach alternate server. Try again in a few minutes"

        results = []
        for game in games:

            names = game.findAll('div', {'class': 'name'})
            for name in names:
                if name is not None:
                    if 'nba' in name.get_text().lower() or 'nfl' in name.get_text().lower():
                        found_games = game

        if found_games is not None:
            links = found_games.findAll('a', href=True)

            for link in links:
                results.append(link['href'])

        # find all streams
        if len(args) == 1:
            if len(results) == 1:
                return results[0]
            else:
                return results

        # find a certain team stream
        elif len(args) == 2:

            team = args[1]
            for result in results:
                if team in result:
                    return result


def get_score(*args):

    if 3 > len(args) > 0:

        date_now = datetime.now() - timedelta(hours=8)
        date = date_now.strftime('%Y-%m-%d')
        team_scores = []

        url = ''
        if args[0].lower() == 'nba':
            url = 'https://sports.yahoo.com/nba/scoreboard/?confId=&schedState=1&dateRange=' + str(date)
        elif args[0].lower() == 'nfl':
            url = 'https://ca.sports.yahoo.com/nfl/scoreboard/'

        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        scoreboards = soup.findAll('div', {'class': 'scoreboard'})

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
