import streamlit as st
import json
import os
from pathlib import Path
from datetime import datetime, timedelta

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


def format_date_for_slack(date_obj, format_type, is_today=False, is_yesterday=False):
    """Format date according to the selected format type."""
    # Handle special cases for "today" and "yesterday" first
    if is_today:
        return "today"
    if is_yesterday:
        return "yesterday"
    
    # If date is None or empty, return None (won't be added to query)
    if date_obj is None:
        return None
    
    if format_type == "Full Date":
        return date_obj.strftime("%Y-%m-%d")
    elif format_type == "Month":
        # Format as "January" with full month name only
        month_names = ["January", "February", "March", "April", "May", "June",
                      "July", "August", "September", "October", "November", "December"]
        month_name = month_names[date_obj.month - 1]
        return month_name
    elif format_type == "Year":
        return date_obj.strftime("%Y")
    else:
        return date_obj.strftime("%Y-%m-%d")


def build_query(channel, from_user, file_type, date_enabled, use_during, during_date, during_date_format, during_is_today, during_is_yesterday, start_date, start_date_format, start_is_today, start_is_yesterday, end_date, end_date_format, end_is_today, end_is_yesterday, keywords):
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
        if use_during:
            # Check if today/yesterday is selected, or if during_date is set
            if during_is_today or during_is_yesterday or during_date:
                date_str = format_date_for_slack(during_date, during_date_format, during_is_today, during_is_yesterday)
                if date_str:  # Only add if date_str is not None
                    query_parts.append(f"during:{date_str}")
        else:
            if start_date or start_is_today or start_is_yesterday:
                date_str = format_date_for_slack(start_date, start_date_format, start_is_today, start_is_yesterday)
                if date_str:  # Only add if date_str is not None
                    query_parts.append(f"after:{date_str}")
            
            if end_date or end_is_today or end_is_yesterday:
                date_str = format_date_for_slack(end_date, end_date_format, end_is_today, end_is_yesterday)
                if date_str:  # Only add if date_str is not None
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
    
    # Initialize date format preferences
    if 'use_during' not in st.session_state:
        st.session_state.use_during = False
    if 'during_date_format' not in st.session_state:
        st.session_state.during_date_format = "Full Date"
    if 'start_date_format' not in st.session_state:
        st.session_state.start_date_format = "Full Date"
    if 'end_date_format' not in st.session_state:
        st.session_state.end_date_format = "Full Date"
    
    # During filter toggle
    use_during = st.checkbox("Use 'during' filter (single date)", value=st.session_state.use_during, key="use_during_checkbox")
    st.session_state.use_during = use_during
    
    if use_during:
        # During filter section
        st.markdown("**During Date**")
        
        # Initialize flags
        if 'during_is_today' not in st.session_state:
            st.session_state.during_is_today = False
        if 'during_is_yesterday' not in st.session_state:
            st.session_state.during_is_yesterday = False
        if 'during_date' not in st.session_state:
            st.session_state.during_date = datetime.now().date()
        
        # Quick date options
        quick_date_col1, quick_date_col2, quick_date_col3 = st.columns(3)
        with quick_date_col1:
            use_today = st.button("Today", key="during_today_btn", use_container_width=True)
        with quick_date_col2:
            use_yesterday = st.button("Yesterday", key="during_yesterday_btn", use_container_width=True)
        with quick_date_col3:
            reset_during = st.button("Reset", key="reset_during_btn", use_container_width=True)
            # Style reset button red
            st.markdown("""
                <style>
                    button[key="reset_during_btn"] {
                        background-color: #ff4444 !important;
                        color: white !important;
                    }
                    button[key="reset_during_btn"]:hover {
                        background-color: #cc0000 !important;
                    }
                </style>
            """, unsafe_allow_html=True)
        
        # Handle reset button
        if reset_during:
            st.session_state.during_is_today = False
            st.session_state.during_is_yesterday = False
            st.session_state.during_date = None
            st.session_state.during_year_only = ""
            st.session_state.during_month_selected = ""
            st.rerun()
        
        # Handle quick date buttons
        if use_today:
            st.session_state.during_is_today = True
            st.session_state.during_is_yesterday = False
            st.rerun()
        if use_yesterday:
            st.session_state.during_is_today = False
            st.session_state.during_is_yesterday = True
            st.rerun()
        
        during_date_format = st.selectbox(
            "Date format",
            options=["Full Date", "Month", "Year"],
            index=0 if st.session_state.during_date_format == "Full Date" else (1 if st.session_state.during_date_format == "Month" else 2),
            key="during_date_format_select",
            help="Choose how to format the date in the query (ignored if Today/Yesterday is selected)"
        )
        st.session_state.during_date_format = during_date_format
        
        # If today/yesterday is selected, don't show date inputs
        if not st.session_state.during_is_today and not st.session_state.during_is_yesterday:
            if during_date_format == "Full Date":
                during_date = st.date_input(
                    "Date",
                    value=st.session_state.during_date,
                    help="Show messages during this date",
                    key="during_date"
                )
                # Note: st.session_state.during_date is automatically managed by the widget
            elif during_date_format == "Month":
                months = [""] + ["January", "February", "March", "April", "May", "June",
                         "July", "August", "September", "October", "November", "December"]
                if 'during_month_selected' not in st.session_state:
                    st.session_state.during_month_selected = ""
                # Ensure the value is in the list, default to empty string
                if st.session_state.during_month_selected not in months:
                    st.session_state.during_month_selected = ""
                month_index = months.index(st.session_state.during_month_selected)
                
                selected_month_name = st.selectbox(
                    "Month",
                    options=months,
                    index=month_index,
                    key="during_month_select"
                )
                st.session_state.during_month_selected = selected_month_name
                if selected_month_name and selected_month_name != "":
                    selected_month_idx = months.index(selected_month_name)
                    current_year = datetime.now().year
                    during_date = datetime(current_year, selected_month_idx, 1).date()
                else:
                    during_date = None
            else:  # Year
                current_year = datetime.now().year
                years = [""] + list(range(current_year - 20, current_year + 21))
                if 'during_year_only' not in st.session_state:
                    st.session_state.during_year_only = ""
                # Ensure the value is in the list, default to empty string (index 0)
                current_value = st.session_state.during_year_only
                if current_value == "" or current_value in years:
                    year_index = years.index(current_value) if current_value != "" else 0
                else:
                    st.session_state.during_year_only = ""
                    year_index = 0
                selected_year = st.selectbox(
                    "Year",
                    options=years,
                    index=year_index,
                    key="during_year_only_select"
                )
                st.session_state.during_year_only = selected_year
                if selected_year and selected_year != "":
                    during_date = datetime(selected_year, 1, 1).date()
                else:
                    during_date = None
        else:
            during_date = datetime.now().date()  # Dummy value, won't be used
        
        # Assign during flags from session state
        during_is_today = st.session_state.during_is_today
        during_is_yesterday = st.session_state.during_is_yesterday
        
        # Set start/end to None when using during
        start_date = None
        start_date_format = "Full Date"
        start_is_today = False
        start_is_yesterday = False
        end_date = None
        end_date_format = "Full Date"
        end_is_today = False
        end_is_yesterday = False
    else:
        # Regular start/end date range
        during_date = None
        during_date_format = "Full Date"
        during_is_today = False
        during_is_yesterday = False
    
        # Initialize month/year selections
        if 'start_month' not in st.session_state:
            st.session_state.start_month = datetime.now().month
        if 'start_year' not in st.session_state:
            st.session_state.start_year = datetime.now().year
        if 'end_month' not in st.session_state:
            st.session_state.end_month = datetime.now().month
        if 'end_year' not in st.session_state:
            st.session_state.end_year = datetime.now().year
        if 'start_year_only' not in st.session_state:
            st.session_state.start_year_only = datetime.now().year
        if 'end_year_only' not in st.session_state:
            st.session_state.end_year_only = datetime.now().year
        
        # Initialize flags
        if 'start_is_today' not in st.session_state:
            st.session_state.start_is_today = False
        if 'start_is_yesterday' not in st.session_state:
            st.session_state.start_is_yesterday = False
        if 'end_is_today' not in st.session_state:
            st.session_state.end_is_today = False
        if 'end_is_yesterday' not in st.session_state:
            st.session_state.end_is_yesterday = False
        
        date_col1, date_col2 = st.columns(2)
        
        with date_col1:
            st.markdown("**Start Date**")
            
            # Quick date options
            quick_date_col1, quick_date_col2, quick_date_col3 = st.columns(3)
            with quick_date_col1:
                use_today_start = st.button("Today", key="start_today_btn", use_container_width=True)
            with quick_date_col2:
                use_yesterday_start = st.button("Yesterday", key="start_yesterday_btn", use_container_width=True)
            with quick_date_col3:
                reset_start = st.button("Reset", key="reset_start_btn", use_container_width=True)
                # Style reset button red
                st.markdown("""
                    <style>
                        button[key="reset_start_btn"] {
                            background-color: #ff4444 !important;
                            color: white !important;
                        }
                        button[key="reset_start_btn"]:hover {
                            background-color: #cc0000 !important;
                        }
                    </style>
                """, unsafe_allow_html=True)
            
            # Handle reset button
            if reset_start:
                st.session_state.start_is_today = False
                st.session_state.start_is_yesterday = False
                st.session_state.start_date_value = None
                st.session_state.start_month_selected = ""
                st.session_state.start_year = ""
                st.session_state.start_year_only = ""
                st.rerun()
            
            # Initialize start date
            if 'start_date_value' not in st.session_state:
                st.session_state.start_date_value = datetime.now().date()
            
            # Handle quick date buttons
            if use_today_start:
                st.session_state.start_is_today = True
                st.session_state.start_is_yesterday = False
                st.rerun()
            if use_yesterday_start:
                st.session_state.start_is_today = False
                st.session_state.start_is_yesterday = True
                st.rerun()
            
            start_date_format = st.selectbox(
                "Start date format",
                options=["Full Date", "Month", "Year"],
                index=0 if st.session_state.start_date_format == "Full Date" else (1 if st.session_state.start_date_format == "Month" else 2),
                key="start_date_format_select",
                help="Choose how to format the start date in the query (ignored if Today/Yesterday is selected)"
            )
            st.session_state.start_date_format = start_date_format
            
            # If today/yesterday is selected, don't show date inputs
            if not st.session_state.start_is_today and not st.session_state.start_is_yesterday:
                if start_date_format == "Full Date":
                    # Initialize start_date_value if not exists
                    if 'start_date_value' not in st.session_state:
                        st.session_state.start_date_value = datetime.now().date()
                    start_date = st.date_input(
                        "From Date",
                        value=st.session_state.start_date_value,
                        help="Show messages after this date",
                        key="start_date"
                    )
                    # Note: st.session_state.start_date is automatically managed by the widget
                    # Use the widget's return value, which is the same as st.session_state.start_date
                    # Update start_date_value for when widget is not shown
                    st.session_state.start_date_value = start_date
                elif start_date_format == "Month":
                    months = [""] + ["January", "February", "March", "April", "May", "June",
                             "July", "August", "September", "October", "November", "December"]
                    if 'start_month_selected' not in st.session_state:
                        st.session_state.start_month_selected = ""
                    # Ensure the value is in the list, default to empty string
                    if st.session_state.start_month_selected not in months:
                        st.session_state.start_month_selected = ""
                    month_index = months.index(st.session_state.start_month_selected)
                    
                    selected_month_name = st.selectbox(
                        "Month",
                        options=months,
                        index=month_index,
                        key="start_month_select"
                    )
                    st.session_state.start_month_selected = selected_month_name
                    if selected_month_name and selected_month_name != "":
                        selected_month_idx = months.index(selected_month_name)
                        current_year = datetime.now().year
                        start_date = datetime(current_year, selected_month_idx, 1).date()
                    else:
                        start_date = None
                else:  # Year
                    current_year = datetime.now().year
                    years = [""] + list(range(current_year - 20, current_year + 21))
                    if 'start_year_only' not in st.session_state:
                        st.session_state.start_year_only = ""
                    # Ensure the value is in the list, default to empty string (index 0)
                    current_value = st.session_state.start_year_only
                    if current_value == "" or current_value in years:
                        year_index = years.index(current_value) if current_value != "" else 0
                    else:
                        st.session_state.start_year_only = ""
                        year_index = 0
                    selected_year = st.selectbox(
                        "Year",
                        options=years,
                        index=year_index,
                        key="start_year_only_select"
                    )
                    st.session_state.start_year_only = selected_year
                    if selected_year and selected_year != "":
                        start_date = datetime(selected_year, 1, 1).date()
                    else:
                        start_date = None
            else:
                start_date = datetime.now().date()  # Dummy value, won't be used
            
            start_is_today = st.session_state.start_is_today
            start_is_yesterday = st.session_state.start_is_yesterday
        
        with date_col2:
            st.markdown("**End Date**")
            
            # Quick date options
            quick_date_col1, quick_date_col2, quick_date_col3 = st.columns(3)
            with quick_date_col1:
                use_today_end = st.button("Today", key="end_today_btn", use_container_width=True)
            with quick_date_col2:
                use_yesterday_end = st.button("Yesterday", key="end_yesterday_btn", use_container_width=True)
            with quick_date_col3:
                reset_end = st.button("Reset", key="reset_end_btn", use_container_width=True)
                # Style reset button red
                st.markdown("""
                    <style>
                        button[key="reset_end_btn"] {
                            background-color: #ff4444 !important;
                            color: white !important;
                        }
                        button[key="reset_end_btn"]:hover {
                            background-color: #cc0000 !important;
                        }
                    </style>
                """, unsafe_allow_html=True)
            
            # Handle reset button
            if reset_end:
                st.session_state.end_is_today = False
                st.session_state.end_is_yesterday = False
                st.session_state.end_date_value = None
                st.session_state.end_month_selected = ""
                st.session_state.end_year = ""
                st.session_state.end_year_only = ""
                st.rerun()
            
            # Initialize end date
            if 'end_date_value' not in st.session_state:
                st.session_state.end_date_value = None
            
            # Handle quick date buttons
            if use_today_end:
                st.session_state.end_is_today = True
                st.session_state.end_is_yesterday = False
                st.rerun()
            if use_yesterday_end:
                st.session_state.end_is_today = False
                st.session_state.end_is_yesterday = True
                st.rerun()
            
            end_date_format = st.selectbox(
                "End date format",
                options=["Full Date", "Month", "Year"],
                index=0 if st.session_state.end_date_format == "Full Date" else (1 if st.session_state.end_date_format == "Month" else 2),
                key="end_date_format_select",
                help="Choose how to format the end date in the query (ignored if Today/Yesterday is selected)"
            )
            st.session_state.end_date_format = end_date_format
            
            # If today/yesterday is selected, don't show date inputs
            if not st.session_state.end_is_today and not st.session_state.end_is_yesterday:
                if end_date_format == "Full Date":
                    # Initialize end_date_value if not exists
                    if 'end_date_value' not in st.session_state:
                        st.session_state.end_date_value = None
                    end_date = st.date_input(
                        "To Date",
                        value=st.session_state.end_date_value,
                        help="Show messages before this date (optional)",
                        key="end_date"
                    )
                    # Note: st.session_state.end_date is automatically managed by the widget
                    # Use the widget's return value, which is the same as st.session_state.end_date
                    # Update end_date_value for when widget is not shown
                    st.session_state.end_date_value = end_date
                elif end_date_format == "Month":
                    months = [""] + ["January", "February", "March", "April", "May", "June",
                             "July", "August", "September", "October", "November", "December"]
                    if 'end_month_selected' not in st.session_state:
                        st.session_state.end_month_selected = ""
                    # Ensure the value is in the list, default to empty string
                    if st.session_state.end_month_selected not in months:
                        st.session_state.end_month_selected = ""
                    month_index = months.index(st.session_state.end_month_selected)
                    
                    selected_month_name = st.selectbox(
                        "Month",
                        options=months,
                        index=month_index,
                        key="end_month_select"
                    )
                    st.session_state.end_month_selected = selected_month_name
                    if selected_month_name and selected_month_name != "":
                        selected_month_idx = months.index(selected_month_name)
                        current_year = datetime.now().year
                        end_date = datetime(current_year, selected_month_idx, 1).date()
                    else:
                        end_date = None
                else:  # Year
                    current_year = datetime.now().year
                    years = [""] + list(range(current_year - 20, current_year + 21))
                    if 'end_year_only' not in st.session_state:
                        st.session_state.end_year_only = ""
                    # Ensure the value is in the list, default to empty string (index 0)
                    current_value = st.session_state.end_year_only
                    if current_value == "" or current_value in years:
                        year_index = years.index(current_value) if current_value != "" else 0
                    else:
                        st.session_state.end_year_only = ""
                        year_index = 0
                    selected_year = st.selectbox(
                        "Year",
                        options=years,
                        index=year_index,
                        key="end_year_only_select"
                    )
                    st.session_state.end_year_only = selected_year
                    if selected_year and selected_year != "":
                        end_date = datetime(selected_year, 1, 1).date()
                    else:
                        end_date = None
            else:
                end_date = datetime.now().date()  # Dummy value, won't be used
            
            end_is_today = st.session_state.end_is_today
            end_is_yesterday = st.session_state.end_is_yesterday
else:
    start_date = None
    start_date_format = "Full Date"
    end_date = None
    end_date_format = "Full Date"
    use_during = False
    during_date = None
    during_date_format = "Full Date"

# Query Output Section
st.header("📝 Generated Query")

query = build_query(
    selected_channel,
    from_user,
    file_type,
    date_enabled,
    use_during if date_enabled else False,
    during_date if date_enabled else None,
    during_date_format if date_enabled else "Full Date",
    during_is_today if date_enabled else False,
    during_is_yesterday if date_enabled else False,
    start_date if date_enabled else None,
    start_date_format if date_enabled else "Full Date",
    start_is_today if date_enabled else False,
    start_is_yesterday if date_enabled else False,
    end_date if date_enabled else None,
    end_date_format if date_enabled else "Full Date",
    end_is_today if date_enabled else False,
    end_is_yesterday if date_enabled else False,
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

# Initialize session state for channel add notification
if 'channel_add_success' not in st.session_state:
    st.session_state.channel_add_success = None
if 'channel_add_error' not in st.session_state:
    st.session_state.channel_add_error = None

# Display notifications if they exist
if st.session_state.channel_add_success:
    st.success(st.session_state.channel_add_success)
    st.toast(st.session_state.channel_add_success, icon="✅")
    # Clear after displaying
    st.session_state.channel_add_success = None

if st.session_state.channel_add_error:
    st.error(st.session_state.channel_add_error)
    # Clear after displaying
    st.session_state.channel_add_error = None

# Use form to handle Enter key submission
with st.form("add_channel_form", clear_on_submit=True):
    new_channel = st.text_input(
        "Add a new channel",
        placeholder="e.g., general, deployments, random",
        key="new_channel_input"
    )
    
    submitted = st.form_submit_button("Add Channel", type="primary", use_container_width=True)
    
    if submitted:
        if new_channel:
            success, message = save_channel(new_channel)
            if success:
                # Update cache immediately
                st.session_state.channels_cache = load_channels()
                channel_name = new_channel.strip()
                if channel_name.startswith("#"):
                    channel_name = channel_name[1:].strip()
                st.session_state.channel_add_success = f"✅ Channel '{channel_name}' added successfully!"
                st.rerun()
            else:
                st.session_state.channel_add_error = message
                st.rerun()
        else:
            st.session_state.channel_add_error = "Please enter a channel name"
            st.rerun()

st.markdown("💡 [Manage all channels →](pages/Channels.py)")

