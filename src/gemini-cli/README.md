# Google Gemini CLI Installation

## Overview

Google Gemini CLI is part of Google Cloud SDK that provides AI-powered code assistance through Google's Gemini models. It offers code suggestions, explanations, and intelligent programming support integrated with Google Cloud Platform services.

This directory contains installation, update, and uninstall scripts that follow repository conventions and provide comprehensive Google Cloud SDK integration.

## Official Installation Page

Canonical documentation and setup: https://cloud.google.com/gemini/docs/codeassist/gemini-cli

These scripts complement the official guide by adding automated checks for SDK presence, authentication status, project configuration, and API enablement.

## Prerequisites

### Platform Requirements
- **macOS** (Darwin) - Primary support
- **Linux** - Full support
- **Windows** - Not supported by these scripts

### Dependencies

**Google Cloud SDK Requirements:**
- **Google Cloud SDK** - Core requirement for all Gemini CLI functionality
- **Internet connection** - Required for gcloud operations and API access
- **Python 3.7+** - Required by Google Cloud SDK (usually auto-installed)

### Account Requirements
- **Google Cloud account** - Sign up at https://console.cloud.google.com/
- **Active GCP project** - Required for API access and billing
- **Generative AI API enabled** - Required for Gemini functionality
- **Appropriate IAM permissions** - For accessing Gemini APIs

## Installation

### Quick Install
```bash
./install_gemini_cli.sh
```

The install script automatically:
1. Detects your platform (macOS/Linux)
2. Verifies Google Cloud SDK installation
3. Checks authentication and project configuration
4. Attempts to install/enable Gemini CLI components
5. Validates Generative AI API access
6. Provides detailed setup instructions

### Manual Installation

**Step 1: Install Google Cloud SDK**
```bash
# macOS with Homebrew
brew install google-cloud-sdk

# Linux (Ubuntu/Debian)
curl https://sdk.cloud.google.com | bash

# Other methods: https://cloud.google.com/sdk/docs/install
```

**Step 2: Initialize and Authenticate**
```bash
# Initialize gcloud
gcloud init

# Or authenticate manually
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

**Step 3: Enable Generative AI API**
```bash
gcloud services enable generativeai.googleapis.com
```

**Step 4: Install Gemini CLI (if separate component)**
```bash
# May be available as separate component
gcloud components install gemini

# Or may be part of core gcloud SDK
gcloud gemini --help  # Test if available
```

## Authentication & Project Setup

### Google Cloud Authentication

**Initial Setup:**
```bash
# Interactive authentication and project setup
gcloud init

# Manual authentication
gcloud auth login

# Set default project
gcloud config set project YOUR_PROJECT_ID

# Verify setup
gcloud auth list
gcloud config get-value project
```

**Service Account Authentication (CI/CD):**
```bash
# Set up service account key
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS"
```

### API Configuration

**Enable Required APIs:**
```bash
# Enable Generative AI API (required)
gcloud services enable generativeai.googleapis.com

# Check enabled services
gcloud services list --enabled --filter="name:generativeai.googleapis.com"
```

**Verify API Access:**
```bash
# Test Gemini CLI availability
gcloud gemini --help

# Check quota and limits (if available)
gcloud quota list --service=generativeai.googleapis.com
```

## Usage

### Basic Commands

**Help and Version:**
```bash
gcloud gemini --help              # Show Gemini CLI help
gcloud version                    # Show Google Cloud SDK version
gcloud info                       # Show detailed SDK information
```

### Code Assistance (If Available)

**Note:** Exact Gemini CLI commands may vary based on Google's implementation and your region/project access.

**Potential Commands:**
```bash
# Code suggestions (example - actual syntax may differ)
gcloud gemini code-assist suggest --help
gcloud gemini code-assist suggest --query="create a Python REST API"

# Code explanations (example)
gcloud gemini code-assist explain --help
gcloud gemini code-assist explain --code="$(cat myfile.py)"

# Interactive mode (if available)
gcloud gemini interactive
```

### Project Management

**Manage Projects:**
```bash
# List available projects
gcloud projects list

# Switch projects
gcloud config set project PROJECT_ID

# Create new project
gcloud projects create PROJECT_ID --name="My Project"
```

## Updates

### Quick Update
```bash
./update_gemini_cli.sh
```

The update script:
- Updates all Google Cloud SDK components
- Preserves authentication and configuration
- Shows version changes and component status
- Validates Gemini CLI availability after update

### Manual Update

```bash
# Update all gcloud components
gcloud components update

# List available updates
gcloud components list --show-versions

# Update specific component (if Gemini is separate)
gcloud components update gemini
```

## Uninstallation

### Quick Uninstall
```bash
./uninstall_gemini_cli.sh
```

### Uninstall Options
```bash
./uninstall_gemini_cli.sh -y              # Skip confirmation prompts
./uninstall_gemini_cli.sh -p              # Preserve configuration files
./uninstall_gemini_cli.sh -g              # Remove entire Google Cloud SDK
./uninstall_gemini_cli.sh --help          # Show all options
```

**Important:** By default, uninstall only removes Gemini components, not the entire Google Cloud SDK. Use `-g` flag to remove the complete SDK.

### Manual Uninstall

**Remove Gemini Component Only:**
```bash
# If Gemini is a separate component
gcloud components remove gemini
```

**Remove Entire Google Cloud SDK:**
```bash
# Homebrew installation
brew uninstall google-cloud-sdk

# Manual installation
rm -rf ~/google-cloud-sdk

# Remove from shell profile
# Edit ~/.zshrc or ~/.bashrc and remove gcloud PATH additions
```

## Troubleshooting

### Common Issues

**Issue**: "gcloud: command not found"
```bash
# Solution: Install Google Cloud SDK
# macOS: brew install google-cloud-sdk
# Linux: curl https://sdk.cloud.google.com | bash

# Add to PATH manually if needed
export PATH="$HOME/google-cloud-sdk/bin:$PATH"
source ~/.zshrc
```

**Issue**: "gcloud gemini: command group not found"
```bash
# Solution 1: Update Google Cloud SDK
gcloud components update

# Solution 2: Check if Gemini is available in your region
gcloud components list | grep -i gemini

# Solution 3: Verify API access and project permissions
gcloud services list --enabled | grep generativeai
```

**Issue**: Authentication failures
```bash
# Solution: Re-authenticate
gcloud auth login
gcloud auth list

# Check project access
gcloud projects list
gcloud config set project YOUR_PROJECT_ID
```

**Issue**: "Generative AI API not enabled" errors
```bash
# Solution: Enable API and check quotas
gcloud services enable generativeai.googleapis.com
gcloud services list --enabled --filter="generativeai"

# Check billing account (required for API usage)
gcloud billing accounts list
gcloud billing projects link PROJECT_ID --billing-account=BILLING_ACCOUNT_ID
```

**Issue**: Permission denied or access errors
```bash
# Solution: Check IAM permissions
gcloud projects get-iam-policy PROJECT_ID

# Required roles may include:
# - roles/aiplatform.user
# - roles/ml.developer
# - roles/serviceusage.serviceUsageConsumer

# Add role to user
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="user:EMAIL" \
    --role="roles/aiplatform.user"
```

### Regional Availability

**Note:** Gemini CLI availability may depend on:
- Google Cloud region settings
- API regional availability
- Project configuration and access levels

**Check Regional Settings:**
```bash
# View current region/zone
gcloud config get-value compute/region
gcloud config get-value compute/zone

# Set region if needed
gcloud config set compute/region us-central1
```

### API Quotas and Limits

**Monitor Usage:**
```bash
# Check quota usage (if available)
gcloud services quota list --service=generativeai.googleapis.com

# Monitor billing
gcloud billing accounts list
```

## Configuration

### Environment Variables

**GOOGLE_APPLICATION_CREDENTIALS**
- Path to service account key file (for automated authentication)
- Example: `export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"`

**GCLOUD_PROJECT** or **GOOGLE_CLOUD_PROJECT**
- Default project ID for gcloud commands
- Example: `export GOOGLE_CLOUD_PROJECT="my-project-id"`

### Configuration Files

Google Cloud SDK stores configuration in:
- **macOS**: `~/Library/Application Support/gcloud/`
- **Linux**: `~/.config/gcloud/`

Key configuration files:
- `configurations/config_default` - Default configuration
- `credentials_db` - Authentication credentials
- `active_config` - Currently active configuration

## Billing and Cost Management

### Understanding Costs
- **API-based pricing**: Gemini CLI usage consumes Google Cloud API quotas
- **Model costs**: Different Gemini models have different pricing tiers
- **Regional variations**: Costs may vary by Google Cloud region

### Cost Management
```bash
# Set up billing alerts in Google Cloud Console
# Monitor API usage through Cloud Console
# Set quotas to limit unexpected charges

# Check current project billing
gcloud billing projects describe PROJECT_ID
```

## Integration with Development Workflow

### CI/CD Integration
```bash
# Use service account authentication
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS"

# Automated project setup
gcloud config set project $PROJECT_ID
gcloud services enable generativeai.googleapis.com
```

### Editor Integration
- **VS Code**: Use Google Cloud Code extension alongside Gemini CLI
- **Terminal workflow**: Integrate Gemini commands in development scripts
- **Git hooks**: Use for automated code review or documentation

### Team Usage
- **Shared projects**: Use Google Cloud IAM for team access
- **Service accounts**: For automated/CI environments
- **Quota management**: Monitor team API usage

## Security Considerations

### Authentication Security
- **Secure credential storage**: Use Google Cloud credential management
- **Service account keys**: Rotate regularly, store securely
- **IAM best practices**: Use principle of least privilege
- **Project isolation**: Separate development/production projects

### Code Privacy
- **Google Cloud terms**: Review data handling and privacy policies
- **On-premise alternatives**: Consider if cloud processing is appropriate
- **Audit logs**: Monitor API usage through Cloud Console
- **Data residency**: Understand where your data is processed

## References

### Official Documentation
- **Google Cloud SDK**: https://cloud.google.com/sdk/docs/
- **Gemini API**: https://cloud.google.com/gemini/docs/
- **Google Cloud Console**: https://console.cloud.google.com/
- **IAM Documentation**: https://cloud.google.com/iam/docs/

### Installation Resources
- **Google Cloud SDK Install**: https://cloud.google.com/sdk/docs/install
- **gcloud CLI Reference**: https://cloud.google.com/sdk/gcloud/reference/
- **API Client Libraries**: https://cloud.google.com/apis/docs/client-libraries-explained

### Repository Guidelines
- **Coding Standards**: See `../../AGENTS.md`
- **Shell Utilities**: See `../../bash/common/repo_lib.sh`

## Changelog

### Version 1.0 (2024-10-30)
- Initial Google Gemini CLI installation scripts
- Complete install/update/uninstall workflow with Google Cloud SDK integration
- GCP authentication and project configuration validation
- Generative AI API enablement and access checking
- Comprehensive error handling for Google Cloud SDK operations
- Platform detection and compatibility checks
- Detailed troubleshooting for common GCP setup issues

## License & Support

This tooling follows the repository license. For Google Gemini CLI issues:
- **Installation problems**: Check this README's troubleshooting section
- **Google Cloud SDK issues**: Visit https://cloud.google.com/sdk/docs/troubleshooting
- **API/billing questions**: Contact Google Cloud Support
- **Gemini CLI features**: Consult official Google Cloud documentation

---

**Note**: Google Gemini CLI availability and features may vary based on your Google Cloud project, region, and access permissions. Some features may be in preview or require special access.