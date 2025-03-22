import discord
from discord.ext import commands
import config
import sqlite3

class TicketUnhold(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="unhold")
    async def unhold_ticket(self, ctx):
        """
        Reverts the hold on the ticket channel by re-enabling send_messages for all added users (not roles).
        Also removes the channel id from tickethold.db.
        This command only works if executed in a channel whose category ID is in config.TICKET_CATEGORY_IDS.
        """
        if not ctx.channel.category or ctx.channel.category.id not in config.TICKET_CATEGORY_IDS:
            return

        count = 0
        for target, overwrite in ctx.channel.overwrites.items():
            if isinstance(target, discord.Member):
                new_overwrite = overwrite
                new_overwrite.send_messages = True
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
            c.execute("DELETE FROM ticket_hold WHERE channel_id = ?", (ctx.channel.id,))
            conn.commit()
            conn.close()
        except Exception as e:
            embed = discord.Embed(
                title="Database Error",
                description=f"Error removing channel from hold database: {e}",
                color=config.EMBED_COLOR
            )
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title="Ticket Unheld",
            description=f"Ticket is now unheld. Re-enabled send messages for {count} user(s).",
            color=config.EMBED_COLOR
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(TicketUnhold(bot))