import discord
from discord.ext import commands
import config

class TicketRemove(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="remove")
    async def remove_user(self, ctx, member: discord.Member):
        """
        Removes a user's permission overwrites in the ticket channel,
        effectively removing them from the ticket.
        This command only works if executed in a channel whose category ID
        is in config.TICKET_CATEGORY_IDS.
        """
        if not ctx.channel.category or ctx.channel.category.id not in config.TICKET_CATEGORY_IDS:
            return  
        try:
            await ctx.channel.set_permissions(member, overwrite=None)
            embed = discord.Embed(
                title="User Removed",
                description=f"{member.mention} has been removed from this ticket.",
                color=config.EMBED_COLOR
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"Failed to remove {member.mention}: {e}",
                color=config.EMBED_COLOR
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(TicketRemove(bot))
