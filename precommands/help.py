import discord
from discord.ext import commands
import config

class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_command(self, ctx):
        embed = discord.Embed(title="Help Commands", color=config.EMBED_COLOR)
        embed.add_field(
            name="!ping",
            value="Shows bot's latency.\nUsage: `!ping`",
            inline=False
        )
        embed.add_field(
            name="!ts",
            value="Translates a message to English.\nUsage: `!ts <message>` or use `!ts` while replying to a message.",
            inline=False
        )
        embed.add_field(
            name="?tag",
            value="Gets information or terminology about a keyword or term.\nUsage: `?tag <keyword>`",
            inline=False
        )
        embed.add_field(
            name="?cleardm",
            value="Deletes all the messages sent by Lumino in your DMs.\nUsage: `!cleardm`",
            inline=False
        )
        if any(role.id in (config.MODERATOR_ROLE_ID, config.VOLUNTEER_ROLE_ID) for role in ctx.author.roles):
            embed.add_field(
                name="!sb",
                value="Starboards a message.\nUsage: use `!sb` while replying to a message.",
                inline=False
            )
            embed.add_field(
                name="!purge",
                value="Deletes a specified number of messages.\nUsage: !purge [Number of Messages] <User>.",
                inline=False
            )
            
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(HelpCommand(bot))
