# ChatGPT with File Processing

A Streamlit-based chat application that integrates OpenAI's API with powerful file processing capabilities. Upload multiple text files, chat with AI about their contents, and automatically update files based on AI responses.

## Features

### 🤖 Multiple AI Models
- **GPT-3.5 Turbo**: Fastest and most cost-effective
- **GPT-4o / GPT-4o Mini**: Advanced multimodal capabilities
- **GPT-5 Series**: Latest models including Mini, Nano, and Codex variants
- **o1 Series**: Specialized reasoning models for complex tasks

### 🔍 Web Search Integration
- Enable real-time web search using OpenAI's Responses API
- Get up-to-date information with sourced citations
- Works with most models (GPT-4o, GPT-5, etc.)

### 📁 File Processing
- **Upload Multiple Files**: Drag and drop or select multiple `.txt` files
- **Automatic Context Inclusion**: All uploaded files are automatically included in AI context
- **File Status Tracking**: See which files have been modified (✏️ indicator)
- **Individual Downloads**: Download each file separately after processing
- **Bulk Management**: Clear all files or remove individual files

### 🎯 Smart Question Answering
The app recognizes questions marked with `***` at the end of your text files and can:
- Answer questions without modifying files (view only mode)
- Update files with answers embedded in the content
- Handle multiple questions across multiple files simultaneously

### 💬 Conversation Management
- **Save Conversations**: Save chat history as `.txt` files to a folder
- **Load Conversations**: Resume previous conversations from saved files
- **Copy Conversations**: Export entire chat to clipboard
- **Persistent Storage**: Use IndexedDB slots (1-5) to save/load conversation states

## Installation

### Prerequisites
- Python 3.8+
- pip package manager

### Setup

1. **Clone or download this repository**

2. **Install required packages**:
```bash
pip install streamlit openai
```

3. **Run the application**:
```bash
streamlit run chat_5.py
```

4. **Open your browser**: The app should automatically open at `http://localhost:8501`

## Usage

### Getting Started

1. **Enter your OpenAI API Key** in the sidebar
   - Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)
   - The key is stored only in your session (not saved permanently)

2. **Select your preferred model** from the dropdown

3. **Upload text files** (optional) if you want to work with files

### Working with Files

#### Upload Files
- Click "Upload text files to work with" in the sidebar
- Select one or multiple `.txt` files
- Files are immediately loaded and included in AI context

#### View Only Mode - Answer Questions
To get answers without updating your files, use prompts like:
- "Please answer the questions that start with ***"
- "Answer all *** questions"
- "List answers to the questions in each file"

**Example**:
```
User: Please answer each question in each file that is formatted with *** before the question, it's at the end of each file

AI will respond with just the answers:

**file1.txt:**
*** How much profit per year by pharmaceutical companies?
ANSWER: [Detailed answer]

**file2.txt:**
*** What are the founding principles of Hamas?
ANSWER: [Detailed answer]
```

#### Update Files Mode - Save Answers to Files
To update your files with AI responses, use prompts with keywords like "write", "update", or "save":
- "Write answers to the *** questions in each file"
- "Update files with answers to *** questions"
- "Save answers to the *** questions in the files"

**The AI will respond with**:
```
--- FILE: file1.txt ---
[Full original content]

*** Your question here?
ANSWER: [Detailed answer]

--- FILE: file2.txt ---
[Full original content]

*** Another question?
ANSWER: [Another detailed answer]
```

Files with `--- FILE: filename.txt ---` markers will be automatically updated, and you'll see a success message with the ✏️ indicator.

#### Download Modified Files
- Click the **⬇️** button next to any file to download it
- Files marked with ✏️ have been modified by AI
- Download files before clearing them or closing the app

### Web Search Feature

1. **Enable Web Search**: Check the "🔍 Enable Web Search" box in the sidebar
2. **Ask current questions**: "What's the weather in NYC today?"
3. **View citations**: Expand the "🔍 Web Search Citations" section to see sources

**Note**: Web search uses the Responses API and works best with GPT-4o, GPT-5, and similar models.

### Conversation Management

#### Save Conversation
1. Specify a folder path (default: "conversations")
2. Enter a filename in "Save conversation as"
3. Click "Save Current Conversation"
4. Conversation is saved in the format:
   ```
   User: [message]

   Assistant: [response]
   ```

#### Load Conversation
1. Click "Process Folder" to scan for `.txt` files
2. Select a conversation file from the dropdown
3. Click "Load Conversation"
4. Previous conversation loads into the chat

#### Copy Conversation
1. Click "📋 Show Conversation Text"
2. Select all text (Ctrl+A / Cmd+A)
3. Copy (Ctrl+C / Cmd+C)
4. Click "❌ Hide" to close

## File Format for Questions

To use the automatic question answering feature, format your text files like this:

```
Your main content here...

More content...

*** How much profit per year by pharmaceutical companies, get the latest data that you have please?
*** What are the founding principles of Hamas?
*** What is the current population of Tokyo?
```

**Important**:
- Questions should be at the END of the file
- Each question should start with `***` (three asterisks)
- Put each question on its own line

## Tips and Best Practices

### Model Selection
- **Quick tasks**: Use GPT-3.5 Turbo or GPT-4o Mini (fastest, cheapest)
- **Complex reasoning**: Use o1 or GPT-5 (slower, more expensive, better quality)
- **File processing**: GPT-4o Mini works great for most file operations
- **Latest information**: Enable web search with GPT-4o or GPT-5

### Cost Optimization
- GPT-3.5 Turbo is ~30x cheaper than GPT-4o
- o1 models are ~3x more expensive than GPT-4o
- Web search adds tool call costs
- File context increases token usage (more files = higher cost)

### Working with Large Files
- The app includes all file contents in every message
- Large files or many files increase API costs
- Consider summarizing files first, then working with summaries
- Remove files you're done with to reduce context size

### Question Answering Workflow
1. Upload your files with `***` questions at the end
2. First ask: "Please answer the questions that start with ***" (view only)
3. Review the answers
4. If satisfied, ask: "Write answers to the *** questions in each file" (updates files)
5. Download the updated files

## Debug Features

### File Context Debug
When files are loaded, expand "🔍 Debug: Files included in context" to see:
- Total messages sent to API
- Number of files loaded
- Preview of system message with file contents

This helps verify files are being included correctly.

## Troubleshooting

### AI doesn't recognize my files
- Check the debug expander to confirm files are included
- Make sure web search is DISABLED (web search bypasses file context currently)
- Verify files uploaded successfully (check sidebar for file list)

### Questions aren't being answered
- Ensure questions start with `***` (three asterisks)
- Questions should be at the END of each file
- Try the example prompt: "Please answer each question in each file that is formatted with *** before the question, it's at the end of each file"

### File updates not working
- Use keywords like "write", "update", or "save" in your prompt
- Check that AI responded with `--- FILE: filename.txt ---` markers
- Verify filename in AI response matches uploaded filename exactly

### Web search not working
- Some models don't support Responses API yet
- Error "model not supported" means use a different model
- Try GPT-4o, GPT-4o Mini, or GPT-5

### Conversation not saving
- Ensure folder path exists (app will create if missing)
- Check filename ends with `.txt` (auto-added if missing)
- Verify you have write permissions to the folder

## API Costs

Approximate costs per 1K tokens (as of 2025):

| Model | Input | Output |
|-------|-------|--------|
| GPT-3.5 Turbo | $0.0005 | $0.0015 |
| GPT-4o Mini | $0.15 | $0.60 |
| GPT-4o | $2.50 | $10.00 |
| GPT-4 Turbo | $10.00 | $30.00 |
| o1 | $15.00 | $60.00 |

**Cost Estimation**:
- 1 page of text ≈ 500 tokens
- 3 files × 2 pages each = ~3,000 tokens per message
- Chat with 10 messages = ~30,000 tokens
- With GPT-4o Mini: ~$4.50

## Privacy & Security

- **API Key**: Stored only in session, never saved to disk
- **Files**: Kept in browser memory, never sent to external servers (except OpenAI API)
- **Conversations**: Saved locally only if you explicitly save them
- **No telemetry**: App doesn't track usage or send analytics

## Limitations

- Maximum file size depends on model context window (typically 128K tokens)
- Web search only works with compatible models via Responses API
- File updates require exact filename match (case-sensitive)
- No support for file formats other than `.txt`
- No built-in file preview (must download to view full content)

## Advanced Features

### Using with Custom Prompts
You can craft custom prompts for specific file operations:

**Summarization**:
```
Write a 3-sentence summary at the top of each file
```

**Translation**:
```
Translate all content in each file to Spanish, keeping the *** questions in English
```

**Formatting**:
```
Reformat each file as a bulleted list of key points
```

**Analysis**:
```
Add a "Key Insights" section at the end of each file with 5 bullet points
```

### IndexedDB Storage Slots
The app includes 5 storage slots for saving conversation states:
1. Select a slot (Slot 1-5) in the sidebar
2. Click "💾 Save" to store current conversations to that slot
3. Click "📂 Load" to restore conversations from that slot
4. Each slot stores the section database independently

## Development

### Project Structure
```
streamlit_openai_chat/
├── chat_5.py                    # Main application
├── readme_text_app.md          # This file
├── conversations/              # Default folder for saved conversations
└── clipboardReaderFormat/      # Additional clipboard reader tools
```

### Key Functions
- `build_messages_with_files()`: Adds file context to chat messages
- `parse_response_for_file_updates()`: Detects file update markers in AI responses
- `save_conversation()`: Exports chat to text file
- `load_conversation()`: Imports chat from text file

### Extending the App
To add new features:
1. Add session state variables at the top
2. Create UI elements in sidebar or main area
3. Modify `build_messages_with_files()` for custom context
4. Add parsing logic in `parse_response_for_file_updates()` for new formats

## Support

For issues, questions, or feature requests:
1. Check the troubleshooting section above
2. Review OpenAI API documentation: https://platform.openai.com/docs
3. Check Streamlit documentation: https://docs.streamlit.io

## License

This project is provided as-is for personal and educational use.

## Changelog

### Version 1.0 (Current)
- Multi-file upload and management
- Smart *** question recognition and answering
- Web search integration via Responses API
- View-only vs update-files modes
- Conversation save/load/copy
- Debug features for troubleshooting
- Support for GPT-3.5, GPT-4o, GPT-5, and o1 model families

---

**Quick Start Command**:
```bash
streamlit run chat_5.py
```

Enjoy using ChatGPT with File Processing! 🚀
