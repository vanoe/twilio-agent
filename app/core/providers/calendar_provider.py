from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from langchain_core.tools import tool

class CalendarProvider(ABC):

    @tool("schedule_appointment")
    @abstractmethod
    def schedule_appointment(
        self,
        user_id: str,
        start_time: datetime,
        end_time: datetime,
        title: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
    ) -> str:
        """
        Schedule an appointment for a user.

        Args:
            user_id (str): The ID of the user.
            start_time (datetime): The start time of the appointment.
            end_time (datetime): The end time of the appointment.
            title (str): The title of the appointment.
            description (Optional[str]): A description of the appointment.
            location (Optional[str]): The location of the appointment.

        Returns:
            str: Confirmation message or appointment ID.
        """
        pass

    @tool("cancel_appointment")
    @abstractmethod
    def cancel_appointment(
        self,
        appointment_id: str
    ) -> bool:
        """
        Cancel an existing appointment using the appointment ID.
        
        Args:
            appointment_id (str): The ID of the appointment to cancel.
        
        Returns:
            bool: True if the appointment was successfully cancelled, False otherwise.
        """
        pass

    @tool("check_availability")
    @abstractmethod
    def check_availability(
        self,
        user_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> bool:
        """
        Check if a user is available for an appointment within a specified time range.
        Args:
            user_id (str): The ID of the user.
            start_time (datetime): The start time of the appointment.
            end_time (datetime): The end time of the appointment.
        Returns:
            bool: True if the user is available, False otherwise.
        """
        pass

    @tool("get_availability_slots")
    @abstractmethod
    def get_availability_slots(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, datetime]]:
        """
        Get available time slots for a user within a specified date range.

        Args:
            user_id (str): The ID of the user.
            start_date (datetime): The start date of the range.
            end_date (datetime): The end date of the range.

        Returns:
            List[Dict[str, datetime]]: A list of available time slots with start and end times.
        """
        pass

    @tool("reschedule_appointment")
    @abstractmethod
    def reschedule_appointment(
        self, appointment_id: str, new_start_time: datetime, new_end_time: datetime
    ) -> bool:
        """Reschedule an existing appointment to a new time slot."""
        pass
    