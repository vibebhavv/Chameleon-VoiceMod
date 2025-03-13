import sys
import datetime
import logging
from typing import Optional
import tkinter as tk
from customtkinter import CTkTextbox

class ConsoleLogging:
    def __init__(self, text_widget: CTkTextbox):
        self.text_widget = text_widget
        self.text_widget.configure(state="disabled")
        
        # Store original stdout
        self.stdout = sys.stdout
        sys.stdout = self
        
        # Configure logging
        self.logger = logging.getLogger('GuiLogger')
        self.logger.setLevel(logging.DEBUG)
        
        # Create custom handler
        self.handler = GuiLogHandler(self.text_widget)
        self.handler.setLevel(logging.DEBUG)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s', 
                                    datefmt='%H:%M:%S')
        self.handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(self.handler)
        
        # Color codes for different log levels
        self.colors = {
            'INFO': '#FFFFFF',     # White
            'ERROR': '#FF0000',    # Red
            'WARNING': '#FFA500'
        }

    def write(self, message: str) -> None:
        """Write message to text widget with appropriate formatting"""
        if message.strip():  # Only process non-empty messages
            # Parse the log level from the message
            level = self._parse_log_level(message)
            
            self.text_widget.configure(state="normal")
            
            # Add timestamp in green
            timestamp = datetime.datetime.now().strftime('%H:%M:%S')
            self.text_widget._textbox.insert('end', f'{timestamp} - ', '')
            self.text_widget._textbox.tag_add('timestamp', 'end-1l linestart', 'end-1l lineend')
            self.text_widget._textbox.tag_config('timestamp', foreground='#00FF00')
            
            # Insert the message with appropriate color
            if level:
                color = self.colors.get(level, '#FFFFFF')
                self.text_widget._textbox.insert('end', message, '')
                self.text_widget._textbox.tag_add(f'tag_{level.lower()}', 
                                                'end-1l linestart', 'end-1l lineend')
                self.text_widget._textbox.tag_config(f'tag_{level.lower()}', 
                                                   foreground=color)
            else:
                self.text_widget._textbox.insert('end', message)
            
            # Ensure latest messages are visible
            self.text_widget.see('end')
            self.text_widget.configure(state="disabled")

    def flush(self) -> None:
        """Required for file-like object interface"""
        pass

    def _parse_log_level(self, message: str) -> Optional[str]:
        """Parse the log level from a message"""
        level_indicators = {
            '[INFO]': 'INFO',
            '[ERR]': 'ERROR',
            '[WARN]': 'WARNING'
        }
        
        for indicator, level in level_indicators.items():
            if indicator in message:
                return level
        return None

    def setup_tags(self) -> None:
        """Configure text tags for different log levels"""
        # Access the underlying tkinter Text widget
        text_widget = self.text_widget._textbox
        
        for level, color in self.colors.items():
            tag_name = f'tag_{level.lower()}'
            text_widget.tag_configure(tag_name, foreground=color)
        
        # Configure timestamp tag
        text_widget.tag_configure('timestamp', foreground='#00FF00')

    def log_info(self, message: str) -> None:
        """Log info message"""
        self.logger.info(message)

    def log_error(self, message: str) -> None:
        """Log error message"""
        self.logger.error(message)

    def log_warning(self, message: str) -> None:
        """Log warning message"""
        self.logger.warning(message)

class GuiLogHandler(logging.Handler):
    """Custom logging handler that writes to the GUI"""
    def __init__(self, text_widget: CTkTextbox):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        """Emit a log record to the text widget"""
        try:
            msg = self.format(record)
            self.text_widget.configure(state="normal")
            # Access the underlying tkinter Text widget
            self.text_widget._textbox.insert('end', msg + '\n')
            
            # Apply color based on log level
            level = record.levelname
            if level in ['INFO', 'ERROR']:
                tag_name = f'tag_{level.lower()}'
                self.text_widget._textbox.tag_add(
                    tag_name, 
                    'end-2l linestart', 
                    'end-2l lineend'
                )
            
            self.text_widget.see('end')
            self.text_widget.configure(state="disabled")
        except Exception:
            self.handleError(record)