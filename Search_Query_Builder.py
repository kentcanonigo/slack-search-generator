import streamlit as st
import json
import os
from pathlib import Path
from datetime import datetime, time

# Configuration
DATA_DIR = Path("data")
CHANNELS_FILE = DATA_DIR / "channels.json"

# File type to Slack operator mapping
FILE_TYPE_MAPPING = {
    "PDF": "has:pdf",
    "Image": "has:image",
    "Snippet": "has:snippet",
    "GDoc": "has:gdoc",
    "Spreadsheet": "has:spreadsheet",
}


def ensure_data_directory():
    """Ensure the data directory exists."""
    DATA_DIR.mkdir(exist_ok=True)


def load_channels():
    """Load channels from JSON file. Returns empty list if file doesn't exist."""
    ensure_data_directory()
    if CHANNELS_FILE.exists():
        try:
            with open(CHANNELS_FILE, "r") as f:
                channels = json.load(f)
                return sorted(channels) if isinstance(channels, list) else []
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_channels(channels_list):
    """Save channels list to JSON file."""
    ensure_data_directory()
    try:
        with open(CHANNELS_FILE, "w") as f:
            json.dump(sorted(channels_list), f, indent=2)
        return True, "Channels saved successfully!"
    except IOError:
        return False, "Error saving channels to file"


def save_channel(channel):
    """Append a new channel to the JSON file."""
    ensure_data_directory()
    channels = load_channels()
    
    # Trim whitespace and remove leading # if present
    channel = channel.strip()
    if channel.startswith("#"):
        channel = channel[1:].strip()
    
    if not channel:
        return False, "Channel name cannot be empty"
    
    if channel in channels:
        return False, f"Channel '{channel}' already exists"
    
    channels.append(channel)
    channels = sorted(channels)
    
    return save_channels(channels)


def delete_channel(channel):
    """Delete a channel from the JSON file."""
    channels = load_channels()
    
    if channel not in channels:
        return False, f"Channel '{channel}' not found"
    
    channels.remove(channel)
    
    return save_channels(channels)


def update_channel(old_channel, new_channel):
    """Update a channel name in the JSON file."""
    channels = load_channels()
    
    if old_channel not in channels:
        return False, f"Channel '{old_channel}' not found"
    
    # Trim whitespace and remove leading # if present
    new_channel = new_channel.strip()
    if new_channel.startswith("#"):
        new_channel = new_channel[1:].strip()
    
    if not new_channel:
        return False, "Channel name cannot be empty"
    
    if new_channel in channels and new_channel != old_channel:
        return False, f"Channel '{new_channel}' already exists"
    
    # Update the channel
    index = channels.index(old_channel)
    channels[index] = new_channel
    channels = sorted(channels)
    
    return save_channels(channels)


def build_query(channel, from_user, file_type, date_enabled, start_date, start_time, end_date, end_time, keywords):
    """Construct Slack search query string from form inputs."""
    query_parts = []
    
    if channel:
        query_parts.append(f"in:#{channel}")
    
    if from_user:
        user = from_user.strip()
        if user and not user.startswith("@"):
            user = f"@{user}"
        query_parts.append(f"from:{user}")
    
    if file_type and file_type in FILE_TYPE_MAPPING:
        query_parts.append(FILE_TYPE_MAPPING[file_type])
    
    if date_enabled:
        if start_date:
            # Format date with time if provided
            if start_time:
                datetime_str = datetime.combine(start_date, start_time).strftime("%Y-%m-%d %H:%M")
                query_parts.append(f"after:{datetime_str}")
            else:
                date_str = start_date.strftime("%Y-%m-%d")
                query_parts.append(f"after:{date_str}")
        
        if end_date:
            # Format date with time if provided
            if end_time:
                datetime_str = datetime.combine(end_date, end_time).strftime("%Y-%m-%d %H:%M")
                query_parts.append(f"before:{datetime_str}")
            else:
                date_str = end_date.strftime("%Y-%m-%d")
                query_parts.append(f"before:{date_str}")
    
    if keywords:
        keywords_clean = keywords.strip()
        if keywords_clean:
            query_parts.append(keywords_clean)
    
    return " ".join(query_parts)


# Page configuration
st.set_page_config(
    page_title="Search Query Builder",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Slack Search Query Wizard")
st.markdown("Generate complex Slack search queries without API access")

# Initialize session state for channels cache
# Refresh cache on each run to ensure it's up to date
st.session_state.channels_cache = load_channels()

# Load channels from cache
channels = st.session_state.channels_cache

# Search Query Builder Section
st.header("🔍 Search Query Builder")

# Use cached channels (already updated if a new one was added)
channels = st.session_state.channels_cache

col1, col2 = st.columns(2)

with col1:
    selected_channel = st.selectbox(
        "Channel",
        options=[""] + channels,
        help="Select a channel from your saved list"
    )
    
    from_user = st.text_input(
        "From User",
        placeholder="e.g., bob or @bob",
        help="Enter username with or without @"
    )
    
    file_type = st.selectbox(
        "File Type",
        options=["", "PDF", "Image", "Snippet", "GDoc", "Spreadsheet"],
        help="Filter by file type"
    )

with col2:
    keywords = st.text_input(
        "Keywords",
        placeholder="e.g., deployment, error, meeting",
        help="Search for specific keywords"
    )
    
    date_enabled = st.checkbox("Enable date range filter", value=False)

# Date Range Section (only show if enabled)
if date_enabled:
    st.subheader("📅 Date Range")
    date_col1, date_col2 = st.columns(2)
    
    with date_col1:
        st.markdown("**Start Date**")
        start_date = st.date_input(
            "From Date",
            value=datetime.now().date(),
            help="Show messages after this date",
            key="start_date"
        )
        use_start_time = st.checkbox("Include start time", key="use_start_time", value=False)
        start_time = None
        if use_start_time:
            start_time = st.time_input(
                "From Time",
                value=time(0, 0),
                help="Specify start time",
                key="start_time"
            )
    
    with date_col2:
        st.markdown("**End Date**")
        end_date = st.date_input(
            "To Date",
            value=None,
            help="Show messages before this date (optional)",
            key="end_date"
        )
        use_end_time = st.checkbox("Include end time", key="use_end_time", value=False)
        end_time = None
        if use_end_time and end_date:
            end_time = st.time_input(
                "To Time",
                value=time(23, 59),
                help="Specify end time",
                key="end_time"
            )
else:
    start_date = None
    start_time = None
    end_date = None
    end_time = None

# Query Output Section
st.header("📝 Generated Query")

query = build_query(
    selected_channel,
    from_user,
    file_type,
    date_enabled,
    start_date,
    start_time,
    end_date,
    end_time,
    keywords
)

if query:
    st.code(query, language="text")
    st.info("💡 Copy the query above and paste it into Slack's search bar")
else:
    st.info("👆 Fill in the fields above to generate a search query")

# Channel Management Section (moved to bottom)
st.divider()
st.header("📋 Channel Management")

col1, col2 = st.columns([3, 1])

with col1:
    new_channel = st.text_input(
        "Add a new channel",
        placeholder="e.g., general, deployments, random",
        key="new_channel_input"
    )

with col2:
    st.write("")  # Spacing
    add_button = st.button("Add Channel", type="primary")

if add_button:
    if new_channel:
        success, message = save_channel(new_channel)
        if success:
            # Update cache immediately
            st.session_state.channels_cache = load_channels()
            st.success(f"✅ {message}")
            st.toast(f"Channel '{new_channel.strip()}' has been added!", icon="✅")
            st.rerun()
        else:
            st.error(message)
    else:
        st.warning("Please enter a channel name")

st.markdown("💡 [Manage all channels →](pages/Channels.py)")

