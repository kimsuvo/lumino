import discord
from discord.ext import commands
import sqlite3
import datetime
import config

class MessageSnipe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = sqlite3.connect("snipe.db", detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute("PRAGMA journal_mode=WAL")
        self.conn.commit()
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS mentions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER,
                mentioned_user_id INTEGER,
                mentioner_id INTEGER,
                message_content TEXT,
                timestamp INTEGER
            )
            """
        )
        self.conn.commit()

    def __del__(self):
        self.conn.close()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if message.mentions:
            current_time = int(datetime.datetime.utcnow().timestamp())
            for user in message.mentions:
                self.cursor.execute(
                    "INSERT INTO mentions (channel_id, mentioned_user_id, mentioner_id, message_content, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (message.channel.id, user.id, message.author.id, message.content, current_time)
                )
                self.conn.commit()
                self.cursor.execute(
                    """
                    DELETE FROM mentions
                    WHERE id NOT IN (
                        SELECT id FROM mentions
                        WHERE channel_id = ? AND mentioned_user_id = ?
                        ORDER BY id DESC LIMIT 5
                    )
                    AND channel_id = ? AND mentioned_user_id = ?
                    """,
                    (message.channel.id, user.id, message.channel.id, user.id)
                )
                self.conn.commit()

    @commands.command(name="snipe")
    async def snipe(self, ctx):
        await ctx.message.delete() 

        """
        Sends an embed with up to the last 5 times the command invoker was mentioned in this channel.
        The embed will auto-delete after 5 seconds.
        """
        self.cursor.execute(
            """
            SELECT mentioner_id, message_content, timestamp 
            FROM mentions 
            WHERE channel_id = ? AND mentioned_user_id = ? 
            ORDER BY id DESC LIMIT 5
            """,
            (ctx.channel.id, ctx.author.id)
        )
        rows = self.cursor.fetchall()

        if not rows:
            embed = discord.Embed(
                title="Last 5 Mentions",
                description="No mentions found.",
                color=config.EMBED_COLOR
            )
            await ctx.send(embed=embed, delete_after=5)
            return

        embed = discord.Embed(title="Last 5 Mentions", color=config.EMBED_COLOR)
        for i, (mentioner_id, message_content, timestamp) in enumerate(rows, 1):
            mentioner = self.bot.get_user(mentioner_id)
            mentioner_name = mentioner.name if mentioner else f"User ID {mentioner_id}"
            formatted_time = f"<t:{timestamp}:F>"
            embed.add_field(
                name=f"Mention {i}",
                value=f"**From:** {mentioner_name}\n**Message:** {message_content}\n**Time:** {formatted_time}",
                inline=False
            )

        await ctx.send(embed=embed, delete_after=5)

async def setup(bot):
    await bot.add_cog(MessageSnipe(bot))
