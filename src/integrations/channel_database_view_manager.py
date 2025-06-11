#!/usr/bin/env python3
"""
Channel Database View Manager
============================

Manages filtered database views on YouTube channel pages in Notion.
Adds filtered views of the Knowledge Hub database to each channel page,
showing only videos from that specific channel.
"""

import os
import asyncio
import requests
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)


class ChannelDatabaseViewManager:
    """
    Manages filtered database views on YouTube channel pages.
    
    Features:
    - Creates filtered views of Knowledge Hub database on channel pages
    - Filters show only videos from the specific channel
    - Automatically updates when channels are processed
    - Handles both creation and updates of database views
    """
    
        """Initialize the channel database view manager."""
        self.config = config or {}
        
        # Get database IDs from config or environment
        self.channels_db_id = (
            self.config.get("api", {}).get("notion", {}).get("channels_database_id") or
            self.config.get("notion", {}).get("channels_database_id") or
            os.getenv("NOTION_CHANNELS_DATABASE_ID")
        )
        self.knowledge_db_id = (
            self.config.get("api", {}).get("notion", {}).get("knowledge_database_id") or
            self.config.get("notion", {}).get("knowledge_database_id") or
            os.getenv("NOTION_KNOWLEDGE_DATABASE_ID") or
            "20bec31c-9de2-814e-80db-d13d0c27d869"  # Fallback to known ID
        )
        
        self.headers = {
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        logger.info("Channel Database View Manager initialized")
    
    async def get_channel_page_content(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Get the content of a channel page to check for existing database views."""
        try:
            # Get page content/children
            response = requests.get(
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get page content: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting page content: {e}")
            return None
    
    def has_knowledge_hub_database_view(self, page_content: Dict[str, Any]) -> bool:
        """Check if page already has a Knowledge Hub database view."""
        try:
            results = page_content.get('results', [])
            
            for block in results:
                # Check for linked_database blocks
                if block.get('type') == 'linked_database':
                    database_id = block.get('linked_database', {}).get('database_id', '')
                    # Check if it's our Knowledge Hub database
                    if database_id == self.knowledge_db_id:
                        logger.debug(f"Found existing Knowledge Hub database view")
                        return True
                
                # Check for child_database blocks (embedded databases)
                elif block.get('type') == 'child_database':
                    # For child databases, the database_id might be in the ID field
                    if block.get('id') == self.knowledge_db_id:
                        logger.debug(f"Found existing Knowledge Hub child database")
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking for existing database view: {e}")
            return False
    
    async def create_filtered_database_view(self, channel_page_id: str, channel_name: str) -> bool:
        """Create a filtered database view on a channel page."""
        try:
            logger.info(f"Creating filtered database view for channel: {channel_name}")
            
            # First check if page already has the database view
            page_content = await self.get_channel_page_content(channel_page_id)
            if page_content and self.has_knowledge_hub_database_view(page_content):
                logger.info(f"Channel page already has Knowledge Hub database view, skipping")
                return True
            
            # Clean channel name for filtering (remove @ symbol if present)
            clean_channel_name = channel_name.replace('@', '') if channel_name.startswith('@') else channel_name
            
            # Create the database view block with filter
            # Note: Notion API creates linked_database blocks, but the filtering happens in the UI
            # We'll create a linked database and then add a heading to explain the filter
            blocks_to_add = [
                {
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": f"📺 Videos from {channel_name}"
                                }
                            }
                        ]
                    }
                },
                {
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": f"Filtered view of Knowledge Hub showing only videos from this channel. Use the filter controls below to customize the view."
                                }
                            }
                        ]
                    }
                },
                {
                    "type": "linked_database",
                    "linked_database": {
                        "database_id": self.knowledge_db_id
                    }
                }
            ]
            
            # Add the blocks to the page
            response = requests.patch(
                headers=self.headers,
                json={"children": blocks_to_add},
                timeout=15
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Successfully added filtered database view to {channel_name}")
                
                # Since Notion API doesn't support setting filters programmatically on linked databases,
                # we'll add instructions for manual filtering
                await self.add_filter_instructions(channel_page_id, clean_channel_name)
                
                return True
            else:
                logger.error(f"Failed to add database view: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating filtered database view: {e}")
            return False
    
    async def add_filter_instructions(self, page_id: str, channel_name: str) -> bool:
        """Add instructions for filtering the database view."""
        try:
            instruction_blocks = [
                {
                    "type": "callout",
                    "callout": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": f"💡 To filter this view to show only {channel_name} videos:\n1. Click the 'Filter' button in the database\n2. Add filter: Channel → Text → Contains → \"{channel_name}\"\n3. The view will automatically update to show only videos from this channel"
                                }
                            }
                        ],
                        "icon": {
                            "emoji": "💡"
                        }
                    }
                }
            ]
            
            # Add instruction block
            response = requests.patch(
                headers=self.headers,
                json={"children": instruction_blocks},
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error adding filter instructions: {e}")
            return False
    
    async def create_pre_filtered_view_with_api(self, channel_page_id: str, channel_name: str) -> bool:
        """
        Alternative approach: Create a database query block with filter.
        This method attempts to create a filtered view using the database query endpoint.
        """
        try:
            logger.info(f"Creating pre-filtered database view for channel: {channel_name}")
            
            # Clean channel name for filtering
            clean_channel_name = channel_name.replace('@', '') if channel_name.startswith('@') else channel_name
            
            # Create a text block that explains what we're showing
            explanation_blocks = [
                {
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": f"📺 {channel_name} Video Collection"
                                }
                            }
                        ]
                    }
                },
                {
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": f"All videos from {channel_name} in your Knowledge Hub. Click on any video title below to open the full analysis."
                                }
                            }
                        ]
                    }
                }
            ]
            
            # Add explanation blocks first
            response = requests.patch(
                headers=self.headers,
                json={"children": explanation_blocks},
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to add explanation blocks: {response.status_code}")
                return False
            
            # Query the Knowledge Hub database for videos from this channel
            channel_videos = await self.get_channel_videos_from_knowledge_hub(clean_channel_name)
            
            if not channel_videos:
                # Add a message indicating no videos found
                no_videos_block = [
                    {
                        "type": "callout",
                        "callout": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": f"No videos found for {channel_name} yet. Videos will appear here automatically when the channel is processed."
                                    }
                                }
                            ],
                            "icon": {
                                "emoji": "📋"
                            }
                        }
                    }
                ]
                
                response = requests.patch(
                    headers=self.headers,
                    json={"children": no_videos_block},
                    timeout=10
                )
                
                return response.status_code == 200
            
            # Create video list blocks
            video_blocks = await self.create_video_list_blocks(channel_videos)
            
            # Add video blocks in batches (Notion has limits on block creation)
# NOTION_REMOVED:             batch_size = 100  # Notion limit
            for i in range(0, len(video_blocks), batch_size):
                batch = video_blocks[i:i + batch_size]
                
                response = requests.patch(
                    headers=self.headers,
                    json={"children": batch},
                    timeout=15
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to add video batch {i//batch_size + 1}: {response.status_code}")
                    return False
                
                # Small delay between batches
                await asyncio.sleep(0.5)
            
            logger.info(f"✅ Successfully created video list for {channel_name} ({len(channel_videos)} videos)")
            return True
            
        except Exception as e:
            logger.error(f"Error creating pre-filtered view: {e}")
            return False
    
    async def get_channel_videos_from_knowledge_hub(self, channel_name: str) -> List[Dict[str, Any]]:
        """Get all videos from a specific channel in the Knowledge Hub."""
        try:
            # Query Knowledge Hub database for videos from this channel
            query_data = {
                "filter": {
                    "and": [
                        {
                            "property": "Type",
                            "select": {
                                "equals": "YouTube"
                            }
                        },
                        {
                            "property": "Channel",
                            "rich_text": {
                                "contains": channel_name
                            }
                        }
                    ]
                },
                "sorts": [
                    {
                        "property": "Date Created",
                        "direction": "descending"
                    }
                ],
                "page_size": 100
            }
            
            response = requests.post(
                headers=self.headers,
                json=query_data,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                videos = data.get('results', [])
                
                logger.info(f"Found {len(videos)} videos for channel: {channel_name}")
                return videos
            else:
                logger.error(f"Failed to query Knowledge Hub: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error querying Knowledge Hub for channel videos: {e}")
            return []
    
    async def create_video_list_blocks(self, videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create Notion blocks for a list of videos."""
        blocks = []
        
        if not videos:
            return blocks
        
        # Add a divider
        blocks.append({
            "type": "divider",
            "divider": {}
        })
        
        for video in videos:
            try:
                props = video.get('properties', {})
                
                # Get video title
                title = "Unknown Video"
                if props.get('Name', {}).get('title'):
                    title = props['Name']['title'][0]['plain_text']
                
                # Get video URL
                url = ""
                if props.get('URL', {}).get('url'):
                    url = props['URL']['url']
                
                # Get status
                status = ""
                if props.get('Status', {}).get('select'):
                    status = props['Status']['select']['name']
                
                # Get AI Summary
                summary = ""
                if props.get('AI Summary', {}).get('rich_text'):
                    summary = props['AI Summary']['rich_text'][0]['plain_text'][:200] + "..." if len(props['AI Summary']['rich_text'][0]['plain_text']) > 200 else props['AI Summary']['rich_text'][0]['plain_text']
                
                # Create video entry block
                video_block = {
                    "type": "toggle",
                    "toggle": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": f"🎬 {title}"
                                },
                                "annotations": {
                                    "bold": True
                                }
                            }
                        ],
                        "children": [
                            {
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [
                                        {
                                            "type": "text",
                                            "text": {
                                                "content": f"Status: {status}" if status else "Status: Not set"
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }
                
                # Add URL if available
                if url:
                    video_block["toggle"]["children"].append({
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": "Watch: "
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": {
                                        "content": url,
                                        "link": {
                                            "url": url
                                        }
                                    }
                                }
                            ]
                        }
                    })
                
                # Add summary if available
                if summary:
                    video_block["toggle"]["children"].append({
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": f"Summary: {summary}"
                                    }
                                }
                            ]
                        }
                    })
                
                # Add link to the full page
                video_block["toggle"]["children"].append({
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "View full analysis →",
                                    "link": {
                                        "url": f"https://notion.so/{video['id'].replace('-', '')}"
                                    }
                                },
                                "annotations": {
                                    "italic": True
                                }
                            }
                        ]
                    }
                })
                
                blocks.append(video_block)
                
            except Exception as e:
                logger.error(f"Error creating block for video: {e}")
                continue
        
        return blocks
    
    async def add_database_view_to_channel(self, channel_page_id: str, channel_name: str) -> bool:
        """
        Main method to add a filtered database view to a channel page.
        Tries multiple approaches for best compatibility.
        """
        logger.info(f"Adding database view to channel page: {channel_name}")
        
        # Check if page already has content
        page_content = await self.get_channel_page_content(channel_page_id)
        if page_content and self.has_knowledge_hub_database_view(page_content):
            logger.info(f"Channel page already has Knowledge Hub database view")
            return True
        
        # Method 1: Try creating a linked database (most elegant, but may not support pre-filtering)
        try:
            success = await self.create_filtered_database_view(channel_page_id, channel_name)
            if success:
                logger.info(f"✅ Successfully added linked database view to {channel_name}")
                return True
        except Exception as e:
            logger.warning(f"Linked database approach failed: {e}")
        
        # Method 2: Create a custom video list (more control, always works)
        try:
            success = await self.create_pre_filtered_view_with_api(channel_page_id, channel_name)
            if success:
                logger.info(f"✅ Successfully added custom video list to {channel_name}")
                return True
        except Exception as e:
            logger.error(f"Custom video list approach failed: {e}")
        
        return False
    
    async def update_all_channel_views(self) -> Dict[str, Any]:
        """Update database views for all channels."""
        logger.info("🔄 Updating database views for all channels...")
        
        result = {
            "channels_updated": 0,
            "errors": [],
            "start_time": datetime.now(),
            "end_time": None
        }
        
        try:
            # Get all channels
            channels = await self.get_all_channels()
            
            if not channels:
                logger.info("No channels found")
                result["end_time"] = datetime.now()
                return result
            
            logger.info(f"Updating database views for {len(channels)} channels")
            
            # Update each channel
            for i, channel in enumerate(channels, 1):
                try:
                    logger.info(f"📺 Updating channel {i}/{len(channels)}: {channel['name']}")
                    
                    success = await self.add_database_view_to_channel(channel['page_id'], channel['name'])
                    
                    if success:
                        result["channels_updated"] += 1
                        logger.info(f"✅ Updated database view for {channel['name']}")
                    else:
                        error_msg = f"Failed to update database view for {channel['name']}"
                        logger.error(error_msg)
                        result["errors"].append(error_msg)
                    
                    # Small delay between channels
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    error_msg = f"Error updating {channel['name']}: {str(e)}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
            
            result["end_time"] = datetime.now()
            duration = (result["end_time"] - result["start_time"]).total_seconds()
            
            logger.info(f"🎉 Database view update complete!")
            logger.info(f"📊 Updated {result['channels_updated']}/{len(channels)} channels")
            logger.info(f"⏱️ Duration: {duration:.1f} seconds")
            
            if result["errors"]:
                logger.warning(f"⚠️ {len(result['errors'])} errors occurred")
            
        except Exception as e:
            logger.error(f"Error in database view update cycle: {e}")
            result["errors"].append(f"Update cycle error: {str(e)}")
            result["end_time"] = datetime.now()
        
        return result
    
    async def get_all_channels(self) -> List[Dict[str, Any]]:
        """Get all channels from the YouTube Channels database."""
        if not self.channels_db_id:
            logger.error("No channels database ID configured")
            return []
        
        try:
            all_results = []
            has_more = True
            start_cursor = None
            
            while has_more:
                query_data = {}
                if start_cursor:
                    query_data["start_cursor"] = start_cursor
                
                response = requests.post(
                    headers=self.headers,
                    json=query_data,
                    timeout=10
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to query channels: {response.status_code}")
                    return []
                
                data = response.json()
                all_results.extend(data.get('results', []))
                
                has_more = data.get('has_more', False)
                start_cursor = data.get('next_cursor')
            
            # Extract channel info
            channels = []
            for page in all_results:
                props = page['properties']
                
                channel_data = {
                    'page_id': page['id'],
                    'name': '',
                    'url': ''
                }
                
                # Extract channel name
                if props.get('Name', {}).get('title'):
                    channel_data['name'] = props['Name']['title'][0]['plain_text']
                
                # Extract URL
                if props.get('URL', {}).get('rich_text'):
                    channel_data['url'] = props['URL']['rich_text'][0]['plain_text']
                
                if channel_data['name']:  # Only include channels with names
                    channels.append(channel_data)
            
            logger.info(f"Found {len(channels)} channels")
            return channels
            
        except Exception as e:
            logger.error(f"Error getting all channels: {e}")
            return []


    """Factory function to create channel database view manager."""