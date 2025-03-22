# precommands/listemoji.py
import discord
from discord.ext import commands
import config

class ListEmoji(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_any_role(*config.STARBOARD_PERMISSIONS)

    async def listemoji(self, ctx):
        
        emojis = ctx.guild.emojis
        if not emojis:
            await ctx.send("No custom emojis found in this server.")
            return

        lines = [f"{emoji} -- `{emoji}`" for emoji in emojis]
        
        message = "\n".join(lines)
        if len(message) > 2000:
            chunks = [message[i : i + 2000] for i in range(0, len(message), 2000)]
            for chunk in chunks:
                await ctx.send(chunk)
        else:
            await ctx.send(message)

async def setup(bot):
    await bot.add_cog(ListEmoji(bot))
