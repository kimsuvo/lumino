import discord
from discord.ext import commands
import sqlite3

class TagListener(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = sqlite3.connect("tags.db")
        self.cursor = self.db.cursor()

    def cog_unload(self):
        self.db.close()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.content.startswith("?tag"):
            parts = message.content.split()
            if len(parts) < 2:
                return
            tag_name = parts[1]
            self.cursor.execute("SELECT message FROM tags WHERE tag = ?", (tag_name,))
            row = self.cursor.fetchone()

            if row:
                tag_message = row[0]
                if message.reference:
                    try:
                        ref_msg = await message.channel.fetch_message(message.reference.message_id)
                        await ref_msg.reply(tag_message, mention_author=False)
                    except Exception as e:
                        await message.channel.send(f"Error sending reply: {e}")
                else:
                    await message.channel.send(tag_message)
            else:
                await message.channel.send(f"Tag '{tag_name}' not found. Sorry!")

async def setup(bot: commands.Bot):
    await bot.add_cog(TagListener(bot))
