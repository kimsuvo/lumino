import discord
from discord.ext import commands
import config
import sqlite3
import logging

logger = logging.getLogger(__name__)

class RemindTicket(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="remind")
    async def remind(self, ctx: commands.Context):
        await ctx.message.delete()

        """
        Check the current channel's ID in both API and DEV ticket databases for a ticket owner.
        If a ticket is found, DM that user a reminder that their ticket is still open in r/thelumen.
        Only executable by members with the developer role (config.DEVELOPER_ROLE_ID).
        """
        if config.DEVELOPER_ROLE_ID not in [role.id for role in ctx.author.roles]:
            await ctx.send("You do not have permission to use this command.", delete_after=5)
            return

        channel_id = ctx.channel.id
        ticket_owner_id = None

        try:
            conn = sqlite3.connect("api_tickets.db")
            c = conn.cursor()
            c.execute("SELECT user_id FROM tickets WHERE channel_id = ?", (channel_id,))
            result = c.fetchone()
            conn.close()
            if result:
                ticket_owner_id = result[0]
        except Exception as e:
            logger.error(f"Error checking API tickets for channel {channel_id}: {e}")

        if ticket_owner_id is None:
            try:
                conn = sqlite3.connect("dev_tickets.db")
                c = conn.cursor()
                c.execute("SELECT user_id FROM tickets WHERE channel_id = ?", (channel_id,))
                result = c.fetchone()
                conn.close()
                if result:
                    ticket_owner_id = result[0]
            except Exception as e:
                logger.error(f"Error checking DEV tickets for channel {channel_id}: {e}")

        if ticket_owner_id is None:
            await ctx.send("No open ticket found for this channel.", delete_after=5)
            return

        embed = discord.Embed(
            title="Ticket Reminder",
            description=(
                "Your ticket is still open in [r/thelumen](https://discord.gg/thelumen).\n"
                "Kindly check your ticket for further details."
            ),
            color=config.EMBED_COLOR
        )

        view = discord.ui.View()
        view_ticket_url = f"https://discord.com/channels/{ctx.guild.id}/{ctx.channel.id}"
        button_view_ticket = discord.ui.Button(
            label="View Ticket",
            style=discord.ButtonStyle.link,
            url=view_ticket_url,
            emoji="<:lumen_transcript:1345750636746117210>"
        )
        view.add_item(button_view_ticket)
        
        button_rthelumen = discord.ui.Button(
            label="r/thelumen",
            style=discord.ButtonStyle.link,
            url="https://discord.gg/thelumen",
            emoji="<:lumen_circular:1346864579757477968>"
        )
        view.add_item(button_rthelumen)

        try:
            ticket_owner = await self.bot.fetch_user(ticket_owner_id)
            await ticket_owner.send(embed=embed, view=view)
            await ctx.send("Reminder sent successfully.", delete_after=5)
        except Exception as e:
            logger.error(f"Error sending reminder DM to user {ticket_owner_id}: {e}")
            await ctx.send("Failed to send the reminder DM.", delete_after=5)

async def setup(bot: commands.Bot):
    await bot.add_cog(RemindTicket(bot))
