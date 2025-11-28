# 🔍 Slack Search Query Generator

A Streamlit web application that helps you build complex Slack search queries without needing API access. Generate precise search queries with an intuitive interface and copy them directly into Slack's search bar.

## Features

- **Channel Filtering**: Select from a saved list of Slack channels or add new ones
- **User Filtering**: Search for messages from specific users
- **File Type Filtering**: Filter by PDF, Image, Snippet, Google Docs, or Spreadsheets
- **Advanced Date Range Filtering**:
  - Single date filtering with "during" operator
  - Date range filtering with "after" and "before" operators
  - Support for "today" and "yesterday" quick selections
  - Multiple date formats: Full Date, Month, or Year
- **Keyword Search**: Add custom keywords to your search query
- **Channel Management**: Dedicated page to add, edit, and delete channels from your list
- **Real-time Query Generation**: See your Slack search query update as you modify filters

## Installation

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

### Local Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd slack-search-generator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run Search_Query_Builder.py
```

The application will be available at `http://localhost:8501`

## Docker Deployment

### Using Docker Compose (Recommended)

1. Build and start the container:
```bash
docker-compose up -d
```

2. Access the application at `http://localhost:8501`

3. Stop the container:
```bash
docker-compose down
```

### Using Docker Directly

1. Build the Docker image:
```bash
docker build -t slack-search-generator .
```

2. Run the container:
```bash
docker run -p 8501:8501 -v $(pwd)/data:/app/data slack-search-generator
```

The `-v` flag mounts the local `data` directory to persist your channel list across container restarts.

## Usage

### Building a Search Query

1. **Select a Channel**: Choose a channel from your saved list (or leave empty to search all channels)
2. **Filter by User**: Enter a username (with or without @ prefix)
3. **Filter by File Type**: Select a file type if you want to search for specific file attachments
4. **Add Keywords**: Enter any keywords you want to search for
5. **Set Date Range** (optional):
   - Enable the date range filter checkbox
   - Choose between "during" (single date) or "after/before" (date range)
   - Select date format: Full Date, Month, or Year
   - Use quick buttons for "Today" or "Yesterday"
6. **Copy the Generated Query**: The query will appear in the output section - copy it and paste into Slack's search bar

### Managing Channels

1. Navigate to the Channel Management page using the link at the bottom of the main page
2. **Add a Channel**: Enter the channel name (without #) and click "Add Channel"
3. **Edit a Channel**: Click the "Edit" button next to a channel, modify the name, and save
4. **Delete a Channel**: Click the "Delete" button and confirm the deletion

## Project Structure

```
slack-search-generator/
├── Search_Query_Builder.py    # Main Streamlit application
├── pages/
│   └── Channels.py            # Channel management page
├── data/
│   └── channels.json          # Stored channel list (auto-generated)
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker image configuration
├── docker-compose.yml         # Docker Compose configuration
├── LICENSE                    # License file
└── README.md                  # This file
```

## How It Works

The application generates Slack search queries using Slack's native search syntax:

- `in:#channel` - Search within a specific channel
- `from:@user` - Search messages from a specific user
- `has:pdf`, `has:image`, etc. - Filter by file type
- `during:date`, `after:date`, `before:date` - Filter by date
- Keywords are added as-is to the query

All components are combined into a single query string that you can paste directly into Slack's search bar.

## Data Storage

Channel data is stored in `data/channels.json`. This file is automatically created when you add your first channel. The data directory is persisted when using Docker, so your channel list will be preserved across container restarts.

## Requirements

- `streamlit>=1.28.0`

## License

This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues, questions, or feature requests, please open an issue on the repository.

