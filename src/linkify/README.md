# go_linkify - Google Docs Link Tools

A Google Apps Script utility that enhances Google Docs with various link-related functionality.

## Features

1. **go/linkify**: Converts "go/xyz" shorthand links into clickable hyperlinks (https://go/xyz)
2. **Email to Person Chips**: Converts plain email addresses into Google Docs person chips (smart chips)
3. **Extract Links**: Extracts all hyperlinks from the document and lists them at the end
4. **Extract People**: Extracts all person mentions from the document and lists them at the end
5. **All-in-one**: Run all the above features with a single click

## Setup Instructions

### Method 1: Using the Script Editor in Google Docs

1. **Open a Google Doc**:
   - Open an existing document or create a new one at [docs.google.com](https://docs.google.com)

2. **Access the Script Editor**:
   - Click on **Extensions** > **Apps Script** in the menu bar
   - This will open the Google Apps Script editor in a new tab

3. **Add the Script**:
   - Delete any code that appears in the editor
   - Copy the entire contents of the `go_linkify.gs` file
   - Paste it into the script editor
   - Click **File** > **Save** (or press Ctrl+S / Cmd+S)
   - Give your project a name (e.g., "go_linkify")

4. **Authorize the Script** (one-time setup):
   - Click the **Run** button (▶️) or select any function like `onOpen` to run
   - Google will prompt you to authorize the script
   - Click "Review Permissions"
   - Choose your Google account
   - Click "Allow" to grant the necessary permissions

5. **Close and Reload**:
   - Close the script editor tab
   - Reload your Google Doc
   - You should now see a new menu item called "Link Tools" in the menu bar

### Method 2: Using Google Apps Script Dashboard (for multiple documents)

1. **Go to Google Apps Script**:
   - Visit [script.google.com](https://script.google.com)
   - Sign in with your Google account if prompted

2. **Create a New Project**:
   - Click the **+ New project** button
   - Delete any code that appears in the editor
   - Copy the entire contents of the `go_linkify.gs` file
   - Paste it into the script editor
   - Click **File** > **Save** (or press Ctrl+S / Cmd+S)
   - Give your project a name (e.g., "go_linkify")

3. **Deploy as Web App** (optional, for sharing with others):
   - Click **Deploy** > **New deployment**
   - Select **Web app** as the type
   - Set "Who has access" to the appropriate level (yourself, your organization, or anyone)
   - Click **Deploy**
   - Copy the URL if you want to share it

4. **Connect to Your Documents**:
   - Open any Google Doc
   - Click **Extensions** > **Apps Script**
   - Delete any code that appears
   - Add this single line: `eval(UrlFetchApp.fetch('YOUR_SCRIPT_URL').getContentText())`
   - Replace `YOUR_SCRIPT_URL` with the URL from the previous step
   - Click **File** > **Save** and reload your document

## Using go_linkify

After setup, a new menu item labeled "Link Tools" will appear in your Google Docs menu bar. It contains the following options:

1. **go/linkify**:
   - Click this option to convert all instances of "go/something" text into clickable hyperlinks
   - The links will be transformed to the format "https://go/something"

2. **Email to Person Chips**:
   - Click this option to convert all email addresses in your document to Google Docs person chips
   - Person chips show profile information when clicked and enable convenient collaboration

3. **Extract Links**:
   - Click this option to gather all hyperlinks from your document
   - The links will be appended as a list at the end of your document

4. **Extract People**:
   - Click this option to gather all person mentions from your document
   - The people will be appended as a list at the end of your document

5. **go/linkify and extract all**:
   - Click this option to run all the above functions in sequence

## Troubleshooting

- **Menu Not Appearing**: If the "Link Tools" menu doesn't appear, try refreshing the page or reopening the document
- **Permissions Error**: If you see permission errors, ensure you authorized the script correctly in the setup steps
- **Script Errors**: Check the script execution logs by going to the script editor and clicking **View** > **Logs**

## Limitations

- The script only works on text in the main document body
- Some complex document structures might not be fully processed
- Email addresses within tables, headers, or footnotes might not be detected properly

## Advanced Usage

You can modify the script to handle additional link formats or customize how links are processed by editing the regular expression patterns in the script code.