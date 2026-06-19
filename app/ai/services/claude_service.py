import hashlib
import json
import logging
import time
from anthropic import AsyncAnthropic
from typing import Dict, Any
import sentry_sdk
from sentry_sdk.tracing import trace
from app.config import settings
from app.ai.prompts.system_prompt import get_system_prompt
from app.ai.prompts.action_plan_prompt import ACTION_PLAN_USER_PROMPT
from app.ai.prompts.urgency_prompt import URGENCY_CLASSIFICATION_PROMPT
from app.ai.prompts.rights_prompt import RIGHTS_SUMMARY_PROMPT
from app.ai.prompts.checklist_prompt import DOCUMENT_CHECKLIST_PROMPT
from app.ai.schemas.action_plan import (
    ActionPlanResponse,
    ActionPlanContext,
    UrgencyLevel,
    UrgencyColor
)
from app.ai.schemas.urgency import UrgencyClassificationResponse, IntakeData
from app.ai.schemas.checklist import ChecklistResponse
from app.ai.pipeline.rag_pipeline import RAGPipeline
from app.ai.pipeline.cache_service import CacheService
from app.ai.safety.guardrails import SafetyGuardrails
from app.ai.safety.refusal_handler import RefusalHandler

logger = logging.getLogger(__name__)


class ClaudeService:
    """Main service for interacting with Claude API, with full observability and safety"""
    
    def __init__(self):
        self.client = AsyncAnthropic(
            api_key=settings.ANTHROPIC_API_KEY,
            max_retries=getattr(settings, 'CLAUDE_MAX_RETRIES', 3)
        )
        self.model = settings.CLAUDE_MODEL
        self.max_tokens = settings.CLAUDE_MAX_TOKENS
        self.temperature = getattr(settings, 'CLAUDE_TEMPERATURE', 0.3)
        self.rag = RAGPipeline()
        self.cache_service = CacheService()
        self.guardrails = SafetyGuardrails()
        self.refusal_handler = RefusalHandler()

    def _build_user_context(self, intake: ActionPlanContext, rag_chunks: str) -> str:
        """Build formatted user context for Claude"""
        return ACTION_PLAN_USER_PROMPT.format(
            state=intake.state,
            county=intake.county,
            urgency_days=intake.urgency_days,
            income_monthly=intake.income_monthly,
            household_size=intake.household_size,
            situation_type=intake.situation_type,
            has_received_notice=intake.has_received_notice,
            language=intake.language,
            rag_chunks=rag_chunks,
            prior_steps=intake.prior_steps or ""
        )

    @trace
    async def generate_action_plan(self, context: ActionPlanContext) -> ActionPlanResponse:
        """Generate full action plan with all safety, caching, and monitoring"""
        start_time = time.time()
        cache_hit = False
        tokens_used = 0

        try:
            with sentry_sdk.start_transaction(name="generate_action_plan", op="ai.claude") as transaction:
                transaction.set_tag("state", context.state)
                transaction.set_tag("language", context.language)
                transaction.set_tag("urgency_days", context.urgency_days)

                # Check cache
                cache_key = f"plan:{hashlib.md5(f'{context.state}{context.situation_type}{context.income_monthly}{context.urgency_days}'.encode()).hexdigest()}"
                cached = await self.cache_service.redis.get(cache_key)
                if cached:
                    logger.info("Cache hit: Action plan")
                    cache_hit = True
                    return ActionPlanResponse(**json.loads(cached))

                # Get RAG context
                rag_chunks = await self.rag.run(
                    state=context.state,
                    situation_type=context.situation_type,
                    county=context.county
                )

                # Build prompts
                system_prompt = get_system_prompt(context.language)
                user_prompt = self._build_user_context(context, rag_chunks)

                # Call Claude
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )

                raw_response = response.content[0].text if response.content else ""
                tokens_input = response.usage.input_tokens if hasattr(response, 'usage') else 0
                tokens_output = response.usage.output_tokens if hasattr(response, 'usage') else 0
                tokens_used = tokens_input + tokens_output

                # Parse and validate
                plan = await self.refusal_handler.handle_response(
                    raw_response,
                    ActionPlanResponse
                )

                # Apply safety guardrails
                plan = await self.guardrails.check_output(plan)

                # Cache the result
                await self.cache_service.redis.setex(
                    cache_key,
                    getattr(settings, 'CACHE_TTL_PLANS', 3600),
                    plan.model_dump_json()
                )

                # Log structured event
                latency_ms = int((time.time() - start_time) * 1000)
                logger.info(
                    json.dumps({
                        "event": "claude_api_call",
                        "model": self.model,
                        "state": context.state,
                        "urgency_level": plan.urgency_level.value if hasattr(plan.urgency_level, 'value') else str(plan.urgency_level),
                        "tokens_input": tokens_input,
                        "tokens_output": tokens_output,
                        "latency_ms": latency_ms,
                        "cache_hit": cache_hit,
                        "rag_chunks_used": rag_chunks.count("[SOURCE"),
                        "safety_passed": True,
                        "retries": 0,
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    })
                )

                # Track in PostHog if configured
                if getattr(settings, 'POSTHOG_API_KEY', None):
                    try:
                        import posthog
                        posthog.capture(
                            distinct_id="system",
                            event="action_plan_generated",
                            properties={
                                "state": context.state,
                                "urgency": plan.urgency_level.value if hasattr(plan.urgency_level, 'value') else str(plan.urgency_level),
                                "language": context.language
                            }
                        )
                    except Exception:
                        pass

                return plan

        except Exception as e:
            logger.error(f"Error generating action plan: {str(e)}", exc_info=True)
            sentry_sdk.capture_exception(e)
            return self.refusal_handler.get_fallback_response()

    @trace
    async def classify_urgency(self, intake_data: IntakeData) -> UrgencyClassificationResponse:
        """Classify urgency level of situation (fast, no RAG)"""
        start_time = time.time()

        try:
            with sentry_sdk.start_transaction(name="classify_urgency", op="ai.claude") as transaction:
                transaction.set_tag("state", intake_data.state)
                transaction.set_tag("urgency_days", intake_data.urgency_days)

                system_prompt = "You are a housing urgency classifier. Return only JSON, no other text."
                user_prompt = URGENCY_CLASSIFICATION_PROMPT.format(
                    urgency_days=intake_data.urgency_days,
                    has_received_notice=intake_data.has_received_notice,
                    situation_type=intake_data.situation_type,
                    state=intake_data.state
                )

                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=300,
                    temperature=0.0,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )

                raw_response = response.content[0].text if response.content else ""
                result = await self.refusal_handler.handle_response(
                    raw_response,
                    UrgencyClassificationResponse
                )

                latency_ms = int((time.time() - start_time) * 1000)
                logger.info(
                    json.dumps({
                        "event": "claude_api_call",
                        "model": self.model,
                        "state": intake_data.state,
                        "urgency_level": result.urgency_level.value if hasattr(result.urgency_level, 'value') else str(result.urgency_level),
                        "latency_ms": latency_ms,
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    })
                )

                return result

        except Exception as e:
            logger.error(f"Error classifying urgency: {str(e)}", exc_info=True)
            sentry_sdk.capture_exception(e)
            return UrgencyClassificationResponse(
                urgency_level=UrgencyLevel.CRITICAL,
                urgency_reason="Error classifying urgency, please contact 211 immediately",
                urgency_color=UrgencyColor.RED,
                show_911=False,
                show_211=True,
                hours_to_act=24
            )

    @trace
    async def generate_rights_summary(self, state: str, language: str) -> Dict[str, Any]:
        """Generate rights summary (heavily cached)"""
        try:
            with sentry_sdk.start_transaction(name="generate_rights_summary", op="ai.claude") as transaction:
                transaction.set_tag("state", state)
                transaction.set_tag("language", language)

                # Check cache
                cached = await self.cache_service.get_rights_summary(state, language)
                if cached:
                    return cached

                # Get RAG context
                rag_chunks = await self.rag.run(
                    state=state,
                    situation_type="EVICTION_NOTICE",
                    county="ALL"
                )

                # Build prompts
                system_prompt = get_system_prompt(language)
                user_prompt = RIGHTS_SUMMARY_PROMPT.format(
                    state=state,
                    situation_type="EVICTION_NOTICE",
                    rag_chunks=rag_chunks
                )

                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=1000,
                    temperature=self.temperature,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )

                raw_response = response.content[0].text if response.content else ""
                summary = json.loads(raw_response)

                # Cache the result
                await self.cache_service.set_rights_summary(state, language, summary)

                return summary

        except Exception as e:
            logger.error(f"Error generating rights summary: {str(e)}", exc_info=True)
            sentry_sdk.capture_exception(e)
            return {}

    @trace
    async def generate_checklist(self, intake_data: IntakeData) -> ChecklistResponse:
        """Generate document checklist"""
        try:
            with sentry_sdk.start_transaction(name="generate_checklist", op="ai.claude") as transaction:
                transaction.set_tag("state", intake_data.state)

                system_prompt = get_system_prompt(intake_data.language)
                user_prompt = DOCUMENT_CHECKLIST_PROMPT.format(
                    state=intake_data.state,
                    county=intake_data.county,
                    situation_type=intake_data.situation_type,
                    urgency_days=intake_data.urgency_days
                )

                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=1000,
                    temperature=self.temperature,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )

                raw_response = response.content[0].text if response.content else ""
                return await self.refusal_handler.handle_response(
                    raw_response,
                    ChecklistResponse
                )

        except Exception as e:
            logger.error(f"Error generating checklist: {str(e)}", exc_info=True)
            sentry_sdk.capture_exception(e)
            return ChecklistResponse(
                documents=[],
                disclaimer="This is informational guidance only, not legal advice. Contact Legal Aid for legal questions."
            )

    @trace
    async def translate_content(self, content: str, target_lang: str) -> str:
        """Translate content between EN and ES"""
        try:
            cache_key = f"translation:{hashlib.md5(content.encode()).hexdigest()}:{target_lang}"
            cached = await self.cache_service.redis.get(cache_key)
            if cached:
                return cached

            system_prompt = "You are a professional translator. Translate the content accurately while preserving all phone numbers, URLs, and formatting."
            from app.ai.prompts.spanish_prompt import SPANISH_TRANSLATION_PROMPT
            user_prompt = SPANISH_TRANSLATION_PROMPT.format(content=content)

            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.3,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )

            translated = response.content[0].text if response.content else content
            await self.cache_service.redis.setex(cache_key, getattr(settings, 'CACHE_TTL_RIGHTS', 86400), translated)

            return translated

        except Exception as e:
            logger.error(f"Error translating content: {str(e)}", exc_info=True)
            sentry_sdk.capture_exception(e)
            return content
