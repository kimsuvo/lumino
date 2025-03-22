import discord
from discord.ext import commands
import config
import sqlite3
import io
import logging
import chat_exporter
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

class DeveloperTicketCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="close")
    async def close_ticket(self, ctx: commands.Context):
        if not ctx.guild or not isinstance(ctx.channel, discord.TextChannel):
            await ctx.send("This command can only be used in a guild text channel.")
            return
        if config.DEVELOPER_ROLE_ID not in [role.id for role in ctx.author.roles]:
            await ctx.send("You are not authorized to use this command.")
            return
        if not ctx.channel.category:
            await ctx.send("This channel is not recognized as a ticket channel.")
            return
        if ctx.channel.category.id == config.DEV_SUPPORT_CATEGORY_ID:
            db_path = "dev_tickets.db"
            transcript_channel_id = config.DEV_SUPPORT_TRANSCRIPT_CHANNEL_ID
        elif ctx.channel.category.id == config.API_CATEGORY_ID:
            db_path = "api_tickets.db"
            transcript_channel_id = config.API_TRANSCRIPT_CHANNEL_ID
        else:
            await ctx.send("This channel is not recognized as a valid ticket channel.")
            return
        try:
            conn = sqlite3.connect("tickethold.db")
            c = conn.cursor()
            c.execute("SELECT channel_id FROM ticket_hold WHERE channel_id = ?", (ctx.channel.id,))
            if c.fetchone():
                await ctx.send("This ticket is currently on hold. Please unhold before closing.")
                conn.close()
                return
            conn.close()
        except Exception as e:
            logger.error(f"Error checking ticket hold status for channel {ctx.channel.id}: {e}")
            await ctx.send("Error checking ticket hold status.")
            return
        try:
            transcript = await chat_exporter.export(ctx.channel)
            transcript_file = discord.File(io.StringIO(transcript), filename=f"transcript-{ctx.channel.id}.html")
        except Exception as e:
            logger.error(f"Error generating transcript for channel {ctx.channel.id}: {e}")
            await ctx.send("Failed to generate transcript.")
            return
        try:
            messages = [msg async for msg in ctx.channel.history(limit=None)]
            user_message_counts = {}
            for msg in messages:
                user_message_counts[msg.author.id] = user_message_counts.get(msg.author.id, 0) + 1
            user_message_breakdown = "\n".join(f"<@{uid}> - {count} messages" for uid, count in user_message_counts.items())
        except Exception as e:
            logger.error(f"Error processing messages in channel {ctx.channel.id}: {e}")
            user_message_breakdown = "N/A"

        ticket_created_epoch = 0
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT created FROM tickets WHERE channel_id = ?", (ctx.channel.id,))
            result = c.fetchone()
            if result:
                ticket_created_str = result[0]
                ticket_created_dt = datetime.fromisoformat(ticket_created_str)
                ticket_created_epoch = int(ticket_created_dt.timestamp())
            conn.close()
        except Exception as e:
            logger.error(f"Error fetching ticket creation time for channel {ctx.channel.id}: {e}")

        ticket_closed_epoch = int(datetime.utcnow().timestamp())
        ticket_owner_id = None
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT user_id FROM tickets WHERE channel_id = ?", (ctx.channel.id,))
            result = c.fetchone()
            if result:
                ticket_owner_id = result[0]
            conn.close()
        except Exception as e:
            logger.error(f"Error fetching ticket owner for channel {ctx.channel.id}: {e}")

        if ticket_owner_id is None:
            await ctx.send("No ticket owner found. This ticket may have already been closed or not properly registered.")
            return

        ticket_owner_mention = f"<@{ticket_owner_id}>"
        ticket_name = ctx.channel.name
        ticket_category = ctx.channel.category.name if ctx.channel.category else "None"
        embed_transcript = discord.Embed(
            title="Ticket Transcript",
            description="Below are the details of the closed ticket:",
            color=config.EMBED_COLOR
        )
        embed_transcript.add_field(name="Ticket Name", value=ticket_name, inline=True)
        embed_transcript.add_field(name="Ticket Category", value=ticket_category, inline=True)
        embed_transcript.add_field(
            name="Users Involved",
            value=user_message_breakdown,
            inline=False
        )
        embed_transcript.add_field(name="Ticket Created at", value=f"<t:{ticket_created_epoch}:F>", inline=False)
        embed_transcript.add_field(name="Ticket Closed at", value=f"<t:{ticket_closed_epoch}:F>", inline=False)

        transcript_channel = ctx.guild.get_channel(transcript_channel_id)
        if transcript_channel:
            await transcript_channel.send(embed=embed_transcript, file=transcript_file)
        else:
            logger.error("Transcript channel not found in guild.")
            await ctx.send("Transcript channel not found.")
            return

        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("DELETE FROM tickets WHERE channel_id = ?", (ctx.channel.id,))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error deleting ticket data for channel {ctx.channel.id}: {e}")
            await ctx.send("Failed to remove ticket data from the database.")
            return

        await ctx.send("Ticket closed successfully.")
        await ctx.channel.delete()

async def setup(bot: commands.Bot):
    await bot.add_cog(DeveloperTicketCommands(bot))
