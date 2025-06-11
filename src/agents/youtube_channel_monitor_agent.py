#!/usr/bin/env python3
"""
YouTube Channel Monitor Agent
============================

Monitors YouTube Channels database for channels marked for processing.
Part of the multi-agent YouTube processing pipeline.
"""

import asyncio
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from loguru import logger

from ..agents.agent_base import AgentBase
from ..core.shared_memory import SharedMemory


class YouTubeChannelMonitorAgent(AgentBase):
    """
    Agent responsible for monitoring YouTube channels database and triggering processing.
    
    Features:
    - Monitors "Process Channel" checkbox in YouTube Channels database
    - Monitors "Auto Process" for automated processing
    - Validates channel URLs and resolves channel IDs
    - Triggers video discovery for marked channels
    - Updates processing status after completion
    """
    
    def __init__(self, agent_id: str, shared_memory: SharedMemory):
        super().__init__(agent_id, shared_memory)
        self.name = "YouTube Channel Monitor"
        self.description = "Monitors YouTube channels for processing triggers"
        
        # Database configuration from environment
# NOTION_REMOVED:         self.channels_db_id = os.getenv('NOTION_CHANNELS_DATABASE_ID', '203ec31c-9de2-8079-ae4e-ed754d474888')
        
        self.headers = {
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        # Processing state
        self.processing_channels = set()
        self.check_interval = 60  # Check every minute
        
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute channel monitoring task."""
        try:
            logger.info(f"🔍 {self.name} starting channel monitoring cycle")
            
            # Get channels marked for processing
            marked_channels = await self._get_marked_channels()
            
            if not marked_channels:
                logger.info("No channels marked for processing")
                return {
                    "status": "success",
                    "channels_found": 0,
                    "channels_processed": 0
                }
            
            logger.info(f"Found {len(marked_channels)} channels to process")
            
            # Process each channel
            processed_count = 0
            for channel in marked_channels:
                if channel['id'] not in self.processing_channels:
                    self.processing_channels.add(channel['id'])
                    
                    # Create task for video discovery agent
                    discovery_task = {
                        "type": "discover_videos",
                        "channel": channel,
                        "triggered_by": self.agent_id,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Send to shared memory for video discovery agent
                    await self.shared_memory.set(
                        f"youtube_discovery_{channel['id']}", 
                        discovery_task
                    )
                    
                    # Log the event
                    await self.log_event(
                        "channel_marked_for_processing",
                        {
                            "channel_name": channel['name'],
                            "channel_id": channel.get('channel_id'),
                            "url": channel.get('url')
                        }
                    )
                    
                    processed_count += 1
                    logger.info(f"📺 Triggered processing for: {channel['name']}")
            
            return {
                "status": "success",
                "channels_found": len(marked_channels),
                "channels_processed": processed_count,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in channel monitoring: {e}")
            await self.log_error("channel_monitoring_error", str(e))
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _get_marked_channels(self) -> List[Dict[str, Any]]:
        """Get channels marked for processing from Notion."""
        import aiohttp
        
        try:
            # Query for channels with Process Channel = true OR Auto Process = true
            query_data = {
                "filter": {
                    "or": [
                        {
                            "property": "Process Channel",
                            "checkbox": {"equals": True}
                        },
                        {
                            "property": "Auto Process", 
                            "checkbox": {"equals": True}
                        }
                    ]
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    headers=self.headers,
                    json=query_data,
                    timeout=10
                ) as response:
                    if response.status != 200:
                        logger.error(f"Failed to query channels: {response.status}")
                        return []
                    
                    data = await response.json()
                    results = data.get('results', [])
            
            # Extract channel information
            channels = []
            for page in results:
                props = page['properties']
                
                channel_data = {
                    'id': page['id'],
                    'name': self._extract_text_property(props.get('Name')),
                    'url': self._extract_text_property(props.get('URL')),
                    'channel_id': self._extract_text_property(props.get('Channel')),
                    'hashtags': self._extract_multi_select(props.get('Hashtags')),
                    'auto_process': props.get('Auto Process', {}).get('checkbox', False),
                    'manual_process': props.get('Process Channel', {}).get('checkbox', False)
                }
                
                # Validate channel has required data
                if channel_data['name'] and (channel_data['url'] or channel_data['channel_id']):
                    channels.append(channel_data)
                else:
                    logger.warning(f"Skipping channel with incomplete data: {channel_data}")
            
            return channels
            
        except Exception as e:
            logger.error(f"Error getting marked channels: {e}")
            return []
    
    async def update_channel_status(self, channel_id: str, status: Dict[str, Any]):
        """Update channel processing status in Notion."""
        import aiohttp
        
        try:
            # Prepare update data
            properties = {
                "Last Processed": {
                    "date": {"start": datetime.now().isoformat()}
                }
            }
            
            # Uncheck Process Channel if it was manually triggered
            if status.get('manual_process'):
                properties["Process Channel"] = {"checkbox": False}
            
            # Add processing notes
            if status.get('stats'):
                stats = status['stats']
                notes = f"Processed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                notes += f"Total videos: {stats.get('total_videos', 0)}\n"
                notes += f"New videos: {stats.get('new_videos', 0)}\n"
                notes += f"Imported: {stats.get('imported_videos', 0)}"
                
                properties["Notes"] = {
                    "rich_text": [{"text": {"content": notes}}]
                }
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(
                    headers=self.headers,
                    json={"properties": properties},
                    timeout=10
                ) as response:
                    if response.status == 200:
                        logger.info(f"✅ Updated channel status for {channel_id}")
                        return True
                    else:
                        logger.error(f"Failed to update channel: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error updating channel status: {e}")
            return False
    
    def _extract_text_property(self, prop: Optional[Dict]) -> str:
        """Extract text from various Notion property types."""
        if not prop:
            return ""
        
        # Title property
        if prop.get('title'):
            return prop['title'][0].get('plain_text', '') if prop['title'] else ""
        
        # Rich text property
        if prop.get('rich_text'):
            return prop['rich_text'][0].get('plain_text', '') if prop['rich_text'] else ""
        
        # URL property
        if prop.get('url'):
            return prop['url']
        
        return ""
    
    def _extract_multi_select(self, prop: Optional[Dict]) -> List[str]:
        """Extract values from multi-select property."""
        if not prop or not prop.get('multi_select'):
            return []
        
        return [item['name'] for item in prop['multi_select']]
    
    async def continuous_monitor(self):
        """Run continuous monitoring loop."""
        logger.info(f"🚀 Starting continuous channel monitoring (interval: {self.check_interval}s)")
        
        while self.is_running:
            try:
                # Execute monitoring cycle
                result = await self.execute({})
                
                # Handle channel completion messages
                await self._process_completion_messages()
                
                # Wait for next cycle
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(10)  # Brief pause on error
    
    async def _process_completion_messages(self):
        """Process completion messages from other agents."""
        # Check for completion messages
        completion_keys = await self.shared_memory.list_keys("youtube_complete_*")
        
        for key in completion_keys:
            try:
                completion_data = await self.shared_memory.get(key)
                if completion_data:
                    channel_id = completion_data.get('channel_id')
                    
                    # Update channel status
                    await self.update_channel_status(channel_id, completion_data)
                    
                    # Remove from processing set
                    self.processing_channels.discard(channel_id)
                    
                    # Clear the completion message
                    await self.shared_memory.delete(key)
                    
                    logger.info(f"✅ Processed completion for channel: {channel_id}")
                    
            except Exception as e:
                logger.error(f"Error processing completion message: {e}")


def create_youtube_channel_monitor_agent(agent_id: str, shared_memory: SharedMemory) -> YouTubeChannelMonitorAgent:
    """Factory function to create YouTube channel monitor agent."""
    return YouTubeChannelMonitorAgent(agent_id, shared_memory)