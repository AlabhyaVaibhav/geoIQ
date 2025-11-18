# geoIQ

## Amazon Rufus AI Automation

This project automates interactions with Amazon's Rufus AI assistant to ask questions and capture responses.

### Features

- Automated login to Amazon.com
- Finds and interacts with the Rufus AI button
- Asks questions from a predefined list
- Captures and stores responses in JSON format
- Extracts product recommendations and detailed responses

### Prerequisites

- Python 3.8 or higher
- Chrome browser installed
- ChromeDriver (automatically managed by Selenium 4.6+)
- Amazon account credentials

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd GEO
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install ChromeDriver (if not automatically managed):
   - On macOS: `brew install chromedriver`
   - On Linux: Download from https://chromedriver.chromium.org/
   - On Windows: Download and add to PATH

### Configuration

1. Create a questions file (`questions.txt`) with one question per line:
```
What are the best 2-liter sodas for Thanksgiving dinner that stay fizzy the longest?
Show carbonation saver products
Best sodas for holiday parties
```

2. (Optional) Create a config file for credentials (not recommended for security):
   - Copy `config.example.json` to `config.json`
   - Fill in your Amazon credentials

### Usage

#### Basic Usage

Run the script with command-line arguments:

```bash
python amazon_rufus_automation.py \
  --email your-email@example.com \
  --password your-password \
  --questions-file questions.txt
```

#### Options

- `--email`: Your Amazon account email (required unless using `--manual-login`)
- `--password`: Your Amazon account password (required unless using `--manual-login`)
- `--questions-file`: Path to file containing questions (default: `questions.txt`)
- `--headless`: Run browser in headless mode (no GUI)
- `--output`: Custom filename for output JSON file
- `--manual-login`: Pause for manual login instead of automated login (recommended if login fails)

#### Examples

**Automated login:**
```bash
python amazon_rufus_automation.py \
  --email user@example.com \
  --password mypassword \
  --questions-file questions.txt \
  --output my_results.json
```

**Manual login (recommended if automated login fails):**
```bash
python amazon_rufus_automation.py \
  --manual-login \
  --questions-file questions.txt
```

**Headless mode:**
```bash
python amazon_rufus_automation.py \
  --email user@example.com \
  --password mypassword \
  --questions-file questions.txt \
  --headless
```

### Output

The script creates a `rufus_responses/` directory and saves results in JSON format:

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "total_questions": 5,
  "results": [
    {
      "question": "What are the best 2-liter sodas...",
      "response": "Perfect timing for Thanksgiving! Here are...",
      "timestamp": "2024-01-15T10:30:15",
      "raw_html": "..."
    }
  ]
}
```

### How It Works

1. **Login**: Automatically logs into Amazon.com using provided credentials
2. **Find Rufus**: Locates the Rufus AI button on the home page using the provided HTML selectors
3. **Ask Questions**: Submits each question from the questions file to the Rufus chat interface
4. **Capture Responses**: Extracts:
   - Customer question text
   - Main response text
   - Product recommendations (ASIN cards)
   - Product details (titles, prices, descriptions)
5. **Save Results**: Stores all captured data in JSON format

### HTML Elements Used

- **Rufus Button**: `button#nav-rufus-disco` or `.nav-rufus-disco`
- **Question Input**: `textarea#rufus-text-area`
- **Response Container**: `.conversation-turn-container`
- **Customer Text**: `.rufus-customer-text-wrap`
- **Response Text**: `.rufus-text-subsections-with-avatar-branding-update`
- **Product Cards**: `.rufus-asin-faceout`

### Troubleshooting

1. **Login fails**: 
   - **Use manual login mode**: If automated login fails, use the `--manual-login` flag:
     ```bash
     python amazon_rufus_automation.py --manual-login --questions-file questions.txt
     ```
     This will open the browser and pause for you to log in manually.
   
   - **Check credentials**: Ensure your email and password are correct
   
   - **2FA/OTP**: If your account has 2FA enabled, the script will detect it and pause for you to enter the code manually
   
   - **CAPTCHA**: Amazon may show a CAPTCHA - the script will detect it and pause for you to solve it
   
   - **Screenshots**: If login fails, check the generated screenshot files:
     - `login_error_email_field.png`
     - `login_error_password_field.png`
     - `login_error_message.png`
     - `login_verification_failed.png`
   
   - **Check logs**: Review `rufus_automation.log` for detailed error messages
   
   - **Run without headless mode**: Try running without `--headless` to see what's happening:
     ```bash
     python amazon_rufus_automation.py --email your@email.com --password yourpass
     ```

2. **Rufus button not found**:
   - Ensure you're logged in
   - Rufus may not be available in all regions
   - Try refreshing the page manually

3. **Responses not captured**:
   - Increase wait times in the script
   - Check network connection
   - Amazon's page structure may have changed

4. **ChromeDriver issues**:
   - Update Chrome browser to latest version
   - Ensure ChromeDriver matches Chrome version
   - Use `webdriver-manager` for automatic management

### Security Notes

- Never commit credentials to version control
- Use environment variables for sensitive data when possible
- Consider using a dedicated Amazon account for automation

### Logging

The script creates a `rufus_automation.log` file with detailed execution logs.

---

## Brand Presence Audit

The brand audit module analyzes Rufus AI responses to track brand mentions and compare your brands against competitors.

### Features

- Analyzes all responses for brand mentions
- Tracks your brands vs competitor brands
- Calculates presence rates and statistics
- Provides detailed context for each mention
- Exports reports in JSON, CSV, or text format

### Usage

#### Using a brands file (recommended):

1. Create a brands file (`brands.json`) based on `brands.example.json`:
```json
{
  "your_brands": ["Coca-Cola", "Coke", "Sprite"],
  "competitor_brands": ["Pepsi", "Diet Pepsi", "Canada Dry"]
}
```

2. Run the audit:
```bash
python brand_audit.py rufus_responses/rufus_responses_20251118_115151.json --brands-file brands.json
```

#### Using command-line arguments:

```bash
python brand_audit.py rufus_responses/rufus_responses_20251118_115151.json \
  --your-brands "Coca-Cola" "Coke" "Sprite" \
  --competitor-brands "Pepsi" "Diet Pepsi" "Canada Dry"
```

#### Output formats:

```bash
# JSON format (default)
python brand_audit.py responses.json --brands-file brands.json --format json

# CSV format (creates multiple CSV files)
python brand_audit.py responses.json --brands-file brands.json --format csv

# Text format (human-readable report)
python brand_audit.py responses.json --brands-file brands.json --format txt

# All formats
python brand_audit.py responses.json --brands-file brands.json --format all
```

### Output

The audit generates comprehensive reports including:

- **Summary Statistics**: Total responses, presence rates, mention counts
- **Brand Statistics**: Individual brand performance metrics
- **Detailed Analysis**: Per-response breakdown with context
- **Comparison Metrics**: Your brands vs competitors

#### Example Output:

```
SUMMARY
--------------------------------------------------------------------------------
Total Responses Analyzed: 5
Responses with Your Brands: 2 (40.0%)
Responses with Competitors: 4 (80.0%)
Total Your Brand Mentions: 3
Total Competitor Mentions: 8

YOUR BRANDS
--------------------------------------------------------------------------------
  coca-cola:
    Total Mentions: 2
    Responses Mentioned In: 1
  sprite:
    Total Mentions: 1
    Responses Mentioned In: 1

COMPETITOR BRANDS
--------------------------------------------------------------------------------
  pepsi:
    Total Mentions: 3
    Responses Mentioned In: 2
  canada dry:
    Total Mentions: 5
    Responses Mentioned In: 3
```

### Brand Matching

The auditor uses case-insensitive word boundary matching to find brand mentions. This means:
- "Coca-Cola" will match "Coca-Cola", "coca-cola", "COCA-COLA"
- It won't match partial words (e.g., "Coca" won't match "Coca-Cola" unless "Coca" is in your brand list)

### Integration with Automation

You can chain the automation and audit:

```bash
# 1. Collect responses
python amazon_rufus_automation.py --manual-login --questions-file questions.txt

# 2. Audit brand presence
python brand_audit.py rufus_responses/rufus_responses_*.json --brands-file brands.json --format all
```

---

## Response Visualizer

A simple web-based visualizer for viewing and exploring Rufus AI responses.

### Features

- **Interactive Dashboard**: View all questions and responses in a clean, organized interface
- **Statistics**: See summary statistics including total questions, response completeness, and average response length
- **Search & Filter**: Quickly find specific questions or responses using the search bar
- **Drag & Drop**: Easy file upload with drag-and-drop support
- **Responsive Design**: Works on desktop and mobile devices
- **Status Indicators**: Visual badges show which responses are complete vs incomplete

### Usage

1. Open `rufus_visualizer.html` in your web browser:
   ```bash
   open rufus_visualizer.html
   # Or double-click the file in your file manager
   ```

2. Upload a JSON file:
   - Click the upload area or drag and drop a `rufus_responses_*.json` file
   - The visualizer will automatically load and display the data

3. Explore the responses:
   - Use the search bar to filter questions/responses
   - View statistics in the summary cards
   - Scroll through all responses in an organized card layout

### Features

- **Question/Response Cards**: Each response is displayed in an easy-to-read card format
- **Timestamps**: See when each question was asked
- **Response Status**: Visual indicators show if responses are complete or still loading
- **Character Count**: View response length for each answer
- **Real-time Search**: Filter responses as you type

### Complete Workflow

```bash
# 1. Collect responses from Rufus
python amazon_rufus_automation.py --manual-login --questions-file questions.txt

# 2. Audit brand presence
python brand_audit.py rufus_responses/rufus_responses_*.json --brands-file brands.json

# 3. Visualize responses
open rufus_visualizer.html
# Then upload the JSON file in the browser
```

### License

[Add your license here]
