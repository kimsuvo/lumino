import discord
from discord.ext import commands
import config
import sqlite3
from datetime import datetime

class TicketHold(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="hold")
    async def hold_ticket(self, ctx):
        """
        Puts the ticket on hold by removing the ability to send messages for all added users (not roles).
        Logs the hold event in tickethold.db with the channel ID and timestamp.
        This command only works if executed in a channel whose category ID is in config.TICKET_CATEGORY_IDS.
        """
        if not ctx.channel.category or ctx.channel.category.id not in config.TICKET_CATEGORY_IDS:
            return

        count = 0
        for target, overwrite in ctx.channel.overwrites.items():
            if isinstance(target, discord.Member):
                new_overwrite = overwrite
                new_overwrite.send_messages = False
                try:
                    await ctx.channel.set_permissions(target, overwrite=new_overwrite)
                    count += 1
                except Exception as e:
                    embed = discord.Embed(
                        title="Error",
                        description=f"Failed to update permissions for {target.mention}: {e}",
                        color=config.EMBED_COLOR
                    )
                    await ctx.send(embed=embed)
                    continue
        try:
            conn = sqlite3.connect("tickethold.db")
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS ticket_hold (
                    channel_id INTEGER PRIMARY KEY,
                    hold_time TEXT
                )
            """)
            c.execute("INSERT OR REPLACE INTO ticket_hold (channel_id, hold_time) VALUES (?, ?)",
                      (ctx.channel.id, datetime.utcnow().isoformat()))
            conn.commit()
            conn.close()
        except Exception as e:
            embed = discord.Embed(
                title="Database Error",
                description=f"Error logging ticket hold: {e}",
                color=config.EMBED_COLOR
            )
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title="Ticket On Hold",
            description=f"Ticket is now on hold. Disabled send messages for {count} user(s).",
            color=config.EMBED_COLOR
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(TicketHold(bot))