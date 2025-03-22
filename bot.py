import discord
from discord.ext import commands
import os
import config
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

intents = discord.Intents.all()
help_command = None
bot = commands.Bot(command_prefix="!", intents=intents, help_command=help_command, application_id=config.APPLICATION_ID)

async def load_extensions():
    precommands_dir = "./precommands"
    if os.path.exists(precommands_dir):
        for filename in os.listdir(precommands_dir):
            if filename.endswith(".py"):
                extension = filename[:-3]
                try:
                    await bot.load_extension(f"precommands.{extension}")
                    logger.info(f"Loaded precommand extension: {extension}")
                except Exception as e:
                    logger.error(f"Failed to load precommand {extension}: {e}")

    cogs_dir = "./cogs"
    if os.path.exists(cogs_dir):
        for filename in os.listdir(cogs_dir):
            if filename.endswith(".py"):
                extension = filename[:-3]
                try:
                    await bot.load_extension(f"cogs.{extension}")
                    logger.info(f"Loaded cog extension: {extension}")
                except Exception as e:
                    logger.error(f"Failed to load cog {extension}: {e}")

async def load_app_extensions():
    appcommands_dir = "./guild_appcommands"
    if os.path.exists(appcommands_dir):
        for filename in os.listdir(appcommands_dir):
            if filename.endswith(".py"):
                extension = filename[:-3]
                try:
                    await bot.load_extension(f"guild_appcommands.{extension}")
                    logger.info(f"Loaded guild app command extension: {extension}")
                except Exception as e:
                    logger.error(f"Failed to load guild app command {extension}: {e}")

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online)
    logger.info(f"Logged in as {bot.user}")

    for guild in bot.guilds:
        if guild.id != config.GUILD_ID:
            await guild.leave()
            logger.info(f"Left guild '{guild.name}' because it's not the allowed guild (ID: {config.GUILD_ID}).")
    
    target_guild = discord.Object(id=config.GUILD_ID)
    await bot.tree.sync(guild=target_guild)
    logger.info(f"Synced app commands to the guild with ID: {config.GUILD_ID}")


@bot.event
async def on_guild_join(guild):
    if guild.id != config.GUILD_ID:
        await guild.leave()
        logger.info(f"Left guild '{guild.name}' upon joining because it's not the allowed guild (ID: {config.GUILD_ID}).")

async def main():
    await load_extensions()
    await load_app_extensions()
    await bot.start(config.TOKEN)

if __name__ == '__main__':
    asyncio.run(main())
