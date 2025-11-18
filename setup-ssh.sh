#!/bin/zsh

# Script to set up SSH agent and add keys for GitHub

echo "🔑 Setting up SSH for GitHub..."

# Start SSH agent if not running
if [ -z "$SSH_AUTH_SOCK" ]; then
    echo "Starting SSH agent..."
    eval "$(ssh-agent -s)"
fi

# Add SSH keys
echo "Adding SSH keys to agent..."
ssh-add ~/.ssh/id_ed25519 2>/dev/null
ssh-add ~/.ssh/id_rsa 2>/dev/null

# Test connection
echo ""
echo "Testing GitHub SSH connection..."
ssh -T git@github.com 2>&1 | head -1

echo ""
echo "✅ SSH setup complete!"
echo ""
echo "If you see 'Permission denied', you need to add your public key to GitHub:"
echo "1. Copy your public key:"
echo "   pbcopy < ~/.ssh/id_ed25519.pub"
echo "2. Go to: https://github.com/settings/keys"
echo "3. Click 'New SSH key' and paste your key"

