import discord
from discord.ext import commands
import sqlite3
from config import TAG_PERMISSIONS  # List of allowed role IDs

class RemoveTag(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = sqlite3.connect("tags.db")
        self.cursor = self.db.cursor()

    def cog_unload(self):
        self.db.close()

    async def cog_check(self, ctx: commands.Context) -> bool:
        if any(role.id in TAG_PERMISSIONS for role in ctx.author.roles):
            return True
        await ctx.send("You do not have permission to use this command.")
        return False

    @commands.command(name="rmtag", help="Remove a stored tag. Usage: ?rmtag <tag name>")
    async def rmtag(self, ctx: commands.Context, tag_name: str):
        self.cursor.execute("SELECT message FROM tags WHERE tag = ?", (tag_name,))
        row = self.cursor.fetchone()

        if row:
            self.cursor.execute("DELETE FROM tags WHERE tag = ?", (tag_name,))
            self.db.commit()
            await ctx.send(f"Tag '{tag_name}' has been removed.")
        else:
            await ctx.send(f"Tag '{tag_name}' not found.")

async def setup(bot: commands.Bot):
    await bot.add_cog(RemoveTag(bot))
