"""
Eisenhower Quadrant AI Classifier

Classifies tasks into one of four Eisenhower quadrants:
- important_urgent: Critical tasks that need immediate attention
- important_not_urgent: Important but can be planned
- not_important_urgent: Urgent but not important (can delegate)
- not_important_not_urgent: Neither important nor urgent (eliminate/decrease)
"""

import json
import logging
from typing import Optional, Dict, Any, Literal
from datetime import datetime

import redis
from openai import AsyncOpenAI
from pydantic import BaseModel, Field, field_validator

from backend.config import settings

logger = logging.getLogger(__name__)

# Module-level quadrant constants for easier imports
IMPORTANT_URGENT = "important_urgent"
IMPORTANT_NOT_URGENT = "important_not_urgent"
NOT_IMPORTANT_URGENT = "not_important_urgent"
NOT_IMPORTANT_NOT_URGENT = "not_important_not_urgent"


class QuadrantClassification(BaseModel):
    """Structured output from GPT-4 for task classification"""

    quadrant: Literal[
        "important_urgent",
        "important_not_urgent",
        "not_important_urgent",
        "not_important_not_urgent",
    ] = Field(
        ...,
        description="One of: important_urgent, important_not_urgent, not_important_urgent, not_important_not_urgent",
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")
    reasoning: str = Field(..., description="Explanation for the classification")
    keywords: list[str] = Field(
        default_factory=list, description="Keywords that influenced classification"
    )


class EisenhowerQuadrantClassifier:
    """
    AI-powered Eisenhower quadrant classifier with caching and fallback.
    """

    # Quadrant constants
    IMPORTANT_URGENT = "important_urgent"
    IMPORTANT_NOT_URGENT = "important_not_urgent"
    NOT_IMPORTANT_URGENT = "not_important_urgent"
    NOT_IMPORTANT_NOT_URGENT = "not_important_not_urgent"

    QUADRANTS = [
        IMPORTANT_URGENT,
        IMPORTANT_NOT_URGENT,
        NOT_IMPORTANT_URGENT,
        NOT_IMPORTANT_NOT_URGENT,
    ]

    def __init__(self):
        """Initialize classifier with OpenAI client and Redis connection"""
        # OpenAI client
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        # Redis client for caching
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL, decode_responses=True
            )
            self.redis_available = True
            logger.info("Redis connection established for classifier caching")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Caching disabled.")
            self.redis_client = None
            self.redis_available = False

        # Cache TTL (24 hours)
        self.cache_ttl = 86400

    def _generate_cache_key(
        self, task_title: str, task_description: Optional[str] = None
    ) -> str:
        """Generate a cache key for a task"""
        content = f"{task_title}|{task_description or ''}"
        return f"eisenhower:{hash(content)}"

    async def _classify_with_gpt4(
        self, task_title: str, task_description: Optional[str] = None
    ) -> QuadrantClassification:
        """
        Classify task using OpenAI GPT-4 with structured output.
        """
        prompt = self._build_classification_prompt(task_title, task_description)

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a productivity expert specializing in Eisenhower Matrix task classification.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,  # Low temperature for consistent results
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from OpenAI")

            data = json.loads(content)

            # Validate quadrant
            if data["quadrant"] not in self.QUADRANTS:
                raise ValueError(f"Invalid quadrant returned: {data['quadrant']}")

            return QuadrantClassification(
                quadrant=data["quadrant"],
                confidence=float(data.get("confidence", 0.7)),
                reasoning=data.get("reasoning", ""),
                keywords=data.get("keywords", []),
            )

        except Exception as e:
            logger.error(f"GPT-4 classification failed: {e}")
            raise

    def _build_classification_prompt(
        self, task_title: str, task_description: Optional[str] = None
    ) -> str:
        """Build the prompt for GPT-4 classification"""
        description_text = (
            f"\nDescription: {task_description}" if task_description else ""
        )

        return f"""Please classify the following task according to the Eisenhower Matrix (also known as the Eisenhower Box or Eisenhower Matrix):

The Eisenhower Matrix has 4 quadrants:
1. IMPORTANT & URGENT: Critical tasks requiring immediate attention. These are crises, deadlines, emergencies.
2. IMPORTANT & NOT URGENT: Important tasks for long-term goals. These include planning, relationship building, personal development, new opportunities.
3. NOT IMPORTANT & URGENT: Urgent but not important tasks that can often be delegated. These include some emails, meetings, interruptions.
4. NOT IMPORTANT & NOT URGENT: Tasks that are neither urgent nor important. These include time wasters, busy work, trivial tasks.

Task to classify:
Title: {task_title}{description_text}

Please respond with valid JSON in this exact format:
{{
    "quadrant": "important_urgent | important_not_urgent | not_important_urgent | not_important_not_urgent",
    "confidence": <float between 0.0 and 1.0>,
    "reasoning": "<explanation of why this classification was chosen>",
    "keywords": ["<keyword1>", "<keyword2>", ...]
}}

Think carefully about:
- Is the task critical to goals or survival? (Important)
- Does it have a tight deadline or require immediate action? (Urgent)
- Will it matter in 6 months or a year? (Important vs Not Important)
- Does someone else need to do it or can it be delegated? (Not Important)
- Is it just entertainment or low-value activity? (Not Important, Not Urgent)

Respond with JSON only."""

    def _classify_with_keywords(
        self, task_title: str, task_description: Optional[str] = None
    ) -> QuadrantClassification:
        """
        Fallback keyword-based classifier when GPT-4 is unavailable.
        Uses pattern matching on task title and description.
        """
        text = f"{task_title} {task_description or ''}".lower()

        # Keyword patterns for each quadrant
        urgent_important_keywords = [
            "emergency",
            "crisis",
            "urgent",
            "immediate",
            "asap",
            "deadline",
            "critical",
            "now",
            "today",
            "this week",
            "fix",
            "repair",
            "resolve",
            "accident",
            "problem",
            "issue",
            "crash",
            "failure",
            "outage",
        ]

        important_not_urgent_keywords = [
            "plan",
            "strategy",
            "goal",
            "improve",
            "learn",
            "develop",
            "relationship",
            "networking",
            "health",
            "exercise",
            "education",
            "career",
            "growth",
            "vision",
            "mission",
            "purpose",
            "future",
            "prevent",
            "prepare",
            "review",
            "analyze",
            "research",
        ]

        not_important_urgent_keywords = [
            "meeting",
            "email",
            "call",
            "interrupt",
            "request",
            "somebody",
            "someone",
            "ask",
            "quick",
            "small",
            "minor",
            "routine",
            "administrative",
            "paperwork",
            "report",
            "update",
            "inform",
        ]

        # Track matched keywords for each quadrant
        matched_keywords = {
            self.IMPORTANT_URGENT: [],
            self.IMPORTANT_NOT_URGENT: [],
            self.NOT_IMPORTANT_URGENT: [],
            self.NOT_IMPORTANT_NOT_URGENT: [],
        }

        # Score each quadrant and track keywords
        for keyword in urgent_important_keywords:
            if keyword in text:
                matched_keywords[self.IMPORTANT_URGENT].append(keyword)

        for keyword in important_not_urgent_keywords:
            if keyword in text:
                matched_keywords[self.IMPORTANT_NOT_URGENT].append(keyword)

        for keyword in not_important_urgent_keywords:
            if keyword in text:
                matched_keywords[self.NOT_IMPORTANT_URGENT].append(keyword)

        # Check for explicit not important/not urgent markers
        not_important_keywords = [
            "waste",
            "trivial",
            "busy work",
            "time waster",
            "entertainment",
            "social media",
            "tv",
            "netflix",
            "youtube",
        ]
        for term in not_important_keywords:
            if term in text:
                matched_keywords[self.NOT_IMPORTANT_NOT_URGENT].append(term)

        # Calculate scores from matched keywords
        scores = {
            quadrant: len(keywords) for quadrant, keywords in matched_keywords.items()
        }

        # Determine quadrant (default to not important not urgent if all scores are 0)
        max_score = max(scores.values())
        if max_score == 0:
            quadrant = self.NOT_IMPORTANT_NOT_URGENT
            confidence = 0.3
        else:
            # Get quadrant with highest score
            quadrant, max_q_score = max(scores.items(), key=lambda x: x[1])
            # Confidence based on score dominance
            second_max = sorted(scores.values())[-2] if len(scores) > 1 else 0
            if second_max == 0:
                confidence = 0.7
            else:
                confidence = min(0.9, 0.5 + (max_score - second_max) * 0.2)

        return QuadrantClassification(
            quadrant=quadrant,
            confidence=confidence,
            reasoning=f"Keyword-based classification: {', '.join(matched_keywords[quadrant])}",
            keywords=matched_keywords[quadrant],
        )

    async def classify(
        self,
        task_title: str,
        task_description: Optional[str] = None,
        use_cache: bool = True,
    ) -> QuadrantClassification:
        """
        Classify a task into an Eisenhower quadrant.

        Args:
            task_title: The task title
            task_description: Optional task description
            use_cache: Whether to use cached results (default True)

        Returns:
            QuadrantClassification with quadrant, confidence, reasoning, and keywords
        """
        # Check cache first if enabled and Redis is available
        if use_cache and self.redis_available:
            cache_key = self._generate_cache_key(task_title, task_description)
            try:
                cached = self.redis_client.get(cache_key)
                if cached:
                    data = json.loads(cached)
                    logger.info(f"Cache hit for task: {task_title[:50]}")
                    return QuadrantClassification(**data)
            except Exception as e:
                logger.warning(f"Cache read failed: {e}")

        # Try GPT-4 classification first
        try:
            result = await self._classify_with_gpt4(task_title, task_description)
        except Exception as e:
            logger.warning(f"GPT-4 classification failed, using fallback: {e}")
            result = self._classify_with_keywords(task_title, task_description)

        # Cache the result if Redis is available
        if self.redis_available and result.confidence > 0.5:
            cache_key = self._generate_cache_key(task_title, task_description)
            try:
                self.redis_client.setex(
                    cache_key, self.cache_ttl, json.dumps(result.model_dump())
                )
            except Exception as e:
                logger.warning(f"Cache write failed: {e}")

        return result

    def classify_sync(
        self, task_title: str, task_description: Optional[str] = None
    ) -> QuadrantClassification:
        """
        Synchronous classification using fallback only (for testing or when async not available).
        """
        return self._classify_with_keywords(task_title, task_description)

    async def bulk_classify(
        self, tasks: list[Dict[str, str]]
    ) -> list[QuadrantClassification]:
        """
        Classify multiple tasks efficiently.

        Args:
            tasks: List of dicts with 'title' and optional 'description' keys

        Returns:
            List of QuadrantClassification results
        """
        results = []
        for task in tasks:
            title = task["title"]
            description = task.get("description")
            result = await self.classify(title, description)
            results.append(result)
        return results


# Convenience function for quick classification
async def classify_task(
    task_title: str, task_description: Optional[str] = None
) -> QuadrantClassification:
    """
    Quick helper function to classify a single task.

    Args:
        task_title: The task title
        task_description: Optional task description

    Returns:
        QuadrantClassification result
    """
    classifier = EisenhowerQuadrantClassifier()
    return await classifier.classify(task_title, task_description)
