import json
import operator
import re
from typing import Annotated, List, Tuple, TypedDict, Union

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain.tools import Tool
from langchain_openai import ChatOpenAI


class AgentState(TypedDict):
    messages: Annotated[List[Union[HumanMessage, AIMessage]], operator.add]
    context: dict


class FinancialAdvisorAgent:
    def __init__(self, tools: List[Tool], openai_api_key: str):
        self.tools = tools
        self.llm = ChatOpenAI(
            api_key=openai_api_key, model="gpt-4.1-2025-04-14", temperature=0.7
        )
        self.tools_by_name = {tool.name: tool for tool in tools}

        # Create agent with tools
        self.system_prompt = """You are a professional financial advisor AI assistant with access to specialized tools.

Available tools:
- budget_planner: Use when users ask about budgeting, income allocation, or expense planning. Input should be JSON with 'income' and 'expenses' keys.
- investment_analyzer: Use when users ask about specific stocks or investments. Input should be a stock symbol (e.g., AAPL).
- expense_tracker: Use when users want to track or analyze expenses. Input should be JSON with 'expenses' array.
- market_trends: Use when users ask about market trends or financial news. Input should be a search query.
- portfolio_analyzer: Use when users want to analyze their portfolio. Input should be JSON with 'holdings' array.

IMPORTANT: You MUST use these tools when answering financial questions. Do not provide generic advice without using the appropriate tool first.

When a user asks a question:
1. Identify which tool is most appropriate
2. Extract or request the necessary information
3. Use the tool to get specific data
4. Provide advice based on the tool's output"""

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                MessagesPlaceholder(variable_name="messages"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        self.agent = create_openai_tools_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            return_intermediate_steps=True,
        )

    def _extract_tool_usage(self, intermediate_steps):
        """Extract tool usage from intermediate steps"""
        tool_used = None
        tool_result = None

        for action, result in intermediate_steps:
            if hasattr(action, "tool"):
                tool_used = action.tool
                tool_result = result
                break

        return tool_used, tool_result

    def _prepare_tool_input(self, message: str, tool_name: str) -> str:
        """Prepare input for specific tools based on the message"""
        if tool_name == "investment_analyzer":
            # Extract stock symbols
            symbols = re.findall(r"\b[A-Z]{2,5}\b", message)
            if symbols:
                return symbols[0]
            return "AAPL"  # Default

        elif tool_name == "budget_planner":
            # Try to extract income and expenses from message
            income_match = re.search(
                r"\$?(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:monthly\s*)?income",
                message,
                re.I,
            )
            income = (
                float(income_match.group(1).replace(",", "")) if income_match else 5000
            )

            # Extract expenses
            expenses = {}
            expense_patterns = [
                (r"rent:?\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)", "rent"),
                (r"food:?\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)", "food"),
                (r"utilities:?\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)", "utilities"),
                (
                    r"transportation:?\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)",
                    "transportation",
                ),
            ]

            for pattern, category in expense_patterns:
                match = re.search(pattern, message, re.I)
                if match:
                    expenses[category] = float(match.group(1).replace(",", ""))

            return json.dumps({"income": income, "expenses": expenses})

        elif tool_name == "portfolio_analyzer":
            # Try to extract portfolio data
            if "holdings" in message:
                return message  # Assume it's already formatted
            return json.dumps({"holdings": [{"symbol": "AAPL", "shares": 100}]})

        elif tool_name == "market_trends":
            return message

        return message

    def process_message_with_details(
        self, message: str, history: List[dict] = None
    ) -> Tuple[str, str, str]:
        """Process a message and return response, tool used, and tool result"""
        if history is None:
            history = []

        # Determine which tool to use based on message content
        message_lower = message.lower()
        selected_tool = None

        if any(
            word in message_lower
            for word in ["budget", "income", "expense", "spending"]
        ):
            selected_tool = "budget_planner"
        elif any(
            word in message_lower
            for word in ["stock", "invest", "buy", "sell", "analyze"]
        ) and re.search(r"\b[A-Z]{2,5}\b", message):
            selected_tool = "investment_analyzer"
        elif any(
            word in message_lower for word in ["portfolio", "holdings", "allocation"]
        ):
            selected_tool = "portfolio_analyzer"
        elif any(
            word in message_lower for word in ["market", "trend", "news", "sector"]
        ):
            selected_tool = "market_trends"
        elif any(word in message_lower for word in ["track", "expense", "spending"]):
            selected_tool = "expense_tracker"

        # If a tool is selected, use it directly
        if selected_tool and selected_tool in self.tools_by_name:
            try:
                tool = self.tools_by_name[selected_tool]
                tool_input = self._prepare_tool_input(message, selected_tool)
                tool_result = tool.func(tool_input)

                # Generate response based on tool result
                response_prompt = f"""Based on the following analysis from {selected_tool}:

{tool_result}

Provide comprehensive financial advice to the user addressing their question: {message}

Be specific, actionable, and reference the data from the analysis."""

                response = self.llm.invoke(
                    [
                        SystemMessage(
                            content="You are a professional financial advisor. Provide clear, actionable advice based on the analysis results."
                        ),
                        HumanMessage(content=response_prompt),
                    ]
                )

                return response.content, selected_tool, tool_result

            except Exception as e:
                return f"Error using {selected_tool}: {str(e)}", selected_tool, None

        # Fallback to agent executor
        try:
            result = self.agent_executor.invoke({"input": message, "messages": []})

            tool_used, tool_result = self._extract_tool_usage(
                result.get("intermediate_steps", [])
            )
            return result["output"], tool_used, tool_result

        except Exception as e:
            return (
                f"I encountered an error processing your request: {str(e)}",
                None,
                None,
            )

    def process_message(self, message: str, history: List[dict] = None):
        """Process a user message and return response"""
        response, _, _ = self.process_message_with_details(message, history)
        return response
