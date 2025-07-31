#!/bin/bash

echo "🚀 Preparing for Streamlit Cloud Deployment..."
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit with Streamlit app"
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository already exists"
fi

# Check if remote is set
if ! git remote get-url origin &> /dev/null; then
    echo ""
    echo "🔗 Please add your GitHub repository as remote:"
    echo "git remote add origin https://github.com/yourusername/your-repo.git"
    echo ""
    echo "Then run:"
    echo "git push -u origin main"
    echo ""
    echo "After that, go to https://share.streamlit.io and:"
    echo "1. Connect your GitHub repository"
    echo "2. Set main file path to: streamlit_app.py"
    echo "3. Add your GOOGLE_API_KEY in the secrets"
    exit 1
fi

echo "📤 Pushing to GitHub..."
git add .
git commit -m "Update Streamlit app"
git push

echo ""
echo "✅ Code pushed to GitHub!"
echo ""
echo "🌐 Now go to https://share.streamlit.io and:"
echo "1. Connect your GitHub repository"
echo "2. Set main file path to: streamlit_app.py"
echo "3. Add your GOOGLE_API_KEY in the secrets"
echo ""
echo "🎉 Your app will be live at: https://your-app-name.streamlit.app"
echo ""
echo "💡 Don't forget to get your Google API key from:"
echo "https://makersuite.google.com/app/apikey" 