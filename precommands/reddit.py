import discord
from discord.ext import commands
import config

class RedditCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="reddit")
    async def reddit_command(self, ctx):
        embed = discord.Embed(
            title="r/thelumen Subreddit",
            description="Check out our community on Reddit: [r/thelumen](https://www.reddit.com/r/thelumen)",
            color=config.EMBED_COLOR
        )
        
        view = discord.ui.View()
        button = discord.ui.Button(
            label="Visit Reddit",
            style=discord.ButtonStyle.link,
            url="https://www.reddit.com/r/thelumen",
            emoji="<:lumen_reddit:1346817971414372422>"
        )
        view.add_item(button)
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(RedditCommand(bot))
