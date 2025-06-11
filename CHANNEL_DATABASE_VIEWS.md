# Channel Database Views Setup

This guide explains how to add filtered database views to your YouTube channel pages in Notion, so each channel page shows only videos from that specific channel.

## Overview

The Channel Database Views functionality automatically adds filtered views of your Knowledge Hub database to each YouTube channel page. When you click to open a channel page (e.g., @NateBJones), you'll see a filtered view showing only videos from that channel.

## Features

✅ **Automatic Integration**: Database views are added automatically when channels are processed  
✅ **Filtered Views**: Each view shows only videos from the specific channel  
✅ **Multiple Approaches**: Uses both linked databases and custom video lists for maximum compatibility  
✅ **Smart Detection**: Avoids creating duplicate views  
✅ **Filter Instructions**: Provides clear instructions for manual filtering if needed

## Quick Setup

### Option 1: Setup All Channels (Recommended)

Run this command to add database views to all your channel pages:

```bash
python setup_channel_database_views.py
```

### Option 2: Setup Specific Channel

To add a database view for just one channel:

```bash
python setup_channel_database_views.py --channel "@NateBJones"
```

## What Gets Created

For each channel page, the system adds:

1. **Heading**: "📺 Videos from [Channel Name]"
2. **Database View**: A filtered view of your Knowledge Hub database
3. **Instructions**: Clear guidance on how to set up the filter
4. **Video List**: If linked database doesn't work, a custom list of videos

## How It Works

### Architecture

```
YouTube Channel Page
├── Channel Info (existing)
├── 📺 Videos from [Channel Name] ← NEW
│   ├── Knowledge Hub Database View ← NEW
│   └── Filter Instructions ← NEW
└── Other content (existing)
```

### Integration Points

1. **YouTube Channel Processor**: Automatically adds views when processing channels
2. **Enhanced Channel Processor**: Dedicated service for managing database views  
3. **Notion MCP Client**: Enhanced with database view creation capabilities

## Configuration

### Environment Variables

```bash
# Required
NOTION_TOKEN=your_notion_api_token

# Optional (will use defaults if not set)
NOTION_KNOWLEDGE_DATABASE_ID=your_knowledge_hub_db_id
NOTION_CHANNELS_DATABASE_ID=your_channels_db_id
```

### Database IDs

The system uses these default database IDs:
- **Knowledge Hub**: `20bec31c-9de2-814e-80db-d13d0c27d869`
- **YouTube Channels**: `203ec31c-9de2-8079-ae4e-ed754d474888`

## Usage Examples

### Manual Setup

```python
from src.integrations.enhanced_channel_processor import EnhancedChannelProcessor
from src.integrations.notion_mcp_client import NotionMCPClient

# Initialize
notion_client = NotionMCPClient(token)
processor = EnhancedChannelProcessor(notion_client, knowledge_db_id)

# Add view to specific channel
await processor.add_database_view_for_specific_channel("@NateBJones")

# Process all channels
result = await processor.process_all_channels_for_database_views()
```

### Automatic Integration

The database views are automatically created when you process channels:

```python
from src.processors.youtube_channel_processor import YouTubeChannelProcessor

# Initialize processor (now includes database view manager)
processor = YouTubeChannelProcessor(notion_token, config)

# Process channels - database views added automatically
result = await processor.process_marked_channels()
```

## Filter Setup

After the database view is created, you need to set up the filter:

1. Click the **"Filter"** button in the database view
2. Add a new filter:
   - **Property**: Channel
   - **Condition**: Contains
   - **Value**: [channel name without @]
3. The view will automatically update to show only videos from that channel

### Example Filter

For channel `@NateBJones`:
- Property: `Channel`
- Condition: `Contains`  
- Value: `NateBJones`

## Troubleshooting

### Common Issues

**Database view not appearing:**
- Check that your Notion token has access to both databases
- Verify the database IDs are correct
- Ensure the channel page exists and is accessible

**Filter not working:**
- Make sure the Channel field in Knowledge Hub contains the channel name
- Use the exact channel name (without @) in the filter
- Check that videos have been properly processed with channel information

**Permission errors:**
- Ensure your Notion integration has access to both databases
- Check that the integration can edit the channel pages

### Debug Commands

Check if views already exist:
```python
await notion_client.has_linked_database(page_id, knowledge_db_id)
```

Test connection:
```python
success = await notion_client.test_connection()
```

## API Reference

### ChannelDatabaseViewManager

Main class for managing database views on channel pages.

```python
class ChannelDatabaseViewManager:
    async def add_database_view_to_channel(page_id: str, channel_name: str) -> bool
    async def create_filtered_database_view(page_id: str, channel_name: str) -> bool
    async def update_all_channel_views() -> Dict[str, Any]
```

### EnhancedChannelProcessor

Simplified interface using the Notion MCP client.

```python
class EnhancedChannelProcessor:
    async def add_filtered_database_view_to_channel(page_id: str, channel_name: str) -> bool
    async def process_all_channels_for_database_views() -> Dict[str, Any]
    async def add_database_view_for_specific_channel(channel_name: str) -> bool
```

### NotionMCPClient Extensions

New methods added to support database views.

```python
async def create_linked_database_block(page_id: str, database_id: str, heading_text: str = None) -> bool
async def get_page_blocks(page_id: str) -> List[Dict[str, Any]]
async def has_linked_database(page_id: str, database_id: str) -> bool
```

## Implementation Details

### Notion API Limitations

The Notion API doesn't support creating pre-filtered database views programmatically. The system works around this by:

1. Creating a linked database block
2. Adding filter instructions for manual setup
3. Providing alternative custom video lists when needed

### Error Handling

The system includes comprehensive error handling:
- Graceful degradation when database views can't be created
- Automatic retry mechanisms
- Clear error messages and solutions

### Performance Considerations

- Uses batch processing for multiple channels
- Includes rate limiting to avoid API limits
- Caches checks to avoid duplicate view creation

## Future Enhancements

Potential improvements being considered:

1. **Smart Filtering**: Automatically detect channel name variations
2. **View Customization**: Allow different view layouts and sorting
3. **Real-time Updates**: Automatically refresh views when new videos are added
4. **Bulk Operations**: More efficient processing for large numbers of channels

## Support

If you encounter issues:

1. Check the [troubleshooting section](#troubleshooting)
2. Review the logs for detailed error messages
3. Verify your Notion integration permissions
4. Test with a single channel first

For additional help, check the main project documentation or create an issue with:
- Error messages from logs
- Channel name and page ID
- Database IDs being used
- Steps to reproduce the issue