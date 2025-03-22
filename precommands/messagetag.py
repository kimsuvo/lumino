import discord
from discord.ext import commands
import sqlite3
from config import TAG_PERMISSIONS 

class MessageTags(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = sqlite3.connect("tags.db")
        self.cursor = self.db.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                tag TEXT PRIMARY KEY,
                message TEXT
            )
        """)
        self.db.commit()

    def cog_unload(self):
        self.db.close()

    async def cog_check(self, ctx: commands.Context) -> bool:
        if any(role.id in TAG_PERMISSIONS for role in ctx.author.roles):
            return True
        await ctx.send("You do not have permission to use this command.")
        return False

    @commands.command(name="mtag", help="Create or retrieve a message tag. Usage: !mtag <tag name> [message]")
    async def mtag(self, ctx: commands.Context, tag_name: str, *, message: str = None):
        if message is None:
            self.cursor.execute("SELECT message FROM tags WHERE tag = ?", (tag_name,))
            row = self.cursor.fetchone()
            if row:
                tag_message = row[0]
                if ctx.message.reference:
                    try:
                        ref_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                        await ref_msg.reply(tag_message, mention_author=False)
                    except Exception as e:
                        await ctx.send(f"Error sending reply: {e}")
                else:
                    await ctx.send(tag_message)
            else:
                await ctx.send(f"Tag '{tag_name}' not found.")
        else:
            self.cursor.execute("REPLACE INTO tags (tag, message) VALUES (?, ?)", (tag_name, message))
            self.db.commit()
            await ctx.send(f"Tag '{tag_name}' saved.")

async def setup(bot: commands.Bot):
    await bot.add_cog(MessageTags(bot))
