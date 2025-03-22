import discord
from discord.ext import commands
import config
from datetime import datetime, timedelta, timezone

class PurgeCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.has_role(config.MODERATOR_ROLE_ID)
    @commands.command(name="purge")
    async def purge_command(self, ctx, amount: int, user: discord.Member = None):
        await ctx.message.delete()

        if amount < 1:
            embed = discord.Embed(
                title="Error",
                description="Please specify a number greater than 0.",
                color=config.EMBED_COLOR
            )
            return await ctx.send(embed=embed, delete_after=5)
        
        if amount > 100:
            amount = 100

        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        messages_to_delete = []

        try:
            async for message in ctx.channel.history(limit=100):
                if message.id == ctx.message.id:
                    continue
                if message.created_at < cutoff:
                    continue
                if user and message.author.id != user.id:
                    continue
                messages_to_delete.append(message)
                if len(messages_to_delete) >= amount:
                    break

            if not messages_to_delete:
                embed = discord.Embed(
                    title="Purge Result",
                    description="No messages found that match the criteria.",
                    color=config.EMBED_COLOR
                )
                return await ctx.send(embed=embed, delete_after=5)

            await ctx.channel.delete_messages(messages_to_delete)
            embed = discord.Embed(
                title="Purge Successful",
                description=f"Successfully purged {len(messages_to_delete)} message(s).",
                color=config.EMBED_COLOR
            )
            await ctx.send(embed=embed, delete_after=5)
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"An error occurred: {str(e)}",
                color=config.EMBED_COLOR
            )
            await ctx.send(embed=embed, delete_after=5)

    @purge_command.error
    async def purge_command_error(self, ctx, error):
        try:
            await ctx.message.delete()
        except Exception:
            pass

        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="Error",
                description="Missing arguments. Usage: `!purge [number of messages] <user>`",
                color=config.EMBED_COLOR
            )
            await ctx.send(embed=embed, delete_after=5)
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="Error",
                description="Invalid argument type. Make sure to specify a number for the message count and a valid user if provided.",
                color=config.EMBED_COLOR
            )
            await ctx.send(embed=embed, delete_after=5)
        elif isinstance(error, commands.CheckFailure):
            embed = discord.Embed(
                title="Error",
                description="You do not have permission to use this command.",
                color=config.EMBED_COLOR
            )
            await ctx.send(embed=embed, delete_after=5)
        else:
            embed = discord.Embed(
                title="Error",
                description=f"An unexpected error occurred: {str(error)}",
                color=config.EMBED_COLOR
            )
            await ctx.send(embed=embed, delete_after=5)

async def setup(bot):
    await bot.add_cog(PurgeCommand(bot))
