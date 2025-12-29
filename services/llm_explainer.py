"""
LLM explainer service using Google Gemini via API key (Google AI Studio style).
Rewrites rule-based explanations into simple, tenant-friendly language.
"""
import os
import json
from typing import Optional
from loguru import logger
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# NOTE: This function rewrites /query results into simple 8th-grade language.
# It must NOT invent new clauses. If in doubt, it should say the document
# does not clearly talk about the topic.

def explain_with_llm(query: str, matches: list[dict], base_answer: str) -> str:
    """
    Use Gemini API to rewrite the base_answer into simple, tenant-friendly language.
    
    Args:
        query: User's question
        matches: List of matched clauses with risk info (up to top 3)
        base_answer: Original rule-based answer string
    
    Returns:
        Plain string explanation in simple language (8th-grade level)
    """
    # If no matches, return a simple message without calling LLM
    if not matches:
        return "Your document does not clearly talk about this topic. I couldn't find a specific clause about it."
    
    # Check for API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY not set. LLM features disabled, returning base_answer")
        return base_answer
    
    model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash")
    
    # Build the system instruction prompt
    system_instruction = """You are explaining rental agreement terms to someone in simple, everyday language. Write like you're helping a friend understand their contract.

You will receive:
- The user's question.
- Some text from their rental agreement.
- A risk level: GREEN (safe/okay), YELLOW (be careful), RED (risky/problem).

Your job:
- Answer their question using ONLY the information from the agreement text provided.
- Explain what it means in simple words - what they need to do, what they need to pay, etc.
- Tell them if it's safe or if they should be careful.

IMPORTANT RULES:
- Use simple, everyday words. No legal jargon or complicated terms.
- Write in a friendly, helpful tone - like explaining to a friend.
- Don't say "Clause 1" or reference clause numbers - just explain naturally.
- Don't copy the exact legal text word-for-word - explain what it MEANS in plain language.
- ONLY use information that's actually in the agreement text provided. Don't add anything extra.
- If the document doesn't clearly answer their question, say: "Your document doesn't clearly talk about this. I couldn't find a specific answer in your agreement."
- Don't say you're a lawyer. Just be helpful and clear.
- Keep it short: 2-4 sentences. One small paragraph.
- No emojis or casual slang. Keep it friendly but professional."""

    # Build context from matches (up to top 3)
    matches_data = []
    for match in matches[:3]:
        matches_data.append({
            "clause_text": match.get("text", ""),
            "risk_level": match.get("risk_level", "UNKNOWN"),
            "risk_score": match.get("risk_score", 0.0),
            "reasons": match.get("reasons", [])
        })
    
    # Build the user message
    matches_text = []
    for i, match_data in enumerate(matches_data, 1):
        reasons_str = "; ".join(match_data["reasons"]) if match_data["reasons"] else "No specific issues identified"
        matches_text.append(
            f"Clause {i}:\n"
            f"Text: {match_data['clause_text']}\n"
            f"Risk Level: {match_data['risk_level']}\n"
            f"Risk Score: {match_data['risk_score']:.2f}\n"
            f"Reasons: {reasons_str}"
        )
    
    context = "\n\n".join(matches_text)
    
    user_message = f"""User asked: {query}

Here's what the agreement says:
{context}

The risk level is: {matches_data[0]['risk_level'] if matches_data else 'UNKNOWN'}

Now explain this to them like you're talking to a 13-year-old friend. Use simple words. Don't copy the legal text - explain what it MEANS in everyday life. Keep it short and friendly."""

    # Prepare the API request
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json"
    }
    
    # Build the request payload
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": f"{system_instruction}\n\n---\n\n{user_message}"
                    }
                ]
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        # Extract the generated text from the response
        if "candidates" in result and len(result["candidates"]) > 0:
            if "content" in result["candidates"][0] and "parts" in result["candidates"][0]["content"]:
                if len(result["candidates"][0]["content"]["parts"]) > 0:
                    answer_llm = result["candidates"][0]["content"]["parts"][0].get("text", "").strip()
                    
                    # Ensure plain text (no JSON or bullet lists if it looks like structured data)
                    # Truncate if very long
                    if len(answer_llm) > 800:
                        answer_llm = answer_llm[:800].rsplit(".", 1)[0] + "."
                    
                    logger.info(f"LLM explanation generated successfully (length: {len(answer_llm)})")
                    return answer_llm
        
        # If we couldn't extract text, log and fallback
        logger.warning("Unexpected response format from Gemini API, falling back to base_answer")
        return base_answer
        
    except requests.exceptions.Timeout:
        logger.error("Timeout calling Gemini API, returning base_answer")
        return base_answer
    except requests.exceptions.HTTPError as e:
        error_detail = ""
        if e.response is not None:
            try:
                error_json = e.response.json()
                error_detail = f"Status {e.response.status_code}: {error_json.get('error', {}).get('message', 'Unknown error')}"
            except:
                error_detail = f"Status {e.response.status_code}: {e.response.text[:200]}"
        else:
            error_detail = "Unknown HTTP error"
        logger.error(f"HTTP error calling Gemini API: {error_detail}, returning base_answer")
        return base_answer
    except (requests.exceptions.RequestException, json.JSONDecodeError, KeyError, ValueError) as e:
        logger.error(f"Error calling Gemini API: {e}, returning base_answer")
        return base_answer
    except Exception as e:
        logger.error(f"Unexpected error calling Gemini API: {e}, returning base_answer")
        return base_answer
