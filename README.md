# 🏙️ City of Better Choices - Interactive Blockchain Adventure

An interactive text-based adventure game with AI-generated images and blockchain integration. Make sustainable choices that impact your community and environment, then save your story outcomes on the blockchain!

## ✨ Features

- **🎮 Interactive Storytelling**: Choice-based gameplay with branching narratives focused on sustainability
- **🎨 AI-Generated Images**: Dynamic images for each scene using Pollinations.ai
- **⛓️ Blockchain Integration**: Save story outcomes on VeChain blockchain
- **🏆 Multiple Endings**: Different endings based on your choices and environmental impact score
- **📱 Responsive Design**: Works on desktop and mobile devices
- **🔗 Sync2 Integration**: Seamless VeChain wallet connection and network switching

## 🚀 Live Demo

[Play the Game](https://city-of-better-choices.vercel.app) | [View on GitHub](https://github.com/yourusername/city-of-better-choices)

> **Note**: Replace `yourusername` with your actual GitHub username

## 🎯 Sustainability Focus

This project is built to promote **sustainable living and environmental awareness** through interactive storytelling and blockchain technology.

## 🛠️ Tech Stack

- **Frontend**: HTML, CSS, JavaScript, Ethers.js
- **Backend**: Python Flask
- **Blockchain**: VeChain (Sync2 wallet integration)
- **Smart Contract**: Solidity
- **Image Generation**: Pollinations.ai API
- **Deployment**: Vercel

## 📋 Prerequisites

- Python 3.7+
- Sync2 (VeChain wallet) for testnet
- VeChain Thor testnet access (no mainnet)
- Modern web browser with JavaScript enabled

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/city-of-better-choices.git
   cd city-of-better-choices
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python -m flask --app api/index.py run
   ```

4. **Open in browser**
   ```
   http://127.0.0.1:5000
   ```

### Blockchain Setup (VeChain Testnet + Sync2)

1. **Install Sync2** wallet (desktop or mobile) and have it available on your machine.
2. **Open Sync2** via any deeplink prompt (for example the faucet prompt).
3. For testing signatures, no tokens are required. If you need test VET/VTHO, visit the VeChain testnet faucet: `https://faucet.vecha.in/`.
4. This app uses Connex to request a Sync2 identification certificate and to sign a message for your story outcome. No mainnet is used.

## 🎮 How to Play

1. **Start your journey** in the City of Better Choices
2. **Make sustainable choices** that affect your environmental impact and score
3. **Watch AI-generated images** for each scene
4. **Reach an ending** based on your decisions
5. **Save to blockchain** to permanently store your story
6. **Share your impact** with friends and community

## 🏗️ Project Structure

```
city-of-better-choices/
├── api/
│   └── index.py              # Flask backend server
├── public/
│   ├── index.html            # Main game page
│   ├── script.js             # Frontend JavaScript
│   ├── style.css             # Game styling
│   └── ethers-offline.js     # Offline ethers.js fallback
├── ForestAdventure.sol       # Smart contract
├── forest-adventure.js       # Contract interaction
├── requirements.txt          # Python dependencies
├── vercel.json              # Vercel configuration
└── README.md                # This file
```

## 🔧 Blockchain Integration

The game uses **VeChain message signing** for story verification:

- **Method**: VeChain Sync2 message signing (no smart contract required)
- **Wallet**: Sync2 desktop/mobile wallet
- **Network**: VeChain testnet
- **Cost**: Free (no gas fees)

### What Gets Signed

Each story outcome includes:
- Story ending category and score
- Environmental impact metrics
- Generated image URLs
- Player's wallet signature
- Timestamp

### Smart Contract (Optional)

A Solidity smart contract is available for permanent storage:
- **File**: `ForestAdventure.sol`
- **Status**: Ready for deployment (not required)
- **Deployment**: See `SMART_CONTRACT_DEPLOYMENT.md`

## 🌐 Deployment

### Quick Deployment

1. **Create GitHub Repository**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: City of Better Choices"
   git remote add origin https://github.com/YOUR_USERNAME/city-of-better-choices.git
   git push -u origin main
   ```

2. **Deploy to Vercel**:
   - Go to [Vercel](https://vercel.com)
   - Import your GitHub repository
   - Vercel will auto-detect the configuration from `vercel.json`
   - Click "Deploy"

3. **Your app will be live at**: `https://city-of-better-choices.vercel.app`

### Detailed Instructions

See [QUICK_DEPLOYMENT.md](QUICK_DEPLOYMENT.md) for step-by-step deployment guide.

### Environment Variables

No environment variables required for basic functionality. The app uses:
- Pollinations.ai API (no key required)
- VeChain testnet (no key required)

## 🎯 Sustainability Impact

This project promotes **environmental awareness and sustainable living** through:

- ✅ **Educational Gaming**: Interactive story game teaches sustainability
- ✅ **Blockchain Integration**: Stories stored on VeChain blockchain
- ✅ **User Ownership**: Players own their story outcomes
- ✅ **Innovation**: AI-generated content with blockchain persistence
- ✅ **User Experience**: Seamless Sync2 wallet integration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **VeChain Foundation** for the blockchain infrastructure
- **Pollinations.ai** for AI image generation
- **Sustainability Community** for inspiration
- **Sync2** for wallet integration

## 📞 Support

If you encounter any issues:

1. Check the [Issues](https://github.com/yourusername/city-of-better-choices/issues) page
2. Create a new issue with detailed description
3. Contact the development team for support

---

**Built with ❤️ for a Sustainable Future**