import discord
from discord.ext import commands
import config

class StarboardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="sb")
    @commands.has_any_role(*config.STARBOARD_PERMISSIONS)
    async def starboard(self, ctx):
        await ctx.message.delete()
        
        if not ctx.message.reference:
            error_embed = discord.Embed(
                title="Error",
                description="You must reply to a message to starboard it.",
                color=config.EMBED_COLOR
            )
            await ctx.send(embed=error_embed, delete_after=5)
            return
        try:
            ref_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        except Exception:
            error_embed = discord.Embed(
                title="Error",
                description="Could not fetch the referenced message.",
                color=config.EMBED_COLOR
            )
            await ctx.send(embed=error_embed, delete_after=5)
            return

        embed = discord.Embed(color=config.EMBED_COLOR)
        embed.set_author(name=ref_message.author.display_name, icon_url=ref_message.author.display_avatar.url)
        embed.add_field(name="Message:", value=ref_message.content or "No content", inline=False)

        if ref_message.reference and ref_message.reference.message_id:
            try:
                replied_message = await ctx.channel.fetch_message(ref_message.reference.message_id)
                replied_link = (
                    f"https://discord.com/channels/{replied_message.guild.id}/"
                    f"{replied_message.channel.id}/{replied_message.id}"
                ) if replied_message.guild else "Unknown"
                embed.add_field(
                    name="Replying to:",
                    value=f"[{replied_message.author.display_name}]({replied_link})",
                    inline=False
                )
            except Exception:
                pass

        original_link = (
            f"https://discord.com/channels/{ref_message.guild.id}/"
            f"{ref_message.channel.id}/{ref_message.id}"
        ) if ref_message.guild else "Unknown"
        embed.add_field(
            name="Original:",
            value=f"[Jump]({original_link})",
            inline=False
        )

        starboard_channel = self.bot.get_channel(config.STARBOARD_CHANNEL_ID)
        if starboard_channel is None:
            error_embed = discord.Embed(
                title="Error",
                description="Starboard channel not found.",
                color=config.EMBED_COLOR
            )
            await ctx.send(embed=error_embed, delete_after=5)
            return

        starboard_msg = await starboard_channel.send(embed=embed)
        await starboard_msg.add_reaction("<:lumen_upvote:1345656649616195594>")

async def setup(bot):
    await bot.add_cog(StarboardCog(bot))
