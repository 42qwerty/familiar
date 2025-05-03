# File: command_dispatcher.py (Working + Debug + add_alias)
# -*- coding: utf-8 -*-

import utils
# Import handlers from the intent_handlers directory
from intent_handlers import handle_manage_app
from intent_handlers import handle_add_alias # <-- ADDED: Import the new handler
# TODO: Import handlers for other intents when ready

# Global variable for aliases (loaded on initialization)
APP_ALIASES = {}

# Routing dictionary: maps intent strings to handler functions
INTENT_HANDLERS = {
    "manage_app": handle_manage_app.handle,
    "add_alias": handle_add_alias.handle, # <-- ADDED: Route 'add_alias' intent
    # TODO: Add other intents and their handlers
    # "manage_system": handle_manage_system.handle,
    # ... etc.
}

def initialize_dispatcher():
    """Loads aliases at startup."""
    global APP_ALIASES
    APP_ALIASES = utils.load_aliases()
    if APP_ALIASES:
        print(f"[DISPATCHER][INFO] Aliases loaded successfully ({len(APP_ALIASES)} found).")
    else:
        print("[DISPATCHER][WARN] Aliases not loaded or file is empty.")

def dispatch_command(parsed_nlu, debug_mode=False):
    """
    Routes the command to the appropriate handler OR prints NLU results in debug mode.

    Args:
        parsed_nlu (dict): The parsed NLU output (intent and parameters).
        debug_mode (bool): Flag to enable debug output instead of execution.

    Returns:
        str: The result message from the handler or a debug/error message.
    """
    if not parsed_nlu or "intent" not in parsed_nlu:
        log_prefix = "[DISPATCHER_DEBUG]" if debug_mode else "[DISPATCHER][ERROR]"
        print(f"{log_prefix} Received invalid NLU data.")
        return "Не удалось распознать команду." # Failed to recognize command.

    intent = parsed_nlu.get("intent")
    parameters = parsed_nlu.get("parameters", {})
    log_source = "[DISPATCHER_DEBUG]" if debug_mode else "[DISPATCHER][INFO]"
    print(f"{log_source} Received intent: '{intent}', parameters: {parameters}")

    # --- DEBUG MODE ---
    if debug_mode:
        print("="*20 + " DEBUG MODE " + "="*20)
        print(f"[DISPATCHER_DEBUG] Recognized Intent: {intent}")
        print(f"[DISPATCHER_DEBUG] Recognized Parameters: {parameters}")
        # Show normalization for relevant intents for reference
        if intent == "manage_app" and "app_name" in parameters:
             app_name_raw = parameters.get("app_name")
             canonical_name = APP_ALIASES.get(app_name_raw.lower(), app_name_raw.lower())
             print(f"[DISPATCHER_DEBUG] Normalized app_name (for reference): '{canonical_name}'")
        elif intent == "add_alias":
             alias_name = parameters.get("alias_name")
             app_name = parameters.get("app_name")
             if alias_name:
                 print(f"[DISPATCHER_DEBUG] Alias name (for reference): '{alias_name.lower()}'")
             if app_name:
                 print(f"[DISPATCHER_DEBUG] Target app name (for reference): '{app_name.lower()}'")
        print("="*52)
        return f"ДЕБАГ: Распознано: интент='{intent}', параметры={parameters}" # DEBUG: Recognized: ...
    # --- END DEBUG MODE ---

    # --- NORMAL EXECUTION MODE ---
    else:
        print(f"[DISPATCHER][INFO] Routing intent: '{intent}'")
        handler_function = INTENT_HANDLERS.get(intent)

        if handler_function:
            try:
                # Call the found handler, passing parameters and the current aliases
                # The handler itself will parse the specific parameters it needs (like 'action')
                # We pass the whole aliases dict so handlers can potentially modify it (like add_alias)
                # Note: handle_add_alias now calls save_aliases itself.
                return handler_function(parameters, APP_ALIASES)

            except Exception as e:
                print(f"[DISPATCHER][ERROR] Error executing handler for intent '{intent}': {e}")
                import traceback
                traceback.print_exc() # Print full traceback for debugging
                return f"Произошла ошибка при выполнении команды '{intent}'." # An error occurred while executing the command
        else:
            # Handler not found
            print(f"[DISPATCHER][WARN] Handler for intent '{intent}' not found.")
            # TODO: Optionally handle 'unknown' intent here
            return "Извините, я пока не умею обрабатывать такую команду." # Sorry, I don't know how to handle this command yet.

# --- Initialize dispatcher when the module is imported ---
initialize_dispatcher()
