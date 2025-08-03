#!/bin/bash

echo "🚀 Setting up GitHub repository for VIS Scraper..."

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install git first."
    exit 1
fi

# Check if we're in a git repository
if [ -d ".git" ]; then
    echo "✅ Git repository already initialized"
else
    echo "📁 Initializing git repository..."
    git init
fi

# Add all files
echo "📝 Adding files to git..."
git add .

# Check if there are changes to commit
if git diff --cached --quiet; then
    echo "ℹ️  No changes to commit"
else
    echo "💾 Committing changes..."
    git commit -m "Initial commit: VIS Scraper with multi-language validation

- Multi-language web scraper using Playwright
- Targets select id='attr-lang' dropdown
- Extracts PDF URLs, dates, and English VIS links
- Comprehensive validation reporting
- Clean CSV output with language-specific columns"
fi

echo ""
echo "🎯 Next steps to publish to GitHub:"
echo ""
echo "1. Create a new repository on GitHub:"
echo "   - Go to https://github.com/new"
echo "   - Choose a repository name (e.g., 'vis-scraper')"
echo "   - Make it public or private as preferred"
echo "   - Don't initialize with README (we already have one)"
echo ""
echo "2. Connect your local repository to GitHub:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git"
echo ""
echo "3. Push to GitHub:"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "📋 Current git status:"
git status

echo ""
echo "✅ Setup complete! Follow the steps above to publish to GitHub." 