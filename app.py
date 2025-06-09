import json
import os
import time
from pathlib import Path

import gradio as gr
from gradio import ChatMessage

from agents.financial_agent import FinancialAdvisorAgent
from agents.tools import FinancialTools

# Avatar configuration
AVATAR_IMAGES = (
    None,
    "./public/images/fin_logo.png",
)

# Initialize tools and agent
financial_tools = FinancialTools(tavily_api_key=os.getenv("TAVILY_API_KEY"))
tools = financial_tools.get_all_tools()

agent = FinancialAdvisorAgent(tools=tools, openai_api_key=os.getenv("OPENAI_API_KEY"))

gr.set_static_paths(paths=[(Path.cwd() / "public" / "images").absolute()])


def analyze_data_with_repl(data_type, data):
    """Analyze financial data using Python REPL with comprehensive insights"""

    if data_type == "budget":
        try:
            budget_data = json.loads(data)
            categories = list(budget_data.get("current_expenses", {}).keys())
            values = list(budget_data.get("current_expenses", {}).values())
            income = budget_data.get("monthly_income", budget_data.get("income", 0))

            if categories and values:
                total_expenses = sum(values)
                analysis_text = "💰 **Comprehensive Budget Analysis**\n\n"
                
                # Income vs Expenses Overview
                analysis_text += "## 📈 **Income vs Expenses Overview**\n"
                analysis_text += f"- **Monthly Income**: ${income:,.0f}\n"
                analysis_text += f"- **Total Expenses**: ${total_expenses:,.0f}\n"
                
                if income > 0:
                    remaining = income - total_expenses
                    savings_rate = (remaining / income * 100) if income > 0 else 0
                    
                    if remaining > 0:
                        analysis_text += f"- **💚 Surplus**: ${remaining:,.0f}\n"
                        analysis_text += f"- **💎 Savings Rate**: {savings_rate:.1f}%\n"
                    else:
                        analysis_text += f"- **🔴 Deficit**: ${abs(remaining):,.0f}\n"
                        analysis_text += f"- **⚠️ Overspending**: {abs(savings_rate):.1f}%\n"
                
                # Expense Breakdown with Progress Bars
                analysis_text += "\n## 💳 **Expense Breakdown**\n"
                for i, (category, amount) in enumerate(zip(categories, values)):
                    percentage = (amount / total_expenses * 100) if total_expenses > 0 else 0
                    income_percentage = (amount / income * 100) if income > 0 else 0
                    bar = "█" * min(int(percentage / 3), 30)  # Max 30 chars
                    
                    analysis_text += f"**{category.title()}**: ${amount:,.0f}\n"
                    analysis_text += f"  └─ {percentage:.1f}% of expenses | {income_percentage:.1f}% of income {bar}\n\n"
                
                # Financial Health Metrics
                analysis_text += "## 📊 **Financial Health Metrics**\n"
                avg_expense = total_expenses / len(values)
                largest_expense = max(values)
                smallest_expense = min(values)
                largest_category = categories[values.index(largest_expense)]
                smallest_category = categories[values.index(smallest_expense)]
                
                analysis_text += f"- **Average Category Expense**: ${avg_expense:,.0f}\n"
                analysis_text += f"- **Highest Expense**: {largest_category} (${largest_expense:,.0f})\n"
                analysis_text += f"- **Lowest Expense**: {smallest_category} (${smallest_expense:,.0f})\n"
                analysis_text += f"- **Expense Range**: ${largest_expense - smallest_expense:,.0f}\n"
                
                # Budget Recommendations
                analysis_text += "\n## 💡 **Smart Budget Insights**\n"
                
                # 50/30/20 Rule Analysis
                if income > 0:
                    needs_target = income * 0.50
                    wants_target = income * 0.30
                    savings_target = income * 0.20
                    
                    analysis_text += f"**50/30/20 Rule Comparison:**\n"
                    analysis_text += f"- Needs Target (50%): ${needs_target:,.0f}\n"
                    analysis_text += f"- Wants Target (30%): ${wants_target:,.0f}\n"
                    analysis_text += f"- Savings Target (20%): ${savings_target:,.0f}\n"
                    
                    if savings_rate >= 20:
                        analysis_text += "✅ **Excellent savings rate!**\n"
                    elif savings_rate >= 10:
                        analysis_text += "⚠️ **Good savings, aim for 20%**\n"
                    else:
                        analysis_text += "🔴 **Consider reducing expenses to save more**\n"
                
                # Category Warnings
                for category, amount in zip(categories, values):
                    if income > 0:
                        cat_percentage = (amount / income * 100)
                        if category.lower() in ['rent', 'housing'] and cat_percentage > 30:
                            analysis_text += f"⚠️ **Housing costs high**: {cat_percentage:.1f}% (recommend <30%)\n"
                        elif category.lower() in ['food', 'dining'] and cat_percentage > 15:
                            analysis_text += f"⚠️ **Food costs high**: {cat_percentage:.1f}% (recommend <15%)\n"
                
                return analysis_text
        except Exception as e:
            return f"Error analyzing budget data: {str(e)}"

    elif data_type == "portfolio":
        try:
            portfolio_data = json.loads(data)
            holdings = portfolio_data.get("holdings", [])
            total_value = sum(holding.get("value", 0) for holding in holdings)
            
            analysis_text = "📊 **Advanced Portfolio Analysis**\n\n"
            
            # Portfolio Overview
            analysis_text += "## 💼 **Portfolio Overview**\n"
            analysis_text += f"- **Total Portfolio Value**: ${total_value:,.2f}\n"
            analysis_text += f"- **Number of Holdings**: {len(holdings)}\n"
            
            if holdings:
                values = [holding.get("value", 0) for holding in holdings]
                avg_holding = sum(values) / len(values)
                max_holding = max(values)
                min_holding = min(values)
                
                analysis_text += f"- **Average Holding Size**: ${avg_holding:,.2f}\n"
                analysis_text += f"- **Largest Position**: ${max_holding:,.2f}\n"
                analysis_text += f"- **Smallest Position**: ${min_holding:,.2f}\n"
            
            # Detailed Holdings breakdown
            analysis_text += "\n## 📈 **Holdings Breakdown**\n"
            sorted_holdings = sorted(holdings, key=lambda x: x.get("value", 0), reverse=True)
            
            for i, holding in enumerate(sorted_holdings, 1):
                symbol = holding.get("symbol", "Unknown")
                value = holding.get("value", 0)
                shares = holding.get("shares", 0)
                allocation = holding.get("allocation", (value/total_value*100) if total_value > 0 else 0)
                sector = holding.get("sector", "Unknown")
                
                # Calculate position concentration risk
                risk_level = "🟢 Low" if allocation < 10 else "🟡 Medium" if allocation < 25 else "🔴 High"
                
                analysis_text += f"**#{i} {symbol}** - {sector}\n"
                analysis_text += f"  └─ Value: ${value:,.2f} | Shares: {shares:,.0f} | Weight: {allocation:.1f}%\n"
                analysis_text += f"  └─ Concentration Risk: {risk_level}\n\n"
            
            # Sector analysis with advanced metrics
            sectors = {}
            sector_values = {}
            for holding in holdings:
                sector = holding.get("sector", "Unknown")
                allocation = holding.get("allocation", 0)
                value = holding.get("value", 0)
                
                sectors[sector] = sectors.get(sector, 0) + allocation
                sector_values[sector] = sector_values.get(sector, 0) + value
            
            if sectors:
                analysis_text += "## 🏭 **Sector Diversification Analysis**\n"
                sorted_sectors = sorted(sectors.items(), key=lambda x: x[1], reverse=True)
                
                for sector, allocation in sorted_sectors:
                    bar = "█" * min(int(allocation / 2), 30)
                    value = sector_values.get(sector, 0)
                    
                    # Sector concentration assessment
                    if allocation > 40:
                        risk_emoji = "🔴"
                        risk_text = "Over-concentrated"
                    elif allocation > 25:
                        risk_emoji = "🟡"
                        risk_text = "Moderate concentration"
                    else:
                        risk_emoji = "🟢"
                        risk_text = "Well diversified"
                    
                    analysis_text += f"**{sector}**: {allocation:.1f}% (${value:,.2f}) {risk_emoji}\n"
                    analysis_text += f"  └─ {bar} {risk_text}\n\n"
            
            # Portfolio Health Metrics
            analysis_text += "## 🎯 **Portfolio Health Assessment**\n"
            
            # Diversification Score
            num_sectors = len(sectors)
            if num_sectors >= 8:
                diversification = "🟢 Excellent"
            elif num_sectors >= 5:
                diversification = "🟡 Good"
            else:
                diversification = "🔴 Poor"
            
            analysis_text += f"- **Sector Diversification**: {diversification} ({num_sectors} sectors)\n"
            
            # Concentration Risk
            if holdings:
                top_3_allocation = sum(sorted([h.get("allocation", 0) for h in holdings], reverse=True)[:3])
                if top_3_allocation > 60:
                    concentration_risk = "🔴 High"
                elif top_3_allocation > 40:
                    concentration_risk = "🟡 Medium"
                else:
                    concentration_risk = "🟢 Low"
                
                analysis_text += f"- **Concentration Risk**: {concentration_risk} (Top 3: {top_3_allocation:.1f}%)\n"
            
            # Portfolio Recommendations
            analysis_text += "\n## 💡 **Portfolio Optimization Recommendations**\n"
            
            # Check for over-concentration
            for holding in holdings:
                allocation = holding.get("allocation", 0)
                if allocation > 25:
                    analysis_text += f"⚠️ **{holding.get('symbol', 'Unknown')}** is over-weighted at {allocation:.1f}% (consider rebalancing)\n"
            
            # Sector recommendations
            for sector, allocation in sectors.items():
                if allocation > 40:
                    analysis_text += f"⚠️ **{sector}** sector over-weighted at {allocation:.1f}% (consider diversification)\n"
            
            # Diversification suggestions
            if num_sectors < 5:
                analysis_text += "💡 **Consider adding exposure to more sectors for better diversification**\n"
            
            if len(holdings) < 10:
                analysis_text += "💡 **Consider adding more holdings to reduce single-stock risk**\n"
            
            return analysis_text
        except Exception as e:
            return f"Error analyzing portfolio data: {str(e)}"

    elif data_type == "stock":
        try:
            stock_data = json.loads(data)
            symbol = stock_data.get("symbol", "Unknown")
            price_str = stock_data.get("current_price", "0")
            
            analysis_text = f"📈 **Comprehensive Stock Analysis: {symbol}**\n\n"
            
            # Company Overview
            analysis_text += "## 🏢 **Company Overview**\n"
            analysis_text += f"- **Symbol**: {symbol}\n"
            analysis_text += f"- **Current Price**: {price_str}\n"
            analysis_text += f"- **Company**: {stock_data.get('company_name', 'N/A')}\n"
            analysis_text += f"- **Sector**: {stock_data.get('sector', 'N/A')}\n"
            analysis_text += f"- **Industry**: {stock_data.get('industry', 'N/A')}\n"
            analysis_text += f"- **Market Cap**: {stock_data.get('market_cap', 'N/A')}\n\n"
            
            # Financial Metrics
            financials = stock_data.get("financials", {})
            if financials:
                analysis_text += "## 💹 **Key Financial Metrics**\n"
                
                # Valuation metrics
                pe_ratio = financials.get("pe_ratio", "N/A")
                pb_ratio = financials.get("pb_ratio", "N/A")
                ps_ratio = financials.get("ps_ratio", "N/A")
                
                analysis_text += f"- **P/E Ratio**: {pe_ratio}"
                if pe_ratio != "N/A" and isinstance(pe_ratio, (int, float)):
                    if pe_ratio < 15:
                        analysis_text += " 🟢 (Undervalued)"
                    elif pe_ratio > 25:
                        analysis_text += " 🔴 (Potentially Overvalued)"
                    else:
                        analysis_text += " 🟡 (Fairly Valued)"
                analysis_text += "\n"
                
                analysis_text += f"- **P/B Ratio**: {pb_ratio}\n"
                analysis_text += f"- **P/S Ratio**: {ps_ratio}\n"
                
                # Profitability metrics
                analysis_text += f"- **ROE**: {financials.get('roe', 'N/A')}\n"
                analysis_text += f"- **ROA**: {financials.get('roa', 'N/A')}\n"
                analysis_text += f"- **Profit Margin**: {financials.get('profit_margin', 'N/A')}\n"
                analysis_text += f"- **Revenue Growth**: {financials.get('revenue_growth', 'N/A')}\n\n"
            
            # Performance analysis with trend indicators
            performance = stock_data.get("performance", {})
            if performance:
                analysis_text += "## 📊 **Performance Analysis**\n"
                
                periods = ["1d", "1w", "1m", "3m", "6m", "1y", "ytd"]
                for period in periods:
                    if period in performance:
                        return_pct = performance[period]
                        
                        # Add trend indicators
                        if isinstance(return_pct, str) and "%" in return_pct:
                            try:
                                pct_value = float(return_pct.replace("%", ""))
                                if pct_value > 0:
                                    trend = "📈"
                                elif pct_value < 0:
                                    trend = "📉"
                                else:
                                    trend = "➡️"
                            except:
                                trend = ""
                        else:
                            trend = ""
                        
                        analysis_text += f"- **{period.upper()}**: {return_pct} {trend}\n"
                analysis_text += "\n"
            
            # Advanced Risk Assessment
            risk_data = stock_data.get("risk_assessment", {})
            if risk_data:
                analysis_text += "## ⚠️ **Risk Assessment**\n"
                
                risk_level = risk_data.get('risk_level', 'N/A')
                volatility = risk_data.get('volatility_30d', 'N/A')
                beta = risk_data.get('beta', 'N/A')
                
                # Risk level with emoji indicators
                if risk_level.lower() == "low":
                    risk_emoji = "🟢"
                elif risk_level.lower() == "medium":
                    risk_emoji = "🟡"
                elif risk_level.lower() == "high":
                    risk_emoji = "🔴"
                else:
                    risk_emoji = ""
                
                analysis_text += f"- **Risk Level**: {risk_level} {risk_emoji}\n"
                analysis_text += f"- **30-Day Volatility**: {volatility}\n"
                analysis_text += f"- **Beta**: {beta}"
                
                if beta != "N/A" and isinstance(beta, (int, float)):
                    if beta > 1.2:
                        analysis_text += " (High volatility vs market)"
                    elif beta < 0.8:
                        analysis_text += " (Low volatility vs market)"
                    else:
                        analysis_text += " (Similar to market)"
                analysis_text += "\n\n"
            
            # Technical Analysis
            technical = stock_data.get("technical_analysis", {})
            if technical:
                analysis_text += "## 📈 **Technical Analysis**\n"
                analysis_text += f"- **50-Day MA**: {technical.get('ma_50', 'N/A')}\n"
                analysis_text += f"- **200-Day MA**: {technical.get('ma_200', 'N/A')}\n"
                analysis_text += f"- **RSI**: {technical.get('rsi', 'N/A')}\n"
                analysis_text += f"- **Support Level**: {technical.get('support', 'N/A')}\n"
                analysis_text += f"- **Resistance Level**: {technical.get('resistance', 'N/A')}\n\n"
            
            # Investment Recommendation with detailed reasoning
            recommendation = stock_data.get("recommendation", {})
            if recommendation:
                action = recommendation.get('action', 'N/A')
                confidence = recommendation.get('confidence', 'N/A')
                reasoning = recommendation.get('reasoning', '')
                
                analysis_text += "## 💡 **Investment Recommendation**\n"
                
                # Action with emoji
                if action.lower() == "buy":
                    action_emoji = "🟢"
                elif action.lower() == "sell":
                    action_emoji = "🔴"
                elif action.lower() == "hold":
                    action_emoji = "🟡"
                else:
                    action_emoji = ""
                
                analysis_text += f"- **Action**: {action} {action_emoji}\n"
                analysis_text += f"- **Confidence**: {confidence}\n"
                
                if reasoning:
                    analysis_text += f"- **Reasoning**: {reasoning}\n"
                
                analysis_text += "\n"
            
            # Additional Investment Considerations
            analysis_text += "## 🎯 **Investment Considerations**\n"
            
            # Dividend info
            dividend_yield = stock_data.get("dividend_yield", "N/A")
            if dividend_yield != "N/A":
                analysis_text += f"- **Dividend Yield**: {dividend_yield}\n"
            
            # Analyst ratings
            analyst_rating = stock_data.get("analyst_rating", "N/A")
            if analyst_rating != "N/A":
                analysis_text += f"- **Analyst Rating**: {analyst_rating}\n"
            
            # Price targets
            price_target = stock_data.get("price_target", "N/A")
            if price_target != "N/A":
                analysis_text += f"- **Price Target**: {price_target}\n"
            
            # ESG score
            esg_score = stock_data.get("esg_score", "N/A")
            if esg_score != "N/A":
                analysis_text += f"- **ESG Score**: {esg_score}\n"
            
            return analysis_text
        except Exception as e:
            return f"Error analyzing stock data: {str(e)}"

    return None


def determine_intended_tool(message):
    """Determine which tool the AI intends to use based on the message"""
    message_lower = message.lower()
    
    tool_detection_map = {
        "budget_planner": ["budget", "income", "expense", "spending", "allocat", "monthly", "plan", "financial plan", "money"],
        "investment_analyzer": ["stock", "invest", "buy", "sell", "analyze", "AAPL", "GOOGL", "TSLA", "share", "equity"],
        "portfolio_analyzer": ["portfolio", "holdings", "allocation", "diversif", "asset", "position"],
        "market_trends": ["market", "trend", "news", "sector", "economic", "latest", "current"],
        "expense_tracker": ["track", "expense", "spending", "categoriz", "cost"]
    }
    
    tool_names = {
        "budget_planner": "Budget Planner",
        "investment_analyzer": "Investment Analyzer", 
        "expense_tracker": "Expense Tracker",
        "market_trends": "Market Trends Analyzer",
        "portfolio_analyzer": "Portfolio Analyzer",
    }
    
    for tool_key, keywords in tool_detection_map.items():
        if any(keyword in message_lower for keyword in keywords):
            return tool_key, tool_names.get(tool_key, tool_key)
    
    return None, None


def determine_response_type(message):
    """Determine if user wants detailed report or short response"""
    message_lower = message.lower()
    
    # Keywords indicating detailed response preference
    detailed_keywords = [
        "detailed", "detail", "comprehensive", "thorough", "in-depth", "full analysis", 
        "complete", "report", "breakdown", "explain", "elaborate", "deep dive",
        "extensive", "detailed analysis", "full report", "comprehensive report"
    ]
    
    # Keywords indicating short response preference  
    short_keywords = [
        "quick", "brief", "short", "summary", "concise", "simple", "fast",
        "just tell me", "quickly", "in short", "tldr", "bottom line"
    ]
    
    # Check for detailed indicators first
    if any(keyword in message_lower for keyword in detailed_keywords):
        return "detailed"
    
    # Check for short indicators
    if any(keyword in message_lower for keyword in short_keywords):
        return "short"
    
    # Default to short response
    return "short"


def process_financial_query(message, history):
    """Process user queries through the financial agent with streaming response"""
    # Get the actual user message from the last entry in history
    if not history or len(history) == 0:
        return history

    # Extract the last user message
    last_user_message = None
    for msg in reversed(history):
        if msg["role"] == "user":
            last_user_message = msg["content"]
            break

    if not last_user_message:
        return history

    # Convert Gradio history to agent format (excluding the last user message we just added)
    agent_history = []
    for i, msg in enumerate(history[:-1]):  # Exclude the last message
        agent_history.append(
            {
                "role": msg["role"],
                "content": msg["content"]
                if isinstance(msg["content"], str)
                else str(msg["content"]),
            }
        )

    # Start timer
    start_time = time.time()
    init_message_start_index = len(history)
    
    try:
        # Show what tool will be used and processing status
        intended_tool_key, intended_tool_name = determine_intended_tool(last_user_message)
        response_type = determine_response_type(last_user_message)
        
        # Always show status for all tools with expected time estimates
        if intended_tool_name:
            if intended_tool_key == "market_trends":
                status_msg = f"🔍 Fetching market news & analyzing trends (estimated 20-30 seconds)..."
            elif intended_tool_key == "investment_analyzer":
                status_msg = f"📈 Analyzing stock data & calculating metrics (estimated 10-15 seconds)..."
            elif intended_tool_key == "budget_planner":
                status_msg = f"💰 Processing budget analysis (estimated 5-10 seconds)..."
            elif intended_tool_key == "portfolio_analyzer":
                status_msg = f"📊 Analyzing portfolio data (estimated 8-12 seconds)..."
            elif intended_tool_key == "expense_tracker":
                status_msg = f"💳 Processing expense analysis (estimated 5-10 seconds)..."
            else:
                status_msg = f"🔄 Using {intended_tool_name} (estimated 5-15 seconds)..."
            
            history.append(ChatMessage(role="assistant", content=status_msg))
            yield history
        else:
            # If no tool detected, show generic processing message
            history.append(ChatMessage(role="assistant", content=f"🧠 Processing your request (estimated 10-15 seconds)..."))
            yield history
        
        # Process message through agent
        response, tool_used, tool_result, all_tools, all_results = agent.process_message_with_details(
            last_user_message, agent_history
        )
        
        # Clear the processing message now that tool is complete
        if len(history) > init_message_start_index:
            history.pop()  # Remove the processing message
        # Step 5: Show tool execution results
        if all_tools and all_results:
            # Remove initialization messages but keep all previous conversation and tool info
            history = history[:init_message_start_index]
            
            tool_names = {
                "budget_planner": "Budget Planner",
                "investment_analyzer": "Investment Analyzer", 
                "expense_tracker": "Expense Tracker",
                "market_trends": "Market Trends Analyzer",
                "portfolio_analyzer": "Portfolio Analyzer",
            }
            
            tool_emojis = {
                "Budget Planner": "💰",
                "Investment Analyzer": "📈", 
                "Expense Tracker": "💳",
                "Market Trends Analyzer": "📰",
                "Portfolio Analyzer": "📊",
            }
            
            # Show results for all tools used
            for i, (used_tool, result) in enumerate(zip(all_tools, all_results)):
                tool_display_name = tool_names.get(used_tool, used_tool)
                
                if result:
                    # Format tool result for display
                    try:
                        import json

                        if result.startswith("{") or result.startswith("["):
                            # Pretty format JSON output
                            parsed_result = json.loads(result)
                            # Truncate very long results for display
                            if len(str(parsed_result)) > 2000:
                                # Show summary for long results
                                if isinstance(parsed_result, dict):
                                    summary = {
                                        k: f"[{type(v).__name__}]"
                                        if isinstance(v, (list, dict))
                                        else v
                                        for k, v in list(parsed_result.items())[:10]
                                    }
                                    display_result = f"```json\n{json.dumps(summary, indent=2)}\n... (truncated)\n```"
                                else:
                                    display_result = f"```json\n{json.dumps(parsed_result, indent=2)[:1000]}...\n```"
                            else:
                                formatted_result = json.dumps(parsed_result, indent=2)
                                display_result = f"```json\n{formatted_result}\n```"
                        else:
                            # Truncate non-JSON results
                            display_result = (
                                result[:1000] + "..."
                                if len(result) > 1000
                                else result
                            )
                    except Exception as e:
                        display_result = (
                            str(result)[:1000] + "..."
                            if len(str(result)) > 1000
                            else str(result)
                        )

                    tool_emoji = tool_emojis.get(tool_display_name, "🔧")
                    
                    collapsible_content = f"""
<details>
<summary><strong>{tool_emoji} {tool_display_name} Results</strong> - Click to expand</summary>

{display_result}

</details>
"""
                    
                    history.append(ChatMessage(
                        role="assistant",
                        content=collapsible_content,
                    ))
                    yield history

        # Add visualization for all applicable tools
        if all_tools and all_results:
            for used_tool, result in zip(all_tools, all_results):
                if result and used_tool in ["budget_planner", "portfolio_analyzer", "investment_analyzer"]:
                    viz_type = {
                        "budget_planner": "budget",
                        "portfolio_analyzer": "portfolio", 
                        "investment_analyzer": "stock",
                    }.get(used_tool)

                    try:
                        analysis_data = analyze_data_with_repl(viz_type, result)

                        if analysis_data:
                            tool_display_name = {
                                "budget_planner": "Budget",
                                "portfolio_analyzer": "Portfolio",
                                "investment_analyzer": "Stock",
                            }.get(used_tool, "Data")
                            
                            # Create collapsible data analysis output
                            collapsible_analysis = f"""
<details>
<summary><strong>🔍 {tool_display_name} Data Analysis</strong> - Click to expand</summary>

{analysis_data}

</details>
"""
                            
                            history.append(ChatMessage(
                                role="assistant",
                                content=collapsible_analysis,
                            ))
                            yield history

                    except Exception as e:
                        # Silently continue if analysis fails
                        pass

        # Stream the final response in real-time using LLM streaming
        if tool_used and tool_result:
            # Use real LLM streaming with response type
            streaming_content = ""
            history.append(ChatMessage(role="assistant", content=""))
            
            for chunk in agent.stream_response(last_user_message, tool_result, tool_used, response_type):
                streaming_content += chunk
                history[-1] = ChatMessage(role="assistant", content=streaming_content)
                yield history
        else:
            # Fallback for non-streaming response
            history.append(ChatMessage(role="assistant", content=response))
            yield history

        elapsed = time.time() - start_time

    except Exception as e:
        elapsed = time.time() - start_time
        history[-1] = ChatMessage(
            role="assistant",
            content=f"I encountered an error while processing your request: {str(e)}. Please try rephrasing your question.",
            metadata={"title": f"💥 Error ({elapsed:.1f}s)"},
        )
        yield history


# Create the Gradio interface
with gr.Blocks(theme=gr.themes.Base(), title="Financial Advisory Agent") as demo:
    gr.HTML("""<center><img src="/gradio_api/file=public/images/fin_logo.png" alt="Fin Logo" style="width: 50px; vertical-align: middle;">
    <h1 style="text-align: center;">AI Financial Advisory Agent</h1>
    Your AI-powered financial advisor for budgeting, investments, expense tracking, portfolio analysis, and market trends.
                </center>
    """)

    chatbot = gr.Chatbot(
        type="messages",
        scale=2,
        height=400,
        avatar_images=AVATAR_IMAGES,
        show_copy_button=True,
    )

    with gr.Row(equal_height=True):
        msg = gr.Textbox(
            placeholder="Ask me about budgeting, investments, or any financial topic...",
            show_label=False,
            scale=19,
            autofocus=True,
        )
        submit = gr.Button("Send", variant="primary", scale=1, min_width=60)

    # Example queries
    example_queries = [
        "Analyze AAPL stock and tell me if it's a good investment",
        "Help me create a budget with $5000 monthly income and expenses: rent $1500, food $500, utilities $200",
        "What are the latest market trends in tech stocks?",
        "Analyze my portfolio: {'holdings': [{'symbol': 'AAPL', 'shares': 100}, {'symbol': 'GOOGL', 'shares': 50}]}",
    ]

    gr.Examples(examples=example_queries, inputs=msg, label="Example Queries")

    # Handle message submission
    def user_submit(message, history):
        if not message.strip():
            return "", history, gr.update(interactive=True), gr.update(interactive=True)
        history = history + [ChatMessage(role="user", content=message)]
        return "", history, gr.update(interactive=False), gr.update(interactive=False)

    def enable_input():
        return gr.update(interactive=True), gr.update(interactive=True)

    # Connect events
    submit_event = (
        msg.submit(user_submit, [msg, chatbot], [msg, chatbot, msg, submit])
        .then(process_financial_query, [msg, chatbot], chatbot)
        .then(enable_input, [], [msg, submit])
    )

    click_event = (
        submit.click(user_submit, [msg, chatbot], [msg, chatbot, msg, submit])
        .then(process_financial_query, [msg, chatbot], chatbot)
        .then(enable_input, [], [msg, submit])
    )

    # Add like functionality for feedback
    def like_handler(evt: gr.LikeData):
        pass

    chatbot.like(like_handler)

if __name__ == "__main__":
    demo.launch(debug=True)
