import streamlit as st
import json
from pathlib import Path

# Configuration
DATA_DIR = Path("data")
CHANNELS_FILE = DATA_DIR / "channels.json"


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


# Page configuration
st.set_page_config(
    page_title="Channel Management",
    page_icon="📋",
    layout="wide"
)

st.title("📋 Channel Management")
st.markdown("View, add, edit, and delete your Slack channels")

# Initialize session state
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = {}
if 'delete_confirm' not in st.session_state:
    st.session_state.delete_confirm = None
if 'new_channel_name' not in st.session_state:
    st.session_state.new_channel_name = ""

# Load channels
channels = load_channels()

# Add New Channel Section
st.header("➕ Add New Channel")

col1, col2 = st.columns([3, 1])

with col1:
    new_channel_input = st.text_input(
        "Channel name",
        placeholder="e.g., general, deployments, random",
        key="add_channel_input",
        value=st.session_state.new_channel_name
    )

with col2:
    st.write("")  # Spacing
    add_button = st.button("Add Channel", type="primary", use_container_width=True)

if add_button:
    if new_channel_input:
        success, message = save_channel(new_channel_input)
        if success:
            # Invalidate main page cache if it exists
            if 'channels_cache' in st.session_state:
                st.session_state.channels_cache = load_channels()
            st.success(f"✅ {message}")
            st.toast(f"Channel '{new_channel_input.strip()}' has been added!", icon="✅")
            st.session_state.new_channel_name = ""
            st.rerun()
        else:
            st.error(message)
    else:
        st.warning("Please enter a channel name")

st.divider()

# Channels List Section
st.header("📝 Your Channels")

if not channels:
    st.info("👆 No channels yet. Add your first channel above!")
else:
    st.markdown(f"**Total channels: {len(channels)}**")
    
    # Create a container for each channel
    for idx, channel in enumerate(channels):
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                if idx in st.session_state.edit_mode:
                    # Edit mode
                    edited_name = st.text_input(
                        f"Editing: {channel}",
                        value=channel,
                        key=f"edit_{idx}",
                        label_visibility="collapsed"
                    )
                else:
                    # Display mode
                    st.markdown(f"**#{channel}**")
            
            with col2:
                if idx in st.session_state.edit_mode:
                    # Save button
                    if st.button("💾 Save", key=f"save_{idx}", use_container_width=True):
                        if edited_name and edited_name.strip():
                            success, message = update_channel(channel, edited_name.strip())
                            if success:
                                # Invalidate main page cache if it exists
                                if 'channels_cache' in st.session_state:
                                    st.session_state.channels_cache = load_channels()
                                st.success(f"✅ {message}")
                                st.toast(f"Channel updated to '{edited_name.strip()}'!", icon="✅")
                                del st.session_state.edit_mode[idx]
                                st.rerun()
                            else:
                                st.error(message)
                        else:
                            st.error("Channel name cannot be empty")
                else:
                    # Edit button
                    if st.button("✏️ Edit", key=f"edit_btn_{idx}", use_container_width=True):
                        st.session_state.edit_mode[idx] = True
                        st.rerun()
            
            with col3:
                if idx in st.session_state.edit_mode:
                    # Cancel button
                    if st.button("❌ Cancel", key=f"cancel_{idx}", use_container_width=True):
                        del st.session_state.edit_mode[idx]
                        st.rerun()
                else:
                    # Delete button
                    if st.session_state.delete_confirm == idx:
                        if st.button("🗑️ Confirm", key=f"confirm_delete_{idx}", use_container_width=True, type="primary"):
                            success, message = delete_channel(channel)
                            if success:
                                # Invalidate main page cache if it exists
                                if 'channels_cache' in st.session_state:
                                    st.session_state.channels_cache = load_channels()
                                st.success(f"✅ Channel '{channel}' deleted!")
                                st.toast(f"Channel '{channel}' has been deleted!", icon="✅")
                                st.session_state.delete_confirm = None
                                st.rerun()
                            else:
                                st.error(message)
                    else:
                        if st.button("🗑️ Delete", key=f"delete_{idx}", use_container_width=True):
                            st.session_state.delete_confirm = idx
                            st.rerun()
            
            with col4:
                if st.session_state.delete_confirm == idx:
                    if st.button("↩️ Cancel", key=f"cancel_delete_{idx}", use_container_width=True):
                        st.session_state.delete_confirm = None
                        st.rerun()
            
            if idx < len(channels) - 1:
                st.divider()

# Clear delete confirmation if channel was deleted
if st.session_state.delete_confirm is not None:
    if st.session_state.delete_confirm >= len(channels):
        st.session_state.delete_confirm = None

st.markdown("---")
st.markdown("🔍 [Back to Query Builder →](/)")

