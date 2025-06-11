#!/usr/bin/env python3
"""
Enhanced Channel Processor with Database Views
==============================================

Enhanced version of the YouTube channel processor that automatically adds
filtered database views to channel pages after processing videos.
"""

import os
import asyncio
from typing import Dict, List, Any, Optional
try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

from .notion_mcp_client 

class EnhancedChannelProcessor:
    """
    Enhanced channel processor that adds database views to channel pages.
    
    This class extends the basic channel processing functionality by automatically
    creating filtered database views on each channel page that show only videos
    from that specific channel.
    """
    
# NOTION_REMOVED:     def __init__(self, notion_client: NotionMCPClient, knowledge_db_id: str):
        """Initialize the enhanced channel processor."""
# NOTION_REMOVED:         self.notion_client = notion_client
        self.knowledge_db_id = knowledge_db_id
        logger.info("Enhanced Channel Processor initialized")
    
    async def add_filtered_database_view_to_channel(self, channel_page_id: str, channel_name: str) -> bool:
        """Add a filtered database view to a channel page."""
        try:
            logger.info(f"Adding database view to channel: {channel_name}")
            
            # Check if the page already has a linked database for Knowledge Hub
            if await self.notion_client.has_linked_database(channel_page_id, self.knowledge_db_id):
                logger.info(f"Channel page already has Knowledge Hub database view")
                return True
            
            # Create the linked database block with heading
            heading_text = f"📺 Videos from {channel_name}"
# NOTION_REMOVED:             success = await self.notion_client.create_linked_database_block(
                channel_page_id, 
                self.knowledge_db_id, 
                heading_text
            )
            
            if success:
                # Add instructions for filtering
                await self.add_filter_instructions(channel_page_id, channel_name)
                logger.info(f"✅ Successfully added database view to {channel_name}")
                return True
            else:
                logger.error(f"Failed to add database view to {channel_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error adding database view to {channel_name}: {e}")
            return False
    
    async def add_filter_instructions(self, page_id: str, channel_name: str) -> bool:
        """Add instructions for filtering the database view."""
        try:
            # Clean channel name for filtering
            clean_channel_name = channel_name.replace('@', '') if channel_name.startswith('@') else channel_name
            
            instruction_blocks = [
                {
                    "type": "callout",
                    "callout": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": f"💡 Filter Instructions:\n1. Click 'Filter' in the database above\n2. Add filter: Channel → Contains → \"{clean_channel_name}\"\n3. The view will show only videos from this channel\n\nThe filter will automatically include new videos as they're processed."
                                }
                            }
                        ],
                        "icon": {
                            "emoji": "💡"
                        },
                        "color": "blue"
                    }
                }
            ]
            
            return await self.notion_client.add_page_content(page_id, instruction_blocks)
            
        except Exception as e:
            logger.error(f"Error adding filter instructions: {e}")
            return False
    
    async def process_all_channels_for_database_views(self) -> Dict[str, Any]:
        """Process all channel pages to add database views."""
        logger.info("🔄 Adding database views to all channel pages...")
        
        result = {
            "channels_processed": 0,
            "channels_updated": 0,
            "channels_skipped": 0,
            "errors": []
        }
        
        try:
            # Search for channel pages (assuming they have "Channel" in the title or are in a specific location)
            # This is a simplified approach - you may need to adjust based on your page structure
# NOTION_REMOVED:             pages = await self.notion_client.search_pages("YouTube Channel", 50)
            
            if not pages:
                logger.info("No channel pages found")
                return result
            
            logger.info(f"Found {len(pages)} potential channel pages")
            
            for page in pages:
                try:
                    page_id = page.get('id', '')
                    
                    # Get page title
                    page_title = "Unknown Page"
                    if page.get('properties', {}).get('title', {}).get('title'):
                        page_title = page['properties']['title']['title'][0]['plain_text']
                    elif page.get('properties', {}).get('Name', {}).get('title'):
                        page_title = page['properties']['Name']['title'][0]['plain_text']
                    
                    result["channels_processed"] += 1
                    logger.info(f"Processing page: {page_title}")
                    
                    # Check if this page already has a database view
                    if await self.notion_client.has_linked_database(page_id, self.knowledge_db_id):
                        logger.info(f"Page already has database view, skipping")
                        result["channels_skipped"] += 1
                        continue
                    
                    # Add database view
                    success = await self.add_filtered_database_view_to_channel(page_id, page_title)
                    
                    if success:
                        result["channels_updated"] += 1
                        logger.info(f"✅ Added database view to {page_title}")
                    else:
                        error_msg = f"Failed to add database view to {page_title}"
                        logger.error(error_msg)
                        result["errors"].append(error_msg)
                    
                    # Small delay between pages
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    error_msg = f"Error processing page {page.get('id', 'unknown')}: {str(e)}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
            
            logger.info(f"🎉 Database view processing complete!")
            logger.info(f"📊 Processed: {result['channels_processed']}")
            logger.info(f"✅ Updated: {result['channels_updated']}")
            logger.info(f"⏭️ Skipped: {result['channels_skipped']}")
            
            if result["errors"]:
                logger.warning(f"⚠️ Errors: {len(result['errors'])}")
            
        except Exception as e:
            logger.error(f"Error in database view processing: {e}")
            result["errors"].append(f"Processing error: {str(e)}")
        
        return result
    
    async def add_database_view_for_specific_channel(self, channel_name: str) -> bool:
        """Add database view for a specific channel by name."""
        try:
            logger.info(f"Looking for channel page: {channel_name}")
            
            # Search for the specific channel page
# NOTION_REMOVED:             pages = await self.notion_client.search_pages(channel_name, 10)
            
            if not pages:
                logger.error(f"No pages found for channel: {channel_name}")
                return False
            
            # Find the best matching page
            best_match = None
            for page in pages:
                page_title = "Unknown"
                if page.get('properties', {}).get('title', {}).get('title'):
                    page_title = page['properties']['title']['title'][0]['plain_text']
                elif page.get('properties', {}).get('Name', {}).get('title'):
                    page_title = page['properties']['Name']['title'][0]['plain_text']
                
                if channel_name.lower() in page_title.lower():
                    best_match = page
                    break
            
            if not best_match:
                best_match = pages[0]  # Use first result as fallback
            
            page_id = best_match.get('id', '')
            page_title = "Unknown"
            if best_match.get('properties', {}).get('title', {}).get('title'):
                page_title = best_match['properties']['title']['title'][0]['plain_text']
            elif best_match.get('properties', {}).get('Name', {}).get('title'):
                page_title = best_match['properties']['Name']['title'][0]['plain_text']
            
            logger.info(f"Found matching page: {page_title}")
            
            # Add database view
            return await self.add_filtered_database_view_to_channel(page_id, channel_name)
            
        except Exception as e:
            logger.error(f"Error adding database view for {channel_name}: {e}")
            return False


# NOTION_REMOVED: def create_enhanced_channel_processor(notion_client: NotionMCPClient, knowledge_db_id: str) -> EnhancedChannelProcessor:
    """Factory function to create enhanced channel processor."""
    return EnhancedChannelProcessor(notion_client, knowledge_db_id)