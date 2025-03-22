import discord
from discord.ext import commands
from googletrans import Translator
import config
import random
import asyncio

class MessageTranslate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.translator = Translator()
        self.lock = asyncio.Lock()

    @commands.command(name="ts")
    async def translate_command(self, ctx, *, message: str = None):
        """
        Translates a given message to English.
        Usage:
        1) !ts <message>  - Translate provided text.
        2) Reply to a message with !ts - Translates the replied message.
        3) !ts with no content or reply - Returns an error embed.
        """
        async with self.lock:
            await asyncio.sleep(random.uniform(0.5, 1.5))
            text_to_translate = None
            if message:
                text_to_translate = message
            elif ctx.message.reference:
                try:
                    ref_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                    text_to_translate = ref_msg.content
                except Exception:
                    pass
            if not text_to_translate:
                embed = discord.Embed(
                    description="Please provide a message to translate or reply to a message with the command.",
                    color=config.EMBED_COLOR
                )
                await ctx.send(embed=embed)
                return
            try:
                translation = self.translator.translate(text_to_translate, dest='en')
                translated_text = translation.text
            except Exception:
                embed = discord.Embed(
                    title="Translation Error",
                    description="An error occurred while translating the text.",
                    color=config.EMBED_COLOR
                )
                await ctx.send(embed=embed)
                return
            if ctx.message.reference:
                await ctx.send(
                    translated_text,
                    reference=ctx.message,
                    allowed_mentions=discord.AllowedMentions(users=False, replied_user=False)
                )
            else:
                await ctx.send(translated_text)

async def setup(bot):
    await bot.add_cog(MessageTranslate(bot))
