"""
Dynamic Query Generator with AI-Powered Query Expansion
========================================================

This module provides AI-powered query generation with Query Fan-Out support.

Query Fan-Out Strategy:
----------------------
Query Fan-Out is a technique to expand search coverage by generating multiple
related queries that cover broader lead intentions. It includes:

1. **Generalization**: Create broader versions of the original query
   - Example: "Sales Manager Hamburg" → "Sales Hamburg", "Vertrieb Hamburg"
   
2. **Follow-ups**: Generate related queries that discover additional leads
   - Example: "Sales Manager" → "Business Development", "Account Manager"

Usage:
------
The DynamicQueryGenerator is activated via the OPENAI_API_KEY environment variable:

1. **With OPENAI_API_KEY set**: Full AI-powered query expansion with Query Fan-Out
   - Generates generalized queries (broader search terms)
   - Creates follow-up queries (related positions/roles)
   - Returns expanded query set for maximum lead coverage

2. **Without OPENAI_API_KEY**: Fallback to basic query generation
   - Returns the original query without expansion
   - No API calls are made

Example:
--------
    import asyncio
    from luca_scraper.ai.query_generator import DynamicQueryGenerator
    
    async def main():
        generator = DynamicQueryGenerator()
        
        # Generate expanded queries with AI (if OPENAI_API_KEY is set)
        queries = await generator.generate_expanded_queries(
            base_query="Sales Manager Hamburg",
            industry="B2B Software",
            count=5
        )
        
        for query in queries:
            print(f"{query['type']}: {query['query']}")
    
    asyncio.run(main())

Environment Variables:
---------------------
- OPENAI_API_KEY: Required for AI-powered query expansion
- OPENAI_MODEL: Model to use (default: gpt-4o-mini)

"""

import json
import os
from typing import Any, Dict, List, Optional

import aiohttp

from luca_scraper.config import OPENAI_API_KEY, HTTP_TIMEOUT


def log(level: str, msg: str, **ctx):
    """Simple logging function."""
    from datetime import datetime
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ctx_str = (" " + json.dumps(ctx, ensure_ascii=False)) if ctx else ""
    line = f"[{ts}] [{level.upper():7}] {msg}{ctx_str}"
    print(line, flush=True)


class DynamicQueryGenerator:
    """
    AI-powered query generator with Query Fan-Out support.
    
    Features:
    ---------
    - Query Generalization: Broader search terms for wider coverage
    - Query Follow-ups: Related queries to discover additional leads
    - Environment-based activation: Uses OPENAI_API_KEY to enable AI features
    - Graceful fallback: Returns basic queries when API key is not set
    
    Query Fan-Out ensures that generated search queries cover broader lead
    intentions by expanding the original query into multiple related searches.
    """
    
    def __init__(self):
        """Initialize the DynamicQueryGenerator."""
        self.api_key = OPENAI_API_KEY
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.enabled = bool(self.api_key)
        
        if self.enabled:
            log("info", "DynamicQueryGenerator: AI features ENABLED")
        else:
            log("info", "DynamicQueryGenerator: AI features DISABLED (no OPENAI_API_KEY)")
    
    def is_enabled(self) -> bool:
        """
        Check if AI-powered query expansion is enabled.
        
        Returns:
            bool: True if OPENAI_API_KEY is set, False otherwise
        """
        return self.enabled
    
    async def generate_expanded_queries(
        self,
        base_query: str,
        industry: Optional[str] = None,
        count: int = 5,
        include_original: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Generate expanded queries using Query Fan-Out strategy.
        
        This method applies Query Fan-Out to expand the base query into multiple
        related searches that cover broader lead intentions:
        
        1. **Generalization**: Creates broader versions of the query
           - Removes specific location constraints
           - Simplifies job titles to more generic terms
           - Expands to related industries
        
        2. **Follow-ups**: Generates related queries for additional leads
           - Related job titles and roles
           - Alternative search patterns
           - Cross-industry variations
        
        Args:
            base_query: The original search query to expand
            industry: Optional industry context for better expansion
            count: Number of expanded queries to generate (default: 5)
            include_original: Whether to include the original query (default: True)
        
        Returns:
            List of query dicts with keys:
            - query: The search query string
            - type: Query type ("original", "generalized", "follow-up")
            - confidence: Confidence score (0-100)
            - reason: Explanation of why this query was generated
        
        Example:
            >>> generator = DynamicQueryGenerator()
            >>> queries = await generator.generate_expanded_queries(
            ...     base_query="Sales Manager Hamburg",
            ...     industry="B2B Software",
            ...     count=5
            ... )
            >>> for q in queries:
            ...     print(f"{q['type']}: {q['query']}")
            original: Sales Manager Hamburg
            generalized: Sales Hamburg
            generalized: Vertrieb Hamburg
            follow-up: Business Development Hamburg
            follow-up: Account Manager Hamburg
        """
        if not self.enabled:
            # Fallback: return only the original query
            log("debug", "AI query expansion disabled, returning base query only")
            return [{
                "query": base_query,
                "type": "original",
                "confidence": 100,
                "reason": "AI features disabled (no OPENAI_API_KEY)"
            }]
        
        try:
            # Build the AI prompt with Query Fan-Out instructions
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(base_query, industry, count)
            
            # Call OpenAI API
            response = await self._call_openai_api(system_prompt, user_prompt)
            
            if not response:
                log("warn", "AI query expansion failed, returning base query")
                return self._fallback_queries(base_query)
            
            # Parse response and build query list
            queries = self._parse_response(response, base_query, include_original)
            
            log("info", "Generated expanded queries", count=len(queries), base=base_query)
            return queries
            
        except Exception as e:
            log("error", "Query expansion error", error=str(e), base=base_query)
            return self._fallback_queries(base_query)
    
    def _build_system_prompt(self) -> str:
        """
        Build the system prompt with Query Fan-Out instructions.
        
        The prompt includes specific instructions for:
        - Query generalization (broader terms)
        - Query follow-ups (related searches)
        - Lead intention coverage (wider discovery)
        """
        return """You are an expert at search query optimization for lead generation.

Your task is to apply QUERY FAN-OUT strategy to expand search coverage:

1. **GENERALIZATION**: Create broader versions of the query
   - Remove specific location constraints where appropriate
   - Simplify job titles to more generic terms
   - Use both German and English terms
   - Include common synonyms and variations
   
   Example:
   - Input: "Sales Manager Hamburg"
   - Generalized: "Sales Hamburg", "Vertrieb Hamburg", "Sales Mitarbeiter Hamburg"

2. **FOLLOW-UPS**: Generate related queries for additional leads
   - Related job titles and roles
   - Alternative positions with similar responsibilities
   - Adjacent roles in the same department
   
   Example:
   - Input: "Sales Manager"
   - Follow-ups: "Business Development Manager", "Account Manager", "Vertriebsleiter"

GOAL: Cover broader lead intentions to maximize discovery of potential contacts.

Return JSON format:
{
  "queries": [
    {
      "query": "...",
      "type": "generalized|follow-up",
      "confidence": 0-100,
      "reason": "..."
    }
  ]
}

Only return valid, actionable search queries. Each query should be distinct and add value."""
    
    def _build_user_prompt(
        self,
        base_query: str,
        industry: Optional[str],
        count: int
    ) -> str:
        """Build the user prompt with query expansion request."""
        industry_context = f"\nIndustry context: {industry}" if industry else ""
        
        return f"""Base Query: "{base_query}"{industry_context}

Generate {count} expanded queries using Query Fan-Out strategy:
- Mix of generalized queries (broader terms)
- Mix of follow-up queries (related searches)

Focus on queries that will discover additional relevant leads beyond the base query."""
    
    async def _call_openai_api(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> Optional[Dict[str, Any]]:
        """
        Call OpenAI API to generate expanded queries.
        
        Args:
            system_prompt: System instructions for the AI
            user_prompt: User request with base query
        
        Returns:
            Parsed JSON response or None on error
        """
        endpoint = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7,  # Some creativity for query variations
            "max_tokens": 1000
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    headers=headers,
                    json=payload,
                    timeout=HTTP_TIMEOUT
                ) as resp:
                    if resp.status != 200:
                        log("warn", "OpenAI API error", status=resp.status)
                        return None
                    
                    data = await resp.json()
                    choices = data.get("choices", [])
                    if not choices:
                        log("warn", "OpenAI returned no choices")
                        return None
                    
                    content = choices[0].get("message", {}).get("content", "")
                    if not content:
                        log("warn", "OpenAI returned empty content")
                        return None
                    
                    return json.loads(content)
                    
        except Exception as e:
            log("error", "OpenAI API call failed", error=str(e))
            return None
    
    def _parse_response(
        self,
        response: Dict[str, Any],
        base_query: str,
        include_original: bool
    ) -> List[Dict[str, Any]]:
        """
        Parse the OpenAI response and build query list.
        
        Args:
            response: Parsed JSON response from OpenAI
            base_query: Original query to optionally include
            include_original: Whether to include the original query
        
        Returns:
            List of query dicts
        """
        queries = []
        
        # Add original query first if requested
        if include_original:
            queries.append({
                "query": base_query,
                "type": "original",
                "confidence": 100,
                "reason": "Original base query"
            })
        
        # Parse generated queries
        generated = response.get("queries", [])
        if not isinstance(generated, list):
            log("warn", "Invalid response format: 'queries' is not a list")
            return queries
        
        for item in generated:
            if not isinstance(item, dict):
                continue
            
            query = item.get("query", "").strip()
            if not query:
                continue
            
            # Avoid duplicates
            if any(q["query"].lower() == query.lower() for q in queries):
                continue
            
            queries.append({
                "query": query,
                "type": item.get("type", "unknown"),
                "confidence": item.get("confidence", 50),
                "reason": item.get("reason", "")
            })
        
        return queries
    
    def _fallback_queries(self, base_query: str) -> List[Dict[str, Any]]:
        """
        Fallback query list when AI expansion fails.
        
        Args:
            base_query: The original query
        
        Returns:
            List with only the base query
        """
        return [{
            "query": base_query,
            "type": "original",
            "confidence": 100,
            "reason": "Fallback (AI expansion failed)"
        }]
    
    async def generate_dorks_with_fanout(
        self,
        industry: str,
        count: int = 5
    ) -> List[str]:
        """
        Generate Google dorks with Query Fan-Out for an industry.
        
        This is a specialized version for dork generation that applies
        Query Fan-Out to create varied search patterns.
        
        Args:
            industry: Industry name or "candidates"/"recruiter" for job seeker mode
            count: Number of dorks to generate (default: 5)
        
        Returns:
            List of search dork strings
        """
        if not self.enabled:
            log("debug", "AI dork generation disabled")
            return []
        
        # Determine mode
        industry_lower = industry.lower()
        is_candidates = industry_lower in ("candidates", "recruiter")
        
        # Build prompt with Query Fan-Out for dorks
        if is_candidates:
            base_prompt = (
                "Generate Google Dorks with QUERY FAN-OUT to find JOB SEEKERS:\n\n"
                "1. GENERALIZATION: Broader job search patterns\n"
                "   - Generic job seeker terms across platforms\n"
                "   - Multiple classifieds sites (kleinanzeigen, markt.de, etc.)\n"
                "2. FOLLOW-UPS: Related search approaches\n"
                "   - Social media job seeker profiles\n"
                "   - Freelancer platforms\n"
                "   - Professional networks\n\n"
                'Examples:\n'
                'site:kleinanzeigen.de/s-stellengesuche "vertrieb"\n'
                'site:xing.com/profile "offen für angebote" "sales"\n'
                '"ich suche job" "vertrieb" "NRW"\n\n'
                "Return ONLY the dorks, one per line."
            )
        else:
            base_prompt = (
                f"Generate Google Dorks with QUERY FAN-OUT for {industry}:\n\n"
                "1. GENERALIZATION: Broader employee discovery patterns\n"
                "   - Team pages across company types\n"
                "   - CV/resume documents with variations\n"
                "2. FOLLOW-UPS: Related discovery methods\n"
                "   - LinkedIn profiles with adjacent roles\n"
                "   - Freelancer platforms\n"
                "   - Job seeker profiles (reverse recruiting)\n\n"
                'Examples:\n'
                f'intitle:"Team" "Sales" {industry}\n'
                f'filetype:pdf "Lebenslauf" {industry}\n'
                f'site:linkedin.com/in/ "{industry}" "open to work"\n\n'
                "Return ONLY the dorks, one per line."
            )
        
        # Call API
        system_prompt = "You create Google search dorks with Query Fan-Out strategy."
        try:
            response = await self._call_openai_api(system_prompt, base_prompt)
            
            if not response:
                return []
            
            # Parse dorks from response
            # The response might be plain text (line-separated) or JSON
            if isinstance(response, dict):
                # Try to extract from various possible keys
                content = (
                    response.get("dorks") or 
                    response.get("queries") or 
                    response.get("content", "")
                )
                if isinstance(content, list):
                    return [str(d).strip() for d in content if d]
                content = str(content)
            else:
                content = str(response)
            
            # Parse line-separated dorks
            lines = [ln.strip(" -*\t") for ln in content.splitlines() if ln.strip()]
            
            # Deduplicate
            unique = []
            seen = set()
            for ln in lines:
                if ln.lower() in seen or not ln:
                    continue
                seen.add(ln.lower())
                unique.append(ln)
                if len(unique) >= count:
                    break
            
            log("info", "Generated dorks with fan-out", count=len(unique), industry=industry)
            return unique
            
        except Exception as e:
            log("error", "Dork generation with fan-out failed", error=str(e))
            return []
