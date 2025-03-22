import discord
from discord.ext import commands
import config

class TicketAdd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="add")
    async def add_user(self, ctx, member: discord.Member):
        """
        Adds a user to the ticket channel with permissions:
        view_channel, send_messages, and attach_files.
        This command only works if executed in a channel whose category ID
        is in config.TICKET_CATEGORY_IDS.
        """
        if not ctx.channel.category or ctx.channel.category.id not in config.TICKET_CATEGORY_IDS:
            return
        try:
            await ctx.channel.set_permissions(
                member,
                view_channel=True,
                send_messages=True,
                attach_files=True
            )
            embed = discord.Embed(
                title="User Added",
                description=f"{member.mention} has been added to this ticket.",
                color=config.EMBED_COLOR
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"Failed to add {member.mention}: {e}",
                color=config.EMBED_COLOR
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(TicketAdd(bot))