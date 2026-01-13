"""
Time coordination utility for data generation
"""
import time
from datetime import datetime

class TimeCoordinator:
    """Synchronizes time across multiple data generators"""
    
    def __init__(self):
        self.start_time = time.time()
        self.current_timestamp = datetime.now()
    
    def get_current_time(self) -> datetime:
        """Get current coordinated timestamp"""
        return self.current_timestamp
    
    def advance_time(self, seconds: int = 1):
        """Advance the coordinated time by specified seconds"""
        self.current_timestamp = datetime.fromtimestamp(
            self.current_timestamp.timestamp() + seconds
        )
    
    def set_time(self, timestamp: datetime):
        """Set the coordinated time to specific timestamp"""
        self.current_timestamp = timestamp
    
    def reset_time(self):
        """Reset to current system time"""
        self.current_timestamp = datetime.now()