import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

import pandas as pd
import yfinance as yf
from langchain.tools import Tool
from langchain_community.tools.tavily_search import TavilySearchResults


class FinancialTools:
    def __init__(self, tavily_api_key: str):
        self.tavily_search = TavilySearchResults(api_key=tavily_api_key)

    def create_budget_planner(self) -> Tool:
        def budget_planner(input_str: str) -> str:
            """Create a personalized budget plan with advanced features"""
            try:
                data = json.loads(input_str)
                income = data.get("income", 0)
                expenses = data.get("expenses", {})
                goals = data.get("savings_goals", {})
                debt = data.get("debt", {})

                # Calculate budget allocations using 50/30/20 rule
                needs = income * 0.5
                wants = income * 0.3
                savings = income * 0.2

                total_expenses = sum(expenses.values())
                remaining = income - total_expenses

                # Debt analysis
                total_debt = sum(debt.values()) if debt else 0
                debt_to_income = (total_debt / income * 100) if income > 0 else 0

                # Emergency fund calculation (3-6 months of expenses)
                emergency_fund_needed = total_expenses * 6
                emergency_fund_goal = goals.get("emergency_fund", 0)

                # Calculate actual savings potential
                debt_payments = debt.get("monthly_payments", 0)
                available_for_savings = remaining - debt_payments

                budget_plan = {
                    "monthly_income": income,
                    "recommended_allocation": {
                        "needs": needs,
                        "wants": wants,
                        "savings": savings,
                    },
                    "current_expenses": expenses,
                    "total_expenses": total_expenses,
                    "remaining_budget": remaining,
                    "savings_rate": (available_for_savings / income * 100) if income > 0 else 0,
                    "debt_analysis": {
                        "total_debt": total_debt,
                        "debt_to_income_ratio": debt_to_income,
                        "monthly_payments": debt_payments,
                    },
                    "emergency_fund": {
                        "recommended": emergency_fund_needed,
                        "current": emergency_fund_goal,
                        "progress": (emergency_fund_goal / emergency_fund_needed * 100) if emergency_fund_needed > 0 else 0,
                    },
                    "savings_optimization": {
                        "available_monthly": available_for_savings,
                        "annual_savings_potential": available_for_savings * 12,
                    },
                    "recommendations": [],
                }

                # Enhanced recommendations
                if available_for_savings < savings:
                    budget_plan["recommendations"].append(
                        f"Increase savings by ${savings - available_for_savings:.2f}/month to reach 20% goal"
                    )

                if debt_to_income > 36:
                    budget_plan["recommendations"].append(
                        f"High debt-to-income ratio ({debt_to_income:.1f}%). Consider debt consolidation."
                    )

                if emergency_fund_goal < emergency_fund_needed:
                    monthly_needed = (emergency_fund_needed - emergency_fund_goal) / 12
                    budget_plan["recommendations"].append(
                        f"Build emergency fund: save ${monthly_needed:.2f}/month for 12 months"
                    )

                # Expense optimization suggestions
                largest_expense = max(expenses.items(), key=lambda x: x[1]) if expenses else None
                if largest_expense and largest_expense[1] > income * 0.35:
                    budget_plan["recommendations"].append(
                        f"Your {largest_expense[0]} expense (${largest_expense[1]:.2f}) is high. Consider cost reduction."
                    )

                return json.dumps(budget_plan, indent=2)
            except Exception as e:
                return f"Error creating budget plan: {str(e)}"

        return Tool(
            name="budget_planner",
            description="Create personalized budget plans with income and expense analysis",
            func=budget_planner,
        )

    def create_investment_analyzer(self) -> Tool:
        def investment_analyzer(symbol: str) -> str:
            """Analyze stocks with advanced metrics, sector comparison, and risk assessment"""
            try:
                stock = yf.Ticker(symbol.upper())
                info = stock.info
                hist = stock.history(period="1y")  # Reduced from 2y to 1y for speed

                if hist.empty:
                    return f"No data available for {symbol}"

                # Calculate key metrics
                current_price = info.get("currentPrice", hist["Close"].iloc[-1])
                pe_ratio = info.get("trailingPE", "N/A")
                pb_ratio = info.get("priceToBook", "N/A")
                dividend_yield = (info.get("dividendYield", 0) * 100 if info.get("dividendYield") else 0)
                market_cap = info.get("marketCap", "N/A")
                beta = info.get("beta", "N/A")
                sector = info.get("sector", "Unknown")
                industry = info.get("industry", "Unknown")

                # Advanced technical indicators
                sma_20 = hist["Close"].rolling(window=20).mean().iloc[-1]
                sma_50 = hist["Close"].rolling(window=50).mean().iloc[-1] if len(hist) >= 50 else None
                sma_200 = hist["Close"].rolling(window=200).mean().iloc[-1] if len(hist) >= 200 else None
                
                # RSI calculation
                delta = hist["Close"].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs)).iloc[-1]

                # Simplified MACD calculation
                ema_12 = hist["Close"].ewm(span=12).mean()
                ema_26 = hist["Close"].ewm(span=26).mean()
                macd = ema_12 - ema_26
                macd_signal = macd.ewm(span=9).mean()

                # Simplified Bollinger Bands (only what we need)
                bb_middle = hist["Close"].rolling(window=20).mean()
                bb_std_dev = hist["Close"].rolling(window=20).std()
                bb_upper = bb_middle + (bb_std_dev * 2)
                bb_lower = bb_middle - (bb_std_dev * 2)

                # Simplified volatility analysis
                volatility_30d = hist["Close"].pct_change().rolling(30).std().iloc[-1] * 100
                
                # Value at Risk (VaR) - 5% level
                returns = hist["Close"].pct_change().dropna()
                var_5 = returns.quantile(0.05) * 100

                # Performance metrics
                price_1m = hist["Close"].iloc[-22] if len(hist) >= 22 else None
                price_3m = hist["Close"].iloc[-66] if len(hist) >= 66 else None
                price_6m = hist["Close"].iloc[-132] if len(hist) >= 132 else None
                price_1y = hist["Close"].iloc[-252] if len(hist) >= 252 else None

                performance = {}
                if price_1m: performance["1_month"] = ((current_price - price_1m) / price_1m * 100)
                if price_3m: performance["3_month"] = ((current_price - price_3m) / price_3m * 100)
                if price_6m: performance["6_month"] = ((current_price - price_6m) / price_6m * 100)
                if price_1y: performance["1_year"] = ((current_price - price_1y) / price_1y * 100)

                # Sharpe ratio calculation (using risk-free rate of 4%)
                risk_free_rate = 0.04
                mean_return = returns.mean() * 252
                return_std = returns.std() * (252**0.5)
                sharpe_ratio = (mean_return - risk_free_rate) / return_std if return_std > 0 else 0

                # Risk assessment
                risk_score = 0
                risk_factors = []
                
                if volatility_30d > 30:
                    risk_score += 2
                    risk_factors.append("High volatility (>30%)")
                elif volatility_30d > 20:
                    risk_score += 1
                    risk_factors.append("Moderate volatility (20-30%)")

                if isinstance(beta, (int, float)):
                    if beta > 1.5:
                        risk_score += 2
                        risk_factors.append(f"High beta ({beta:.2f}) - market sensitive")
                    elif beta > 1.2:
                        risk_score += 1
                        risk_factors.append(f"Above-average beta ({beta:.2f})")

                if var_5 < -5:
                    risk_score += 2
                    risk_factors.append(f"High downside risk (VaR: {var_5:.1f}%)")

                # Enhanced recommendation logic
                recommendation = "HOLD"
                confidence = 50
                reasoning = []

                # Technical analysis
                if current_price < bb_lower.iloc[-1]:
                    recommendation = "BUY"
                    confidence += 20
                    reasoning.append("Price below Bollinger Band lower bound (oversold)")
                elif current_price > bb_upper.iloc[-1]:
                    recommendation = "SELL"
                    confidence += 15
                    reasoning.append("Price above Bollinger Band upper bound (overbought)")

                # RSI analysis
                if rsi < 30:
                    if recommendation != "SELL":
                        recommendation = "BUY"
                    confidence += 15
                    reasoning.append(f"RSI oversold ({rsi:.1f})")
                elif rsi > 70:
                    if recommendation != "BUY":
                        recommendation = "SELL"
                    confidence += 10
                    reasoning.append(f"RSI overbought ({rsi:.1f})")

                # MACD analysis
                if macd.iloc[-1] > macd_signal.iloc[-1] and macd.iloc[-2] <= macd_signal.iloc[-2]:
                    if recommendation != "SELL":
                        recommendation = "BUY"
                    confidence += 10
                    reasoning.append("MACD bullish crossover")

                # Fundamental analysis
                if isinstance(pe_ratio, (int, float)):
                    if pe_ratio < 15:
                        confidence += 10
                        reasoning.append("Low P/E ratio suggests undervaluation")
                    elif pe_ratio > 30:
                        confidence -= 5
                        reasoning.append("High P/E ratio suggests overvaluation")

                # Risk adjustment
                if risk_score >= 4:
                    if recommendation == "BUY":
                        recommendation = "HOLD"
                    confidence -= 15
                    reasoning.append("High risk profile suggests caution")

                analysis = {
                    "symbol": symbol.upper(),
                    "company_name": info.get("longName", symbol),
                    "sector": sector,
                    "industry": industry,
                    "current_price": f"${current_price:.2f}",
                    "market_cap": f"${market_cap:,.0f}" if isinstance(market_cap, (int, float)) else "N/A",
                    "fundamental_metrics": {
                        "pe_ratio": pe_ratio,
                        "pb_ratio": pb_ratio,
                        "dividend_yield": f"{dividend_yield:.2f}%",
                        "beta": beta,
                        "sharpe_ratio": f"{sharpe_ratio:.2f}",
                    },
                    "technical_indicators": {
                        "sma_20": f"${sma_20:.2f}",
                        "sma_50": f"${sma_50:.2f}" if sma_50 else "N/A",
                        "sma_200": f"${sma_200:.2f}" if sma_200 else "N/A",
                        "rsi": f"{rsi:.1f}",
                        "macd": f"{macd.iloc[-1]:.2f}",
                        "bollinger_position": "Lower" if current_price < bb_lower.iloc[-1] else "Upper" if current_price > bb_upper.iloc[-1] else "Middle",
                    },
                    "risk_assessment": {
                        "volatility_30d": f"{volatility_30d:.1f}%",
                        "value_at_risk_5%": f"{var_5:.1f}%",
                        "risk_score": f"{risk_score}/6",
                        "risk_factors": risk_factors,
                        "risk_level": "Low" if risk_score <= 1 else "Medium" if risk_score <= 3 else "High",
                    },
                    "price_levels": {
                        "52_week_high": f"${info.get('fiftyTwoWeekHigh', 'N/A')}",
                        "52_week_low": f"${info.get('fiftyTwoWeekLow', 'N/A')}",
                    },
                    "performance": {k: f"{v:.1f}%" for k, v in performance.items()},
                    "recommendation": {
                        "action": recommendation,
                        "confidence": f"{min(max(confidence, 20), 95)}%",
                        "reasoning": reasoning,
                        "target_allocation": "5-10%" if recommendation == "BUY" else "0-5%" if recommendation == "SELL" else "3-7%",
                    },
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }

                return json.dumps(analysis, indent=2)
            except Exception as e:
                return f"Error analyzing {symbol}: {str(e)}"

        return Tool(
            name="investment_analyzer",
            description="Analyze stocks and provide investment recommendations",
            func=investment_analyzer,
        )

    def create_expense_tracker(self) -> Tool:
        def expense_tracker(input_str: str) -> str:
            """Track and analyze expenses with advanced insights, trends, and predictions"""
            try:
                data = json.loads(input_str)
                expenses = data.get("expenses", [])
                historical_data = data.get("historical_expenses", [])
                budget_limits = data.get("budget_limits", {})

                # Combine current and historical data
                all_expenses = expenses + historical_data
                df = pd.DataFrame(all_expenses)

                if df.empty:
                    return "No expense data provided"

                # Ensure date column exists and is properly formatted
                if "date" in df.columns:
                    df["date"] = pd.to_datetime(df["date"])
                    df = df.sort_values("date")
                else:
                    # Add current date for expenses without dates
                    df["date"] = datetime.now()

                # Current period analysis
                current_df = pd.DataFrame(expenses) if expenses else pd.DataFrame()
                total_current = current_df["amount"].sum() if not current_df.empty else 0

                # Category analysis
                category_summary = df.groupby("category")["amount"].agg(["sum", "mean", "count", "std"]).to_dict("index")
                
                # Trend analysis (if historical data available)
                trends = {}
                predictions = {}
                
                if len(df) > 1 and "date" in df.columns:
                    # Monthly spending trends
                    df["month"] = df["date"].dt.to_period("M")
                    monthly_spending = df.groupby("month")["amount"].sum()
                    
                    if len(monthly_spending) > 1:
                        # Calculate month-over-month growth
                        mom_growth = monthly_spending.pct_change().iloc[-1] * 100
                        trends["monthly_growth"] = f"{mom_growth:.1f}%"
                        
                        # Simple linear trend prediction for next month
                        if len(monthly_spending) >= 3:
                            recent_trend = monthly_spending.tail(3).mean()
                            predictions["next_month_estimate"] = f"${recent_trend:.2f}"

                    # Category trends
                    for category in df["category"].unique():
                        cat_data = df[df["category"] == category].groupby("month")["amount"].sum()
                        if len(cat_data) > 1:
                            cat_trend = cat_data.pct_change().iloc[-1] * 100
                            trends[f"{category}_trend"] = f"{cat_trend:.1f}%"

                # Spending pattern analysis
                if "date" in df.columns:
                    df["day_of_week"] = df["date"].dt.day_name()
                    df["hour"] = df["date"].dt.hour
                    
                    spending_patterns = {
                        "busiest_day": df.groupby("day_of_week")["amount"].sum().idxmax(),
                        "peak_spending_hour": df.groupby("hour")["amount"].sum().idxmax(),
                    }
                else:
                    spending_patterns = {}

                # Budget analysis
                budget_analysis = {}
                if budget_limits:
                    for category, limit in budget_limits.items():
                        cat_spending = category_summary.get(category, {}).get("sum", 0)
                        budget_analysis[category] = {
                            "limit": f"${limit:.2f}",
                            "spent": f"${cat_spending:.2f}",
                            "remaining": f"${max(0, limit - cat_spending):.2f}",
                            "percentage_used": f"{(cat_spending / limit * 100):.1f}%" if limit > 0 else "N/A",
                            "status": "Over Budget" if cat_spending > limit else "Within Budget"
                        }

                # Anomaly detection (expenses significantly above average)
                anomalies = []
                if not df.empty:
                    for category in df["category"].unique():
                        cat_data = df[df["category"] == category]["amount"]
                        if len(cat_data) > 2:
                            mean_spending = cat_data.mean()
                            std_spending = cat_data.std()
                            threshold = mean_spending + (2 * std_spending)
                            
                            recent_anomalies = cat_data[cat_data > threshold]
                            if not recent_anomalies.empty:
                                anomalies.append({
                                    "category": category,
                                    "unusual_amount": f"${recent_anomalies.iloc[-1]:.2f}",
                                    "typical_range": f"${mean_spending:.2f} ± ${std_spending:.2f}"
                                })

                # Generate insights and recommendations
                insights = []
                recommendations = []

                # Top spending categories
                top_categories = sorted(category_summary.items(), key=lambda x: x[1]["sum"], reverse=True)[:3]
                category_strings = [f'{cat} (${data["sum"]:.2f})' for cat, data in top_categories]
                insights.append(f"Top 3 spending categories: {', '.join(category_strings)}")

                # Spending frequency analysis
                if not df.empty:
                    avg_transaction = df["amount"].mean()
                    insights.append(f"Average transaction: ${avg_transaction:.2f}")
                    
                    if avg_transaction > 100:
                        recommendations.append("Consider breaking down large expenses into smaller, more frequent transactions for better budget control")

                # Trend-based recommendations
                if "monthly_growth" in trends:
                    growth = float(trends["monthly_growth"].rstrip("%"))
                    if growth > 10:
                        recommendations.append(f"Spending increased {growth:.1f}% this month. Review discretionary expenses.")
                    elif growth < -10:
                        recommendations.append(f"Good job! Spending decreased {abs(growth):.1f}% this month.")

                # Budget recommendations
                for category, analysis in budget_analysis.items():
                    if "Over Budget" in analysis["status"]:
                        recommendations.append(f"Reduce {category} spending - currently over budget")
                    elif float(analysis["percentage_used"].rstrip("%")) > 80:
                        recommendations.append(f"Approaching {category} budget limit ({analysis['percentage_used']})")

                analysis_result = {
                    "current_period": {
                        "total_expenses": f"${total_current:.2f}",
                        "transaction_count": len(current_df) if not current_df.empty else 0,
                        "average_transaction": f"${(total_current / len(current_df)):.2f}" if not current_df.empty else "$0.00",
                    },
                    "category_analysis": {
                        category: {
                            "total": f"${data['sum']:.2f}",
                            "average": f"${data['mean']:.2f}",
                            "transactions": int(data['count']),
                            "variability": f"${data.get('std', 0):.2f}"
                        } for category, data in category_summary.items()
                    },
                    "trends": trends,
                    "predictions": predictions,
                    "spending_patterns": spending_patterns,
                    "budget_analysis": budget_analysis,
                    "anomalies": anomalies,
                    "insights": insights,
                    "recommendations": recommendations,
                    "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }

                return json.dumps(analysis_result, indent=2)

            except Exception as e:
                return f"Error tracking expenses: {str(e)}"

        return Tool(
            name="expense_tracker",
            description="Track and analyze expenses with detailed insights",
            func=expense_tracker,
        )

    def create_market_trends_analyzer(self) -> Tool:
        def market_trends(query: str) -> str:
            """Get comprehensive real-time market trends, news, and sector analysis"""
            try:
                # Get current year for search queries
                current_year = datetime.now().year
                
                # Status tracking for API calls
                status_updates = []
                
                # Optimized single comprehensive search instead of multiple calls
                comprehensive_query = f"stock market {query} trends analysis financial news {current_year} latest"
                
                # Get primary market information
                status_updates.append("🔍 Fetching latest market news via Tavily Search API...")
                market_news = self.tavily_search.run(comprehensive_query)
                status_updates.append("✅ Market news retrieved successfully")
                
                # Quick market indices check (reduced to just S&P 500 and NASDAQ for speed)
                index_data = {}
                market_sentiment = {"overall": "Unknown", "note": "Limited data"}
                
                try:
                    status_updates.append("📊 Fetching market indices via Yahoo Finance API...")
                    # Fetch only key indices for speed
                    key_indices = ["^GSPC", "^IXIC"]  # S&P 500, NASDAQ
                    
                    for index in key_indices:
                        index_names = {"^GSPC": "S&P 500", "^IXIC": "NASDAQ"}
                        status_updates.append(f"📈 Getting {index_names[index]} data...")
                        
                        ticker = yf.Ticker(index)
                        hist = ticker.history(period="2d")  # Reduced period for speed
                        if not hist.empty:
                            current = hist["Close"].iloc[-1]
                            prev = hist["Close"].iloc[-2] if len(hist) > 1 else current
                            change = ((current - prev) / prev * 100) if prev != 0 else 0
                            
                            index_data[index_names[index]] = {
                                "current": round(current, 2),
                                "change_pct": round(change, 2),
                                "direction": "📈" if change > 0 else "📉" if change < 0 else "➡️"
                            }
                    
                    status_updates.append("✅ Market indices data retrieved successfully")
                    
                    # Simple sentiment based on available indices
                    if index_data:
                        status_updates.append("🧠 Analyzing market sentiment...")
                        positive_count = sum(1 for data in index_data.values() if data["change_pct"] > 0)
                        total_count = len(index_data)
                        
                        if positive_count >= total_count * 0.75:
                            sentiment = "🟢 Bullish"
                        elif positive_count <= total_count * 0.25:
                            sentiment = "🔴 Bearish"
                        else:
                            sentiment = "🟡 Mixed"
                        
                        market_sentiment = {
                            "overall": sentiment,
                            "summary": f"{positive_count}/{total_count} indices positive"
                        }
                        status_updates.append("✅ Market sentiment analysis completed")
                        
                except Exception as index_error:
                    status_updates.append(f"❌ Error fetching market indices: {str(index_error)}")
                    index_data = {"error": f"Index data unavailable: {str(index_error)}"}
                
                # Extract key themes from search results
                status_updates.append("🔍 Analyzing key market themes...")
                key_themes = _extract_key_themes(market_news)
                status_updates.append("✅ Theme analysis completed")
                
                # Format output for better readability
                def format_search_results(results):
                    """Convert search results to readable format"""
                    if isinstance(results, list):
                        # Extract key information from search results
                        formatted = []
                        for item in results[:3]:  # Limit to top 3 results
                            if isinstance(item, dict):
                                title = item.get('title', 'No title')
                                content = item.get('content', item.get('snippet', 'No content'))
                                formatted.append(f"• {title}: {content[:200]}...")
                            else:
                                formatted.append(f"• {str(item)[:200]}...")
                        return "\n".join(formatted)
                    elif isinstance(results, str):
                        return results[:1000] + "..." if len(results) > 1000 else results
                    else:
                        return str(results)[:1000]
                
                status_updates.append("📋 Compiling final analysis report...")
                
                # Compile streamlined analysis
                analysis = {
                    "query": query,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "api_execution_log": status_updates,
                    "market_summary": format_search_results(market_news),
                    "key_indices": index_data,
                    "market_sentiment": market_sentiment,
                    "key_themes": key_themes,
                    "note": "Real-time API status tracking enabled"
                }
                
                status_updates.append("✅ Analysis report completed successfully")
                
                return json.dumps(analysis, indent=2, ensure_ascii=False)
                
            except Exception as e:
                return f"Error fetching market analysis: {str(e)}"
        
        def _extract_key_themes(news_text) -> list:
            """Extract key themes from market news"""
            themes = []
            keywords = {
                "earnings": ["earnings", "quarterly results", "revenue", "profit"],
                "fed_policy": ["federal reserve", "interest rates", "fed", "monetary policy"],
                "inflation": ["inflation", "cpi", "price increases", "cost of living"],
                "geopolitical": ["geopolitical", "war", "trade war", "sanctions"],
                "technology": ["ai", "artificial intelligence", "tech stocks", "innovation"],
                "recession": ["recession", "economic downturn", "market crash"],
            }
            
            # Handle both string and list inputs
            if isinstance(news_text, list):
                # Convert list to string
                news_text = " ".join(str(item) for item in news_text)
            elif not isinstance(news_text, str):
                # Convert other types to string
                news_text = str(news_text)
            
            news_lower = news_text.lower()
            for theme, terms in keywords.items():
                if any(term in news_lower for term in terms):
                    themes.append(theme.replace("_", " ").title())
            
            return themes[:5]  # Return top 5 themes

        return Tool(
            name="market_trends",
            description="Get real-time market trends and financial news",
            func=market_trends,
        )

    def create_portfolio_analyzer(self) -> Tool:
        def portfolio_analyzer(input_str: str) -> str:
            """Analyze portfolio performance and diversification"""
            try:
                data = json.loads(input_str)
                holdings = data.get("holdings", [])

                total_value = 0
                portfolio_data = []

                for holding in holdings:
                    symbol = holding["symbol"]
                    shares = holding["shares"]

                    stock = yf.Ticker(symbol)
                    current_price = stock.info.get("currentPrice", 0)
                    value = current_price * shares
                    total_value += value

                    portfolio_data.append(
                        {
                            "symbol": symbol,
                            "shares": shares,
                            "current_price": current_price,
                            "value": value,
                            "sector": stock.info.get("sector", "Unknown"),
                        }
                    )

                # Calculate allocations
                for item in portfolio_data:
                    item["allocation"] = (
                        (item["value"] / total_value * 100) if total_value > 0 else 0
                    )

                # Sector diversification
                df = pd.DataFrame(portfolio_data)
                sector_allocation = df.groupby("sector")["allocation"].sum().to_dict()

                analysis = {
                    "total_portfolio_value": f"${total_value:.2f}",
                    "holdings": portfolio_data,
                    "sector_allocation": sector_allocation,
                    "diversification_score": len(sector_allocation)
                    / 11
                    * 100,  # 11 major sectors
                    "recommendations": [],
                }

                # Add recommendations
                if len(holdings) < 5:
                    analysis["recommendations"].append(
                        "Consider diversifying with more holdings"
                    )

                max_allocation = max(item["allocation"] for item in portfolio_data)
                if max_allocation > 30:
                    analysis["recommendations"].append(
                        f"High concentration risk: largest holding is {max_allocation:.1f}%"
                    )

                return json.dumps(analysis, indent=2)

            except Exception as e:
                return f"Error analyzing portfolio: {str(e)}"

        return Tool(
            name="portfolio_analyzer",
            description="Analyze portfolio performance and diversification",
            func=portfolio_analyzer,
        )

    def get_all_tools(self) -> List[Tool]:
        return [
            self.create_budget_planner(),
            self.create_investment_analyzer(),
            self.create_expense_tracker(),
            self.create_market_trends_analyzer(),
            self.create_portfolio_analyzer(),
        ]
