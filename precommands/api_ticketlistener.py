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
class TicketListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        if channel.category and channel.category.id == config.API_CATEGORY_ID:
            ticket_owner_id = None
            timeout = 5.0
            interval = 0.5
            elapsed = 0.0
            while elapsed < timeout:
                try:
                    conn = sqlite3.connect("api_tickets.db")
                    c = conn.cursor()
                    c.execute("SELECT user_id FROM tickets WHERE channel_id = ?", (channel.id,))
                    result = c.fetchone()
                    conn.close()
                    if result:
                        ticket_owner_id = result[0]
                        break
                except Exception as e:
                    logger.error(f"Error fetching ticket owner for channel {channel.id}: {e}")
                await asyncio.sleep(interval)
                elapsed += interval
            
            if ticket_owner_id is None:
                logger.error(f"No ticket owner found for channel {channel.id} after waiting {timeout} seconds.")
                return            
            developer_role_mention = f"<@&{config.DEVELOPER_ROLE_ID}>"
            ticket_owner_mention = f"<@{ticket_owner_id}>"

            await channel.send(ticket_owner_mention)
            embed = discord.Embed(
                title="Ticket Management",
                description=(
                    f"Welcome {ticket_owner_mention}, {developer_role_mention} will be here shortly to help you.\n"
                    "In the meantime, kindly describe your issue using the button below."
                ),
                color=config.EMBED_COLOR

            )
            view = TicketActionView(channel)
            message = await channel.send(embed=embed, view=view)
            view.message = message

class TicketActionView(discord.ui.View):
    def __init__(self, channel: discord.TextChannel):
        super().__init__(timeout=None)
        self.channel = channel
        self.message: discord.Message = None
        self.ticket_owner_id = None
        try:
            conn = sqlite3.connect("api_tickets.db")
            c = conn.cursor()
            c.execute("SELECT user_id FROM tickets WHERE channel_id = ?", (channel.id,))
            result = c.fetchone()
            if result:
                self.ticket_owner_id = result[0]
            conn.close()
        except Exception as e:
            logger.error(f"Error fetching ticket owner for channel {channel.id}: {e}")

    @discord.ui.button(label="Describe your Issue", style=discord.ButtonStyle.primary)
    async def describe_issue(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ticket_owner_id:
            await interaction.response.send_message("You are not authorized to interact with this ticket.", ephemeral=True)
            return
        modal = IssueModal(self.message, self.ticket_owner_id)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ticket_owner_id:
            await interaction.response.send_message("You are not authorized to close this ticket.", ephemeral=True)
            return

        try:
            conn = sqlite3.connect("tickethold.db")
            c = conn.cursor()
            c.execute("SELECT channel_id FROM ticket_hold WHERE channel_id = ?", (interaction.channel.id,))
            if c.fetchone():
                await interaction.response.send_message("This ticket is currently on hold. Please unhold before closing.", ephemeral=True)
                conn.close()
                return
            conn.close()
        except Exception as e:
            await interaction.response.send_message("Error checking ticket hold status.", ephemeral=True)
            return
        try:
            transcript = await chat_exporter.export(interaction.channel)
            transcript_file = discord.File(io.StringIO(transcript), filename=f"transcript-{interaction.channel.id}.html")
        except Exception as e:
            logger.error(f"Error generating transcript: {e}")
            await interaction.response.send_message("Failed to generate transcript.", ephemeral=True)
            return
        try:
            messages = [msg async for msg in interaction.channel.history(limit=None)]
            message_count = len(messages)
        except Exception as e:
            logger.error(f"Error counting messages in channel {interaction.channel.id}: {e}")
            message_count = "N/A"

        ticket_created_epoch = 0
        try:
            conn = sqlite3.connect("api_tickets.db")
            c = conn.cursor()
            c.execute("SELECT created FROM tickets WHERE channel_id = ?", (interaction.channel.id,))
            result = c.fetchone()
            if result:
                ticket_created_str = result[0]
                ticket_created_dt = datetime.fromisoformat(ticket_created_str)
                ticket_created_epoch = int(ticket_created_dt.timestamp())
        except Exception as e:
            logger.error(f"Error fetching ticket creation time for channel {interaction.channel.id}: {e}")
        finally:
            conn.close()

        ticket_closed_epoch = int(datetime.utcnow().timestamp())
        ticket_name = interaction.channel.name
        ticket_category = interaction.channel.category.name if interaction.channel.category else "None"
        ticket_owner_mention = f"<@{self.ticket_owner_id}>"
        embed_transcript = discord.Embed(
            title="Ticket Transcript",
            description="Below are the details of the closed ticket:",
            color=config.EMBED_COLOR
        )
        embed_transcript.add_field(name="Ticket Name", value=ticket_name, inline=True)
        embed_transcript.add_field(name="Ticket Category", value=ticket_category, inline=True)
        embed_transcript.add_field(name="User Involved", value=f"{ticket_owner_mention} - {message_count} messages", inline=False)
        embed_transcript.add_field(name="Ticket Created at", value=f"<t:{ticket_created_epoch}:F>", inline=False)
        embed_transcript.add_field(name="Ticket Closed at", value=f"<t:{ticket_closed_epoch}:F>", inline=False)

        transcript_channel = interaction.guild.get_channel(config.API_TRANSCRIPT_CHANNEL_ID)
        if transcript_channel:
            await transcript_channel.send(embed=embed_transcript, file=transcript_file)
        else:
            logger.error("Transcript channel not found in guild.")
            await interaction.response.send_message("Transcript channel not found.", ephemeral=True)
            return

        try:
            conn = sqlite3.connect("api_tickets.db")
            c = conn.cursor()
            c.execute("DELETE FROM tickets WHERE channel_id = ?", (interaction.channel.id,))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error deleting ticket data for channel {interaction.channel.id}: {e}")
            await interaction.response.send_message("Failed to remove ticket data from the database.", ephemeral=True)
            return

        await interaction.response.send_message("Ticket closed successfully. ", ephemeral=True)
        await interaction.channel.delete()


class IssueModal(discord.ui.Modal, title="Describe Your Issue"):
    def __init__(self, original_message: discord.Message, ticket_owner_id: int):
        super().__init__()
        self.original_message = original_message
        self.ticket_owner_id = ticket_owner_id
        self.issue_input = discord.ui.TextInput(
            label="Describe your issue",
            style=discord.TextStyle.paragraph,
            placeholder="Enter the details of your issue..."
        )
        self.add_item(self.issue_input)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.ticket_owner_id:
            await interaction.response.send_message("You are not authorized to submit this ticket.", ephemeral=True)
            return
        embed = self.original_message.embeds[0]
        embed.add_field(name="Issue", value=self.issue_input.value, inline=False)
        await self.original_message.edit(embed=embed)
        await interaction.response.send_message("Your issue has been recorded.", ephemeral=True)
        await self.original_message.channel.send(f"<@&{config.DEVELOPER_ROLE_ID}>")

async def setup(bot: commands.Bot):
    await bot.add_cog(TicketListener(bot))
