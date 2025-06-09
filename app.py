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
    """Analyze financial data using Python REPL without visualization"""

    fig = None

    if data_type == "budget":
        try:
            budget_data = json.loads(data)
            categories = list(budget_data.get("current_expenses", {}).keys())
            values = list(budget_data.get("current_expenses", {}).values())

            if categories and values:
                # Calculate analysis using Python
                total = sum(values)
                analysis_text = "📊 **Budget Analysis**\n\n"
                
                for i, (category, amount) in enumerate(zip(categories, values)):
                    percentage = (amount / total * 100) if total > 0 else 0
                    bar = "█" * int(percentage / 5)
                    analysis_text += f"**{category.title()}**: ${amount:,.0f} ({percentage:.1f}%) {bar}\n"
                
                # Add summary statistics
                avg_expense = total / len(values)
                largest_expense = max(values)
                largest_category = categories[values.index(largest_expense)]
                
                analysis_text += f"\n**Summary:**\n"
                analysis_text += f"- Total Expenses: ${total:,.0f}\n"
                analysis_text += f"- Average per Category: ${avg_expense:,.0f}\n"
                analysis_text += f"- Largest Expense: {largest_category} (${largest_expense:,.0f})\n"
                
                return analysis_text
        except Exception as e:
            return f"Error analyzing budget data: {str(e)}"

    elif data_type == "portfolio":
        try:
            portfolio_data = json.loads(data)
            holdings = portfolio_data.get("holdings", [])
            total_value = sum(holding.get("value", 0) for holding in holdings)
            
            analysis_text = "📊 **Portfolio Analysis**\n\n"
            
            # Holdings breakdown
            for holding in holdings:
                symbol = holding.get("symbol", "Unknown")
                value = holding.get("value", 0)
                allocation = holding.get("allocation", 0)
                analysis_text += f"**{symbol}**: ${value:,.2f} ({allocation:.1f}%)\n"
            
            # Sector analysis
            sectors = {}
            for holding in holdings:
                sector = holding.get("sector", "Unknown")
                sectors[sector] = sectors.get(sector, 0) + holding.get("allocation", 0)
            
            if sectors:
                analysis_text += "\n**Sector Allocation:**\n"
                for sector, allocation in sorted(sectors.items(), key=lambda x: x[1], reverse=True):
                    bar = "█" * int(allocation / 10)
                    analysis_text += f"- {sector}: {allocation:.1f}% {bar}\n"
            
            analysis_text += f"\n**Total Portfolio Value**: ${total_value:,.2f}\n"
            
            return analysis_text
        except Exception as e:
            return f"Error analyzing portfolio data: {str(e)}"

    elif data_type == "stock":
        try:
            stock_data = json.loads(data)
            symbol = stock_data.get("symbol", "Unknown")
            price_str = stock_data.get("current_price", "0")
            
            analysis_text = f"📊 **Stock Analysis for {symbol}**\n\n"
            
            # Basic info
            analysis_text += f"**Current Price**: {price_str}\n"
            analysis_text += f"**Company**: {stock_data.get('company_name', 'N/A')}\n"
            analysis_text += f"**Sector**: {stock_data.get('sector', 'N/A')}\n\n"
            
            # Performance metrics
            performance = stock_data.get("performance", {})
            if performance:
                analysis_text += "**Performance:**\n"
                for period, return_pct in performance.items():
                    analysis_text += f"- {period.replace('_', ' ').title()}: {return_pct}\n"
            
            # Risk assessment
            risk_data = stock_data.get("risk_assessment", {})
            if risk_data:
                analysis_text += f"\n**Risk Level**: {risk_data.get('risk_level', 'N/A')}\n"
                analysis_text += f"**30d Volatility**: {risk_data.get('volatility_30d', 'N/A')}\n"
            
            # Recommendation
            recommendation = stock_data.get("recommendation", {})
            if recommendation:
                analysis_text += f"\n**Recommendation**: {recommendation.get('action', 'N/A')}\n"
                analysis_text += f"**Confidence**: {recommendation.get('confidence', 'N/A')}\n"
            
            return analysis_text
        except Exception as e:
            return f"Error analyzing stock data: {str(e)}"

    return None


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

    # Show processing status with timer
    def update_timer(base_message, start_time):
        elapsed = time.time() - start_time
        return f"{base_message} ({elapsed:.1f}s)"

    # Show processing animation with actual work happening
    processing_messages = [
        "🔄 Assistant is analyzing your request...",
        "🔍 Understanding your financial query...", 
        "🧠 Processing financial data...",
        "⚙️ Activating financial tools..."
    ]
    
    init_message_start_index = len(history)
    
    # Show first message and start processing
    elapsed = time.time() - start_time
    history.append(ChatMessage(role="assistant", content=f"{processing_messages[0]} ({elapsed:.1f}s)"))
    yield history
    
    try:
        # Show animation messages while doing actual processing
        for i, msg in enumerate(processing_messages[1:], 1):
            elapsed = time.time() - start_time
            history[-1] = ChatMessage(role="assistant", content=f"{msg} ({elapsed:.1f}s)")
            yield history
            time.sleep(1.0)  # Shorter delay
        
        # Process message through agent using the actual user message
        response, tool_used, tool_result = agent.process_message_with_details(
            last_user_message, agent_history
        )
        # Show which tool is being used with enhanced status messages
        if tool_used:
            tool_names = {
                "budget_planner": "Budget Planner",
                "investment_analyzer": "Investment Analyzer", 
                "expense_tracker": "Expense Tracker",
                "market_trends": "Market Trends Analyzer",
                "portfolio_analyzer": "Portfolio Analyzer",
            }
            tool_display_name = tool_names.get(tool_used, tool_used)
            
            # Skip tool processing animation to make it faster
            pass

            # Show tool output with metadata
            if tool_result:
                # Remove initialization messages but keep all previous conversation and tool info
                # Remove the initialization animation messages that were added
                history = history[:init_message_start_index]
                
                # Don't show tool activation message, go directly to results
                
                # Format tool result for display
                try:
                    import json

                    if tool_result.startswith("{") or tool_result.startswith("["):
                        # Pretty format JSON output
                        parsed_result = json.loads(tool_result)
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
                            tool_result[:1000] + "..."
                            if len(tool_result) > 1000
                            else tool_result
                        )
                except Exception as e:
                    display_result = (
                        str(tool_result)[:1000] + "..."
                        if len(str(tool_result)) > 1000
                        else str(tool_result)
                    )

                elapsed = time.time() - start_time
                
                # Create collapsible tool output with specific emojis for each tool
                tool_emojis = {
                    "Budget Planner": "💰",
                    "Investment Analyzer": "📈", 
                    "Expense Tracker": "💳",
                    "Market Trends Analyzer": "📰",
                    "Portfolio Analyzer": "📊",
                }
                tool_emoji = tool_emojis.get(tool_display_name, "🔧")
                
                collapsible_content = f"""
<details>
<summary><strong>{tool_emoji} {tool_display_name} Results ({elapsed:.1f}s)</strong> - Click to expand</summary>

{display_result}

</details>
"""
                
                history.append(ChatMessage(
                    role="assistant",
                    content=collapsible_content,
                ))
                yield history

        # Add visualization if applicable
        if tool_result and tool_used in [
            "budget_planner",
            "portfolio_analyzer",
            "investment_analyzer",
        ]:
            viz_type = {
                "budget_planner": "budget",
                "portfolio_analyzer": "portfolio",
                "investment_analyzer": "stock",
            }.get(tool_used)

            try:
                analysis_data = analyze_data_with_repl(viz_type, tool_result)

                if analysis_data:
                    elapsed = time.time() - start_time
                    
                    # Create collapsible data analysis output
                    collapsible_analysis = f"""
<details>
<summary><strong>🔍 Data Analysis ({elapsed:.1f}s)</strong> - Click to expand</summary>

{analysis_data}

</details>
"""
                    
                    history.append(ChatMessage(
                        role="assistant",
                        content=collapsible_analysis,
                    ))
                    yield history
                else:
                    history.pop()

            except Exception as e:
                history.pop()

        # Show response generation with timer
        elapsed = time.time() - start_time
        history.append(
            ChatMessage(
                role="assistant", content=f"✍️ Generating response... ({elapsed:.1f}s)"
            )
        )
        yield history
        time.sleep(3)

        # Stream the final response
        words = response.split()
        streamed_content = ""

        for i, word in enumerate(words):
            streamed_content += word + " "

            # Update every few words for smooth streaming
            if i % 5 == 0 or word.endswith((".", "!", "?", ":")):
                history[-1] = ChatMessage(
                    role="assistant", content=streamed_content.strip()
                )
                yield history
                time.sleep(0.08)

        # Final update with complete response (no metadata - just a regular message)
        history[-1] = ChatMessage(role="assistant", content=response)
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
