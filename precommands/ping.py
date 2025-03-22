import discord
from discord.ext import commands
import config

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="<:lumen_check:1345664525042712586> Lumino's Latency",
            description=f"```{latency}ms```",
            color=config.EMBED_COLOR
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Ping(bot))
