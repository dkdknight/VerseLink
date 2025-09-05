from datetime import datetime, timezone
from typing import List, Optional
from icalendar import Calendar, Event as ICalEvent, vText
from models.event import Event
from models.organization import Organization
from models.user import User
import uuid

class CalendarService:
    """Service for generating iCal calendar files"""
    
    def generate_event_ics(self, event: Event, org: Optional[Organization] = None) -> bytes:
        """Generate iCal file for a single event"""
        cal = Calendar()
        cal.add('prodid', '-//VerseLink//Star Citizen Events//EN')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'PUBLISH')
        
        # Create event
        ical_event = ICalEvent()
        ical_event.add('uid', f"verselink-event-{event.id}@verselink.com")
        ical_event.add('dtstart', event.start_at_utc.replace(tzinfo=timezone.utc))
        ical_event.add('dtend', (event.start_at_utc + 
                                datetime.timedelta(minutes=event.duration_minutes)).replace(tzinfo=timezone.utc))
        ical_event.add('dtstamp', datetime.now(timezone.utc))
        ical_event.add('summary', event.title)
        ical_event.add('description', self._format_event_description(event, org))
        
        if event.location:
            ical_event.add('location', event.location)
        
        # Add categories
        ical_event.add('categories', [event.type.upper(), 'STAR_CITIZEN'])
        
        # Add organizer if org available
        if org:
            ical_event.add('organizer', f"MAILTO:noreply@verselink.com")
            ical_event['organizer'].params['cn'] = vText(f"{org.name} ({org.tag})")
        
        # Add URL
        ical_event.add('url', f"https://verselink.com/events/{event.slug}")
        
        cal.add_component(ical_event)
        
        return cal.to_ical()
    
    def generate_org_calendar(self, events: List[Event], org: Organization) -> bytes:
        """Generate iCal calendar for organization events"""
        cal = Calendar()
        cal.add('prodid', '-//VerseLink//Star Citizen Events//EN')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'PUBLISH')
        cal.add('x-wr-calname', f"{org.name} ({org.tag}) - Events")
        cal.add('x-wr-caldesc', f"Star Citizen events from {org.name}")
        
        for event in events:
            ical_event = ICalEvent()
            ical_event.add('uid', f"verselink-event-{event.id}@verselink.com")
            ical_event.add('dtstart', event.start_at_utc.replace(tzinfo=timezone.utc))
            ical_event.add('dtend', (event.start_at_utc + 
                                    datetime.timedelta(minutes=event.duration_minutes)).replace(tzinfo=timezone.utc))
            ical_event.add('dtstamp', datetime.now(timezone.utc))
            ical_event.add('summary', event.title)
            ical_event.add('description', self._format_event_description(event, org))
            
            if event.location:
                ical_event.add('location', event.location)
            
            ical_event.add('categories', [event.type.upper(), 'STAR_CITIZEN'])
            ical_event.add('organizer', f"MAILTO:noreply@verselink.com")
            ical_event['organizer'].params['cn'] = vText(f"{org.name} ({org.tag})")
            ical_event.add('url', f"https://verselink.com/events/{event.slug}")
            
            cal.add_component(ical_event)
        
        return cal.to_ical()
    
    def generate_user_calendar(self, events: List[Event], user: User) -> bytes:
        """Generate iCal calendar for user's events"""
        cal = Calendar()
        cal.add('prodid', '-//VerseLink//Star Citizen Events//EN')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'PUBLISH')
        cal.add('x-wr-calname', f"{user.handle} - Star Citizen Events")
        cal.add('x-wr-caldesc', f"Star Citizen events for {user.handle}")
        
        for event in events:
            ical_event = ICalEvent()
            ical_event.add('uid', f"verselink-event-{event.id}-user-{user.id}@verselink.com")
            ical_event.add('dtstart', event.start_at_utc.replace(tzinfo=timezone.utc))
            ical_event.add('dtend', (event.start_at_utc + 
                                    datetime.timedelta(minutes=event.duration_minutes)).replace(tzinfo=timezone.utc))
            ical_event.add('dtstamp', datetime.now(timezone.utc))
            ical_event.add('summary', event.title)
            ical_event.add('description', self._format_event_description(event))
            
            if event.location:
                ical_event.add('location', event.location)
            
            ical_event.add('categories', [event.type.upper(), 'STAR_CITIZEN'])
            ical_event.add('url', f"https://verselink.com/events/{event.slug}")
            
            cal.add_component(ical_event)
        
        return cal.to_ical()
    
    def _format_event_description(self, event: Event, org: Optional[Organization] = None) -> str:
        """Format event description for iCal"""
        lines = [
            event.description,
            "",
            f"Type: {event.type.title()}",
            f"Duration: {event.duration_minutes} minutes",
        ]
        
        if event.location:
            lines.append(f"Location: {event.location}")
        
        if org:
            lines.extend([
                "",
                f"Organized by: {org.name} ({org.tag})"
            ])
        
        lines.extend([
            "",
            f"View event: https://verselink.com/events/{event.slug}",
            "",
            "Generated by VerseLink - Star Citizen Community Platform"
        ])
        
        return "\\n".join(lines)