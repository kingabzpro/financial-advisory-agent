import base64
import json
import os
import time

import gradio as gr
import plotly.graph_objects as go
from gradio import ChatMessage

from agents.financial_agent import FinancialAdvisorAgent
from agents.tools import FinancialTools

# Avatar configuration
AVATAR_IMAGES = (None, "https://media.roboflow.com/spaces/gemini-icon.png")

# Initialize tools and agent
financial_tools = FinancialTools(tavily_api_key=os.getenv("TAVILY_API_KEY"))
tools = financial_tools.get_all_tools()

agent = FinancialAdvisorAgent(tools=tools, openai_api_key=os.getenv("OPENAI_API_KEY"))


def create_visualization(data_type, data):
    """Create financial visualizations and return as base64 image"""
    print(f"[VIZ LOG] Creating visualization of type: {data_type}")
    print(f"[VIZ LOG] Data preview: {str(data)[:200]}...")
    
    fig = None

    if data_type == "budget":
        print(f"[VIZ LOG] Processing budget visualization")
        try:
            # Create budget allocation pie chart
            budget_data = json.loads(data)
            print(f"[VIZ LOG] Budget data parsed successfully")
            
            categories = list(budget_data.get("current_expenses", {}).keys())
            values = list(budget_data.get("current_expenses", {}).values())
            print(f"[VIZ LOG] Categories: {categories}")
            print(f"[VIZ LOG] Values: {values}")

            if categories and values:
                print(f"[VIZ LOG] Creating pie chart")
                fig = go.Figure(data=[go.Pie(labels=categories, values=values, hole=0.3)])
                fig.update_layout(title="Expense Breakdown", height=400, width=600)
                print(f"[VIZ LOG] Pie chart created successfully")
            else:
                print(f"[VIZ LOG] No categories or values found for budget chart")
        except Exception as e:
            print(f"[VIZ LOG] Error in budget visualization: {e}")
            return None

    elif data_type == "portfolio":
        # Create portfolio allocation chart
        portfolio_data = json.loads(data)
        sectors = {}
        for holding in portfolio_data.get("holdings", []):
            sector = holding.get("sector", "Unknown")
            sectors[sector] = sectors.get(sector, 0) + holding.get("allocation", 0)

        if sectors:
            fig = go.Figure(
                data=[
                    go.Pie(
                        labels=list(sectors.keys()),
                        values=list(sectors.values()),
                        hole=0.3,
                    )
                ]
            )
            fig.update_layout(
                title="Portfolio Sector Allocation", height=400, width=600
            )

    elif data_type == "stock":
        # Create stock price chart
        stock_data = json.loads(data)
        price_str = stock_data.get("current_price", "0")
        # Remove $ and convert to float
        price = (
            float(price_str.replace("$", "").replace(",", ""))
            if price_str != "N/A"
            else 0
        )

        if price > 0:
            fig = go.Figure()
            fig.add_trace(
                go.Indicator(
                    mode="number+delta",
                    value=price,
                    title={
                        "text": f"{stock_data.get('symbol', 'Stock')} Current Price"
                    },
                    delta={"reference": price * 0.95},
                    number={"prefix": "$"},
                )
            )
            fig.update_layout(height=300, width=500)

    if fig:
        print(f"[VIZ LOG] Converting figure to base64 image")
        try:
            # Use a simpler approach - just return chart data as text for now
            print(f"[VIZ LOG] Skipping image conversion (known to hang) - returning chart description")
            
            # Create a text-based representation instead
            if data_type == "budget":
                budget_data = json.loads(data)
                expenses = budget_data.get("current_expenses", {})
                total = sum(expenses.values())
                
                chart_text = "📊 **Expense Breakdown Chart**\n\n"
                for category, amount in expenses.items():
                    percentage = (amount / total * 100) if total > 0 else 0
                    bar = "█" * int(percentage / 5)  # Visual bar
                    chart_text += f"**{category.title()}**: ${amount:,.0f} ({percentage:.1f}%) {bar}\n"
                
                return chart_text
                
            elif data_type == "portfolio":
                # Similar text representation for portfolio
                return "📊 **Portfolio Allocation Chart** (Text representation)"
                
            elif data_type == "stock":
                # Similar text representation for stock
                return "📊 **Stock Price Chart** (Text representation)"
                
        except Exception as e:
            print(f"[VIZ LOG] Error creating text chart: {e}")
            return None
    else:
        print(f"[VIZ LOG] No figure to convert")

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

    history.append(ChatMessage(role="assistant", content="🔄 Assistant is processing..."))
    yield history

    try:
        print(f"[LOG] Starting to process message: {last_user_message}")
        
        # Process message through agent using the actual user message
        response, tool_used, tool_result = agent.process_message_with_details(
            last_user_message, agent_history
        )
        
        print(f"[LOG] Agent processing complete. Tool used: {tool_used}")
        print(f"[LOG] Tool result length: {len(str(tool_result)) if tool_result else 0}")
        print(f"[LOG] Response length: {len(response) if response else 0}")

        # Show which tool is being used with timer
        if tool_used:
            tool_names = {
                "budget_planner": "Budget Planner",
                "investment_analyzer": "Investment Analyzer", 
                "expense_tracker": "Expense Tracker",
                "market_trends": "Market Trends Analyzer",
                "portfolio_analyzer": "Portfolio Analyzer"
            }
            tool_display_name = tool_names.get(tool_used, tool_used)
            
            elapsed = time.time() - start_time
            history[-1] = ChatMessage(
                role="assistant",
                content=f"🛠️ Using {tool_display_name}... ({elapsed:.1f}s)",
            )
            yield history
            print(f"[LOG] Showing tool usage message")

            # Show tool output with metadata
            if tool_result:
                # Format tool result for display
                try:
                    import json
                    if tool_result.startswith('{') or tool_result.startswith('['):
                        # Pretty format JSON output
                        parsed_result = json.loads(tool_result)
                        # Truncate very long results for display
                        if len(str(parsed_result)) > 2000:
                            # Show summary for long results
                            if isinstance(parsed_result, dict):
                                summary = {k: f"[{type(v).__name__}]" if isinstance(v, (list, dict)) else v for k, v in list(parsed_result.items())[:10]}
                                display_result = f"```json\n{json.dumps(summary, indent=2)}\n... (truncated)\n```"
                            else:
                                display_result = f"```json\n{json.dumps(parsed_result, indent=2)[:1000]}...\n```"
                        else:
                            formatted_result = json.dumps(parsed_result, indent=2)
                            display_result = f"```json\n{formatted_result}\n```"
                    else:
                        # Truncate non-JSON results
                        display_result = tool_result[:1000] + "..." if len(tool_result) > 1000 else tool_result
                except Exception as e:
                    print(f"Error formatting tool result: {e}")
                    display_result = str(tool_result)[:1000] + "..." if len(str(tool_result)) > 1000 else str(tool_result)

                elapsed = time.time() - start_time
                history[-1] = ChatMessage(
                    role="assistant",
                    content=display_result,
                    metadata={"title": f"🛠️ {tool_display_name} Results ({elapsed:.1f}s)"},
                )
                yield history

        # Add visualization if applicable
        if tool_result and tool_used in [
            "budget_planner",
            "portfolio_analyzer", 
            "investment_analyzer",
        ]:
            print(f"[LOG] Creating visualization for {tool_used}")
            viz_type = {
                "budget_planner": "budget",
                "portfolio_analyzer": "portfolio",
                "investment_analyzer": "stock",
            }.get(tool_used)

            try:
                elapsed = time.time() - start_time
                history.append(
                    ChatMessage(
                        role="assistant",
                        content=f"📊 Generating visualization... ({elapsed:.1f}s)",
                    )
                )
                yield history
                print(f"[LOG] About to create visualization of type: {viz_type}")

                img_data = create_visualization(viz_type, tool_result)
                print(f"[LOG] Visualization created. Data length: {len(img_data) if img_data else 0}")
                
                if img_data:
                    elapsed = time.time() - start_time
                    history[-1] = ChatMessage(
                        role="assistant",
                        content=f"![Financial Analysis]({img_data})",
                        metadata={"title": f"📊 Financial Visualization ({elapsed:.1f}s)"},
                    )
                    yield history
                    print(f"[LOG] Visualization displayed successfully")
                else:
                    print(f"[LOG] No visualization data generated")
                    # Remove the "Generating visualization..." message if no data
                    history.pop()
                    
            except Exception as e:
                print(f"[LOG] Error creating visualization: {e}")
                # Remove the "Generating visualization..." message on error
                history.pop()

        # Show response generation with timer
        elapsed = time.time() - start_time
        history.append(
            ChatMessage(
                role="assistant", 
                content=f"✍️ Generating response... ({elapsed:.1f}s)"
            )
        )
        yield history
        time.sleep(0.5)

        # Stream the final response
        words = response.split()
        streamed_content = ""
        
        for i, word in enumerate(words):
            streamed_content += word + " "
            
            # Update every few words for smooth streaming
            if i % 5 == 0 or word.endswith(('.', '!', '?', ':')):
                history[-1] = ChatMessage(
                    role="assistant", 
                    content=streamed_content.strip()
                )
                yield history
                time.sleep(0.08)
        
        # Final update with complete response (no metadata - just a regular message)
        history[-1] = ChatMessage(
            role="assistant", 
            content=response
        )
        yield history
        
        # Log completion time in console only
        elapsed = time.time() - start_time
        print(f"[LOG] ✅ Response completed in {elapsed:.1f}s")

    except Exception as e:
        elapsed = time.time() - start_time
        history[-1] = ChatMessage(
            role="assistant",
            content=f"I encountered an error while processing your request: {str(e)}. Please try rephrasing your question.",
            metadata={"title": f"💥 Error ({elapsed:.1f}s)"},
        )
        yield history


# Create the Gradio interface
with gr.Blocks(theme=gr.themes.Soft(), title="Financial Advisory Agent") as demo:
    gr.Markdown("""
    # 🏦 AI Financial Advisory Agent
    
    Your AI-powered financial advisor for budgeting, investments, expense tracking, portfolio analysis, and market trends.
    """)

    chatbot = gr.Chatbot(
        type="messages",
        height=500,
        avatar_images=AVATAR_IMAGES,
        show_copy_button=True,
    )

    with gr.Row():
        msg = gr.Textbox(
            placeholder="Ask me about budgeting, investments, or any financial topic...",
            show_label=False,
            scale=9,
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
    submit_event = msg.submit(
        user_submit, [msg, chatbot], [msg, chatbot, msg, submit]
    ).then(
        process_financial_query, [msg, chatbot], chatbot
    ).then(
        enable_input, [], [msg, submit]
    )

    click_event = submit.click(
        user_submit, [msg, chatbot], [msg, chatbot, msg, submit]
    ).then(
        process_financial_query, [msg, chatbot], chatbot
    ).then(
        enable_input, [], [msg, submit]
    )

    # Add like functionality for feedback
    def like_handler(evt: gr.LikeData):
        print(f"User {'liked' if evt.liked else 'disliked'} response: {evt.value}")
        print(f"Response index: {evt.index}")

    chatbot.like(like_handler)

if __name__ == "__main__":
    demo.launch()
