"""
Unit tests for DynamicQueryGenerator with Query Fan-Out
========================================================

Tests the AI-powered query expansion with Query Fan-Out strategy.
"""

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from luca_scraper.ai.query_generator import DynamicQueryGenerator


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response for query expansion."""
    return {
        "queries": [
            {
                "query": "Sales Hamburg",
                "type": "generalized",
                "confidence": 90,
                "reason": "Generalized location-based search"
            },
            {
                "query": "Vertrieb Hamburg",
                "type": "generalized",
                "confidence": 85,
                "reason": "German synonym for sales"
            },
            {
                "query": "Business Development Hamburg",
                "type": "follow-up",
                "confidence": 80,
                "reason": "Related role for lead generation"
            },
            {
                "query": "Account Manager Hamburg",
                "type": "follow-up",
                "confidence": 75,
                "reason": "Adjacent sales position"
            }
        ]
    }


@pytest.fixture
def mock_dork_response():
    """Mock OpenAI API response for dork generation."""
    return {
        "content": """intitle:"Team" "Sales" Software
filetype:pdf "Lebenslauf" "Software"
site:linkedin.com/in/ "Software" "open to work"
"stellengesuch" "Software" "verfügbar ab"
site:xing.com/profile "Software" "offen für angebote"
"""
    }


class TestDynamicQueryGenerator:
    """Test DynamicQueryGenerator functionality."""
    
    def test_initialization_with_api_key(self):
        """Test initialization when OPENAI_API_KEY is set."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            generator = DynamicQueryGenerator()
            assert generator.is_enabled() is True
            assert generator.api_key == "test-key"
    
    def test_initialization_without_api_key(self):
        """Test initialization when OPENAI_API_KEY is not set."""
        with patch.dict(os.environ, {}, clear=True):
            generator = DynamicQueryGenerator()
            assert generator.is_enabled() is False
            assert generator.api_key is None
    
    @pytest.mark.asyncio
    async def test_generate_expanded_queries_disabled(self):
        """Test query expansion when AI features are disabled."""
        with patch.dict(os.environ, {}, clear=True):
            generator = DynamicQueryGenerator()
            
            queries = await generator.generate_expanded_queries(
                base_query="Sales Manager Hamburg",
                count=5
            )
            
            # Should return only the base query
            assert len(queries) == 1
            assert queries[0]["query"] == "Sales Manager Hamburg"
            assert queries[0]["type"] == "original"
    
    @pytest.mark.asyncio
    async def test_generate_expanded_queries_with_ai(self, mock_openai_response):
        """Test query expansion with AI enabled."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            generator = DynamicQueryGenerator()
            
            # Mock the OpenAI API call
            with patch.object(
                generator,
                "_call_openai_api",
                new=AsyncMock(return_value=mock_openai_response)
            ):
                queries = await generator.generate_expanded_queries(
                    base_query="Sales Manager Hamburg",
                    industry="B2B Software",
                    count=5,
                    include_original=True
                )
                
                # Should include original + expanded queries
                assert len(queries) == 5  # 1 original + 4 expanded
                assert queries[0]["query"] == "Sales Manager Hamburg"
                assert queries[0]["type"] == "original"
                
                # Check expanded queries
                types = [q["type"] for q in queries[1:]]
                assert "generalized" in types
                assert "follow-up" in types
    
    @pytest.mark.asyncio
    async def test_generate_expanded_queries_without_original(self, mock_openai_response):
        """Test query expansion without including original query."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            generator = DynamicQueryGenerator()
            
            with patch.object(
                generator,
                "_call_openai_api",
                new=AsyncMock(return_value=mock_openai_response)
            ):
                queries = await generator.generate_expanded_queries(
                    base_query="Sales Manager Hamburg",
                    count=5,
                    include_original=False
                )
                
                # Should not include original
                assert all(q["type"] != "original" for q in queries)
                assert len(queries) == 4  # Only expanded queries
    
    @pytest.mark.asyncio
    async def test_generate_expanded_queries_deduplication(self):
        """Test that duplicate queries are removed."""
        response = {
            "queries": [
                {"query": "Sales Hamburg", "type": "generalized", "confidence": 90, "reason": "Test"},
                {"query": "sales hamburg", "type": "generalized", "confidence": 85, "reason": "Duplicate"},
                {"query": "Vertrieb Hamburg", "type": "generalized", "confidence": 80, "reason": "Test"}
            ]
        }
        
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            generator = DynamicQueryGenerator()
            
            with patch.object(
                generator,
                "_call_openai_api",
                new=AsyncMock(return_value=response)
            ):
                queries = await generator.generate_expanded_queries(
                    base_query="Sales Manager Hamburg",
                    count=5,
                    include_original=False
                )
                
                # Should remove duplicate (case-insensitive)
                assert len(queries) == 2
                query_texts = [q["query"] for q in queries]
                assert "Sales Hamburg" in query_texts
                assert "Vertrieb Hamburg" in query_texts
    
    @pytest.mark.asyncio
    async def test_generate_expanded_queries_api_failure(self):
        """Test fallback when API call fails."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            generator = DynamicQueryGenerator()
            
            # Mock API failure
            with patch.object(
                generator,
                "_call_openai_api",
                new=AsyncMock(return_value=None)
            ):
                queries = await generator.generate_expanded_queries(
                    base_query="Sales Manager Hamburg",
                    count=5
                )
                
                # Should fallback to base query
                assert len(queries) == 1
                assert queries[0]["query"] == "Sales Manager Hamburg"
                assert "Fallback" in queries[0]["reason"]
    
    @pytest.mark.asyncio
    async def test_generate_dorks_with_fanout_disabled(self):
        """Test dork generation when AI is disabled."""
        with patch.dict(os.environ, {}, clear=True):
            generator = DynamicQueryGenerator()
            
            dorks = await generator.generate_dorks_with_fanout(
                industry="Software",
                count=5
            )
            
            # Should return empty list when disabled
            assert dorks == []
    
    @pytest.mark.asyncio
    async def test_generate_dorks_with_fanout_b2b(self, mock_dork_response):
        """Test dork generation for B2B industry."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            generator = DynamicQueryGenerator()
            
            with patch.object(
                generator,
                "_call_openai_api",
                new=AsyncMock(return_value=mock_dork_response)
            ):
                dorks = await generator.generate_dorks_with_fanout(
                    industry="Software",
                    count=5
                )
                
                # Should return parsed dorks
                assert len(dorks) == 5
                assert any("Team" in d for d in dorks)
                assert any("Lebenslauf" in d for d in dorks)
    
    @pytest.mark.asyncio
    async def test_generate_dorks_with_fanout_candidates(self):
        """Test dork generation for candidates mode."""
        mock_response = {
            "content": """site:kleinanzeigen.de/s-stellengesuche "vertrieb"
site:xing.com/profile "offen für angebote"
"ich suche job" "vertrieb"
"""
        }
        
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            generator = DynamicQueryGenerator()
            
            with patch.object(
                generator,
                "_call_openai_api",
                new=AsyncMock(return_value=mock_response)
            ):
                dorks = await generator.generate_dorks_with_fanout(
                    industry="candidates",
                    count=3
                )
                
                # Should use candidates-specific prompts
                assert len(dorks) == 3
                assert any("kleinanzeigen" in d for d in dorks)
    
    def test_build_system_prompt(self):
        """Test system prompt contains Query Fan-Out instructions."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            generator = DynamicQueryGenerator()
            prompt = generator._build_system_prompt()
            
            # Should contain Query Fan-Out keywords
            assert "QUERY FAN-OUT" in prompt
            assert "GENERALIZATION" in prompt
            assert "FOLLOW-UPS" in prompt
            assert "broader lead intentions" in prompt.lower()
    
    def test_build_user_prompt(self):
        """Test user prompt construction."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            generator = DynamicQueryGenerator()
            
            # With industry
            prompt = generator._build_user_prompt(
                base_query="Sales Manager",
                industry="Software",
                count=5
            )
            assert "Sales Manager" in prompt
            assert "Software" in prompt
            assert "5" in prompt
            
            # Without industry
            prompt = generator._build_user_prompt(
                base_query="Sales Manager",
                industry=None,
                count=3
            )
            assert "Sales Manager" in prompt
            assert "3" in prompt
    
    def test_fallback_queries(self):
        """Test fallback query generation."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            generator = DynamicQueryGenerator()
            queries = generator._fallback_queries("Test Query")
            
            assert len(queries) == 1
            assert queries[0]["query"] == "Test Query"
            assert queries[0]["type"] == "original"
            assert "Fallback" in queries[0]["reason"]


@pytest.mark.asyncio
async def test_integration_generate_expanded_queries():
    """Integration test for query expansion (requires OPENAI_API_KEY)."""
    # Skip if no API key
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")
    
    generator = DynamicQueryGenerator()
    
    # Test with real API call
    queries = await generator.generate_expanded_queries(
        base_query="Sales Manager Hamburg",
        industry="B2B Software",
        count=3
    )
    
    # Should return queries
    assert len(queries) >= 1
    assert queries[0]["query"] == "Sales Manager Hamburg"
    assert all("query" in q for q in queries)
    assert all("type" in q for q in queries)


@pytest.mark.asyncio
async def test_integration_generate_dorks_with_fanout():
    """Integration test for dork generation with fan-out (requires OPENAI_API_KEY)."""
    # Skip if no API key
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")
    
    generator = DynamicQueryGenerator()
    
    # Test with real API call
    dorks = await generator.generate_dorks_with_fanout(
        industry="Software",
        count=3
    )
    
    # Should return dorks
    assert len(dorks) >= 1
    assert all(isinstance(d, str) for d in dorks)
    assert all(len(d) > 0 for d in dorks)


if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"])
