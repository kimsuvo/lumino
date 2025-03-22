import discord
from discord.ext import commands
import logging
import config

logger = logging.getLogger(__name__)

class ClearDMView(discord.ui.View):
    def __init__(self, user: discord.User):
        super().__init__(timeout=60)
        self.user = user

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger)
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "You are not authorized to perform this action.", ephemeral=True
            )
            return

        dm_channel = await self.user.create_dm()
        deleted_count = 0
        try:
            async for message in dm_channel.history(limit=None):
                if message.author.id == interaction.client.user.id:
                    try:
                        await message.delete()
                        deleted_count += 1
                    except Exception as e:
                        logger.error(f"Error deleting message {message.id} in DM: {e}")
            success_embed = discord.Embed(
                title="Clear DM",
                description=f"Successfully deleted {deleted_count} message(s) from your DMs.",
                color=config.EMBED_COLOR
            )
            await interaction.response.edit_message(embed=success_embed, view=None)
        except Exception as e:
            logger.error(f"Error during DM deletion: {e}")
            error_embed = discord.Embed(
                title="Clear DM",
                description="An error occurred while deleting messages.",
                color=config.EMBED_COLOR
            )
            await interaction.response.edit_message(embed=error_embed, view=None)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "You are not authorized to perform this action.", ephemeral=True
            )
            return

        cancel_embed = discord.Embed(
            title="Clear DM",
            description="Operation cancelled.",
            color=config.EMBED_COLOR
        )
        await interaction.response.edit_message(embed=cancel_embed, view=None)

class ClearDM(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="cleardm")
    async def cleardm(self, ctx: commands.Context):
        """
        Sends a confirmation embed with buttons to delete all messages the bot sent in your DMs.
        """
        embed = discord.Embed(
            title="Clear DM Confirmation",
            description="Do you really want to delete all messages I sent to you in your DMs?",
            color=config.EMBED_COLOR
        )
        view = ClearDMView(ctx.author)
        await ctx.send(embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(ClearDM(bot))
