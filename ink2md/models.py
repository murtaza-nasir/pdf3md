#!/usr/bin/env python3
"""
Ink2MD Data Models
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
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
import json

class ConversionStatus(Enum):
    """Enumeration of possible conversion statuses."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

@dataclass
class ConversionRecord:
    """Data model for a conversion record."""
    id: Optional[int] = None
    conversion_id: str = ""
    original_filename: str = ""
    output_filename: Optional[str] = None
    conversion_timestamp: Optional[datetime] = None
    status: ConversionStatus = ConversionStatus.QUEUED
    htr_provider: Optional[str] = None
    formatting_provider: Optional[str] = None
    error_message: Optional[str] = None
    raw_htr_output_path: Optional[str] = None
    final_markdown_path: Optional[str] = None
    retry_count: int = 0
    file_size: Optional[int] = None
    page_count: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the record to a dictionary for JSON serialization."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat() if value else None
            elif isinstance(value, ConversionStatus):
                result[key] = value.value
            else:
                result[key] = value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversionRecord':
        """Create a ConversionRecord from a dictionary."""
        # Handle datetime fields
        for date_field in ['conversion_timestamp', 'created_at', 'updated_at']:
            if data.get(date_field) and isinstance(data[date_field], str):
                try:
                    data[date_field] = datetime.fromisoformat(data[date_field])
                except ValueError:
                    data[date_field] = None

        # Handle status enum
        if 'status' in data and isinstance(data['status'], str):
            try:
                data['status'] = ConversionStatus(data['status'])
            except ValueError:
                data['status'] = ConversionStatus.QUEUED

        return cls(**data)

    def is_retryable(self, max_retries: int = 3) -> bool:
        """Check if this conversion can be retried."""
        return (self.status == ConversionStatus.FAILED and 
                self.retry_count < max_retries)

    def get_display_status(self) -> str:
        """Get a human-readable status string."""
        status_map = {
            ConversionStatus.QUEUED: "Queued",
            ConversionStatus.PROCESSING: "Processing",
            ConversionStatus.COMPLETED: "Completed",
            ConversionStatus.FAILED: "Failed",
            ConversionStatus.RETRYING: "Retrying"
        }
        return status_map.get(self.status, "Unknown")

    def get_file_size_formatted(self) -> str:
        """Get formatted file size string."""
        if not self.file_size:
            return "Unknown"
        
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"

@dataclass
class ConversionProgress:
    """Data model for tracking conversion progress."""
    conversion_id: str
    progress: int = 0  # 0-100
    stage: str = "Initializing"
    current_page: int = 0
    total_pages: int = 0
    filename: str = ""
    file_size: Optional[int] = None
    status: ConversionStatus = ConversionStatus.QUEUED
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, ConversionStatus):
                result[key] = value.value
            else:
                result[key] = value
        return result

@dataclass
class AIProviderConfig:
    """Data model for AI provider configuration."""
    provider_id: str
    display_name: str
    type: str  # "ollama", "anthropic", "openai", etc.
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    model: Optional[str] = None
    is_htr_capable: bool = False
    is_formatting_capable: bool = False
    enabled: bool = True
    additional_config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "provider_id": self.provider_id,
            "display_name": self.display_name,
            "type": self.type,
            "api_key": self.api_key,
            "api_base_url": self.api_base_url,
            "model": self.model,
            "is_htr_capable": self.is_htr_capable,
            "is_formatting_capable": self.is_formatting_capable,
            "enabled": self.enabled,
            **self.additional_config
        }

    @classmethod
    def from_dict(cls, provider_id: str, data: Dict[str, Any]) -> 'AIProviderConfig':
        """Create an AIProviderConfig from a dictionary."""
        # Extract known fields
        known_fields = {
            'display_name', 'type', 'api_key', 'api_base_url', 'model',
            'is_htr_capable', 'is_formatting_capable', 'enabled'
        }
        
        config_data = {'provider_id': provider_id}
        additional_config = {}
        
        for key, value in data.items():
            if key in known_fields:
                config_data[key] = value
            else:
                additional_config[key] = value
        
        config_data['additional_config'] = additional_config
        return cls(**config_data)

    def is_available(self) -> bool:
        """Check if this provider is available for use."""
        if not self.enabled:
            return False
        
        # Basic validation - can be extended with actual connectivity checks
        if self.type == "anthropic" and not self.api_key:
            return False
        
        if self.type == "ollama" and not self.api_base_url:
            return False
        
        return True

@dataclass
class AppSettings:
    """Data model for application settings."""
    monitored_input_dir: str = "/app/input_pdfs"
    processed_output_dir: str = "/app/output_markdown"
    default_output_pattern: str = "YYYY-MM-DD-[OriginalFileName].md"
    custom_output_pattern: Optional[str] = None
    global_retry_attempts: int = 2
    enable_directory_monitoring: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "monitored_input_dir": self.monitored_input_dir,
            "processed_output_dir": self.processed_output_dir,
            "default_output_pattern": self.default_output_pattern,
            "custom_output_pattern": self.custom_output_pattern,
            "global_retry_attempts": self.global_retry_attempts,
            "enable_directory_monitoring": self.enable_directory_monitoring
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppSettings':
        """Create AppSettings from a dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

    def get_output_pattern(self) -> str:
        """Get the effective output pattern (custom or default)."""
        return self.custom_output_pattern or self.default_output_pattern

@dataclass
class ConversionStatistics:
    """Data model for conversion statistics."""
    total_conversions: int = 0
    completed_conversions: int = 0
    failed_conversions: int = 0
    queued_conversions: int = 0
    processing_conversions: int = 0
    recent_activity: int = 0  # Last 24 hours
    status_breakdown: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_conversions": self.total_conversions,
            "completed_conversions": self.completed_conversions,
            "failed_conversions": self.failed_conversions,
            "queued_conversions": self.queued_conversions,
            "processing_conversions": self.processing_conversions,
            "recent_activity": self.recent_activity,
            "status_breakdown": self.status_breakdown
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversionStatistics':
        """Create ConversionStatistics from a dictionary."""
        return cls(**data)

    def get_success_rate(self) -> float:
        """Calculate the success rate as a percentage."""
        if self.total_conversions == 0:
            return 0.0
        return (self.completed_conversions / self.total_conversions) * 100

@dataclass
class UserSetting:
    """Data model for user settings stored in database."""
    id: Optional[int] = None
    setting_key: str = ""
    setting_value: str = ""  # JSON string for complex values
    setting_type: str = "string"  # string, json, boolean, number
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    version: int = 1  # For settings versioning

    def to_dict(self) -> Dict[str, Any]:
        """Convert the setting to a dictionary for JSON serialization."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat() if value else None
            else:
                result[key] = value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserSetting':
        """Create a UserSetting from a dictionary."""
        # Handle datetime fields
        for date_field in ['created_at', 'updated_at']:
            if data.get(date_field) and isinstance(data[date_field], str):
                try:
                    data[date_field] = datetime.fromisoformat(data[date_field])
                except ValueError:
                    data[date_field] = None
        return cls(**data)

    def get_parsed_value(self) -> Any:
        """Parse the setting value based on its type."""
        if self.setting_type == "json":
            try:
                return json.loads(self.setting_value)
            except (json.JSONDecodeError, TypeError):
                return None
        elif self.setting_type == "boolean":
            return self.setting_value.lower() in ('true', '1', 'yes', 'on')
        elif self.setting_type == "number":
            try:
                if '.' in self.setting_value:
                    return float(self.setting_value)
                return int(self.setting_value)
            except (ValueError, TypeError):
                return 0
        return self.setting_value

    def set_value(self, value: Any) -> None:
        """Set the setting value with automatic type detection."""
        if isinstance(value, (dict, list)):
            self.setting_type = "json"
            self.setting_value = json.dumps(value)
        elif isinstance(value, bool):
            self.setting_type = "boolean"
            self.setting_value = str(value).lower()
        elif isinstance(value, (int, float)):
            self.setting_type = "number"
            self.setting_value = str(value)
        else:
            self.setting_type = "string"
            self.setting_value = str(value)

# Validation functions
def validate_conversion_record(data: Dict[str, Any]) -> Dict[str, str]:
    """Validate conversion record data and return any errors."""
    errors = {}
    
    if not data.get('conversion_id'):
        errors['conversion_id'] = "Conversion ID is required"
    
    if not data.get('original_filename'):
        errors['original_filename'] = "Original filename is required"
    
    if 'status' in data:
        try:
            ConversionStatus(data['status'])
        except ValueError:
            errors['status'] = f"Invalid status: {data['status']}"
    
    if 'retry_count' in data and not isinstance(data['retry_count'], int):
        errors['retry_count'] = "Retry count must be an integer"
    
    if 'file_size' in data and data['file_size'] is not None:
        if not isinstance(data['file_size'], int) or data['file_size'] < 0:
            errors['file_size'] = "File size must be a non-negative integer"
    
    if 'page_count' in data and data['page_count'] is not None:
        if not isinstance(data['page_count'], int) or data['page_count'] < 0:
            errors['page_count'] = "Page count must be a non-negative integer"
    
    return errors

def validate_user_setting(data: Dict[str, Any]) -> Dict[str, str]:
    """Validate user setting data and return any errors."""
    errors = {}
    
    if not data.get('setting_key'):
        errors['setting_key'] = "Setting key is required"
    
    if 'setting_value' not in data:
        errors['setting_value'] = "Setting value is required"
    
    setting_type = data.get('setting_type', 'string')
    if setting_type not in ['string', 'json', 'boolean', 'number']:
        errors['setting_type'] = "Setting type must be one of: string, json, boolean, number"
    
    # Validate value format based on type
    setting_value = data.get('setting_value', '')
    if setting_type == 'json':
        try:
            json.loads(setting_value)
        except (json.JSONDecodeError, TypeError):
            errors['setting_value'] = "Invalid JSON format for json type setting"
    elif setting_type == 'number':
        try:
            float(setting_value)
        except (ValueError, TypeError):
            errors['setting_value'] = "Invalid number format for number type setting"
    
    if 'version' in data and not isinstance(data['version'], int):
        errors['version'] = "Version must be an integer"
    
    return errors

def validate_ai_provider_config(data: Dict[str, Any]) -> Dict[str, str]:
    """Validate AI provider configuration and return any errors."""
    errors = {}
    
    if not data.get('display_name'):
        errors['display_name'] = "Display name is required"
    
    if not data.get('type'):
        errors['type'] = "Provider type is required"
    
    provider_type = data.get('type', '').lower()
    
    if provider_type == 'anthropic' and not data.get('api_key'):
        errors['api_key'] = "API key is required for Anthropic providers"
    
    if provider_type == 'ollama' and not data.get('api_base_url'):
        errors['api_base_url'] = "API base URL is required for Ollama providers"
    
    if not data.get('model'):
        errors['model'] = "Model name is required"
    
    # Validate capability flags
    is_htr = data.get('is_htr_capable', False)
    is_formatting = data.get('is_formatting_capable', False)
    
    if not is_htr and not is_formatting:
        errors['capabilities'] = "Provider must be capable of either HTR or formatting"
    
    return errors

# Example usage
if __name__ == '__main__':
    # Test ConversionRecord
    record = ConversionRecord(
        conversion_id="test-123",
        original_filename="test.pdf",
        status=ConversionStatus.PROCESSING,
        file_size=1024,
        page_count=5
    )
    
    print("ConversionRecord:")
    print(f"  Dict: {record.to_dict()}")
    print(f"  Status: {record.get_display_status()}")
    print(f"  File size: {record.get_file_size_formatted()}")
    print(f"  Retryable: {record.is_retryable()}")
    
    # Test AIProviderConfig
    provider = AIProviderConfig(
        provider_id="test_provider",
        display_name="Test Provider",
        type="anthropic",
        api_key="test_key",
        model="claude-3-haiku",
        is_formatting_capable=True
    )
    
    print(f"\nAIProviderConfig:")
    print(f"  Dict: {provider.to_dict()}")
    print(f"  Available: {provider.is_available()}")
    
    # Test validation
    print(f"\nValidation test:")
    invalid_record = {"conversion_id": "", "status": "invalid_status"}
    errors = validate_conversion_record(invalid_record)
    print(f"  Errors: {errors}")