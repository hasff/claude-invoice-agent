import os
import json
from pyexpat.errors import messages
import time
from dotenv import load_dotenv

import anthropic

load_dotenv()

from tools import TOOLS, run_tool

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
CLIENT = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-haiku-4-5"

SYSTEM_PROMPT = """You are an assistant specialized in extracting data from PDF invoices.

When the user asks you to process invoices, always follow this workflow:
1. Use the `list_pdfs` tool to see which files are available. Inform the user.
2. For each PDF found, use `extract_pdf_text` to read its content.
   Inform the user before processing each file (e.g. "Processing invoice_001.pdf...").
3. Analyse the text and extract: client name, address, phone number and amount owed.
   If a field is not found, use "N/A".
4. After processing ALL files, call `create_excel` with all the accumulated data.
5. Inform the user that the process is complete and provide the name of the generated Excel file.

## /explain command
When the user's message starts with /explain, you MUST:
1. Always call the `read_project_code` tool first — no exceptions.
2. Read the full source code returned by the tool.
3. Answer the user's question based strictly on the actual code, not assumptions.
4. Be precise: reference specific function names, line logic, or patterns where relevant.

Be clear and concise. Keep the user informed of progress at every step.
End the conversation with a smile 😊
"""

# ─────────────────────────────────────────────
# TOOL USE LOOP
# ─────────────────────────────────────────────
def process_tool_calls(response, messages: list) -> anthropic.types.Message:
    """
    Processes tool calls in a loop until Claude finishes (stop_reason = 'end_turn').
    Updates the message history on each iteration.
    """   
    while response.stop_reason == "tool_use":

        # Add Claude's response to the history
        messages.append({
            "role": "assistant",
            "content": response.content
        })


        # Process each tool call in the response block
        tool_requests = [block for block in response.content if block.type == "tool_use"]
        tool_results = []
        for tool_request in tool_requests:
            tool_name = tool_request.name
            tool_input = tool_request.input

            # Visual feedback during execution
            print(f"\n  🔧 Tool call: {tool_name}")
            if tool_input:
                print(f"     Input: {json.dumps(tool_input, ensure_ascii=False)}")          

            # Simulate thinking time
            time.sleep(0.8)   

            # Execute the tool
            result = run_tool(tool_name, tool_input) 

            # Result feedback
            result_dict = json.loads(result)
            if "error" in result_dict:
                print(f"     ❌ Error: {result_dict['error']}")

                # 🚨important: 
                #       send error details back to Claude
                #       it may want to try another tool or adjust its approach based on the error!
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_request.id,
                    "content": f"Error: {result_dict['error']}",
                    "is_error": True
                })                
            else:
                if tool_name == "list_pdfs":
                    print(f"     ✅ {result_dict.get('total', 0)} PDF(s) found")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_request.id,
                    "content": result,
                    "is_error": False
                })          

        # Return tool results to Claude
        messages.append({
            "role": "user",
            "content": tool_results
        })

        # New API call with updated history
        print("\n  💭 Claude is processing the results...")
        time.sleep(0.5)

        try:
            response = send_to_claude(messages)

        except anthropic.APIError as e:
            print(f"\n  ❌ API error: {e}")
            continue         

    return response

# ─────────────────────────────────────────────
# MAIN CHAT LOOP
# ─────────────────────────────────────────────
def get_user_input(prompt="\n You: "):
    try:
        user_input = input(prompt).strip()
        
        # user entered nothing
        if not user_input:
            return ""

        # exit commands
        if user_input.lower() in ("exit", "quit", "bye"):
            return None
            
        return user_input

    except (KeyboardInterrupt, EOFError) as e:
        print(f"Error: {e} — exiting.")
        return None
    
def send_to_claude(messages: list) -> anthropic.types.Message:
    return CLIENT.messages.create(
        model=MODEL,
        max_tokens=1000,
        messages=messages,

        tools=TOOLS,
        system=SYSTEM_PROMPT,
    )  

def chat():
    print("=" * 55)
    print("  📄 Invoice Extractor — Powered by Claude API")
    print("=" * 55)
    print("  Type 'exit' to quit.\n")
    print("  Example: 'extract client data from the invoices'")
    print("-" * 55)

    """Main chat loop with message history."""
    messages = []  # Full conversation history    

    while True:
        # user input
        user_input = get_user_input()

        if user_input is None:
            print("\nGoodbye!")
            break

        if not user_input:
            continue   


        # user message
        user_message = {
            "role": "user",
            "content": user_input
        } 
        messages.append(user_message)


        # API call to Claude
        print("\n  ⏳ Contacting Claude...\n")  

        try:
            response = send_to_claude(messages)
        except anthropic.APIError as e:
            print(f"\n  ❌ API error: {e}")
            continue      

        # print(response) 

        # # Process tool calls if any
        # if response.stop_reason == "tool_use":
        #     for block in response.content:
        #         if block.type == "tool_use":
        #             tool_name = block.name
        #             tool_input = block.input
        #             print(f"\n  🛠️  Claude is calling tool: {tool_name} with input: {tool_input}")

        #             tool_output = run_tool(tool_name, tool_input)
        #             print(f"\n  🧰 Tool output: {tool_output}")

        # Process tool calls if any
        if response.stop_reason == "tool_use":
            response = process_tool_calls(response, messages)        


        response_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                response_text += block.text 

        # assistant message (Claude's response)
        assistant_message = {
            "role": "assistant",
            "content": response_text
        }   
        messages.append(assistant_message)                


        print(f"\n Claude: {response_text}")
        print("-" * 55)
                          

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    chat()