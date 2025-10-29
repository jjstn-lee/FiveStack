bot_instance = None

def get_bot():
    """Get the global bot instance"""
    if bot_instance is None:
        raise RuntimeError("Bot instance not initialized! Call set_bot() first.")
    return bot_instance

def set_bot(instance):
    """Set the global bot instance"""
    global bot_instance
    bot_instance = instance