import discord
from discord.ext import commands
import config

class MediaChannelListener(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.channel.id != config.MEDIA_CHANNEL_ID:
            return
        if message.attachments:
            return
        try:
            await message.delete()
        except discord.errors.NotFound:
            return

        embed = discord.Embed(
            description="Do not send message content here. This channel is made for sending media files.",
            color=config.EMBED_COLOR
        )
        error_message = await message.channel.send(embed=embed)
        await error_message.delete(delay=5)

async def setup(bot: commands.Bot):
    await bot.add_cog(MediaChannelListener(bot))
