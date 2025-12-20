# AI Financial Advisory Agent

An intelligent financial advisory agent powered by OpenAI's `gpt-4.1-mini` and specialized financial tools. This agent provides comprehensive financial analysis, investment recommendations, budget planning, and market insights through an intuitive web interface.

## 🚀 Features

### Core Financial Tools
- **📊 Investment Analyzer**: Real-time stock analysis with technical indicators, risk assessment, and investment recommendations
- **💰 Budget Planner**: Personalized budget creation using the 50/30/20 rule with optimization suggestions
- **💳 Expense Tracker**: Advanced expense analysis with trends, predictions, and anomaly detection
- **📈 Portfolio Analyzer**: Portfolio diversification analysis and performance optimization
- **📰 Market Trends Analyzer**: Real-time market news, sector analysis, and economic insights

### Advanced Features
- **🎯 Smart Response Type Detection**: Automatically detects if users want short summaries or detailed reports
- **⚡ Real-time LLM Streaming**: Live token-by-token response generation from OpenAI API
- **📋 Interactive Tool Results**: Collapsible sections for clean data presentation
- **🔍 Comprehensive Data Analysis**: Enhanced visualizations and insights for all financial data
- **⏱️ Real-time Status Updates**: Shows which APIs are being called and estimated completion times

## 🛠️ Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/financial-advisory-agent.git
cd financial-advisory-agent
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
Create a `.env` file or set environment variables:
```bash
export OPENAI_API_KEY="your-openai-api-key"
export TAVILY_API_KEY="your-tavily-api-key"
```

4. **Run the application**
```bash
python app.py
```

## 💬 Example Prompts

### Single Tool Invocation

#### Investment Analyzer
```
"Analyze AAPL stock and tell me if it's a good investment"
"Should I buy Tesla stock right now?"
"Give me a detailed analysis of Microsoft shares"
"Quick summary of NVDA stock performance"
```

#### Budget Planner
```
"Help me create a budget with $5000 monthly income and expenses: rent $1500, food $500, utilities $200"
"I make $75,000 annually, help me budget my expenses"
"Create a budget plan for someone earning $4000/month"
"Quick budget advice for $6000 monthly income"
```

#### Market Trends Analyzer
```
"What are the latest market trends in tech stocks?"
"Give me current market news and analysis"
"Detailed report on today's market movements"
"Quick market update for technology sector"
```

#### Portfolio Analyzer
```
"Analyze my portfolio: {'holdings': [{'symbol': 'AAPL', 'shares': 100}, {'symbol': 'GOOGL', 'shares': 50}]}"
"Check my diversification with holdings: AAPL 40%, MSFT 30%, TSLA 30%"
"Detailed portfolio analysis for my current investments"
```

#### Expense Tracker
```
"Track my expenses: [{'category': 'food', 'amount': 150}, {'category': 'gas', 'amount': 80}]"
"Analyze my spending patterns from last month"
"Help me categorize and analyze my expenses"
```

### Response Type Control

#### Short Responses (Under 200 words)
```
"Quick analysis of AAPL"
"Brief summary of market trends"
"Give me a short budget recommendation"
"Simple portfolio check"
"Fast expense analysis"
```

#### Detailed Responses (Comprehensive reports)
```
"Give me a detailed report on AAPL stock"
"Comprehensive market analysis for tech sector"
"Thorough budget breakdown with recommendations"
"In-depth portfolio diversification analysis"
"Complete expense tracking report with insights"
```

### Multi-Tool Queries
```
"Analyze AAPL stock and create a budget for investing $1000 monthly"
"What are the current market trends and how should I adjust my portfolio?"
"Help me budget $5000 income and recommend some good stocks to invest in"
"Track my expenses and suggest a better budget allocation"
```

### Advanced Queries
```
"I have $50K to invest. Analyze current market trends, suggest a diversified portfolio, and create a budget for monthly investments of $2000"
"Detailed analysis: Review AAPL, MSFT, and GOOGL stocks, then help me rebalance my portfolio"
"Comprehensive financial review: Budget analysis for $8000 monthly income, expense tracking, and investment recommendations"
```

## 🎯 Response Types

The system automatically detects your preference:

### Short Response Keywords
- `quick`, `brief`, `short`, `summary`, `concise`, `simple`, `fast`, `tldr`, `bottom line`

### Detailed Response Keywords  
- `detailed`, `comprehensive`, `thorough`, `in-depth`, `report`, `breakdown`, `explain`, `elaborate`, `deep dive`

### Default Behavior
- **Short responses** are the default (under 200 words)
- **Detailed responses** are triggered by specific keywords (comprehensive analysis)

## 🔧 Technical Architecture

- **Frontend**: Gradio web interface with real-time streaming
- **Backend**: LangChain agents with OpenAI GPT-4
- **Data Sources**: 
  - Yahoo Finance API for stock data
  - Tavily Search API for market news
  - Real-time financial calculations
- **Streaming**: Direct LLM token streaming from OpenAI API
- **Tools**: Specialized financial analysis functions

## 📊 Tool Capabilities

### Investment Analyzer
- Real-time stock prices and historical data
- Technical indicators (RSI, MACD, Bollinger Bands, Moving Averages)
- Risk assessment (volatility, VaR, beta analysis)
- Fundamental analysis (P/E, P/B ratios, dividend yield)
- Buy/Hold/Sell recommendations with confidence scores

### Budget Planner
- 50/30/20 rule implementation
- Emergency fund calculations
- Debt-to-income ratio analysis
- Savings optimization recommendations
- Expense category warnings

### Market Trends Analyzer
- Real-time market news via Tavily Search
- Major index tracking (S&P 500, NASDAQ)
- Market sentiment analysis
- Key theme extraction
- Economic trend identification

### Portfolio Analyzer
- Diversification scoring
- Sector allocation analysis
- Concentration risk assessment
- Rebalancing recommendations
- Performance metrics

### Expense Tracker
- Category-wise spending analysis
- Trend detection and predictions
- Budget vs. actual comparisons
- Anomaly detection
- Spending pattern insights

## 🚀 Recent Updates

- ✅ **Smart Response Detection**: Automatically detects if users want short or detailed responses
- ✅ **Real LLM Streaming**: Genuine token-by-token streaming from OpenAI API
- ✅ **Enhanced Tool Status**: Real-time API call tracking with time estimates
- ✅ **Improved Data Analysis**: Comprehensive visualizations and insights
- ✅ **Optimized Performance**: Faster tool execution and response times
- ✅ **Collapsible Results**: Clean, organized tool output presentation

## 🔒 API Keys Required

- **OpenAI API Key**: For language model
- **Tavily API Key**: For real-time market news and trends

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

