import discord
from discord.ext import commands
import config
import sqlite3
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)

class TicketPanelView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.select(
        custom_id="ticket_panel_select",
        placeholder="Choose ticket type...",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="Request API", value="api", description="Open an API ticket."),
            discord.SelectOption(label="Request Developer Support", value="dev", description="Open a Developer Support ticket.")
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.send_message("Creating ticket...", ephemeral=True)
        
        ticket_type = select.values[0]
        if ticket_type == "api":
            category_id = config.API_CATEGORY_ID
            db_file = "api_tickets.db"
        elif ticket_type == "dev":
            category_id = config.DEV_SUPPORT_CATEGORY_ID
            db_file = "dev_tickets.db"
        else:
            await interaction.edit_original_response(content="Invalid selection.")
            return
        try:
            conn = sqlite3.connect(db_file)
            c = conn.cursor()
            c.execute("SELECT channel_id FROM tickets WHERE user_id = ?", (interaction.user.id,))
            rows = c.fetchall()
            conn.close()
            for (channel_id,) in rows:
                if interaction.guild.get_channel(channel_id) is not None:
                    await interaction.edit_original_response(
                        content="You already have an open ticket for this type. Please close it before opening a new one."
                    )
                    return
        except Exception as e:
            logger.error(f"Error checking tickets in {db_file}: {e}")

        category = interaction.guild.get_channel(category_id)
        if category is None:
            await interaction.edit_original_response(content="Ticket category not found.")
            return

        base_channel_name = re.sub(r'[^a-z0-9-]', '', interaction.user.display_name.lower().replace(" ", "-"))
        if not base_channel_name:
            base_channel_name = f"ticket-{interaction.user.id}"
        channel_name = base_channel_name

        ticket_user_overwrites = discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            attach_files=True
        )
        default_overwrites = discord.PermissionOverwrite(view_channel=False)
        developer_role = interaction.guild.get_role(config.DEVELOPER_ROLE_ID)
        if not developer_role:
            await interaction.edit_original_response(content="Developer role not found.")
            return
        developer_overwrites = discord.PermissionOverwrite(**{perm: True for perm in discord.Permissions.VALID_FLAGS})

        overwrites = {
            interaction.guild.default_role: default_overwrites,
            interaction.user: ticket_user_overwrites,
            developer_role: developer_overwrites
        }

        try:
            channel = await interaction.guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites
            )
        except Exception as e:
            logger.error(f"Error creating channel: {e}")
            await interaction.edit_original_response(content=f"Failed to create channel: {e}")
            return

        try:
            conn = sqlite3.connect(db_file)
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    user_id INTEGER,
                    channel_id INTEGER,
                    created TEXT
                )
            """)
            c.execute("INSERT INTO tickets (user_id, channel_id, created) VALUES (?, ?, ?)",
                      (interaction.user.id, channel.id, datetime.utcnow().isoformat()))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error logging ticket: {e}")
            await interaction.edit_original_response(content=f"Failed to log ticket: {e}")
            return

        await interaction.edit_original_response(content=f"Ticket created: {channel.mention}")

class TicketPanels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ticket_panel_view = TicketPanelView(self.bot)
        self.bot.add_view(self.ticket_panel_view)

    @commands.command()
    async def ticketpanel(self, ctx):
        """Sends a ticket panel with a dropdown to create tickets."""
        embed = discord.Embed(
            title="Request Support",
            description=(
                "Select the type of ticket you would like to open. "
                "Once selected, a private support channel will be created for you. "
                "Please ensure you have reviewed <#1345267437599326268> before creating a ticket. \n\n"
                "**<:lumen_transcript:1345750636746117210> API Request**: Use this option for API-related issues.\n"
                "**<:lumen_transcript:1345750636746117210> Developer Support**: Use this option for issues related to development support."
            ),
            color=config.EMBED_COLOR,
        )
        embed.set_footer(text="If you need further assistance, please contact a moderator.")
        
        await ctx.send(embed=embed, view=self.ticket_panel_view)

async def setup(bot):
    await bot.add_cog(TicketPanels(bot))
