#!/usr/bin/env python3
"""
Ink2MD Configuration Manager
Based on PDF3MD by Murtaza Nsair
Original: https://github.com/murtaza-nasir/pdf3md

Copyright (C) 2025 Ink2MD Contributors
Copyright (C) 2024 Murtaza Nsair (original PDF3MD)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
import json
import os
import logging
from copy import deepcopy

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config', 'config.json')
USER_CONFIG_PATH = os.environ.get('PDF3MD_CONFIG_PATH', os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config')), 'config.json')) # User config in /config folder at project root

DEFAULT_CONFIG_STRUCTURE = {
  "app_settings": {
    "monitored_input_dir": "/app/input_pdfs",
    "processed_output_dir": "/app/output_markdown",
    "default_output_pattern": "YYYY-MM-DD-[OriginalFileName].md",
    "custom_output_pattern": None,
    "global_retry_attempts": 2,
    "enable_directory_monitoring": False
  },
  "active_services": {
    "htr_provider_id": "ollama_llava",
    "formatting_provider_id": "anthropic_claude_haiku"
  },
  "ai_provider_configs": {
    "ollama_llava": {
      "display_name": "Ollama (LLaVA for HTR)",
      "type": "ollama",
      "api_base_url": "http://10.0.0.97:11434",
      "model": "llava",
      "is_htr_capable": True,
      "is_formatting_capable": False,
      "enabled": True
    },
    "ollama_mistral": {
      "display_name": "Ollama (Mistral for Formatting)",
      "type": "ollama",
      "api_base_url": "http://10.0.0.97:11434",
      "model": "mistral",
      "is_htr_capable": False,
      "is_formatting_capable": True,
      "enabled": True
    },
    "anthropic_claude_haiku": {
      "display_name": "Anthropic (Claude 3 Haiku)",
      "type": "anthropic",
      "api_key": "${ANTHROPIC_API_KEY}",
      "model": "claude-3-haiku-20240307",
      "is_htr_capable": True,
      "is_formatting_capable": True,
      "is_vlm_capable": True,
      "enabled": True
    },
    "anthropic_claude_sonnet": {
      "display_name": "Anthropic (Claude 3.5 Sonnet)",
      "type": "anthropic",
      "api_key": "${ANTHROPIC_API_KEY}",
      "model": "claude-3-5-sonnet-20241022",
      "is_htr_capable": True,
      "is_formatting_capable": True,
      "is_vlm_capable": True,
      "enabled": True
    },
    "anthropic_claude_opus": {
      "display_name": "Anthropic (Claude 3 Opus)",
      "type": "anthropic",
      "api_key": "${ANTHROPIC_API_KEY}",
      "model": "claude-3-opus-20240229",
      "is_htr_capable": True,
      "is_formatting_capable": True,
      "is_vlm_capable": True,
      "enabled": True
    },
    "anthropic_claude_sonnet_new": {
      "display_name": "Anthropic (Claude 3.5 Sonnet New)",
      "type": "anthropic",
      "api_key": "${ANTHROPIC_API_KEY}",
      "model": "claude-3-5-sonnet-20241022",
      "is_htr_capable": True,
      "is_formatting_capable": True,
      "is_vlm_capable": True,
      "enabled": True
    }
  }
}

class ConfigManager:
    def __init__(self, config_path=None, db_manager=None):
        self.config_path = config_path or USER_CONFIG_PATH
        self.config = {}
        self.db_manager = db_manager
        self._load_config()

    def _ensure_config_dir_exists(self):
        """Ensures the directory for the user config file exists."""
        config_dir = os.path.dirname(self.config_path)
        if not os.path.exists(config_dir):
            try:
                os.makedirs(config_dir)
                logger.info(f"Created configuration directory: {config_dir}")
            except OSError as e:
                logger.error(f"Error creating configuration directory {config_dir}: {e}")
                raise

    def _create_default_config(self):
        """Creates a default config.json if it doesn't exist."""
        self._ensure_config_dir_exists()
        try:
            with open(self.config_path, 'w') as f:
                json.dump(DEFAULT_CONFIG_STRUCTURE, f, indent=2)
            logger.info(f"Created default configuration file at {self.config_path}")
            return DEFAULT_CONFIG_STRUCTURE
        except IOError as e:
            logger.error(f"Error creating default configuration file at {self.config_path}: {e}")
            raise

    def _substitute_env_variables(self, config_dict):
        """Recursively substitutes ${ENV_VAR} placeholders in the config."""
        if isinstance(config_dict, dict):
            return {k: self._substitute_env_variables(v) for k, v in config_dict.items()}
        elif isinstance(config_dict, list):
            return [self._substitute_env_variables(i) for i in config_dict]
        elif isinstance(config_dict, str):
            if config_dict.startswith("${") and config_dict.endswith("}"):
                env_var_name = config_dict[2:-1]
                return os.environ.get(env_var_name, config_dict) # Return original placeholder if env var not found
            return config_dict
        return config_dict

    def _load_config(self):
        """Loads configuration from config.json, creating it if it doesn't exist."""
        if not os.path.exists(self.config_path):
            logger.warning(f"Configuration file not found at {self.config_path}. Creating default config.")
            self.config = self._create_default_config()
        else:
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                # Ensure all default keys are present, merge if necessary
                self.config = self._merge_configs(deepcopy(DEFAULT_CONFIG_STRUCTURE), loaded_config)
                logger.info(f"Successfully loaded configuration from {self.config_path}")
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON from {self.config_path}: {e}. Using default configuration.")
                self.config = deepcopy(DEFAULT_CONFIG_STRUCTURE)
            except IOError as e:
                logger.error(f"Error reading configuration file {self.config_path}: {e}. Using default configuration.")
                self.config = deepcopy(DEFAULT_CONFIG_STRUCTURE)

        # Substitute environment variables
        self.config = self._substitute_env_variables(self.config)
        self._validate_config()


    def _merge_configs(self, default, user):
        """
        Recursively merges user config into default config.
        User's values take precedence. Adds missing keys from default.
        """
        if isinstance(default, dict) and isinstance(user, dict):
            merged = deepcopy(default)
            for key, value in user.items():
                if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                    merged[key] = self._merge_configs(merged[key], value)
                else:
                    merged[key] = deepcopy(value) # User's value overrides
            # Add keys from default that are not in user config at this level
            for key, value in default.items():
                if key not in merged:
                    merged[key] = deepcopy(value)
            return merged
        return deepcopy(user) # If not dicts, user value takes precedence or is the value


    def _validate_config(self):
        """Validates the loaded configuration."""
        # Basic validation, can be expanded
        if not isinstance(self.config.get("app_settings"), dict):
            logger.error("Invalid config: 'app_settings' must be a dictionary.")
            # Potentially raise an error or revert to a known good state
        if not isinstance(self.config.get("active_services"), dict):
            logger.error("Invalid config: 'active_services' must be a dictionary.")
        if not isinstance(self.config.get("ai_provider_configs"), dict):
            logger.error("Invalid config: 'ai_provider_configs' must be a dictionary.")
        
        # Validate that active services point to existing provider configs
        active_htr = self.get_setting('active_services.htr_provider_id')
        active_formatting = self.get_setting('active_services.formatting_provider_id')
        
        if active_htr and active_htr not in self.config.get("ai_provider_configs", {}):
            logger.warning(f"Active HTR provider '{active_htr}' not found in 'ai_provider_configs'.")
        if active_formatting and active_formatting not in self.config.get("ai_provider_configs", {}):
            logger.warning(f"Active formatting provider '{active_formatting}' not found in 'ai_provider_configs'.")

        logger.info("Configuration validation completed.")


    def get_setting(self, key_path, default=None):
        """
        Retrieves a setting using a dot-separated key path.
        Example: get_setting('app_settings.monitored_input_dir')
        """
        keys = key_path.split('.')
        value = self.config
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def update_setting(self, key_path, value):
        """
        Updates a setting using a dot-separated key path.
        Example: update_setting('app_settings.monitored_input_dir', '/new/path')
        Saves the configuration after updating.
        """
        keys = key_path.split('.')
        current_level = self.config
        for i, key in enumerate(keys[:-1]):
            if key not in current_level or not isinstance(current_level[key], dict):
                current_level[key] = {}  # Create intermediate dicts if they don't exist
            current_level = current_level[key]
        
        current_level[keys[-1]] = value
        self.save_config()
        
        # Also save to database if db_manager is available
        if self.db_manager and key_path.startswith('ai_provider_configs.'):
            try:
                from models import UserSetting
                user_setting = UserSetting(setting_key=key_path)
                user_setting.set_value(value)
                self.db_manager.update_user_setting(
                    key_path,
                    user_setting.setting_value,
                    user_setting.setting_type
                )
                logger.info(f"Synced setting '{key_path}' to database.")
            except Exception as e:
                logger.warning(f"Failed to sync setting '{key_path}' to database: {e}")
        
        logger.info(f"Updated setting '{key_path}' to '{value}' and saved configuration.")
        return True

    def save_config(self):
        """Saves the current configuration to config.json."""
        self._ensure_config_dir_exists()
        try:
            # Before saving, revert environment variable placeholders if they were substituted from actual env values
            # This is to avoid writing sensitive data (like API keys from env) directly into the config file.
            # We only want to save the ${ENV_VAR} placeholders.
            config_to_save = self._revert_env_placeholders(deepcopy(self.config), deepcopy(DEFAULT_CONFIG_STRUCTURE))

            with open(self.config_path, 'w') as f:
                json.dump(config_to_save, f, indent=2)
            logger.info(f"Configuration saved to {self.config_path}")
        except IOError as e:
            logger.error(f"Error saving configuration to {self.config_path}: {e}")
            raise

    def _revert_env_placeholders(self, current_config, default_template):
        """
        Recursively reverts substituted environment variables to their placeholder form
        if the current value matches an environment variable and the default template
        had a placeholder for it.
        """
        if isinstance(current_config, dict) and isinstance(default_template, dict):
            reverted_dict = {}
            for key, current_value in current_config.items():
                default_value = default_template.get(key)
                reverted_dict[key] = self._revert_env_placeholders(current_value, default_value)
            return reverted_dict
        elif isinstance(current_config, list) and isinstance(default_template, list):
            # Assuming lists have corresponding elements for simplicity, or handle more complex list diffing
            reverted_list = []
            for i, current_item in enumerate(current_config):
                default_item = default_template[i] if i < len(default_template) else None
                reverted_list.append(self._revert_env_placeholders(current_item, default_item))
            return reverted_list
        elif isinstance(current_config, str) and isinstance(default_template, str):
            if default_template.startswith("${") and default_template.endswith("}"):
                env_var_name = default_template[2:-1]
                env_var_value = os.environ.get(env_var_name)
                if env_var_value == current_config: # If current value is the one from env
                    return default_template # Revert to placeholder
            return current_config
        return current_config

    def get_all_config(self):
        """Returns the entire current configuration."""
        return deepcopy(self.config)

    def load_user_settings_from_db(self):
        """Load user settings from database and merge with config."""
        if not self.db_manager:
            return
        
        try:
            user_settings = self.db_manager.get_all_user_settings()
            
            for setting in user_settings:
                setting_key = setting['setting_key']
                if setting_key.startswith('ai_provider_configs.'):
                    from models import UserSetting
                    user_setting = UserSetting.from_dict(setting)
                    value = user_setting.get_parsed_value()
                    
                    # Update config with database value
                    keys = setting_key.split('.')
                    current_level = self.config
                    for i, key in enumerate(keys[:-1]):
                        if key not in current_level or not isinstance(current_level[key], dict):
                            current_level[key] = {}
                        current_level = current_level[key]
                    
                    current_level[keys[-1]] = value
                    
            logger.info(f"Loaded {len(user_settings)} user settings from database.")
            
        except Exception as e:
            logger.warning(f"Failed to load user settings from database: {e}")

    def sync_config_to_db(self):
        """Sync current AI provider config to database."""
        if not self.db_manager:
            return
        
        try:
            ai_configs = self.config.get('ai_provider_configs', {})
            synced_count = 0
            
            for provider_id, provider_config in ai_configs.items():
                for config_key, config_value in provider_config.items():
                    setting_key = f"ai_provider_configs.{provider_id}.{config_key}"
                    
                    from models import UserSetting
                    user_setting = UserSetting(setting_key=setting_key)
                    user_setting.set_value(config_value)
                    
                    try:
                        self.db_manager.update_user_setting(
                            setting_key,
                            user_setting.setting_value,
                            user_setting.setting_type
                        )
                        synced_count += 1
                    except Exception as sync_error:
                        logger.warning(f"Failed to sync config setting {setting_key}: {sync_error}")
            
            logger.info(f"Synced {synced_count} config settings to database.")
            return synced_count
            
        except Exception as e:
            logger.error(f"Failed to sync config to database: {e}")
            return 0

# Example usage (optional, for testing)
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Test with a custom path for the user config to avoid overwriting default during test
    test_config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'test_config'))
    if not os.path.exists(test_config_dir):
        os.makedirs(test_config_dir)
    test_user_config_path = os.path.join(test_config_dir, 'test_config.json')

    # Clean up previous test file if it exists
    if os.path.exists(test_user_config_path):
        os.remove(test_user_config_path)

    # Set a test environment variable
    os.environ['ANTHROPIC_API_KEY'] = 'test_api_key_from_env'

    manager = ConfigManager(config_path=test_user_config_path)
    
    print("\nInitial loaded config:")
    print(json.dumps(manager.get_all_config(), indent=2))

    print(f"\nMonitored input dir: {manager.get_setting('app_settings.monitored_input_dir')}")
    print(f"Anthropic API Key: {manager.get_setting('ai_provider_configs.anthropic_claude_haiku.api_key')}")
    
    manager.update_setting('app_settings.monitored_input_dir', '/new/test/path')
    print(f"\nUpdated monitored input dir: {manager.get_setting('app_settings.monitored_input_dir')}")

    manager.update_setting('ai_provider_configs.anthropic_claude_haiku.model', 'claude-3-opus-20240229')
    print(f"\nUpdated Anthropic model: {manager.get_setting('ai_provider_configs.anthropic_claude_haiku.model')}")

    print("\nConfig after updates (before explicit save, but update_setting saves):")
    print(json.dumps(manager.get_all_config(), indent=2))

    # Test saving explicitly (though update_setting already saves)
    manager.save_config()
    print(f"\nConfig saved to {test_user_config_path}. Check its content.")

    # Test loading again to ensure persistence and env var substitution on load
    print("\nLoading config again...")
    manager_reloaded = ConfigManager(config_path=test_user_config_path)
    print("\nReloaded config:")
    print(json.dumps(manager_reloaded.get_all_config(), indent=2))
    print(f"Anthropic API Key (reloaded): {manager_reloaded.get_setting('ai_provider_configs.anthropic_claude_haiku.api_key')}")

    # Clean up test file
    if os.path.exists(test_user_config_path):
        os.remove(test_user_config_path)
    if os.path.exists(test_config_dir):
        os.rmdir(test_config_dir)
    del os.environ['ANTHROPIC_API_KEY']
    print("\nTest cleanup complete.")