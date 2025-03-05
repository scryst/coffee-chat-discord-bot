import discord
from discord.ext import commands
from discord import app_commands
import logging
import traceback
import sys

logger = logging.getLogger('coffee_bot.error_handler')

class ErrorHandler(commands.Cog):
    """Cog for handling errors in the bot."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Handle command errors."""
        if isinstance(error, commands.CommandNotFound):
            return
        
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument: {error.param}")
            return
        
        if isinstance(error, commands.BadArgument):
            await ctx.send(f"Bad argument: {error}")
            return
        
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f"You don't have the required permissions: {', '.join(error.missing_permissions)}")
            return
        
        if isinstance(error, commands.BotMissingPermissions):
            await ctx.send(f"I don't have the required permissions: {', '.join(error.missing_permissions)}")
            return
        
        # Log the error
        logger.error(f"Ignoring exception in command {ctx.command}:")
        logger.error(''.join(traceback.format_exception(type(error), error, error.__traceback__)))
        
        # Send error message to user
        await ctx.send("An error occurred while executing the command. Please try again later.")
    
    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        """Handle general errors."""
        logger.error(f"Ignoring exception in event {event}:")
        logger.error(traceback.format_exc())
    
    @commands.Cog.listener()
    async def on_application_command_error(self, interaction: discord.Interaction, error):
        """Handle application command errors."""
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"This command is on cooldown. Try again in {error.retry_after:.2f} seconds.",
                ephemeral=True
            )
            return
        
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                f"You don't have the required permissions: {', '.join(error.missing_permissions)}",
                ephemeral=True
            )
            return
        
        if isinstance(error, app_commands.BotMissingPermissions):
            await interaction.response.send_message(
                f"I don't have the required permissions: {', '.join(error.missing_permissions)}",
                ephemeral=True
            )
            return
        
        # Log the error
        logger.error(f"Ignoring exception in application command {interaction.command}:")
        logger.error(''.join(traceback.format_exception(type(error), error, error.__traceback__)))
        
        # Send error message to user
        try:
            if interaction.response.is_done():
                await interaction.followup.send(
                    "An error occurred while executing the command. Please try again later.",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "An error occurred while executing the command. Please try again later.",
                    ephemeral=True
                )
        except discord.errors.InteractionResponded:
            await interaction.followup.send(
                "An error occurred while executing the command. Please try again later.",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")

async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))
